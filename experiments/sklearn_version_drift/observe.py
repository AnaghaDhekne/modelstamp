"""Observe baseline and Modelstamp behavior in one pinned environment."""

from __future__ import annotations

import argparse
import json
import platform
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List

import joblib
import numpy
import scipy
import sklearn
from sklearn.base import BaseEstimator
from sklearn.datasets import load_iris
from sklearn.exceptions import InconsistentVersionWarning

import modelstamp


def _warning_record(item: warnings.WarningMessage) -> Dict[str, str]:
    return {
        "category": item.category.__name__,
        "message": str(item.message),
    }


def _predictions(model: Any) -> Dict[str, Any]:
    X, _ = load_iris(return_X_y=True)
    probe = X[:20]
    return {
        "predictions": model.predict(probe).tolist(),
        "probabilities": model.predict_proba(probe).round(12).tolist(),
    }


def _trace_joblib_load(
    operation: Callable[[], Any],
) -> tuple[Any, List[str], Exception | None]:
    calls: List[str] = []
    original = joblib.load

    def traced_load(*args: Any, **kwargs: Any) -> Any:
        calls.append("joblib.load")
        return original(*args, **kwargs)

    joblib.load = traced_load
    result = None
    error = None
    try:
        result = operation()
    except Exception as exc:
        error = exc
    finally:
        joblib.load = original
    return result, calls, error


def baseline_observation(path: Path, expected: Dict[str, Any]) -> Dict[str, Any]:
    reconstruction_calls: List[str] = []
    original_setstate = BaseEstimator.__setstate__

    def traced_setstate(self: BaseEstimator, state: Dict[str, Any]) -> None:
        reconstruction_calls.append(f"{type(self).__module__}.{type(self).__name__}")
        original_setstate(self, state)

    BaseEstimator.__setstate__ = traced_setstate
    caught: List[warnings.WarningMessage] = []
    error = None
    loaded = None
    try:
        with warnings.catch_warnings(record=True) as records:
            warnings.simplefilter("always")
            try:
                loaded = joblib.load(path)
            except Exception as exc:  # Preserve baseline behavior as data.
                error = f"{type(exc).__name__}: {exc}"
            caught = list(records)
    finally:
        BaseEstimator.__setstate__ = original_setstate

    outputs = _predictions(loaded) if loaded is not None else None
    warning_records = [_warning_record(item) for item in caught]
    return {
        "system": "joblib + scikit-learn baseline",
        "operation": "joblib.load",
        "load_succeeded": loaded is not None,
        "error": error,
        "reconstruction_started": bool(reconstruction_calls),
        "reconstruction_calls": reconstruction_calls,
        "warnings": warning_records,
        "inconsistent_version_warning": any(
            item.category is InconsistentVersionWarning for item in caught
        ),
        "outputs": outputs,
        "predictions_match_save_environment": bool(
            outputs
            and outputs["predictions"] == expected["expected_predictions"]
            and outputs["probabilities"] == expected["expected_probabilities"]
        ),
    }


def modelstamp_observation(path: Path, expected: Dict[str, Any]) -> Dict[str, Any]:
    report, check_calls, check_error = _trace_joblib_load(
        lambda: modelstamp.check(path)
    )
    if check_error is not None:
        raise check_error
    package_changes = [
        {"name": item.name, "saved": item.saved, "current": item.current}
        for item in report.package_changes
    ]

    strict_error = None
    strict_model = None

    def strict_load() -> Any:
        return modelstamp.load(path, on_mismatch="raise", return_manifest=False)

    strict_model, strict_calls, strict_exception = _trace_joblib_load(strict_load)
    if strict_exception is not None:
        strict_error = f"{type(strict_exception).__name__}: {strict_exception}"

    strict_outputs = _predictions(strict_model) if strict_model is not None else None
    return {
        "system": "modelstamp",
        "preload_check": {
            "operation": "modelstamp.check",
            "mismatch": bool(report),
            "package_changes": package_changes,
            "runtime_changes": report.runtime_changes,
            "integrity_error": report.integrity_error,
            "deserialized": bool(check_calls),
            "loader_calls": check_calls,
        },
        "strict_load": {
            "operation": 'modelstamp.load(on_mismatch="raise")',
            "load_succeeded": strict_model is not None,
            "error": strict_error,
            "environment_mismatch_error": bool(
                strict_error and strict_error.startswith("EnvironmentMismatchError:")
            ),
            "deserialized": bool(strict_calls),
            "loader_calls": strict_calls,
            "outputs": strict_outputs,
            "predictions_match_save_environment": bool(
                strict_outputs
                and strict_outputs["predictions"] == expected["expected_predictions"]
                and strict_outputs["probabilities"]
                == expected["expected_probabilities"]
            ),
        },
    }


def validate(condition: str, result: Dict[str, Any]) -> None:
    baseline = result["baseline"]
    preload = result["modelstamp"]["preload_check"]
    strict = result["modelstamp"]["strict_load"]

    assert baseline["load_succeeded"]
    assert baseline["reconstruction_started"]
    assert not preload["deserialized"]

    if condition == "control":
        assert not baseline["inconsistent_version_warning"]
        assert baseline["predictions_match_save_environment"]
        assert not preload["mismatch"]
        assert not preload["package_changes"]
        assert strict["load_succeeded"]
        assert strict["deserialized"]
        assert strict["predictions_match_save_environment"]
    else:
        assert baseline["inconsistent_version_warning"]
        assert [item["name"] for item in preload["package_changes"]] == ["scikit-learn"]
        assert preload["package_changes"][0]["saved"] == "1.5.2"
        assert preload["package_changes"][0]["current"] == "1.6.1"
        assert strict["environment_mismatch_error"]
        assert not strict["load_succeeded"]
        assert not strict["deserialized"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", choices=("control", "drift"), required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    artifacts = args.artifacts.resolve()
    expected = json.loads(
        (artifacts / "save_metadata.json").read_text(encoding="utf-8")
    )
    result = {
        "protocol_version": 1,
        "condition": args.condition,
        "environment": {
            "python": platform.python_version(),
            "packages": {
                "modelstamp": modelstamp.__version__,
                "scikit-learn": sklearn.__version__,
                "numpy": numpy.__version__,
                "scipy": scipy.__version__,
                "joblib": joblib.__version__,
            },
        },
        "baseline": baseline_observation(artifacts / "baseline.joblib", expected),
        "modelstamp": modelstamp_observation(artifacts / "modelstamp.joblib", expected),
    }
    validate(args.condition, result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

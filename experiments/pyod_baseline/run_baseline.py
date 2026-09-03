import json
from pathlib import Path

import joblib
import modelstamp
import sklearn
from pyod.utils.persistence import load as pyod_load


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
RESULTS = ROOT / "results.json"


def modelstamp_observation():
    report = modelstamp.check(ARTIFACTS / "modelstamp.joblib")
    return {
        "system": "modelstamp",
        "operation": "check",
        "sklearn_version": sklearn.__version__,
        "drift_detected": bool(report),
        "package_changes": [
            {
                "name": change.name,
                "saved": change.saved,
                "current": change.current,
            }
            for change in report.package_changes
        ],
        "deserialized": False,
        "basis": "modelstamp.check() does not call the serialization backend loader",
    }


def pyod_observation():
    calls = []
    original_load = joblib.load

    def traced_load(*args, **kwargs):
        calls.append("joblib.load")
        return original_load(*args, **kwargs)

    joblib.load = traced_load
    error = None
    try:
        pyod_load(ARTIFACTS / "pyod.joblib", trusted=True, strict=True)
    except Exception as exc:  # Record strict-version rejection without hiding it.
        error = f"{type(exc).__name__}: {exc}"
    finally:
        joblib.load = original_load

    return {
        "system": "pyod",
        "operation": "load(trusted=True, strict=True)",
        "sklearn_version": sklearn.__version__,
        "drift_detected": error is not None,
        "deserialized": bool(calls),
        "loader_calls": calls,
        "error": error,
    }


def main():
    observations = [modelstamp_observation(), pyod_observation()]
    RESULTS.write_text(json.dumps(observations, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(observations, indent=2))


if __name__ == "__main__":
    main()

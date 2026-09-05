"""Fit and persist equivalent baseline and Modelstamp artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import joblib
import numpy
import scipy
import sklearn
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

import modelstamp


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    baseline_path = output / "baseline.joblib"
    modelstamp_path = output / "modelstamp.joblib"

    X, y = load_iris(return_X_y=True)
    model = LogisticRegression(max_iter=500, random_state=0).fit(X, y)
    probe = X[:20]
    expected_predictions = model.predict(probe).tolist()
    expected_probabilities = model.predict_proba(probe).round(12).tolist()

    joblib.dump(model, baseline_path)
    manifest = modelstamp.save(
        model,
        modelstamp_path,
        backend="joblib",
        include_git=False,
        metadata={
            "experiment": "sklearn-version-drift",
            "dataset": "sklearn.datasets.load_iris",
            "probe_rows": 20,
        },
    )

    metadata = {
        "protocol_version": 1,
        "python": platform.python_version(),
        "packages": {
            "modelstamp": modelstamp.__version__,
            "scikit-learn": sklearn.__version__,
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "joblib": joblib.__version__,
        },
        "model": {
            "class": type(model).__name__,
            "module": type(model).__module__,
            "parameters": {"max_iter": 500, "random_state": 0},
            "training_dataset": "sklearn.datasets.load_iris",
            "probe_rows": 20,
        },
        "expected_predictions": expected_predictions,
        "expected_probabilities": expected_probabilities,
        "artifacts": {
            "baseline.joblib": {
                "sha256": _sha256(baseline_path),
                "size_bytes": baseline_path.stat().st_size,
            },
            "modelstamp.joblib": {
                "sha256": _sha256(modelstamp_path),
                "size_bytes": modelstamp_path.stat().st_size,
                "relevant_packages": manifest.relevant_packages,
            },
        },
    }
    destination = output / "save_metadata.json"
    destination.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()

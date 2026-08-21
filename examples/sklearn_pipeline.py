"""Train, verify, and restore a scikit-learn pipeline with Modelstamp."""

from pathlib import Path
from tempfile import TemporaryDirectory

from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import modelstamp as ms


def main() -> None:
    X, y = load_iris(return_X_y=True)
    pipeline = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=500, random_state=0),
    )
    pipeline.fit(X, y)

    with TemporaryDirectory() as directory:
        path = Path(directory) / "iris.joblib"
        manifest = ms.save(
            pipeline,
            path,
            metadata={"dataset": "iris", "purpose": "documentation example"},
        )

        ms.verify(path)
        report = ms.check(path)
        restored, _ = ms.load(path, on_mismatch="raise")

        print(f"SHA-256: {manifest.artifact['sha256']}")
        print(f"Relevant packages: {manifest.relevant_packages}")
        print(f"Compatibility report: {report}")
        print(f"Predictions: {restored.predict(X[:3]).tolist()}")


if __name__ == "__main__":
    main()

from pathlib import Path

from pyod.utils.persistence import save as pyod_save
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

import modelstamp

OUT = Path("experiments/pyod_baseline/artifacts")
OUT.mkdir(parents=True, exist_ok=True)

X, y = load_iris(return_X_y=True)
model = LogisticRegression(max_iter=500, random_state=0).fit(X, y)

modelstamp.save(
    model,
    OUT / "modelstamp.joblib",
    backend="joblib",
    include_git=False,
)
pyod_save(
    model,
    OUT / "pyod.joblib",
    metadata={"experiment": "pyod-baseline"},
)

print("created", OUT / "modelstamp.joblib")
print("created", OUT / "pyod.joblib")

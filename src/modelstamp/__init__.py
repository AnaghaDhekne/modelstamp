"""modelstamp -- version-aware persistence for scikit-learn and friends.

Wrap ``joblib.dump`` / ``joblib.load`` (or stdlib pickle) so every saved model
carries a manifest of the environment it was trained in. On load, modelstamp
diffs the current environment and warns you when a package changed underneath
you -- the silent-prediction-drift bug that scikit-learn's own docs tell you
to guard against by hand.

    import modelstamp as ms

    ms.save(pipeline, "model.pkl", metadata={"cv_accuracy": 0.94})
    model, info = ms.load("model.pkl")   # warns if sklearn/numpy/... differ
"""

from __future__ import annotations

from ._manifest import Manifest, MismatchReport, PackageChange
from .core import check, inspect, load, save, verify
from .exceptions import (
    ArtifactIntegrityError,
    EnvironmentMismatchError,
    EnvironmentMismatchWarning,
    ManifestError,
    ModelStampWarning,
)

__version__ = "0.1.0"

__all__ = [
    "ArtifactIntegrityError",
    "EnvironmentMismatchError",
    "EnvironmentMismatchWarning",
    "ManifestError",
    "ModelStampWarning",
    "Manifest",
    "MismatchReport",
    "PackageChange",
    "__version__",
    "check",
    "inspect",
    "load",
    "save",
    "verify",
]

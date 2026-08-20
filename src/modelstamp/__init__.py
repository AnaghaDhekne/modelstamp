"""Integrity-checked persistence for Python machine-learning models.

``modelstamp`` saves a model with a sidecar manifest that records its checksum,
serialization backend, model details, and runtime dependency versions. The
artifact is verified before deserialization, and environment differences can
warn or block loading.

Example
-------
>>> import modelstamp as ms
>>> ms.save(model, "model.joblib", metadata={"validation_roc_auc": 0.883})
>>> model, manifest = ms.load("model.joblib")
>>> ms.verify("model.joblib")
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from ._manifest import Manifest, MismatchReport
from .core import check, inspect, load, save, verify
from .exceptions import (
    ArtifactIntegrityError,
    EnvironmentMismatchError,
    EnvironmentMismatchWarning,
    ManifestError,
    ModelStampWarning,
)

try:
    __version__ = version("modelstamp")
except PackageNotFoundError:  # pragma: no cover - uninstalled source tree.
    __version__ = "0+unknown"

__all__ = [
    # Operations
    "save",
    "load",
    "verify",
    "check",
    "inspect",
    # Result types
    "Manifest",
    "MismatchReport",
    # Errors and warnings
    "ArtifactIntegrityError",
    "EnvironmentMismatchError",
    "EnvironmentMismatchWarning",
    "ManifestError",
    "ModelStampWarning",
    # Package metadata
    "__version__",
]

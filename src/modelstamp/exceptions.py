"""Warning and exception types raised by modelstamp."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._manifest import MismatchReport


class ModelStampWarning(UserWarning):
    """Base class for all warnings emitted by modelstamp."""


class EnvironmentMismatchWarning(ModelStampWarning):
    """Emitted when the load-time environment differs from the save-time one."""


class EnvironmentMismatchError(RuntimeError):
    """Raised instead of warning when ``load(..., on_mismatch="raise")``."""

    def __init__(self, report: "MismatchReport") -> None:
        super().__init__(str(report))
        self.report = report


class ArtifactIntegrityError(RuntimeError):
    """Raised when a model does not match the digest in its manifest."""


class ManifestError(RuntimeError):
    """Raised when a manifest file is missing or malformed."""

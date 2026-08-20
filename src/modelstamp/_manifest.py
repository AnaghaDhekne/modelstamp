"""Manifest models, validation, serialization, and environment comparison."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ._environment import capture_environment
from .exceptions import ManifestError

MANIFEST_SCHEMA_VERSION = 1


@dataclass
class PackageChange:
    """One relevant package whose version changed or disappeared."""

    name: str
    saved: Optional[str]
    current: Optional[str]

    def describe(self) -> str:
        if self.current is None:
            return f"{self.name}: {self.saved} at save time -> not installed now"
        return f"{self.name}: {self.saved} -> {self.current}"


@dataclass
class MismatchReport:
    """Comparison of the saved runtime with the current runtime."""

    package_changes: List[PackageChange] = field(default_factory=list)
    runtime_changes: List[str] = field(default_factory=list)
    integrity_error: Optional[str] = None

    @property
    def has_mismatch(self) -> bool:
        return bool(
            self.package_changes or self.runtime_changes or self.integrity_error
        )

    def __bool__(self) -> bool:
        return self.has_mismatch

    def __str__(self) -> str:
        if not self.has_mismatch:
            return "Environment and artifact match the saved manifest."
        lines = ["Model artifact check found differences:"]
        if self.integrity_error:
            lines.append(f"  integrity: {self.integrity_error}")
        lines.extend(f"  {change}" for change in self.runtime_changes)
        lines.extend(f"  {change.describe()}" for change in self.package_changes)
        if self.package_changes or self.runtime_changes:
            lines.append(
                "Loading under this runtime is unsupported and behavior may differ."
            )
        return "\n".join(lines)


@dataclass
class Manifest:
    """Validated record describing a serialized model artifact."""

    environment: Dict[str, object]
    artifact: Dict[str, object]
    serialization: Dict[str, object]
    model: Dict[str, object]
    relevant_packages: List[str]
    metadata: Dict[str, object] = field(default_factory=dict)
    schema_version: int = MANIFEST_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "artifact": self.artifact,
            "serialization": self.serialization,
            "model": self.model,
            "environment": self.environment,
            "relevant_packages": self.relevant_packages,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Manifest":
        if not isinstance(data, dict):
            raise ManifestError("manifest root must be a JSON object")
        version = data.get("schema_version")
        if version != MANIFEST_SCHEMA_VERSION:
            raise ManifestError(
                f"unsupported schema_version {version!r}; "
                f"expected {MANIFEST_SCHEMA_VERSION}"
            )
        required_dicts = (
            "environment",
            "artifact",
            "serialization",
            "model",
            "metadata",
        )
        for key in required_dicts:
            if not isinstance(data.get(key), dict):
                raise ManifestError(f"{key!r} must be a JSON object")
        relevant = data.get("relevant_packages")
        if not isinstance(relevant, list) or not all(
            isinstance(item, str) for item in relevant
        ):
            raise ManifestError("'relevant_packages' must be a list of strings")
        artifact = dict(data["artifact"])
        if not isinstance(artifact.get("sha256"), str):
            raise ManifestError("artifact.sha256 must be a string")
        if not isinstance(artifact.get("size_bytes"), int):
            raise ManifestError("artifact.size_bytes must be an integer")
        serialization = dict(data["serialization"])
        if serialization.get("backend") not in ("pickle", "joblib"):
            raise ManifestError("serialization.backend must be pickle or joblib")
        environment = dict(data["environment"])
        if not isinstance(environment.get("packages"), dict):
            raise ManifestError("environment.packages must be a JSON object")
        return cls(
            environment=environment,
            artifact=artifact,
            serialization=serialization,
            model=dict(data["model"]),
            relevant_packages=list(relevant),
            metadata=dict(data["metadata"]),
            schema_version=version,
        )

    @classmethod
    def from_json(cls, text: str) -> "Manifest":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ManifestError(f"invalid JSON: {exc}") from exc
        return cls.from_dict(data)

    def compare_to_current(self) -> MismatchReport:
        return _diff_environments(
            self.environment,
            capture_environment(),
            self.relevant_packages,
        )


def _diff_environments(
    saved: Dict[str, object],
    current: Dict[str, object],
    relevant_packages: Optional[List[str]] = None,
) -> MismatchReport:
    saved_pkgs = dict(saved.get("packages", {}) or {})
    current_pkgs = dict(current.get("packages", {}) or {})
    names = relevant_packages if relevant_packages is not None else list(saved_pkgs)
    changes = []
    for name in sorted(set(names)):
        saved_v = saved_pkgs.get(name)
        current_v = current_pkgs.get(name)
        if saved_v != current_v:
            changes.append(PackageChange(name, saved_v, current_v))

    runtime_changes = []
    runtime_fields = (
        ("python_version", "python"),
        ("python_implementation", "python implementation"),
        ("platform", "platform"),
    )
    for key, label in runtime_fields:
        saved_value = saved.get(key)
        current_value = current.get(key)
        if saved_value and current_value and saved_value != current_value:
            runtime_changes.append(f"{label}: {saved_value} -> {current_value}")
    return MismatchReport(package_changes=changes, runtime_changes=runtime_changes)

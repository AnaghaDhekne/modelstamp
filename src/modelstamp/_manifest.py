"""Manifest models, validation, serialization, and environment comparison."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ._environment import capture_environment
from .exceptions import ManifestError

MANIFEST_SCHEMA_VERSION = 1


def _nonempty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field_name} must be a non-empty string")
    return value


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
    signature: Optional[Dict[str, str]] = None
    schema_version: int = MANIFEST_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, object]:
        data = {
            "schema_version": self.schema_version,
            "artifact": self.artifact,
            "serialization": self.serialization,
            "model": self.model,
            "environment": self.environment,
            "relevant_packages": self.relevant_packages,
            "metadata": self.metadata,
        }
        if self.signature is not None:
            data["signature"] = self.signature
        return data

    def signing_bytes(self) -> bytes:
        """Return a stable representation used by keyed manifest signatures."""
        data = self.to_dict()
        signature = data.pop("signature", None)
        # Legacy signatures covered the manifest without a signature object.
        # Keyed signatures also bind the algorithm and key identifier so an
        # attacker cannot redirect verification to a different registry entry.
        if isinstance(signature, dict) and "key_id" in signature:
            data["signature"] = {
                "algorithm": signature["algorithm"],
                "key_id": signature["key_id"],
            }
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(), indent=indent, sort_keys=False, allow_nan=False
        )

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Manifest":
        if not isinstance(data, dict):
            raise ManifestError("manifest root must be a JSON object")
        version = data.get("schema_version")
        if (
            isinstance(version, bool)
            or not isinstance(version, int)
            or version != MANIFEST_SCHEMA_VERSION
        ):
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
            isinstance(item, str) and bool(item.strip()) for item in relevant
        ):
            raise ManifestError(
                "'relevant_packages' must be a list of non-empty strings"
            )
        artifact = dict(data["artifact"])
        filename = _nonempty_string(artifact.get("filename"), "artifact.filename")
        if filename != filename.rsplit("/", 1)[-1] or "\\" in filename:
            raise ManifestError("artifact.filename must not contain directories")
        digest = _nonempty_string(artifact.get("sha256"), "artifact.sha256")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ManifestError(
                "artifact.sha256 must be 64 lowercase hexadecimal characters"
            )
        size = artifact.get("size_bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ManifestError("artifact.size_bytes must be a non-negative integer")

        serialization = dict(data["serialization"])
        if serialization.get("backend") not in ("pickle", "joblib"):
            raise ManifestError("serialization.backend must be pickle or joblib")

        signature_data = data.get("signature")
        signature: Optional[Dict[str, str]] = None
        if signature_data is not None:
            if not isinstance(signature_data, dict):
                raise ManifestError("signature must be a JSON object")
            allowed_signature_fields = {"algorithm", "digest", "key_id"}
            if not {"algorithm", "digest"}.issubset(signature_data) or not set(
                signature_data
            ).issubset(allowed_signature_fields):
                raise ManifestError(
                    "signature must contain algorithm and digest, with optional key_id"
                )
            if signature_data.get("algorithm") != "hmac-sha256":
                raise ManifestError("signature.algorithm must be hmac-sha256")
            signature_digest = _nonempty_string(
                signature_data.get("digest"), "signature.digest"
            )
            if len(signature_digest) != 64 or any(
                char not in "0123456789abcdef" for char in signature_digest
            ):
                raise ManifestError(
                    "signature.digest must be 64 lowercase hexadecimal characters"
                )
            signature = {
                "algorithm": "hmac-sha256",
                "digest": signature_digest,
            }
            if "key_id" in signature_data:
                key_id = _nonempty_string(
                    signature_data.get("key_id"), "signature.key_id"
                )
                if key_id != key_id.strip():
                    raise ManifestError(
                        "signature.key_id must not have leading or trailing whitespace"
                    )
                if len(key_id) > 128:
                    raise ManifestError(
                        "signature.key_id must be at most 128 characters"
                    )
                signature["key_id"] = key_id

        model = dict(data["model"])
        _nonempty_string(model.get("class"), "model.class")
        _nonempty_string(model.get("module"), "model.module")
        components = model.get("components", [])
        if not isinstance(components, list):
            raise ManifestError("model.components must be a list")
        for index, component in enumerate(components):
            if not isinstance(component, dict):
                raise ManifestError(f"model.components[{index}] must be an object")
            for key in ("name", "class", "module"):
                _nonempty_string(component.get(key), f"model.components[{index}].{key}")

        environment = dict(data["environment"])
        for key in (
            "python_version",
            "python_implementation",
            "platform",
            "created_at",
        ):
            _nonempty_string(environment.get(key), f"environment.{key}")
        packages = environment.get("packages")
        if not isinstance(packages, dict):
            raise ManifestError("environment.packages must be a JSON object")
        if not all(
            isinstance(name, str)
            and bool(name)
            and isinstance(package_version, str)
            and bool(package_version)
            for name, package_version in packages.items()
        ):
            raise ManifestError(
                "environment.packages must map non-empty names to versions"
            )
        if len(relevant) != len(set(relevant)):
            raise ManifestError("relevant_packages must not contain duplicates")
        unknown_relevant = set(relevant) - set(packages)
        if unknown_relevant:
            names = ", ".join(sorted(unknown_relevant))
            raise ManifestError(
                f"relevant_packages contains packages absent from environment: {names}"
            )
        return cls(
            environment=environment,
            artifact=artifact,
            serialization=serialization,
            model=model,
            relevant_packages=list(relevant),
            metadata=dict(data["metadata"]),
            signature=signature,
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

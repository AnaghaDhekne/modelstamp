"""Public persistence API with manifests and pre-deserialization verification."""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import tempfile
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ._environment import capture_environment
from ._manifest import Manifest, MismatchReport
from .exceptions import (
    ArtifactIntegrityError,
    EnvironmentMismatchError,
    EnvironmentMismatchWarning,
    ManifestError,
)

PathLike = Union[str, Path]

try:
    import joblib as _joblib
except ImportError:  # pragma: no cover
    _joblib = None


def _manifest_path(model_path: Path) -> Path:
    return model_path.with_name(model_path.name + ".manifest.json")


def _resolve_save_backend(backend: str) -> str:
    if backend == "auto":
        return "joblib" if _joblib is not None else "pickle"
    if backend not in ("joblib", "pickle"):
        raise ValueError("backend must be 'auto', 'joblib', or 'pickle'")
    if backend == "joblib" and _joblib is None:
        raise ImportError("backend='joblib' requires the optional joblib package")
    return backend


def _resolve_load_backend(requested: str, manifest: Manifest) -> str:
    if requested == "auto":
        backend = str(manifest.serialization["backend"])
    else:
        backend = _resolve_save_backend(requested)
        recorded = manifest.serialization["backend"]
        if backend != recorded:
            raise ManifestError(
                f"requested backend {backend!r} differs from recorded {recorded!r}"
            )
    if backend == "joblib" and _joblib is None:
        raise ImportError(
            "this artifact was saved with joblib; install modelstamp[joblib]"
        )
    return backend


def _dump(obj: Any, path: Path, backend: str) -> None:
    if backend == "joblib":
        if _joblib is None:  # Defensive guard for direct internal calls.
            raise ImportError("joblib is not installed")
        _joblib.dump(obj, path)
    else:
        with path.open("wb") as stream:
            pickle.dump(obj, stream, protocol=pickle.HIGHEST_PROTOCOL)


def _load_object(path: Path, backend: str) -> Any:
    if backend == "joblib":
        if _joblib is None:  # Defensive guard for direct internal calls.
            raise ImportError("joblib is not installed")
        return _joblib.load(path)
    with path.open("rb") as stream:
        return pickle.load(stream)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _model_details(obj: Any) -> Tuple[Dict[str, object], List[str]]:
    cls = type(obj)
    details: Dict[str, object] = {"class": cls.__name__, "module": cls.__module__}
    modules = {cls.__module__.split(".", 1)[0]}
    steps = getattr(obj, "steps", None)
    if isinstance(steps, list) and all(
        isinstance(step, tuple)
        and len(step) == 2
        and isinstance(step[0], str)
        and bool(step[0])
        for step in steps
    ):
        components = []
        for name, component in steps:
            component_cls = type(component)
            components.append(
                {
                    "name": name,
                    "class": component_cls.__name__,
                    "module": component_cls.__module__,
                }
            )
            modules.add(component_cls.__module__.split(".", 1)[0])
        details["components"] = components

    relevant = set()
    if "sklearn" in modules:
        relevant.update(("scikit-learn", "numpy", "scipy", "joblib"))
    mapping = {
        "numpy": "numpy",
        "pandas": "pandas",
        "xgboost": "xgboost",
        "lightgbm": "lightgbm",
        "catboost": "catboost",
    }
    relevant.update(mapping[module] for module in modules if module in mapping)
    return details, sorted(relevant)


def _stage_text(path: Path, content: str) -> Path:
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        return Path(temporary)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _commit_artifact_pair(
    staged_model: Path,
    model_path: Path,
    staged_manifest: Path,
    manifest_path: Path,
) -> None:
    backup_path: Optional[Path] = None
    if model_path.exists():
        descriptor, backup_name = tempfile.mkstemp(
            prefix=f".{model_path.name}.", suffix=".backup", dir=str(model_path.parent)
        )
        os.close(descriptor)
        backup_path = Path(backup_name)
        backup_path.unlink()
        os.replace(model_path, backup_path)

    try:
        os.replace(staged_model, model_path)
        try:
            # Two paths cannot be replaced as one filesystem transaction. Staging
            # both first keeps this window small; rollback prevents an orphan.
            os.replace(staged_manifest, manifest_path)
        except BaseException:
            model_path.unlink(missing_ok=True)
            if backup_path is not None:
                os.replace(backup_path, model_path)
            raise
    except BaseException:
        if backup_path is not None and backup_path.exists() and not model_path.exists():
            os.replace(backup_path, model_path)
        raise
    finally:
        if backup_path is not None:
            backup_path.unlink(missing_ok=True)


def save(
    obj: Any,
    path: PathLike,
    metadata: Optional[Dict[str, Any]] = None,
    backend: str = "auto",
    include_git: bool = True,
) -> Manifest:
    """Serialize an object and write a verified environment manifest beside it."""
    if metadata is not None:
        try:
            json.dumps(metadata, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise TypeError("metadata must be strictly JSON-serializable") from exc

    model_path = Path(path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    resolved = _resolve_save_backend(backend)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{model_path.name}.", suffix=".tmp", dir=str(model_path.parent)
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    staged_manifest: Optional[Path] = None
    try:
        _dump(obj, temporary_path, resolved)
        model_details, relevant = _model_details(obj)
        manifest = Manifest(
            artifact={
                "filename": model_path.name,
                "sha256": _sha256(temporary_path),
                "size_bytes": temporary_path.stat().st_size,
            },
            serialization={"backend": resolved},
            model=model_details,
            environment=capture_environment(include_git=include_git),
            relevant_packages=relevant,
            metadata=dict(metadata) if metadata else {},
        )
        manifest_path = _manifest_path(model_path)
        staged_manifest = _stage_text(manifest_path, manifest.to_json())
        _commit_artifact_pair(
            temporary_path,
            model_path,
            staged_manifest,
            manifest_path,
        )
        return manifest
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
        if staged_manifest is not None:
            staged_manifest.unlink(missing_ok=True)


def verify(path: PathLike, manifest: Optional[Manifest] = None) -> None:
    """Verify artifact size and SHA-256 without deserializing it."""
    model_path = Path(path)
    manifest = manifest or _read_manifest(model_path)
    if not model_path.is_file():
        raise ArtifactIntegrityError(f"artifact not found: {model_path}")
    expected_size = manifest.artifact["size_bytes"]
    actual_size = model_path.stat().st_size
    if actual_size != expected_size:
        raise ArtifactIntegrityError(
            f"size mismatch: expected {expected_size}, found {actual_size}"
        )
    expected_hash = manifest.artifact["sha256"]
    actual_hash = _sha256(model_path)
    if actual_hash != expected_hash:
        raise ArtifactIntegrityError(
            f"SHA-256 mismatch: expected {expected_hash}, found {actual_hash}"
        )


def load(
    path: PathLike,
    on_mismatch: str = "warn",
    backend: str = "auto",
    return_manifest: bool = True,
) -> Union[Any, Tuple[Any, Manifest]]:
    """Verify, compatibility-check, then load a model artifact."""
    if on_mismatch not in ("warn", "raise", "ignore"):
        raise ValueError("on_mismatch must be 'warn', 'raise', or 'ignore'")
    model_path = Path(path)
    manifest = _read_manifest(model_path)
    verify(model_path, manifest)
    resolved = _resolve_load_backend(backend, manifest)
    report = manifest.compare_to_current()
    if report and on_mismatch != "ignore":
        if on_mismatch == "raise":
            raise EnvironmentMismatchError(report)
        warnings.warn(str(report), EnvironmentMismatchWarning, stacklevel=2)
    obj = _load_object(model_path, resolved)
    return (obj, manifest) if return_manifest else obj


def inspect(path: PathLike) -> Manifest:
    """Read a manifest without loading or verifying the model."""
    return _read_manifest(Path(path))


def check(path: PathLike) -> MismatchReport:
    """Check both artifact integrity and runtime compatibility."""
    model_path = Path(path)
    manifest = _read_manifest(model_path)
    report = manifest.compare_to_current()
    try:
        verify(model_path, manifest)
    except ArtifactIntegrityError as exc:
        report.integrity_error = str(exc)
    return report


def _read_manifest(model_path: Path) -> Manifest:
    manifest_path = _manifest_path(model_path)
    if not manifest_path.is_file():
        raise ManifestError(f"no manifest found at {manifest_path}")
    try:
        return Manifest.from_json(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ManifestError(f"cannot read manifest at {manifest_path}: {exc}") from exc

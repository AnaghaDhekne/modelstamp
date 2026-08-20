"""Public persistence API with manifests and pre-deserialization verification."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import pickle
import tempfile
import threading
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Any, BinaryIO, Dict, Iterator, List, Optional, Tuple, Union

from ._environment import capture_environment
from ._manifest import Manifest, MismatchReport
from .exceptions import (
    ArtifactIntegrityError,
    EnvironmentMismatchError,
    EnvironmentMismatchWarning,
    ManifestError,
)

PathLike = Union[str, Path]
SigningKey = Union[bytes, bytearray, memoryview]
_THREAD_LOCKS: Dict[str, threading.RLock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()

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


def _load_object(stream: BinaryIO, backend: str) -> Any:
    if backend == "joblib":
        if _joblib is None:  # Defensive guard for direct internal calls.
            raise ImportError("joblib is not installed")
        return _joblib.load(stream)
    return pickle.load(stream)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _signing_key_bytes(signing_key: Optional[SigningKey]) -> Optional[bytes]:
    if signing_key is None:
        return None
    if not isinstance(signing_key, (bytes, bytearray, memoryview)):
        raise TypeError("signing_key must be bytes-like")
    key = bytes(signing_key)
    if not key:
        raise ValueError("signing_key must not be empty")
    return key


def _sign_manifest(manifest: Manifest, signing_key: bytes) -> None:
    manifest.signature = {
        "algorithm": "hmac-sha256",
        "digest": hmac.new(
            signing_key, manifest.signing_bytes(), hashlib.sha256
        ).hexdigest(),
    }


def _verify_manifest_signature(
    manifest: Manifest, signing_key: Optional[SigningKey]
) -> None:
    key = _signing_key_bytes(signing_key)
    if manifest.signature is None:
        if key is not None:
            raise ArtifactIntegrityError("manifest is not signed")
        return
    if key is None:
        raise ArtifactIntegrityError(
            "manifest is signed; provide signing_key to verify it"
        )
    expected = hmac.new(key, manifest.signing_bytes(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, manifest.signature["digest"]):
        raise ArtifactIntegrityError("manifest HMAC signature is invalid")


def _normalize_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, object]:
    if metadata is None:
        return {}
    if not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON object")
    try:
        encoded = json.dumps(metadata, allow_nan=False)
        normalized = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise TypeError("metadata must be strictly JSON-serializable") from exc
    return normalized


@contextmanager
def _artifact_lock(model_path: Path) -> Iterator[None]:
    """Serialize operations on one artifact across local processes."""
    identity = str(model_path.resolve(strict=False))
    with _THREAD_LOCKS_GUARD:
        thread_lock = _THREAD_LOCKS.setdefault(identity, threading.RLock())
    lock_name = (
        hashlib.sha256(identity.encode("utf-8", errors="surrogatepass")).hexdigest()
        + ".lock"
    )
    lock_root = Path(tempfile.gettempdir()) / "modelstamp-locks"
    lock_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    with thread_lock, (lock_root / lock_name).open("a+b") as stream:
        if os.name == "nt":  # pragma: no cover - exercised on Windows.
            import msvcrt

            stream.seek(0)
            if not stream.read(1):
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


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
    bundles = {
        "numpy": {"numpy"},
        "scipy": {"numpy", "scipy"},
        "pandas": {"numpy", "pandas"},
        "joblib": {"joblib"},
        "xgboost": {"numpy", "scipy", "xgboost"},
        "lightgbm": {"lightgbm", "numpy", "scipy"},
        "catboost": {"catboost", "numpy"},
        "statsmodels": {"numpy", "pandas", "scipy", "statsmodels"},
    }
    for module in modules:
        relevant.update(bundles.get(module, set()))
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
        # Two paths cannot be replaced as one filesystem transaction. Staging
        # both first keeps this window small; rollback prevents an orphan.
        os.replace(staged_manifest, manifest_path)
    except BaseException:
        model_path.unlink(missing_ok=True)
        if backup_path is not None:
            try:
                os.replace(backup_path, model_path)
                backup_path = None
            except BaseException as rollback_error:
                raise RuntimeError(
                    "artifact commit and rollback both failed; "
                    f"the previous model is preserved at {backup_path}"
                ) from rollback_error
        raise
    if backup_path is not None:
        backup_path.unlink(missing_ok=True)


def save(
    obj: Any,
    path: PathLike,
    metadata: Optional[Dict[str, Any]] = None,
    backend: str = "auto",
    include_git: bool = True,
    signing_key: Optional[SigningKey] = None,
) -> Manifest:
    """Serialize an object and write a verified environment manifest beside it."""
    normalized_metadata = _normalize_metadata(metadata)
    normalized_signing_key = _signing_key_bytes(signing_key)

    model_path = Path(path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    if model_path.exists() and not model_path.is_file():
        raise IsADirectoryError(f"artifact path is not a regular file: {model_path}")
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
        environment = capture_environment(include_git=include_git)
        installed_packages = dict(environment["packages"])
        relevant = [name for name in relevant if name in installed_packages]
        manifest = Manifest(
            artifact={
                "filename": model_path.name,
                "sha256": _sha256(temporary_path),
                "size_bytes": temporary_path.stat().st_size,
            },
            serialization={"backend": resolved},
            model=model_details,
            environment=environment,
            relevant_packages=relevant,
            metadata=normalized_metadata,
        )
        if normalized_signing_key is not None:
            _sign_manifest(manifest, normalized_signing_key)
        manifest_path = _manifest_path(model_path)
        staged_manifest = _stage_text(manifest_path, manifest.to_json())
        with _artifact_lock(model_path):
            if model_path.exists() and not model_path.is_file():
                raise IsADirectoryError(
                    f"artifact path is not a regular file: {model_path}"
                )
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


def _verify_stream(stream: BinaryIO, manifest: Manifest) -> None:
    expected_size = manifest.artifact["size_bytes"]
    actual_size = os.fstat(stream.fileno()).st_size
    if actual_size != expected_size:
        raise ArtifactIntegrityError(
            f"size mismatch: expected {expected_size}, found {actual_size}"
        )
    digest = hashlib.sha256()
    stream.seek(0)
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    actual_hash = digest.hexdigest()
    expected_hash = manifest.artifact["sha256"]
    if actual_hash != expected_hash:
        raise ArtifactIntegrityError(
            f"SHA-256 mismatch: expected {expected_hash}, found {actual_hash}"
        )
    stream.seek(0)


def verify(
    path: PathLike,
    signing_key: Optional[SigningKey] = None,
) -> None:
    """Verify artifact size and SHA-256 without deserializing it."""
    model_path = Path(path)
    with _artifact_lock(model_path):
        manifest = _read_manifest(model_path)
        _verify_manifest_signature(manifest, signing_key)
        if not model_path.is_file():
            raise ArtifactIntegrityError(f"artifact not found: {model_path}")
        with model_path.open("rb") as stream:
            _verify_stream(stream, manifest)


def load(
    path: PathLike,
    on_mismatch: str = "warn",
    backend: str = "auto",
    return_manifest: bool = True,
    signing_key: Optional[SigningKey] = None,
) -> Union[Any, Tuple[Any, Manifest]]:
    """Verify, compatibility-check, then load a model artifact."""
    if on_mismatch not in ("warn", "raise", "ignore"):
        raise ValueError("on_mismatch must be 'warn', 'raise', or 'ignore'")
    model_path = Path(path)
    with _artifact_lock(model_path):
        manifest = _read_manifest(model_path)
        _verify_manifest_signature(manifest, signing_key)
        resolved = _resolve_load_backend(backend, manifest)
        if not model_path.is_file():
            raise ArtifactIntegrityError(f"artifact not found: {model_path}")
        with model_path.open("rb") as stream:
            _verify_stream(stream, manifest)
            report = manifest.compare_to_current()
            if report and on_mismatch != "ignore":
                if on_mismatch == "raise":
                    raise EnvironmentMismatchError(report)
                warnings.warn(str(report), EnvironmentMismatchWarning, stacklevel=2)
            obj = _load_object(stream, resolved)
    return (obj, manifest) if return_manifest else obj


def inspect(path: PathLike) -> Manifest:
    """Read a manifest without loading or verifying the model."""
    model_path = Path(path)
    with _artifact_lock(model_path):
        return _read_manifest(model_path)


def check(path: PathLike, signing_key: Optional[SigningKey] = None) -> MismatchReport:
    """Check both artifact integrity and runtime compatibility."""
    model_path = Path(path)
    with _artifact_lock(model_path):
        manifest = _read_manifest(model_path)
        report = manifest.compare_to_current()
        try:
            _verify_manifest_signature(manifest, signing_key)
            if not model_path.is_file():
                raise ArtifactIntegrityError(f"artifact not found: {model_path}")
            with model_path.open("rb") as stream:
                _verify_stream(stream, manifest)
        except ArtifactIntegrityError as exc:
            report.integrity_error = str(exc)
        return report


def _read_manifest(model_path: Path) -> Manifest:
    manifest_path = _manifest_path(model_path)
    if not manifest_path.is_file():
        raise ManifestError(f"no manifest found at {manifest_path}")
    try:
        return Manifest.from_json(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise ManifestError(f"cannot read manifest at {manifest_path}: {exc}") from exc

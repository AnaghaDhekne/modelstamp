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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Dict, Iterator, List, Mapping, Optional, Tuple, Union

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


@dataclass
class _ThreadLockEntry:
    lock: threading.RLock
    users: int = 0


_THREAD_LOCKS: Dict[str, _ThreadLockEntry] = {}
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


def _validate_key_id(key_id: Optional[str]) -> Optional[str]:
    if key_id is None:
        return None
    if not isinstance(key_id, str) or not key_id.strip():
        raise TypeError("key_id must be a non-empty string")
    if key_id != key_id.strip():
        raise ValueError("key_id must not have leading or trailing whitespace")
    if len(key_id) > 128:
        raise ValueError("key_id must be at most 128 characters")
    return key_id


def _sign_manifest(
    manifest: Manifest, signing_key: bytes, key_id: Optional[str]
) -> None:
    signature = {"algorithm": "hmac-sha256"}
    if key_id is not None:
        signature["key_id"] = key_id
    manifest.signature = signature
    signature["digest"] = hmac.new(
        signing_key, manifest.signing_bytes(), hashlib.sha256
    ).hexdigest()


def _select_verification_key(
    manifest: Manifest,
    signing_key: Optional[SigningKey],
    signing_keys: Optional[Mapping[str, SigningKey]],
) -> Optional[bytes]:
    if signing_key is not None and signing_keys is not None:
        raise ValueError("provide signing_key or signing_keys, not both")
    if signing_keys is None:
        return _signing_key_bytes(signing_key)
    if not isinstance(signing_keys, Mapping):
        raise TypeError("signing_keys must be a mapping of key IDs to keys")
    if manifest.signature is None:
        return b"registry-requires-a-signed-manifest"
    key_id = manifest.signature.get("key_id")
    if key_id is None:
        raise ArtifactIntegrityError(
            "signed manifest has no key_id; provide signing_key directly"
        )
    if key_id not in signing_keys:
        raise ArtifactIntegrityError(f"no signing key registered for key_id {key_id!r}")
    return _signing_key_bytes(signing_keys[key_id])


def _verify_manifest_signature(
    manifest: Manifest,
    signing_key: Optional[SigningKey],
    signing_keys: Optional[Mapping[str, SigningKey]],
) -> None:
    key = _select_verification_key(manifest, signing_key, signing_keys)
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
        entry = _THREAD_LOCKS.get(identity)
        if entry is None:
            entry = _ThreadLockEntry(threading.RLock())
            _THREAD_LOCKS[identity] = entry
        entry.users += 1
    lock_name = (
        hashlib.sha256(identity.encode("utf-8", errors="surrogatepass")).hexdigest()
        + ".lock"
    )
    lock_root = Path(tempfile.gettempdir()) / "modelstamp-locks"
    try:
        lock_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        with entry.lock, (lock_root / lock_name).open("a+b") as stream:
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
    finally:
        with _THREAD_LOCKS_GUARD:
            entry.users -= 1
            if entry.users == 0 and _THREAD_LOCKS.get(identity) is entry:
                del _THREAD_LOCKS[identity]


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
    key_id: Optional[str] = None,
) -> Manifest:
    """Serialize an object and write its environment manifest atomically.

    Args:
        obj: Python object to persist.
        path: Destination artifact path.
        metadata: Optional JSON-compatible model metadata.
        backend: ``"auto"``, ``"pickle"``, or ``"joblib"``.
        include_git: Record the current Git commit and dirty state when available.
        signing_key: Optional bytes-like HMAC secret.
        key_id: Optional identifier stored and authenticated with the signature.

    Returns:
        The normalized manifest written beside the artifact.

    Raises:
        TypeError: Metadata, signing key, or key identifier has an invalid type.
        ValueError: An option is invalid or ``key_id`` lacks a signing key.
    """
    normalized_metadata = _normalize_metadata(metadata)
    normalized_signing_key = _signing_key_bytes(signing_key)
    normalized_key_id = _validate_key_id(key_id)
    if normalized_key_id is not None and normalized_signing_key is None:
        raise ValueError("key_id requires signing_key")

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
            _sign_manifest(manifest, normalized_signing_key, normalized_key_id)
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
    signing_keys: Optional[Mapping[str, SigningKey]] = None,
) -> None:
    """Verify an artifact without deserializing it.

    Args:
        path: Artifact whose sidecar manifest should be verified.
        signing_key: Direct HMAC key for legacy or single-key deployments.
        signing_keys: Registry mapping authenticated key IDs to HMAC keys.

    Raises:
        ArtifactIntegrityError: The artifact or signature does not match.
        ManifestError: The sidecar is missing or malformed.
    """
    model_path = Path(path)
    with _artifact_lock(model_path):
        manifest = _read_manifest(model_path)
        _verify_manifest_signature(manifest, signing_key, signing_keys)
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
    signing_keys: Optional[Mapping[str, SigningKey]] = None,
) -> Union[Any, Tuple[Any, Manifest]]:
    """Verify, compatibility-check, then deserialize an artifact.

    Args:
        path: Artifact to load.
        on_mismatch: ``"warn"``, ``"raise"``, or ``"ignore"`` for runtime
            compatibility differences.
        backend: ``"auto"``, ``"pickle"``, or ``"joblib"``.
        return_manifest: Return ``(object, manifest)`` instead of only the object.
        signing_key: Direct HMAC key for legacy or single-key deployments.
        signing_keys: Registry mapping authenticated key IDs to HMAC keys.

    Returns:
        The deserialized object, optionally paired with its manifest.

    Raises:
        ArtifactIntegrityError: Artifact or signature verification fails.
        EnvironmentMismatchError: Runtime differences exist under ``"raise"``.
        ManifestError: The sidecar is missing, malformed, or incompatible.
    """
    if on_mismatch not in ("warn", "raise", "ignore"):
        raise ValueError("on_mismatch must be 'warn', 'raise', or 'ignore'")
    model_path = Path(path)
    with _artifact_lock(model_path):
        manifest = _read_manifest(model_path)
        _verify_manifest_signature(manifest, signing_key, signing_keys)
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
    """Read a sidecar manifest without verifying or deserializing the artifact.

    Args:
        path: Artifact path used to locate the sidecar.

    Returns:
        The validated manifest.

    Raises:
        ManifestError: The sidecar is missing or malformed.
    """
    model_path = Path(path)
    with _artifact_lock(model_path):
        return _read_manifest(model_path)


def check(
    path: PathLike,
    signing_key: Optional[SigningKey] = None,
    signing_keys: Optional[Mapping[str, SigningKey]] = None,
) -> MismatchReport:
    """Check integrity and runtime compatibility without deserializing.

    Args:
        path: Artifact to check.
        signing_key: Direct HMAC key for legacy or single-key deployments.
        signing_keys: Registry mapping authenticated key IDs to HMAC keys.

    Returns:
        A report whose truth value indicates a mismatch.

    Raises:
        ManifestError: The sidecar is missing or malformed.
    """
    model_path = Path(path)
    with _artifact_lock(model_path):
        manifest = _read_manifest(model_path)
        report = MismatchReport()
        try:
            # Authenticate before using manifest-controlled environment data.
            _verify_manifest_signature(manifest, signing_key, signing_keys)
            report = manifest.compare_to_current()
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

from __future__ import annotations

import json
import pickle
import warnings
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Thread

import pytest

import modelstamp as ms
from modelstamp import core
from modelstamp.core import _model_details
from modelstamp.exceptions import (
    ArtifactIntegrityError,
    EnvironmentMismatchError,
    EnvironmentMismatchWarning,
    ManifestError,
)


class DummyModel:
    def __init__(self, weights):
        self.weights = list(weights)

    def predict(self, rows):
        return [sum(w * x for w, x in zip(self.weights, row)) for row in rows]

    def __eq__(self, other):
        return isinstance(other, DummyModel) and other.weights == self.weights


@pytest.fixture
def model():
    return DummyModel([1.0, 2.0, 3.0])


def test_pickle_round_trip_and_manifest(tmp_path, model):
    path = tmp_path / "model.pkl"
    manifest = ms.save(
        model,
        path,
        backend="pickle",
        metadata={"cv_accuracy": 0.94},
        include_git=False,
    )
    loaded, restored_manifest = ms.load(path)
    assert loaded == model
    assert loaded.predict([[1, 1, 1]]) == [6.0]
    assert restored_manifest.metadata == {"cv_accuracy": 0.94}
    assert manifest.serialization["backend"] == "pickle"
    assert manifest.artifact["size_bytes"] == path.stat().st_size
    assert len(manifest.artifact["sha256"]) == 64
    assert manifest.model["class"] == "DummyModel"


def test_bare_object_return(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle")
    assert ms.load(path, return_manifest=False) == model


def test_nested_output_directory(tmp_path, model):
    path = tmp_path / "nested" / "models" / "model.pkl"
    ms.save(model, path, backend="pickle")
    assert path.is_file()
    assert path.with_name("model.pkl.manifest.json").is_file()


def test_existing_directory_is_rejected_without_modification(tmp_path, model):
    path = tmp_path / "models"
    path.mkdir()
    important = path / "important.txt"
    important.write_text("keep", encoding="utf-8")

    with pytest.raises(IsADirectoryError, match="not a regular file"):
        ms.save(model, path, backend="pickle", include_git=False)

    assert path.is_dir()
    assert important.read_text(encoding="utf-8") == "keep"


def test_manifest_commit_failure_does_not_orphan_new_artifact(
    tmp_path, model, monkeypatch
):
    path = tmp_path / "model.pkl"
    manifest_path = path.with_name("model.pkl.manifest.json")
    real_replace = core.os.replace

    def fail_manifest_replace(source, destination):
        if Path(destination) == manifest_path:
            raise OSError("simulated manifest failure")
        real_replace(source, destination)

    monkeypatch.setattr(core.os, "replace", fail_manifest_replace)
    with pytest.raises(OSError, match="simulated manifest failure"):
        ms.save(model, path, backend="pickle", include_git=False)
    assert not path.exists()
    assert not manifest_path.exists()


def test_failed_overwrite_restores_existing_artifact(tmp_path, model, monkeypatch):
    path = tmp_path / "model.pkl"
    manifest_path = path.with_name("model.pkl.manifest.json")
    ms.save(model, path, backend="pickle", include_git=False)
    original_model = path.read_bytes()
    original_manifest = manifest_path.read_bytes()
    real_replace = core.os.replace

    def fail_manifest_replace(source, destination):
        if Path(destination) == manifest_path:
            raise OSError("simulated manifest failure")
        real_replace(source, destination)

    monkeypatch.setattr(core.os, "replace", fail_manifest_replace)
    with pytest.raises(OSError, match="simulated manifest failure"):
        ms.save(DummyModel([9.0]), path, backend="pickle", include_git=False)
    assert path.read_bytes() == original_model
    assert manifest_path.read_bytes() == original_manifest


def test_failed_rollback_preserves_backup(tmp_path, model, monkeypatch):
    path = tmp_path / "model.pkl"
    manifest_path = path.with_name("model.pkl.manifest.json")
    ms.save(model, path, backend="pickle", include_git=False)
    real_replace = core.os.replace

    def fail_commit_and_rollback(source, destination):
        source = Path(source)
        destination = Path(destination)
        if destination == manifest_path:
            raise OSError("simulated manifest failure")
        if source.suffix == ".backup" and destination == path:
            raise OSError("simulated rollback failure")
        real_replace(source, destination)

    monkeypatch.setattr(core.os, "replace", fail_commit_and_rollback)
    with pytest.raises(RuntimeError, match="previous model is preserved"):
        ms.save(DummyModel([9.0]), path, backend="pickle", include_git=False)

    backups = list(tmp_path.glob(".model.pkl.*.backup"))
    assert len(backups) == 1
    assert pickle.loads(backups[0].read_bytes()) == model


def test_concurrent_saves_leave_a_valid_pair(tmp_path, monkeypatch):
    path = tmp_path / "model.pkl"
    first_dump_started = Event()
    allow_first_dump = Event()
    real_dump = core._dump

    def coordinated_dump(obj, destination, backend):
        if obj == {"writer": "first"}:
            first_dump_started.set()
            assert allow_first_dump.wait(5)
        real_dump(obj, destination, backend)

    monkeypatch.setattr(core, "_dump", coordinated_dump)
    errors = []

    def save_value(value):
        try:
            ms.save(value, path, backend="pickle", include_git=False)
        except Exception as exc:  # pragma: no cover - assertion reports details.
            errors.append(exc)

    first = Thread(target=save_value, args=({"writer": "first"},))
    second = Thread(target=save_value, args=({"writer": "second"},))
    first.start()
    assert first_dump_started.wait(5)
    second.start()
    allow_first_dump.set()
    first.join(5)
    second.join(5)

    assert not errors
    assert not first.is_alive()
    assert not second.is_alive()
    ms.verify(path)
    assert ms.load(path, return_manifest=False) in (
        {"writer": "first"},
        {"writer": "second"},
    )


def test_thread_locks_are_released_after_each_artifact(tmp_path):
    for index in range(100):
        path = tmp_path / f"model-{index}.pkl"
        ms.save({"index": index}, path, backend="pickle", include_git=False)
        ms.verify(path)
    assert core._THREAD_LOCKS == {}


def test_thread_lock_entry_is_released_when_lock_setup_fails(tmp_path, monkeypatch):
    path = tmp_path / "model.pkl"
    ms.save({"value": 1}, path, backend="pickle", include_git=False)

    def fail_mkdir(*args, **kwargs):
        raise PermissionError("lock directory unavailable")

    monkeypatch.setattr(core.Path, "mkdir", fail_mkdir)
    with pytest.raises(PermissionError, match="lock directory unavailable"):
        ms.verify(path)
    assert core._THREAD_LOCKS == {}


def test_check_and_verify_clean_artifact(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle", include_git=False)
    ms.verify(path)
    report = ms.check(path)
    assert not report
    assert "match" in str(report)


def test_tampered_artifact_is_rejected_before_load(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle")
    path.write_bytes(path.read_bytes() + b"tampered")
    with pytest.raises(ArtifactIntegrityError):
        ms.load(path)
    report = ms.check(path)
    assert report
    assert report.integrity_error is not None


def test_same_size_tampering_is_detected_by_hash(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle")
    content = bytearray(path.read_bytes())
    content[-1] ^= 1
    path.write_bytes(content)
    with pytest.raises(ArtifactIntegrityError, match="SHA-256"):
        ms.verify(path)


def test_load_uses_the_verified_open_file(tmp_path, model, monkeypatch):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle", include_git=False)
    replacement = pickle.dumps(DummyModel([9.0]), protocol=pickle.HIGHEST_PROTOCOL)
    replacement_path = tmp_path / "replacement.pkl"
    replacement_path.write_bytes(replacement)
    real_load = core._load_object

    def replace_path_then_load(stream, backend):
        try:
            core.os.replace(replacement_path, path)
        except PermissionError:
            # Windows prevents replacing a file while modelstamp holds it open.
            pass
        return real_load(stream, backend)

    monkeypatch.setattr(core, "_load_object", replace_path_then_load)
    assert ms.load(path, on_mismatch="ignore", return_manifest=False) == model


def test_backend_mismatch_is_rejected(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle")
    with pytest.raises(ManifestError, match="differs from recorded"):
        ms.load(path, backend="joblib")


def test_non_json_metadata_is_rejected_before_writing(tmp_path, model):
    path = tmp_path / "model.pkl"
    with pytest.raises(TypeError):
        ms.save(model, path, metadata={"bad": {1, 2}}, backend="pickle")
    assert not path.exists()


def test_non_finite_metadata_is_rejected(tmp_path, model):
    with pytest.raises(TypeError):
        ms.save(model, tmp_path / "model.pkl", metadata={"score": float("nan")})


def test_metadata_is_normalized_to_its_persisted_json_shape(tmp_path, model):
    path = tmp_path / "model.pkl"
    manifest = ms.save(
        model,
        path,
        metadata={"folds": (1, 2)},
        backend="pickle",
        include_git=False,
    )
    assert manifest.metadata == {"folds": [1, 2]}
    assert ms.inspect(path).metadata == manifest.metadata


def test_metadata_must_be_a_json_object(tmp_path, model):
    with pytest.raises(TypeError, match="JSON object"):
        ms.save(model, tmp_path / "model.pkl", metadata=["not", "an", "object"])


def test_missing_and_malformed_manifests(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle")
    sidecar = path.with_name("model.pkl.manifest.json")
    sidecar.unlink()
    with pytest.raises(ManifestError, match="no manifest"):
        ms.load(path)
    sidecar.write_text("{bad json", encoding="utf-8")
    with pytest.raises(ManifestError, match="invalid JSON"):
        ms.inspect(path)


def test_non_utf8_manifest_is_reported_as_manifest_error(tmp_path):
    path = tmp_path / "model.pkl"
    path.with_name("model.pkl.manifest.json").write_bytes(b"\xff\xfe")
    with pytest.raises(ManifestError, match="cannot read manifest"):
        ms.inspect(path)


def test_inspect_uses_the_artifact_lock(tmp_path, model, monkeypatch):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle", include_git=False)
    locked_paths = []

    @contextmanager
    def recording_lock(model_path):
        locked_paths.append(model_path)
        yield

    monkeypatch.setattr(core, "_artifact_lock", recording_lock)
    ms.inspect(path)
    assert locked_paths == [path]


def test_unknown_schema_version_is_rejected(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle")
    sidecar = path.with_name("model.pkl.manifest.json")
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["schema_version"] = 999
    sidecar.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ManifestError, match="unsupported schema"):
        ms.inspect(path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", True, "unsupported schema"),
        ("artifact.sha256", "not-a-digest", "64 lowercase"),
        ("artifact.size_bytes", -1, "non-negative integer"),
        ("artifact.size_bytes", True, "non-negative integer"),
    ],
)
def test_invalid_manifest_fields_are_rejected(tmp_path, model, field, value, message):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle", include_git=False)
    sidecar = path.with_name("model.pkl.manifest.json")
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    target = data
    parts = field.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    sidecar.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ManifestError, match=message):
        ms.inspect(path)


def test_package_change_is_not_public_api():
    assert "PackageChange" not in ms.__all__
    assert not hasattr(ms, "PackageChange")


def test_malformed_steps_attribute_does_not_break_save(tmp_path):
    model = DummyModel([1.0])
    model.steps = ["not-a-pipeline-step"]
    manifest = ms.save(model, tmp_path / "model.pkl", backend="pickle")
    assert "components" not in manifest.model


@pytest.mark.parametrize(
    ("module", "expected"),
    [
        ("scipy.sparse", {"numpy", "scipy"}),
        ("joblib.memory", {"joblib"}),
        ("statsmodels.api", {"numpy", "pandas", "scipy", "statsmodels"}),
        ("xgboost.sklearn", {"numpy", "scipy", "xgboost"}),
        ("lightgbm.sklearn", {"lightgbm", "numpy", "scikit-learn", "scipy"}),
    ],
)
def test_model_details_include_dependency_bundle(module, expected):
    example_type = type("Example", (), {"__module__": module})
    _, relevant = _model_details(example_type())
    assert set(relevant) == expected


def test_joblib_round_trip_when_installed(tmp_path, model):
    pytest.importorskip("joblib")
    path = tmp_path / "model.joblib"
    manifest = ms.save(model, path, backend="joblib", include_git=False)
    assert manifest.serialization["backend"] == "joblib"
    assert ms.load(path, return_manifest=False) == model


def test_environment_policy_warn_raise_and_ignore(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle")
    sidecar = path.with_name("model.pkl.manifest.json")
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["environment"]["python_version"] = "0.0.0"
    sidecar.write_text(json.dumps(data), encoding="utf-8")
    with pytest.warns(EnvironmentMismatchWarning):
        ms.load(path)
    with pytest.raises(EnvironmentMismatchError):
        ms.load(path, on_mismatch="raise")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert ms.load(path, on_mismatch="ignore", return_manifest=False) == model


def test_invalid_policy_is_rejected(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle")
    with pytest.raises(ValueError):
        ms.load(path, on_mismatch="explode")


def test_signed_manifest_round_trip(tmp_path, model):
    path = tmp_path / "model.pkl"
    key = b"test-only-secret-key"
    manifest = ms.save(
        model, path, backend="pickle", include_git=False, signing_key=key
    )
    assert manifest.signature["algorithm"] == "hmac-sha256"
    ms.verify(path, signing_key=key)
    assert ms.load(path, signing_key=key, return_manifest=False) == model
    assert not ms.check(path, signing_key=key)


def test_key_id_selects_rotated_signing_key(tmp_path, model):
    path = tmp_path / "model.pkl"
    keys = {"2026-q2": b"old-key", "2026-q3": b"current-key"}
    manifest = ms.save(
        model,
        path,
        backend="pickle",
        include_git=False,
        signing_key=keys["2026-q3"],
        key_id="2026-q3",
    )
    assert manifest.signature["key_id"] == "2026-q3"
    ms.verify(path, signing_keys=keys)
    assert ms.load(path, signing_keys=keys, return_manifest=False) == model


def test_key_id_is_authenticated(tmp_path, model):
    path = tmp_path / "model.pkl"
    keys = {"old": b"old-key", "current": b"current-key"}
    ms.save(
        model,
        path,
        backend="pickle",
        signing_key=keys["current"],
        key_id="current",
    )
    sidecar = path.with_name("model.pkl.manifest.json")
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["signature"]["key_id"] = "old"
    sidecar.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="signature is invalid"):
        ms.verify(path, signing_keys=keys)


def test_unknown_rotated_key_is_rejected(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(
        model,
        path,
        backend="pickle",
        signing_key=b"current-key",
        key_id="current",
    )
    with pytest.raises(ArtifactIntegrityError, match="no signing key registered"):
        ms.verify(path, signing_keys={"old": b"old-key"})


def test_legacy_signature_uses_direct_key(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle", signing_key=b"legacy-key")
    ms.verify(path, signing_key=b"legacy-key")
    with pytest.raises(ArtifactIntegrityError, match="has no key_id"):
        ms.verify(path, signing_keys={"legacy": b"legacy-key"})


def test_signed_manifest_requires_the_correct_key(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(path=path, obj=model, backend="pickle", signing_key=b"correct-key")
    with pytest.raises(ArtifactIntegrityError, match="provide signing_key"):
        ms.verify(path)
    with pytest.raises(ArtifactIntegrityError, match="signature is invalid"):
        ms.load(path, signing_key=b"wrong-key")
    report = ms.check(path, signing_key=b"wrong-key")
    assert report.integrity_error == "manifest HMAC signature is invalid"


def test_check_authenticates_before_comparing_environment(tmp_path, model, monkeypatch):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle", signing_key=b"correct-key")

    def fail_if_called(self):
        raise AssertionError("untrusted environment data was compared")

    monkeypatch.setattr(core.Manifest, "compare_to_current", fail_if_called)
    report = ms.check(path, signing_key=b"wrong-key")
    assert report.integrity_error == "manifest HMAC signature is invalid"


def test_manifest_tampering_invalidates_signature(tmp_path, model):
    path = tmp_path / "model.pkl"
    key = b"correct-key"
    ms.save(model, path, backend="pickle", signing_key=key)
    sidecar = path.with_name("model.pkl.manifest.json")
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["metadata"]["untrusted"] = True
    sidecar.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="signature is invalid"):
        ms.verify(path, signing_key=key)


def test_providing_a_key_rejects_an_unsigned_manifest(tmp_path, model):
    path = tmp_path / "model.pkl"
    ms.save(model, path, backend="pickle")
    with pytest.raises(ArtifactIntegrityError, match="not signed"):
        ms.verify(path, signing_key=b"expected-signing-key")


@pytest.mark.parametrize("key", [b"", "text-key"])
def test_invalid_signing_keys_are_rejected(tmp_path, model, key):
    expected = ValueError if key == b"" else TypeError
    with pytest.raises(expected):
        ms.save(model, tmp_path / "model.pkl", backend="pickle", signing_key=key)


def test_invalid_key_ids_and_key_arguments_are_rejected(tmp_path, model):
    path = tmp_path / "model.pkl"
    with pytest.raises(ValueError, match="requires signing_key"):
        ms.save(model, path, backend="pickle", key_id="current")
    with pytest.raises(TypeError, match="non-empty string"):
        ms.save(model, path, backend="pickle", signing_key=b"key", key_id="")
    with pytest.raises(ValueError, match="whitespace"):
        ms.save(model, path, backend="pickle", signing_key=b"key", key_id=" current ")

    ms.save(
        model,
        path,
        backend="pickle",
        signing_key=b"key",
        key_id="current",
    )
    with pytest.raises(ValueError, match="not both"):
        ms.verify(
            path,
            signing_key=b"key",
            signing_keys={"current": b"key"},
        )

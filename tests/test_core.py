from __future__ import annotations

import json
import pickle
import warnings
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
        core.os.replace(replacement_path, path)
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

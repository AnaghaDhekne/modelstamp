"""Control tests for complete artifact-and-manifest replacement scenarios."""

import json
import shutil

import pytest

import modelstamp as ms
from modelstamp import ArtifactIntegrityError


def _sidecar(path):
    return path.with_name(path.name + ".manifest.json")


def _replace_pair(source, destination):
    shutil.copyfile(source, destination)
    shutil.copyfile(_sidecar(source), _sidecar(destination))


def test_unsigned_replacement_pair_is_not_authenticated(tmp_path):
    approved = tmp_path / "approved.pkl"
    replacement = tmp_path / "replacement.pkl"
    ms.save({"model": "approved"}, approved, include_git=False)
    ms.save({"model": "replacement"}, replacement, include_git=False)
    _replace_pair(replacement, approved)
    ms.verify(approved)
    assert ms.load(approved, return_manifest=False) == {"model": "replacement"}


def test_editing_unsigned_manifest_hash_is_detected(tmp_path):
    artifact = tmp_path / "model.pkl"
    ms.save({"model": "approved"}, artifact, include_git=False)
    sidecar = _sidecar(artifact)
    manifest = json.loads(sidecar.read_text(encoding="utf-8"))
    manifest["artifact"]["sha256"] = "0" * 64
    sidecar.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ArtifactIntegrityError, match="SHA-256 mismatch"):
        ms.verify(artifact)


def test_unsigned_manifest_identity_is_not_authenticated(tmp_path):
    artifact = tmp_path / "model.pkl"
    ms.save({"model": "approved"}, artifact, include_git=False)
    sidecar = _sidecar(artifact)
    manifest = json.loads(sidecar.read_text(encoding="utf-8"))
    manifest["model"]["class"] = "UntrustedIdentityClaim"
    sidecar.write_text(json.dumps(manifest), encoding="utf-8")
    ms.verify(artifact)
    assert ms.inspect(artifact).model["class"] == "UntrustedIdentityClaim"


def test_unsigned_replacement_is_rejected_when_hmac_is_required(tmp_path):
    approved = tmp_path / "approved.pkl"
    replacement = tmp_path / "replacement.pkl"
    key = b"trusted-key"
    ms.save({"model": "approved"}, approved, include_git=False, signing_key=key)
    ms.save({"model": "replacement"}, replacement, include_git=False)
    _replace_pair(replacement, approved)
    with pytest.raises(ArtifactIntegrityError, match="manifest is not signed"):
        ms.verify(approved, signing_key=key)


def test_replacement_signed_with_untrusted_key_is_rejected(tmp_path):
    approved = tmp_path / "approved.pkl"
    replacement = tmp_path / "replacement.pkl"
    trusted_key = b"trusted-key"
    ms.save(
        {"model": "approved"}, approved, include_git=False, signing_key=trusted_key
    )
    ms.save(
        {"model": "replacement"},
        replacement,
        include_git=False,
        signing_key=b"untrusted-key",
    )
    _replace_pair(replacement, approved)
    with pytest.raises(ArtifactIntegrityError, match="signature is invalid"):
        ms.verify(approved, signing_key=trusted_key)


def test_shared_key_holder_can_create_an_accepted_replacement(tmp_path):
    approved = tmp_path / "approved.pkl"
    replacement = tmp_path / "replacement.pkl"
    shared_key = b"shared-key"
    ms.save(
        {"model": "approved"}, approved, include_git=False, signing_key=shared_key
    )
    ms.save(
        {"model": "replacement"},
        replacement,
        include_git=False,
        signing_key=shared_key,
    )
    _replace_pair(replacement, approved)
    ms.verify(approved, signing_key=shared_key)
    assert ms.load(
        approved, signing_key=shared_key, return_manifest=False
    ) == {"model": "replacement"}


def test_older_valid_signed_pair_can_be_replayed(tmp_path):
    current = tmp_path / "current.pkl"
    old = tmp_path / "old.pkl"
    shared_key = b"shared-key"
    ms.save(
        {"model": "current", "version": 2},
        current,
        include_git=False,
        signing_key=shared_key,
    )
    ms.save(
        {"model": "old", "version": 1},
        old,
        include_git=False,
        signing_key=shared_key,
    )
    _replace_pair(old, current)
    ms.verify(current, signing_key=shared_key)
    assert ms.load(current, signing_key=shared_key, return_manifest=False)[
        "version"
    ] == 1

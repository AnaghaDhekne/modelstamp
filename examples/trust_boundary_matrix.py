"""Exercise Modelstamp's artifact-integrity and HMAC trust boundaries.

Run from the repository root with:

    PYTHONPATH=src python examples/trust_boundary_matrix.py

The examples intentionally use pickle and simple dictionaries so the results
test Modelstamp's controls without requiring a machine-learning framework.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import modelstamp as ms
from modelstamp import ArtifactIntegrityError


@dataclass
class Result:
    scenario: str
    expected: str
    observed: str
    passed: bool


def _sidecar(path: Path) -> Path:
    return path.with_name(path.name + ".manifest.json")


def _expect_rejection(action: Callable[[], None], message: str) -> str:
    try:
        action()
    except ArtifactIntegrityError as exc:
        if message not in str(exc):
            raise AssertionError(f"unexpected rejection: {exc}") from exc
        return f"REJECTED — {exc}"
    raise AssertionError("verification unexpectedly succeeded")


def _replace_pair(source: Path, destination: Path) -> None:
    shutil.copyfile(source, destination)
    shutil.copyfile(_sidecar(source), _sidecar(destination))


def run_matrix(root: Path) -> list[Result]:
    results: list[Result] = []

    artifact = root / "01-artifact-tampered.pkl"
    ms.save({"model": "approved", "version": 1}, artifact, include_git=False)
    original = artifact.read_bytes()
    artifact.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
    observed = _expect_rejection(lambda: ms.verify(artifact), "SHA-256 mismatch")
    results.append(
        Result("artifact changed; manifest unchanged", "reject", observed, True)
    )

    approved = root / "02-approved-unsigned.pkl"
    replacement = root / "02-replacement-unsigned.pkl"
    ms.save({"model": "approved", "version": 1}, approved, include_git=False)
    ms.save(
        {"model": "attacker-replacement", "version": 2},
        replacement,
        include_git=False,
    )
    _replace_pair(replacement, approved)
    ms.verify(approved)
    loaded = ms.load(approved, return_manifest=False)
    observed = f"ACCEPTED — loaded model={loaded['model']!r}"
    results.append(
        Result(
            "artifact and unsigned manifest replaced together",
            "accept",
            observed,
            True,
        )
    )

    # Editing the unsigned manifest's artifact digest while leaving the artifact
    # unchanged is detected because the recalculated digest no longer matches.
    hash_claim = root / "03-manifest-hash-edited.pkl"
    ms.save({"model": "approved", "version": 1}, hash_claim, include_git=False)
    manifest_data = json.loads(_sidecar(hash_claim).read_text(encoding="utf-8"))
    manifest_data["artifact"]["sha256"] = "0" * 64
    _sidecar(hash_claim).write_text(
        json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    observed = _expect_rejection(lambda: ms.verify(hash_claim), "SHA-256 mismatch")
    results.append(
        Result(
            "unsigned manifest hash edited; artifact unchanged",
            "reject",
            observed,
            True,
        )
    )

    # In an unsigned manifest, descriptive model identity fields are not
    # authenticated. Editing one does not affect the artifact checksum.
    identity_claim = root / "04-manifest-identity-edited.pkl"
    ms.save({"model": "approved", "version": 1}, identity_claim, include_git=False)
    manifest_data = json.loads(_sidecar(identity_claim).read_text(encoding="utf-8"))
    manifest_data["model"]["class"] = "UntrustedIdentityClaim"
    _sidecar(identity_claim).write_text(
        json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    ms.verify(identity_claim)
    observed = "ACCEPTED — unsigned identity metadata is not authenticated"
    results.append(
        Result(
            "unsigned manifest identity edited; artifact unchanged",
            "accept",
            observed,
            True,
        )
    )

    signed = root / "05-approved-signed.pkl"
    unsigned = root / "05-replacement-unsigned.pkl"
    trusted_key = b"trusted-receiver-key"
    ms.save(
        {"model": "approved", "version": 1},
        signed,
        include_git=False,
        signing_key=trusted_key,
    )
    ms.save(
        {"model": "attacker-replacement", "version": 2},
        unsigned,
        include_git=False,
    )
    _replace_pair(unsigned, signed)
    observed = _expect_rejection(
        lambda: ms.verify(signed, signing_key=trusted_key), "manifest is not signed"
    )
    results.append(
        Result("signed pair replaced by unsigned pair", "reject", observed, True)
    )

    trusted = root / "06-approved-trusted.pkl"
    untrusted = root / "06-replacement-untrusted.pkl"
    ms.save(
        {"model": "approved", "version": 1},
        trusted,
        include_git=False,
        signing_key=trusted_key,
    )
    ms.save(
        {"model": "attacker-replacement", "version": 2},
        untrusted,
        include_git=False,
        signing_key=b"attacker-key",
    )
    _replace_pair(untrusted, trusted)
    observed = _expect_rejection(
        lambda: ms.verify(trusted, signing_key=trusted_key), "signature is invalid"
    )
    results.append(
        Result("replacement pair signed with untrusted key", "reject", observed, True)
    )

    shared = root / "07-approved-shared-key.pkl"
    forged = root / "07-replacement-shared-key.pkl"
    ms.save(
        {"model": "approved", "version": 1},
        shared,
        include_git=False,
        signing_key=trusted_key,
    )
    ms.save(
        {"model": "key-holder-replacement", "version": 2},
        forged,
        include_git=False,
        signing_key=trusted_key,
    )
    _replace_pair(forged, shared)
    ms.verify(shared, signing_key=trusted_key)
    loaded = ms.load(shared, signing_key=trusted_key, return_manifest=False)
    observed = f"ACCEPTED — loaded model={loaded['model']!r}"
    results.append(
        Result("replacement pair signed by shared-key holder", "accept", observed, True)
    )

    # A previously valid signed pair can be replayed because HMAC authenticates
    # its contents but does not enforce freshness or monotonic model versions.
    current = root / "08-current-signed.pkl"
    old = root / "08-old-signed.pkl"
    ms.save(
        {"model": "current", "version": 2},
        current,
        include_git=False,
        signing_key=trusted_key,
    )
    ms.save(
        {"model": "previously-valid", "version": 1},
        old,
        include_git=False,
        signing_key=trusted_key,
    )
    _replace_pair(old, current)
    ms.verify(current, signing_key=trusted_key)
    loaded = ms.load(current, signing_key=trusted_key, return_manifest=False)
    observed = f"ACCEPTED — loaded version={loaded['version']}"
    results.append(Result("older valid signed pair replayed", "accept", observed, True))

    return results


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="modelstamp-trust-") as directory:
        results = run_matrix(Path(directory))

    print("Modelstamp trust-boundary validation")
    print("=" * 40)
    for index, result in enumerate(results, start=1):
        status = "PASS" if result.passed else "FAIL"
        print(f"{index}. [{status}] {result.scenario}")
        print(f"   expected: {result.expected}")
        print(f"   observed: {result.observed}")


if __name__ == "__main__":
    main()

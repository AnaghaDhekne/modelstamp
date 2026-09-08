# Security boundary

Pickle and joblib can execute arbitrary code while loading. A valid checksum or
HMAC does not make an untrusted serialized object safe; it only establishes
that the object matches a manifest or was authenticated by a holder of the
configured secret.

HMAC uses one shared secret for both signing and verification. A verifier with
the HMAC key can also forge manifests, so the key is not safe to publish or
give to verification-only third parties. `modelstamp` does not currently offer
asymmetric signatures such as Ed25519 or Sigstore.

- Load artifacts only from trusted producers.
- Keep HMAC keys outside source control, artifact storage, and public clients.
- Rotate keys using an authenticated `key_id` and a verification registry.
- Use `skops.io` or ONNX when their reduced execution surface fits the model.
- Use `inspect()`, `check()`, and `verify()` when deserialization is unnecessary.

## Resilience-test boundary

The test suite exercises simultaneous saves across independent processes,
verification and loading while another process replaces an artifact pair,
arbitrary manifest bytes, and manifest filenames that attempt directory
traversal. These tests run on Linux, Windows, and macOS through the supported
CI matrix.

They establish fail-closed parsing and cooperative local-process locking under
the tested conditions. They do not claim protection from a privileged attacker
who can ignore locks, replace files or keys, or alter the running process. Use
filesystem permissions and an external trust system for those boundaries.

Report suspected vulnerabilities privately according to the repository's
[security policy](https://github.com/AnaghaDhekne/modelstamp/security/policy).

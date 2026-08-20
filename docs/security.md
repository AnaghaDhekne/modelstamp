# Security boundary

Pickle and joblib can execute arbitrary code while loading. A valid checksum or
HMAC does not make an untrusted serialized object safe; it only establishes
that the object matches a manifest or was authenticated by a holder of the
configured secret.

- Load artifacts only from trusted producers.
- Keep HMAC keys outside source control and artifact storage.
- Rotate keys using an authenticated `key_id` and a verification registry.
- Use `skops.io` or ONNX when their reduced execution surface fits the model.
- Use `inspect()`, `check()`, and `verify()` when deserialization is unnecessary.

Report suspected vulnerabilities privately according to the repository's
[security policy](https://github.com/AnaghaDhekne/modelstamp/security/policy).


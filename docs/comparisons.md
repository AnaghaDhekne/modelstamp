# When to use Modelstamp

Modelstamp is a focused verification layer for persisted Python ML artifacts.
It complements environment managers, registries, and safer serialization
formats rather than replacing them.

## Modelstamp and requirements files

`requirements.txt`, lock files, and environment specifications describe an
environment that can be installed. Modelstamp records the runtime associated
with one specific artifact, connects it to the artifact digest, and compares it
at verification or loading time.

Use both when you need reproducible installation and artifact-level evidence.

## Modelstamp and model registries

Registries such as MLflow manage model versions, lifecycle stages, metadata,
and deployment workflows. Modelstamp is intentionally smaller: it works with
ordinary files and adds local integrity and runtime checks.

Use Modelstamp when a registry would be excessive, or use it as an additional
verification step when artifacts leave a registry.

## Modelstamp and skops.io or ONNX

Modelstamp preserves pickle and joblib compatibility. It does not reduce their
ability to execute code during loading. `skops.io` and ONNX provide different
serialization and portability tradeoffs and may be better when their supported
model surface fits the application.

Use Modelstamp when retaining the existing Python object is necessary. Prefer
a format with a narrower execution surface when untrusted distribution is the
primary requirement.

## Modelstamp and cryptographic signatures

Modelstamp supports HMAC-SHA-256 authentication with a shared secret. It is
appropriate when trusted producers and verifiers can safely share that secret.
It is not appropriate for public verification because every verifier could
also forge a valid manifest. Public distribution requires an asymmetric system
such as Ed25519 or Sigstore, which Modelstamp does not currently provide.

## Good fits

- Persisted scikit-learn or Python models stored as files.
- Teams that need integrity checks before deserialization.
- Deployment gates that should detect dependency drift.
- Small projects that do not need a full registry.
- Internal artifact exchange using a protected shared HMAC key.

## Poor fits

- Loading models from untrusted sources.
- Public verification with publishable verification keys.
- Cross-language inference where Python object persistence is unsuitable.
- Complete experiment tracking, lineage, or registry lifecycle management.


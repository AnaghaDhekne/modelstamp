# modelstamp

**Model files with receipts.**

[![Tests](https://github.com/AnaghaDhekne/modelstamp/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/AnaghaDhekne/modelstamp/actions/workflows/test.yml?query=branch%3Amain+event%3Apush)
[![Python 3.8–3.13](https://img.shields.io/badge/python-3.8%E2%80%933.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/AnaghaDhekne/modelstamp/blob/main/LICENSE)

[Documentation](https://anaghadhekne.github.io/modelstamp/) ·
[Benchmarks](https://github.com/AnaghaDhekne/modelstamp/blob/main/BENCHMARKS.md) ·
[Security policy](https://github.com/AnaghaDhekne/modelstamp/security/policy)

`modelstamp` adds a verifiable environment manifest to persisted Python machine
learning models. It keeps the familiar pickle or joblib workflow while making
dependency changes and artifact corruption visible before deserialization.

Loading a persisted model under different dependency versions is unsupported
and may fail or behave differently. The scikit-learn documentation therefore
recommends preserving the training environment alongside the model. `modelstamp`
packages that practice into a small API.

## Why modelstamp?

A normal `model.pkl` remembers the fitted object, but not the environment that
made it work. `modelstamp` adds the missing receipt:

- **Integrity:** detect truncated, replaced, or corrupted artifacts.
- **Compatibility:** identify Python and relevant dependency changes.
- **Traceability:** record model details, metadata, time, and optional Git state.
- **Familiarity:** keep using pickle or joblib through `save()` and `load()`.

## Installation

```bash
pip install modelstamp
```

Install joblib support explicitly when scikit-learn is not already installed:

```bash
pip install "modelstamp[joblib]"
```

## Save and load

```python
import modelstamp as ms

manifest = ms.save(
    model,
    "model.joblib",
    metadata={"validation_roc_auc": 0.883},
)

model, manifest = ms.load("model.joblib")
```

Saving creates two files:

```text
model.joblib
model.joblib.manifest.json
```

The manifest records:

- SHA-256 and byte size of the artifact
- pickle or joblib serialization backend
- model class and scikit-learn pipeline components
- Python, platform, and relevant package versions
- creation time and optional Git commit/worktree status
- caller-provided JSON metadata

`load()` verifies the artifact before deserializing it. It then compares the
current runtime with the saved runtime and warns when a relevant dependency has
changed.

Operations targeting the same artifact are serialized across local processes.
During loading, verification and deserialization use the same open file so a
concurrent replacement cannot bypass the digest check.

## Mismatch policy

```python
# Default: verify, then warn about environment changes.
model, manifest = ms.load("model.joblib")

# Refuse to load when the runtime differs.
model, manifest = ms.load("model.joblib", on_mismatch="raise")

# Verify integrity but skip the environment warning.
model = ms.load(
    "model.joblib",
    on_mismatch="ignore",
    return_manifest=False,
)
```

Integrity failures always raise `ArtifactIntegrityError`; `on_mismatch` does not
disable the digest check.

## Inspect without loading

```python
manifest = ms.inspect("model.joblib")
report = ms.check("model.joblib")
ms.verify("model.joblib")
```

The same operations are available from the command line:

```bash
modelstamp inspect model.joblib
modelstamp check model.joblib
modelstamp verify model.joblib
```

You can also use `python -m modelstamp` in environments where the console
script is not on `PATH`. `inspect` validates the manifest structure but does
not authenticate its contents; use `verify` or `check` when trust matters.

`check` exits with status 0 for a clean artifact, 1 for a compatibility or
integrity mismatch, and 2 when the manifest cannot be read.

## Signed manifests

A checksum detects accidental corruption, but someone who can replace both
files can also create a matching checksum. For artifacts crossing a trust
boundary, sign the manifest with a secret key:

```python
import os
import modelstamp as ms

key = os.environ["MODELSTAMP_SIGNING_KEY"].encode()
ms.save(
    model,
    "model.joblib",
    signing_key=key,
    key_id="production-2026-q3",
)
model, manifest = ms.load("model.joblib", signing_key=key)
```

The signature is an HMAC-SHA-256 over the complete manifest, including the
artifact digest. A signed artifact cannot be loaded or verified without its
key. Supplying a key also rejects an unsigned manifest, preventing silent
downgrades. Keep the key outside source control and separate from the artifact.

HMAC is symmetric, so anyone who can verify with the shared secret can also
forge a valid manifest. `modelstamp` does not currently provide asymmetric
public-key verification such as Ed25519 or Sigstore.

For CLI verification, name the environment variable containing the key:

```bash
modelstamp verify model.joblib --signing-key-env MODELSTAMP_SIGNING_KEY
```

For key rotation, verify through a registry. The authenticated `key_id` chooses
the correct secret without changing old artifacts:

```python
keys = {
    "production-2026-q2": old_key,
    "production-2026-q3": current_key,
}
model, manifest = ms.load("model.joblib", signing_keys=keys)
```

See the [signing and key-rotation guide](https://anaghadhekne.github.io/modelstamp/signing/)
for the migration and security model.

## Complete scikit-learn example

```python
from pathlib import Path

from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import modelstamp as ms

X, y = load_iris(return_X_y=True)
pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))
pipeline.fit(X, y)

path = Path("iris.joblib")
ms.save(pipeline, path, metadata={"dataset": "iris"})
restored, manifest = ms.load(path)
print(restored.predict(X[:3]))
print(manifest.relevant_packages)

# Safe inspection does not deserialize the model.
print(ms.check(path))

# Corruption is detected before pickle/joblib can execute anything.
path.write_bytes(path.read_bytes() + b"changed")
try:
    ms.verify(path)
except ms.ArtifactIntegrityError as exc:
    print(f"Rejected: {exc}")
```

## API at a glance

| Operation | Purpose | Deserializes the model? |
|---|---|---:|
| `save(model, path)` | Save an artifact and its environment receipt | No |
| `load(path)` | Verify, compare environments, and load | Yes |
| `verify(path)` | Check artifact size and SHA-256 | No |
| `check(path)` | Check integrity and runtime compatibility | No |
| `inspect(path)` | Read schema-validated, unauthenticated manifest metadata | No |

## Security boundary

Pickle and joblib can execute code during loading. The SHA-256 recorded by
`modelstamp` detects accidental changes and mismatched sidecars; it is not a
digital signature and does not make an untrusted model safe. Only load artifacts
from sources you trust. For a safer serialization format, consider `skops.io` or
ONNX where they fit your model.

Security issues should be reported according to the
[security policy](https://github.com/AnaghaDhekne/modelstamp/security/policy).

## Supported Python versions

Python 3.8 through 3.13 are declared for the initial release. The package has no
required runtime dependency; joblib is optional.

## Development

```bash
python -m pip install ".[dev]"
pytest
ruff format --check .
ruff check .
python -m build
twine check dist/*
mkdocs build --strict
```

GitHub Actions runs the test suite on Python 3.8 through 3.13. Publishing is
configured for PyPI Trusted Publishing and runs when a GitHub release is
published.

`pyproject.toml` is the single source of truth for the package version. Update
only its `project.version` value when preparing a release; `modelstamp.__version__`
reads the resulting installed distribution metadata.

Property-based tests exercise malformed manifest structures. Verification
throughput for representative artifact sizes is recorded in
[BENCHMARKS.md](BENCHMARKS.md).

Contributions are welcome. See the
[contribution guide](https://github.com/AnaghaDhekne/modelstamp/blob/main/CONTRIBUTING.md)
for the local development and pull-request workflow.

## License

MIT

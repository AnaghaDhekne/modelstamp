# modelstamp

**Model files with receipts.**

[![Tests](https://github.com/AnaghaDhekne/modelstamp/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/AnaghaDhekne/modelstamp/actions/workflows/test.yml?query=branch%3Amain+event%3Apush)
[![Python 3.8–3.13](https://img.shields.io/badge/python-3.8%E2%80%933.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/AnaghaDhekne/modelstamp/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22047771.svg)](https://doi.org/10.5281/zenodo.22047771)

![Modelstamp detecting a tampered machine-learning artifact](https://raw.githubusercontent.com/AnaghaDhekne/modelstamp/main/docs/assets/modelstamp_demo.gif)

**Verify persisted Python ML models before deserialization and detect dependency
drift between the environments that save and load them.**

```bash
pip install modelstamp
```

```python
import modelstamp as ms

model = {"feature_names": ["age", "income"], "weights": [0.3, 0.7]}
ms.save(model, "model.pkl")
restored, manifest = ms.load("model.pkl", on_mismatch="raise")
print(restored, manifest.relevant_packages)
```

[Documentation](https://anaghadhekne.github.io/modelstamp/) ·
[Benchmarks](https://github.com/AnaghaDhekne/modelstamp/blob/main/BENCHMARKS.md) ·
[Security policy](https://github.com/AnaghaDhekne/modelstamp/security/policy)

`modelstamp` verifies persisted Python machine-learning models, detects relevant
dependency drift, and records reproducible environment metadata. It keeps the
familiar pickle or joblib workflow while making artifact corruption and runtime
changes visible before deserialization.

Loading a persisted model under different dependency versions is unsupported
and may fail or behave differently. The
[scikit-learn model-persistence documentation](https://scikit-learn.org/stable/model_persistence.html)
therefore recommends preserving the training environment alongside the model.
`modelstamp` packages that practice into a small API.

## Why modelstamp?

A normal `model.pkl` remembers the fitted object, but not the environment that
made it work. `modelstamp` adds the missing receipt:

- **Integrity:** detect truncated, replaced, or corrupted artifacts.
- **Compatibility:** identify Python and relevant dependency changes.
- **Traceability:** record model details, metadata, time, and optional Git state.
- **Familiarity:** keep using pickle or joblib through `save()` and `load()`.

## When to use it

Modelstamp is designed for scikit-learn and other persisted Python ML models
when you need artifact-level integrity checks, dependency-drift detection, or
reproducibility metadata without adopting a full model registry.

It complements lock files and registries: those tools recreate environments or
manage model lifecycles, while Modelstamp connects one artifact to its digest
and recorded runtime. It does not make untrusted pickle or joblib payloads safe
to execute and does not currently provide asymmetric public-key signatures.

See the guides for [dependency drift](https://anaghadhekne.github.io/modelstamp/dependency-drift/),
[joblib artifact verification](https://anaghadhekne.github.io/modelstamp/verify-joblib/),
[CI/CD checks](https://anaghadhekne.github.io/modelstamp/ci/), and
[comparisons with related tools](https://anaghadhekne.github.io/modelstamp/comparisons/).

## Optional joblib support

Install joblib support explicitly when it is not already available in the
model environment:

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

Additional standalone examples cover a scikit-learn pipeline, tamper detection,
and HMAC-authenticated manifests in the
[`examples/`](https://github.com/AnaghaDhekne/modelstamp/tree/main/examples)
directory.

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
published. Production releases must use a protected `v*` tag whose commit is
contained in `main`; the PyPI deployment also requires maintainer approval.

`pyproject.toml` is the runtime source of truth for the package version;
`modelstamp.__version__` reads the resulting installed distribution metadata.
Release preparation also keeps the human-facing version and date in
`CITATION.cff` synchronized.

Maintainers should follow the [release checklist](docs/releasing.md). A merge
to `main` does not publish to PyPI by itself, and lockfile-only maintenance does
not require a package release.

Property-based tests exercise malformed manifest structures. Verification
throughput for representative artifact sizes is recorded in
[BENCHMARKS.md](BENCHMARKS.md).

Contributions are welcome. See the
[contribution guide](https://github.com/AnaghaDhekne/modelstamp/blob/main/CONTRIBUTING.md)
for the local development and pull-request workflow.

## Maintainer

[Anagha Dhekne](https://github.com/AnaghaDhekne)

## License

MIT

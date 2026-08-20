# modelstamp

`modelstamp` adds a verifiable environment manifest to persisted Python machine
learning models. It keeps the familiar pickle or joblib workflow while making
dependency changes and artifact corruption visible before deserialization.

Loading a persisted model under different dependency versions is unsupported
and may fail or behave differently. The scikit-learn documentation therefore
recommends preserving the training environment alongside the model. `modelstamp`
packages that practice into a small API.

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

`check` exits with status 0 for a clean artifact, 1 for a compatibility or
integrity mismatch, and 2 when the manifest cannot be read.

## Security boundary

Pickle and joblib can execute code during loading. The SHA-256 recorded by
`modelstamp` detects accidental changes and mismatched sidecars; it is not a
digital signature and does not make an untrusted model safe. Only load artifacts
from sources you trust. For a safer serialization format, consider `skops.io` or
ONNX where they fit your model.

## Supported Python versions

Python 3.8 through 3.12 are declared for the initial release. The package has no
required runtime dependency; joblib is optional.

## Development

```bash
python -m pip install ".[dev]"
pytest
ruff format --check .
ruff check .
python -m build
twine check dist/*
```

GitHub Actions runs the test suite on Python 3.8 through 3.12. Publishing is
configured for PyPI Trusted Publishing and runs when a GitHub release is
published.

## License

MIT

# modelstamp

**Model files with receipts.**

`modelstamp` saves Python machine-learning models with a sidecar manifest that
records the artifact checksum, serialization backend, model details, runtime
dependencies, and caller-provided metadata.

```bash
pip install modelstamp
```

```python
import modelstamp as ms

ms.save(model, "model.joblib", metadata={"validation_auc": 0.91})
model, manifest = ms.load("model.joblib")
```

The artifact is hashed before deserialization. Dependency changes can warn or
block loading, and optional HMAC authentication protects the model/manifest
pair against unauthorized replacement.

Start with the [quick start](quickstart.md), then review the
[security boundary](security.md) before loading persisted Python objects.

Releases are published from protected `v*` tags using PyPI Trusted Publishing.
Maintainers can use the [release checklist](releasing.md) for the protected
`main`-to-PyPI workflow.

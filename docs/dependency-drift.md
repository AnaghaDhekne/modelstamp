# Detect dependency drift in persisted ML models

A persisted scikit-learn model depends on more than its fitted parameters.
Changes to Python, scikit-learn, NumPy, SciPy, joblib, or an estimator-specific
package can make an old artifact fail to load or behave differently.

Modelstamp records the relevant runtime versions when the artifact is saved and
compares them with the environment in which it is checked or loaded.

## Save the training environment

```python
import modelstamp as ms

ms.save(model, "model.joblib", metadata={"training_run": "2026-08-21"})
```

This creates the serialized model and a schema-validated JSON manifest:

```text
model.joblib
model.joblib.manifest.json
```

## Check without deserializing

```python
report = ms.check("model.joblib")

if report:
    print(report)
```

`check()` verifies the artifact and compares the current runtime with the
recorded runtime without executing pickle or joblib payloads.

The command-line equivalent is suitable for deployment checks:

```bash
modelstamp check model.joblib
```

The command exits with status 0 for a clean artifact, 1 for an integrity or
compatibility mismatch, and 2 when the artifact or manifest cannot be read.

## Choose the loading policy

```python
# Warn when a relevant runtime dependency changed.
model, manifest = ms.load("model.joblib")

# Refuse to deserialize when the runtime changed.
model, manifest = ms.load("model.joblib", on_mismatch="raise")

# Keep integrity verification but ignore environment differences.
model = ms.load(
    "model.joblib",
    on_mismatch="ignore",
    return_manifest=False,
)
```

Modelstamp compares packages relevant to the saved model rather than treating
every installed package as a compatibility requirement. It does not prove that
two environments will produce identical predictions; it makes recorded
environment differences visible so the caller can enforce an appropriate
policy.


# Quick start

## Save and load

```python
import modelstamp as ms

manifest = ms.save(
    model,
    "model.joblib",
    metadata={"dataset": "training-2026-08"},
)

model, manifest = ms.load("model.joblib")
```

Saving creates `model.joblib` and `model.joblib.manifest.json`.

## Choose the mismatch policy

```python
# Warn when Python or a relevant dependency differs.
model, manifest = ms.load("model.joblib")

# Refuse to deserialize under a different environment.
model, manifest = ms.load("model.joblib", on_mismatch="raise")

# Verify integrity but ignore environment differences.
model = ms.load(
    "model.joblib",
    on_mismatch="ignore",
    return_manifest=False,
)
```

## Inspect safely

These operations never deserialize the artifact:

```python
manifest = ms.inspect("model.joblib")
report = ms.check("model.joblib")
ms.verify("model.joblib")
```

The same commands are available through the `modelstamp` CLI.
Use `python -m modelstamp` if the console script is not on `PATH`.

`inspect()` validates the manifest structure, but it does not verify its
checksum or signature. Use `verify()` or `check()` when trust matters.

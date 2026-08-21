# Runnable examples

The repository includes standalone examples that can be copied or executed
from a development checkout.

Install the example dependencies:

```bash
python -m pip install "modelstamp[examples]"
```

## scikit-learn pipeline

```bash
python examples/sklearn_pipeline.py
```

Trains an Iris classifier, saves it with metadata, verifies it without loading,
and restores it with a strict environment policy.

## Integrity failure

```bash
python examples/detect_tampering.py
```

Saves an artifact, changes its bytes, and demonstrates rejection before
deserialization.

## HMAC-authenticated manifest

```bash
MODELSTAMP_SIGNING_KEY="replace-with-a-secret" \
  python examples/signed_artifact.py
```

Demonstrates manifest authentication. The example key must not be reused in
production.

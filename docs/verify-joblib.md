# Verify a joblib model before loading it

Pickle and joblib can execute code during deserialization. Modelstamp verifies
the persisted bytes before passing the same open file to the deserializer,
preventing a concurrent replacement from bypassing the digest check.

## Save an artifact with a receipt

```python
import modelstamp as ms

ms.save(model, "classifier.joblib")
```

The sidecar manifest records the artifact byte size and SHA-256 digest.

## Verify without loading

```python
ms.verify("classifier.joblib")
```

Or from a shell:

```bash
modelstamp verify classifier.joblib
```

Any truncation, replacement, or same-size modification raises
`ArtifactIntegrityError` before deserialization.

## Understand the trust boundary

A checksum detects a mismatch between the artifact and its manifest, but an
attacker who can replace both files can calculate a new checksum. For artifacts
moving across a trust boundary, use an HMAC-authenticated manifest and protect
the shared key separately:

```python
import os
import modelstamp as ms

key = os.environ["MODELSTAMP_SIGNING_KEY"].encode()
ms.save(model, "classifier.joblib", signing_key=key)
model, manifest = ms.load("classifier.joblib", signing_key=key)
```

HMAC is symmetric: anyone who can verify with the secret can also create a
valid signature. Modelstamp does not make an untrusted pickle safe and does not
currently provide public-key verification. See the [security guide](security.md)
and [signing guide](signing.md) before distributing artifacts.


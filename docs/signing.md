# Signing and key rotation

Checksums detect corruption but cannot stop someone who can replace both the
artifact and its manifest. HMAC authentication adds a shared-secret trust
boundary.

HMAC is symmetric: the signing key and verification key are the same secret.
Anyone who can verify an artifact with that key can also create a valid forgery.
Do not distribute an HMAC key to parties that should have verification-only
access. Public or third-party verification without signing authority requires
an asymmetric mechanism such as Ed25519 or Sigstore, which `modelstamp` does
not currently provide.

## Sign an artifact

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
```

Never store the secret in source control or beside the artifact.

## Verify with a key registry

Applications can retain old keys while rotating new writes to a new key ID:

```python
keys = {
    "production-2026-q2": old_key,
    "production-2026-q3": current_key,
}

model, manifest = ms.load("model.joblib", signing_keys=keys)
```

The authenticated `key_id` selects the registry entry. An unknown identifier
fails immediately during key selection. A wrong key, missing signature, or
modified identifier also rejects before artifact hashing or deserialization.

Artifacts created before key IDs were supported remain compatible:

```python
model, manifest = ms.load("legacy.joblib", signing_key=legacy_key)
```

Use either `signing_key` or `signing_keys`, never both.

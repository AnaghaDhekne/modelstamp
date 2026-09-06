# ADR-0001: Verify before model reconstruction

- Status: Accepted; recorded retrospectively
- Recorded: 2026-09-06
- Owners: Modelstamp maintainers
- Related: `src/modelstamp/core.py`, `experiments/deserialization_boundary/`,
  `experiments/pyod_baseline/`

## Context

Pickle and joblib reconstruct Python objects during loading and may execute
code. Dependency incompatibility and artifact corruption are often knowable
from external metadata and artifact bytes. If those checks occur only after the
loader starts, a strict rejection is too late to preserve that boundary.

## Decision

Modelstamp exposes `verify()` and `check()` paths that do not deserialize the
artifact. `load()` authenticates the configured manifest, verifies size and
SHA-256, and evaluates environment policy before calling the serialization
backend. Integrity verification and deserialization use the same already-open
artifact stream while the artifact lock is held.

## Alternatives considered

### Check after ordinary deserialization

This is easy to wrap around existing loaders and still reports drift, but it
cannot reject before reconstruction has begun.

### Inspect pickle opcodes or scan for malicious content

Static inspection cannot establish that arbitrary Python deserialization is
safe. Modelstamp therefore does not claim malware detection.

### Replace pickle/joblib with a restricted format

Formats such as skops.io or ONNX can narrow execution risk, but they do not
preserve every existing fitted Python object. They remain preferable when their
supported model surface is sufficient.

## Consequences

### Benefits

- Known integrity and strict compatibility failures can stop before loading.
- CI and deployment systems can evaluate artifacts without reconstructing them.
- The ordering guarantee is observable and independently testable.

### Costs and limitations

- Successful verification does not make subsequent deserialization safe.
- The sidecar must remain available and trustworthy for its intended use.
- Reading the artifact to hash it adds work proportional to artifact size.

## Evidence and follow-up

- The controlled deserialization-boundary experiment checks that strict
  rejection occurs before a reconstruction side effect.
- The PyOD baseline isolates the ordering distinction without claiming greater
  drift-detection accuracy.
- Trust-boundary tests cover replacement between path lookup and loading.


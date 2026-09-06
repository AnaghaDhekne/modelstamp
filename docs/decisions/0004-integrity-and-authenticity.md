# ADR-0004: Keep integrity and authenticity guarantees distinct

- Status: Accepted; recorded retrospectively
- Recorded: 2026-09-06
- Owners: Modelstamp maintainers
- Related: `docs/security.md`, `docs/signing.md`,
  `tests/test_trust_boundaries.py`

## Context

A digest can show whether artifact bytes match a manifest, but an attacker who
can replace both files can create a consistent pair. Authenticity requires a
trust anchor. Modelstamp's current authentication mechanism is HMAC, whose
signing and verification secret is the same.

## Decision

Always distinguish these guarantees:

- SHA-256 and size provide integrity relative to the manifest.
- Optional HMAC authenticates the manifest as produced by a holder of the
  shared secret and transitively binds the artifact digest.
- `key_id` supports key selection and rotation but is authenticated metadata,
  not an identity proof by itself.

Supplying a verification key makes a signature mandatory. Documentation and
errors must not present HMAC as public-key publisher identity, replay
protection, malware detection, or safety for untrusted pickle/joblib payloads.

## Alternatives considered

### Describe the checksum as authenticity

This would be simpler language but would be incorrect when an artifact and
unsigned manifest are replaced together.

### Require HMAC for every artifact

Mandatory keys would add operational burden to local reproducibility workflows
that need corruption detection but do not cross a producer/verifier boundary.

### Implement asymmetric signatures immediately

Public verification and separation of signing authority are valuable, but add
key formats, trust-root distribution, revocation, and lifecycle responsibilities
beyond the initial shared-secret use case. Sigstore integration remains a
possible future decision.

## Consequences

### Benefits

- Claims align with the actual cryptographic trust boundary.
- Unsigned local workflows remain lightweight.
- Key rotation can use authenticated identifiers without hiding HMAC's limits.

### Costs and limitations

- Every HMAC verifier can forge a valid manifest.
- A shared-key holder can replace a pair, and an older valid pair can be replayed.
- Public distribution needs an asymmetric or identity-based system.

## Evidence and follow-up

- Trust-boundary tests encode both guarantees and intentional non-guarantees,
  including pair swap, shared-key forgery, and replay.
- An asymmetric-signing proposal requires a new ADR defining identity,
  revocation, offline verification, and migration behavior.


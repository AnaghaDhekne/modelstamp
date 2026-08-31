# Model integrity trust-boundary case study

## Control objective

Detect accidental corruption or unauthorized replacement of a persisted model
before pickle or joblib deserialization. Make the remaining trust assumptions
explicit so checksum verification is not mistaken for proof of provenance.

## Test design

The validation changes either the model artifact, its sidecar manifest, or both.
Each scenario then calls `verify()` before any model is deserialized.

| Scenario | Expected | Observed | Control interpretation |
| --- | --- | --- | --- |
| Artifact changed; manifest unchanged | Reject | SHA-256 mismatch | Digest binds the artifact to the recorded manifest. |
| Artifact and unsigned manifest replaced together | Accept | Replacement loaded | A consistent checksum does not authenticate the producer. |
| Unsigned manifest hash edited; artifact unchanged | Reject | SHA-256 mismatch | Recalculation detects a false digest claim. |
| Unsigned manifest identity edited; artifact unchanged | Accept | Edited identity retained | Descriptive fields are not authenticated without HMAC. |
| Signed pair replaced by an unsigned pair | Reject | Manifest not signed | Supplying the trusted HMAC key makes authentication mandatory. |
| Replacement pair signed with an untrusted key | Reject | Invalid HMAC | The trusted verifier detects the wrong key. |
| Replacement pair signed by a shared-key holder | Accept | Replacement loaded | A key holder has verification and signing authority. |
| Older valid signed pair replayed | Accept | Older version loaded | HMAC authenticates contents but does not establish freshness. |

The same eight scenarios are enforced in GitHub Actions by
`.github/workflows/trust-boundary-validation.yml`, so changes to the implementation
or case-study script rerun the trust-boundary evidence automatically.

Run the complete matrix locally from the repository root:

```bash
PYTHONPATH=src python examples/trust_boundary_matrix.py
```

## Result and residual risk

Modelstamp detects changes when the verifier retains either a trusted manifest
or an HMAC key unknown to the party replacing the files. It cannot establish
the provenance of an unsigned artifact-manifest pair that is replaced as a
unit. HMAC closes that gap only inside a shared-secret trust boundary.

Because HMAC uses the same key for signing and verification, it does not provide
verification-only access. Anyone who receives the shared key can create a new
artifact and a valid manifest. Public distribution or separation of signing and
verification authority therefore requires asymmetric signatures or an external
trusted signing service, neither of which Modelstamp currently claims to
provide.

HMAC also does not prevent rollback or replay. An older artifact and manifest
that were validly signed with the same trusted key still authenticate when
reintroduced later. Preventing rollback requires trusted external state—such as
an append-only registry, deployment policy, or monotonic version check—that
identifies which signed artifact is currently authorized.

## Model-risk-audit framing

The control should be evaluated against its stated objective, evidence, and
trust assumptions—not merely against the presence of a cryptographic feature.
The tests demonstrate both successful control operation and negative cases in
which the control is not designed to protect the artifact. Those negative cases
are residual risks to document, assign, and address through key management,
access control, or a stronger signing architecture when the use case requires
it.

## Interview talk track

> I built Modelstamp after identifying a control gap in normal model
> persistence: the artifact, its environment record, and verification are often
> disconnected. I tested the control against its actual trust boundary, not
> just the happy path. Changing an artifact while retaining the original
> manifest caused verification to fail before deserialization. Replacing both
> an unsigned artifact and its manifest passed, which demonstrates that a
> checksum establishes integrity relative to the manifest but not provenance.
> Requiring HMAC rejected unsigned and incorrectly signed replacements. The
> remaining risk is that HMAC is symmetric, so anyone holding the verification
> key can also sign a replacement. I documented that limitation rather than
> presenting HMAC as equivalent to asymmetric signing. The exercise reflects
> how I approach model-risk controls: define the objective, test positive and
> negative cases, identify trust assumptions, and communicate residual risk.

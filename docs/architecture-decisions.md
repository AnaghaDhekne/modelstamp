# Architecture decision records

Modelstamp records consequential design choices as architecture decision
records (ADRs). ADRs preserve the alternatives and trade-offs that source code
alone cannot explain. They are historical records, not promises that a decision
will never change.

## Decision log

| ADR | Decision | Status |
|---|---|---|
| [0001](decisions/0001-pre-deserialization-verification.md) | Verify before model reconstruction | Accepted; recorded retrospectively |
| [0002](decisions/0002-sidecar-manifest.md) | Use a versioned JSON sidecar manifest | Accepted; recorded retrospectively |
| [0003](decisions/0003-dependency-relevance.md) | Compare artifact-relevant dependencies | Accepted; recorded retrospectively |
| [0004](decisions/0004-integrity-and-authenticity.md) | Keep integrity and authenticity guarantees distinct | Accepted; recorded retrospectively |
| [0005](decisions/0005-compatibility-not-replication.md) | Report compatibility evidence, not environment replication | Accepted; recorded retrospectively |

The first five ADRs document decisions that predate this log. Their record date
is not presented as the date on which the original decision was made.

## When to add an ADR

Add an ADR when a change affects a public guarantee, trust boundary, persisted
format, compatibility policy, supported workflow, or a choice that a future
maintainer might otherwise reverse without knowing the original trade-off.
Routine implementation details do not need ADRs.

1. Copy the [template](decisions/0000-template.md) to the next four-digit number.
2. Use status `Proposed` while the decision is under review.
3. Describe at least one credible alternative and why it was not chosen.
4. Link code, tests, experiments, issues, or prior ADRs that constrain the choice.
5. Merge the ADR with the change that makes the decision, when practical.
6. If a decision changes, add a new ADR and mark the old one `Superseded by
   ADR-NNNN`; do not rewrite the old rationale as if it never existed.

ADRs record human judgment. Generated summaries or proposed wording must be
reviewed by a maintainer who accepts responsibility for the rationale.


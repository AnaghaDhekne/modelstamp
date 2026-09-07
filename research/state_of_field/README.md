# State-of-the-field evidence

This directory is the source-auditable starting point for Modelstamp's
state-of-the-field comparison. It records what nearby tools say they solve and
keeps those sourced facts separate from Modelstamp maintainer analysis.

The evidence was reviewed on **2026-09-06**. It is a bounded comparison, not a
systematic literature review and not a claim that the listed projects are the
only alternatives.

## Included tool classes

- Python object persistence: pickle/joblib and scikit-learn guidance
- safer sklearn-oriented persistence: skops.io
- portable inference graphs: ONNX
- versioned dependency envelopes: PyOD persistence
- model lifecycle and packaging: MLflow Models and Model Registry
- artifact and pipeline versioning: DVC
- public artifact authenticity: Sigstore

The ledger evaluates Sigstore's general software-artifact signing boundary. The
SaTML manuscript separately discusses OpenSSF Model Signing (OMS), a
model-specific signing specification whose signature file follows the Sigstore
Bundle Format and supports multiple signing options, including Sigstore. The two
names are related but not interchangeable, and the Sigstore ledger entry should
not be read as an evaluation of OMS. See the official
[OpenSSF OMS overview](https://openssf.org/blog/2025/06/25/an-introduction-to-the-openssf-model-signing-oms-specification/).

These classes were selected because each overlaps at least one Modelstamp
responsibility or trust-boundary decision. General environment managers are
represented by scikit-learn's persistence guidance rather than exhaustively
catalogued.

## Files

- `evidence.json` is the machine-readable claim ledger. Every comparison claim
  has an official documentation URL, an access date, and a bounded paraphrase.
- `validate_evidence.py` checks schema invariants, unique identifiers, HTTPS
  source URLs, known status vocabulary, source references, and tool coverage.
- [`docs/comparisons.md`](../../docs/comparisons.md) is the reader-facing
  synthesis.

## Reproduce the local evidence checks

From the repository root:

```bash
python research/state_of_field/validate_evidence.py
```

The validator deliberately does not fetch the web. This makes the check stable
offline and avoids presenting a changed webpage as if it were the page reviewed
on the access date. To refresh the research, a researcher should revisit every
URL, update the bounded paraphrases and access date, then rerun the validator and
review the rendered comparison.

## Interpretation rules

1. `supported` means an official source documents the capability.
2. `partial` means the source documents an overlapping capability with a
   materially different boundary.
3. `not_documented` means the reviewed official source did not document the
   capability. It does **not** prove that no extension or undocumented path
   exists.
4. `not_applicable` means the dimension is outside the tool's stated problem.
5. Statements about whether Modelstamp could have been implemented inside an
   existing project are maintainer analysis, not claims made by those projects.

## Refresh checklist

1. Confirm that every URL is still an official project source.
2. Re-read the relevant section; do not infer absence from a search snippet.
3. Update claims when behavior or scope changed.
4. Add a new source rather than silently broadening an old paraphrase.
5. Run the validator and `mkdocs build --strict`.
6. Record any experimentally testable distinction in a separate, pinned
   experiment before making a performance or ordering claim.

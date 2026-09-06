# ADR-0003: Compare artifact-relevant dependencies

- Status: Accepted; recorded retrospectively
- Recorded: 2026-09-06
- Owners: Modelstamp maintainers
- Related: `src/modelstamp/_model.py`, `src/modelstamp/_environment.py`,
  `experiments/reproducible_evidence/`

## Context

A full Python environment commonly contains packages unrelated to a persisted
model. Reporting every change creates noise, while recording too little can
miss libraries that participate in reconstruction or inference. Python object
graphs do not provide a perfect, stable declaration of all semantic
dependencies.

## Decision

Record versions for a bounded set of common ML distributions, then store an
artifact-specific `relevant_packages` subset derived from the model type and
known wrapper relationships. Compatibility comparison reports Python/runtime
changes and version changes only for that relevant subset. Installed-package
discovery uses distribution metadata and does not import ML packages.

Treat relevance as an explicit, testable heuristic rather than a claim of
complete dependency discovery.

## Alternatives considered

### Compare every installed distribution

This maximizes captured differences but makes unrelated tools, notebooks, and
transitive packages appear as model drift.

### Compare only the top-level model library

This is simple but misses known serializer and numerical dependencies and
dependencies embedded by third-party sklearn wrappers.

### Capture imports or traverse the complete object graph

Runtime tracing depends on the training path, and arbitrary object traversal is
fragile and may itself invoke unsafe behavior. Neither yields a complete
semantic dependency set.

## Consequences

### Benefits

- Reports remain focused enough for CI and deployment gates.
- Relevance policy can be expanded with controlled positive and noise cases.
- Version capture avoids importing large or side-effectful ML libraries.

### Costs and limitations

- False negatives and false positives remain possible outside tested stacks.
- New estimator wrappers may require an explicit relevance rule.
- A version match does not guarantee behavioral equivalence.

## Evidence and follow-up

- The reproducible drift matrix includes sklearn, LightGBM wrappers, XGBoost,
  CatBoost, NumPy, SciPy, joblib, and unrelated-package controls.
- New relevance rules should include a positive drift case and, where useful, a
  negative noise control.


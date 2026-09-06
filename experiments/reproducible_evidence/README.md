# Reproducible drift and trust-boundary evidence

This package turns Modelstamp's dependency-drift matrix and trust-boundary
tests into one independently rerunnable research protocol. It fits and saves
real sklearn, LightGBM, XGBoost, and CatBoost models in pinned environments,
checks them in changed environments, and exercises eight integrity and HMAC
trust-boundary scenarios.

## Reproduce

Prerequisites are Git, Python 3.11, and network access to PyPI. From a clean
checkout at the commit being evaluated, run:

```bash
python3.11 experiments/reproducible_evidence/run_evidence.py
```

The command creates isolated virtual environments and writes `results.json`,
`SUMMARY.md`, per-scenario JSON observations, artifacts, and manifests under
`experiments/reproducible_evidence/output/`. No credentials, private data, or
external services are required.

To run only one suite or a selected drift case:

```bash
python3.11 experiments/reproducible_evidence/run_evidence.py --suite trust
python3.11 experiments/reproducible_evidence/run_evidence.py \
  --suite drift --scenario lightgbm-embedded-sklearn-drift
```

`scenarios.json` is the protocol source of truth for package pins, expected
changed-package sets, frameworks, and scenario identifiers. The runner records
its SHA-256 digest in the aggregate result so observations can be tied to the
exact protocol definition.

## Acceptance criteria

- Every drift case saves a real fitted model in environment A.
- `modelstamp.check()` runs in environment B without loading the model.
- The observed changed-package set exactly equals the predeclared set.
- All eight trust-boundary outcomes equal their documented accept/reject result.
- Any unexpected result exits nonzero.
- Completed observations are retained as JSON evidence and a readable summary.

## Interpretation boundary

The drift suite evaluates detection and relevance filtering for the pinned
models and version pairs; it does not infer semantic compatibility or claim
that every reported change alters predictions. The trust suite distinguishes
integrity detection from authentication and deliberately records accepted
shared-key replacement and replay cases. Modelstamp does not make pickle or
joblib safe for untrusted artifacts.

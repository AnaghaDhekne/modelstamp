# Reproducible drift and trust-boundary evidence

Modelstamp packages its controlled dependency-drift and trust-boundary
evaluations as one rerunnable Python 3.11 protocol. A clean checkout and one
command reproduce 14 pinned drift cases and eight trust-boundary cases:

```bash
python3.11 experiments/reproducible_evidence/run_evidence.py
```

The protocol produces an aggregate JSON result, a Markdown summary,
per-scenario observations, persisted model artifacts, and manifests. The
scenario catalog is hashed into the result to connect observations to the
predeclared package pins and expected outcomes.

## Evidence covered

The drift suite includes sklearn patch and minor changes, LightGBM and its
embedded sklearn dependency, XGBoost, CatBoost, NumPy, SciPy, joblib,
identical-environment controls, and unrelated-package noise controls. Each case
fits a real estimator in environment A and checks it without deserialization in
environment B.

The trust-boundary suite covers artifact tampering, an unsigned pair swap,
manifest hash and identity edits, unsigned replacement of a signed pair,
untrusted-key replacement, shared-key-holder replacement, and replay of an
older valid signed pair. Accepted cases are documented limitations, not
security successes.

See the [experiment README](https://github.com/AnaghaDhekne/modelstamp/tree/main/experiments/reproducible_evidence)
for prerequisites, selective-run commands, acceptance criteria, and the
interpretation boundary.

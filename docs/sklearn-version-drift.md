# Definitive scikit-learn version-drift experiment

This experiment persists a fitted scikit-learn model under version 1.5.2 and
then evaluates it under both a same-version control and scikit-learn 1.6.1. It
records ordinary joblib/scikit-learn loading behavior beside Modelstamp's
non-deserializing comparison and strict pre-load rejection.

The complete protocol, pinned requirements, executable scripts, acceptance
criteria, and limitations are in
[`experiments/sklearn_version_drift`](https://github.com/AnaghaDhekne/modelstamp/tree/main/experiments/sklearn_version_drift).

## Protocol at a glance

1. Fit `LogisticRegression(max_iter=500, random_state=0)` on the Iris dataset.
2. Persist equivalent ordinary joblib and Modelstamp artifacts under
   scikit-learn 1.5.2.
3. Execute a same-environment control under 1.5.2.
4. Execute the changed environment under 1.6.1 while holding NumPy, SciPy, and
   joblib constant.
5. Record whether reconstruction begins, what warnings or mismatches appear,
   whether loading succeeds, and whether fixed probe outputs match.
6. Assert that `modelstamp.check()` does not invoke the serialization loader and
   that strict mismatch handling rejects the changed environment before
   `joblib.load()` is called.

## Reproduce

From the repository root with Python 3.11:

```bash
python experiments/sklearn_version_drift/run_experiment.py
```

The same command runs in GitHub Actions. Each run uploads the ordinary and
Modelstamp artifacts, manifest, save metadata, full control and drift
observations, and a compact `summary.json`.

## Interpretation boundary

The experiment compares ordering for one predeclared model and version pair. It
does not compare population-level drift-detection accuracy, establish semantic
compatibility between scikit-learn releases, or claim that version drift must
change predictions. Modelstamp's relevance check covers a selected package set,
not the complete dependency graph. Neither Modelstamp nor the ordinary baseline
makes pickle/joblib safe for untrusted artifacts.

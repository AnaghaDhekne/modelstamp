# Definitive scikit-learn version-drift experiment

This experiment follows one real fitted `LogisticRegression` model from
scikit-learn 1.5.2 into a scikit-learn 1.6.1 environment. It records ordinary
joblib/scikit-learn loading behavior and compares that ordering with
Modelstamp's non-deserializing comparison and strict pre-load rejection.

## Research question

For one pinned persisted model and version change, when does dependency-version
evidence become available relative to model reconstruction?

This is an ordering experiment. It is not a population-level comparison of
drift-detection accuracy, and it does not claim that every version change alters
predictions or is semantically incompatible.

## Predeclared environments

All conditions use Python 3.11, NumPy 1.26.4, SciPy 1.13.1, and joblib 1.4.2.
Only scikit-learn changes.

| Stage | scikit-learn | Purpose |
| --- | --- | --- |
| Save | 1.5.2 | Fit and persist equivalent ordinary joblib and Modelstamp artifacts. |
| Control | 1.5.2 | Establish same-environment behavior. |
| Drift | 1.6.1 | Observe behavior after a minor-version change. |

The model is trained on `sklearn.datasets.load_iris` with
`LogisticRegression(max_iter=500, random_state=0)`. The save step records model
parameters, package versions, artifact hashes, and predictions/probabilities for
a fixed 20-row probe.

## One-command reproduction

From the repository root with Python 3.11 available:

```bash
python experiments/sklearn_version_drift/run_experiment.py
```

The runner creates two temporary virtual environments, installs the exact
requirements, creates the artifacts, executes the control and drift conditions,
and writes:

```text
experiments/sklearn_version_drift/output/
├── artifacts/
│   ├── baseline.joblib
│   ├── modelstamp.joblib
│   ├── modelstamp.joblib.manifest.json
│   └── save_metadata.json
├── control.json
├── drift.json
└── summary.json
```

No pre-generated result is trusted: assertions are evaluated against the
observations produced by that run. CI executes the same command and uploads the
complete output directory as a workflow artifact.

## Observations and acceptance criteria

The same-environment control must show:

- ordinary joblib loading reconstructs and returns the model without an
  `InconsistentVersionWarning`;
- `modelstamp.check()` reports no mismatch and invokes no serialization loader;
- strict Modelstamp loading succeeds and returns matching probe outputs.

The changed environment must show:

- ordinary `joblib.load()` begins estimator reconstruction and records whether
  scikit-learn emits `InconsistentVersionWarning`;
- the ordinary load result and fixed probe outputs are recorded rather than
  interpreted as general compatibility evidence;
- `modelstamp.check()` reports exactly `scikit-learn: 1.5.2 -> 1.6.1` without
  invoking `joblib.load()`;
- `modelstamp.load(..., on_mismatch="raise")` raises
  `EnvironmentMismatchError` before `joblib.load()` is invoked.

The scripts fail if these ordering assertions are not satisfied.

## Instrumentation

The baseline wraps `BaseEstimator.__setstate__` only as an observation probe to
record when estimator reconstruction begins. It delegates immediately to the
original method, preserving scikit-learn's warning and load behavior.

Modelstamp observations wrap `joblib.load` to record whether the serialization
loader is reached. The probe does not alter either artifact, the manifest,
version comparison, or mismatch policy.

## Scope and limitations

- The result applies to the pinned model, package versions, Python version, and
  platform represented by the run.
- Matching predictions in this probe do not establish compatibility between
  scikit-learn releases; differing predictions would not identify a cause.
- Modelstamp compares recorded version strings for a bounded, model-relevant
  package set. It does not infer semantic compatibility or cover the complete
  dependency graph.
- scikit-learn's baseline warning is valuable version evidence. The tested
  distinction is that it is surfaced while reconstruction is already underway,
  whereas Modelstamp exposes the represented difference without deserializing.
- Neither path makes pickle/joblib safe for untrusted artifacts.

## Files

- `create_artifacts.py`: deterministic model fitting and equivalent persistence.
- `observe.py`: baseline and Modelstamp observations plus assertions.
- `summarize_results.py`: compact machine-readable result summary.
- `run_experiment.py`: isolated, cross-platform orchestration.
- `requirements-*.txt`: exact save/control and drift environments.
- `.github/workflows/sklearn-version-drift.yml`: independent CI execution.

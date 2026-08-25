# Dependency-drift validation matrix

This matrix tests Modelstamp against models saved in one installed environment
and checked in another. Each case builds two isolated Python 3.11 environments,
saves a real fitted model under environment A, and runs `modelstamp.check()`
under environment B without deserializing the artifact.

The workflow fails when the observed changed-package set differs from the
expected set. The recorded run completed successfully for all eight cases:
[GitHub Actions run 32865721805](https://github.com/AnaghaDhekne/modelstamp/actions/runs/32865721805).

| Scenario | Save environment | Check environment | Observed change | Interpretation |
| --- | --- | --- | --- | --- |
| sklearn patch | scikit-learn 1.5.1 | scikit-learn 1.5.2 | `scikit-learn` | Patch changes are reported. |
| sklearn minor | scikit-learn 1.5.2 | scikit-learn 1.6.1 | `scikit-learn` | Minor changes are reported. |
| XGBoost cross-version | XGBoost 2.1.3 | XGBoost 3.0.2 | `xgboost` | Estimator-specific drift is reported. |
| LightGBM cross-version | LightGBM 4.5.0 | LightGBM 4.6.0 | `lightgbm` | Estimator-specific drift is reported. |
| LightGBM sklearn wrapper | sklearn 1.3.2 | sklearn 1.9.0 | `scikit-learn` | Drift beneath the wrapper is reported before load. |
| NumPy relevance | NumPy 1.26.4 | NumPy 2.0.2 | `numpy` | A relevant numerical dependency is reported. |
| joblib relevance | joblib 1.3.2 | joblib 1.4.2 | `joblib` | A relevant serialization dependency is reported. |
| pandas noise control | pandas 2.2.3 | pandas 2.3.1 | None | An unrelated installed-package change is suppressed. |

All other pinned packages in a row were held constant. The sklearn cases held
NumPy 1.26.4, SciPy 1.13.1, and (except for the joblib case) joblib 1.4.2
constant. The XGBoost and LightGBM cases held NumPy, SciPy, and joblib constant.

## What the result establishes

- Modelstamp reports exact version differences, including patch changes.
- Framework-specific packages are selected from the persisted model type.
- LightGBM's sklearn-compatible wrapper also tracks scikit-learn.
- NumPy and joblib are treated as relevant to a scikit-learn pipeline.
- A pandas-only change does not create noise for that pipeline, even when
  pandas is installed and recorded in both environments.

This matrix validates detection and relevance filtering. It does not claim
that every reported version change will alter predictions, nor does it define
semantic compatibility between releases. Model owners must still decide
whether a reported difference is acceptable for their deployment policy.

## Reproduce or extend the matrix

The scenario runner is
[`benchmarks/drift_matrix_case.py`](https://github.com/AnaghaDhekne/modelstamp/blob/main/benchmarks/drift_matrix_case.py),
and the exact environments are defined in
[`.github/workflows/drift-validation.yml`](https://github.com/AnaghaDhekne/modelstamp/blob/main/.github/workflows/drift-validation.yml).

When contributing another case, report:

```text
Scenario:
Save environment:
Check environment:
Expected:
Observed:
Interpretation:
```

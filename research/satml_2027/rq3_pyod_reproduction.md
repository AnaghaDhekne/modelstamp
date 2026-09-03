# Supplementary validation — RQ3 PyOD baseline reproduction

## Purpose

Record an independent re-execution of the SaTML RQ3 baseline using the exact dependency versions already specified by the repository workflow that produced the frozen result.

## Baseline and versions

- Baseline: `pyod.utils.persistence.load(path, trusted=True, strict=True)`
- PyOD: `3.6.5`
- Save/control scikit-learn: `1.7.2`
- Drift scikit-learn: `1.8.0`
- Repository source of version pins: `.github/workflows/pyod-baseline.yml`

PyOD 3.6.5 post-dates the PyOD 3.6.2 security change associated with CVE-2026-15529. The experiment therefore evaluates the post-fix persistence API rather than a pre-fix vulnerable release.

## Re-execution context

Independent re-execution was recorded on `2026-09-03T21:18:38Z` in a clean pinned environment using the experiment protocol in `experiments/pyod_baseline/`.

## Protocol

1. Install Modelstamp together with `scikit-learn==1.7.2` and `pyod==3.6.5`.
2. Create equivalent persisted artifacts using `experiments/pyod_baseline/create_artifacts.py`.
3. Run `experiments/pyod_baseline/run_baseline.py` in the same environment as the control condition.
4. Upgrade scikit-learn to `1.8.0` while leaving PyOD pinned at `3.6.5`.
5. Run the same baseline script in the drift condition.
6. Record both dependency-drift outcomes and whether the serialization backend loader was invoked before the relevant decision.

## Expected outcome

- Modelstamp control: no relevant drift and no deserialization through the verification path.
- Modelstamp drift: relevant dependency drift surfaced without deserialization.
- PyOD control: load succeeds after invoking `joblib.load`.
- PyOD drift: strict dependency policy rejects the mismatch after `joblib.load` has already been invoked.

## Observed outcome

| Condition | Modelstamp | PyOD 3.6.5 |
| --- | --- | --- |
| Control (`scikit-learn==1.7.2`) | `deserialized: false`; no drift reported | `deserialized: true`; no drift; no rejection |
| Drift (`1.7.2 -> 1.8.0`) | `deserialized: false`; drift reported by `check()` | `deserialized: true`; subsequently rejected with dependency-drift `ValueError` |

The independently reproduced observations match the frozen RQ3 result. In the drift condition, the observation probe recorded `loader_calls: ["joblib.load"]` before PyOD's strict-version rejection. A scikit-learn `InconsistentVersionWarning` was also emitted during deserialization, providing an independent indication that reconstruction had already begun before the PyOD dependency-policy decision.

## Interpretation

The result does **not** show that PyOD cannot detect dependency drift. PyOD 3.6.5 surfaces the tested mismatch under `strict=True`. The measured distinction is ordering: Modelstamp exposes the tested dependency evidence through a non-deserializing verification path, whereas PyOD's strict dependency rejection occurs after reconstruction has been invoked.

The result also does **not** establish that Modelstamp is generally safer than PyOD. PyOD's `trusted=True` acknowledgement and its strict dependency checks serve different purposes; RQ3 isolates only the position of dependency-drift evaluation relative to reconstruction.

## Relationship to frozen evidence

This file is a supplementary reproduction record. It does not alter the previously frozen RQ3 outcome or any RQ1-RQ5 counts. Its purpose is to document the exact tested PyOD version and independently confirm that the frozen ordering observation reproduces under the pinned environment.

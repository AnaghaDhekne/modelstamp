# Supplementary record — RQ4 experiment invalidity and correction

Status: **non-frozen; documents invalidation of the original RQ4 execution and
the corrected replacement experiment**

## Original experiment: invalid

During SaTML manuscript preparation, direct re-execution and source/manifest
inspection identified three independent defects in the original controlled
deserialization-boundary experiment.

1. **Invalid load argument.** The script called
   `modelstamp.load(ARTIFACT, strict=True)`, but `load()` has no `strict`
   parameter. The resulting `TypeError` occurred before the intended
   runtime-mismatch gate. A broad `except Exception` incorrectly recorded that
   unrelated exception as the expected rejection.

2. **Wrong sidecar path.** The drift manipulation wrote
   `controlled.joblib.modelstamp.json`, while Modelstamp's manifest path for
   the artifact is `controlled.joblib.manifest.json`. The intended drift was
   therefore not written to the manifest consumed by `check()` or `load()`.

3. **Empty inferred relevance set for the synthetic fixture.** `MarkerOnLoad`
   is defined in `side_effect_fixture`, which is outside Modelstamp's
   predefined package-relevance mappings. The normally saved fixture therefore
   had an empty `relevant_packages` set. Even if the first two defects were
   corrected, a joblib version edit alone would not be evaluated as a relevant
   package mismatch.

Each defect was independently sufficient to prevent the original execution from
establishing the intended RQ4 claim. The prior apparent success was therefore a
false positive and must not be used as evidence.

## Corrected experiment

The corrected experiment isolates RQ4's intended variable: reconstruction
ordering after a controlled relevant-package mismatch has been established.

It:

- saves the controlled `MarkerOnLoad` fixture normally;
- modifies the actual `.manifest.json` sidecar;
- explicitly sets `relevant_packages = ["joblib"]`, rather than relying on
  relevance inference that is outside this synthetic fixture's purpose;
- replaces the recorded joblib version with
  `0.0.0-controlled-drift`;
- calls `modelstamp.check()` first and asserts that exactly the intended
  joblib mismatch is surfaced;
- calls `modelstamp.load(..., on_mismatch="raise")`;
- accepts only `EnvironmentMismatchError` as the expected rejection;
- asserts that the rejection evidence names joblib and that the reconstruction
  marker does not exist; and
- calls direct `joblib.load()` as a positive reconstruction control and
  asserts that the marker is created.

The sentinel save-time version is intentionally distinct from a real installed
joblib version. The current version is read from the captured environment rather
than hardcoded.

## Independent pre-commit re-execution

A corrected candidate was independently executed on 2026-09-03T22:05:07Z before
this repository correction was committed. The run exited successfully. The
precondition surfaced:

`joblib: 0.0.0-controlled-drift -> 1.6.0`

The strict Modelstamp case raised `EnvironmentMismatchError`, named the joblib
mismatch, and did not create the reconstruction marker. Direct `joblib.load()`
created the marker.

This timestamped execution is confirmatory provenance. The repository CI run for
the committed correction is the authoritative post-commit validation.

## Evidence status

The original RQ4 execution is invalidated and must not be cited as supporting
evidence.

RQ4's hypothesis is supported only by the corrected execution and subsequent
validation:

> Under an explicitly established controlled relevant-package mismatch, strict
> Modelstamp loading rejects before the controlled reconstruction side effect,
> whereas direct joblib loading reaches that side effect.

This does not establish automatic relevance inference for the synthetic fixture,
malicious-payload detection, safe deserialization, or general prevention of code
execution.

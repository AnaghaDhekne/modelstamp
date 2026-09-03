# PyOD vs Modelstamp pre-deserialization baseline

This experiment compares **ordering**, not whether either project can detect
dependency drift.

## Question

Can dependency-version evidence be checked before reconstructing the persisted
model object?

The comparison uses the public APIs of both projects:

- Modelstamp: `modelstamp.check(path)`
- PyOD: `pyod.utils.persistence.load(path, trusted=True, strict=True)`

## Protocol

1. In the save environment, fit one scikit-learn model and persist equivalent
   copies with Modelstamp and PyOD.
2. Run a same-environment control.
3. Change scikit-learn to a different supported experiment version.
4. Run the same checks in the drift environment.
5. Record whether drift is reported and whether the serialization backend's
   loader is invoked before the PyOD strict-version decision.

`run_baseline.py` wraps `joblib.load` only as an observation probe. It does
not change the serialized object or PyOD's decision logic. Modelstamp's
`check()` path does not invoke joblib/pickle loading.

## Interpretation

A positive result is **not** "PyOD cannot detect drift." PyOD provides strict
dependency-version checks. The tested distinction is whether comparable
evidence is available through a non-deserializing verification path.

Expected interpretation only after execution:

- Modelstamp control: no relevant drift; no deserialization.
- Modelstamp drift: relevant drift reported; no deserialization.
- PyOD control: load succeeds and necessarily deserializes.
- PyOD drift: strict version policy may reject, but only after the persisted
  envelope has been deserialized.

The generated `results.json` files are workflow artifacts and are not committed
as predeclared results.

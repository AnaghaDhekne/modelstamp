# modelstamp

**Model files with receipts.**

[![Tests](https://github.com/AnaghaDhekne/modelstamp/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/AnaghaDhekne/modelstamp/actions/workflows/test.yml?query=branch%3Amain+event%3Apush)
[![Python 3.8–3.13](https://img.shields.io/badge/python-3.8%E2%80%933.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/AnaghaDhekne/modelstamp/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22036020.svg)](https://doi.org/10.5281/zenodo.22036020)

[Documentation](https://anaghadhekne.github.io/modelstamp/) ·
[Benchmarks](https://github.com/AnaghaDhekne/modelstamp/blob/main/BENCHMARKS.md) ·
[Security policy](https://github.com/AnaghaDhekne/modelstamp/security/policy)

`modelstamp` adds a verifiable environment manifest to persisted Python machine
learning models. It keeps the familiar pickle or joblib workflow while making
dependency changes and artifact corruption visible before deserialization.

Loading a persisted model under different dependency versions is unsupported
and may fail or behave differently. The scikit-learn documentation therefore
recommends preserving the training environment alongside the model. `modelstamp`
packages that practice into a small API.

## Why modelstamp?

A normal `model.pkl` remembers the fitted object, but not the environment that
made it work. `modelstamp` adds the missing receipt:

- **Integrity:** detect truncated, replaced, or corrupted artifacts.
- **Compatibility:** identify Python and relevant dependency changes.
- **Traceability:** record model details, metadata, time, and optional Git state.
- **Familiarity:** keep using pickle or joblib through `save()` and `load()`.

## Installation

```bash
pip install modelstamp
```

Install joblib support explicitly when scikit-learn is not already installed:

```bash
pip install "modelstamp[joblib]"
```

## Save and load

```python
import modelstamp as ms

manifest = ms.save(
    model,
    "model.joblib",
    metadata={"validation_roc_auc": 0.883},
)

model, manifest = ms.load("model.joblib")
```

Saving creates two files:

```text
model.joblib
model.joblib.manifest.json
```

The manifest records:

- SHA-256 and byte size of the artifact
- pickle or joblib serialization backend
- model class and scikit-learn pipeline components

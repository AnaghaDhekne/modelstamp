# modelstamp


**Model files with receipts.**


[![Tests](https://github.com/AnaghaDhekne/modelstamp/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/AnaghaDhekne/modelstamp/actions/workflows/test.yml?query=branch%3Amain+event%3Apush)
[![Python 3.8–3.13](https://img.shields.io/badge/python-3.8%E2%80%933.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/AnaghaDhekne/modelstamp/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22047771.svg)](https://doi.org/10.5281/zenodo.22047771)
[![arXiv](https://img.shields.io/badge/arXiv-2609.01781-b31b1b.svg)](https://arxiv.org/abs/2609.01781)


![Modelstamp detecting a tampered machine-learning artifact](https://raw.githubusercontent.com/AnaghaDhekne/modelstamp/main/docs/assets/modelstamp_demo.gif)


**Pre-deserialization verification for persisted Python machine-learning
artifacts: detect integrity failures and relevant dependency drift before
loading pickle or joblib models.**


```bash
pip install modelstamp
```


```python
import modelstamp as ms


model = {"feature_names": ["age", "income"], "weights": [0.3, 0.7]}
ms.save(model, "model.pkl")
restored, manifest = ms.load("model.pkl", on_mismatch="raise")
print(restored, manifest.relevant_packages)
```


[Documentation](https://anaghadhekne.github.io/modelstamp/) ·
[Benchmarks](https://github.com/AnaghaDhekne/modelstamp/blob/main/BENCHMARKS.md) ·
[Drift matrix](https://anaghadhekne.github.io/modelstamp/drift-benchmarks/) ·
[Research use & citation](https://anaghadhekne.github.io/modelstamp/research-use/) ·
[Research & adoption](https://anaghadhekne.github.io/modelstamp/research-adoption/) ·
[Preprint](https://arxiv.org/abs/2609.01781) ·
[Security policy](https://github.com/AnaghaDhekne/modelstamp/security/policy)


`modelstamp` is a lightweight Python model-persistence layer that records an
artifact's SHA-256 digest, runtime metadata, and artifact-specific dependencies.
It verifies integrity, compares environments, and can authenticate manifests
with HMAC before deserialization. It complements lock files and model registries;
it does not make untrusted pickle or joblib payloads safe to execute.


Loading a persisted model under different dependency versions is unsupported
and may fail or behave differently. The
[scikit-learn model-persistence documentation](https://scikit-learn.org/stable/model_persistence.html)
therefore recommends preserving the training environment alongside the model.
`modelstamp` packages that practice into a small API.


## Research evidence


The [current arXiv preprint](https://arxiv.org/abs/2609.01781) evaluates 14
controlled environment-drift scenarios, eight controlled trust-boundary

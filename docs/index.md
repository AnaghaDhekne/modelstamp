# modelstamp

**Model files with receipts.**

`modelstamp` verifies persisted Python machine-learning models, detects relevant
dependency drift, and records reproducible environment metadata. Its sidecar
manifest connects each artifact to its checksum, serialization backend, model
details, runtime dependencies, and caller-provided metadata.

```bash
pip install modelstamp
```

```python
import modelstamp as ms

ms.save(model, "model.joblib", metadata={"validation_auc": 0.91})
model, manifest = ms.load("model.joblib")
```

The artifact is hashed before deserialization. Dependency changes can warn or
block loading, and optional HMAC authentication protects the model/manifest
pair against unauthorized replacement.

The [Modelstamp preprint](https://arxiv.org/abs/2609.01781) documents the threat
model, 14 controlled environment-drift scenarios, eight trust-boundary
scenarios, and artifact-size scaling results. Cite it as:

> Anagha Dhekne. "Modelstamp: Pre-Deserialization Verification of
> Machine-Learning Artifacts and Runtime Environment State." arXiv:2609.01781,
> 2026.

Software citation metadata and the archived release remain available through
[`CITATION.cff`](https://github.com/AnaghaDhekne/modelstamp/blob/main/CITATION.cff)
and the [Zenodo software DOI](https://doi.org/10.5281/zenodo.22047771).

## Research evidence

The [current Modelstamp preprint](https://arxiv.org/abs/2609.01781) evaluates 14
controlled environment-drift scenarios, eight controlled trust-boundary
scenarios, and verification scaling from 10 MiB to 1 GiB.

Two experiments added to the repository after that preprint extend the evidence
base: the
[PyOD ordering baseline](https://github.com/AnaghaDhekne/modelstamp/blob/main/experiments/pyod_baseline/README.md)
and the
[controlled deserialization-boundary experiment](https://github.com/AnaghaDhekne/modelstamp/blob/main/experiments/deserialization_boundary/README.md).
They test verification ordering and whether a pre-load rejection can stop before
a harmless reconstruction side effect occurs. They do not claim that Modelstamp
detects malicious models or makes pickle/joblib safe for untrusted artifacts.

Start with the [quick start](quickstart.md), then review the
[security boundary](security.md) before loading persisted Python objects.
The [Research & Adoption page](research-adoption.md) is the canonical record of
papers, reproducible evidence, independent use, citations, and community review.

## Choose a guide

- [Detect dependency drift](dependency-drift.md) without loading the model.
- [Verify a joblib artifact](verify-joblib.md) before deserialization.
- Add [artifact checks to CI/CD](ci.md).
- Review the CI-enforced [dependency-drift validation matrix](drift-benchmarks.md).
- Examine the runnable [model-risk trust-boundary case study](model-risk-case-study.md).
- Understand [when to use Modelstamp](comparisons.md) with lock files,
  registries, `skops.io`, or ONNX.
- Run the repository's [complete examples](examples.md).

Releases are published from protected `v*` tags using PyPI Trusted Publishing.
Maintainers can use the [release checklist](releasing.md) for the protected
`main`-to-PyPI workflow.

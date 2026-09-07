# State of the field and Modelstamp's scope

Modelstamp is a focused verification layer for persisted Python ML artifacts.
It complements environment managers, model registries, safer serialization
formats, and public signing systems rather than replacing them.

This comparison was reviewed on **2026-09-06** from official project
documentation. “Not documented” means only that the reviewed source does not
describe the capability; it is not proof of absence. The machine-readable
[claim ledger](https://github.com/AnaghaDhekne/modelstamp/tree/main/research/state_of_field)
records the sources and review method.

This page evaluates Sigstore as a general software-artifact signing system. The
SaTML manuscript separately discusses OpenSSF Model Signing (OMS), a
model-specific specification that uses the Sigstore Bundle Format and can use
Sigstore as one of several signing options. OMS and Sigstore are related, not
synonyms; the Sigstore row below is not an evaluation of OMS. See the official
[OpenSSF OMS overview](https://openssf.org/blog/2025/06/25/an-introduction-to-the-openssf-model-signing-oms-specification/).

## Factual comparison

| Tool or approach | Primary problem documented by the project | Overlap with Modelstamp | Material difference |
|---|---|---|---|
| scikit-learn pickle/joblib guidance | Persist fitted Python objects and record enough surrounding information to reproduce results | Python-object persistence and dependency-version awareness | Cross-version loading is unsupported; the guidance does not define an artifact-bound, non-deserializing policy gate. [Source](https://scikit-learn.org/stable/model_persistence.html) |
| joblib | Efficient persistence and reconstruction of Python objects, including NumPy data | Modelstamp can retain joblib artifacts | `joblib.load` relies on pickle and can execute arbitrary code; artifact integrity and dependency policy are outside the reviewed persistence API. [Source](https://joblib.readthedocs.io/en/stable/generated/joblib.load.html) |
| skops.io | More secure sklearn-oriented persistence without pickle, with inspection of unknown types before construction | Pre-load inspection and concern for persisted-model trust | It uses a different, deliberately narrower format, cannot persist arbitrary Python code, and cannot remove sklearn's cross-version compatibility limits. [Source](https://skops.readthedocs.io/en/stable/persistence.html) |
| ONNX | Portable serialized computation graphs for framework-independent inference | Reduces dependence on the original training environment | It represents supported operators and inference behavior, not the original arbitrary fitted Python object. [Source](https://onnx.ai/onnx/intro/concepts.html) |
| PyOD persistence | A versioned joblib envelope with dependency drift warnings, strict rejection, and limited sklearn compatibility repair | Closest overlap: persisted object plus recorded dependency versions and strict policy | Its documented metadata path unpickles the model; Modelstamp's tested distinction is a separate check path that does not reconstruct it. [Source](https://pyod.readthedocs.io/en/latest/model_persistence.html) |
| MLflow Models and Model Registry | Package models with dependencies; manage versions, aliases, tags, source runs, and deployment organization | Environment metadata and model lifecycle | It is a broader packaging/tracking system. The reviewed docs do not specify Modelstamp's file-local digest-plus-runtime pre-load check. [Dependencies](https://mlflow.org/docs/latest/ml/model/dependencies/) · [Registry](https://mlflow.org/docs/latest/ml/model-registry/workflow/) |
| DVC | Git-oriented versioning of data and model artifacts, pipelines, experiments, and remote storage | Artifact history, retrieval, and reproducible workflow context | It treats model files as versioned artifacts rather than defining serializer-aware runtime compatibility before model reconstruction. [Source](https://dvc.org/doc/user-guide) |
| Sigstore | Identity-based signing and verification of software artifacts with transparency logging | Strong artifact authenticity and integrity | It does not decide which Python ML dependencies are relevant or orchestrate a model loader. Modelstamp's current shared-secret HMAC is not a substitute for Sigstore's public-verification model. [Source](https://docs.sigstore.dev/about/overview/) |

## The narrower Modelstamp problem

Modelstamp keeps an existing pickle or joblib artifact, creates a sidecar that
binds a digest to selected runtime evidence, and exposes verification before
deserialization. Its strict load path can reject a known integrity or dependency
condition before invoking the serializer.

That combination matters only when retaining the Python object is a requirement.
If the model can be represented by ONNX, or if skops supports the full object
graph, those formats can reduce the loading risk rather than merely gate it.
Modelstamp does **not** make pickle/joblib safe for untrusted input.

## Could this have been an upstream contribution?

The following is **maintainer analysis**, not a claim made by the compared
projects.

| Possible upstream home | What could plausibly be contributed | Why that alone may not satisfy Modelstamp's scope |
|---|---|---|
| joblib or scikit-learn | Optional environment metadata, warnings, or a companion verification API | A generic serializer or estimator library would need to adopt model-relevance policy, sidecar lifecycle, signing semantics, and support responsibilities beyond its current persistence guidance. Modelstamp also targets third-party estimator ecosystems. |
| skops | Runtime metadata and stricter cross-version checks | This would be valuable for `.skops` files, but would not preserve existing pickle/joblib artifacts or arbitrary fitted Python objects. Integration remains complementary. |
| PyOD | A header-only inspection API and artifact authentication | PyOD is the closest technical home for the tested PyOD detector case. Modelstamp additionally aims to be estimator-library-neutral and file-local. The existing controlled experiment should remain the evidence for the ordering distinction. |
| MLflow | A model flavor, plugin, or deployment hook that invokes Modelstamp verification | This could provide a useful integration, but users of standalone files would inherit an unnecessary tracking/registry stack if it were the only implementation. |
| DVC | A pipeline stage or check that runs Modelstamp | DVC can orchestrate and version the evidence, but the model-relevance and serializer-boundary logic would still need a dedicated component. |
| ONNX | Additional metadata conventions or validation | It would apply after accepting graph conversion and would not cover the requirement to retain arbitrary Python model state. |
| Sigstore | Model artifact signing conventions | Sigstore can strengthen publisher identity and public verification, but a separate layer must still capture dependency evidence and decide whether to invoke a Python loader. |

The practical conclusion is not that upstream contribution was impossible.
Several integrations are sensible. A separate small package was justified by
the intersection of three constraints: ordinary file workflows, multiple
Python estimator ecosystems, and a policy decision before deserialization.

## Choosing a tool

- Choose skops.io or ONNX when changing format is acceptable and their supported
  model surface fits.
- Choose MLflow or DVC when lifecycle, lineage, experiment management, or remote
  artifact organization is the main requirement.
- Choose Sigstore when public publisher identity and independently verifiable
  signatures are required.
- Add Modelstamp when a trusted pickle/joblib workflow must retain its Python
  object and needs file-local integrity and relevant dependency checks before
  loading.
- Combine them when requirements cross these boundaries; they solve different
  layers of the problem.

## Claim boundaries

Modelstamp does not detect malware, guarantee semantic compatibility when
versions match, capture a complete execution environment, prevent replay by
itself, provide public-key identity, or replace experiment tracking and model
registries. The [reproducible research evidence](reproducible-evidence.md)
documents the narrower tested claims.

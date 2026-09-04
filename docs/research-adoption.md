# Research and adoption

This page is the canonical public record of Modelstamp research outputs,
independent use, integrations, citations, and community review. Entries are
linked to public evidence and labeled by source so that maintainer-produced
evaluation is not mistaken for independent adoption.

**Last evidence review:** 4 September 2026

## Evidence status

| Evidence type | Publicly verified status |
| --- | --- |
| Papers about Modelstamp | 1 maintainer-authored preprint |
| Archived software releases | Zenodo software record available |
| Reproducible evaluations | Public benchmarks, validation matrices, and follow-up experiments |
| Independent repositories or integrations | None reported yet |
| Independent research users | None reported yet |
| Independent citations | None found yet |
| External technical issues or pull requests | None reported yet |
| Accepted or delivered talks | None reported yet |

“None reported yet” means that no qualifying public evidence was identified by
the review date. It is not a claim about private use, package downloads, or
activity that cannot be independently checked.

## Papers and software records

### Modelstamp preprint

- **Record:** [Modelstamp: Pre-Deserialization Verification of
  Machine-Learning Artifacts and Runtime Environment State](https://arxiv.org/abs/2609.01781)
- **Authors and provenance:** Anagha Dhekne; maintainer-authored
- **Published:** arXiv, 2026
- **Evidence covered:** 14 controlled environment-drift scenarios, eight
  controlled trust-boundary scenarios, and an artifact-size scaling benchmark
  from 10 MiB to 1 GiB

### Archived software

- **Record:** [Zenodo software DOI](https://doi.org/10.5281/zenodo.22047771)
- **Citation metadata:** [`CITATION.cff`](https://github.com/AnaghaDhekne/modelstamp/blob/main/CITATION.cff)
- **Source and releases:** [Modelstamp on GitHub](https://github.com/AnaghaDhekne/modelstamp)

## Reproducible project evidence

The resources in this section are produced and maintained by the Modelstamp
project. They support reproducibility and inspection, but they do not count as
independent adoption.

| Evidence | What can be reproduced | Source |
| --- | --- | --- |
| Dependency-drift matrix | Relevant dependency changes, unchanged environments, and unrelated-package noise controls | [Documentation](drift-benchmarks.md) |
| Trust-boundary matrix | Intended detections and documented limitations, including shared-key forgery and replay | [Case study](model-risk-case-study.md) · [Runnable example](https://github.com/AnaghaDhekne/modelstamp/blob/main/examples/trust_boundary_matrix.py) |
| Verification benchmark | Median verification time across 10 MiB, 100 MiB, and 1 GiB artifacts | [Benchmark results](benchmarks.md) · [Benchmark script](https://github.com/AnaghaDhekne/modelstamp/blob/main/benchmarks/benchmark_verify.py) |
| PyOD baseline | The point at which dependency-version evidence is evaluated relative to model reconstruction | [Experiment](https://github.com/AnaghaDhekne/modelstamp/tree/main/experiments/pyod_baseline) |
| Deserialization-boundary experiment | Whether a relevant pre-load rejection occurs before a controlled reconstruction side effect | [Experiment](https://github.com/AnaghaDhekne/modelstamp/tree/main/experiments/deserialization_boundary) · [correction record](https://github.com/AnaghaDhekne/modelstamp/blob/main/research/satml_2027/rq4_correction_record.md) |

These evaluations characterize Modelstamp as a pre-deserialization integrity
and represented-environment verification control. They do not show that
Modelstamp detects malicious models, makes pickle or joblib safe for untrusted
artifacts, or provides public-key publisher authentication.

## Independent adoption and citations

No independent public repository, integration, research workflow, external
user report, or citation has been verified yet. This section will list only
uses with a durable public source, such as a repository, paper, archived
workflow, issue, pull request, or published talk material.

PyPI download counts are not treated as adoption evidence because they do not
identify a user, workflow, successful integration, or research outcome.

## Community review and discovery

The following records may lead to review or adoption, but are not counted as
independent use unless they produce qualifying public evidence.

| Activity | Status on 4 September 2026 | Record |
| --- | --- | --- |
| pyOpenSci pre-submission inquiry | Open; no response recorded | [Inquiry #343](https://github.com/pyOpenSci/software-submission/issues/343) |
| Awesome MLOps listing proposal | Open; no response recorded | [Pull request #253](https://github.com/kelvins/awesome-mlops/pull/253) |
| Real-workflow feedback request | Open; maintainer comments only | [Modelstamp issue #18](https://github.com/AnaghaDhekne/modelstamp/issues/18) |

## Research workflow examples

Modelstamp can be evaluated in research workflows where a fitted Python model
must be transferred, archived, rechecked, or reproduced later. Examples
include:

- attaching a manifest to a model artifact deposited with replication code;
- checking dependency drift before reproducing an earlier analysis;
- verifying an artifact in CI before a benchmark or evaluation job loads it;
- recording model class, relevant package versions, Git state, and study
  metadata alongside a serialized estimator;
- authenticating an artifact/manifest pair when producer and verifier share a
  protected HMAC key.

These are supported use cases, not claims of independent use. See the
[quick start](quickstart.md), [CI/CD guide](ci.md), and
[security boundary](security.md) before applying them.

## Report a public use

If you use Modelstamp in a paper, repository, integration, course, benchmark,
or talk, add a comment to the
[public feedback issue](https://github.com/AnaghaDhekne/modelstamp/issues/18)
or open a new issue. Include:

- a durable public link;
- the model framework, serializer, Python version, and operating system;
- what Modelstamp was used to verify;
- whether the report is independent of the Modelstamp maintainer; and
- any issue, limitation, or change produced by the use.

Do not publish proprietary models, datasets, credentials, signing keys, or
sensitive manifests. After verification, qualifying evidence will be added to
this page with its source and date.

## Inclusion policy

An entry must be publicly accessible, attributable, and specific enough to
verify. The page distinguishes:

- **maintainer-produced evidence** — papers, experiments, examples, and project
  documentation produced by the Modelstamp maintainer;
- **external feedback** — a public technical report, issue, or pull request
  from someone outside the project, whether or not it leads to adoption; and
- **independent adoption** — external use in a repository, research workflow,
  integration, paper, or talk with public evidence.

Outreach messages, impressions, stars, clones, and anonymous download counts
are not counted as indepent adoption. Entries are updated when their public
status changes; superseded or corrected evidence retains a link to its
provenance record.

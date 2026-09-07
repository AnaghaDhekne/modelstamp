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

## Research-adoption funnel

This funnel tracks observable progress from a specific outreach record to
repeat use. Counts include only publicly verifiable evidence reviewed on the
date above. They are evidence counts, not estimates of total users or conversion
rates.

### Anonymous distribution activity

[PyPI Stats](https://pypistats.org/packages/modelstamp) reported the following
Modelstamp download activity when retrieved on **7 September 2026**:

| Window | Downloads |
| --- | ---: |
| Last day | 14 |
| Last week | 142 |
| Last month | 689 |

These counts are a top-of-funnel reach indicator, not verified installs or
users. They can include automated CI jobs, mirrors, scanners, repeated downloads
by one user, and downloads that never led to installation or use. The windows
overlap and must not be summed. Because the source updates daily, every future
change must record its retrieval date rather than silently replacing the values.

### Verified adoption stages

| Stage | Qualification rule | Verified count | Current evidence |
| --- | --- | ---: | --- |
| Contacts | A directed, attributable request for review, listing, testing, or integration with a durable public record | 2 | pyOpenSci inquiry #343; Awesome MLOps PR #253 |
| Replies | A substantive response from someone outside the Modelstamp project to a counted contact | 0 | None verified |
| Installs or trials | A public report or reproducible workflow showing that an external person installed or ran Modelstamp | 0 | None verified |
| Technical feedback | External, Modelstamp-specific findings, questions, issues, or patches resulting from a trial | 0 | None verified |
| Repeat use | Evidence that the same external user or project used Modelstamp in a later run, release, study, or workflow | 0 | None verified |

The stages are progressive for a single adoption record: a reply does not imply
an install, and an install does not imply successful or repeated use. A record
can therefore appear at its highest verified stage only after links establish
the preceding stages. Rejections and negative technical findings still count at
the appropriate reply or feedback stage; the funnel measures engagement, not
only favorable outcomes.

Anonymous package downloads are reported separately above but excluded from the
verified stages because they cannot establish who used the package or what
happened. Repository views, stars, impressions, and maintainer activity are also
excluded. The maintainer-created feedback issue is an open invitation, not a
directed contact, external reply, or adoption event.

### Funnel record ledger

| Record | Contact | Reply | Install or trial | Feedback | Repeat use |
| --- | --- | --- | --- | --- | --- |
| [pyOpenSci pre-submission inquiry #343](https://github.com/pyOpenSci/software-submission/issues/343) | Verified | None recorded | None recorded | None recorded | None recorded |
| [Awesome MLOps listing PR #253](https://github.com/kelvins/awesome-mlops/pull/253) | Verified | None recorded | None recorded | None recorded | None recorded |

When evidence changes, update both the summary count and this ledger in the same
commit. Add the dated public link, identify whether the actor is independent of
the project, and advance only the stages supported by that source. Preserve
closed, rejected, or superseded records instead of deleting them so conversion
and non-conversion outcomes remain auditable.

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
| Definitive sklearn version-drift experiment | Baseline reconstruction and warning behavior compared with Modelstamp's non-deserializing check and strict pre-load rejection | [Protocol and reproduction](sklearn-version-drift.md) · [Experiment source](https://github.com/AnaghaDhekne/modelstamp/tree/main/experiments/sklearn_version_drift) |
| Unified drift and trust-boundary evidence | Fourteen pinned dependency-drift cases and eight integrity/authentication cases with machine-readable observations | [Protocol and reproduction](reproducible-evidence.md) · [Experiment source](https://github.com/AnaghaDhekne/modelstamp/tree/main/experiments/reproducible_evidence) |
| PyOD baseline | The point at which dependency-version evidence is evaluated relative to model reconstruction | [Experiment](https://github.com/AnaghaDhekne/modelstamp/tree/main/experiments/pyod_baseline) |
| State-of-the-field comparison | Official-source claims about adjacent persistence, registry, versioning, and signing tools | [Evidence ledger](https://github.com/AnaghaDhekne/modelstamp/tree/main/research/state_of_field) |
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
are not counted as independent adoption. Entries are updated when their public
status changes; superseded or corrected evidence retains a link to its
provenance record.

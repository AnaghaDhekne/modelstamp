# Pre-submission artifact contents

Status: **repository-side source manifest; anonymous artifact not yet assembled**

This file is the hard gate for assembling the anonymized Open Science artifact.
It maps each manuscript claim to the exact version-controlled material needed to
reproduce or audit it. Generated models, manifests, virtual environments, and
run outputs are deliberately absent from Git; the listed runners create them.

The frozen interpretation and numerical claims are in the SaTML evidence
freeze. A protocol or test supports only the bounded claim named below; its
presence here does not broaden that claim.

## Claim-to-file inventory

<!-- artifact-paths:start -->

| Claim | Evidence role | Exact repository path |
| --- | --- | --- |
| RQ1--RQ5 | Frozen outcomes, numerical claims, and interpretation guardrails | `research/satml_2027/evidence_freeze.md` |
| RQ1 | Rerunnable protocol, pins, expected sets, and scenario identifiers | `experiments/reproducible_evidence/scenarios.json` |
| RQ1 | Isolated-environment runner and assertions | `experiments/reproducible_evidence/run_evidence.py` |
| RQ1 | Independent reproduction instructions and acceptance criteria | `experiments/reproducible_evidence/README.md` |
| RQ1 | CI execution of the bundled protocol | `.github/workflows/reproducible-research-evidence.yml` |
| RQ1 | Legacy per-scenario save/check implementation | `benchmarks/drift_matrix_case.py` |
| RQ1 | Independently declared 14-case CI matrix | `.github/workflows/drift-validation.yml` |
| RQ1 | Reader-facing matrix and reproduction notes | `docs/drift-benchmarks.md` |
| RQ2: all eight controlled trust-boundary cases matched their predefined accept/reject outcomes | Executable eight-scenario demonstration | `examples/trust_boundary_matrix.py` |
| RQ2 | Unit coverage for core integrity and authentication behavior | `tests/test_core.py` |
| RQ2 | Unit coverage for pair swaps, shared-key replacement, and replay boundaries | `tests/test_trust_boundaries.py` |
| RQ2 | Independent eight-case CI check | `.github/workflows/trust-boundary-validation.yml` |
| RQ3: both systems surfaced the pinned drift, but only the tested Modelstamp check path did so before reconstruction | Protocol and interpretation boundary | `experiments/pyod_baseline/README.md` |
| RQ3 | Exact experiment dependencies | `experiments/pyod_baseline/requirements.txt` |
| RQ3 | Equivalent artifact construction | `experiments/pyod_baseline/create_artifacts.py` |
| RQ3 | Symmetric loader tracing, observations, and assertions | `experiments/pyod_baseline/run_baseline.py` |
| RQ3 | CI execution and retained generated outputs | `.github/workflows/pyod-baseline.yml` |
| RQ3 | Independent pinned re-execution record | `research/satml_2027/rq3_pyod_reproduction.md` |
| RQ4: strict Modelstamp rejection preceded the controlled reconstruction side effect | Corrected protocol and limitations | `experiments/deserialization_boundary/README.md` |
| RQ4 | Controlled harmless reconstruction fixture | `experiments/deserialization_boundary/side_effect_fixture.py` |
| RQ4 | Corrected runner, precondition, exception, and marker assertions | `experiments/deserialization_boundary/run_experiment.py` |
| RQ4 | CI execution of the corrected experiment | `.github/workflows/deserialization-boundary.yml` |
| RQ4 | Invalidity record, correction provenance, and authoritative claim boundary | `research/satml_2027/rq4_correction_record.md` |
| RQ5: warm-cache verification scaled from 0.032 s at 10 MiB to 3.334 s at 1 GiB in the reported environment | Benchmark implementation | `benchmarks/benchmark_verify.py` |
| RQ5 | Reproduction command, environment, protocol, and recorded results | `BENCHMARKS.md` |
| RQ5 | Reader-facing interpretation boundary | `docs/benchmarks.md` |
| Supplementary design property: the opened artifact that was verified is the stream passed to deserialization | Exact regression test, separate from the eight RQ2 cases | `research/satml_2027/verified_open_file_validation.md` |
| All RQs | Public overview of the rerunnable evidence bundle | `docs/reproducible-evidence.md` |
| Artifact gate | Offline check that every mapped path exists and the required claims are represented | `research/validate_artifact_contents.py` |

<!-- artifact-paths:end -->

The same-size tampering regression in the core tests is useful supporting
coverage, but it is not a ninth RQ2 scenario. Likewise, the standalone
scikit-learn 1.5.2 to 1.6.1 experiment elaborates RQ1's existing
`sklearn-minor` case; it is not an additional RQ1 finding.

## Assembly gate

Do not describe an anonymized artifact as available until every item below is
complete:

1. Copy only the mapped evidence sources and the minimum package source needed
   by their runners into a clean staging directory.
2. Apply the venue's anonymization policy to names, repository links, DOI and
   release metadata, Git history, and generated workflow metadata.
3. Run `python research/validate_artifact_contents.py` in the staged tree.
4. Reproduce RQ1--RQ5 from the clean staged tree and compare the observations
   with the frozen evidence and correction record.
5. Confirm that no credentials, private data, local paths, generated virtual
   environments, or stale experiment outputs are present.
6. Generate checksums for the final archive and record the commit used to build
   it outside the anonymized archive when required by the review policy.

Until those checks pass, manuscript language should refer to the repository
protocols, not to a completed anonymous bundle.

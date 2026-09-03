# SaTML 2027 evidence freeze

Status: **frozen for manuscript drafting**

This document is the canonical claim-to-evidence map for the SaTML manuscript.
It separates controlled validation outcomes from statistical accuracy claims
and keeps the two newer pre-deserialization experiments distinct from the
original three-RQ evaluation.

## RQ1 — Selected environment drift

Question: can selected model-relevant dependency differences be surfaced before
deserialization while selected unrelated environmental changes are suppressed?

The CI matrix contains **14 controlled scenarios**. All 14 are expected-outcome
validation cases, not samples from a population and not an accuracy estimate.

| Scenario | Controlled change | Frozen observed relevant change |
|---|---|---|
| sklearn patch | 1.5.1 -> 1.5.2 | scikit-learn |
| sklearn minor | 1.5.2 -> 1.6.1 | scikit-learn |
| XGBoost | 2.1.3 -> 3.0.2 | xgboost |
| LightGBM | 4.5.0 -> 4.6.0 | lightgbm |
| LightGBM sklearn wrapper | sklearn 1.3.2 -> 1.9.0 | scikit-learn |
| NumPy relevance | 1.26.4 -> 2.0.2 | numpy |
| joblib relevance | 1.3.2 -> 1.4.2 | joblib |
| pandas noise | 2.2.3 -> 2.3.1 | none |
| identical environment | same pinned stack | none |
| SciPy relevance | 1.12.0 -> 1.13.1 | scipy |
| requests noise | 2.31.0 -> 2.32.3 | none |
| noisy environment | six unrelated package changes | none |
| noise + relevant drift | same noise + sklearn 1.5.1 -> 1.5.2 | scikit-learn |
| CatBoost | 1.2.7 -> 1.2.8 | catboost |

**Frozen finding:** all 14 controlled scenarios matched their predefined
expected package-difference sets.

Do not describe 14/14 as accuracy, recall, detection rate, or general coverage.

## RQ2 — Trust boundaries

Question: which tested integrity/authentication conditions are rejected and
which remain possible under the stated trust model?

| Scenario | Frozen expected/observed behavior |
|---|---|
| artifact changed; manifest unchanged | reject — SHA-256 mismatch |
| artifact + unsigned manifest replaced | accept |
| unsigned manifest hash edited | reject — SHA-256 mismatch |
| unsigned identity metadata edited | accept |
| signed pair replaced by unsigned pair | reject — manifest not signed |
| replacement signed with untrusted key | reject — invalid signature |
| replacement signed by shared-key holder | accept |
| older valid signed pair replayed | accept |

**Frozen finding:** all eight controlled scenarios behaved according to the
predefined trust-model expectation.

The four accepted cases are demonstrated non-guarantees, not missed detections.
Do not describe 8/8 as attack-detection accuracy.

## RQ3 — Pre-deserialization ordering baseline

Question: can comparable dependency-version evidence be surfaced without
reconstructing the serialized model?

The merged PyOD baseline uses a same-environment control and a scikit-learn
1.7.2 -> 1.8.0 drift condition.

| System / condition | Drift surfaced | Serialized model reconstructed first |
|---|---:|---:|
| Modelstamp control | no | no |
| PyOD control | no | yes |
| Modelstamp drift | yes | no |
| PyOD strict drift | yes | yes |

**Frozen finding:** both tested systems can surface recorded dependency-version
differences. In the tested public APIs, Modelstamp's check path does so without
model reconstruction, while PyOD's strict persistence load path invokes
joblib deserialization before its dependency-version decision.

Do not claim that PyOD cannot detect drift.

## RQ4 — Consequence of the deserialization boundary

Question: when a relevant mismatch is sufficient for rejection, can verification
stop before a controlled reconstruction side effect occurs?

The merged experiment uses a deliberately controlled fixture whose reconstruction
creates only a temporary marker file.

| Path | Relevant drift condition | Rejected before reconstruction | Marker created |
|---|---:|---:|---:|
| Modelstamp strict load | yes | yes | no |
| direct joblib load | not applicable to joblib policy | no | yes |

**Frozen finding:** under the controlled mismatch, Modelstamp's strict path
rejected without triggering fixture reconstruction; direct joblib
deserialization reconstructed the fixture and created the marker.

This demonstrates an ordering consequence only. It does **not** establish that
Modelstamp detects malware, makes pickle/joblib safe, or prevents arbitrary code
execution after deserialization begins.

## RQ5 — Verification scaling

The existing benchmark isolates `modelstamp.verify()` from deserialization,
warms filesystem caches once per artifact size, performs three measured runs,
and reports the median.

| Artifact size | Median verification time | Throughput |
|---:|---:|---:|
| 10 MiB | 0.032 s | 311.6 MiB/s |
| 100 MiB | 0.326 s | 307.1 MiB/s |
| 1024 MiB (1 GiB) | 3.334 s | 307.1 MiB/s |

**Frozen finding:** in the reported benchmark environment, verification time
increased from 0.032 s at 10 MiB to 3.334 s at 1 GiB while measured throughput
remained approximately 307–312 MiB/s.

Do not generalize the absolute timings to other CPUs, storage systems, cold
caches, or network filesystems.

## Manuscript-safe headline results

The following are safe to carry into drafting:

1. The 14 controlled environment-drift scenarios matched their predefined
   expected package-difference sets.
2. The eight controlled trust-boundary scenarios matched the stated guarantees
   and non-guarantees.
3. The PyOD baseline showed an experimentally observable ordering distinction:
   both systems surfaced the tested dependency drift, but only Modelstamp's
   tested check path did so without reconstructing the model first.
4. The controlled marker experiment showed that a verification condition known
   before deserialization can stop Modelstamp's strict load before fixture
   reconstruction.
5. Verification scaled approximately with artifact size in the reported
   benchmark, with measured throughput around 307–312 MiB/s.

## Claim guardrails

The manuscript must not claim that Modelstamp:

- makes pickle or joblib safe for untrusted artifacts;
- determines whether serialized content is malicious;
- guarantees semantic model compatibility when versions match;
- captures the complete execution environment;
- prevents replay without an external freshness policy;
- resists a holder of the trusted HMAC secret;
- establishes public publisher identity;
- outperforms PyOD on drift detection accuracy.

Any new number or stronger claim added after this freeze must be linked to a
reproducible experiment before it enters the manuscript.

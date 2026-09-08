# JOSS 2026 scope and readiness baseline

**Baseline date:** 8 September 2026  
**Policy snapshot reviewed:** 8 September 2026  
**Status:** Not ready for submission

This document freezes Modelstamp's current evidence against the 2026 Journal
of Open Source Software (JOSS) scope and pre-review criteria. It is a planning
and audit record, not an assertion that JOSS has determined the project to be
in scope. The live policy must be checked again before submission.

## Policy basis

The official [JOSS submission requirements](https://joss.readthedocs.io/en/latest/submitting.html)
reviewed on the date above require, among other things:

- an OSI-licensed, browsable, feature-complete research-software project;
- more than six months of public repository history, with active and iterative
  development spanning that period;
- demonstrated research use rather than only prospective use or promotion;
- good open-source practice, including tests, CI, documentation, releases or a
  changelog, contribution pathways, and a meaningful public history;
- meaningful human problem framing, design decisions, and architectural
  judgment; and
- disclosure of generative-AI tools, versions, use locations, and scope, plus
  confirmation that the human authors reviewed and validated the output and
  made the core design decisions.

The official [JOSS scope overview](https://joss.theoj.org/about#scope--submission-requirements)
also excludes minor utilities, thin clients, single-function packages, and
software without an obvious research application or demonstrated research
impact.

These requirements are summarized here to drive project decisions. The linked
official pages, not this snapshot, control at submission time.

## Public-development chronology

The following facts are reproducible from the repository's Git objects and
tags at commit `394bf1c` on the baseline date.

| Evidence | Observed state | Reproduction |
| --- | --- | --- |
| First commit | `ceac80c`, 20 August 2026, “Initial modelstamp release” | `git log --reverse --format='%H %aI %s'` |
| First code, tests, and CI | Separate commits on 20 August 2026 immediately after the initial commit | Same log, beginning at the root commit |
| First tagged release | `v0.1.0`, 20 August 2026 | `git for-each-ref refs/tags --sort=creatordate` |
| Later tagged releases | `v0.1.1`–`v0.1.3` on 21 August; `v0.1.4` on 25 August; `v0.1.5` on 3 September 2026 | Same tag command |
| Commit activity | 127 commits on 10 distinct dates from 20 August through 7 September 2026 | `git rev-list --count 394bf1c`; inspect dates with `git log --format='%ad' --date=short` |
| Recorded identities | 295 commits attributed to Anagha Dhekne, 14 to Codex, and 4 to Dependabot across all locally available refs | `git shortlog -sne --all` on the baseline date |
| Public issue/PR workflow | Numbered public records exist through at least PR #59; issue #18 is a public request for external workflow feedback | Follow the repository links in the evidence map below |

The Git history establishes the first recorded development date, but it does
**not** prove when GitHub repository visibility changed. GitHub's repository
creation date and any private-to-public visibility history were not independently
recoverable from the local clone. Before submission, preserve authoritative
evidence of the repository creation/public date and determine whether the
repository was public from inception. Until then, the defensible public-history
start used for planning is **20 August 2026**, the date of the first commit and
release—not an earlier date.

The current history is also concentrated in the project's first three weeks.
It does not yet satisfy JOSS's requirement for active development spanning more
than six months, regardless of commit volume.

## Earliest submission timing

Using 20 August 2026 as the conservative public-history start, six calendar
months ends on **20 February 2027**. Because JOSS requires **more than** six
months, 20 February 2027 is a calendar floor rather than an eligible submission
date. Submission should occur only after that date and only when the repository
also shows sustained iteration and every required evidence gate below is met.

Waiting passively does not close the gap. Releases, fixes, public discussion,
research workflows, and responses to real use must be distributed across the
period. Re-check the live JOSS policy and this baseline before choosing a
submission date.

## Scope case and limits

Modelstamp has an obvious intended research application: it records and checks
artifact integrity and selected runtime-environment evidence before persisted
Python machine-learning objects are deserialized. Researchers can use it when
transferring, archiving, reproducing, or rechecking fitted models. The package
has an installable Python distribution, documented API and CLI, typed package
metadata, tests and cross-platform CI, tagged releases, citation metadata, and
rerunnable experiments.

The case that Modelstamp represents more than a minor utility rests on its
combined design boundary rather than code volume:

- verification is ordered before reconstruction;
- a versioned sidecar manifest binds artifact bytes to represented environment
  evidence;
- dependency comparison is limited to packages represented as relevant to the
  persisted model;
- integrity and shared-secret authenticity guarantees are kept distinct; and
- compatibility evidence is reported without claiming environment replication
  or safe deserialization.

Those choices and rejected alternatives are recorded in the
[architecture decision log](../docs/architecture-decisions.md). The
[state-of-the-field evidence](state_of_field/README.md) compares adjacent
persistence, portability, registry, versioning, and signing tools using official
sources. The project rationale is that those tools solve neighboring problems,
while none of the reviewed interfaces supplied this exact bounded,
pre-deserialization check as a small persistence-layer control. This is a
maintainer analysis, not a claim that extending an existing project was
impossible.

The largest present scope risk is research impact. The project has a
maintainer-authored preprint and maintainer-produced experiments, but no verified
independent research user, integration, citation, or repeat use as of this
baseline. Anonymous PyPI downloads show distribution activity only; they do not
establish installation, use, research impact, or distinct users. The canonical
[research and adoption record](../docs/research-adoption.md) must remain the
source for these outcomes.

## Human design and AI-assistance record

AI-assisted work must not be concealed or treated as independent contribution.
The `Codex` Git identity records tool-assisted commits; it does not establish a
second human contributor. Dependabot is automation. The human maintainer remains
responsible for the problem framing, acceptance or rejection of proposed
changes, architecture, claim boundaries, review, testing, licensing, and
accuracy.

Before submission, create a complete prospective AI-use ledger that records:

1. each tool and model/version used;
2. whether it assisted code, tests, documentation, experiments, or paper text;
3. the nature and approximate scope of that assistance; and
4. how the maintainer reviewed, edited, and validated the output.

The eventual JOSS paper must contain the disclosure required by the then-current
policy and affirm the human author's review and core-design responsibility.
AI must not be used for author conversations with JOSS editors or reviewers
except where the policy expressly permits it, such as translation.

## Evidence map at baseline

| JOSS consideration | Current public evidence | Baseline assessment |
| --- | --- | --- |
| Open source and installable | `LICENSE`, `pyproject.toml`, PyPI releases, quick start | Present |
| Obvious research application | Research-use guide, preprint, reproducible experiments | Present as maintainer-authored evidence |
| Feature completeness and maintainability | API/CLI, typed package, 79 tests, cross-platform CI, contribution guide | Substantial evidence; reassess at submission |
| Public history over more than six months | Git history starts 20 August 2026 | **Not met** |
| Iteration distributed over time | Six releases and activity on 10 dates within the first three weeks | **Not met yet** |
| Demonstrated research use | Maintainer preprint and experiments | Minimum developer-use signal present; independent use absent |
| External adoption or integration | Research-adoption ledger | **None verified** |
| Design thinking | Five ADRs and state-of-the-field comparison | Present; maintain prospectively |
| Open workflows | Changelog, CI, contribution guide, public issues and PRs | Present but young; sustain over time |
| Community engagement | Public feedback issue and external outreach records | Invitations exist; substantive external engagement not yet verified |
| AI transparency | Git attribution and this baseline; full tool/version ledger not yet present | **Incomplete** |
| Repository public-from-inception evidence | Not established by local Git history | **Needs authoritative evidence** |

## Submission gates

Do not submit until all of the following are true:

- [ ] More than six months of public, active development is evidenced after the
      verified public-history start date.
- [ ] Meaningful changes and releases are distributed across that period rather
      than concentrated in the launch window.
- [ ] At least one real research workflow using Modelstamp is documented;
      independent use is strongly preferred and tracked without inflating
      downloads into adoption.
- [ ] Repository creation/public-visibility evidence is preserved.
- [ ] The state-of-the-field comparison and build-versus-contribute rationale
      are refreshed against current official sources.
- [ ] Architecture decisions made after this baseline are recorded when they
      affect public guarantees, trust boundaries, formats, or compatibility.
- [ ] The AI-use ledger and paper disclosure are complete, accurate, and
      reviewed by the human author.
- [ ] Installation, tests, CI, documentation, contribution pathways, releases,
      citation metadata, and archival records are current and independently
      reproducible.
- [ ] The live JOSS scope, screening, ethics, and AI-use policies are rechecked.
- [ ] A final scope review concludes that Modelstamp is not merely a minor
      utility and has demonstrated research impact rather than only potential.

## Reassessment cadence

Update this baseline when a material gate changes, and perform formal reviews
on **20 November 2026**, **20 January 2027**, and after **20 February 2027**.
Each update should preserve the prior facts, add dated evidence links, and avoid
rewriting absence of evidence as success.

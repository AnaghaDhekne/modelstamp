# Supplementary design-property validation — verified-open-file continuity

## Test

`tests/test_core.py::test_load_uses_the_verified_open_file`

## Provenance

The regression test was introduced in commit `882b458` (`Add persistence safety regression coverage`) and subsequently made cross-platform in commit `2bce00a` (`Make verified-file test cross-platform`). This history predates the SaTML novelty review that surfaced the property for explicit discussion in the paper and shows that the regression coverage was not introduced in response to that review.

## Purpose

Validate that the artifact whose integrity is verified through an opened file remains the artifact consumed by the subsequent deserialization operation when the artifact pathname is replaced in the interval between those operations.

## Setup

An artifact is saved with its corresponding manifest. During `load()`, the deserialization step is intercepted so that a distinct replacement artifact is substituted at the original pathname using `os.replace` after integrity verification of the already-opened artifact but before `_load_object` consumes the open stream.

## Expected outcome

`load()` returns the object contained in the originally verified artifact rather than the object associated with the replacement pathname.

## Observed outcome

The dedicated regression test passes: the replacement artifact is not consumed by the load operation.

The behavior was independently re-verified during the pre-submission review on 2026-09-03 in a clean Linux x86_64 environment using Python 3.12.3; the isolated test completed with `1 passed`.

## Platform behavior

Where pathname replacement of an opened file succeeds under the tested filesystem semantics, the existing open file continues to supply the originally verified content to deserialization. Where replacement of the opened file is rejected, the substitution attempt is prevented before deserialization. These observations should not be generalized to all operating systems or filesystem configurations.

## Relationship to the SaTML evaluation

This validation is supplementary to the five research questions. It is **not one of the eight RQ2 trust-boundary scenarios and does not alter the RQ2 scenario count or the previously frozen RQ1–RQ5 evidence** in `evidence_freeze.md`.

## Scope limitation

The test evaluates one specific pathname-replacement interval between integrity verification and deserialization. It does **not** establish general resistance to time-of-check-to-time-of-use (TOCTOU) attacks, general filesystem-attack resistance, safe deserialization, or malicious-artifact detection.

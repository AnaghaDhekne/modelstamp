# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-20

### Added
- `save()` / `load()` wrapping joblib (with a pickle fallback) plus a JSON
  environment manifest sidecar.
- Environment capture: Python, scikit-learn, numpy, scipy, pandas, xgboost,
  lightgbm, catboost, joblib, statsmodels, platform, timestamp, and git commit.
- `on_mismatch` policy on load: `"warn"` (default), `"raise"`, `"ignore"`.
- `check()` and `inspect()` to read the manifest without loading the model.
- JSON-compatible user metadata stored in the manifest.
- SHA-256 and size verification before deserialization.
- Serialization backend and model component metadata in the manifest.
- Strict manifest schema validation and atomic replacement of individual files.
- Rollback-safe paired artifact/manifest commits and concurrent-writer locking.
- Verification and deserialization through the same open artifact file.
- Relevant-package comparison to avoid warnings about unrelated installations.
- `inspect`, `check`, and `verify` command-line commands.
- Optional HMAC-SHA-256 manifest authentication through `signing_key`.
- JSON-normalized metadata, locked manifest inspection, and clean CLI handling
  for filesystem errors.
- Python 3.13 testing and typed-package metadata.
- Reference-counted artifact locks that do not accumulate in long-running
  processes.
- Distribution-backed `__version__` lookup to prevent release version drift.
- Authenticated signing-key identifiers and registry-based key rotation.
- Property-based manifest validation tests and reproducible verification
  benchmarks.
- Searchable MkDocs API documentation with GitHub Pages deployment.
- Current Node.js 24-based GitHub Actions versions.
- Explicit symmetric-HMAC trust-boundary guidance and single-source release
  version instructions.

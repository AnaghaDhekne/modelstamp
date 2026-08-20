# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-20

### Added
- `save()` / `load()` wrapping joblib (with a pickle fallback) plus a JSON
  environment manifest sidecar.
- Environment capture: Python, scikit-learn, numpy, scipy, pandas, xgboost,
  lightgbm, catboost, joblib, platform, timestamp, and git commit.
- `on_mismatch` policy on load: `"warn"` (default), `"raise"`, `"ignore"`.
- `check()` and `inspect()` to read the manifest without loading the model.
- User `metadata` stored verbatim in the manifest.
- SHA-256 and size verification before deserialization.
- Serialization backend and model component metadata in the manifest.
- Strict manifest schema validation and atomic file replacement.
- Relevant-package comparison to avoid warnings about unrelated installations.
- `inspect`, `check`, and `verify` command-line commands.

# Contributing to modelstamp

Thank you for helping improve `modelstamp`. Bug reports, focused feature
proposals, documentation fixes, and pull requests are welcome.

## Development setup

```bash
git clone https://github.com/AnaghaDhekne/modelstamp.git
cd modelstamp
python -m pip install -e ".[dev]"
```

Run the same checks used by continuous integration:

```bash
ruff format --check .
ruff check .
pytest
python -m build
python -m twine check dist/*
mkdocs build --strict
```

## Pull requests

- Keep each change focused and explain the user-facing reason for it.
- Add regression tests for bug fixes and tests for new behavior.
- Preserve compatibility with Python 3.8 through 3.13.
- Update the README or changelog when public behavior changes.
- Never include real model artifacts, credentials, or private training data.

All changes to `main` go through a pull request. Required CI and CodeQL checks
must pass, conversations must be resolved, and a Code Owner must approve
contributor pull requests. New commits dismiss an earlier approval so the final
revision is always reviewed.

Merging a pull request does not publish a package. Maintainers publish releases
separately by following the [release checklist](docs/releasing.md).

For suspected vulnerabilities, follow [SECURITY.md](SECURITY.md) instead of
opening a public issue.

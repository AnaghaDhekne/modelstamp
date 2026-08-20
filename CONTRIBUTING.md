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
- Preserve compatibility with Python 3.8 through 3.12.
- Update the README or changelog when public behavior changes.
- Never include real model artifacts, credentials, or private training data.

For suspected vulnerabilities, follow [SECURITY.md](SECURITY.md) instead of
opening a public issue.

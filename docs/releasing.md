# Release checklist

This page is for `modelstamp` maintainers. Merging a pull request into `main`
does not publish a package automatically.

## Before the release

1. Confirm that the intended changes are covered by tests and documented.
2. Add user-visible changes under a new version in `CHANGELOG.md`.
3. Update only `project.version` in `pyproject.toml`. Installed package metadata
   is the source for `modelstamp.__version__`.
4. Open a pull request. Wait for the required test matrix, build checks, and
   CodeQL analysis to pass, resolve review conversations, and obtain the
   required Code Owner approval.
5. Merge the approved pull request into `main`.

## Publish

1. Create a tag matching the version, for example `v0.1.1`, on the release
   commit in `main`.
2. Publish a GitHub release from that tag.
3. Confirm that the `Publish to PyPI` workflow verifies the tagged commit is
   contained in `main` and builds the distributions.
4. Review the pending `pypi` environment deployment and approve it.
5. Confirm the workflow succeeds, then install the exact version from PyPI in a
   clean environment and run a small import or save/load smoke test.

Protected `v*` tags cannot be updated or deleted. If a release is incorrect,
fix it in a new version; do not attempt to replace an existing PyPI artifact.

## When no release is needed

Do not publish a new package solely for repository administration, CI hardening,
or a regenerated `uv.lock` that does not alter packaged runtime requirements.
Documentation-only changes need a release only when the updated documentation
must be included in the built distribution rather than published on the
documentation site.

TestPyPI remains available for an intentional pre-release validation. It is not
part of every production release.

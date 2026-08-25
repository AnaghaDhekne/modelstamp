# Release checklist

This page is for `modelstamp` maintainers. Merging a pull request into `main`
does not publish a package automatically.

## Before the release

1. Confirm that the intended changes are covered by tests and documented. Audit
   the README, MkDocs guides and navigation, examples, `llms.txt`,
   `llms-full.txt`, package metadata, and any version- or behavior-bearing
   references affected by the release.
2. Add user-visible changes under a new version in `CHANGELOG.md`.
3. Update `project.version` in `pyproject.toml`. Installed package metadata is
   the source for `modelstamp.__version__`; do not hard-code a runtime version
   in the package source.
4. Update the human-facing `version` and `date-released` fields in
   `CITATION.cff` to match the planned release.
5. Search the repository for the previous version and release date. Historical
   changelog entries may remain; current metadata, badges, examples, and guides
   must not accidentally describe the previous release. Confirm DOI links use
   the intended Zenodo concept DOI unless a version-specific DOI is required.
6. Build the documentation with strict link and navigation checks.
7. Open a pull request. Wait for the required test matrix, build checks, and
   CodeQL analysis to pass, resolve review conversations, and obtain the
   required Code Owner approval.
8. Merge the approved pull request into `main`.

## Publish

1. Confirm that the Zenodo GitHub integration is enabled for the repository.
   Without it, publishing a GitHub release will not create the corresponding
   Zenodo archive and version DOI.
2. Create a tag matching the version, for example `vX.Y.Z`, on the release
   commit in `main`.
3. Publish a GitHub release from that tag.
4. Confirm that the `Publish to PyPI` workflow verifies the tagged commit is
   contained in `main` and builds the distributions.
5. Review the pending `pypi` environment deployment and approve it.
6. Confirm the workflow succeeds, then install the exact version from PyPI in a
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

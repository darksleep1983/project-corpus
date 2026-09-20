# Release pipeline

**Current status:** active and verified through Project Corpus 2.1.0.

The repository's release path is deliberately owner-controlled:

```text
frozen commit
→ local tests + repository integrity + package build
→ full P10/history scan on that exact commit
→ push exact commit + required GitHub CI
→ release qualification for the exact SHA
→ annotated tag + GitHub Release
→ PyPI Trusted Publishing
→ clean public-install smoke
```

## Qualification automation

The `release qualification` workflow accepts an exact frozen 40-character
commit SHA. It checks out that SHA with full history, runs the complete test
suite, builds sdist/wheel, validates package metadata, records SHA-256 hashes,
and retains the artifacts for review.

Qualification does not create a tag, GitHub Release, or PyPI publication.

## Security gate

P10 findings and exception policy remain an owner-controlled decision. The full
history scan runs on the exact frozen candidate after all release-source commits
are complete.

If a source commit changes after the scan, that exact-head attestation is no
longer sufficient for the new commit and the required release gates must be
re-run.

Matched secret values must never be copied into release evidence.

## Publication

The active `.github/workflows/publish-pypi.yml` workflow is triggered by a
published GitHub Release. It verifies that the release tag and package version
match, rebuilds the distributions from the tag target, validates them, creates
GitHub build provenance, and publishes through PyPI Trusted Publishing.

The `pypi` environment and Trusted Publisher are already configured and were
verified by the 2.1.0 release. No long-lived PyPI API token is required.

Tag creation, GitHub Release publication, PyPI publication, repository setting
changes, and any new security exception remain explicit owner-controlled
actions.

## Post-publication verification

Every public package release should be verified from outside the repository
checkout:

1. confirm the GitHub Release and remote annotated tag resolve to the qualified
   release commit;
2. confirm the PyPI version, wheel, sdist, hashes, and provenance;
3. install the exact version from PyPI in a clean environment with no editable
   or direct local install;
4. run import/version and CLI smoke checks appropriate to the release;
5. confirm the local worktree is clean and record factual release evidence in
   local continuity.

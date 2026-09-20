# PyPI Trusted Publishing

**Status: active and verified.**

The repository uses the active workflow
`.github/workflows/publish-pypi.yml`. It is triggered by a published GitHub
Release and publishes `project-corpus` through PyPI Trusted Publishing.

The GitHub `pypi` environment and the PyPI Trusted Publisher are configured.
The 2.1.0 release verified the complete path, including GitHub build provenance
and PyPI Integrity provenance.

The neighboring `.github/workflows/publish-pypi.yml.example` file is retained
only as a reference/template artifact. It is not the active publication path.

## Current publication contract

1. The owner authorizes the release and the exact frozen candidate passes the
   current release/security gates.
2. The qualified commit is pushed and required CI is green.
3. An annotated `vX.Y.Z` tag points to that exact commit.
4. A GitHub Release for that tag is explicitly published.
5. `publish-pypi.yml` checks out the release tag, verifies tag/package-version
   agreement, builds and validates sdist/wheel, and creates build provenance.
6. The publish job uses the protected `pypi` environment and GitHub OIDC to
   obtain short-lived publishing identity.
7. PyPI publication is verified with public artifact/provenance checks and a
   clean install smoke.

## Security properties

- No long-lived PyPI API token is stored in the repository.
- GitHub OIDC supplies short-lived identity for publication.
- The build job and publish job are separate.
- The publish job receives only the permissions required for Trusted
  Publishing.
- The workflow verifies the release tag and package version before publishing.
- Published files carry provenance that can be checked against the GitHub
  repository/workflow identity.
- Tag creation, GitHub Release publication, environment/ruleset changes, and
  publication remain owner-controlled.

## Maintainer checks

Re-review the workflow, the `pypi` environment, and the PyPI Trusted Publisher
when maintainer access, repository ownership, workflow identity, or publication
policy changes. For ordinary releases, do not recreate the publisher and do not
introduce a long-lived token.

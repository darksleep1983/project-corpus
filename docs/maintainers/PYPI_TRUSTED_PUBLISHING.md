# PyPI Trusted Publishing plan

**Status: prepared, not configured.** The repository contains a non-active
workflow template at `.github/workflows/publish-pypi.yml.example`. Its filename
prevents it from running until the owner deliberately activates it.

## Owner configuration required

1. Confirm that the frozen release candidate has a version matching its intended
   `vX.Y.Z` tag and has a final P10 owner-reviewed attestation outside Git
   history.
2. On PyPI, create `project-corpus` or configure a pending Trusted Publisher
   with GitHub owner `darksleep1983`, repository `project-corpus`, workflow
   filename `publish-pypi.yml`, and environment `pypi`.
3. In GitHub, create the `pypi` environment and require an owner approval for
   deployment. Do not add a long-lived PyPI token as a repository secret.
4. Review the template, rename it to `publish-pypi.yml`, and commit it only with
   an explicit owner publication decision.

## Security properties

- GitHub OIDC supplies a short-lived identity; no PyPI API token is stored.
- The publisher job receives only `id-token: write`; build remains a separate
  least-privilege job.
- The workflow verifies the release tag and package version, builds sdist/wheel,
  checks metadata, and attaches build provenance before publishing.
- The protected `pypi` environment supplies the explicit approval boundary.

PyPI recommends trusting the smallest possible dedicated workflow and using a
protected environment. Re-review the workflow and all Trusted Publishers when
maintainer access changes.

# Release pipeline

The repository's release path is deliberately owner-controlled:

```text
frozen commit
→ full tests
→ build sdist + wheel
→ metadata validation + hashes
→ final P10 scan and owner-reviewed attestation
→ annotated tag and GitHub Release
→ optional PyPI Trusted Publishing
```

## What automation may do

The `release qualification` workflow accepts an exact, frozen 40-character
commit SHA. It verifies that checkout, runs the complete test suite, builds
sdist/wheel, validates package metadata, writes SHA-256 hashes, and retains the
artifacts for review. It cannot create a tag, release, or publish a package.

## What automation must not decide

P10 findings and any narrow exception policy remain an owner decision. The final
P10 scan runs after all repository commits on the frozen release-candidate HEAD;
its attestation belongs outside Git history so an evidence commit cannot change
the scanned source.

## Publication gate

Only after the owner explicitly authorizes release and configures the protected
PyPI environment may the inactive Trusted Publishing template become active.
The package version must exactly match the release tag and artifacts must be
built from that tag target.

## Optional enhancements

GitHub artifact attestations are included in the publication template. A full
SBOM is deferred: the Runtime has no third-party runtime dependencies, and an
SBOM should be added only when a release consumer or dependency profile makes a
standard CycloneDX or SPDX artifact useful.

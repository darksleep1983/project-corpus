# PyPI readiness

**Current status:** `project-corpus` is published on PyPI. Project Corpus
2.1.0 is the current verified release baseline as of 2026-09-20.

The distribution name is already claimed by this project. Future release work
must update the existing project and verify the intended new version.

## Repository package status

| Item | Status |
| --- | --- |
| Distribution name | `project-corpus`, published |
| Current verified release baseline | `2.1.0` |
| Import package | `project_corpus` |
| CLI entry point | `project-corpus = project_corpus.cli:main` |
| Runtime requirement | Python 3.11+ |
| License | MIT metadata and `LICENSE` file |
| Long description | `README.md` declared in `pyproject.toml` |
| URLs | Homepage, documentation, repository, issues, and changelog declared |
| Dependencies | No third-party runtime dependencies declared |
| Publication path | GitHub Release → PyPI Trusted Publishing |
| Public PyPI project | `https://pypi.org/project/project-corpus/` |

## Future-release readiness checklist

For each new package version:

1. freeze the exact release candidate commit and verify the intended version in
   `pyproject.toml`, package metadata, and the planned `vX.Y.Z` tag;
2. run the complete test suite, repository-integrity checks, documentation/link
   checks relevant to the delta, and `git diff --check`;
3. build sdist and wheel from the frozen candidate and run
   `python -m twine check dist/*`;
4. complete the required full-history P10/security scan on that exact commit and
   resolve any new finding before publication;
5. push the exact qualified commit and require green GitHub CI and release
   qualification for that SHA;
6. only after explicit owner authorization, create the annotated tag and GitHub
   Release;
7. let the active Trusted Publishing workflow publish to PyPI;
8. verify the public version, hashes/provenance, and a clean install/import/CLI
   smoke from PyPI rather than from the local checkout.

Do not use PyPI publication as a test mechanism or a way to reserve a version.

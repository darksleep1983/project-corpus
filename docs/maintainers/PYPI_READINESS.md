# PyPI readiness

**Current observation:** on 2026-09-17, the official PyPI JSON endpoint for
`project-corpus` returned `404`, so the desired distribution name appeared
available at that moment. This is not a reservation; availability must be
checked again immediately before publication.

## Repository package status

| Item | Status |
| --- | --- |
| Distribution name | `project-corpus` observed available; not claimed |
| Import package | `project_corpus` |
| CLI entry point | `project-corpus = project_corpus.cli:main` |
| Runtime requirement | Python 3.11+ |
| License | MIT metadata and `LICENSE` file |
| Long description | `README.md` declared in `pyproject.toml` |
| URLs | Homepage, documentation, repository, issues, and changelog declared |
| Dependencies | No third-party runtime dependencies declared |
| Public PyPI package | Not published |

## Pre-publication checklist

1. Re-check `https://pypi.org/pypi/project-corpus/json` from the release
   operator's environment.
2. Build sdist and wheel from the frozen release commit.
3. Run `python -m twine check dist/*` and inspect the rendered README.
4. Confirm that the wheel version equals the intended release tag version and
   that `project-corpus --help` works in a clean environment.
5. Complete P10 and retain the final owner-reviewed attestation outside Git
   history.
6. Configure PyPI Trusted Publishing only after the owner approves release.

Do not publish to TestPyPI or PyPI merely to reserve a name.

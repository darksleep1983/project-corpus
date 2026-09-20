# Release and publication checklist

[Русская версия](PUBLISHING_CHECKLIST_RU.md)

Use this repeatable checklist for future Project Corpus public releases. The
repository and PyPI project already exist.

1. Confirm the intended release scope, version, and exact repository state.
2. Verify that no unintended embedded server, installer, port, package runtime,
   secret, or machine-specific configuration has entered the public product.
3. Run the complete test suite and verify the repository manifest.
4. Review English/Russian parity and every task-relevant internal Markdown link.
5. Test changed quick-start or Runtime paths from a clean copy when the release
   affects them.
6. Fetch every available branch/tag/ref, confirm the clone is not shallow, and
   run `project-corpus security scan-history REPOSITORY_ROOT` on the exact
   frozen candidate. Review only redacted categories/locations; never copy
   matched values. The gate must cover reachable history, deleted files,
   commits, patches, binaries, metadata, and locally available
   dangling/unreachable objects. Do not claim coverage of server-side objects
   that GitHub did not transfer.
7. Confirm public-facing status wording, package metadata, security reporting
   route, and release notes are current.
8. Verify the required GitHub repository/environment/Trusted Publisher settings
   are still appropriate. Do not change them as part of an ordinary release
   unless the owner separately authorizes that change.
9. Create the annotated `vX.Y.Z` tag and publish the matching GitHub Release
   only after the frozen candidate passes required tests/CI/P10 and the owner
   explicitly authorizes that release.
10. Let the active Trusted Publishing workflow publish the matching package
    version to PyPI, then verify public hashes/provenance and perform a clean
    PyPI install/import/CLI smoke.

Never use force-push, history rewrite, a broad security exception, or a
long-lived publishing token as a shortcut around these gates.

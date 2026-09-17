# Pre-publication checklist

[Русская версия](PUBLISHING_CHECKLIST_RU.md)

1. Confirm the repository is still Private while preparing.
2. Verify that the embedded server, installers, ports, package runtime, and
   machine-specific configuration are absent.
3. Run the complete test suite and verify the repository manifest.
4. Review English/Russian parity and every internal Markdown link.
5. Test each quick-start path from a clean copy:
   - direct folder;
   - owner-provided MCP documentation;
   - manual session and replacement-file handoff.
6. Fetch every available branch/tag/ref, confirm the clone is not shallow, and
   run `project-corpus security scan-history REPOSITORY_ROOT`. Review only the
   redacted categories/locations; never copy matched values. The gate must cover
   reachable history, deleted files, commits, patches, binaries, metadata, and
   locally available dangling/unreachable objects. Do not claim coverage of
   server-side objects that GitHub did not transfer.
7. Confirm that public-facing status wording and the security reporting route
   are current.
8. Configure description, topics, and Private Vulnerability Reporting.
9. Create the `v2.0.0` tag or release only after the frozen release-candidate
   P10 attestation and a separate explicit owner release command.
10. Change visibility to Public only after a separate owner decision.

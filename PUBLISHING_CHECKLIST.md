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
6. Review Git history for local paths, user names, credentials, and obsolete
   server instructions.
7. Confirm that public-facing status wording and the security reporting route
   are current.
8. Configure description, topics, and Private Vulnerability Reporting.
9. Prepare `v0.1.0-preview` as a draft release only after the content is frozen.
10. Change visibility to Public only after a separate owner decision.

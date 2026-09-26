# Security model

[Русская версия](security.ru.md)

Project Corpus is a documentation protocol, not a security boundary by itself.

## Optional controlled Runtime

The local Python Runtime adds policy-enforced CLI and stdio MCP operations.
Controlled operations are bounded by Runtime hard limits, an external owner
trust grant, project policy, and the client's requested capability subset.
Guarantees apply only to the documented modes and qualified local filesystems;
see the [platform and guarantee matrix](security/platform-guarantees.md).
The Runtime is not a general-purpose sandbox and provides no HTTP or remote MCP.

## Direct-folder mode

The AI client's sandbox and filesystem permissions decide what can be read or
changed. Grant only the project and Corpus folders that are actually needed.

## V1 your-own-MCP mode

Security depends on the server you choose, its authentication, root restriction,
path validation, write policy, network exposure, and audit behavior. These
recommendations describe a third-party server and do not certify its
controls. The optional Project Corpus Runtime's own local stdio adapter is
documented separately in the [stdio MCP guide](runtime/stdio-mcp.md).

Prefer a server that restricts one exact root, blocks traversal, protects
specific files, verifies stale writes, backs up old content, performs readback,
and returns receipts. Verify these features rather than assuming them.

## Manual mode

The AI sees only the files you upload, but the cloud client receives their
contents according to its own data policy. The AI cannot save local replacements
for you or prove that you performed readback.

## Universal rules

- Keep secrets, credentials, tokens, cookies, private keys, and seed phrases
  outside the Corpus.
- Review every requested permission.
- Keep one authoritative writer at a time.
- Back up files before replacement.
- Treat saved runtime claims as stale until freshly checked.
- Do not expose an unauthenticated local MCP endpoint to the public internet.

Instructions can guide an AI but cannot enforce operating-system permissions.

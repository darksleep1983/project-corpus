# Security model

[Русская версия](security.ru.md)

Project Corpus is a documentation protocol, not a security boundary by itself.

## Direct-folder mode

The AI client's sandbox and filesystem permissions decide what can be read or
changed. Grant only the project and Corpus folders that are actually needed.

## Your-own-MCP mode

Security depends on the server you choose, its authentication, root restriction,
path validation, write policy, network exposure, and audit behavior. This
repository does not provide or certify those controls.

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

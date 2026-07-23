# Security model

Project Corpus is intentionally narrow.

- One server instance is configured for one Corpus root.
- The server resolves and validates every path under that root.
- Root writes are limited to known current files.
- New files may be created only directly in `Tasks/` or `Report/` and must be Markdown.
- `OPERATOR_PROFILE.md` is not writable.
- `AGENTS.md` requires explicit protocol-change authorization.
- Updates require the exact current SHA-256.
- Backups and audit receipts live outside the Corpus.
- Streamable HTTP is loopback-only by default, and the SDK rejects requests with
  untrusted Origin headers.

## What this does not protect against

- a malicious person who already controls your operating-system account;
- a second independent writer changing files behind the server;
- exposing the HTTP endpoint to an untrusted network;
- secrets deliberately placed inside Markdown;
- unsafe instructions accepted by the AI client.

Run the server on loopback, review the code, use one authoritative writer per Corpus, and keep secrets elsewhere.

# FAQ

## Is this tied to ChatGPT or Claude?

No. The server speaks MCP. Any compatible client can connect if it supports the chosen transport and permissions.

## Does it send my whole project to the internet?

The server reads only the configured Corpus folder. The AI client may receive file contents when it calls a tool, according to that client's own data handling. Review your client's policy.

## Does it control my computer?

No. The included server only reads and writes the Corpus according to its policy.

## Can I keep two projects in one Corpus?

The protocol intentionally supports one active project per Corpus. Create another Corpus and another server configuration for a separate project.

## Can I rename the files?

Yes, but you must update both the template protocol and the server's allowlist. The default names work together as shipped.

## Why Tasks and Reports?

A Task defines what is allowed and required. A Report records what was actually done and verified. Keeping them separate prevents plans from being mistaken for evidence.

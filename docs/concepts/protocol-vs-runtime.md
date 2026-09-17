# Protocol vs Runtime

The Protocol is the portable product contract. It is Markdown-first,
vendor-neutral, install-free, and usable manually.

The optional Runtime is a reference implementation of that contract. It offers
validation, external trust, policy enforcement, safe transactions,
audit/recovery, a controlled CLI, and local stdio MCP. It does not redefine
Protocol semantics through implementation behavior.

Manual and direct-folder workflows are useful, but they do not receive Runtime
enforcement. Controlled guarantees are limited to the documented Runtime modes
and qualified local filesystems.

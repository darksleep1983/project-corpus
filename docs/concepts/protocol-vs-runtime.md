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

## Higher-level architectures

Project Corpus provides durable project-owned identity and continuity. Lifecycle,
recovery and orchestration frameworks can consume that substrate without becoming
Protocol authority. Living Software Organism is a higher-level architecture and
reference direction of this kind, not a required Project Corpus dependency or a
claim that a public LSO repository/package exists. Organism functions and recovery
execution contracts belong to their own layer. Manual Markdown operation remains
independently useful without Runtime, MCP, a server or database.

The same boundary is explained in the English `README.md` and
Russian `README.ru.md` at the repository root. No Protocol or package version changes follow
from this non-normative clarification.

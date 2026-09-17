# Read-only validator and doctor

The V2 doctor reads project files and returns structured checks without changing
the project or external trust configuration.

It reports one of these current levels:

- `MARKDOWN_COMPATIBLE` for a completely readable V1 seven-file corpus;
- `DIRECT_FOLDER_OBSERVABLE` for a conforming V2 project inspected read-only;
- `DIAGNOSTIC_ONLY` when required files, identity, policy or generated-view
  rules fail.

When an external trust grant is supplied, doctor opens the pinned root through
the production native backend and verifies root identity, filesystem, project
identity and policy digest. This is still diagnosis: doctor never provisions
Runtime state or promotes its result to controlled CLI or MCP.

The validator detects missing required paths, role overlap, project-ID mismatch,
absolute physical roots in PROJECT, policy-schema violations, symlinked required
paths where the host API exposes them, and generated Markdown without the
`NON_AUTHORITATIVE_VIEW` marker.

Read-only doctor is not a substitute for runtime confinement. A compromised
direct folder may race ordinary path reads; controlled mode is enabled only
after the production native backend verifies the pinned root identity.

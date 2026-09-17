# GitHub metadata plan

[Русская версия](REPOSITORY_METADATA.ru.md)

**Status: proposal only.** This file records a recommended final public state;
it does not change GitHub repository settings.

## Current observation

- Visibility: public.
- Description: `Persistent project state and authority for AI agents —
  Markdown-first protocol with optional policy-enforced CLI and MCP runtime.`
- Homepage: not set.
- Social preview: not set.
- Topics: broad and partly client-specific (14 total).

## Recommended public metadata

Description — retain the current description. It accurately presents the
Protocol/Runtime separation without claiming that MCP is required.

Homepage — after GitHub Pages receives owner approval:

```text
https://darksleep1983.github.io/project-corpus/
```

Topics — use these ten precise topics rather than client-name or generic keyword
spam:

```text
ai-agents
agent-memory
project-memory
project-state
context-management
model-context-protocol
mcp
markdown
developer-tools
ai-tools
```

Social preview — upload `docs/assets/social-preview.png` in GitHub Settings
after owner approval. It is 1280×640 PNG, the size GitHub recommends for best
social rendering, and remains below GitHub's 1 MB limit.

Do not add a PyPI badge until a public distribution actually exists. The README
uses only CI, docs-build, Python, MIT license, and GitHub Release badges.

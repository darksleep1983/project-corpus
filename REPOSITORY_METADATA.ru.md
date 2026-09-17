# План метаданных GitHub

[English](REPOSITORY_METADATA.md)

**Статус: только предложение.** Этот файл фиксирует рекомендуемое публичное
состояние; он не меняет настройки GitHub.

## Текущее наблюдение

- Visibility: public.
- Description: `Persistent project state and authority for AI agents —
  Markdown-first protocol with optional policy-enforced CLI and MCP runtime.`
- Homepage: не задан.
- Social preview: не задан.
- Topics: слишком широкие и частично привязаны к именам клиентов (всего 14).

## Рекомендуемые публичные метаданные

Description — оставить текущий. Он точно показывает разделение Protocol/Runtime
и не создаёт впечатления, что MCP обязателен.

Homepage — после owner approval для GitHub Pages:

```text
https://darksleep1983.github.io/project-corpus/
```

Topics — использовать эти десять точных topics вместо client-name или общего
keyword spam:

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

Social preview — после owner approval загрузить
`docs/assets/social-preview.png` в GitHub Settings. Это PNG 1280×640 —
рекомендованный GitHub размер для social rendering; файл меньше лимита 1 MB.

Не добавляйте PyPI badge, пока не появится публичный distribution. В README
оставлены только badges CI, docs build, Python, MIT license и GitHub Release.

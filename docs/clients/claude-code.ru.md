# Использование Project Corpus с Claude Code

[English](claude-code.md)

## Рекомендуется: прямая папка

Поместите Corpus внутрь workspace проекта или разрешите его как дополнительную
рабочую папку. Claude Code читает `CLAUDE.md`, а не `AGENTS.md`, поэтому:

1. вставляйте `PROJECT_INSTRUCTION_TEMPLATE.ru.md` в начале работы; либо
2. добавьте короткий project `CLAUDE.md`, который требует до работы полностью
   прочитать и соблюдать `Corpus/AGENTS.md`.

Не дублируйте весь протокол внутри `CLAUDE.md`; оставьте одну authority-копию в
Corpus.

Официальная инструкция по memory:
<https://docs.anthropic.com/en/docs/claude-code/memory>

## Свой MCP

Добавьте доверенный remote или local MCP-сервер, используя его настоящую команду
или URL. Общий синтаксис для локального stdio-сервера:

```bash
claude mcp add --transport stdio <name> -- <command> [args...]
```

Выполните `/mcp` внутри Claude Code для проверки соединения. Ограничьте сервер
точным root Corpus и запишите реальные возможности в
`CORPUS_ACCESS_CURRENT.md`.

Официальная инструкция MCP:
<https://docs.anthropic.com/en/docs/claude-code/mcp>

Project Corpus не поставляет команду сервера.

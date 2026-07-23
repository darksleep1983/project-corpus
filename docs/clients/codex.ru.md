# Использование Project Corpus с Codex

[English](codex.md)

## Рекомендуется: прямая папка

Поместите Corpus внутрь доверенного workspace проекта либо откройте Corpus как
локальную папку. Запускайте Codex из иерархии папок, содержащей `AGENTS.md`.
Codex обнаруживает `AGENTS.md` по пути от project root до текущей рабочей папки.

Если Corpus находится вне активного workspace, разрешите доступ к этой точной
папке, а не ко всему диску. Используйте project instruction template, чтобы
явно задать загрузку и синхронизацию.

Официальные инструкции:

- <https://developers.openai.com/codex/agent-configuration/agents-md>
- <https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex>

## Свой MCP

Codex хранит MCP-настройки в `config.toml`. Desktop-приложение ChatGPT, Codex CLI
и IDE extension используют общую конфигурацию. Добавляйте только доверенный
сервер и ограничивайте его точным root Corpus.

Шаблон CLI для локального stdio-сервера:

```bash
codex mcp add <server-name> -- <server-command> [args...]
```

Проверка:

```bash
codex mcp list
```

Официальная инструкция: <https://developers.openai.com/codex/mcp>

Project Corpus не поставляет `<server-command>`.

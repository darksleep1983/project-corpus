# Использование Project Corpus с Claude Desktop

[English](claude-desktop.md)

## Новые проекты: начните с V2

Следуйте [Quick Start для V2](../quickstart.md). Для ручной сессии передайте
`AGENTS.md`, `.project-corpus/state/PROJECT.md` и
`.project-corpus/state/STATUS.md`, а также только нужные активную Task и Reports.

## Существующие проекты V1

В V1 используются семь current-файлов. Приложите их к новому проекту или
разговору, добавьте только нужные Tasks и Reports и используйте ручную
инструкцию. В конце сохраните возвращённые файлы-замены самостоятельно.

## Свой MCP

Project Corpus Runtime включает локальный stdio MCP adapter; см.
[инструкцию adapter](../runtime/stdio-mcp.md). Репозиторий не поставляет
extension или `.mcpb`-пакет специально для Claude Desktop. Также можно
использовать проверенное extension или свой упакованный сервер после проверки
permissions и ограничения файлового root.

В Claude Desktop подключённые tools можно проверить через меню Connectors или
developer settings. Точная доступность может зависеть от тарифа и политики
организации.

Официальные инструкции:

- <https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop>
- <https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp>

Не открывайте неаутентифицированный локальный endpoint в публичный интернет.

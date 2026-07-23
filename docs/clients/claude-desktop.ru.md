# Использование Project Corpus с Claude Desktop

[English](claude-desktop.md)

## Проще всего: ручной режим

Приложите семь current-файлов к новому проекту или разговору, добавьте только
нужные Tasks и Reports и используйте инструкцию ручного режима. В конце сами
сохраните возвращённые файлы-замены.

## Свой MCP

Claude Desktop поддерживает desktop extensions и управляемые организацией
connectors. Используйте проверенное extension или свой упакованный сервер только
после проверки permissions и ограничения файлового root. Репозиторий не
поставляет `.mcpb`-пакет или локальный сервер.

В Claude Desktop подключённые tools можно проверить через меню Connectors или
developer settings. Точная доступность может зависеть от тарифа и политики
организации.

Официальные инструкции:

- <https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop>
- <https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp>

Не открывайте неаутентифицированный локальный endpoint в публичный интернет.

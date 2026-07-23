# Подключение к Claude Code

Для локального Project Corpus сначала используйте stdio. Claude Code сам запускает
сервер как локальный дочерний процесс, поэтому отдельный HTTP-сервер держать
включённым не нужно.

1. Установите Project Corpus.
2. Выведите готовую команду:

```powershell
.\.venv\Scripts\python.exe .\scripts\print_client_config.py claude-code
```

3. Выполните напечатанную команду в терминале. Она добавит `project-corpus` как
   локальный stdio MCP-сервер в user scope Claude Code.
4. В Claude Code выполните `/mcp` и убедитесь, что `project-corpus` подключён.
5. Добавьте `PROJECT_INSTRUCTION_TEMPLATE.ru.md` в инструкции проекта либо дайте
   Claude ту же инструкцию перед началом работы.

## Необязательно: локальный Streamable HTTP

Если вам осознанно нужен отдельно работающий сервер, запустите `.\start.ps1`, а
затем добавьте его командой:

```bash
claude mcp add --transport http project-corpus http://127.0.0.1:8334/mcp
```

Используйте HTTP для удалённого сервера только при нормальной аутентификации. В
JSON-конфигурации transport должен быть `http` или `streamable-http`; URL без type
не является корректной конфигурацией.

Официальная документация: https://code.claude.com/docs/en/mcp

# Подключение к Claude Desktop

Claude Desktop теперь поддерживает установку Desktop Extensions одним нажатием, но
в этом репозитории пока нет пакета расширения `.mcpb`. Для первого preview самый
прозрачный путь — локальная конфигурация stdio.

После установки выполните:

```powershell
.\.venv\Scripts\python.exe .\scripts\print_client_config.py claude-desktop
```

Скрипт выведет готовый JSON с абсолютными путями. Затем в Claude Desktop:

1. Откройте **Settings → Developer → Edit Config**.
2. Добавьте выведенный блок `project-corpus` в раздел `mcpServers`.
3. Сохраните файл и перезапустите Claude Desktop.
4. Откройте список connectors и убедитесь, что появились инструменты Project
   Corpus.

На Windows конфигурационный файл обычно находится в
`%APPDATA%\Claude\claude_desktop_config.json`. Сохраните сгенерированные
абсолютные пути: относительные пути ненадёжны, когда сервер запускает desktop app.

Когда появится подписанный или проверенный пакет `.mcpb`, его можно будет
установить через **Settings → Extensions**. До этого предпочитайте проверяемый
JSON-вариант.

Официальные материалы:

- https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop
- https://modelcontextprotocol.io/docs/develop/connect-local-servers

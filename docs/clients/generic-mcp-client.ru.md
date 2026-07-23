# Подключение другого MCP-клиента

Project Corpus поддерживает два транспорта.

## Streamable HTTP

Запустите сервер:

```bash
./start.sh
```

Адрес:

```text
http://127.0.0.1:8334/mcp
```

Укажите этот адрес в настройках клиента.

## stdio

Команда запуска:

```bash
project-corpus-mcp --transport stdio \
  --corpus-root /absolute/path/to/Corpus \
  --mcp-root /absolute/path/to/mcp-state
```

В клиентах, которые сами запускают MCP как дочерний процесс, используйте абсолютный путь к исполняемому файлу и абсолютные пути к папкам.

Официальная документация протокола: https://modelcontextprotocol.io/docs/

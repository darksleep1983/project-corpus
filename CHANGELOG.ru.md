# История изменений

[English](CHANGELOG.md)

## Unreleased

- Улучшено знакомство с проектом в README после v2.0.0: добавлены наглядная
  схема состояния проекта, ручной 60-секундный старт V2 и более ясное описание
  опционального Runtime.

## 2.0.0 — 2026-09-17

- Добавлен независимый Markdown-first Project Corpus Protocol V2 с разделёнными
  ролями canonical state и явными conformance rules.
- Добавлен необязательный reference Runtime для Python 3.11+: внешний owner
  trust, нативные confined transactions, audit/recovery, CLI и локальный stdio
  MCP.
- Добавлены read-only планирование и controlled create-only миграция V1→V2;
  V1-шаблоны остаются неизменными и работоспособными.
- Добавлен обязательный редактированный release gate всей доступной локальной
  Git history.
- Не включены Git commit/push, HTTP/remote MCP, arbitrary shell execution,
  sandbox, orchestration, distributed locking и multi-project operation.
- Project Corpus переосмыслен как Markdown-протокол, а не встроенный сервер.
- Добавлены три равноправных режима: прямая папка, MCP владельца и ручная
  загрузка в сессию.
- `MCP_CONNECTION_CURRENT.md` заменён нейтральным
  `CORPUS_ACCESS_CURRENT.md`.
- Добавлены парные инструкции режимов доступа и отдельные инструкции Codex.
- Удалены встроенный MCP-runtime, transports, порты, установщики, package
  metadata и обязательная пользовательская зависимость от Python.
- Сохранены паритет русского и английского, защита файлов, обратная связь через
  GitHub Issues и добровольная поддержка через USDT в сети TON.
- Подготовлены публичный статус и правила сообщения об уязвимостях.

## 0.1.0 — исторический preview серверной версии

- Первый объединённый preview протокола и встроенного MCP-сервера.

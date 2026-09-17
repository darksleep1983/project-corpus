# Проверка перед публикацией

[English](PUBLISHING_CHECKLIST.md)

1. Во время подготовки убедиться, что репозиторий остаётся Private.
2. Проверить отсутствие встроенного сервера, установщиков, портов, package
   runtime и machine-specific конфигурации.
3. Запустить полный набор тестов и проверить manifest репозитория.
4. Проверить паритет русского/английского и все внутренние Markdown-ссылки.
5. Проверить каждый quick start на чистой копии:
   - прямая папка;
   - документация своего MCP;
   - ручная сессия и передача файлов-замен.
6. Получить все доступные branches/tags/refs, убедиться, что clone не shallow,
   и выполнить `project-corpus security scan-history REPOSITORY_ROOT`.
   Проверять только редактированные категории/locations и никогда не копировать
   найденные значения. Gate должен охватывать reachable history, удалённые
   файлы, commits, patches, binaries, metadata и локально доступные
   dangling/unreachable objects. Не заявлять coverage server-side объектов,
   которые GitHub не передал.
7. Убедиться, что публичный статус и путь сообщения об уязвимостях актуальны.
8. Настроить description, topics и Private Vulnerability Reporting.
9. Подготовить `v0.1.0-preview` как draft release только после заморозки content.
10. Переключать visibility на Public только после отдельного решения владельца.

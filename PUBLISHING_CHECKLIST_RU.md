# Чек-лист релиза и публикации

[English](PUBLISHING_CHECKLIST.md)

Используйте этот повторяемый чек-лист для будущих публичных релизов Project
Corpus. Репозиторий и проект на PyPI уже существуют.

1. Подтвердить scope релиза, версию и точное состояние репозитория.
2. Проверить, что в публичный продукт не попали неожиданные встроенный сервер,
   установщик, порт, package runtime, секрет или machine-specific конфигурация.
3. Запустить полный набор тестов и проверить manifest репозитория.
4. Проверить паритет русского/английского и все относящиеся к изменению
   внутренние Markdown-ссылки.
5. Если релиз меняет quick start или Runtime, проверить затронутые пути на
   чистой копии.
6. Получить все доступные branches/tags/refs, убедиться, что clone не shallow,
   и выполнить `project-corpus security scan-history REPOSITORY_ROOT` на
   точном замороженном кандидате. Проверять только редактированные
   categories/locations и никогда не копировать найденные значения. Gate должен
   охватывать reachable history, удалённые файлы, commits, patches, binaries,
   metadata и локально доступные dangling/unreachable objects. Не заявлять
   coverage server-side объектов, которые GitHub не передал.
7. Убедиться, что публичный статус, package metadata, путь сообщения об
   уязвимостях и release notes актуальны.
8. Проверить, что настройки GitHub repository/environment/Trusted Publisher
   по-прежнему корректны. Не менять их в рамках обычного релиза без отдельного
   разрешения владельца.
9. Создавать annotated tag `vX.Y.Z` и публиковать соответствующий GitHub
   Release только после прохождения требуемых tests/CI/P10 замороженным
   кандидатом и явного разрешения владельца на этот релиз.
10. Дать активному Trusted Publishing workflow опубликовать соответствующую
    версию в PyPI, затем проверить публичные hashes/provenance и выполнить
    чистый PyPI install/import/CLI smoke.

Нельзя использовать force-push, переписывание истории, широкое security
exception или долгоживущий publishing token как способ обойти эти gates.

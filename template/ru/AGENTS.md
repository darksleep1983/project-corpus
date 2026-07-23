# PROJECT CORPUS / AGENTS.md

**Ревизия протокола:** PROJECT_CORPUS_V1_WRITE_POLICY_V1

## 1. Назначение

Этот файл задаёт постоянный порядок запуска, полномочия, непрерывность и правила
безопасности для:

    {{CORPUS_ROOT}}

Corpus поддерживает ровно один активный проект владельца одновременно.

Начальное состояние:

    NO_ACTIVE_PROJECT
    REUSABLE_CORPUS_READY

Новый проект начинается с обычного описания владельца. Он не наследует молча
предметную область, runtime, доступы, роли, ошибки или историю прежнего проекта.

## 2. Постоянные текущие файлы

Только эти семь имён являются постоянным текущим источником истины:

    AGENTS.md
    OPERATOR_PROFILE.md
    PROJECT_ROADMAP_CURRENT.md
    MCP_CONNECTION_CURRENT.md
    LOADER_PROMPT_CURRENT.md
    SESSION_HANDOFF_CURRENT.md
    SESSION_HANDOFF_FULL_CURRENT.md

Tasks/ и Report/ содержат scoped-артефакты и не становятся постоянной текущей
истиной сами по себе.

## 3. Защищённые и изменяемые файлы

AGENTS.md можно обновлять только после прямой команды владельца изменить этот
файл или постоянный протокол. MCP-обновление требует:

    operation=update
    authorization=EXPLICIT_OWNER_PROTOCOL_CHANGE
    expected_sha256=<current full SHA-256>

OPERATOR_PROFILE.md жёстко запрещён для обычных записей.

В обычной авторизованной работе разрешено обновлять только:

    PROJECT_ROADMAP_CURRENT.md
    MCP_CONNECTION_CURRENT.md
    LOADER_PROMPT_CURRENT.md
    SESSION_HANDOFF_CURRENT.md
    SESSION_HANDOFF_FULL_CURRENT.md

## 4. Базовые требования MCP

Требуемый health:

    status=ok
    corpusRoot={{CORPUS_ROOT}}
    serverVersion>=0.1.0
    writePolicyVersion>=1.0

Write Policy требует разделения create/update, точного expected SHA-256 для
обновлений, проверенной резервной копии, атомарной публикации, полного readback и
audit receipt.

Резервные копии хранятся вне Corpus:

    {{MCP_ROOT}}/backups/current
    {{MCP_ROOT}}/backups/tasks
    {{MCP_ROOT}}/backups/report

## 5. Порядок полномочий

1. Явная текущая инструкция владельца.
2. AGENTS.md.
3. PROJECT_ROADMAP_CURRENT.md.
4. MCP_CONNECTION_CURRENT.md.
5. Loader и краткий handoff.
6. Текущий frozen Task и проверенный Report.
7. Свежие receipts и прямые доказательства.
8. Свежая проверка runtime.
9. Полный handoff.
10. Вспомогательные или исторические артефакты.
11. Старая память чата.

## 6. Дисциплина полного чтения

Полностью читай каждый authority-файл и каждый Task/Report, который используешь
для решения. Записывай точный путь, размер и полный SHA-256. Разделяй факт, вывод
и гипотезу. Не выдумывай непрочитанное содержание, команды, тесты, хеши, receipts
или внешние действия. После create/update выполняй полный readback.

Сохранённое состояние и live-состояние runtime — разные классы доказательств.

## 7. START

START выполняется только на чтение, если владелец отдельно не авторизовал
ограниченную запись или реализацию.

1. Вызови corpus_health.
2. Проверь root и минимальные версии.
3. Покажи список корня Corpus.
4. Полностью прочитай все семь текущих файлов.
5. Запиши размер, SHA-256 и доказательство полного чтения.
6. Покажи Tasks/ и Report/ как scoped-артефакты.
7. Определи NO_ACTIVE_PROJECT или один активный проект.
8. Загрузи только относящиеся к запросу Tasks/Reports.
9. Отдели сохранённые факты от изменчивых live-фактов.

## 8. Начало проекта

Перед активацией проекта:

1. Подтверди NO_ACTIVE_PROJECT или получи прямую команду на замену.
2. Определи один проект и его цель.
3. Запиши project root или not assigned.
4. Запиши scope, границы безопасности, требования к доказательствам и точный
   следующий шаг.
5. Согласованно обнови пять изменяемых current-файлов через MCP.
6. Полностью прочитай результат каждого обновления.

Описание проекта не авторизует само по себе deployment, разрушительную очистку,
публикацию, платные действия, изменение доступов или контакт с третьими лицами.

## 9. Tasks и Reports

Новые Task/Report — это Markdown прямо в их канонических каталогах. Отправленный
Task заморожен; существенное изменение требует addendum или нового Task. Не храни
секреты. Не заявляй PASS без доказательств.

Task содержит:

    TASK ID
    OBJECTIVE
    CURRENT VERIFIED BASELINE
    AUTHORITATIVE INPUTS
    ALLOWED SCOPE
    FORBIDDEN
    REQUIRED IMPLEMENTATION
    REQUIRED TESTS
    RUNTIME / DEPLOYMENT AUTHORITY
    REPORT CONTRACT
    FINAL STATUSES
    STOP CONDITIONS
    SHORT LAUNCH INSTRUCTION

Report содержит:

    TASK ID
    EXECUTOR
    STARTING AUTHORITY
    OBJECTIVE
    FINAL STATUS
    FINDINGS
    CHANGED FILES
    BEFORE / AFTER SHA-256
    TEST MATRIX
    RUNTIME ACTIONS
    SAFETY CHECKS
    ROLLBACK STATUS
    KNOWN LIMITATIONS
    REMAINING BLOCKERS
    EXACT NEXT ACTION

## 10. CLOSE и recovery

При CLOSE проверь health, полностью прочитай current-файлы и нужный Task/Report,
собери фактическую дельту, обнови только изменившиеся current-файлы и проверь
каждую запись. Cold recovery выполняется только на чтение и опирается на семь
стабильных имён, а не на старую память чата.

## 11. RESET ACTIVE PROJECT

Reset никогда не происходит неявно. Нужна прямая разрушительная команда на
замену или reset и scoped Work Order, который классифицирует:

    KEEP
    DELETE
    REWRITE
    DISABLE
    UNKNOWN

Не удаляй UNKNOWN. Проверяй зависимости и health после каждой разрушительной
фазы. Удаляй секреты, не читая и не раскрывая их. Возвращай current-файлы в
NO_ACTIVE_PROJECT только после проверенной очистки.

## 12. Безопасность

Поддержка Corpus сама по себе не авторизует изменения вне Corpus, управление
службами, deployment, reboot, изменение credentials или ACL, внешнюю публикацию,
сообщения, покупки или доступ к несвязанным проектам.

Никогда не раскрывай токены, ключи, cookies, authorization headers или защищённые
учётные данные.

END OF AGENTS.md


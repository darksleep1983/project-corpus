# Context Intelligence (необязательный Runtime, 2.2.0)

[English](context.md)

Project Corpus Protocol остаётся **2.0**. Для переносимого Markdown layout и ручной работы не требуются Runtime, SQLite, LLM или сеть. Context Intelligence — локальное пересобираемое неавторитетное представление для любого AI-клиента. Внешняя БД и сторонние зависимости не нужны. В будущем возможны необязательные адаптеры к Graphiti, Cognee и другим системам; ядро от них не зависит.

## Источники и границы

Первый provider читает только разрешённые policy Markdown-файлы в `state/`, `tasks/`, `reports/`, `history/` через native confined backend. Код и документация вне Corpus не сканируются. Оба канонических state-файла должны входить в read scope. Явный путь к SQLite-индексу — файл `.sqlite3` непосредственно в `.project-corpus/cache/`; policy не задаёт его и не выдаёт через него полномочия. Индекс содержит ID проекта, пути и SHA-256 источников, тип, класс authority, timestamp, временной класс и provenance строк/строк разделов. **Текст источников не хранится**. Удаление индекса не повреждает Corpus; `build` пересоздаёт его. Query/bundle отклоняют устаревшие хэши до пересборки. SQLite FTS5 не требуется.

Provider ограничивает один файл существующим лимитом чтения Runtime 8 МиБ, scoped snapshot — 2 048 источниками/64 МиБ и 50 000 непустыми строками, а сохранённый индекс — 128 МиБ. Более крупный Corpus получает ограниченную ошибку. Не добавляйте `.project-corpus/cache/` в Git: это удаляемое неавторитетное производное представление. Запись индекса использует ограниченную native staging/publication и отклоняет ссылки/reparse-пути.

```text
project-corpus context build ROOT --index ROOT/.project-corpus/cache/context.sqlite3
project-corpus context query ROOT "запрос" --index ROOT/.project-corpus/cache/context.sqlite3 [--limit N]
project-corpus context bundle ROOT "запрос" --index ROOT/.project-corpus/cache/context.sqlite3 [--max-tokens N]
project-corpus context doctor ROOT --index ROOT/.project-corpus/cache/context.sqlite3
project-corpus context eval ROOT --index ROOT/.project-corpus/cache/context.sqlite3 --dataset ROOT/eval.json
project-corpus context candidate-validate ROOT --input ROOT/candidate.json
```

Команды возвращают JSON; неверный ввод, stale index, выход за границы пути и запрет policy имеют стабильные коды ошибок и exit `2`. `doctor` и `eval` возвращают `ok: false` в JSON при обнаруженных проблемах. JSON dataset/candidate должен быть обычным файлом внутри корня проекта размером до 1 МиБ. Context-команды не меняют PROJECT или STATUS.

## Retrieval и время

Порядок детерминирован: совпадение терминов и фраз, классы canonical/active/cited/scoped, штраф истории, явный timestamp, точный ID проекта и provenance раздела. Точные и близкие дубликаты подавляются. Результат — указатель, а не канонический вывод: `non_authoritative=true` и `freshness_requirement=READ_PRIMARY_SOURCE_BEFORE_AUTHORITY_CLAIM` требуют повторного чтения первоисточника.

Необязательная ненормативная строка `Supersedes: .project-corpus/reports/old.md` в scoped Task, Report или History помечает именно этот видимый policy источник как `superseded`. Такая связь не может заместить PROJECT, STATUS или активную Task. Ошибочная или отсутствующая ссылка не создаёт предполагаемого замещения. Старые источники остаются доступными для поиска. Без ссылки старые нецитируемые Reports и неактивные Tasks являются historical; цитируемые Reports — scoped. Текущее состояние определяет только STATUS, а устойчивую идентичность — PROJECT. Синтаксис не меняет обязательные метаданные Protocol V2 и не ломает старые Corpus.

## Bundle, receipt и candidate v1

`compile_bundle()` выдаёт JSON-совместимые `schema_version=1`, `project_id`, `query`, `created_at`, `index_schema_version`, `source_snapshot_digest` и `source_count` для всего scoped Corpus, ограниченный `selected_source_snapshot`, `mandatory_reads`, `budget`, `items`, `serialized_bytes`, `non_authoritative=true`, `bundle_sha256`. Полная карта путей/хэшей в Bundle не включается. Каждый item содержит ID, excerpt, путь, диапазон строк, SHA-256, классы authority и времени, требование свежести, score и причины выбора. PROJECT, STATUS и активная Task получают ограниченные структурные выдержки; `mandatory_reads` указывает путь/хэш первоисточника и разделы для полного чтения. При малом бюджете выдержки сокращаются, а требование полного чтения остаётся явным. `max_tokens` оценивает **только текст excerpt** как ceil(UTF-8 bytes/4), а не токены всего JSON; для полного сериализованного конверта отдельно действуют предел 65 536 байт и точный счётчик. Детерминированный хэш исключает лишь `created_at` и само поле хэша. Изменение любого scoped источника меняет полный digest и хэш Bundle после пересборки.

`make_receipt(bundle, consumer)` проверяет хэш bundle и выдаёт receipt `schema_version=1`: ID проекта, хэш bundle, доставленные item IDs, consumer ID, timestamp, digest snapshot и неавторитетный флаг. Вызывающая сторона фиксирует фактическую доставку; helper не доказывает, что внешний агент использовал контекст.

`validate_candidate(corpus, candidate)` принимает только candidate `schema_version=1`, ID, project ID, kind, statement, source refs с точными путём/хэшем/строкой, UTC-время и `status=candidate`. Kinds: `semantic_fact`, `episodic_evidence`, `procedural_knowledge`, `environment_gotcha`, `premise`, `resource_reference`. Проверка не записывает и не повышает каноническое состояние. Promotion остаётся явным действием supervisor/owner.

Memory Doctor проверяет схему/устаревание индекса, отсутствующие источники, provenance, отсутствующие/ошибочные/циклические связи supersession, несовпадение проекта, чрезмерный STATUS, изменчивые фразы на английском/русском без freshness label, полный и выбранный snapshot Bundle, а также необязательные candidate evidence. Автоматического исправления нет. CorpusEval v1 принимает `{"schema_version":"1","cases":[...]}` с query, ожидаемым верхним источником/top-k retrieval, индивидуальными temporal/authority ожиданиями источников, ожидаемыми/запрещёнными путями или классами Bundle, необязательными must-contain/must-not-contain, budget, изоляцией проекта и digest snapshot. Retrieval и Bundle проверяются отдельно; изоляцию нужно испытывать на fixtures другого проекта или с запретом policy. Метрики включают recall, contamination, индивидуальную корректность, бюджет, устаревание и повторяемость; LLM judge не нужен.

`forbidden_scope_paths` проверяет, что источники другого проекта или запрещённые policy fixtures не попадают ни в собранный snapshot, ни в выдачу. Без явной проверки scope изоляция отмечается непроверенной.

Необязательный stdio MCP открывает `corpus.context_query`, `corpus.context_bundle`, `corpus.context_doctor`, `corpus.candidate_validate`, только если `corpus.context` разрешён hard limits Runtime, внешним trust grant, project policy и session subset. MCP строит временное представление из текущих scoped источников; в аргументах tools нет index или произвольного пути. Поэтому MCP doctor проверяет текущие источники, а CLI doctor дополнительно сравнивает сохранённый индекс. Контракты существующих tools сохранены.

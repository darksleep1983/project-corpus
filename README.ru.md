# Project Corpus

[English version](README.md)

[![CI](https://github.com/darksleep1983/project-corpus/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/darksleep1983/project-corpus/actions/workflows/test.yml)
[![Docs build](https://github.com/darksleep1983/project-corpus/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/darksleep1983/project-corpus/actions/workflows/docs.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-66d9c2)](LICENSE)
[![Release](https://img.shields.io/github/v/release/darksleep1983/project-corpus?display_name=tag&sort=semver)](https://github.com/darksleep1983/project-corpus/releases)
[![PyPI](https://img.shields.io/pypi/v/project-corpus)](https://pypi.org/project/project-corpus/)
[![Protocol 2.0](https://img.shields.io/badge/Protocol-2.0-66d9c2)](protocol/v2/README.md)

**Долговременная идентичность, непрерывность и полномочия проекта для работы с ИИ.**

AI-сессии и модели меняются. Понимание проекта о самом себе, его текущее
состояние и доказательства этого состояния должны сохраняться дольше. Project
Corpus — независимый от поставщика Markdown-first protocol, который даёт этим
сведениям понятное место внутри проекта. Он определяет, что является
каноническим и текущим, что проверено, какой следующий шаг нужен и какие правила
ограничивают изменения.

Protocol полезен самостоятельно. Необязательный Python Runtime добавляет
локальную проверку, контролируемые операции, audit/recovery, CLI и stdio MCP.

## Начните за три шага

1. Скачайте или клонируйте этот репозиторий. Скопируйте
   [`templates/v2/minimal/`](templates/v2/minimal/) в корень проекта, который
   вы хотите продолжать между AI-сессиями:

   ```sh
   cp -R templates/v2/minimal/. /path/to/your-project/
   ```

   PowerShell:

   ```powershell
   Copy-Item -Force .\templates\v2\minimal\AGENTS.md C:\path\to\your-project\
   Copy-Item -Recurse -Force .\templates\v2\minimal\.project-corpus C:\path\to\your-project\
   ```

2. Заполните `.project-corpus/state/PROJECT.md` устойчивой идентичностью
   проекта. Используйте тот же ID проекта в `.project-corpus/state/STATUS.md` и
   `.project-corpus/policy.toml`; в STATUS укажите проверенное текущее
   состояние, блокеры, доказательства и точное следующее действие.
3. Дайте AI-клиенту доступ к папке проекта или загрузите `AGENTS.md`,
   `PROJECT.md`, `STATUS.md` и относящиеся к работе активную Task и Reports.
   Попросите следовать `AGENTS.md`, прочитать каноническое состояние, назвать
   актуальные факты и продолжить с точного следующего шага.

В [Quick Start](docs/quickstart.md) есть готовый запрос для загрузки контекста.

## Как это работает

У каждого проекта есть собственный набор канонических Markdown-записей:

- `PROJECT.md` описывает долговременную идентичность, назначение и границы.
- `STATUS.md` фиксирует проверенное текущее состояние и следующий шаг.
- `AGENTS.md` задаёт локальный workflow и правила полномочий.
- Tasks ограничивают запрошенную работу; Reports фиксируют сделанное и
  доказательства.

В начале сессии AI читает эти источники и сверяет изменяемые факты с живым
проектом. Это помогает не принять старый чат, сохранённую выжимку или одного
исполнителя за актуальный источник полномочий проекта.

## Protocol и необязательный Runtime

| Project Corpus Protocol | Необязательный Project Corpus Runtime |
| --- | --- |
| Markdown-first, независим от поставщика и подходит для ручной работы | Локальная реализация на Python для дополнительного enforcement |
| Не требует установки, базы данных или MCP | Validation, controlled CLI и локальный stdio MCP |
| Переносимым источником полномочий остаются файлы проекта | Внешний owner trust, policy enforcement, транзакции, audit и recovery |

Runtime реализует Protocol, но не определяет и не меняет молча его семантику.
Технические гарантии действуют только в описанных controlled-режимах и на
проверенных локальных файловых системах. См. [Protocol и Runtime](docs/concepts/protocol-vs-runtime.md)
и [модель безопасности](docs/security.ru.md).

Установка необязательного Runtime из PyPI:

```sh
pip install project-corpus
project-corpus validate /path/to/your-project
project-corpus doctor /path/to/your-project
```

Runtime 2.2.0 также включает необязательный [Context Intelligence](docs/runtime/context.ru.md):
пересобираемый индекс в рамках policy и ограниченный контекст с источниками для
любого AI-клиента. Результаты неавторитетны; источником истины остаётся
канонический Markdown.

## Связь с архитектурами более высокого уровня

Lifecycle-, recovery- и orchestration-архитектуры могут использовать Project
Corpus как долговременную основу состояния проекта, сохраняя собственные
контракты и ответственность за проверку. Living Software Organism (LSO) — одно
из таких направлений архитектуры и reference direction. Project Corpus полезен
самостоятельно и не требует LSO, Runtime, MCP, базы данных или определённого
поставщика ИИ. Здесь описана архитектурная связь; это не заявление о доступном
публичном пакете или репозитории LSO. Project Corpus не является LSO.

## Существующие проекты V1

Исходный workflow и шаблоны V1 по-прежнему поддерживаются. Необязательный
Runtime может read-only спланировать миграцию V1 и создать отдельное назначение
V2, не переписывая файлы V1. См. [обзор совместимости V1](docs/how-it-works.ru.md),
инструкции для [прямой папки](docs/access/direct-folder.ru.md),
[ручной сессии](docs/access/manual.ru.md) и [своего MCP](docs/access/own-mcp.ru.md),
а также [инструкцию по миграции](docs/migration/v1-read-only-planner.md).

## Документация

- [Quick Start](docs/quickstart.md)
- [Как это работает](docs/how-it-works.ru.md)
- [Частые вопросы](docs/faq.ru.md)
- [Runtime и CLI](docs/runtime.md)
- [Локальный stdio MCP](docs/runtime/stdio-mcp.md)
- [Примеры](docs/examples.md)
- [Безопасность](docs/security.ru.md)
- [English README](README.md)

## О проекте

Project Corpus Protocol имеет версию 2.0. Необязательный Python Runtime имеет
версию 2.2.0, поддерживает Python 3.11+ и не требует сторонних runtime-
зависимостей. История релизов находится в [changelog](CHANGELOG.ru.md). Вопросы
и сообщения об ошибках размещайте в [GitHub Issues](https://github.com/darksleep1983/project-corpus/issues);
не публикуйте содержимое личного Corpus или секреты.

Project Corpus распространяется бесплатно по лицензии MIT. Добровольные
пожертвования описаны на [странице поддержки](SUPPORT.ru.md); они не дают
дополнительных прав или гарантий.

## Лицензия

MIT. См. [LICENSE](LICENSE).

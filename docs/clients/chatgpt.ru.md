# Использование Project Corpus с ChatGPT

[English](chatgpt.md)

## Новые проекты: начните с V2

Следуйте [Quick Start для V2](../quickstart.md). Для ручной работы в ChatGPT
Project загрузите `AGENTS.md`, `.project-corpus/state/PROJECT.md` и
`.project-corpus/state/STATUS.md`, затем добавляйте только активную Task и
Reports, нужные для работы. При замене источников сохраняйте уникальные
канонические имена файлов.

Официальная инструкция:
<https://help.openai.com/en/articles/10169521-projects-in-chatgpt>

## Существующие проекты V1

В V1 используются семь current-файлов. Для ручной работы в ChatGPT Project
добавьте эти файлы как project sources, а ручной раздел из
`PROJECT_INSTRUCTION_TEMPLATE.ru.md` поместите в Project instructions. В каждый
чат добавляйте только нужные Tasks и Reports. При замене файлов не оставляйте
источники-дубликаты с одинаковыми каноническими именами.

## Прямая папка

В desktop-приложении ChatGPT режим Work умеет открывать локальную папку. Откройте
только Corpus или содержащий его workspace проекта, дайте минимально нужный
доступ и используйте `DIRECT_FOLDER`.

Официальная инструкция:
<https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex>

## Свой MCP

Custom MCP apps и запись зависят от текущего тарифа ChatGPT, роли в workspace,
настроек администратора и rollout. Настраивайте app только после подготовки
доверенного удалённого MCP endpoint и проверки его permissions. Репозиторий не
поставляет такой endpoint.

Официальная инструкция:
<https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt>

Не открывайте неаутентифицированный локальный сервер в интернет только ради
подключения ChatGPT.

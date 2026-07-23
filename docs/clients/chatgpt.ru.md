# Использование Project Corpus с ChatGPT

[English](chatgpt.md)

## Проще всего: ручной режим

Создайте ChatGPT Project, добавьте семь current-файлов как project sources, а
секцию ручного режима из `PROJECT_INSTRUCTION_TEMPLATE.ru.md` поместите в Project
instructions. В конкретный чат добавляйте только нужные Tasks и Reports.

При замене current-файла не оставляйте два source с одинаковым каноническим
именем. ChatGPT может предложить загрузить дубликат вместо замены старого файла.

Официальная инструкция:
<https://help.openai.com/en/articles/10169521-projects-in-chatgpt>

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

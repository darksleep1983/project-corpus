# Подключение к ChatGPT

ChatGPT подключается к удалённым MCP-серверам, а не напрямую к серверу, который
слушает только 127.0.0.1. Оставьте Project Corpus на loopback и используйте
поддерживаемый Secure MCP Tunnel, если сервер работает на вашем компьютере или в
закрытой сети. Не открывайте локальный сервер в интернет только ради подключения.

## Перед началом

- Точные возможности зависят от тарифа ChatGPT, роли в workspace и текущей
  доступности Apps/developer mode.
- Полные MCP-действия записи и изменения сейчас доступны пользователям Business
  и Enterprise/Edu. Pro может использовать custom MCP apps с правами read/fetch
  в developer mode.
- Custom MCP apps сейчас работают только в веб-версии; не планируйте это
  подключение для мобильного приложения.

## Порядок подключения

1. Установите Project Corpus и запустите его локально.
2. Следуйте инструкции Secure MCP Tunnel, чтобы дать ChatGPT
   аутентифицированный удалённый путь к локальному серверу, не открывая его в
   публичный интернет.
3. Включите developer mode в ChatGPT, если это допускает ваш тариф и workspace.
4. Откройте **Settings или Workspace settings → Apps → Create**, укажите MCP
   endpoint и нужные metadata, выберите authentication при необходимости, затем
   выполните **Scan Tools** и создайте app.
5. Выберите созданное app в новом веб-чате ChatGPT. До вызова write-инструментов
   внимательно проверьте запрос на разрешение.
6. Добавьте текст из `PROJECT_INSTRUCTION_TEMPLATE.ru.md` в инструкции проекта
   ChatGPT Project.

Для этого сервера сначала выберите permission, при котором изменения требуют
подтверждения. Запись в Corpus меняет локальное состояние проекта.

## Официальные материалы

- https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt-beta
- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://help.openai.com/en/articles/11487775-apps-in-chatgpt

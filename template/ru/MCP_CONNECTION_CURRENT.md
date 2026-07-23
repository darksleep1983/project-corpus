# MCP CONNECTION CURRENT

**Статус:** CONFIGURATION_PENDING
**Корень Corpus:** {{CORPUS_ROOT}}
**Корень MCP:** {{MCP_ROOT}}

## Требуемая архитектура

    AI-клиент
    → аутентифицированное или локальное MCP-подключение
    → Project Corpus MCP
    → {{CORPUS_ROOT}}

## Требуемый health

    status=ok
    corpusRoot={{CORPUS_ROOT}}
    serverVersion>=0.1.0
    writePolicyVersion>=1.0

Результат health доказывает соединение только в момент проверки.


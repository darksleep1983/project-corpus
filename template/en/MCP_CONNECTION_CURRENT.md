# MCP CONNECTION CURRENT

**Status:** `CONFIGURATION_PENDING`
**Corpus root:** `{{CORPUS_ROOT}}`
**MCP root:** `{{MCP_ROOT}}`

## Required architecture

```text
AI client
→ authenticated or local MCP connection
→ Project Corpus MCP
→ {{CORPUS_ROOT}}
```

## Required health

```text
status=ok
corpusRoot={{CORPUS_ROOT}}
serverVersion>=0.1.0
writePolicyVersion>=1.0
```

A health result proves connectivity only at its timestamp.

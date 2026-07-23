#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$REPO_ROOT/.project-corpus.local.json"
[ -f "$CONFIG" ] || { echo "Run install.sh first"; exit 2; }
exec "$REPO_ROOT/.venv/bin/python" - "$CONFIG" "$REPO_ROOT/.venv/bin/project-corpus-mcp" <<'PY'
import json
import os
import sys

config_path, executable = sys.argv[1:]
with open(config_path, encoding="utf-8") as fh:
    config = json.load(fh)

os.execv(executable, [
    executable,
    "--transport", "streamable-http",
    "--corpus-root", config["corpusRoot"],
    "--mcp-root", config["mcpRoot"],
    "--host", config["host"],
    "--port", str(config["port"]),
])
PY

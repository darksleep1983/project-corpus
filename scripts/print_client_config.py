#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys


def load(repo: Path) -> dict:
    path = repo / ".project-corpus.local.json"
    if not path.is_file():
        raise SystemExit("Run install.ps1 or install.sh first")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=("claude-desktop", "claude-code", "generic-http"))
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    cfg = load(repo)
    exe = repo / (".venv/Scripts/project-corpus-mcp.exe" if sys.platform == "win32" else ".venv/bin/project-corpus-mcp")

    if args.client == "claude-desktop":
        block = {
            "mcpServers": {
                "project-corpus": {
                    "command": str(exe.resolve()),
                    "args": [
                        "--transport", "stdio",
                        "--corpus-root", cfg["corpusRoot"],
                        "--mcp-root", cfg["mcpRoot"],
                    ],
                }
            }
        }
        print(json.dumps(block, indent=2, ensure_ascii=False))
    elif args.client == "claude-code":
        command = [
            "claude", "mcp", "add", "--scope", "user", "--transport", "stdio",
            "project-corpus", "--", str(exe.resolve()), "--transport", "stdio",
            "--corpus-root", cfg["corpusRoot"], "--mcp-root", cfg["mcpRoot"],
        ]
        print(subprocess.list2cmdline(command) if sys.platform == "win32" else shlex.join(command))
    else:
        print(f'http://{cfg["host"]}:{cfg["port"]}/mcp')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

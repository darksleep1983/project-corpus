#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

MESSAGES = {
    "en": {
        "ready": "Project Corpus ready: {corpus}",
        "start": "Start the server with start.ps1 or start.sh",
    },
    "ru": {
        "ready": "Project Corpus готов: {corpus}",
        "start": "Запустите сервер через start.ps1 или start.sh",
    },
}


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Create a local Project Corpus")
    parser.add_argument("--project-home", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--language", choices=("en", "ru"), default="en")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    repo = args.repo_root.expanduser().resolve()
    home = args.project_home.expanduser().resolve()
    corpus = home / "Corpus"
    mcp_root = home / "mcp-state"
    template = repo / "template" / args.language
    if not template.is_dir():
        raise SystemExit(f"Template language is unavailable: {args.language}")
    mcp_root.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable, str(repo / "scripts" / "init_corpus.py"),
        "--template", str(template),
        "--destination", str(corpus),
        "--mcp-root", str(mcp_root),
    ]
    if args.force:
        command.append("--force")
    subprocess.run(command, check=True)

    config = {
        "projectHome": str(home),
        "corpusRoot": str(corpus),
        "mcpRoot": str(mcp_root),
        "host": "127.0.0.1",
        "port": 8334,
        "language": args.language,
    }
    (repo / ".project-corpus.local.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    messages = MESSAGES[args.language]
    print(messages["ready"].format(corpus=corpus))
    print(messages["start"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

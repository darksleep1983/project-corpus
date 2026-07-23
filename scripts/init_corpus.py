#!/usr/bin/env python3
"""Initialize a Project Corpus from the reusable template."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

MARKERS = ("{{CORPUS_ROOT}}", "{{MCP_ROOT}}")


def manifest(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.name == "MANIFEST_SHA256.json":
            continue
        result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--mcp-root", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    template = args.template.expanduser().resolve()
    destination = args.destination.expanduser().resolve()
    mcp_root = args.mcp_root.expanduser().resolve()

    if not template.is_dir():
        raise SystemExit(f"Template not found: {template}")
    if destination.exists() and any(destination.iterdir()) and not args.force:
        raise SystemExit("Destination is not empty. Use --force only after reviewing it.")

    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template, destination, dirs_exist_ok=True)

    replacements = {
        "{{CORPUS_ROOT}}": str(destination),
        "{{MCP_ROOT}}": str(mcp_root),
    }
    for path in destination.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for marker, value in replacements.items():
            text = text.replace(marker, value)
        path.write_text(text, encoding="utf-8", newline="\n")

    unresolved = []
    for path in destination.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in MARKERS):
            unresolved.append(str(path))
    if unresolved:
        raise SystemExit("Unresolved markers: " + ", ".join(unresolved))

    data = {
        "format": "project-corpus-sha256-manifest-v1",
        "files": manifest(destination),
    }
    (destination / "MANIFEST_SHA256.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Initialized: {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

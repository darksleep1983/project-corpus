#!/usr/bin/env python3
"""Validate the structure and SHA manifest of a Project Corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REQUIRED = {
    "AGENTS.md",
    "OPERATOR_PROFILE.md",
    "PROJECT_ROADMAP_CURRENT.md",
    "MCP_CONNECTION_CURRENT.md",
    "LOADER_PROMPT_CURRENT.md",
    "SESSION_HANDOFF_CURRENT.md",
    "SESSION_HANDOFF_FULL_CURRENT.md",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    args = parser.parse_args()
    root = args.corpus.expanduser().resolve()

    errors: list[str] = []
    if not root.is_dir():
        raise SystemExit(f"Corpus not found: {root}")

    names = {p.name for p in root.iterdir() if p.is_file()}
    missing = sorted(REQUIRED - names)
    if missing:
        errors.append("Missing current files: " + ", ".join(missing))
    for directory in ("Tasks", "Report"):
        if not (root / directory).is_dir():
            errors.append(f"Missing directory: {directory}")

    for path in root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "{{CORPUS_ROOT}}" in text or "{{MCP_ROOT}}" in text:
            errors.append(f"Unresolved marker: {path.relative_to(root)}")

    manifest_path = root / "MANIFEST_SHA256.json"
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rel, expected in data.get("files", {}).items():
            path = root / rel
            if not path.is_file():
                errors.append(f"Manifest file missing: {rel}")
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                errors.append(f"SHA mismatch: {rel}")

    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())

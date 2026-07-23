from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from typing import Any, Iterable
from uuid import uuid4


class CorpusError(RuntimeError):
    """Policy or filesystem error safe to return to an MCP client."""


@dataclass(frozen=True)
class CorpusConfig:
    corpus_root: Path
    mcp_root: Path
    server_name: str = "project-corpus-mcp"
    server_version: str = "0.1.0"
    write_policy_version: str = "1.0"

    @classmethod
    def from_env(cls) -> "CorpusConfig":
        corpus = os.environ.get("PROJECT_CORPUS_ROOT")
        mcp_root = os.environ.get("PROJECT_CORPUS_MCP_ROOT")
        if not corpus or not mcp_root:
            raise CorpusError("PROJECT_CORPUS_ROOT and PROJECT_CORPUS_MCP_ROOT are required")
        return cls(
            corpus_root=Path(corpus).expanduser().resolve(),
            mcp_root=Path(mcp_root).expanduser().resolve(),
            server_version=os.environ.get("PROJECT_CORPUS_SERVER_VERSION", "0.1.0"),
            write_policy_version=os.environ.get("PROJECT_CORPUS_WRITE_POLICY_VERSION", "1.0"),
        )


class CorpusStore:
    CURRENT_MUTABLE = {
        "PROJECT_ROADMAP_CURRENT.md",
        "MCP_CONNECTION_CURRENT.md",
        "LOADER_PROMPT_CURRENT.md",
        "SESSION_HANDOFF_CURRENT.md",
        "SESSION_HANDOFF_FULL_CURRENT.md",
    }
    PROTECTED_AGENTS = "AGENTS.md"
    PROTECTED_PROFILE = "OPERATOR_PROFILE.md"
    AUTHORIZATION = "EXPLICIT_OWNER_PROTOCOL_CHANGE"

    def __init__(self, config: CorpusConfig):
        self.config = config
        self.root = config.corpus_root
        self.mcp_root = config.mcp_root
        if not self.root.is_dir():
            raise CorpusError(f"Corpus root not found: {self.root}")
        self.root = self.root.resolve()
        self.mcp_root = self.mcp_root.resolve()
        if self.mcp_root == self.root or self.root in self.mcp_root.parents:
            raise CorpusError("MCP state root must be outside the Corpus root")
        self.mcp_root.mkdir(parents=True, exist_ok=True)
        for bucket in ("current", "tasks", "report"):
            (self.mcp_root / "backups" / bucket).mkdir(parents=True, exist_ok=True)
        (self.mcp_root / "audit").mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()

    @staticmethod
    def sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _normalize_relative(value: str) -> str:
        if not value or value.strip() != value:
            raise CorpusError("Path must be a non-empty trimmed relative path")
        if any(ord(ch) < 32 for ch in value):
            raise CorpusError("Control characters are forbidden in paths")
        value = value.replace("\\", "/")
        if value.startswith("/") or value.startswith("//") or ":" in value:
            raise CorpusError("Absolute, UNC, drive, and ADS-like paths are forbidden")
        parts = value.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise CorpusError("Empty, dot, and traversal path segments are forbidden")
        return "/".join(parts)

    def resolve_path(self, relative: str, *, must_exist: bool | None = None) -> Path:
        normalized = self._normalize_relative(relative)
        candidate = self.root.joinpath(*normalized.split("/"))
        parent = candidate.parent.resolve(strict=True)
        try:
            parent.relative_to(self.root)
        except ValueError as exc:
            raise CorpusError("Resolved path escapes corpus root") from exc
        if candidate.exists():
            resolved = candidate.resolve(strict=True)
            try:
                resolved.relative_to(self.root)
            except ValueError as exc:
                raise CorpusError("Resolved path escapes corpus root") from exc
        if must_exist is True and not candidate.exists():
            raise CorpusError("Path does not exist")
        if must_exist is False and candidate.exists():
            raise CorpusError("Path already exists")
        return candidate

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "serverName": self.config.server_name,
            "serverVersion": self.config.server_version,
            "writePolicyVersion": self.config.write_policy_version,
            "corpusRoot": str(self.root),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def list(self, subpath: str = ".") -> dict[str, Any]:
        if subpath == ".":
            target = self.root
        else:
            target = self.resolve_path(subpath, must_exist=True)
        if not target.is_dir():
            raise CorpusError("List target is not a directory")
        entries = []
        for p in sorted(target.iterdir(), key=lambda x: x.name.lower()):
            entries.append({
                "name": p.name,
                "type": "directory" if p.is_dir() else "file",
                "size": p.stat().st_size if p.is_file() else 0,
                "mtime": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
            })
        return {"subpath": subpath, "entries": entries}

    def stat(self, path: str) -> dict[str, Any]:
        target = self.resolve_path(path, must_exist=True)
        if not target.is_file():
            raise CorpusError("Stat target is not a file")
        data = target.read_bytes()
        st = target.stat()
        return {
            "path": self._normalize_relative(path),
            "size": len(data),
            "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
            "sha256": self.sha256_bytes(data),
        }

    def read(self, path: str, offset: int = 0, limit: int = 1_000_000,
             encoding: str = "utf8") -> dict[str, Any]:
        if offset < 0 or limit < 0 or limit > 5_000_000:
            raise CorpusError("Invalid offset or limit")
        target = self.resolve_path(path, must_exist=True)
        if not target.is_file():
            raise CorpusError("Read target is not a file")
        data = target.read_bytes()
        chunk = data[offset:offset + limit]
        if encoding == "utf8":
            content = chunk.decode("utf-8")
        elif encoding == "base64":
            content = base64.b64encode(chunk).decode("ascii")
        else:
            raise CorpusError("encoding must be utf8 or base64")
        return {
            "path": self._normalize_relative(path),
            "offset": offset,
            "returnedBytes": len(chunk),
            "totalBytes": len(data),
            "truncated": offset + len(chunk) < len(data),
            "encoding": encoding,
            "content": content,
            "fullFileSha256": self.sha256_bytes(data),
        }

    def read_many(self, paths: Iterable[str]) -> dict[str, Any]:
        requested = list(paths)
        if len(requested) > 50:
            raise CorpusError("Too many paths; maximum is 50")
        results = []
        total = 0
        max_total = 5_000_000
        for path in requested:
            try:
                item = self.read(path, limit=max_total - total)
                total += item["returnedBytes"]
                results.append({"status": "ok", **item})
                if total >= max_total:
                    break
            except Exception as exc:
                results.append({"path": path, "status": "error", "error": str(exc)})
        return {"count": len(results), "totalBytes": total, "results": results}

    def search(self, query: str, mode: str = "both", max_results: int = 100) -> dict[str, Any]:
        if not query or len(query) > 500:
            raise CorpusError("Invalid query")
        if mode not in {"filename", "text", "both"}:
            raise CorpusError("mode must be filename, text, or both")
        max_results = max(1, min(max_results, 500))
        needle = query.casefold()
        results = []
        for path in sorted(self.root.rglob("*")):
            if len(results) >= max_results:
                break
            if not path.is_file() or path.is_symlink():
                continue
            rel = path.relative_to(self.root).as_posix()
            if mode in {"filename", "both"} and needle in rel.casefold():
                results.append({"path": rel, "matchType": "filename", "snippet": rel})
                continue
            if mode in {"text", "both"} and path.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml"}:
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                index = text.casefold().find(needle)
                if index >= 0:
                    start = max(0, index - 80)
                    end = min(len(text), index + len(query) + 120)
                    results.append({"path": rel, "matchType": "text", "snippet": text[start:end]})
        return {"query": query, "mode": mode, "count": len(results), "results": results}

    def _classify_write_path(self, path: str) -> tuple[str, str]:
        normalized = self._normalize_relative(path)
        parts = normalized.split("/")
        if len(parts) == 1:
            name = parts[0]
            if name == self.PROTECTED_PROFILE:
                raise CorpusError("OPERATOR_PROFILE.md is not writable")
            if name == self.PROTECTED_AGENTS:
                return "agents", normalized
            if name in self.CURRENT_MUTABLE:
                return "current", normalized
            raise CorpusError("Root file is not writable")
        if len(parts) == 2 and parts[0] in {"Tasks", "Report"}:
            if not parts[1].lower().endswith(".md"):
                raise CorpusError("Scoped files must be Markdown")
            return ("tasks" if parts[0] == "Tasks" else "report"), normalized
        raise CorpusError("Nested scoped paths are forbidden")

    def _audit(self, receipt: dict[str, Any]) -> None:
        line = json.dumps(receipt, ensure_ascii=False, separators=(",", ":")) + "\n"
        audit_path = self.mcp_root / "audit" / "receipts.jsonl"
        with audit_path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())

    def write(self, *, path: str, content: str, operation: str = "update",
              encoding: str = "utf8", expected_sha256: str | None = None,
              authorization: str | None = None) -> dict[str, Any]:
        # One authoritative server process serializes writes. The expected hash
        # still protects against stale clients; the lock closes the in-process
        # check-to-replace race.
        with self._write_lock:
            return self._write_unlocked(
                path=path, content=content, operation=operation, encoding=encoding,
                expected_sha256=expected_sha256, authorization=authorization,
            )

    def _write_unlocked(self, *, path: str, content: str, operation: str = "update",
                        encoding: str = "utf8", expected_sha256: str | None = None,
                        authorization: str | None = None) -> dict[str, Any]:
        kind, normalized = self._classify_write_path(path)
        if encoding == "utf8":
            new_bytes = content.encode("utf-8")
        elif encoding == "base64":
            try:
                new_bytes = base64.b64decode(content, validate=True)
            except Exception as exc:
                raise CorpusError("Invalid base64 content") from exc
        else:
            raise CorpusError("encoding must be utf8 or base64")

        if len(new_bytes) > 5_000_000:
            raise CorpusError("Content exceeds the 5 MB write limit")
        if operation not in {"create", "update"}:
            raise CorpusError("operation must be create or update")
        target = self.resolve_path(normalized, must_exist=(operation == "update"))
        if operation == "create":
            if kind not in {"tasks", "report"}:
                raise CorpusError("Create is permitted only in Tasks or Report")
            if expected_sha256 is not None:
                raise CorpusError("expected_sha256 must be omitted for create")
        else:
            if expected_sha256 is None or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
                raise CorpusError("A full expected_sha256 is required for update")
            if kind == "agents" and authorization != self.AUTHORIZATION:
                raise CorpusError("Protected AGENTS.md update requires explicit authorization")

        old_bytes = target.read_bytes() if target.exists() else None
        old_sha = self.sha256_bytes(old_bytes) if old_bytes is not None else None
        if operation == "update" and old_sha != expected_sha256.lower():
            raise CorpusError("STALE_EXPECTED_SHA256")

        backup_path = None
        backup_sha = None
        if old_bytes is not None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
            backup_bucket = "current" if kind == "agents" else kind
            bucket = self.mcp_root / "backups" / backup_bucket
            backup_path = bucket / f"{target.name}.{timestamp}.{old_sha[:12]}.bak"
            backup_path.write_bytes(old_bytes)
            backup_sha = self.sha256_bytes(backup_path.read_bytes())
            if backup_sha != old_sha:
                backup_path.unlink(missing_ok=True)
                raise CorpusError("BACKUP_VERIFICATION_FAILED")

        temp_name = f".{target.name}.{uuid4().hex}.tmp"
        temp_path = target.parent / temp_name
        try:
            with temp_path.open("xb") as fh:
                fh.write(new_bytes)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(temp_path, target)
            readback = target.read_bytes()
            new_sha = self.sha256_bytes(new_bytes)
            readback_sha = self.sha256_bytes(readback)
            if readback_sha != new_sha:
                if old_bytes is not None:
                    target.write_bytes(old_bytes)
                else:
                    target.unlink(missing_ok=True)
                raise CorpusError("READBACK_VERIFICATION_FAILED")
        finally:
            temp_path.unlink(missing_ok=True)

        receipt = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "receiptId": str(uuid4()),
            "tool": "corpus_write",
            "operation": operation,
            "policyKind": kind,
            "path": normalized,
            "oldSha256": old_sha,
            "newSha256": new_sha,
            "backupPath": str(backup_path) if backup_path else None,
            "backupSha256": backup_sha,
            "readbackSha256": readback_sha,
            "status": "ok",
        }
        try:
            self._audit(receipt)
        except Exception as exc:
            # A write without its required receipt is not considered published.
            # Roll back atomically where possible.
            if old_bytes is None:
                target.unlink(missing_ok=True)
            else:
                rollback_temp = target.parent / f".{target.name}.{uuid4().hex}.rollback"
                try:
                    with rollback_temp.open("xb") as fh:
                        fh.write(old_bytes)
                        fh.flush()
                        os.fsync(fh.fileno())
                    os.replace(rollback_temp, target)
                finally:
                    rollback_temp.unlink(missing_ok=True)
            raise CorpusError("AUDIT_RECEIPT_FAILED_ROLLED_BACK") from exc
        return {
            "operation": operation,
            "path": normalized,
            "oldSha256": old_sha,
            "newSha256": new_sha,
            "backupPath": str(backup_path) if backup_path else None,
            "backupSha256": backup_sha,
            "readbackSha256": readback_sha,
            "auditReceipt": receipt,
            "bytesWritten": len(new_bytes),
        }

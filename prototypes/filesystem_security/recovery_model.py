from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil


PHASES = ("STAGED", "BACKED_UP", "PUBLISHED", "VERIFIED", "AUDITED")


class InjectedCrash(RuntimeError):
    pass


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_journal(path: Path, record: dict[str, str]) -> None:
    path.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")


def simulate_transaction(area: Path, data: bytes, crash_after: str | None) -> None:
    """Small crash model; not a confinement or production transaction API."""
    target = area / "STATUS.md"
    stage = area / ".stage"
    backup = area / ".backup"
    journal = area / ".journal"
    audit = area / ".audit"
    record = {
        "old": _hash(target),
        "new": hashlib.sha256(data).hexdigest(),
        "phase": "STAGED",
    }
    stage.write_bytes(data)
    _write_journal(journal, record)
    if crash_after == "STAGED":
        raise InjectedCrash(crash_after)
    shutil.copyfile(target, backup)
    record["phase"] = "BACKED_UP"
    _write_journal(journal, record)
    if crash_after == "BACKED_UP":
        raise InjectedCrash(crash_after)
    os.replace(stage, target)
    record["phase"] = "PUBLISHED"
    _write_journal(journal, record)
    if crash_after == "PUBLISHED":
        raise InjectedCrash(crash_after)
    if _hash(target) != record["new"]:
        raise RuntimeError("verification mismatch")
    record["phase"] = "VERIFIED"
    _write_journal(journal, record)
    if crash_after == "VERIFIED":
        raise InjectedCrash(crash_after)
    audit.write_text(record["new"] + "\n", encoding="ascii")
    record["phase"] = "AUDITED"
    _write_journal(journal, record)
    if crash_after == "AUDITED":
        raise InjectedCrash(crash_after)
    backup.unlink()
    journal.unlink()


def recover(area: Path) -> str:
    target = area / "STATUS.md"
    stage = area / ".stage"
    backup = area / ".backup"
    journal = area / ".journal"
    audit = area / ".audit"
    record = json.loads(journal.read_text(encoding="utf-8"))
    phase = record["phase"]
    actual = _hash(target)
    if phase in {"STAGED", "BACKED_UP"}:
        if actual != record["old"]:
            return "NEEDS_OWNER"
        stage.unlink(missing_ok=True)
        backup.unlink(missing_ok=True)
        journal.unlink()
        return "ROLLED_BACK"
    if actual != record["new"]:
        return "NEEDS_OWNER"
    if phase == "PUBLISHED":
        record["phase"] = "VERIFIED"
        _write_journal(journal, record)
    if phase in {"PUBLISHED", "VERIFIED"}:
        audit.write_text(record["new"] + "\n", encoding="ascii")
        record["phase"] = "AUDITED"
        _write_journal(journal, record)
    if audit.read_text(encoding="ascii").strip() != record["new"]:
        return "NEEDS_OWNER"
    stage.unlink(missing_ok=True)
    backup.unlink(missing_ok=True)
    journal.unlink()
    return "COMPLETED_AFTER_RECOVERY"

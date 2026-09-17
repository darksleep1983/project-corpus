from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import subprocess


class SecurityScanError(RuntimeError):
    pass


@dataclass(frozen=True)
class Finding:
    category: str
    rule: str
    location_kind: str
    object_id: str | None
    object_type: str | None
    path: str | None


@dataclass(frozen=True)
class ScanReport:
    format: str
    repository: str
    coverage_complete: bool
    shallow_repository: bool
    refs_scanned: tuple[str, ...]
    object_count: int
    reachable_object_count: int
    unreachable_object_count: int
    commit_patch_count: int
    working_tree_file_count: int
    findings: tuple[Finding, ...]
    limitations: tuple[str, ...]

    @property
    def release_gate_pass(self) -> bool:
        return self.coverage_complete and not self.findings

    def public_receipt(self) -> dict[str, object]:
        value = asdict(self)
        value["release_gate_pass"] = self.release_gate_pass
        return value


RULES: tuple[tuple[str, str, re.Pattern[bytes]], ...] = (
    ("credential", "aws-access-key-id", re.compile(b"AKIA" + b"[0-9A-Z]{16}")),
    ("token", "github-token", re.compile(b"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("token", "slack-token", re.compile(b"xox[baprs]-[A-Za-z0-9-]{16,}")),
    ("credential", "private-key", re.compile(b"-----BEGIN " + b"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("token", "jwt", re.compile(rb"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("credential", "credential-assignment", re.compile(
        b"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd)"
        b"[ \t]{0,8}(?:=|:)[ \t]{0,8}[\"']?[A-Za-z0-9_./+=-]{12,}"
    )),
    ("private_url", "url-embedded-credential", re.compile(
        rb"(?i)https?://[^\s/:@]{1,64}:[^\s/@]{1,128}@"
    )),
    ("private_url", "private-network-url", re.compile(
        rb"(?i)https?://(?:localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
        rb"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|[^\s/:]+\.(?:local|internal|lan|corp))(?::\d+)?"
    )),
    ("personal_infrastructure", "windows-user-path", re.compile(
        rb"(?i)[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"']+"
    )),
    ("personal_infrastructure", "posix-user-path", re.compile(
        rb"/(?:home|Users)/[^/\s\"']+"
    )),
)


def _git(root: Path, *arguments: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *arguments], cwd=root, input=input_bytes,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise SecurityScanError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def _scan_bytes(
    content: bytes, *, location_kind: str, object_id: str | None,
    object_type: str | None, path: str | None,
) -> list[Finding]:
    return [
        Finding(category, rule, location_kind, object_id, object_type, path)
        for category, rule, pattern in RULES if pattern.search(content)
    ]


def _all_objects(root: Path) -> list[tuple[str, str, bytes]]:
    raw = _git(root, "cat-file", "--batch-all-objects", "--batch")
    objects: list[tuple[str, str, bytes]] = []
    offset = 0
    while offset < len(raw):
        end = raw.find(b"\n", offset)
        if end < 0:
            raise SecurityScanError("truncated cat-file header")
        header = raw[offset:end].decode("ascii", "strict").split()
        if len(header) != 3:
            raise SecurityScanError("unexpected cat-file header")
        object_id, object_type, size_text = header
        size = int(size_text)
        start = end + 1
        finish = start + size
        if finish >= len(raw) or raw[finish:finish + 1] != b"\n":
            raise SecurityScanError("truncated cat-file object")
        objects.append((object_id, object_type, raw[start:finish]))
        offset = finish + 1
    return objects


def scan_git_history(root: Path) -> ScanReport:
    root = root.resolve()
    repository = _git(root, "rev-parse", "--show-toplevel").decode().strip()
    if Path(repository).resolve() != root:
        raise SecurityScanError("scan root must be the repository top level")
    shallow = _git(root, "rev-parse", "--is-shallow-repository").strip() == b"true"
    refs = tuple(sorted(filter(None, _git(
        root, "for-each-ref", "--format=%(refname)"
    ).decode().splitlines())))
    reachable_rows = _git(root, "rev-list", "--objects", "--all").decode(
        "utf-8", "surrogateescape"
    ).splitlines()
    reachable: set[str] = set()
    paths: dict[str, set[str]] = {}
    for row in reachable_rows:
        object_id, separator, path = row.partition(" ")
        reachable.add(object_id)
        if separator:
            paths.setdefault(object_id, set()).add(path)

    objects = _all_objects(root)
    findings: list[Finding] = []
    commit_ids: list[str] = []
    for object_id, object_type, content in objects:
        object_paths = sorted(paths.get(object_id, {None}), key=lambda item: item or "")
        for path in object_paths:
            findings.extend(_scan_bytes(
                content, location_kind="git_object", object_id=object_id,
                object_type=object_type, path=path,
            ))
        if object_type == "commit":
            commit_ids.append(object_id)

    for ref in refs:
        findings.extend(_scan_bytes(
            ref.encode(), location_kind="git_ref", object_id=None,
            object_type="ref", path=ref,
        ))

    patch_count = 0
    for commit_id in sorted(commit_ids):
        patch = _git(
            root, "show", "--format=fuller", "--binary", "--find-renames",
            "--find-copies", "--no-ext-diff", commit_id,
        )
        patch_count += 1
        findings.extend(_scan_bytes(
            patch, location_kind="commit_patch", object_id=commit_id,
            object_type="commit", path=None,
        ))

    working_count = 0
    for path in sorted(root.rglob("*")):
        if (
            not path.is_file()
            or ".git" in path.parts
            or "__pycache__" in path.parts
            or path.suffix in {".pyc", ".pyo"}
        ):
            continue
        relative = path.relative_to(root).as_posix()
        working_count += 1
        findings.extend(_scan_bytes(
            path.read_bytes(), location_kind="working_tree", object_id=None,
            object_type="file", path=relative,
        ))

    unique = {
        (
            item.category, item.rule, item.location_kind, item.object_id,
            item.object_type, item.path,
        ): item for item in findings
    }
    limitations = (
        "Scans only objects and refs present in the local object database.",
        "Server-side objects not transferred through refs/object transfer are unavailable.",
        "Pattern scanning can require human classification of non-secret private-infrastructure references.",
    )
    return ScanReport(
        "project-corpus-release-security-scan-v1", str(root), not shallow,
        shallow, refs, len(objects), len(reachable),
        len({item[0] for item in objects} - reachable), patch_count,
        working_count,
        tuple(sorted(unique.values(), key=lambda item: (
            item.category, item.rule, item.location_kind,
            item.path or "", item.object_id or "",
        ))),
        limitations,
    )

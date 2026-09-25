from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

from .authority import RUNTIME_HARD_LIMITS, evaluate_authority
from .compatibility import load_v1_corpus
from .context import build_index, open_index, query_index, compile_bundle, memory_doctor, evaluate_dataset, validate_candidate
from .context.index import collect
from .context.schema import ContextError
from .discovery import search, show, timeline
from .doctor import doctor
from .migration import (
    apply_migration, authorize_migration, load_migration_authorization,
    plan_v1_migration,
)
from .mcp_stdio import run_stdio
from .platform import open_native_backend
from .policy import parse_project_policy
from .security_scan import scan_git_history
from .transactions import ABSENT, MAX_MANAGED_BYTES, TransactionEngine, path_matches_scopes
from .trust import (
    TrustGrant, load_trust_grant, provision_runtime_state, runtime_state_path,
    write_trust_grant,
)
from .validation import parse_document, validate_state_pair, validate_v2_project


ARTIFACT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _json(value: object, *, stream=None) -> None:
    if stream is None:
        stream = sys.stdout
    stream.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def _discovery_limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("limit must be an integer between 1 and 100") from exc
    if not 1 <= limit <= 100:
        raise argparse.ArgumentTypeError("limit must be between 1 and 100")
    return limit


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))


def _require_disjoint(left: Path, right: Path, code: str) -> None:
    left_path = left.resolve()
    right_path = right.resolve()
    try:
        common = Path(os.path.commonpath((left_path, right_path)))
    except ValueError:
        return
    if _same_path(common, left_path) or _same_path(common, right_path):
        raise ValueError(code)


def _qualified_project_policy(root: Path, backend):
    validation = validate_v2_project(root)
    if not validation.valid:
        codes = sorted({item.code for item in validation.issues if item.severity == "ERROR"})
        raise ValueError(f"project is not V2-conformant: {codes}")
    backend.read_bytes("AGENTS.md", max_bytes=MAX_MANAGED_BYTES)
    project = backend.read_bytes(
        ".project-corpus/state/PROJECT.md", max_bytes=MAX_MANAGED_BYTES
    )
    status = backend.read_bytes(
        ".project-corpus/state/STATUS.md", max_bytes=MAX_MANAGED_BYTES
    )
    state_issues = validate_state_pair(project, status)
    if any(item.severity == "ERROR" for item in state_issues):
        raise ValueError("native state validation failed")
    policy = parse_project_policy(
        backend.read_bytes(".project-corpus/policy.toml", max_bytes=1024 * 1024)
    )
    project_id = parse_document(
        project, ".project-corpus/state/PROJECT.md"
    ).metadata.get("Project-ID")
    if validation.project_id != project_id or policy.project_id != project_id:
        raise ValueError("project id differs across canonical documents")
    return policy


def _trust(args: argparse.Namespace) -> tuple[Path, TrustGrant]:
    path = Path(args.trust).absolute()
    grant = load_trust_grant(path)
    _require_disjoint(grant.physical_root, path, "TRUST_GRANT_NOT_EXTERNAL")
    return path, grant


def _engine(args: argparse.Namespace, capability: str) -> TransactionEngine:
    trust_path, trust = _trust(args)
    return TransactionEngine(
        trust=trust,
        runtime_state_root=runtime_state_path(trust_path, trust.project_id),
        session_capabilities={capability},
        transport="cli",
    )


def _cmd_search(args: argparse.Namespace) -> object:
    return search(Path(args.root), args.query, artifact_type=args.artifact_type, limit=args.limit)


def _cmd_timeline(args: argparse.Namespace) -> object:
    return timeline(Path(args.root), args.selector)


def _cmd_show(args: argparse.Namespace) -> object:
    return show(Path(args.root), args.artifact)


def _cmd_doctor(args: argparse.Namespace) -> object:
    return asdict(
        doctor(
            Path(args.root),
            trust_grant_path=Path(args.trust) if args.trust else None,
        )
    )


def _cmd_validate(args: argparse.Namespace) -> object:
    result = validate_v2_project(Path(args.root))
    return {
        "ok": result.valid,
        "project_id": result.project_id,
        "issues": [asdict(item) for item in result.issues],
        "guarantee_level": "DIRECT_FOLDER_OBSERVABLE",
    }


def _cmd_migration_plan(args: argparse.Namespace) -> object:
    snapshot = load_v1_corpus(Path(args.root))
    return plan_v1_migration(
        snapshot, project_id=args.project_id, logical_name=args.logical_name
    ).public_receipt()


def _cmd_migration_authorize(args: argparse.Namespace) -> object:
    source = Path(args.root).absolute()
    destination = Path(args.destination).absolute()
    authorization_path = Path(args.authorization).absolute()
    _require_disjoint(source, destination, "MIGRATION_DESTINATION_NOT_SEPARATE")
    _require_disjoint(source, authorization_path, "MIGRATION_AUTH_NOT_EXTERNAL")
    _require_disjoint(destination, authorization_path, "MIGRATION_AUTH_NOT_EXTERNAL")
    authorization = authorize_migration(
        source, destination, authorization_path,
        project_id=args.project_id, logical_name=args.logical_name,
    )
    return {
        "ok": True,
        "project_id": authorization.project_id,
        "plan_sha256": authorization.plan_sha256,
        "destination_name": authorization.destination_name,
        "filesystem": authorization.filesystem,
        "warnings_acknowledged": True,
    }


def _cmd_migration_apply(args: argparse.Namespace) -> object:
    source = Path(args.root).absolute()
    authorization_path = Path(args.authorization).absolute()
    trust_path = Path(args.trust).absolute()
    authorization = load_migration_authorization(authorization_path)
    destination = authorization.destination_parent / authorization.destination_name
    _require_disjoint(source, destination, "MIGRATION_DESTINATION_NOT_SEPARATE")
    _require_disjoint(source, authorization_path, "MIGRATION_AUTH_NOT_EXTERNAL")
    _require_disjoint(destination, authorization_path, "MIGRATION_AUTH_NOT_EXTERNAL")
    _require_disjoint(destination, trust_path, "TRUST_GRANT_NOT_EXTERNAL")
    capabilities = frozenset(args.allow or ())
    outside = capabilities - RUNTIME_HARD_LIMITS
    if outside or "migration.apply" in capabilities:
        raise ValueError("invalid post-migration capability ceiling")
    return apply_migration(
        source, authorization_path, trust_path, capabilities=capabilities
    )


def _cmd_trust_create(args: argparse.Namespace) -> object:
    root = Path(args.root).absolute()
    trust_path = Path(args.trust).absolute()
    _require_disjoint(root, trust_path, "TRUST_GRANT_NOT_EXTERNAL")
    capabilities = frozenset(args.allow or ())
    outside = capabilities - RUNTIME_HARD_LIMITS
    if outside:
        raise ValueError(f"capabilities outside runtime hard limits: {sorted(outside)}")
    with open_native_backend(root) as backend:
        policy = _qualified_project_policy(root, backend)
        grant = TrustGrant(
            project_id=policy.project_id,
            physical_root=root,
            root_identity=backend.root_identity,
            policy_sha256=policy.digest,
            capability_ceiling=capabilities,
            filesystem=backend.filesystem,
            transports=frozenset(args.transport or ("cli",)),
            approved_at=_now(),
            protocol_version="2.0",
        )
    write_trust_grant(trust_path, grant, replace=False)
    return {
        "ok": True,
        "project_id": grant.project_id,
        "trust_path": str(trust_path),
        "root_identity": grant.root_identity,
        "filesystem": grant.filesystem,
        "capability_ceiling": sorted(grant.capability_ceiling),
    }


def _cmd_trust_approve(args: argparse.Namespace) -> object:
    trust_path, grant = _trust(args)
    with open_native_backend(grant.physical_root) as backend:
        if backend.root_identity != grant.root_identity or backend.filesystem != grant.filesystem:
            raise ValueError("root identity or filesystem changed")
        policy = _qualified_project_policy(grant.physical_root, backend)
    if policy.project_id != grant.project_id:
        raise ValueError("project id changed")
    updated = replace(grant, policy_sha256=policy.digest, approved_at=_now())
    write_trust_grant(trust_path, updated, replace=True)
    return {"ok": True, "project_id": updated.project_id, "policy_sha256": updated.policy_sha256}


def _cmd_runtime_init(args: argparse.Namespace) -> object:
    trust_path, grant = _trust(args)
    state = runtime_state_path(trust_path, grant.project_id)
    _require_disjoint(grant.physical_root, state, "RUNTIME_STATE_NOT_EXTERNAL")
    if grant.protocol_version != "2.0":
        raise ValueError("unsupported trusted protocol version")
    with open_native_backend(grant.physical_root) as project:
        if (
            project.root_identity != grant.root_identity or
            project.filesystem != grant.filesystem
        ):
            raise ValueError("root identity or filesystem changed")
        policy = _qualified_project_policy(grant.physical_root, project)
        if policy.project_id != grant.project_id or policy.digest != grant.policy_sha256:
            raise ValueError("trusted project identity or policy digest changed")
    provision_runtime_state(state)
    with open_native_backend(state) as backend:
        filesystem = backend.filesystem
    return {"ok": True, "runtime_state": str(state), "filesystem": filesystem}


def _cmd_mutate(args: argparse.Namespace, capability: str, target: str) -> object:
    content = Path(args.input).read_bytes()
    expected = args.expected_sha256 if capability == "state.update" else ABSENT
    with _engine(args, capability) as runtime:
        return asdict(runtime.mutate(
            capability=capability, target=target, content=content,
            expected_sha256=expected,
        ))


def _cmd_recover(args: argparse.Namespace) -> object:
    with _engine(args, "state.update") as runtime:
        result = runtime.recover()
    return {"result": None if result is None else asdict(result)}


def _controlled_read(args: argparse.Namespace, capability: str) -> object:
    _, trust = _trust(args)
    if trust.protocol_version != "2.0":
        raise ValueError("unsupported trusted protocol version")
    with open_native_backend(trust.physical_root) as backend:
        if backend.filesystem != trust.filesystem:
            raise ValueError("trusted filesystem changed")
        policy = parse_project_policy(
            backend.read_bytes(".project-corpus/policy.toml", max_bytes=1024 * 1024)
        )
        decision = evaluate_authority(
            trust=trust, policy=policy, session_capabilities={capability},
            observed_root_identity=backend.root_identity, transport="cli",
        )
        if not decision.permits(capability):
            raise PermissionError(f"capability denied: {capability}")
        if not path_matches_scopes(args.path, policy.read_scopes):
            raise PermissionError(f"read scope denied: {args.path}")
        stat = backend.stat(args.path)
        value: dict[str, object] = {"stat": asdict(stat)}
        if capability in {"corpus.read", "audit.read"}:
            content = backend.read_bytes(args.path, max_bytes=MAX_MANAGED_BYTES)
            value["content"] = content.decode("utf-8")
        return value


def _cmd_audit_read(args: argparse.Namespace) -> object:
    if not re.fullmatch(r"[0-9a-f]{32}", args.transaction_id):
        raise ValueError("transaction id must be 32 lowercase hexadecimal characters")
    args.path = f".project-corpus/audit/{args.transaction_id}.json"
    return _controlled_read(args, "audit.read")


def _cmd_mcp(args: argparse.Namespace) -> None:
    capabilities = frozenset(args.allow or ())
    outside = capabilities - RUNTIME_HARD_LIMITS
    if outside:
        raise ValueError(f"capabilities outside runtime hard limits: {sorted(outside)}")
    run_stdio(Path(args.trust), capabilities)


def _cmd_security_scan(args: argparse.Namespace) -> object:
    report = scan_git_history(Path(args.root))
    args.result_exit_code = 0 if report.release_gate_pass else 3
    return report.public_receipt()


def _scoped_json(root: str, name: str) -> object:
    base = Path(root).resolve(strict=True)
    path = Path(name).absolute()
    if path.is_symlink() or not path.resolve(strict=False).is_relative_to(base):
        raise ContextError("CONTEXT_INPUT_PATH", "JSON input must be a regular file inside project root")
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ContextError("CONTEXT_INPUT_PATH", "JSON input must be a file of at most 1 MiB")
    return json.loads(path.read_text(encoding="utf-8"))


def _cmd_context(args: argparse.Namespace) -> object:
    if args.context_command == "build":
        return build_index(args.root, args.index)
    if args.context_command == "doctor":
        return memory_doctor(args.root, index=args.index)
    if args.context_command == "candidate-validate":
        return validate_candidate(collect(args.root), _scoped_json(args.root, args.input))
    corpus = open_index(args.root, args.index)
    if args.context_command == "query":
        return query_index(corpus, args.query, limit=args.limit)
    if args.context_command == "bundle":
        return compile_bundle(corpus, args.query, max_tokens=args.max_tokens)
    return evaluate_dataset(corpus, _scoped_json(args.root, args.dataset))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project-corpus")
    commands = parser.add_subparsers(dest="command", required=True)

    command = commands.add_parser("doctor")
    command.add_argument("root")
    command.add_argument("--trust")
    command.set_defaults(handler=_cmd_doctor)

    command = commands.add_parser("validate")
    command.add_argument("root")
    command.set_defaults(handler=_cmd_validate)

    command = commands.add_parser("search")
    command.add_argument("root")
    command.add_argument("query")
    command.add_argument("--type", dest="artifact_type", choices=("state", "task", "report", "history"))
    command.add_argument("--limit", type=_discovery_limit, default=20)
    command.set_defaults(handler=_cmd_search)
    command = commands.add_parser("timeline")
    command.add_argument("root")
    command.add_argument("selector")
    command.set_defaults(handler=_cmd_timeline)
    command = commands.add_parser("show")
    command.add_argument("root")
    command.add_argument("artifact")
    command.set_defaults(handler=_cmd_show)

    context = commands.add_parser("context").add_subparsers(dest="context_command", required=True)
    command = context.add_parser("build")
    command.add_argument("root")
    command.add_argument("--index", required=True)
    command.set_defaults(handler=_cmd_context)
    command = context.add_parser("query")
    command.add_argument("root")
    command.add_argument("query")
    command.add_argument("--index", required=True)
    command.add_argument("--limit", type=_discovery_limit, default=20)
    command.set_defaults(handler=_cmd_context)
    command = context.add_parser("bundle")
    command.add_argument("root")
    command.add_argument("query")
    command.add_argument("--index", required=True)
    command.add_argument("--max-tokens", type=int, default=1200)
    command.set_defaults(handler=_cmd_context)
    command = context.add_parser("doctor")
    command.add_argument("root")
    command.add_argument("--index", required=True)
    command.set_defaults(handler=_cmd_context)
    command = context.add_parser("eval")
    command.add_argument("root")
    command.add_argument("--index", required=True)
    command.add_argument("--dataset", required=True)
    command.set_defaults(handler=_cmd_context)
    command = context.add_parser("candidate-validate")
    command.add_argument("root")
    command.add_argument("--input", required=True)
    command.set_defaults(handler=_cmd_context)

    migration = commands.add_parser("migration").add_subparsers(dest="migration", required=True)
    command = migration.add_parser("plan")
    command.add_argument("root")
    command.add_argument("--project-id", required=True)
    command.add_argument("--logical-name", required=True)
    command.set_defaults(handler=_cmd_migration_plan)
    command = migration.add_parser("authorize")
    command.add_argument("root")
    command.add_argument("--destination", required=True)
    command.add_argument("--authorization", required=True)
    command.add_argument("--project-id", required=True)
    command.add_argument("--logical-name", required=True)
    command.set_defaults(handler=_cmd_migration_authorize)
    command = migration.add_parser("apply")
    command.add_argument("root")
    command.add_argument("--authorization", required=True)
    command.add_argument("--trust", required=True)
    command.add_argument("--allow", action="append", default=[])
    command.set_defaults(handler=_cmd_migration_apply)

    trust = commands.add_parser("trust").add_subparsers(dest="trust_command", required=True)
    command = trust.add_parser("create")
    command.add_argument("root")
    command.add_argument("--trust", required=True)
    command.add_argument("--allow", action="append", default=[])
    command.add_argument("--transport", action="append", choices=("cli", "stdio-mcp"))
    command.set_defaults(handler=_cmd_trust_create)
    command = trust.add_parser("approve-policy")
    command.add_argument("--trust", required=True)
    command.set_defaults(handler=_cmd_trust_approve)

    runtime = commands.add_parser("runtime").add_subparsers(dest="runtime_command", required=True)
    command = runtime.add_parser("init")
    command.add_argument("--trust", required=True)
    command.set_defaults(handler=_cmd_runtime_init)
    command = runtime.add_parser("recover")
    command.add_argument("--trust", required=True)
    command.set_defaults(handler=_cmd_recover)

    state = commands.add_parser("state").add_subparsers(dest="state_command", required=True)
    command = state.add_parser("update")
    command.add_argument("--trust", required=True)
    command.add_argument("--input", required=True)
    command.add_argument("--expected-sha256", required=True)
    command.set_defaults(
        handler=lambda args: _cmd_mutate(
            args, "state.update", ".project-corpus/state/STATUS.md"
        )
    )

    for noun, capability, directory in (
        ("task", "task.create", "tasks"),
        ("report", "report.create", "reports"),
    ):
        group = commands.add_parser(noun).add_subparsers(dest=f"{noun}_command", required=True)
        command = group.add_parser("create")
        command.add_argument("--trust", required=True)
        command.add_argument("--input", required=True)
        command.add_argument("--id", required=True)
        command.set_defaults(
            handler=lambda args, cap=capability, folder=directory: (
                _cmd_mutate(args, cap, _artifact_target(folder, args.id))
            )
        )

    for name, capability in (("read", "corpus.read"), ("stat", "corpus.stat")):
        command = commands.add_parser(name)
        command.add_argument("--trust", required=True)
        command.add_argument("--path", required=True)
        command.set_defaults(handler=lambda args, cap=capability: _controlled_read(args, cap))

    command = commands.add_parser("audit-read")
    command.add_argument("--trust", required=True)
    command.add_argument("--transaction-id", required=True)
    command.set_defaults(handler=_cmd_audit_read)

    command = commands.add_parser("mcp")
    command.add_argument("--trust", required=True)
    command.add_argument("--allow", action="append", default=[])
    command.set_defaults(handler=_cmd_mcp)

    security = commands.add_parser("security").add_subparsers(
        dest="security_command", required=True
    )
    command = security.add_parser("scan-history")
    command.add_argument("root")
    command.set_defaults(handler=_cmd_security_scan)
    return parser


def _artifact_target(directory: str, artifact_id: str) -> str:
    if not ARTIFACT_ID.fullmatch(artifact_id):
        raise ValueError("artifact id is not portable")
    return f".project-corpus/{directory}/{artifact_id}.md"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        result = args.handler(args)
        if result is not None:
            _json(result)
        return getattr(args, "result_exit_code", 0)
    except (OSError, UnicodeError, ValueError, RuntimeError, PermissionError) as exc:
        _json(
            {
                "ok": False,
                "error": getattr(exc, "code", type(exc).__name__),
                "detail": getattr(exc, "detail", str(exc)),
            },
            stream=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

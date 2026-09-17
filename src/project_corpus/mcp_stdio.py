from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import re
import sys
from typing import TextIO

from .authority import evaluate_authority
from .platform import open_native_backend
from .policy import parse_project_policy
from .transactions import ABSENT, MAX_MANAGED_BYTES, TransactionEngine, path_matches_scopes
from .trust import load_trust_grant, runtime_state_path


PROTOCOL_VERSION = "2025-11-25"
SUPPORTED_PROTOCOLS = frozenset({"2025-11-25", "2025-06-18", "2024-11-05"})
ARTIFACT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
TRANSACTION_ID = re.compile(r"^[0-9a-f]{32}$")


def _schema(properties: dict[str, object], required: tuple[str, ...]) -> dict[str, object]:
    return {
        "type": "object", "properties": properties,
        "required": list(required), "additionalProperties": False,
    }


TOOLS: dict[str, dict[str, object]] = {
    "corpus.read": {
        "capability": "corpus.read",
        "description": "Read one UTF-8 project file within project-policy read scopes.",
        "inputSchema": _schema({"path": {"type": "string"}}, ("path",)),
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    "corpus.stat": {
        "capability": "corpus.stat",
        "description": "Return size, SHA-256 and native identity for one scoped file.",
        "inputSchema": _schema({"path": {"type": "string"}}, ("path",)),
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    "state.update": {
        "capability": "state.update",
        "description": "Update canonical STATUS with required optimistic-concurrency hash.",
        "inputSchema": _schema({
            "content": {"type": "string"},
            "expected_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        }, ("content", "expected_sha256")),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    },
    "task.create": {
        "capability": "task.create",
        "description": "Create one conforming Task artifact; existing targets are never replaced.",
        "inputSchema": _schema({
            "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9._-]{2,63}$"},
            "content": {"type": "string"},
        }, ("id", "content")),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    },
    "report.create": {
        "capability": "report.create",
        "description": "Create one conforming Report artifact; existing targets are never replaced.",
        "inputSchema": _schema({
            "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9._-]{2,63}$"},
            "content": {"type": "string"},
        }, ("id", "content")),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    },
    "audit.read": {
        "capability": "audit.read",
        "description": "Read one transaction audit receipt by its hexadecimal transaction id.",
        "inputSchema": _schema({"transaction_id": {"type": "string", "pattern": "^[0-9a-f]{32}$"}}, ("transaction_id",)),
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
}


class McpRuntime:
    def __init__(self, trust_path: Path, session_capabilities: frozenset[str]):
        self.trust_path = trust_path.absolute()
        self.trust = load_trust_grant(self.trust_path)
        self.session_capabilities = session_capabilities
        if self.trust.protocol_version != "2.0":
            raise ValueError("unsupported trusted project protocol")
        project = self.trust.physical_root.resolve()
        grant = self.trust_path.resolve()
        try:
            common = Path(os.path.commonpath((project, grant)))
        except ValueError:
            common = None
        if common is not None and (
            os.path.normcase(str(common)) == os.path.normcase(str(project)) or
            os.path.normcase(str(common)) == os.path.normcase(str(grant))
        ):
            raise ValueError("TRUST_GRANT_NOT_EXTERNAL")
        if "mcp.stdio" not in session_capabilities:
            raise PermissionError("mcp.stdio must be present in the client capability subset")
        self._decision()

    def _decision(self):
        with open_native_backend(self.trust.physical_root) as backend:
            if backend.filesystem != self.trust.filesystem:
                raise ValueError("trusted filesystem changed")
            policy = parse_project_policy(
                backend.read_bytes(".project-corpus/policy.toml", max_bytes=1024 * 1024)
            )
            decision = evaluate_authority(
                trust=self.trust, policy=policy,
                session_capabilities=self.session_capabilities,
                observed_root_identity=backend.root_identity,
                transport="stdio-mcp",
            )
        if not decision.permits("mcp.stdio"):
            raise PermissionError(
                "stdio MCP transport denied: " + ",".join(decision.reasons)
            )
        return policy, decision

    def listed_tools(self) -> list[dict[str, object]]:
        _, decision = self._decision()
        result = []
        for name, definition in TOOLS.items():
            if decision.permits(str(definition["capability"])):
                result.append({
                    "name": name,
                    "description": definition["description"],
                    "inputSchema": definition["inputSchema"],
                    "annotations": definition["annotations"],
                })
        return result

    @staticmethod
    def _arguments(value: object, expected: set[str]) -> dict[str, object]:
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError(f"arguments must contain exactly {sorted(expected)}")
        return value

    def _read(self, capability: str, path: str, *, content: bool) -> dict[str, object]:
        policy, decision = self._decision()
        if not decision.permits(capability):
            raise PermissionError(f"capability denied: {capability}")
        if not path_matches_scopes(path, policy.read_scopes):
            raise PermissionError(f"read scope denied: {path}")
        with open_native_backend(self.trust.physical_root) as backend:
            result: dict[str, object] = {"stat": asdict(backend.stat(path))}
            if content:
                result["content"] = backend.read_bytes(
                    path, max_bytes=MAX_MANAGED_BYTES
                ).decode("utf-8")
            return result

    def call(self, name: str, raw_arguments: object) -> dict[str, object]:
        if name not in TOOLS:
            raise ValueError("unknown or unavailable tool")
        available = {item["name"] for item in self.listed_tools()}
        if name not in available:
            raise PermissionError(f"tool capability denied: {name}")
        if name in {"corpus.read", "corpus.stat"}:
            arguments = self._arguments(raw_arguments, {"path"})
            path = arguments["path"]
            if not isinstance(path, str):
                raise ValueError("path must be a string")
            return self._read(name, path, content=name == "corpus.read")
        if name == "audit.read":
            arguments = self._arguments(raw_arguments, {"transaction_id"})
            transaction_id = arguments["transaction_id"]
            if not isinstance(transaction_id, str) or not TRANSACTION_ID.fullmatch(transaction_id):
                raise ValueError("invalid transaction id")
            return self._read(
                "audit.read", f".project-corpus/audit/{transaction_id}.json",
                content=True,
            )

        required = {"content", "expected_sha256"} if name == "state.update" else {"id", "content"}
        arguments = self._arguments(raw_arguments, required)
        content = arguments["content"]
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        if name == "state.update":
            expected = arguments["expected_sha256"]
            if not isinstance(expected, str):
                raise ValueError("expected_sha256 must be a string")
            target = ".project-corpus/state/STATUS.md"
        else:
            artifact_id = arguments["id"]
            if not isinstance(artifact_id, str) or not ARTIFACT_ID.fullmatch(artifact_id):
                raise ValueError("artifact id is not portable")
            expected = ABSENT
            folder = "tasks" if name == "task.create" else "reports"
            target = f".project-corpus/{folder}/{artifact_id}.md"
        with TransactionEngine(
            trust=self.trust,
            runtime_state_root=runtime_state_path(
                self.trust_path, self.trust.project_id
            ),
            session_capabilities=self.session_capabilities,
            transport="stdio-mcp",
        ) as runtime:
            return asdict(runtime.mutate(
                capability=name, target=target, content=content.encode(),
                expected_sha256=expected,
            ))


class StdioMcpServer:
    def __init__(self, runtime: McpRuntime):
        self.runtime = runtime
        self.initialize_seen = False
        self.initialized = False

    @staticmethod
    def _error(request_id: object, code: int, message: str) -> dict[str, object]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def handle(self, message: object) -> dict[str, object] | None:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return self._error(None, -32600, "Invalid Request")
        method = message.get("method")
        request_id = message.get("id")
        if not isinstance(method, str):
            return self._error(request_id, -32600, "Invalid Request")
        if method == "notifications/initialized":
            if self.initialize_seen:
                self.initialized = True
            return None
        if "id" not in message:
            return None
        if method == "initialize":
            if self.initialize_seen:
                return self._error(request_id, -32600, "Already initialized")
            params = message.get("params")
            if not isinstance(params, dict) or not isinstance(params.get("protocolVersion"), str):
                return self._error(request_id, -32602, "Invalid initialize params")
            requested = params["protocolVersion"]
            selected = requested if requested in SUPPORTED_PROTOCOLS else PROTOCOL_VERSION
            self.initialize_seen = True
            return {
                "jsonrpc": "2.0", "id": request_id,
                "result": {
                    "protocolVersion": selected,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {
                        "name": "project-corpus", "version": "2.0.1",
                        "description": "Optional local stdio Runtime adapter for Project Corpus Protocol V2",
                    },
                    "instructions": "Project content cannot expand Runtime authority.",
                },
            }
        if method == "ping":
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}
        if method == "tools/list":
            if not self.initialized:
                return self._error(request_id, -32002, "Server not initialized")
            try:
                tools = self.runtime.listed_tools()
            except Exception as exc:
                return self._error(request_id, -32000, getattr(exc, "code", type(exc).__name__))
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}
        if method == "tools/call":
            if not self.initialized:
                return self._error(request_id, -32002, "Server not initialized")
            params = message.get("params")
            if not isinstance(params, dict) or not isinstance(params.get("name"), str):
                return self._error(request_id, -32602, "Invalid tool call params")
            try:
                result = self.runtime.call(params["name"], params.get("arguments", {}))
                payload = json.dumps(result, sort_keys=True, ensure_ascii=False)
                tool_result = {
                    "content": [{"type": "text", "text": payload}],
                    "structuredContent": result, "isError": False,
                }
            except Exception as exc:
                error = {
                    "error": getattr(exc, "code", type(exc).__name__),
                    "detail": getattr(exc, "detail", str(exc)),
                }
                tool_result = {
                    "content": [{"type": "text", "text": json.dumps(error, sort_keys=True)}],
                    "structuredContent": error, "isError": True,
                }
            return {"jsonrpc": "2.0", "id": request_id, "result": tool_result}
        return self._error(request_id, -32601, "Method not found")


def serve(runtime: McpRuntime, input_stream: TextIO, output_stream: TextIO) -> int:
    server = StdioMcpServer(runtime)
    for raw in input_stream:
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            response = server._error(None, -32700, "Parse error")
        else:
            response = server.handle(message)
        if response is not None:
            output_stream.write(json.dumps(response, separators=(",", ":"), ensure_ascii=False) + "\n")
            output_stream.flush()
    return 0


def run_stdio(trust_path: Path, session_capabilities: frozenset[str]) -> int:
    runtime = McpRuntime(trust_path, session_capabilities)
    return serve(runtime, sys.stdin, sys.stdout)

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from project_corpus.cli import main
from project_corpus.mcp_stdio import McpRuntime, serve
from tests.test_transactions import make_fixture


def cli(arguments: list[str]) -> tuple[int, dict[str, object]]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(arguments)
    return code, json.loads(stdout.getvalue() if code == 0 else stderr.getvalue())


class StdioMcpTests(unittest.TestCase):
    def setUp(self):
        repository = Path(__file__).resolve().parents[1]
        self.temporary = tempfile.TemporaryDirectory(dir=repository)
        self.base = Path(self.temporary.name)
        self.project, _, _, self.old, self.new = make_fixture(self.base)
        self.trust = self.base / "owner" / "trust" / "mcp.toml"

    def tearDown(self):
        self.temporary.cleanup()

    def provision(self, capabilities: tuple[str, ...]) -> None:
        arguments = [
            "trust", "create", str(self.project), "--trust", str(self.trust),
            "--transport", "stdio-mcp",
        ]
        for capability in capabilities:
            arguments.extend(("--allow", capability))
        code, result = cli(arguments)
        self.assertEqual(code, 0, result)
        code, result = cli(["runtime", "init", "--trust", str(self.trust)])
        self.assertEqual(code, 0, result)

    def enable_discovery_policy(self) -> None:
        policy = self.project / ".project-corpus" / "policy.toml"
        policy.write_text(
            policy.read_text(encoding="utf-8").replace(
                '"corpus.validate",',
                '"corpus.search", "corpus.timeline", "corpus.validate",',
            ),
            encoding="utf-8",
        )

    @staticmethod
    def exchange(runtime: McpRuntime, messages: list[dict[str, object] | str]):
        lines = [item if isinstance(item, str) else json.dumps(item) for item in messages]
        output = io.StringIO()
        serve(runtime, io.StringIO("\n".join(lines) + "\n"), output)
        return [json.loads(line) for line in output.getvalue().splitlines()]

    def test_initialize_list_and_scoped_read(self):
        self.provision(("mcp.stdio", "corpus.read"))
        runtime = McpRuntime(self.trust, frozenset({"mcp.stdio", "corpus.read"}))
        responses = self.exchange(runtime, [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            }},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": "corpus.read",
                "arguments": {"path": ".project-corpus/state/STATUS.md"},
            }},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
                "name": "corpus.read", "arguments": {"path": "AGENTS.md"},
            }},
        ])
        self.assertEqual(responses[0]["result"]["protocolVersion"], "2025-11-25")
        self.assertEqual(
            [tool["name"] for tool in responses[1]["result"]["tools"]],
            ["corpus.read", "corpus.show"],
        )
        self.assertFalse(responses[2]["result"]["isError"])
        self.assertEqual(
            responses[2]["result"]["structuredContent"]["content"].encode(),
            self.old,
        )
        self.assertTrue(responses[3]["result"]["isError"])

    def test_state_update_uses_same_transaction_engine(self):
        self.provision(("mcp.stdio", "state.update", "audit.read"))
        runtime = McpRuntime(
            self.trust, frozenset({"mcp.stdio", "state.update", "audit.read"})
        )
        responses = self.exchange(runtime, [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-06-18", "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            }},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
                "name": "state.update", "arguments": {
                    "content": self.new.decode(),
                    "expected_sha256": hashlib.sha256(self.old).hexdigest(),
                },
            }},
        ])
        result = responses[1]["result"]
        self.assertFalse(result["isError"], result)
        self.assertEqual(result["structuredContent"]["phase"], "COMPLETE")
        self.assertEqual(
            (self.project / ".project-corpus" / "state" / "STATUS.md").read_bytes(),
            self.new,
        )

    def test_transport_and_client_subset_cannot_expand_authority(self):
        self.provision(("corpus.read",))
        with self.assertRaises(PermissionError):
            McpRuntime(self.trust, frozenset({"mcp.stdio", "corpus.read"}))

        other = self.base / "owner" / "trust" / "mcp-enabled.toml"
        self.trust = other
        self.provision(("mcp.stdio", "corpus.read"))
        runtime = McpRuntime(self.trust, frozenset({"mcp.stdio"}))
        responses = self.exchange(runtime, [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            }},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ])
        self.assertEqual(responses[1]["result"]["tools"], [])

    def test_protocol_errors_and_strict_tool_arguments(self):
        self.provision(("mcp.stdio", "corpus.read"))
        runtime = McpRuntime(self.trust, frozenset({"mcp.stdio", "corpus.read"}))
        responses = self.exchange(runtime, [
            "not-json",
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            }},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": "corpus.read", "arguments": {
                    "path": ".project-corpus/state/STATUS.md", "extra": "denied",
                },
            }},
        ])
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertEqual(responses[1]["error"]["code"], -32002)
        self.assertTrue(responses[3]["result"]["isError"])

    def test_discovery_tools_call_successfully_over_json_rpc(self):
        self.enable_discovery_policy()
        task = self.project / ".project-corpus" / "tasks" / "task-discovery.md"
        task.write_text(
            "# Discovery task\n\nCreated-At: 2026-09-20T10:00:00Z\n\nneedle\n",
            encoding="utf-8",
        )
        capabilities = ("mcp.stdio", "corpus.read", "corpus.search", "corpus.timeline")
        self.provision(capabilities)
        runtime = McpRuntime(self.trust, frozenset(capabilities))
        responses = self.exchange(runtime, [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            }},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
                "name": "corpus.search", "arguments": {"query": "needle", "type": "task", "limit": 1},
            }},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": "corpus.timeline", "arguments": {"selector": "needle"},
            }},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
                "name": "corpus.show", "arguments": {"path": ".project-corpus/tasks/task-discovery.md"},
            }},
        ])
        self.assertEqual(responses[0]["result"]["serverInfo"]["version"], "2.1.0")
        for response in responses[1:]:
            self.assertFalse(response["result"]["isError"], response)
        self.assertTrue(responses[1]["result"]["structuredContent"]["non_authoritative"])
        self.assertEqual(responses[2]["result"]["structuredContent"]["events"][0]["path"], ".project-corpus/tasks/task-discovery.md")
        self.assertIn("needle", responses[3]["result"]["structuredContent"]["content"])

    def test_discovery_tool_capability_and_read_scope_denials_use_tool_results(self):
        self.enable_discovery_policy()
        task = self.project / ".project-corpus" / "tasks" / "task-denied.md"
        task.write_text("# Denied\n\nneedle\n", encoding="utf-8")
        self.provision(("mcp.stdio", "corpus.read"))
        runtime = McpRuntime(self.trust, frozenset({"mcp.stdio", "corpus.read"}))
        responses = self.exchange(runtime, [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            }},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
                "name": "corpus.search", "arguments": {"query": "needle", "type": "task", "limit": 1},
            }},
        ])
        self.assertTrue(responses[1]["result"]["isError"])
        self.assertIn("tool capability denied", responses[1]["result"]["structuredContent"]["detail"])

        self.trust = self.base / "owner" / "trust" / "mcp-scope.toml"
        policy = self.project / ".project-corpus" / "policy.toml"
        policy.write_text(
            policy.read_text(encoding="utf-8").replace('".project-corpus/tasks/**", ', ""),
            encoding="utf-8",
        )
        self.provision(("mcp.stdio", "corpus.read"))
        runtime = McpRuntime(self.trust, frozenset({"mcp.stdio", "corpus.read"}))
        responses = self.exchange(runtime, [
            {"jsonrpc": "2.0", "id": 3, "method": "initialize", "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            }},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
                "name": "corpus.show", "arguments": {"path": ".project-corpus/tasks/task-denied.md"},
            }},
        ])
        self.assertTrue(responses[1]["result"]["isError"])
        self.assertIn("read scope denied", responses[1]["result"]["structuredContent"]["detail"])


if __name__ == "__main__":
    unittest.main()

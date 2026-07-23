#!/usr/bin/env python3
"""Run a real stdio and Streamable HTTP verification against the installed server."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client


CURRENT_FILES = (
    "AGENTS.md",
    "OPERATOR_PROFILE.md",
    "PROJECT_ROADMAP_CURRENT.md",
    "MCP_CONNECTION_CURRENT.md",
    "LOADER_PROMPT_CURRENT.md",
    "SESSION_HANDOFF_CURRENT.md",
    "SESSION_HANDOFF_FULL_CURRENT.md",
)
EXPECTED_TOOLS = {
    "corpus_health", "corpus_list", "corpus_read", "corpus_read_many",
    "corpus_search", "corpus_stat", "corpus_write",
}


def text(result) -> str:
    return "\n".join(getattr(item, "text", "") for item in result.content)


def seed_corpus(root: Path) -> None:
    (root / "Tasks").mkdir(parents=True)
    (root / "Report").mkdir()
    for name in CURRENT_FILES:
        (root / name).write_text(f"# {name}\nNO_ACTIVE_PROJECT\n", encoding="utf-8")


async def verify_stdio(corpus: Path, mcp_root: Path) -> dict:
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "project_corpus_mcp.server", "--transport", "stdio", "--corpus-root", str(corpus), "--mcp-root", str(mcp_root)],
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            if {item.name for item in tools.tools} != EXPECTED_TOOLS:
                raise RuntimeError("The stdio server did not expose exactly seven expected tools")
            health = json.loads(text(await session.call_tool("corpus_health", {})))
            if health["status"] != "ok":
                raise RuntimeError("corpus_health did not report ok")
            await session.call_tool("corpus_list", {"subpath": "."})
            await session.call_tool("corpus_read", {"path": "AGENTS.md"})
            await session.call_tool("corpus_read_many", {"paths": ["AGENTS.md", "PROJECT_ROADMAP_CURRENT.md"]})
            await session.call_tool("corpus_search", {"query": "NO_ACTIVE_PROJECT", "mode": "text"})
            await session.call_tool("corpus_stat", {"path": "AGENTS.md"})
            created = json.loads(text(await session.call_tool(
                "corpus_write",
                {"path": "Tasks/VERIFY__TASK.md", "content": "# Verification\n", "operation": "create"},
            )))
            updated = json.loads(text(await session.call_tool(
                "corpus_write",
                {
                    "path": "Tasks/VERIFY__TASK.md",
                    "content": "# Updated\n",
                    "operation": "update",
                    "expected_sha256": created["newSha256"],
                },
            )))
            if updated["backupSha256"] != created["newSha256"]:
                raise RuntimeError("Update backup SHA does not match the prior file")
            if updated["newSha256"] != updated["readbackSha256"]:
                raise RuntimeError("Update readback SHA does not match the new file")
            stale = await session.call_tool(
                "corpus_write",
                {
                    "path": "Tasks/VERIFY__TASK.md",
                    "content": "# Stale\n",
                    "operation": "update",
                    "expected_sha256": "0" * 64,
                },
            )
            traversal = await session.call_tool(
                "corpus_write",
                {"path": "../escape.md", "content": "# Escape\n", "operation": "create"},
            )
            if not stale.isError or not traversal.isError:
                raise RuntimeError("Negative write tests were unexpectedly accepted")
            return {"tools": len(tools.tools), "health": health}


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(port: int) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Timed out waiting for Streamable HTTP server")


async def verify_http(port: int) -> dict:
    def client_factory(**kwargs):
        return httpx.AsyncClient(trust_env=False, **kwargs)

    url = f"http://127.0.0.1:{port}/mcp"
    async with streamablehttp_client(url, httpx_client_factory=client_factory) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            health = json.loads(text(await session.call_tool("corpus_health", {})))
    response = httpx.post(
        url,
        headers={
            "Origin": "https://untrusted.example",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "verify-mcp", "version": "1"},
            },
        },
        timeout=5,
        trust_env=False,
    )
    if response.status_code != 403:
        raise RuntimeError(f"Hostile Origin was not rejected: HTTP {response.status_code}")
    if {item.name for item in tools.tools} != EXPECTED_TOOLS or health["status"] != "ok":
        raise RuntimeError("The HTTP server did not expose the expected healthy tool set")
    return {"tools": len(tools.tools), "health": health, "hostileOriginStatus": response.status_code}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="project-corpus-verify-") as temporary:
        base = Path(temporary)
        corpus = base / "Corpus"
        mcp_root = base / "mcp-state"
        seed_corpus(corpus)
        stdio = asyncio.run(verify_stdio(corpus, mcp_root))
        port = free_port()
        process = subprocess.Popen([
            sys.executable, "-m", "project_corpus_mcp.server", "--transport", "streamable-http", "--corpus-root", str(corpus),
            "--mcp-root", str(mcp_root), "--host", "127.0.0.1", "--port", str(port),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            wait_for_server(port)
            http = asyncio.run(verify_http(port))
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    print(json.dumps({"status": "ok", "stdio": stdio, "http": http}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

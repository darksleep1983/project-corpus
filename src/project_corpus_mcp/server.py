from __future__ import annotations

import argparse
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .core import CorpusConfig, CorpusError, CorpusStore


def build_server() -> FastMCP:
    config = CorpusConfig.from_env()
    store = CorpusStore(config)
    host = os.environ.get("PROJECT_CORPUS_HOST", "127.0.0.1")
    port = int(os.environ.get("PROJECT_CORPUS_PORT", "8334"))

    mcp = FastMCP(
        "Project Corpus MCP",
        stateless_http=True,
        json_response=True,
        host=host,
        port=port,
    )

    @mcp.tool()
    def corpus_health() -> dict[str, Any]:
        """Report server health, exact corpus root, and policy versions."""
        return store.health()

    @mcp.tool()
    def corpus_list(subpath: str = ".") -> dict[str, Any]:
        """List files and directories strictly under the corpus root."""
        return store.list(subpath)

    @mcp.tool()
    def corpus_read(path: str, offset: int = 0, limit: int = 1_000_000,
                    encoding: str = "utf8") -> dict[str, Any]:
        """Read a bounded file chunk with full-file SHA-256."""
        return store.read(path, offset, limit, encoding)

    @mcp.tool()
    def corpus_read_many(paths: list[str]) -> dict[str, Any]:
        """Read multiple corpus files with per-file status."""
        return store.read_many(paths)

    @mcp.tool()
    def corpus_search(query: str, mode: str = "both",
                      max_results: int = 100) -> dict[str, Any]:
        """Search filenames and supported text files under the corpus root."""
        return store.search(query, mode, max_results)

    @mcp.tool()
    def corpus_stat(path: str) -> dict[str, Any]:
        """Return size, mtime, and SHA-256 for a corpus file."""
        return store.stat(path)

    @mcp.tool()
    def corpus_write(path: str, content: str, operation: str = "update",
                     encoding: str = "utf8", expected_sha256: str | None = None,
                     authorization: str | None = None) -> dict[str, Any]:
        """Perform a scoped create/update under the Project Corpus write policy."""
        return store.write(
            path=path,
            content=content,
            operation=operation,
            encoding=encoding,
            expected_sha256=expected_sha256,
            authorization=authorization,
        )

    return mcp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Project Corpus MCP server")
    parser.add_argument("--transport", choices=("streamable-http", "stdio"),
                        default=os.environ.get("PROJECT_CORPUS_TRANSPORT", "streamable-http"))
    parser.add_argument("--corpus-root")
    parser.add_argument("--mcp-root")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.corpus_root:
        os.environ["PROJECT_CORPUS_ROOT"] = args.corpus_root
    if args.mcp_root:
        os.environ["PROJECT_CORPUS_MCP_ROOT"] = args.mcp_root
    if args.host:
        os.environ["PROJECT_CORPUS_HOST"] = args.host
    if args.port:
        os.environ["PROJECT_CORPUS_PORT"] = str(args.port)

    try:
        server = build_server()
        server.run(transport=args.transport)
    except CorpusError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()

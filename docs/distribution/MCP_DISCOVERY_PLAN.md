# MCP discovery plan

**Status: research and preparation only. Do not submit this project to any
registry without an owner decision.**

Project Corpus currently provides an optional local stdio MCP adapter. It has no
remote transport and is not yet published as a PyPI distribution, so it does not
qualify for public package-backed listings today.

| Channel | Status | Requirements | Does Project Corpus qualify today? | Later submission steps |
| --- | --- | --- | --- | --- |
| [Official MCP Registry](https://registry.modelcontextprotocol.io/docs) | Official; preview | Public package or remote endpoint, `server.json`, namespace authentication, package ownership verification | No. A public package and release metadata are still required. | Publish the package; add the required PyPI `mcp-name` ownership marker and reviewed `server.json`; validate with `mcp-publisher validate`; authenticate to the matching namespace; publish; verify the registry entry. |
| [Smithery](https://smithery.ai/docs/build/publish) | Third-party | Public Streamable HTTP endpoint with OAuth, or a pre-built MCPB bundle for local stdio | No. The Runtime is stdio-only and does not publish an MCPB bundle. | First make an explicit product decision about remote hosting or MCPB packaging; prepare metadata/configuration; submit through Smithery; verify the generated listing and permissions. |
| [Glama](https://glama.ai/mcp/faq) | Third-party | Public GitHub repository, server metadata, and successful automated indexing/health checks | Not yet. A reviewed installable distribution and listing metadata are needed. | Confirm its current submission policy; add only reviewed metadata such as `glama.json` if still required; submit the repository; inspect the generated configuration before announcing it. |

## Required metadata before any listing

- A public, installable, versioned package with a verified CLI entry point.
- An accurate stdio launch command and Python version requirement.
- Exact capability and filesystem guarantee wording; no remote-MCP implication.
- Repository URL, license, icon/social asset, support and security reporting route.
- A reviewed `server.json` and registry namespace. For a GitHub namespace, use
  the identity allowed by the publisher's GitHub authentication.

## Safety rule

Do not publish a registry record that suggests HTTP transport, remote operation,
whole-disk access, or enforcement outside the documented controlled Runtime
modes. Re-check each directory's current policies at the time of submission.

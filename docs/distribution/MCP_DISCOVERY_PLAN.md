# MCP directory discovery plan

**Status: preparation only. Do not submit or publish a directory listing without
an explicit owner decision.**

Project Corpus includes an optional local stdio MCP adapter in the Python
Runtime, distributed as the `project-corpus` package on
[PyPI](https://pypi.org/project/project-corpus/). The adapter has no HTTP or
remote transport. This document records a possible future review; it does not
claim current eligibility or listing status for any third-party directory.

## Before considering a submission

- Confirm that a directory's current publisher policy supports the intended
  local stdio package and that this adapter meets its requirements.
- Review all requested metadata, ownership proofs, manifests, and authentication
  steps against that directory's current official instructions.
- Verify the exact package version, launch command, capabilities, filesystem
  boundaries, repository URL, license, support, and security-reporting route.
- Ensure the listing cannot imply HTTP transport, whole-disk access, arbitrary
  tool dispatch, or guarantees beyond the documented controlled Runtime modes.
- Record the owner's explicit decision and verify the resulting public listing
  before announcing it.

## Possible directories

These links are research starting points, not eligibility claims:

- [Official MCP Registry](https://registry.modelcontextprotocol.io/docs)
- [Smithery](https://smithery.ai/docs/build/publish)
- [Glama](https://glama.ai/mcp/faq)

Recheck each directory's current policies when an owner authorizes review. Do
not publish a record that suggests remote operation or capabilities outside the
local adapter contract.

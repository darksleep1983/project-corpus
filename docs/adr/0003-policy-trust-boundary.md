# ADR 0003: External owner trust grant bounds project policy

Status: accepted by the owner

## Decision

The project-local `.project-corpus/policy.toml` is a portable request, not an
independent source of runtime authority. Runtime stores an owner-approved trust
grant outside the project root. Effective authority is the intersection of:

```text
runtime hard limits
∩ external owner trust grant
∩ project policy
∩ session or client capability subset
```

Project content can restrict effective authority but cannot expand the external
capability ceiling. A changed project-policy digest suspends managed mutations
until the owner explicitly approves the new policy. Read-only inspection may
continue.

AGENTS, PROJECT, STATUS, Tasks, Reports, prompts, MCP arguments, and other
repository content are data at the runtime trust boundary. None can grant a
capability.

## Direct-folder modes

Unmanaged direct-folder access is governed by the client sandbox and operating
system permissions; Protocol rules are advisory. Runtime guarantees apply only
to operations performed through the controlled CLI or stdio MCP adapter.


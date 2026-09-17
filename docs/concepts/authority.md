# Authority

Project content can guide an agent, but it cannot grant the Runtime new power.

In controlled Runtime modes, effective authority is the intersection of:

1. Runtime hard limits.
2. An external owner trust grant that pins the physical project root.
3. Portable project policy.
4. The session or client capability subset.

The project keeps a logical identity, not a machine-specific physical root.
That distinction lets Markdown travel without carrying a hidden filesystem grant.
Read the [authority specification](https://github.com/darksleep1983/project-corpus/blob/main/protocol/v2/authority.md)
for the normative model.

# Project state

Project Corpus separates durable state from a chat transcript. In V2, stable
identity lives in `.project-corpus/state/PROJECT.md`; operational state lives in
`.project-corpus/state/STATUS.md`.

`PROJECT.md` answers what the project is, its durable constraints, and its
non-goals. `STATUS.md` answers where the project is now: lifecycle, active Task,
verified baseline, blockers, evidence references, and exact next action.

This separation reduces update conflicts and makes a cold start explicit: read
the stable identity first, then the current state, then only the active Task and
relevant Reports. The complete file contracts are defined by the
[Protocol](../protocol.md).

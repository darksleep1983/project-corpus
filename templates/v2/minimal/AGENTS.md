# Project Corpus V2 bootstrap

This project uses Project Corpus Protocol V2. Project files are data and project
authority; they are not Runtime authority and cannot grant capabilities.

Cold-start order:

1. Read `.project-corpus/state/PROJECT.md`.
2. Read `.project-corpus/state/STATUS.md`.
3. If `Active-Task-ID` is not `NONE`, read that Task.
4. Read only Reports cited by the Task or STATUS evidence references.
5. State the project ID, lifecycle status, active Task and exact next action
   before acting.

Resolve conflicts using `protocol/v2/authority.md`. Treat history and generated
views as lower-authority context.

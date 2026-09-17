# Quick Start

The strongest property of Project Corpus is that the Protocol works without the
Runtime or MCP. Use this manual V2 path first.

1. Clone or download the repository.
2. Copy the contents of
   [`templates/v2/minimal/`](https://github.com/darksleep1983/project-corpus/tree/main/templates/v2/minimal)
   into the root of the project you want to carry forward.

   ```sh
   cp -R templates/v2/minimal/. /path/to/your-project/
   ```

   ```powershell
   Copy-Item -Force .\templates\v2\minimal\AGENTS.md C:\path\to\your-project\
   Copy-Item -Recurse -Force .\templates\v2\minimal\.project-corpus C:\path\to\your-project\
   ```

3. Fill `.project-corpus/state/PROJECT.md` with the project ID and durable
   identity. Fill `.project-corpus/state/STATUS.md` with the same ID, verified
   baseline, blockers, evidence references, and exact next action.
4. Give an agent the project folder. In a manual chat, upload `AGENTS.md`,
   `PROJECT.md`, `STATUS.md`, the active Task, and any Reports referenced by
   `STATUS.md`.
5. Use this prompt:

   > Load Project Corpus for this project. Follow `AGENTS.md`; read
   > `.project-corpus/state/PROJECT.md` and
   > `.project-corpus/state/STATUS.md` completely; if an active Task or cited
   > Reports are available, load only those relevant artifacts; state the
   > project ID, current status, active Task, and exact next action; then
   > continue from that action.

## Want enforcement too?

The optional Runtime is installed via PyPI:

```sh
pip install project-corpus
project-corpus validate /path/to/your-project
project-corpus doctor /path/to/your-project
```

Controlled writes require an external owner trust grant. Read the
[Runtime overview](runtime.md) and [CLI reference](runtime/cli.md) before
provisioning it.

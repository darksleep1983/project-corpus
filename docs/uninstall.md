# Move or remove a Corpus

[Русская версия](uninstall.ru.md)

The Markdown Protocol has no required application or service. The optional
Runtime is a locally installed Python package; uninstalling it does not remove
project state.

## Move it

For V2, move the project with its `AGENTS.md` and `.project-corpus/` directory,
or follow the project's own storage rules. A Runtime owner trust grant pins a
physical project root, so after moving a project, follow the
[Runtime CLI guide](runtime/cli.md) to review and reconfigure trust before
controlled operations.

For an existing V1 Corpus, move its whole folder, including `Tasks/` and
`Report/`, then update the exact location in `CORPUS_ACCESS_CURRENT.md` and any
client or third-party MCP configuration.

## Remove project state

Back up first. Remove the V2 `.project-corpus/` directory only when you
intentionally want to remove that state. Review `AGENTS.md` and remove only its
Corpus-specific instructions, preserving any other project rules. For V1,
remove the whole Corpus folder only when you intentionally want to remove that
state.

For manual mode, also remove uploaded copies from the AI project if you no longer
want them stored there. Remove third-party MCP configuration separately using
that server and client's documentation.

## Uninstall the optional Runtime

If installed with pip, uninstall the package in the same Python environment:

```sh
python -m pip uninstall project-corpus
```

Review and remove external owner trust and Runtime state separately according
to the setup you chose. Removing the package does not erase a project's Corpus.

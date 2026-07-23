# Uninstall or move Project Corpus

Project Corpus does not install an operating-system service. Stop a running HTTP
server with Ctrl+C before changing files.

## Keep your project memory

The safe default is to keep your project data. Remove only these items from the
repository folder:

- .venv/
- .project-corpus.local.json

Your Corpus and mcp-state folder stay in the ProjectHome you selected during
installation. You can later install another copy of the repository and point it
at the same ProjectHome only after reviewing the version and backup policy.

## Remove everything

A Corpus contains project state, Tasks, and Reports. Back up or export it first.
Then remove the entire ProjectHome you chose during installation. This is an
intentional destructive action and is not performed by the installer.

If you connected the server to an AI client, remove that client configuration
separately. Use the client guide for the relevant configuration location.


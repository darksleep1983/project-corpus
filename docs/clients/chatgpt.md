# Use Project Corpus with ChatGPT

[Русская версия](chatgpt.ru.md)

## New projects: start with V2

Follow the [V2 Quick Start](../quickstart.md). In a manual ChatGPT Project,
upload `AGENTS.md`, `.project-corpus/state/PROJECT.md`, and
`.project-corpus/state/STATUS.md`, then add only the active Task and Reports
needed for the work. Keep canonical file names distinct when replacing sources.

Official guide: <https://help.openai.com/en/articles/10169521-projects-in-chatgpt>

## Existing V1 projects

V1 uses seven current files. In a manual ChatGPT Project, add those files as
project sources and put the manual section of
`PROJECT_INSTRUCTION_TEMPLATE.md` in Project instructions. Add only relevant
Tasks and Reports to each chat. For replacement files, avoid keeping duplicate
sources with the same canonical name.

## Direct folder

In the ChatGPT desktop app, Work can open a local folder. Open only the Corpus
folder or a project workspace that contains it, grant the minimum access needed,
and use `DIRECT_FOLDER`.

Official guide:
<https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex>

## Your own MCP

Custom MCP apps and write capabilities depend on the current ChatGPT plan,
workspace role, admin settings, and rollout. Configure an app only after you
have a trusted remote MCP endpoint and have reviewed its permissions. This
repository does not provide that endpoint.

Official guide:
<https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt>

Do not expose an unauthenticated local server to the internet merely to connect
ChatGPT.

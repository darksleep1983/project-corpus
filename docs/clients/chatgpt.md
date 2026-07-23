# Use Project Corpus with ChatGPT

[Русская версия](chatgpt.ru.md)

## Easiest: manual mode

Create a ChatGPT Project, add the seven current files as project sources, and
place the manual section of `PROJECT_INSTRUCTION_TEMPLATE.md` in Project
instructions. Add only relevant Tasks and Reports to a chat.

When replacing a current file, avoid leaving two sources with the same canonical
filename. ChatGPT may offer to upload a duplicate rather than replace the old
source.

Official guide: <https://help.openai.com/en/articles/10169521-projects-in-chatgpt>

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

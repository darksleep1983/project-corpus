# Connect ChatGPT

ChatGPT connects to remote MCP servers, not directly to a server bound only to
127.0.0.1. Keep Project Corpus on loopback and use the supported Secure MCP
Tunnel when the server runs on your own computer or private network. Do not
expose the local server publicly just to connect it.

## Before you begin

- The exact options depend on your ChatGPT plan, workspace role, and current
  Apps/developer-mode availability.
- Full MCP write/modify actions are currently available for Business and
  Enterprise/Edu users. Pro users can use custom MCP apps with read/fetch
  permissions in developer mode.
- Custom MCP apps are currently web-only; do not plan this connection around
  mobile use.

## Connection path

1. Install Project Corpus and start it locally.
2. Follow the Secure MCP Tunnel guide to give ChatGPT an authenticated remote
   route to the local server without opening it to the public internet.
3. In ChatGPT, enable developer mode when your plan and workspace permit it.
4. Go to **Settings or Workspace settings → Apps → Create**, provide the MCP
   endpoint and required metadata, choose authentication if applicable, then
   use **Scan Tools** and create the app.
5. Select the resulting app in a new ChatGPT web chat. Review the permission
   prompt before calling write tools.
6. Add the text from `PROJECT_INSTRUCTION_TEMPLATE.md` to the ChatGPT Project
   instructions.

For this server, choose an app permission that requires confirmation for changes
until you have reviewed its behavior. A Corpus write changes local project state.

## Official references

- https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt-beta
- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://help.openai.com/en/articles/11487775-apps-in-chatgpt

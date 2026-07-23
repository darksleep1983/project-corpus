$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigPath = Join-Path $RepoRoot ".project-corpus.local.json"
if (-not (Test-Path $ConfigPath)) { throw "Run install.ps1 first." }
$Config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$Exe = Join-Path $RepoRoot ".venv\Scripts\project-corpus-mcp.exe"
& $Exe --transport streamable-http --corpus-root $Config.corpusRoot --mcp-root $Config.mcpRoot --host $Config.host --port $Config.port

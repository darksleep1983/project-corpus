param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectHome,
    [string]$Python = "python",
    [ValidateSet("en", "ru")]
    [string]$Language = "en",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$Text = if ($Language -eq "ru") {
    @{ PythonMissing = "Python 3.11 или новее не найден."; PythonOld = "Нужен Python 3.11 или новее."; Installed = "Готово. Запустите сервер командой:"; ClaudeCode = "Команда для Claude Code:"; ClaudeDesktop = "Конфигурация для Claude Desktop:" }
} else {
    @{ PythonMissing = "Python 3.11 or newer was not found."; PythonOld = "Python 3.11 or newer is required."; Installed = "Installed. Start the server with:"; ClaudeCode = "Claude Code command:"; ClaudeDesktop = "Claude Desktop configuration:" }
}

if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) { throw $Text.PythonMissing }
$PythonVersion = & $Python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if ($LASTEXITCODE -ne 0) { throw $Text.PythonMissing }
if ([version]$PythonVersion -lt [version]"3.11") { throw $Text.PythonOld }

$Venv = Join-Path $RepoRoot ".venv"
if (-not (Test-Path $Venv)) {
    & $Python -m venv $Venv
}

$VenvPython = Join-Path $Venv "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e $RepoRoot

$argsList = @(
    (Join-Path $RepoRoot "scripts\setup_project.py"),
    "--project-home", $ProjectHome,
    "--repo-root", $RepoRoot,
    "--language", $Language
)
if ($Force) { $argsList += "--force" }
& $VenvPython @argsList

Write-Host ""
Write-Host $Text.Installed
Write-Host "  .\start.ps1"
Write-Host ""
Write-Host $Text.ClaudeCode
Write-Host "  .\.venv\Scripts\python.exe .\scripts\print_client_config.py claude-code"
Write-Host ""
Write-Host $Text.ClaudeDesktop
Write-Host "  .\.venv\Scripts\python.exe .\scripts\print_client_config.py claude-desktop"

# BM Builder — one-command launcher (Windows / PowerShell)
# ---------------------------------------------------------------------------
# Usage:  right-click this file -> "Run with PowerShell", or in a terminal:
#           .\run.ps1
# It creates a virtual environment, installs dependencies, and starts the app.
# If activation is ever blocked, run once:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# 1. Check for Python
try { python --version | Out-Null }
catch {
    Write-Host "Python was not found." -ForegroundColor Red
    Write-Host "Install Python 3.9+ from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then re-run." -ForegroundColor Yellow
    exit 1
}

# 2. Create the virtual environment on first run
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Cyan
    python -m venv .venv
}
$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

# 3. Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
& $venvPy -m pip install --upgrade pip | Out-Null
& $venvPy -m pip install -r requirements.txt

# 4. Make sure a .env exists (you add your key there or in the app's Settings page)
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env - add your Anthropic API key there, or later in the app's Settings page." -ForegroundColor Yellow
}

# 4b. Heads-up: Node.js + Claude Code power the autonomous build (optional - the app runs without them)
$haveNode   = [bool](Get-Command node   -ErrorAction SilentlyContinue)
$haveClaude = [bool](Get-Command claude -ErrorAction SilentlyContinue)
if (-not ($haveNode -and $haveClaude)) {
    Write-Host ""
    Write-Host "Heads-up: the one-click autonomous build uses Claude Code (optional - you can still brainstorm & plan without it):" -ForegroundColor Yellow
    if (-not $haveNode)   { Write-Host "  * Node.js not found     -> winget install OpenJS.NodeJS.LTS   (then open a NEW terminal)" -ForegroundColor Yellow }
    if (-not $haveClaude) { Write-Host "  * Claude Code not found -> npm install -g @anthropic-ai/claude-code, then run 'claude' to sign in" -ForegroundColor Yellow }
    Write-Host "  Set this up anytime - or pick your AI provider in the app's 'Setup & checks' screen." -ForegroundColor Yellow
    Write-Host ""
}

# 5. Launch
Write-Host "Starting BM Builder..." -ForegroundColor Green
& $venvPy -m streamlit run app.py

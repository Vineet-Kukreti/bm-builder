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

# 5. Launch
Write-Host "Starting BM Builder..." -ForegroundColor Green
& $venvPy -m streamlit run app.py

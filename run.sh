#!/usr/bin/env bash
# BM Builder — one-command launcher (macOS / Linux)
# ---------------------------------------------------------------------------
# Usage (first time):  chmod +x run.sh
#               then:  ./run.sh
# It creates a virtual environment, installs dependencies, and starts the app.

set -e
cd "$(dirname "$0")"

# 1. Find Python
PY=python3
command -v "$PY" >/dev/null 2>&1 || PY=python
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Python was not found. Install Python 3.9+ from https://www.python.org/downloads/ and re-run."
  exit 1
fi

# 2. Create the virtual environment on first run
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment (.venv)..."
  "$PY" -m venv .venv
fi
VENVPY=".venv/bin/python"

# 3. Install dependencies
echo "Installing dependencies..."
"$VENVPY" -m pip install --upgrade pip >/dev/null
"$VENVPY" -m pip install -r requirements.txt

# 4. Make sure a .env exists (you add your key there or in the app's Settings page)
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env - add your Anthropic API key there, or later in the app's Settings page."
fi

# 4b. Heads-up: Node.js + Claude Code power the autonomous build (optional - the app runs without them)
if ! command -v node >/dev/null 2>&1 || ! command -v claude >/dev/null 2>&1; then
  echo ""
  echo "Heads-up: the one-click autonomous build uses Claude Code (optional - you can still brainstorm & plan without it):"
  command -v node   >/dev/null 2>&1 || echo "  * Node.js not found     -> install from https://nodejs.org (or 'brew install node')"
  command -v claude >/dev/null 2>&1 || echo "  * Claude Code not found -> npm install -g @anthropic-ai/claude-code, then run 'claude' to sign in"
  echo "  Set this up anytime - or pick your AI provider in the app's 'Setup & checks' screen."
  echo ""
fi

# 5. Launch
echo "Starting BM Builder..."
exec "$VENVPY" -m streamlit run app.py

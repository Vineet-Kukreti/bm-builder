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

# 5. Launch
echo "Starting BM Builder..."
exec "$VENVPY" -m streamlit run app.py

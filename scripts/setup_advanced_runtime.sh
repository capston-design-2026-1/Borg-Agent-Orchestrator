#!/bin/zsh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if command -v python3.13 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.13)"
elif command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.12)"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.11)"
else
  PYTHON_BIN="$(command -v python3)"
fi

if [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
  if [[ ! -f /opt/homebrew/opt/libomp/lib/libomp.dylib ]]; then
    echo "Installing libomp via Homebrew..."
    brew install libomp
  fi
fi

echo "Using Python interpreter: ${PYTHON_BIN}"
"${PYTHON_BIN}" -m venv "${REPO_ROOT}/.venv"
"${REPO_ROOT}/.venv/bin/python" -m pip install --upgrade pip
"${REPO_ROOT}/.venv/bin/python" -m pip install -r "${REPO_ROOT}/requirements.txt"

echo "Advanced runtime ready."
echo "Python: ${REPO_ROOT}/.venv/bin/python"

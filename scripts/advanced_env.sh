#!/bin/zsh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${(%):-%N}")/.." && pwd)"
ENV_FILE="${BORG_ADVANCED_ENV_FILE:-$HOME/Documents/borg_xgboost_workspace/config/advanced_xgboost.env}"

"${REPO_ROOT}/scripts/setup_advanced_xgboost_workspace.sh" >/dev/null

if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${REPO_ROOT}/config/advanced_xgboost.env.example" "${ENV_FILE}"
fi

set -a
source "${ENV_FILE}"
set +a

export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
  export BORG_ADVANCED_PYTHON="${REPO_ROOT}/.venv/bin/python"
elif command -v python3.13 >/dev/null 2>&1; then
  export BORG_ADVANCED_PYTHON="$(command -v python3.13)"
else
  export BORG_ADVANCED_PYTHON="$(command -v python3)"
fi

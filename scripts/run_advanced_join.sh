#!/bin/zsh

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/advanced_env.sh"

"${BORG_ADVANCED_PYTHON}" "${REPO_ROOT}/scripts/make_dataset.py"

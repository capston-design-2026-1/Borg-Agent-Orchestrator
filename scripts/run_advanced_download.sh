#!/bin/zsh

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/advanced_env.sh"

"${REPO_ROOT}/scripts/download_shards.sh"

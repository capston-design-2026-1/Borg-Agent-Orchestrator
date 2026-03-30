#!/bin/zsh

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/advanced_env.sh"

LOG_DIR="${HOME}/Documents/borg_xgboost_workspace/runtime/logs"
mkdir -p "${LOG_DIR}"
STAMP="$(TZ=Asia/Seoul date +%Y%m%d%H%M%S)"
LOG_FILE="${LOG_DIR}/${STAMP}_advanced_join_resumable.log"
LATEST_LOG="${LOG_DIR}/latest_advanced_join_resumable.log"
ln -sfn "${LOG_FILE}" "${LATEST_LOG}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[advanced_join_resumable] started_at=${STAMP}"
echo "[advanced_join_resumable] log=${LOG_FILE}"

clusters=("${(@s:,:)BORG_CLUSTERS}")
dataset_dir="${BORG_DATASET_DIR}"

for cluster_id in "${clusters[@]}"; do
  dataset_path="${dataset_dir}/${cluster_id}_dataset.parquet"
  if [[ -f "${dataset_path}" ]]; then
    echo "[advanced_join_resumable] skip cluster=${cluster_id} reason=dataset_exists path=${dataset_path}"
    continue
  fi

  echo "[advanced_join_resumable] start cluster=${cluster_id}"
  BORG_CLUSTERS="${cluster_id}" "${BORG_ADVANCED_PYTHON}" -u "${REPO_ROOT}/scripts/make_dataset.py"
  echo "[advanced_join_resumable] done cluster=${cluster_id} path=${dataset_path}"
done

echo "[advanced_join_resumable] completed"

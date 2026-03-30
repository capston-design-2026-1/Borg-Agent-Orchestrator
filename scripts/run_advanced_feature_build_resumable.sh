#!/bin/zsh

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/advanced_env.sh"

LOG_DIR="${HOME}/Documents/borg_xgboost_workspace/runtime/logs"
mkdir -p "${LOG_DIR}"
STAMP="$(TZ=Asia/Seoul date +%Y%m%d%H%M%S)"
LOG_FILE="${LOG_DIR}/${STAMP}_advanced_feature_build_resumable.log"
LATEST_LOG="${LOG_DIR}/latest_advanced_feature_build_resumable.log"
ln -sfn "${LOG_FILE}" "${LATEST_LOG}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[advanced_feature_build_resumable] started_at=${STAMP}"
echo "[advanced_feature_build_resumable] log=${LOG_FILE}"

clusters=("${(@s:,:)BORG_CLUSTERS}")
feature_dir="${BORG_XGBOOST_FEATURE_DIR}"

for cluster_id in "${clusters[@]}"; do
  feature_path="${feature_dir}/${cluster_id}_advanced_failure_features.parquet"
  if [[ -f "${feature_path}" ]]; then
    echo "[advanced_feature_build_resumable] skip cluster=${cluster_id} reason=feature_exists path=${feature_path}"
    continue
  fi

  echo "[advanced_feature_build_resumable] start cluster=${cluster_id}"
  BORG_CLUSTERS="${cluster_id}" "${BORG_ADVANCED_PYTHON}" -u "${REPO_ROOT}/scripts/build_advanced_xgboost_dataset.py"
  echo "[advanced_feature_build_resumable] done cluster=${cluster_id} path=${feature_path}"
done

echo "[advanced_feature_build_resumable] completed"

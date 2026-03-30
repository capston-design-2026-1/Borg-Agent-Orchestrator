#!/bin/zsh

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/advanced_env.sh"

LOG_DIR="${HOME}/Documents/borg_xgboost_workspace/runtime/logs"
mkdir -p "${LOG_DIR}"
STAMP="$(TZ=Asia/Seoul date +%Y%m%d%H%M%S)"
LOG_FILE="${LOG_DIR}/${STAMP}_advanced_train_resumable.log"
LATEST_LOG="${LOG_DIR}/latest_advanced_train_resumable.log"
ln -sfn "${LOG_FILE}" "${LATEST_LOG}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[advanced_train_resumable] started_at=${STAMP}"
echo "[advanced_train_resumable] log=${LOG_FILE}"

raw_horizons="${BORG_PREDICTION_HORIZON_MINUTES:-5,15,30,45,60}"
horizons=("${(@s:,:)raw_horizons}")
model_name="${BORG_XGB_MODEL_NAME:-${BORG_XGBOOST_MODEL_NAME:-xgboost_failure_risk}}"

for minutes in "${horizons[@]}"; do
  target="target_failure_${minutes}m"
  model_path="${BORG_XGBOOST_MODEL_DIR}/${model_name}_${target}/model.json"
  metrics_path="${BORG_XGBOOST_MODEL_DIR}/${model_name}_${target}/metrics.json"

  if [[ -f "${model_path}" && -f "${metrics_path}" ]]; then
    echo "[advanced_train_resumable] skip target=${target} reason=artifacts_exist"
    continue
  fi

  echo "[advanced_train_resumable] start target=${target}"
  BORG_PREDICTION_HORIZON_MINUTES="${minutes}" "${BORG_ADVANCED_PYTHON}" -u "${REPO_ROOT}/scripts/train_advanced_xgboost.py"
  echo "[advanced_train_resumable] done target=${target}"
done

echo "[advanced_train_resumable] completed"

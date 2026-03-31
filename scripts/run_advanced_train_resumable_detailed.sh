#!/bin/zsh

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/advanced_env.sh"

LOG_DIR="${HOME}/Documents/borg_xgboost_workspace/runtime/logs"
mkdir -p "${LOG_DIR}"
STAMP="$(TZ=Asia/Seoul date +%Y%m%d%H%M%S)"
LOG_FILE="${LOG_DIR}/${STAMP}_advanced_train_resumable_detailed.log"
LATEST_LOG="${LOG_DIR}/latest_advanced_train_resumable_detailed.log"
ln -sfn "${LOG_FILE}" "${LATEST_LOG}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[advanced_train_resumable_detailed] started_at=${STAMP}"
echo "[advanced_train_resumable_detailed] log=${LOG_FILE}"

raw_horizons="${BORG_PREDICTION_HORIZON_MINUTES:-5,15,30,45,60}"
horizons=("${(@s:,:)raw_horizons}")
model_name="${BORG_XGBOOST_MODEL_NAME:-${BORG_XGB_MODEL_NAME:-xgboost_failure_risk}}"

for minutes in "${horizons[@]}"; do
  target="target_failure_${minutes}m"
  model_path="${BORG_XGBOOST_MODEL_DIR}/${model_name}_${target}/model.json"
  metrics_path="${BORG_XGBOOST_MODEL_DIR}/${model_name}_${target}/metrics.json"

  if [[ -f "${model_path}" && -f "${metrics_path}" ]]; then
    echo "[advanced_train_resumable_detailed] skip target=${target} reason=artifacts_exist"
    continue
  fi

  echo "[advanced_train_resumable_detailed] start target=${target} model_name=${model_name}"
  echo "[advanced_train_resumable_detailed] params n_estimators=${BORG_XGB_N_ESTIMATORS:-400} max_depth=${BORG_XGB_MAX_DEPTH:-8} learning_rate=${BORG_XGB_LEARNING_RATE:-0.05} subsample=${BORG_XGB_SUBSAMPLE:-0.8} colsample_bytree=${BORG_XGB_COLSAMPLE_BYTREE:-0.8} min_child_weight=${BORG_XGB_MIN_CHILD_WEIGHT:-5} reg_alpha=${BORG_XGB_REG_ALPHA:-0.0} reg_lambda=${BORG_XGB_REG_LAMBDA:-1.0} early_stopping=${BORG_XGB_EARLY_STOPPING_ROUNDS:-off}"
  BORG_PREDICTION_HORIZON_MINUTES="${minutes}" \
  BORG_XGB_VERBOSE_EVAL="${BORG_XGB_VERBOSE_EVAL:-25}" \
  "${BORG_ADVANCED_PYTHON}" -u "${REPO_ROOT}/scripts/train_advanced_xgboost.py"
  echo "[advanced_train_resumable_detailed] done target=${target}"
done

echo "[advanced_train_resumable_detailed] completed"

#!/bin/zsh

set -euo pipefail

OVERRIDE_BORG_CLUSTERS="${BORG_CLUSTERS-}"
source "$(cd "$(dirname "$0")" && pwd)/advanced_env.sh"
if [[ -n "${OVERRIDE_BORG_CLUSTERS}" ]]; then
  export BORG_CLUSTERS="${OVERRIDE_BORG_CLUSTERS}"
fi

LOG_DIR="${HOME}/Documents/borg_xgboost_workspace/runtime/logs"
mkdir -p "${LOG_DIR}"
STAMP="$(TZ=Asia/Seoul date +%Y%m%d%H%M%S)"
LOG_FILE="${LOG_DIR}/${STAMP}_advanced_feature_build_resumable_detailed.log"
LATEST_LOG="${LOG_DIR}/latest_advanced_feature_build_resumable_detailed.log"
ln -sfn "${LOG_FILE}" "${LATEST_LOG}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[advanced_feature_build_resumable_detailed] started_at=${STAMP}"
echo "[advanced_feature_build_resumable_detailed] log=${LOG_FILE}"

clusters=("${(@s:,:)BORG_CLUSTERS}")
feature_dir="${BORG_XGBOOST_FEATURE_DIR}"

for cluster_id in "${clusters[@]}"; do
  feature_path="${feature_dir}/${cluster_id}_advanced_failure_features.parquet"
  echo "[advanced_feature_build_resumable_detailed] cluster=${cluster_id} output=${feature_path}"
  BORG_CLUSTERS="${cluster_id}" "${BORG_ADVANCED_PYTHON}" -u "${REPO_ROOT}/scripts/build_advanced_xgboost_dataset.py"
  "${BORG_ADVANCED_PYTHON}" - <<PY
from pathlib import Path
import polars as pl
path = Path("${feature_path}")
if path.exists():
    frame = pl.scan_parquet(str(path)).select([
        pl.len().alias("rows"),
        pl.col("target_failure_5m").sum().alias("failure_5m"),
        pl.col("target_failure_15m").sum().alias("failure_15m"),
        pl.col("target_failure_30m").sum().alias("failure_30m"),
        pl.col("target_failure_45m").sum().alias("failure_45m"),
        pl.col("target_failure_60m").sum().alias("failure_60m"),
    ]).collect().to_dicts()[0]
    print(f"[advanced_feature_build_resumable_detailed] cluster=${cluster_id} stats={frame}")
else:
    print(f"[advanced_feature_build_resumable_detailed] cluster=${cluster_id} output_missing")
PY
done

echo "[advanced_feature_build_resumable_detailed] completed"

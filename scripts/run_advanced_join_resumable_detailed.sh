#!/bin/zsh

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/advanced_env.sh"

LOG_DIR="${HOME}/Documents/borg_xgboost_workspace/runtime/logs"
mkdir -p "${LOG_DIR}"
STAMP="$(TZ=Asia/Seoul date +%Y%m%d%H%M%S)"
LOG_FILE="${LOG_DIR}/${STAMP}_advanced_join_resumable_detailed.log"
LATEST_LOG="${LOG_DIR}/latest_advanced_join_resumable_detailed.log"
ln -sfn "${LOG_FILE}" "${LATEST_LOG}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[advanced_join_resumable_detailed] started_at=${STAMP}"
echo "[advanced_join_resumable_detailed] log=${LOG_FILE}"

clusters=("${(@s:,:)BORG_CLUSTERS}")
dataset_dir="${BORG_DATASET_DIR}"

for cluster_id in "${clusters[@]}"; do
  dataset_path="${dataset_dir}/${cluster_id}_dataset.parquet"
  echo "[advanced_join_resumable_detailed] cluster=${cluster_id} output=${dataset_path}"
  BORG_CLUSTERS="${cluster_id}" "${BORG_ADVANCED_PYTHON}" -u "${REPO_ROOT}/scripts/make_dataset.py"
  "${BORG_ADVANCED_PYTHON}" - <<PY
from pathlib import Path
import polars as pl
path = Path("${dataset_path}")
if path.exists():
    rows = pl.scan_parquet(str(path)).select(pl.len()).collect().item()
    event_rows = pl.scan_parquet(str(path)).select(pl.col("final_event_type").is_not_null().sum()).collect().item()
    print(f"[advanced_join_resumable_detailed] cluster=${cluster_id} rows={rows} event_labeled_rows={event_rows}")
else:
    print(f"[advanced_join_resumable_detailed] cluster=${cluster_id} output_missing")
PY
done

echo "[advanced_join_resumable_detailed] completed"

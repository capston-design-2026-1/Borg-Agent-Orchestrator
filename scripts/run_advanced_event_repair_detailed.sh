#!/bin/zsh

set -euo pipefail

source "$(cd "$(dirname "$0")" && pwd)/advanced_env.sh"

LOG_DIR="${HOME}/Documents/borg_xgboost_workspace/runtime/logs"
mkdir -p "${LOG_DIR}"
STAMP="$(TZ=Asia/Seoul date +%Y%m%d%H%M%S)"
LOG_FILE="${LOG_DIR}/${STAMP}_advanced_event_repair_detailed.log"
LATEST_LOG="${LOG_DIR}/latest_advanced_event_repair_detailed.log"
ln -sfn "${LOG_FILE}" "${LATEST_LOG}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[advanced_event_repair_detailed] started_at=${STAMP}"
echo "[advanced_event_repair_detailed] log=${LOG_FILE}"

clusters_raw="${BORG_CLUSTERS:-e,f,g}"
clusters=("${(@s:,:)clusters_raw}")

for cluster_id in "${clusters[@]}"; do
  target_dir="${BORG_PROCESSED_DIR}/flat_shards/events/${cluster_id}"
  count_before="$(find "${target_dir}" -type f -name '*.parquet' 2>/dev/null | wc -l | tr -d ' ')"
  echo "[advanced_event_repair_detailed] delete cluster=${cluster_id} event_parquet_count_before=${count_before}"
  rm -f "${target_dir}"/*.parquet
done

echo "[advanced_event_repair_detailed] regenerate clusters=${clusters_raw} kinds=events"
BORG_CLUSTERS="${clusters_raw}" \
BORG_FLATTEN_KINDS="events" \
"${BORG_ADVANCED_PYTHON}" -u "${REPO_ROOT}/scripts/data_flattener_detailed.py"

echo "[advanced_event_repair_detailed] completed"

# Detailed Progress And Repair Plan

Timestamp: `2026-03-31 15:03 KST`

## Why New Additive Scripts Were Added

- Existing advanced wrappers were good enough for batch execution, but they were too sparse for long-running repair and retraining work
- The new scripts were added instead of replacing the earlier ones so previous workflows and reports remain intact
- The goal is:
  - more detailed live logs
  - per-cluster and per-kind checkpoints
  - audit summaries after repair runs
  - explicit rerun paths for broken event shards

## New Scripts

- `scripts/data_flattener_detailed.py`
  - supports `BORG_FLATTEN_KINDS`
  - logs queue counts, heartbeat rate, ETA, and post-run audits
- `scripts/run_advanced_event_repair_detailed.sh`
  - deletes selected advanced event parquet shards
  - regenerates only the selected event shards with the detailed flattener
- `scripts/run_advanced_join_resumable_detailed.sh`
  - reruns join cluster-by-cluster and logs resulting row counts and event-labeled rows
- `scripts/run_advanced_feature_build_resumable_detailed.sh`
  - rebuilds feature parquet cluster-by-cluster and logs positive-label totals per horizon

## Immediate Repair Target

- Clusters `e`, `f`, and `g`
- Current problem:
  - event flat shards exist
  - but event join-key columns are all null in the existing parquet files
  - therefore joined datasets have zero event labels
  - therefore feature sets have zero positives for all horizons

## Repair Sequence

1. Stop the currently running tuned retrain to free machine resources
2. Delete only `e/f/g` event parquet shards under the advanced workspace
3. Regenerate only those event shards with `run_advanced_event_repair_detailed.sh`
4. Rerun join for `e/f/g` with `run_advanced_join_resumable_detailed.sh`
5. Rerun feature build for `e/f/g` with `run_advanced_feature_build_resumable_detailed.sh`
6. Confirm that positive labels now exist
7. Resume model training on the repaired dataset

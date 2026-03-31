# Advanced Join Fix Handoff

Timestamp: `2026-03-31 03:42 KST`

## What Was Fixed

- `scripts/make_dataset.py` no longer glob-scans mixed-schema advanced parquet shards directly
- The joiner now scans each shard lazily, casts into the expected schema per shard, and only then concatenates the normalized lazy frames
- This fixes the prior advanced join crash:

```text
polars.exceptions.SchemaError: data type mismatch for column time: incoming: Int64 != target: String
```

- `scripts/data_flattener.py` no longer relies on `scan_ndjson(..., schema_overrides=Int64)` for quoted numeric scalar fields
- The flattener now scans those fields permissively and casts them with `strict=False` in `with_columns(...)`
- This fixes the advanced usage-shard bug where `start_time`, `end_time`, `collection_id`, `instance_index`, and `machine_id` were written as all-null for clusters `b`, `d`, `e`, `f`, and `g`

## Verification

- Raw advanced usage sample check for `b_usage-000000000000.json.gz` now casts correctly to `Int64`
- All advanced usage shard parquets under `~/Documents/borg_xgboost_workspace/processed/flat_shards/usage` were deleted and regenerated successfully
- Post-regeneration usage-key validation now shows non-null counts equal to row counts for clusters `b`, `c`, `d`, `e`, `f`, and `g`
- Current join rerun log: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331033021_advanced_join.log`
- Verified joined output so far:
  - `b_dataset.parquet`: `62,116,886` rows

## Current State

- `./scripts/run_advanced_join.sh` is still running from the `20260331033021` log
- No new join error has appeared after the fixes
- Cluster `b` completed successfully during the rerun
- The next step after join completion is still `./scripts/run_advanced_feature_build.sh`, then `./scripts/run_advanced_train.sh`

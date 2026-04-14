# Advanced Flatten Handoff

Timestamp: `2026-03-31 02:36 KST`

## Scope

This report records the current state of the isolated advanced XGBoost pipeline under `~/Documents/borg_xgboost_workspace`.

## Current Runtime State

- Live pipeline entrypoint: `./scripts/run_advanced_xgboost_pipeline.sh`
- Live pipeline log: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331021002_advanced_pipeline.log`
- Live flatten log: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331021002_advanced_flatten.log`
- Advanced flatten config:
  - `BORG_FLATTEN_WORKERS=20`
  - `BORG_FLATTEN_HEARTBEAT_SECONDS=10`
- Current flattened advanced shard count: `56` non-`.DS_Store` parquet files under `~/Documents/borg_xgboost_workspace/processed/flat_shards`

## Recent Behavioral Changes

- Advanced stage wrappers now write timestamped logs and maintain `latest_advanced_*.log` symlinks.
- The flattener now resumes from existing shard parquet outputs instead of restarting from zero.
- The flattener now logs:
  - `started ...` when a worker begins a shard
  - `done ...` when a shard parquet is written
  - `heartbeat completed=... running=... pending=...` during long-running shard work
- Advanced flattening was pushed from `8` workers to `10`, then to `20`, at the user's request.

## Current Bottleneck

- Large advanced `events` shards are still the slowest part of the pipeline.
- Example event shard sizes are roughly `500 MB` compressed each.
- The current event flatten path still extracts nested `resource_request` values through `pl.Object` plus `map_elements(...)`, which is slower than a native struct-based path.
- This is the main reason the log can show repeated `heartbeat` lines without frequent `done ...` lines.

## Current Interpretation

- If the log shows `started ...` plus repeated `heartbeat completed=...` lines, the flattener is active even when shard completions are sparse.
- Sparse completions are expected while the first wave of large event shards is being parsed and written.
- If a future session needs more throughput, the next high-value optimization is to replace the object-backed event nested extraction path rather than only increasing worker count further.

## Next Actions

1. Let the current advanced flatten run continue.
2. If completions remain too sparse, optimize event nested-field extraction in `scripts/data_flattener.py`.
3. After flatten completes, continue through join, feature build, and XGBoost training using the same isolated advanced workspace.

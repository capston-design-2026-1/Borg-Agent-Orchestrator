# Advanced Training Completed

Timestamp: `2026-03-31 04:23 KST`

## Outcome

- The advanced XGBoost training stage is complete for all configured horizons:
  - `5m`
  - `15m`
  - `30m`
  - `45m`
  - `60m`
- Final train log:
  - `~/Documents/borg_xgboost_workspace/runtime/logs/20260331041159_advanced_train_resumable.log`

## Training Configuration

- Runtime wrapper:
  - `scripts/run_advanced_train_resumable.sh`
- Threads:
  - `BORG_XGB_N_JOBS=10`
- Deterministic bounded sampling:
  - train cap: `8,000,000` rows
  - validation cap: `2,000,000` rows
- Positive examples were preserved in full within each split
- Negatives were deterministically sampled by hashed row id

## Metrics Summary

- `target_failure_5m`
  - average precision: `0.9810528429`
  - precision@1%: `0.9940523790`
  - recall@1%: `0.3911846272`
- `target_failure_15m`
  - average precision: `0.9726464046`
  - precision@1%: `0.9951022040`
  - recall@1%: `0.3226700374`
- `target_failure_30m`
  - average precision: `0.9720370948`
  - precision@1%: `0.9954522739`
  - recall@1%: `0.2821028481`
- `target_failure_45m`
  - average precision: `0.9659209812`
  - precision@1%: `0.9960021988`
  - recall@1%: `0.2523550266`
- `target_failure_60m`
  - average precision: `0.9595348583`
  - precision@1%: `0.9960519740`
  - recall@1%: `0.2326268120`

## Artifacts

- Model root:
  - `~/Documents/borg_xgboost_workspace/models/xgboost`
- Each horizon now has:
  - `model.json`
  - `model_config.json`
  - `metrics.json`
  - `feature_importance.json`
  - `validation_predictions.parquet`

## Important Notes

- The full feature store spans all clusters `b` through `g`, but the current fixed-shard slice produced no positive labels for clusters `e`, `f`, and `g`
- Positive training signal currently comes from clusters `b`, `c`, and `d`
- The next useful investigation is whether increasing advanced raw shard depth or selecting different shard windows restores positive examples for `e`, `f`, and `g`

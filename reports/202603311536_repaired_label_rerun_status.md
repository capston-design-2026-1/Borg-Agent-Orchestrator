# Repaired Label Rerun Status

## Summary

- Repaired the advanced event flat shards with new additive detailed wrappers instead of replacing earlier scripts.
- Regenerated advanced event parquet with fully populated join keys for clusters `b` through `g`.
- Reran the advanced join for repaired clusters `e`, `f`, and `g`.
- Reran the advanced feature build for repaired clusters `e`, `f`, and `g`.
- Confirmed that `e`, `f`, and `g` no longer have zero positives.
- Restarted tuned XGBoost training under a new model name that isolates repaired-label training from the obsolete pre-repair tuned run.

## Detailed Logs

- Event repair: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331151302_advanced_event_repair_detailed.log`
- Join rerun: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331152055_advanced_join_resumable_detailed.log`
- Feature rerun: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331152830_advanced_feature_build_resumable_detailed.log`
- Live training rerun: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331153419_advanced_train_resumable_detailed.log`

## Repaired Join Results

- `e`: `58,784,525` rows, `22,553,673` event-labeled rows
- `f`: `71,298,784` rows, `54,306,159` event-labeled rows
- `g`: `61,083,781` rows, `20,708,106` event-labeled rows

## Repaired Feature Label Totals

- `b`: `5m=65,537`, `15m=78,359`, `30m=91,387`, `45m=96,116`, `60m=99,303`
- `c`: `5m=152,711`, `15m=182,451`, `30m=200,980`, `45m=212,647`, `60m=222,296`
- `d`: `5m=27,307`, `15m=35,422`, `30m=42,821`, `45m=48,111`, `60m=52,288`
- `e`: `5m=129,553`, `15m=175,699`, `30m=200,677`, `45m=220,331`, `60m=233,409`
- `f`: `5m=48,677`, `15m=93,644`, `30m=148,814`, `45m=194,633`, `60m=240,144`
- `g`: `5m=39,509`, `15m=60,618`, `30m=81,189`, `45m=97,625`, `60m=111,570`

## Training Rerun

- Obsolete tuned run: `xgboost_failure_risk_tuned_v1`
  - This run started before the `e/f/g` repair and should not be treated as the final tuned candidate.
- Current tuned run: `xgboost_failure_risk_tuned_v2_repaired_labels`
- Current target in progress at restart: `target_failure_5m`
- Tuned parameters:
  - `n_estimators=1600`
  - `max_depth=6`
  - `learning_rate=0.03`
  - `subsample=0.9`
  - `colsample_bytree=0.7`
  - `min_child_weight=8`
  - `reg_alpha=0.2`
  - `reg_lambda=2.0`
  - `early_stopping_rounds=80`
  - `verbose_eval=25`

## Fix Applied During Rerun

- The first attempt to start the detailed tuned retrain silently reset explicit hyperparameter overrides back to the env-file defaults.
- Cause: `scripts/run_advanced_train_resumable_detailed.sh` preserved model-name and horizon overrides, but not the rest of the `BORG_XGB_*` overrides.
- Fix: preserved all training-related runtime overrides before sourcing `advanced_env.sh`, then restored them afterward.
- Commit: `5f66e48` (`Preserve tuned train overrides in detailed wrapper`)

## Next Action

- Let `xgboost_failure_risk_tuned_v2_repaired_labels` finish all horizons.
- Compare repaired-label tuned metrics against the baseline trained model.
- Regenerate the English and Korean evaluation reports from the repaired-label winner.

# Advanced XGBoost Evaluation Report (English)

Generated at `2026-03-31 10:50 KST`

## Executive Summary

- All five production horizons (`5m`, `15m`, `30m`, `45m`, `60m`) completed successfully.
- The strongest average precision is at `5m` with `0.981053`.
- The strongest recall at the operational `1%` alert budget is also at `5m` with `0.391185`.
- Metric quality declines gradually as the prediction window gets longer, which is expected because longer horizons are harder and include more ambiguous pre-failure states.
- Even at `60m`, the model still keeps `precision@1%` above `0.996`, but recall falls from `0.391` at `5m` to `0.233` at `60m`.

## Horizon Comparison

| Horizon | AP | Precision@0.1% | Recall@0.1% | Precision@1% | Recall@1% | Valid Positives | Sampled Valid Rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5m | 0.981053 | 0.995502 | 0.039179 | 0.994052 | 0.391185 | 50,843 | 2,000,796 |
| 15m | 0.972646 | 0.998001 | 0.032363 | 0.995102 | 0.322670 | 61,707 | 2,000,815 |
| 30m | 0.972037 | 0.996502 | 0.028240 | 0.995452 | 0.282103 | 70,609 | 2,000,972 |
| 45m | 0.965921 | 0.998501 | 0.025310 | 0.996002 | 0.252355 | 78,980 | 2,001,067 |
| 60m | 0.959535 | 0.998501 | 0.023320 | 0.996052 | 0.232627 | 85,678 | 2,000,920 |

## Interpretation

- `5m` is the cleanest detection setting. The signal is closest to the terminal event, so separation is strongest and both AP and recall are best.
- `15m` and `30m` remain strong. Precision stays almost unchanged, but recall drops as more uncertain windows enter the positive set.
- `45m` and `60m` show the expected degradation pattern: AP falls and recall drops further, but the model still ranks the highest-risk windows very effectively.
- The ranking quality is unusually strong for every horizon. That is partly a real signal win, but it is also helped by the sampled training/evaluation design keeping all positives while deterministically downsampling negatives.

## Sampling And Evaluation Method

- Source train rows per horizon: about `307.8M`
- Source validation rows per horizon: about `77.0M`
- Sampled train rows per horizon: about `8.0M`
- Sampled validation rows per horizon: about `2.0M`
- All positive rows were retained.
- Negative rows were deterministically sampled by hashed row id.
- Temporal validation was used by splitting on `end_time` rather than random row shuffling.

This design keeps the experiment feasible on a `24 GB` laptop while preserving rare failure examples, but it also means the reported precision values describe a sampled alert population, not the untouched full negative pool.

## Feature Observations

- `task_age_us` appeared in the top-10 list for `5` horizon(s)
- `event_count` appeared in the top-10 list for `5` horizon(s)
- `observed_failure_by_window` appeared in the top-10 list for `5` horizon(s)
- `scheduling_class` appeared in the top-10 list for `5` horizon(s)
- `collection_recent_failure_count_12` appeared in the top-10 list for `5` horizon(s)
- `collection_recent_terminal_count_12` appeared in the top-10 list for `5` horizon(s)
- `priority` appeared in the top-10 list for `4` horizon(s)
- `usage_window` appeared in the top-10 list for `4` horizon(s)
- `req_cpu` appeared in the top-10 list for `4` horizon(s)
- `avg_mem_to_request_ratio` appeared in the top-10 list for `3` horizon(s)
- `max_mem_to_request_ratio` appeared in the top-10 list for `2` horizon(s)
- `collection_window_avg_cpu_sum` appeared in the top-10 list for `1` horizon(s)

The most repeated top features should be treated as the current stable core of the model. In practice these usually reflect a mix of:

- direct resource stress and utilization
- task-local temporal momentum
- local machine aggregation pressure
- recent terminal/failure history
- missingness indicators that mark structurally weak observations

## Remaining Risks

- Clusters `e`, `f`, and `g` produced zero positive labels in the current fixed-shard slice. The current model is therefore learning positive behavior mainly from `b`, `c`, and `d`.
- The evaluation is temporally split, which is good, but it is still drawn from the same shard-selection policy. Generalization to deeper or different shard windows is not yet proven.
- Because negatives are sampled, the current precision values should not be read as the exact production precision under the full raw event stream.
- Longer horizons may be more vulnerable to overfitting if model capacity is increased without stronger regularization or earlier stopping.
- The current report does not yet include calibration curves or cluster-held-out testing, so score calibration and cross-cluster portability are still open questions.

## Recommended Next Tuning Priorities

- Continue the ongoing hyperparameter sweep with early stopping and stronger regularization candidates.
- Check whether deeper shard coverage restores positive labels for `e`, `f`, and `g`.
- Add cluster-level holdout comparisons and calibration analysis.
- Compare the current production configuration against the tuning winner before promoting a new default.

## Reference Artifacts

- Models: `~/Documents/borg_xgboost_workspace/models/xgboost`
- Runtime log: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331041159_advanced_train_resumable.log`
- Handoff summary: `reports/202603310423_advanced_training_completed.md`

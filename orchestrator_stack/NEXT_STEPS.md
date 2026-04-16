# Orchestrator Stack Next Steps

1. Validate the live AIOpsLab adapter against the actual upstream package/session API and replace the current multi-method fallback probing with a confirmed contract.
2. Extend PPO training beyond smoke profile (`rllib_train_iters=1`) and benchmark policy performance over longer episodes.
3. Add SHAP diagnostics for XGBoost models to provide feature importance transparency.
4. Add model calibration and threshold optimization for `SafetyRiskForecast`.
5. Add curriculum training schedule for RLlib PPO multi-agent agents.

## Latest Session Note (2026-04-16 KST)

- Layer 5 Optuna tuning now executes a PPO-backed policy objective instead of the previous learning-rate-only heuristic stub:
  - `tune-policy-rewards` now samples `learning_rate`, `train_batch_size`, `minibatch_size`, `num_epochs`, and a batch-compatible `rollout_fragment_length`.
  - `run_policy_training()` and the example config now expose the PPO batch/epoch knobs directly.
  - Layer 4 PPO training now pins Ray trial artifacts under the requested runtime output directory and returns the actual training reward metric plus the resolved PPO hyperparameters.
  - Added `orchestrator_stack/tests/test_optuna_meta_tuning.py` to verify that Layer 5 forwards sampled RL hyperparameters into `train_multiagent_ppo()` rather than scoring a placeholder objective.
- Validation run status:
  - `python3 -m compileall orchestrator_stack/run.py orchestrator_stack/orchestrator/config.py orchestrator_stack/orchestrator/main.py orchestrator_stack/orchestrator/layer4/ppo_trainer.py orchestrator_stack/orchestrator/layer5/optuna_tuner.py orchestrator_stack/tests/test_optuna_meta_tuning.py`: success
  - `PYTHONPATH=orchestrator_stack ./.venv/bin/python -m unittest orchestrator_stack.tests.test_optuna_meta_tuning`: success
  - `PYTHONPATH=orchestrator_stack ./.venv/bin/python orchestrator_stack/run.py tune --config <temp-config> --trials 1`: success, wrote `reports/tuning/202604161029_optuna_orchestrator_reward_weights.md`
  - `PYTHONPATH=orchestrator_stack ./.venv/bin/python orchestrator_stack/run.py tune-policy-rewards --config <temp-config> --trials 1`: reached the PPO-backed trial path, but Ray initialization is blocked in this sandbox by macOS process-enumeration permissions (`PermissionError` from `psutil`/`sysctl`), so the command now returns a structured `"status": "skipped"` result instead of crashing
- Remaining validation gap:
  - Re-run `tune-policy-rewards` in a non-sandboxed local shell where `ray.init()` is allowed to enumerate processes, then confirm a completed Optuna study report for `orchestrator_policy_and_rewards`.

- Layer 2 simulator + feature extraction were expanded to use a shared AIOpsLab-style normalization path:
  - `state_to_observation()` now accepts nested state wrappers, dict-backed node/task collections, queued-task placement, and common alternate field names (`machines`, `pods`, `risk_scores`, `demand_scores`, etc.).
  - `AIOpsLabBackend` now falls back to a stateful local twin-style simulation instead of returning an empty mock observation on every step, so Layer 4/5 loops can exercise Layer 2 behavior without the upstream package.
  - `TraceDrivenTwinBackend` and Layer 2 feature extraction now both depend on the same normalized observation contract instead of separate raw-dict parsing.
- Layer 2 features are now pinned at `FEATURE_COUNT=8`; synthetic asset generation now derives its matrix width from that shared constant.
- Added simulator normalization and adapter tests in `orchestrator_stack/tests/test_simulator.py`.
- Extended feature tests in `orchestrator_stack/tests/test_feature_extractor.py` to cover per-node task pressure/power-state signals and flat Prometheus-style metric-row ingestion.
- Validation run status:
  - `python3 -m compileall orchestrator_stack/orchestrator/layer2 orchestrator_stack/tests orchestrator_stack/examples/generate_synthetic_assets.py`: success
  - `PYTHONPATH=orchestrator_stack python3` Layer 2 smoke for `state_to_observation()`, fallback `AIOpsLabBackend`, and feature extraction over grouped + flat metric rows: success (`layer2-smoke-ok`)
  - `pytest` could not be executed because this worktree `.venv` is a self-referential symlink and the fallback `python3` runtime is missing `numpy` and `pytest`

- Previous session (2026-04-15 KST): Layer 1 ingestion and trace loading contracts were hardened:
  - Collector now validates all rows (not only the first row), detects mixed flat/grouped shapes, and reports row-indexed schema errors.
  - Collector now enforces non-negative queue fields, bool-like parsing for `alive/task_death`, and positive `interval_seconds`.
  - Trace ingestor now validates required trace keys and node/task minimum schema for both `.json` and `.jsonl`.
  - Trace ingestor now validates optional task fields (`urgency`, `queue_priority`, `alive`), enforces non-negative `queue_length`, and fails fast on missing trace files.
  - JSONL decode errors now include exact line number.
- Added contract tests in `orchestrator_stack/tests/test_collector.py` and `orchestrator_stack/tests/test_trace_ingestor.py`.
- Added artifact/schema notes for Layer 1 and trace logs in `orchestrator_stack/examples/README.md` and `reports/traces/README.md`.
- Validation gap: this worktree runtime does not currently have `pytest` installed, so only smoke + compile checks were executed in-session.

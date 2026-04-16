# Orchestrator Stack Next Steps

1. Validate the live AIOpsLab adapter against the actual upstream package/session API and replace the current multi-method fallback probing with a confirmed contract.
2. Extend PPO training beyond smoke profile (`rllib_train_iters=1`) and benchmark policy performance over longer episodes.
3. Add SHAP diagnostics for XGBoost models to provide feature importance transparency.
4. Add model calibration and threshold optimization for `SafetyRiskForecast`.
5. Add curriculum training schedule for RLlib PPO multi-agent agents.

## Latest Session Note (2026-04-16 KST, targeted fixups/resiliency slice)

- `run.py run --config orchestrator_stack/config/orchestrator.example.json` no longer crashes when the configured trace exists but the configured XGBoost model artifacts are missing:
  - `ensure_brain_models_exist()` now trains both predictor models from the configured trace before the episode starts.
  - Added focused coverage in `orchestrator_stack/tests/test_main.py` for missing-model bootstrap behavior.
- `run.py full-process --config orchestrator_stack/config/orchestrator.example.json --trials 1` now completes end to end in this sandboxed worktree instead of aborting during RLlib startup:
  - Layer 4 now redirects Ray trial storage into `orchestrator_stack/runtime/rllib`.
  - If RLlib cannot initialize because the environment blocks Ray internals (observed here: macOS `sysctl`/`psutil` permission failure during `ray.init()`), PPO returns a structured `status=skipped` payload and the remaining full-process stages continue.
- Validation run status:
  - `PYTHONPATH=orchestrator_stack .venv/bin/python -m compileall orchestrator_stack/orchestrator/main.py orchestrator_stack/orchestrator/layer4/ppo_trainer.py orchestrator_stack/tests/test_main.py`: success
  - `PYTHONPATH=orchestrator_stack .venv/bin/python orchestrator_stack/run.py run --config <temp-config-with-missing-model-paths>`: success; auto-trained models and completed 5-step episode
  - `PYTHONPATH=orchestrator_stack .venv/bin/python orchestrator_stack/run.py full-process --config orchestrator_stack/config/orchestrator.example.json --trials 1`: success; PPO returned `status=skipped`, reward tuning and policy+reward tuning completed
  - `.venv/bin/python -m pytest ...`: still unavailable because `pytest` is not installed in the repo virtualenv
- Follow-up still needed outside this sandbox:
  - validate PPO training on an unrestricted host where Ray can initialize normally and confirm the `status=trained` path still works

## Previous Session Note (2026-04-16 KST, RLlib/referee slice)

- Layer 4 referee resolution is now explicit and deterministic instead of a simple priority sort:
  - `resolve_with_context()` records the chosen action, rationale, and overridden proposals while keeping `resolve()` as the single-action backend adapter.
  - Agent A migration now preempts other actions, Agent C protective admission (`queue`/`reject`) now preempts efficiency actions, and idle/noop fallback stays deterministic.
- `OrchestratorMultiAgentEnv` now includes RLlib-facing referee metadata in per-agent `infos`:
  - each agent sees its decoded proposal, whether it was overridden, the override reason, the resolved backend action, and the current weighted global score.
- Added focused Layer 4 tests in `orchestrator_stack/tests/test_referee.py` and `orchestrator_stack/tests/test_rllib_env.py`.
- Validation run status:
  - `PYTHONPATH=orchestrator_stack .venv/bin/python -m compileall orchestrator_stack/orchestrator/layer4 orchestrator_stack/tests/test_referee.py orchestrator_stack/tests/test_rllib_env.py`: success
  - `PYTHONPATH=orchestrator_stack .venv/bin/python` smoke invoking `test_policy_decode`, `test_referee`, and `test_rllib_env`: success (`layer4-smoke-ok`)
  - `.venv/bin/python -m pytest ...`: failed because `pytest` is not installed in the repo virtualenv

## Previous Session Note (2026-04-16 KST, Layer 2 slice)

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

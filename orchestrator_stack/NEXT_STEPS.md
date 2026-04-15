# Orchestrator Stack Next Steps

1. Complete AIOpsLab state mapping for `_to_observation` (convert real telemetry to internal Node/Task models).
2. Extend PPO training beyond smoke profile (`rllib_train_iters=1`) and benchmark policy performance over longer episodes.
3. Add SHAP diagnostics for XGBoost models to provide feature importance transparency.
4. Add model calibration and threshold optimization for `SafetyRiskForecast`.
5. Add curriculum training schedule for RLlib PPO multi-agent agents.

## Latest Session Note (2026-04-15 KST)

- Layer 1 ingestion and trace loading contracts were hardened:
  - Collector now validates all rows (not only the first row), detects mixed flat/grouped shapes, and reports row-indexed schema errors.
  - Trace ingestor now validates required trace keys and node/task minimum schema for both `.json` and `.jsonl`.
  - JSONL decode errors now include exact line number.
- Added contract tests in `orchestrator_stack/tests/test_collector.py` and `orchestrator_stack/tests/test_trace_ingestor.py`.
- Added artifact/schema notes for Layer 1 and trace logs in `orchestrator_stack/examples/README.md` and `reports/traces/README.md`.
- Validation gap: this worktree runtime does not currently have `pytest` installed, so only smoke + compile checks were executed in-session.

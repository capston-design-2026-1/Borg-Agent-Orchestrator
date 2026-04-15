# Orchestrator Stack Next Steps

1. Replace `AIOpsLabBackend` placeholder mapping with full `_to_observation` conversion from live AIOpsLab telemetry to internal `Observation`/`Node`/`Task`.
2. Complete Layer 4 RLlib runtime hardening for restricted macOS/sandbox hosts so `full-process` yields `ppo.status="trained"` (currently degrades with `sysctl` permission errors in restricted environments).
3. Extend PPO training beyond smoke profile (`rllib_train_iters=1`) and benchmark policy quality over longer episodes with saved checkpoints.
4. Add SHAP diagnostics for Layer 3 XGBoost predictors and include feature-importance artifacts in reports.
5. Add calibration/threshold optimization for `SafetyRiskForecast` and wire chosen thresholds into action gating.
6. Add curriculum schedule support for multi-agent PPO (staged reward weights / episode complexity).

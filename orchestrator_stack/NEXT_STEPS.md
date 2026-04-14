# Orchestrator Stack Next Steps

1. Complete AIOpsLab state mapping for `_to_observation` (convert real telemetry to internal Node/Task models).
2. Extend PPO training beyond smoke profile (`rllib_train_iters=1`) and benchmark policy performance over longer episodes.
3. Add SHAP diagnostics for XGBoost models to provide feature importance transparency.
4. Add model calibration and threshold optimization for `SafetyRiskForecast`.
5. Add curriculum training schedule for RLlib PPO multi-agent agents.

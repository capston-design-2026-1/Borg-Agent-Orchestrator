# Orchestrator Stack Next Steps

1. Bind `AIOpsLabBackend` to actual upstream environment APIs (replace trace shim calls with native action/state exchange).
2. Extend PPO training beyond smoke profile (`rllib_train_iters=1`) and benchmark policy performance over longer episodes.
3. Add timestamped Optuna sweep export reports under top-level `reports/` for each tuning run.
4. Add CI tests with `pytest` and an optional RLlib integration marker for `full-process`.
5. Add schema validation for incoming Prometheus JSON to detect metric/key drift before trace conversion.

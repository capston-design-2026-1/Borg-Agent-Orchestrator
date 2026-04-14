# Orchestrator Stack Next Steps

1. Bind `AIOpsLabBackend` to actual upstream environment APIs (replace trace shim calls with native action/state exchange).
2. Train and evaluate real PPO policies with RLlib on longer traces; compare against heuristic fallback scores.
3. Add persistent trial report export (KST timestamped markdown/json under top-level `reports/`) for each Optuna sweep.
4. Add CI tests with `pytest` + optional RLlib marker to validate `build-trace -> train-brains -> run` pipeline.
5. Add schema validation for incoming Prometheus JSON to detect metric/key drift before trace conversion.

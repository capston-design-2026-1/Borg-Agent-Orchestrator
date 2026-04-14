# Orchestrator Stack Next Steps

1. Implement native AIOpsLab adapter methods in `layer2/simulator.py` against the exact environment APIs from the pinned upstream revision.
2. Replace heuristic action generation in `layer4/rllib_env.py` with PPO policy-driven actions and configure per-agent policy mapping.
3. Add feature-store pipeline that builds training matrices from real Prometheus/JSON traces rather than synthetic `.npz` files.
4. Add persistent trial tracking for Optuna studies (SQLite storage) and export trial reports under top-level `reports/` with KST timestamps.
5. Add integration tests that run one short end-to-end episode using trained toy models in CI.

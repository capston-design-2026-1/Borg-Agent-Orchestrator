# Milestone Journey (Full Orchestrator)

## M1: Foundation and Isolation

- Create independent `orchestrator_stack/` workspace
- Implement 6-layer code skeleton with real data contracts
- Add CLI to run train/execute/tune flows
- Add dedicated operational docs (`README`, `AGENTS`, `NEXT_STEPS`)

## M2: Real Data Ingestion

- Replace synthetic traces with Prometheus-exported JSON pipelines
- Validate cardinality, timestamp monotonicity, and schema drift checks
- Add local-cloud adapter tests for production trace formats

## M3: Digital Twin Integration

- Wire `AIOpsLabBackend` against upstream AIOpsLab APIs
- Support state sync, action dispatch, reward callbacks
- Add deterministic replay mode and episode-level trace debugging

## M4: Predictive Intelligence Hardening

- Train risk and demand models on real feature store outputs
- Add model calibration, threshold optimization, and SHAP diagnostics
- Version models and feature schemas with compatibility checks

## M5: RLlib Multi-Agent PPO

- Replace heuristic action generation with learned PPO policies
- Add per-agent policy configs and curriculum schedules
- Add evaluation benchmarks against heuristic and single-agent baselines

## M6: Optuna Governance and Productionization

- Run Optuna studies over policy hyperparameters and reward weights
- Persist studies and publish KST timestamped reports in `reports/`
- Add deployment runbook and rollback-safe operation procedures

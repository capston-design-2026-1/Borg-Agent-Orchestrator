# Orchestrator Optuna Meta-Tuning Integration (Session 1, 2026-04-16 KST)

## Scope

- `orchestrator_stack/` Layer 4 and Layer 5 tuning/runtime integration
- Root/orchestrator continuity docs for the same slice

## Implemented

1. PPO-backed policy tuning path
- Replaced the previous `tune-policy-rewards` placeholder objective that only penalized learning rate.
- Optuna policy trials now sample and forward these RL hyperparameters into `train_multiagent_ppo()`:
  - `learning_rate`
  - `train_batch_size`
  - `minibatch_size`
  - `num_epochs`
  - `rollout_fragment_length`
- The rollout fragment search space is restricted to divisors of the sampled train batch size so RLlib batch validation does not reject invalid trial combinations.

2. PPO runtime plumbing
- Added PPO config fields to `OrchestratorConfig` and `orchestrator_stack/config/orchestrator.example.json`.
- `run_policy_training()` now passes the PPO batch and epoch knobs through to Layer 4.
- Layer 4 training now pins Ray trial output under the requested runtime directory and returns the effective PPO hyperparameters with the training summary.

3. Failure handling
- `tune-policy-rewards` now returns a structured `"status": "skipped"` result if no PPO-backed Optuna trial completes, instead of crashing the CLI.
- This keeps the runtime path explicit about Ray/runtime failures while preserving successful reward-only Optuna studies.

4. Tests
- Added `orchestrator_stack/tests/test_optuna_meta_tuning.py`.
- Coverage in this slice:
  - Layer 5 samples RL hyperparameters in addition to reward weights.
  - `tune_policy_and_reward_layer()` calls `train_multiagent_ppo()` with the sampled trial values instead of a stubbed heuristic-only score path.

## Validation

Executed in-session:

- `python3 -m compileall orchestrator_stack/run.py orchestrator_stack/orchestrator/config.py orchestrator_stack/orchestrator/main.py orchestrator_stack/orchestrator/layer4/ppo_trainer.py orchestrator_stack/orchestrator/layer5/optuna_tuner.py orchestrator_stack/tests/test_optuna_meta_tuning.py`
  - Result: success
- `PYTHONPATH=orchestrator_stack ./.venv/bin/python -m unittest orchestrator_stack.tests.test_optuna_meta_tuning`
  - Result: success
- `PYTHONPATH=orchestrator_stack ./.venv/bin/python orchestrator_stack/run.py train-brains --trace orchestrator_stack/examples/sample_trace.json --risk-out orchestrator_stack/examples/models/risk_model.json --demand-out orchestrator_stack/examples/models/demand_model.json`
  - Result: success
- `PYTHONPATH=orchestrator_stack ./.venv/bin/python orchestrator_stack/run.py tune --config <temp-config> --trials 1`
  - Result: success
  - Artifact: `reports/tuning/202604161029_optuna_orchestrator_reward_weights.md`
- `PYTHONPATH=orchestrator_stack ./.venv/bin/python orchestrator_stack/run.py tune-policy-rewards --config <temp-config> --trials 1`
  - Result: reached the PPO-backed trial path, but Ray initialization is blocked in this sandbox by a macOS `PermissionError` from process enumeration (`psutil` / `sysctl`)
  - Runtime behavior after this slice: returns structured JSON skip instead of crashing

## Remaining Gap

- Re-run `tune-policy-rewards` outside the current sandbox so `ray.init()` can complete and emit a finished `orchestrator_policy_and_rewards` Optuna report.
- The policy-tuning objective still adds a small heuristic stability term after PPO training; a later slice can replace that with learned-policy checkpoint evaluation.

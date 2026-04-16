# Orchestrator Global Scoreboard + Feedback Loop (Session 1, 2026-04-16 KST)

## Scope

- `orchestrator_stack/` Layer 6 scoreboard and direct Layer 4/main integrations only
- Root/orchestrator continuity docs for this slice

## Implemented

1. Shared Layer 6 feedback loop
- Added `FeedbackLoop` in `orchestrator_stack/orchestrator/layer6/scoreboard.py` so manual episodes, heuristic evaluation, and the RLlib env all use the same resolve-and-apply path.
- Removed duplicated local scoreboard/feedback bookkeeping from `run_episode()`, `evaluate_heuristic_policy()`, and `OrchestratorMultiAgentEnv.step()`.

2. Global scoreboard context for policy input
- Added `Scoreboard.current_feedback()` to provide a neutral pre-step feedback state.
- Added bounded `Scoreboard.observation_features(agent_name)` signals for:
  - latest global score
  - balance gap
  - current agent weight
  - current cumulative deficit
- Expanded RLlib env observations from `6` to `10` features by appending those 4 scoreboard signals to the base simulator vector.

3. Regression coverage
- Extended `orchestrator_stack/tests/test_scoreboard.py` to cover neutral feedback bootstrapping and scoreboard-feature imbalance behavior.

## Validation

Executed in-session:

- `python3 -m compileall orchestrator_stack/orchestrator/layer6 orchestrator_stack/orchestrator/layer4/rllib_env.py orchestrator_stack/orchestrator/layer4/ppo_trainer.py orchestrator_stack/orchestrator/main.py orchestrator_stack/tests/test_scoreboard.py`
  - Result: success
- `PYTHONPATH=orchestrator_stack python3` smoke for `FeedbackLoop`, scoreboard observation features, and referee weighting
  - Result: success (`scoreboard-feedback-smoke-ok`)

Could not execute in-session:

- `pytest`
  - Reason: this worktree `.venv` is a self-referential symlink, and fallback `python3` is missing `numpy` and `pytest`
- End-to-end RLlib env rollout
  - Reason: same runtime dependency gap prevented importing the full NumPy-backed RL env stack in-session

## Remaining Gap

- Run the new Layer 6 and RL env regression tests in a healthy repo `.venv` with `numpy`, `pytest`, and Ray installed.
- Direct upstream AIOpsLab API validation remains open and unchanged by this slice.

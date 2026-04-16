# Orchestrator RLlib + Referee (Session 1, 2026-04-16 KST)

## Scope

- `orchestrator_stack/` Layer 4 RLlib PPO multi-agent environment and referee conflict logic only.
- Focus kept on deterministic referee behavior plus RLlib-facing environment metadata.

## Completed

1. Referee conflict semantics
- Added `RefereeDecision` and `resolve_with_context()` in `orchestrator_stack/orchestrator/layer4/referee.py`.
- Preserved the existing single-action backend contract through `resolve()`, which now unwraps the structured decision.
- Implemented explicit precedence rules:
  - Agent A migration preempts all lower-priority actions.
  - Agent C protective admission (`queue` or `reject`) preempts efficiency actions.
  - Power-state proposals fall back to highest score when no safety action is present.
  - All-noop cycles still resolve deterministically.

2. RLlib environment behavior
- Updated `orchestrator_stack/orchestrator/layer4/rllib_env.py` to execute the structured referee decision while keeping the backend step signature unchanged.
- Added per-agent `infos` fields for:
  - decoded proposal
  - overridden flag and reason
  - resolved backend action
  - referee rationale
  - current weighted global score

3. Tests
- Extended `orchestrator_stack/tests/test_referee.py` to cover gatekeeper-vs-efficiency conflicts and deterministic noop fallback.
- Added `orchestrator_stack/tests/test_rllib_env.py` to pin the RLlib environment info contract and verify that a safety migration overrides concurrent sleep/queue proposals.

## Validation

- `PYTHONPATH=orchestrator_stack .venv/bin/python -m compileall orchestrator_stack/orchestrator/layer4 orchestrator_stack/tests/test_referee.py orchestrator_stack/tests/test_rllib_env.py`
  - Result: success
- `PYTHONPATH=orchestrator_stack .venv/bin/python` smoke importing and invoking:
  - `test_policy_decode`
  - `test_referee`
  - `test_rllib_env`
  - Result: success (`layer4-smoke-ok`)

## Validation Gaps

- `pytest` is not installed in the repository virtualenv, so the focused Layer 4 tests could not be executed through the normal test runner in this session.

## Suggested Session 2 Start

1. Run the Layer 4 test set under a virtualenv that has `pytest` installed.
2. Exercise `train_multiagent_ppo()` against the repo Ray runtime to validate that the new `infos` contract and multi-agent setup behave correctly under an actual PPO training iteration.

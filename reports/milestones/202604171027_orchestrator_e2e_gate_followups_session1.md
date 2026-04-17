# Orchestrator End-to-End Gate Follow-Up Split (Session 1, 2026-04-17 KST)

## Scope

- Split residual work from the final orchestrator gate into narrow follow-up tasks.
- Keep this branch limited to task specs, issue references, and minimal continuity updates.

## Source Validation State

The split is based on the final-gate result recorded in the prior task runtime log:

- `full-process` passed in repo `.venv` with the smoke config.
- In the current macOS sandbox, PPO returned a structured `status="skipped"` result because Ray could not start its local runtime.
- The documented repo `.venv` pytest path was still not usable because `pytest` was not installed in that environment.

Reference sources reviewed for this split:

- Current task issue: #48
  - https://github.com/capston-design-2026-1/Borg-Agent-Orchestrator/issues/48
- Existing RLlib/referee issue: #39
  - https://github.com/capston-design-2026-1/Borg-Agent-Orchestrator/issues/39
- Existing simulator/AIOpsLab issue: #32
  - https://github.com/capston-design-2026-1/Borg-Agent-Orchestrator/issues/32
- Prior final-gate session output:
  - `codex_autonomy/runtime/logs/orchestrator-e2e-final-gate/session_001.stdout.log`

## Follow-Up Routing

1. Queued a dedicated PPO validation task:
- `codex_autonomy/tasks/queue/orchestrator-e2e-ppo-trained-gate.yaml`
- Purpose: re-run `tune-policy-rewards` and `full-process` outside the restricted sandbox and confirm a trained PPO outcome instead of the current structured skip.
- Related issue link: #39

2. Queued a dedicated pytest repair task:
- `codex_autonomy/tasks/queue/orchestrator-e2e-pytest-runner-repair.yaml`
- Purpose: repair the repo `.venv` gate runner so `./.venv/bin/pytest orchestrator_stack/tests/` works as the normal validation path.

3. Left the live AIOpsLab contract validation on the existing simulator track instead of duplicating it:
- Existing issue link: #32
- Reason: that gap predates the final gate and already has an active dedicated task surface.

## Sandbox Note

The requested runtime-log follow-up YAML path for this session could not be written from this worktree:

- `/Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator/codex_autonomy/runtime/logs/orchestrator-e2e-gate-followups/session_001.followups.yaml`

Attempting to write that path returned macOS sandbox `operation not permitted`, so the same follow-up split is recorded here in git-tracked form and enqueued through queue YAML files instead.

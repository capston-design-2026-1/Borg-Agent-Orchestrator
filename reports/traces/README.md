# Episode Trace Artifacts

This directory stores step-by-step orchestrator episode logs written by `orchestrator.main.run_episode`.

## File Naming

- Format: `YYYYMMDDHHMM_episode_trace.log` (KST timestamp prefix)

## Log Record Shape

Each run emits:

1. Episode start line with total planned steps
2. Per-step records:
`Step NNN | Proposals: [...] | Referee: ... | Rewards: [...]`
3. Episode end line

These logs are execution traces for action/reward auditing, separate from Layer 1 trace datasets (`orchestrator_stack/examples/sample_trace.json`).

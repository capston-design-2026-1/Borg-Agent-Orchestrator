# Orchestrator PPO Curriculum Validation

- Generated (KST): 2026-04-28 15:35
- Config: `orchestrator_stack/config/orchestrator.example.json`
- Output directory: `orchestrator_stack/runtime/rllib_curriculum_validation`

## PPO Curriculum Result

Two PPO curriculum stages completed locally after Ray compatibility fixes:

| Stage | Train iters | Batch | Minibatch | Epochs | Fragment | LR | Reward mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 32 | 16 | 1 | 8 | 0.0003 | 0.0 |
| 2 | 3 | 64 | 32 | 2 | 16 | 0.0002 | 0.0 |

## Heuristic Baseline

A direct heuristic-policy evaluation on `sample_trace.json` without predictor enrichment completed:

- Steps: `120`
- Total score: `648.0`
- Average score: `5.4`

## Interpretation

The PPO curriculum path is now executable in the local repo virtualenv, but this smoke curriculum does not beat the heuristic baseline. The current result should be treated as a runtime validation, not a trained-policy quality milestone.

## Remaining Blockers

- Live AIOpsLab validation is blocked in this virtualenv because AIOpsLab requires Python `>=3.11,<3.13`, while the repo virtualenv is Python `3.13.12`.
- No live Prometheus/AIOpsLab telemetry is connected yet, so reward replacement with real SLA/energy/task-completion metrics remains open.

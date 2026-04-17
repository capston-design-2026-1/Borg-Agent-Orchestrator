# Orchestrator Fixups And Errors Session 1 (2026-04-17 KST)

## Scope

- `orchestrator_stack/orchestrator/cli.py`
- `codex_autonomy/codex_autonomy/cli.py`
- `codex_autonomy/codex_autonomy/config.py`
- `codex_autonomy/codex_autonomy/task_store.py`

## Fixes

- Deferred heavy orchestrator imports so `python3 orchestrator_stack/run.py --help` and Layer 1 `build-trace` work even when ML dependencies are unavailable.
- Replaced raw orchestrator `ModuleNotFoundError` tracebacks with direct dependency guidance for dataset-backed and runtime-backed commands.
- Deferred autonomy YAML/task-store imports so `python3 codex_autonomy/scripts/run_daemon.py --help` and `python3 codex_autonomy/scripts/run_guardian.py --help` remain usable in degraded environments.
- Replaced raw autonomy `yaml` import tracebacks with explicit `PyYAML` dependency messages during YAML-backed command execution.

## Validation

- `python3 -m compileall orchestrator_stack/orchestrator/cli.py codex_autonomy/codex_autonomy/cli.py codex_autonomy/codex_autonomy/config.py codex_autonomy/codex_autonomy/task_store.py`
- `python3 orchestrator_stack/run.py --help`
- `python3 orchestrator_stack/run.py build-trace --metrics orchestrator_stack/examples/sample_metrics.json --out /tmp/orchestrator_trace_validation_2.json`
- `python3 orchestrator_stack/run.py train-risk --dataset /tmp/missing.npz --out /tmp/model.json`
  - expected degraded-environment result: explicit missing `numpy` message
- `python3 codex_autonomy/scripts/run_daemon.py --help`
- `python3 codex_autonomy/scripts/run_guardian.py --help`
- `python3 codex_autonomy/scripts/run_daemon.py status --config codex_autonomy/config/autonomy.example.yaml --limit 5`
  - expected degraded-environment result: explicit missing `PyYAML` message

## Residual Risks

1. The repo-root `.venv` in this worktree is still a broken/self-referential symlink, so dependency-complete validation remains blocked here.
2. `pytest`, `numpy`, and other orchestrator/autonomy runtime dependencies are still unavailable under system `python3`, so this slice only validated parser/help, compile, and degraded-environment behavior.

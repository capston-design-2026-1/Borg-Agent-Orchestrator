# Codex Autonomy Runner Bootstrap (2026-04-14 KST)

## Objective

Provide a local agentic environment that can run Codex sessions continuously, roll over sessions automatically, keep durable continuity state in git-tracked files, and run independent tasks in parallel.

## Delivered

- New isolated subsystem: `codex_autonomy/`
- Daemon manager loop with parallel scheduling:
  - `codex_autonomy/codex_autonomy/manager.py`
- Worker execution with per-task git branch/worktree isolation:
  - `codex_autonomy/codex_autonomy/worker.py`
  - `codex_autonomy/codex_autonomy/worktree.py`
- Session adapter for configurable Codex command templates:
  - `codex_autonomy/codex_autonomy/session_adapter.py`
- YAML task queue + archive handling:
  - `codex_autonomy/codex_autonomy/task_store.py`
- SQLite state/event logging:
  - `codex_autonomy/codex_autonomy/state_db.py`
- Health loop auto-task generation (lint/test/upgrade scanners):
  - `codex_autonomy/codex_autonomy/health.py`
- CLI commands:
  - `run`, `enqueue`, `status`
  - `codex_autonomy/codex_autonomy/cli.py`
- Runtime docs/config/templates:
  - `codex_autonomy/README.md`
  - `codex_autonomy/AGENTS.md`
  - `codex_autonomy/NEXT_STEPS.md`
  - `codex_autonomy/config/autonomy.example.yaml`
  - `codex_autonomy/tasks/templates/example_bootstrap.yaml`

## Smoke Validation

Validated with temporary config using a safe shell command template:

- Enqueued task `smoke-runner`
- Daemon started and processed task
- Session logs written under `codex_autonomy/runtime/logs/smoke-runner/`
- State persisted in `codex_autonomy/runtime/state.db`
- `status` command returned task/session rows

## Notes

- `command_template` must be set to your local Codex CLI invocation.
- `repo_root` in config is resolved relative to current working directory by default.
- Task templates are separated from live queue to avoid repeated accidental execution.

# Codex Autonomy Runner

Local supervisor to run Codex sessions continuously with task queueing, session rollover, parallel worktrees, and health-triggered self-healing tasks.

## What It Provides

- Endless manager loop (`run` command)
- Task queue in `codex_autonomy/tasks/queue/*.yaml`
- Task templates in `codex_autonomy/tasks/templates/*.yaml`
- Parallel independent execution with `git worktree` branches (`auto/<task-id>`)
- Session rollover per task when one session budget is exhausted
- Persistent event/session logs in SQLite (`codex_autonomy/runtime/state.db`)
- Auto-generated healing/upgrade tasks from lint/test/upgrade scanners
- Automatic archive of completed/failed task specs
- GitHub issue/PR automation with optional auto-merge (`gh` CLI)

## Architecture

1. `manager.py` polls queue and schedules runnable tasks
2. `worker.py` creates branch/worktree, runs Codex session(s), validates completion, commits/pushes
3. `health.py` periodically runs lint/test/upgrade checks and enqueues repair tasks
4. `state_db.py` tracks task events and session history
5. `task_store.py` persists YAML queue items

## Setup

1. Copy config:

```bash
cp codex_autonomy/config/autonomy.example.yaml codex_autonomy/config/autonomy.local.yaml
```

2. Edit `command_template` for your Codex CLI form.
   Optional: set `session.rate_limit_cooldown_seconds` to control automatic wait time after Codex quota/rate-limit failures.
3. Configure GitHub flow in `github:` block (`repo`, auto issue/PR/merge policy).
4. If using GitHub automation, install/authenticate GitHub CLI:

```bash
gh auth status
```

3. Install dependencies:

```bash
./.venv/bin/python -m pip install pyyaml
```

## Run

```bash
./.venv/bin/python codex_autonomy/scripts/run_daemon.py run --config codex_autonomy/config/autonomy.local.yaml
```

Enqueue task manually:

```bash
./.venv/bin/python codex_autonomy/scripts/run_daemon.py enqueue \
  --config codex_autonomy/config/autonomy.local.yaml \
  --task-id improve-ci \
  --title "Improve CI reliability" \
  --prompt "Strengthen CI checks and fix failures." \
  --priority 10
```

Inspect runtime status:

```bash
./.venv/bin/python codex_autonomy/scripts/run_daemon.py status \
  --config codex_autonomy/config/autonomy.local.yaml \
  --limit 30
```

## Session Rollover Rules

- Each task has `max_sessions`
- If not done after one session, task is re-queued (`pending`) and resumed in next session
- If retries exceed `max_retries`, task is marked failed and archived
- If Codex returns quota/rate-limit errors, task is auto re-queued with a cooldown (`metadata.not_before_epoch`) and resumes automatically after wait time

## GitHub Flow

- Task starts: issue can be auto-created and linked (`issue_number`, `issue_url`)
- Completion on branch: PR can be auto-created and linked (`pr_number`, `pr_url`)
- If `auto_merge=false`: task status becomes `review`
- If `auto_merge=true`: manager attempts merge and marks task completed when successful
- Branch naming: `auto/<task-id>`

## Parallel Rules

- `max_parallel_workers` controls concurrent sessions
- Each task uses its own worktree path: `codex_autonomy/runtime/worktrees/<task-id>`
- Independent tasks can run simultaneously without branch conflicts

## Notes

- Keep repository `Agents.md`/`NEXT_STEPS.md` current; prompts force every session to read/update them.
- For strict review separation, enqueue explicit review tasks with dependency on implementation tasks.

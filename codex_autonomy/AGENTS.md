# Codex Autonomy Rules

## Execution Mode

- Manager must keep running until externally stopped.
- Guardian should be the default long-running entrypoint; it must restart manager automatically if manager exits.
- Do not block on a single task if other ready tasks exist.
- Prefer parallel execution for independent tasks.

## Task Discipline

- One task file per unit of work.
- One `task_id` must map to exactly one queue YAML file (canonical filename `<task_id>.yaml`).
- Use dependencies to serialize tasks when needed.
- Keep task prompts concrete and outcome-based.
- Prefer bundle-driven decomposition for large initiatives so each minor feature/bugfix is its own task/branch/PR.
- Avoid single mega-task prompts for multi-layer architecture work when a dependency chain can split the work.
- During task execution, Codex should emit follow-up tasks for newly discovered feature slices/bugs so issue+PR splitting continues dynamically.

## Session Continuity

- Every session prompt includes repository continuity instructions.
- If context/session budget is exhausted, re-queue task and continue automatically.
- If Codex quota/rate limits are detected, set cooldown and resume automatically after cooldown.
- Persist progress in queue YAML and SQLite logs.

## Git Discipline

- Branch per task: `auto/<task-id>`
- Worktree per task under `runtime/worktrees`
- Commit and push after meaningful changes.
- Archive task files after completion/failure.
- For autonomy-runner code changes, keep near per-file commits where practical.

## GitHub Collaboration Flow

- Use GitHub Issues as the canonical intake for bugs/features/upgrades.
- Use Pull Requests for all implementation branches.
- Keep tasks in `review` until PR merge when auto-merge is disabled.
- Use merge commits, not squash merges, so fine-grained commit history from feature branches is preserved after merge.

## Operator UX Rule

- Do not paste terminal commands directly in assistant chat replies.
- Store runnable commands in tracked Markdown runbooks under `codex_autonomy/` (copy-safe formatting).
- In chat replies, point to the runbook path and provide only the numbered step sequence to execute.
- Use `codex_autonomy/TRACKING_STEPS.md` as the canonical live-monitoring and recovery runbook.

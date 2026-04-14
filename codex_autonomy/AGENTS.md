# Codex Autonomy Rules

## Execution Mode

- Manager must keep running until externally stopped.
- Do not block on a single task if other ready tasks exist.
- Prefer parallel execution for independent tasks.

## Task Discipline

- One task file per unit of work.
- Use dependencies to serialize tasks when needed.
- Keep task prompts concrete and outcome-based.

## Session Continuity

- Every session prompt includes repository continuity instructions.
- If context/session budget is exhausted, re-queue task and continue automatically.
- Persist progress in queue YAML and SQLite logs.

## Git Discipline

- Branch per task: `auto/<task-id>`
- Worktree per task under `runtime/worktrees`
- Commit and push after meaningful changes.
- Archive task files after completion/failure.

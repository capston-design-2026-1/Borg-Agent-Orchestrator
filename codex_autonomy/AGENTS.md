# Codex Autonomy Rules

## Execution Mode

- Manager must keep running until externally stopped.
- Guardian should be the default long-running entrypoint; it must restart manager automatically if manager exits.
- Do not block on a single task if other ready tasks exist.
- Prefer parallel execution for independent tasks.

## Task Discipline

- One task file per unit of work.
- One `task_id` must map to exactly one queue YAML file (canonical filename `<task_id>.yaml`).
- Cooldown-waiting tasks should move out of `tasks/queue` into `tasks/deferred` so only runnable/review-active work remains in the hot queue.
- Default to no task dependencies; add dependencies only when one task is truly blocked on another task's merged outcome.
- Do not use catch-all endgame tasks that mix runtime fixes, docs, reports, and follow-up issue creation in one PR; split finalization work into narrow validation/docs/follow-up slices.
- Default intake model: enqueue one broad objective and let Codex emit follow-up task specs for newly discovered feature slices, bugs, docs sync, and cleanup work during execution.
- Do not require the operator to pre-shard work into YAML bundles unless they explicitly want fixed manual work items from the start.
- Keep task prompts concrete and outcome-based.
- Prefer bundle-driven decomposition for large initiatives so each minor feature/bugfix is its own task/branch/PR.
- Avoid single mega-task prompts for multi-layer architecture work when a dependency chain can split the work.
- During task execution, Codex should emit follow-up tasks for newly discovered feature slices/bugs so issue+PR splitting continues dynamically.

## Session Continuity

- Every session prompt includes repository continuity instructions.
- If context/session budget is exhausted, re-queue task and continue automatically.
- If Codex quota/rate limits are detected, set cooldown and resume automatically after cooldown.
- Persist progress in queue YAML and SQLite logs.
- Never reset an existing task branch to `origin/main` during rollover; resume from the existing local branch, or recreate it from `origin/auto/<task-id>` if only the remote branch remains.
- Include a compact continuation handoff in each new session prompt from the latest task journal plus prior stdout/stderr tails so rollover continues the active slice instead of rediscovering prior work.
- Keep repo-root `.venv` as a local virtualenv directory only; do not commit or preserve a symlinked `.venv` artifact in git state.
- `.gitignore` must ignore both `.venv` and `.venv/` because a symlinked `.venv` is a file entry, not a directory entry.
- Worktree setup must automatically remove tracked `.venv` from task branches before creating the local worktree symlink so old branches cannot reintroduce the self-referential loop.

## Git Discipline

- Branch per task: `auto/<task-id>`
- Worktree per task under `runtime/worktrees`
- Commit and push after meaningful changes.
- During active execution, supervisor publishes tracked progress notes to `codex_autonomy/task_journal/<task-id>.md` from session heartbeats so the remote branch shows live operation history even when no code changed.
- During active execution, commit code/doc changes immediately at file granularity when practical; do not batch unrelated files until session end.
- Feature/bug/upgrade tasks must not be treated as complete if the branch delta versus base is journal/docs-only; those tasks need substantive non-doc changes before PR merge.
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
- When repairing launchd/guardian startup, prefer rebuilding `.venv` locally and reinstalling `codex_autonomy/requirements.txt` before restarting services.

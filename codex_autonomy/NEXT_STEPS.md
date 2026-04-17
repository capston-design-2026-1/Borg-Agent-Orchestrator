# Codex Autonomy Next Steps

## Latest Session Note (2026-04-17 KST, targeted fixups slice)

- Hardened autonomy CLI imports so parser/help flows no longer require `PyYAML` at module import time.
- Verified `python3 codex_autonomy/scripts/run_daemon.py --help` and `python3 codex_autonomy/scripts/run_guardian.py --help` now succeed even when the repo `.venv` is broken and system `python3` lacks repo dependencies.
- YAML-backed commands now exit with explicit dependency messages instead of tracebacks, for example `missing dependency 'PyYAML' ... install codex_autonomy requirements`.
- Remaining operator gap: the worker path still assumes a valid repo-root `.venv`; add an explicit health/status signal for broken `.venv` state in a follow-up slice.

1. Configure your local Codex CLI invocation in `autonomy.local.yaml` (`session.command_template`).
2. Use bundle enqueue (`enqueue-bundle` + `orchestrator_finish_bundle.yaml`) as the default for orchestrator completion so each small slice lands as its own PR.
3. Monitor auto-generated follow-up tasks (`followup_enqueued` events) and tune task prompts so generated scopes stay small and reviewable.
4. Tune `recovery.stuck_task_seconds` for your environment (use explicit value if default timeout+120 is too strict/loose).
5. Configure GitHub flow block (`github.enabled=true`, `github.repo=<owner/repo>`, reviewer/assignee lists).
6. Enable real health checks (`lint_command`, `test_command`, `upgrade_scan_command`).
7. Add webhook/cron triggers to auto-enqueue upgrade tasks daily.
8. Add a richer dashboard view (grouped task states + PR/issue links) from `state.db`, including `task_watchdog`, `task_recovered`, and `followup_enqueued` events.
9. Expose `session_progress` heartbeat rows in dashboard so active work is visible before session completion.
10. Keep launchd guardian installed in local environments so manager is auto-restarted and runtime remains continuously active.
11. Keep `.venv` local and rebuild it immediately if it ever becomes a broken symlink; guardian launchd now selects a usable Python automatically, but worker commands still assume a valid repo-root virtualenv.
12. Extend `status` output to show active-queue vs deferred-cooldown counts so operators can distinguish blocked cooldown work from runnable work at a glance.

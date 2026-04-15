# Codex Autonomy Next Steps

1. Configure your local Codex CLI invocation in `autonomy.local.yaml` (`session.command_template`).
2. Use bundle enqueue (`enqueue-bundle` + `orchestrator_finish_bundle.yaml`) as the default for orchestrator completion so each small slice lands as its own PR.
3. Monitor auto-generated follow-up tasks (`followup_enqueued` events) and tune task prompts so generated scopes stay small and reviewable.
4. Tune `recovery.stuck_task_seconds` for your environment (use explicit value if default timeout+120 is too strict/loose).
5. Configure GitHub flow block (`github.enabled=true`, `github.repo=<owner/repo>`, reviewer/assignee lists).
6. Enable real health checks (`lint_command`, `test_command`, `upgrade_scan_command`).
7. Add webhook/cron triggers to auto-enqueue upgrade tasks daily.
8. Add a richer dashboard view (grouped task states + PR/issue links) from `state.db`, including `task_watchdog`, `task_recovered`, and `followup_enqueued` events.
9. Expose `session_progress` heartbeat rows in dashboard so active work is visible before session completion.

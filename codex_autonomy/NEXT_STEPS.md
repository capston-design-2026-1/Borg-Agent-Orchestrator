# Codex Autonomy Next Steps

1. Configure your local Codex CLI invocation in `autonomy.local.yaml` (`session.command_template`).
2. Use bundle enqueue (`enqueue-bundle` + `orchestrator_finish_bundle.yaml`) as the default for orchestrator completion so each small slice lands as its own PR.
3. Tune `recovery.stuck_task_seconds` for your environment (use explicit value if default timeout+120 is too strict/loose).
4. Configure GitHub flow block (`github.enabled=true`, `github.repo=<owner/repo>`, reviewer/assignee lists).
5. Enable real health checks (`lint_command`, `test_command`, `upgrade_scan_command`).
6. Add webhook/cron triggers to auto-enqueue upgrade tasks daily.
7. Add a richer dashboard view (grouped task states + PR/issue links) from `state.db`, including `task_watchdog` and `task_recovered` events.

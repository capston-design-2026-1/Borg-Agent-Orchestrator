# Codex Autonomy Next Steps

1. Configure your local Codex CLI invocation in `autonomy.local.yaml` (`session.command_template`).
2. Configure GitHub flow block (`github.enabled=true`, `github.repo=<owner/repo>`, reviewer/assignee lists).
3. Enable real health checks (`lint_command`, `test_command`, `upgrade_scan_command`).
4. Add webhook/cron triggers to auto-enqueue upgrade tasks daily.
5. Add a richer dashboard view (grouped task states + PR/issue links) from `state.db`.

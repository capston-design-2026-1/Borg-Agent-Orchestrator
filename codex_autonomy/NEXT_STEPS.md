# Codex Autonomy Next Steps

1. Configure your local Codex CLI invocation in `autonomy.local.yaml` (`session.command_template`).
2. Enable real health checks (`lint_command`, `test_command`, `upgrade_scan_command`).
3. Add a dedicated review-agent task template and enforce branch review before merge.
4. Add webhook/cron triggers to auto-enqueue upgrade tasks daily.
5. Add dashboard command to inspect task/session status from `state.db`.

# Codex Autonomy Runbook (Step-Number Execution)

This file is the canonical command source for Codex autonomy operations.

- Full copy-safe command blocks live in `codex_autonomy/SETUP_COPY_SAFE.md`.
- Assistant replies should reference this file and provide only step numbers.

## Main Flow (Resume/Run Full Orchestrator Finish)

Execute these numbered sections from `SETUP_COPY_SAFE.md` in this exact order:

1. `0) Pull latest repository changes`
2. `1) Install dependencies`
3. `2) Create local config safely (recommended: copy example)`
4. `3) Set Codex command template (required)`
5. `4) Enable GitHub flow and set repository`
6. `7) Verify GitHub CLI auth`
7. `15) Cleanup duplicate task files with same task_id`
8. `27) Start decomposed orchestrator bundle (recommended for many small PRs)`
9. `29) Install always-on macOS launchd guardian service`
10. `30) Verify guardian and manager runtime state`
11. Legacy single-task option only: `17)` then `18)`
12. `12) Track processes continuously (copy-safe)`
13. `14) Track GitHub issue/PR flow`
14. Optional monitor: `13.1) Live append-only event stream (new events at bottom)`
15. Optional monitor: `13.2) Live append-only session stream (new rc lines at bottom)`
16. Optional monitor: `13.3) Live append-only in-session progress stream (heartbeat + excerpt)`

## Recovery Flows

If you hit `rc=2` loop, execute:

1. `20) Recover from rc=2 loop (--prompt-file error)`

If you hit `rc=1` loop, execute:

1. `23) Recover from rc=1 loop (missing modules/worktree runtime mismatch)`

If task stays `running` but streams/logs are silent for several minutes, execute:

1. `26) Recover from stuck running state (no new events/sessions for several minutes)`

## Rule for Future Replies

When asked what to run:

1. Point user to this file.
2. Return only the section numbers/names above.
3. Do not paste command blocks in chat.

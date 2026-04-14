# Copy-Safe Local Setup (No Heredoc Indent Issues)

Use these commands by copying directly from this file.

## 0) Pull latest repository changes

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
git pull origin main
```

## 1) Install dependencies

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python -m pip install -r orchestrator_stack/requirements.txt -r codex_autonomy/requirements.txt
```

## 2) Create local config safely (recommended: copy example)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
cp codex_autonomy/config/autonomy.example.yaml codex_autonomy/config/autonomy.local.yaml
```

## 3) Set Codex command template (required)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
sed -i '' 's|^  command_template:.*$|  command_template: "codex exec - < {prompt_file}"|' codex_autonomy/config/autonomy.local.yaml
```

## 4) Enable GitHub flow and set repository

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
sed -i '' 's/^  enabled: false$/  enabled: true/' codex_autonomy/config/autonomy.local.yaml
sed -i '' 's|^  repo: "owner/repo"$|  repo: "capston-design-2026-1/Borg-Agent-Orchestrator"|' codex_autonomy/config/autonomy.local.yaml
```

## 5) Set cooldown for Codex limit windows (optional)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
grep -q "rate_limit_cooldown_seconds" codex_autonomy/config/autonomy.local.yaml || sed -i '' '/^  max_session_minutes:/a\
  rate_limit_cooldown_seconds: 1800' codex_autonomy/config/autonomy.local.yaml
```

## 6) Verify config

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
cat codex_autonomy/config/autonomy.local.yaml
```

## 7) Verify GitHub CLI auth

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
gh auth status
```

If not logged in:

```bash
gh auth login --web
```

## 8) Start autonomy manager

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/run_daemon.py run --config codex_autonomy/config/autonomy.local.yaml
```

## 9) One-line command: enqueue full finish task + check status

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator && cp -f codex_autonomy/tasks/templates/full_orchestrator_finish.yaml codex_autonomy/tasks/queue/full-orchestrator-e2e-finish.yaml && ./.venv/bin/python codex_autonomy/scripts/run_daemon.py status --config codex_autonomy/config/autonomy.local.yaml
```

## 10) One-line command: enqueue full finish task + start manager

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator && cp -f codex_autonomy/tasks/templates/full_orchestrator_finish.yaml codex_autonomy/tasks/queue/full-orchestrator-e2e-finish.yaml && ./.venv/bin/python codex_autonomy/scripts/run_daemon.py run --config codex_autonomy/config/autonomy.local.yaml
```

## 11) In another terminal, check status

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/run_daemon.py status --config codex_autonomy/config/autonomy.local.yaml
```

## 12) Track processes continuously (copy-safe)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
while true; do
  clear
  date
  ./.venv/bin/python codex_autonomy/scripts/run_daemon.py status --config codex_autonomy/config/autonomy.local.yaml
  sleep 5
done
```

## 13) Track recent runtime events from SQLite

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
sqlite3 codex_autonomy/runtime/state.db "SELECT task_id,event_type,message,ts FROM task_events ORDER BY id DESC LIMIT 30;"
sqlite3 codex_autonomy/runtime/state.db "SELECT task_id,branch_name,return_code,duration_seconds,ts FROM sessions ORDER BY id DESC LIMIT 30;"
```

## 13.1) Live append-only event stream (new events at bottom)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/stream_events.py --db codex_autonomy/runtime/state.db
```

## 13.2) Live append-only session stream (new rc lines at bottom)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/stream_sessions.py --db codex_autonomy/runtime/state.db --task-id full-orchestrator-e2e-finish
```

## 14) Track GitHub issue/PR flow

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
gh issue list -R capston-design-2026-1/Borg-Agent-Orchestrator --limit 20
gh pr list -R capston-design-2026-1/Borg-Agent-Orchestrator --limit 20
```

## 15) Cleanup duplicate task files with same task_id

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
rm -f codex_autonomy/tasks/queue/full_orchestrator_finish.yaml
```

## 16) Optional: enqueue a task

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/run_daemon.py enqueue \
  --config codex_autonomy/config/autonomy.local.yaml \
  --task-id feature-health-dashboard \
  --title "Build health dashboard" \
  --prompt "Add dashboard summarizing lint/test/upgrade outcomes and task queue status" \
  --task-type feature
```

## 17) Start full orchestrator-finish task (recommended)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
cp -f codex_autonomy/tasks/templates/full_orchestrator_finish.yaml codex_autonomy/tasks/queue/full-orchestrator-e2e-finish.yaml
```

## 18) Cleanup duplicate GitHub issues for this task (keep #19)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
for n in $(gh issue list -R capston-design-2026-1/Borg-Agent-Orchestrator --state open --limit 200 --search '"task_id: `full-orchestrator-e2e-finish`" in:body' --json number --jq '.[].number'); do [ "$n" = "19" ] || gh issue close "$n" -R capston-design-2026-1/Borg-Agent-Orchestrator --comment "Closing as duplicate of #19 (same task_id: full-orchestrator-e2e-finish)."; done
```

## 19) Verify only canonical issue remains open

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
gh issue list -R capston-design-2026-1/Borg-Agent-Orchestrator --state open --limit 200 --search '"task_id: `full-orchestrator-e2e-finish`" in:body'
```

## 20) Recover from rc=2 loop (`--prompt-file` error)

1) Stop old manager process:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
pkill -f "codex_autonomy/scripts/run_daemon.py run" || true
```

2) Fix local command template:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
sed -i '' 's|^  command_template:.*$|  command_template: "codex exec - < {prompt_file}"|' codex_autonomy/config/autonomy.local.yaml
```

3) Re-enqueue canonical task file:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
rm -f codex_autonomy/tasks/queue/full_orchestrator_finish.yaml
cp -f codex_autonomy/tasks/templates/full_orchestrator_finish.yaml codex_autonomy/tasks/queue/full-orchestrator-e2e-finish.yaml
```

4) Start manager again:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/run_daemon.py run --config codex_autonomy/config/autonomy.local.yaml
```

5) Verify active progress in another terminal:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/run_daemon.py status --config codex_autonomy/config/autonomy.local.yaml
```

## 21) If you still must use heredoc

- The closing marker (`PY`, `EOF`, `YAML`) must be at column 1 (no spaces).
- Do not indent lines inside `python - <<'PY' ... PY`.

## 22) Ordered execution list

Run these sections in order:

1. `0) Pull latest repository changes`
2. `1) Install dependencies`
3. `2) Create local config safely (recommended: copy example)`
4. `3) Set Codex command template (required)`
5. `4) Enable GitHub flow and set repository`
6. `5) Set cooldown for Codex limit windows (optional)`
7. `7) Verify GitHub CLI auth`
8. `15) Cleanup duplicate task files with same task_id`
9. `17) Start full orchestrator-finish task (recommended)`
10. `18) Cleanup duplicate GitHub issues for this task (keep #19)`
11. `8) Start autonomy manager`
12. `12) Track processes continuously (copy-safe)`
13. `14) Track GitHub issue/PR flow`
14. If you want new events appended at bottom, run `13.1) Live append-only event stream (new events at bottom)`
15. If you want new session rc lines appended at bottom, run `13.2) Live append-only session stream (new rc lines at bottom)`
16. If you see rapid `rc=2`, run `20) Recover from rc=2 loop (--prompt-file error)`

## 23) Recover from rc=1 loop (missing modules/worktree runtime mismatch)

1) Stop manager process:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
pkill -f "codex_autonomy/scripts/run_daemon.py run" || true
```

2) Pull latest fixes:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
git pull origin main
```

3) Remove stale task worktree:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
git worktree remove --force codex_autonomy/runtime/worktrees/full-orchestrator-e2e-finish 2>/dev/null || true
```

4) Re-enqueue canonical task:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
cp -f codex_autonomy/tasks/templates/full_orchestrator_finish.yaml codex_autonomy/tasks/queue/full-orchestrator-e2e-finish.yaml
```

5) Start manager:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/run_daemon.py run --config codex_autonomy/config/autonomy.local.yaml
```

## 24) Verify manager process is alive

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
pgrep -af "codex_autonomy/scripts/run_daemon.py run"
```

## 25) Tail active task session logs live

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
LATEST_STDERR=$(ls -1t codex_autonomy/runtime/logs/full-orchestrator-e2e-finish/*.stderr.log | head -n 1)
LATEST_STDOUT=$(ls -1t codex_autonomy/runtime/logs/full-orchestrator-e2e-finish/*.stdout.log | head -n 1)
echo "stderr: $LATEST_STDERR"
echo "stdout: $LATEST_STDOUT"
tail -f "$LATEST_STDERR" "$LATEST_STDOUT"
```

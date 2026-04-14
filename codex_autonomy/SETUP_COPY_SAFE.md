# Copy-Safe Local Setup (No Heredoc Indent Issues)

Use these commands by copying directly from this file.

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

## 2.1) Set Codex command template (required)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
sed -i '' 's|^  command_template:.*$|  command_template: "codex exec - < {prompt_file}"|' codex_autonomy/config/autonomy.local.yaml
```

## 3) Enable GitHub flow and set repository

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
sed -i '' 's/^  enabled: false$/  enabled: true/' codex_autonomy/config/autonomy.local.yaml
sed -i '' 's|^  repo: "owner/repo"$|  repo: "capston-design-2026-1/Borg-Agent-Orchestrator"|' codex_autonomy/config/autonomy.local.yaml
```

## 3.1) Set cooldown for Codex limit windows (optional)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
grep -q "rate_limit_cooldown_seconds" codex_autonomy/config/autonomy.local.yaml || sed -i '' '/^  max_session_minutes:/a\
  rate_limit_cooldown_seconds: 1800' codex_autonomy/config/autonomy.local.yaml
```

## 4) Verify config

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
cat codex_autonomy/config/autonomy.local.yaml
```

## 5) Verify GitHub CLI auth

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
gh auth status
```

If not logged in:

```bash
gh auth login --web
```

## 6) Start autonomy manager

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/run_daemon.py run --config codex_autonomy/config/autonomy.local.yaml
```

## One-line command: enqueue full finish task + check status

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator && cp -f codex_autonomy/tasks/templates/full_orchestrator_finish.yaml codex_autonomy/tasks/queue/full_orchestrator_finish.yaml && ./.venv/bin/python codex_autonomy/scripts/run_daemon.py status --config codex_autonomy/config/autonomy.local.yaml
```

## One-line command: enqueue full finish task + start manager

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator && cp -f codex_autonomy/tasks/templates/full_orchestrator_finish.yaml codex_autonomy/tasks/queue/full_orchestrator_finish.yaml && ./.venv/bin/python codex_autonomy/scripts/run_daemon.py run --config codex_autonomy/config/autonomy.local.yaml
```

## 7) In another terminal, check status

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/run_daemon.py status --config codex_autonomy/config/autonomy.local.yaml
```

## Track processes continuously (copy-safe)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
while true; do
  clear
  date
  ./.venv/bin/python codex_autonomy/scripts/run_daemon.py status --config codex_autonomy/config/autonomy.local.yaml
  sleep 5
done
```

## Track recent runtime events from SQLite

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
sqlite3 codex_autonomy/runtime/state.db "SELECT task_id,event,status,datetime(ts,'unixepoch','localtime') FROM task_events ORDER BY id DESC LIMIT 30;"
sqlite3 codex_autonomy/runtime/state.db "SELECT task_id,session_index,return_code,duration_sec,datetime(ts,'unixepoch','localtime') FROM sessions ORDER BY id DESC LIMIT 30;"
```

## Track GitHub issue/PR flow

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
gh issue list -R capston-design-2026-1/Borg-Agent-Orchestrator --limit 20
gh pr list -R capston-design-2026-1/Borg-Agent-Orchestrator --limit 20
```

## Optional: enqueue a task

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/run_daemon.py enqueue \
  --config codex_autonomy/config/autonomy.local.yaml \
  --task-id feature-health-dashboard \
  --title "Build health dashboard" \
  --prompt "Add dashboard summarizing lint/test/upgrade outcomes and task queue status" \
  --task-type feature
```

## Start full orchestrator-finish task (recommended)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
cp codex_autonomy/tasks/templates/full_orchestrator_finish.yaml codex_autonomy/tasks/queue/full_orchestrator_finish.yaml
```

## If you still must use heredoc

- The closing marker (`PY`, `EOF`, `YAML`) must be at column 1 (no spaces).
- Do not indent lines inside `python - <<'PY' ... PY`.

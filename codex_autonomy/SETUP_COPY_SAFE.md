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

## 3) Enable GitHub flow and set repository

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
sed -i '' 's/^  enabled: false$/  enabled: true/' codex_autonomy/config/autonomy.local.yaml
sed -i '' 's|^  repo: "owner/repo"$|  repo: "capston-design-2026-1/Borg-Agent-Orchestrator"|' codex_autonomy/config/autonomy.local.yaml
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
./.venv/bin/python -m codex_autonomy.cli run --config codex_autonomy/config/autonomy.local.yaml
```

## 7) In another terminal, check status

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python -m codex_autonomy.cli status --config codex_autonomy/config/autonomy.local.yaml
```

## Optional: enqueue a task

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python -m codex_autonomy.cli enqueue \
  --config codex_autonomy/config/autonomy.local.yaml \
  --task-id feature-health-dashboard \
  --title "Build health dashboard" \
  --goal "Add dashboard summarizing lint/test/upgrade outcomes and task queue status" \
  --task-type feature
```

## If you still must use heredoc

- The closing marker (`PY`, `EOF`, `YAML`) must be at column 1 (no spaces).
- Do not indent lines inside `python - <<'PY' ... PY`.

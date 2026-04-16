# Autonomy Tracking Steps (Copy-Safe)

Canonical command pack for checking whether autonomy is alive, what it is doing, and whether it needs recovery.

## 1) Live runtime status (guardian + manager + queue)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/run_daemon.py status --config codex_autonomy/config/autonomy.local.yaml --limit 30
```

## 2) Verify core processes are alive

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
pgrep -af "codex_autonomy/scripts/run_guardian.py|codex_autonomy/scripts/run_daemon.py run|codex exec"
```

## 3) Stream task events (queue + recovery + completion)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/stream_events.py --db codex_autonomy/runtime/state.db
```

## 4) Stream in-session progress (heartbeat + excerpt)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/stream_progress.py --db codex_autonomy/runtime/state.db
```

## 5) Stream session results (return codes + duration)

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
./.venv/bin/python codex_autonomy/scripts/stream_sessions.py --db codex_autonomy/runtime/state.db
```

## 6) Tail active task logs directly

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
LATEST_STDERR=$(ls -1t codex_autonomy/runtime/logs/*/*.stderr.log | head -n 1)
LATEST_STDOUT=$(ls -1t codex_autonomy/runtime/logs/*/*.stdout.log | head -n 1)
echo "stderr: $LATEST_STDERR"
echo "stdout: $LATEST_STDOUT"
tail -f "$LATEST_STDERR" "$LATEST_STDOUT"
```

## 7) Interpret heartbeat lines correctly

- `session_heartbeat` with increasing `elapsed` means the task is active.
- `out=0` is acceptable; many Codex runs primarily emit to stderr.
- Increasing `err` can still be healthy when the stream is progress text, git output, or patches.

## 7.1) Inspect remote-visible task journal progress

- Each autonomous task branch should update `codex_autonomy/task_journal/<task-id>.md` during execution.
- Session start/end markers and heartbeat trace entries are pushed by the supervisor from outside the Codex session.
- Journal entries include recent output excerpts plus a snapshot of `git status` so you can see work advancing without waiting for final commits.

## 8) Recovery if manager is down or task is stale

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator
test -L .venv && rm .venv
test -x ./.venv/bin/python || python3 -m venv .venv
./.venv/bin/python -m pip install -r codex_autonomy/requirements.txt
./.venv/bin/python codex_autonomy/scripts/install_guardian_launchd.py --config codex_autonomy/config/autonomy.local.yaml
./.venv/bin/python codex_autonomy/scripts/run_daemon.py status --config codex_autonomy/config/autonomy.local.yaml --limit 30
```

If `.venv` is a broken symlink, remove it first and recreate the virtualenv locally.

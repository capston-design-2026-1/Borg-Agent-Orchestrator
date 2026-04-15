from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from codex_autonomy.config import ManagerConfig
from codex_autonomy.state_db import init_db, log_event


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_pid(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _pid_command_contains(pid: int, needle: str, cwd: Path) -> bool:
    proc = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return False
    return needle in (proc.stdout or "")


def _manager_paths(config: ManagerConfig) -> tuple[Path, Path]:
    pid_path = (config.runtime_dir / "manager.pid").resolve()
    log_path = (config.runtime_dir / "manager.nohup.log").resolve()
    config.runtime_dir.mkdir(parents=True, exist_ok=True)
    return pid_path, log_path


def _manager_alive(config: ManagerConfig) -> bool:
    pid_path, _ = _manager_paths(config)
    pid = _read_pid(pid_path)
    if pid is None or not _pid_alive(pid):
        return False
    return _pid_command_contains(pid, "codex_autonomy/scripts/run_daemon.py run", config.repo_root)


def _start_manager(config: ManagerConfig, config_path: Path) -> int | None:
    pid_path, log_path = _manager_paths(config)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    base_path = env.get("PATH", "")
    required = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    merged = ":".join(dict.fromkeys([p for p in (base_path.split(":") + required) if p]))
    env["PATH"] = merged

    with log_path.open("a", encoding="utf-8") as out:
        proc = subprocess.Popen(
            [
                sys.executable,
                str((config.repo_root / "codex_autonomy/scripts/run_daemon.py").resolve()),
                "run",
                "--config",
                str(config_path.resolve()),
            ],
            cwd=str(config.repo_root),
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
            env=env,
        )
    pid_path.write_text(f"{proc.pid}\n", encoding="utf-8")
    return proc.pid


def run_guardian_forever(config: ManagerConfig, config_path: Path) -> None:
    if not config.guardian.enabled:
        return
    init_db(config.state_db_path)
    guardian_pid_path = (config.runtime_dir / "guardian.pid").resolve()
    guardian_pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")

    while True:
        if not _manager_alive(config):
            pid = _start_manager(config, config_path)
            log_event(
                config.state_db_path,
                ts=datetime.utcnow().isoformat(),
                task_id="__guardian__",
                event_type="manager_restarted",
                message=f"manager restarted with pid={pid}",
            )
            time.sleep(max(1, int(config.guardian.restart_backoff_seconds)))

        time.sleep(max(2, int(config.guardian.poll_interval_seconds)))

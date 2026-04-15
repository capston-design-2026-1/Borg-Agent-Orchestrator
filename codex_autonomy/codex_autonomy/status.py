from __future__ import annotations

import sqlite3
from pathlib import Path
import os
import subprocess

from codex_autonomy.task_store import load_tasks


def recent_events(db_path: Path, limit: int = 20) -> list[tuple]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT ts, task_id, event_type, message FROM task_events ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def recent_sessions(db_path: Path, limit: int = 20) -> list[tuple]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT ts, task_id, branch_name, return_code, duration_seconds FROM sessions ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def recent_progress(db_path: Path, limit: int = 20) -> list[tuple]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            """
            SELECT ts, task_id, session_index, elapsed_seconds, stdout_chars, stderr_chars, excerpt
            FROM session_progress
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return rows


def queue_snapshot(queue_dir: Path) -> list[tuple[str, str, int | None, int | None]]:
    tasks = load_tasks(queue_dir)
    tasks.sort(key=lambda t: (t.priority, t.created_at))
    return [(t.task_id, t.status.value, t.issue_number, t.pr_number) for t in tasks]


def process_state(pid_file: Path, command_substring: str = "") -> tuple[int | None, bool]:
    if not pid_file.exists():
        return None, False
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None, False
    try:
        os.kill(pid, 0)
    except OSError:
        return pid, False
    if not command_substring:
        return pid, True
    proc = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return pid, False
    return pid, command_substring in (proc.stdout or "")

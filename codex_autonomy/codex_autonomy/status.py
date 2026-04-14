from __future__ import annotations

import sqlite3
from pathlib import Path

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


def queue_snapshot(queue_dir: Path) -> list[tuple[str, str, int | None, int | None]]:
    tasks = load_tasks(queue_dir)
    tasks.sort(key=lambda t: (t.priority, t.created_at))
    return [(t.task_id, t.status.value, t.issue_number, t.pr_number) for t in tasks]

from __future__ import annotations

import sqlite3
from pathlib import Path


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

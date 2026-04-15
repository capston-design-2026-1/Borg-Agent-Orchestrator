from __future__ import annotations

import sqlite3
from pathlib import Path


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS task_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            task_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            message TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            task_id TEXT NOT NULL,
            branch_name TEXT NOT NULL,
            return_code INTEGER NOT NULL,
            duration_seconds REAL NOT NULL,
            stdout_path TEXT,
            stderr_path TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS session_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            task_id TEXT NOT NULL,
            session_index INTEGER NOT NULL,
            elapsed_seconds REAL NOT NULL,
            stdout_chars INTEGER NOT NULL,
            stderr_chars INTEGER NOT NULL,
            stdout_lines INTEGER NOT NULL,
            stderr_lines INTEGER NOT NULL,
            excerpt TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def log_event(db_path: Path, *, ts: str, task_id: str, event_type: str, message: str) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO task_events(ts, task_id, event_type, message) VALUES (?, ?, ?, ?)",
        (ts, task_id, event_type, message),
    )
    conn.commit()
    conn.close()


def log_session(
    db_path: Path,
    *,
    ts: str,
    task_id: str,
    branch_name: str,
    return_code: int,
    duration_seconds: float,
    stdout_path: str,
    stderr_path: str,
) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO sessions(ts, task_id, branch_name, return_code, duration_seconds, stdout_path, stderr_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (ts, task_id, branch_name, return_code, duration_seconds, stdout_path, stderr_path),
    )
    conn.commit()
    conn.close()


def log_session_progress(
    db_path: Path,
    *,
    ts: str,
    task_id: str,
    session_index: int,
    elapsed_seconds: float,
    stdout_chars: int,
    stderr_chars: int,
    stdout_lines: int,
    stderr_lines: int,
    excerpt: str,
) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO session_progress(
            ts, task_id, session_index, elapsed_seconds,
            stdout_chars, stderr_chars, stdout_lines, stderr_lines, excerpt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ts,
            task_id,
            session_index,
            elapsed_seconds,
            stdout_chars,
            stderr_chars,
            stdout_lines,
            stderr_lines,
            excerpt,
        ),
    )
    conn.commit()
    conn.close()

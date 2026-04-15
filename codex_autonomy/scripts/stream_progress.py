from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Append-only session progress stream")
    parser.add_argument("--db", required=True, help="Path to sqlite state.db")
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--task-id", default="", help="Optional task_id filter")
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.execute("SELECT COALESCE(MAX(id), 0) AS last_id FROM session_progress")
        last_id = int(cur.fetchone()["last_id"])
    except sqlite3.OperationalError:
        last_id = 0
    scope = f" task_id={args.task_id}" if args.task_id else " all tasks"
    print(f"streaming session_progress from id>{last_id} ({scope}, db={db_path})")

    while True:
        try:
            if args.task_id:
                rows = conn.execute(
                    """
                    SELECT id, ts, task_id, session_index, elapsed_seconds, stdout_chars, stderr_chars, excerpt
                    FROM session_progress
                    WHERE id > ? AND task_id = ?
                    ORDER BY id ASC
                    """,
                    (last_id, args.task_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, ts, task_id, session_index, elapsed_seconds, stdout_chars, stderr_chars, excerpt
                    FROM session_progress
                    WHERE id > ?
                    ORDER BY id ASC
                    """,
                    (last_id,),
                ).fetchall()
        except sqlite3.OperationalError:
            rows = []

        for row in rows:
            print(
                f"{row['id']}|{row['ts']}|{row['task_id']}|s{row['session_index']}|"
                f"elapsed={int(row['elapsed_seconds'])}s|out={row['stdout_chars']}|err={row['stderr_chars']}|"
                f"{row['excerpt']}"
            )
            last_id = int(row["id"])

        time.sleep(max(0.2, args.poll_seconds))


if __name__ == "__main__":
    main()

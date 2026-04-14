from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Append-only session stream")
    parser.add_argument("--db", required=True, help="Path to sqlite state.db")
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--task-id", default="", help="Optional task_id filter")
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    cur = conn.execute("SELECT COALESCE(MAX(id), 0) AS last_id FROM sessions")
    last_id = int(cur.fetchone()["last_id"])
    scope = f" task_id={args.task_id}" if args.task_id else " all tasks"
    print(f"streaming sessions from id>{last_id} ({scope}, db={db_path})")

    while True:
        if args.task_id:
            rows = conn.execute(
                """
                SELECT id, ts, task_id, branch_name, return_code, duration_seconds
                FROM sessions
                WHERE id > ? AND task_id = ?
                ORDER BY id ASC
                """,
                (last_id, args.task_id),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, ts, task_id, branch_name, return_code, duration_seconds
                FROM sessions
                WHERE id > ?
                ORDER BY id ASC
                """,
                (last_id,),
            ).fetchall()

        for row in rows:
            print(
                f"{row['id']}|{row['ts']}|{row['task_id']}|{row['branch_name']}|"
                f"rc={row['return_code']}|dur={row['duration_seconds']:.2f}s"
            )
            last_id = int(row["id"])

        time.sleep(max(0.2, args.poll_seconds))


if __name__ == "__main__":
    main()

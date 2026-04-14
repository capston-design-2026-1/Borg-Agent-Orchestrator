from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Append-only task event stream")
    parser.add_argument("--db", required=True, help="Path to sqlite state.db")
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    cur = conn.execute("SELECT COALESCE(MAX(id), 0) AS last_id FROM task_events")
    last_id = int(cur.fetchone()["last_id"])
    print(f"streaming task_events from id>{last_id} (db={db_path})")

    while True:
        rows = conn.execute(
            """
            SELECT id, ts, task_id, event_type, message
            FROM task_events
            WHERE id > ?
            ORDER BY id ASC
            """,
            (last_id,),
        ).fetchall()

        for row in rows:
            print(f"{row['id']}|{row['ts']}|{row['task_id']}|{row['event_type']}|{row['message']}")
            last_id = int(row["id"])

        time.sleep(max(0.2, args.poll_seconds))


if __name__ == "__main__":
    main()

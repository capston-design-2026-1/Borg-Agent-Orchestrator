from __future__ import annotations

import argparse
from pathlib import Path

from codex_autonomy.config import load_config
from codex_autonomy.models import TaskSpec


def cmd_run(args: argparse.Namespace) -> None:
    from codex_autonomy.manager import AutonomyManager

    config = load_config(args.config)
    manager = AutonomyManager(config)
    manager.run_forever()


def cmd_enqueue(args: argparse.Namespace) -> None:
    from codex_autonomy.task_store import save_task

    config = load_config(args.config)
    task = TaskSpec(
        task_id=args.task_id,
        title=args.title,
        prompt=args.prompt,
        task_type=args.task_type,
        priority=args.priority,
        scope_paths=args.scope_paths or [],
        done_when_commands=args.done_when_commands or [],
    )
    save_task(config.queue_dir, task)
    print(f"enqueued: {task.task_id}")


def cmd_status(args: argparse.Namespace) -> None:
    from codex_autonomy.status import (
        process_state,
        queue_snapshot,
        recent_events,
        recent_progress,
        recent_sessions,
    )

    config = load_config(args.config)
    guardian_pid, guardian_alive = process_state(
        config.runtime_dir / "guardian.pid",
        "codex_autonomy/scripts/run_guardian.py",
    )
    manager_pid, manager_alive = process_state(
        config.runtime_dir / "manager.pid",
        "codex_autonomy/scripts/run_daemon.py run",
    )
    queue = queue_snapshot(config.queue_dir)
    events = recent_events(config.state_db_path, limit=args.limit)
    sessions = recent_sessions(config.state_db_path, limit=args.limit)
    progress = recent_progress(config.state_db_path, limit=args.limit)

    print("Runtime Processes:")
    print(f"- guardian | pid={guardian_pid} | alive={guardian_alive}")
    print(f"- manager  | pid={manager_pid} | alive={manager_alive}")

    print("\nQueue Snapshot:")
    for row in queue:
        print(f"- {row[0]} | status={row[1]} | issue={row[2]} | pr={row[3]}")

    print("Recent Task Events:")
    for row in events:
        print(f"- {row[0]} | {row[1]} | {row[2]} | {row[3]}")

    print("\nRecent Sessions:")
    for row in sessions:
        print(f"- {row[0]} | {row[1]} | {row[2]} | rc={row[3]} | dur={row[4]:.2f}s")

    print("\nRecent Session Progress:")
    for row in progress:
        print(
            f"- {row[0]} | {row[1]} | s{row[2]} | elapsed={int(row[3])}s | "
            f"out={row[4]} err={row[5]} | {row[6]}"
        )


def cmd_enqueue_bundle(args: argparse.Namespace) -> None:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "missing dependency 'PyYAML'; install codex_autonomy requirements before using "
            "enqueue-bundle or other YAML-backed commands"
        ) from exc

    from codex_autonomy.task_store import save_task

    config = load_config(args.config)
    bundle_path = Path(args.bundle).resolve()
    raw = yaml.safe_load(bundle_path.read_text(encoding="utf-8")) or {}
    items = list(raw.get("tasks", []))
    if not items:
        raise SystemExit(f"no tasks found in bundle: {bundle_path}")

    created: list[str] = []
    for item in items:
        task = TaskSpec(
            task_id=str(item["task_id"]),
            title=str(item.get("title", item["task_id"])),
            prompt=str(item["prompt"]),
            task_type=str(item.get("task_type", "feature")),
            priority=int(item.get("priority", 100)),
            dependencies=list(item.get("dependencies", [])),
            scope_paths=list(item.get("scope_paths", [])),
            done_when_commands=list(item.get("done_when_commands", [])),
            max_sessions=int(item.get("max_sessions", 12)),
            max_retries=int(item.get("max_retries", 5)),
            review_prompt=str(item.get("review_prompt", "Review branch changes for correctness and regressions.")),
            metadata=dict(item.get("metadata", {})),
        )
        save_task(config.queue_dir, task)
        created.append(task.task_id)

    print(f"enqueued bundle: {bundle_path}")
    for task_id in created:
        print(f"- {task_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex autonomy manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run")
    p_run.add_argument("--config", required=True)
    p_run.set_defaults(func=cmd_run)

    p_enqueue = sub.add_parser("enqueue")
    p_enqueue.add_argument("--config", required=True)
    p_enqueue.add_argument("--task-id", required=True)
    p_enqueue.add_argument("--title", required=True)
    p_enqueue.add_argument("--prompt", required=True)
    p_enqueue.add_argument("--task-type", default="feature", choices=["feature", "bug", "upgrade", "chore"])
    p_enqueue.add_argument("--priority", type=int, default=100)
    p_enqueue.add_argument("--scope-paths", nargs="*")
    p_enqueue.add_argument("--done-when-commands", nargs="*")
    p_enqueue.set_defaults(func=cmd_enqueue)

    p_status = sub.add_parser("status")
    p_status.add_argument("--config", required=True)
    p_status.add_argument("--limit", type=int, default=20)
    p_status.set_defaults(func=cmd_status)

    p_bundle = sub.add_parser("enqueue-bundle")
    p_bundle.add_argument("--config", required=True)
    p_bundle.add_argument("--bundle", required=True, help="YAML file containing top-level 'tasks' list")
    p_bundle.set_defaults(func=cmd_enqueue_bundle)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

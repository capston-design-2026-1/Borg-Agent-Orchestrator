from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import yaml

from codex_autonomy.models import TaskSpec, TaskStatus


def _task_from_raw(raw: dict) -> TaskSpec:
    status = TaskStatus(str(raw.get("status", "pending")))
    return TaskSpec(
        task_id=str(raw["task_id"]),
        title=str(raw.get("title", raw["task_id"])),
        prompt=str(raw["prompt"]),
        task_type=str(raw.get("task_type", "feature")),
        priority=int(raw.get("priority", 100)),
        dependencies=list(raw.get("dependencies", [])),
        scope_paths=list(raw.get("scope_paths", [])),
        done_when_commands=list(raw.get("done_when_commands", [])),
        max_sessions=int(raw.get("max_sessions", 12)),
        max_retries=int(raw.get("max_retries", 5)),
        retries=int(raw.get("retries", 0)),
        status=status,
        review_prompt=str(raw.get("review_prompt", "Review branch changes for correctness and regressions.")),
        issue_number=(int(raw["issue_number"]) if raw.get("issue_number") is not None else None),
        issue_url=(str(raw["issue_url"]) if raw.get("issue_url") else None),
        pr_number=(int(raw["pr_number"]) if raw.get("pr_number") is not None else None),
        pr_url=(str(raw["pr_url"]) if raw.get("pr_url") else None),
        metadata=dict(raw.get("metadata", {})),
        created_at=str(raw.get("created_at", datetime.utcnow().isoformat())),
        updated_at=str(raw.get("updated_at", datetime.utcnow().isoformat())),
    )


def _prefer_task(current: TaskSpec, candidate: TaskSpec) -> TaskSpec:
    # Prefer richer state first (issue/pr linkage), then newer update timestamp.
    current_links = int(current.issue_number is not None) + int(current.pr_number is not None)
    candidate_links = int(candidate.issue_number is not None) + int(candidate.pr_number is not None)
    if candidate_links != current_links:
        return candidate if candidate_links > current_links else current
    return candidate if candidate.updated_at >= current.updated_at else current


def load_tasks(queue_dir: Path) -> list[TaskSpec]:
    by_id: dict[str, TaskSpec] = {}
    for path in sorted(queue_dir.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        task = _task_from_raw(raw)
        existing = by_id.get(task.task_id)
        by_id[task.task_id] = task if existing is None else _prefer_task(existing, task)
    return list(by_id.values())


def save_task(queue_dir: Path, task: TaskSpec) -> Path:
    queue_dir.mkdir(parents=True, exist_ok=True)
    task.updated_at = datetime.utcnow().isoformat()
    payload = asdict(task)
    payload["status"] = task.status.value
    path = queue_dir / f"{task.task_id}.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    # Canonicalize queue files: one task_id -> one YAML file.
    for other in queue_dir.glob("*.yaml"):
        if other == path:
            continue
        raw = yaml.safe_load(other.read_text(encoding="utf-8")) or {}
        if str(raw.get("task_id", "")) == task.task_id:
            other.unlink(missing_ok=True)
    return path


def archive_task(queue_dir: Path, archive_dir: Path, task_id: str) -> None:
    source = queue_dir / f"{task_id}.yaml"
    if not source.exists():
        return
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    target = archive_dir / f"{timestamp}_{task_id}.yaml"
    source.replace(target)


def dependency_satisfied(task: TaskSpec, all_tasks: dict[str, TaskSpec]) -> bool:
    for dep in task.dependencies:
        dep_task = all_tasks.get(dep)
        if dep_task is None:
            return False
        if dep_task.status != TaskStatus.COMPLETED:
            return False
    return True

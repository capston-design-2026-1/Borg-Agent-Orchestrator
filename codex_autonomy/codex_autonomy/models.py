from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class TaskSpec:
    task_id: str
    title: str
    prompt: str
    priority: int = 100
    dependencies: list[str] = field(default_factory=list)
    scope_paths: list[str] = field(default_factory=list)
    done_when_commands: list[str] = field(default_factory=list)
    max_sessions: int = 12
    max_retries: int = 5
    retries: int = 0
    status: TaskStatus = TaskStatus.PENDING
    review_prompt: str = "Review branch changes for correctness and regressions."
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass(slots=True)
class SessionResult:
    return_code: int
    stdout: str
    stderr: str
    duration_seconds: float


@dataclass(slots=True)
class WorkerResult:
    task_id: str
    branch_name: str
    status: TaskStatus
    message: str
    sessions_used: int

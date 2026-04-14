from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class HealthCheckConfig:
    lint_command: str = ""
    test_command: str = ""
    upgrade_scan_command: str = ""
    interval_seconds: int = 900


@dataclass(slots=True)
class SessionConfig:
    command_template: str = "codex exec - < {prompt_file}"
    timeout_seconds: int = 1800
    max_session_minutes: int = 25
    rate_limit_cooldown_seconds: int = 1800


@dataclass(slots=True)
class GitHubFlowConfig:
    enabled: bool = False
    repo: str = ""
    auto_create_issue: bool = True
    auto_create_pr: bool = True
    auto_merge: bool = False
    merge_method: str = "squash"
    draft_pr: bool = True
    auto_issue_on_health: bool = True
    reviewers: list[str] = field(default_factory=list)
    assignees: list[str] = field(default_factory=list)
    label_feature: str = "enhancement"
    label_bug: str = "bug"
    label_upgrade: str = "dependencies"


@dataclass(slots=True)
class ManagerConfig:
    repo_root: Path
    queue_dir: Path
    archive_dir: Path
    runtime_dir: Path
    state_db_path: Path
    max_parallel_workers: int = 3
    poll_interval_seconds: int = 10
    base_branch: str = "main"
    auto_push: bool = True
    enable_health_loop: bool = True
    session: SessionConfig = field(default_factory=SessionConfig)
    health: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    github: GitHubFlowConfig = field(default_factory=GitHubFlowConfig)


def _path(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p).resolve()


def load_config(path: str | Path) -> ManagerConfig:
    config_path = Path(path).resolve()
    raw: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    cwd = Path.cwd().resolve()

    repo_root = _path(cwd, raw.get("repo_root", "."))
    queue_dir = _path(repo_root, raw.get("queue_dir", "codex_autonomy/tasks/queue"))
    archive_dir = _path(repo_root, raw.get("archive_dir", "codex_autonomy/tasks/archive"))
    runtime_dir = _path(repo_root, raw.get("runtime_dir", "codex_autonomy/runtime"))
    state_db_path = _path(repo_root, raw.get("state_db_path", "codex_autonomy/runtime/state.db"))

    session_raw = raw.get("session", {})
    health_raw = raw.get("health", {})
    github_raw = raw.get("github", {})

    return ManagerConfig(
        repo_root=repo_root,
        queue_dir=queue_dir,
        archive_dir=archive_dir,
        runtime_dir=runtime_dir,
        state_db_path=state_db_path,
        max_parallel_workers=int(raw.get("max_parallel_workers", 3)),
        poll_interval_seconds=int(raw.get("poll_interval_seconds", 10)),
        base_branch=str(raw.get("base_branch", "main")),
        auto_push=bool(raw.get("auto_push", True)),
        enable_health_loop=bool(raw.get("enable_health_loop", True)),
        session=SessionConfig(
            command_template=str(session_raw.get("command_template", "codex exec - < {prompt_file}")),
            timeout_seconds=int(session_raw.get("timeout_seconds", 1800)),
            max_session_minutes=int(session_raw.get("max_session_minutes", 25)),
            rate_limit_cooldown_seconds=int(session_raw.get("rate_limit_cooldown_seconds", 1800)),
        ),
        health=HealthCheckConfig(
            lint_command=str(health_raw.get("lint_command", "")),
            test_command=str(health_raw.get("test_command", "")),
            upgrade_scan_command=str(health_raw.get("upgrade_scan_command", "")),
            interval_seconds=int(health_raw.get("interval_seconds", 900)),
        ),
        github=GitHubFlowConfig(
            enabled=bool(github_raw.get("enabled", False)),
            repo=str(github_raw.get("repo", "")),
            auto_create_issue=bool(github_raw.get("auto_create_issue", True)),
            auto_create_pr=bool(github_raw.get("auto_create_pr", True)),
            auto_merge=bool(github_raw.get("auto_merge", False)),
            merge_method=str(github_raw.get("merge_method", "squash")),
            draft_pr=bool(github_raw.get("draft_pr", True)),
            auto_issue_on_health=bool(github_raw.get("auto_issue_on_health", True)),
            reviewers=list(github_raw.get("reviewers", [])),
            assignees=list(github_raw.get("assignees", [])),
            label_feature=str(github_raw.get("label_feature", "enhancement")),
            label_bug=str(github_raw.get("label_bug", "bug")),
            label_upgrade=str(github_raw.get("label_upgrade", "dependencies")),
        ),
    )

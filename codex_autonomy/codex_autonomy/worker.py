from __future__ import annotations

import subprocess
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from codex_autonomy.config import ManagerConfig
from codex_autonomy.models import TaskSpec, TaskStatus, WorkerResult
from codex_autonomy.session_adapter import SessionAdapter
from codex_autonomy.state_db import log_event, log_session
from codex_autonomy.task_store import save_task
from codex_autonomy.worktree import cleanup_worktree, ensure_branch, ensure_worktree


def _run(command: str, cwd: Path) -> int:
    proc = subprocess.run(command, cwd=str(cwd), shell=True)
    return proc.returncode


def _check_done(task: TaskSpec, worktree_path: Path) -> bool:
    if not task.done_when_commands:
        return True
    return all(_run(cmd, worktree_path) == 0 for cmd in task.done_when_commands)


def _auto_commit_and_push(config: ManagerConfig, worktree_path: Path, branch_name: str, task: TaskSpec) -> None:
    subprocess.run(["git", "add", "-A"], cwd=str(worktree_path), check=False)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(worktree_path), check=False)
    if diff.returncode != 0:
        subprocess.run(
            ["git", "commit", "-m", f"auto(task): {task.task_id} - {task.title}"],
            cwd=str(worktree_path),
            check=False,
        )
    if config.auto_push:
        subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=str(worktree_path), check=False)


def _make_prompt(task: TaskSpec, session_idx: int) -> str:
    resume = (
        "Read Agents.md, NEXT_STEPS.md, and latest reports before coding. "
        "When context is exhausted, update task/report files and let supervisor continue next session. "
        "Do implementation, verification, commit, and push."
    )
    return (
        f"Task ID: {task.task_id}\n"
        f"Title: {task.title}\n"
        f"Session: {session_idx + 1}/{task.max_sessions}\n"
        f"Scope paths: {', '.join(task.scope_paths) if task.scope_paths else 'not restricted'}\n\n"
        f"Primary objective:\n{task.prompt}\n\n"
        f"Continuation protocol:\n{resume}\n"
    )


def run_task(config: ManagerConfig, task: TaskSpec) -> WorkerResult:
    branch_name = f"auto/{task.task_id}"
    worktree_path = (config.runtime_dir / "worktrees" / task.task_id).resolve()
    logs_dir = (config.runtime_dir / "logs" / task.task_id).resolve()
    logs_dir.mkdir(parents=True, exist_ok=True)

    ensure_branch(config.repo_root, config.base_branch, branch_name)
    ensure_worktree(config.repo_root, branch_name, worktree_path)

    adapter = SessionAdapter(
        command_template=config.session.command_template,
        timeout_seconds=config.session.timeout_seconds,
    )

    task = replace(task, status=TaskStatus.RUNNING)
    save_task(config.queue_dir, task)

    sessions_used = 0
    try:
        for idx in range(task.max_sessions):
            sessions_used = idx + 1
            now = datetime.utcnow().isoformat()
            prompt_text = _make_prompt(task, idx)
            prompt_file = logs_dir / f"session_{idx + 1:03d}.prompt.txt"
            stdout_file = logs_dir / f"session_{idx + 1:03d}.stdout.log"
            stderr_file = logs_dir / f"session_{idx + 1:03d}.stderr.log"
            prompt_file.write_text(prompt_text, encoding="utf-8")

            result = adapter.run(workdir=worktree_path, prompt_file=prompt_file)
            stdout_file.write_text(result.stdout, encoding="utf-8")
            stderr_file.write_text(result.stderr, encoding="utf-8")

            log_session(
                config.state_db_path,
                ts=now,
                task_id=task.task_id,
                branch_name=branch_name,
                return_code=result.return_code,
                duration_seconds=result.duration_seconds,
                stdout_path=str(stdout_file),
                stderr_path=str(stderr_file),
            )

            if result.return_code != 0:
                log_event(
                    config.state_db_path,
                    ts=now,
                    task_id=task.task_id,
                    event_type="session_failed",
                    message=f"session {idx + 1} exit code {result.return_code}",
                )
                continue

            if _check_done(task, worktree_path):
                _auto_commit_and_push(config, worktree_path, branch_name, task)
                task = replace(task, status=TaskStatus.COMPLETED)
                save_task(config.queue_dir, task)
                return WorkerResult(
                    task_id=task.task_id,
                    branch_name=branch_name,
                    status=TaskStatus.COMPLETED,
                    message="completed",
                    sessions_used=sessions_used,
                )

        task = replace(task, retries=task.retries + 1)
        if task.retries >= task.max_retries:
            task = replace(task, status=TaskStatus.FAILED)
            save_task(config.queue_dir, task)
            return WorkerResult(
                task_id=task.task_id,
                branch_name=branch_name,
                status=TaskStatus.FAILED,
                message="max sessions exceeded and retries exhausted",
                sessions_used=sessions_used,
            )

        task = replace(task, status=TaskStatus.PENDING)
        save_task(config.queue_dir, task)
        return WorkerResult(
            task_id=task.task_id,
            branch_name=branch_name,
            status=TaskStatus.PENDING,
            message="session budget exhausted; re-queued for rollover",
            sessions_used=sessions_used,
        )
    finally:
        cleanup_worktree(config.repo_root, worktree_path)

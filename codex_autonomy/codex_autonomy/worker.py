from __future__ import annotations

import subprocess
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path
import re
from typing import Any

import yaml

from codex_autonomy.config import ManagerConfig
from codex_autonomy.github_flow import ensure_issue, ensure_pr, try_merge_pr
from codex_autonomy.models import TaskSpec, TaskStatus, WorkerResult
from codex_autonomy.session_adapter import SessionAdapter
from codex_autonomy.state_db import log_event, log_session, log_session_progress
from codex_autonomy.task_store import save_task
from codex_autonomy.worktree import cleanup_worktree, ensure_branch, ensure_worktree


def _journal_relpath(task_id: str) -> Path:
    return Path("codex_autonomy") / "task_journal" / f"{task_id}.md"


def _run(command: str, cwd: Path) -> int:
    proc = subprocess.run(command, cwd=str(cwd), shell=True)
    return proc.returncode


def _check_done(task: TaskSpec, worktree_path: Path) -> bool:
    if not task.done_when_commands:
        return True
    return all(_run(cmd, worktree_path) == 0 for cmd in task.done_when_commands)


def _is_limit_error(stdout: str, stderr: str) -> bool:
    text = f"{stdout}\n{stderr}".lower()
    patterns = (
        "rate limit",
        "too many requests",
        "quota",
        "usage limit",
        "limit exceeded",
        "weekly limit",
        "daily limit",
        "5 hour",
        "try again later",
    )
    return any(p in text for p in patterns)


def _is_command_template_error(stdout: str, stderr: str) -> bool:
    text = f"{stdout}\n{stderr}".lower()
    patterns = (
        "unexpected argument '--prompt-file'",
        "usage: codex",
        "for more information, try '--help'",
    )
    return all(p in text for p in patterns)


def _append_task_journal(
    worktree_path: Path,
    task: TaskSpec,
    *,
    session_idx: int,
    heading: str,
    details: list[str],
) -> Path:
    relpath = _journal_relpath(task.task_id)
    path = worktree_path / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            (
                f"# Task Journal: {task.task_id}\n\n"
                f"- Title: {task.title}\n"
                f"- Task type: {task.task_type}\n"
                f"- Issue: {task.issue_url or 'n/a'}\n"
                f"- Scope: {', '.join(task.scope_paths) if task.scope_paths else 'not restricted'}\n\n"
            ),
            encoding="utf-8",
        )

    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    body = [f"## {timestamp} | Session {session_idx + 1} | {heading}", ""]
    body.extend(f"- {line}" for line in details)
    body.append("")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(body))
    return relpath


def _worktree_status_lines(worktree_path: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=str(worktree_path),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return ["git status unavailable"]
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return lines or ["clean"]


def _heartbeat_commit_message(excerpt: str) -> str:
    return _trace_subject_from_excerpt(excerpt, fallback="heartbeat")


def _trace_subject_from_excerpt(excerpt: str, *, fallback: str) -> str:
    noise_prefixes = (
        "to https://",
        "remote:",
        "hint:",
        "everything up-to-date",
        "succeeded in",
        "## auto/",
        "fatal:",
        "error:",
        "branch ",
    )
    candidates: list[str] = []
    for raw_line in excerpt.splitlines():
        line = raw_line.strip().replace("`", "'")
        line = re.sub(r"^[+\-]+\s*", "", line)
        line = re.sub(r"^\d+\.\s*", "", line)
        line = re.sub(r"^\?\?\s*", "", line)
        line = re.sub(r"^[MADRCU]{1,2}\s+", "", line)
        line = re.sub(r"\s+", " ", line).strip(" .,:;|-")
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith(noise_prefixes):
            continue
        if re.fullmatch(r"[./\w-]+\.[A-Za-z0-9_]+", line):
            continue
        if "/" in line and " " not in line:
            continue
        if not re.search(r"[A-Za-z]", line):
            continue
        line = re.sub(r"^[^A-Za-z(]+", "", line)
        if not line:
            continue
        candidates.append(line)

    cleaned = candidates[0] if candidates else fallback
    cleaned = cleaned[0].upper() + cleaned[1:] if cleaned and cleaned[0].isalpha() else cleaned
    words = cleaned.split()
    summary = " ".join(words[:18])
    max_len = 72 - len("trace : ")
    if len(summary) > max_len:
        summary = summary[: max_len - 3].rstrip(" ,.;:-") + "..."
    return f"trace : {summary}"


def _commit_paths_and_push(
    config: ManagerConfig,
    worktree_path: Path,
    branch_name: str,
    *,
    paths: list[Path],
    message: str,
) -> bool:
    if not paths:
        return False
    subprocess.run(["git", "add", "--", *[str(path) for path in paths]], cwd=str(worktree_path), check=False)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet", "--", *[str(path) for path in paths]], cwd=str(worktree_path), check=False)
    if diff.returncode == 0:
        return False
    commit = subprocess.run(
        ["git", "commit", "-m", message, "--", *[str(path) for path in paths]],
        cwd=str(worktree_path),
        check=False,
    )
    if commit.returncode != 0:
        return False
    if config.auto_push:
        subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=str(worktree_path), check=False)
    return True


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


def _load_followup_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        tasks = raw.get("tasks", [])
        if isinstance(tasks, list):
            return [item for item in tasks if isinstance(item, dict)]
    return []


def _enqueue_followups(
    config: ManagerConfig,
    parent_task: TaskSpec,
    session_idx: int,
    followups_file: Path,
) -> list[str]:
    created: list[str] = []
    for item in _load_followup_items(followups_file):
        task_id = str(item.get("task_id", "")).strip()
        prompt = str(item.get("prompt", "")).strip()
        if not task_id or not prompt:
            continue
        metadata = dict(item.get("metadata", {}))
        metadata["generated_by_task"] = parent_task.task_id
        metadata["generated_by_session"] = session_idx + 1
        task = TaskSpec(
            task_id=task_id,
            title=str(item.get("title", task_id)),
            prompt=prompt,
            task_type=str(item.get("task_type", "feature")),
            priority=int(item.get("priority", parent_task.priority + 10)),
            dependencies=list(item.get("dependencies", [])),
            scope_paths=list(item.get("scope_paths", parent_task.scope_paths)),
            done_when_commands=list(item.get("done_when_commands", [])),
            max_sessions=int(item.get("max_sessions", parent_task.max_sessions)),
            max_retries=int(item.get("max_retries", parent_task.max_retries)),
            review_prompt=str(
                item.get("review_prompt", "Review branch changes for correctness and regressions.")
            ),
            metadata=metadata,
        )
        save_task(config.queue_dir, task)
        created.append(task.task_id)
    return created


def _make_prompt(task: TaskSpec, session_idx: int, followups_file: Path) -> str:
    resume = (
        "Read Agents.md, NEXT_STEPS.md, and latest reports before coding. "
        "When context is exhausted, update task/report files and let supervisor continue next session. "
        "Do implementation, verification, commit, and push."
    )
    commit_rules = (
        "Commit/push protocol:\n"
        "- Commit code and docs in small validated slices while you work; prefer one changed file per commit when practical.\n"
        "- Push after each meaningful commit so the branch stays current.\n"
        "- Supervisor will publish heartbeat trace commits separately; do not spend task context writing bookkeeping notes unless needed for handoff clarity.\n"
    )
    expansion = (
        "Autonomous decomposition protocol:\n"
        "- Treat the current task as intake, not as permission to batch every discovered change into one PR.\n"
        "- If you discover additional feature slices or bugs that should be separate PRs/issues, write follow-up tasks "
        f"to YAML file: {followups_file}\n"
        "- Output schema: top-level 'tasks' list; each item should include task_id, title, task_type, prompt, "
        "priority, dependencies (optional), scope_paths (optional), done_when_commands (optional), max_sessions, "
        "max_retries, metadata (optional).\n"
        "- Keep follow-up tasks narrowly scoped so each can become a small independent PR.\n"
        "- Prefer emitting follow-up tasks instead of expanding the current PR when the newly discovered work is not an immediate blocker for the current slice.\n"
        "- Only keep directly blocking fixes in the current task; enqueue adjacent features, cleanup, docs-only work, and newly discovered bugs as follow-ups.\n"
    )
    return (
        f"Task ID: {task.task_id}\n"
        f"Title: {task.title}\n"
        f"Session: {session_idx + 1}/{task.max_sessions}\n"
        f"Scope paths: {', '.join(task.scope_paths) if task.scope_paths else 'not restricted'}\n\n"
        f"Primary objective:\n{task.prompt}\n\n"
        f"Continuation protocol:\n{resume}\n"
        f"{commit_rules}\n"
        f"{expansion}\n"
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

    if task.metadata.get("skip_auto_issue", False):
        issue_number, issue_url = task.issue_number, task.issue_url
    else:
        issue_number, issue_url = ensure_issue(config, task)
    task = replace(task, status=TaskStatus.RUNNING, issue_number=issue_number, issue_url=issue_url)
    save_task(config.queue_dir, task)

    sessions_used = 0
    try:
        for idx in range(task.max_sessions):
            sessions_used = idx + 1
            now = datetime.utcnow().isoformat()
            followups_file = logs_dir / f"session_{idx + 1:03d}.followups.yaml"
            journal_relpath = _append_task_journal(
                worktree_path,
                task,
                session_idx=idx,
                heading="session_started",
                details=[
                    f"supervisor started session {idx + 1} of {task.max_sessions}",
                    f"prompt file: {logs_dir / f'session_{idx + 1:03d}.prompt.txt'}",
                    "supervisor will publish heartbeat trace commits during execution",
                ],
            )
            _commit_paths_and_push(
                config,
                worktree_path,
                branch_name,
                paths=[journal_relpath],
                message=f"trace : Session {idx + 1} started",
            )
            prompt_text = _make_prompt(task, idx, followups_file)
            prompt_file = logs_dir / f"session_{idx + 1:03d}.prompt.txt"
            stdout_file = logs_dir / f"session_{idx + 1:03d}.stdout.log"
            stderr_file = logs_dir / f"session_{idx + 1:03d}.stderr.log"
            followups_file.unlink(missing_ok=True)
            prompt_file.write_text(prompt_text, encoding="utf-8")
            last_trace_excerpt = ""
            def _on_progress(snapshot: dict[str, Any]) -> None:
                tail = str(snapshot.get("stderr_tail") or snapshot.get("stdout_tail") or "").strip()
                excerpt = tail[-int(config.session.progress_excerpt_chars) :] if tail else "(heartbeat)"
                ts = datetime.utcnow().isoformat()
                log_session_progress(
                    config.state_db_path,
                    ts=ts,
                    task_id=task.task_id,
                    session_index=idx + 1,
                    elapsed_seconds=float(snapshot.get("elapsed_seconds", 0.0)),
                    stdout_chars=int(snapshot.get("stdout_chars", 0)),
                    stderr_chars=int(snapshot.get("stderr_chars", 0)),
                    stdout_lines=int(snapshot.get("stdout_lines", 0)),
                    stderr_lines=int(snapshot.get("stderr_lines", 0)),
                    excerpt=excerpt,
                )
                log_event(
                    config.state_db_path,
                    ts=ts,
                    task_id=task.task_id,
                    event_type="session_heartbeat",
                    message=(
                        f"s{idx + 1}: elapsed={int(float(snapshot.get('elapsed_seconds', 0.0)))}s "
                        f"out={int(snapshot.get('stdout_chars', 0))} err={int(snapshot.get('stderr_chars', 0))}"
                    ),
                )
                nonlocal last_trace_excerpt
                status_lines = _worktree_status_lines(worktree_path)
                trace_signature = f"{excerpt}\n{status_lines[:8]}"
                if trace_signature == last_trace_excerpt:
                    return
                last_trace_excerpt = trace_signature
                journal_relpath = _append_task_journal(
                    worktree_path,
                    task,
                    session_idx=idx,
                    heading="heartbeat",
                    details=[
                        f"elapsed_seconds: {int(float(snapshot.get('elapsed_seconds', 0.0)))}",
                        f"stdout_chars: {int(snapshot.get('stdout_chars', 0))}",
                        f"stderr_chars: {int(snapshot.get('stderr_chars', 0))}",
                        f"excerpt: {excerpt}",
                        "worktree_status:",
                        *[f"  {line}" for line in status_lines[:12]],
                    ],
                )
                _commit_paths_and_push(
                    config,
                    worktree_path,
                    branch_name,
                    paths=[journal_relpath],
                    message=_heartbeat_commit_message(excerpt),
                )

            result = adapter.run(
                workdir=worktree_path,
                prompt_file=prompt_file,
                heartbeat_seconds=max(1, int(config.session.heartbeat_seconds)),
                progress_callback=_on_progress,
            )
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
            session_detail = [
                f"return_code: {result.return_code}",
                f"duration_seconds: {result.duration_seconds:.1f}",
                f"timed_out: {result.timed_out}",
            ]
            if result.return_code != 0:
                session_detail.append("result: session_failed_or_incomplete")
            else:
                session_detail.append("result: session_completed")
            journal_relpath = _append_task_journal(
                worktree_path,
                task,
                session_idx=idx,
                heading="session_finished",
                details=session_detail,
            )
            _commit_paths_and_push(
                config,
                worktree_path,
                branch_name,
                paths=[journal_relpath],
                message=f"trace : Session {idx + 1} finished rc={result.return_code}",
            )

            if result.return_code != 0:
                if result.timed_out:
                    log_event(
                        config.state_db_path,
                        ts=now,
                        task_id=task.task_id,
                        event_type="session_timeout",
                        message=f"session {idx + 1} timed out after {int(config.session.timeout_seconds)}s",
                    )
                if _is_command_template_error(result.stdout, result.stderr):
                    task = replace(task, status=TaskStatus.FAILED)
                    save_task(config.queue_dir, task)
                    log_event(
                        config.state_db_path,
                        ts=now,
                        task_id=task.task_id,
                        event_type="session_config_error",
                        message="invalid command_template for installed codex CLI",
                    )
                    return WorkerResult(
                        task_id=task.task_id,
                        branch_name=branch_name,
                        status=TaskStatus.FAILED,
                        message="invalid command_template; update config to codex exec mode",
                        sessions_used=sessions_used,
                    )
                if _is_limit_error(result.stdout, result.stderr):
                    now_epoch = int(time.time())
                    cooldown = max(60, int(config.session.rate_limit_cooldown_seconds))
                    not_before = now_epoch + cooldown
                    metadata = dict(task.metadata)
                    metadata["not_before_epoch"] = not_before
                    metadata["wait_reason"] = "codex_limit_cooldown"
                    task = replace(task, status=TaskStatus.PENDING, metadata=metadata)
                    save_task(config.queue_dir, task)
                    log_event(
                        config.state_db_path,
                        ts=now,
                        task_id=task.task_id,
                        event_type="session_rate_limited",
                        message=f"cooldown {cooldown}s until {not_before}",
                    )
                    return WorkerResult(
                        task_id=task.task_id,
                        branch_name=branch_name,
                        status=TaskStatus.PENDING,
                        message=f"codex limit detected; cooling down {cooldown}s",
                        sessions_used=sessions_used,
                    )
                log_event(
                    config.state_db_path,
                    ts=now,
                    task_id=task.task_id,
                    event_type="session_failed",
                    message=f"session {idx + 1} exit code {result.return_code}",
                )
                continue

            created_followups = _enqueue_followups(config, task, idx, followups_file)
            for child_id in created_followups:
                log_event(
                    config.state_db_path,
                    ts=now,
                    task_id=task.task_id,
                    event_type="followup_enqueued",
                    message=f"generated follow-up task {child_id}",
                )

            if _check_done(task, worktree_path):
                _auto_commit_and_push(config, worktree_path, branch_name, task)
                pr_number, pr_url = ensure_pr(config, task, branch_name)
                task = replace(task, pr_number=pr_number, pr_url=pr_url)

                merged = False
                if pr_number is not None:
                    merged = try_merge_pr(config, pr_number)

                final_status = TaskStatus.COMPLETED if merged or not pr_number else TaskStatus.REVIEW
                task = replace(task, status=final_status)
                save_task(config.queue_dir, task)
                return WorkerResult(
                    task_id=task.task_id,
                    branch_name=branch_name,
                    status=final_status,
                    message=(
                        "completed and merged"
                        if merged
                        else ("completed" if final_status == TaskStatus.COMPLETED else "awaiting PR review/merge")
                    ),
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

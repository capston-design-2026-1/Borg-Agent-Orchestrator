from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime
import subprocess

from codex_autonomy.config import ManagerConfig
from codex_autonomy.github_flow import try_merge_pr
from codex_autonomy.health import run_health_checks
from codex_autonomy.models import TaskSpec, TaskStatus
from codex_autonomy.state_db import init_db, log_event
from codex_autonomy.task_store import archive_task, load_tasks, save_task
from codex_autonomy.worker import run_task


class AutonomyManager:
    def __init__(self, config: ManagerConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=config.max_parallel_workers)
        self.inflight: dict[str, Future] = {}
        self.inflight_started_at: dict[str, float] = {}
        self.last_health_check = 0.0

    def _select_runnable_tasks(self, tasks: list[TaskSpec]) -> list[TaskSpec]:
        now_ts = int(time.time())
        by_id = {t.task_id: t for t in tasks}
        runnable: list[TaskSpec] = []
        for task in tasks:
            if task.status != TaskStatus.PENDING:
                continue
            not_before = int(task.metadata.get("not_before_epoch", 0) or 0)
            if not_before > now_ts:
                continue
            if task.task_id in self.inflight:
                continue
            if self._dependency_satisfied(task, by_id):
                runnable.append(task)
        runnable.sort(key=lambda t: (t.priority, t.created_at))
        return runnable

    def _dependency_satisfied(self, task: TaskSpec, by_id: dict[str, TaskSpec]) -> bool:
        for dep in task.dependencies:
            dep_task = by_id.get(dep)
            if dep_task is not None:
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
                continue
            # Completed tasks are archived and removed from queue; treat archived dep as satisfied.
            archived = list(self.config.archive_dir.glob(f"*_{dep}.yaml"))
            if not archived:
                return False
        return True

    def _handle_finished(self) -> None:
        done_ids: list[str] = []
        for task_id, future in self.inflight.items():
            if not future.done():
                continue
            done_ids.append(task_id)
            try:
                result = future.result()
                now = datetime.utcnow().isoformat()
                log_event(
                    self.config.state_db_path,
                    ts=now,
                    task_id=task_id,
                    event_type="task_result",
                    message=f"{result.status.value}: {result.message}",
                )
                if result.status in {TaskStatus.COMPLETED, TaskStatus.FAILED}:
                    archive_task(self.config.queue_dir, self.config.archive_dir, task_id)
            except Exception as exc:
                tasks = load_tasks(self.config.queue_dir)
                for task in tasks:
                    if task.task_id != task_id:
                        continue
                    task.status = TaskStatus.PENDING
                    save_task(self.config.queue_dir, task)
                    break
                log_event(
                    self.config.state_db_path,
                    ts=datetime.utcnow().isoformat(),
                    task_id=task_id,
                    event_type="worker_crashed",
                    message=f"worker future exception: {type(exc).__name__}: {exc}",
                )

        for task_id in done_ids:
            self.inflight.pop(task_id, None)
            self.inflight_started_at.pop(task_id, None)

    def _stuck_timeout_seconds(self) -> int:
        configured = int(self.config.recovery.stuck_task_seconds)
        if configured > 0:
            return configured
        return int(self.config.session.timeout_seconds) + 120

    def _kill_task_processes(self, task_id: str) -> int:
        pattern = f"codex_autonomy/runtime/logs/{task_id}/session_"
        proc = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, check=False)
        if proc.returncode != 0 or not proc.stdout.strip():
            return 0

        pids: list[int] = []
        for token in proc.stdout.split():
            try:
                pids.append(int(token))
            except ValueError:
                continue

        if not pids:
            return 0

        for pid in pids:
            subprocess.run(["kill", "-TERM", str(pid)], check=False)
        time.sleep(1.0)
        for pid in pids:
            subprocess.run(["kill", "-KILL", str(pid)], check=False)
        return len(pids)

    def _recover_stuck_or_orphan_running(self, tasks: list[TaskSpec]) -> None:
        if not self.config.recovery.enabled:
            return
        timeout_seconds = self._stuck_timeout_seconds()
        now = time.time()

        for task in tasks:
            if task.status != TaskStatus.RUNNING:
                continue

            # Orphan running state can happen when manager restarts mid-session.
            if task.task_id not in self.inflight:
                killed = 0
                if self.config.recovery.kill_orphan_task_processes:
                    killed = self._kill_task_processes(task.task_id)
                recovered = replace(task, status=TaskStatus.PENDING)
                save_task(self.config.queue_dir, recovered)
                log_event(
                    self.config.state_db_path,
                    ts=datetime.utcnow().isoformat(),
                    task_id=task.task_id,
                    event_type="task_recovered",
                    message=f"orphan running state recovered; re-queued (killed_pids={killed})",
                )
                continue

            started = self.inflight_started_at.get(task.task_id, now)
            elapsed = now - started
            if elapsed < timeout_seconds:
                continue

            killed = self._kill_task_processes(task.task_id)
            log_event(
                self.config.state_db_path,
                ts=datetime.utcnow().isoformat(),
                task_id=task.task_id,
                event_type="task_watchdog",
                message=f"stuck task watchdog fired after {int(elapsed)}s (killed_pids={killed})",
            )

    def _advance_review_tasks(self, tasks: list[TaskSpec]) -> None:
        for task in tasks:
            if task.status != TaskStatus.REVIEW:
                continue
            if task.pr_number is None:
                continue
            if not self.config.github.auto_merge:
                continue
            merged = try_merge_pr(self.config, task.pr_number)
            if not merged:
                continue
            task.status = TaskStatus.COMPLETED
            save_task(self.config.queue_dir, task)
            archive_task(self.config.queue_dir, self.config.archive_dir, task.task_id)
            log_event(
                self.config.state_db_path,
                ts=datetime.utcnow().isoformat(),
                task_id=task.task_id,
                event_type="pr_merged",
                message=f"merged PR #{task.pr_number}",
            )

    def run_forever(self) -> None:
        init_db(self.config.state_db_path)
        self.config.queue_dir.mkdir(parents=True, exist_ok=True)
        self.config.archive_dir.mkdir(parents=True, exist_ok=True)
        self.config.runtime_dir.mkdir(parents=True, exist_ok=True)

        while True:
            self._handle_finished()

            now_ts = time.time()
            if (
                self.config.enable_health_loop
                and now_ts - self.last_health_check >= self.config.health.interval_seconds
            ):
                created = run_health_checks(self.config)
                self.last_health_check = now_ts
                for task_id in created:
                    log_event(
                        self.config.state_db_path,
                        ts=datetime.utcnow().isoformat(),
                        task_id=task_id,
                        event_type="health_generated",
                        message="auto-generated by health loop",
                    )

            tasks = load_tasks(self.config.queue_dir)
            self._recover_stuck_or_orphan_running(tasks)
            tasks = load_tasks(self.config.queue_dir)
            self._advance_review_tasks(tasks)
            tasks = load_tasks(self.config.queue_dir)
            runnable = self._select_runnable_tasks(tasks)
            free_slots = self.config.max_parallel_workers - len(self.inflight)

            for task in runnable[: max(0, free_slots)]:
                fut = self.executor.submit(run_task, self.config, task)
                self.inflight[task.task_id] = fut
                self.inflight_started_at[task.task_id] = time.time()
                log_event(
                    self.config.state_db_path,
                    ts=datetime.utcnow().isoformat(),
                    task_id=task.task_id,
                    event_type="task_started",
                    message="worker launched",
                )

            time.sleep(self.config.poll_interval_seconds)

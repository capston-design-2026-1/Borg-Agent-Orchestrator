from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from codex_autonomy.config import ManagerConfig
from codex_autonomy.models import TaskSpec
from codex_autonomy.task_store import save_task


def _run(command: str, cwd: Path) -> tuple[int, str]:
    if not command.strip():
        return 0, ""
    proc = subprocess.run(command, cwd=str(cwd), shell=True, text=True, capture_output=True)
    merged = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return proc.returncode, merged.strip()


def _enqueue_if_missing(config: ManagerConfig, task: TaskSpec) -> None:
    task_file = config.queue_dir / f"{task.task_id}.yaml"
    if not task_file.exists():
        save_task(config.queue_dir, task)


def run_health_checks(config: ManagerConfig) -> list[str]:
    created: list[str] = []
    now = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    code, output = _run(config.health.lint_command, config.repo_root)
    if code != 0:
        task_id = f"heal-lint-{now}"
        _enqueue_if_missing(
            config,
            TaskSpec(
                task_id=task_id,
                title="Heal lint failures",
                prompt=f"Fix lint failures.\nCommand: {config.health.lint_command}\nOutput:\n{output}",
                priority=10,
                done_when_commands=[config.health.lint_command],
            ),
        )
        created.append(task_id)

    code, output = _run(config.health.test_command, config.repo_root)
    if code != 0:
        task_id = f"heal-test-{now}"
        _enqueue_if_missing(
            config,
            TaskSpec(
                task_id=task_id,
                title="Heal test failures",
                prompt=f"Fix test failures.\nCommand: {config.health.test_command}\nOutput:\n{output}",
                priority=5,
                done_when_commands=[config.health.test_command],
            ),
        )
        created.append(task_id)

    code, output = _run(config.health.upgrade_scan_command, config.repo_root)
    if code == 0 and output.strip():
        task_id = f"upgrade-deps-{now}"
        _enqueue_if_missing(
            config,
            TaskSpec(
                task_id=task_id,
                title="Upgrade dependencies from scanner output",
                prompt=f"Process dependency upgrade candidates and apply safe upgrades.\nOutput:\n{output}",
                priority=30,
                done_when_commands=[],
            ),
        )
        created.append(task_id)

    return created

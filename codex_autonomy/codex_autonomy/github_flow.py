from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from codex_autonomy.config import ManagerConfig
from codex_autonomy.models import TaskSpec


def _run(args: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(args, cwd=str(cwd), text=True, capture_output=True)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "gh not found"


def github_enabled(config: ManagerConfig) -> bool:
    if not config.github.enabled:
        return False
    code, _, _ = _run(["gh", "--version"], config.repo_root)
    return code == 0


def _label_for_task(config: ManagerConfig, task: TaskSpec) -> str:
    if task.task_type == "bug":
        return config.github.label_bug
    if task.task_type == "upgrade":
        return config.github.label_upgrade
    return config.github.label_feature


def _extract_number(url: str) -> int | None:
    m = re.search(r"/(\d+)$", url.strip())
    return int(m.group(1)) if m else None


def _find_existing_issue(config: ManagerConfig, task: TaskSpec) -> tuple[int | None, str | None]:
    query = f'"task_id: `{task.task_id}`" in:body'
    code, stdout, _ = _run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            config.github.repo,
            "--search",
            query,
            "--state",
            "all",
            "--json",
            "number,url",
            "--limit",
            "1",
        ],
        config.repo_root,
    )
    if code != 0 or not stdout:
        return None, None
    rows = json.loads(stdout)
    if not rows:
        return None, None
    return int(rows[0]["number"]), str(rows[0]["url"])


def ensure_issue(config: ManagerConfig, task: TaskSpec) -> tuple[int | None, str | None]:
    if not github_enabled(config):
        return task.issue_number, task.issue_url
    if not config.github.auto_create_issue:
        return task.issue_number, task.issue_url
    if task.issue_number is not None and task.issue_url:
        return task.issue_number, task.issue_url
    found_number, found_url = _find_existing_issue(config, task)
    if found_number is not None and found_url:
        return found_number, found_url

    body = (
        f"## Task\n{task.prompt}\n\n"
        f"- task_id: `{task.task_id}`\n"
        f"- task_type: `{task.task_type}`\n"
        f"- priority: `{task.priority}`\n"
        f"- scope_paths: `{', '.join(task.scope_paths) if task.scope_paths else 'n/a'}`\n"
        f"- done_when: `{'; '.join(task.done_when_commands) if task.done_when_commands else 'n/a'}`\n"
    )

    args = [
        "gh",
        "issue",
        "create",
        "--repo",
        config.github.repo,
        "--title",
        f"[{task.task_type}] {task.title}",
        "--body",
        body,
        "--label",
        _label_for_task(config, task),
    ]
    for assignee in config.github.assignees:
        args.extend(["--assignee", assignee])

    code, stdout, _ = _run(args, config.repo_root)
    if code != 0:
        return task.issue_number, task.issue_url

    issue_url = stdout.splitlines()[-1].strip()
    issue_number = _extract_number(issue_url)
    return issue_number, issue_url


def ensure_pr(config: ManagerConfig, task: TaskSpec, branch_name: str) -> tuple[int | None, str | None]:
    if not github_enabled(config):
        return task.pr_number, task.pr_url
    if not config.github.auto_create_pr:
        return task.pr_number, task.pr_url

    if task.pr_number is not None and task.pr_url:
        return task.pr_number, task.pr_url

    code, stdout, _ = _run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            config.github.repo,
            "--head",
            branch_name,
            "--state",
            "open",
            "--json",
            "number,url",
            "--limit",
            "1",
        ],
        config.repo_root,
    )
    if code == 0 and stdout:
        rows = json.loads(stdout)
        if rows:
            return int(rows[0]["number"]), str(rows[0]["url"])

    issue_ref = f"\n\nCloses #{task.issue_number}" if task.issue_number else ""
    body = f"Automated task execution for `{task.task_id}`.{issue_ref}"

    args = [
        "gh",
        "pr",
        "create",
        "--repo",
        config.github.repo,
        "--base",
        config.base_branch,
        "--head",
        branch_name,
        "--title",
        f"[{task.task_type}] {task.title}",
        "--body",
        body,
    ]
    if config.github.draft_pr:
        args.append("--draft")

    code, stdout, _ = _run(args, config.repo_root)
    if code != 0:
        return task.pr_number, task.pr_url

    pr_url = stdout.splitlines()[-1].strip()
    pr_number = _extract_number(pr_url)

    if pr_number and config.github.reviewers:
        _run(
            [
                "gh",
                "pr",
                "edit",
                str(pr_number),
                "--repo",
                config.github.repo,
                "--add-reviewer",
                ",".join(config.github.reviewers),
            ],
            config.repo_root,
        )
    return pr_number, pr_url


def try_merge_pr(config: ManagerConfig, pr_number: int) -> bool:
    if not github_enabled(config):
        return False
    if not config.github.auto_merge:
        return False

    method_flag = "--squash"
    if config.github.merge_method == "rebase":
        method_flag = "--rebase"
    if config.github.merge_method == "merge":
        method_flag = "--merge"

    args = [
        "gh",
        "pr",
        "merge",
        str(pr_number),
        "--repo",
        config.github.repo,
        method_flag,
        "--delete-branch",
    ]
    code, _, _ = _run(args, config.repo_root)
    return code == 0

from __future__ import annotations

import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=str(cwd), check=True, text=True, capture_output=True)
    return proc.stdout.strip()


def ensure_branch(repo_root: Path, base_branch: str, branch_name: str) -> None:
    _run(["git", "fetch", "origin", base_branch], cwd=repo_root)
    _run(["git", "branch", "-f", branch_name, f"origin/{base_branch}"], cwd=repo_root)


def ensure_worktree(repo_root: Path, branch_name: str, worktree_path: Path) -> None:
    if worktree_path.exists() and (worktree_path / ".git").exists():
        _run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", "--force", str(worktree_path), branch_name], cwd=repo_root)


def cleanup_worktree(repo_root: Path, worktree_path: Path) -> None:
    if worktree_path.exists():
        _run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)

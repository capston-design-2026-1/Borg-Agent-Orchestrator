from __future__ import annotations

import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=str(cwd), check=True, text=True, capture_output=True)
    return proc.stdout.strip()


def _try_run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, text=True, capture_output=True)


def _resolve_startpoint(repo_root: Path, base_branch: str) -> str:
    # Prefer synced remote base, then local base, then current HEAD.
    remote_ref = f"origin/{base_branch}"
    probe = _try_run(["git", "rev-parse", "--verify", remote_ref], cwd=repo_root)
    if probe.returncode == 0:
        return remote_ref
    probe = _try_run(["git", "rev-parse", "--verify", base_branch], cwd=repo_root)
    if probe.returncode == 0:
        return base_branch
    return "HEAD"


def ensure_branch(repo_root: Path, base_branch: str, branch_name: str) -> None:
    _try_run(["git", "fetch", "origin", base_branch], cwd=repo_root)
    startpoint = _resolve_startpoint(repo_root, base_branch)
    # If the branch is currently checked out in another worktree, avoid force-moving it.
    move = _try_run(["git", "branch", "-f", branch_name, startpoint], cwd=repo_root)
    if move.returncode == 0:
        return
    err = move.stderr.lower()
    if "checked out" in err or "used by worktree" in err:
        return
    exists = _try_run(["git", "rev-parse", "--verify", branch_name], cwd=repo_root)
    if exists.returncode == 0:
        return
    _run(["git", "branch", branch_name, startpoint], cwd=repo_root)


def ensure_worktree(repo_root: Path, branch_name: str, worktree_path: Path) -> None:
    if worktree_path.exists() and (worktree_path / ".git").exists():
        _run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", "--force", str(worktree_path), branch_name], cwd=repo_root)


def cleanup_worktree(repo_root: Path, worktree_path: Path) -> None:
    if worktree_path.exists():
        _run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)

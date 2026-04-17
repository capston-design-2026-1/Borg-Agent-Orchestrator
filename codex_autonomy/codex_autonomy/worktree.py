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


def _is_tracked(path: Path, relpath: str) -> bool:
    probe = _try_run(["git", "ls-files", "--error-unmatch", "--", relpath], cwd=path)
    return probe.returncode == 0


def _sanitize_local_venv(worktree_path: Path) -> None:
    relpath = ".venv"
    venv_path = worktree_path / relpath
    if not _is_tracked(worktree_path, relpath):
        return
    if venv_path.is_symlink() or venv_path.is_file():
        venv_path.unlink(missing_ok=True)
    _run(["git", "rm", "--cached", "--force", "--", relpath], cwd=worktree_path)


def ensure_branch(repo_root: Path, base_branch: str, branch_name: str) -> None:
    _try_run(["git", "fetch", "origin", base_branch], cwd=repo_root)
    _try_run(["git", "fetch", "origin", branch_name], cwd=repo_root)

    existing = _try_run(["git", "rev-parse", "--verify", branch_name], cwd=repo_root)
    if existing.returncode == 0:
        return

    remote_branch = f"origin/{branch_name}"
    remote_exists = _try_run(["git", "rev-parse", "--verify", remote_branch], cwd=repo_root)
    if remote_exists.returncode == 0:
        _run(["git", "branch", "--track", branch_name, remote_branch], cwd=repo_root)
        return

    startpoint = _resolve_startpoint(repo_root, base_branch)
    _run(["git", "branch", branch_name, startpoint], cwd=repo_root)


def ensure_worktree(repo_root: Path, branch_name: str, worktree_path: Path) -> None:
    if worktree_path.exists() and (worktree_path / ".git").exists():
        _run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", "--force", str(worktree_path), branch_name], cwd=repo_root)
    _sanitize_local_venv(worktree_path)
    # Make repo-root virtualenv available inside worktree for relative commands like ./.venv/bin/python.
    root_venv = repo_root / ".venv"
    worktree_venv = worktree_path / ".venv"
    if root_venv.exists() and not worktree_venv.exists():
        worktree_venv.symlink_to(root_venv, target_is_directory=True)


def cleanup_worktree(repo_root: Path, worktree_path: Path) -> None:
    if worktree_path.exists():
        _run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)

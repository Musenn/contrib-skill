"""git 命令调用封装。"""
from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def run_git(repo_path: Path | str, *args: str) -> str:
    cmd = ["git", "-C", str(repo_path), *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} 失败: {result.stderr.strip()}")
    return result.stdout


def is_git_repo(repo_path: Path | str) -> bool:
    try:
        out = run_git(repo_path, "rev-parse", "--is-inside-work-tree")
        return out.strip() == "true"
    except (GitError, FileNotFoundError):
        return False

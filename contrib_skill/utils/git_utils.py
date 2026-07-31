"""git 命令调用封装。"""
from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def run_git(repo_path: Path | str, *args: str) -> str:
    cmd = [
        "git",
        "-c", "i18n.logOutputEncoding=UTF-8",
        "-c", "core.quotepath=false",
        "-C", str(repo_path),
        *args,
    ]
    # Git stores commit metadata as UTF-8. Relying on Windows' active code page
    # makes Chinese commit messages crash the subprocess reader thread.
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} 失败: {result.stderr.strip()}")
    return result.stdout


def is_git_repo(repo_path: Path | str) -> bool:
    try:
        out = run_git(repo_path, "rev-parse", "--is-inside-work-tree")
        return out.strip() == "true"
    except (GitError, FileNotFoundError):
        return False

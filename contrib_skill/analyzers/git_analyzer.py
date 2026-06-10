"""GitAnalyzer：提取 commit 历史、numstat、作者聚合统计。全部为事实层数据。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import AuthorStats, Commit, FileStat
from ..utils.file_utils import module_of_path
from ..utils.git_utils import is_git_repo, run_git
from ..utils.time_utils import is_night, is_weekend, month_key

_FIELD_SEP = "\x1f"
_RECORD_SEP = "\x1e"


class GitAnalyzer:
    def __init__(self, repo_path: Path | str):
        self.repo_path = Path(repo_path).resolve()
        if not is_git_repo(self.repo_path):
            raise ValueError(f"{self.repo_path} 不是 Git 仓库")

    def collect_commits(
        self,
        base: Optional[str] = None,
        branch: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        max_commits: Optional[int] = None,
    ) -> list[Commit]:
        """读取 commit 列表（含逐文件 numstat），按时间倒序返回。"""
        pretty = (
            f"--pretty=format:{_RECORD_SEP}%H{_FIELD_SEP}%h{_FIELD_SEP}%an"
            f"{_FIELD_SEP}%ae{_FIELD_SEP}%ad{_FIELD_SEP}%P{_FIELD_SEP}%s"
        )
        args = ["log", "--numstat", "--date=iso-strict", pretty]
        if since:
            args.append(f"--since={since}")
        if until:
            args.append(f"--until={until}")
        if max_commits:
            args.append(f"-n{max_commits}")
        if base and branch:
            args.append(f"{base}..{branch}")
        elif branch:
            args.append(branch)

        out = run_git(self.repo_path, *args)
        return self._parse_log(out)

    @staticmethod
    def _parse_log(output: str) -> list[Commit]:
        commits: list[Commit] = []
        for record in output.split(_RECORD_SEP):
            record = record.strip("\n")
            if not record.strip():
                continue
            lines = record.split("\n")
            header = lines[0].split(_FIELD_SEP)
            if len(header) < 7:
                continue
            chash, short, name, email, date_str, parents, message = header[:7]
            files: list[FileStat] = []
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) != 3:
                    continue
                add_s, del_s, path = parts
                binary = add_s == "-" or del_s == "-"
                files.append(
                    FileStat(
                        path=path,
                        additions=0 if binary else int(add_s),
                        deletions=0 if binary else int(del_s),
                        binary=binary,
                    )
                )
            commits.append(
                Commit(
                    hash=chash,
                    short_hash=short,
                    author_name=name,
                    author_email=email,
                    date=datetime.fromisoformat(date_str),
                    message=message,
                    is_merge=len(parents.split()) > 1,
                    files=files,
                )
            )
        return commits

    @staticmethod
    def aggregate_authors(commits: list[Commit]) -> dict[str, AuthorStats]:
        """按作者（邮箱小写为主键）聚合统计。"""
        stats: dict[str, AuthorStats] = {}
        for c in commits:
            key = c.author_email.lower() or c.author_name.lower()
            st = stats.get(key)
            if st is None:
                st = AuthorStats(name=c.author_name, email=c.author_email.lower())
                stats[key] = st
            if c.author_name not in st.aliases and c.author_name != st.name:
                st.aliases.append(c.author_name)
            st.commit_count += 1
            if c.is_merge:
                st.merge_count += 1
            st.additions += c.additions
            st.deletions += c.deletions
            if st.first_commit_date is None or c.date < st.first_commit_date:
                st.first_commit_date = c.date
            if st.last_commit_date is None or c.date > st.last_commit_date:
                st.last_commit_date = c.date
            for f in c.files:
                st.file_counts[f.path] = st.file_counts.get(f.path, 0) + 1
                mod = module_of_path(f.path)
                st.module_counts[mod] = st.module_counts.get(mod, 0) + 1
            mk = month_key(c.date)
            st.monthly_activity[mk] = st.monthly_activity.get(mk, 0) + 1
            if is_weekend(c.date):
                st.weekend_commits += 1
            else:
                st.weekday_commits += 1
            if is_night(c.date):
                st.night_commits += 1
            else:
                st.daytime_commits += 1
            st.commit_hashes.append(c.hash)
        return stats

    @staticmethod
    def match_author(commit: Commit, author: str) -> bool:
        """按名称或邮箱（不区分大小写、支持子串）匹配作者。"""
        needle = author.lower()
        return needle in commit.author_name.lower() or needle in commit.author_email.lower()

"""Git 原始数据模型：commit、文件变更、作者聚合统计。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FileStat(BaseModel):
    path: str
    additions: int = 0
    deletions: int = 0
    binary: bool = False


class Commit(BaseModel):
    hash: str
    short_hash: str
    author_name: str
    author_email: str
    date: datetime
    message: str
    is_merge: bool = False
    files: list[FileStat] = Field(default_factory=list)

    @property
    def additions(self) -> int:
        return sum(f.additions for f in self.files)

    @property
    def deletions(self) -> int:
        return sum(f.deletions for f in self.files)

    @property
    def changed_files(self) -> list[str]:
        return [f.path for f in self.files]


class AuthorStats(BaseModel):
    """单个作者在仓库内的聚合统计（事实层，不含推断）。"""

    name: str
    email: str
    aliases: list[str] = Field(default_factory=list)
    commit_count: int = 0
    merge_count: int = 0
    additions: int = 0
    deletions: int = 0
    first_commit_date: Optional[datetime] = None
    last_commit_date: Optional[datetime] = None
    file_counts: dict[str, int] = Field(default_factory=dict)
    module_counts: dict[str, int] = Field(default_factory=dict)
    monthly_activity: dict[str, int] = Field(default_factory=dict)
    weekday_commits: int = 0
    weekend_commits: int = 0
    daytime_commits: int = 0
    night_commits: int = 0
    commit_hashes: list[str] = Field(default_factory=list)

    @property
    def active_days(self) -> int:
        if self.first_commit_date and self.last_commit_date:
            return (self.last_commit_date - self.first_commit_date).days + 1
        return 0

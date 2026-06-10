"""分析参数配置。"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

MODES = ("strict", "resume", "interview", "audit", "full")
LANGUAGES = ("zh", "en")


class AnalyzeOptions(BaseModel):
    repo: str = "."
    author: Optional[str] = None
    all_authors: bool = False
    base: Optional[str] = None
    branch: Optional[str] = None
    since: Optional[str] = None
    until: Optional[str] = None
    mode: str = "full"
    target_role: str = ""
    language: str = "zh"
    output: str = "./contrib_output"
    max_commits: int = 2000
    include_diff: bool = False
    strict: bool = False

    def normalized_mode(self) -> str:
        return self.mode if self.mode in MODES else "full"

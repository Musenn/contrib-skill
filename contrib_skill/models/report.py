"""完整分析结果容器：evidence.json 的顶层结构。"""
from __future__ import annotations

from pydantic import BaseModel, Field

from .evidence import (
    ArchitectureEvidence,
    AuthorEvidence,
    BusinessContextEvidence,
    GitCommitEvidence,
    ProjectEvidence,
    ResumeClaim,
    TechStackEvidence,
)


class AnalysisResult(BaseModel):
    project: ProjectEvidence
    tech_stack: TechStackEvidence
    architecture: ArchitectureEvidence
    business: BusinessContextEvidence
    commits: list[GitCommitEvidence] = Field(default_factory=list)
    authors: list[AuthorEvidence] = Field(default_factory=list)
    target_author: str = ""
    resume_claims: list[ResumeClaim] = Field(default_factory=list)
    analysis_params: dict = Field(default_factory=dict)

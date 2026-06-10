"""证据链数据模型：所有分析结论必须落到这些结构上，并区分事实与推断。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# 置信度等级统一使用：高 / 中 / 低
CONFIDENCE_HIGH = "高"
CONFIDENCE_MEDIUM = "中"
CONFIDENCE_LOW = "低"

# 简历表述风险等级
RISK_SAFE = "safe"
RISK_NEEDS_CONFIRMATION = "needs_confirmation"
RISK_RISKY = "risky"


class GitCommitEvidence(BaseModel):
    hash: str
    short_hash: str
    author_name: str
    author_email: str
    date: datetime
    message: str
    changed_files: list[str] = Field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    file_stats: list[dict] = Field(default_factory=list)
    is_merge: bool = False
    inferred_type: str = "unknown"
    type_confidence: str = CONFIDENCE_LOW
    changed_modules: list[str] = Field(default_factory=list)
    possible_reason: str = ""
    possible_impact: str = ""
    evidence_keywords: list[str] = Field(default_factory=list)
    risk_notes: str = ""


class TechStackEvidence(BaseModel):
    languages: dict[str, int] = Field(default_factory=dict)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    middlewares: list[str] = Field(default_factory=list)
    build_tools: list[str] = Field(default_factory=list)
    deployment: list[str] = Field(default_factory=list)
    test_tools: list[str] = Field(default_factory=list)
    possible_architecture_style: str = ""
    evidence_files: list[str] = Field(default_factory=list)


class ArchitectureEvidence(BaseModel):
    architecture_style: str = "无法从代码中确定完整架构"
    module_map: dict[str, list[str]] = Field(default_factory=dict)
    layer_analysis: list[str] = Field(default_factory=list)
    dependency_observations: list[str] = Field(default_factory=list)
    architecture_strengths: list[str] = Field(default_factory=list)
    architecture_risks: list[str] = Field(default_factory=list)
    confidence: str = CONFIDENCE_LOW


class BusinessContextEvidence(BaseModel):
    inferred_domain: str = "通用工具项目"
    project_goal: str = ""
    solved_problem: str = ""
    target_users: str = ""
    core_business_flow: str = ""
    confidence: str = CONFIDENCE_LOW
    missing_information_questions: list[str] = Field(default_factory=list)
    evidence_sources: list[str] = Field(default_factory=list)


class ProjectEvidence(BaseModel):
    repo_path: str
    project_name: str
    languages: dict[str, int] = Field(default_factory=dict)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    middlewares: list[str] = Field(default_factory=list)
    deployment: list[str] = Field(default_factory=list)
    architecture_style: str = ""
    inferred_domain: str = ""
    confidence: str = CONFIDENCE_LOW


class AuthorEvidence(BaseModel):
    author_name: str
    author_email: str
    commit_count: int = 0
    first_commit_date: Optional[datetime] = None
    last_commit_date: Optional[datetime] = None
    total_additions: int = 0
    total_deletions: int = 0
    main_files: list[str] = Field(default_factory=list)
    main_modules: list[str] = Field(default_factory=list)
    change_type_distribution: dict[str, int] = Field(default_factory=dict)
    activity_timeline: dict[str, int] = Field(default_factory=dict)
    weekday_commits: int = 0
    weekend_commits: int = 0
    daytime_commits: int = 0
    night_commits: int = 0
    is_project_initializer: bool = False
    touches_core_modules: bool = False
    does_late_maintenance: bool = False
    contribution_roles: list[str] = Field(default_factory=list)
    contribution_level: str = "中等"
    module_ownership: dict[str, str] = Field(default_factory=dict)
    evidence_commits: list[str] = Field(default_factory=list)


class ResumeClaim(BaseModel):
    text: str
    risk_level: str = RISK_NEEDS_CONFIRMATION
    support_evidence: list[str] = Field(default_factory=list)
    needs_user_confirmation: bool = False
    forbidden_reason: str = ""

"""AuthorProfiler：聚合指定作者的贡献画像，输出角色、含金量等级与证据链。

含金量不按代码行数线性计算，而是 变更类型权重 × 文件路径权重 的加权和，
再与仓库内其他作者对比得出等级（很高/较高/中等/较低/低）。
"""
from __future__ import annotations

from ..models import (
    AuthorEvidence,
    AuthorStats,
    Commit,
    GitCommitEvidence,
)
from ..utils.text_utils import top_n

TYPE_WEIGHTS = {
    "architecture": 1.0,
    "feature": 0.9,
    "performance": 0.9,
    "security": 0.85,
    "bugfix": 0.8,
    "refactor": 0.75,
    "test": 0.7,
    "config": 0.65,
    "build": 0.65,
    "ci": 0.65,
    "dependency": 0.65,
    "docs": 0.4,
    "unknown": 0.3,
    "style": 0.1,
}

PATH_WEIGHTS = [
    ("service", 1.0),
    ("core", 1.0),
    ("controller", 0.85),
    ("api", 0.85),
    ("repository", 0.75),
    ("mapper", 0.75),
    ("dao", 0.75),
    ("security", 0.8),
    ("auth", 0.8),
    ("config", 0.8),
    ("model", 0.7),
    ("entity", 0.7),
    ("domain", 0.7),
    ("test", 0.65),
    ("docs", 0.35),
    ("assets", 0.2),
    ("style", 0.2),
]

_DEFAULT_PATH_WEIGHT = 0.6

CORE_PATH_HINTS = ("service", "core", "controller", "api", "domain")

LEVELS = ["低", "较低", "中等", "较高", "很高"]


def path_weight(path: str) -> float:
    low = path.lower()
    for hint, weight in PATH_WEIGHTS:
        if hint in low:
            return weight
    return _DEFAULT_PATH_WEIGHT


def commit_score(ev: GitCommitEvidence) -> float:
    """单个 commit 的含金量分：类型权重 × 涉及文件的最高路径权重。merge 不计分。"""
    if ev.is_merge:
        return 0.0
    type_w = TYPE_WEIGHTS.get(ev.inferred_type, 0.3)
    file_w = max((path_weight(p) for p in ev.changed_files), default=_DEFAULT_PATH_WEIGHT)
    return type_w * file_w


def build_author_evidence(
    author_key: str,
    stats: AuthorStats,
    author_commit_evidence: list[GitCommitEvidence],
    all_commits: list[Commit],
    all_scores: dict[str, float],
) -> AuthorEvidence:
    ev = AuthorEvidence(
        author_name=stats.name,
        author_email=stats.email,
        commit_count=stats.commit_count,
        first_commit_date=stats.first_commit_date,
        last_commit_date=stats.last_commit_date,
        total_additions=stats.additions,
        total_deletions=stats.deletions,
        main_files=top_n(stats.file_counts, 10),
        main_modules=top_n(stats.module_counts, 6),
        activity_timeline=dict(sorted(stats.monthly_activity.items())),
        weekday_commits=stats.weekday_commits,
        weekend_commits=stats.weekend_commits,
        daytime_commits=stats.daytime_commits,
        night_commits=stats.night_commits,
        evidence_commits=[e.short_hash for e in author_commit_evidence[:30]],
    )

    # 变更类型分布
    for e in author_commit_evidence:
        ev.change_type_distribution[e.inferred_type] = (
            ev.change_type_distribution.get(e.inferred_type, 0) + 1
        )

    # 是否参与项目初始化：在仓库最早 10% 提交（至少前 5 个）中出现，
    # 且这些提交含依赖/配置/架构类文件
    ev.is_project_initializer = _check_initializer(stats, all_commits)

    # 是否触达核心模块
    ev.touches_core_modules = any(
        any(h in f.lower() for h in CORE_PATH_HINTS) for f in stats.file_counts
    )

    # 是否参与后期维护：最近提交落在仓库最后 20% 时间段
    ev.does_late_maintenance = _check_late_maintenance(stats, all_commits)

    ev.contribution_roles = _infer_roles(ev, stats)
    ev.contribution_level = _contribution_level(author_key, all_scores)
    return ev


def compute_all_scores(
    evidence_by_author: dict[str, list[GitCommitEvidence]]
) -> dict[str, float]:
    return {
        key: sum(commit_score(e) for e in evs)
        for key, evs in evidence_by_author.items()
    }


def _check_initializer(stats: AuthorStats, all_commits: list[Commit]) -> bool:
    if not all_commits or stats.first_commit_date is None:
        return False
    ordered = sorted(all_commits, key=lambda c: c.date)
    head = ordered[: max(5, len(ordered) // 10)]
    early_hashes = {c.hash for c in head}
    early_own = [c for c in head if c.hash in set(stats.commit_hashes)]
    if not early_own:
        return False
    init_hints = ("pom.xml", "package.json", "pyproject.toml", "requirements.txt",
                  "go.mod", "cargo.toml", "build.gradle", "dockerfile", ".gitignore",
                  "config", "readme")
    for c in early_own:
        if any(any(h in f.path.lower() for h in init_hints) for f in c.files):
            return True
    # 提交了仓库的第一个 commit 也视为初始化者
    return ordered[0].hash in set(stats.commit_hashes)


def _check_late_maintenance(stats: AuthorStats, all_commits: list[Commit]) -> bool:
    if not all_commits or stats.last_commit_date is None:
        return False
    dates = sorted(c.date for c in all_commits)
    start, end = dates[0], dates[-1]
    span = (end - start).total_seconds()
    if span <= 0:
        return True
    cutoff = start + (end - start) * 4 / 5
    return stats.last_commit_date >= cutoff


def _infer_roles(ev: AuthorEvidence, stats: AuthorStats) -> list[str]:
    roles: list[str] = []
    dist = ev.change_type_distribution
    total = max(1, sum(dist.values()))

    if ev.is_project_initializer:
        roles.append("项目初始化者")
    if ev.touches_core_modules and dist.get("feature", 0) >= 2:
        roles.append("核心业务开发者")
    if dist.get("bugfix", 0) / total >= 0.3:
        roles.append("Bug 修复者")
    if dist.get("refactor", 0) + dist.get("architecture", 0) >= 2:
        roles.append("架构/重构参与者")
    if dist.get("config", 0) + dist.get("ci", 0) + dist.get("dependency", 0) >= 2:
        roles.append("配置部署维护者")
    if dist.get("test", 0) >= 2:
        roles.append("测试质量保障者")
    if dist.get("docs", 0) / total >= 0.3:
        roles.append("文档维护者")

    file_text = " ".join(stats.file_counts).lower()
    if any(h in file_text for h in (".vue", ".tsx", ".jsx", "components/", "pages/")):
        roles.append("前端开发者")
    if any(h in file_text for h in ("controller", "service", "mapper", "repository",
                                    "api/", "server/")):
        roles.append("后端开发者")
    if any(h in file_text for h in ("model/", "train", "inference", "prompt",
                                    "agent", "llm", "embedding")):
        roles.append("AI/算法模块参与者")
    if any(h in file_text for h in ("etl", "pipeline", "spark", "flink", "数据")):
        roles.append("数据处理开发者")

    if not roles:
        roles.append("模块维护者（具体角色证据不足）")
    return roles


def _contribution_level(author_key: str, all_scores: dict[str, float]) -> str:
    """与仓库内其他作者比较，给出粗粒度等级，避免假精度。"""
    score = all_scores.get(author_key, 0.0)
    total = sum(all_scores.values())
    if total <= 0:
        return "中等"
    share = score / total
    if len(all_scores) == 1:
        # 单人仓库：按绝对体量粗略分级
        if score >= 20:
            return "很高"
        if score >= 8:
            return "较高"
        if score >= 3:
            return "中等"
        return "较低"
    if share >= 0.6:
        return "很高"
    if share >= 0.35:
        return "较高"
    if share >= 0.15:
        return "中等"
    if share >= 0.05:
        return "较低"
    return "低"

"""Generate a paste-ready resume project entry backed by Git evidence."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from ..analyzers.claim_risk_checker import check_claim
from ..models import (
    AuthorEvidence,
    BusinessContextEvidence,
    GitCommitEvidence,
    ProjectEvidence,
    RISK_SAFE,
    ResumeClaim,
    TechStackEvidence,
)

METRIC_SUGGESTIONS = [
    "接口响应时间 / P95 / P99（需压测或监控数据）",
    "吞吐量、QPS 或批处理耗时（需压测记录）",
    "故障率、超时率或缺陷数量变化",
    "测试覆盖率与自动化用例数量",
    "真实用户量、数据量级与线上运行时长",
]

_ROLE_TECH_HINTS = {
    "java": ["Spring Boot", "Spring Security", "MyBatis", "MyBatis-Plus", "JPA",
             "MySQL", "Redis", "Kafka"],
    "前端": ["React", "Vue", "Angular", "Next.js", "Nuxt", "TypeScript", "Vite"],
    "ai": ["LangChain", "LlamaIndex", "Transformers", "PyTorch", "TensorFlow",
           "FastAPI"],
    "算法": ["PyTorch", "TensorFlow", "Transformers"],
    "python": ["FastAPI", "Flask", "Django", "MySQL", "Redis"],
    "go": ["Gin", "Echo", "Gorm"],
    "全栈": [],
}

_CONVENTIONAL_PREFIX = re.compile(
    r"^(?:feat(?:ure)?|fix|bugfix|hotfix|perf|performance|refactor|test|tests|"
    r"docs?|ci|build|chore|style|security|sec|config|init)(?:\([^)]*\))?[!：:]?\s*",
    re.IGNORECASE,
)

_TYPE_ORDER = (
    "architecture", "feature", "security", "performance", "refactor",
    "bugfix", "test", "ci", "config", "dependency", "build",
)


def generate_resume(
    author_ev: AuthorEvidence,
    author_commits: list[GitCommitEvidence],
    tech: TechStackEvidence,
    target_role: str = "",
    strict: bool = False,
    project: ProjectEvidence | None = None,
    business: BusinessContextEvidence | None = None,
) -> dict:
    """Build one concise project entry, then keep evidence outside the paste area."""
    selected_groups = _select_resume_groups(author_commits, max_items=4)
    ready_bullets = [
        _claim_from_group(group, author_ev, tech)
        for group in selected_groups
    ]
    if strict:
        ready_bullets = [c for c in ready_bullets if c.risk_level == RISK_SAFE]

    project_entry = {
        "project_name": project.project_name if project else "项目名称",
        "subtitle": _project_subtitle(business),
        "period": _period(author_ev.first_commit_date, author_ev.last_commit_date),
        "role": _resume_role(author_ev),
        "tech_stack": _tech_string(tech),
        "summary": _project_summary(business),
    }

    # Keep the former keys for callers that consumed the Python return value.
    # The Markdown output intentionally presents only one primary version.
    return {
        "project_entry": project_entry,
        "ready_bullets": ready_bullets,
        "confirmation_prompts": _confirmation_prompts(
            [commit for group in selected_groups for commit in group], business
        ),
        "target_role_notes": _target_role_notes(target_role, tech),
        "metric_suggestions": METRIC_SUGGESTIONS,
        "conservative": ready_bullets,
        "standard": ready_bullets,
        "enhanced": ready_bullets,
        "star": [],
        "english": [],
    }


def _select_resume_groups(
    commits: list[GitCommitEvidence], max_items: int
) -> list[list[GitCommitEvidence]]:
    eligible = [
        c for c in commits
        if not c.is_merge and c.inferred_type in _TYPE_ORDER
    ]
    by_type = {
        ctype: sorted(
            (c for c in eligible if c.inferred_type == ctype),
            key=lambda c: c.date,
        )
        for ctype in _TYPE_ORDER
    }

    selected: list[list[GitCommitEvidence]] = []
    used_hashes: set[str] = set()

    def add(group: list[GitCommitEvidence]) -> None:
        fresh = [c for c in group if c.hash not in used_hashes]
        if fresh and len(selected) < max_items:
            selected.append(fresh)
            used_hashes.update(c.hash for c in fresh)

    # Establish the project, show up to two concrete features, then reserve room
    # for a different engineering dimension such as security or performance.
    if by_type["architecture"]:
        add([by_type["architecture"][0]])
    for group in _group_feature_commits(by_type["feature"])[:2]:
        add(group)
    for ctype in ("security", "performance", "refactor", "bugfix", "test",
                  "ci", "config", "dependency", "build"):
        if by_type[ctype]:
            add([by_type[ctype][0]])

    # Fill any remaining slots deterministically without duplicating a commit.
    for ctype in _TYPE_ORDER:
        for commit in by_type[ctype]:
            add([commit])

    # A documentation-only or unconventional repository should still produce a
    # truthful, modest entry instead of an empty file.
    if not selected:
        fallback = [c for c in commits if not c.is_merge]
        selected = [[c] for c in sorted(fallback, key=lambda c: c.date)[:max_items]]
    return selected


def _group_feature_commits(
    commits: list[GitCommitEvidence],
) -> list[list[GitCommitEvidence]]:
    groups: dict[str, list[GitCommitEvidence]] = {}
    for commit in commits:
        groups.setdefault(_commit_topic(commit), []).append(commit)
    return list(groups.values())


def _commit_topic(commit: GitCommitEvidence) -> str:
    generic = {"index", "main", "app", "application", "config", "utils", "common"}
    suffixes = (
        "_controller", "_service", "_repository", "_repo", "_handler",
        "_api", "_client", "_model", "_entity", "_test", "_tests",
    )
    for file_path in commit.changed_files:
        stem = Path(file_path).stem.lower()
        for suffix in suffixes:
            if stem.endswith(suffix):
                stem = stem[:-len(suffix)]
                break
        if stem and stem not in generic:
            return stem
    words = re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]+", _clean_commit_message(commit.message))
    return words[0].lower() if words else commit.short_hash


def _claim_from_group(
    commits: list[GitCommitEvidence],
    author_ev: AuthorEvidence,
    tech: TechStackEvidence,
) -> ResumeClaim:
    commit = commits[0]
    summaries = [_clean_commit_message(item.message) for item in commits]
    summary = "、".join(dict.fromkeys(summaries))
    modules = sorted({module for item in commits for module in item.changed_modules})
    verb = _role_verb(author_ev, modules)

    if commit.inferred_type == "architecture" or _looks_like_initialization(summary):
        if _looks_like_initialization(summary):
            action = "完成项目骨架、依赖与基础配置初始化"
        else:
            action = summary
        text = (
            f"参与项目初始化与基础架构搭建，{action}；"
            f"基于 {_architecture_tech_string(tech)} 建立可持续迭代的工程基线。"
        )
    elif commit.inferred_type == "feature":
        text = f"{verb}核心功能开发，{summary}，完善项目关键业务链路。"
    elif commit.inferred_type == "security":
        text = f"{verb}安全能力建设，{summary}，加强关键链路的认证、授权或数据保护。"
    elif commit.inferred_type == "performance":
        text = f"围绕关键链路开展性能优化，{summary}，减少重复计算或资源访问开销。"
    elif commit.inferred_type == "refactor":
        text = f"{verb}代码重构，{summary}，改善模块边界与后续维护效率。"
    elif commit.inferred_type == "bugfix":
        text = f"参与稳定性治理，{summary}，完善异常路径和边界输入处理。"
    elif commit.inferred_type == "test":
        text = f"补充质量保障能力，{summary}，覆盖关键场景的自动化回归。"
    elif commit.inferred_type in {"ci", "config", "dependency", "build"}:
        text = f"完善工程化建设，{summary}，提升构建、配置与交付流程的可维护性。"
    else:
        text = f"参与项目迭代与维护，{summary}。"

    evidence = [item for commit in commits for item in _evidence_list(commit)]
    return check_claim(text, author_ev, evidence)


def _role_verb(author_ev: AuthorEvidence, modules: list[str]) -> str:
    levels = [
        author_ev.module_ownership[m]
        for m in modules
        if m != "(root)" and m in author_ev.module_ownership
    ]
    if not levels:
        return "参与"
    rank = {"assistant": 0, "participant": 1, "maintainer": 2, "deep": 3, "owner": 4}
    weakest = min(rank.get(level, 1) for level in levels)
    if weakest >= 4:
        return "主要负责"
    if weakest >= 3:
        return "深度参与"
    if weakest >= 2:
        return "负责"
    return "参与"


def _clean_commit_message(message: str) -> str:
    text = _CONVENTIONAL_PREFIX.sub("", message.strip())
    text = re.sub(r"\s+", " ", text).strip(" ;；,.，。")
    return text or "完成相关功能与工程调整"


def _looks_like_initialization(text: str) -> bool:
    low = text.lower()
    return any(word in low for word in (
        "init", "scaffold", "初始化", "脚手架", "项目骨架", "搭建项目",
    ))


def _evidence_list(commit: GitCommitEvidence) -> list[str]:
    files = "、".join(commit.changed_files[:4]) or "无文件路径"
    return [
        f"commit {commit.short_hash} [{commit.inferred_type}] "
        f"{commit.message}；文件：{files}"
    ]


def _tech_items(tech: TechStackEvidence) -> list[str]:
    languages = [
        name for name, _ in
        sorted(tech.languages.items(), key=lambda item: -item[1])[:2]
    ]
    candidates = (
        languages + tech.frameworks + tech.databases + tech.middlewares
        + tech.build_tools + tech.deployment + tech.test_tools
    )
    out: list[str] = []
    for item in candidates:
        if item and item not in out:
            out.append(item)
        if len(out) >= 8:
            break
    return out


def _tech_string(tech: TechStackEvidence) -> str:
    return " · ".join(_tech_items(tech)) or "仓库现有技术栈"


def _architecture_tech_string(tech: TechStackEvidence) -> str:
    candidates = tech.frameworks + tech.databases + tech.middlewares
    if not candidates:
        candidates = [
            name for name, _ in
            sorted(tech.languages.items(), key=lambda item: -item[1])
        ]
    return " + ".join(dict.fromkeys(candidates[:5])) or "仓库现有技术栈"


def _project_subtitle(business: BusinessContextEvidence | None) -> str:
    if not business or not business.inferred_domain:
        return "代码贡献项目"
    return business.inferred_domain.split("（", 1)[0].strip()


def _project_summary(business: BusinessContextEvidence | None) -> str:
    if not business:
        return "基于仓库代码与 Git 历史还原的项目贡献。"
    text = business.project_goal.strip()
    for prefix in ("README 描述（事实）：", "推断："):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!\[[^]]*]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", text)
    text = re.sub(r"(?:\*\*|__)(.+?)(?:\*\*|__)", r"\1", text)
    text = re.sub(r"(?:\*|_)(.+?)(?:\*|_)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip(" #")
    if not text or "无 README" in text:
        return f"围绕{_project_subtitle(business)}场景建设的工程项目。"
    return text[:180]


def _period(start: datetime | None, end: datetime | None) -> str:
    if not start and not end:
        return "时间待补充"
    if start and end:
        return f"{start:%Y.%m} — {end:%Y.%m}"
    value = start or end
    assert value is not None
    return f"{value:%Y.%m}"


def _resume_role(author_ev: AuthorEvidence) -> str:
    levels = set(author_ev.module_ownership.values())
    if "owner" in levels:
        return "核心模块主要负责人"
    if author_ev.is_project_initializer and author_ev.touches_core_modules:
        return "项目初始化与核心功能开发"
    if "deep" in levels:
        return "核心模块深度参与"
    if "maintainer" in levels:
        return "模块开发与维护"
    return "功能开发参与"


def _confirmation_prompts(
    commits: list[GitCommitEvidence],
    business: BusinessContextEvidence | None,
) -> list[str]:
    prompts = [
        "确认项目性质与使用场景：真实上线、公司内部使用、开源项目，还是课程/练习项目。",
        "确认个人角色与团队边界：团队人数、本人负责范围，以及是否可使用“主导/主要负责”。",
        "补充真实规模：用户量、数据量、QPS、运行时长或 star；没有可靠数据就不要填写。",
    ]
    types = {c.inferred_type for c in commits}
    if "performance" in types:
        prompts.append("如有压测或监控记录，补充性能优化前后的 P95/P99、吞吐量或资源消耗。")
    if "test" in types:
        prompts.append("如有测试报告，补充自动化用例数量、覆盖率或回归耗时变化。")
    if business and business.target_users and "推断" not in business.target_users:
        prompts.append(f"核对目标用户描述：{business.target_users}")
    return prompts[:5]


def _target_role_notes(target_role: str, tech: TechStackEvidence) -> list[str]:
    if not target_role:
        return []
    role_low = target_role.lower()
    matched: list[str] = []
    available = _tech_items(tech)
    for key, hints in _ROLE_TECH_HINTS.items():
        if key in role_low:
            matched = [item for item in hints if item in available]
            break
    if matched:
        return [
            f"面向「{target_role}」：优先保留 {', '.join(matched)} 相关成果，"
            "并在面试中准备对应的设计取舍与问题排查过程。"
        ]
    return [
        f"仓库技术栈与「{target_role}」的典型要求匹配度有限；"
        "应如实呈现现有技术，不包装不存在的经验。"
    ]

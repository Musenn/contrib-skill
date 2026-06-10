"""ResumeGenerator：基于证据生成多版本简历表述，每条都经过 ClaimRiskChecker。"""
from __future__ import annotations

from ..analyzers.claim_risk_checker import check_claim, verb_for_module
from ..models import (
    AuthorEvidence,
    GitCommitEvidence,
    RISK_SAFE,
    ResumeClaim,
    TechStackEvidence,
)

METRIC_SUGGESTIONS = [
    "接口响应时间变化（需有压测或监控数据）",
    "bug 数量 / 故障率下降情况",
    "测试覆盖率提升幅度",
    "用户量 / 数据量级",
    "QPS / 并发量（需有压测记录）",
    "部署环境（测试 / 预发 / 生产）",
    "线上使用情况与运行时长",
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

_VERB_EN = {
    "主要负责": "Took primary responsibility for",
    "深度参与": "Was deeply involved in",
    "负责该模块部分开发与维护": "Developed and maintained parts of",
    "参与": "Contributed to",
    "协助": "Assisted in",
}

_TYPE_LABEL = {
    "feature": "功能开发",
    "bugfix": "缺陷修复",
    "refactor": "重构",
    "performance": "性能相关改动",
    "security": "安全相关改动",
    "test": "测试补充",
    "docs": "文档维护",
    "config": "配置与部署调整",
    "ci": "CI 维护",
    "dependency": "依赖管理",
    "architecture": "基础架构搭建",
    "build": "构建调整",
    "style": "样式调整",
    "unknown": "其他改动",
}


def generate_resume(
    author_ev: AuthorEvidence,
    author_commits: list[GitCommitEvidence],
    tech: TechStackEvidence,
    target_role: str = "",
    strict: bool = False,
) -> dict:
    # (root) 是「仓库根目录散落文件」的占位，不构成业务模块，仅在没有其他模块时保留
    modules = [m for m in author_ev.main_modules if m != "(root)"][:4]
    if not modules and "(root)" in author_ev.main_modules:
        modules = ["(root)"]
    tech_str = _tech_string(tech)
    tech_str_en = _tech_string_en(tech)

    conservative: list[ResumeClaim] = []
    standard: list[ResumeClaim] = []
    enhanced: list[ResumeClaim] = []
    english: list[ResumeClaim] = []
    star: list[dict] = []

    for module in modules:
        mod_commits = [e for e in author_commits if module in e.changed_modules]
        if not mod_commits:
            continue
        evidence = _evidence_list(module, mod_commits)
        work_desc = _work_description(mod_commits)
        verb = verb_for_module(author_ev, module)

        # 保守真实版：一律用「参与」
        conservative.append(
            check_claim(
                f"参与 {module} 模块的开发与维护，{work_desc}",
                author_ev, evidence,
            )
        )
        # 标准求职版：按模块归属等级用词
        standard.append(
            check_claim(
                f"{verb} {module} 模块，基于 {tech_str}，{work_desc}",
                author_ev, evidence,
            )
        )
        # 强化表达版：仅在归属等级允许时加强，不凭空拔高
        enhanced.append(
            check_claim(
                _enhanced_text(verb, module, tech_str, work_desc, author_ev),
                author_ev, evidence,
            )
        )
        # 英文版
        en_verb = _VERB_EN.get(verb, "Contributed to")
        english.append(
            check_claim(
                f"{en_verb} the {module} module ({tech_str_en}); "
                f"work covered {_work_description_en(mod_commits)}.",
                author_ev, evidence,
            )
        )
        star.append(_star_entry(module, verb, tech_str, mod_commits, evidence))

    if strict:
        conservative = [c for c in conservative if c.risk_level == RISK_SAFE]
        standard = [c for c in standard if c.risk_level == RISK_SAFE]
        enhanced = [c for c in enhanced if c.risk_level == RISK_SAFE]
        english = [c for c in english if c.risk_level == RISK_SAFE]

    return {
        "conservative": conservative,
        "standard": standard,
        "enhanced": enhanced,
        "star": star,
        "english": english,
        "target_role_notes": _target_role_notes(target_role, tech),
        "metric_suggestions": METRIC_SUGGESTIONS,
    }


def _tech_string(tech: TechStackEvidence) -> str:
    parts = tech.frameworks[:3] + tech.databases[:2] + tech.middlewares[:2]
    return "、".join(parts) if parts else "项目现有技术栈"


def _tech_string_en(tech: TechStackEvidence) -> str:
    parts = tech.frameworks[:3] + tech.databases[:2] + tech.middlewares[:2]
    return ", ".join(parts) if parts else "the project's existing tech stack"


def _evidence_list(module: str, commits: list[GitCommitEvidence]) -> list[str]:
    out = []
    for e in commits[:5]:
        files = ", ".join(e.changed_files[:3])
        out.append(f"commit {e.short_hash}（{e.inferred_type}）：{files}")
    return out


def _work_description(commits: list[GitCommitEvidence]) -> str:
    counts: dict[str, int] = {}
    for e in commits:
        counts[e.inferred_type] = counts.get(e.inferred_type, 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:3]
    parts = [f"{_TYPE_LABEL.get(t, t)}（{n} 次提交）" for t, n in top]
    return "工作包括 " + "、".join(parts)


def _work_description_en(commits: list[GitCommitEvidence]) -> str:
    counts: dict[str, int] = {}
    for e in commits:
        counts[e.inferred_type] = counts.get(e.inferred_type, 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:3]
    return ", ".join(f"{t} ({n} commits)" for t, n in top)


def _enhanced_text(
    verb: str, module: str, tech_str: str, work_desc: str, author_ev: AuthorEvidence
) -> str:
    if verb == "主要负责":
        span = ""
        if author_ev.first_commit_date and author_ev.last_commit_date:
            days = (author_ev.last_commit_date - author_ev.first_commit_date).days
            if days >= 60:
                span = f"，持续迭代 {days // 30} 个月以上"
        return f"主要负责 {module} 模块的设计与实现，基于 {tech_str}，{work_desc}{span}"
    if verb == "深度参与":
        return f"深度参与 {module} 模块开发，基于 {tech_str}，{work_desc}"
    # 归属等级不够，强化版也不拔高
    return f"{verb} {module} 模块，基于 {tech_str}，{work_desc}"


def _star_entry(
    module: str,
    verb: str,
    tech_str: str,
    commits: list[GitCommitEvidence],
    evidence: list[str],
) -> dict:
    feature_msgs = [e.message for e in commits if e.inferred_type == "feature"][:2]
    fix_msgs = [e.message for e in commits if e.inferred_type == "bugfix"][:2]
    return {
        "module": module,
        "situation": f"项目需要 {module} 模块支撑相关业务能力（背景细节建议结合实际补充）",
        "task": f"{verb}该模块的开发任务",
        "action": (
            f"基于 {tech_str} 完成相关提交，"
            f"代表性工作：{'；'.join(feature_msgs + fix_msgs) or '见证据 commit'}"
        ),
        "result": "模块按提交记录持续演进并合入主干；量化效果需补充真实指标",
        "evidence": evidence,
    }


def _target_role_notes(target_role: str, tech: TechStackEvidence) -> list[str]:
    if not target_role:
        return []
    role_low = target_role.lower()
    notes: list[str] = []
    matched: list[str] = []
    for key, hints in _ROLE_TECH_HINTS.items():
        if key in role_low:
            matched = [t for t in hints if t in
                       tech.frameworks + tech.databases + tech.middlewares]
            break
    if matched:
        notes.append(
            f"面向「{target_role}」：建议在简历中突出 {', '.join(matched)} 相关经验"
            "（仓库依赖中确有这些技术）"
        )
    else:
        notes.append(
            f"注意：仓库技术栈与「{target_role}」的典型技术要求匹配度有限，"
            "建议如实呈现项目技术栈，不要包装成不存在的技术经验"
        )
    return notes

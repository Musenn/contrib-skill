"""Generate a paste-ready resume project entry backed by Git evidence."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from ..analyzers.claim_risk_checker import check_claim
from ..models import (
    ArchitectureEvidence,
    AuthorEvidence,
    BenchmarkEvidence,
    BusinessContextEvidence,
    GitCommitEvidence,
    ProjectEvidence,
    ProjectContextAssessment,
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
    architecture: ArchitectureEvidence | None = None,
    repository_commits: list[GitCommitEvidence] | None = None,
    project_context: str = "",
    context_assessments: list[ProjectContextAssessment] | None = None,
    benchmark: BenchmarkEvidence | None = None,
) -> dict:
    """Build a context-rich project entry, then keep evidence outside the paste area."""
    context_commits = repository_commits or author_commits
    selected_groups = _select_resume_groups(author_commits, max_items=4)
    benchmark_group_index: int | None = None
    if benchmark:
        benchmark_group_index = next(
            (
                index for index, group in enumerate(selected_groups)
                if group[0].inferred_type == "performance"
                and _benchmark_matches_group(benchmark, group)
            ),
            None,
        )
        if benchmark_group_index is None:
            performance_commits = sorted(
                (
                    commit for commit in author_commits
                    if not commit.is_merge and commit.inferred_type == "performance"
                    and _benchmark_matches_group(benchmark, [commit])
                ),
                key=lambda commit: commit.date,
            )
            if performance_commits:
                performance_group = [performance_commits[0]]
                if len(selected_groups) >= 4:
                    selected_groups[-1] = performance_group
                    benchmark_group_index = len(selected_groups) - 1
                else:
                    selected_groups.append(performance_group)
                    benchmark_group_index = len(selected_groups) - 1
            else:
                # Keep the entry at four numbered items: three repository-backed
                # contributions plus one independently measured STAR result.
                selected_groups = selected_groups[:3]

    ready_bullets = []
    for index, group in enumerate(selected_groups):
        ready_bullets.append(
            _claim_from_group(
                group,
                author_ev,
                tech,
                business=business,
                architecture=architecture,
                benchmark=benchmark if index == benchmark_group_index else None,
            )
        )
    benchmark_claim = (
        _benchmark_star_claim(benchmark, author_ev)
        if benchmark and benchmark_group_index is None else None
    )
    if benchmark_claim:
        ready_bullets.append(benchmark_claim)
    if strict:
        ready_bullets = [c for c in ready_bullets if c.risk_level == RISK_SAFE]

    project_entry = {
        "project_name": project.project_name if project else "项目名称",
        "subtitle": _project_subtitle(business),
        "period": _period(author_ev.first_commit_date, author_ev.last_commit_date),
        "role": _resume_role(author_ev),
        "tech_stack": _tech_string(tech),
        "summary": _project_summary(
            business, architecture, tech, context_commits, project_context
        ),
    }

    # Keep the former keys for callers that consumed the Python return value.
    # The Markdown output intentionally presents only one primary version.
    return {
        "project_entry": project_entry,
        "ready_bullets": ready_bullets,
        "project_context_evidence": _project_context_evidence(
            business, architecture, tech, context_commits, project_context, benchmark
        ),
        "context_assessments": context_assessments or [],
        "benchmark_star": _benchmark_star(benchmark) if benchmark else None,
        "confirmation_prompts": _confirmation_prompts(
            [commit for group in selected_groups for commit in group],
            business,
            project_context,
        ),
        "target_role_notes": _target_role_notes(target_role, tech),
        "metric_suggestions": _metric_suggestions(selected_groups, benchmark),
        "conservative": ready_bullets,
        "standard": ready_bullets,
        "enhanced": ready_bullets,
        "star": [_benchmark_star(benchmark)] if benchmark else [],
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


def _metric_suggestions(
    groups: list[list[GitCommitEvidence]],
    benchmark: BenchmarkEvidence | None = None,
) -> list[str]:
    suggestions: list[str] = []
    for group in groups:
        commit_type = group[0].inferred_type
        topic = _topic_label(group)
        summary = " ".join(commit.message for commit in group).lower()
        if commit_type == "performance":
            suggestions.append(
                "性能优化：缓存命中率、数据库查询次数、QPS、P95/P99 与资源消耗"
            )
        elif commit_type == "security":
            suggestions.append(
                "安全边界：未授权请求拦截数、误拦截率、安全事件数或审计覆盖范围"
            )
        elif commit_type == "test":
            suggestions.append(
                "质量保障：自动化用例数、测试覆盖率、缺陷回归率或发布前拦截缺陷数"
            )
        elif "订单" in topic:
            suggestions.append(
                "订单链路：状态流转成功率、异常状态数量、单日订单处理量或状态处理耗时"
            )
        elif "支付" in topic:
            suggestions.append(
                "支付链路：回调成功率、回调处理耗时、异常回调数量或重复回调比例"
            )
        elif "报告与简历生成" in topic:
            if any(word in summary for word in ("benchmark", "pattern", "模式")):
                suggestions.append(
                    "证据生成：可识别模式数量、风险表述拦截数、报告生成耗时或规则覆盖率"
                )
            elif any(word in summary for word in ("context", "背景", "validate", "risk")):
                suggestions.append(
                    "背景校验：强声明识别数、风险表述拦截数、人工复核通过率或误报率"
                )
            else:
                suggestions.append(
                    "材料生成：可追溯贡献条目数、报告生成耗时、人工改写比例或支持的仓库规模"
                )
        elif commit_type in {"architecture", "ci", "config", "dependency", "build"}:
            suggestions.append(
                "工程效率：环境初始化耗时、构建耗时、部署成功率或新模块接入耗时"
            )
    if benchmark:
        suggestions = [
            item for item in suggestions
            if not item.startswith("性能优化：")
        ]
    suggestions.extend(METRIC_SUGGESTIONS)
    return list(dict.fromkeys(suggestions))[:8]


def _benchmark_matches_group(
    benchmark: BenchmarkEvidence,
    commits: list[GitCommitEvidence],
) -> bool:
    scenario = benchmark.scenario.lower()
    commit_corpus = " ".join(
        [commit.message for commit in commits]
        + [path for commit in commits for path in commit.changed_files]
    ).lower()
    topic = _topic_label(commits).strip().lower()
    if topic and topic not in {"项目", "project"} and topic in scenario:
        return True
    domain_terms = (
        "订单", "order", "支付", "payment", "用户", "user", "账号", "account",
        "认证", "auth", "权限", "permission", "库存", "inventory", "合同",
        "contract", "文档", "document", "消息", "message", "通知", "notify",
        "报告", "report", "简历", "resume", "智能体", "agent", "工作流", "workflow",
    )
    return any(term in scenario and term in commit_corpus for term in domain_terms)


def _group_feature_commits(
    commits: list[GitCommitEvidence],
) -> list[list[GitCommitEvidence]]:
    groups: dict[str, list[GitCommitEvidence]] = {}
    for commit in commits:
        groups.setdefault(_feature_group_key(commit), []).append(commit)
    return list(groups.values())


def _feature_group_key(commit: GitCommitEvidence) -> str:
    topic = _topic_label([commit])
    if topic != "报告与简历生成":
        return _commit_topic(commit)
    corpus = commit.message.lower()
    if any(word in corpus for word in ("benchmark", "pattern", "模式")):
        return "resume-evidence-and-benchmark"
    if any(word in corpus for word in ("context", "背景", "validate", "risk")):
        return "resume-context-validation"
    return "resume-material-generation"


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
    business: BusinessContextEvidence | None = None,
    architecture: ArchitectureEvidence | None = None,
    benchmark: BenchmarkEvidence | None = None,
) -> ResumeClaim:
    commit = commits[0]
    summaries = [_clean_commit_message(item.message) for item in commits]
    summary = "、".join(dict.fromkeys(summaries))
    modules = sorted({module for item in commits for module in item.changed_modules})
    verb = _role_verb(author_ev, modules)
    topic = _topic_label(commits)
    layer = _layer_phrase(commits)
    pattern_phrase = _commit_pattern_phrase(commits)

    if commit.inferred_type == "architecture" or _looks_like_initialization(summary):
        project_scope = _project_scope_label(business)
        architecture_verb = "负责" if author_ev.is_project_initializer else "参与"
        text = _three_part_claim(
            "项目持续开发中的依赖、运行约定与仓库规则一致性要求",
            (
                f"{architecture_verb}工程基线建设，基于 {_architecture_tech_string(tech)} "
                "完成工程初始化与依赖集成，统一依赖版本、仓库忽略规则和运行说明"
            ),
            f"形成一致的工程入口，支撑{project_scope}核心业务模块持续扩展",
            label="工程基线",
        )
    elif commit.inferred_type == "feature":
        technical_approach = _feature_technical_approach(
            tech, pattern_phrase, topic, summary
        )
        text = _three_part_claim(
            _feature_problem(topic, summary),
            (
                f"{_feature_heading(verb, topic, summary)}，"
                f"{technical_approach}{_business_action(topic, summary)}"
            ),
            _feature_effect(topic, summary, layer),
            label=_feature_label(topic, summary),
        )
    elif commit.inferred_type == "security":
        text = _three_part_claim(
            f"{topic}关键链路需要明确认证、授权与数据保护边界的安全约束",
            (
                f"{verb}{topic}安全边界建设，围绕{summary}落地认证、授权或数据保护机制"
            ),
            "将安全校验纳入关键业务链路，收敛未授权访问与敏感数据暴露风险",
            label=f"{topic}安全边界",
        )
    elif commit.inferred_type == "performance":
        text = _performance_claim(summary, topic, tech, benchmark)
    elif commit.inferred_type == "refactor":
        text = _three_part_claim(
            f"{topic}后续扩展中职责边界与协作关系需要持续保持清晰的工程要求",
            f"{verb}{topic}模块重构，围绕{summary}重新梳理职责边界与协作关系",
            "收敛模块职责与跨模块依赖，为后续功能迭代提供清晰扩展路径",
            label=f"{topic}模块重构",
        )
    elif commit.inferred_type == "bugfix":
        text = _bugfix_claim(summary, topic)
    elif commit.inferred_type == "test":
        test_tool = tech.test_tools[0] if tech.test_tools else "自动化测试"
        text = _three_part_claim(
            f"{topic}持续迭代缺少可重复验证核心路径与边界场景的质量风险",
            (
                f"基于 {test_tool} 建立自动化回归保障，覆盖{summary}涉及的"
                "核心路径与边界场景"
            ),
            "形成统一测试入口，为功能迭代与缺陷修复提供持续验证能力",
            label=f"{topic}质量保障",
        )
    elif commit.inferred_type in {"ci", "config", "dependency", "build"}:
        text = _three_part_claim(
            "多环境协作中依赖、构建与配置入口需要保持一致的工程要求",
            f"完善项目工程化建设，落地{summary}并统一依赖、构建与配置入口",
            "形成可复用的环境准备与交付路径，减少重复配置和协作维护成本",
            label="工程化建设",
        )
    else:
        text = f"参与项目迭代与维护，{summary}。"

    evidence = [item for commit in commits for item in _evidence_list(commit)]
    if benchmark:
        evidence.extend(_benchmark_evidence(benchmark))
    return check_claim(
        text,
        author_ev,
        evidence,
        has_benchmark_evidence=benchmark is not None,
    )


def _three_part_claim(
    problem: str,
    solution: str,
    result: str,
    label: str = "",
) -> str:
    prefix = f"{label}：" if label else ""
    return f"{prefix}针对{problem}，{solution}；{result}。"


def _feature_problem(topic: str, summary: str) -> str:
    corpus = summary.lower()
    if "报告与简历生成" in topic:
        if any(word in corpus for word in ("benchmark", "pattern", "模式")):
            return "技术术语与量化指标容易脱离仓库和测试证据、导致简历表述不可追溯的问题"
        if any(word in corpus for word in ("context", "背景", "validate", "risk")):
            return "用户提供的上线、高可用或高并发背景无法仅凭代码仓库直接证实的问题"
        return "Git 提交与目录信息难以直接转化为面试官可理解项目贡献的问题"
    if "订单" in topic:
        return "订单跨阶段状态需要统一生命周期承载与约束的问题"
    if "支付" in topic:
        return "外部支付结果需要接入系统并与内部业务处理衔接的问题"
    if "用户" in topic or "账号" in topic:
        return "用户请求、身份处理与业务响应需要形成连续处理链路的问题"
    if "认证" in topic or "权限" in topic:
        return "身份校验与权限控制需要在关键业务入口形成统一边界的问题"
    if "合同" in topic or "文档" in topic:
        return "文档从接入、内容处理到结果输出需要保持链路连续的问题"
    if "智能体" in topic or "工作流" in topic:
        return "复杂任务需要在拆解、工具调用与结果处理之间建立可控协作链路的问题"
    return f"{topic}从请求接入到结果返回需要形成完整处理闭环的问题"


def _feature_label(topic: str, summary: str) -> str:
    corpus = summary.lower()
    if "报告与简历生成" in topic:
        if any(word in corpus for word in ("benchmark", "pattern", "模式")):
            return "技术证据与量化结果"
        if any(word in corpus for word in ("context", "背景", "validate", "risk")):
            return "项目背景可信校验"
        return "简历材料生成"
    if "订单" in topic:
        return "订单状态建模" if any(
            word in corpus for word in ("状态", "流转", "transition")
        ) else "订单核心链路"
    if "支付" in topic:
        return "支付回调链路" if any(
            word in corpus for word in ("回调", "callback")
        ) else "支付核心链路"
    if "认证" in topic or "权限" in topic:
        return "认证与权限边界"
    if "智能体" in topic or "工作流" in topic:
        return "Agent 工作流"
    return topic.strip() or "核心能力"


def _feature_technical_approach(
    tech: TechStackEvidence,
    pattern_phrase: str,
    topic: str,
    summary: str,
) -> str:
    parts: list[str] = []
    if "报告与简历生成" in topic:
        language = next(iter(tech.languages), "Python")
        corpus = summary.lower()
        if any(word in corpus for word in ("benchmark", "pattern", "模式")):
            parts.append(f"基于 {language} 构建设计模式识别与 benchmark 证据解析流程")
        elif any(word in corpus for word in ("context", "背景", "validate", "risk")):
            parts.append(f"基于 {language} 构建背景声明解析与仓库证据校验流程")
        else:
            parts.append(f"基于 {language} 构建证据分析与材料生成流程")
    elif tech.frameworks:
        parts.append(f"基于 {tech.frameworks[0]} 组织请求接入与业务处理")
    if pattern_phrase:
        parts.append(pattern_phrase.rstrip("，"))
    return "，".join(parts) + ("，" if parts else "")


def _feature_heading(verb: str, topic: str, summary: str) -> str:
    if "报告与简历生成" not in topic:
        return f"{verb}{topic}核心链路建设"
    corpus = summary.lower()
    if any(word in corpus for word in ("benchmark", "pattern", "模式")):
        return f"{verb}技术证据与量化结果链路建设"
    if any(word in corpus for word in ("context", "背景", "validate", "risk")):
        return f"{verb}项目背景可信校验机制建设"
    return f"{verb}简历材料生成链路建设"


def _bugfix_claim(summary: str, topic: str) -> str:
    corpus = summary.lower()
    if any(word in corpus for word in ("空指针", "null", "none", "nil")):
        return _three_part_claim(
            f"{summary}使异常输入可能中断{topic}业务处理链路的问题",
            f"参与{topic}稳定性治理，定位异常触发路径并引入空值校验与保护性处理",
            "将无效请求隔离在异常处理路径，补齐关键链路的边界输入保护",
            label=f"{topic}稳定性治理",
        )
    return _three_part_claim(
        f"{summary}暴露的{topic}稳定性与边界输入问题",
        f"参与{topic}稳定性治理，定位根因并补充异常路径与边界输入处理",
        "完善关键流程的异常隔离与恢复路径，提高后续维护的确定性",
        label=f"{topic}稳定性治理",
    )


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


def _topic_label(commits: list[GitCommitEvidence]) -> str:
    message_corpus = " ".join(c.message for c in commits).lower()
    path_corpus = " ".join(
        path for c in commits for path in c.changed_files
    ).lower()
    developer_tool_paths = (
        "contrib_skill/", "resume_generator", "report_generator",
        "project_context_validator", "claim_risk", "author_profiler",
    )
    if any(path in path_corpus for path in developer_tool_paths):
        return "报告与简历生成"
    topics = (
        ("报告与简历生成", ("report", "报告", "resume", "简历", "interview", "面试", "render", "渲染")),
        ("订单", ("order", "订单")),
        ("支付", ("payment", "pay", "支付", "退款")),
        ("用户与账号", ("user", "account", "用户", "账号", "登录")),
        ("认证与权限", ("auth", "permission", "security", "鉴权", "权限")),
        ("库存", ("inventory", "stock", "库存")),
        ("合同文档", ("contract", "document", "合同", "文档")),
        ("智能体工作流", ("agent", "workflow", "skill", "智能体", "工作流")),
        ("消息通知", ("message", "notify", "notification", "消息", "通知")),
        ("数据处理", ("data", "etl", "pipeline", "数据", "报表")),
    )
    # Commit messages describe intent more precisely than generic package paths
    # such as ``contrib_skill/...``. Prefer them before falling back to paths.
    for label, keywords in topics:
        if any(keyword in message_corpus for keyword in keywords):
            return label
    corpus = f"{message_corpus} {path_corpus}"
    for label, keywords in topics:
        if any(keyword in corpus for keyword in keywords):
            return label
    key = _commit_topic(commits[0]).replace("_", " ").strip()
    if key and not re.fullmatch(r"[0-9a-f]{7,}", key):
        return f"{key} "
    return "项目"


def _layer_phrase(commits: list[GitCommitEvidence]) -> str:
    corpus = " ".join(
        [module for c in commits for module in c.changed_modules]
        + [path.replace("\\", "/").lower() for c in commits for path in c.changed_files]
    ).lower()
    layers: list[str] = []
    layer_rules = (
        ("Controller 接口层", ("controller", "/api/", "/routes/", "/router/")),
        ("Service 业务层", ("service", "/core/", "/domain/")),
        ("Repository 数据访问层", ("repository", "mapper", "/dao/")),
        ("前端交互层", ("component", "/pages/", "/views/")),
        ("测试层", ("/tests/", "/test/", ".test.", ".spec.")),
    )
    for label, hints in layer_rules:
        if any(hint in corpus for hint in hints):
            layers.append(label)
    return "、".join(layers[:3])


def _feature_effect(topic: str, summary: str, layer: str) -> str:
    corpus = f"{topic} {summary}".lower()
    if "报告与简历生成" in topic:
        if any(word in corpus for word in ("benchmark", "pattern", "模式")):
            return "形成技术术语证据化、测试结果可追溯的简历生成链路"
        if any(word in corpus for word in ("context", "背景", "validate", "risk")):
            return "在保留真实使用场景的同时，将证据不足的强声明隔离到审计区"
        return "形成从仓库证据采集、风险校验到可投递材料生成的处理闭环"
    if "订单" in corpus and any(word in corpus for word in ("状态", "流转", "创建")):
        return "形成覆盖订单创建、业务处理与状态演进的业务闭环，为跨阶段状态变化提供统一承载入口"
    if "支付" in corpus and any(word in corpus for word in ("回调", "callback", "refund")):
        return "形成回调接收、支付结果处理与业务响应闭环，为外部结果与内部业务衔接提供统一入口"
    if "用户" in corpus or "账号" in corpus:
        return "串联用户请求接入、身份处理与业务响应流程"
    if "认证" in corpus or "权限" in corpus:
        return "形成从身份校验到权限控制的完整处理链路"
    if "合同" in corpus or "文档" in corpus:
        return "串联文档接入、内容处理与结果输出流程"
    if "agent" in corpus or "工作流" in corpus:
        return "串联任务拆解、工具调用与结果处理流程"
    if "Controller" in layer and "Service" in layer:
        return "串联接口接入、业务处理与结果返回流程"
    return "形成可独立讲清的功能闭环"


def _business_action(topic: str, summary: str) -> str:
    corpus = summary.lower()
    if "报告与简历生成" in topic:
        if any(word in corpus for word in ("benchmark", "pattern", "模式")):
            return "扩展架构/设计模式证据识别与 benchmark 报告导入能力"
        if any(word in corpus for word in ("context", "背景", "validate", "risk")):
            return "建立用户背景与仓库证据的交叉校验机制，并对强声明输出风险分级"
        return "串联 Git 提交与仓库结构解析、个人贡献与风险分析、简历及面试材料生成"
    if "订单" in topic:
        has_create = any(word in corpus for word in ("创建", "create"))
        has_state = any(word in corpus for word in ("状态", "流转", "transition"))
        if has_create and has_state:
            return "实现订单创建与状态流转，并以状态驱动方式统一约束订单生命周期"
        if has_create:
            return "实现订单创建能力"
    if "支付" in topic and any(word in corpus for word in ("回调", "callback")):
        return "接入支付回调并统一处理返回结果"
    action = re.sub(r"(?:新增|实现|接入)([^，。、；]+?)接口", r"建设\1能力", summary)
    return action


def _commit_pattern_phrase(commits: list[GitCommitEvidence]) -> str:
    message_corpus = " ".join(commit.message for commit in commits).lower()
    paths = [
        path.replace("\\", "/").lower()
        for commit in commits for path in commit.changed_files
    ]
    corpus = f"{message_corpus} {' '.join(paths)}"
    rules = (
        ("策略模式组织可变业务规则", ("strategy", "策略")),
        ("工厂模式封装对象创建", ("factory", "工厂")),
        ("适配器模式统一外部能力接入", ("adapter", "适配器")),
        ("观察者模式解耦事件发布与处理", ("observer", "listener", "观察者")),
        ("责任链模式编排多阶段处理", ("handler_chain", "chain_of_responsibility", "责任链")),
        ("DAO 模式封装数据访问", ("/dao/",)),
        ("Data Mapper 模式完成对象与存储映射", ("mapper",)),
    )
    for description, keywords in rules:
        if any(keyword in corpus for keyword in keywords):
            separator = " " if re.match(r"[A-Za-z]", description) else ""
            return f"采用{separator}{description}，"
    repository_path = any(
        re.search(r"(?:^|/)(?:repositories?|[^/]*_repository)(?:/|\.|$)", path)
        for path in paths
    )
    repository_claim = any(
        phrase in message_corpus
        for phrase in ("repository pattern", "repository 模式")
    )
    if repository_path or repository_claim:
        return "采用 Repository 模式隔离业务逻辑与数据访问，"
    return ""


def _performance_claim(
    summary: str,
    topic: str,
    tech: TechStackEvidence,
    benchmark: BenchmarkEvidence | None = None,
) -> str:
    corpus = summary.lower()
    cache_tech = next(
        (item for item in tech.middlewares if item.lower() in corpus),
        "Redis" if "redis" in corpus else "缓存",
    )
    if "cache" in corpus or "缓存" in corpus or "redis" in corpus:
        subject = re.sub(
            r"(?:增加|新增|引入|添加)?\s*(?:redis\s*)?(?:cache|缓存).*",
            "",
            summary,
            flags=re.IGNORECASE,
        ).strip(" ，,;；") or topic
        scene = (
            f"{subject}这一高频场景"
            if any(word in subject for word in ("查询", "检索", "读取"))
            else f"{subject}高频查询场景"
        )
        result = (
            f"减少对 {_primary_database(tech)} 的重复访问并收敛核心查询路径"
        )
        if benchmark:
            result += f"；{_benchmark_result_clause(benchmark)}"
        return _three_part_claim(
            f"{scene}存在重复读取持久化数据、核心查询路径需要收敛的问题",
            f"采用 {cache_tech} 缓存机制，将重复读取前移至缓存层",
            result,
            label="查询性能优化",
        )
    else:
        result = "收敛资源访问与核心处理路径，形成可持续验证的性能优化入口"
        if benchmark:
            result += f"；{_benchmark_result_clause(benchmark)}"
        return _three_part_claim(
            f"{topic}关键链路的资源访问与处理效率需要持续优化的问题",
            f"围绕核心路径落地{summary}并梳理资源访问关系",
            result,
            label=f"{topic}性能治理",
        )


def _primary_database(tech: TechStackEvidence) -> str:
    return tech.databases[0] if tech.databases else "持久化存储"


def _benchmark_result_clause(benchmark: BenchmarkEvidence) -> str:
    environment = _environment_label(benchmark.environment)
    return (
        f"在{environment}环境针对{benchmark.scenario}编写并执行 HTTP 压测脚本，"
        f"以 {benchmark.concurrency} 并发完成 {benchmark.total_requests} 次请求，"
        f"实测成功率 {benchmark.success_rate:.2f}%、吞吐量 "
        f"{benchmark.requests_per_second:.2f} QPS、P95 延迟 "
        f"{benchmark.latency_p95_ms:.2f} ms，形成可复核性能基线"
    )


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
    corpus = " ".join((
        business.inferred_domain,
        business.project_goal,
        business.core_business_flow,
    ))
    if all(keyword in corpus for keyword in ("电商", "订单", "支付")):
        return "电商订单与支付"
    return business.inferred_domain.split("（", 1)[0].strip()


def _project_scope_label(business: BusinessContextEvidence | None) -> str:
    subtitle = _project_subtitle(business)
    if subtitle.startswith("开发者工具"):
        return "Git 贡献分析与简历生成"
    return subtitle


def _project_summary(
    business: BusinessContextEvidence | None,
    architecture: ArchitectureEvidence | None,
    tech: TechStackEvidence,
    commits: list[GitCommitEvidence],
    project_context: str = "",
) -> str:
    tech_context = _context_tech_string(tech)
    scope = _project_scope_label(business)
    architecture_context = _architecture_vocabulary(architecture)
    requirement_clause = _requirement_background(business, commits).rstrip("。")
    context_clause = _user_context_clause(project_context)
    background_parts = [part for part in (context_clause, requirement_clause) if part]
    background_sentence = "；".join(background_parts)
    if background_sentence:
        background_sentence += "。"

    solution_parts: list[str] = []
    if tech_context:
        solution_parts.append(f"基于 {tech_context} 构建{scope}核心链路")
    else:
        separator = " " if re.match(r"[A-Za-z]", scope) else ""
        solution_parts.append(f"围绕{separator}{scope}组织核心链路")
    if architecture_context:
        solution_parts.append(architecture_context)
    solution_sentence = "，".join(solution_parts) + "。"
    return f"{background_sentence}{solution_sentence}"


def _clean_context_text(text: str) -> str:
    value = text.strip()
    for prefix in ("README 描述（事实）：", "推断："):
        if value.startswith(prefix):
            value = value[len(prefix):].strip()
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"!\[[^]]*]\([^)]*\)", "", value)
    value = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", value)
    value = re.sub(r"(?:\*\*|__)(.+?)(?:\*\*|__)", r"\1", value)
    value = re.sub(r"(?:\*|_)(.+?)(?:\*|_)", r"\1", value)
    return re.sub(r"\s+", " ", value).strip(" #。")


def _context_tech_string(tech: TechStackEvidence) -> str:
    items = list(dict.fromkeys(
        tech.frameworks[:2] + tech.databases[:2] + tech.middlewares[:2]
    ))
    return "、".join(items[:5])


def _architecture_vocabulary(architecture: ArchitectureEvidence | None) -> str:
    if not architecture or architecture.confidence == "低":
        return ""
    if architecture.design_patterns:
        patterns = "、".join(architecture.design_patterns[:3])
        separator = " " if re.match(r"[A-Za-z]", patterns) else ""
        return f"采用{separator}{patterns}，组织核心模块与扩展边界"
    style = architecture.architecture_style.lower()
    if "mvc" in style:
        return "采用 MVC 分层架构组织接口接入与业务职责"
    if "单体" in architecture.architecture_style:
        return "采用模块化单体架构划分核心职责"
    if architecture.layer_analysis:
        return "按核心职责划分模块边界，保持功能组织与扩展路径清晰"
    return ""


def _requirement_background(
    business: BusinessContextEvidence | None,
    commits: list[GitCommitEvidence],
) -> str:
    if not business:
        return ""
    corpus = " ".join((
        business.inferred_domain,
        business.project_goal,
        business.core_business_flow,
    )).lower()
    if "开发者工具" in corpus or ("git" in corpus and "简历" in corpus):
        return (
            "面向需要从 Git 历史还原个人工作的开发者，"
            "项目解决提交记录难以直接转化为可信简历与面试材料的问题。"
        )
    if "订单" in corpus and "支付" in corpus:
        performance = any(commit.inferred_type == "performance" for commit in commits)
        suffix = "，并兼顾高频查询效率" if performance else ""
        return (
            "面向电商交易中的订单处理与支付结果衔接需求，"
            f"项目聚焦订单状态流转和支付回调处理{suffix}。"
        )
    flow = _clean_context_text(business.core_business_flow)
    if flow and "无法" not in flow:
        flow = re.sub(r"\s*→\s*", "、", flow)
        return f"面向{_project_subtitle(business)}场景的多环节协同需求，项目聚焦{flow}流程衔接。"
    return ""


def _project_context_evidence(
    business: BusinessContextEvidence | None,
    architecture: ArchitectureEvidence | None,
    tech: TechStackEvidence,
    commits: list[GitCommitEvidence],
    project_context: str = "",
    benchmark: BenchmarkEvidence | None = None,
) -> list[str]:
    evidence: list[str] = []
    if project_context.strip():
        evidence.append(f"用户提供背景：{' '.join(project_context.split())}")
    if business:
        evidence.extend(business.evidence_sources[:2])
        flow = _clean_context_text(business.core_business_flow)
        if flow and "无法" not in flow:
            evidence.append(f"业务流程（仓库语义推断）：{flow}")
    if architecture and architecture.layer_analysis:
        evidence.append(f"目录分层：{'、'.join(architecture.layer_analysis[:4])}")
    if architecture and architecture.design_patterns:
        evidence.append(f"架构/设计模式：{'、'.join(architecture.design_patterns)}")
    if tech.evidence_files:
        evidence.append(
            f"依赖文件：{'、'.join(tech.evidence_files[:3])} → {_tech_string(tech)}"
        )
    for commit in commits:
        corpus = commit.message.lower()
        if commit.inferred_type == "performance" and any(
            word in corpus for word in ("cache", "缓存", "redis")
        ):
            evidence.append(f"技术机制：commit {commit.short_hash} {commit.message}")
            break
    if benchmark:
        evidence.append(
            f"压测报告：{benchmark.source_file}（{benchmark.environment} 环境，"
            f"{benchmark.total_requests} 次请求 / {benchmark.concurrency} 并发）"
        )
    return list(dict.fromkeys(evidence))


def _benchmark_star(benchmark: BenchmarkEvidence) -> dict[str, str]:
    environment = _environment_label(benchmark.environment)
    return {
        "situation": f"{benchmark.scenario}在并发访问下缺乏可复核的响应稳定性与容量基线",
        "task": f"在{environment}环境验证接口吞吐、成功率与尾延迟",
        "action": (
            f"编写并执行 HTTP 压测脚本，以 {benchmark.concurrency} 并发"
            f"完成 {benchmark.total_requests} 次请求"
        ),
        "result": (
            f"实测成功率 {benchmark.success_rate:.2f}%，吞吐量 "
            f"{benchmark.requests_per_second:.2f} QPS，P95 延迟 "
            f"{benchmark.latency_p95_ms:.2f} ms"
        ),
    }


def _benchmark_star_claim(
    benchmark: BenchmarkEvidence,
    author_ev: AuthorEvidence,
) -> ResumeClaim:
    environment = _environment_label(benchmark.environment)
    text = _three_part_claim(
        f"{benchmark.scenario}缺少可复核的响应稳定性与容量基线",
        (
            f"在{environment}环境承担接口吞吐、成功率与尾延迟验证，"
            f"编写并执行 HTTP 压测脚本，以 {benchmark.concurrency} 并发"
            f"完成 {benchmark.total_requests} 次请求"
        ),
        (
            f"实测成功率 {benchmark.success_rate:.2f}%、吞吐量 "
            f"{benchmark.requests_per_second:.2f} QPS、P95 延迟 "
            f"{benchmark.latency_p95_ms:.2f} ms，为后续容量评估与性能优化建立量化基线"
        ),
        label="接口性能基线",
    )
    evidence = _benchmark_evidence(benchmark)
    return check_claim(
        text,
        author_ev,
        evidence,
        has_benchmark_evidence=True,
    )


def _benchmark_evidence(benchmark: BenchmarkEvidence) -> list[str]:
    return [
        f"benchmark report: {benchmark.source_file}",
        f"tool={benchmark.tool}; environment={benchmark.environment}; target={benchmark.target}",
    ]


def _environment_label(value: str) -> str:
    labels = {
        "local": "本地",
        "test": "测试",
        "testing": "测试",
        "staging": "预发布",
        "prod": "生产",
        "production": "生产",
    }
    return labels.get(value.lower(), value)


def _architecture_baseline(architecture: ArchitectureEvidence | None) -> str:
    if architecture:
        layers = " ".join(architecture.layer_analysis).lower()
        if "controller" in layers and "service" in layers:
            return " Controller/Service 分层"
        if architecture.layer_analysis:
            return "模块化分层"
    return "可持续迭代的"


def _user_context_clause(project_context: str) -> str:
    text = " ".join(project_context.split()).strip()
    if not text:
        return ""
    text = re.sub(r"[。！？!?；;]+", "，", text)
    return text.strip("， ")


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
    project_context: str = "",
) -> list[str]:
    prompts = [
        "确认个人角色与团队边界：团队人数、本人负责范围，以及是否可使用“主导/主要负责”。",
        "补充真实规模：用户量、数据量、QPS、运行时长或 star；没有可靠数据就不要填写。",
    ]
    if not project_context.strip():
        prompts.insert(
            0,
            "确认项目性质与使用场景：真实上线、公司内部使用、开源项目，还是课程/练习项目。",
        )
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

"""ClaimRiskChecker：对简历表述做证据校验，输出 safe / needs_confirmation / risky。

核心规则：
- 强表述（主导 / 从 0 到 1 / 独立负责 / 核心负责人）必须有强 Git 证据；
- 量化指标（性能提升 X%、百万级并发等）仓库无 benchmark 证据时一律不放行；
- 模块归属按该作者在模块内的提交占比与持续度分级。
"""
from __future__ import annotations

import re

from ..models import (
    AuthorEvidence,
    AuthorStats,
    GitCommitEvidence,
    RISK_NEEDS_CONFIRMATION,
    RISK_RISKY,
    RISK_SAFE,
    ResumeClaim,
)

# 模块归属等级 -> 允许使用的动词
OWNERSHIP_VERBS = {
    "owner": "主要负责",
    "deep": "深度参与",
    "maintainer": "负责该模块部分开发与维护",
    "participant": "参与",
    "assistant": "协助",
}

_STRONG_PHRASES = ["主导", "从 0 到 1", "从0到1", "独立负责", "核心负责人", "一人完成"]
_METRIC_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?\s*%|百万级|千万级|亿级|qps|tps|并发|响应时间|耗时降低|性能提升)",
    re.IGNORECASE,
)


def module_ownership(
    author_stats: AuthorStats,
    all_author_stats: dict[str, AuthorStats],
    author_key: str,
    author_evidence: list[GitCommitEvidence],
) -> dict[str, str]:
    """对作者的每个主要模块给出归属等级。"""
    ownership: dict[str, str] = {}
    feature_like = {"feature", "architecture", "performance", "security"}

    for module, own_count in author_stats.module_counts.items():
        total = sum(
            st.module_counts.get(module, 0) for st in all_author_stats.values()
        )
        share = own_count / total if total else 0.0
        span_days = _module_span_days(module, author_evidence)
        feature_count = sum(
            1
            for e in author_evidence
            if module in e.changed_modules and e.inferred_type in feature_like
        )

        if share >= 0.6 and own_count >= 5 and feature_count >= 2:
            level = "owner"
        elif own_count >= 4 and span_days >= 30:
            level = "deep"
        elif own_count >= 3:
            level = "maintainer"
        elif own_count >= 2:
            level = "participant"
        else:
            level = "assistant"
        ownership[module] = level
    return ownership


def _module_span_days(module: str, evidence: list[GitCommitEvidence]) -> int:
    dates = [e.date for e in evidence if module in e.changed_modules]
    if len(dates) < 2:
        return 0
    return (max(dates) - min(dates)).days


def check_claim(
    text: str,
    author_ev: AuthorEvidence,
    support_evidence: list[str] | None = None,
    has_benchmark_evidence: bool = False,
) -> ResumeClaim:
    """校验一条简历表述。生成器产出的每条 bullet 都必须过这里。"""
    claim = ResumeClaim(text=text, support_evidence=support_evidence or [])

    # 规则 1：量化指标无证据 -> needs_confirmation（若是生成的则不应生成）
    if _METRIC_PATTERN.search(text) and not has_benchmark_evidence:
        claim.risk_level = RISK_NEEDS_CONFIRMATION
        claim.needs_user_confirmation = True
        claim.forbidden_reason = (
            "包含量化指标，但仓库内无 benchmark / 压测 / 监控数据佐证，"
            "必须由本人确认真实数据后才能使用"
        )
        return claim

    # 规则 2：强表述需要强证据
    strong_hit = next((p for p in _STRONG_PHRASES if p in text), None)
    if strong_hit:
        strong_ok = (
            author_ev.is_project_initializer
            and author_ev.contribution_level in ("很高", "较高")
            and author_ev.commit_count >= 10
        )
        if not strong_ok:
            claim.risk_level = RISK_RISKY
            claim.forbidden_reason = (
                f"使用了强表述「{strong_hit}」，但 Git 证据不足"
                f"（贡献等级：{author_ev.contribution_level}，"
                f"提交数：{author_ev.commit_count}，"
                f"是否初始化者：{author_ev.is_project_initializer}）。"
                "建议降级为「参与」「负责部分模块」"
            )
            return claim
        claim.risk_level = RISK_NEEDS_CONFIRMATION
        claim.needs_user_confirmation = True
        claim.forbidden_reason = (
            "Git 证据支持较强角色，但「主导/从 0 到 1」类表述仍建议与团队确认口径，"
            "避免与其他成员表述冲突"
        )
        return claim

    # 规则 3：声称负责的模块必须在作者主要模块内
    owned_modules = {
        m for m, lvl in author_ev.module_ownership.items()
        if lvl in ("owner", "deep", "maintainer")
    }
    mentions_unowned = any(
        m in text for m in author_ev.module_ownership
        if author_ev.module_ownership[m] in ("participant", "assistant")
        and ("负责" in text or "主要" in text)
        and m in text
    )
    if mentions_unowned:
        claim.risk_level = RISK_RISKY
        claim.forbidden_reason = (
            "声称「负责」的模块中，该作者提交占比偏低，可能冒领他人贡献，"
            "建议改为「参与」或「协助」"
        )
        return claim

    # 规则 4：团队角色 / 线上效果类表述需要确认
    if any(kw in text for kw in ("上线", "线上", "团队", "带领", "落地生产")):
        claim.risk_level = RISK_NEEDS_CONFIRMATION
        claim.needs_user_confirmation = True
        claim.forbidden_reason = "涉及线上效果或团队角色，仓库无法佐证，需本人确认"
        return claim

    # 默认：有证据支撑即 safe，无证据则需确认
    if claim.support_evidence:
        claim.risk_level = RISK_SAFE
    else:
        claim.risk_level = RISK_NEEDS_CONFIRMATION
        claim.needs_user_confirmation = True
        claim.forbidden_reason = "该表述未关联任何 commit 证据，建议补充证据或确认"
    return claim


def verb_for_module(author_ev: AuthorEvidence, module: str) -> str:
    level = author_ev.module_ownership.get(module, "participant")
    return OWNERSHIP_VERBS[level]

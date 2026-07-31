"""Validate user-provided project context against visible repository evidence."""
from __future__ import annotations

from ..models import (
    ArchitectureEvidence,
    GitCommitEvidence,
    ProjectContextAssessment,
    RISK_NEEDS_CONFIRMATION,
    RISK_RISKY,
    TechStackEvidence,
)


def validate_project_context(
    context: str,
    architecture: ArchitectureEvidence,
    tech: TechStackEvidence,
    commits: list[GitCommitEvidence],
) -> list[ProjectContextAssessment]:
    context = " ".join(context.split()).strip()
    if not context:
        return []

    assessments = [ProjectContextAssessment(
        statement=f"项目性质/使用场景：{context}",
        risk_level=RISK_NEEDS_CONFIRMATION,
        analysis=(
            "按用户明确提供的背景写入项目简介；项目是否真实上线、内部使用、"
            "开源或课程实践通常无法仅凭代码仓库独立核验。"
        ),
        support_evidence=["用户明确提供的项目背景"],
    )]

    low = context.lower()
    repository_corpus = " ".join([
        architecture.architecture_style,
        *architecture.architecture_strengths,
        *architecture.architecture_risks,
        *tech.deployment,
        *tech.middlewares,
        *(commit.message for commit in commits),
        *(path for commit in commits for path in commit.changed_files),
    ]).lower()

    if any(word in low for word in ("高可用", "high availability", "ha 架构")):
        assessments.append(_availability_assessment(repository_corpus, architecture, tech))
    if any(word in low for word in ("高并发", "high concurrency", "大并发")):
        assessments.append(_concurrency_assessment(repository_corpus, tech))
    return assessments


def _availability_assessment(
    corpus: str,
    architecture: ArchitectureEvidence,
    tech: TechStackEvidence,
) -> ProjectContextAssessment:
    signals: list[str] = []
    if any(word in corpus for word in ("kubernetes", "nginx", "负载均衡", "load balanc")):
        signals.append("发现编排或负载均衡相关配置")
    if any(word in corpus for word in (
        "熔断", "降级", "限流", "failover", "circuit breaker", "health check", "重试",
    )):
        signals.append("发现容错、健康检查或流量保护机制")
    if any(word in corpus for word in ("prometheus", "grafana", "监控", "告警", "chaos")):
        signals.append("发现监控、告警或故障演练相关证据")

    if len(signals) >= 2:
        risk = RISK_NEEDS_CONFIRMATION
        analysis = "仓库存在部分高可用设计信号，但仍需部署拓扑、故障演练或线上监控数据确认整体效果。"
    else:
        risk = RISK_RISKY
        analysis = (
            "仓库证据不足以证明整体项目满足高可用要求；"
            "未形成可核验的冗余部署、故障转移、流量保护和可观测性证据链。"
        )
    evidence = signals or [
        f"架构判断：{architecture.architecture_style}",
        f"部署识别：{'、'.join(tech.deployment) or '未识别'}",
    ]
    return ProjectContextAssessment(
        statement="整体项目满足高可用要求",
        risk_level=risk,
        analysis=analysis,
        support_evidence=evidence,
    )


def _concurrency_assessment(
    corpus: str,
    tech: TechStackEvidence,
) -> ProjectContextAssessment:
    mechanism_signals: list[str] = []
    if any(name in tech.middlewares for name in ("Redis", "Kafka", "RabbitMQ", "RocketMQ")):
        mechanism_signals.append(f"中间件：{'、'.join(tech.middlewares)}")
    if any(word in corpus for word in ("异步", "队列", "缓存", "cache", "限流", "rate limit")):
        mechanism_signals.append("发现缓存、异步或流量保护相关实现")
    benchmark = any(word in corpus for word in (
        "benchmark", "压测", "load test", "jmeter", "gatling", "k6", "qps", "tps", "p95", "p99",
    ))

    if benchmark and mechanism_signals:
        risk = RISK_NEEDS_CONFIRMATION
        analysis = "仓库存在并发处理机制与压测信号，但整体高并发能力仍需核验压测报告、数据规模与部署环境。"
    else:
        risk = RISK_RISKY
        analysis = (
            "仓库证据不足以证明整体项目满足高并发要求；"
            "即使存在缓存或消息中间件，也缺少可核验的压测、吞吐量或线上监控数据。"
        )
    evidence = mechanism_signals[:2]
    evidence.append("压测/监控证据：已识别" if benchmark else "压测/监控证据：未识别")
    return ProjectContextAssessment(
        statement="整体项目满足高并发要求",
        risk_level=risk,
        analysis=analysis,
        support_evidence=evidence,
    )

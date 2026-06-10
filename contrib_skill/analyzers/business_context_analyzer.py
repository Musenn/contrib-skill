"""BusinessContextAnalyzer：从 README、命名与提交语义推断业务背景。

业务背景大多是推断，输出必须携带置信度与待确认问题。
"""
from __future__ import annotations

from pathlib import Path

from ..models import (
    BusinessContextEvidence,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    Commit,
)
from ..utils.file_utils import safe_read_text
from .repo_scanner import RepoStructure

_DOMAIN_KEYWORDS: list[tuple[str, list[str]]] = [
    ("电商/订单交易", ["order", "cart", "sku", "spu", "goods", "product", "订单",
                    "商品", "购物车", "下单", "库存", "inventory"]),
    ("支付", ["payment", "pay", "refund", "支付", "退款", "回调", "账单", "billing"]),
    ("用户中心/账号体系", ["user", "account", "profile", "register", "login",
                       "用户", "注册", "登录", "会员"]),
    ("内容管理", ["cms", "article", "post", "content", "文章", "内容", "发布"]),
    ("舆情/情感分析", ["sentiment", "舆情", "情感", "opinion", "monitor"]),
    ("AI Agent / LLM 应用", ["agent", "llm", "prompt", "chat", "rag", "embedding",
                          "大模型", "智能体", "对话"]),
    ("数据分析/数据处理", ["etl", "pipeline", "analytics", "dashboard", "report",
                       "数据分析", "报表", "指标", "数仓"]),
    ("后台管理系统", ["admin", "管理后台", "后台", "console", "管理系统"]),
    ("金融", ["finance", "stock", "trade", "风控", "金融", "quant", "行情"]),
    ("教育", ["course", "exam", "教育", "课程", "题库", "学习"]),
    ("CRM", ["crm", "customer", "客户管理", "线索", "lead"]),
    ("OA/协同办公", ["oa", "approval", "审批", "考勤", "工作流", "workflow"]),
    ("物流", ["logistics", "shipping", "delivery", "物流", "运单", "仓储"]),
    ("医疗", ["medical", "hospital", "patient", "医疗", "挂号", "问诊"]),
    ("通知/消息服务", ["notify", "notification", "message", "通知", "消息推送", "提醒"]),
]

_STANDARD_QUESTIONS = [
    "这个项目是真实上线、内部使用，还是课程/练习项目？",
    "项目的实际用户是谁？大概什么量级？",
    "项目立项的直接原因是什么（业务痛点 / 课程要求 / 个人兴趣）？",
    "是否有线上运行数据（QPS、日活、数据量）可以补充？",
    "团队总人数和分工是怎样的？",
]


def analyze_business_context(
    repo_path: Path | str,
    structure: RepoStructure,
    commits: list[Commit],
    project_name: str,
) -> BusinessContextEvidence:
    ev = BusinessContextEvidence(
        missing_information_questions=list(_STANDARD_QUESTIONS)
    )
    root = Path(repo_path).resolve()

    readme_text = ""
    if structure.readme_path:
        readme_text = safe_read_text(root / structure.readme_path, max_chars=8000)
        ev.evidence_sources.append(f"README: {structure.readme_path}")

    corpus_parts = [
        project_name,
        readme_text,
        " ".join(structure.module_paths),
        " ".join(c.message for c in commits[:300]),
        " ".join(f for c in commits[:300] for f in c.changed_files[:20]),
    ]
    corpus = "\n".join(corpus_parts).lower()

    scores: dict[str, int] = {}
    hit_words: dict[str, list[str]] = {}
    for domain, keywords in _DOMAIN_KEYWORDS:
        hits = [kw for kw in keywords if kw.lower() in corpus]
        if hits:
            scores[domain] = len(hits)
            hit_words[domain] = hits

    if scores:
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        top_domain, top_score = ranked[0]
        ev.inferred_domain = top_domain
        ev.evidence_sources.append(
            f"领域关键词命中：{', '.join(hit_words[top_domain][:8])}"
        )
        secondary = [d for d, s in ranked[1:3] if s >= 2]
        if secondary:
            ev.inferred_domain += f"（次要相关：{', '.join(secondary)}）"
    else:
        ev.inferred_domain = "通用工具项目（推断，证据不足）"

    # 项目目标：优先取 README 第一段（事实），否则给推断
    first_para = _first_paragraph(readme_text)
    if first_para:
        ev.project_goal = f"README 描述（事实）：{first_para}"
        ev.solved_problem = "推断：见 README 描述；具体业务痛点建议向项目负责人确认"
    else:
        ev.project_goal = f"推断：围绕「{ev.inferred_domain}」领域的系统，无 README 佐证"
        ev.solved_problem = "无法从仓库内容确定项目解决的具体问题，需要补充确认"

    ev.target_users = "推断：需结合业务方确认（仓库内无直接证据）"
    ev.core_business_flow = _infer_flow(corpus)

    if readme_text and scores:
        ev.confidence = CONFIDENCE_HIGH if scores[next(iter(sorted(scores, key=scores.get, reverse=True)))] >= 4 else CONFIDENCE_MEDIUM
    elif scores:
        ev.confidence = CONFIDENCE_MEDIUM
    else:
        ev.confidence = CONFIDENCE_LOW
    return ev


def _first_paragraph(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#") or s.startswith("!["):
            continue
        if not s:
            if lines:
                break
            continue
        lines.append(s)
        if len(lines) >= 4:
            break
    return " ".join(lines)[:300]


def _infer_flow(corpus: str) -> str:
    flows = []
    if "login" in corpus or "登录" in corpus:
        flows.append("用户登录/鉴权")
    if "order" in corpus or "订单" in corpus:
        flows.append("订单创建与状态流转")
    if "pay" in corpus or "支付" in corpus:
        flows.append("支付与回调处理")
    if "notify" in corpus or "通知" in corpus:
        flows.append("消息/通知触达")
    if "report" in corpus or "报表" in corpus:
        flows.append("数据统计与报表")
    if flows:
        return "推断：" + " → ".join(flows)
    return "无法从代码中还原核心业务流程，需补充确认"

"""InterviewGenerator：基于证据生成面试话术。回答贴合 evidence，不夸大。"""
from __future__ import annotations

from ..models import (
    AnalysisResult,
    AuthorEvidence,
    GitCommitEvidence,
)


def generate_interview(
    result: AnalysisResult,
    author_ev: AuthorEvidence,
    author_commits: list[GitCommitEvidence],
) -> dict:
    project = result.project
    biz = result.business
    arch = result.architecture
    tech = result.tech_stack

    tech_str = "、".join(
        (tech.frameworks[:4] + tech.databases[:2] + tech.middlewares[:2]) or ["仓库内可见技术栈"]
    )
    modules_str = "、".join(
        [m for m in author_ev.main_modules if m != "(root)"][:3]
        or author_ev.main_modules[:3]
    ) or "若干模块"

    intro_30s = (
        f"这个项目是{_short_domain(biz.inferred_domain)}方向的系统（{project.project_name}），"
        f"技术栈以 {tech_str} 为主。我在其中{_my_part(author_ev)}，"
        f"主要工作集中在 {modules_str}。"
    )

    intro_1m = intro_30s + (
        f"\n\n架构上，{arch.architecture_style}（置信度：{arch.confidence}）。"
        f"我从 {_fmt_date(author_ev.first_commit_date)} 到 "
        f"{_fmt_date(author_ev.last_commit_date)} 共提交 {author_ev.commit_count} 次，"
        f"变更类型以 {_top_types(author_ev)} 为主。"
    )

    intro_3m = intro_1m + (
        f"\n\n业务背景方面：{biz.project_goal}\n"
        f"核心流程：{biz.core_business_flow}\n"
        f"我的具体贡献都有 commit 可查，代表性提交："
        f"{', '.join(author_ev.evidence_commits[:5])}。"
        "讲项目时我会按「背景 → 我负责的模块 → 具体改动 → 验证方式」的顺序展开。"
    )

    difficulties = _difficulties(author_commits)

    faq = _build_faq(result, author_ev, author_commits)

    weaknesses = list(arch.architecture_risks) or ["项目不足需结合实际运行情况补充"]
    improvements = [
        "补充自动化测试与覆盖率统计" if not result.analysis_params.get("has_tests") else "扩展测试场景",
        "完善监控与指标采集，让性能/稳定性有数据可讲",
        "梳理文档，沉淀架构决策记录",
    ]

    anti_grilling = [
        "只讲有 commit 证据的内容；面试官追问细节时，落到具体文件和改动上",
        f"明确个人边界：你的主要模块是 {modules_str}，其他模块如实说「了解但非我负责」",
        "量化指标没有真实数据就不要说；可以说「当时没有做系统压测，这是我后续会补的」",
        "项目性质（上线/课程/练习）如实回答，背调一查便知",
        "提前准备好「如果重新设计会怎么改」——这题答得好可以化被动为主动",
    ]

    return {
        "intro_30s": intro_30s,
        "intro_1m": intro_1m,
        "intro_3m": intro_3m,
        "difficulties": difficulties,
        "contribution_pitch": _contribution_pitch(author_ev),
        "faq": faq,
        "weaknesses": weaknesses,
        "improvements": improvements,
        "anti_grilling": anti_grilling,
    }


def _short_domain(domain: str) -> str:
    return domain.split("（")[0]


def _my_part(author_ev: AuthorEvidence) -> str:
    roles = "、".join(author_ev.contribution_roles[:3])
    return f"承担{roles}的角色"


def _fmt_date(dt) -> str:
    return dt.strftime("%Y-%m") if dt else "未知"


def _top_types(author_ev: AuthorEvidence) -> str:
    dist = sorted(author_ev.change_type_distribution.items(), key=lambda kv: -kv[1])
    return "、".join(t for t, _ in dist[:3]) or "unknown"


def _difficulties(commits: list[GitCommitEvidence]) -> list[dict]:
    out = []
    interesting = [
        e for e in commits
        if e.inferred_type in ("performance", "refactor", "security", "bugfix")
    ]
    for e in interesting[:3]:
        out.append({
            "title": f"[{e.inferred_type}] {e.message}",
            "detail": (
                f"涉及文件：{', '.join(e.changed_files[:4])}。"
                f"{e.possible_impact}。"
                "面试讲法：还原当时的问题现象 → 定位过程 → 这次提交的改动 → 如何验证。"
                "具体细节请结合本人记忆补充，此处仅给出证据锚点。"
            ),
            "evidence": f"commit {e.short_hash}",
        })
    if not out:
        out.append({
            "title": "未从提交记录中识别出明显的难点型提交",
            "detail": "建议从实际开发记忆中挑选难点，并找到对应 commit 作为证据",
            "evidence": "",
        })
    return out


def _contribution_pitch(author_ev: AuthorEvidence) -> str:
    return (
        f"个人贡献建议这样讲：我在项目中共提交 {author_ev.commit_count} 次"
        f"（+{author_ev.total_additions}/-{author_ev.total_deletions} 行），"
        f"集中在 {', '.join(author_ev.main_modules[:3])}。"
        f"角色上属于{('、'.join(author_ev.contribution_roles[:2]))}。"
        "讲的时候按模块说具体做了什么，不要说「整个项目都是我做的」——"
        "除非 Git 记录确实支持这一点。"
    )


def _build_faq(
    result: AnalysisResult,
    author_ev: AuthorEvidence,
    author_commits: list[GitCommitEvidence],
) -> list[dict]:
    biz = result.business
    arch = result.architecture
    tech = result.tech_stack
    has_test = any(e.inferred_type == "test" for e in author_commits)
    has_security = any(e.inferred_type == "security" for e in author_commits)
    has_perf = any(e.inferred_type == "performance" for e in author_commits)

    def yn(flag: bool, yes: str, no: str) -> str:
        return yes if flag else no

    return [
        {"q": "这个项目为什么要做？",
         "a": f"{biz.project_goal} 注意：这部分若是推断，请结合真实立项背景回答，"
              f"并准备回答「{biz.missing_information_questions[0]}」"},
        {"q": "你主要负责哪部分？",
         "a": f"如实回答：{', '.join(author_ev.main_modules[:3])}。"
              f"模块归属等级：{author_ev.module_ownership}。"
              "不要把归属等级为「参与/协助」的模块说成「负责」"},
        {"q": "项目整体架构是什么？",
         "a": f"{arch.architecture_style}。分层情况：{'；'.join(arch.layer_analysis[:4]) or '从目录无法识别明显分层'}"},
        {"q": "为什么选择这个技术栈？",
         "a": f"仓库可见技术栈：{', '.join(tech.frameworks[:5])}。"
              "选型理由仓库无法还原——如果选型不是你做的，就说「我加入时选型已定，"
              "我的理解是……」，这比编造选型故事安全"},
        {"q": "你遇到的最大难点是什么？",
         "a": "从「技术难点」一节挑一个有 commit 证据的，按 问题→定位→方案→验证 展开"},
        {"q": "有没有做性能优化？",
         "a": yn(has_perf,
                 "有 performance 类提交，可以讲；但优化效果数字必须有真实测量才能说",
                 "你的提交中未发现明显性能优化类改动，建议回答「这个项目里我没有专门做性能优化，"
                 "但我了解……」，不要现编")},
        {"q": "有没有做权限控制？",
         "a": yn(has_security,
                 "有 security 类提交，可结合具体文件讲",
                 "你的提交中未发现权限/安全类改动，如项目中有此模块但非你负责，如实说明")},
        {"q": "有没有做测试？",
         "a": yn(has_test,
                 "有 test 类提交，可讲测试策略与覆盖场景",
                 "你的提交中未发现测试类改动，建议如实回答并表达补测试的意识")},
        {"q": "你说你负责这个模块，具体证据是什么？",
         "a": f"可直接引用 commit：{', '.join(author_ev.evidence_commits[:5])}。"
              "这是本工具存在的意义——你说的每句话都应有 commit 兜底"},
        {"q": "这个项目是真实上线还是课程/练习项目？",
         "a": "如实回答。仓库无法证明上线状态，谎称上线属于高风险行为，背调易暴露"},
        {"q": "你的贡献和其他人的边界是什么？",
         "a": f"全仓库共 {len(result.authors)} 位作者。你的等级：{author_ev.contribution_level}。"
              "清晰说出自己模块边界反而是加分项"},
        {"q": "如果重新设计，你会怎么改？",
         "a": f"可从架构风险入手：{'；'.join(arch.architecture_risks[:3]) or '结合实际痛点回答'}"},
    ]

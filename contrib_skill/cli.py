"""contrib-skill CLI 入口与分析编排。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .analyzers.architecture_analyzer import analyze_architecture
from .analyzers.author_profiler import build_author_evidence, compute_all_scores
from .analyzers.business_context_analyzer import analyze_business_context
from .analyzers.claim_risk_checker import module_ownership
from .analyzers.diff_analyzer import classify_commit
from .analyzers.git_analyzer import GitAnalyzer
from .analyzers.repo_scanner import scan_repo
from .analyzers.tech_stack_detector import detect_tech_stack
from .config import AnalyzeOptions, LANGUAGES, MODES
from .generators.interview_generator import generate_interview
from .generators.report_generator import ReportGenerator
from .generators.resume_generator import generate_resume
from .models import AnalysisResult, ProjectEvidence

app = typer.Typer(
    name="contrib-skill",
    help="代码贡献洞察与项目包装工具：基于 Git 证据链分析贡献，生成可背调的简历与面试材料",
    no_args_is_help=True,
)
console = Console()


@app.callback()
def _root() -> None:
    """contrib-skill：基于 Git 证据链的贡献洞察工具。"""


@app.command()
def analyze(
    repo: str = typer.Option(".", "--repo", help="Git 仓库路径"),
    author: Optional[str] = typer.Option(None, "--author", help="目标作者名称或邮箱（支持子串匹配）"),
    all_authors: bool = typer.Option(False, "--all-authors", help="分析所有作者"),
    base: Optional[str] = typer.Option(None, "--base", help="对比基础分支，如 main"),
    branch: Optional[str] = typer.Option(None, "--branch", help="目标分支，如 feature/order"),
    since: Optional[str] = typer.Option(None, "--since", help="起始日期，如 2025-01-01"),
    until: Optional[str] = typer.Option(None, "--until", help="截止日期，如 2025-06-01"),
    mode: str = typer.Option("full", "--mode", help=f"分析模式：{'/'.join(MODES)}"),
    target_role: str = typer.Option("", "--target-role", help="目标岗位，如 Java后端开发工程师"),
    language: str = typer.Option("zh", "--language", help=f"输出语言：{'/'.join(LANGUAGES)}（MVP 报告以中文为主，简历含英文版）"),
    output: str = typer.Option("./contrib_output", "--output", help="输出目录"),
    max_commits: int = typer.Option(2000, "--max-commits", help="最大分析 commit 数"),
    include_diff: bool = typer.Option(False, "--include-diff", help="evidence 中保留逐文件 numstat"),
    strict: bool = typer.Option(False, "--strict", help="严格模式：只保留 safe 等级的简历表述"),
):
    """分析仓库并生成贡献洞察报告。"""
    opts = AnalyzeOptions(
        repo=repo, author=author, all_authors=all_authors, base=base,
        branch=branch, since=since, until=until, mode=mode,
        target_role=target_role, language=language, output=output,
        max_commits=max_commits, include_diff=include_diff, strict=strict,
    )
    try:
        result, structure, resume, interview = run_analysis(opts)
    except ValueError as exc:
        console.print(f"[red]错误：{exc}[/red]")
        raise typer.Exit(code=1)

    gen = ReportGenerator(opts.output)
    written = gen.write_all(
        result, structure, resume, interview, mode=opts.normalized_mode()
    )
    _print_summary(result, written)


def run_analysis(opts: AnalyzeOptions):
    """执行完整分析流水线，返回 (AnalysisResult, RepoStructure, resume, interview)。"""
    repo_path = Path(opts.repo).resolve()
    analyzer = GitAnalyzer(repo_path)
    commits = analyzer.collect_commits(
        base=opts.base, branch=opts.branch,
        since=opts.since, until=opts.until,
        max_commits=opts.max_commits,
    )
    if not commits:
        raise ValueError("指定范围内没有任何 commit，请检查分支/时间过滤条件")

    structure = scan_repo(repo_path)
    tech = detect_tech_stack(repo_path, structure)
    arch = analyze_architecture(structure, tech)
    project_name = repo_path.name
    biz = analyze_business_context(repo_path, structure, commits, project_name)

    # commit 语义分类
    commit_evidence = [classify_commit(c, opts.include_diff) for c in commits]
    evidence_by_hash = {e.hash: e for e in commit_evidence}

    # 作者聚合与画像
    author_stats = GitAnalyzer.aggregate_authors(commits)
    evidence_by_author = {
        key: [evidence_by_hash[h] for h in st.commit_hashes]
        for key, st in author_stats.items()
    }
    all_scores = compute_all_scores(evidence_by_author)

    authors = []
    for key, st in author_stats.items():
        ev = build_author_evidence(
            key, st, evidence_by_author[key], commits, all_scores
        )
        ev.module_ownership = module_ownership(
            st, author_stats, key, evidence_by_author[key]
        )
        authors.append(ev)
    authors.sort(key=lambda a: -a.commit_count)

    # 目标作者
    target_key, target_ev = _resolve_target(opts, author_stats, authors)

    project = ProjectEvidence(
        repo_path=str(repo_path),
        project_name=project_name,
        languages=tech.languages,
        frameworks=tech.frameworks,
        databases=tech.databases,
        middlewares=tech.middlewares,
        deployment=tech.deployment,
        architecture_style=arch.architecture_style,
        inferred_domain=biz.inferred_domain,
        confidence=biz.confidence,
    )

    result = AnalysisResult(
        project=project,
        tech_stack=tech,
        architecture=arch,
        business=biz,
        commits=commit_evidence,
        authors=authors,
        target_author=opts.author or "",
        analysis_params={
            "base": opts.base, "branch": opts.branch,
            "since": opts.since, "until": opts.until,
            "mode": opts.normalized_mode(), "strict": opts.strict,
            "max_commits": opts.max_commits,
            "has_tests": bool(structure.test_dirs),
        },
    )

    resume = interview = None
    if target_ev is not None:
        target_commits = evidence_by_author.get(target_key, [])
        resume = generate_resume(
            target_ev, target_commits, tech,
            target_role=opts.target_role, strict=opts.strict,
        )
        interview = generate_interview(result, target_ev, target_commits)
        result.resume_claims = (
            resume["conservative"] + resume["standard"] + resume["enhanced"]
        )
    return result, structure, resume, interview


def _resolve_target(opts: AnalyzeOptions, author_stats, authors):
    """确定简历/面试材料的目标作者。"""
    if opts.author:
        needle = opts.author.lower()
        for key, st in author_stats.items():
            names = [st.name, st.email, *st.aliases]
            if any(needle in n.lower() for n in names):
                ev = next(a for a in authors if a.author_email == st.email)
                return key, ev
        available = "、".join(
            f"{st.name} <{st.email}>" for st in author_stats.values()
        )
        raise ValueError(
            f"未找到作者「{opts.author}」。仓库内的作者有：{available}"
        )
    if opts.all_authors:
        # 全员分析：简历/面试材料默认生成给提交数最高的作者，并在报告中说明
        if authors:
            top = authors[0]
            key = next(
                k for k, st in author_stats.items() if st.email == top.author_email
            )
            return key, top
    return None, None


def _print_summary(result: AnalysisResult, written: list[Path]) -> None:
    console.print(f"\n[bold green]分析完成[/bold green]：{result.project.project_name}")
    console.print(
        f"领域（推断）：{result.business.inferred_domain}"
        f"（置信度：{result.business.confidence}）"
    )
    console.print(f"架构（推断）：{result.architecture.architecture_style}\n")

    table = Table(title="作者贡献概况")
    table.add_column("作者")
    table.add_column("提交", justify="right")
    table.add_column("+/-", justify="right")
    table.add_column("主要模块")
    table.add_column("贡献等级")
    for a in result.authors:
        table.add_row(
            a.author_name,
            str(a.commit_count),
            f"+{a.total_additions}/-{a.total_deletions}",
            "、".join(a.main_modules[:3]),
            a.contribution_level,
        )
    console.print(table)

    if result.resume_claims:
        risky = sum(1 for c in result.resume_claims if c.risk_level == "risky")
        confirm = sum(
            1 for c in result.resume_claims if c.risk_level == "needs_confirmation"
        )
        console.print(
            f"\n简历表述：{len(result.resume_claims)} 条 "
            f"（risky {risky} 条，needs_confirmation {confirm} 条，详见风险报告）"
        )
    console.print("\n[bold]输出文件：[/bold]")
    for p in written:
        console.print(f"  - {p}")

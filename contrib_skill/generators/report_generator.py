"""ReportGenerator：汇总所有分析结果，输出 Markdown 报告与 JSON 证据。"""
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..analyzers.repo_scanner import RepoStructure
from ..models import AnalysisResult, AuthorEvidence, GitCommitEvidence

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

# 模式 -> 需要输出的 Markdown 文件键
MODE_SECTIONS = {
    "full": ["overview", "architecture", "git", "author", "key_commits",
             "resume", "interview", "risk"],
    "strict": ["overview", "architecture", "git", "author", "key_commits",
               "resume", "interview", "risk"],
    "resume": ["overview", "author", "resume", "risk"],
    "interview": ["overview", "architecture", "author", "interview", "risk"],
    "audit": ["git", "author", "key_commits", "risk"],
}

class ReportGenerator:
    def __init__(self, output_dir: Path | str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(_TEMPLATE_DIR),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def write_all(
        self,
        result: AnalysisResult,
        structure: RepoStructure,
        resume: dict | None,
        interview: dict | None,
        mode: str = "full",
    ) -> list[Path]:
        written: list[Path] = []
        sections_wanted = MODE_SECTIONS.get(mode, MODE_SECTIONS["full"])
        target_author_ev = self._target_author_ev(result)

        # JSON 证据与指标（任何模式都输出）
        written.append(self._write_json("evidence.json", result.model_dump(mode="json")))
        written.append(self._write_json("metrics.json", self._metrics(result)))

        bodies: dict[str, str] = {}
        if "overview" in sections_wanted:
            bodies["overview"] = self._overview_md(result, structure)
            written.append(self._write_md("01_project_overview.md", bodies["overview"]))
        if "architecture" in sections_wanted:
            bodies["architecture"] = self._architecture_md(result)
            written.append(self._write_md("02_architecture_analysis.md", bodies["architecture"]))
        if "git" in sections_wanted:
            bodies["git"] = self._git_summary_md(result)
            written.append(self._write_md("03_git_history_summary.md", bodies["git"]))
        if "author" in sections_wanted:
            bodies["author"] = self._authors_md(result)
            written.append(self._write_md("04_author_contribution.md", bodies["author"]))
        if "key_commits" in sections_wanted:
            bodies["key_commits"] = self._key_commits_md(result)
            written.append(self._write_md("05_key_commits_analysis.md", bodies["key_commits"]))
        if "resume" in sections_wanted and resume is not None:
            bodies["resume"] = self.env.get_template("resume.md.j2").render(
                resume=resume,
                author_name=target_author_ev.author_name if target_author_ev else "",
            )
            written.append(self._write_md("06_resume_bullets.md", bodies["resume"]))
        if "interview" in sections_wanted and interview is not None:
            bodies["interview"] = self.env.get_template("interview.md.j2").render(
                interview=interview,
                author_name=target_author_ev.author_name if target_author_ev else "",
            )
            written.append(self._write_md("07_interview_script.md", bodies["interview"]))
        if "risk" in sections_wanted:
            bodies["risk"] = self.env.get_template("risk.md.j2").render(
                claims=[c.model_dump() for c in result.resume_claims],
            )
            written.append(self._write_md("08_claim_risk_report.md", bodies["risk"]))

        full = self.env.get_template("full_report.md.j2").render(
            project_name=result.project.project_name,
            repo_path=result.project.repo_path,
            target_author=result.target_author,
            params=json.dumps(result.analysis_params, ensure_ascii=False),
            sections=[bodies[k] for k in sections_wanted if k in bodies],
        )
        written.append(self._write_md("full_report.md", full))
        return written

    # ---------- 内部工具 ----------

    @staticmethod
    def _target_author_ev(result: AnalysisResult) -> AuthorEvidence | None:
        if not result.target_author:
            return result.authors[0] if result.authors else None
        needle = result.target_author.lower()
        for a in result.authors:
            if needle in a.author_name.lower() or needle in a.author_email.lower():
                return a
        return None

    def _write_json(self, name: str, data: dict) -> Path:
        path = self.output_dir / name
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        return path

    def _write_md(self, name: str, content: str) -> Path:
        path = self.output_dir / name
        path.write_text(content, encoding="utf-8")
        return path

    @staticmethod
    def _metrics(result: AnalysisResult) -> dict:
        type_dist: dict[str, int] = {}
        for c in result.commits:
            type_dist[c.inferred_type] = type_dist.get(c.inferred_type, 0) + 1
        return {
            "total_commits": len(result.commits),
            "total_authors": len(result.authors),
            "commit_type_distribution": type_dist,
            "authors": [
                {
                    "name": a.author_name,
                    "email": a.author_email,
                    "commits": a.commit_count,
                    "additions": a.total_additions,
                    "deletions": a.total_deletions,
                    "contribution_level": a.contribution_level,
                }
                for a in result.authors
            ],
        }

    @staticmethod
    def _overview_md(result: AnalysisResult, structure: RepoStructure) -> str:
        p, b, t = result.project, result.business, result.tech_stack
        langs = "、".join(
            f"{k}({v})" for k, v in
            sorted(t.languages.items(), key=lambda kv: -kv[1])[:5]
        ) or "未识别"
        lines = [
            "# 项目概览",
            "",
            f"- **项目名称**：{p.project_name}",
            f"- **仓库路径**：{p.repo_path}",
            f"- **主要语言**（按文件数）：{langs}",
            f"- **框架**：{'、'.join(t.frameworks) or '未识别'}",
            f"- **数据库**：{'、'.join(t.databases) or '未识别'}",
            f"- **中间件**：{'、'.join(t.middlewares) or '未识别'}",
            f"- **构建工具**：{'、'.join(t.build_tools) or '未识别'}",
            f"- **部署方式**：{'、'.join(t.deployment) or '未识别'}",
            f"- **依赖证据文件**：{'、'.join(t.evidence_files[:6]) or '无'}",
            "",
            "## 业务背景（推断为主，注意置信度）",
            "",
            f"- **推断业务领域**：{b.inferred_domain}（置信度：{b.confidence}）",
            f"- **项目目标**：{b.project_goal}",
            f"- **解决的问题**：{b.solved_problem}",
            f"- **目标用户**：{b.target_users}",
            f"- **核心业务流程**：{b.core_business_flow}",
            f"- **证据来源**：{'；'.join(b.evidence_sources) or '无'}",
            "",
            "## 待确认问题（写简历/面试前建议先回答）",
            "",
        ]
        lines += [f"{i}. {q}" for i, q in enumerate(b.missing_information_questions, 1)]
        lines += [
            "",
            "## 目录结构要点",
            "",
            f"- 顶层目录：{'、'.join(structure.top_dirs[:12]) or '（空）'}",
            f"- 关键目录：{'、'.join(structure.key_dirs[:8]) or '未识别'}",
            f"- 测试目录：{'、'.join(structure.test_dirs[:5]) or '未发现'}",
            f"- README：{structure.readme_path or '未发现'}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _architecture_md(result: AnalysisResult) -> str:
        a = result.architecture
        lines = [
            "# 架构分析",
            "",
            f"- **架构风格**：{a.architecture_style}",
            f"- **置信度**：{a.confidence}",
            "",
            "## 分层分析",
            "",
        ]
        lines += [f"- {l}" for l in a.layer_analysis] or ["- 未识别出明显分层"]
        lines += ["", "## 模块地图", ""]
        for top, subs in list(a.module_map.items())[:15]:
            lines.append(f"- **{top}**：{'、'.join(subs[:6])}")
        if not a.module_map:
            lines.append("- 无")
        lines += ["", "## 依赖观察", ""]
        lines += [f"- {o}" for o in a.dependency_observations]
        lines += ["", "## 架构优势（基于可见证据）", ""]
        lines += [f"- {s}" for s in a.architecture_strengths] or ["- 证据不足"]
        lines += ["", "## 架构风险", ""]
        lines += [f"- {r}" for r in a.architecture_risks] or ["- 暂未发现明显风险"]
        return "\n".join(lines)

    @staticmethod
    def _git_summary_md(result: AnalysisResult) -> str:
        lines = [
            "# Git 历史摘要",
            "",
            f"- 分析 commit 总数：{len(result.commits)}",
            f"- 作者总数：{len(result.authors)}",
            "",
            "## 作者概况",
            "",
            "| 作者 | 提交数 | +行 | -行 | 首次提交 | 最近提交 | 贡献等级 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for a in sorted(result.authors, key=lambda x: -x.commit_count):
            first = a.first_commit_date.strftime("%Y-%m-%d") if a.first_commit_date else "-"
            last = a.last_commit_date.strftime("%Y-%m-%d") if a.last_commit_date else "-"
            lines.append(
                f"| {a.author_name} | {a.commit_count} | {a.total_additions} "
                f"| {a.total_deletions} | {first} | {last} | {a.contribution_level} |"
            )
        lines += [
            "",
            "> 说明：贡献等级综合变更类型权重与文件路径权重计算，不是单纯代码行数；",
            "> merge commit 不计入个人含金量分。",
        ]
        return "\n".join(lines)

    @staticmethod
    def _authors_md(result: AnalysisResult) -> str:
        lines = ["# 作者贡献分析", ""]
        for a in result.authors:
            first = a.first_commit_date.strftime("%Y-%m-%d") if a.first_commit_date else "-"
            last = a.last_commit_date.strftime("%Y-%m-%d") if a.last_commit_date else "-"
            dist = "、".join(
                f"{t}:{n}" for t, n in
                sorted(a.change_type_distribution.items(), key=lambda kv: -kv[1])
            )
            timeline = "、".join(f"{m}({n})" for m, n in a.activity_timeline.items())
            ownership = "、".join(
                f"{m}→{lvl}" for m, lvl in list(a.module_ownership.items())[:6]
            ) or "无"
            lines += [
                f"## {a.author_name} <{a.author_email}>",
                "",
                f"- 参与时间：{first} ~ {last}",
                f"- 提交：{a.commit_count} 次（+{a.total_additions}/-{a.total_deletions} 行）",
                f"- 主要模块：{'、'.join(a.main_modules) or '无'}",
                f"- 主要文件：{'、'.join(a.main_files[:6]) or '无'}",
                f"- 变更类型分布：{dist or '无'}",
                f"- 月度活跃：{timeline or '无'}",
                f"- 工作日/周末提交：{a.weekday_commits}/{a.weekend_commits}；"
                f"白天/夜间：{a.daytime_commits}/{a.night_commits}",
                f"- 是否参与项目初始化：{'是' if a.is_project_initializer else '否'}",
                f"- 是否触达核心模块：{'是' if a.touches_core_modules else '否'}",
                f"- 是否参与后期维护：{'是' if a.does_late_maintenance else '否'}",
                f"- 推断角色：{'、'.join(a.contribution_roles)}（推断，需本人确认）",
                f"- 贡献等级：**{a.contribution_level}**（与仓库内其他作者相对比较）",
                f"- 模块归属等级：{ownership}",
                f"- 证据 commit（前 10）：{'、'.join(a.evidence_commits[:10])}",
                "",
            ]
        return "\n".join(lines)

    @staticmethod
    def _key_commits_md(result: AnalysisResult) -> str:
        lines = [
            "# 关键 commit 分析",
            "",
            "> possible_reason / possible_impact 均为规则推断，已显式标注，不可当作事实。",
            "",
        ]
        key_types = {"architecture", "feature", "performance", "security",
                     "refactor", "bugfix"}
        shown = 0
        for c in result.commits:
            if c.inferred_type not in key_types or c.is_merge:
                continue
            shown += 1
            if shown > 30:
                break
            lines += [
                f"## {c.short_hash} [{c.inferred_type}] {c.message}",
                "",
                f"- 作者：{c.author_name} | 日期：{c.date.strftime('%Y-%m-%d')}",
                f"- 变更：+{c.additions}/-{c.deletions}，文件 {len(c.changed_files)} 个，"
                f"模块：{'、'.join(c.changed_modules[:5])}",
                f"- 主要文件：{'、'.join(c.changed_files[:5])}",
                f"- 类型置信度：{c.type_confidence}（关键词：{'、'.join(c.evidence_keywords[:5]) or '无'}）",
                f"- {c.possible_reason}",
                f"- {c.possible_impact}",
            ]
            if c.risk_notes:
                lines.append(f"- ⚠️ {c.risk_notes}")
            lines.append("")
        if shown == 0:
            lines.append("未识别出关键类型的 commit。")
        return "\n".join(lines)

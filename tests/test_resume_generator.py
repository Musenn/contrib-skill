import re

from contrib_skill.cli import run_analysis
from contrib_skill.config import AnalyzeOptions
from contrib_skill.generators.report_generator import ReportGenerator
from contrib_skill.generators.resume_generator import _claim_from_group, _project_summary


def _analyze_alice(sample_repo):
    opts = AnalyzeOptions(
        repo=str(sample_repo),
        author="Alice",
        mode="resume",
        target_role="Java后端开发工程师",
    )
    return run_analysis(opts)


def test_resume_entry_is_paste_ready(sample_repo):
    result, _, resume, _ = _analyze_alice(sample_repo)

    assert resume is not None
    assert len(resume["ready_bullets"]) >= 2
    assert result.resume_claims == resume["ready_bullets"]
    assert resume["project_entry"]["project_name"] == sample_repo.name
    assert resume["project_entry"]["subtitle"] == "电商订单与支付"
    summary = resume["project_entry"]["summary"]
    assert "电商订单与支付后端服务" in summary
    assert "基于 Express、MySQL、Redis" in summary
    assert "订单创建与状态流转、支付与回调处理" in summary
    assert "Controller/Service 分层" in summary

    texts = [claim.text for claim in resume["ready_bullets"]]
    assert any(
        "Controller 接口层、Service 业务层新增订单创建接口、实现订单状态流转" in text
        and "订单创建、业务处理与状态演进流程" in text
        for text in texts
    )
    assert all("次提交" not in text for text in texts)
    assert all("service 模块" not in text for text in texts)
    assert all(claim.support_evidence for claim in resume["ready_bullets"])
    assert resume["project_context_evidence"]

    unsupported_metrics = re.compile(
        r"\d+(?:\.\d+)?\s*%|百万级|千万级|亿级|\bqps\b|\btps\b",
        re.IGNORECASE,
    )
    assert not unsupported_metrics.search(summary)
    assert all(not unsupported_metrics.search(text) for text in texts)


def test_project_summary_adds_only_commit_backed_cache_context(sample_repo):
    result, _, _, _ = _analyze_alice(sample_repo)
    base_summary = _project_summary(
        result.business,
        result.architecture,
        result.tech_stack,
        result.commits,
    )
    assert "Redis 缓存优化订单查询" not in base_summary

    cache_commit = result.commits[0].model_copy(update={
        "message": "perf: 订单查询增加 redis 缓存",
        "inferred_type": "performance",
        "changed_files": ["src/service/order_service.js"],
        "changed_modules": ["service"],
    })
    rich_summary = _project_summary(
        result.business,
        result.architecture,
        result.tech_stack,
        [*result.commits, cache_commit],
    )
    assert "Redis 缓存优化订单查询" in rich_summary


def test_commit_context_enriches_personal_contributions(sample_repo):
    result, _, _, _ = _analyze_alice(sample_repo)
    author = next(a for a in result.authors if a.author_email == "alice@example.com")
    source = result.commits[0]

    payment_commit = source.model_copy(update={
        "message": "feat: 接入支付回调",
        "inferred_type": "feature",
        "changed_files": [
            "src/controller/payment_controller.js",
            "src/service/payment_service.js",
        ],
        "changed_modules": ["controller", "service"],
    })
    payment_claim = _claim_from_group(
        [payment_commit], author, result.tech_stack,
        business=result.business,
        architecture=result.architecture,
    )
    assert "Controller 接口层、Service 业务层" in payment_claim.text
    assert "支付结果接收与业务处理链路" in payment_claim.text

    cache_commit = source.model_copy(update={
        "message": "perf: 订单查询增加 redis 缓存",
        "inferred_type": "performance",
        "changed_files": ["src/service/order_service.js"],
        "changed_modules": ["service"],
    })
    cache_claim = _claim_from_group(
        [cache_commit], author, result.tech_stack,
        business=result.business,
        architecture=result.architecture,
    )
    assert "Service 业务层引入 Redis 缓存" in cache_claim.text
    assert "减少重复数据访问" in cache_claim.text


def test_commit_message_topic_outranks_generic_skill_path(sample_repo):
    result, _, _, _ = _analyze_alice(sample_repo)
    author = next(a for a in result.authors if a.author_email == "alice@example.com")
    report_commit = result.commits[0].model_copy(update={
        "message": "fix: 修复报告渲染与措辞问题",
        "inferred_type": "bugfix",
        "changed_files": ["contrib_skill/generators/report_generator.py"],
        "changed_modules": ["generators"],
    })

    claim = _claim_from_group(
        [report_commit], author, result.tech_stack,
        business=result.business,
        architecture=result.architecture,
    )

    assert "报告与简历生成链路稳定性治理" in claim.text
    assert "智能体工作流" not in claim.text
    assert "Agent" not in claim.text


def test_markdown_separates_resume_body_from_audit(sample_repo, tmp_path):
    result, structure, resume, _ = _analyze_alice(sample_repo)
    ReportGenerator(tmp_path).write_all(
        result, structure, resume, interview=None, mode="resume"
    )

    text = (tmp_path / "06_resume_bullets.md").read_text(encoding="utf-8")
    paste_area = text.split("## 证据映射", 1)[0]

    assert "## 可直接粘贴的项目条目" in paste_area
    assert "风险等级" not in paste_area
    assert "commit " not in paste_area
    assert "次提交" not in paste_area
    assert "`safe`- 证据" not in text
    assert "## 待本人确认后补强" in text

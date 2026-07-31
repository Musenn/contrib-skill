from contrib_skill.cli import run_analysis
from contrib_skill.config import AnalyzeOptions
from contrib_skill.generators.report_generator import ReportGenerator


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
    assert "电商订单与支付后端服务" in resume["project_entry"]["summary"]

    texts = [claim.text for claim in resume["ready_bullets"]]
    assert any("新增订单创建接口、实现订单状态流转" in text for text in texts)
    assert all("次提交" not in text for text in texts)
    assert all("service 模块" not in text for text in texts)
    assert all(claim.support_evidence for claim in resume["ready_bullets"])


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

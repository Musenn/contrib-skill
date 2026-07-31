from contrib_skill.analyzers.business_context_analyzer import (
    _first_paragraph,
    analyze_business_context,
)
from contrib_skill.analyzers.repo_scanner import RepoStructure


def test_first_paragraph_skips_logo_html():
    text = """<p align=\"center\">
<img src=\"logo.svg\">
</p>
<p align=\"center\">
<b>中文</b> | <a href=\"README.en.md\">English</a>
</p>
# contrib-skill

**代码贡献洞察与项目包装工具。**
"""
    assert _first_paragraph(text) == "**代码贡献洞察与项目包装工具。**"


def test_domain_uses_readme_intro_not_late_demo(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "# contrib-skill\n\n"
        "代码贡献洞察与简历包装工具，分析 Git commit 与仓库历史。\n\n"
        "## 示例\n\n下面用电商订单、支付回调和购物车作为演示。\n",
        encoding="utf-8",
    )
    structure = RepoStructure(root=str(tmp_path), readme_path="README.md")

    result = analyze_business_context(
        tmp_path, structure, commits=[], project_name="contrib-skill"
    )

    assert result.inferred_domain.startswith("开发者工具/Git 分析")
    assert "电商" not in result.inferred_domain
    assert "Git 提交与仓库结构解析" in result.core_business_flow
    assert "个人贡献与风险分析" in result.core_business_flow
    assert "简历与面试材料生成" in result.core_business_flow

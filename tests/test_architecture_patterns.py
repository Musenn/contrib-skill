from datetime import datetime, timezone

from contrib_skill.analyzers.architecture_analyzer import analyze_architecture
from contrib_skill.analyzers.repo_scanner import RepoStructure
from contrib_skill.models import Commit, FileStat, TechStackEvidence


def test_architecture_patterns_require_repository_path_evidence(tmp_path):
    structure = RepoStructure(
        root=str(tmp_path),
        module_paths=["src/domain", "src/application"],
        key_dirs=["src"],
        dependency_files=["pyproject.toml"],
    )
    commit = Commit(
        hash="a" * 40,
        short_hash="a" * 7,
        author_name="Alice",
        author_email="alice@example.com",
        date=datetime.now(timezone.utc),
        message="feat: add pricing strategy and repository",
        files=[
            FileStat(path="src/domain/pricing/discount_strategy.py"),
            FileStat(path="src/infrastructure/order_repository.py"),
        ],
    )
    tech = TechStackEvidence(frameworks=["FastAPI"])

    result = analyze_architecture(structure, tech, [commit])

    assert "DDD 领域驱动设计" in result.design_patterns
    assert "Repository 模式" in result.design_patterns
    assert "策略模式" in result.design_patterns
    assert result.pattern_evidence["DDD 领域驱动设计"]
    assert "DDD 分层架构" in result.architecture_style


def test_domain_directory_alone_does_not_claim_ddd(tmp_path):
    structure = RepoStructure(
        root=str(tmp_path),
        module_paths=["src/domain"],
        dependency_files=["pyproject.toml"],
    )

    result = analyze_architecture(
        structure,
        TechStackEvidence(frameworks=["FastAPI"]),
        commits=[],
    )

    assert "DDD 领域驱动设计" not in result.design_patterns
    assert "DDD" not in result.architecture_style

from contrib_skill.analyzers.repo_scanner import scan_repo
from contrib_skill.analyzers.tech_stack_detector import detect_tech_stack


def test_detect_from_package_json(sample_repo):
    structure = scan_repo(sample_repo)
    tech = detect_tech_stack(sample_repo, structure)
    assert "Express" in tech.frameworks
    assert "MySQL" in tech.databases
    assert "Redis" in tech.middlewares
    assert "Jest" in tech.test_tools
    assert "npm/yarn/pnpm" in tech.build_tools
    assert "package.json" in tech.evidence_files
    assert "后端" in tech.possible_architecture_style

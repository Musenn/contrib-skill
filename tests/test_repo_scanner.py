from contrib_skill.analyzers.repo_scanner import scan_repo


def test_scan_repo_basics(sample_repo):
    structure = scan_repo(sample_repo)
    assert structure.readme_path == "README.md"
    assert "package.json" in structure.dependency_files
    assert "src" in structure.top_dirs
    assert structure.language_file_counts.get("JavaScript", 0) >= 3


def test_skip_dirs(sample_repo, tmp_path):
    (sample_repo / "node_modules" / "lodash").mkdir(parents=True, exist_ok=True)
    (sample_repo / "node_modules" / "lodash" / "index.js").write_text("x")
    structure = scan_repo(sample_repo)
    assert "node_modules" not in structure.top_dirs
    assert all("node_modules" not in p for p in structure.module_paths)


def test_prefers_canonical_readme_over_localized_variant(tmp_path):
    (tmp_path / "README.en.md").write_text("English description", encoding="utf-8")
    (tmp_path / "README.md").write_text("中文项目介绍", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("示例目录说明", encoding="utf-8")

    structure = scan_repo(tmp_path)

    assert structure.readme_path == "README.md"

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

from contrib_skill.analyzers.git_analyzer import GitAnalyzer
from contrib_skill.utils.git_utils import run_git


def test_collect_commits(sample_repo):
    commits = GitAnalyzer(sample_repo).collect_commits()
    assert len(commits) == 5
    latest = commits[0]
    assert latest.message == "docs: update readme"
    assert latest.author_name == "Alice Zhang"
    assert latest.short_hash
    assert not latest.is_merge


def test_numstat_parsing(sample_repo):
    commits = GitAnalyzer(sample_repo).collect_commits()
    first = commits[-1]
    paths = {f.path for f in first.files}
    assert "package.json" in paths
    assert first.additions > 0


def test_since_filter(sample_repo):
    commits = GitAnalyzer(sample_repo).collect_commits(since="2025-02-01")
    assert len(commits) == 3
    assert all(c.date.month >= 2 for c in commits)


def test_max_commits(sample_repo):
    commits = GitAnalyzer(sample_repo).collect_commits(max_commits=2)
    assert len(commits) == 2


def test_aggregate_authors(sample_repo):
    commits = GitAnalyzer(sample_repo).collect_commits()
    stats = GitAnalyzer.aggregate_authors(commits)
    assert len(stats) == 2
    alice = stats["alice@example.com"]
    bob = stats["bob@example.com"]
    assert alice.commit_count == 4
    assert bob.commit_count == 1
    assert alice.first_commit_date.month == 1
    assert alice.last_commit_date.month == 3
    assert bob.night_commits == 1
    assert "service" in alice.module_counts or "src" in alice.module_counts


def test_run_git_forces_utf8_decoding(sample_repo, monkeypatch):
    import subprocess

    original_run = subprocess.run
    captured = {}

    def spy(*args, **kwargs):
        captured.update(kwargs)
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)
    output = run_git(sample_repo, "log", "-1", "--pretty=%s")

    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"
    assert "update readme" in output

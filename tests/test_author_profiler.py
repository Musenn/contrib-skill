from contrib_skill.analyzers.author_profiler import (
    build_author_evidence,
    compute_all_scores,
)
from contrib_skill.analyzers.claim_risk_checker import check_claim, module_ownership
from contrib_skill.analyzers.diff_analyzer import classify_commit
from contrib_skill.analyzers.git_analyzer import GitAnalyzer
from contrib_skill.models import RISK_RISKY, RISK_SAFE


def _profiles(sample_repo):
    commits = GitAnalyzer(sample_repo).collect_commits()
    stats = GitAnalyzer.aggregate_authors(commits)
    evidence = {c.hash: classify_commit(c) for c in commits}
    by_author = {
        key: [evidence[h] for h in st.commit_hashes]
        for key, st in stats.items()
    }
    scores = compute_all_scores(by_author)
    profiles = {}
    for key, st in stats.items():
        ev = build_author_evidence(key, st, by_author[key], commits, scores)
        ev.module_ownership = module_ownership(st, stats, key, by_author[key])
        profiles[key] = ev
    return profiles, by_author


def test_diff_classification(sample_repo):
    commits = GitAnalyzer(sample_repo).collect_commits()
    types = {c.message: classify_commit(c).inferred_type for c in commits}
    assert types["feat: 新增订单创建接口"] == "feature"
    assert types["fix: 修复支付回调空指针"] == "bugfix"
    assert types["docs: update readme"] == "docs"


def test_alice_profile(sample_repo):
    profiles, _ = _profiles(sample_repo)
    alice = profiles["alice@example.com"]
    assert alice.is_project_initializer
    assert alice.commit_count == 4
    assert alice.contribution_level in ("很高", "较高")
    assert "项目初始化者" in alice.contribution_roles


def test_bob_profile_is_modest(sample_repo):
    profiles, _ = _profiles(sample_repo)
    bob = profiles["bob@example.com"]
    assert not bob.is_project_initializer
    assert bob.contribution_level in ("较低", "低", "中等")


def test_claim_checker_blocks_strong_claims(sample_repo):
    profiles, _ = _profiles(sample_repo)
    bob = profiles["bob@example.com"]
    claim = check_claim("主导整体项目架构设计", bob, ["commit abc"])
    assert claim.risk_level == RISK_RISKY
    assert "证据不足" in claim.forbidden_reason


def test_claim_checker_blocks_unproven_metrics(sample_repo):
    profiles, _ = _profiles(sample_repo)
    alice = profiles["alice@example.com"]
    claim = check_claim("优化接口性能提升 30%", alice, ["commit abc"])
    assert claim.needs_user_confirmation
    assert "benchmark" in claim.forbidden_reason


def test_claim_checker_allows_evidenced_participation(sample_repo):
    profiles, _ = _profiles(sample_repo)
    alice = profiles["alice@example.com"]
    claim = check_claim(
        "参与 service 模块的开发与维护", alice, ["commit abc：order_service.js"]
    )
    assert claim.risk_level == RISK_SAFE

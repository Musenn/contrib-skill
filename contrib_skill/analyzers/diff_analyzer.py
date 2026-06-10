"""DiffAnalyzer：基于 commit message 与文件路径的规则分类。

输出的 possible_reason / possible_impact 一律为推断，文案中显式标注。
"""
from __future__ import annotations

from ..models import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    Commit,
    GitCommitEvidence,
)
from ..utils.file_utils import module_of_path
from ..utils.text_utils import find_keywords

# message 关键词规则，按优先级排列：先命中者类型优先
_MESSAGE_RULES: list[tuple[str, list[str]]] = [
    ("security", ["security", "auth", "permission", "jwt", "oauth", "encrypt",
                  "signature", "鉴权", "权限", "加密", "签名", "越权"]),
    ("performance", ["perf", "performance", "cache", "batch", "async", "index",
                     "pool", "parallel", "性能", "缓存", "优化耗时", "提速", "并发优化"]),
    ("bugfix", ["fix", "bug", "hotfix", "修复", "异常", "空指针", "报错", "npe",
                "崩溃", "bugfix"]),
    ("refactor", ["refactor", "重构", "抽取", "拆分", "优化结构", "整理代码", "解耦"]),
    ("test", ["test", "测试", "单测", "用例", "覆盖率"]),
    ("docs", ["doc", "docs", "readme", "文档", "注释", "说明"]),
    ("ci", ["ci", "pipeline", "workflow", "流水线"]),
    ("dependency", ["upgrade", "bump", "依赖", "升级版本", "dependency"]),
    ("config", ["config", "配置", "环境变量", "yml", "properties"]),
    ("style", ["style", "format", "lint", "格式化", "样式调整"]),
    ("architecture", ["architecture", "架构", "脚手架", "初始化项目", "init project",
                      "scaffold", "搭建框架"]),
    ("feature", ["feat", "add", "create", "implement", "新增", "实现", "支持",
                 "完成", "开发", "接入"]),
]

# 文件路径关键词规则
_PATH_RULES: list[tuple[str, list[str]]] = [
    ("ci", [".github/workflows", "gitlab-ci", "jenkinsfile"]),
    ("dependency", ["pom.xml", "package.json", "requirements.txt",
                    "pyproject.toml", "go.mod", "cargo.toml", "build.gradle"]),
    ("config", ["dockerfile", "docker-compose", "k8s", "nginx",
                "application.yml", "application.yaml", "application.properties",
                ".env", "config"]),
    ("test", ["/test/", "/tests/", "__tests__", ".spec.", "_test.", "test_"]),
    ("docs", ["readme", "/docs/", ".md"]),
    ("security", ["security", "auth", "permission", "jwt", "oauth", "encrypt",
                  "signature"]),
]

_TYPE_IMPACT_HINT = {
    "feature": "推断：为项目引入新功能或扩展既有能力",
    "bugfix": "推断：修复缺陷，提升稳定性与正确性",
    "refactor": "推断：改善代码结构与可维护性，不改变外部行为",
    "performance": "推断：优化性能相关路径（缓存/批处理/异步/索引等）",
    "security": "推断：加强认证、授权或数据安全",
    "test": "推断：补充测试，提升质量保障与回归能力",
    "docs": "推断：完善文档与说明，降低协作成本",
    "config": "推断：调整配置或部署相关设置",
    "architecture": "推断：搭建或调整项目基础结构",
    "dependency": "推断：管理第三方依赖版本",
    "build": "推断：调整构建流程",
    "ci": "推断：维护持续集成流水线",
    "style": "推断：代码风格或格式调整，无逻辑影响",
    "unknown": "无法从现有证据判断影响，需结合代码内容确认",
}


def classify_commit(commit: Commit, include_diff: bool = False) -> GitCommitEvidence:
    msg_type, msg_keywords = _match_rules(commit.message, _MESSAGE_RULES)

    joined_paths = "\n".join(commit.changed_files).lower()
    path_type, path_keywords = _match_rules(joined_paths, _PATH_RULES)

    if msg_type:
        inferred = msg_type
        confidence = CONFIDENCE_HIGH if path_type in (msg_type, None) else CONFIDENCE_MEDIUM
    elif path_type:
        inferred = path_type
        confidence = CONFIDENCE_MEDIUM
    else:
        inferred = "unknown"
        confidence = CONFIDENCE_LOW

    modules = sorted({module_of_path(p) for p in commit.changed_files})
    keywords = msg_keywords + path_keywords

    if inferred == "unknown":
        reason = "无法从 commit message 与文件路径推断动机，需人工确认"
    else:
        reason = f"推断：该提交属于 {inferred} 类变更（依据关键词 {', '.join(keywords[:5])}）"

    risk_notes = ""
    if commit.is_merge:
        risk_notes = "merge commit：变更可能来自他人分支，不应直接计为个人产出"

    return GitCommitEvidence(
        hash=commit.hash,
        short_hash=commit.short_hash,
        author_name=commit.author_name,
        author_email=commit.author_email,
        date=commit.date,
        message=commit.message,
        changed_files=commit.changed_files,
        additions=commit.additions,
        deletions=commit.deletions,
        file_stats=(
            [f.model_dump() for f in commit.files] if include_diff else []
        ),
        is_merge=commit.is_merge,
        inferred_type=inferred,
        type_confidence=confidence,
        changed_modules=modules,
        possible_reason=reason,
        possible_impact=_TYPE_IMPACT_HINT[inferred],
        evidence_keywords=keywords,
        risk_notes=risk_notes,
    )


def _match_rules(
    text: str, rules: list[tuple[str, list[str]]]
) -> tuple[str | None, list[str]]:
    for ctype, keywords in rules:
        hits = find_keywords(text, keywords)
        if hits:
            return ctype, hits
    return None, []

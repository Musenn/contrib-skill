"""RepoScanner：扫描项目目录结构，识别关键目录、配置、依赖与语言分布。"""
from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", "target", ".next", ".venv",
    "venv", "__pycache__", ".idea", ".vscode", "coverage", ".pytest_cache",
    ".mypy_cache", "out",
}

KEY_DIR_NAMES = {
    "src", "app", "apps", "server", "client", "frontend", "backend", "web",
    "api", "services", "service", "core", "common", "packages", "cmd",
    "internal", "pkg",
}

DEPENDENCY_FILES = {
    "pom.xml", "build.gradle", "build.gradle.kts", "package.json",
    "requirements.txt", "pyproject.toml", "setup.py", "go.mod", "Cargo.toml",
    "Gemfile", "composer.json",
}

CONFIG_FILE_HINTS = (
    "application.yml", "application.yaml", "application.properties",
    "config", ".env", "settings", "nginx",
)

DOCKER_CI_HINTS = (
    "dockerfile", "docker-compose", "k8s", "kubernetes", ".github/workflows",
    ".gitlab-ci", "jenkinsfile",
)

LANGUAGE_EXT = {
    ".py": "Python", ".java": "Java", ".kt": "Kotlin", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript",
    ".vue": "Vue", ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".cs": "C#", ".cpp": "C++", ".cc": "C++", ".c": "C", ".scala": "Scala",
    ".sql": "SQL", ".sh": "Shell", ".html": "HTML", ".css": "CSS",
    ".scss": "CSS", ".swift": "Swift", ".m": "Objective-C",
}


class RepoStructure(BaseModel):
    root: str
    top_dirs: list[str] = Field(default_factory=list)
    key_dirs: list[str] = Field(default_factory=list)
    readme_path: str = ""
    docs_dirs: list[str] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)
    dependency_files: list[str] = Field(default_factory=list)
    docker_ci_files: list[str] = Field(default_factory=list)
    test_dirs: list[str] = Field(default_factory=list)
    language_file_counts: dict[str, int] = Field(default_factory=dict)
    module_paths: list[str] = Field(default_factory=list)
    total_files: int = 0


def scan_repo(repo_path: Path | str, max_files: int = 50000) -> RepoStructure:
    root = Path(repo_path).resolve()
    structure = RepoStructure(root=str(root))

    structure.top_dirs = sorted(
        p.name for p in root.iterdir() if p.is_dir() and p.name not in SKIP_DIRS
    )

    seen = 0
    module_dirs: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_dir = os.path.relpath(dirpath, root)
        rel_dir = "" if rel_dir == "." else rel_dir
        dir_low = rel_dir.lower()

        base = os.path.basename(rel_dir).lower()
        if base in KEY_DIR_NAMES and rel_dir not in structure.key_dirs:
            structure.key_dirs.append(rel_dir)
        if base in {"docs", "doc", "documentation"}:
            structure.docs_dirs.append(rel_dir)
        if base in {"test", "tests", "__tests__", "spec", "e2e"}:
            structure.test_dirs.append(rel_dir)
        # 记录二级以内目录作为候选模块
        if rel_dir and rel_dir.count(os.sep) <= 1:
            module_dirs.add(rel_dir)

        for fname in filenames:
            seen += 1
            if seen > max_files:
                break
            rel_file = os.path.join(rel_dir, fname) if rel_dir else fname
            low = fname.lower()
            rel_low = rel_file.lower()

            if low.startswith("readme") and not structure.readme_path:
                structure.readme_path = rel_file
            if fname in DEPENDENCY_FILES:
                structure.dependency_files.append(rel_file)
            if any(h in low for h in CONFIG_FILE_HINTS):
                structure.config_files.append(rel_file)
            if any(h in rel_low for h in DOCKER_CI_HINTS):
                structure.docker_ci_files.append(rel_file)

            ext = os.path.splitext(fname)[1].lower()
            lang = LANGUAGE_EXT.get(ext)
            if lang:
                structure.language_file_counts[lang] = (
                    structure.language_file_counts.get(lang, 0) + 1
                )
        if seen > max_files:
            break

    structure.total_files = seen
    structure.module_paths = sorted(module_dirs)
    return structure

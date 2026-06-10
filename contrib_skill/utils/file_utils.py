"""文件路径与读取工具。"""
from __future__ import annotations

from pathlib import Path

# 路径中无业务含义的前缀段，提取模块名时跳过
_GENERIC_SEGMENTS = {
    "src", "main", "java", "kotlin", "scala", "app", "apps", "lib", "libs",
    "packages", "pkg", "internal", "cmd", "resources", "python",
}


def module_of_path(path: str) -> str:
    """从文件路径粗略提取模块名（第一段有业务含义的目录）。"""
    parts = Path(path).parts
    if len(parts) <= 1:
        return "(root)"
    for seg in parts[:-1]:
        low = seg.lower()
        if low in _GENERIC_SEGMENTS:
            continue
        # 跳过 Java 包名常见的公司域前缀
        if low in {"com", "org", "io", "net", "cn"}:
            continue
        return seg
    return parts[0]


def safe_read_text(path: Path, max_chars: int = 20000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""

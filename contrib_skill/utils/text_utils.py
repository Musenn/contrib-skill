"""文本与统计小工具。"""
from __future__ import annotations


def find_keywords(text: str, keywords: list[str]) -> list[str]:
    """返回 text（不区分大小写）中命中的关键词列表。"""
    low = text.lower()
    return [kw for kw in keywords if kw.lower() in low]


def top_n(counter: dict[str, int], n: int) -> list[str]:
    return [k for k, _ in sorted(counter.items(), key=lambda kv: -kv[1])[:n]]

"""时间相关工具。"""
from __future__ import annotations

from datetime import datetime


def month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def is_weekend(dt: datetime) -> bool:
    return dt.weekday() >= 5


def is_night(dt: datetime) -> bool:
    """22:00 - 07:00 视为夜间提交。"""
    return dt.hour >= 22 or dt.hour < 7

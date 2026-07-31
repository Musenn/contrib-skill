"""Load and validate measured benchmark evidence."""
from __future__ import annotations

import json
from pathlib import Path

from ..models import BenchmarkEvidence


def load_benchmark_report(path: str | Path) -> BenchmarkEvidence:
    report_path = Path(path).resolve()
    if not report_path.is_file():
        raise ValueError(f"压测报告不存在：{report_path}")
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取压测报告：{exc}") from exc

    config = data.get("config") or {}
    results = data.get("results") or {}
    latency = results.get("latency_ms") or {}
    total = _positive_int(config.get("requests"), "config.requests")
    concurrency = _positive_int(config.get("concurrency"), "config.concurrency")
    successful = _non_negative_int(results.get("successful_requests"), "results.successful_requests")
    failed = _non_negative_int(results.get("failed_requests"), "results.failed_requests")
    if successful + failed != total:
        raise ValueError("压测报告不一致：成功请求数 + 失败请求数必须等于总请求数")

    duration = _positive_float(results.get("duration_seconds"), "results.duration_seconds")
    success_rate = round(successful / total * 100, 2)
    requests_per_second = round(total / duration, 2)
    return BenchmarkEvidence(
        schema_version=int(data.get("schema_version", 1)),
        tool=str(data.get("tool", "unknown")),
        scenario=str(data.get("scenario", "HTTP 接口")),
        target=str(data.get("target", "")),
        environment=str(data.get("environment", "local")),
        generated_at=str(data.get("generated_at", "")),
        total_requests=total,
        concurrency=concurrency,
        duration_seconds=duration,
        successful_requests=successful,
        failed_requests=failed,
        success_rate=success_rate,
        requests_per_second=requests_per_second,
        latency_avg_ms=_non_negative_float(latency.get("avg"), "results.latency_ms.avg"),
        latency_p50_ms=_non_negative_float(latency.get("p50"), "results.latency_ms.p50"),
        latency_p95_ms=_non_negative_float(latency.get("p95"), "results.latency_ms.p95"),
        latency_p99_ms=_non_negative_float(latency.get("p99"), "results.latency_ms.p99"),
        source_file=str(report_path),
    )


def _positive_int(value, field: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"压测报告字段无效：{field}") from exc
    if number <= 0:
        raise ValueError(f"压测报告字段必须大于 0：{field}")
    return number


def _non_negative_int(value, field: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"压测报告字段无效：{field}") from exc
    if number < 0:
        raise ValueError(f"压测报告字段不能小于 0：{field}")
    return number


def _positive_float(value, field: str) -> float:
    number = _non_negative_float(value, field)
    if number <= 0:
        raise ValueError(f"压测报告字段必须大于 0：{field}")
    return number


def _non_negative_float(value, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"压测报告字段无效：{field}") from exc
    if number < 0:
        raise ValueError(f"压测报告字段不能小于 0：{field}")
    return number

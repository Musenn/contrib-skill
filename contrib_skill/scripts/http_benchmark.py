"""Small dependency-free HTTP benchmark runner for local/test environments."""
from __future__ import annotations

import argparse
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def run_benchmark(
    url: str,
    requests: int,
    concurrency: int,
    timeout: float,
    environment: str,
    scenario: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    allow_production: bool = False,
) -> dict:
    _validate_inputs(url, requests, concurrency, environment, allow_production)
    headers = headers or {}

    def send_one(_: int) -> tuple[bool, float]:
        started = time.perf_counter()
        try:
            request = Request(url, data=body, headers=headers, method=method.upper())
            with urlopen(request, timeout=timeout) as response:
                response.read()
                ok = 200 <= response.status < 400
        except (HTTPError, URLError, TimeoutError, OSError):
            ok = False
        return ok, (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        samples = list(pool.map(send_one, range(requests)))
    duration = max(time.perf_counter() - started, 1e-9)
    successful = sum(1 for ok, _ in samples if ok)
    latencies = sorted(latency for _, latency in samples)
    return {
        "schema_version": 1,
        "tool": "contrib-skill-http-benchmark",
        "scenario": scenario,
        "target": url,
        "environment": environment,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "requests": requests,
            "concurrency": concurrency,
            "timeout_seconds": timeout,
            "method": method.upper(),
        },
        "results": {
            "duration_seconds": round(duration, 4),
            "successful_requests": successful,
            "failed_requests": requests - successful,
            "success_rate": round(successful / requests * 100, 2),
            "requests_per_second": round(requests / duration, 2),
            "latency_ms": {
                "avg": round(sum(latencies) / len(latencies), 2),
                "p50": round(_percentile(latencies, 50), 2),
                "p95": round(_percentile(latencies, 95), 2),
                "p99": round(_percentile(latencies, 99), 2),
                "max": round(max(latencies), 2),
            },
        },
    }


def _validate_inputs(
    url: str,
    requests: int,
    concurrency: int,
    environment: str,
    allow_production: bool,
) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("--url 必须是有效的 http/https 地址")
    if not 1 <= requests <= 100_000:
        raise ValueError("--requests 必须在 1 到 100000 之间")
    if not 1 <= concurrency <= min(requests, 1000):
        raise ValueError("--concurrency 必须在 1 到请求总数之间，且不超过 1000")
    if environment.lower() in {"prod", "production", "线上", "生产"} and not allow_production:
        raise ValueError("默认拒绝压测生产环境；确认授权后显式传入 --allow-production")


def _percentile(values: list[float], percentile: int) -> float:
    index = max(0, math.ceil(percentile / 100 * len(values)) - 1)
    return values[index]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an evidence-producing HTTP benchmark")
    parser.add_argument("--url", required=True)
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--environment", default="local")
    parser.add_argument("--scenario", default="HTTP 接口")
    parser.add_argument("--method", default="GET")
    parser.add_argument("--header", action="append", default=[])
    parser.add_argument("--body-file")
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    headers = {}
    for raw in args.header:
        if ":" not in raw:
            raise SystemExit(f"无效 --header：{raw}，应为 Name: Value")
        name, value = raw.split(":", 1)
        headers[name.strip()] = value.strip()
    body = Path(args.body_file).read_bytes() if args.body_file else None
    report = run_benchmark(
        url=args.url,
        requests=args.requests,
        concurrency=args.concurrency,
        timeout=args.timeout,
        environment=args.environment,
        scenario=args.scenario,
        method=args.method,
        headers=headers,
        body=body,
        allow_production=args.allow_production,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Benchmark report written to {output.resolve()}")


if __name__ == "__main__":
    main()

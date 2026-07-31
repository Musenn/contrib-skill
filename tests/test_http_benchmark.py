import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from contrib_skill.analyzers.benchmark_loader import load_benchmark_report
from contrib_skill.cli import run_analysis
from contrib_skill.config import AnalyzeOptions
from contrib_skill.generators.report_generator import ReportGenerator
from contrib_skill.scripts.http_benchmark import run_benchmark


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


@pytest.fixture()
def benchmark_report(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        report = run_benchmark(
            url=f"http://127.0.0.1:{server.server_port}/orders",
            requests=20,
            concurrency=4,
            timeout=2,
            environment="test",
            scenario="订单查询接口",
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return path


def test_http_benchmark_generates_loadable_measured_report(benchmark_report):
    result = load_benchmark_report(benchmark_report)

    assert result.total_requests == 20
    assert result.concurrency == 4
    assert result.successful_requests == 20
    assert result.success_rate == 100
    assert result.requests_per_second > 0
    assert result.latency_p95_ms >= 0
    assert result.source_file == str(benchmark_report.resolve())


def test_http_benchmark_refuses_production_without_explicit_override():
    with pytest.raises(ValueError, match="默认拒绝压测生产环境"):
        run_benchmark(
            url="https://example.com/health",
            requests=1,
            concurrency=1,
            timeout=1,
            environment="production",
            scenario="健康检查",
        )


def test_benchmark_report_enables_safe_star_metric_claim(
    sample_repo, benchmark_report, tmp_path
):
    opts = AnalyzeOptions(
        repo=str(sample_repo),
        author="Alice",
        mode="resume",
        project_context="公司内部订单系统，业务场景要求高并发",
        benchmark_report=str(benchmark_report),
    )
    result, structure, resume, _ = run_analysis(opts)

    assert result.benchmark is not None
    assert resume is not None
    claim = resume["ready_bullets"][-1]
    assert claim.risk_level == "safe"
    assert "订单查询接口在并发访问下缺乏可复核的响应稳定性与容量基线" in claim.text
    assert "承担在测试环境验证接口吞吐、成功率与尾延迟任务" in claim.text
    assert "20 次请求" in claim.text
    assert "100.00%" in claim.text
    assert "QPS" in claim.text
    assert "P95 延迟" in claim.text
    assert resume["benchmark_star"]["action"].endswith("20 次请求")

    concurrency = next(
        item for item in result.project_context_assessments
        if item.statement == "整体项目满足高并发要求"
    )
    assert concurrency.risk_level == "needs_confirmation"
    assert "不等同于生产环境" in concurrency.analysis

    output = tmp_path / "output"
    ReportGenerator(output).write_all(
        result, structure, resume, interview=None, mode="resume"
    )
    text = (output / "06_resume_bullets.md").read_text(encoding="utf-8")
    assert "压测量化成果的 STAR 结构" in text
    assert "**Situation**" in text
    assert "**Result**" in text

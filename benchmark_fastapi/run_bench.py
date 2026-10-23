"""Benchmark Flask, Django REST Framework, and FastAPI endpoints.

Start all three servers as described in README_bench.md, then run:
    python run_bench.py
"""

import argparse
import concurrent.futures
import csv
import json
import math
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BenchmarkCase:
    framework: str
    scenario: str
    url: str
    method: str
    payload: Optional[dict]
    expected_status: int


@dataclass
class RequestResult:
    elapsed_ms: float
    status: Optional[int]
    error: Optional[str] = None


def make_cases(args):
    return [
        BenchmarkCase("FastAPI", "Validation hợp lệ", args.fastapi_url + "/items", "POST",
                      {"name": "Banana", "price": 2.5}, 201),
        BenchmarkCase("Flask", "Validation hợp lệ", args.flask_url + "/items", "POST",
                      {"name": "Banana", "price": 2.5}, 201),
        BenchmarkCase("DRF", "Validation hợp lệ", args.drf_url + "/items/", "POST",
                      {"name": "Banana", "price": 2.5}, 201),
        BenchmarkCase("FastAPI", "Validation không hợp lệ", args.fastapi_url + "/items", "POST",
                      {"name": "", "price": -1}, 422),
        BenchmarkCase("Flask", "Validation không hợp lệ", args.flask_url + "/items", "POST",
                      {"name": "", "price": -1}, 422),
        BenchmarkCase("DRF", "Validation không hợp lệ", args.drf_url + "/items/", "POST",
                      {"name": "", "price": -1}, 400),
        BenchmarkCase("FastAPI", "Chờ I/O 100 ms", args.fastapi_url + "/io-async", "GET", None, 200),
        BenchmarkCase("Flask", "Chờ I/O 100 ms", args.flask_url + "/io-sync", "GET", None, 200),
        BenchmarkCase("DRF", "Chờ I/O 100 ms", args.drf_url + "/io/", "GET", None, 200),
        BenchmarkCase("FastAPI", "Async đúng: await asyncio.sleep",
                      args.fastapi_url + "/io-async", "GET", None, 200),
        BenchmarkCase("FastAPI", "Async sai: time.sleep trong async def",
                      args.fastapi_url + "/io-blocking-wrong", "GET", None, 200),
        BenchmarkCase("FastAPI", "Sync def: time.sleep trong def",
                      args.fastapi_url + "/io-sync", "GET", None, 200),
    ]


def make_request(case):
    body = None if case.payload is None else json.dumps(case.payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = urllib.request.Request(case.url, data=body, headers=headers, method=case.method)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
            status = response.status
        return RequestResult((time.perf_counter() - started) * 1000, status)
    except urllib.error.HTTPError as error:
        error.read()
        return RequestResult((time.perf_counter() - started) * 1000, error.code)
    except urllib.error.URLError as error:
        return RequestResult((time.perf_counter() - started) * 1000, None, str(error.reason))


def run_trial(case, requests, concurrency):
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(executor.map(lambda _: make_request(case), range(requests)))
    elapsed = time.perf_counter() - started
    latencies = [result.elapsed_ms for result in results]
    statuses = Counter(str(result.status) for result in results)
    errors = [result.error for result in results if result.error]
    unexpected = sum(result.status != case.expected_status for result in results)
    ordered = sorted(latencies)
    p95 = ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]
    return {
        "rps": requests / elapsed,
        "mean_ms": statistics.fmean(latencies),
        "p50_ms": statistics.median(latencies),
        "p95_ms": p95,
        "unexpected": unexpected,
        "statuses": dict(statuses),
        "errors": errors,
    }


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="So sánh thực nghiệm Flask, DRF và FastAPI.")
    parser.add_argument("--requests", type=int, default=500, help="số request mỗi lần đo (mặc định: 500)")
    parser.add_argument("--concurrency", type=int, default=50, help="số request đồng thời (mặc định: 50)")
    parser.add_argument("--runs", type=int, default=3, help="số lần lặp (mặc định: 3)")
    parser.add_argument("--warmup", type=int, default=50, help="số request khởi động mỗi kịch bản (mặc định: 50)")
    parser.add_argument("--output", default="benchmark_results.csv", help="tệp CSV kết quả")
    parser.add_argument("--fastapi-url", default="http://127.0.0.1:8000")
    parser.add_argument("--flask-url", default="http://127.0.0.1:8001")
    parser.add_argument("--drf-url", default="http://127.0.0.1:8002")
    args = parser.parse_args()
    if min(args.requests, args.concurrency, args.runs) < 1 or args.warmup < 0:
        parser.error("requests, concurrency, runs phải >= 1; warmup phải >= 0")

    rows = []
    any_failure = False
    print("Framework | Kịch bản | RPS trung vị | Độ trễ TB (ms) | p50 (ms) | p95 (ms) | HTTP | Lỗi")
    print("---|---|---:|---:|---:|---:|---|---:")
    for case in make_cases(args):
        if args.warmup:
            warmup = run_trial(case, args.warmup, min(args.concurrency, args.warmup))
            if warmup["unexpected"]:
                print("Cảnh báo: warm-up có response ngoài dự kiến: " + case.url)

        trials = [run_trial(case, args.requests, args.concurrency) for _ in range(args.runs)]
        if any(trial["unexpected"] for trial in trials):
            any_failure = True
        if any(trial["errors"] for trial in trials):
            any_failure = True

        row = {
            "framework": case.framework,
            "scenario": case.scenario,
            "requests_per_run": args.requests,
            "concurrency": args.concurrency,
            "runs": args.runs,
            "rps_median": statistics.median(trial["rps"] for trial in trials),
            "mean_ms_median": statistics.median(trial["mean_ms"] for trial in trials),
            "p50_ms_median": statistics.median(trial["p50_ms"] for trial in trials),
            "p95_ms_median": statistics.median(trial["p95_ms"] for trial in trials),
            "unexpected_responses": sum(trial["unexpected"] for trial in trials),
            "http_statuses_last_run": json.dumps(trials[-1]["statuses"], ensure_ascii=False),
            "connection_errors": sum(len(trial["errors"]) for trial in trials),
        }
        rows.append(row)
        print(
            "{framework} | {scenario} | {rps_median:.1f} | {mean_ms_median:.2f} | "
            "{p50_ms_median:.2f} | {p95_ms_median:.2f} | {http_statuses_last_run} | "
            "{connection_errors}".format(**row)
        )
        for trial in trials:
            for error in trial["errors"][:1]:
                print("  Lỗi kết nối {}: {}".format(case.url, error))

    with open(args.output, "w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("\nĐã ghi kết quả: {}".format(args.output))
    if any_failure:
        raise SystemExit("Có response sai mã trạng thái hoặc lỗi kết nối; kiểm tra server và kết quả.")


if __name__ == "__main__":
    main()

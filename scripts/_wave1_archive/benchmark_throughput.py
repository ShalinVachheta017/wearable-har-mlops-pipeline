#!/usr/bin/env python3
"""
Throughput Scaling Benchmark — HAR Inference API
=================================================
Measures requests/second across increasing concurrency levels (1 → 16 workers)
to produce a scaling curve.  Also measures windows/second locally at different
batch sizes.

Results saved to reports/benchmark/throughput_report_<timestamp>.json

Usage:
    # HTTP concurrent load test
    python scripts/benchmark_throughput.py --endpoint http://localhost:8000

    # Local model batch-size scaling
    python scripts/benchmark_throughput.py --local
"""
import argparse
import concurrent.futures
import json
import sys
import time
from pathlib import Path
from typing import List

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

REPORTS_DIR = PROJECT_ROOT / "reports" / "benchmark"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_csv_bytes(n_rows: int = 600) -> bytes:
    rng = np.random.default_rng(0)
    acc = rng.normal([0.0, 0.0, -9.81], 1.0, size=(n_rows, 3)).astype(np.float32)
    gyro = rng.normal(0, 0.3, size=(n_rows, 3)).astype(np.float32)
    lines = ["acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z"]
    for i in range(n_rows):
        lines.append(",".join(f"{v:.5f}" for v in list(acc[i]) + list(gyro[i])))
    return "\n".join(lines).encode()


def _send_one(endpoint: str, payload: bytes) -> bool:
    import requests  # noqa: PLC0415
    try:
        r = requests.post(
            f"{endpoint}/api/upload",
            files={"file": ("b.csv", payload, "text/csv")},
            timeout=30,
        )
        return r.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# HTTP concurrency scaling
# ---------------------------------------------------------------------------

def run_concurrency_level(
    endpoint: str, n_workers: int, n_requests: int, payload: bytes
) -> dict:
    t0 = time.perf_counter()
    successes = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as ex:
        futures = [ex.submit(_send_one, endpoint, payload) for _ in range(n_requests)]
        for f in concurrent.futures.as_completed(futures):
            if f.result():
                successes += 1
    elapsed = time.perf_counter() - t0
    return {
        "concurrency": n_workers,
        "n_requests": n_requests,
        "n_successful": successes,
        "elapsed_s": round(elapsed, 3),
        "requests_per_sec": round(successes / elapsed, 2) if elapsed > 0 else 0.0,
        "error_rate_pct": round((n_requests - successes) / n_requests * 100, 1),
    }


def run_http_throughput(endpoint: str, n_requests: int) -> dict:
    payload = _generate_csv_bytes(600)
    levels = [1, 2, 4, 8, 16]
    curve: List[dict] = []

    # Warmup
    print("  Warming up (5 requests)…")
    for _ in range(5):
        _send_one(endpoint, payload)

    for workers in levels:
        print(f"  concurrency={workers:>2}  …", end=" ", flush=True)
        r = run_concurrency_level(endpoint, workers, n_requests, payload)
        print(f"{r['requests_per_sec']:>7.1f} req/s  "
              f"(errors: {r['error_rate_pct']:.0f}%)")
        curve.append(r)

    peak = max(curve, key=lambda x: x["requests_per_sec"])
    return {
        "mode": "http",
        "endpoint": endpoint,
        "scaling_curve": curve,
        "peak_requests_per_sec": peak["requests_per_sec"],
        "peak_at_concurrency": peak["concurrency"],
    }


# ---------------------------------------------------------------------------
# Local batch-size scaling
# ---------------------------------------------------------------------------

def run_local_throughput(batch_sizes: List[int], n_repeats: int = 20) -> dict:
    try:
        import tensorflow as tf  # noqa: PLC0415
    except ImportError:
        sys.exit("TensorFlow required for --local mode.")
    tf.get_logger().setLevel("ERROR")

    model_path = (
        PROJECT_ROOT / "models" / "pretrained" / "fine_tuned_model_1dcnnbilstm.keras"
    )
    if not model_path.exists():
        sys.exit(f"Model not found: {model_path}\nRun: dvc pull models/pretrained.dvc")
    model = tf.keras.models.load_model(str(model_path))

    curve = []
    for bs in batch_sizes:
        X = np.random.rand(bs, 200, 6).astype(np.float32)
        # Warmup
        model.predict(X, verbose=0)
        t0 = time.perf_counter()
        for _ in range(n_repeats):
            model.predict(X, verbose=0)
        elapsed = time.perf_counter() - t0
        windows_per_sec = bs * n_repeats / elapsed
        latency_ms = elapsed / n_repeats * 1000
        print(f"  batch={bs:>5}  {windows_per_sec:>10.1f} windows/s  "
              f"  {latency_ms:>8.2f} ms/call")
        curve.append({
            "batch_size": bs,
            "windows_per_sec": round(windows_per_sec, 1),
            "latency_ms_per_call": round(latency_ms, 2),
        })

    return {
        "mode": "local_model",
        "n_repeats_per_level": n_repeats,
        "scaling_curve": curve,
        "peak_windows_per_sec": max(r["windows_per_sec"] for r in curve),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="HAR API Throughput Benchmark")
    ap.add_argument("--endpoint", default="http://localhost:8000")
    ap.add_argument("--requests-per-level", type=int, default=30,
                    help="Number of requests per concurrency level (HTTP mode)")
    ap.add_argument("--local", action="store_true",
                    help="Benchmark local model batch scaling, no HTTP")
    args = ap.parse_args()

    print("=" * 56)
    print("  HAR MLOps — Throughput Scaling Benchmark")
    print("=" * 56)

    if args.local:
        print("  Mode: local batch-size scaling")
        result = run_local_throughput(
            batch_sizes=[1, 4, 8, 16, 32, 64, 128, 256, 512]
        )
    else:
        print(f"  Mode: HTTP concurrent load test → {args.endpoint}")
        result = run_http_throughput(args.endpoint, args.requests_per_level)

    result["benchmark_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = REPORTS_DIR / f"throughput_report_{ts}.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\n✅  Saved → {out.relative_to(PROJECT_ROOT)}")
    print("   Cite in thesis as:  reports/benchmark/throughput_report_<timestamp>.json")


if __name__ == "__main__":
    main()

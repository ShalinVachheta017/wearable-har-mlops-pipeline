#!/usr/bin/env python3
"""
Latency Benchmark — HAR Inference API
=======================================
Measures per-request end-to-end latency (p50/p95/p99).
Results are saved to reports/benchmark/latency_report_<timestamp>.json
and can be cited directly in the thesis (Chapter 5 / Evaluation).

Usage:
    # HTTP mode (API must be running)
    python scripts/benchmark_latency.py --endpoint http://localhost:8000

    # Local model mode (no HTTP overhead — measures pure inference latency)
    python scripts/benchmark_latency.py --local

    # Custom window count per request
    python scripts/benchmark_latency.py --local --windows 64

Output columns (all in milliseconds):
    p50, p75, p95, p99 | mean | std | min | max
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

REPORTS_DIR = PROJECT_ROOT / "reports" / "benchmark"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_csv_bytes(n_rows: int = 600) -> bytes:
    """Synthetic 6-channel IMU CSV payload (n_rows > WINDOW_SIZE=200)."""
    rng = np.random.default_rng(42)
    acc = rng.normal([0.0, 0.0, -9.81], [2.0, 2.0, 0.5], size=(n_rows, 3)).astype(np.float32)
    gyro = rng.normal(0, 0.3, size=(n_rows, 3)).astype(np.float32)
    header = "acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z"
    rows = [header]
    for i in range(n_rows):
        rows.append(",".join(f"{v:.5f}" for v in list(acc[i]) + list(gyro[i])))
    return "\n".join(rows).encode()


def _stats(latencies: list) -> dict:
    a = np.array(latencies, dtype=float)
    return {
        "n_successful": len(a),
        "p50_ms": round(float(np.percentile(a, 50)), 2),
        "p75_ms": round(float(np.percentile(a, 75)), 2),
        "p95_ms": round(float(np.percentile(a, 95)), 2),
        "p99_ms": round(float(np.percentile(a, 99)), 2),
        "mean_ms": round(float(np.mean(a)), 2),
        "std_ms": round(float(np.std(a)), 2),
        "min_ms": round(float(np.min(a)), 2),
        "max_ms": round(float(np.max(a)), 2),
    }


# ---------------------------------------------------------------------------
# HTTP benchmark
# ---------------------------------------------------------------------------

def run_http_benchmark(endpoint: str, n_requests: int, warmup: int = 5) -> dict:
    """Send n_requests to /api/upload and measure round-trip latency."""
    import requests  # noqa: PLC0415

    base = endpoint.rstrip("/")
    health = requests.get(f"{base}/api/health", timeout=10)
    health.raise_for_status()
    print(f"  API health: {health.json().get('status')}")

    payload = _generate_csv_bytes(600)
    files = {"file": ("bench.csv", payload, "text/csv")}

    print(f"  Warming up ({warmup} requests)…")
    for _ in range(warmup):
        requests.post(f"{base}/api/upload", files={"file": ("b.csv", payload, "text/csv")})

    print(f"  Benchmarking ({n_requests} requests)…")
    latencies = []
    for i in range(n_requests):
        t0 = time.perf_counter()
        r = requests.post(f"{base}/api/upload",
                          files={"file": ("b.csv", payload, "text/csv")}, timeout=30)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        if r.status_code == 200:
            latencies.append(elapsed_ms)
            # Also pull server-side processing_time_ms if available
        else:
            print(f"    Request {i+1}/{n_requests}: HTTP {r.status_code} ⚠", file=sys.stderr)

    s = _stats(latencies)
    s["mode"] = "http"
    s["endpoint"] = base
    s["n_requested"] = n_requests
    return s


# ---------------------------------------------------------------------------
# Local model benchmark
# ---------------------------------------------------------------------------

def run_local_benchmark(n_requests: int, n_windows: int = 15, warmup: int = 3) -> dict:
    """Run inference locally — measures pure model predict() latency."""
    try:
        import tensorflow as tf  # noqa: PLC0415
    except ImportError:
        sys.exit("TensorFlow is required for --local mode. pip install tensorflow")
    tf.get_logger().setLevel("ERROR")

    model_path = (
        PROJECT_ROOT / "models" / "pretrained" / "fine_tuned_model_1dcnnbilstm.keras"
    )
    if not model_path.exists():
        sys.exit(f"Model not found: {model_path}\nRun: dvc pull models/pretrained.dvc")

    print(f"  Loading model from {model_path} …")
    model = tf.keras.models.load_model(str(model_path))
    X = np.random.rand(n_windows, 200, 6).astype(np.float32)

    print(f"  Warming up ({warmup} passes, batch={n_windows})…")
    for _ in range(warmup):
        model.predict(X, verbose=0)

    print(f"  Benchmarking ({n_requests} passes, batch={n_windows})…")
    latencies = []
    for _ in range(n_requests):
        t0 = time.perf_counter()
        model.predict(X, verbose=0)
        latencies.append((time.perf_counter() - t0) * 1000)

    s = _stats(latencies)
    s["mode"] = "local"
    s["n_windows_per_call"] = n_windows
    s["n_requested"] = n_requests
    s["windows_per_sec_p50"] = round(n_windows / (s["p50_ms"] / 1000), 1)
    return s


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="HAR API Latency Benchmark")
    ap.add_argument("--endpoint", default="http://localhost:8000", help="API base URL")
    ap.add_argument("--requests", type=int, default=100, help="Number of timed requests")
    ap.add_argument("--windows", type=int, default=15,
                    help="Windows per local-mode batch (--local only)")
    ap.add_argument("--local", action="store_true",
                    help="Benchmark model directly, no HTTP overhead")
    args = ap.parse_args()

    print("=" * 56)
    print("  HAR MLOps — Latency Benchmark")
    print("=" * 56)

    if args.local:
        result = run_local_benchmark(args.requests, n_windows=args.windows)
    else:
        result = run_http_benchmark(args.endpoint, args.requests)

    result["benchmark_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    # Pretty-print
    print("\n" + "-" * 40)
    print(f"  n_successful  : {result['n_successful']}/{result['n_requested']}")
    print(f"  p50           : {result['p50_ms']:>8.2f} ms")
    print(f"  p95           : {result['p95_ms']:>8.2f} ms")
    print(f"  p99           : {result['p99_ms']:>8.2f} ms")
    print(f"  mean ± std    : {result['mean_ms']:.2f} ± {result['std_ms']:.2f} ms")
    print(f"  min / max     : {result['min_ms']:.2f} / {result['max_ms']:.2f} ms")
    print("-" * 40)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = REPORTS_DIR / f"latency_report_{ts}.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\n✅  Saved → {out.relative_to(PROJECT_ROOT)}")
    print("   Cite in thesis as:  reports/benchmark/latency_report_<timestamp>.json")


if __name__ == "__main__":
    main()

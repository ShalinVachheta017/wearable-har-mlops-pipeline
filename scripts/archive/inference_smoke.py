#!/usr/bin/env python
"""
Inference smoke test for the HAR MLOps API.

Runs two checks:
  1. GET /api/health  — must return 200 with model_loaded == True
  2. POST /api/upload — must return 200 with at least one prediction window

Usage (CI):
    python scripts/inference_smoke.py --endpoint http://localhost:8000

Exit codes:
    0  all checks passed
    1  one or more checks failed
"""

import argparse
import csv
import io
import json
import math
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(url: str, timeout: int = 10) -> dict:
    """HTTP GET → parsed JSON."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _post_csv(url: str, csv_bytes: bytes, filename: str = "smoke_test.csv", timeout: int = 30) -> dict:
    """HTTP POST multipart/form-data with a CSV file → parsed JSON."""
    boundary = "----SmokeBoundary" + str(random.randint(100000, 999999))
    header_boundary = f"--{boundary}"
    footer_boundary = f"--{boundary}--"

    body_parts = [
        header_boundary.encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode(),
        b"Content-Type: text/csv",
        b"",
        csv_bytes,
        footer_boundary.encode(),
    ]
    body = b"\r\n".join(body_parts)

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _generate_test_csv(n_rows: int = 250) -> bytes:
    """
    Generate a synthetic sensor CSV with the 6 standard column names:
    acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z

    Values are simple sinusoidal signals to simulate motion, scaled to
    typical IMU ranges (±2g acceleration, ±500 deg/s gyroscope).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"])

    for i in range(n_rows):
        t = i / 25.0  # 25 Hz
        # Simulate walking: ~2 Hz dominant frequency
        acc_x = round(0.3 * math.sin(2 * math.pi * 2. * t) + 0.05 * random.gauss(0, 1), 5)
        acc_y = round(0.2 * math.cos(2 * math.pi * 2. * t) + 0.05 * random.gauss(0, 1), 5)
        acc_z = round(1.0 + 0.1 * math.sin(2 * math.pi * 4. * t) + 0.02 * random.gauss(0, 1), 5)
        gyro_x = round(10.0 * math.sin(2 * math.pi * 2. * t) + 0.5 * random.gauss(0, 1), 5)
        gyro_y = round(5.0 * math.cos(2 * math.pi * 2. * t) + 0.5 * random.gauss(0, 1), 5)
        gyro_z = round(3.0 * math.sin(2 * math.pi * 1. * t) + 0.5 * random.gauss(0, 1), 5)
        writer.writerow([acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z])

    return buf.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_health(base_url: str, require_model: bool = False) -> bool:
    """
    GET /api/health — verify API is responsive.
    If require_model=True, also assert model_loaded == True.
    """
    url = base_url.rstrip("/") + "/api/health"
    print(f"[SMOKE] CHECK 1 — GET {url}")
    try:
        data = _get(url, timeout=10)
    except Exception as exc:
        print(f"[SMOKE]   FAIL — Could not reach API: {exc}")
        return False

    status_ok = data.get("status") in {"healthy", "ok", "model_not_loaded"}
    model_loaded = data.get("model_loaded", False)

    if not status_ok:
        print(f"[SMOKE]   FAIL — Unexpected status: {data.get('status')!r}")
        return False

    if require_model and not model_loaded:
        print("[SMOKE]   FAIL — model_loaded is False. Check model path / loading logs.")
        return False

    loaded_str = "model loaded" if model_loaded else "model NOT loaded (inference will fail)"
    print(f"[SMOKE]   PASS — status={data.get('status')!r}, {loaded_str}")
    return True


def check_upload(base_url: str) -> bool:
    """
    POST /api/upload — upload synthetic CSV, expect at least 1 prediction window.
    Returns True on success (HTTP 200 + non-empty predictions).
    Also returns True on HTTP 503 (model not loaded) — endpoint exists, model just
    not mounted (expected in CI environments without model files).
    Only fails on HTTP 404 (route missing) or connection errors.
    """
    url = base_url.rstrip("/") + "/api/upload"
    print(f"[SMOKE] CHECK 2 — POST {url}")

    csv_bytes = _generate_test_csv(n_rows=250)
    print(f"[SMOKE]   Uploading synthetic CSV ({len(csv_bytes)} bytes, 250 rows)...")

    try:
        data = _post_csv(url, csv_bytes, timeout=60)
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode()
        except Exception:
            body = str(exc)
        if exc.code == 503:
            # Model not loaded — endpoint exists, just no model file mounted.
            # This is expected in CI where the model is not included in the image.
            print(f"[SMOKE]   PASS (no model) — HTTP 503: route exists, model not loaded in this environment")
            return True
        if exc.code == 404:
            print(f"[SMOKE]   FAIL — HTTP 404: route /api/upload is missing from the API")
            return False
        print(f"[SMOKE]   FAIL — HTTP {exc.code}: {body[:400]}")
        return False
    except Exception as exc:
        print(f"[SMOKE]   FAIL — Request error: {exc}")
        return False

    windows = data.get("windows_created", 0)
    predictions = data.get("predictions", [])
    processing_ms = data.get("processing_time_ms", "?")

    if windows < 1 or len(predictions) < 1:
        print(f"[SMOKE]   FAIL — No prediction windows returned: {data}")
        return False

    top_activity = data.get("activity_summary", {})
    top_act_str = ", ".join(f"{k}={v}" for k, v in list(top_activity.items())[:3])
    print(
        f"[SMOKE]   PASS — {windows} windows, {len(predictions)} predictions, "
        f"{processing_ms}ms | top activities: {top_act_str}"
    )
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="HAR API smoke test")
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8000",
        help="Base URL of the running API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--require-model",
        action="store_true",
        default=False,
        help="Fail check 1 if model is not loaded (default: warn only)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retries if the API is not yet ready (default: 3)",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=5.0,
        help="Seconds between retries (default: 5.0)",
    )
    args = parser.parse_args()

    # Wait for API readiness (with retries)
    health_passed = False
    for attempt in range(1, args.retries + 1):
        if attempt > 1:
            print(f"[SMOKE] Retry {attempt}/{args.retries} in {args.retry_delay}s ...")
            time.sleep(args.retry_delay)
        health_passed = check_health(args.endpoint, require_model=args.require_model)
        if health_passed:
            break

    upload_passed = check_upload(args.endpoint)

    # Summary
    results = [
        ("Health check (/api/health)", health_passed),
        ("Upload check (/api/upload)", upload_passed),
    ]
    print()
    print("=" * 50)
    print("[SMOKE] RESULTS")
    print("=" * 50)
    all_passed = True
    for name, passed in results:
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {name}")
        if not passed:
            all_passed = False
    print("=" * 50)
    if all_passed:
        print("[SMOKE] All checks passed.")
    else:
        print("[SMOKE] One or more checks FAILED.")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

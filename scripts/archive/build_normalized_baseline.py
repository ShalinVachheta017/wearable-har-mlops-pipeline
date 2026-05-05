#!/usr/bin/env python3
"""
Build Normalized Baseline
=========================

Creates a baseline statistics JSON from training/reference data.
Used by Layer 3 (drift detection) in post-inference monitoring.

Usage:
    python scripts/build_normalized_baseline.py
    python scripts/build_normalized_baseline.py --data data/prepared/production_X.npy
    python scripts/build_normalized_baseline.py --data data/prepared/production_X.npy --output models/normalized_baseline.json
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

# Channel names for 6-axis IMU (accel + gyro)
CHANNEL_NAMES = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]


def build_baseline(X: np.ndarray) -> dict:
    """
    Compute baseline statistics from reference data.

    Args:
        X: np.ndarray of shape (n_windows, timesteps, channels)

    Returns:
        dict with both flat arrays (for monitoring Layer 3) and
        per-channel detail (for Wasserstein drift, reporting).
    """
    n_windows, timesteps, n_channels = X.shape
    channels = CHANNEL_NAMES[:n_channels]

    # Flat per-channel stats (compatible with PostInferenceMonitor._analyze_drift)
    mean = X.mean(axis=(0, 1)).tolist()
    std = X.std(axis=(0, 1)).tolist()
    min_val = X.min(axis=(0, 1)).tolist()
    max_val = X.max(axis=(0, 1)).tolist()

    # Percentiles over flattened (windows × timesteps) axis
    flat = X.reshape(-1, n_channels)
    p5 = np.percentile(flat, 5, axis=0).tolist()
    p25 = np.percentile(flat, 25, axis=0).tolist()
    p50 = np.percentile(flat, 50, axis=0).tolist()
    p75 = np.percentile(flat, 75, axis=0).tolist()
    p95 = np.percentile(flat, 95, axis=0).tolist()

    # Per-channel detail dict
    per_channel = {}
    for i, ch in enumerate(channels):
        per_channel[ch] = {
            "mean": mean[i],
            "std": std[i],
            "min": min_val[i],
            "max": max_val[i],
            "p5": p5[i],
            "p25": p25[i],
            "p50": p50[i],
            "p75": p75[i],
            "p95": p95[i],
        }

    baseline = {        "schema_version": 1,        # Flat arrays — used by PostInferenceMonitor._analyze_drift()
        "mean": mean,
        "std": std,
        "min": min_val,
        "max": max_val,
        "percentiles": {"p5": p5, "p25": p25, "p50": p50, "p75": p75, "p95": p95},
        # Per-channel detail — used for logging and Wasserstein drift
        "per_channel": per_channel,
        "channel_names": channels,
        # Metadata
        "metadata": {
            "n_windows": int(n_windows),
            "window_size": int(timesteps),
            "n_channels": int(n_channels),
            "created_at": datetime.now().isoformat(),
            "source": "training reference data",
        },
    }
    return baseline


def main():
    parser = argparse.ArgumentParser(description="Build normalized baseline for drift detection")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/prepared/production_X.npy"),
        help="Path to reference data .npy (n_windows, timesteps, channels)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("models/normalized_baseline.json"),
        help="Output path for baseline JSON",
    )
    args = parser.parse_args()

    if not args.data.exists():
        logger.error(f"Data file not found: {args.data}")
        return 1

    logger.info(f"Loading reference data: {args.data}")
    X = np.load(args.data)
    logger.info(f"  Shape: {X.shape}, dtype: {X.dtype}")

    if X.ndim != 3:
        logger.error(f"Expected 3D array (windows, timesteps, channels), got {X.ndim}D")
        return 1

    baseline = build_baseline(X)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)

    logger.info(f"Baseline saved: {args.output}")
    logger.info(f"  Channels: {baseline['channel_names']}")
    logger.info(f"  Windows: {baseline['metadata']['n_windows']}")
    logger.info(f"  Per-channel means: {[f'{m:.4f}' for m in baseline['mean']]}")
    logger.info(f"  Per-channel stds:  {[f'{s:.4f}' for s in baseline['std']]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

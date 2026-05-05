"""Calibrate dataset-specific MMD thresholds from reference windows.

This script intentionally derives thresholds from this repository's own
reference tensor. It does not define universal MMD cutoffs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from src.monitoring.post_inference_monitor import PostInferenceMonitor


def _sample(values: np.ndarray, size: int, rng: np.random.Generator) -> np.ndarray:
    if len(values) <= size:
        return values
    idx = rng.choice(len(values), size=size, replace=False)
    return values[idx]


def _calibrate(
    reference_windows: np.ndarray,
    sample_size: int,
    iterations: int,
    seed: int,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    rng = np.random.default_rng(seed)
    features = PostInferenceMonitor._window_summary_features(reference_windows)
    sample_size = min(sample_size, max(32, len(features) // 2))
    bandwidth = PostInferenceMonitor._median_bandwidth(features, rng)

    rows = []
    for i in range(iterations):
        first = _sample(features, sample_size, rng)
        second = _sample(features, sample_size, rng)
        score = PostInferenceMonitor._mmd2_rbf(first, second, bandwidth)
        rows.append(
            {
                "iteration": i,
                "sample_size": sample_size,
                "bandwidth": bandwidth,
                "mmd_score": score,
            }
        )

    df = pd.DataFrame(rows)
    thresholds = {
        "healthy_p90": float(df["mmd_score"].quantile(0.90)),
        "warning_p95": float(df["mmd_score"].quantile(0.95)),
        "critical_p99": float(df["mmd_score"].quantile(0.99)),
        "mean": float(df["mmd_score"].mean()),
        "std": float(df["mmd_score"].std(ddof=1)),
        "min": float(df["mmd_score"].min()),
        "max": float(df["mmd_score"].max()),
        "sample_size": int(sample_size),
        "iterations": int(iterations),
        "bandwidth": float(bandwidth),
        "seed": int(seed),
    }
    return df, thresholds


def _write_markdown(out_dir: Path, reference_path: Path, thresholds: Dict[str, float]) -> None:
    lines = [
        "# MMD Threshold Calibration",
        "",
        "## Procedure",
        "",
        f"- Reference artifact: `{reference_path}`",
        "- Feature level: per-window summary features, channel means plus channel standard deviations.",
        f"- Repeated reference-vs-reference comparisons: `{thresholds['iterations']}`",
        f"- Sample size per side: `{thresholds['sample_size']}` windows",
        "- Thresholds are empirical percentiles of healthy reference comparisons.",
        "",
        "## Thresholds",
        "",
        f"- Healthy upper reference band, p90: `{thresholds['healthy_p90']:.8f}`",
        f"- Warning threshold, p95: `{thresholds['warning_p95']:.8f}`",
        f"- Critical candidate, p99: `{thresholds['critical_p99']:.8f}`",
        "",
        "## Limitations",
        "",
        "- These thresholds are valid only for this reference artifact, feature representation, sample size, and preprocessing path.",
        "- The calibration does not establish universal MMD values.",
        "- Promotion into runtime governance still requires evidence that final trigger decisions improve, not only that drift warnings increase.",
    ]
    (out_dir / "MMD_THRESHOLD_CALIBRATION.md").write_text("\n".join(lines), encoding="utf-8")


def _plot(out_dir: Path, df: pd.DataFrame, thresholds: Dict[str, float]) -> None:
    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(df["mmd_score"], bins=30, color="#4c78a8", alpha=0.8)
        ax.axvline(thresholds["warning_p95"], color="#f58518", linestyle="--", label="warning p95")
        ax.axvline(thresholds["critical_p99"], color="#e45756", linestyle="--", label="critical p99")
        ax.set_title("Reference-vs-reference MMD calibration")
        ax.set_xlabel("MMD score")
        ax.set_ylabel("Count")
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_dir / "mmd_reference_bootstrap_histogram.png", dpi=160)
        plt.close(fig)
    except Exception:
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate MMD thresholds from reference windows")
    parser.add_argument("--reference-npy", default="models/mmd_reference_windows.npy")
    parser.add_argument(
        "--output-dir",
        default="outputs/thesis_branch_comparison/mmd_threshold_calibration",
    )
    parser.add_argument("--sample-size", type=int, default=384)
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reference_path = Path(args.reference_npy)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    windows = np.load(reference_path)
    df, thresholds = _calibrate(windows, args.sample_size, args.iterations, args.seed)
    thresholds["reference_npy"] = str(reference_path)
    thresholds["feature_level"] = "per-window summary features: channel means + channel stds"

    df.to_csv(out_dir / "mmd_reference_bootstrap_scores.csv", index=False)
    (out_dir / "mmd_thresholds.json").write_text(json.dumps(thresholds, indent=2), encoding="utf-8")
    _write_markdown(out_dir, reference_path, thresholds)
    _plot(out_dir, df, thresholds)
    print(json.dumps(thresholds, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

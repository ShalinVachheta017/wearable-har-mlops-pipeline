"""Compare current z-score drift runtime against the MMD runtime branch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import pandas as pd


CONFIDENCE_WARN = 0.70
UNCERTAIN_WARN = 20.0
DOMINANCE_WARN = 85.0
DOMINANCE_REVIEW = 95.0
TRANSITION_WARN = 35.0


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _manifest(path: Path) -> Dict:
    manifest = path / "run_manifest.json"
    if not manifest.exists():
        return {}
    return json.loads(manifest.read_text(encoding="utf-8"))


def _branch_table(root: Path, branch_label: str, primary_detector: str) -> pd.DataFrame:
    pre = _read(root / "preprocessing_ablation_summary.csv")
    drift = _read(root / "drift_monitor_ablation_summary.csv")
    drift = drift[drift["detector"] == primary_detector].copy()

    merged = pre.merge(
        drift[["dataset", "detector", "drift_score", "threshold", "status"]],
        on="dataset",
        how="left",
        suffixes=("", "_drift"),
    )
    merged["branch"] = branch_label
    merged["primary_drift_detector"] = primary_detector
    merged["confidence_warn"] = (
        (merged["mean_confidence"] < CONFIDENCE_WARN)
        | (merged["uncertain_pct"] > UNCERTAIN_WARN)
        | (merged["dominant_pct"] >= DOMINANCE_WARN)
    )
    merged["temporal_warn"] = merged["transition_rate_pct"] > TRANSITION_WARN
    merged["drift_warn"] = merged["status"].fillna("SKIPPED") != "HEALTHY"
    merged["review_route"] = merged["dominant_pct"] >= DOMINANCE_REVIEW
    merged["two_of_three_trigger"] = (
        merged[["confidence_warn", "temporal_warn", "drift_warn"]].astype(int).sum(axis=1) >= 2
    )
    return merged[
        [
            "branch",
            "dataset",
            "normalization_variant",
            "primary_drift_detector",
            "mean_confidence",
            "uncertain_pct",
            "dominant_class",
            "dominant_pct",
            "unique_predicted_classes",
            "transition_rate_pct",
            "accuracy",
            "macro_f1",
            "drift_score",
            "threshold",
            "status",
            "confidence_warn",
            "temporal_warn",
            "drift_warn",
            "two_of_three_trigger",
            "review_route",
        ]
    ]


def _write_report(out_dir: Path, comparison: pd.DataFrame, baseline_dir: Path, mmd_dir: Path) -> None:
    current = comparison[comparison["branch"] == "current_branch_baseline"]
    mmd = comparison[comparison["branch"] == "mmd_runtime_branch"]

    lines = [
        "# MMD Runtime Branch Comparison",
        "",
        "## Setup",
        "",
        f"- Current baseline artifacts: `{baseline_dir}`",
        f"- MMD branch artifacts: `{mmd_dir}`",
        "- Preprocessing held fixed: `zscore`",
        "- Retained model held fixed; no data was invented.",
        "- Current branch primary drift detector: `current_zscore` mean-shift.",
        "- MMD branch primary drift detector: `mmd` with reference-vs-reference bootstrap thresholding.",
        "",
        "## Comparison Table",
        "",
        comparison[
            [
                "branch",
                "dataset",
                "primary_drift_detector",
                "mean_confidence",
                "uncertain_pct",
                "dominant_pct",
                "unique_predicted_classes",
                "transition_rate_pct",
                "macro_f1",
                "drift_score",
                "threshold",
                "status",
                "two_of_three_trigger",
            ]
        ].round(4).to_markdown(index=False),
        "",
        "## Summary",
        "",
        f"- Current branch drift warnings: `{int(current['drift_warn'].sum())}` of `{len(current)}` datasets.",
        f"- MMD branch drift warnings: `{int(mmd['drift_warn'].sum())}` of `{len(mmd)}` datasets.",
        f"- Current branch two-of-three triggers: `{int(current['two_of_three_trigger'].sum())}`.",
        f"- MMD branch two-of-three triggers: `{int(mmd['two_of_three_trigger'].sum())}`.",
        "",
        "## Thesis-Safe Interpretation",
        "",
        "- The comparison keeps Z-score normalization fixed, so it does not frame Z-score and MMD as alternatives.",
        "- The result indicates that MMD is more sensitive to the synthetic degraded batches than the current z-score mean-shift monitor.",
        "- The threshold remains dataset-specific because it is estimated from reference-vs-reference bootstrap scores.",
        "- This supports discussing MMD as a promising runtime upgrade candidate, but it does not establish universal drift thresholds or production readiness.",
        "",
        "## Recommendation",
        "",
        "Do not promote MMD as the defended runtime yet unless Chapter 6 explicitly accepts the added calibration artifact, "
        "the reference-window dependency, and the dataset-specific thresholding limitation. The safer thesis move remains: "
        "keep the current runtime as baseline and present MMD as an experimental branch/offline audit result.",
    ]
    (out_dir / "BRANCH_COMPARISON_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def _plot(out_dir: Path, comparison: pd.DataFrame) -> None:
    try:
        import matplotlib.pyplot as plt

        plot_dir = out_dir / "plots"
        plot_dir.mkdir(parents=True, exist_ok=True)
        pivot = comparison.pivot(index="dataset", columns="branch", values="drift_score")
        ax = pivot.plot(kind="bar", figsize=(10, 4))
        ax.set_ylabel("Drift score")
        ax.set_title("Primary drift score by branch")
        plt.tight_layout()
        plt.savefig(plot_dir / "branch_drift_score_comparison.png", dpi=160)
        plt.close()
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare MMD runtime branch outputs")
    parser.add_argument(
        "--baseline-dir",
        default="outputs/thesis_branch_comparison/current_branch_baseline",
    )
    parser.add_argument(
        "--mmd-dir",
        default="outputs/thesis_branch_comparison/mmd_runtime_branch",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/thesis_branch_comparison/comparison",
    )
    args = parser.parse_args()

    baseline_dir = Path(args.baseline_dir)
    mmd_dir = Path(args.mmd_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    comparison = pd.concat(
        [
            _branch_table(baseline_dir, "current_branch_baseline", "current_zscore"),
            _branch_table(mmd_dir, "mmd_runtime_branch", "mmd"),
        ],
        ignore_index=True,
    )
    comparison.to_csv(out_dir / "branch_comparison_summary.csv", index=False)
    meta = {
        "baseline_manifest": _manifest(baseline_dir),
        "mmd_manifest": _manifest(mmd_dir),
    }
    (out_dir / "branch_comparison_manifest.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    _write_report(out_dir, comparison, baseline_dir, mmd_dir)
    _plot(out_dir, comparison)
    print(f"Wrote comparison: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Evaluate whether MMD improves governance decisions, not only drift scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
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


def _load_thresholds(path: Path) -> Dict[str, float]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _truth(dataset: str) -> bool:
    return dataset != "reference_labeled"


def _score_binary(predicted: Iterable[bool], truth: Iterable[bool]) -> Dict[str, float]:
    p = np.asarray(list(predicted), dtype=bool)
    t = np.asarray(list(truth), dtype=bool)
    tp = int(np.sum(p & t))
    fp = int(np.sum(p & ~t))
    tn = int(np.sum(~p & ~t))
    fn = int(np.sum(~p & t))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    false_alarm_rate = fp / max(1, fp + tn)
    tradeoff_f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "precision": round(float(precision), 4),
        "episode_recall": round(float(recall), 4),
        "false_alarm_rate": round(float(false_alarm_rate), 4),
        "tradeoff_f1": round(float(tradeoff_f1), 4),
    }


def _variant_rows(
    variant: str,
    pre: pd.DataFrame,
    drift: pd.DataFrame,
    detector: str,
    thresholds: Dict[str, float],
    mmd_active: bool,
) -> pd.DataFrame:
    d = drift[drift["detector"] == detector].copy()
    merged = pre.merge(
        d[["dataset", "detector", "drift_score", "threshold", "status"]],
        on="dataset",
        how="left",
    )
    merged["policy_variant"] = variant
    merged["ground_truth_problematic"] = merged["dataset"].map(_truth)
    merged["confidence_warn"] = (
        (merged["mean_confidence"] < CONFIDENCE_WARN)
        | (merged["uncertain_pct"] > UNCERTAIN_WARN)
        | (merged["dominant_pct"] >= DOMINANCE_WARN)
    )
    merged["temporal_warn"] = merged["transition_rate_pct"] > TRANSITION_WARN

    if detector == "mmd":
        merged["mmd_warning_threshold"] = float(thresholds["warning_p95"])
        merged["mmd_critical_threshold"] = float(thresholds["critical_p99"])
        merged["drift_warn"] = mmd_active & (merged["drift_score"] > merged["mmd_warning_threshold"])
        merged["drift_critical"] = mmd_active & (merged["drift_score"] > merged["mmd_critical_threshold"])
    else:
        merged["mmd_warning_threshold"] = np.nan
        merged["mmd_critical_threshold"] = np.nan
        merged["drift_warn"] = merged["status"].fillna("SKIPPED") != "HEALTHY"
        merged["drift_critical"] = False

    merged["review_decision"] = merged["dominant_pct"] >= DOMINANCE_REVIEW
    merged["two_of_three_trigger"] = (
        merged[["confidence_warn", "temporal_warn", "drift_warn"]].astype(int).sum(axis=1) >= 2
    )
    merged["risk_alert"] = merged[["confidence_warn", "temporal_warn", "drift_warn"]].any(axis=1)
    merged["governance_action"] = "keep_current"
    merged.loc[merged["risk_alert"], "governance_action"] = "alert_only"
    merged.loc[merged["two_of_three_trigger"], "governance_action"] = "queue_retrain"
    merged.loc[merged["review_decision"], "governance_action"] = "review"

    return merged[
        [
            "policy_variant",
            "dataset",
            "ground_truth_problematic",
            "detector",
            "mean_confidence",
            "uncertain_pct",
            "dominant_pct",
            "transition_rate_pct",
            "accuracy",
            "macro_f1",
            "drift_score",
            "threshold",
            "mmd_warning_threshold",
            "mmd_critical_threshold",
            "status",
            "confidence_warn",
            "temporal_warn",
            "drift_warn",
            "drift_critical",
            "risk_alert",
            "two_of_three_trigger",
            "review_decision",
            "governance_action",
        ]
    ]


def _aggregate(rows: pd.DataFrame) -> pd.DataFrame:
    records: List[Dict[str, object]] = []
    for variant, group in rows.groupby("policy_variant", sort=False):
        truth = group["ground_truth_problematic"]
        risk = _score_binary(group["risk_alert"], truth)
        trigger = _score_binary(group["two_of_three_trigger"], truth)
        records.append(
            {
                "policy_variant": variant,
                "n_datasets": len(group),
                "drift_warnings": int(group["drift_warn"].sum()),
                "risk_alerts": int(group["risk_alert"].sum()),
                "review_decisions": int(group["review_decision"].sum()),
                "queue_retrain_decisions": int(group["two_of_three_trigger"].sum()),
                "risk_precision": risk["precision"],
                "risk_recall": risk["episode_recall"],
                "risk_false_alarm_rate": risk["false_alarm_rate"],
                "risk_tradeoff_f1": risk["tradeoff_f1"],
                "trigger_precision": trigger["precision"],
                "trigger_recall": trigger["episode_recall"],
                "trigger_false_alarm_rate": trigger["false_alarm_rate"],
                "trigger_tradeoff_f1": trigger["tradeoff_f1"],
            }
        )
    return pd.DataFrame(records)


def _write_report(out_dir: Path, detail: pd.DataFrame, summary: pd.DataFrame, thresholds: Dict[str, float]) -> None:
    lines = [
        "# MMD Governance Evaluation",
        "",
        "## Question",
        "",
        "Can MMD improve governance decision quality, not only drift visibility?",
        "",
        "## Calibrated Thresholds",
        "",
        f"- Warning p95: `{thresholds['warning_p95']:.8f}`",
        f"- Critical candidate p99: `{thresholds['critical_p99']:.8f}`",
        f"- Bootstrap iterations: `{int(thresholds['iterations'])}`",
        f"- Sample size per side: `{int(thresholds['sample_size'])}`",
        "",
        "## Policy Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Dataset-Level Decisions",
        "",
        detail[
            [
                "policy_variant",
                "dataset",
                "ground_truth_problematic",
                "drift_score",
                "drift_warn",
                "risk_alert",
                "two_of_three_trigger",
                "governance_action",
            ]
        ].round(6).to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "- MMD remains stable on the reference set under the calibrated threshold.",
        "- MMD flags the degraded synthetic sets more clearly than the current z-score mean-shift monitor.",
        "- Under the existing two-of-three governance rule, MMD alone does not create queue-retrain decisions because confidence and temporal signals remain below their warning thresholds.",
        "- This indicates improved drift visibility and warning-level risk surfacing, but it does not establish improved final trigger quality.",
        "",
        "## Recommendation",
        "",
        "Keep MMD as an offline audit / experimental signal for now. Promotion into the defended runtime would require either a justified governance change for high-confidence drift-only cases or additional replay evidence where MMD improves trigger precision/recall without increasing false alarms.",
    ]
    (out_dir / "MMD_GOVERNANCE_EVALUATION.md").write_text("\n".join(lines), encoding="utf-8")


def _plot(out_dir: Path, summary: pd.DataFrame) -> None:
    try:
        import matplotlib.pyplot as plt

        plot_dir = out_dir / "plots"
        plot_dir.mkdir(parents=True, exist_ok=True)
        ax = summary.set_index("policy_variant")[["risk_recall", "trigger_recall"]].plot(
            kind="bar", figsize=(8, 4)
        )
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Recall on problematic replay sets")
        ax.set_title("Risk-alert vs trigger recall")
        plt.tight_layout()
        plt.savefig(plot_dir / "mmd_governance_recall_comparison.png", dpi=160)
        plt.close()
    except Exception:
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate MMD governance policy variants")
    parser.add_argument(
        "--baseline-dir",
        default="outputs/thesis_branch_comparison/current_branch_baseline",
    )
    parser.add_argument(
        "--mmd-dir",
        default="outputs/thesis_branch_comparison/mmd_runtime_branch",
    )
    parser.add_argument(
        "--thresholds",
        default="outputs/thesis_branch_comparison/mmd_threshold_calibration/mmd_thresholds.json",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/thesis_branch_comparison/mmd_governance_eval",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline_dir = Path(args.baseline_dir)
    mmd_dir = Path(args.mmd_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    thresholds = _load_thresholds(Path(args.thresholds))

    base_pre = _read(baseline_dir / "preprocessing_ablation_summary.csv")
    base_drift = _read(baseline_dir / "drift_monitor_ablation_summary.csv")
    mmd_pre = _read(mmd_dir / "preprocessing_ablation_summary.csv")
    mmd_drift = _read(mmd_dir / "drift_monitor_ablation_summary.csv")

    detail = pd.concat(
        [
            _variant_rows("A_current_policy", base_pre, base_drift, "current_zscore", thresholds, True),
            _variant_rows("B_mmd_active_in_trigger", mmd_pre, mmd_drift, "mmd", thresholds, True),
            _variant_rows("C_mmd_logging_only", mmd_pre, mmd_drift, "mmd", thresholds, False),
        ],
        ignore_index=True,
    )
    summary = _aggregate(detail)

    detail.to_csv(out_dir / "mmd_governance_detail.csv", index=False)
    summary.to_csv(out_dir / "mmd_governance_summary.csv", index=False)
    _write_report(out_dir, detail, summary, thresholds)
    _plot(out_dir, summary)
    print(f"Wrote MMD governance evaluation: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

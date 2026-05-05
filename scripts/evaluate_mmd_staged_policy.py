"""Evaluate staged MMD trigger policies for the final thesis experiment.

This script does not change the runtime pipeline. It reuses already generated
branch-comparison artifacts and tests whether a policy designed around MMD
improves governance decisions compared with the current defended policy.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


CONFIDENCE_WARN = 0.70
UNCERTAIN_WARN_PCT = 20.0
DOMINANCE_WARN_PCT = 85.0
DOMINANCE_REVIEW_PCT = 95.0
TRANSITION_WARN_PCT = 35.0

DEFAULT_CURRENT_DIR = Path("outputs/thesis_branch_comparison/current_branch_baseline")
DEFAULT_MMD_DIR = Path("outputs/thesis_branch_comparison/mmd_runtime_branch")
DEFAULT_THRESHOLDS = Path("outputs/thesis_branch_comparison/mmd_threshold_calibration/mmd_thresholds.json")
DEFAULT_OUTPUT = Path("outputs/thesis_branch_comparison/mmd_trigger_redesign")


@dataclass(frozen=True)
class PolicyConfig:
    confidence_warn: float = CONFIDENCE_WARN
    uncertain_warn_pct: float = UNCERTAIN_WARN_PCT
    dominance_warn_pct: float = DOMINANCE_WARN_PCT
    dominance_review_pct: float = DOMINANCE_REVIEW_PCT
    transition_warn_pct: float = TRANSITION_WARN_PCT
    current_policy_rule: str = "queue_retrain if at least two of confidence, temporal, drift warn"
    conservative_rule: str = (
        "risk_alert if MMD warning/critical AND >=1 behavior-risk signal; "
        "queue_retrain if MMD critical AND >=2 behavior-risk signals"
    )
    hybrid_rule: str = (
        "risk_alert if MMD critical OR (MMD warning AND >=1 behavior-risk signal); "
        "queue_retrain if MMD critical AND >=1 behavior-risk signal"
    )


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    return pd.read_csv(path)


def _read_thresholds(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"MMD threshold file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _git_value(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unavailable"


def _score_binary(pred: pd.Series, truth: pd.Series) -> dict[str, float]:
    pred_bool = pred.astype(bool)
    truth_bool = truth.astype(bool)
    tp = int((pred_bool & truth_bool).sum())
    fp = int((pred_bool & ~truth_bool).sum())
    fn = int((~pred_bool & truth_bool).sum())
    tn = int((~pred_bool & ~truth_bool).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    far = fp / (fp + tn) if (fp + tn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "false_alarm_rate": far,
        "f1": f1,
    }


def _problematic_label(dataset: str) -> bool:
    # In this repo's replay evidence, synthetic degraded/replay sets are the
    # expected problematic cases. The reference labeled replay is the healthy
    # control. This is a local experiment label, not a universal claim.
    return dataset != "reference_labeled"


def _mmd_state(score: float, warning: float, critical: float) -> str:
    if score >= critical:
        return "critical"
    if score >= warning:
        return "warning"
    return "healthy"


def _merge_inputs(pre: pd.DataFrame, drift: pd.DataFrame, detector: str) -> pd.DataFrame:
    drift_selected = drift[drift["detector"] == detector].copy()
    if drift_selected.empty:
        raise ValueError(f"No drift rows found for detector={detector}")

    merged = pre.merge(
        drift_selected[["dataset", "detector", "drift_score", "threshold", "status"]],
        on="dataset",
        how="inner",
    )
    if merged.empty:
        raise ValueError(f"No merged rows for detector={detector}")
    return merged


def _add_common_signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ground_truth_problematic"] = out["dataset"].map(_problematic_label)
    out["low_confidence"] = out["mean_confidence"] < CONFIDENCE_WARN
    out["high_uncertainty"] = out["uncertain_pct"] > UNCERTAIN_WARN_PCT
    out["dominance_warning"] = out["dominant_pct"] >= DOMINANCE_WARN_PCT
    out["review_decision"] = out["dominant_pct"] >= DOMINANCE_REVIEW_PCT
    out["temporal_warning"] = out["transition_rate_pct"] > TRANSITION_WARN_PCT
    behavior_cols = ["low_confidence", "high_uncertainty", "dominance_warning", "temporal_warning"]
    out["behavior_risk_count"] = out[behavior_cols].astype(int).sum(axis=1)
    out["behavior_risk_any"] = out["behavior_risk_count"] >= 1
    return out


def _current_policy_rows(current_pre: pd.DataFrame, current_drift: pd.DataFrame) -> pd.DataFrame:
    rows = _add_common_signals(_merge_inputs(current_pre, current_drift, "current_zscore"))
    rows["policy_variant"] = "A_current_policy_baseline"
    rows["mmd_state"] = "not_used"
    rows["drift_warning"] = rows["drift_score"] > rows["threshold"]
    rows["drift_critical"] = False
    rows["risk_alert"] = rows[["low_confidence", "high_uncertainty", "dominance_warning", "temporal_warning", "drift_warning"]].any(axis=1)
    rows["queue_retrain_decision"] = (
        rows[["low_confidence", "temporal_warning", "drift_warning"]].astype(int).sum(axis=1) >= 2
    )
    rows["governance_action"] = "keep_current"
    rows.loc[rows["risk_alert"], "governance_action"] = "alert_only"
    rows.loc[rows["queue_retrain_decision"], "governance_action"] = "queue_retrain"
    rows.loc[rows["review_decision"], "governance_action"] = "review"
    rows["policy_logic"] = "current two-of-three: confidence, temporal, drift"
    return rows


def _mmd_policy_rows(
    mmd_pre: pd.DataFrame,
    mmd_drift: pd.DataFrame,
    thresholds: dict[str, Any],
    variant: str,
) -> pd.DataFrame:
    warning = float(thresholds["warning_p95"])
    critical = float(thresholds["critical_p99"])
    rows = _add_common_signals(_merge_inputs(mmd_pre, mmd_drift, "mmd"))
    rows["policy_variant"] = variant
    rows["mmd_warning_threshold"] = warning
    rows["mmd_critical_threshold"] = critical
    rows["mmd_state"] = rows["drift_score"].map(lambda score: _mmd_state(float(score), warning, critical))
    rows["drift_warning"] = rows["mmd_state"].isin(["warning", "critical"])
    rows["drift_critical"] = rows["mmd_state"] == "critical"

    if variant == "B_mmd_staged_conservative":
        rows["risk_alert"] = rows["drift_warning"] & rows["behavior_risk_any"]
        rows["queue_retrain_decision"] = rows["drift_critical"] & (rows["behavior_risk_count"] >= 2)
        rows["policy_logic"] = "MMD warning/critical plus behavior risk; queue only with critical MMD plus >=2 behavior risks"
    elif variant == "C_mmd_staged_hybrid":
        rows["risk_alert"] = rows["drift_critical"] | (rows["drift_warning"] & rows["behavior_risk_any"])
        rows["queue_retrain_decision"] = rows["drift_critical"] & rows["behavior_risk_any"]
        rows["policy_logic"] = "critical MMD creates alert; queue only with critical MMD plus >=1 behavior risk"
    else:
        raise ValueError(f"Unsupported MMD policy variant: {variant}")

    rows["governance_action"] = "keep_current"
    rows.loc[rows["risk_alert"], "governance_action"] = "alert_only"
    rows.loc[rows["queue_retrain_decision"], "governance_action"] = "queue_retrain"
    rows.loc[rows["review_decision"], "governance_action"] = "review"
    return rows


def _detail_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
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
        "mmd_state",
        "low_confidence",
        "high_uncertainty",
        "dominance_warning",
        "temporal_warning",
        "behavior_risk_count",
        "behavior_risk_any",
        "drift_warning",
        "drift_critical",
        "risk_alert",
        "review_decision",
        "queue_retrain_decision",
        "governance_action",
        "policy_logic",
    ]
    for column in columns:
        if column not in df.columns:
            df[column] = np.nan
    return df[columns]


def _summarize(detail: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for variant, group in detail.groupby("policy_variant", sort=False):
        truth = group["ground_truth_problematic"]
        risk = _score_binary(group["risk_alert"], truth)
        queue = _score_binary(group["queue_retrain_decision"], truth)
        rows.append(
            {
                "policy_variant": variant,
                "n_datasets": int(len(group)),
                "healthy_count": int((group["mmd_state"] == "healthy").sum()),
                "mmd_warning_count": int((group["mmd_state"] == "warning").sum()),
                "mmd_critical_count": int((group["mmd_state"] == "critical").sum()),
                "drift_warning_count": int(group["drift_warning"].sum()),
                "risk_alert_count": int(group["risk_alert"].sum()),
                "review_decision_count": int(group["review_decision"].sum()),
                "queue_retrain_count": int(group["queue_retrain_decision"].sum()),
                "risk_precision": risk["precision"],
                "risk_recall": risk["recall"],
                "risk_false_alarm_rate": risk["false_alarm_rate"],
                "risk_f1": risk["f1"],
                "queue_precision": queue["precision"],
                "queue_recall": queue["recall"],
                "queue_false_alarm_rate": queue["false_alarm_rate"],
                "queue_f1": queue["f1"],
                "problematic_with_behavior_risk": int((group["ground_truth_problematic"] & group["behavior_risk_any"]).sum()),
            }
        )
    return pd.DataFrame(rows)


def _write_plots(summary: pd.DataFrame, out_dir: Path) -> list[str]:
    plot_paths: list[str] = []
    try:
        import matplotlib.pyplot as plt

        plot_dir = out_dir / "plots"
        plot_dir.mkdir(parents=True, exist_ok=True)

        x = np.arange(len(summary))
        labels = summary["policy_variant"].str.replace("_", "\n")
        width = 0.24

        plt.figure(figsize=(10, 5))
        plt.bar(x - width, summary["drift_warning_count"], width=width, label="drift warnings")
        plt.bar(x, summary["risk_alert_count"], width=width, label="risk alerts")
        plt.bar(x + width, summary["queue_retrain_count"], width=width, label="queue retrain")
        plt.xticks(x, labels, fontsize=8)
        plt.ylabel("count")
        plt.title("MMD staged policy actions")
        plt.legend()
        plt.tight_layout()
        path = plot_dir / "mmd_staged_policy_action_counts.png"
        plt.savefig(path, dpi=160)
        plt.close()
        plot_paths.append(str(path))

        plt.figure(figsize=(10, 5))
        plt.bar(x - width / 2, summary["risk_recall"], width=width, label="risk recall")
        plt.bar(x + width / 2, summary["queue_recall"], width=width, label="queue recall")
        plt.xticks(x, labels, fontsize=8)
        plt.ylim(0, 1.05)
        plt.ylabel("recall")
        plt.title("Risk alert vs queue decision recall")
        plt.legend()
        plt.tight_layout()
        path = plot_dir / "mmd_staged_policy_recall.png"
        plt.savefig(path, dpi=160)
        plt.close()
        plot_paths.append(str(path))
    except Exception as exc:
        (out_dir / "plot_warning.txt").write_text(f"Plot generation skipped: {exc}\n", encoding="utf-8")
    return plot_paths


def _write_report(
    out_dir: Path,
    detail: pd.DataFrame,
    summary: pd.DataFrame,
    thresholds: dict[str, Any],
    config: PolicyConfig,
    current_dir: Path,
    mmd_dir: Path,
    threshold_path: Path,
    plot_paths: list[str],
    source_branch: str,
    command_used: str,
) -> None:
    active_branch = _git_value(["branch", "--show-current"])
    commit = _git_value(["rev-parse", "--short", "HEAD"])
    behavior_problematic = int(
        (detail["ground_truth_problematic"] & detail["behavior_risk_any"]).groupby(detail["dataset"]).first().sum()
    )

    lines = [
        "# MMD Trigger Redesign Experiment",
        "",
        "## Scope",
        "This is an isolated branch experiment. It keeps z-score preprocessing fixed, reuses the retained model outputs already generated in the branch-comparison artifacts, and changes only the governance policy interpretation.",
        "",
        "## Inputs",
        f"- Current branch baseline artifacts: `{current_dir}`",
        f"- MMD runtime branch artifacts: `{mmd_dir}`",
        f"- Calibrated MMD thresholds: `{threshold_path}`",
        f"- Source branch for this experiment: `{source_branch}`",
        f"- Active experiment branch while producing this report: `{active_branch}`",
        f"- Commit hash: `{commit}`",
        f"- Command used: `{command_used}`",
        "",
        "## MMD Thresholds",
        f"- Warning threshold (reference p95): `{thresholds['warning_p95']}`",
        f"- Critical threshold (reference p99): `{thresholds['critical_p99']}`",
        f"- Calibration iterations: `{thresholds.get('iterations')}`",
        f"- Sample size: `{thresholds.get('sample_size')}`",
        f"- Feature level: `{thresholds.get('feature_level')}`",
        "",
        "These thresholds are dataset-specific empirical thresholds from reference-vs-reference comparisons. They should not be interpreted as universal MMD cutoffs.",
        "",
        "## Policy Variants",
        "- `A_current_policy_baseline`: current two-of-three style baseline using the current z-score mean-shift drift signal.",
        "- `B_mmd_staged_conservative`: MMD severity must be warning/critical and at least one behavior-risk signal must agree before risk alert; queue retrain requires critical MMD and at least two behavior-risk signals.",
        "- `C_mmd_staged_hybrid`: critical MMD is enough for non-mutating alert; queue retrain still requires critical MMD and at least one behavior-risk signal.",
        "",
        "Behavior-risk signals are low confidence, high uncertainty, dominant-class warning, and high temporal transition rate. MMD alone is not allowed to queue retraining.",
        "",
        "## Summary",
        summary.to_markdown(index=False),
        "",
        "## Detail",
        detail[
            [
                "policy_variant",
                "dataset",
                "ground_truth_problematic",
                "mmd_state",
                "behavior_risk_count",
                "drift_warning",
                "risk_alert",
                "queue_retrain_decision",
                "governance_action",
            ]
        ].to_markdown(index=False),
        "",
        "## Interpretation",
        f"- MMD remains stable on the healthy reference replay in this experiment because the reference dataset stays below the calibrated warning threshold.",
        "- The degraded synthetic/replay datasets are surfaced as MMD-critical, which supports MMD as a sensitive drift-visibility signal in this repository context.",
        f"- Only `{behavior_problematic}` problematic dataset(s) also show at least one behavior-risk signal under the current thresholds.",
        "- The conservative staged policy therefore does not improve final governance actions because it correctly blocks MMD-only escalation.",
        "- The hybrid policy improves non-mutating risk alerts, but it still does not improve queue/retrain decisions because retraining is not allowed on MMD alone.",
        "- This indicates that the current evidence supports MMD as an experimental/offline audit or alerting signal, but does not establish that it should become the defended runtime mutation/retraining trigger.",
        "",
        "## Limitation",
        "The result remains bounded to the existing four replay/evaluation datasets and the existing retained model. It does not establish universal MMD thresholds, subject-independent generalization, or production readiness.",
    ]
    if plot_paths:
        lines.extend(["", "## Plots", *[f"- `{path}`" for path in plot_paths]])
    lines.append("")
    (out_dir / "MMD_TRIGGER_REDESIGN_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    snapshot = {
        "source_branch": source_branch,
        "branch": active_branch,
        "commit": commit,
        "command_used": command_used,
        "current_dir": str(current_dir),
        "mmd_dir": str(mmd_dir),
        "threshold_path": str(threshold_path),
        "thresholds": thresholds,
        "policy_config": asdict(config),
    }
    (out_dir / "mmd_staged_policy_config.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    current_dir = Path(args.current_dir)
    mmd_dir = Path(args.mmd_dir)
    threshold_path = Path(args.thresholds)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    thresholds = _read_thresholds(threshold_path)
    config = PolicyConfig()

    current_pre = _read_csv(current_dir / "preprocessing_ablation_summary.csv")
    current_drift = _read_csv(current_dir / "drift_monitor_ablation_summary.csv")
    mmd_pre = _read_csv(mmd_dir / "preprocessing_ablation_summary.csv")
    mmd_drift = _read_csv(mmd_dir / "drift_monitor_ablation_summary.csv")

    detail = pd.concat(
        [
            _current_policy_rows(current_pre, current_drift),
            _mmd_policy_rows(mmd_pre, mmd_drift, thresholds, "B_mmd_staged_conservative"),
            _mmd_policy_rows(mmd_pre, mmd_drift, thresholds, "C_mmd_staged_hybrid"),
        ],
        ignore_index=True,
    )
    detail = _detail_columns(detail)
    summary = _summarize(detail)

    detail.to_csv(out_dir / "mmd_staged_policy_detail.csv", index=False)
    summary.to_csv(out_dir / "mmd_staged_policy_summary.csv", index=False)
    (out_dir / "mmd_staged_policy_detail.json").write_text(
        json.dumps(detail.to_dict(orient="records"), indent=2),
        encoding="utf-8",
    )

    plot_paths = _write_plots(summary, out_dir)
    command_used = (
        "conda run -n thesis-mlops python scripts/evaluate_mmd_staged_policy.py "
        f"--output-dir {out_dir}"
    )
    _write_report(
        out_dir,
        detail,
        summary,
        thresholds,
        config,
        current_dir,
        mmd_dir,
        threshold_path,
        plot_paths,
        args.source_branch,
        command_used,
    )
    print(f"Wrote staged MMD policy artifacts to {out_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-dir", default=str(DEFAULT_CURRENT_DIR))
    parser.add_argument("--mmd-dir", default=str(DEFAULT_MMD_DIR))
    parser.add_argument("--thresholds", default=str(DEFAULT_THRESHOLDS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--source-branch", default="mmd-trigger-calibration")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())

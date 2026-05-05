"""Evaluate candidate promotion eligibility from the scaler comparison report."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPARISON = PROJECT_ROOT / "reports" / "scaler_policy_comparison_2026-04-27.json"
OUT_JSON = PROJECT_ROOT / "reports" / "model_promotion_gate_2026-04-27.json"
OUT_MD = PROJECT_ROOT / "reports" / "model_promotion_gate_2026-04-27.md"


def _metric(report: dict, scaler: str, model: str, split: str, key: str) -> float:
    return float(report["evaluations"][scaler][model]["splits"][split][key])


def _fmt(value: float) -> str:
    return f"{value:.4f}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, default=DEFAULT_COMPARISON)
    parser.add_argument("--min-macro-f1-delta", type=float, default=0.01)
    args = parser.parse_args()

    report = json.loads(args.comparison.read_text(encoding="utf-8"))
    scaler = "train_only_users_1_4"
    baseline = "defended_runtime"
    candidate = "candidate_har_model_latest"
    splits = ["val_user_5", "test_user_6"]

    split_results = {}
    for split in splits:
        baseline_f1 = _metric(report, scaler, baseline, split, "macro_f1")
        candidate_f1 = _metric(report, scaler, candidate, split, "macro_f1")
        baseline_acc = _metric(report, scaler, baseline, split, "accuracy")
        candidate_acc = _metric(report, scaler, candidate, split, "accuracy")
        split_results[split] = {
            "baseline_accuracy": baseline_acc,
            "candidate_accuracy": candidate_acc,
            "baseline_macro_f1": baseline_f1,
            "candidate_macro_f1": candidate_f1,
            "macro_f1_delta": candidate_f1 - baseline_f1,
            "passes": (candidate_f1 - baseline_f1) >= args.min_macro_f1_delta,
        }

    eligible = all(item["passes"] for item in split_results.values())
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "comparison_report": str(args.comparison),
        "baseline_model": report["evaluations"][scaler][baseline]["path"],
        "candidate_model": report["evaluations"][scaler][candidate]["path"],
        "scaler_policy_for_gate": scaler,
        "min_macro_f1_delta": args.min_macro_f1_delta,
        "split_results": split_results,
        "promotion_eligible": eligible,
        "promotion_applied": False,
        "reason": (
            "Candidate is promotion-eligible on labeled val/test splits, but this script does not "
            "change runtime defaults automatically."
            if eligible
            else "Candidate is not promotion-eligible because at least one labeled split failed the gate."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Model Promotion Gate",
        "",
        f"Generated: {payload['created_at']}",
        "",
        f"Baseline: `{payload['baseline_model']}`",
        f"Candidate: `{payload['candidate_model']}`",
        f"Scaler policy: `{scaler}`",
        "",
        "| Split | Baseline acc | Candidate acc | Baseline macro-F1 | Candidate macro-F1 | Delta | Pass |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for split, metrics in split_results.items():
        lines.append(
            "| {split} | {ba} | {ca} | {bf} | {cf} | {delta} | {passes} |".format(
                split=split,
                ba=_fmt(metrics["baseline_accuracy"]),
                ca=_fmt(metrics["candidate_accuracy"]),
                bf=_fmt(metrics["baseline_macro_f1"]),
                cf=_fmt(metrics["candidate_macro_f1"]),
                delta=_fmt(metrics["macro_f1_delta"]),
                passes=metrics["passes"],
            )
        )
    lines.extend(
        [
            "",
            f"Promotion eligible: **{eligible}**",
            "",
            "Promotion applied: **False**",
            "",
            "Reason: the gate records eligibility only. Runtime defaults must be changed as a separate explicit governance decision.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Promotion eligible: {eligible}")
    for split, metrics in split_results.items():
        print(
            f"{split}: baseline_f1={metrics['baseline_macro_f1']:.4f} "
            f"candidate_f1={metrics['candidate_macro_f1']:.4f} "
            f"delta={metrics['macro_f1_delta']:.4f}"
        )
    print(f"Saved: {OUT_JSON}")
    print(f"Saved: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

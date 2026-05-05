"""Build the A4/A5 retraining-governance matrix artifact.

The matrix separates three decisions that must not be mixed:
1. monitoring/trigger action,
2. whether retraining is allowed,
3. whether a trained candidate may be promoted.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.trigger_policy import TriggerPolicyEngine


OUT_JSON = PROJECT_ROOT / "reports" / "governance_matrix_2026-04-27.json"
OUT_MD = PROJECT_ROOT / "reports" / "governance_matrix_2026-04-27.md"
STATE_DIR = PROJECT_ROOT / "reports" / "governance_matrix_state"


def _report(mean_conf: float, entropy: float, uncertain: float, flip: float, drift: float) -> Dict:
    return {
        "confidence_report": {
            "metrics": {
                "mean_confidence": mean_conf,
                "mean_entropy": entropy,
                "uncertain_ratio": uncertain,
            }
        },
        "temporal_report": {"metrics": {"flip_rate": flip}},
        "drift_report": {
            "aggregate_drift_score": drift,
            "n_drifted_channels": 0,
            "per_channel_metrics": {
                "Ax": {"drift_zscore": drift},
                "Ay": {"drift_zscore": drift},
                "Az": {"drift_zscore": drift},
                "Gx": {"drift_zscore": drift},
                "Gy": {"drift_zscore": drift},
                "Gz": {"drift_zscore": drift},
            },
        },
    }


def _collapse_report() -> Dict:
    report = _report(mean_conf=0.94, entropy=0.3, uncertain=0.02, flip=0.0, drift=0.4)
    report["collapse_signals"] = {
        "dominance_warning": True,
        "dominant_class": "hand_tapping",
        "dominant_pct": 96.0,
        "mean_confidence": 0.94,
        "transition_rate": 0.0,
    }
    return report


def _decision_for(name: str, report: Dict) -> Dict[str, Any]:
    state_file = STATE_DIR / f"{name}.json"
    if state_file.exists():
        state_file.unlink()
    engine = TriggerPolicyEngine(state_file=state_file)
    decision = engine.evaluate(report)
    return decision.to_dict()


def _promotion_decision(
    *,
    name: str,
    labels_available: bool,
    baseline_macro_f1: float | None,
    candidate_macro_f1: float | None,
    min_delta: float = 0.01,
) -> Dict[str, Any]:
    if not labels_available:
        return {
            "scenario": name,
            "labels_available": False,
            "promote": False,
            "reason": "No labels available; unlabeled data cannot authorize promotion.",
        }
    if baseline_macro_f1 is None or candidate_macro_f1 is None:
        return {
            "scenario": name,
            "labels_available": True,
            "promote": False,
            "reason": "Missing baseline or candidate macro-F1.",
        }
    delta = candidate_macro_f1 - baseline_macro_f1
    promote = delta >= min_delta
    return {
        "scenario": name,
        "labels_available": True,
        "baseline_macro_f1": baseline_macro_f1,
        "candidate_macro_f1": candidate_macro_f1,
        "min_delta": min_delta,
        "delta": delta,
        "promote": promote,
        "reason": (
            "Candidate exceeds baseline by the required margin."
            if promote
            else "Candidate does not exceed baseline by the required margin."
        ),
    }


def _row(name: str, trigger_decision: Dict, retraining_allowed: bool, promotion: Dict) -> Dict:
    return {
        "scenario": name,
        "trigger_action": trigger_decision["action"],
        "alert_level": trigger_decision["alert_level"],
        "trigger_should_retrain": trigger_decision["should_trigger"],
        "offline_retraining_allowed": retraining_allowed,
        "candidate_promote": promotion["promote"],
        "reason": trigger_decision["reason"],
        "promotion_reason": promotion["reason"],
    }


def _to_markdown(rows: List[Dict], promotion_cases: List[Dict]) -> str:
    header = (
        "| Scenario | Trigger action | Alert | Trigger retrain | Offline retraining | "
        "Candidate promotion | Reason |"
    )
    sep = "|---|---|---|---|---|---|---|"
    body = [
        "| {scenario} | {trigger_action} | {alert_level} | {trigger_should_retrain} | "
        "{offline_retraining_allowed} | {candidate_promote} | {reason} |".format(**row)
        for row in rows
    ]
    promo_header = "| Case | Labels | Baseline F1 | Candidate F1 | Promote | Reason |"
    promo_sep = "|---|---|---|---|---|---|"
    promo_body = []
    for case in promotion_cases:
        promo_body.append(
            "| {scenario} | {labels_available} | {baseline_macro_f1} | {candidate_macro_f1} | "
            "{promote} | {reason} |".format(
                scenario=case["scenario"],
                labels_available=case["labels_available"],
                baseline_macro_f1=case.get("baseline_macro_f1", ""),
                candidate_macro_f1=case.get("candidate_macro_f1", ""),
                promote=case["promote"],
                reason=case["reason"],
            )
        )
    return "\n".join(
        [
            "# A4/A5 Retraining Governance Matrix",
            "",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Trigger And Retraining Decisions",
            "",
            header,
            sep,
            *body,
            "",
            "## Candidate Promotion Gate",
            "",
            promo_header,
            promo_sep,
            *promo_body,
            "",
            "## Rule",
            "",
            "Retraining may produce candidates offline, but promotion requires labeled evidence and improvement over the current baseline. Collapse and no-label cases block automatic promotion.",
            "",
        ]
    )


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    decisions = {
        "healthy": _decision_for("healthy", _report(0.82, 0.9, 0.05, 0.08, 0.5)),
        "warning_review": _decision_for("warning_review", _report(0.60, 1.9, 0.22, 0.10, 0.5)),
        "critical_trigger": _decision_for("critical_trigger", _report(0.44, 2.3, 0.38, 0.45, 3.4)),
        "collapse_review": _decision_for("collapse_review", _collapse_report()),
    }

    promotion_cases = [
        _promotion_decision(
            name="no_labels",
            labels_available=False,
            baseline_macro_f1=None,
            candidate_macro_f1=None,
        ),
        _promotion_decision(
            name="worse_candidate",
            labels_available=True,
            baseline_macro_f1=0.72,
            candidate_macro_f1=0.68,
        ),
        _promotion_decision(
            name="better_candidate",
            labels_available=True,
            baseline_macro_f1=0.72,
            candidate_macro_f1=0.78,
        ),
    ]

    rows = [
        _row("healthy", decisions["healthy"], False, promotion_cases[0]),
        _row("warning_review", decisions["warning_review"], False, promotion_cases[0]),
        _row("critical_trigger_offline_candidate", decisions["critical_trigger"], True, promotion_cases[0]),
        _row("collapse_review_no_auto_retrain", decisions["collapse_review"], False, promotion_cases[0]),
        _row("worse_candidate_no_promotion", decisions["critical_trigger"], True, promotion_cases[1]),
        _row("better_candidate_promotion_eligible", decisions["critical_trigger"], True, promotion_cases[2]),
    ]

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decisions": decisions,
        "promotion_cases": promotion_cases,
        "matrix": rows,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_MD.write_text(_to_markdown(rows, promotion_cases), encoding="utf-8")

    print(f"Saved: {OUT_JSON}")
    print(f"Saved: {OUT_MD}")
    for row in rows:
        print(
            f"{row['scenario']}: action={row['trigger_action']} "
            f"trigger={row['trigger_should_retrain']} promote={row['candidate_promote']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

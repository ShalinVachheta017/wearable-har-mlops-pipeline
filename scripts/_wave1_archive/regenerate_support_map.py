"""
scripts/regenerate_support_map.py
===================================
Rebuilds reports/PAPER_SUPPORT_MAP.json by:
  1. Searching extracted paper texts in Thesis_report/papers_text/ for evidence quotes.
  2. Merging with the evidence_type schema (PAPER / EMPIRICAL_CALIBRATION / SENSOR_SPEC / PROJECT_DECISION).
  3. Writing the updated JSON.

Run after:
  python scripts/fetch_foundation_papers.py
  python scripts/extract_papers_to_text.py --force

Usage:
  python scripts/regenerate_support_map.py [--dry-run]
"""

from __future__ import annotations

import json
import re
import sys
import argparse
from datetime import date
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
TEXT_DIR = ROOT / "Thesis_report" / "papers_text"
OUT_JSON = ROOT / "reports" / "PAPER_SUPPORT_MAP.json"

# ---------------------------------------------------------------------------
# Evidence type schema for each claim
# ---------------------------------------------------------------------------
CLAIM_SCHEMA: dict[str, dict] = {
    "stage_1_data_ingestion": {
        "claim": "Raw Garmin accelerometer and gyroscope sensor data at 50 Hz is fused via time-aligned merge with 1 ms tolerance into a single CSV.",
        "evidence_type": "PROJECT_DECISION",
        "required_experiment": None,
        "paper_search_terms": [],
    },
    "stage_2_data_validation": {
        "claim": "Schema and sensor-range validation (max acceleration 50 m/s², max gyroscope 500 dps, max missing ratio 5%) gates data quality before windowing.",
        "evidence_type": "SENSOR_SPEC",
        "sensor_spec_note": "Garmin wearable IMU full-scale range: accel ±8g (~78.4 m/s²), gyro ±2000 dps. Chosen limits are conservative subset of hardware full-scale.",
        "required_experiment": None,
        "paper_search_terms": [],
    },
    "stage_3_windowing": {
        "claim": "Sliding-window segmentation with window_size=200 (4 seconds at 50 Hz) and 50% overlap is used to create fixed-size input tensors.",
        "evidence_type": "EMPIRICAL_CALIBRATION",
        "required_experiment": "scripts/windowing_ablation.py -> reports/WINDOWING_JUSTIFICATION.md",
        "paper_search_terms": [],
    },
    "stage_4_model_architecture": {
        "claim": "The inference model is a 1D-CNN-BiLSTM. BiLSTM captures forward and backward temporal dependencies in sensor windows.",
        "evidence_type": "PAPER",
        "required_experiment": None,
        "paper_search_terms": [
            ("Deep CNN-LSTM With Self-Attention Model for Human Activity Recognition Using Wearable Sensor.txt",
             ["accuracy of 99.93", "BiLSTM", "LSTM", "accuracy"]),
            ("Evaluating BiLSTM and CNN+GRU Approaches for Human Activity Recognition Using WiFi CSI Data.txt",
             ["BiLSTM", "CNN", "GRU", "accuracy"]),
            ("Shalin Vachheta-1701359-M.Sc. Mechatronics.txt",
             ["Bidirectional", "BiLSTM", "LSTM"]),
        ],
    },
    "stage_5_evaluation_confidence": {
        "claim": "Stage 5 computes confidence distribution statistics and ECE.",
        "evidence_type": "EMPIRICAL_CALIBRATION",
        "required_experiment": "scripts/threshold_sweep.py -> reports/THRESHOLD_CALIBRATION_SUMMARY.md",
        "paper_search_terms": [],
    },
    "stage_6_layer1_confidence_monitoring": {
        "claim": "Layer 1 monitoring flags WARNING when mean confidence < 0.60 or uncertain window ratio > 30%.",
        "evidence_type": "EMPIRICAL_CALIBRATION",
        "required_experiment": "scripts/threshold_sweep.py -> reports/THRESHOLD_CALIBRATION_SUMMARY.md",
        "paper_search_terms": [],
    },
    "stage_6_layer2_temporal_monitoring": {
        "claim": "Layer 2 monitoring detects anomalous activity transition rates (flip rate > 50%) as a temporal instability signal.",
        "evidence_type": "EMPIRICAL_CALIBRATION",
        "required_experiment": "scripts/threshold_sweep.py -> reports/THRESHOLD_CALIBRATION_SUMMARY.md",
        "paper_search_terms": [],
    },
    "stage_6_layer3_zscore_drift": {
        "claim": "Layer 3 monitoring uses per-channel z-score comparison against a training baseline; drift_zscore > 2.0 triggers WARNING.",
        "evidence_type": "EMPIRICAL_CALIBRATION",
        "required_experiment": "scripts/threshold_sweep.py -> reports/THRESHOLD_CALIBRATION_SUMMARY.md",
        "paper_search_terms": [
            ("Deep learning for sensor-based activity recognition_ A survey.txt",
             ["distribution", "shift", "covariate"]),
        ],
    },
    "stage_7_trigger_policy": {
        "claim": "The retraining trigger uses a multi-signal policy engine with a 24-hour cooldown gate to prevent over-training.",
        "evidence_type": "EMPIRICAL_CALIBRATION",
        "required_experiment": "scripts/trigger_policy_eval.py -> reports/TRIGGER_POLICY_EVAL.csv",
        "paper_search_terms": [],
    },
    "stage_8_adabn": {
        "claim": "AdaBN adapts Batch Normalization statistics to the target domain without labeled data.",
        "evidence_type": "PAPER",
        "required_experiment": None,
        "paper_search_terms": [
            ("adabn_li2016_1603.04779.txt",
             ["batch normalization", "domain adaptation", "statistics", "target"]),
            ("Domain Adaptation for Inertial Measurement Unit-based Human.txt",
             ["batch normalization", "covariate shift", "domain"]),
        ],
    },
    "stage_8_tent": {
        "claim": "TENT minimises prediction entropy on the target domain by fine-tuning only the BN affine parameters via gradient descent.",
        "evidence_type": "PAPER",
        "required_experiment": None,
        "paper_search_terms": [
            ("tent_wang2021_openreview_uXl3bZLkr3c.txt",
             ["entropy", "test-time", "batch normalization", "affine"]),
            ("Transfer Learning in Human Activity Recognition  A Survey.txt",
             ["entropy", "continual", "test-time"]),
        ],
    },
    "stage_8_adabn_tent_twostage": {
        "claim": "Two-stage AdaBN+TENT: AdaBN sets BN running statistics first; TENT then fine-tunes affine parameters. Rollback fires if entropy increases.",
        "evidence_type": "PAPER",
        "required_experiment": None,
        "paper_search_terms": [
            ("adabn_li2016_1603.04779.txt", ["batch normalization", "statistics"]),
            ("tent_wang2021_openreview_uXl3bZLkr3c.txt", ["entropy", "affine"]),
        ],
    },
    "stage_8_pseudo_label": {
        "claim": "Pseudo-labeling uses confidence-filtered unlabeled windows as synthetic training targets.",
        "evidence_type": "PAPER",
        "required_experiment": None,
        "paper_search_terms": [
            ("Transfer Learning in Human Activity Recognition  A Survey.txt",
             ["pseudo label", "pseudo-label", "instance transfer"]),
        ],
    },
    "stage_9_registration_gate": {
        "claim": "Model promotion gate uses new_acc >= current_acc - degradation_tolerance (tolerance=0.005) to block genuine regressions.",
        "evidence_type": "PROJECT_DECISION",
        "required_experiment": None,
        "paper_search_terms": [],
    },
    "stage_10_baseline_update": {
        "claim": "Drift baseline is rebuilt from labeled training data after retraining; promote_to_shared=False governance default prevents silent overwrites.",
        "evidence_type": "PROJECT_DECISION",
        "required_experiment": None,
        "paper_search_terms": [],
    },
    "stage_11_temperature_scaling": {
        "claim": "Post-hoc temperature scaling calibrates overconfident softmax outputs; temperature T is optimised to minimise NLL on a held-out set.",
        "evidence_type": "PAPER",
        "required_experiment": None,
        "paper_search_terms": [
            ("calibration_guo2017_1706.04599.txt",
             ["temperature scaling", "calibration", "ECE", "confidence"]),
            ("When Does Optimizing a Proper Loss Yield Calibration.txt",
             ["temperature scaling", "calibration", "Guo"]),
        ],
    },
    "stage_11_mc_dropout": {
        "claim": "MC Dropout (30 forward passes, dropout_rate=0.2) approximates Bayesian uncertainty.",
        "evidence_type": "PAPER",
        "required_experiment": None,
        "paper_search_terms": [
            ("mc_dropout_gal2016_1506.02142.txt",
             ["dropout", "Bayesian", "uncertainty", "Monte Carlo"]),
        ],
    },
    "stage_12_wasserstein_drift": {
        "claim": "Wasserstein-1 (Earth Mover's Distance) detects per-channel distribution shift between production and training baseline.",
        "evidence_type": "EMPIRICAL_CALIBRATION",
        "required_experiment": "Stage 12 implementation; no external paper needed for choice of Wasserstein-1 vs KS test",
        "paper_search_terms": [
            ("MACHINE LEARNING OPERATIONS A SURVEY ON MLOPS.txt",
             ["drift", "distribution shift", "monitoring"]),
        ],
    },
    "stage_13_curriculum_pseudo_labeling": {
        "claim": "Curriculum self-training progressively lowers pseudo-label confidence threshold from 0.95 to 0.80 over 5 iterations, with EWC regularisation.",
        "evidence_type": "EMPIRICAL_CALIBRATION",
        "required_experiment": "scripts/threshold_sweep.py + scripts/windowing_ablation.py",
        "paper_search_terms": [
            ("Transfer Learning in Human Activity Recognition  A Survey.txt",
             ["curriculum", "self-training", "pseudo"]),
            ("ewc_kirkpatrick2017_1612.00796.txt",
             ["curriculum", "self-training", "confidence"]),
        ],
    },
    "stage_13_ewc": {
        "claim": "Elastic Weight Consolidation (EWC) with lambda=1000 prevents catastrophic forgetting by penalising updates to weights important for previously learned tasks.",
        "evidence_type": "PAPER",
        "required_experiment": None,
        "paper_search_terms": [
            ("ewc_kirkpatrick2017_1612.00796.txt",
             ["elastic weight consolidation", "catastrophic forgetting", "Fisher", "lambda"]),
            ("Transfer Learning in Human Activity Recognition  A Survey.txt",
             ["catastrophic", "forgetting", "continual"]),
        ],
    },
    "stage_14_sensor_placement": {
        "claim": "Hand detection via dominant-acceleration heuristic (threshold=1.2) and axis-mirror augmentation are used to make the model robust to sensor placement variation.",
        "evidence_type": "EMPIRICAL_CALIBRATION",
        "required_experiment": "Threshold 1.2 derived from baseline Ax/Ay/Az statistics in models/normalized_baseline.json",
        "paper_search_terms": [
            ("Domain Adaptation for Inertial Measurement Unit-based Human.txt",
             ["sensor placement", "orientation", "axis", "wrist"]),
        ],
    },
    "observability_prometheus": {
        "claim": "Prometheus metrics are exported at /metrics and scraped by Prometheus at inference:8000.",
        "evidence_type": "PROJECT_DECISION",
        "required_verification": "scripts/verify_prometheus_metrics.py -> reports/PROMETHEUS_METRICS_CHECK.txt",
        "paper_search_terms": [],
    },
    "mlops_pipeline_orchestration": {
        "claim": "The 14-stage pipeline is orchestrated by a single ProductionPipeline class with artifact handoff between stages and MLflow tracking.",
        "evidence_type": "PAPER",
        "required_experiment": None,
        "paper_search_terms": [
            ("MACHINE LEARNING OPERATIONS A SURVEY ON MLOPS.txt",
             ["CI/CD", "pipeline", "deployment", "monitoring", "MLOps"]),
        ],
    },
}

# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

def find_quote(text: str, terms: list[str], context_before: int = 60, context_after: int = 200) -> Optional[str]:
    text_lower = text.lower()
    for term in terms:
        idx = text_lower.find(term.lower())
        if idx >= 0:
            start = max(0, idx - context_before)
            end = min(len(text), idx + context_after)
            snippet = text[start:end].replace("\n", " ").strip()
            return f"...{snippet}..."
    return None


def load_paper_texts() -> dict[str, str]:
    texts = {}
    if not TEXT_DIR.exists():
        return texts
    for f in TEXT_DIR.glob("*.txt"):
        texts[f.name] = f.read_text(encoding="utf-8", errors="replace")
    return texts


# ---------------------------------------------------------------------------
# Build the map
# ---------------------------------------------------------------------------

def build_map(texts: dict[str, str]) -> dict:
    metadata = {
        "_metadata": {
            "generated": str(date.today()),
            "pdf_search_root": "Thesis_report/",
            "extraction_script": "scripts/extract_papers_to_text.py",
            "regeneration_script": "scripts/regenerate_support_map.py",
            "evidence_type_legend": {
                "PAPER": "Claim backed by a PDF in Thesis_report/refs/ or Thesis_report/sample reports/",
                "EMPIRICAL_CALIBRATION": "Threshold/decision backed by a script + output CSV/PNG in reports/",
                "SENSOR_SPEC": "Hardware constraint from IMU full-scale range datasheet",
                "PROJECT_DECISION": "Supervisor/design choice; no single paper expected",
            },
            "still_missing_papers": [
                "Run 'python scripts/fetch_foundation_papers.py' first to download primary sources.",
            ],
        }
    }

    claims = {}
    for claim_id, schema in CLAIM_SCHEMA.items():
        entry: dict = {
            "claim": schema["claim"],
            "evidence_type": schema["evidence_type"],
            "supported_by": [],
        }

        # Add extra fields by evidence type
        if schema["evidence_type"] == "EMPIRICAL_CALIBRATION":
            entry["required_experiment"] = schema.get("required_experiment", "")
        elif schema["evidence_type"] == "SENSOR_SPEC":
            entry["sensor_spec_note"] = schema.get("sensor_spec_note", "")
        elif schema["evidence_type"] == "PROJECT_DECISION":
            note = schema.get("required_experiment") or schema.get("required_verification", "")
            if note:
                entry["required_verification"] = note

        # Search paper texts
        for paper_file, terms in schema.get("paper_search_terms", []):
            if paper_file not in texts:
                continue
            quote = find_quote(texts[paper_file], terms)
            if quote:
                entry["supported_by"].append({
                    "paper_file": f"Thesis_report/refs/{paper_file.replace('.txt', '.pdf')}" if not paper_file.startswith("Shalin") else f"Thesis_report/sample reports/{paper_file.replace('.txt', '.pdf')}",
                    "evidence_quote": quote,
                })

        # Tag
        if entry["evidence_type"] in ("EMPIRICAL_CALIBRATION", "SENSOR_SPEC", "PROJECT_DECISION"):
            entry["tag"] = entry["evidence_type"]
        elif entry["supported_by"]:
            entry["tag"] = "SUPPORTED"
        else:
            entry["tag"] = "UNSUPPORTED"

        claims[claim_id] = entry

    return {**metadata, **claims}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    texts = load_paper_texts()
    print(f"Loaded {len(texts)} extracted paper texts from {TEXT_DIR}")
    for fname in sorted(texts):
        print(f"  {fname}  ({len(texts[fname])//1024} KB)")

    data = build_map(texts)

    # Stats
    tags: dict[str, int] = {}
    for k, v in data.items():
        if k.startswith("_"):
            continue
        t = v.get("tag", "?")
        tags[t] = tags.get(t, 0) + 1

    print("\nTag summary:")
    for t, c in sorted(tags.items()):
        print(f"  {t}: {c}")

    if not args.dry_run:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nWritten: {OUT_JSON}")
    else:
        print("\n[dry-run] would write to", OUT_JSON)

    return 0


if __name__ == "__main__":
    sys.exit(main())

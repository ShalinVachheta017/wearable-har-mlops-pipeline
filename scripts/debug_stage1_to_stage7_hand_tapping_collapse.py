#!/usr/bin/env python
"""Audit stages 1-7 for single-class HAR prediction collapse.

This script is read-only. It inspects current pipeline artifacts, runs model
inference if TensorFlow is available, and writes machine-readable debug reports.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SENSOR_COLS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
ALT_SENSOR_COLS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
DEFAULT_CLASS_MAP = {
    0: "ear_rubbing",
    1: "forehead_rubbing",
    2: "hair_pulling",
    3: "hand_scratching",
    4: "hand_tapping",
    5: "knuckles_cracking",
    6: "nail_biting",
    7: "nape_rubbing",
    8: "sitting",
    9: "smoking",
    10: "standing",
}


def rel(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def exists_info(path: Path) -> Dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
    }


def load_class_map() -> Dict[int, str]:
    try:
        from src.utils.label_mapping import get_activity_classes

        loaded = get_activity_classes()
        return {int(k): str(v) for k, v in loaded.items()}
    except Exception:
        return DEFAULT_CLASS_MAP.copy()


def choose_sensor_columns(columns: Iterable[str]) -> List[str]:
    cols = list(columns)
    if all(c in cols for c in SENSOR_COLS):
        return SENSOR_COLS
    if all(c in cols for c in ALT_SENSOR_COLS):
        return ALT_SENSOR_COLS
    found = [c for c in SENSOR_COLS + ALT_SENSOR_COLS if c in cols]
    return found


def numeric_stats(df: pd.DataFrame, columns: List[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for col in columns:
        values = pd.to_numeric(df[col], errors="coerce")
        out[col] = {
            "count": int(values.notna().sum()),
            "missing": int(values.isna().sum()),
            "mean": finite_float(values.mean()),
            "std": finite_float(values.std()),
            "min": finite_float(values.min()),
            "max": finite_float(values.max()),
            "zero_fraction": finite_float((values == 0).mean()),
            "constant": bool(values.nunique(dropna=True) <= 1),
        }
    return out


def array_channel_stats(x: np.ndarray) -> Dict[str, Dict[str, Any]]:
    if x.ndim != 3 or x.shape[-1] != 6:
        return {"error": {"message": f"expected (N,T,6), got {x.shape}"}}
    flat = x.reshape(-1, x.shape[-1])
    out: Dict[str, Dict[str, Any]] = {}
    for i, col in enumerate(SENSOR_COLS):
        values = flat[:, i]
        finite = values[np.isfinite(values)]
        out[col] = {
            "mean": finite_float(np.mean(finite)) if finite.size else None,
            "std": finite_float(np.std(finite)) if finite.size else None,
            "min": finite_float(np.min(finite)) if finite.size else None,
            "max": finite_float(np.max(finite)) if finite.size else None,
            "nan_count": int(np.isnan(values).sum()),
            "inf_count": int(np.isinf(values).sum()),
            "zero_fraction": finite_float(np.mean(values == 0)),
            "constant": bool(finite.size > 0 and np.nanstd(values) < 1e-8),
        }
    return out


def finite_float(value: Any) -> Optional[float]:
    try:
        f = float(value)
    except Exception:
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def timestamp_report(df: pd.DataFrame) -> Dict[str, Any]:
    candidates = ["timestamp", "true_time", "timestamp_iso", "datetime", "time"]
    ts_col = next((c for c in candidates if c in df.columns), None)
    if ts_col is None:
        return {"timestamp_column": None, "warning": "no timestamp-like column found"}

    ts = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
    bad = int(ts.isna().sum())
    ts = ts.dropna().sort_values()
    if len(ts) < 2:
        return {"timestamp_column": ts_col, "bad_timestamps": bad, "warning": "not enough timestamps"}

    gaps_ms = ts.diff().dropna().dt.total_seconds().to_numpy() * 1000.0
    med = float(np.median(gaps_ms)) if gaps_ms.size else 0.0
    est_hz = 1000.0 / med if med > 0 else 0.0
    return {
        "timestamp_column": ts_col,
        "bad_timestamps": bad,
        "duplicate_timestamps": int(ts.duplicated().sum()),
        "gap_ms": {
            "mean": finite_float(np.mean(gaps_ms)),
            "median": finite_float(med),
            "min": finite_float(np.min(gaps_ms)),
            "max": finite_float(np.max(gaps_ms)),
            "p95": finite_float(np.percentile(gaps_ms, 95)),
            "p99": finite_float(np.percentile(gaps_ms, 99)),
        },
        "estimated_hz_from_median_gap": finite_float(est_hz),
        "large_gap_count_gt_40ms": int(np.sum(gaps_ms > 40.0)),
        "off_50hz_by_gt_10pct": bool(abs(est_hz - 50.0) / 50.0 > 0.10) if est_hz else True,
    }


def load_scaler(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"path": rel(path), "exists": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"path": rel(path), "exists": True, "error": str(exc)}
    return {
        "path": rel(path),
        "exists": True,
        "fit_users": payload.get("fit_users"),
        "sensor_cols": payload.get("sensor_cols"),
        "normalization_variant": payload.get("normalization_variant"),
        "mean": payload.get("scaler_mean"),
        "scale": payload.get("scaler_scale"),
    }


def entropy_from_probs(probs: np.ndarray) -> np.ndarray:
    p = np.clip(probs.astype(np.float64), 1e-12, 1.0)
    return -np.sum(p * np.log(p), axis=1)


def run_model(model_path: Path, x: np.ndarray, class_map: Dict[int, str], batch_size: int) -> Dict[str, Any]:
    if not model_path.exists():
        return {"loaded": False, "error": f"model not found: {rel(model_path)}"}
    try:
        import tensorflow as tf
    except Exception as exc:
        return {"loaded": False, "error": f"TensorFlow import failed: {exc}"}

    model = tf.keras.models.load_model(str(model_path), compile=False)
    probs = model.predict(x, batch_size=batch_size, verbose=0)
    preds = probs.argmax(axis=1)
    conf = probs.max(axis=1)
    ent = entropy_from_probs(probs)

    counts = Counter(int(p) for p in preds)
    total = int(len(preds))
    distribution = {}
    for idx, count in sorted(counts.items()):
        label = class_map.get(idx, f"class_{idx}")
        distribution[label] = {
            "class_index": idx,
            "count": int(count),
            "percentage": float(100.0 * count / max(total, 1)),
        }
    dominant_idx, dominant_count = counts.most_common(1)[0] if counts else (-1, 0)
    dominant_label = class_map.get(dominant_idx, f"class_{dominant_idx}")

    top3_rows = []
    for i in range(min(20, len(probs))):
        top = np.argsort(probs[i])[-3:][::-1]
        row = {"window_id": i}
        for rank, idx in enumerate(top, start=1):
            row[f"top{rank}_class_index"] = int(idx)
            row[f"top{rank}_label"] = class_map.get(int(idx), f"class_{idx}")
            row[f"top{rank}_probability"] = float(probs[i, idx])
        top3_rows.append(row)

    return {
        "loaded": True,
        "model_path": rel(model_path),
        "input_shape": str(getattr(model, "input_shape", None)),
        "output_shape": str(getattr(model, "output_shape", None)),
        "probability_shape": list(probs.shape),
        "prediction_distribution": distribution,
        "dominant_class": dominant_label,
        "dominant_class_index": int(dominant_idx),
        "dominant_percentage": float(100.0 * dominant_count / max(total, 1)),
        "mean_confidence": finite_float(np.mean(conf)),
        "confidence": {
            "std": finite_float(np.std(conf)),
            "min": finite_float(np.min(conf)),
            "max": finite_float(np.max(conf)),
        },
        "entropy": {
            "mean": finite_float(np.mean(ent)),
            "std": finite_float(np.std(ent)),
            "min": finite_float(np.min(ent)),
            "max": finite_float(np.max(ent)),
        },
        "top3_first20": top3_rows,
        "warnings": {
            "one_class_gt_70pct": bool(100.0 * dominant_count / max(total, 1) > 70.0),
            "one_class_gt_90pct": bool(100.0 * dominant_count / max(total, 1) > 90.0),
            "one_class_gt_95pct": bool(100.0 * dominant_count / max(total, 1) > 95.0),
        },
    }


def infer_x_space(stats: Dict[str, Dict[str, Any]]) -> str:
    means = [abs(v.get("mean") or 0.0) for v in stats.values() if isinstance(v, dict)]
    stds = [v.get("std") or 0.0 for v in stats.values() if isinstance(v, dict)]
    if not means or not stds:
        return "unknown"
    mean_abs = float(np.mean(means))
    std_avg = float(np.mean(stds))
    if mean_abs < 0.75 and 0.4 <= std_avg <= 1.8:
        return "probably_zscore_scaled"
    if std_avg > 2.0 or mean_abs > 1.0:
        return "probably_raw_or_unit_converted"
    return "ambiguous"


def labeled_metrics(y: np.ndarray, preds: np.ndarray, class_map: Dict[int, str]) -> Dict[str, Any]:
    if len(y) != len(preds):
        return {
            "available": False,
            "reason": f"length mismatch: y={len(y)} predictions={len(preds)}",
        }
    accuracy = float(np.mean(preds == y))
    rows = {}
    for idx, label in class_map.items():
        mask = y == idx
        if not np.any(mask):
            continue
        rows[label] = {
            "support": int(np.sum(mask)),
            "recall": float(np.mean(preds[mask] == idx)),
        }
    return {
        "available": True,
        "accuracy": accuracy,
        "per_class_recall": rows,
    }


def build_findings(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    x_shape = report.get("production_X", {}).get("shape")
    y_shape = report.get("production_y", {}).get("shape")
    if x_shape and (len(x_shape) != 3 or x_shape[1:] != [200, 6]):
        findings.append({
            "severity": "critical",
            "finding": f"production_X shape is {x_shape}, expected (N,200,6)",
            "why_it_matters": "The model expects 200-sample windows with six IMU channels.",
            "fix_or_test": "Fail Stage 3 or Stage 4 when shape is not exactly (N,200,6).",
            "fix_now": True,
        })
    if x_shape and y_shape and x_shape[0] != y_shape[0]:
        findings.append({
            "severity": "critical",
            "finding": f"production_X windows ({x_shape[0]}) and production_y labels ({y_shape[0]}) differ",
            "why_it_matters": "Evaluation accuracy is meaningless if labels and windows are not paired.",
            "fix_or_test": "Add a Stage 5 assertion before labeled metrics.",
            "fix_now": True,
        })

    ts = report.get("ingestion_csv", {}).get("timestamp", {})
    if ts.get("off_50hz_by_gt_10pct"):
        findings.append({
            "severity": "high",
            "finding": "Detected sampling frequency is not within 10 percent of 50 Hz",
            "why_it_matters": "Window duration and model temporal filters assume 50 Hz.",
            "fix_or_test": "Make Stage 2 sampling-frequency deviation an error, not only a warning.",
            "fix_now": True,
        })

    x_space = report.get("production_X", {}).get("inferred_feature_space")
    if x_space == "probably_raw_or_unit_converted":
        findings.append({
            "severity": "high",
            "finding": "production_X appears unnormalized/raw",
            "why_it_matters": "The default inference loader documents that input should already be normalized.",
            "fix_or_test": "Compare model accuracy/distribution with and without the canonical scaler on paired labels.",
            "fix_now": True,
        })

    infer = report.get("inference", {})
    dom = infer.get("dominant_percentage")
    if dom is not None and dom >= 70.0:
        findings.append({
            "severity": "critical" if dom >= 95.0 else "high",
            "finding": f"Prediction collapse: {infer.get('dominant_class')} at {dom:.1f} percent",
            "why_it_matters": "Single-class dominance can hide a bad model/input-space mismatch under high confidence.",
            "fix_or_test": "Keep trigger action at REVIEW and block automatic retraining from these pseudo-labels.",
            "fix_now": True,
        })
    elif dom is not None and dom >= 50.0:
        findings.append({
            "severity": "medium",
            "finding": f"Dominant-class warning: {infer.get('dominant_class')} at {dom:.1f} percent",
            "why_it_matters": "This is below the hard collapse guard but still shows strong class bias.",
            "fix_or_test": "Compare the same X through the raw-vs-scaled diagnostic before changing retraining.",
            "fix_now": True,
        })

    metrics = infer.get("labeled_metrics", {})
    if metrics.get("available") and metrics.get("accuracy", 1.0) < 0.30:
        findings.append({
            "severity": "high",
            "finding": f"Labeled accuracy is very low: {metrics.get('accuracy'):.4f}",
            "why_it_matters": "With paired labels present, this points to model/checkpoint/input-space parity, not trigger logic.",
            "fix_or_test": "Run one controlled matrix: raw X, canonical scaled X, and the model's original scaler if available.",
            "fix_now": True,
        })

    if not findings:
        findings.append({
            "severity": "low",
            "finding": "No structural stage 1-7 artifact failure detected by this script",
            "why_it_matters": "If collapse persists, the likely cause is checkpoint/scaler provenance or real distribution shift.",
            "fix_or_test": "Run paired labeled evaluation against users 1-4/5/6 before retraining.",
            "fix_now": False,
        })
    return findings


def final_suspected_root_cause(report: Dict[str, Any], findings: List[Dict[str, Any]]) -> str:
    if any("differ" in f["finding"] for f in findings):
        return "Current evaluation labels are not paired with production_X; fix artifact pairing first."
    infer = report.get("inference", {})
    dom = infer.get("dominant_percentage")
    mean_conf = infer.get("mean_confidence")
    x_space = report.get("production_X", {}).get("inferred_feature_space")
    if dom is not None and dom >= 50.0 and mean_conf is not None and mean_conf >= 0.70:
        return (
            "High-confidence dominant-class behavior with structurally valid X points to "
            "model/scaler/class-provenance mismatch before retraining."
        )
    if x_space == "probably_raw_or_unit_converted":
        return "production_X feature space may not match the documented normalized inference contract."
    return "No single root cause proven; inspect checkpoint provenance and train/serve scaler parity next."


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fused-csv", type=Path, default=ROOT / "data/processed/sensor_fused_50Hz.csv")
    parser.add_argument("--production-x", type=Path, default=ROOT / "data/prepared/production_X.npy")
    parser.add_argument("--production-y", type=Path, default=ROOT / "data/prepared/production_y.npy")
    parser.add_argument("--model", type=Path, default=ROOT / "models/pretrained/fine_tuned_model_1dcnnbilstm.keras")
    parser.add_argument("--scaler", type=Path, default=ROOT / "data/prepared/scaler_train_only.json")
    parser.add_argument("--baseline", type=Path, default=ROOT / "models/normalized_baseline.json")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "reports/debug_stage1_to_stage7")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--skip-model", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    class_map = load_class_map()

    report: Dict[str, Any] = {
        "repository_root": str(ROOT),
        "input_files": {
            "fused_csv": exists_info(args.fused_csv),
            "production_x": exists_info(args.production_x),
            "production_y": exists_info(args.production_y),
            "model": exists_info(args.model),
            "scaler": exists_info(args.scaler),
            "baseline": exists_info(args.baseline),
        },
        "class_mapping": class_map,
        "scaler": load_scaler(args.scaler),
    }

    if args.fused_csv.exists():
        df = pd.read_csv(args.fused_csv)
        cols = choose_sensor_columns(df.columns)
        report["ingestion_csv"] = {
            "path": rel(args.fused_csv),
            "shape": list(df.shape),
            "columns": list(df.columns),
            "detected_sensor_columns": cols,
            "timestamp": timestamp_report(df),
            "channel_stats_before_transformation": numeric_stats(df, cols) if cols else {},
        }
    else:
        report["ingestion_csv"] = {"error": "fused CSV not found"}

    x = None
    if args.production_x.exists():
        x = np.load(args.production_x)
        x_stats = array_channel_stats(x)
        report["production_X"] = {
            "path": rel(args.production_x),
            "shape": list(x.shape),
            "dtype": str(x.dtype),
            "channel_stats_after_transformation": x_stats,
            "inferred_feature_space": infer_x_space(x_stats),
        }
    else:
        report["production_X"] = {"error": "production_X not found"}

    y = None
    if args.production_y.exists():
        y = np.load(args.production_y)
        report["production_y"] = {
            "path": rel(args.production_y),
            "shape": list(y.shape),
            "dtype": str(y.dtype),
            "label_distribution": {
                class_map.get(int(k), f"class_{int(k)}"): int(v)
                for k, v in zip(*np.unique(y, return_counts=True))
            },
        }
    else:
        report["production_y"] = {"exists": False}

    if x is not None and not args.skip_model:
        report["inference"] = run_model(args.model, x, class_map, args.batch_size)
        if report["inference"].get("loaded") and y is not None:
            # Recreate predictions from the persisted distribution output would lose
            # ordering, so run argmax from top-level probabilities is intentionally
            # avoided here. Instead, reload model output only once in run_model would
            # require storing all probabilities, which is too large for JSON.
            try:
                import tensorflow as tf

                model = tf.keras.models.load_model(str(args.model), compile=False)
                probs_for_metrics = model.predict(x, batch_size=args.batch_size, verbose=0)
                preds_for_metrics = probs_for_metrics.argmax(axis=1)
                report["inference"]["labeled_metrics"] = labeled_metrics(
                    y, preds_for_metrics, class_map
                )
            except Exception as exc:
                report["inference"]["labeled_metrics"] = {
                    "available": False,
                    "reason": str(exc),
                }
    elif args.skip_model:
        report["inference"] = {"skipped": True}
    else:
        report["inference"] = {"skipped": True, "reason": "production_X missing"}

    findings = build_findings(report)
    report["findings"] = findings
    report["final_suspected_root_cause"] = final_suspected_root_cause(report, findings)

    json_path = args.out_dir / "hand_tapping_collapse_debug_report.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_csv(args.out_dir / "prediction_top3_first20.csv", report.get("inference", {}).get("top3_first20", []))
    write_csv(args.out_dir / "findings.csv", findings)

    print("Stage 1-7 hand_tapping collapse diagnostic")
    print(f"Report JSON: {json_path}")
    print(f"Findings CSV: {args.out_dir / 'findings.csv'}")
    if "shape" in report.get("production_X", {}):
        print(f"production_X shape: {tuple(report['production_X']['shape'])}")
        print(f"production_X feature space: {report['production_X']['inferred_feature_space']}")
    if "shape" in report.get("production_y", {}):
        print(f"production_y shape: {tuple(report['production_y']['shape'])}")
    infer = report.get("inference", {})
    if infer.get("loaded"):
        print(
            "dominant prediction: "
            f"{infer.get('dominant_class')} at {infer.get('dominant_percentage'):.1f}%"
        )
        print(f"mean confidence: {infer.get('mean_confidence'):.4f}")
    print("final suspected root cause:", report["final_suspected_root_cause"])
    print("top findings:")
    for finding in findings[:5]:
        print(f"- [{finding['severity']}] {finding['finding']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

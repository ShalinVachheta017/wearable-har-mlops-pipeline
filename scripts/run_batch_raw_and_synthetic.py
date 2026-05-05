#!/usr/bin/env python3
"""
Batch rerun for 26 raw sessions + 2 synthetic datasets.

What this script does:
1) Discovers all paired raw accelerometer/gyroscope sessions in data/raw.
2) Adds synthetic CSV datasets (default: synthetic_codex_input.csv, synthetic_other_input.csv).
3) Runs pipeline stages 1-7 for each dataset via run_pipeline.py.
4) Extracts confidence, activity distribution, drift, monitoring, trigger, and
   (if labeled) evaluation metrics such as accuracy.
5) Saves one consolidated metrics file (CSV + JSON).
6) Creates simple matplotlib charts for quick review.
7) Optionally trains on synthetic datasets and appends training metrics.

Usage examples:
  python scripts/run_batch_raw_and_synthetic.py
  python scripts/run_batch_raw_and_synthetic.py --resume
  python scripts/run_batch_raw_and_synthetic.py --max-runs 3
  python scripts/run_batch_raw_and_synthetic.py --train-synthetic --train-epochs 30
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib
import pandas as pd

# Use non-interactive backend for server/headless environments.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


DEFAULT_STAGES = [
    "ingestion",
    "validation",
    "transformation",
    "inference",
    "evaluation",
    "monitoring",
    "trigger",
]

DEFAULT_SYNTHETIC_FILES = [
    "synthetic_codex_input.csv",
    "synthetic_other_input.csv",
]

ACTIVITY_LABELS = [
    "ear_rubbing",
    "forehead_rubbing",
    "hair_pulling",
    "hand_scratching",
    "hand_tapping",
    "knuckles_cracking",
    "nail_biting",
    "nape_rubbing",
    "sitting",
    "smoking",
    "standing",
    "REVIEW",
]


@dataclass(frozen=True)
class DatasetSpec:
    dataset_id: str
    dataset_type: str  # raw | synthetic
    accel_file: Optional[Path] = None
    gyro_file: Optional[Path] = None
    input_csv: Optional[Path] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run 26 raw + 2 synthetic datasets through stages 1-7 and aggregate metrics."
    )

    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (default: auto-detected).",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw"),
        help="Raw data directory relative to repo root.",
    )
    parser.add_argument(
        "--synthetic-dir",
        type=Path,
        default=Path("data/synthetic_runs"),
        help="Synthetic data directory relative to repo root.",
    )
    parser.add_argument(
        "--synthetic-files",
        nargs="+",
        default=DEFAULT_SYNTHETIC_FILES,
        help=(
            "Synthetic CSV files to include (relative to synthetic-dir unless absolute). "
            "Default: synthetic_codex_input.csv synthetic_other_input.csv"
        ),
    )
    parser.add_argument(
        "--include-unlabeled-synthetic",
        action="store_true",
        help="Also include synthetic_codex_input_unlabeled.csv if present.",
    )

    parser.add_argument(
        "--skip-raw",
        action="store_true",
        help="Skip raw session reruns.",
    )
    parser.add_argument(
        "--skip-synthetic",
        action="store_true",
        help="Skip synthetic dataset reruns.",
    )

    parser.add_argument(
        "--model",
        type=Path,
        default=None,
        help="Optional model override passed to run_pipeline.py --model.",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Limit total datasets processed (for smoke tests).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing output CSV and skip already finished dataset keys.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned commands without executing pipeline or training.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Output directory (default: reports/pipeline_runs/batch_28_<timestamp>)."
        ),
    )

    parser.add_argument(
        "--train-synthetic",
        action="store_true",
        help="Also run src/train.py on each synthetic CSV and append training metrics.",
    )
    parser.add_argument(
        "--train-epochs",
        type=int,
        default=30,
        help="Epochs for optional synthetic training (default: 30).",
    )
    parser.add_argument(
        "--train-batch-size",
        type=int,
        default=64,
        help="Batch size for optional synthetic training (default: 64).",
    )
    parser.add_argument(
        "--train-with-cv",
        dest="train_skip_cv",
        action="store_false",
        help="Use CV for synthetic training (slower). Default behavior skips CV.",
    )
    parser.set_defaults(train_skip_cv=True)

    return parser.parse_args()


def session_id_from_accel_name(name: str) -> Optional[str]:
    suffixes = ["_accelerometer.csv", "-accelerometer_data.xlsx"]
    for suffix in suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return None


def expected_gyro_name_from_session(session_id: str, accel_name: str) -> Optional[str]:
    if accel_name.endswith("_accelerometer.csv"):
        return f"{session_id}_gyroscope.csv"
    if accel_name.endswith("-accelerometer_data.xlsx"):
        return f"{session_id}-gyroscope_data.xlsx"
    return None


def discover_raw_pairs(raw_dir: Path) -> List[DatasetSpec]:
    accel_files = sorted(list(raw_dir.glob("*_accelerometer.csv")) + list(raw_dir.glob("*-accelerometer_data.xlsx")))
    specs: List[DatasetSpec] = []

    for accel in accel_files:
        session_id = session_id_from_accel_name(accel.name)
        if not session_id:
            continue
        gyro_name = expected_gyro_name_from_session(session_id, accel.name)
        if not gyro_name:
            continue
        gyro = raw_dir / gyro_name
        if not gyro.exists():
            continue

        specs.append(
            DatasetSpec(
                dataset_id=session_id,
                dataset_type="raw",
                accel_file=accel,
                gyro_file=gyro,
            )
        )

    return sorted(specs, key=lambda x: x.dataset_id)


def resolve_synthetic_file(path_str: str, synthetic_dir: Path) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    return synthetic_dir / p


def build_synthetic_specs(synthetic_dir: Path, file_names: Iterable[str]) -> List[DatasetSpec]:
    specs: List[DatasetSpec] = []
    for entry in file_names:
        csv_path = resolve_synthetic_file(entry, synthetic_dir)
        if not csv_path.exists():
            print(f"[WARN] Synthetic file not found, skipping: {csv_path}")
            continue
        specs.append(
            DatasetSpec(
                dataset_id=csv_path.stem,
                dataset_type="synthetic",
                input_csv=csv_path,
            )
        )
    return sorted(specs, key=lambda x: x.dataset_id)


def safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def load_json_file(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def snapshot_pipeline_result_files(result_dir: Path) -> set[Path]:
    return set(result_dir.glob("pipeline_result_*.json"))


def locate_new_pipeline_result(
    before: set[Path],
    result_dir: Path,
    run_start_ts: float,
) -> Optional[Path]:
    after = snapshot_pipeline_result_files(result_dir)
    new_files = sorted(after - before, key=lambda p: p.stat().st_mtime)
    if new_files:
        return new_files[-1]

    # Fallback: if no set-diff match, pick file modified after command started.
    candidates = sorted(
        [p for p in after if p.stat().st_mtime >= run_start_ts - 1.0],
        key=lambda p: p.stat().st_mtime,
    )
    if candidates:
        return candidates[-1]
    return None


def resolve_model_training_metrics(
    active_model_path: Optional[str],
    cache: Dict[str, Dict],
) -> Dict:
    if not active_model_path:
        return {}

    key = active_model_path
    if key in cache:
        return cache[key]

    metrics: Dict[str, Optional[float]] = {}
    model_path = Path(active_model_path)

    report_path: Optional[Path] = None
    stem = model_path.stem
    if stem.startswith("har_model_"):
        ts = stem.replace("har_model_", "", 1)
        candidate = model_path.parent / f"training_report_{ts}.json"
        if candidate.exists():
            report_path = candidate

    if report_path is None and model_path.parent.exists():
        candidates = sorted(
            model_path.parent.glob("training_report_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            report_path = candidates[0]

    if report_path and report_path.exists():
        try:
            payload = load_json_file(report_path)
            src = payload.get("metrics", {})
            metrics = {
                "model_training_report_path": str(report_path),
                "model_train_final_accuracy": safe_float(src.get("final_accuracy")),
                "model_train_f1_macro": safe_float(src.get("f1_macro")),
                "model_train_f1_weighted": safe_float(src.get("f1_weighted")),
                "model_train_cohen_kappa": safe_float(src.get("cohen_kappa")),
            }
        except Exception:
            metrics = {}

    cache[key] = metrics
    return metrics


def extract_metrics_row(
    spec: DatasetSpec,
    return_code: int,
    duration_sec: float,
    command: List[str],
    result_json_path: Optional[Path],
    run_log_path: Path,
    artifacts_dir: Path,
    model_metrics_cache: Dict[str, Dict],
    dry_run: bool,
) -> Dict:
    row = {
        "dataset_id": spec.dataset_id,
        "dataset_type": spec.dataset_type,
        "source_accel": str(spec.accel_file) if spec.accel_file else None,
        "source_gyro": str(spec.gyro_file) if spec.gyro_file else None,
        "source_csv": str(spec.input_csv) if spec.input_csv else None,
        "command": subprocess.list2cmdline(command),
        "return_code": return_code,
        "duration_sec": round(duration_sec, 3),
        "dry_run": dry_run,
        "pipeline_result_json": str(result_json_path) if result_json_path else None,
        "pipeline_log": str(run_log_path),
        "run_id": None,
        "overall_status": None,
        "stages_completed": None,
        "stages_failed": None,
        "dataset_has_labels": None,
        "dataset_label_source": None,
        "active_model_path": None,
        "model_version": None,
        "n_predictions": None,
        "mean_confidence": None,
        "std_confidence": None,
        "min_confidence": None,
        "max_confidence": None,
        "n_uncertain": None,
        "uncertain_pct": None,
        "dominant_class": None,
        "dominant_count": None,
        "dominant_pct": None,
        "n_predicted_classes": None,
        "activity_distribution_json": None,
        "evaluation_has_labels": None,
        "eval_accuracy": None,
        "eval_precision_macro": None,
        "eval_recall_macro": None,
        "eval_f1_macro": None,
        "distribution_dominance_warning": None,
        "eval_dominant_class": None,
        "eval_dominant_pct": None,
        "monitoring_status": None,
        "layer1_status": None,
        "layer2_status": None,
        "layer3_status": None,
        "layer1_mean_confidence": None,
        "layer1_uncertain_pct": None,
        "layer1_mean_entropy": None,
        "transition_rate": None,
        "mean_dwell_time_seconds": None,
        "short_dwell_ratio": None,
        "longest_sequence_max": None,
        "max_drift": None,
        "n_drifted_channels": None,
        "trigger_should_retrain": None,
        "trigger_action": None,
        "trigger_alert": None,
        "trigger_cooldown_active": None,
        "trigger_reason": None,
        "artifact_run_dir": None,
        "model_training_report_path": None,
        "model_train_final_accuracy": None,
        "model_train_f1_macro": None,
        "model_train_f1_weighted": None,
        "model_train_cohen_kappa": None,
    }

    # Initialize predictable fields so CSV columns remain stable.
    for label in ACTIVITY_LABELS:
        row[f"activity_count_{label}"] = None
        row[f"activity_pct_{label}"] = None

    if dry_run or result_json_path is None or not result_json_path.exists():
        return row

    try:
        payload = load_json_file(result_json_path)
    except Exception as exc:
        row["parse_error"] = str(exc)
        return row

    run_id = payload.get("run_id")
    overall_status = payload.get("overall_status")

    inference = payload.get("inference") or {}
    conf = inference.get("confidence_stats") or {}
    activity_dist = inference.get("activity_distribution") or {}

    n_predictions = inference.get("n_predictions")
    mean_conf = safe_float(conf.get("mean"))
    n_uncertain = conf.get("n_uncertain")
    uncertain_pct = None
    if isinstance(n_predictions, int) and n_predictions > 0 and isinstance(n_uncertain, int):
        uncertain_pct = 100.0 * n_uncertain / n_predictions

    dominant_class = None
    dominant_count = None
    dominant_pct = None
    if activity_dist and isinstance(n_predictions, int) and n_predictions > 0:
        dominant_class = max(activity_dist, key=lambda k: activity_dist[k])
        dominant_count = activity_dist[dominant_class]
        dominant_pct = 100.0 * dominant_count / n_predictions

    monitoring = payload.get("monitoring") or {}
    l1 = monitoring.get("layer1_confidence") or {}
    l2 = monitoring.get("layer2_temporal") or {}
    l3 = monitoring.get("layer3_drift") or {}

    trigger = payload.get("trigger") or {}

    evaluation = payload.get("evaluation") or {}
    cls = evaluation.get("classification_metrics") or {}

    longest_sequences = l2.get("longest_sequences") or {}
    longest_seq_max = None
    if isinstance(longest_sequences, dict) and longest_sequences:
        numeric_vals = [v for v in longest_sequences.values() if isinstance(v, (int, float))]
        if numeric_vals:
            longest_seq_max = float(max(numeric_vals))

    row.update(
        {
            "run_id": run_id,
            "overall_status": overall_status,
            "stages_completed": len(payload.get("stages_completed") or []),
            "stages_failed": len(payload.get("stages_failed") or []),
            "dataset_has_labels": payload.get("dataset_has_labels"),
            "dataset_label_source": payload.get("dataset_label_source"),
            "active_model_path": inference.get("active_model_path"),
            "model_version": inference.get("model_version"),
            "n_predictions": n_predictions,
            "mean_confidence": mean_conf,
            "std_confidence": safe_float(conf.get("std")),
            "min_confidence": safe_float(conf.get("min")),
            "max_confidence": safe_float(conf.get("max")),
            "n_uncertain": n_uncertain,
            "uncertain_pct": uncertain_pct,
            "dominant_class": dominant_class,
            "dominant_count": dominant_count,
            "dominant_pct": dominant_pct,
            "n_predicted_classes": len(activity_dist) if isinstance(activity_dist, dict) else None,
            "activity_distribution_json": json.dumps(activity_dist),
            "evaluation_has_labels": evaluation.get("has_labels"),
            "eval_accuracy": safe_float(cls.get("accuracy")),
            "eval_precision_macro": safe_float(cls.get("precision_macro")),
            "eval_recall_macro": safe_float(cls.get("recall_macro")),
            "eval_f1_macro": safe_float(cls.get("f1_macro")),
            "distribution_dominance_warning": evaluation.get("distribution_dominance_warning"),
            "eval_dominant_class": evaluation.get("dominant_class"),
            "eval_dominant_pct": safe_float(evaluation.get("dominant_pct")),
            "monitoring_status": monitoring.get("overall_status"),
            "layer1_status": l1.get("status"),
            "layer2_status": l2.get("status"),
            "layer3_status": l3.get("status"),
            "layer1_mean_confidence": safe_float(l1.get("mean_confidence")),
            "layer1_uncertain_pct": safe_float(l1.get("uncertain_percentage")),
            "layer1_mean_entropy": safe_float(l1.get("mean_entropy")),
            "transition_rate": safe_float(l2.get("transition_rate")),
            "mean_dwell_time_seconds": safe_float(l2.get("mean_dwell_time_seconds")),
            "short_dwell_ratio": safe_float(l2.get("short_dwell_ratio")),
            "longest_sequence_max": longest_seq_max,
            "max_drift": safe_float(l3.get("max_drift")),
            "n_drifted_channels": l3.get("n_drifted_channels"),
            "trigger_should_retrain": trigger.get("should_retrain"),
            "trigger_action": trigger.get("action"),
            "trigger_alert": trigger.get("alert_level"),
            "trigger_cooldown_active": trigger.get("cooldown_active"),
            "trigger_reason": (trigger.get("reasons") or [None])[0],
            "artifact_run_dir": str(artifacts_dir / run_id) if run_id else None,
        }
    )

    if isinstance(activity_dist, dict) and isinstance(n_predictions, int) and n_predictions > 0:
        for label in ACTIVITY_LABELS:
            count = activity_dist.get(label)
            if count is None:
                continue
            row[f"activity_count_{label}"] = int(count)
            row[f"activity_pct_{label}"] = 100.0 * float(count) / float(n_predictions)

    row.update(resolve_model_training_metrics(inference.get("active_model_path"), model_metrics_cache))

    return row


def run_pipeline_for_dataset(
    spec: DatasetSpec,
    args: argparse.Namespace,
    repo_root: Path,
    result_dir: Path,
    artifacts_dir: Path,
    run_logs_dir: Path,
    model_metrics_cache: Dict[str, Dict],
) -> Dict:
    cmd = [sys.executable, "run_pipeline.py", "--stages", *DEFAULT_STAGES]

    if args.model:
        cmd += ["--model", str(args.model)]

    if spec.dataset_type == "raw":
        if not spec.accel_file or not spec.gyro_file:
            raise ValueError(f"Raw dataset missing accel/gyro files: {spec.dataset_id}")
        cmd += ["--accel-file", str(spec.accel_file), "--gyro-file", str(spec.gyro_file)]
    else:
        if not spec.input_csv:
            raise ValueError(f"Synthetic dataset missing CSV file: {spec.dataset_id}")
        cmd += ["--input-csv", str(spec.input_csv)]

    run_log_path = run_logs_dir / f"pipeline_{spec.dataset_type}_{spec.dataset_id}.log"

    if args.dry_run:
        return extract_metrics_row(
            spec=spec,
            return_code=0,
            duration_sec=0.0,
            command=cmd,
            result_json_path=None,
            run_log_path=run_log_path,
            artifacts_dir=artifacts_dir,
            model_metrics_cache=model_metrics_cache,
            dry_run=True,
        )

    before = snapshot_pipeline_result_files(result_dir)
    run_start_ts = time.time()

    with run_log_path.open("w", encoding="utf-8") as log_f:
        proc = subprocess.run(
            cmd,
            cwd=repo_root,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            text=True,
        )

    run_end_ts = time.time()
    result_json_path = locate_new_pipeline_result(before, result_dir, run_start_ts)

    return extract_metrics_row(
        spec=spec,
        return_code=proc.returncode,
        duration_sec=run_end_ts - run_start_ts,
        command=cmd,
        result_json_path=result_json_path,
        run_log_path=run_log_path,
        artifacts_dir=artifacts_dir,
        model_metrics_cache=model_metrics_cache,
        dry_run=False,
    )


def run_synthetic_training(
    synthetic_specs: List[DatasetSpec],
    args: argparse.Namespace,
    repo_root: Path,
    output_dir: Path,
) -> pd.DataFrame:
    rows: List[Dict] = []
    train_logs_dir = output_dir / "logs"
    train_logs_dir.mkdir(parents=True, exist_ok=True)

    train_out_root = output_dir / "synthetic_training"
    train_out_root.mkdir(parents=True, exist_ok=True)

    for idx, spec in enumerate(synthetic_specs, start=1):
        assert spec.input_csv is not None
        print(
            f"[train {idx}/{len(synthetic_specs)}] "
            f"{spec.dataset_id} -> synthetic training"
        )

        per_dataset_out = train_out_root / spec.dataset_id
        per_dataset_out.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            "src/train.py",
            "--data",
            str(spec.input_csv),
            "--epochs",
            str(args.train_epochs),
            "--batch-size",
            str(args.train_batch_size),
            "--output-dir",
            str(per_dataset_out),
            "--experiment-name",
            "synthetic-batch-training",
        ]
        if args.train_skip_cv:
            cmd.append("--skip-cv")

        log_path = train_logs_dir / f"train_{spec.dataset_id}.log"
        start_ts = time.time()

        if args.dry_run:
            rows.append(
                {
                    "dataset_id": spec.dataset_id,
                    "dataset_type": "synthetic",
                    "train_command": subprocess.list2cmdline(cmd),
                    "train_return_code": 0,
                    "train_duration_sec": 0.0,
                    "train_report_path": None,
                }
            )
            continue

        before = set(per_dataset_out.glob("training_report_*.json"))
        with log_path.open("w", encoding="utf-8") as log_f:
            proc = subprocess.run(
                cmd,
                cwd=repo_root,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                text=True,
            )
        duration = time.time() - start_ts

        after = sorted(per_dataset_out.glob("training_report_*.json"), key=lambda p: p.stat().st_mtime)
        new_reports = sorted(set(after) - before, key=lambda p: p.stat().st_mtime)
        report_path = new_reports[-1] if new_reports else (after[-1] if after else None)

        metrics = {}
        if report_path and report_path.exists():
            try:
                payload = load_json_file(report_path)
                src = payload.get("metrics", {})
                metrics = {
                    "synthetic_train_final_accuracy": safe_float(src.get("final_accuracy")),
                    "synthetic_train_f1_macro": safe_float(src.get("f1_macro")),
                    "synthetic_train_f1_weighted": safe_float(src.get("f1_weighted")),
                    "synthetic_train_cohen_kappa": safe_float(src.get("cohen_kappa")),
                    "synthetic_train_best_epoch": safe_float(src.get("best_epoch")),
                }
            except Exception:
                metrics = {}

        rows.append(
            {
                "dataset_id": spec.dataset_id,
                "dataset_type": "synthetic",
                "train_command": subprocess.list2cmdline(cmd),
                "train_return_code": proc.returncode,
                "train_duration_sec": round(duration, 3),
                "train_report_path": str(report_path) if report_path else None,
                "train_log": str(log_path),
                **metrics,
            }
        )

    return pd.DataFrame(rows)


def save_outputs(df: pd.DataFrame, output_dir: Path) -> Tuple[Path, Path]:
    csv_path = output_dir / "all_runs_metrics.csv"
    json_path = output_dir / "all_runs_metrics.json"

    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)

    return csv_path, json_path


def make_charts(df: pd.DataFrame, charts_dir: Path) -> List[Path]:
    charts_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []

    if df.empty:
        return outputs

    plot_df = df.copy()
    color_map = {"raw": "#1f77b4", "synthetic": "#ff7f0e"}

    # 1) Mean confidence by dataset.
    if "mean_confidence" not in plot_df.columns:
        return outputs

    cdf = plot_df.dropna(subset=["mean_confidence"]).sort_values("mean_confidence")
    if not cdf.empty:
        colors = cdf["dataset_type"].map(color_map).fillna("#7f7f7f")
        fig, ax = plt.subplots(figsize=(12, max(6, 0.32 * len(cdf))))
        ax.barh(cdf["dataset_id"], cdf["mean_confidence"], color=colors)
        ax.set_xlabel("Mean confidence")
        ax.set_ylabel("Dataset")
        ax.set_title("Mean Confidence per Dataset")
        ax.grid(axis="x", alpha=0.25)
        fig.tight_layout()
        out = charts_dir / "mean_confidence_by_dataset.png"
        fig.savefig(out, dpi=160)
        plt.close(fig)
        outputs.append(out)

    # 2) Drift vs uncertain percentage.
    if "max_drift" in plot_df.columns and "uncertain_pct" in plot_df.columns:
        ddf = plot_df.dropna(subset=["max_drift", "uncertain_pct"])
    else:
        ddf = pd.DataFrame()
    if not ddf.empty:
        fig, ax = plt.subplots(figsize=(8, 6))
        for dtype, group in ddf.groupby("dataset_type"):
            ax.scatter(
                group["max_drift"],
                group["uncertain_pct"],
                label=dtype,
                alpha=0.8,
                s=45,
                color=color_map.get(dtype, "#7f7f7f"),
            )
        ax.set_xlabel("Max drift (Layer 3 z-score)")
        ax.set_ylabel("Uncertain percentage")
        ax.set_title("Drift vs Uncertainty")
        ax.grid(alpha=0.25)
        ax.legend()
        fig.tight_layout()
        out = charts_dir / "drift_vs_uncertain_scatter.png"
        fig.savefig(out, dpi=160)
        plt.close(fig)
        outputs.append(out)

    # 3) Dominant class percentage by dataset.
    if "dominant_pct" in plot_df.columns:
        pcf = plot_df.dropna(subset=["dominant_pct"]).sort_values("dominant_pct", ascending=False)
    else:
        pcf = pd.DataFrame()
    if not pcf.empty:
        colors = pcf["dataset_type"].map(color_map).fillna("#7f7f7f")
        fig, ax = plt.subplots(figsize=(12, max(6, 0.32 * len(pcf))))
        ax.barh(pcf["dataset_id"], pcf["dominant_pct"], color=colors)
        ax.invert_yaxis()
        ax.set_xlabel("Dominant class share (%)")
        ax.set_ylabel("Dataset")
        ax.set_title("Dominant Activity Share per Dataset")
        ax.grid(axis="x", alpha=0.25)
        fig.tight_layout()
        out = charts_dir / "dominant_pct_by_dataset.png"
        fig.savefig(out, dpi=160)
        plt.close(fig)
        outputs.append(out)

    # 4) Synthetic labeled evaluation accuracy.
    if "eval_accuracy" in plot_df.columns:
        sdf = plot_df[(plot_df["dataset_type"] == "synthetic") & (plot_df["eval_accuracy"].notna())]
    else:
        sdf = pd.DataFrame()
    if not sdf.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(sdf["dataset_id"], sdf["eval_accuracy"], color="#ff7f0e")
        ax.set_ylim(0.0, 1.0)
        ax.set_ylabel("Evaluation accuracy")
        ax.set_title("Synthetic Dataset Accuracy (Stage 5)")
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        out = charts_dir / "synthetic_eval_accuracy.png"
        fig.savefig(out, dpi=160)
        plt.close(fig)
        outputs.append(out)

    # 5) Optional synthetic training accuracy chart.
    if "synthetic_train_final_accuracy" in plot_df.columns:
        tdf = plot_df[
            (plot_df["dataset_type"] == "synthetic")
            & (plot_df["synthetic_train_final_accuracy"].notna())
        ]
        if not tdf.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(tdf["dataset_id"], tdf["synthetic_train_final_accuracy"], color="#2ca02c")
            ax.set_ylim(0.0, 1.0)
            ax.set_ylabel("Training final accuracy")
            ax.set_title("Synthetic Training Final Accuracy")
            ax.grid(axis="y", alpha=0.25)
            fig.tight_layout()
            out = charts_dir / "synthetic_training_accuracy.png"
            fig.savefig(out, dpi=160)
            plt.close(fig)
            outputs.append(out)

    return outputs


def write_summary_markdown(
    df: pd.DataFrame,
    output_dir: Path,
    csv_path: Path,
    json_path: Path,
    chart_paths: List[Path],
    planned_count: int,
) -> Path:
    summary_path = output_dir / "SUMMARY.md"

    success_df = df[df["overall_status"] == "SUCCESS"] if "overall_status" in df else pd.DataFrame()
    failed_mask = pd.Series(False, index=df.index)
    if "return_code" in df.columns:
        failed_mask = failed_mask | (df["return_code"] != 0)
    if "overall_status" in df.columns:
        failed_mask = failed_mask | (df["overall_status"] == "FAILED")
    failed_df = df[failed_mask]

    grouped = pd.DataFrame()
    if not success_df.empty:
        grouped = (
            success_df.groupby("dataset_type")
            .agg(
                runs=("dataset_id", "count"),
                mean_confidence=("mean_confidence", "mean"),
                mean_uncertain_pct=("uncertain_pct", "mean"),
                mean_max_drift=("max_drift", "mean"),
                mean_dominant_pct=("dominant_pct", "mean"),
                mean_n_predicted_classes=("n_predicted_classes", "mean"),
            )
            .reset_index()
        )

    def _as_table_text(table_df: pd.DataFrame) -> str:
        """Return a plain-text table without requiring optional dependencies."""
        if table_df.empty:
            return "(no rows)"
        return table_df.to_string(index=False)

    lines = []
    lines.append("# Batch 28 Run Summary")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Scope")
    lines.append(f"- Planned datasets: {planned_count}")
    lines.append(f"- Rows in consolidated file: {len(df)}")
    lines.append(f"- Success rows: {len(success_df)}")
    lines.append(f"- Failed rows: {len(failed_df)}")
    lines.append("")
    lines.append("## Output Files")
    lines.append(f"- CSV: {csv_path}")
    lines.append(f"- JSON: {json_path}")
    lines.append(f"- Charts directory: {output_dir / 'charts'}")
    lines.append("")

    if chart_paths:
        lines.append("## Chart Files")
        for chart in chart_paths:
            lines.append(f"- {chart}")
        lines.append("")

    if not grouped.empty:
        lines.append("## Aggregates by Dataset Type")
        lines.append("")
        lines.append("```")
        lines.append(_as_table_text(grouped))
        lines.append("```")
        lines.append("")

    if "dataset_type" in df.columns:
        synthetic_eval = df[(df["dataset_type"] == "synthetic") & (df["eval_accuracy"].notna())]
        if not synthetic_eval.empty:
            lines.append("## Synthetic Evaluation Metrics")
            lines.append("")
            cols = [
                "dataset_id",
                "eval_accuracy",
                "eval_precision_macro",
                "eval_recall_macro",
                "eval_f1_macro",
            ]
            lines.append("```")
            lines.append(_as_table_text(synthetic_eval[cols]))
            lines.append("```")
            lines.append("")

    if not failed_df.empty:
        lines.append("## Failed Runs")
        lines.append("")
        fail_cols = ["dataset_id", "dataset_type", "return_code", "pipeline_log", "pipeline_result_json"]
        avail = [c for c in fail_cols if c in failed_df.columns]
        lines.append("```")
        lines.append(_as_table_text(failed_df[avail]))
        lines.append("```")
        lines.append("")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


def ensure_output_dir(repo_root: Path, requested_output_dir: Optional[Path]) -> Path:
    if requested_output_dir is not None:
        output_dir = requested_output_dir
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = repo_root / "reports" / "pipeline_runs" / f"batch_28_{ts}"

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "logs").mkdir(parents=True, exist_ok=True)
    (output_dir / "charts").mkdir(parents=True, exist_ok=True)
    return output_dir


def main() -> int:
    args = parse_args()

    repo_root = args.repo_root.resolve()
    raw_dir = (repo_root / args.raw_dir).resolve()
    synthetic_dir = (repo_root / args.synthetic_dir).resolve()

    if not repo_root.exists():
        raise FileNotFoundError(f"Repo root does not exist: {repo_root}")

    output_dir = ensure_output_dir(repo_root, args.output_dir)
    result_dir = repo_root / "logs" / "pipeline"
    artifacts_dir = repo_root / "artifacts"
    run_logs_dir = output_dir / "logs"

    synthetic_files = list(args.synthetic_files)
    if args.include_unlabeled_synthetic and "synthetic_codex_input_unlabeled.csv" not in synthetic_files:
        synthetic_files.append("synthetic_codex_input_unlabeled.csv")

    raw_specs = [] if args.skip_raw else discover_raw_pairs(raw_dir)
    synthetic_specs = [] if args.skip_synthetic else build_synthetic_specs(synthetic_dir, synthetic_files)

    all_specs: List[DatasetSpec] = raw_specs + synthetic_specs
    all_specs = sorted(all_specs, key=lambda s: (0 if s.dataset_type == "raw" else 1, s.dataset_id))

    if args.max_runs is not None:
        all_specs = all_specs[: args.max_runs]

    if not all_specs:
        print("No datasets selected. Nothing to do.")
        return 1

    print("=" * 80)
    print("BATCH RUN: RAW + SYNTHETIC")
    print("=" * 80)
    print(f"Repo root:              {repo_root}")
    print(f"Raw sessions discovered: {len(raw_specs)}")
    print(f"Synthetic discovered:    {len(synthetic_specs)}")
    print(f"Planned runs:            {len(all_specs)}")
    print(f"Output directory:        {output_dir}")
    print(f"Dry run:                 {args.dry_run}")
    print("=" * 80)

    live_csv = output_dir / "all_runs_metrics_live.csv"
    rows: List[Dict] = []

    if args.resume and live_csv.exists():
        existing = pd.read_csv(live_csv)
        rows = existing.to_dict(orient="records")
        done = {(str(r.get("dataset_id")), str(r.get("dataset_type"))) for r in rows}
        before_count = len(all_specs)
        all_specs = [s for s in all_specs if (s.dataset_id, s.dataset_type) not in done]
        print(f"Resume mode: skipped {before_count - len(all_specs)} already recorded runs.")

    model_metrics_cache: Dict[str, Dict] = {}

    total = len(all_specs)
    for idx, spec in enumerate(all_specs, start=1):
        print(f"[{idx}/{total}] Running {spec.dataset_id} ({spec.dataset_type})")
        row = run_pipeline_for_dataset(
            spec=spec,
            args=args,
            repo_root=repo_root,
            result_dir=result_dir,
            artifacts_dir=artifacts_dir,
            run_logs_dir=run_logs_dir,
            model_metrics_cache=model_metrics_cache,
        )
        rows.append(row)

        # Persist after every run so resume is always safe.
        pd.DataFrame(rows).to_csv(live_csv, index=False)

        status = row.get("overall_status") or "NO_RESULT"
        mean_conf = row.get("mean_confidence")
        drift = row.get("max_drift")
        print(
            f"    -> return_code={row.get('return_code')} status={status} "
            f"mean_conf={mean_conf} max_drift={drift}"
        )

    df = pd.DataFrame(rows)

    # Optional synthetic training pass.
    if args.train_synthetic and synthetic_specs:
        print("=" * 80)
        print("OPTIONAL STEP: SYNTHETIC TRAINING")
        print("=" * 80)
        train_df = run_synthetic_training(
            synthetic_specs=synthetic_specs,
            args=args,
            repo_root=repo_root,
            output_dir=output_dir,
        )
        if not train_df.empty:
            train_df.to_csv(output_dir / "synthetic_training_metrics.csv", index=False)
            df = df.merge(train_df, on=["dataset_id", "dataset_type"], how="left")

    csv_path, json_path = save_outputs(df, output_dir)
    chart_paths = make_charts(df, output_dir / "charts")
    summary_path = write_summary_markdown(
        df=df,
        output_dir=output_dir,
        csv_path=csv_path,
        json_path=json_path,
        chart_paths=chart_paths,
        planned_count=len(raw_specs) + len(synthetic_specs),
    )

    print("=" * 80)
    print("DONE")
    print("=" * 80)
    print(f"Consolidated CSV: {csv_path}")
    print(f"Consolidated JSON: {json_path}")
    print(f"Summary report: {summary_path}")
    print(f"Charts: {output_dir / 'charts'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

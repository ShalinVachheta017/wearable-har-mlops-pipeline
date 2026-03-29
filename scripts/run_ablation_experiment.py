"""
Run preprocessing ablation across production datasets.

Goal:
    Compare 4 preprocessing configs (A/B/C/D) across all sessions in data/raw
    to diagnose hand_tapping collapse.

Outputs:
    - outputs/ablation/ablation_results.csv
    - outputs/ablation/ablation_summary.csv

Notes:
    - Reuses existing pipeline components from src/:
      DataIngestion -> DataTransformation -> ModelInference
    - Does not reimplement preprocessing or inference logic.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components.data_ingestion import DataIngestion, discover_sensor_files
from src.components.data_transformation import DataTransformation
from src.components.model_inference import ModelInference
from src.entity.artifact_entity import DataIngestionArtifact
from src.entity.config_entity import (
    DataIngestionConfig,
    DataTransformationConfig,
    ModelInferenceConfig,
    PipelineConfig,
)


LOGGER = logging.getLogger("ablation")

# Training Az mean used by the deployed z-score scaler (m/s^2)
TRAINING_AZ_MEAN_MS2 = -3.5289


@dataclass(frozen=True)
class SessionSpec:
    """A single production session source."""

    session_id: str
    source_type: str  # "pair" or "csv"
    accel_path: Optional[Path] = None
    gyro_path: Optional[Path] = None
    csv_path: Optional[Path] = None


@dataclass(frozen=True)
class AblationConfig:
    """One preprocessing configuration under test."""

    config_id: str
    gravity_removal: bool
    calibration: bool
    description: str


ABLATION_CONFIGS: Sequence[AblationConfig] = (
    AblationConfig(
        config_id="A",
        gravity_removal=False,
        calibration=False,
        description="baseline: gravity_removal=False, calibration=False",
    ),
    AblationConfig(
        config_id="B",
        gravity_removal=False,
        calibration=True,
        description="calibration only: gravity_removal=False, calibration=True",
    ),
    AblationConfig(
        config_id="C",
        gravity_removal=True,
        calibration=False,
        description="gravity only: gravity_removal=True, calibration=False",
    ),
    AblationConfig(
        config_id="D",
        gravity_removal=True,
        calibration=True,
        description="both: gravity_removal=True, calibration=True",
    ),
)


def setup_logging(verbose: bool = False) -> None:
    """Configure console logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)-8s | %(message)s")


def _session_id_from_pair(accel_path: Path, gyro_path: Path) -> str:
    """Build a stable session id from accel/gyro file names."""
    accel_name = accel_path.name
    gyro_name = gyro_path.name
    prefix_a = accel_name.lower().split("accelerometer")[0].rstrip("_- ")
    prefix_g = gyro_name.lower().split("gyroscope")[0].rstrip("_- ")
    prefix = prefix_a if prefix_a == prefix_g else f"{prefix_a}__{prefix_g}"
    return prefix or accel_path.stem


def _looks_like_fused_csv(path: Path) -> bool:
    """Quick schema check for a fused production CSV."""
    try:
        df_head = pd.read_csv(path, nrows=5)
    except Exception:
        return False
    cols = set(df_head.columns)
    needed = {"Ax", "Ay", "Az", "Gx", "Gy", "Gz"}
    return needed.issubset(cols)


def discover_sessions(raw_dir: Path) -> List[SessionSpec]:
    """
    Discover production sessions under data/raw.

    Includes:
      1) accel/gyro file pairs discovered by existing ingestion helper
      2) standalone fused CSV sessions (Ax..Gz) not part of pair naming
    """
    sessions: List[SessionSpec] = []

    # 1) Paired raw files (accelerometer + gyroscope)
    pair_specs = discover_sensor_files(raw_dir, search_subdirs=True)
    seen_ids = set()
    for accel_path, gyro_path in pair_specs:
        session_id = _session_id_from_pair(accel_path, gyro_path)
        if session_id in seen_ids:
            continue
        sessions.append(
            SessionSpec(
                session_id=session_id,
                source_type="pair",
                accel_path=accel_path,
                gyro_path=gyro_path,
            )
        )
        seen_ids.add(session_id)

    # 2) Standalone fused CSVs
    for csv_path in sorted(raw_dir.rglob("*.csv")):
        name_l = csv_path.name.lower()
        if "accelerometer" in name_l or "gyroscope" in name_l:
            continue
        if not _looks_like_fused_csv(csv_path):
            continue

        session_id = csv_path.stem
        if session_id in seen_ids:
            continue

        sessions.append(
            SessionSpec(
                session_id=session_id,
                source_type="csv",
                csv_path=csv_path,
            )
        )
        seen_ids.add(session_id)

    sessions.sort(key=lambda s: s.session_id)
    return sessions


def prepare_fused_csv(
    session: SessionSpec,
    pipeline_config: PipelineConfig,
    ingest_output_dir: Path,
) -> DataIngestionArtifact:
    """Run Stage 1 ingestion for a session and return artifact."""
    ingest_output_dir.mkdir(parents=True, exist_ok=True)

    if session.source_type == "pair":
        ingest_cfg = DataIngestionConfig(
            accel_file=session.accel_path,
            gyro_file=session.gyro_path,
            target_hz=50,
            output_dir=ingest_output_dir,
        )
    else:
        ingest_cfg = DataIngestionConfig(
            input_csv=session.csv_path,
            target_hz=50,
            output_dir=ingest_output_dir,
        )

    ingest = DataIngestion(pipeline_config=pipeline_config, config=ingest_cfg)
    return ingest.initiate_data_ingestion()


def _extract_az_mean_after_unit_conversion(csv_path: Path) -> float:
    """Compute Az mean after unit conversion, before calibration/normalization."""
    df = pd.read_csv(csv_path)

    # Match DataTransformation behavior: run UnitDetector conversion step first.
    accel_candidates = ["Ax", "Ay", "Az", "Ax_w", "Ay_w", "Az_w"]
    accel_cols = [c for c in accel_candidates if c in df.columns and c.startswith(("Ax", "Ay", "Az"))]
    if not accel_cols:
        raise ValueError(f"No accelerometer columns found in {csv_path}")

    from src.preprocess_data import UnitDetector

    unit_logger = logging.getLogger("ablation.unit_probe")
    unit_logger.setLevel(logging.CRITICAL)
    detector = UnitDetector(unit_logger)
    df_converted, _ = detector.process_units(df, accel_cols)

    for col in ("Az", "Az_w", "az", "az_w"):
        if col in df_converted.columns:
            return float(df_converted[col].mean())
    raise ValueError(f"No Az column found after conversion in {csv_path}")


def _extract_prediction_metrics(predictions_csv: Path) -> Dict[str, float | int | str]:
    """Compute requested metrics from predictions output."""
    pred_df = pd.read_csv(predictions_csv)
    if pred_df.empty:
        return {
            "dominant_class": "UNKNOWN",
            "dominant_class_pct": 0.0,
            "unique_classes_predicted": 0,
            "mean_confidence": float("nan"),
            "hand_tapping_pct": 0.0,
        }

    if "predicted_activity" in pred_df.columns:
        series = pred_df["predicted_activity"].astype(str)
    elif "predicted_class" in pred_df.columns:
        series = pred_df["predicted_class"].astype(str)
    else:
        raise ValueError(
            f"Expected 'predicted_activity' or 'predicted_class' in {predictions_csv}"
        )

    counts = series.value_counts()
    dominant_class = str(counts.index[0])
    dominant_class_pct = float(100.0 * counts.iloc[0] / len(series))
    unique_classes_predicted = int(series.nunique())
    hand_tapping_pct = float(100.0 * (series == "hand_tapping").mean())

    if "confidence" in pred_df.columns:
        mean_confidence = float(pred_df["confidence"].mean())
    else:
        mean_confidence = float("nan")

    return {
        "dominant_class": dominant_class,
        "dominant_class_pct": dominant_class_pct,
        "unique_classes_predicted": unique_classes_predicted,
        "mean_confidence": mean_confidence,
        "hand_tapping_pct": hand_tapping_pct,
    }


def run_one_config(
    session: SessionSpec,
    ab_cfg: AblationConfig,
    fused_artifact: DataIngestionArtifact,
    pipeline_config: PipelineConfig,
    run_dir: Path,
    model_path: Optional[Path] = None,
) -> Dict[str, float | int | str | bool]:
    """Run Stage 3 + Stage 4 for one session/config pair and collect metrics."""
    prepared_dir = run_dir / "prepared"
    pred_dir = run_dir / "predictions"
    prepared_dir.mkdir(parents=True, exist_ok=True)
    pred_dir.mkdir(parents=True, exist_ok=True)

    # Stage 3: preprocessing using existing DataTransformation component
    t_cfg = DataTransformationConfig(
        input_csv=fused_artifact.fused_csv_path,
        enable_unit_conversion=True,
        enable_gravity_removal=ab_cfg.gravity_removal,
        enable_calibration=ab_cfg.calibration,
        enable_normalization=True,
        normalization_variant="zscore",
        output_dir=prepared_dir,
    )
    transformation = DataTransformation(
        pipeline_config=pipeline_config,
        config=t_cfg,
        ingestion_artifact=fused_artifact,
    )
    t_artifact = transformation.initiate_data_transformation()

    # Az mean after preprocessing+normalization (windowed tensor space)
    X = np.load(t_artifact.production_X_path)
    if X.ndim != 3 or X.shape[-1] < 3:
        raise ValueError(f"Unexpected window tensor shape at {t_artifact.production_X_path}: {X.shape}")
    az_mean_after_norm = float(X[:, :, 2].mean())

    # Stage 4: inference using existing ModelInference component
    m_cfg = ModelInferenceConfig(
        model_path=model_path,
        input_npy=t_artifact.production_X_path,
        output_dir=pred_dir,
        batch_size=32,
        confidence_threshold=0.50,
        mode="batch",
    )
    inference = ModelInference(
        pipeline_config=pipeline_config,
        config=m_cfg,
        transformation_artifact=t_artifact,
    )
    m_artifact = inference.initiate_model_inference()

    az_mean_before_norm = _extract_az_mean_after_unit_conversion(fused_artifact.fused_csv_path)
    az_offset_from_training = float(az_mean_before_norm - TRAINING_AZ_MEAN_MS2)
    pred_metrics = _extract_prediction_metrics(m_artifact.predictions_csv_path)

    result: Dict[str, float | int | str | bool] = {
        "dataset_id": session.session_id,
        "source_type": session.source_type,
        "config_id": ab_cfg.config_id,
        "gravity_removal": ab_cfg.gravity_removal,
        "calibration": ab_cfg.calibration,
        "dominant_class": pred_metrics["dominant_class"],
        "dominant_class_pct": pred_metrics["dominant_class_pct"],
        "unique_classes_predicted": pred_metrics["unique_classes_predicted"],
        "mean_confidence": pred_metrics["mean_confidence"],
        "Az_mean_before_norm": az_mean_before_norm,
        "Az_offset_from_training": az_offset_from_training,
        "Az_mean_after_norm": az_mean_after_norm,
        "hand_tapping_pct": pred_metrics["hand_tapping_pct"],
        "n_windows": int(t_artifact.n_windows),
        "predictions_csv": str(m_artifact.predictions_csv_path),
    }
    return result


def build_summary(results_df: pd.DataFrame) -> pd.DataFrame:
    """Build compact summary table required by the experiment."""
    rows: List[Dict[str, str | float]] = []

    def _safe_corr(x: pd.Series, y: pd.Series) -> Tuple[float, str]:
        """Return Pearson correlation with guardrails for degenerate inputs."""
        x_num = pd.to_numeric(x, errors="coerce")
        y_num = pd.to_numeric(y, errors="coerce")
        valid = x_num.notna() & y_num.notna()
        x_v = x_num[valid]
        y_v = y_num[valid]

        if len(x_v) < 2:
            return float("nan"), "Pearson correlation (insufficient points)"
        if float(x_v.std(ddof=0)) == 0.0:
            return float("nan"), "Pearson correlation (Az mean is constant)"
        if float(y_v.std(ddof=0)) == 0.0:
            return float("nan"), "Pearson correlation (hand_tapping_pct is constant)"
        return float(x_v.corr(y_v)), "Pearson correlation"

    if results_df.empty:
        rows.append(
            {
                "metric": "status",
                "scope": "all",
                "value": float("nan"),
                "notes": "No successful runs; summary unavailable",
            }
        )
        return pd.DataFrame(rows)

    by_config = (
        results_df.groupby("config_id", as_index=False)
        .agg(
            mean_unique_classes=("unique_classes_predicted", "mean"),
            mean_hand_tapping_pct=("hand_tapping_pct", "mean"),
            mean_dominant_class_pct=("dominant_class_pct", "mean"),
            mean_confidence=("mean_confidence", "mean"),
        )
        .sort_values("config_id")
    )

    # 1) Most diverse configuration
    best_diverse = by_config.sort_values("mean_unique_classes", ascending=False).iloc[0]
    rows.append(
        {
            "metric": "most_diverse_predictions",
            "scope": "config",
            "value": float(best_diverse["mean_unique_classes"]),
            "notes": f"config={best_diverse['config_id']}",
        }
    )

    # 2) Hand-tapping dominance reduction vs baseline A
    baseline_row = by_config[by_config["config_id"] == "A"]
    if not baseline_row.empty:
        baseline_hand = float(baseline_row.iloc[0]["mean_hand_tapping_pct"])
        for _, row in by_config.iterrows():
            reduction = baseline_hand - float(row["mean_hand_tapping_pct"])
            rows.append(
                {
                    "metric": "hand_tapping_reduction_vs_A_pct_points",
                    "scope": str(row["config_id"]),
                    "value": reduction,
                    "notes": f"A_mean={baseline_hand:.4f}, cfg_mean={float(row['mean_hand_tapping_pct']):.4f}",
                }
            )

        best_reduce = by_config.copy()
        best_reduce["reduction"] = baseline_hand - best_reduce["mean_hand_tapping_pct"]
        best_row = best_reduce.sort_values("reduction", ascending=False).iloc[0]
        rows.append(
            {
                "metric": "best_hand_tapping_reduction_config",
                "scope": "config",
                "value": float(best_row["reduction"]),
                "notes": f"config={best_row['config_id']}",
            }
        )

    # 3) Correlation between Az_mean and hand_tapping %
    corr_all_before, note_before = _safe_corr(
        results_df["Az_mean_before_norm"], results_df["hand_tapping_pct"]
    )
    rows.append(
        {
            "metric": "corr_az_before_vs_hand_tapping_pct",
            "scope": "all",
            "value": corr_all_before,
            "notes": note_before,
        }
    )

    corr_all_after, note_after = _safe_corr(
        results_df["Az_mean_after_norm"], results_df["hand_tapping_pct"]
    )
    rows.append(
        {
            "metric": "corr_az_after_vs_hand_tapping_pct",
            "scope": "all",
            "value": corr_all_after,
            "notes": note_after,
        }
    )

    for cfg_id, grp in results_df.groupby("config_id"):
        corr_b, note_b = _safe_corr(grp["Az_mean_before_norm"], grp["hand_tapping_pct"])
        corr_a, note_a = _safe_corr(grp["Az_mean_after_norm"], grp["hand_tapping_pct"])

        rows.append(
            {
                "metric": "corr_az_before_vs_hand_tapping_pct",
                "scope": str(cfg_id),
                "value": corr_b,
                "notes": f"{note_b} within config",
            }
        )
        rows.append(
            {
                "metric": "corr_az_after_vs_hand_tapping_pct",
                "scope": str(cfg_id),
                "value": corr_a,
                "notes": f"{note_a} within config",
            }
        )

    # Include compact per-config averages for easy reading
    for _, row in by_config.iterrows():
        rows.append(
            {
                "metric": "config_mean_unique_classes",
                "scope": str(row["config_id"]),
                "value": float(row["mean_unique_classes"]),
                "notes": "Average unique_classes_predicted across datasets",
            }
        )
        rows.append(
            {
                "metric": "config_mean_hand_tapping_pct",
                "scope": str(row["config_id"]),
                "value": float(row["mean_hand_tapping_pct"]),
                "notes": "Average hand_tapping window percentage",
            }
        )

    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run preprocessing ablation experiment")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=ROOT / "data" / "raw",
        help="Directory containing production sessions (default: data/raw)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "ablation",
        help="Output folder for ablation CSV files (default: outputs/ablation)",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="Optional custom model path (default: pretrained pipeline model)",
    )
    parser.add_argument(
        "--max-datasets",
        type=int,
        default=None,
        help="Optional cap for number of discovered datasets (for quick tests)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(verbose=args.verbose)

    raw_dir = args.raw_dir
    output_dir = args.output_dir
    runs_dir = output_dir / "runs"
    output_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    if not raw_dir.exists():
        LOGGER.error("Raw directory not found: %s", raw_dir)
        return 1

    pipeline_config = PipelineConfig()

    sessions = discover_sessions(raw_dir)
    if args.max_datasets is not None:
        sessions = sessions[: max(0, args.max_datasets)]

    LOGGER.info("Discovered %d session(s) in %s", len(sessions), raw_dir)
    if not sessions:
        LOGGER.error("No sessions found. Expected fused CSVs or accel/gyro file pairs in %s", raw_dir)
        return 2

    for s in sessions:
        LOGGER.info("  - %s (%s)", s.session_id, s.source_type)

    results: List[Dict[str, float | int | str | bool]] = []
    errors: List[Dict[str, str]] = []

    total_jobs = len(sessions) * len(ABLATION_CONFIGS)
    job_idx = 0

    for session in sessions:
        session_base = runs_dir / session.session_id
        ingest_dir = session_base / "ingestion"

        try:
            fused_artifact = prepare_fused_csv(
                session=session,
                pipeline_config=pipeline_config,
                ingest_output_dir=ingest_dir,
            )
        except Exception as exc:
            LOGGER.exception("Failed ingestion for session %s", session.session_id)
            errors.append(
                {
                    "dataset_id": session.session_id,
                    "config_id": "ALL",
                    "error": f"ingestion_failed: {exc}",
                }
            )
            continue

        for ab_cfg in ABLATION_CONFIGS:
            job_idx += 1
            LOGGER.info(
                "[%d/%d] Running %s on %s",
                job_idx,
                total_jobs,
                ab_cfg.config_id,
                session.session_id,
            )
            run_dir = session_base / f"config_{ab_cfg.config_id}"
            try:
                row = run_one_config(
                    session=session,
                    ab_cfg=ab_cfg,
                    fused_artifact=fused_artifact,
                    pipeline_config=pipeline_config,
                    run_dir=run_dir,
                    model_path=args.model_path,
                )
                results.append(row)
            except Exception as exc:
                LOGGER.exception(
                    "Failed run for dataset=%s config=%s", session.session_id, ab_cfg.config_id
                )
                errors.append(
                    {
                        "dataset_id": session.session_id,
                        "config_id": ab_cfg.config_id,
                        "error": str(exc),
                    }
                )

    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df = results_df.sort_values(["dataset_id", "config_id"]).reset_index(drop=True)

    summary_df = build_summary(results_df)

    results_path = output_dir / "ablation_results.csv"
    summary_path = output_dir / "ablation_summary.csv"
    results_df.to_csv(results_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    LOGGER.info("Saved results: %s", results_path)
    LOGGER.info("Saved summary: %s", summary_path)

    if errors:
        errors_path = output_dir / "ablation_errors.json"
        with open(errors_path, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2)
        LOGGER.warning("Completed with %d error(s); see %s", len(errors), errors_path)
    else:
        LOGGER.info("Completed without run errors")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

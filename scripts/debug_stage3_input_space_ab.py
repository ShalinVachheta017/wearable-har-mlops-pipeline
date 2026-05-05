"""A/B diagnostic for Stage 3 model input space.

Runs the same fused CSV through Stage 3 twice:
1. raw physical units (m/s^2 + deg/s)
2. saved z-score scaler

Then loads the current model and compares prediction collapse signals.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import tensorflow as tf

from src.components.data_transformation import DataTransformation
from src.entity.artifact_entity import DataIngestionArtifact
from src.entity.config_entity import DataTransformationConfig, PipelineConfig
from src.utils.label_mapping import get_activity_classes


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    return value


def _entropy(probs: np.ndarray) -> np.ndarray:
    safe = np.clip(probs, 1e-12, 1.0)
    return -np.sum(safe * np.log(safe), axis=1)


def _run_transformation(
    input_csv: Path,
    output_dir: Path,
    enable_normalization: bool,
    normalization_variant: str,
    scaler_path: Path,
) -> Dict[str, Any]:
    pipeline_cfg = PipelineConfig(data_prepared_dir=output_dir)
    transform_cfg = DataTransformationConfig(
        input_csv=input_csv,
        output_dir=output_dir,
        enable_unit_conversion=True,
        enable_gravity_removal=False,
        enable_calibration=False,
        enable_normalization=enable_normalization,
        normalization_variant=normalization_variant,
        scaler_path=scaler_path,
    )
    ingestion_artifact = DataIngestionArtifact(
        fused_csv_path=input_csv,
        n_rows=0,
        n_columns=0,
        sampling_hz=50,
        ingestion_timestamp=datetime.now().isoformat(),
        source_type="diagnostic",
        source_path=input_csv,
    )
    artifact = DataTransformation(
        pipeline_cfg,
        transform_cfg,
        ingestion_artifact,
        validation_artifact=None,
    ).initiate_data_transformation()
    return {
        "artifact": artifact,
        "X": np.load(artifact.production_X_path),
    }


def _summarize_predictions(
    name: str,
    X: np.ndarray,
    model: tf.keras.Model,
    index_to_class: Dict[int, str],
    top_rows: List[Dict[str, Any]],
    batch_size: int,
) -> Dict[str, Any]:
    probs = model.predict(X, batch_size=batch_size, verbose=0)
    preds = probs.argmax(axis=1)
    conf = probs.max(axis=1)
    ent = _entropy(probs)

    values, counts = np.unique(preds, return_counts=True)
    distribution = {
        index_to_class.get(int(idx), str(idx)): int(count)
        for idx, count in zip(values, counts)
    }
    dominant_idx = int(values[np.argmax(counts)]) if len(values) else -1
    dominant_count = int(counts.max()) if len(counts) else 0
    dominant_pct = float(dominant_count / max(len(preds), 1) * 100.0)

    for window_id in range(min(20, len(probs))):
        order = np.argsort(probs[window_id])[::-1][:3]
        top_rows.append(
            {
                "variant": name,
                "window_id": window_id,
                "prediction_index": int(preds[window_id]),
                "prediction_label": index_to_class.get(int(preds[window_id]), str(preds[window_id])),
                "confidence": float(conf[window_id]),
                "top1_label": index_to_class.get(int(order[0]), str(order[0])),
                "top1_probability": float(probs[window_id, order[0]]),
                "top2_label": index_to_class.get(int(order[1]), str(order[1])),
                "top2_probability": float(probs[window_id, order[1]]),
                "top3_label": index_to_class.get(int(order[2]), str(order[2])),
                "top3_probability": float(probs[window_id, order[2]]),
            }
        )

    warning_level = "OK"
    if dominant_pct >= 95.0:
        warning_level = "CRITICAL_ONE_CLASS_COLLAPSE"
    elif dominant_pct >= 90.0:
        warning_level = "HIGH_ONE_CLASS_DOMINANCE"
    elif dominant_pct >= 70.0:
        warning_level = "WARNING_ONE_CLASS_DOMINANCE"

    return {
        "variant": name,
        "x_shape": list(X.shape),
        "x_dtype": str(X.dtype),
        "prediction_distribution": distribution,
        "dominant_class": index_to_class.get(dominant_idx, str(dominant_idx)),
        "dominant_pct": dominant_pct,
        "mean_confidence": float(conf.mean()) if len(conf) else 0.0,
        "entropy_mean": float(ent.mean()) if len(ent) else 0.0,
        "entropy_min": float(ent.min()) if len(ent) else 0.0,
        "entropy_max": float(ent.max()) if len(ent) else 0.0,
        "warning_level": warning_level,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 3 raw-vs-zscore A/B diagnostic")
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("data/processed/fused_2025_03_23_15_23_10_50Hz.csv"),
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("models/pretrained/fine_tuned_model_1dcnnbilstm.keras"),
    )
    parser.add_argument(
        "--scaler",
        type=Path,
        default=Path("data/prepared/scaler_train_only.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/stage3_ab_diagnostics"),
    )
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    index_to_class = get_activity_classes()

    model = tf.keras.models.load_model(args.model, compile=False)
    top_rows: List[Dict[str, Any]] = []
    report: Dict[str, Any] = {
        "created_at": datetime.now().isoformat(),
        "input_csv": args.input_csv,
        "model_path": args.model,
        "scaler_path": args.scaler,
        "model_input_shape": model.input_shape,
        "model_output_shape": model.output_shape,
        "class_mapping": index_to_class,
        "variants": {},
    }

    variants = [
        ("raw_physical_units_ms2_dps", False, "none"),
        ("zscore_scaled_current_scaler", True, "zscore"),
    ]
    for name, enable_norm, variant in variants:
        stage_out = args.output_dir / name
        result = _run_transformation(
            input_csv=args.input_csv,
            output_dir=stage_out,
            enable_normalization=enable_norm,
            normalization_variant=variant,
            scaler_path=args.scaler,
        )
        summary = _summarize_predictions(
            name=name,
            X=result["X"],
            model=model,
            index_to_class=index_to_class,
            top_rows=top_rows,
            batch_size=args.batch_size,
        )
        artifact = result["artifact"]
        summary["production_X_path"] = artifact.production_X_path
        summary["transformation_report_path"] = artifact.transformation_report_path
        report["variants"][name] = summary

    json_path = args.output_dir / "stage3_input_space_ab_report.json"
    csv_path = args.output_dir / "stage3_input_space_ab_top20.csv"
    json_path.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")
    pd.DataFrame(top_rows).to_csv(csv_path, index=False)

    print(f"Saved JSON report: {json_path}")
    print(f"Saved top-20 CSV:  {csv_path}")
    for name, summary in report["variants"].items():
        print(
            f"{name}: dominant={summary['dominant_class']} "
            f"{summary['dominant_pct']:.2f}% | "
            f"mean_conf={summary['mean_confidence']:.4f} | "
            f"entropy={summary['entropy_mean']:.4f} | "
            f"{summary['warning_level']}"
        )


if __name__ == "__main__":
    main()

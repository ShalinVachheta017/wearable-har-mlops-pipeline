"""
Stage 4 - Model Inference.

This component owns offline batch inference. It loads the Stage 3 tensor, runs
the configured Keras model, writes prediction artifacts, and returns a Stage 4
artifact with collapse evidence for downstream evaluation and monitoring.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.config import DEFAULT_MODEL_PATH
from src.entity.artifact_entity import DataTransformationArtifact, ModelInferenceArtifact
from src.entity.config_entity import ModelInferenceConfig, PipelineConfig
from src.utils.common import get_timestamp
from src.utils.label_mapping import get_activity_classes, get_class_to_index

logger = logging.getLogger(__name__)

ACTIVITY_CLASSES: Dict[int, str] = get_activity_classes()
CLASS_TO_INDEX: Dict[str, int] = get_class_to_index()
EXPECTED_MODEL_INPUT = (None, 200, 6)
EXPECTED_MODEL_OUTPUT = (None, 11)
EXPECTED_WINDOW_SHAPE = (200, 6)
CHANNEL_ORDER = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]


@dataclass
class InferenceResponse:
    """Container for completed Stage 4 inference outputs."""

    results_df: pd.DataFrame
    probabilities: np.ndarray
    report: Dict[str, Any]
    output_files: Dict[str, Path]
    model_path: Path
    model_md5: str
    inference_time_seconds: float


def _file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _numeric_stats(values: np.ndarray) -> Dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "median": float(np.median(arr)),
        "max": float(np.max(arr)),
    }


def _confidence_level(confidence: float, threshold: float) -> str:
    if confidence > 0.90:
        return "HIGH"
    if confidence > 0.70:
        return "MODERATE"
    if confidence > threshold:
        return "LOW"
    return "UNCERTAIN"


def _collapse_level(dominant_pct: float) -> str:
    if dominant_pct > 95.0:
        return "CRITICAL_COLLAPSE"
    if dominant_pct > 90.0:
        return "WARNING_90"
    if dominant_pct > 70.0:
        return "WARNING_70"
    return "NONE"


def _softmax_entropy(probabilities: np.ndarray) -> np.ndarray:
    safe = np.clip(probabilities, 1e-12, 1.0)
    return -np.sum(safe * np.log(safe), axis=1)


def _top2_margin(probabilities: np.ndarray) -> np.ndarray:
    sorted_probs = np.sort(probabilities, axis=1)
    return sorted_probs[:, -1] - sorted_probs[:, -2]


class ModelInference:
    """Run Stage 4 model inference."""

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        config: ModelInferenceConfig,
        transformation_artifact: DataTransformationArtifact,
    ):
        """
        Method Name :   __init__
        Description :   Store Stage 4 configuration and Stage 3 artifact paths.

        Output      :   Initializes the ModelInference component.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            self.pipeline_config = pipeline_config
            self.config = config
            self.transformation_artifact = transformation_artifact
        except Exception as exc:
            logger.exception("Failed to initialize Stage 4 model inference.")
            raise exc

    def load_model(self, model_path: Path):
        """
        Method Name :   load_model
        Description :   Load the configured Keras model and validate input/output shape.

        Output      :   Returns the loaded Keras model.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")

            import tensorflow as tf

            model = tf.keras.models.load_model(str(model_path), compile=False)
            input_shape = tuple(model.input_shape)
            output_shape = tuple(model.output_shape)
            if input_shape != EXPECTED_MODEL_INPUT:
                raise ValueError(
                    f"Unexpected model input shape {input_shape}; expected {EXPECTED_MODEL_INPUT}."
                )
            if output_shape != EXPECTED_MODEL_OUTPUT:
                raise ValueError(
                    f"Unexpected model output shape {output_shape}; expected {EXPECTED_MODEL_OUTPUT}."
                )
            return model
        except Exception as exc:
            logger.exception("Failed to load inference model from %s", model_path)
            raise exc

    def load_input_tensor(self, input_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Method Name :   load_input_tensor
        Description :   Load and validate production_X.npy from Stage 3.

        Output      :   Returns the input tensor and metadata summary.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            if not input_path.exists():
                raise FileNotFoundError(f"Input tensor not found: {input_path}")

            data = np.load(input_path)
            if data.ndim != 3:
                raise ValueError(f"Expected a 3D tensor, got shape {data.shape}.")
            if tuple(data.shape[1:]) != EXPECTED_WINDOW_SHAPE:
                raise ValueError(
                    f"Expected window shape {EXPECTED_WINDOW_SHAPE}, got {tuple(data.shape[1:])}."
                )
            if not np.isfinite(data).all():
                raise ValueError("production_X.npy contains NaN or inf; check Stage 3 output.")

            data = data.astype(np.float32, copy=False)
            metadata = {
                "input_path": str(input_path),
                "shape": list(data.shape),
                "dtype": str(data.dtype),
                "n_windows": int(data.shape[0]),
                "window_size": int(data.shape[1]),
                "n_channels": int(data.shape[2]),
                "channel_order": CHANNEL_ORDER,
                "loaded_at": datetime.now().isoformat(),
            }
            return data, metadata
        except Exception as exc:
            logger.exception("Failed to load inference input from %s", input_path)
            raise exc

    def validate_activity_mapping(self) -> None:
        """
        Method Name :   validate_activity_mapping
        Description :   Validate the canonical 11-class activity mapping.

        Output      :   Returns None when mapping is valid.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            if set(ACTIVITY_CLASSES.keys()) != set(range(11)):
                raise ValueError(f"Activity ids must be 0..10, got {sorted(ACTIVITY_CLASSES)}")
            if len(CLASS_TO_INDEX) != 11:
                raise ValueError(f"Expected 11 activity names, got {len(CLASS_TO_INDEX)}")
            if CLASS_TO_INDEX.get("hand_tapping") != 4:
                raise ValueError("Activity mapping mismatch: hand_tapping must be index 4.")
            for class_id, activity in ACTIVITY_CLASSES.items():
                if CLASS_TO_INDEX.get(activity) != class_id:
                    raise ValueError(f"Reverse mapping mismatch for {activity!r}.")
        except Exception as exc:
            logger.exception("Activity mapping validation failed.")
            raise exc

    def predict(self, model: Any, data: np.ndarray) -> Tuple[pd.DataFrame, np.ndarray, Dict[str, Any]]:
        """
        Method Name :   predict
        Description :   Run batch prediction and build the Stage 4 prediction table.

        Output      :   Returns predictions DataFrame, probability matrix, and numeric stats.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            probabilities = model.predict(
                data,
                batch_size=self.config.batch_size,
                verbose=0,
            )
            probabilities = np.asarray(probabilities, dtype=np.float32)
            expected_shape = (len(data), len(ACTIVITY_CLASSES))
            if probabilities.shape != expected_shape:
                raise ValueError(
                    f"Expected probabilities shape {expected_shape}, got {probabilities.shape}."
                )
            if not np.isfinite(probabilities).all():
                raise ValueError("Model probabilities contain NaN or inf.")

            row_sums = probabilities.sum(axis=1)
            if not np.allclose(row_sums, 1.0, atol=1e-5):
                raise ValueError(
                    "Model probability rows do not sum to 1 within tolerance "
                    f"(min={row_sums.min()}, max={row_sums.max()})."
                )

            predictions = np.argmax(probabilities, axis=1).astype(np.int32)
            confidence = np.max(probabilities, axis=1)
            entropy = _softmax_entropy(probabilities)
            margins = _top2_margin(probabilities)

            rows = []
            for idx, predicted_class in enumerate(predictions):
                conf = float(confidence[idx])
                row = {
                    "window_id": int(idx),
                    "predicted_class": int(predicted_class),
                    "predicted_activity": ACTIVITY_CLASSES[int(predicted_class)],
                    "confidence": conf,
                    "confidence_pct": f"{100 * conf:.1f}%",
                    "confidence_level": _confidence_level(
                        conf,
                        self.config.confidence_threshold,
                    ),
                    "is_uncertain": bool(conf <= self.config.confidence_threshold),
                    "entropy": float(entropy[idx]),
                    "top2_margin": float(margins[idx]),
                }
                for class_id, activity in ACTIVITY_CLASSES.items():
                    row[f"prob_{activity}"] = float(probabilities[idx, class_id])
                rows.append(row)

            stats = {
                "probability_row_sum_mean": float(np.mean(row_sums)),
                "probability_row_sum_min": float(np.min(row_sums)),
                "probability_row_sum_max": float(np.max(row_sums)),
                "probability_row_sum_close_to_1": bool(np.allclose(row_sums, 1.0, atol=1e-5)),
                "confidence_stats": _numeric_stats(confidence),
                "entropy_stats": _numeric_stats(entropy),
                "top2_margin_stats": _numeric_stats(margins),
            }
            return pd.DataFrame(rows), probabilities, stats
        except Exception as exc:
            logger.exception("Stage 4 batch prediction failed.")
            raise exc

    def build_report(
        self,
        model: Any,
        model_path: Path,
        model_md5: str,
        input_path: Path,
        input_metadata: Dict[str, Any],
        results_df: pd.DataFrame,
        probabilities: np.ndarray,
        prediction_stats: Dict[str, Any],
        inference_time_seconds: float,
    ) -> Dict[str, Any]:
        """
        Method Name :   build_report
        Description :   Build the Stage 4 inference evidence report.

        Output      :   Returns the report dictionary saved as inference_report.json.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            distribution = results_df["predicted_activity"].value_counts().to_dict()
            n_predictions = int(len(results_df))
            dominant_class = None
            dominant_count = 0
            if distribution:
                dominant_class, dominant_count = max(
                    distribution.items(),
                    key=lambda item: item[1],
                )
            dominant_pct = float(dominant_count / n_predictions * 100.0) if n_predictions else 0.0
            collapse = _collapse_level(dominant_pct)

            top3_preview = []
            for row_idx in range(min(20, n_predictions)):
                order = np.argsort(probabilities[row_idx])[::-1][:3]
                top3_preview.append(
                    {
                        "window_id": int(row_idx),
                        "predicted_class": int(results_df.loc[row_idx, "predicted_class"]),
                        "predicted_activity": str(results_df.loc[row_idx, "predicted_activity"]),
                        "confidence": float(results_df.loc[row_idx, "confidence"]),
                        "entropy": float(results_df.loc[row_idx, "entropy"]),
                        "top1": {
                            "class_id": int(order[0]),
                            "activity": ACTIVITY_CLASSES[int(order[0])],
                            "probability": float(probabilities[row_idx, order[0]]),
                        },
                        "top2": {
                            "class_id": int(order[1]),
                            "activity": ACTIVITY_CLASSES[int(order[1])],
                            "probability": float(probabilities[row_idx, order[1]]),
                        },
                        "top3": {
                            "class_id": int(order[2]),
                            "activity": ACTIVITY_CLASSES[int(order[2])],
                            "probability": float(probabilities[row_idx, order[2]]),
                        },
                    }
                )

            return {
                "created_at": datetime.now().isoformat(),
                "stage": "model_inference",
                "configuration": {
                    "batch_size": int(self.config.batch_size),
                    "confidence_threshold": float(self.config.confidence_threshold),
                    "runtime_mode": "offline_batch",
                    "confidence_note": (
                        "Confidence is maximum softmax model confidence, not calibrated "
                        "correctness probability."
                    ),
                },
                "model": {
                    "path": str(model_path),
                    "md5": model_md5,
                    "input_shape": list(model.input_shape),
                    "output_shape": list(model.output_shape),
                    "n_parameters": int(model.count_params()),
                },
                "input": {
                    "path": str(input_path),
                    **input_metadata,
                },
                "class_mapping": {
                    "label_to_activity": {str(k): v for k, v in ACTIVITY_CLASSES.items()},
                    "activity_to_label": CLASS_TO_INDEX,
                    "hand_tapping_index": CLASS_TO_INDEX.get("hand_tapping"),
                },
                "n_predictions": n_predictions,
                "inference_time_seconds": float(inference_time_seconds),
                "throughput_windows_per_sec": (
                    float(n_predictions / inference_time_seconds)
                    if inference_time_seconds > 0
                    else 0.0
                ),
                "prediction_distribution": distribution,
                "dominant_class": dominant_class,
                "dominant_pct": dominant_pct,
                "collapse_level": collapse,
                "collapse_flags": {
                    "dominant_gt_70_pct": bool(dominant_pct > 70.0),
                    "dominant_gt_90_pct": bool(dominant_pct > 90.0),
                    "dominant_gt_95_pct": bool(dominant_pct > 95.0),
                },
                "confidence_stats": prediction_stats["confidence_stats"],
                "entropy_stats": prediction_stats["entropy_stats"],
                "top2_margin_stats": prediction_stats["top2_margin_stats"],
                "probability_checks": {
                    "shape": list(probabilities.shape),
                    "row_sum_mean": prediction_stats["probability_row_sum_mean"],
                    "row_sum_min": prediction_stats["probability_row_sum_min"],
                    "row_sum_max": prediction_stats["probability_row_sum_max"],
                    "row_sum_close_to_1": prediction_stats["probability_row_sum_close_to_1"],
                },
                "top3_first_20_windows": top3_preview,
            }
        except Exception as exc:
            logger.exception("Failed to build Stage 4 inference report.")
            raise exc

    def save_outputs(
        self,
        results_df: pd.DataFrame,
        probabilities: np.ndarray,
        report: Dict[str, Any],
        output_dir: Path,
        timestamp: str,
    ) -> Dict[str, Path]:
        """
        Method Name :   save_outputs
        Description :   Save Stage 4 CSV, NPY, metadata, and inference report artifacts.

        Output      :   Returns a dictionary of output file paths.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            csv_path = output_dir / f"predictions_{timestamp}.csv"
            predictions_path = output_dir / "production_predictions_fresh.npy"
            probabilities_path = output_dir / f"predictions_{timestamp}_probs.npy"
            metadata_path = output_dir / f"predictions_{timestamp}_metadata.json"
            report_path = output_dir / "inference_report.json"

            results_df.to_csv(csv_path, index=False)
            np.save(predictions_path, results_df["predicted_class"].to_numpy(dtype=np.int32))
            np.save(probabilities_path, probabilities)

            metadata = {
                "timestamp": timestamp,
                "model_path": report["model"]["path"],
                "input_path": report["input"]["path"],
                "batch_size": report["configuration"]["batch_size"],
                "confidence_threshold": report["configuration"]["confidence_threshold"],
                "data": report["input"],
                "results_summary": {
                    "total_windows": report["n_predictions"],
                    "activity_distribution": report["prediction_distribution"],
                    "confidence_stats": report["confidence_stats"],
                    "confidence_levels": results_df["confidence_level"].value_counts().to_dict(),
                    "uncertain_count": int(results_df["is_uncertain"].sum()),
                    "dominant_class": report["dominant_class"],
                    "dominant_pct": report["dominant_pct"],
                    "collapse_level": report["collapse_level"],
                },
                "activity_classes": {str(k): v for k, v in ACTIVITY_CLASSES.items()},
                "export_time": datetime.now().isoformat(),
            }
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

            return {
                "csv": csv_path,
                "predictions_npy": predictions_path,
                "probabilities_npy": probabilities_path,
                "metadata_json": metadata_path,
                "inference_report": report_path,
            }
        except Exception as exc:
            logger.exception("Failed to save Stage 4 inference outputs.")
            raise exc

    def run_inference(self) -> InferenceResponse:
        """
        Method Name :   run_inference
        Description :   Execute the complete Stage 4 model inference flow.

        Output      :   Returns an InferenceResponse with report and output paths.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            self.validate_activity_mapping()
            model_path = Path(self.config.model_path or DEFAULT_MODEL_PATH)
            input_path = Path(self.config.input_npy or self.transformation_artifact.production_X_path)
            output_dir = Path(
                self.config.output_dir or self.pipeline_config.data_prepared_dir / "predictions"
            )
            timestamp = get_timestamp()
            model_md5 = _file_md5(model_path)

            model = self.load_model(model_path)
            data, input_metadata = self.load_input_tensor(input_path)

            start = time.perf_counter()
            results_df, probabilities, prediction_stats = self.predict(model, data)
            inference_time = time.perf_counter() - start

            report = self.build_report(
                model=model,
                model_path=model_path,
                model_md5=model_md5,
                input_path=input_path,
                input_metadata=input_metadata,
                results_df=results_df,
                probabilities=probabilities,
                prediction_stats=prediction_stats,
                inference_time_seconds=inference_time,
            )
            output_files = self.save_outputs(
                results_df=results_df,
                probabilities=probabilities,
                report=report,
                output_dir=output_dir,
                timestamp=timestamp,
            )
            self.log_mlflow(report, output_files)
            return InferenceResponse(
                results_df=results_df,
                probabilities=probabilities,
                report=report,
                output_files=output_files,
                model_path=model_path,
                model_md5=model_md5,
                inference_time_seconds=inference_time,
            )
        except Exception as exc:
            logger.exception("Stage 4 inference flow failed.")
            raise exc

    def initiate_model_inference(self) -> ModelInferenceArtifact:
        """
        Method Name :   initiate_model_inference
        Description :   Start Stage 4 and convert the inference response into an artifact.

        Output      :   Returns a ModelInferenceArtifact.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            logger.info("=" * 60)
            logger.info("STAGE 4 - Model Inference")
            logger.info("=" * 60)

            response = self.run_inference()
            report = response.report
            logger.info(
                "Inference complete: %s predictions in %.2fs; dominant=%s %.2f%%; collapse=%s",
                report["n_predictions"],
                response.inference_time_seconds,
                report["dominant_class"],
                report["dominant_pct"],
                report["collapse_level"],
            )

            # Log human-readable class distribution and confidence summary
            results_df = response.results_df
            if not results_df.empty:
                logger.info("")
                logger.info("-" * 60)
                logger.info("PREDICTED ACTIVITY DISTRIBUTION (unlabeled profile)")
                logger.info("-" * 60)

                # Calculate aggregate stats
                res = results_df.groupby('predicted_activity').agg(
                    Count=('window_id', 'count'),
                    Mean_Confidence=('confidence', 'mean')
                ).sort_values('Count', ascending=False)

                res['Percentage'] = (res['Count'] / len(results_df)) * 100
                res['Mean_Confidence'] = (res['Mean_Confidence'] * 100).map('{:.1f}%'.format)
                res['Percentage'] = res['Percentage'].map('{:.1f}%'.format)

                # Print formatted table to logs
                logger.info(f"{'Activity':<25} | {'Count':<8} | {'% of Total':<12} | {'Avg Confidence':<15}")
                logger.info("-" * 60)
                for activity, row in res.iterrows():
                    logger.info(f"{activity:<25} | {row['Count']:<8} | {row['Percentage']:<12} | {row['Mean_Confidence']:<15}")
                logger.info("-" * 60)
                logger.info("")

            return ModelInferenceArtifact(
                predictions_csv_path=response.output_files["csv"],
                predictions_npy_path=response.output_files["predictions_npy"],
                probabilities_npy_path=response.output_files["probabilities_npy"],
                metadata_json_path=response.output_files["metadata_json"],
                inference_report_path=response.output_files["inference_report"],
                n_predictions=report["n_predictions"],
                inference_time_seconds=response.inference_time_seconds,
                model_version=response.model_path.stem,
                active_model_path=response.model_path,
                model_md5=response.model_md5,
                activity_distribution=report["prediction_distribution"],
                confidence_stats=report["confidence_stats"],
                entropy_stats=report["entropy_stats"],
                top2_margin_stats=report["top2_margin_stats"],
                dominant_class=report["dominant_class"],
                dominant_pct=report["dominant_pct"],
                collapse_level=report["collapse_level"],
            )
        except Exception as exc:
            logger.exception("Stage 4 model inference failed.")
            raise exc

    def log_mlflow(self, report: Dict[str, Any], output_files: Dict[str, Path]) -> None:
        """
        Method Name :   log_mlflow
        Description :   Best-effort MLflow logging for Stage 4 evidence.

        Output      :   Logs parameters, metrics, and artifacts when MLflow is available.
        On Failure  :   Logs a warning and continues without failing inference.
        """
        try:
            import mlflow

            mlflow.set_experiment("inference-production")
            with mlflow.start_run(run_name=f"inference_{get_timestamp()}", nested=True):
                mlflow.log_params(
                    {
                        "model_path": report["model"]["path"],
                        "model_md5": report["model"]["md5"],
                        "input_path": report["input"]["path"],
                        "batch_size": report["configuration"]["batch_size"],
                        "confidence_threshold": report["configuration"]["confidence_threshold"],
                        "runtime_mode": report["configuration"]["runtime_mode"],
                    }
                )
                mlflow.log_metrics(
                    {
                        "total_windows": report["n_predictions"],
                        "avg_confidence": report["confidence_stats"]["mean"],
                        "std_confidence": report["confidence_stats"]["std"],
                        "entropy_mean": report["entropy_stats"]["mean"],
                        "top2_margin_mean": report["top2_margin_stats"]["mean"],
                        "dominant_pct": report["dominant_pct"],
                    }
                )
                for activity, count in report["prediction_distribution"].items():
                    mlflow.log_metric(f"count_{activity}", int(count))
                for path in output_files.values():
                    if path.exists():
                        mlflow.log_artifact(str(path))
        except Exception as exc:  # pragma: no cover - MLflow is auxiliary.
            logger.warning("MLflow inference logging skipped: %s", exc)


def run_model_inference_from_paths(
    input_path: Path,
    model_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    batch_size: int = 32,
    confidence_threshold: float = 0.50,
) -> ModelInferenceArtifact:
    """
    Method Name :   run_model_inference_from_paths
    Description :   Convenience helper used by the thin CLI wrapper.

    Output      :   Returns the ModelInferenceArtifact from a one-off Stage 4 run.
    On Failure  :   Logs the error and raises the exception.
    """
    try:
        transformation_artifact = DataTransformationArtifact(
            production_X_path=Path(input_path),
            metadata_path=Path(input_path).with_name("production_metadata.json"),
            n_windows=0,
            window_size=EXPECTED_WINDOW_SHAPE[0],
            unit_conversion_applied=False,
            preprocessing_timestamp=datetime.now().isoformat(),
            channel_order=CHANNEL_ORDER,
        )
        config = ModelInferenceConfig(
            model_path=Path(model_path) if model_path else None,
            input_npy=Path(input_path),
            output_dir=Path(output_dir) if output_dir else None,
            batch_size=batch_size,
            confidence_threshold=confidence_threshold,
        )
        return ModelInference(PipelineConfig(), config, transformation_artifact).initiate_model_inference()
    except Exception as exc:
        logger.exception("Path-based model inference failed.")
        raise exc

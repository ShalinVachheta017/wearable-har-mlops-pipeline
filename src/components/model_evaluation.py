"""
Stage 5 - Model Evaluation.

This component evaluates the Stage 4 prediction CSV. It stays intentionally
simple: load predictions, validate the contract, optionally load paired labels,
summarize distribution/confidence/temporal behavior, write reports, and return
the Stage 5 artifact.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.entity.artifact_entity import ModelEvaluationArtifact, ModelInferenceArtifact
from src.entity.config_entity import (
    ModelEvaluationConfig,
    PipelineConfig,
    PostInferenceMonitoringConfig,
)
from src.utils.common import get_timestamp
from src.utils.label_mapping import get_activity_classes

logger = logging.getLogger(__name__)

ACTIVITY_CLASSES: Dict[int, str] = get_activity_classes()
WINDOW_DURATION_SECONDS = 4.0
WINDOW_STEP_SECONDS = 2.0
REQUIRED_COLUMNS = {
    "window_id",
    "predicted_class",
    "predicted_activity",
    "confidence",
    "confidence_level",
    "is_uncertain",
    "entropy",
    "top2_margin",
}


@dataclass
class EvaluatePredictionsResponse:
    """Container for the completed Stage 5 evaluation result."""

    report_json_path: Path
    report_text_path: Path
    distribution_summary: Dict[str, Dict[str, float]]
    confidence_summary: Dict[str, Any]
    has_labels: bool
    classification_metrics: Optional[Dict[str, Any]]
    dominant_class: str
    dominant_pct: float
    distribution_dominance_warning: bool


class ModelEvaluation:
    """Evaluate Stage 4 prediction artifacts."""

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        config: ModelEvaluationConfig,
        inference_artifact: ModelInferenceArtifact,
    ):
        """
        Method Name :   __init__
        Description :   Store Stage 5 configuration and Stage 4 artifact paths.

        Output      :   Initializes the ModelEvaluation instance.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            self.pipeline_config = pipeline_config
            self.config = config
            self.inference_artifact = inference_artifact
        except Exception as exc:
            logger.exception("Failed to initialize Stage 5 model evaluation.")
            raise exc

    @property
    def probability_columns(self) -> list[str]:
        return [f"prob_{name}" for name in ACTIVITY_CLASSES.values()]

    def read_predictions(self, predictions_csv: Path) -> pd.DataFrame:
        """
        Method Name :   read_predictions
        Description :   Read the Stage 4 prediction CSV.

        Output      :   Returns a prediction DataFrame.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            if not predictions_csv.exists():
                raise FileNotFoundError(f"Prediction CSV not found: {predictions_csv}")
            df = pd.read_csv(predictions_csv)
            if df.empty:
                raise ValueError(f"Prediction CSV is empty: {predictions_csv}")
            logger.info("Loaded %d predictions from %s", len(df), predictions_csv)
            return df
        except Exception as exc:
            logger.exception("Failed to read Stage 5 predictions.")
            raise exc

    def validate_prediction_contract(self, df: pd.DataFrame) -> None:
        """
        Method Name :   validate_prediction_contract
        Description :   Validate the prediction columns written by Stage 4.

        Output      :   Returns None when the prediction table is valid.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            missing = sorted(REQUIRED_COLUMNS - set(df.columns))
            if missing:
                raise ValueError(f"Prediction CSV missing required columns: {missing}")

            missing_probs = [c for c in self.probability_columns if c not in df.columns]
            if missing_probs:
                raise ValueError(
                    f"Prediction CSV missing probability columns: {missing_probs}"
                )

            numeric_cols = [
                "window_id",
                "predicted_class",
                "confidence",
                "entropy",
                "top2_margin",
                *self.probability_columns,
            ]
            numeric = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            if numeric.isna().any().any():
                bad_cols = numeric.columns[numeric.isna().any()].tolist()
                raise ValueError(f"Prediction CSV has non-numeric values in {bad_cols}")
            if not np.isfinite(numeric.to_numpy(dtype=np.float64)).all():
                raise ValueError("Prediction CSV contains NaN or inf numeric values.")

            pred_class = numeric["predicted_class"].astype(int)
            if not pred_class.between(0, len(ACTIVITY_CLASSES) - 1).all():
                raise ValueError(
                    "predicted_class values are outside the canonical range."
                )

            expected_names = pred_class.map(ACTIVITY_CLASSES).astype(str)
            actual_names = df["predicted_activity"].astype(str)
            mismatch = actual_names != expected_names
            if bool(mismatch.any()):
                row = int(np.flatnonzero(mismatch.to_numpy())[0])
                raise ValueError(
                    "predicted_class/predicted_activity mismatch at row "
                    f"{row}: class={pred_class.iloc[row]}, activity={actual_names.iloc[row]}"
                )

            confidence = numeric["confidence"]
            if not confidence.between(0.0, 1.0).all():
                raise ValueError("confidence values must be within [0, 1].")

            prob_sums = numeric[self.probability_columns].sum(axis=1).to_numpy()
            if not np.allclose(prob_sums, 1.0, atol=1e-4):
                raise ValueError("Probability columns do not sum to 1 per row.")

            df["predicted_class"] = pred_class
            df["confidence"] = confidence.astype(float)
        except Exception as exc:
            logger.exception("Stage 5 prediction contract validation failed.")
            raise exc

    def read_labels(
        self, labels_path: Optional[Path]
    ) -> Tuple[Optional[np.ndarray], bool]:
        """
        Method Name :   read_labels
        Description :   Read optional paired window labels for supervised metrics.

        Output      :   Returns labels and whether labeled evaluation is available.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            if labels_path is None:
                return None, False
            if not labels_path.exists():
                logger.warning("Labels file configured but not found: %s", labels_path)
                return None, False

            labels_raw = np.load(labels_path, allow_pickle=True)
            if labels_raw.ndim != 1:
                raise ValueError(f"Labels must be 1D, got shape {labels_raw.shape}")
            labels_float = labels_raw.astype(float)
            if not np.isfinite(labels_float).all():
                raise ValueError("Labels contain NaN or inf values.")
            labels = labels_raw.astype(int)
            if not np.isin(labels, list(ACTIVITY_CLASSES.keys())).all():
                raise ValueError(
                    "Labels contain class ids outside the canonical mapping."
                )
            return labels, True
        except Exception as exc:
            logger.exception("Failed to read Stage 5 labels.")
            raise exc

    def validate_label_alignment(
        self, labels: Optional[np.ndarray], n_predictions: int
    ) -> None:
        """
        Method Name :   validate_label_alignment
        Description :   Ensure labels and predictions are exactly paired.

        Output      :   Returns None when labels and predictions have equal length.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            if labels is not None and len(labels) != n_predictions:
                raise ValueError(
                    "Label/prediction length mismatch: "
                    f"labels={len(labels)}, predictions={n_predictions}. "
                    "Refusing to truncate because this can poison evaluation."
                )
        except Exception as exc:
            logger.exception("Stage 5 label alignment validation failed.")
            raise exc

    def evaluate_predictions(self) -> EvaluatePredictionsResponse:
        """
        Method Name :   evaluate_predictions
        Description :   Analyze prediction distribution, confidence, temporal behavior, and labels.

        Output      :   Returns an EvaluatePredictionsResponse.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            predictions_csv = Path(
                self.config.predictions_csv
                or self.inference_artifact.predictions_csv_path
            )
            output_dir = Path(
                self.config.output_dir
                or self.pipeline_config.outputs_dir / "evaluation"
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            labels_path = (
                Path(self.config.labels_path) if self.config.labels_path else None
            )

            df = self.read_predictions(predictions_csv)
            self.validate_prediction_contract(df)
            labels, has_labels = self.read_labels(labels_path)
            self.validate_label_alignment(labels, len(df))

            if has_labels:
                logger.info("Evaluation mode: LABELED (labels file: %s)", labels_path)
            else:
                logger.info(
                    "Evaluation mode: UNLABELED (distribution/confidence/temporal only)"
                )

            distribution = self._prediction_distribution(df)
            confidence = self._confidence_summary(df)
            report = {
                "timestamp": datetime.now().isoformat(),
                "n_predictions": int(len(df)),
                "has_labels": bool(has_labels),
                "distribution": distribution,
                "dominant_class": self._dominant_class(distribution),
                "dominant_pct": self._dominant_pct(distribution),
                "confidence": confidence,
                "uncertainty": self._uncertainty_summary(df),
                "temporal": self._temporal_summary(df),
                "classification_metrics": (
                    self._classification_metrics(df, labels) if has_labels else None
                ),
            }
            report["distribution_dominance_warning"] = bool(
                report["dominant_pct"]
                >= PostInferenceMonitoringConfig.dominant_class_critical_threshold
            )

            if report["distribution_dominance_warning"]:
                logger.warning(
                    "Stage 5 distribution dominance warning: %s at %.2f%%",
                    report["dominant_class"],
                    report["dominant_pct"],
                )

            json_path, text_path = self.save_reports(report, output_dir)
            return EvaluatePredictionsResponse(
                report_json_path=json_path,
                report_text_path=text_path,
                distribution_summary=distribution,
                confidence_summary=confidence,
                has_labels=has_labels,
                classification_metrics=report["classification_metrics"],
                dominant_class=str(report["dominant_class"]),
                dominant_pct=float(report["dominant_pct"]),
                distribution_dominance_warning=bool(
                    report["distribution_dominance_warning"]
                ),
            )
        except Exception as exc:
            logger.exception("Stage 5 prediction evaluation failed.")
            raise exc

    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
        """
        Method Name :   initiate_model_evaluation
        Description :   Start Stage 5 and convert the evaluation response into an artifact.

        Output      :   Returns a ModelEvaluationArtifact.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            logger.info("=" * 60)
            logger.info("STAGE 5 - Model Evaluation")
            logger.info("=" * 60)
            response = self.evaluate_predictions()
            artifact = ModelEvaluationArtifact(
                report_json_path=response.report_json_path,
                report_text_path=response.report_text_path,
                distribution_summary=response.distribution_summary,
                confidence_summary=response.confidence_summary,
                has_labels=response.has_labels,
                classification_metrics=response.classification_metrics,
                distribution_dominance_warning=response.distribution_dominance_warning,
                dominant_pct=response.dominant_pct,
                dominant_class=response.dominant_class,
            )
            logger.info(
                "Stage 5 complete: dominant=%s %.2f%%; labels=%s",
                artifact.dominant_class,
                artifact.dominant_pct or 0.0,
                "yes" if artifact.has_labels else "no",
            )
            return artifact
        except Exception as exc:
            logger.exception("Stage 5 model evaluation failed.")
            raise exc

    def save_reports(
        self, report: Dict[str, Any], output_dir: Path
    ) -> Tuple[Path, Path]:
        """
        Method Name :   save_reports
        Description :   Save the Stage 5 JSON and text reports.

        Output      :   Returns the JSON report path and text report path.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            timestamp = get_timestamp()
            json_path = output_dir / f"evaluation_{timestamp}.json"
            text_path = output_dir / f"evaluation_{timestamp}.txt"

            json_path.write_text(
                json.dumps(report, indent=2, default=str),
                encoding="utf-8",
            )
            text_path.write_text(self._text_report(report), encoding="utf-8")
            logger.info("Stage 5 reports written: %s, %s", json_path, text_path)
            return json_path, text_path
        except Exception as exc:
            logger.exception("Failed to save Stage 5 reports.")
            raise exc

    def _prediction_distribution(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        counts = df["predicted_activity"].value_counts()
        pct = df["predicted_activity"].value_counts(normalize=True) * 100.0
        return {
            str(activity): {
                "count": int(counts[activity]),
                "percentage": float(pct[activity]),
            }
            for activity in counts.index
        }

    @staticmethod
    def _dominant_class(distribution: Dict[str, Dict[str, float]]) -> str:
        return max(distribution.items(), key=lambda item: item[1]["count"])[0]

    @staticmethod
    def _dominant_pct(distribution: Dict[str, Dict[str, float]]) -> float:
        return float(max(v["percentage"] for v in distribution.values()))

    def _confidence_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        confidence = pd.to_numeric(df["confidence"], errors="raise")
        return {
            "mean": float(confidence.mean()),
            "std": float(confidence.std()),
            "min": float(confidence.min()),
            "max": float(confidence.max()),
            "median": float(confidence.median()),
            "q25": float(confidence.quantile(0.25)),
            "q75": float(confidence.quantile(0.75)),
            "per_class": {
                str(k): float(v)
                for k, v in (
                    df.groupby("predicted_activity")["confidence"]
                    .mean()
                    .sort_values(ascending=False)
                    .to_dict()
                    .items()
                )
            },
            "levels": {
                str(k): int(v) for k, v in df["confidence_level"].value_counts().items()
            },
        }

    def _uncertainty_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        uncertain_mask = (
            df["is_uncertain"].astype(str).str.lower().isin({"true", "1", "yes"})
        )
        uncertain = df[uncertain_mask]
        return {
            "count": int(len(uncertain)),
            "percentage": float(100.0 * len(uncertain) / len(df)),
            "by_class": {
                str(k): int(v)
                for k, v in uncertain["predicted_activity"].value_counts().items()
            },
        }

    def _temporal_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        activities = df["predicted_activity"].astype(str).tolist()
        transitions = sum(
            1 for i in range(1, len(activities)) if activities[i] != activities[i - 1]
        )

        longest_activity = activities[0]
        longest_length = 1
        current_activity = activities[0]
        current_length = 1
        longest_by_class: Dict[str, int] = {}
        for activity in activities[1:]:
            if activity == current_activity:
                current_length += 1
            else:
                longest_by_class[current_activity] = max(
                    longest_by_class.get(current_activity, 0), current_length
                )
                if current_length > longest_length:
                    longest_activity, longest_length = current_activity, current_length
                current_activity, current_length = activity, 1

        longest_by_class[current_activity] = max(
            longest_by_class.get(current_activity, 0), current_length
        )
        if current_length > longest_length:
            longest_activity, longest_length = current_activity, current_length

        return {
            "n_windows": int(len(activities)),
            "transitions": int(transitions),
            "transition_rate": (
                float(transitions / (len(activities) - 1))
                if len(activities) > 1
                else 0.0
            ),
            "longest_sequences": longest_by_class,
            "longest_sequence_activity": str(longest_activity),
            "longest_sequence_length": int(longest_length),
            "longest_sequence_duration_seconds": float(
                WINDOW_DURATION_SECONDS + (longest_length - 1) * WINDOW_STEP_SECONDS
            ),
            "window_duration_seconds": WINDOW_DURATION_SECONDS,
            "window_step_seconds": WINDOW_STEP_SECONDS,
        }

    def _classification_metrics(
        self, df: pd.DataFrame, labels: Optional[np.ndarray]
    ) -> Dict[str, Any]:
        if labels is None:
            raise ValueError("Cannot compute classification metrics without labels.")

        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            confusion_matrix,
            f1_score,
            precision_score,
            recall_score,
        )

        y_true = labels.astype(int)
        y_pred = df["predicted_class"].astype(int).to_numpy()
        ids = list(ACTIVITY_CLASSES.keys())
        names = [ACTIVITY_CLASSES[i] for i in ids]
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision_macro": float(
                precision_score(y_true, y_pred, average="macro", zero_division=0)
            ),
            "recall_macro": float(
                recall_score(y_true, y_pred, average="macro", zero_division=0)
            ),
            "f1_macro": float(
                f1_score(y_true, y_pred, average="macro", zero_division=0)
            ),
            "per_class": classification_report(
                y_true,
                y_pred,
                labels=ids,
                target_names=names,
                zero_division=0,
                output_dict=True,
            ),
            "confusion_matrix": confusion_matrix(y_true, y_pred, labels=ids).tolist(),
        }

    def _text_report(self, report: Dict[str, Any]) -> str:
        lines = [
            "=" * 70,
            "PREDICTION EVALUATION REPORT",
            f"Generated: {report['timestamp']}",
            "=" * 70,
            "",
            f"Label mode: {'LABELED' if report['has_labels'] else 'UNLABELED'}",
            f"Predictions: {report['n_predictions']}",
            f"Dominant class: {report['dominant_class']} ({report['dominant_pct']:.2f}%)",
            f"Distribution dominance warning: {report['distribution_dominance_warning']}",
            "",
            "ACTIVITY DISTRIBUTION",
            "-" * 40,
        ]
        for activity, values in report["distribution"].items():
            lines.append(
                f"{activity:20s}: {values['count']:5d} "
                f"({values['percentage']:5.1f}%)"
            )

        conf = report["confidence"]
        temporal = report["temporal"]
        lines.extend(
            [
                "",
                "CONFIDENCE STATISTICS",
                "-" * 40,
                f"Mean:   {100 * conf['mean']:.1f}%",
                f"Std:    {100 * conf['std']:.1f}%",
                f"Min:    {100 * conf['min']:.1f}%",
                f"Max:    {100 * conf['max']:.1f}%",
                "",
                "TEMPORAL SUMMARY",
                "-" * 40,
                f"Transitions: {temporal['transitions']}",
                f"Transition rate: {100 * temporal['transition_rate']:.1f}%",
                (
                    "Longest sequence: "
                    f"{temporal['longest_sequence_activity']} "
                    f"({temporal['longest_sequence_length']} windows, "
                    f"{temporal['longest_sequence_duration_seconds']:.1f}s)"
                ),
                "",
                "=" * 70,
            ]
        )
        return "\n".join(lines) + "\n"

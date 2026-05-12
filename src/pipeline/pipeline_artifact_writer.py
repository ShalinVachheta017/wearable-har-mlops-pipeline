"""Artifact and summary writing helpers for the production pipeline."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.entity.artifact_entity import PipelineResult
from src.logger import logging

logger = logging.getLogger(__name__)


class PipelineArtifactWriter:
    """Keeps filesystem artifact writing out of the pipeline orchestrator."""

    def __init__(self, artifacts_manager, pipeline_config):
        self.artifacts_manager = artifacts_manager
        self.pipeline_config = pipeline_config

    def record_ingestion(self, artifact) -> None:
        """
        Method Name :   record_ingestion
        Description :   Save Stage 1 output files and the stage completion summary.

        Output      :   Writes ingestion artifacts through ArtifactsManager.
        On Failure  :   Logs the error and raises the exception.
        """
        if artifact.fused_csv_path.exists():
            self.artifacts_manager.save_file(artifact.fused_csv_path, "data_ingestion")
        self.artifacts_manager.log_stage_completion(
            "ingestion",
            "SUCCESS",
            {
                "n_rows": artifact.n_rows,
                "n_columns": artifact.n_columns,
                "sampling_hz": artifact.sampling_hz,
            },
        )

    def record_validation(self, artifact) -> None:
        """
        Method Name :   record_validation
        Description :   Save Stage 2 validation report and status.

        Output      :   Writes validation_report.json and stage completion metadata.
        On Failure  :   Logs the error and raises the exception.
        """
        self.artifacts_manager.save_json(
            {
                "is_valid": artifact.is_valid,
                "errors": artifact.errors,
                "warnings": artifact.warnings,
                "stats": artifact.stats,
            },
            "validation",
            "validation_report.json",
        )
        self.artifacts_manager.log_stage_completion(
            "validation",
            "SUCCESS" if artifact.is_valid else "FAILED",
            {"n_errors": len(artifact.errors)},
        )

    def record_transformation(self, artifact) -> None:
        """
        Method Name :   record_transformation
        Description :   Save Stage 3 prepared arrays, metadata, and report.

        Output      :   Writes transformation artifacts and stage completion metadata.
        On Failure  :   Logs the error and raises the exception.
        """
        for path in (
            artifact.production_X_path,
            artifact.metadata_path,
            artifact.transformation_report_path,
        ):
            self._save_existing(path, "data_transformation")
        self.artifacts_manager.log_stage_completion(
            "transformation",
            "SUCCESS",
            {
                "n_windows": artifact.n_windows,
                "unit_conversion": artifact.unit_conversion_applied,
                "model_input_space": artifact.model_input_space,
                "normalization": artifact.normalization_applied,
                "gravity_removal": artifact.gravity_removal_applied,
            },
        )

    def record_inference(self, artifact) -> None:
        """
        Method Name :   record_inference
        Description :   Save Stage 4 prediction artifacts and inference summary.

        Output      :   Writes inference files, inference_summary.json, and stage metadata.
        On Failure  :   Logs the error and raises the exception.
        """
        for path in (
            artifact.predictions_csv_path,
            artifact.predictions_npy_path,
            artifact.probabilities_npy_path,
            artifact.metadata_json_path,
            artifact.inference_report_path,
        ):
            self._save_existing(path, "inference")

        n_pred = artifact.n_predictions
        t_sec = artifact.inference_time_seconds
        avg_ms = round((t_sec / n_pred) * 1000, 4) if n_pred > 0 else 0.0
        throughput_wps = round(n_pred / t_sec, 2) if t_sec > 0 else 0.0
        act_dist = artifact.activity_distribution or {}
        self.artifacts_manager.save_json(
            {
                "n_predictions": n_pred,
                "inference_time_seconds": t_sec,
                "throughput_windows_per_sec": throughput_wps,
                "avg_ms_per_window": avg_ms,
                "activity_distribution": act_dist,
                "activity_share": {
                    activity: round(count / n_pred, 4) if n_pred > 0 else 0.0
                    for activity, count in act_dist.items()
                },
                "confidence_stats": artifact.confidence_stats,
                "entropy_stats": artifact.entropy_stats,
                "top2_margin_stats": artifact.top2_margin_stats,
                "dominant_class": artifact.dominant_class,
                "dominant_pct": artifact.dominant_pct,
                "collapse_level": artifact.collapse_level,
                "model_version": artifact.model_version,
                "model_md5": artifact.model_md5,
                "inference_report_path": (
                    str(artifact.inference_report_path) if artifact.inference_report_path else None
                ),
            },
            "inference",
            "inference_summary.json",
        )
        self.artifacts_manager.log_stage_completion(
            "inference",
            "SUCCESS",
            {
                "n_predictions": n_pred,
                "inference_time_sec": t_sec,
                "throughput_windows_per_sec": throughput_wps,
                "avg_ms_per_window": avg_ms,
            },
        )

    def record_evaluation(self, artifact) -> None:
        """
        Method Name :   record_evaluation
        Description :   Save Stage 5 reports and evaluation summary.

        Output      :   Writes evaluation artifacts and stage completion metadata.
        On Failure  :   Logs the error and raises the exception.
        """
        for path in (artifact.report_json_path, artifact.report_text_path):
            self._save_existing(path, "evaluation")
        self.artifacts_manager.save_json(
            {
                "distribution_summary": artifact.distribution_summary,
                "confidence_summary": artifact.confidence_summary,
                "has_labels": artifact.has_labels,
                "classification_metrics": artifact.classification_metrics,
                "dominant_class": artifact.dominant_class,
                "dominant_pct": artifact.dominant_pct,
                "distribution_dominance_warning": artifact.distribution_dominance_warning,
            },
            "evaluation",
            "evaluation_summary.json",
        )
        self.artifacts_manager.log_stage_completion(
            "evaluation",
            "SUCCESS",
            {
                "mean_confidence": (
                    artifact.confidence_summary.get("mean", 0) if artifact.confidence_summary else 0
                ),
                "has_labels": artifact.has_labels,
            },
        )

    def record_monitoring(
        self,
        artifact,
        collapse_signals: Dict[str, Any],
        drift_chunked: Optional[Dict[str, Any]],
    ) -> None:
        """
        Method Name :   record_monitoring
        Description :   Save Stage 6 monitoring report and summary.

        Output      :   Writes monitoring artifacts and stage completion metadata.
        On Failure  :   Logs the error and raises the exception.
        """
        self._save_existing(artifact.report_path, "monitoring")
        self.artifacts_manager.save_json(
            {
                "overall_status": artifact.overall_status,
                "layer1_confidence": artifact.layer1_confidence,
                "layer2_temporal": artifact.layer2_temporal,
                "layer3_drift": artifact.layer3_drift,
                "collapse_signals": collapse_signals,
                "drift_monitor_chunked": drift_chunked,
            },
            "monitoring",
            "monitoring_summary.json",
        )
        self.artifacts_manager.log_stage_completion(
            "monitoring",
            artifact.overall_status,
            {
                "overall_status": artifact.overall_status,
                "confidence_status": artifact.layer1_confidence.get("status", "N/A"),
                "temporal_status": artifact.layer2_temporal.get("status", "N/A"),
                "drift_status": artifact.layer3_drift.get("status", "N/A"),
                "collapse_warning": collapse_signals.get("dominance_warning", False),
                "dominant_class": collapse_signals.get("dominant_class", ""),
                "dominant_pct": collapse_signals.get("dominant_pct", 0.0),
            },
        )

    def record_trigger(self, artifact, monitoring_artifact) -> None:
        """
        Method Name :   record_trigger
        Description :   Save Stage 7 trigger decision evidence.

        Output      :   Writes trigger_decision.json and stage completion metadata.
        On Failure  :   Logs the error and raises the exception.
        """
        collapse_signals = {}
        if monitoring_artifact and monitoring_artifact.monitoring_report:
            collapse_signals = monitoring_artifact.monitoring_report.get("collapse_signals", {})
        self.artifacts_manager.save_json(
            {
                "should_retrain": artifact.should_retrain,
                "action": artifact.action,
                "alert_level": artifact.alert_level,
                "reason": artifact.reasons[0] if artifact.reasons else "",
                "reasons": artifact.reasons,
                "cooldown_active": artifact.cooldown_active,
                "collapse_signals": collapse_signals,
            },
            "trigger",
            "trigger_decision.json",
        )
        self.artifacts_manager.log_stage_completion(
            "trigger",
            "SUCCESS",
            {
                "should_retrain": artifact.should_retrain,
                "action": artifact.action,
                "alert_level": artifact.alert_level,
                "n_reasons": len(artifact.reasons),
            },
        )

    def record_calibration(self, artifact, output_dir: Path) -> None:
        """
        Method Name :   record_calibration
        Description :   Save Stage 11 calibration artifacts and summary.

        Output      :   Writes calibration files and stage completion metadata.
        On Failure  :   Logs the error and raises the exception.
        """
        for filename in (
            "temperature.json",
            "calibration_report.json",
            "calibrated_probabilities.npy",
        ):
            self._save_existing(output_dir / filename, "calibration")
        self.artifacts_manager.log_stage_completion(
            "calibration",
            artifact.overall_status,
            {
                "overall_status": artifact.overall_status,
                "n_warnings": len(artifact.calibration_warnings),
            },
        )

    def save_result(self, result: PipelineResult) -> Path:
        """
        Method Name :   save_result
        Description :   Save the final PipelineResult as JSON.

        Output      :   Returns the written JSON path.
        On Failure  :   Logs the error and raises the exception.
        """
        log_dir = self.pipeline_config.logs_dir / "pipeline"
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / f"pipeline_result_{result.run_id}.json"
        data = dataclasses.asdict(result)
        path.write_text(json.dumps(self._to_json_safe(data), indent=2, default=str))
        logger.info("Pipeline result saved: %s", path)
        return path

    def _save_existing(self, path, stage_name: str) -> None:
        if path and Path(path).exists():
            self.artifacts_manager.save_file(Path(path), stage_name)

    def _to_json_safe(self, value):
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {key: self._to_json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._to_json_safe(item) for item in value]
        return value

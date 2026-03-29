"""
=============================================================================
HAR MLOps — Production Pipeline Orchestrator
=============================================================================

Clean ~200-line orchestrator that delegates ALL work to component classes.
Follows the reference pattern from vikashishere/YT-MLops-Proj1.

10 Stages:
    1  Data Ingestion           (Excel/CSV → fused CSV)
    2  Data Validation          (schema + range checks)
    3  Data Transformation      (CSV → windowed .npy)
    4  Model Inference          (.npy + model → predictions)
    5  Model Evaluation         (confidence / distribution / ECE)
    6  Post-Inference Monitoring (3-layer: confidence, temporal, drift)
    7  Trigger Evaluation       (retraining decision)
  ── retraining cycle (optional, stages 8-10) ──
    8  Model Retraining         (standard / AdaBN / pseudo-label)
    9  Model Registration       (version, deploy, rollback)
   10  Baseline Update          (rebuild drift baselines)
"""

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.entity.artifact_entity import PipelineResult
from src.entity.config_entity import (
    BaselineUpdateConfig,
    CalibrationUncertaintyConfig,
    CurriculumPseudoLabelingConfig,
    DataIngestionConfig,
    DataTransformationConfig,
    DataValidationConfig,
    ModelEvaluationConfig,
    ModelInferenceConfig,
    ModelRegistrationConfig,
    ModelRetrainingConfig,
    PipelineConfig,
    PostInferenceMonitoringConfig,
    SensorPlacementConfig,
    TriggerEvaluationConfig,
    WassersteinDriftConfig,
)
from src.exceptions import DataValidationError

# Import centralized logger and artifacts manager
from src.logger import logging
from src.utils.artifacts_manager import ArtifactsManager

logger = logging.getLogger(__name__)

# Ordered list of ALL stages
ALL_STAGES = [
    "ingestion",
    "validation",
    "transformation",
    "inference",
    "evaluation",
    "monitoring",
    "trigger",
    "retraining",
    "registration",
    "baseline_update",
    "calibration",
    "wasserstein_drift",
    "curriculum_pseudo_labeling",
    "sensor_placement",
]
RETRAIN_STAGES = {"retraining", "registration", "baseline_update"}
ADVANCED_STAGES = {
    "calibration",
    "wasserstein_drift",
    "curriculum_pseudo_labeling",
    "sensor_placement",
}


class ProductionPipeline:
    """Orchestrates the full HAR MLOps pipeline."""

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        *,
        ingestion_config: Optional[DataIngestionConfig] = None,
        validation_config: Optional[DataValidationConfig] = None,
        transformation_config: Optional[DataTransformationConfig] = None,
        inference_config: Optional[ModelInferenceConfig] = None,
        evaluation_config: Optional[ModelEvaluationConfig] = None,
        monitoring_config: Optional[PostInferenceMonitoringConfig] = None,
        trigger_config: Optional[TriggerEvaluationConfig] = None,
        retraining_config: Optional[ModelRetrainingConfig] = None,
        registration_config: Optional[ModelRegistrationConfig] = None,
        baseline_config: Optional[BaselineUpdateConfig] = None,
        calibration_config: Optional[CalibrationUncertaintyConfig] = None,
        wasserstein_config: Optional[WassersteinDriftConfig] = None,
        curriculum_config: Optional[CurriculumPseudoLabelingConfig] = None,
        sensor_placement_config: Optional[SensorPlacementConfig] = None,
    ):
        self.pipeline_config = pipeline_config
        self.ingestion_config = ingestion_config or DataIngestionConfig()
        self.validation_config = validation_config or DataValidationConfig()
        self.transformation_config = transformation_config or DataTransformationConfig()
        self.inference_config = inference_config or ModelInferenceConfig()
        self.evaluation_config = evaluation_config or ModelEvaluationConfig()
        self.monitoring_config = monitoring_config or PostInferenceMonitoringConfig()
        self.trigger_config = trigger_config or TriggerEvaluationConfig()
        self.retraining_config = retraining_config or ModelRetrainingConfig()
        self.registration_config = registration_config or ModelRegistrationConfig()
        self.baseline_config = baseline_config or BaselineUpdateConfig()
        self.calibration_config = calibration_config or CalibrationUncertaintyConfig()
        self.wasserstein_config = wasserstein_config or WassersteinDriftConfig()
        self.curriculum_config = curriculum_config or CurriculumPseudoLabelingConfig()
        self.sensor_placement_config = sensor_placement_config or SensorPlacementConfig()

        # Initialize artifacts manager
        self.artifacts_manager = ArtifactsManager()

    # ================================================================== #
    def run(
        self,
        stages: Optional[List[str]] = None,
        skip_ingestion: bool = False,
        skip_validation: bool = False,
        continue_on_failure: bool = False,
        enable_retrain: bool = False,
        enable_advanced: bool = False,
        update_baseline: bool = False,
    ) -> PipelineResult:
        """
        Execute the pipeline.

        Parameters
        ----------
        stages : list[str], optional
            Subset of stages to run.  Default → stages 1-7;
            add "retraining" etc. for the retrain cycle.
        skip_ingestion : bool
            Skip stage 1.
        skip_validation : bool
            Skip stage 2.
        continue_on_failure : bool
            Log errors and continue to next stage instead of aborting.
        enable_retrain : bool
            Include stages 8-10 even when `stages` is None.
        enable_advanced : bool
            Include stages 11-14 (calibration, wasserstein_drift,
            curriculum_pseudo_labeling, sensor_placement).
        update_baseline : bool
            When True, promote the rebuilt baseline to the shared models/ path
            that monitoring reads.  Default False: baseline is written only as
            an MLflow artifact (safe governance default — no silent overwrites).
        """
        result = PipelineResult(
            run_id=self.pipeline_config.timestamp,
            start_time=datetime.now().isoformat(),
        )

        # Determine which stages to run
        if stages is not None:
            run_stages = [s for s in ALL_STAGES if s in stages]
        else:
            run_stages = [
                s for s in ALL_STAGES if s not in RETRAIN_STAGES and s not in ADVANCED_STAGES
            ]
            if enable_retrain:
                run_stages.extend(s for s in ALL_STAGES if s in RETRAIN_STAGES)
            if enable_advanced:
                run_stages.extend(s for s in ALL_STAGES if s in ADVANCED_STAGES)

        if skip_ingestion and "ingestion" in run_stages:
            run_stages.remove("ingestion")
            result.stages_skipped.append("ingestion")
        if skip_validation and "validation" in run_stages:
            run_stages.remove("validation")
            result.stages_skipped.append("validation")

        # Initialize artifacts directory for this run
        run_dir = self.artifacts_manager.initialize()

        logger.info("=" * 70)
        logger.info("HAR MLOPS PRODUCTION PIPELINE - EXECUTION START")
        logger.info("=" * 70)
        logger.info("Run ID: %s", self.pipeline_config.timestamp)
        logger.info("Artifacts Directory: %s", run_dir)
        logger.info("Data Source: %s", self.pipeline_config.data_raw_dir)
        logger.info("Preprocessing Settings:")
        logger.info(
            "  - Unit Conversion (milliG→m/s²): %s",
            "ENABLED" if self.transformation_config.enable_unit_conversion else "DISABLED",
        )
        logger.info(
            "  - Gravity Removal: %s",
            "ENABLED" if self.transformation_config.enable_gravity_removal else "DISABLED",
        )
        logger.info(
            "  - Calibration: %s",
            "ENABLED" if self.transformation_config.enable_calibration else "DISABLED",
        )
        logger.info(
            "  - Normalization: %s (%s)",
            "ENABLED" if self.transformation_config.enable_normalization else "DISABLED",
            self.transformation_config.normalization_variant,
        )
        logger.info("Pipeline stages: %s", run_stages)
        logger.info("=" * 70)

        # Holders for cross-stage artifacts
        ingestion_art = None
        validation_art = None
        transformation_art = None
        inference_art = None
        evaluation_art = None
        monitoring_art = None
        trigger_art = None
        retraining_art = None
        registration_art = None
        baseline_art = None
        collapse_signals = {}
        goto_cleanup = False

        # MLflow tracking (optional — wraps entire run)
        mlflow_tracker = self._init_mlflow()

        for stage in run_stages:
            if goto_cleanup:
                break
            try:
                if stage == "ingestion":
                    from src.components.data_ingestion import DataIngestion

                    comp = DataIngestion(self.pipeline_config, self.ingestion_config)
                    ingestion_art = comp.initiate_data_ingestion()
                    result.ingestion = ingestion_art

                    # Save artifacts
                    if ingestion_art.fused_csv_path.exists():
                        self.artifacts_manager.save_file(
                            ingestion_art.fused_csv_path, "data_ingestion"
                        )
                    self.artifacts_manager.log_stage_completion(
                        "ingestion",
                        "SUCCESS",
                        {
                            "n_rows": ingestion_art.n_rows,
                            "n_columns": ingestion_art.n_columns,
                            "sampling_hz": ingestion_art.sampling_hz,
                        },
                    )

                elif stage == "validation":
                    if ingestion_art is None:
                        ingestion_art = self._make_fallback_ingestion_artifact()
                    from src.components.data_validation import DataValidation

                    comp = DataValidation(
                        self.pipeline_config, self.validation_config, ingestion_art
                    )
                    validation_art = comp.initiate_data_validation()
                    result.validation = validation_art

                    # Save artifacts
                    self.artifacts_manager.save_json(
                        {
                            "is_valid": validation_art.is_valid,
                            "errors": validation_art.errors,
                            "warnings": validation_art.warnings,
                        },
                        "validation",
                        "validation_report.json",
                    )
                    self.artifacts_manager.log_stage_completion(
                        "validation",
                        "SUCCESS" if validation_art.is_valid else "FAILED",
                        {"n_errors": len(validation_art.errors)},
                    )

                    if not validation_art.is_valid:
                        result.stages_failed.append("validation")
                        raise DataValidationError(
                            f"Data validation failed with {len(validation_art.errors)} "
                            f"error(s): {validation_art.errors}. Pipeline aborted to prevent "
                            "invalid data from reaching Stage 3. Fix the source data or "
                            "relax DataValidationConfig thresholds."
                        )

                elif stage == "transformation":
                    if ingestion_art is None:
                        ingestion_art = self._make_fallback_ingestion_artifact()
                    from src.components.data_transformation import DataTransformation

                    comp = DataTransformation(
                        self.pipeline_config,
                        self.transformation_config,
                        ingestion_art,
                        validation_art,
                    )
                    transformation_art = comp.initiate_data_transformation()
                    result.transformation = transformation_art

                    # Save artifacts
                    if transformation_art.production_X_path.exists():
                        self.artifacts_manager.save_file(
                            transformation_art.production_X_path, "data_transformation"
                        )
                    if (
                        transformation_art.metadata_path
                        and transformation_art.metadata_path.exists()
                    ):
                        self.artifacts_manager.save_file(
                            transformation_art.metadata_path, "data_transformation"
                        )
                    self.artifacts_manager.log_stage_completion(
                        "transformation",
                        "SUCCESS",
                        {
                            "n_windows": transformation_art.n_windows,
                            "unit_conversion": transformation_art.unit_conversion_applied,
                            "gravity_removal": transformation_art.gravity_removal_applied,
                        },
                    )

                elif stage == "inference":
                    if transformation_art is None:
                        transformation_art = self._make_fallback_transformation_artifact()
                    from src.components.model_inference import ModelInference

                    comp = ModelInference(
                        self.pipeline_config,
                        self.inference_config,
                        transformation_art,
                    )
                    inference_art = comp.initiate_model_inference()
                    result.inference = inference_art

                    # Save artifacts
                    if (
                        inference_art.predictions_csv_path
                        and inference_art.predictions_csv_path.exists()
                    ):
                        self.artifacts_manager.save_file(
                            inference_art.predictions_csv_path, "inference"
                        )
                    if (
                        inference_art.predictions_npy_path
                        and inference_art.predictions_npy_path.exists()
                    ):
                        self.artifacts_manager.save_file(
                            inference_art.predictions_npy_path, "inference"
                        )
                    if (
                        inference_art.probabilities_npy_path
                        and inference_art.probabilities_npy_path.exists()
                    ):
                        self.artifacts_manager.save_file(
                            inference_art.probabilities_npy_path, "inference"
                        )

                    # Save inference summary as JSON
                    n_pred = inference_art.n_predictions
                    t_sec = inference_art.inference_time_seconds
                    avg_ms = round((t_sec / n_pred) * 1000, 4) if n_pred > 0 else 0.0
                    throughput_wps = round(n_pred / t_sec, 2) if t_sec > 0 else 0.0
                    act_dist = inference_art.activity_distribution or {}
                    per_activity_share = {
                        act: round(cnt / n_pred, 4) if n_pred > 0 else 0.0
                        for act, cnt in act_dist.items()
                    }
                    self.artifacts_manager.save_json(
                        {
                            "n_predictions": n_pred,
                            "inference_time_seconds": t_sec,
                            "throughput_windows_per_sec": throughput_wps,
                            "avg_ms_per_window": avg_ms,
                            "activity_distribution": act_dist,
                            "activity_share": per_activity_share,
                            "confidence_stats": inference_art.confidence_stats,
                            "model_version": inference_art.model_version,
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

                elif stage == "evaluation":
                    if inference_art is None:
                        raise ValueError("No inference artifact — run inference first.")
                    from src.components.model_evaluation import ModelEvaluation

                    comp = ModelEvaluation(
                        self.pipeline_config,
                        self.evaluation_config,
                        inference_art,
                    )
                    evaluation_art = comp.initiate_model_evaluation()
                    result.evaluation = evaluation_art
                    collapse_signals = self._extract_collapse_signals(evaluation_art)

                    # Save artifacts
                    if evaluation_art.report_json_path and evaluation_art.report_json_path.exists():
                        self.artifacts_manager.save_file(
                            evaluation_art.report_json_path, "evaluation"
                        )
                    if evaluation_art.report_text_path and evaluation_art.report_text_path.exists():
                        self.artifacts_manager.save_file(
                            evaluation_art.report_text_path, "evaluation"
                        )

                    # Save evaluation summary
                    self.artifacts_manager.save_json(
                        {
                            "distribution_summary": evaluation_art.distribution_summary,
                            "confidence_summary": evaluation_art.confidence_summary,
                            "has_labels": evaluation_art.has_labels,
                            "classification_metrics": evaluation_art.classification_metrics,
                        },
                        "evaluation",
                        "evaluation_summary.json",
                    )

                    self.artifacts_manager.log_stage_completion(
                        "evaluation",
                        "SUCCESS",
                        {
                            "mean_confidence": (
                                evaluation_art.confidence_summary.get("mean", 0)
                                if evaluation_art.confidence_summary
                                else 0
                            ),
                            "has_labels": evaluation_art.has_labels,
                        },
                    )

                elif stage == "monitoring":
                    if inference_art is None:
                        raise ValueError("No inference artifact — run inference first.")
                    from src.components.post_inference_monitoring import PostInferenceMonitoring

                    comp = PostInferenceMonitoring(
                        self.pipeline_config,
                        self.monitoring_config,
                        inference_art,
                        transformation_art,
                    )
                    monitoring_art = comp.initiate_post_inference_monitoring()
                    result.monitoring = monitoring_art

                    # Propagate Stage 5 collapse indicators into Stage 6/7 flow.
                    if collapse_signals:
                        if monitoring_art.monitoring_report is None:
                            monitoring_art.monitoring_report = {}
                        monitoring_art.monitoring_report["collapse_signals"] = collapse_signals

                        # Keep the persisted monitoring report in sync with runtime enrichment.
                        if monitoring_art.report_path:
                            try:
                                Path(monitoring_art.report_path).write_text(
                                    json.dumps(monitoring_art.monitoring_report, indent=2),
                                    encoding="utf-8",
                                )
                            except Exception as exc:
                                logger.warning(
                                    "Could not update monitoring report with collapse signals: %s",
                                    exc,
                                )

                    # Save monitoring artifacts
                    if monitoring_art.report_path and monitoring_art.report_path.exists():
                        self.artifacts_manager.save_file(monitoring_art.report_path, "monitoring")
                    self.artifacts_manager.save_json(
                        {
                            "overall_status": monitoring_art.overall_status,
                            "layer1_confidence": monitoring_art.layer1_confidence,
                            "layer2_temporal": monitoring_art.layer2_temporal,
                            "layer3_drift": monitoring_art.layer3_drift,
                            "collapse_signals": collapse_signals,
                        },
                        "monitoring",
                        "monitoring_summary.json",
                    )
                    self.artifacts_manager.log_stage_completion(
                        "monitoring",
                        monitoring_art.overall_status,
                        {
                            "overall_status": monitoring_art.overall_status,
                            "confidence_status": monitoring_art.layer1_confidence.get(
                                "status", "N/A"
                            ),
                            "temporal_status": monitoring_art.layer2_temporal.get("status", "N/A"),
                            "drift_status": monitoring_art.layer3_drift.get("status", "N/A"),
                            "collapse_warning": collapse_signals.get("dominance_warning", False),
                            "dominant_class": collapse_signals.get("dominant_class", ""),
                            "dominant_pct": collapse_signals.get("dominant_pct", 0.0),
                        },
                    )

                elif stage == "trigger":
                    if monitoring_art is None:
                        raise ValueError("No monitoring artifact — run monitoring first.")
                    from src.components.trigger_evaluation import TriggerEvaluation

                    comp = TriggerEvaluation(
                        self.pipeline_config,
                        self.trigger_config,
                        monitoring_art,
                    )
                    trigger_art = comp.initiate_trigger_evaluation()
                    result.trigger = trigger_art

                    # Save trigger artifacts
                    self.artifacts_manager.save_json(
                        {
                            "should_retrain": trigger_art.should_retrain,
                            "action": trigger_art.action,
                            "alert_level": trigger_art.alert_level,
                            "reason": trigger_art.reasons[0] if trigger_art.reasons else "",
                            "reasons": trigger_art.reasons,
                            "cooldown_active": trigger_art.cooldown_active,
                            "collapse_signals": (
                                monitoring_art.monitoring_report.get("collapse_signals", {})
                                if monitoring_art and monitoring_art.monitoring_report
                                else {}
                            ),
                        },
                        "trigger",
                        "trigger_decision.json",
                    )
                    self.artifacts_manager.log_stage_completion(
                        "trigger",
                        "SUCCESS",
                        {
                            "should_retrain": trigger_art.should_retrain,
                            "action": trigger_art.action,
                            "alert_level": trigger_art.alert_level,
                            "n_reasons": len(trigger_art.reasons),
                        },
                    )

                elif stage == "retraining":
                    force_retrain = getattr(self.pipeline_config, "force_retraining", False)
                    if not force_retrain and (
                        trigger_art is None or not trigger_art.should_retrain
                    ):
                        logger.info(
                            "Stages 8-10 SKIPPED — trigger decision is REVIEW with should_retrain=False. Unlabeled production data requires human review before retraining. Retraining stages were requested but not executed because the retrain gate was not satisfied."
                        )
                        retraining_art = None
                        registration_art = None
                        baseline_art = None
                        goto_cleanup = True
                        continue

                    from src.components.model_retraining import ModelRetraining

                    comp = ModelRetraining(
                        self.pipeline_config,
                        self.retraining_config,
                        trigger_art,
                        transformation_art,
                    )
                    retraining_art = comp.initiate_model_retraining()
                    result.retraining = retraining_art

                elif stage == "registration":
                    if retraining_art is None:
                        logger.info("Stage 9 SKIPPED — no retraining artifact.")
                        continue
                    from src.components.model_registration import ModelRegistration

                    comp = ModelRegistration(
                        self.pipeline_config,
                        self.registration_config,
                        retraining_art,
                        evaluation_art,
                    )
                    registration_art = comp.initiate_model_registration()
                    result.registration = registration_art

                elif stage == "baseline_update":
                    if retraining_art is None:
                        logger.info("Stage 10 SKIPPED — no retraining artifact.")
                        continue
                    from src.components.baseline_update import BaselineUpdate

                    # Governance: only promote to shared baseline when explicitly requested
                    self.baseline_config.promote_to_shared = update_baseline
                    comp = BaselineUpdate(
                        self.pipeline_config,
                        self.baseline_config,
                        retraining_art,
                    )
                    baseline_art = comp.initiate_baseline_update()
                    result.baseline_update = baseline_art

                elif stage == "calibration":
                    if inference_art is None:
                        raise ValueError("No inference artifact — run inference first.")
                    from src.components.calibration_uncertainty import CalibrationUncertainty

                    comp = CalibrationUncertainty(
                        self.pipeline_config,
                        self.calibration_config,
                        inference_art,
                    )
                    calibration_art = comp.initiate_calibration()
                    result.calibration = calibration_art
                    self.artifacts_manager.log_stage_completion(
                        "calibration",
                        "SUCCESS",
                        {
                            "overall_status": calibration_art.overall_status,
                            "n_warnings": len(calibration_art.calibration_warnings),
                        },
                    )

                elif stage == "wasserstein_drift":
                    if transformation_art is None:
                        transformation_art = self._make_fallback_transformation_artifact()
                    from src.components.wasserstein_drift import WassersteinDrift

                    comp = WassersteinDrift(
                        self.pipeline_config,
                        self.wasserstein_config,
                        transformation_art,
                        monitoring_art,
                    )
                    wasserstein_art = comp.initiate_wasserstein_drift()
                    result.wasserstein_drift = wasserstein_art
                    self.artifacts_manager.log_stage_completion(
                        "wasserstein_drift",
                        "SUCCESS",
                        {
                            "overall_status": wasserstein_art.overall_status,
                            "n_channels_warn": wasserstein_art.n_channels_warn,
                            "n_channels_critical": wasserstein_art.n_channels_critical,
                        },
                    )

                elif stage == "curriculum_pseudo_labeling":
                    if transformation_art is None:
                        transformation_art = self._make_fallback_transformation_artifact()
                    from src.components.curriculum_pseudo_labeling import CurriculumPseudoLabeling

                    comp = CurriculumPseudoLabeling(
                        self.pipeline_config,
                        self.curriculum_config,
                        transformation_art,
                    )
                    curriculum_art = comp.initiate_curriculum_training()
                    result.curriculum_pseudo_labeling = curriculum_art
                    self.artifacts_manager.log_stage_completion(
                        "curriculum_pseudo_labeling",
                        "SUCCESS",
                        {
                            "total_pseudo_labeled": curriculum_art.total_pseudo_labeled,
                            "best_val_accuracy": curriculum_art.best_val_accuracy,
                        },
                    )

                elif stage == "sensor_placement":
                    if transformation_art is None:
                        transformation_art = self._make_fallback_transformation_artifact()
                    from src.components.sensor_placement import SensorPlacement

                    comp = SensorPlacement(
                        self.pipeline_config,
                        self.sensor_placement_config,
                        transformation_art,
                    )
                    sensor_art = comp.initiate_sensor_placement()
                    result.sensor_placement = sensor_art
                    self.artifacts_manager.log_stage_completion(
                        "sensor_placement",
                        "SUCCESS",
                        {
                            "detected_hand": sensor_art.detected_hand,
                            "detection_confidence": sensor_art.detection_confidence,
                        },
                    )

                result.stages_completed.append(stage)
                logger.info("✓ Stage '%s' completed.", stage)

                # Log stage metrics to MLflow
                if mlflow_tracker:
                    self._log_stage_to_mlflow(mlflow_tracker, stage, result)

            except DataValidationError:
                # Data-quality errors are always fatal — never swallow, never continue.
                # stages_failed was already appended inside the validation block.
                raise

            except Exception as e:
                logger.error("✗ Stage '%s' FAILED: %s", stage, e)
                logger.debug(traceback.format_exc())
                result.stages_failed.append(stage)
                if not continue_on_failure:
                    break

        # Finalise
        result.end_time = datetime.now().isoformat()
        result.overall_status = (
            "SUCCESS"
            if not result.stages_failed
            else "PARTIAL" if result.stages_completed else "FAILED"
        )

        # Finalize artifacts
        self.artifacts_manager.finalize()

        self._save_result(result)

        if mlflow_tracker:
            self._end_mlflow(mlflow_tracker, result)

        logger.info("=" * 60)
        logger.info(
            "Pipeline finished: %s  (completed=%d  failed=%d  skipped=%d)",
            result.overall_status,
            len(result.stages_completed),
            len(result.stages_failed),
            len(result.stages_skipped),
        )
        logger.info("=" * 60)

        return result

    # ================================================================== #
    # Helpers
    # ================================================================== #

    @staticmethod
    def _as_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y"}
        return bool(value)

    def _extract_collapse_signals(self, evaluation_art) -> Dict:
        """Extract collapse-related fields from Stage 5 artifact/report JSON.

        Supports both underscored and non-underscored key variants.
        """
        signals: Dict[str, Any] = {
            "dominance_warning": False,
            "dominant_class": None,
            "dominant_pct": None,
            "mean_confidence": None,
            "transition_rate": None,
            "longest_sequence_length": None,
        }

        # From the typed artifact
        signals["dominance_warning"] = self._as_bool(
            getattr(evaluation_art, "distribution_dominance_warning", False)
        )
        dist = getattr(evaluation_art, "distribution_summary", {}) or {}
        conf = getattr(evaluation_art, "confidence_summary", {}) or {}

        # Read from typed artifact fields (reliable path).
        signals["dominant_pct"] = getattr(evaluation_art, "dominant_pct", None)
        signals["dominant_class"] = getattr(evaluation_art, "dominant_class", None)

        # Fallback to distribution summary only when typed fields are missing.
        if signals["dominant_class"] is None:
            signals["dominant_class"] = dist.get("_dominant_class")
            if signals["dominant_class"] is None:
                signals["dominant_class"] = dist.get("dominant_class")

        if signals["dominant_pct"] is None:
            signals["dominant_pct"] = dist.get("_dominant_pct")
            if signals["dominant_pct"] is None:
                signals["dominant_pct"] = dist.get("dominant_pct")

        signals["mean_confidence"] = conf.get("mean") or conf.get("mean_confidence")

        # Infer dominant class/pct when summary only contains class buckets.
        if signals["dominant_class"] is None and dist:
            class_entries = {
                k: v for k, v in dist.items() if isinstance(v, dict) and "percentage" in v
            }
            if class_entries:
                dominant = max(class_entries.items(), key=lambda kv: kv[1].get("percentage", 0.0))
                signals["dominant_class"] = dominant[0]
                if signals["dominant_pct"] is None:
                    signals["dominant_pct"] = dominant[1].get("percentage")

        # From Stage 5 JSON report (contains underscore-prefixed internals)
        report_path = getattr(evaluation_art, "report_json_path", None)
        if report_path and Path(report_path).exists():
            try:
                payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
                d = payload.get("distribution", {})
                t = payload.get("temporal", {})
                c = payload.get("confidence", {})

                if "_distribution_dominance_warning" in d:
                    signals["dominance_warning"] = self._as_bool(
                        d.get("_distribution_dominance_warning")
                    )
                elif "distribution_dominance_warning" in d:
                    signals["dominance_warning"] = self._as_bool(
                        d.get("distribution_dominance_warning")
                    )

                # JSON fallback only when artifact-derived values are still missing.
                if signals["dominant_class"] is None:
                    signals["dominant_class"] = d.get("_dominant_class")
                    if signals["dominant_class"] is None:
                        signals["dominant_class"] = d.get("dominant_class")

                if signals["dominant_pct"] is None:
                    signals["dominant_pct"] = d.get("_dominant_pct")
                    if signals["dominant_pct"] is None:
                        signals["dominant_pct"] = d.get("dominant_pct")

                if signals["mean_confidence"] is None:
                    signals["mean_confidence"] = c.get("mean") or c.get("mean_confidence")

                signals["transition_rate"] = t.get("transition_rate", signals["transition_rate"])
                if "longest_sequence_length" in t:
                    signals["longest_sequence_length"] = t.get("longest_sequence_length")
                elif "longest_sequences" in t and isinstance(t["longest_sequences"], dict):
                    seq_values = [v for v in t["longest_sequences"].values() if isinstance(v, (int, float))]
                    if seq_values:
                        signals["longest_sequence_length"] = max(seq_values)
            except Exception as exc:
                logger.warning("Could not parse Stage 5 evaluation report for collapse signals: %s", exc)

        # Normalize numeric fields
        for key in ("dominant_pct", "mean_confidence", "transition_rate", "longest_sequence_length"):
            try:
                if signals[key] is not None:
                    signals[key] = float(signals[key])
            except Exception:
                pass

        return signals

    def _make_fallback_ingestion_artifact(self):
        """Create a synthetic ingestion artifact pointing to existing CSV."""
        from src.entity.artifact_entity import DataIngestionArtifact

        csv = self.pipeline_config.data_processed_dir / "sensor_fused_50Hz.csv"
        if not csv.exists():
            csv = self.ingestion_config.input_csv or csv
        return DataIngestionArtifact(
            fused_csv_path=Path(csv),
            n_rows=0,
            n_columns=0,
            sampling_hz=50,
            ingestion_timestamp=datetime.now().isoformat(),
            source_type="fallback",
        )

    def _make_fallback_transformation_artifact(self):
        """Create a synthetic transformation artifact pointing to existing .npy."""
        from src.entity.artifact_entity import DataTransformationArtifact

        npy = self.pipeline_config.data_prepared_dir / "production_X.npy"
        return DataTransformationArtifact(
            production_X_path=npy,
            metadata_path=self.pipeline_config.data_prepared_dir / "production_metadata.json",
            n_windows=0,
            window_size=200,
            unit_conversion_applied=False,
            preprocessing_timestamp=datetime.now().isoformat(),
        )

    def _save_result(self, result: PipelineResult):
        """Persist pipeline result as JSON."""
        log_dir = self.pipeline_config.logs_dir / "pipeline"
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / f"pipeline_result_{self.pipeline_config.timestamp}.json"

        # Convert dataclasses to dicts
        import dataclasses

        data = dataclasses.asdict(result)

        # Pathlib → str
        def _convert(obj):
            if isinstance(obj, Path):
                return str(obj)
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_convert(i) for i in obj]
            return obj

        with open(path, "w") as f:
            json.dump(_convert(data), f, indent=2, default=str)
        logger.info("Pipeline result saved: %s", path)

    # ── MLflow helpers ─────────────────────────────────────────────────
    def _init_mlflow(self):
        try:
            from src.mlflow_tracking import MLflowTracker

            tracker = MLflowTracker(experiment_name="har-production-pipeline")
            # Properly use context manager with explicit tracking
            tracker._run_context = tracker.start_run(
                run_name=f"pipeline_{self.pipeline_config.timestamp}",
                tags={"pipeline": "production", "version": "2.0"},
            )
            # Enter the context
            tracker._active_run = tracker._run_context.__enter__()
            return tracker
        except Exception as e:
            logger.warning("MLflow initialization failed (continuing without tracking): %s", e)
            return None

    def _log_stage_to_mlflow(self, tracker, stage, result):
        try:
            metrics = {}

            # Ingestion metrics
            if stage == "ingestion" and result.ingestion:
                metrics["ingestion_n_rows"] = result.ingestion.n_rows
                metrics["ingestion_n_columns"] = result.ingestion.n_columns
                metrics["ingestion_sampling_hz"] = result.ingestion.sampling_hz

            # Validation metrics
            elif stage == "validation" and result.validation:
                metrics["validation_is_valid"] = 1.0 if result.validation.is_valid else 0.0
                metrics["validation_n_errors"] = len(result.validation.errors)
                metrics["validation_n_warnings"] = len(result.validation.warnings)

            # Transformation metrics
            elif stage == "transformation" and result.transformation:
                metrics["transformation_n_windows"] = result.transformation.n_windows
                metrics["transformation_window_size"] = result.transformation.window_size
                metrics["transformation_unit_conversion"] = (
                    1.0 if result.transformation.unit_conversion_applied else 0.0
                )
                metrics["transformation_gravity_removal"] = (
                    1.0 if result.transformation.gravity_removal_applied else 0.0
                )

            # Inference metrics - comprehensive
            elif stage == "inference" and result.inference:
                metrics["inference_n_predictions"] = result.inference.n_predictions
                metrics["inference_time_seconds"] = result.inference.inference_time_seconds
                metrics["inference_speed_windows_per_sec"] = result.inference.n_predictions / max(
                    result.inference.inference_time_seconds, 0.001
                )

                # Confidence statistics
                conf_stats = result.inference.confidence_stats or {}
                metrics["inference_mean_confidence"] = conf_stats.get("mean", 0.0)
                metrics["inference_std_confidence"] = conf_stats.get("std", 0.0)
                metrics["inference_min_confidence"] = conf_stats.get("min", 0.0)
                metrics["inference_max_confidence"] = conf_stats.get("max", 0.0)
                metrics["inference_median_confidence"] = conf_stats.get("median", 0.0)
                metrics["inference_uncertain_count"] = conf_stats.get("n_uncertain", 0)
                metrics["inference_uncertain_pct"] = (
                    conf_stats.get("n_uncertain", 0) / max(result.inference.n_predictions, 1) * 100
                )

                # Activity distribution - count of unique activities
                if result.inference.activity_distribution:
                    metrics["inference_n_activities_detected"] = len(
                        result.inference.activity_distribution
                    )
                    # Log dominant activity percentage
                    total = sum(result.inference.activity_distribution.values())
                    max_count = (
                        max(result.inference.activity_distribution.values())
                        if result.inference.activity_distribution
                        else 0
                    )
                    metrics["inference_dominant_activity_pct"] = (max_count / max(total, 1)) * 100

                # Upload inference summary as artifact
                if hasattr(result.inference, "predictions_csv_path"):
                    summary_path = (
                        self.artifacts_manager.run_dir / "inference" / "inference_summary.json"
                    )
                    if summary_path.exists():
                        tracker.log_artifact(summary_path, "inference")

            # Evaluation metrics
            elif stage == "evaluation" and result.evaluation:
                conf_summary = result.evaluation.confidence_summary or {}
                metrics["eval_mean_confidence"] = conf_summary.get("mean", 0.0)
                metrics["eval_median_confidence"] = conf_summary.get("median", 0.0)
                metrics["eval_std_confidence"] = conf_summary.get("std", 0.0)

                dist_summary = result.evaluation.distribution_summary or {}
                if "n_activities" in dist_summary:
                    metrics["eval_n_activities_detected"] = dist_summary["n_activities"]
                if "dominant_activity_pct" in dist_summary:
                    metrics["eval_dominant_activity_pct"] = dist_summary["dominant_activity_pct"]

                metrics["eval_has_labels"] = 1.0 if result.evaluation.has_labels else 0.0

                # Upload evaluation report
                if (
                    result.evaluation.report_json_path
                    and result.evaluation.report_json_path.exists()
                ):
                    tracker.log_artifact(result.evaluation.report_json_path, "evaluation")

            # Monitoring metrics - comprehensive 3-layer tracking
            elif stage == "monitoring" and result.monitoring:
                # Overall status
                metrics["monitoring_overall_healthy"] = (
                    1.0 if result.monitoring.overall_status == "HEALTHY" else 0.0
                )

                # Layer 1: Confidence
                layer1 = result.monitoring.layer1_confidence or {}
                metrics["monitoring_confidence_mean"] = layer1.get("mean_confidence", 0.0)
                metrics["monitoring_uncertain_pct"] = layer1.get("uncertain_percentage", 0.0)
                metrics["monitoring_std_confidence"] = layer1.get("std_confidence", 0.0)

                # Layer 2: Temporal
                layer2 = result.monitoring.layer2_temporal or {}
                metrics["monitoring_transition_rate"] = layer2.get("transition_rate", 0.0)

                # Layer 3: Drift - KEY metric for retraining decisions
                layer3 = result.monitoring.layer3_drift or {}
                metrics["monitoring_drift_score"] = layer3.get("max_drift", 0.0)
                metrics["monitoring_drift_status"] = 1.0 if layer3.get("status") == "PASS" else 0.0

                # Upload monitoring report
                if result.monitoring.report_path and result.monitoring.report_path.exists():
                    tracker.log_artifact(result.monitoring.report_path, "monitoring")

            # Trigger evaluation - critical for retraining decisions
            elif stage == "trigger" and result.trigger:
                metrics["trigger_should_retrain"] = 1.0 if result.trigger.should_retrain else 0.0
                metrics["trigger_cooldown_active"] = 1.0 if result.trigger.cooldown_active else 0.0

                # Map alert levels to numeric values
                alert_map = {"INFO": 0, "WARNING": 1, "ALERT": 2, "CRITICAL": 3}
                metrics["trigger_alert_level"] = alert_map.get(result.trigger.alert_level, 0)
                metrics["trigger_n_reasons"] = (
                    len(result.trigger.reasons) if result.trigger.reasons else 0
                )

            # Retraining metrics
            elif stage == "retraining" and result.retraining:
                for k, v in result.retraining.metrics.items():
                    if isinstance(v, (int, float)):
                        metrics[f"retrain_{k}"] = v
                metrics["retrain_n_source_samples"] = result.retraining.n_source_samples
                metrics["retrain_n_target_samples"] = result.retraining.n_target_samples

            # Log all metrics
            if metrics:
                tracker.log_metrics(metrics)
                logger.debug(f"Logged {len(metrics)} metrics to MLflow for stage: {stage}")

        except Exception as e:
            logger.warning(f"Failed to log stage '{stage}' to MLflow: {e}")

    def _end_mlflow(self, tracker, result):
        try:
            # Derive forced-retrain flag: retraining ran but trigger said no
            retrain_ran = "retraining" in result.stages_completed
            trigger_requested = (
                bool(result.trigger and result.trigger.should_retrain)
                if hasattr(result, "trigger")
                else False
            )
            forced_retrain_by_cli = retrain_ran and not trigger_requested

            # Log pipeline-level parameters
            tracker.log_params(
                {
                    "stages_completed": ",".join(result.stages_completed),
                    "stages_failed": ",".join(result.stages_failed),
                    "overall_status": result.overall_status,
                    "n_stages_completed": len(result.stages_completed),
                    "n_stages_failed": len(result.stages_failed),
                    "retrain_ran": str(retrain_ran),
                    "retrain_trigger_initiated": str(trigger_requested),
                    "retrain_forced_by_cli": str(forced_retrain_by_cli),
                }
            )

            # Upload run_info.json as artifact
            run_info_path = self.artifacts_manager.run_dir / "run_info.json"
            if run_info_path.exists():
                tracker.log_artifact(run_info_path, "pipeline")

            # ── Model Registry ──────────────────────────────────────
            # Register the current model if the pipeline completed
            # successfully (at least inference ran).  This logs the
            # Keras model to the artifact store AND registers it in
            # the MLflow Model Registry under "har-1dcnn-bilstm".
            if result.overall_status == "SUCCESS" and "inference" in result.stages_completed:
                self._register_model_to_mlflow(tracker, result)

            # Properly exit the context manager
            if hasattr(tracker, "_run_context"):
                tracker._run_context.__exit__(None, None, None)
        except Exception as e:
            logger.warning(f"Failed to finalize MLflow run: {e}")
        finally:
            # Ensure run is always closed
            try:
                if hasattr(tracker, "_run_context"):
                    tracker._run_context.__exit__(None, None, None)
            except Exception:
                pass

    def _register_model_to_mlflow(self, tracker, result):
        """Register the production model in MLflow Model Registry."""
        try:
            model_path = (
                self.pipeline_config.models_pretrained_dir / "fine_tuned_model_1dcnnbilstm.keras"
            )
            if not model_path.exists():
                logger.warning("Model file not found at %s — skipping registration.", model_path)
                return

            loaded_model = self._load_keras_model(model_path)
            # Build a minimal input example so MLflow can infer the signature
            try:
                import numpy as _np

                _in_shape = loaded_model.input_shape  # e.g. (None, 200, 6)
                _example = _np.zeros((1,) + tuple(_in_shape[1:]), dtype=_np.float32)
            except Exception:
                _example = None
            tracker.log_keras_model(
                model=loaded_model,
                artifact_path="model",
                input_example=_example,
                registered_model_name="har-1dcnn-bilstm",
            )

            # Log registration metadata
            conf_mean = 0.0
            if result.inference and result.inference.confidence_stats:
                conf_mean = result.inference.confidence_stats.get("mean", 0.0)
            tracker.log_metrics(
                {
                    "registered_model_confidence": conf_mean,
                }
            )
            logger.info("Model registered in MLflow Model Registry as 'har-1dcnn-bilstm'")

        except Exception as e:
            logger.warning("Model registration failed (non-fatal): %s", e)

    @staticmethod
    def _load_keras_model(path):
        """Load a Keras model (lazy import to avoid TF startup cost)."""
        from tensorflow import keras

        return keras.models.load_model(path)

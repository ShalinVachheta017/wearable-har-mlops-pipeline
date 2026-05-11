"""
=============================================================================
HAR MLOps Production Pipeline Orchestrator
=============================================================================

10 Active Stages:
    1  Data Ingestion           (Excel/CSV -> fused CSV)
    2  Data Validation          (schema + range checks)
    3  Data Transformation      (CSV -> windowed .npy)
    4  Model Inference          (.npy + model -> predictions)
    5  Model Evaluation         (confidence / distribution / ECE)
    6  Post-Inference Monitoring (3-layer: confidence, temporal, drift)
    7  Trigger Evaluation       (retraining decision)
  retraining cycle (optional, stages 8-10) 
    8  Model Retraining         (standard / AdaBN / pseudo-label)
    9  Model Registration       (version, deploy, rollback)
   10  Baseline Update          (rebuild drift baselines)
 advanced analytics (optional, stage 11) 
   11  Calibration              (temperature scaling, MC Dropout)
"""

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from src.entity.artifact_entity import PipelineResult
from src.entity.config_entity import (
    BaselineUpdateConfig,
    CalibrationUncertaintyConfig,
    DataIngestionConfig,
    DataTransformationConfig,
    DataValidationConfig,
    ModelEvaluationConfig,
    ModelInferenceConfig,
    ModelRegistrationConfig,
    ModelRetrainingConfig,
    PipelineConfig,
    PostInferenceMonitoringConfig,
    TriggerEvaluationConfig,
)
from src.exceptions import DataValidationError

from src.logger import logging
from src.utils.artifacts_manager import ArtifactsManager
from src.pipeline.pipeline_input_resolver import PipelineInputResolver
from src.pipeline.pipeline_mlflow_logger import PipelineMLflowLogger
from src.pipeline.pipeline_safety import PipelineSafetyGate, as_bool

logger = logging.getLogger(__name__)

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
]
RETRAIN_STAGES = {"retraining", "registration", "baseline_update"}
ADVANCED_STAGES = {"calibration"}


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

        self.artifacts_manager = ArtifactsManager(run_id=self.pipeline_config.timestamp)
        self.input_resolver = PipelineInputResolver(
            self.pipeline_config, self.ingestion_config, self.retraining_config
        )
        self.safety_gate = PipelineSafetyGate()
        self.mlflow_logger = PipelineMLflowLogger(self.artifacts_manager)

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
            Subset of stages to run.  Default stages 1-7;
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
            Include stage 11 (calibration).
        update_baseline : bool
            When True, promote the rebuilt baseline to the shared models/ path
            that monitoring reads.  Default False: baseline is written only as
            an MLflow artifact (safe governance default: no silent overwrites).
        """
        result = PipelineResult(
            run_id=self.pipeline_config.timestamp,
            start_time=datetime.now().isoformat(),
        )
        run_stages = self._resolve_run_stages(
            stages, enable_retrain, enable_advanced, skip_ingestion, skip_validation, result
        )
        has_labels, label_col, label_src = self._detect_dataset_labels()
        result.dataset_has_labels = has_labels
        result.dataset_label_source = label_src
        result.dataset_label_column = label_col

        run_dir = self.artifacts_manager.initialize()
        self._log_startup(result, run_dir, run_stages)

        ctx: Dict[str, Any] = {
            "ingestion_art": None, "validation_art": None, "transformation_art": None,
            "inference_art": None, "evaluation_art": None, "monitoring_art": None,
            "trigger_art": None, "retraining_art": None, "registration_art": None,
            "baseline_art": None, "collapse_signals": {},
            "dataset_has_labels": has_labels, "dataset_label_column": label_col,
            "dataset_label_source": label_src, "update_baseline": update_baseline,
        }
        _DISPATCH = {
            "ingestion": self._run_ingestion,
            "validation": self._run_validation,
            "transformation": self._run_transformation,
            "inference": self._run_inference,
            "evaluation": self._run_evaluation,
            "monitoring": self._run_monitoring,
            "trigger": self._run_trigger,
            "retraining": self._run_retraining,
            "registration": self._run_registration,
            "baseline_update": self._run_baseline_update,
            "calibration": self._run_calibration,
        }

        mlflow_tracker = self._init_mlflow(result.run_id)
        result.mlflow_tracked = mlflow_tracker is not None
        try:
            for stage in run_stages:
                try:
                    handler = _DISPATCH.get(stage)
                    if handler is None:
                        logger.warning("Unknown stage '%s': skipped.", stage)
                        continue
                    sig = handler(result, ctx)
                    if sig == "BREAK":
                        break
                    if sig == "SKIP":
                        result.stages_skipped.append(stage)
                    else:
                        result.stages_completed.append(stage)
                        logger.info("Stage '%s' completed.", stage)
                        if mlflow_tracker:
                            self._log_stage_to_mlflow(mlflow_tracker, stage, result)
                except DataValidationError:
                    raise
                except Exception as e:
                    logger.error("Stage '%s' FAILED: %s", stage, e)
                    logger.debug(traceback.format_exc())
                    result.stages_failed.append(stage)
                    if not continue_on_failure:
                        break
        finally:
            result.end_time = datetime.now().isoformat()
            result.overall_status = (
                "SUCCESS" if not result.stages_failed
                else "PARTIAL" if result.stages_completed else "FAILED"
            )
            self.artifacts_manager.finalize()
            self._save_result(result)
            if mlflow_tracker:
                self._end_mlflow(mlflow_tracker, result)
        logger.info("=" * 60)
        logger.info(
            "Pipeline finished: %s  (completed=%d  failed=%d  skipped=%d)",
            result.overall_status, len(result.stages_completed),
            len(result.stages_failed), len(result.stages_skipped),
        )
        logger.info("=" * 60)
        return result

    # ================================================================== #
    # Stage helpers
    # ================================================================== #

    def _run_ingestion(self, result: PipelineResult, ctx: Dict[str, Any]) -> None:
        from src.components.data_ingestion import DataIngestion
        art = DataIngestion(
            self.pipeline_config, self.ingestion_config
        ).initiate_data_ingestion()
        result.ingestion = art
        ctx["ingestion_art"] = art

        has_labels = bool(getattr(art, "has_labels", False))
        label_col = getattr(art, "label_column", None)
        if has_labels:
            label_src = (
                f"ingestion output column '{label_col}'" if label_col
                else "ingestion output marked as labeled"
            )
        else:
            label_src = "ingestion output contains no label column"
        ctx["dataset_has_labels"] = has_labels
        ctx["dataset_label_column"] = label_col
        ctx["dataset_label_source"] = label_src
        result.dataset_has_labels = has_labels
        result.dataset_label_source = label_src
        result.dataset_label_column = label_col
        logger.info(
            "Dataset label status (post-ingestion): %s",
            f"LABELED ({label_src})" if has_labels else "UNLABELED",
        )
        if art.fused_csv_path.exists():
            self.artifacts_manager.save_file(art.fused_csv_path, "data_ingestion")
        self.artifacts_manager.log_stage_completion("ingestion", "SUCCESS", {
            "n_rows": art.n_rows, "n_columns": art.n_columns, "sampling_hz": art.sampling_hz,
        })

    def _run_validation(self, result: PipelineResult, ctx: Dict[str, Any]) -> None:
        ingestion_art = ctx["ingestion_art"] or self._make_fallback_ingestion_artifact()
        from src.components.data_validation import DataValidation
        art = DataValidation(
            self.pipeline_config, self.validation_config, ingestion_art
        ).initiate_data_validation()
        result.validation = art
        ctx["validation_art"] = art
        self.artifacts_manager.save_json(
            {
                "is_valid": art.is_valid,
                "errors": art.errors,
                "warnings": art.warnings,
                "stats": art.stats,
            },
            "validation", "validation_report.json",
        )
        self.artifacts_manager.log_stage_completion(
            "validation", "SUCCESS" if art.is_valid else "FAILED", {"n_errors": len(art.errors)}
        )
        if not art.is_valid:
            result.stages_failed.append("validation")
            raise DataValidationError(
                f"Data validation failed with {len(art.errors)} error(s): {art.errors}. "
                "Pipeline aborted to prevent invalid data from reaching Stage 3. "
                "Fix the source data or relax DataValidationConfig thresholds."
            )

    def _run_transformation(self, result: PipelineResult, ctx: Dict[str, Any]) -> None:
        ingestion_art = ctx["ingestion_art"] or self._make_fallback_ingestion_artifact()
        from src.components.data_transformation import DataTransformation
        art = DataTransformation(
            self.pipeline_config, self.transformation_config,
            ingestion_art, ctx["validation_art"],
        ).initiate_data_transformation()
        result.transformation = art
        ctx["transformation_art"] = art
        if art.production_X_path.exists():
            self.artifacts_manager.save_file(art.production_X_path, "data_transformation")
        if art.metadata_path and art.metadata_path.exists():
            self.artifacts_manager.save_file(art.metadata_path, "data_transformation")
        if art.transformation_report_path and art.transformation_report_path.exists():
            self.artifacts_manager.save_file(art.transformation_report_path, "data_transformation")
        self.artifacts_manager.log_stage_completion("transformation", "SUCCESS", {
            "n_windows": art.n_windows,
            "unit_conversion": art.unit_conversion_applied,
            "model_input_space": art.model_input_space,
            "normalization": art.normalization_applied,
            "gravity_removal": art.gravity_removal_applied,
        })

    def _run_inference(self, result: PipelineResult, ctx: Dict[str, Any]) -> None:
        transformation_art = (
            ctx["transformation_art"] or self._make_fallback_transformation_artifact()
        )
        from src.components.model_inference import ModelInference
        art = ModelInference(
            self.pipeline_config, self.inference_config, transformation_art
        ).initiate_model_inference()
        result.inference = art
        ctx["inference_art"] = art
        for path in (
            art.predictions_csv_path,
            art.predictions_npy_path,
            art.probabilities_npy_path,
            art.metadata_json_path,
            art.inference_report_path,
        ):
            if path and path.exists():
                self.artifacts_manager.save_file(path, "inference")
        n_pred = art.n_predictions
        t_sec = art.inference_time_seconds
        avg_ms = round((t_sec / n_pred) * 1000, 4) if n_pred > 0 else 0.0
        throughput_wps = round(n_pred / t_sec, 2) if t_sec > 0 else 0.0
        act_dist = art.activity_distribution or {}
        self.artifacts_manager.save_json({
            "n_predictions": n_pred, "inference_time_seconds": t_sec,
            "throughput_windows_per_sec": throughput_wps, "avg_ms_per_window": avg_ms,
            "activity_distribution": act_dist,
            "activity_share": {
                a: round(cnt / n_pred, 4) if n_pred > 0 else 0.0
                for a, cnt in act_dist.items()
            },
            "confidence_stats": art.confidence_stats,
            "entropy_stats": art.entropy_stats,
            "top2_margin_stats": art.top2_margin_stats,
            "dominant_class": art.dominant_class,
            "dominant_pct": art.dominant_pct,
            "collapse_level": art.collapse_level,
            "model_version": art.model_version,
            "model_md5": art.model_md5,
            "inference_report_path": str(art.inference_report_path) if art.inference_report_path else None,
        }, "inference", "inference_summary.json")
        self.artifacts_manager.log_stage_completion("inference", "SUCCESS", {
            "n_predictions": n_pred, "inference_time_sec": t_sec,
            "throughput_windows_per_sec": throughput_wps, "avg_ms_per_window": avg_ms,
        })

    def _run_evaluation(self, result: PipelineResult, ctx: Dict[str, Any]) -> None:
        inference_art = ctx["inference_art"]
        if inference_art is None:
            raise ValueError("No inference artifact: run inference first.")
        import dataclasses
        from src.components.model_evaluation import ModelEvaluation
        eval_cfg = self.evaluation_config
        transformation_art = ctx["transformation_art"]
        if (
            not eval_cfg.labels_path
            and transformation_art is not None
            and transformation_art.production_y_path is not None
            and transformation_art.production_y_path.exists()
        ):
            eval_cfg = dataclasses.replace(eval_cfg, labels_path=transformation_art.production_y_path)
            logger.info(
                "Stage 5: auto-detected labels from Stage 3; "
                "switching to LABELED evaluation (production_y.npy)."
            )
        art = ModelEvaluation(
            self.pipeline_config, eval_cfg, inference_art
        ).initiate_model_evaluation()
        result.evaluation = art
        ctx["evaluation_art"] = art
        ctx["collapse_signals"] = self._extract_collapse_signals(art)
        for path in (art.report_json_path, art.report_text_path):
            if path and path.exists():
                self.artifacts_manager.save_file(path, "evaluation")
        self.artifacts_manager.save_json({
            "distribution_summary": art.distribution_summary,
            "confidence_summary": art.confidence_summary,
            "has_labels": art.has_labels,
            "classification_metrics": art.classification_metrics,
            "dominant_class": art.dominant_class,
            "dominant_pct": art.dominant_pct,
            "distribution_dominance_warning": art.distribution_dominance_warning,
        }, "evaluation", "evaluation_summary.json")
        self.artifacts_manager.log_stage_completion("evaluation", "SUCCESS", {
            "mean_confidence": (
                art.confidence_summary.get("mean", 0) if art.confidence_summary else 0
            ),
            "has_labels": art.has_labels,
        })

    def _run_monitoring(self, result: PipelineResult, ctx: Dict[str, Any]) -> None:
        inference_art = ctx["inference_art"]
        if inference_art is None:
            raise ValueError("No inference artifact: run inference first.")
        from src.components.post_inference_monitoring import PostInferenceMonitoring
        art = PostInferenceMonitoring(
            self.pipeline_config, self.monitoring_config,
            inference_art, ctx["transformation_art"],
        ).initiate_post_inference_monitoring()
        result.monitoring = art
        ctx["monitoring_art"] = art
        collapse_signals = self._augment_collapse_signals(ctx.get("collapse_signals", {}), art, ctx)
        ctx["collapse_signals"] = collapse_signals
        if collapse_signals:
            if art.monitoring_report is None:
                art.monitoring_report = {}
            art.monitoring_report["collapse_signals"] = collapse_signals
            if art.report_path:
                try:
                    Path(art.report_path).write_text(
                        json.dumps(art.monitoring_report, indent=2), encoding="utf-8"
                    )
                except Exception as exc:
                    logger.warning(
                        "Could not update monitoring report with collapse signals: %s", exc
                    )
        # Additional chunked drift checks every 500 windows using calibrated
        # DriftMonitor reference (models/drift_reference.json).
        drift_chunked = self._run_chunked_drift_monitor(ctx)
        if drift_chunked is not None:
            if art.monitoring_report is None:
                art.monitoring_report = {}
            art.monitoring_report["drift_monitor_chunked"] = drift_chunked
            if art.report_path:
                try:
                    Path(art.report_path).write_text(
                        json.dumps(art.monitoring_report, indent=2), encoding="utf-8"
                    )
                except Exception as exc:
                    logger.warning(
                        "Could not append chunked drift report to monitoring output: %s", exc
                    )
        if art.report_path and art.report_path.exists():
            self.artifacts_manager.save_file(art.report_path, "monitoring")
        self.artifacts_manager.save_json({
            "overall_status": art.overall_status,
            "layer1_confidence": art.layer1_confidence,
            "layer2_temporal": art.layer2_temporal,
            "layer3_drift": art.layer3_drift,
            "collapse_signals": collapse_signals,
            "drift_monitor_chunked": drift_chunked,
        }, "monitoring", "monitoring_summary.json")
        self.artifacts_manager.log_stage_completion("monitoring", art.overall_status, {
            "overall_status": art.overall_status,
            "confidence_status": art.layer1_confidence.get("status", "N/A"),
            "temporal_status": art.layer2_temporal.get("status", "N/A"),
            "drift_status": art.layer3_drift.get("status", "N/A"),
            "collapse_warning": collapse_signals.get("dominance_warning", False),
            "dominant_class": collapse_signals.get("dominant_class", ""),
            "dominant_pct": collapse_signals.get("dominant_pct", 0.0),
        })

    def _augment_collapse_signals(
        self,
        collapse_signals: Optional[Dict[str, Any]],
        monitoring_art,
        ctx: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Method Name :   _augment_collapse_signals
        Description :   Merge Stage 4 and Stage 6 collapse signals into the Stage 7 payload.

        Output      :   Returns the collapse signal dictionary consumed by trigger policy.
        On Failure  :   Logs the error and raises the exception.
        """
        return self.safety_gate.augment_collapse_signals(collapse_signals, monitoring_art, ctx)

    def _run_chunked_drift_monitor(self, ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run drift monitor checks in 500-window chunks if reference exists."""
        transformation_art = ctx.get("transformation_art")
        inference_art = ctx.get("inference_art")
        if transformation_art is None or inference_art is None:
            return None
        x_path = getattr(transformation_art, "production_X_path", None)
        if not x_path or not Path(x_path).exists():
            return None
        try:
            from src.monitoring.drift_monitor import DriftMonitor

            reference_path = self.pipeline_config.models_dir / "drift_reference.json"
            if not reference_path.exists():
                return {
                    "status": "SKIPPED",
                    "reason": f"missing drift reference: {reference_path}",
                }

            monitor = DriftMonitor(
                reference_path=reference_path,
                log_path=self.pipeline_config.project_root / "reports" / "drift_log.json",
            )
            windows = np.load(Path(x_path))

            probs = None
            probs_path = getattr(inference_art, "probabilities_npy_path", None)
            if probs_path and Path(probs_path).exists():
                _p = np.load(Path(probs_path))
                if len(_p) == len(windows):
                    probs = _p

            chunk_size = 500
            entries: List[Dict[str, Any]] = []
            for start in range(0, len(windows), chunk_size):
                end = min(start + chunk_size, len(windows))
                w = windows[start:end]
                p = probs[start:end] if probs is not None else None
                out = monitor.check(w, probabilities=p)
                out["chunk_start"] = int(start)
                out["chunk_end"] = int(end)
                entries.append(out)

            max_psi_overall = max((e.get("max_psi", 0.0) for e in entries), default=0.0)
            any_drift = any(bool(e.get("drift_detected")) for e in entries)
            return {
                "status": "OK",
                "chunk_size": chunk_size,
                "n_chunks": len(entries),
                "max_psi_overall": float(max_psi_overall),
                "drift_detected": any_drift,
                "action_recommended": (
                    "TRIGGER_RETRAINING_GATE" if any_drift else "CONTINUE_MONITORING"
                ),
                "chunks": entries,
            }
        except Exception as exc:
            logger.warning("Chunked drift monitor check failed: %s", exc)
            return {"status": "ERROR", "reason": str(exc)}

    def _run_trigger(self, result: PipelineResult, ctx: Dict[str, Any]) -> None:
        monitoring_art = ctx["monitoring_art"]
        if monitoring_art is None:
            raise ValueError("No monitoring artifact: run monitoring first.")
        from src.components.trigger_evaluation import TriggerEvaluation
        art = TriggerEvaluation(
            self.pipeline_config, self.trigger_config, monitoring_art
        ).initiate_trigger_evaluation()
        result.trigger = art
        ctx["trigger_art"] = art
        self.artifacts_manager.save_json({
            "decision": getattr(art, "decision", "HEALTHY"),
            "should_retrain": art.should_retrain,
            "auto_retrain": getattr(art, "auto_retrain", False),
            "review_required": getattr(art, "review_required", False),
            "label_required": getattr(art, "label_required", False),
            "qa_required": getattr(art, "qa_required", False),
            "action": art.action,
            "alert_level": art.alert_level,
            "reason": art.reasons[0] if art.reasons else "",
            "reasons": art.reasons,
            "required_next_steps": getattr(art, "required_next_steps", []),
            "cooldown_active": art.cooldown_active,
            "collapse_signals": (
                monitoring_art.monitoring_report.get("collapse_signals", {})
                if monitoring_art and monitoring_art.monitoring_report else {}
            ),
        }, "trigger", "trigger_decision.json")
        self.artifacts_manager.log_stage_completion("trigger", "SUCCESS", {
            "should_retrain": art.should_retrain, "action": art.action,
            "alert_level": art.alert_level, "n_reasons": len(art.reasons),
        })

    def _run_retraining(self, result: PipelineResult, ctx: Dict[str, Any]):
        adaptation_method = (self.retraining_config.adaptation_method or "none").lower()
        unlabeled_supported = {"adabn", "tent", "adabn_tent", "pseudo_label"}
        if not ctx["dataset_has_labels"] and adaptation_method not in unlabeled_supported:
            logger.info(
                "Stage 8 SKIPPED: dataset is UNLABELED and supervised retraining is blocked. "
                "Provide --labels for supervised retraining, or use --adapt one of: %s.",
                ", ".join(sorted(unlabeled_supported)),
            )
            ctx["retraining_art"] = None
            return "SKIP"
        if self._should_block_unlabeled_retraining(ctx, adaptation_method, unlabeled_supported):
            logger.warning(
                "Stage 8 BLOCKED - critical collapse or low-motion collapse risk was detected. "
                "Unlabeled adaptation method '%s' is unsafe for this run, even with force_retraining=True.",
                adaptation_method,
            )
            ctx["retraining_art"] = None
            return "SKIP"
        force_retrain = getattr(self.pipeline_config, "force_retraining", False)
        if not force_retrain and (
            ctx["trigger_art"] is None or not ctx["trigger_art"].should_retrain
        ):
            logger.info(
                "Stage 8 SKIPPED: trigger decision is REVIEW with should_retrain=False. "
                "Unlabeled production data requires human review before retraining. "
                "Stages 9-10 will also skip (no retraining artifact). "
                "Stage 11 (calibration) will continue if requested."
            )
            ctx["retraining_art"] = None
            return "SKIP"
        from src.components.model_retraining import ModelRetraining
        art = ModelRetraining(
            self.pipeline_config, self.retraining_config,
            ctx["trigger_art"], ctx["transformation_art"],
        ).initiate_model_retraining()
        result.retraining = art
        ctx["retraining_art"] = art

    def _should_block_unlabeled_retraining(
        self,
        ctx: Dict[str, Any],
        adaptation_method: str,
        unlabeled_supported: set[str],
    ) -> bool:
        """
        Method Name :   _should_block_unlabeled_retraining
        Description :   Check whether critical collapse makes unlabeled adaptation unsafe.

        Output      :   Returns True when Stage 8 must be blocked.
        On Failure  :   Logs the error and raises the exception.
        """
        gate = getattr(self, "safety_gate", PipelineSafetyGate())
        return gate.should_block_unlabeled_retraining(
            ctx, adaptation_method, unlabeled_supported
        )

    def _run_registration(self, result: PipelineResult, ctx: Dict[str, Any]):
        if ctx["retraining_art"] is None:
            logger.info("Stage 9 SKIPPED: no retraining artifact.")
            return "SKIP"
        from src.components.model_registration import ModelRegistration
        art = ModelRegistration(
            self.pipeline_config, self.registration_config,
            ctx["retraining_art"], ctx["evaluation_art"],
        ).initiate_model_registration()
        result.registration = art
        ctx["registration_art"] = art

    def _run_baseline_update(self, result: PipelineResult, ctx: Dict[str, Any]):
        if ctx["retraining_art"] is None:
            logger.info("Stage 10 SKIPPED: no retraining artifact.")
            return "SKIP"
        self.baseline_config.promote_to_shared = ctx["update_baseline"]
        from src.components.baseline_update import BaselineUpdate
        art = BaselineUpdate(
            self.pipeline_config, self.baseline_config, ctx["retraining_art"]
        ).initiate_baseline_update()
        result.baseline_update = art
        ctx["baseline_art"] = art

    def _run_calibration(self, result: PipelineResult, ctx: Dict[str, Any]) -> None:
        inference_art = ctx["inference_art"]
        if inference_art is None:
            raise ValueError("No inference artifact: run inference first.")
        from src.components.calibration_uncertainty import CalibrationUncertainty
        art = CalibrationUncertainty(
            self.pipeline_config, self.calibration_config, inference_art
        ).initiate_calibration()
        result.calibration = art
        output_dir = Path(
            self.calibration_config.output_dir
            or self.pipeline_config.outputs_dir / "calibration"
        )
        for fname in ("temperature.json", "calibration_report.json", "calibrated_probabilities.npy"):
            p = output_dir / fname
            if p.exists():
                self.artifacts_manager.save_file(p, "calibration")
        self.artifacts_manager.log_stage_completion("calibration", art.overall_status, {
            "overall_status": art.overall_status,
            "n_warnings": len(art.calibration_warnings),
        })

    # ================================================================== #
    # Stage resolution and startup
    # ================================================================== #

    def _resolve_run_stages(
        self,
        stages: Optional[List[str]],
        enable_retrain: bool,
        enable_advanced: bool,
        skip_ingestion: bool,
        skip_validation: bool,
        result: PipelineResult,
    ) -> List[str]:
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
        return run_stages

    def _detect_dataset_labels(self):
        """Detect labels presence from config or CSV header scan."""
        return self.input_resolver.detect_dataset_labels()

    def _log_startup(self, result: PipelineResult, run_dir, run_stages: List[str]) -> None:
        logger.info("=" * 70)
        logger.info("HAR MLOPS PRODUCTION PIPELINE - EXECUTION START")
        logger.info("=" * 70)
        logger.info("Run ID: %s", result.run_id)
        logger.info("Artifacts Directory: %s", run_dir)
        logger.info("Data Source: %s", self.pipeline_config.data_raw_dir)
        logger.info("Preprocessing Settings:")
        logger.info(
            "  - Unit Conversion (milliG\u2192m/s\u00b2): %s",
            "ENABLED" if self.transformation_config.enable_unit_conversion else "DISABLED",
        )
        logger.info(
            "  - Unit Conversion Factor: %.8f",
            self.transformation_config.unit_conversion_factor,
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
        logger.info(
            "  - Inference confidence threshold: %.2f",
            self.inference_config.confidence_threshold,
        )
        if result.dataset_has_labels:
            logger.info("Dataset label status: LABELED (%s)", result.dataset_label_source)
        else:
            logger.info(
                "Dataset label status: UNLABELED (no labels file and no label column detected)"
            )
        logger.info("Pipeline stages: %s", run_stages)
        logger.info("=" * 70)

    # ================================================================== #
    # Helpers
    # ================================================================== #

    @staticmethod
    def _label_column_from_headers(headers: List[str]) -> Optional[str]:
        return PipelineInputResolver.label_column_from_headers(headers)

    def _detect_label_column_from_csv(self, csv_path: Optional[Path]) -> Optional[str]:
        return self.input_resolver.detect_label_column_from_csv(csv_path)

    def _resolve_existing_fused_csv(self) -> Path:
        """Resolve best available fused CSV path for skip-ingestion/fallback flows."""
        return self.input_resolver.resolve_existing_fused_csv()

    @staticmethod
    def _as_bool(value) -> bool:
        return as_bool(value)

    def _extract_collapse_signals(self, evaluation_art) -> Dict:
        """Extract collapse-related fields from Stage 5 artifact/report JSON."""
        return self.safety_gate.extract_collapse_signals(evaluation_art)

    def _make_fallback_ingestion_artifact(self):
        """Create a synthetic ingestion artifact pointing to existing CSV."""
        return self.input_resolver.make_fallback_ingestion_artifact()

    def _make_fallback_transformation_artifact(self):
        """Create a synthetic transformation artifact pointing to existing .npy."""
        return self.input_resolver.make_fallback_transformation_artifact()

    def _save_result(self, result: PipelineResult):
        """Persist pipeline result as JSON."""
        log_dir = self.pipeline_config.logs_dir / "pipeline"
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / f"pipeline_result_{result.run_id}.json"
        import dataclasses
        data = dataclasses.asdict(result)

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

    # MLflow helpers
    def _init_mlflow(self, run_id: str):
        return self.mlflow_logger.init_run(run_id)

    def _log_stage_to_mlflow(self, tracker, stage, result):
        self.mlflow_logger.log_stage(tracker, stage, result)

    def _end_mlflow(self, tracker, result):
        self.mlflow_logger.end_run(tracker, result)

    def _register_model_to_mlflow(self, tracker, result):
        """Register the production model in MLflow Model Registry."""
        self.mlflow_logger.register_model(tracker, result)

    @staticmethod
    def _load_keras_model(path):
        """Load a Keras model (lazy import to avoid TF startup cost)."""
        return PipelineMLflowLogger.load_keras_model(path)

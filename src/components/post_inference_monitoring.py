"""
Component 6 - Post-Inference Monitoring.
"""

import logging
from pathlib import Path
from typing import Optional

from src.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelInferenceArtifact,
    PostInferenceMonitoringArtifact,
)
from src.entity.config_entity import PipelineConfig, PostInferenceMonitoringConfig

logger = logging.getLogger(__name__)


class PostInferenceMonitoring:
    """Pipeline component wrapper for 3-layer post-inference monitoring."""

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        config: PostInferenceMonitoringConfig,
        inference_artifact: ModelInferenceArtifact,
        transformation_artifact: Optional[DataTransformationArtifact] = None,
    ):
        """
        Method Name :   __init__
        Description :   Store Stage 6 config and upstream artifacts.

        Output      :   Initializes the PostInferenceMonitoring component.
        On Failure  :   Logs the error and raises the exception.
        """
        self.pipeline_config = pipeline_config
        self.config = config
        self.inference_artifact = inference_artifact
        self.transformation_artifact = transformation_artifact

    def _resolve_calibration_temperature(self) -> float:
        """
        Method Name :   _resolve_calibration_temperature
        Description :   Load the Stage 11 temperature value when calibration is enabled.

        Output      :   Returns the configured or saved calibration temperature.
        On Failure  :   Logs the error and falls back to temperature 1.0.
        """
        import json

        calibration_temperature = float(self.config.calibration_temperature)
        if calibration_temperature != 1.0:
            return calibration_temperature

        temp_path = self.pipeline_config.outputs_dir / "calibration" / "temperature.json"
        if not temp_path.exists():
            return 1.0

        try:
            calib_data = json.loads(temp_path.read_text(encoding="utf-8"))
            calibration_temperature = float(calib_data.get("temperature", 1.0))
            if calibration_temperature != 1.0:
                logger.info(
                    "Loaded calibration temperature %.4f from %s",
                    calibration_temperature,
                    temp_path,
                )
            return calibration_temperature
        except Exception as exc:
            logger.warning("Could not load calibration temperature: %s", exc)
            return 1.0

    def _resolve_mmd_reference(self) -> Optional[Path]:
        """
        Method Name :   _resolve_mmd_reference
        Description :   Resolve the optional reference-window tensor for MMD drift checks.

        Output      :   Returns an existing configured/default MMD reference path or None.
        On Failure  :   Logs the error and raises the exception.
        """
        if self.config.mmd_reference_npy is not None:
            return Path(self.config.mmd_reference_npy)

        candidate = self.pipeline_config.models_dir / "mmd_reference_windows.npy"
        return candidate if candidate.exists() else None

    def _resolve_predictions_path(self) -> Path:
        """
        Method Name :   _resolve_predictions_path
        Description :   Resolve the Stage 4 prediction CSV used by Stage 6.

        Output      :   Returns the prediction CSV path.
        On Failure  :   Logs the error and raises the exception.
        """
        return Path(self.config.predictions_csv or self.inference_artifact.predictions_csv_path)

    def _resolve_production_data_path(self) -> Optional[Path]:
        """
        Method Name :   _resolve_production_data_path
        Description :   Resolve the Stage 3 production window tensor used by monitoring.

        Output      :   Returns production_X.npy path when available, otherwise None.
        On Failure  :   Logs the error and raises the exception.
        """
        if self.config.production_data_npy is not None:
            return Path(self.config.production_data_npy)
        if self.transformation_artifact is not None:
            return Path(self.transformation_artifact.production_X_path)
        default_path = self.pipeline_config.data_prepared_dir / "production_X.npy"
        return default_path if default_path.exists() else None

    def _resolve_baseline_path(self):
        """
        Method Name :   _resolve_baseline_path
        Description :   Resolve and guard the baseline statistics path for drift monitoring.
                        Selects baseline according to baseline_mode:
                          - raw_physical  → models/raw_physical_baseline.json
                          - normalized    → models/normalized_baseline.json
                        Returns (path, missing_reason) where missing_reason is None on
                        success or a status string (DRIFT_BASELINE_MISSING /
                        DRIFT_BASELINE_MISMATCH_REVIEW) when drift must be skipped safely.

        Output      :   Tuple[Optional[Path], Optional[str]]
        On Failure  :   Logs the error and raises the exception.
        """
        import json as _json
        import time

        baseline_mode = getattr(self.config, "baseline_mode", "raw_physical")

        # Override path: explicit baseline_stats_json takes absolute precedence.
        if self.config.baseline_stats_json is not None:
            baseline_json = Path(self.config.baseline_stats_json)
        elif baseline_mode == "normalized":
            candidate = getattr(self.config, "normalized_baseline_path", None)
            baseline_json = (
                Path(candidate)
                if candidate
                else (self.pipeline_config.models_dir / "normalized_baseline.json")
            )
        else:
            # Default production path: raw physical units.
            candidate = getattr(self.config, "raw_baseline_path", None)
            baseline_json = (
                Path(candidate)
                if candidate
                else (self.pipeline_config.models_dir / "raw_physical_baseline.json")
            )

        if not baseline_json.exists():
            if baseline_mode == "raw_physical":
                logger.warning(
                    "Raw physical baseline not found: %s. "
                    "Drift status will be DRIFT_BASELINE_MISSING. "
                    "Run scripts/build_raw_physical_baseline.py to create it.",
                    baseline_json,
                )
                return None, "DRIFT_BASELINE_MISSING"
            else:
                logger.warning(
                    "Normalized baseline not found: %s - drift analysis skipped.",
                    baseline_json,
                )
                return None, "DRIFT_BASELINE_MISSING"

        # Guard: detect unit-space mismatch before comparing.
        # If we are in raw_physical mode but the baseline metadata says
        # feature_space='transformed' (i.e., it was built from normalized data),
        # comparing would produce fake-critical z-scores (raw Az ≈ -9.8 vs ~0).
        try:
            _doc = _json.loads(baseline_json.read_text(encoding="utf-8"))
            _meta = _doc.get("metadata", {}) or {}
            # Support both top-level "feature_space" and the legacy "metadata.feature_space"
            # key so the guard works regardless of which builder created the file.
            baseline_feature_space = (
                _doc.get("feature_space") or _meta.get("feature_space") or "unknown"
            )
            # Normalized-family aliases ("transformed" = scaler was applied).
            _normalized_aliases = {"transformed", "normalized_units"}
            is_normalized_baseline = baseline_feature_space in _normalized_aliases
            is_raw_baseline = baseline_feature_space == "raw_physical_units"

            if baseline_mode == "raw_physical" and is_normalized_baseline:
                logger.warning(
                    "DRIFT_BASELINE_MISMATCH_REVIEW: baseline_mode=raw_physical but "
                    "baseline file has feature_space='%s' (%s). "
                    "This would produce fake-critical drift (raw Az ≈ -9.8 m/s² vs "
                    "normalized baseline mean ≈ 0). Drift layer skipped. "
                    "Rebuild with scripts/build_raw_physical_baseline.py.",
                    baseline_feature_space,
                    baseline_json,
                )
                return None, "DRIFT_BASELINE_MISMATCH_REVIEW"
            if baseline_mode == "normalized" and is_raw_baseline:
                logger.warning(
                    "DRIFT_BASELINE_MISMATCH_REVIEW: baseline_mode=normalized but "
                    "baseline file has feature_space='raw_physical_units' (%s). "
                    "Drift layer skipped.",
                    baseline_json,
                )
                return None, "DRIFT_BASELINE_MISMATCH_REVIEW"
        except Exception as exc:
            logger.warning("Could not read baseline metadata for mismatch check: %s", exc)

        age_days = (time.time() - baseline_json.stat().st_mtime) / 86400
        if age_days > self.config.max_baseline_age_days:
            logger.warning(
                "Baseline is %.0f days old (limit: %d days) — drift scores may not "
                "reflect current sensor characteristics. Consider baseline_update stage.",
                age_days,
                self.config.max_baseline_age_days,
            )

        if self.config.is_training_session:
            logger.warning(
                "is_training_session=True: skipping Layer 3 drift to avoid "
                "self-referential scores (production data = training data)."
            )
            return None, None

        return baseline_json, None

    def _build_monitor(self):
        """
        Method Name :   _build_monitor
        Description :   Create the monitoring engine from the typed Stage 6 config.

        Output      :   Returns a configured PostInferenceMonitor instance.
        On Failure  :   Logs the error and raises the exception.
        """
        from src.monitoring.post_inference_monitor import PostInferenceMonitor

        return PostInferenceMonitor(
            confidence_warn_threshold=self.config.confidence_warn_threshold,
            confidence_threshold=self.config.uncertain_window_threshold,
            uncertain_threshold_pct=self.config.uncertain_pct_threshold,
            transition_rate_threshold=self.config.transition_rate_threshold,
            drift_threshold=self.config.drift_zscore_threshold,
            drift_detector_mode=self.config.drift_detector_mode,
            mmd_reference_path=self._resolve_mmd_reference(),
            mmd_threshold=self.config.mmd_threshold,
            mmd_sample_size=self.config.mmd_sample_size,
            mmd_bootstrap_iterations=self.config.mmd_bootstrap_iterations,
            mmd_random_seed=self.config.mmd_random_seed,
            calibration_temperature=self._resolve_calibration_temperature(),
            dominant_class_warn_threshold=self.config.dominant_class_warn_threshold,
            dominant_class_critical_threshold=self.config.dominant_class_critical_threshold,
            low_gyro_motion_threshold=self.config.low_gyro_motion_threshold,
            low_motion_dominance_threshold=self.config.low_motion_dominance_threshold,
            window_duration_seconds=self.config.window_duration_seconds,
            prediction_stride_seconds=self.config.prediction_stride_seconds,
        )

    def _build_artifact(self, report, output_dir: Path) -> PostInferenceMonitoringArtifact:
        """
        Method Name :   _build_artifact
        Description :   Convert the monitoring report object into the Stage 6 artifact.

        Output      :   Returns PostInferenceMonitoringArtifact.
        On Failure  :   Logs the error and raises the exception.
        """
        report_dict = report.to_dict() if hasattr(report, "to_dict") else {}
        return PostInferenceMonitoringArtifact(
            monitoring_report=report_dict,
            overall_status=getattr(report, "overall_status", "UNKNOWN"),
            layer1_confidence=getattr(report, "layer1_confidence", {}),
            layer2_temporal=getattr(report, "layer2_temporal", {}),
            layer3_drift=getattr(report, "layer3_drift", {}),
            report_path=output_dir / "monitoring_report.json",
        )

    def initiate_post_inference_monitoring(self) -> PostInferenceMonitoringArtifact:
        """
        Method Name :   initiate_post_inference_monitoring
        Description :   Run Stage 6 confidence, temporal, motion-context, and drift monitoring.

        Output      :   Returns PostInferenceMonitoringArtifact.
        On Failure  :   Logs the error and raises the exception.
        """
        logger.info("=" * 60)
        logger.info("STAGE 6 - Post-Inference Monitoring")
        logger.info("=" * 60)

        from src.config import DEFAULT_MODEL_PATH

        monitor = self._build_monitor()
        predictions_csv = self._resolve_predictions_path()
        production_npy = self._resolve_production_data_path()
        baseline_json, baseline_missing_reason = self._resolve_baseline_path()
        model_path = self.config.model_path or DEFAULT_MODEL_PATH
        output_dir = Path(self.config.output_dir or self.pipeline_config.outputs_dir / "monitoring")
        output_dir.mkdir(parents=True, exist_ok=True)

        report = monitor.run(
            predictions_path=predictions_csv,
            production_data_path=production_npy,
            baseline_path=baseline_json,
            model_path=model_path,
            output_dir=output_dir,
            baseline_missing_reason=baseline_missing_reason,
        )

        return self._build_artifact(report, output_dir)

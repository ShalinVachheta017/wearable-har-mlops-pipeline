"""
Component 7 - Trigger Evaluation.

Wraps src/trigger_policy.py and converts Stage 6 reports into trigger decisions.
"""

import logging
from pathlib import Path

from src.entity.artifact_entity import (
    PostInferenceMonitoringArtifact,
    TriggerEvaluationArtifact,
)
from src.entity.config_entity import PipelineConfig, TriggerEvaluationConfig

logger = logging.getLogger(__name__)


class TriggerEvaluation:
    """Evaluate whether retraining should be triggered."""

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        config: TriggerEvaluationConfig,
        monitoring_artifact: PostInferenceMonitoringArtifact,
    ):
        """
        Method Name :   __init__
        Description :   Store Stage 7 config and the Stage 6 monitoring artifact.

        Output      :   Initializes the TriggerEvaluation component.
        On Failure  :   Logs the error and raises the exception.
        """
        self.pipeline_config = pipeline_config
        self.config = config
        self.monitoring_artifact = monitoring_artifact

    def initiate_trigger_evaluation(self) -> TriggerEvaluationArtifact:
        """
        Method Name :   initiate_trigger_evaluation
        Description :   Build the trigger-policy payload and evaluate retraining safety.

        Output      :   Returns TriggerEvaluationArtifact.
        On Failure  :   Logs the error and raises the exception.
        """
        logger.info("=" * 60)
        logger.info("STAGE 7 - Trigger Evaluation")
        logger.info("=" * 60)

        from src.trigger_policy import (
            CooldownConfig,
            TriggerPolicyEngine,
            TriggerThresholds,
        )

        thresholds = TriggerThresholds(
            confidence_warn=self.config.confidence_warn,
            confidence_critical=self.config.confidence_critical,
            drift_zscore_warn=self.config.drift_zscore_warn,
            drift_zscore_critical=self.config.drift_zscore_critical,
            flip_rate_warn=self.config.temporal_flip_warn,
            flip_rate_critical=self.config.temporal_flip_critical,
        )
        cooldown = CooldownConfig(retrain_cooldown_hours=self.config.cooldown_hours)
        state_dir = self.config.state_dir or (self.pipeline_config.logs_dir / "trigger")
        state_file = Path(state_dir) / "trigger_state.json"

        engine = TriggerPolicyEngine(
            thresholds=thresholds,
            cooldown_config=cooldown,
            state_file=state_file,
        )

        trigger_report = self._build_trigger_report()
        decision = engine.evaluate(trigger_report)

        logger.info(
            "Trigger decision: action=%s  should_retrain=%s  alert=%s",
            decision.action,
            decision.should_trigger,
            decision.alert_level,
        )

        return TriggerEvaluationArtifact(
            should_retrain=decision.should_trigger,
            action=(
                str(decision.action.value)
                if hasattr(decision.action, "value")
                else str(decision.action)
            ),
            alert_level=(
                str(decision.alert_level.value)
                if hasattr(decision.alert_level, "value")
                else str(decision.alert_level)
            ),
            reasons=self._build_reasons(decision),
            cooldown_active=getattr(decision, "cooldown_active", False),
            # Governance fields — propagated from TriggerDecision so the artifact
            # exposes the full review-gate contract without extra dict access.
            decision=(
                decision._decision_label()
                if hasattr(decision, "_decision_label")
                else "HEALTHY"
            ),
            auto_retrain=getattr(decision, "auto_retrain", False),
            review_required=getattr(decision, "review_required", False),
            label_required=getattr(decision, "label_required", False),
            qa_required=getattr(decision, "qa_required", False),
            required_next_steps=list(getattr(decision, "required_next_steps", [])),
        )

    def _build_trigger_report(self) -> dict:
        """
        Method Name :   _build_trigger_report
        Description :   Convert Stage 6 artifact fields into TriggerPolicyEngine input.

        Output      :   Returns a trigger-policy report dictionary.
        On Failure  :   Logs the error and raises the exception.
        """
        raw_report = self.monitoring_artifact.monitoring_report or {}
        layer1 = self.monitoring_artifact.layer1_confidence or raw_report.get(
            "layer1_confidence", {}
        )
        layer2 = self.monitoring_artifact.layer2_temporal or raw_report.get(
            "layer2_temporal", {}
        )
        layer3 = self.monitoring_artifact.layer3_drift or raw_report.get(
            "layer3_drift", {}
        )
        collapse = raw_report.get("collapse_signals", {}) or {}
        motion_context = (
            layer2.get("motion_context", {}) if isinstance(layer2, dict) else {}
        )

        return {
            "confidence_report": {
                "metrics": {
                    "mean_confidence": layer1.get("mean_confidence", 0.0),
                    "mean_entropy": layer1.get("mean_entropy", 0.0),
                    "uncertain_ratio": layer1.get("uncertain_percentage", 0.0) / 100.0,
                    "std_confidence": layer1.get("std_confidence", 0.0),
                }
            },
            "temporal_report": {
                "metrics": {
                    "flip_rate": layer2.get("transition_rate", 0.0) / 100.0,
                    "mean_dwell_time_seconds": layer2.get(
                        "mean_dwell_time_seconds", 0.0
                    ),
                    "short_dwell_ratio": layer2.get("short_dwell_ratio", 0.0),
                }
            },
            "drift_report": {
                "per_channel_metrics": layer3.get("per_channel_metrics", {}),
                "n_drifted_channels": layer3.get("n_drifted_channels", 0),
                "aggregate_drift_score": layer3.get(
                    "aggregate_drift_score", layer3.get("max_drift", 0.0)
                ),
                "drift_detector": layer3.get("drift_detector", "zscore_mean_shift"),
                "mmd_score": layer3.get("mmd_score"),
                "mmd_threshold": layer3.get("mmd_threshold"),
                "mmd_threshold_ratio": layer3.get("mmd_threshold_ratio"),
                "overall_status": layer3.get("status", "UNKNOWN"),
            },
            "collapse_signals": {
                "dominance_warning": self._as_bool(
                    collapse.get(
                        "dominance_warning", layer1.get("dominance_warning", False)
                    )
                ),
                "dominant_class": collapse.get(
                    "dominant_class", layer1.get("dominant_class")
                ),
                "dominant_pct": collapse.get(
                    "dominant_pct", layer1.get("dominant_pct")
                ),
                "collapse_level": collapse.get("collapse_level"),
                "mean_confidence": collapse.get(
                    "mean_confidence", layer1.get("mean_confidence", 0.0)
                ),
                "transition_rate": collapse.get(
                    "transition_rate", layer2.get("transition_rate", 0.0)
                ),
                "longest_sequence_length": collapse.get("longest_sequence_length"),
                "top2_margin_mean": collapse.get(
                    "top2_margin_mean", layer1.get("top2_margin_mean")
                ),
                "low_gyro_motion": self._as_bool(
                    collapse.get(
                        "low_gyro_motion", motion_context.get("low_gyro_motion", False)
                    )
                ),
                "low_motion_collapse_risk": self._as_bool(
                    collapse.get(
                        "low_motion_collapse_risk",
                        motion_context.get("low_motion_collapse_risk", False),
                    )
                ),
                "g_mag_median": collapse.get(
                    "g_mag_median", motion_context.get("g_mag_median")
                ),
                "gravity_dominant_axis": collapse.get(
                    "gravity_dominant_axis", motion_context.get("gravity_dominant_axis")
                ),
            },
        }

    @staticmethod
    def _build_reasons(decision) -> list[str]:
        """
        Method Name :   _build_reasons
        Description :   Convert a trigger-policy decision into user-facing reasons.

        Output      :   Returns ordered reason strings.
        On Failure  :   Logs the error and raises the exception.
        """
        reasons: list[str] = []
        primary_reason = getattr(decision, "reason", None)
        if primary_reason:
            reasons.append(str(primary_reason))

        recommendations = (
            list(getattr(decision, "recommendations", []))
            if hasattr(decision, "recommendations")
            else []
        )
        for item in recommendations:
            text = str(item)
            if text and text not in reasons:
                reasons.append(text)

        return reasons

    @staticmethod
    def _as_bool(value) -> bool:
        """
        Method Name :   _as_bool
        Description :   Convert bool-like strings and values into a strict boolean.

        Output      :   Returns True or False.
        On Failure  :   Logs the error and raises the exception.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y"}
        return bool(value)

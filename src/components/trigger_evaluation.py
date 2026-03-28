"""
Component 7 – Trigger Evaluation

Wraps:  src/trigger_policy.py  →  TriggerPolicyEngine
"""

import logging
from pathlib import Path
from typing import Optional

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
        self.pipeline_config = pipeline_config
        self.config = config
        self.monitoring_artifact = monitoring_artifact

    # ------------------------------------------------------------------ #
    def initiate_trigger_evaluation(self) -> TriggerEvaluationArtifact:
        logger.info("=" * 60)
        logger.info("STAGE 7 — Trigger Evaluation")
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
        cooldown = CooldownConfig(
            retrain_cooldown_hours=self.config.cooldown_hours,
        )
        state_dir = self.config.state_dir or (self.pipeline_config.logs_dir / "trigger")
        state_file = Path(state_dir) / "trigger_state.json"

        engine = TriggerPolicyEngine(
            thresholds=thresholds,
            cooldown_config=cooldown,
            state_file=state_file,
        )

        # Transform monitoring report to trigger engine format
        raw_report = self.monitoring_artifact.monitoring_report or {}
        layer1 = raw_report.get("layer1_confidence", {})
        layer2 = raw_report.get("layer2_temporal", {})
        layer3 = raw_report.get("layer3_drift", {})
        collapse = raw_report.get("collapse_signals", {})

        # Map monitoring keys → trigger-policy expected structure
        # Use direct artifact fields (populated from the monitoring component)
        layer1 = self.monitoring_artifact.layer1_confidence or layer1
        layer2 = self.monitoring_artifact.layer2_temporal or layer2
        layer3 = self.monitoring_artifact.layer3_drift or layer3

        trigger_report = {
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
                    "mean_dwell_time_seconds": layer2.get("mean_dwell_time_seconds", 0.0),
                    "short_dwell_ratio": layer2.get("short_dwell_ratio", 0.0),
                }
            },
            "drift_report": {
                "per_channel_metrics": {},
                "n_drifted_channels": layer3.get("n_drifted_channels", 0),
                "aggregate_drift_score": layer3.get("max_drift", 0.0),
                "overall_status": layer3.get("status", "UNKNOWN"),
            },
            "collapse_signals": {
                "dominance_warning": self._as_bool(collapse.get("dominance_warning", False)),
                "dominant_class": collapse.get("dominant_class"),
                "dominant_pct": collapse.get("dominant_pct"),
                "mean_confidence": collapse.get(
                    "mean_confidence", layer1.get("mean_confidence", 0.0)
                ),
                "transition_rate": collapse.get(
                    "transition_rate", layer2.get("transition_rate", 0.0)
                ),
                "longest_sequence_length": collapse.get("longest_sequence_length"),
            },
        }

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
            cooldown_active=False,
        )

    @staticmethod
    def _build_reasons(decision) -> list[str]:
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
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y"}
        return bool(value)

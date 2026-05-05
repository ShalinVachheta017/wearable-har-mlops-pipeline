#!/usr/bin/env python3
"""
Automated Retraining Trigger Policy Module
==========================================

This module implements the decision logic for when to trigger model retraining
based on monitoring metrics. It uses a multi-metric voting scheme to reduce
false positives while catching genuine degradation.

Key Features:
- Multi-metric aggregation (2-of-3 voting scheme)
- Tiered alerting (INFO → WARNING → CRITICAL)
- Cooldown periods to prevent rapid successive retrains
- Configurable thresholds aligned with literature
- MLflow logging for audit trail

Trigger Criteria:
- Confidence-based: Mean confidence drops below threshold
- Drift-based: Multiple channels show significant distribution shift
- Temporal-based: Flip rate or dwell time becomes abnormal
- Combined: Requires multiple signals to confirm

Usage:
    from trigger_policy import TriggerPolicyEngine

    engine = TriggerPolicyEngine()
    decision = engine.evaluate(monitoring_report)

    if decision.should_trigger:
        trigger_retraining(decision.reason)

Author: HAR MLOps Pipeline
Date: January 30, 2026
"""

import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import LOGS_DIR, PROJECT_ROOT
from src.entity.config_entity import PostInferenceMonitoringConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "INFO"  # Notable but not concerning
    WARNING = "WARNING"  # Investigate, may need action
    CRITICAL = "CRITICAL"  # Immediate action required


# Numeric priority for correct severity comparison (string sort order is wrong)
_ALERT_PRIORITY = {AlertLevel.INFO: 0, AlertLevel.WARNING: 1, AlertLevel.CRITICAL: 2}


class TriggerAction(Enum):
    """Possible trigger actions."""

    NONE = "none"  # No action needed
    MONITOR = "monitor"  # Continue monitoring, no action
    REVIEW = "review"  # Manual review required
    QUEUE_RETRAIN = "queue_retrain"  # Add to retrain queue
    TRIGGER_RETRAIN = "trigger"  # Trigger immediate retraining
    ROLLBACK = "rollback"  # Rollback to previous model


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class TriggerThresholds:
    """
    Thresholds for triggering retraining decisions.

    Based on literature and pipeline documentation:
    - Drift thresholds: z-score of mean shift (Gama et al. 2014; Page 1954 CUSUM)
      2.0σ warn (95th pct), 3.0σ critical (99.7th pct, 3-sigma rule)
    - Confidence/entropy from OOD detection research
    - Temporal metrics from HAR-specific studies
    """

    # Layer 1: Confidence thresholds
    # Keep these aligned with TriggerEvaluationConfig defaults so standalone
    # TriggerPolicyEngine behavior matches pipeline-wired stage-7 behavior.
    confidence_warn: float = 0.65  # Below this triggers WARNING
    confidence_critical: float = 0.50  # Below this triggers CRITICAL
    entropy_warn: float = 1.8  # Above this triggers WARNING
    entropy_critical: float = 2.2  # Above this triggers CRITICAL
    uncertain_ratio_warn: float = 0.20  # Above this triggers WARNING
    uncertain_ratio_critical: float = 0.35  # Above this triggers CRITICAL

    # Layer 2: Temporal thresholds
    flip_rate_warn: float = 0.25  # Above this triggers WARNING
    flip_rate_critical: float = 0.40  # Above this triggers CRITICAL

    # Layer 3: Drift thresholds (per channel)
    # NOTE: the metric computed by post_inference_monitoring is a z-score of
    # mean shift per channel:  |prod_mean - base_mean| / (base_std + 1e-8)
    # NOT the Population Stability Index (PSI). Thresholds are therefore on a
    # standard-normal scale:  2.0σ ≈ 95th-pct, 3.0σ ≈ 99.7th-pct (3-sigma rule).
    # References: Gama et al. 2014 (DDM), Page 1954 (CUSUM), Wald 1947 (SPRT).
    ks_pvalue_threshold: float = 0.01  # Below this = significant drift
    drift_zscore_warn: float = 2.0  # Above this triggers WARNING  (≈95th pct)
    drift_zscore_critical: float = 3.0  # Above this triggers CRITICAL (≈99.7th pct)
    # Multi-channel gating
    min_drifted_channels_warn: int = 2  # At least this many for WARNING
    min_drifted_channels_critical: int = 4  # At least this many for CRITICAL

    # Voting thresholds
    min_signals_for_retrain: int = 2  # Require 2+ signals for retraining
    consecutive_warnings_for_trigger: int = 3  # 3 consecutive WARNINGs = trigger

    # Collapse guard thresholds. The 95% critical value is owned by Stage 6
    # monitoring config so Stage 5/7 do not drift from the dashboard signal.
    dominant_pct_critical: float = (
        PostInferenceMonitoringConfig.dominant_class_critical_threshold
    )
    dominant_pct_static_high_confidence: float = 90.0


@dataclass
class CooldownConfig:
    """Cooldown configuration to prevent rapid successive triggers."""

    retrain_cooldown_hours: int = 24  # Min time between retrains
    alert_cooldown_minutes: int = 30  # Min time between same alerts
    batch_accumulation_min: int = 100  # Min batches before next retrain


@dataclass
class TriggerDecision:
    """Result of trigger evaluation."""

    timestamp: str
    action: TriggerAction
    alert_level: AlertLevel
    should_trigger: bool
    reason: str
    signals: Dict[str, Any]
    metrics_summary: Dict[str, float]
    recommendations: List[str]
    cooldown_active: bool = False
    # Governance fields — always set explicitly; defaults are the safe production values.
    auto_retrain: bool = False          # must remain False for unlabeled production data
    review_required: bool = False       # True when human review is required before any action
    label_required: bool = False        # True when labels/QA gate must be satisfied first
    qa_required: bool = False           # True when data QA is required before retraining
    required_next_steps: List[str] = field(default_factory=list)

    def _decision_label(self) -> str:
        """Map action+governance fields to a human-readable decision token."""
        if self.action in (TriggerAction.NONE, TriggerAction.MONITOR):
            return "HEALTHY"
        if self.action == TriggerAction.QUEUE_RETRAIN:
            return "RETRAIN_CANDIDATE_QUEUED"
        if self.action == TriggerAction.REVIEW:
            if self.label_required:
                return "LABEL_QA_REQUIRED"
            if self.qa_required:
                return "DATA_QA_REQUIRED"
            return "REVIEW_REQUIRED"
        return "REVIEW_REQUIRED"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization.

        Key governance contract:
          should_trigger = False  → no automatic retraining is started
          auto_retrain = False    → explicit guard against any automated retrain path
          review_required = True  → human review is mandatory before proceeding
        These three are independent: review_required=True can coexist with
        should_trigger=False, making it explicit that a REVIEW case is NOT hidden.
        """
        return {
            "timestamp": self.timestamp,
            "decision": self._decision_label(),
            "action": self.action.value,
            "alert_level": self.alert_level.value,
            "should_trigger": self.should_trigger,
            "auto_retrain": self.auto_retrain,
            "review_required": self.review_required,
            "label_required": self.label_required,
            "qa_required": self.qa_required,
            "reason": self.reason,
            "required_next_steps": self.required_next_steps,
            "signals": self.signals,
            "metrics_summary": self.metrics_summary,
            "recommendations": self.recommendations,
        }


# ============================================================================
# TRIGGER POLICY ENGINE
# ============================================================================


class TriggerPolicyEngine:
    """
    Main engine for evaluating retraining trigger policies.

    Implements a multi-metric voting scheme:
    1. Evaluate each metric category independently
    2. Aggregate signals using voting logic
    3. Apply cooldown and history checks
    4. Return final decision

    The 2-of-3 voting scheme requires at least 2 of the following
    to be in WARNING/CRITICAL state:
    - Confidence metrics (mean confidence, entropy, uncertain ratio)
    - Temporal metrics (flip rate, dwell times)
    - Drift metrics (z-score per channel vs baseline)
    """

    def __init__(
        self,
        thresholds: TriggerThresholds = None,
        cooldown_config: CooldownConfig = None,
        state_file: Path = None,
    ):
        """
        Initialize trigger policy engine.

        Args:
            thresholds: Custom thresholds (default: use standard)
            cooldown_config: Cooldown configuration
            state_file: Path to persist state between runs
        """
        self.thresholds = thresholds or TriggerThresholds()
        self.cooldown = cooldown_config or CooldownConfig()
        self.state_file = state_file or (LOGS_DIR / "trigger_state.json")

        # Load or initialize state
        self.state = self._load_state()

        self.logger = logging.getLogger(f"{__name__}.TriggerPolicy")

    def _load_state(self) -> Dict:
        """Load persistent state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")

        return {
            "last_retrain_timestamp": None,
            "warning_count": 0,
            "consecutive_warnings": 0,
            "batches_since_retrain": 0,
            "alert_history": [],
        }

    def _save_state(self):
        """Save state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def evaluate(self, monitoring_report: Dict) -> TriggerDecision:
        """
        Evaluate monitoring report and decide on trigger action.

        Args:
            monitoring_report: Dictionary with monitoring metrics from
                              src.monitoring.post_inference_monitor

        Returns:
            TriggerDecision with action recommendation
        """
        self.logger.info("=" * 60)
        self.logger.info("TRIGGER POLICY EVALUATION")
        self.logger.info("=" * 60)

        timestamp = datetime.now().isoformat()

        # Stage 5→7 collapse guard for unlabeled production data.
        collapse_decision = self._evaluate_collapse_guard(monitoring_report, timestamp)
        if collapse_decision is not None:
            return collapse_decision

        # Extract metrics from report
        confidence_metrics = self._extract_confidence_metrics(monitoring_report)
        temporal_metrics = self._extract_temporal_metrics(monitoring_report)
        drift_metrics = self._extract_drift_metrics(monitoring_report)

        # Evaluate each layer
        confidence_signal = self._evaluate_confidence(confidence_metrics)
        temporal_signal = self._evaluate_temporal(temporal_metrics)
        drift_signal = self._evaluate_drift(drift_metrics)

        signals = {
            "confidence": confidence_signal,
            "temporal": temporal_signal,
            "drift": drift_signal,
        }

        # Log individual signals
        self.logger.info("\nSignal Summary:")
        for name, signal in signals.items():
            self.logger.info(f"  {name}: {signal['level']} - {signal['reason']}")

        # Aggregate signals using voting
        decision = self._aggregate_signals(signals, timestamp)

        # Update state and apply final cooldown gate after any escalation.
        decision = self._update_state(decision)

        # Log decision
        self.logger.info(f"\n{'─' * 60}")
        self.logger.info(f"DECISION: {decision.action.value.upper()}")
        self.logger.info(f"Alert Level: {decision.alert_level.value}")
        self.logger.info(f"Should Trigger: {decision.should_trigger}")
        self.logger.info(f"Reason: {decision.reason}")
        self.logger.info(f"{'─' * 60}")

        return decision

    def _extract_confidence_metrics(self, report: Dict) -> Dict[str, float]:
        """Extract confidence metrics from monitoring report."""
        confidence_report = report.get("confidence_report", {})
        metrics = confidence_report.get("metrics", {})

        return {
            "mean_confidence": metrics.get("mean_confidence", 0.0),
            "mean_entropy": metrics.get("mean_entropy", 0.0),
            "uncertain_ratio": metrics.get("uncertain_ratio", 0.0),
            "std_confidence": metrics.get("std_confidence", 0.0),
        }

    def _extract_temporal_metrics(self, report: Dict) -> Dict[str, float]:
        """Extract temporal metrics from monitoring report."""
        temporal_report = report.get("temporal_report", {})
        metrics = temporal_report.get("metrics", {})

        return {
            "flip_rate": metrics.get("flip_rate", 0.0),
            "mean_dwell_time": metrics.get("mean_dwell_time_seconds", 0.0),
            "short_dwell_ratio": metrics.get("short_dwell_ratio", 0.0),
        }

    def _extract_drift_metrics(self, report: Dict) -> Dict[str, Any]:
        """Extract drift metrics from monitoring report."""
        drift_report = report.get("drift_report", {})

        return {
            "channel_metrics": drift_report.get("per_channel_metrics", {}),
            "n_drifted_channels": drift_report.get("n_drifted_channels", 0),
            "aggregate_drift_score": drift_report.get("aggregate_drift_score", 0.0),
            "drift_detector": drift_report.get("drift_detector", "zscore_mean_shift"),
            "mmd_score": drift_report.get("mmd_score"),
            "mmd_threshold": drift_report.get("mmd_threshold"),
            "mmd_threshold_ratio": drift_report.get("mmd_threshold_ratio"),
            "overall_status": drift_report.get("overall_status", "UNKNOWN"),
        }

    def _evaluate_collapse_guard(
        self, monitoring_report: Dict[str, Any], timestamp: str
    ) -> Optional[TriggerDecision]:
        """Return REVIEW decision when collapse-like signals indicate data/path issues."""
        collapse = monitoring_report.get("collapse_signals", {}) or {}

        collapse_level = str(collapse.get("collapse_level") or "NONE").upper()
        low_motion_collapse_risk = self._to_bool(collapse.get("low_motion_collapse_risk", False))
        low_gyro_motion = self._to_bool(collapse.get("low_gyro_motion", False))
        g_mag_median = self._to_float(collapse.get("g_mag_median"))
        gravity_dominant_axis = collapse.get("gravity_dominant_axis")
        dominant_class = collapse.get("dominant_class")
        dominant_pct = self._to_float(collapse.get("dominant_pct"))
        dominance_warning = self._to_bool(collapse.get("dominance_warning", False))
        mean_confidence = self._to_float(collapse.get("mean_confidence"))
        transition_rate = self._to_float(collapse.get("transition_rate"))

        # Fallback for legacy activity distribution payloads.
        activity_dist = monitoring_report.get("activity_distribution", {})
        if (dominant_pct is None or dominant_class is None) and activity_dist:
            total = sum(activity_dist.values())
            if total > 0:
                dominant_class = max(activity_dist, key=activity_dist.get)
                dominant_pct = (activity_dist[dominant_class] / total) * 100.0

        # User-requested REVIEW conditions:
        # 1) dominance warning true
        # 2) dominant pct >= configured critical threshold
        # 3) dominant pct >= 90 with zero transition and high confidence
        cond_1 = dominance_warning
        cond_2 = (
            dominant_pct is not None
            and dominant_pct >= self.thresholds.dominant_pct_critical
        )
        cond_3 = (
            dominant_pct is not None
            and dominant_pct >= self.thresholds.dominant_pct_static_high_confidence
            and transition_rate is not None
            and abs(transition_rate) <= 1e-12
            and mean_confidence is not None
            and mean_confidence >= 0.92
        )
        cond_4 = collapse_level == "CRITICAL_COLLAPSE"
        cond_5 = low_motion_collapse_risk

        if not (cond_1 or cond_2 or cond_3 or cond_4 or cond_5):
            return None

        # Classify dominance context to distinguish controlled sessions from
        # uncontrolled production collapse.
        # Rule: if the session shows high dominance BUT low gyro motion AND low
        # transition rate, it is likely a controlled/focused single-activity
        # session (e.g., sustained hand_tapping) — not a model collapse.
        is_low_motion_session = low_gyro_motion
        is_low_transition = transition_rate is None or abs(transition_rate) < 5.0
        is_critical_dominance = (
            dominant_pct is not None
            and dominant_pct >= self.thresholds.dominant_pct_critical
        )

        if is_critical_dominance and is_low_motion_session and is_low_transition:
            dominance_context = "CONTROLLED_OR_LOW_MOTION_DOMINANCE"
            collapse_level_tag = "EXPECTED_SINGLE_ACTIVITY_DOMINANCE"
        elif is_critical_dominance:
            dominance_context = "UNCONTROLLED_COLLAPSE_REVIEW"
            collapse_level_tag = "CRITICAL_REVIEW"
        elif dominant_pct is not None and dominant_pct >= self.thresholds.dominant_pct_static_high_confidence:
            dominance_context = "DOMINANCE_WARNING"
            collapse_level_tag = collapse_level
        elif dominance_warning:
            dominance_context = "DOMINANCE_WARNING"
            collapse_level_tag = collapse_level
        else:
            dominance_context = "NO_COLLAPSE"
            collapse_level_tag = collapse_level

        matched = []
        if cond_1:
            matched.append("dominance_warning=true")
        if cond_2:
            matched.append(f"dominant_pct>={self.thresholds.dominant_pct_critical:g}")
        if cond_3:
            matched.append(
                "dominant_pct"
                f">={self.thresholds.dominant_pct_static_high_confidence:g}"
                " & transition_rate==0 & mean_confidence>=0.92"
            )
        if cond_4:
            matched.append("collapse_level=CRITICAL_COLLAPSE")
        if cond_5:
            matched.append("low_motion_collapse_risk=true")

        # Controlled/low-motion sessions warrant WARNING review, not CRITICAL.
        # True uncontrolled collapse or critical structural collapse stays CRITICAL.
        if dominance_context == "CONTROLLED_OR_LOW_MOTION_DOMINANCE":
            alert_level = AlertLevel.WARNING
            action = TriggerAction.REVIEW
            label_req = False
            qa_req = False
            decision_note = "CONTROLLED_ACTIVITY_REVIEW"
        elif cond_4 or cond_5:
            alert_level = AlertLevel.CRITICAL
            action = TriggerAction.REVIEW
            label_req = True
            qa_req = True
            decision_note = "REVIEW_REQUIRED"
        else:
            alert_level = AlertLevel.WARNING
            action = TriggerAction.REVIEW
            label_req = False
            qa_req = True
            decision_note = "DATA_QA_REQUIRED"

        reason = (
            f"{decision_note}: collapse proxy detected. "
            f"dominance_context={dominance_context}, dominant_class={dominant_class}, "
            f"dominant_pct={dominant_pct}, transition_rate={transition_rate}, "
            f"mean_confidence={mean_confidence}. "
            f"collapse_level_tag={collapse_level_tag}, low_gyro_motion={low_gyro_motion}, "
            f"g_mag_median={g_mag_median}, gravity_dominant_axis={gravity_dominant_axis}. "
            f"Matched: {', '.join(matched)}. No auto-retrain."
        )

        return TriggerDecision(
            timestamp=timestamp,
            action=action,
            alert_level=alert_level,
            should_trigger=False,
            auto_retrain=False,
            review_required=True,
            label_required=label_req,
            qa_required=qa_req,
            reason=reason,
            signals={
                "collapse_guard": {
                    "level": alert_level.value,
                    "dominance_context": dominance_context,
                    "collapse_level_tag": collapse_level_tag,
                    "dominance_warning": dominance_warning,
                    "dominant_class": dominant_class,
                    "dominant_pct": dominant_pct,
                    "collapse_level": collapse_level,
                    "low_gyro_motion": low_gyro_motion,
                    "low_motion_collapse_risk": low_motion_collapse_risk,
                    "g_mag_median": g_mag_median,
                    "gravity_dominant_axis": gravity_dominant_axis,
                    "transition_rate": transition_rate,
                    "mean_confidence": mean_confidence,
                    "matched_conditions": matched,
                }
            },
            metrics_summary={
                "dominant_pct": dominant_pct or 0.0,
                "transition_rate": transition_rate or 0.0,
                "mean_confidence": mean_confidence or 0.0,
            },
            recommendations=[
                "Inspect preprocessing path and feature distributions.",
                "Collect labels or perform targeted data QA before retraining.",
                "NO_AUTO_RETRAIN: unlabeled retraining blocked until manual review.",
                "Keep monitoring active; retraining must remain gated.",
            ],
            required_next_steps=[
                f"Review dominance_context={dominance_context} before escalating.",
                "For CONTROLLED_OR_LOW_MOTION sessions: verify session type before flagging.",
                "For UNCONTROLLED_COLLAPSE: inspect sensor path and model input space.",
            ],
        )

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y"}
        return bool(value)

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _evaluate_confidence(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate confidence metrics against thresholds."""
        issues = []
        level = AlertLevel.INFO

        mean_conf = metrics.get("mean_confidence", 1.0)
        mean_entropy = metrics.get("mean_entropy", 0.0)
        uncertain_ratio = metrics.get("uncertain_ratio", 0.0)

        # Check mean confidence
        if mean_conf < self.thresholds.confidence_critical:
            level = AlertLevel.CRITICAL
            issues.append(f"Mean confidence critically low: {mean_conf:.3f}")
        elif mean_conf < self.thresholds.confidence_warn:
            level = max(level, AlertLevel.WARNING, key=lambda x: _ALERT_PRIORITY[x])
            issues.append(f"Mean confidence low: {mean_conf:.3f}")

        # Check entropy
        if mean_entropy > self.thresholds.entropy_critical:
            level = AlertLevel.CRITICAL
            issues.append(f"Entropy critically high: {mean_entropy:.3f}")
        elif mean_entropy > self.thresholds.entropy_warn:
            level = max(level, AlertLevel.WARNING, key=lambda x: _ALERT_PRIORITY[x])
            issues.append(f"Entropy elevated: {mean_entropy:.3f}")

        # Check uncertain ratio
        if uncertain_ratio > self.thresholds.uncertain_ratio_critical:
            level = AlertLevel.CRITICAL
            issues.append(f"Uncertain ratio critically high: {uncertain_ratio:.1%}")
        elif uncertain_ratio > self.thresholds.uncertain_ratio_warn:
            level = max(level, AlertLevel.WARNING, key=lambda x: _ALERT_PRIORITY[x])
            issues.append(f"Uncertain ratio elevated: {uncertain_ratio:.1%}")

        return {
            "level": level.value,
            "issues": issues,
            "reason": "; ".join(issues) if issues else "Confidence metrics normal",
            "metrics": metrics,
        }

    def _evaluate_temporal(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate temporal metrics against thresholds."""
        issues = []
        level = AlertLevel.INFO

        flip_rate = metrics.get("flip_rate", 0.0)

        # Check flip rate
        if flip_rate > self.thresholds.flip_rate_critical:
            level = AlertLevel.CRITICAL
            issues.append(f"Flip rate critically high: {flip_rate:.1%}")
        elif flip_rate > self.thresholds.flip_rate_warn:
            level = max(level, AlertLevel.WARNING, key=lambda x: _ALERT_PRIORITY[x])
            issues.append(f"Flip rate elevated: {flip_rate:.1%}")

        return {
            "level": level.value,
            "issues": issues,
            "reason": "; ".join(issues) if issues else "Temporal metrics normal",
            "metrics": metrics,
        }

    def _evaluate_drift(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate drift metrics against thresholds."""
        issues = []
        level = AlertLevel.INFO

        if metrics.get("drift_detector") == "mmd":
            score = self._to_float(metrics.get("mmd_score"))
            threshold = self._to_float(metrics.get("mmd_threshold"))
            ratio = self._to_float(metrics.get("mmd_threshold_ratio"))
            if threshold > 0 and score > threshold:
                level = AlertLevel.WARNING
                issues.append(
                    f"MMD drift score {score:.6f} exceeds calibrated threshold {threshold:.6f}"
                )
            return {
                "level": level.value,
                "issues": issues,
                "reason": "; ".join(issues) if issues else "MMD drift score below calibrated threshold",
                "metrics": {
                    "drift_detector": "mmd",
                    "mmd_score": score,
                    "mmd_threshold": threshold,
                    "mmd_threshold_ratio": ratio,
                },
            }

        n_drifted = metrics.get("n_drifted_channels", 0)
        channel_metrics = metrics.get("channel_metrics", {})
        aggregate_drift = metrics.get("aggregate_drift_score", 0.0)

        # Count channels exceeding z-score drift thresholds
        drift_zscore_warn_count = 0
        drift_zscore_critical_count = 0

        for channel, ch_metrics in channel_metrics.items():
            # `psi` is kept as a one-release compatibility alias. New producers
            # should emit `drift_zscore` because this metric is not PSI.
            zscore = ch_metrics.get("drift_zscore", ch_metrics.get("psi", 0.0))
            if zscore > self.thresholds.drift_zscore_critical:
                drift_zscore_critical_count += 1
            elif zscore > self.thresholds.drift_zscore_warn:
                drift_zscore_warn_count += 1

        # Evaluate based on number of drifted channels
        if drift_zscore_critical_count >= self.thresholds.min_drifted_channels_critical:
            level = AlertLevel.CRITICAL
            issues.append(
                f"{drift_zscore_critical_count} channels with critical drift (z>{self.thresholds.drift_zscore_critical}σ)"
            )
        elif drift_zscore_warn_count >= self.thresholds.min_drifted_channels_warn:
            level = max(level, AlertLevel.WARNING, key=lambda x: _ALERT_PRIORITY[x])
            issues.append(
                f"{drift_zscore_warn_count} channels with elevated drift (z>{self.thresholds.drift_zscore_warn}σ)"
            )

        # Check aggregate drift score (z-score based)
        if aggregate_drift > self.thresholds.drift_zscore_critical:
            level = AlertLevel.CRITICAL
            issues.append(
                f"Aggregate drift z={aggregate_drift:.3f} exceeds critical threshold {self.thresholds.drift_zscore_critical}σ"
            )
        elif aggregate_drift > self.thresholds.drift_zscore_warn:
            level = max(level, AlertLevel.WARNING, key=lambda x: _ALERT_PRIORITY[x])
            issues.append(
                f"Aggregate drift z={aggregate_drift:.3f} exceeds warning threshold {self.thresholds.drift_zscore_warn}σ"
            )

        # Also check overall drift score
        if n_drifted >= self.thresholds.min_drifted_channels_critical:
            level = AlertLevel.CRITICAL
            issues.append(f"{n_drifted} channels show statistical drift")

        return {
            "level": level.value,
            "issues": issues,
            "reason": "; ".join(issues) if issues else "Drift metrics normal",
            "metrics": {
                "n_drifted_channels": n_drifted,
                "drift_zscore_warn_count": drift_zscore_warn_count,
                "drift_zscore_critical_count": drift_zscore_critical_count,
                "aggregate_drift_score": aggregate_drift,
            },
        }

    def _aggregate_signals(self, signals: Dict[str, Dict], timestamp: str) -> TriggerDecision:
        """
        Aggregate individual signals using voting logic.

        Voting scheme:
        - If ANY signal is CRITICAL → CRITICAL alert, recommend retrain
        - If 2+ signals are WARNING → WARNING alert, queue for retrain
        - If 1 signal is WARNING → INFO alert, continue monitoring
        - If all INFO → INFO, no action
        """
        critical_count = sum(1 for s in signals.values() if s["level"] == "CRITICAL")
        warning_count = sum(1 for s in signals.values() if s["level"] == "WARNING")

        all_reasons = []
        for name, signal in signals.items():
            if signal["issues"]:
                all_reasons.extend(signal["issues"])

        # Compile metrics summary
        metrics_summary = {
            "critical_signals": critical_count,
            "warning_signals": warning_count,
            "total_issues": len(all_reasons),
        }

        # Determine action based on voting.
        # NO_AUTO_RETRAIN: production inference runs on unlabeled data.
        # Even CRITICAL signals require human review + label/QA gate before retraining.
        if critical_count > 0:
            return TriggerDecision(
                timestamp=timestamp,
                action=TriggerAction.REVIEW,
                alert_level=AlertLevel.CRITICAL,
                should_trigger=False,
                auto_retrain=False,
                review_required=True,
                label_required=True,
                qa_required=True,
                reason=f"REVIEW_REQUIRED: {'; '.join(all_reasons[:3])}",
                signals=signals,
                metrics_summary=metrics_summary,
                recommendations=[
                    "REVIEW_REQUIRED: Collect labels or perform data QA before any retraining.",
                    "DATA_QA_REQUIRED: Verify preprocessing path and feature distributions.",
                    "NO_AUTO_RETRAIN: Unlabeled production data alone does not justify retraining.",
                ],
                required_next_steps=[
                    "Inspect monitoring dashboard for drifted channels.",
                    "Collect labeled data or perform targeted data QA.",
                    "Label gate must be satisfied before retraining is queued.",
                ],
            )

        elif warning_count >= self.thresholds.min_signals_for_retrain:
            # 2+ warnings → queue candidate, but still requires label/QA gate
            return TriggerDecision(
                timestamp=timestamp,
                action=TriggerAction.QUEUE_RETRAIN,
                alert_level=AlertLevel.WARNING,
                should_trigger=False,
                auto_retrain=False,
                label_required=True,
                qa_required=False,
                reason=f"RETRAIN_CANDIDATE_QUEUED: {'; '.join(all_reasons[:3])}",
                signals=signals,
                metrics_summary=metrics_summary,
                recommendations=[
                    "RETRAIN_CANDIDATE_QUEUED: Data flagged for retraining queue.",
                    "Monitor for escalation to CRITICAL.",
                    "LABEL_QA_REQUIRED: Provide labels before supervised retraining proceeds.",
                ],
                required_next_steps=[
                    "Review recent data for systematic distribution changes.",
                    "Provide labels or confirm data quality before queuing retraining.",
                ],
            )

        elif warning_count == 1:
            # Single warning → monitor closely
            return TriggerDecision(
                timestamp=timestamp,
                action=TriggerAction.MONITOR,
                alert_level=AlertLevel.WARNING,
                should_trigger=False,
                auto_retrain=False,
                reason=f"Single WARNING signal: {'; '.join(all_reasons)}",
                signals=signals,
                metrics_summary=metrics_summary,
                recommendations=[
                    "Continue monitoring.",
                    "No immediate action required.",
                    "Watch for additional signals before escalating.",
                ],
            )

        else:
            # All normal
            return TriggerDecision(
                timestamp=timestamp,
                action=TriggerAction.NONE,
                alert_level=AlertLevel.INFO,
                should_trigger=False,
                auto_retrain=False,
                reason="HEALTHY: All metrics within normal ranges.",
                signals=signals,
                metrics_summary=metrics_summary,
                recommendations=["System operating normally.", "No action required."],
            )

    def _apply_cooldowns(self, decision: TriggerDecision) -> TriggerDecision:
        """Apply cooldown logic to prevent rapid successive triggers."""
        decision.cooldown_active = False

        if not decision.should_trigger:
            return decision

        last_retrain = self.state.get("last_retrain_timestamp")

        if last_retrain:
            last_retrain_dt = datetime.fromisoformat(last_retrain)
            cooldown_period = timedelta(hours=self.cooldown.retrain_cooldown_hours)

            if datetime.now() - last_retrain_dt < cooldown_period:
                # Still in cooldown period
                time_remaining = cooldown_period - (datetime.now() - last_retrain_dt)

                self.logger.warning(
                    "Trigger suppressed: cooldown active. " f"Time remaining: {time_remaining}"
                )

                decision.should_trigger = False
                decision.action = TriggerAction.QUEUE_RETRAIN
                decision.cooldown_active = True
                decision.recommendations.insert(
                    0, f"Cooldown active - retrain queued (wait {time_remaining.seconds//3600}h)"
                )

        return decision

    def _update_state(self, decision: TriggerDecision) -> TriggerDecision:
        """Update persistent state after evaluation and return the final decision."""
        # Update warning counters
        if decision.alert_level == AlertLevel.WARNING:
            self.state["warning_count"] += 1
            self.state["consecutive_warnings"] += 1
        elif decision.alert_level == AlertLevel.CRITICAL:
            self.state["consecutive_warnings"] += 1
        else:
            self.state["consecutive_warnings"] = 0

        # Consecutive warnings escalate to REVIEW — never to automatic retraining.
        if self.state["consecutive_warnings"] >= self.thresholds.consecutive_warnings_for_trigger:
            decision.should_trigger = False
            decision.action = TriggerAction.REVIEW
            decision.auto_retrain = False
            decision.review_required = True
            decision.label_required = True
            decision.qa_required = True
            decision.reason = (
                f"REVIEW_REQUIRED: {self.state['consecutive_warnings']} consecutive warnings — "
                "label/QA gate required before retraining is queued."
            )

        # Cooldown is the final gate and must win over prior escalation paths.
        decision = self._apply_cooldowns(decision)

        # Update retrain timestamp if triggered
        if decision.should_trigger:
            self.state["last_retrain_timestamp"] = decision.timestamp
            self.state["consecutive_warnings"] = 0
            self.state["batches_since_retrain"] = 0
        else:
            self.state["batches_since_retrain"] += 1

        # Add to alert history
        self.state["alert_history"].append(
            {
                "timestamp": decision.timestamp,
                "level": decision.alert_level.value,
                "action": decision.action.value,
            }
        )

        # Keep only last 100 alerts
        self.state["alert_history"] = self.state["alert_history"][-100:]

        # Save state
        self._save_state()

        return decision

    def get_trigger_summary(self) -> Dict[str, Any]:
        """Get summary of trigger state for reporting."""
        return {
            "warning_count": self.state["warning_count"],
            "consecutive_warnings": self.state["consecutive_warnings"],
            "batches_since_retrain": self.state["batches_since_retrain"],
            "last_retrain": self.state["last_retrain_timestamp"],
            "recent_alerts": self.state["alert_history"][-10:],
        }

    def reset_state(self):
        """Reset state (use after successful retraining)."""
        self.state = {
            "last_retrain_timestamp": datetime.now().isoformat(),
            "warning_count": 0,
            "consecutive_warnings": 0,
            "batches_since_retrain": 0,
            "alert_history": self.state.get("alert_history", []),
        }
        self._save_state()
        self.logger.info("Trigger state reset after retraining")


# ============================================================================
# PROXY VALIDATION FOR NEW MODELS
# ============================================================================


class ProxyModelValidator:
    """
    Validate retrained model against old model using proxy metrics.

    Since we don't have ground-truth labels in production, we compare
    models based on:
    - Mean confidence (higher is better)
    - Entropy (lower is better)
    - Flip rate on same data (lower is better)
    - Prediction stability
    """

    def __init__(self, improvement_threshold: float = 0.05):
        """
        Initialize validator.

        Args:
            improvement_threshold: Min relative improvement required (0.05 = 5%)
        """
        self.improvement_threshold = improvement_threshold
        self.logger = logging.getLogger(f"{__name__}.ProxyValidator")

    def compare_models(
        self, old_predictions: Dict[str, np.ndarray], new_predictions: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """
        Compare old and new model predictions using proxy metrics.

        Args:
            old_predictions: Dict with 'probabilities', 'labels'
            new_predictions: Dict with 'probabilities', 'labels'

        Returns:
            Comparison results with recommendation
        """
        self.logger.info("=" * 60)
        self.logger.info("PROXY MODEL VALIDATION")
        self.logger.info("=" * 60)

        # Compute metrics for both models
        old_metrics = self._compute_proxy_metrics(old_predictions)
        new_metrics = self._compute_proxy_metrics(new_predictions)

        # Compare metrics
        comparisons = {}
        improvements = []

        # Confidence (higher is better)
        conf_diff = new_metrics["mean_confidence"] - old_metrics["mean_confidence"]
        conf_rel_change = conf_diff / max(old_metrics["mean_confidence"], 0.01)
        comparisons["confidence"] = {
            "old": old_metrics["mean_confidence"],
            "new": new_metrics["mean_confidence"],
            "diff": conf_diff,
            "rel_change": conf_rel_change,
            "improved": conf_diff > 0,
        }
        if conf_diff > 0:
            improvements.append("confidence")

        # Entropy (lower is better)
        ent_diff = old_metrics["mean_entropy"] - new_metrics["mean_entropy"]
        ent_rel_change = ent_diff / max(old_metrics["mean_entropy"], 0.01)
        comparisons["entropy"] = {
            "old": old_metrics["mean_entropy"],
            "new": new_metrics["mean_entropy"],
            "diff": ent_diff,
            "rel_change": ent_rel_change,
            "improved": ent_diff > 0,
        }
        if ent_diff > 0:
            improvements.append("entropy")

        # Flip rate (lower is better)
        flip_diff = old_metrics["internal_flip_rate"] - new_metrics["internal_flip_rate"]
        comparisons["flip_rate"] = {
            "old": old_metrics["internal_flip_rate"],
            "new": new_metrics["internal_flip_rate"],
            "diff": flip_diff,
            "improved": flip_diff > 0,
        }
        if flip_diff > 0:
            improvements.append("flip_rate")

        # Overall decision
        n_improved = len(improvements)
        should_deploy = n_improved >= 2  # Require at least 2 improvements

        # Check for significant regression
        has_regression = (
            comparisons["confidence"]["rel_change"] < -self.improvement_threshold
            or comparisons["entropy"]["rel_change"] < -self.improvement_threshold
        )

        if has_regression:
            should_deploy = False
            reason = "New model shows regression in key metrics"
        elif should_deploy:
            reason = f"New model improved in {n_improved}/3 metrics: {improvements}"
        else:
            reason = "Insufficient improvement to justify deployment"

        result = {
            "timestamp": datetime.now().isoformat(),
            "should_deploy": should_deploy,
            "reason": reason,
            "metrics_improved": improvements,
            "n_metrics_improved": n_improved,
            "comparisons": comparisons,
            "old_metrics": old_metrics,
            "new_metrics": new_metrics,
        }

        self.logger.info("\nValidation Result:")
        self.logger.info(f"  Should Deploy: {should_deploy}")
        self.logger.info(f"  Reason: {reason}")
        self.logger.info(f"  Improvements: {improvements}")

        return result

    def _compute_proxy_metrics(self, predictions: Dict) -> Dict[str, float]:
        """Compute proxy metrics from predictions."""
        probs = predictions["probabilities"]
        labels = predictions["labels"]

        # Confidence
        confidence = np.max(probs, axis=1)

        # Entropy
        entropy = -np.sum(probs * np.log(probs + 1e-10), axis=1)

        # Internal flip rate (how often predictions change)
        flip_count = np.sum(labels[1:] != labels[:-1])
        flip_rate = flip_count / max(len(labels) - 1, 1)

        return {
            "mean_confidence": float(np.mean(confidence)),
            "std_confidence": float(np.std(confidence)),
            "mean_entropy": float(np.mean(entropy)),
            "std_entropy": float(np.std(entropy)),
            "internal_flip_rate": float(flip_rate),
            "n_samples": len(labels),
        }


# ============================================================================
# MAIN / CLI
# ============================================================================


def main():
    """CLI for trigger policy evaluation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Evaluate retraining trigger policy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--report", type=str, required=True, help="Path to monitoring report JSON")
    parser.add_argument(
        "--state-file", type=str, default=None, help="Path to state persistence file"
    )
    parser.add_argument("--reset", action="store_true", help="Reset trigger state")
    parser.add_argument("--summary", action="store_true", help="Show trigger state summary")

    args = parser.parse_args()

    # Initialize engine
    state_file = Path(args.state_file) if args.state_file else None
    engine = TriggerPolicyEngine(state_file=state_file)

    if args.reset:
        engine.reset_state()
        print("✓ Trigger state reset")
        return 0

    if args.summary:
        summary = engine.get_trigger_summary()
        print(json.dumps(summary, indent=2))
        return 0

    # Load and evaluate report
    with open(args.report, "r") as f:
        report = json.load(f)

    decision = engine.evaluate(report)

    # Output decision
    print("\n" + "=" * 60)
    print("TRIGGER DECISION")
    print("=" * 60)
    print(json.dumps(decision.to_dict(), indent=2))

    return 0 if not decision.should_trigger else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())

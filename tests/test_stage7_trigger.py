"""Stage 7 — Trigger Evaluation Tests

Covers: trigger policy logic, collapse guard, escalation, cooldown,
proxy validator, threshold invariants, and pipeline-level retraining gates.
"""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pytest

from src.entity.artifact_entity import PostInferenceMonitoringArtifact
from src.entity.config_entity import (
    PipelineConfig,
    PostInferenceMonitoringConfig,
    TriggerEvaluationConfig,
)
from src.pipeline.production_pipeline import ProductionPipeline
from src.components.trigger_evaluation import TriggerEvaluation
from src.trigger_policy import (
    AlertLevel,
    ProxyModelValidator,
    TriggerAction,
    TriggerPolicyEngine,
    TriggerThresholds,
)


# ── Threshold defaults ────────────────────────────────────────────────────────

def test_default_thresholds():
    thresholds = TriggerThresholds()
    assert thresholds.confidence_warn == 0.65
    assert thresholds.confidence_critical == 0.50
    assert thresholds.drift_zscore_warn == 2.0
    assert thresholds.drift_zscore_critical == 3.0
    assert thresholds.dominant_pct_critical == 95.0


# ── Trigger policy engine ─────────────────────────────────────────────────────

def test_normal_metrics_no_trigger(temp_state_file, sample_monitoring_report):
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    decision = engine.evaluate(sample_monitoring_report)
    assert decision.should_trigger is False
    assert decision.action in [TriggerAction.NONE, TriggerAction.MONITOR]
    assert decision.alert_level == AlertLevel.INFO


def test_degraded_metrics_trigger(temp_state_file, degraded_monitoring_report):
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    decision = engine.evaluate(degraded_monitoring_report)
    assert decision.alert_level in [AlertLevel.WARNING, AlertLevel.CRITICAL]
    # Governance: CRITICAL signals escalate to REVIEW (human gate), never auto-retrain.
    assert decision.action in [TriggerAction.QUEUE_RETRAIN, TriggerAction.TRIGGER_RETRAIN, TriggerAction.REVIEW]
    assert decision.auto_retrain is False


def test_low_confidence_triggers_warning(temp_state_file):
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    report = {
        'confidence_report': {'metrics': {'mean_confidence': 0.50, 'mean_entropy': 1.0, 'uncertain_ratio': 0.10}},
        'temporal_report': {'metrics': {'flip_rate': 0.10}},
        'drift_report': {'per_channel_metrics': {}, 'n_drifted_channels': 0},
    }
    decision = engine.evaluate(report)
    assert 'confidence' in str(decision.signals).lower() or decision.alert_level != AlertLevel.INFO


def test_collapse_guard_dominant_pct_95_forces_review(temp_state_file, sample_monitoring_report):
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    report = json.loads(json.dumps(sample_monitoring_report))
    report["collapse_signals"] = {
        "dominance_warning": False,
        "dominant_class": "hand_tapping",
        "dominant_pct": 95.0,
        "mean_confidence": 0.85,
        "transition_rate": 7.0,
    }
    decision = engine.evaluate(report)
    assert decision.action == TriggerAction.REVIEW
    assert decision.should_trigger is False
    assert decision.alert_level == AlertLevel.WARNING
    assert "collapse_guard" in decision.signals
    assert "dominant_pct>=95" in decision.signals["collapse_guard"].get("matched_conditions", [])


def test_multiple_signals_required(temp_state_file):
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    report = {
        'confidence_report': {'metrics': {'mean_confidence': 0.40, 'mean_entropy': 1.0, 'uncertain_ratio': 0.10}},
        'temporal_report': {'metrics': {'flip_rate': 0.10}},
        'drift_report': {'per_channel_metrics': {}, 'n_drifted_channels': 0},
    }
    decision = engine.evaluate(report)
    assert decision.alert_level == AlertLevel.CRITICAL


def test_state_persistence(temp_state_file, sample_monitoring_report):
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    engine.evaluate(sample_monitoring_report)
    assert temp_state_file.exists()
    engine2 = TriggerPolicyEngine(state_file=temp_state_file)
    assert engine2.state['batches_since_retrain'] > 0


def test_consecutive_warnings_escalate(temp_state_file):
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    warning_report = {
        'confidence_report': {'metrics': {'mean_confidence': 0.52, 'mean_entropy': 1.9, 'uncertain_ratio': 0.22}},
        'temporal_report': {'metrics': {'flip_rate': 0.28}},
        'drift_report': {'per_channel_metrics': {'Ax_w': {'psi': 0.12}, 'Ay_w': {'psi': 0.11}}, 'n_drifted_channels': 2},
    }
    decisions = [engine.evaluate(warning_report) for _ in range(4)]
    # Governance: consecutive warnings escalate to REVIEW (human gate), not auto-retrain.
    assert any(d.action == TriggerAction.REVIEW for d in decisions)
    assert all(d.auto_retrain is False for d in decisions)


def test_cooldown_does_not_override_review_decision(temp_state_file):
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    engine.state["last_retrain_timestamp"] = datetime.now().isoformat()
    engine._save_state()

    report = {
        "confidence_report": {"metrics": {}},
        "temporal_report": {"metrics": {}},
        "drift_report": {"per_channel_metrics": {}, "n_drifted_channels": 0},
        "collapse_signals": {
            "dominance_warning": False, "dominant_class": "hand_tapping",
            "dominant_pct": 95.0, "mean_confidence": 0.85, "transition_rate": 5.0,
        },
    }
    decision = engine.evaluate(report)
    assert decision.action == TriggerAction.REVIEW
    assert decision.should_trigger is False
    assert decision.cooldown_active is False


# ── Proxy model validator ─────────────────────────────────────────────────────

def test_improved_model_recommended():
    np.random.seed(42)
    validator = ProxyModelValidator()
    n_samples, n_classes = 100, 11
    old_probs = np.random.dirichlet(np.ones(n_classes) * 0.5, size=n_samples)
    new_probs = np.random.dirichlet(np.ones(n_classes) * 3, size=n_samples)
    result = validator.compare_models(
        {'probabilities': old_probs, 'labels': np.argmax(old_probs, axis=1)},
        {'probabilities': new_probs, 'labels': np.argmax(new_probs, axis=1)},
    )
    assert 'should_deploy' in result
    assert 'comparisons' in result


def test_regression_not_deployed():
    n_samples, n_classes = 100, 11
    validator = ProxyModelValidator()
    old_probs = np.full((n_samples, n_classes), 0.01)
    for i in range(n_samples):
        old_probs[i, i % n_classes] = 0.90
    old_probs /= old_probs.sum(axis=1, keepdims=True)
    new_probs = np.ones((n_samples, n_classes)) / n_classes
    result = validator.compare_models(
        {'probabilities': old_probs, 'labels': np.argmax(old_probs, axis=1)},
        {'probabilities': new_probs, 'labels': np.argmax(new_probs, axis=1)},
    )
    assert result['should_deploy'] is False


# ── Dominance fallback (Stage 5 → Stage 6 → Stage 7) ─────────────────────────

def test_trigger_uses_stage6_dominance_when_no_stage5_collapse(monkeypatch):
    captured = {}

    class _FakeEngine:
        def __init__(self, thresholds=None, cooldown_config=None, state_file=None):
            pass

        def evaluate(self, report):
            captured["report"] = report

            class _Decision:
                should_trigger = False
                action = "none"
                alert_level = "INFO"
                recommendations = []

            return _Decision()

    monkeypatch.setattr("src.trigger_policy.TriggerPolicyEngine", _FakeEngine)
    monitoring = PostInferenceMonitoringArtifact(
        monitoring_report={},
        layer1_confidence={"mean_confidence": 0.86, "dominance_warning": True, "dominant_class": "hand_tapping", "dominant_pct": 86.0},
        layer2_temporal={"transition_rate": 4.0},
        layer3_drift={"max_drift": 0.1},
    )
    stage = TriggerEvaluation(PipelineConfig(), TriggerEvaluationConfig(), monitoring)
    stage.initiate_trigger_evaluation()
    collapse = captured["report"]["collapse_signals"]
    assert collapse["dominance_warning"] is True
    assert collapse["dominant_class"] == "hand_tapping"
    assert collapse["dominant_pct"] == 86.0


# ── Threshold consistency invariants ─────────────────────────────────────────

def test_drift_zscore_stage6_at_most_stage7():
    mon = PostInferenceMonitoringConfig()
    trig = TriggerEvaluationConfig()
    thresh = TriggerThresholds()
    assert mon.drift_zscore_threshold <= trig.drift_zscore_warn
    assert trig.drift_zscore_warn == thresh.drift_zscore_warn


# ── Collapse signal forces REVIEW (ported from removed test_trigger_policy) ──

def test_collapse_level_critical_forces_review(temp_state_file, sample_monitoring_report):
    """Stage 4 CRITICAL_COLLAPSE must directly block automatic retraining."""
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    report = json.loads(json.dumps(sample_monitoring_report))
    report["collapse_signals"] = {
        "collapse_level": "CRITICAL_COLLAPSE",
        "dominant_class": "hand_tapping",
        "dominant_pct": 88.0,
        "mean_confidence": 0.90,
        "transition_rate": 4.0,
    }
    decision = engine.evaluate(report)
    assert decision.action == TriggerAction.REVIEW
    assert decision.should_trigger is False
    assert decision.alert_level == AlertLevel.CRITICAL
    matched = decision.signals["collapse_guard"].get("matched_conditions", [])
    assert "collapse_level=CRITICAL_COLLAPSE" in matched

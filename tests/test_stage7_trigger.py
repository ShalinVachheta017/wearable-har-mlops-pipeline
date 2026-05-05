"""Stage 7 — Trigger Evaluation Tests

Covers: trigger policy logic, threshold pass-through, collapse guard,
threshold consistency invariants.
"""
from __future__ import annotations

import json
import sys
import types
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
from unittest.mock import patch

from src.components.post_inference_monitoring import PostInferenceMonitoring
from src.components.trigger_evaluation import TriggerEvaluation
from src.entity.artifact_entity import ModelInferenceArtifact, PostInferenceMonitoringArtifact
from src.entity.config_entity import (
    PipelineConfig,
    PostInferenceMonitoringConfig,
    TriggerEvaluationConfig,
)
from src.pipeline.production_pipeline import ProductionPipeline
from src.trigger_policy import (
    AlertLevel,
    ProxyModelValidator,
    TriggerAction,
    TriggerPolicyEngine,
    TriggerThresholds,
)


# ── Threshold defaults ────────────────────────────────────────────────────────

class TestTriggerThresholds:
    def test_default_thresholds(self):
        thresholds = TriggerThresholds()
        assert thresholds.confidence_warn == 0.65
        assert thresholds.confidence_critical == 0.50
        assert thresholds.drift_zscore_warn == 2.0
        assert thresholds.drift_zscore_critical == 3.0
        assert thresholds.dominant_pct_critical == 95.0

    def test_custom_thresholds(self):
        thresholds = TriggerThresholds(confidence_warn=0.60, drift_zscore_critical=0.30)
        assert thresholds.confidence_warn == 0.60
        assert thresholds.drift_zscore_critical == 0.30


# ── Trigger policy engine ─────────────────────────────────────────────────────

class TestTriggerPolicyEngine:
    def test_engine_initialization(self, temp_state_file):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        assert engine.thresholds is not None
        assert engine.cooldown is not None
        assert engine.state is not None

    def test_normal_metrics_no_trigger(self, temp_state_file, sample_monitoring_report):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        decision = engine.evaluate(sample_monitoring_report)
        assert decision.should_trigger is False
        assert decision.action in [TriggerAction.NONE, TriggerAction.MONITOR]
        assert decision.alert_level == AlertLevel.INFO

    def test_degraded_metrics_trigger(self, temp_state_file, degraded_monitoring_report):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        decision = engine.evaluate(degraded_monitoring_report)
        assert decision.alert_level in [AlertLevel.WARNING, AlertLevel.CRITICAL]
        # Governance: CRITICAL signals escalate to REVIEW (human gate), never auto-retrain.
        assert decision.action in [TriggerAction.QUEUE_RETRAIN, TriggerAction.TRIGGER_RETRAIN, TriggerAction.REVIEW]
        assert decision.auto_retrain is False

    def test_low_confidence_triggers_warning(self, temp_state_file):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        report = {
            'confidence_report': {'metrics': {'mean_confidence': 0.50, 'mean_entropy': 1.0, 'uncertain_ratio': 0.10}},
            'temporal_report': {'metrics': {'flip_rate': 0.10}},
            'drift_report': {'per_channel_metrics': {}, 'n_drifted_channels': 0},
        }
        decision = engine.evaluate(report)
        assert 'confidence' in str(decision.signals).lower() or decision.alert_level != AlertLevel.INFO

    def test_drift_zscore_key_replaces_psi_alias(self, temp_state_file):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        report = {
            "confidence_report": {"metrics": {"mean_confidence": 0.90, "mean_entropy": 1.0, "uncertain_ratio": 0.01}},
            "temporal_report": {"metrics": {"flip_rate": 0.10}},
            "drift_report": {
                "per_channel_metrics": {"Ax_w": {"drift_zscore": 2.2}, "Ay_w": {"drift_zscore": 2.1}},
                "n_drifted_channels": 0,
                "aggregate_drift_score": 0.0,
            },
        }
        decision = engine.evaluate(report)
        assert decision.signals["drift"]["level"] == AlertLevel.WARNING.value

    def test_collapse_guard_dominant_pct_95_forces_review(self, temp_state_file, sample_monitoring_report):
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

    def test_collapse_guard_below_95_does_not_review_by_itself(self, temp_state_file, sample_monitoring_report):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        report = json.loads(json.dumps(sample_monitoring_report))
        report["collapse_signals"] = {
            "dominance_warning": False, "dominant_class": "hand_tapping",
            "dominant_pct": 94.9, "mean_confidence": 0.80, "transition_rate": 5.0,
        }
        decision = engine.evaluate(report)
        assert decision.action in [TriggerAction.NONE, TriggerAction.MONITOR]
        assert decision.should_trigger is False
        assert decision.alert_level == AlertLevel.INFO

    def test_multiple_signals_required(self, temp_state_file):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        report = {
            'confidence_report': {'metrics': {'mean_confidence': 0.40, 'mean_entropy': 1.0, 'uncertain_ratio': 0.10}},
            'temporal_report': {'metrics': {'flip_rate': 0.10}},
            'drift_report': {'per_channel_metrics': {}, 'n_drifted_channels': 0},
        }
        decision = engine.evaluate(report)
        assert decision.alert_level == AlertLevel.CRITICAL

    def test_state_persistence(self, temp_state_file, sample_monitoring_report):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        engine.evaluate(sample_monitoring_report)
        assert temp_state_file.exists()
        engine2 = TriggerPolicyEngine(state_file=temp_state_file)
        assert engine2.state['batches_since_retrain'] > 0

    def test_state_reset(self, temp_state_file, sample_monitoring_report):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        engine.evaluate(sample_monitoring_report)
        engine.evaluate(sample_monitoring_report)
        engine.reset_state()
        assert engine.state['warning_count'] == 0
        assert engine.state['consecutive_warnings'] == 0
        assert engine.state['batches_since_retrain'] == 0

    def test_trigger_summary(self, temp_state_file, sample_monitoring_report):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        engine.evaluate(sample_monitoring_report)
        summary = engine.get_trigger_summary()
        assert 'warning_count' in summary
        assert 'consecutive_warnings' in summary
        assert 'batches_since_retrain' in summary


class TestConsecutiveWarnings:
    def test_consecutive_warnings_escalate(self, temp_state_file):
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


class TestCooldownOrdering:
    def test_consecutive_warnings_at_threshold_produce_review_not_retrain(self, temp_state_file):
        # Governance: consecutive warnings escalate to REVIEW (human gate), not auto-retrain.
        # Cooldown is irrelevant here since should_trigger is never set to True.
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        previous_retrain = datetime.now().isoformat()
        engine.state["last_retrain_timestamp"] = previous_retrain
        engine.state["consecutive_warnings"] = engine.thresholds.consecutive_warnings_for_trigger - 1
        engine._save_state()

        warning_report = {
            "confidence_report": {"metrics": {"mean_confidence": 0.60, "mean_entropy": 1.0, "uncertain_ratio": 0.10}},
            "temporal_report": {"metrics": {"flip_rate": 0.10}},
            "drift_report": {"per_channel_metrics": {}, "n_drifted_channels": 0, "aggregate_drift_score": 0.0},
        }
        decision = engine.evaluate(warning_report)
        assert decision.should_trigger is False
        assert decision.auto_retrain is False
        assert decision.action == TriggerAction.REVIEW
        assert decision.review_required is True
        assert engine.state["last_retrain_timestamp"] == previous_retrain

    def test_cooldown_does_not_override_review_decision(self, temp_state_file):
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


class TestProxyModelValidator:
    def test_validator_initialization(self):
        validator = ProxyModelValidator(improvement_threshold=0.05)
        assert validator.improvement_threshold == 0.05

    def test_improved_model_recommended(self):
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

    def test_regression_not_deployed(self):
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


class TestAlertLevels:
    def test_info_level_for_normal(self, temp_state_file, sample_monitoring_report):
        decision = TriggerPolicyEngine(state_file=temp_state_file).evaluate(sample_monitoring_report)
        assert decision.alert_level == AlertLevel.INFO

    def test_critical_for_severe_degradation(self, temp_state_file, degraded_monitoring_report):
        decision = TriggerPolicyEngine(state_file=temp_state_file).evaluate(degraded_monitoring_report)
        assert decision.alert_level in [AlertLevel.WARNING, AlertLevel.CRITICAL]


# ── Threshold pass-through ────────────────────────────────────────────────────

def test_trigger_temporal_thresholds_pass_through(monkeypatch, tmp_path):
    captured = {}

    class _FakeEngine:
        def __init__(self, thresholds=None, cooldown_config=None, state_file=None):
            captured["thresholds"] = thresholds

        def evaluate(self, report):
            class _Decision:
                should_trigger = False
                action = "none"
                alert_level = "INFO"
                recommendations = []
            return _Decision()

    monkeypatch.setattr("src.trigger_policy.TriggerPolicyEngine", _FakeEngine)
    cfg = TriggerEvaluationConfig(temporal_flip_warn=0.17, temporal_flip_critical=0.31)
    monitoring = PostInferenceMonitoringArtifact(
        monitoring_report={},
        layer1_confidence={"mean_confidence": 0.9},
        layer2_temporal={"transition_rate": 4.0},
        layer3_drift={"max_drift": 0.1},
    )
    stage = TriggerEvaluation(PipelineConfig(), cfg, monitoring)
    stage.initiate_trigger_evaluation()
    thresholds = captured["thresholds"]
    assert thresholds.flip_rate_warn == 0.17
    assert thresholds.flip_rate_critical == 0.31


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


# ── Collapse guard (pipeline level) ──────────────────────────────────────────

def test_unlabeled_pseudo_label_retraining_blocked_on_critical_collapse():
    pipeline = ProductionPipeline.__new__(ProductionPipeline)
    ctx = {"dataset_has_labels": False, "collapse_signals": {"collapse_level": "CRITICAL_COLLAPSE"}}
    assert pipeline._should_block_unlabeled_retraining(ctx, "pseudo_label", {"adabn", "tent", "adabn_tent", "pseudo_label"}) is True


def test_labeled_retraining_not_blocked_by_collapse_guard():
    pipeline = ProductionPipeline.__new__(ProductionPipeline)
    ctx = {"dataset_has_labels": True, "collapse_signals": {"collapse_level": "CRITICAL_COLLAPSE"}}
    assert pipeline._should_block_unlabeled_retraining(ctx, "pseudo_label", {"adabn", "tent", "adabn_tent", "pseudo_label"}) is False


def test_unlabeled_retraining_blocked_on_low_motion_collapse_risk():
    pipeline = ProductionPipeline.__new__(ProductionPipeline)
    ctx = {"dataset_has_labels": False, "collapse_signals": {"low_motion_collapse_risk": "true"}}
    assert pipeline._should_block_unlabeled_retraining(ctx, "tent", {"adabn", "tent", "adabn_tent", "pseudo_label"}) is True


# ── Threshold consistency invariants ─────────────────────────────────────────

def test_drift_zscore_stage6_at_most_stage7():
    mon = PostInferenceMonitoringConfig()
    trig = TriggerEvaluationConfig()
    thresh = TriggerThresholds()
    assert mon.drift_zscore_threshold <= trig.drift_zscore_warn
    assert trig.drift_zscore_warn == thresh.drift_zscore_warn


def test_monitoring_confidence_warn_geq_trigger_confidence_warn():
    mon = PostInferenceMonitoringConfig()
    trig = TriggerEvaluationConfig()
    assert mon.confidence_warn_threshold >= trig.confidence_warn


def test_trigger_policy_defaults_align_with_trigger_config():
    trig = TriggerEvaluationConfig()
    thresh = TriggerThresholds()
    assert thresh.confidence_warn == pytest.approx(trig.confidence_warn)
    assert thresh.confidence_critical == pytest.approx(trig.confidence_critical)


def test_uncertain_window_threshold_is_probability():
    mon = PostInferenceMonitoringConfig()
    assert 0.0 < mon.uncertain_window_threshold <= 1.0


def test_uncertain_pct_threshold_positive():
    mon = PostInferenceMonitoringConfig()
    assert 0.0 < mon.uncertain_pct_threshold <= 100.0


def test_monitoring_and_api_use_same_config_class():
    from src.entity.config_entity import PostInferenceMonitoringConfig as Cfg
    cfg = Cfg()
    required_fields = [
        "confidence_warn_threshold", "uncertain_pct_threshold",
        "uncertain_window_threshold", "transition_rate_threshold",
        "drift_zscore_threshold", "dominant_class_warn_threshold",
        "dominant_class_critical_threshold",
    ]
    for field in required_fields:
        assert hasattr(cfg, field), f"PostInferenceMonitoringConfig is missing field: {field}"


def test_pipeline_and_api_share_same_monitoring_overrides(monkeypatch):
    import src.utils.config_loader as config_loader
    overrides = {
        "monitoring": {
            "confidence_warn_threshold": 0.72,
            "uncertain_pct_threshold": 22.0,
            "transition_rate_threshold": 44.0,
            "drift_zscore_threshold": 1.7,
        }
    }
    monkeypatch.setattr(config_loader, "load_yaml_overrides", lambda path=None: overrides)
    pipeline_cfg = config_loader.load_monitoring_config()
    from src.api import app as app_module
    api_cfg = app_module._load_monitoring_thresholds()
    assert api_cfg.confidence_warn_threshold == pytest.approx(pipeline_cfg.confidence_warn_threshold)
    assert api_cfg.uncertain_pct_threshold == pytest.approx(pipeline_cfg.uncertain_pct_threshold)
    assert api_cfg.transition_rate_threshold == pytest.approx(pipeline_cfg.transition_rate_threshold)
    assert api_cfg.drift_zscore_threshold == pytest.approx(pipeline_cfg.drift_zscore_threshold)


def test_stage6_thresholds_pass_through_to_runtime_monitor(monkeypatch, tmp_path):
    captured = {}

    class _FakeMonitor:
        def __init__(self, **kwargs):
            captured["init_kwargs"] = kwargs

        def run(self, **kwargs):
            captured["run_kwargs"] = kwargs
            class _Report:
                overall_status = "PASS"
                layer1_confidence = {"status": "PASS"}
                layer2_temporal = {"status": "PASS"}
                layer3_drift = {"status": "SKIPPED"}
            return _Report()

    monkeypatch.setitem(
        sys.modules,
        "src.monitoring.post_inference_monitor",
        types.SimpleNamespace(PostInferenceMonitor=_FakeMonitor),
    )

    predictions_csv = tmp_path / "predictions.csv"
    predictions_csv.write_text("confidence,predicted_activity\n0.90,sitting\n", encoding="utf-8")

    inference_artifact = ModelInferenceArtifact(
        predictions_csv_path=predictions_csv,
        predictions_npy_path=tmp_path / "predictions.npy",
        probabilities_npy_path=tmp_path / "probabilities.npy",
        n_predictions=1,
    )

    cfg = PostInferenceMonitoringConfig(
        predictions_csv=predictions_csv,
        output_dir=tmp_path / "monitoring_output",
        confidence_warn_threshold=0.71,
        uncertain_window_threshold=0.44,
        uncertain_pct_threshold=22.0,
        transition_rate_threshold=37.0,
        drift_zscore_threshold=1.9,
        dominant_class_warn_threshold=84.0,
        dominant_class_critical_threshold=94.0,
        calibration_temperature=1.3,
    )

    stage = PostInferenceMonitoring(
        pipeline_config=PipelineConfig(),
        config=cfg,
        inference_artifact=inference_artifact,
    )
    artifact = stage.initiate_post_inference_monitoring()
    init_kwargs = captured["init_kwargs"]

    assert init_kwargs["confidence_warn_threshold"] == pytest.approx(0.71)
    assert init_kwargs["confidence_threshold"] == pytest.approx(0.44)
    assert init_kwargs["uncertain_threshold_pct"] == pytest.approx(22.0)
    assert init_kwargs["transition_rate_threshold"] == pytest.approx(37.0)
    assert init_kwargs["drift_threshold"] == pytest.approx(1.9)
    assert init_kwargs["dominant_class_warn_threshold"] == pytest.approx(84.0)
    assert init_kwargs["dominant_class_critical_threshold"] == pytest.approx(94.0)
    assert init_kwargs["calibration_temperature"] == pytest.approx(1.3)
    assert artifact.overall_status == "PASS"

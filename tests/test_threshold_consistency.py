"""
P1-3: Threshold Consistency Tests
==================================
Assert that monitoring config, trigger config, and alert rules
use aligned threshold values (tiered alerting is intentional, but
drift/entropy must be exactly consistent).
"""

import pytest
import sys
import types

from src.components.post_inference_monitoring import PostInferenceMonitoring
from src.entity.artifact_entity import ModelInferenceArtifact
from src.entity.config_entity import (
    PipelineConfig,
    PostInferenceMonitoringConfig,
    TriggerEvaluationConfig,
)
from src.trigger_policy import TriggerThresholds


def test_drift_zscore_stage6_at_most_stage7():
    """
    A28 tiered alerting (2026-04-21): Stage 6 warns EARLIER than Stage 7 on the same
    metric, so Stage 6 drift threshold must be <= Stage 7 drift warn. Stage 7 trigger
    threshold remains the citation-backed 2.0σ; Stage 6 fires at 1.8σ to give
    dashboards earlier visibility before the voting policy escalates.
    """
    mon = PostInferenceMonitoringConfig()
    trig = TriggerEvaluationConfig()
    thresh = TriggerThresholds()

    assert mon.drift_zscore_threshold <= trig.drift_zscore_warn, (
        f"Stage 6 drift must be at most Stage 7 drift (tiered). "
        f"monitoring={mon.drift_zscore_threshold}, trigger={trig.drift_zscore_warn}"
    )
    # TriggerThresholds and TriggerEvaluationConfig must stay aligned.
    assert trig.drift_zscore_warn == thresh.drift_zscore_warn, (
        f"trigger_eval.drift_zscore_warn={trig.drift_zscore_warn} "
        f"!= trigger_policy.drift_zscore_warn={thresh.drift_zscore_warn}"
    )


def test_monitoring_confidence_warn_geq_trigger_confidence_warn():
    """
    A28 tiered alerting (2026-04-21): Stage 6 must warn at HIGHER confidence than
    Stage 7's trigger. On mean_conf=0.68 Stage 6 warns but Stage 7 does not escalate
    — this is the early-indicator story from thesis ch6 Threshold Calibration Gap.
    """
    mon = PostInferenceMonitoringConfig()
    trig = TriggerEvaluationConfig()

    assert mon.confidence_warn_threshold >= trig.confidence_warn, (
        "Monitoring warning must be >= trigger warning (tiered alerting invariant). "
        f"monitoring={mon.confidence_warn_threshold}, trigger={trig.confidence_warn}"
    )


def test_trigger_policy_defaults_align_with_trigger_config():
    """TriggerPolicyEngine defaults should match TriggerEvaluationConfig defaults."""
    trig = TriggerEvaluationConfig()
    thresh = TriggerThresholds()

    assert thresh.confidence_warn == pytest.approx(trig.confidence_warn)
    assert thresh.confidence_critical == pytest.approx(trig.confidence_critical)


def test_uncertain_window_threshold_is_probability():
    """uncertain_window_threshold must be a valid probability in (0, 1]."""
    mon = PostInferenceMonitoringConfig()
    assert 0.0 < mon.uncertain_window_threshold <= 1.0, (
        f"uncertain_window_threshold={mon.uncertain_window_threshold} must be in (0, 1]"
    )


def test_uncertain_pct_threshold_positive():
    mon = PostInferenceMonitoringConfig()
    assert 0.0 < mon.uncertain_pct_threshold <= 100.0, (
        f"uncertain_pct_threshold={mon.uncertain_pct_threshold} must be in (0, 100]"
    )


def test_monitoring_and_api_use_same_config_class():
    """
    app.py imports PostInferenceMonitoringConfig — importing it must not crash
    and must expose all fields consumed by the API.
    """
    from src.entity.config_entity import PostInferenceMonitoringConfig as Cfg
    cfg = Cfg()
    required_fields = [
        "confidence_warn_threshold",
        "uncertain_pct_threshold",
        "uncertain_window_threshold",
        "transition_rate_threshold",
        "drift_zscore_threshold",
        "dominant_class_warn_threshold",
        "dominant_class_critical_threshold",
    ]
    for field in required_fields:
        assert hasattr(cfg, field), f"PostInferenceMonitoringConfig is missing field: {field}"


def test_pipeline_and_api_share_same_monitoring_overrides(monkeypatch):
    """HAR_PIPELINE_OVERRIDES must drive the same monitoring thresholds in pipeline and API."""
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

    assert api_cfg.confidence_warn_threshold == pytest.approx(
        pipeline_cfg.confidence_warn_threshold
    )
    assert api_cfg.uncertain_pct_threshold == pytest.approx(
        pipeline_cfg.uncertain_pct_threshold
    )
    assert api_cfg.transition_rate_threshold == pytest.approx(
        pipeline_cfg.transition_rate_threshold
    )
    assert api_cfg.drift_zscore_threshold == pytest.approx(
        pipeline_cfg.drift_zscore_threshold
    )


def test_stage6_thresholds_pass_through_to_runtime_monitor(monkeypatch, tmp_path):
    """Stage-6 wrapper must pass configured thresholds into PostInferenceMonitor."""
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
    predictions_csv.write_text(
        "confidence,predicted_activity\n0.90,sitting\n",
        encoding="utf-8",
    )

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

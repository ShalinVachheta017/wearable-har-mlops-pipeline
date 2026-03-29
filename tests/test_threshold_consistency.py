"""
P1-3: Threshold Consistency Tests
==================================
Assert that monitoring config, trigger config, and alert rules
use aligned threshold values (tiered alerting is intentional, but
drift/entropy must be exactly consistent).
"""

import pytest
from src.entity.config_entity import PostInferenceMonitoringConfig, TriggerEvaluationConfig
from src.trigger_policy import TriggerThresholds


def test_drift_zscore_consistent_across_all_sources():
    """Layer-3 drift z-score warn threshold must be identical in monitoring AND trigger."""
    mon = PostInferenceMonitoringConfig()
    trig = TriggerEvaluationConfig()
    thresh = TriggerThresholds()

    assert mon.drift_zscore_threshold == trig.drift_zscore_warn, (
        f"drift_zscore mismatch: monitoring.drift_zscore_threshold={mon.drift_zscore_threshold} "
        f"!= trigger_eval.drift_zscore_warn={trig.drift_zscore_warn}"
    )
    assert mon.drift_zscore_threshold == thresh.drift_zscore_warn, (
        f"drift_zscore mismatch: monitoring.drift_zscore_threshold={mon.drift_zscore_threshold} "
        f"!= trigger_policy.drift_zscore_warn={thresh.drift_zscore_warn}"
    )


def test_trigger_confidence_warn_geq_monitoring_warn():
    """
    Tiered alerting: trigger fires at a higher (stricter) confidence threshold
    than the monitoring layer-1 WARNING.  The trigger must NOT be more lenient.
    """
    mon = PostInferenceMonitoringConfig()
    trig = TriggerEvaluationConfig()

    assert trig.confidence_warn >= mon.confidence_warn_threshold, (
        "Trigger confidence threshold must be >= monitoring warning threshold "
        "(tiered alerting invariant violated). "
        f"trigger={trig.confidence_warn}, monitoring={mon.confidence_warn_threshold}"
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

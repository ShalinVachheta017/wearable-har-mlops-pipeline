from src.components.trigger_evaluation import TriggerEvaluation
from src.entity.artifact_entity import PostInferenceMonitoringArtifact
from src.entity.config_entity import PipelineConfig, TriggerEvaluationConfig


def test_trigger_temporal_thresholds_pass_through(monkeypatch):
    captured = {}

    class _FakeEngine:
        def __init__(self, thresholds=None, cooldown_config=None, state_file=None):
            captured["thresholds"] = thresholds
            captured["cooldown"] = cooldown_config
            captured["state_file"] = state_file

        def evaluate(self, report):
            class _Decision:
                should_trigger = False
                action = "none"
                alert_level = "INFO"
                recommendations = []

            return _Decision()

    monkeypatch.setattr("src.trigger_policy.TriggerPolicyEngine", _FakeEngine)

    cfg = TriggerEvaluationConfig(
        temporal_flip_warn=0.17,
        temporal_flip_critical=0.31,
    )
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
        layer1_confidence={
            "mean_confidence": 0.86,
            "dominance_warning": True,
            "dominant_class": "hand_tapping",
            "dominant_pct": 86.0,
        },
        layer2_temporal={"transition_rate": 4.0},
        layer3_drift={"max_drift": 0.1},
    )

    stage = TriggerEvaluation(PipelineConfig(), TriggerEvaluationConfig(), monitoring)
    stage.initiate_trigger_evaluation()

    collapse = captured["report"]["collapse_signals"]
    assert collapse["dominance_warning"] is True
    assert collapse["dominant_class"] == "hand_tapping"
    assert collapse["dominant_pct"] == 86.0


def test_trigger_passes_collapse_level_and_motion_context(monkeypatch):
    captured = {}

    class _FakeEngine:
        def __init__(self, thresholds=None, cooldown_config=None, state_file=None):
            pass

        def evaluate(self, report):
            captured["report"] = report

            class _Decision:
                should_trigger = False
                action = "review"
                alert_level = "CRITICAL"
                recommendations = ["Manual review required."]

            return _Decision()

    monkeypatch.setattr("src.trigger_policy.TriggerPolicyEngine", _FakeEngine)

    monitoring = PostInferenceMonitoringArtifact(
        monitoring_report={
            "collapse_signals": {
                "collapse_level": "CRITICAL_COLLAPSE",
                "top2_margin_mean": 0.996,
            }
        },
        layer1_confidence={
            "mean_confidence": 0.998,
            "dominant_class": "hand_tapping",
            "dominant_pct": 100.0,
        },
        layer2_temporal={
            "transition_rate": 0.0,
            "motion_context": {
                "low_gyro_motion": True,
                "low_motion_collapse_risk": True,
                "g_mag_median": 0.545,
                "gravity_dominant_axis": "Az",
            },
        },
        layer3_drift={"max_drift": 0.1},
    )

    stage = TriggerEvaluation(PipelineConfig(), TriggerEvaluationConfig(), monitoring)
    stage.initiate_trigger_evaluation()

    collapse = captured["report"]["collapse_signals"]
    assert collapse["collapse_level"] == "CRITICAL_COLLAPSE"
    assert collapse["top2_margin_mean"] == 0.996
    assert collapse["low_gyro_motion"] is True
    assert collapse["low_motion_collapse_risk"] is True
    assert collapse["g_mag_median"] == 0.545
    assert collapse["gravity_dominant_axis"] == "Az"

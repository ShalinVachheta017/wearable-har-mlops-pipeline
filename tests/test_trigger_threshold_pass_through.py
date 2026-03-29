from src.components.trigger_evaluation import TriggerEvaluation
from src.entity.artifact_entity import PostInferenceMonitoringArtifact
from src.entity.config_entity import PipelineConfig, TriggerEvaluationConfig


def test_trigger_temporal_thresholds_pass_through(monkeypatch, tmp_path):
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

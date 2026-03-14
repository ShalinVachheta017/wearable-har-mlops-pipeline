from pathlib import Path

from src.components.model_evaluation import ModelEvaluation
from src.entity.artifact_entity import ModelInferenceArtifact
from src.entity.config_entity import ModelEvaluationConfig, PipelineConfig


def test_stage5_unwraps_success_results_contract(monkeypatch, tmp_path):
    pred_csv = tmp_path / "predictions.csv"
    pred_csv.write_text("predicted_activity,confidence\nhand_tapping,0.91\n", encoding="utf-8")

    json_report = tmp_path / "evaluation.json"
    text_report = tmp_path / "evaluation.txt"
    json_report.write_text("{}", encoding="utf-8")
    text_report.write_text("ok", encoding="utf-8")

    class _FakePipeline:
        def __init__(self, config):
            self.config = config

        def run(self, predictions_csv=None):
            return {
                "success": True,
                "results": {
                    "distribution": {
                        "hand_tapping": {"count": 100, "percentage": 100.0},
                        "_dominant_class": "hand_tapping",
                        "_dominant_pct": 100.0,
                        "_distribution_dominance_warning": True,
                    },
                    "confidence": {"mean": 0.91, "std": 0.02},
                    "output_files": {
                        "json": str(json_report),
                        "txt": str(text_report),
                    },
                },
            }

    monkeypatch.setattr("src.evaluate_predictions.EvaluationPipeline", _FakePipeline)

    pipeline_cfg = PipelineConfig()
    eval_cfg = ModelEvaluationConfig(output_dir=tmp_path)
    inference_artifact = ModelInferenceArtifact(
        predictions_csv_path=pred_csv,
        predictions_npy_path=tmp_path / "preds.npy",
    )

    stage = ModelEvaluation(pipeline_cfg, eval_cfg, inference_artifact)
    artifact = stage.initiate_model_evaluation()

    assert artifact.distribution_summary
    assert "hand_tapping" in artifact.distribution_summary
    assert artifact.confidence_summary.get("mean") == 0.91
    assert artifact.distribution_dominance_warning is True
    assert artifact.report_json_path == json_report
    assert artifact.report_text_path == text_report

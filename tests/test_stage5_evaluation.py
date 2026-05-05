"""Stage 5 — Model Evaluation Tests"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.api import app as api_app
from src.components.model_evaluation import ModelEvaluation
from src.entity.artifact_entity import ModelInferenceArtifact
from src.entity.config_entity import ModelEvaluationConfig, PipelineConfig
from src.evaluate_predictions import ACTIVITY_CLASSES as EVAL_CLASSES
from src.run_inference import ACTIVITY_CLASSES as INF_CLASSES
from src.utils.label_mapping import load_activity_mapping


# ── Label mapping consistency ─────────────────────────────────────────────────

def test_single_source_label_mapping_consistent_across_entrypoints():
    label_to_activity, _ = load_activity_mapping()
    assert INF_CLASSES == label_to_activity
    assert EVAL_CLASSES == label_to_activity
    assert api_app.ACTIVITY_CLASSES == label_to_activity


def test_label_mapping_fail_fast_on_inconsistent_metadata(tmp_path):
    bad_config = {
        "activity_to_label": {
            "ear_rubbing": 0,
            "forehead_rubbing": 2,
        },
        "label_to_activity": {
            "0": "ear_rubbing",
            "1": "forehead_rubbing",
        },
    }
    p = tmp_path / "bad_config.json"
    p.write_text(json.dumps(bad_config), encoding="utf-8")
    with pytest.raises(ValueError):
        load_activity_mapping(metadata_path=p)


# ── Evaluation component contract ─────────────────────────────────────────────

def test_stage5_unwraps_success_results_contract(monkeypatch, tmp_path):
    from src.components.model_evaluation import EvaluatePredictionsResponse

    json_report = tmp_path / "evaluation.json"
    text_report = tmp_path / "evaluation.txt"
    json_report.write_text("{}", encoding="utf-8")
    text_report.write_text("ok", encoding="utf-8")
    pred_csv = tmp_path / "predictions.csv"
    pred_csv.write_text("predicted_activity,confidence\nhand_tapping,0.91\n", encoding="utf-8")

    fake_response = EvaluatePredictionsResponse(
        report_json_path=json_report,
        report_text_path=text_report,
        distribution_summary={"hand_tapping": {"count": 100, "percentage": 100.0}},
        confidence_summary={"mean": 0.91, "std": 0.02},
        has_labels=False,
        classification_metrics=None,
        dominant_class="hand_tapping",
        dominant_pct=100.0,
        distribution_dominance_warning=True,
    )

    monkeypatch.setattr(
        "src.components.model_evaluation.ModelEvaluation.evaluate_predictions",
        lambda self: fake_response,
    )

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

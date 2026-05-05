import json

import numpy as np
import pytest

from src.components.model_evaluation import ModelEvaluation
from src.entity.artifact_entity import ModelInferenceArtifact
from src.entity.config_entity import ModelEvaluationConfig, PipelineConfig


def _write_predictions_csv(path, n_rows=4):
    rows = [
        "window_id,predicted_class,predicted_activity,confidence,confidence_pct,"
        "confidence_level,is_uncertain,entropy,top2_margin,"
        "prob_ear_rubbing,prob_forehead_rubbing,prob_hair_pulling,"
        "prob_hand_scratching,prob_hand_tapping,prob_knuckles_cracking,"
        "prob_nail_biting,prob_nape_rubbing,prob_sitting,prob_smoking,prob_standing"
    ]
    probs = [
        "0.001,0.001,0.001,0.001,0.990,0.001,0.001,0.001,0.001,0.001,0.001"
    ]
    for idx in range(n_rows):
        rows.append(
            f"{idx},4,hand_tapping,0.990,99.0%,HIGH,False,0.060,0.980,"
            f"{probs[0]}"
        )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _make_stage(tmp_path, pred_csv, labels_path=None):
    pipeline_cfg = PipelineConfig()
    eval_cfg = ModelEvaluationConfig(
        predictions_csv=pred_csv,
        labels_path=labels_path,
        output_dir=tmp_path / "evaluation",
    )
    inference_artifact = ModelInferenceArtifact(
        predictions_csv_path=pred_csv,
        predictions_npy_path=tmp_path / "preds.npy",
    )
    return ModelEvaluation(pipeline_cfg, eval_cfg, inference_artifact)


def test_stage5_preserves_dominance_fields_and_writes_reports(tmp_path):
    pred_csv = tmp_path / "predictions.csv"
    _write_predictions_csv(pred_csv, n_rows=4)

    artifact = _make_stage(tmp_path, pred_csv).initiate_model_evaluation()

    assert artifact.distribution_summary["hand_tapping"]["count"] == 4
    assert artifact.confidence_summary["mean"] == pytest.approx(0.99)
    assert artifact.has_labels is False
    assert artifact.classification_metrics is None
    assert artifact.distribution_dominance_warning is True
    assert artifact.dominant_class == "hand_tapping"
    assert artifact.dominant_pct == pytest.approx(100.0)
    assert artifact.report_json_path and artifact.report_json_path.exists()
    assert artifact.report_text_path and artifact.report_text_path.exists()

    payload = json.loads(artifact.report_json_path.read_text(encoding="utf-8"))
    assert payload["dominant_class"] == "hand_tapping"
    assert payload["dominant_pct"] == pytest.approx(100.0)
    assert payload["distribution_dominance_warning"] is True


def test_stage5_rejects_label_prediction_length_mismatch(tmp_path):
    pred_csv = tmp_path / "predictions.csv"
    _write_predictions_csv(pred_csv, n_rows=4)
    labels_path = tmp_path / "labels.npy"
    np.save(labels_path, np.array([4, 4, 4], dtype=np.int32))

    stage = _make_stage(tmp_path, pred_csv, labels_path)

    with pytest.raises(ValueError, match="Label/prediction length mismatch"):
        stage.initiate_model_evaluation()


def test_stage5_rejects_missing_required_prediction_columns(tmp_path):
    pred_csv = tmp_path / "broken_predictions.csv"
    pred_csv.write_text(
        "window_id,predicted_activity,confidence\n0,hand_tapping,0.99\n",
        encoding="utf-8",
    )

    stage = _make_stage(tmp_path, pred_csv)

    with pytest.raises(ValueError, match="missing required columns"):
        stage.initiate_model_evaluation()


def test_stage5_overlap_duration_math(tmp_path):
    pred_csv = tmp_path / "predictions.csv"
    _write_predictions_csv(pred_csv, n_rows=4)

    artifact = _make_stage(tmp_path, pred_csv).initiate_model_evaluation()
    payload = json.loads(artifact.report_json_path.read_text(encoding="utf-8"))

    assert payload["temporal"]["longest_sequence_length"] == 4
    assert payload["temporal"]["longest_sequence_duration_seconds"] == pytest.approx(10.0)

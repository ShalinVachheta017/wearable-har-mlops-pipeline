"""Pipeline Integration, Config Loader, and Regression Tests"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration

from src.entity.artifact_entity import DataValidationArtifact, PipelineResult
from src.entity.config_entity import (
    PipelineConfig,
    PostInferenceMonitoringConfig,
    TriggerEvaluationConfig,
)
from src.exceptions import DataValidationError
from src.pipeline.production_pipeline import ProductionPipeline, ALL_STAGES
from src.utils.config_loader import apply_overrides, load_yaml_overrides


# ── Pipeline integration ──────────────────────────────────────────────────────

def test_default_configs():
    cfg = PipelineConfig()
    pipeline = ProductionPipeline(cfg)
    assert pipeline.pipeline_config is cfg
    assert pipeline.ingestion_config is not None
    assert pipeline.retraining_config is not None


def test_all_stages_list():
    assert len(ALL_STAGES) == 11
    assert ALL_STAGES[0] == "ingestion"
    assert ALL_STAGES[9] == "baseline_update"
    assert ALL_STAGES[-1] == "calibration"


def test_default_runs_7_stages():
    cfg = PipelineConfig()
    pipeline = ProductionPipeline(cfg)
    with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
        with patch("src.components.data_ingestion.DataIngestion") as mock_ing:
            mock_ing.return_value.initiate_data_ingestion.side_effect = Exception("test stop")
            result = pipeline.run(continue_on_failure=False)
    assert "ingestion" in result.stages_failed


def test_retrain_flag_adds_stages():
    cfg = PipelineConfig()
    pipeline = ProductionPipeline(cfg)
    with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
        with patch("src.components.data_ingestion.DataIngestion") as mock_ing:
            mock_ing.return_value.initiate_data_ingestion.side_effect = Exception("stop")
            result = pipeline.run(enable_retrain=True, continue_on_failure=False)
    assert "ingestion" in result.stages_failed


def test_result_dataclass():
    result = PipelineResult()
    assert result.overall_status == "UNKNOWN"
    assert result.stages_completed == []
    assert result.retraining is None


def test_skip_ingestion():
    cfg = PipelineConfig()
    pipeline = ProductionPipeline(cfg)
    with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
        with patch("src.components.data_validation.DataValidation") as mock_val:
            mock_val.return_value.initiate_data_validation.side_effect = Exception("stop")
            result = pipeline.run(skip_ingestion=True, continue_on_failure=False)
    assert "ingestion" in result.stages_skipped


def test_continue_on_failure():
    cfg = PipelineConfig()
    pipeline = ProductionPipeline(cfg)
    with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
        with patch("src.components.data_ingestion.DataIngestion") as mock_ing:
            mock_ing.return_value.initiate_data_ingestion.side_effect = Exception("boom")
            result = pipeline.run(stages=["ingestion"], continue_on_failure=True)
    assert "ingestion" in result.stages_failed
    assert result.overall_status in ("PARTIAL", "FAILED")


# ── Config loader ─────────────────────────────────────────────────────────────

def test_valid_yaml_returns_expected_values(tmp_path):
    yaml_file = tmp_path / "overrides.yaml"
    yaml_file.write_text(textwrap.dedent("""\
        monitoring:
          confidence_warn_threshold: 0.55
          drift_zscore_threshold: 2.5
        trigger:
          cooldown_hours: 12
    """), encoding="utf-8")
    result = load_yaml_overrides(path=yaml_file)
    assert result["monitoring"]["confidence_warn_threshold"] == pytest.approx(0.55)
    assert result["monitoring"]["drift_zscore_threshold"] == pytest.approx(2.5)
    assert result["trigger"]["cooldown_hours"] == 12


def test_known_field_is_overridden():
    cfg = PostInferenceMonitoringConfig()
    original = cfg.confidence_warn_threshold
    apply_overrides(cfg, {"confidence_warn_threshold": 0.50})
    assert cfg.confidence_warn_threshold == pytest.approx(0.50)
    assert cfg.confidence_warn_threshold != original


# ── FIX regression tests ─────────────────────────────────────────────────────

def _pipeline() -> ProductionPipeline:
    return ProductionPipeline(pipeline_config=PipelineConfig())


def _invalid_validation_art() -> DataValidationArtifact:
    return DataValidationArtifact(is_valid=False, errors=["missing sensor columns"])


@patch("src.components.data_validation.DataValidation")
def test_finalize_called_on_validation_failure(mock_cls):
    mock_cls.return_value.initiate_data_validation.return_value = _invalid_validation_art()
    pipeline = _pipeline()
    with patch.object(pipeline.artifacts_manager, "finalize") as mock_finalize, \
         patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
        with pytest.raises(DataValidationError):
            pipeline.run(stages=["validation"])
    mock_finalize.assert_called_once()


def test_trigger_gate_blocked_stages_skipped_not_absent():
    pipeline = _pipeline()
    with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None), \
         patch("src.pipeline.production_pipeline.ProductionPipeline._run_calibration") as mock_cal:
        mock_cal.return_value = None
        result = pipeline.run(
            stages=["retraining", "registration", "baseline_update", "calibration"],
            continue_on_failure=True,
        )
    assert "retraining" in result.stages_skipped
    assert "registration" in result.stages_skipped
    assert "baseline_update" in result.stages_skipped
    mock_cal.assert_called_once()


def test_retrain_gate_does_not_set_status_success_when_nothing_ran():
    pipeline = _pipeline()
    with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
        result = pipeline.run(
            stages=["retraining", "registration", "baseline_update"],
            continue_on_failure=True,
        )
    assert result.overall_status == "SUCCESS"
    assert result.stages_completed == []
    assert len(result.stages_skipped) == 3
    assert "retraining" not in result.stages_failed

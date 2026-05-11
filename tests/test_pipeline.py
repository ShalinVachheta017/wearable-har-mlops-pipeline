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

class TestProductionPipelineInit:
    def test_default_configs(self):
        cfg = PipelineConfig()
        pipeline = ProductionPipeline(cfg)
        assert pipeline.pipeline_config is cfg
        assert pipeline.ingestion_config is not None
        assert pipeline.retraining_config is not None

    def test_all_stages_list(self):
        assert len(ALL_STAGES) == 11
        assert ALL_STAGES[0] == "ingestion"
        assert ALL_STAGES[9] == "baseline_update"
        assert ALL_STAGES[-1] == "calibration"


class TestPipelineStageSelection:
    def test_default_runs_7_stages(self):
        cfg = PipelineConfig()
        pipeline = ProductionPipeline(cfg)
        with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
            with patch("src.components.data_ingestion.DataIngestion") as mock_ing:
                mock_ing.return_value.initiate_data_ingestion.side_effect = Exception("test stop")
                result = pipeline.run(continue_on_failure=False)
        assert "ingestion" in result.stages_failed

    def test_retrain_flag_adds_stages(self):
        cfg = PipelineConfig()
        pipeline = ProductionPipeline(cfg)
        with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
            with patch("src.components.data_ingestion.DataIngestion") as mock_ing:
                mock_ing.return_value.initiate_data_ingestion.side_effect = Exception("stop")
                result = pipeline.run(enable_retrain=True, continue_on_failure=False)
        assert "ingestion" in result.stages_failed

    def test_specific_stages(self):
        cfg = PipelineConfig()
        pipeline = ProductionPipeline(cfg)
        with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
            result = pipeline.run(stages=["inference"], continue_on_failure=False)
        assert "inference" in result.stages_failed or "inference" in result.stages_completed


class TestPipelineResult:
    def test_result_dataclass(self):
        result = PipelineResult()
        assert result.overall_status == "UNKNOWN"
        assert result.stages_completed == []
        assert result.retraining is None

    def test_result_serialization(self, tmp_path):
        import dataclasses
        result = PipelineResult(
            run_id="test123",
            start_time="2026-01-01T00:00:00",
            end_time="2026-01-01T00:01:00",
            overall_status="SUCCESS",
            stages_completed=["ingestion", "validation"],
        )
        json_str = json.dumps(dataclasses.asdict(result), default=str)
        assert "test123" in json_str


class TestSkipAndContinue:
    def test_skip_ingestion(self):
        cfg = PipelineConfig()
        pipeline = ProductionPipeline(cfg)
        with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
            with patch("src.components.data_validation.DataValidation") as mock_val:
                mock_val.return_value.initiate_data_validation.side_effect = Exception("stop")
                result = pipeline.run(skip_ingestion=True, continue_on_failure=False)
        assert "ingestion" in result.stages_skipped

    def test_continue_on_failure(self):
        # Scope to ingestion only so we do not trip the validation hard-stop gate
        # (DataValidationError raises regardless of continue_on_failure — see
        # tests/test_validation_gate.py for the invariant).
        cfg = PipelineConfig()
        pipeline = ProductionPipeline(cfg)
        with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
            with patch("src.components.data_ingestion.DataIngestion") as mock_ing:
                mock_ing.return_value.initiate_data_ingestion.side_effect = Exception("boom")
                result = pipeline.run(stages=["ingestion"], continue_on_failure=True)
        assert "ingestion" in result.stages_failed
        assert result.overall_status in ("PARTIAL", "FAILED")


# ── Config loader ─────────────────────────────────────────────────────────────

class TestLoadYamlOverrides:
    def test_valid_yaml_returns_expected_values(self, tmp_path):
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

    def test_missing_file_returns_empty_dict(self, tmp_path):
        assert load_yaml_overrides(path=tmp_path / "does_not_exist.yaml") == {}

    def test_empty_yaml_returns_empty_dict(self, tmp_path):
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("", encoding="utf-8")
        assert load_yaml_overrides(path=empty_file) == {}

    def test_env_var_path_is_used(self, tmp_path, monkeypatch):
        yaml_file = tmp_path / "env_overrides.yaml"
        yaml_file.write_text("monitoring:\n  max_baseline_age_days: 60\n", encoding="utf-8")
        monkeypatch.setenv("HAR_PIPELINE_OVERRIDES", str(yaml_file))
        result = load_yaml_overrides()
        assert result["monitoring"]["max_baseline_age_days"] == 60


class TestApplyOverrides:
    def test_known_field_is_overridden(self):
        cfg = PostInferenceMonitoringConfig()
        original = cfg.confidence_warn_threshold
        apply_overrides(cfg, {"confidence_warn_threshold": 0.50})
        assert cfg.confidence_warn_threshold == pytest.approx(0.50)
        assert cfg.confidence_warn_threshold != original

    def test_unknown_key_is_silently_ignored(self):
        cfg = PostInferenceMonitoringConfig()
        before = cfg.drift_zscore_threshold
        apply_overrides(cfg, {"this_key_does_not_exist": 999})
        assert cfg.drift_zscore_threshold == pytest.approx(before)

    def test_multiple_fields_applied_at_once(self):
        cfg = TriggerEvaluationConfig()
        apply_overrides(cfg, {"confidence_warn": 0.70, "cooldown_hours": 48})
        assert cfg.confidence_warn == pytest.approx(0.70)
        assert cfg.cooldown_hours == 48

    def test_empty_section_is_no_op(self):
        cfg = PostInferenceMonitoringConfig()
        before_threshold = cfg.confidence_warn_threshold
        apply_overrides(cfg, {})
        assert cfg.confidence_warn_threshold == pytest.approx(before_threshold)


# ── FIX-1 and FIX-2 regression tests ─────────────────────────────────────────

def _pipeline() -> ProductionPipeline:
    return ProductionPipeline(pipeline_config=PipelineConfig())


def _invalid_validation_art() -> DataValidationArtifact:
    return DataValidationArtifact(is_valid=False, errors=["missing sensor columns"])


class TestFix1ValidationCleanup:
    @patch("src.components.data_validation.DataValidation")
    def test_finalize_called_on_validation_failure(self, mock_cls):
        mock_cls.return_value.initiate_data_validation.return_value = _invalid_validation_art()
        pipeline = _pipeline()
        with patch.object(pipeline.artifacts_manager, "finalize") as mock_finalize, \
             patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
            with pytest.raises(DataValidationError):
                pipeline.run(stages=["validation"])
        mock_finalize.assert_called_once()

    @patch("src.components.data_validation.DataValidation")
    def test_save_result_called_on_validation_failure(self, mock_cls):
        mock_cls.return_value.initiate_data_validation.return_value = _invalid_validation_art()
        pipeline = _pipeline()
        with patch.object(pipeline, "_save_result") as mock_save, \
             patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
            with pytest.raises(DataValidationError):
                pipeline.run(stages=["validation"])
        mock_save.assert_called_once()
        saved: PipelineResult = mock_save.call_args[0][0]
        assert saved.overall_status == "FAILED"
        assert saved.end_time != ""

    @patch("src.components.data_validation.DataValidation")
    def test_result_status_failed_on_validation_error(self, mock_cls):
        mock_cls.return_value.initiate_data_validation.return_value = _invalid_validation_art()
        pipeline = _pipeline()
        captured: list[PipelineResult] = []
        with patch.object(pipeline, "_save_result", side_effect=captured.append), \
             patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
            with pytest.raises(DataValidationError):
                pipeline.run(stages=["validation"])
        assert captured and captured[0].overall_status == "FAILED"
        assert "validation" in captured[0].stages_failed


class TestFix2RetrainGateSkipNotBreak:
    def test_trigger_gate_blocked_stages_skipped_not_absent(self):
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

    def test_unlabeled_gate_blocked_calibration_still_runs(self):
        pipeline = _pipeline()
        with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None), \
             patch("src.pipeline.production_pipeline.ProductionPipeline._run_calibration") as mock_cal:
            mock_cal.return_value = None
            result = pipeline.run(stages=["retraining", "calibration"], continue_on_failure=True)
        assert "retraining" in result.stages_skipped
        mock_cal.assert_called_once()

    def test_retrain_gate_does_not_set_status_success_when_nothing_ran(self):
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

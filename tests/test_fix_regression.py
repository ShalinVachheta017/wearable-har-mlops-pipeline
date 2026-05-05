"""
Regression tests for FIX-1 and FIX-2 (2026-04-18 hardening).

FIX-1 — production_pipeline.py try/finally:
    DataValidationError must not bypass finalize() / _save_result().

FIX-2 — Stage 8 BREAK → SKIP:
    When the retrain gate blocks, stage 8 returns SKIP (not BREAK), so the
    stage loop continues and stage 11 (calibration) can still execute.
    Stages 9-10 must also appear in stages_skipped, not be silently absent.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from src.entity.artifact_entity import DataValidationArtifact, PipelineResult
from src.entity.config_entity import PipelineConfig
from src.exceptions import DataValidationError
from src.pipeline.production_pipeline import ProductionPipeline


# ── helpers ──────────────────────────────────────────────────────────────────

def _pipeline() -> ProductionPipeline:
    return ProductionPipeline(pipeline_config=PipelineConfig())


def _invalid_validation_art() -> DataValidationArtifact:
    return DataValidationArtifact(
        is_valid=False,
        errors=["missing sensor columns"],
    )


# ── FIX-1 ────────────────────────────────────────────────────────────────────

class TestFix1ValidationCleanup:
    """finalize() and _save_result() must always run, even on DataValidationError."""

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
        """overall_status must be FAILED, not UNKNOWN, when validation hard-stops."""
        mock_cls.return_value.initiate_data_validation.return_value = _invalid_validation_art()
        pipeline = _pipeline()

        captured: list[PipelineResult] = []

        def capture_result(result):
            captured.append(result)

        with patch.object(pipeline, "_save_result", side_effect=capture_result), \
             patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None):
            with pytest.raises(DataValidationError):
                pipeline.run(stages=["validation"])

        assert captured, "No result was captured — _save_result was not called"
        assert captured[0].overall_status == "FAILED"
        assert "validation" in captured[0].stages_failed


# ── FIX-2 ────────────────────────────────────────────────────────────────────

class TestFix2RetrainGateSkipNotBreak:
    """Stage 8 gate must return SKIP so the loop continues to stage 11."""

    def test_trigger_gate_blocked_stages_skipped_not_absent(self):
        """
        Retrain requested, trigger says should_retrain=False.
        Stages 8-10 must be in stages_skipped.
        Stage 11 must be attempted (in completed or failed — NOT absent).
        """
        pipeline = _pipeline()

        with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None), \
             patch("src.pipeline.production_pipeline.ProductionPipeline._run_calibration") as mock_cal:

            mock_cal.return_value = None  # calibration succeeds (returns None = completed)

            result = pipeline.run(
                stages=["retraining", "registration", "baseline_update", "calibration"],
                continue_on_failure=True,
            )

        # Stages 8-10 must be skipped — trigger_art is None → gate blocks
        assert "retraining" in result.stages_skipped, (
            f"Expected 'retraining' in stages_skipped, got: {result.stages_skipped}"
        )
        assert "registration" in result.stages_skipped, (
            f"Expected 'registration' in stages_skipped, got: {result.stages_skipped}"
        )
        assert "baseline_update" in result.stages_skipped, (
            f"Expected 'baseline_update' in stages_skipped, got: {result.stages_skipped}"
        )
        # Stage 11 must have been called
        mock_cal.assert_called_once()

    def test_unlabeled_gate_blocked_calibration_still_runs(self):
        """
        Unlabeled dataset + supervised-only adaptation → Stage 8 must SKIP.
        Stage 11 must still be attempted.
        """
        pipeline = _pipeline()
        # Default: dataset_has_labels=False, adaptation_method="none" → unlabeled gate fires

        with patch("src.pipeline.production_pipeline.ProductionPipeline._init_mlflow", return_value=None), \
             patch("src.pipeline.production_pipeline.ProductionPipeline._run_calibration") as mock_cal:

            mock_cal.return_value = None

            result = pipeline.run(
                stages=["retraining", "calibration"],
                continue_on_failure=True,
            )

        assert "retraining" in result.stages_skipped, (
            f"Expected 'retraining' in stages_skipped, got: {result.stages_skipped}"
        )
        mock_cal.assert_called_once()

    def test_retrain_gate_does_not_set_status_success_when_nothing_ran(self):
        """
        If all requested stages are skipped, overall_status should be SUCCESS
        (no failures), but stages_completed must be empty and stages_skipped populated.
        """
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

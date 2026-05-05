"""Stage 2 — Data Validation Tests"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from src.entity.config_entity import PipelineConfig
from src.entity.artifact_entity import DataValidationArtifact
from src.exceptions import DataValidationError
from src.pipeline.production_pipeline import ProductionPipeline


# ── Sensor data checks ────────────────────────────────────────────────────────

class TestDataValidation:
    def test_sensor_columns_present(self, sample_sensor_data):
        required_columns = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
        for col in required_columns:
            assert col in sample_sensor_data.columns, f"Missing required column: {col}"

    def test_no_missing_values(self, sample_sensor_data):
        sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
        for col in sensor_cols:
            missing_ratio = sample_sensor_data[col].isna().mean()
            assert missing_ratio == 0, f"Column {col} has {missing_ratio:.1%} missing values"

    def test_accelerometer_range(self, sample_sensor_data):
        accel_cols = ['Ax_w', 'Ay_w', 'Az_w']
        for col in accel_cols:
            max_val = sample_sensor_data[col].abs().max()
            assert max_val < 50.0, f"Column {col} has unreasonable value: {max_val}"

    def test_gyroscope_range(self, sample_sensor_data):
        gyro_cols = ['Gx_w', 'Gy_w', 'Gz_w']
        for col in gyro_cols:
            max_val = sample_sensor_data[col].abs().max()
            assert max_val < 500.0, f"Column {col} has unreasonable value: {max_val}"

    def test_labeled_data_has_activity_column(self, sample_labeled_data):
        assert 'activity' in sample_labeled_data.columns

    def test_labeled_data_has_user_column(self, sample_labeled_data):
        assert 'User' in sample_labeled_data.columns

    def test_activity_labels_valid(self, sample_labeled_data, activity_labels):
        for activity in sample_labeled_data['activity'].unique():
            assert isinstance(activity, str) and len(activity) > 0


class TestDataQuality:
    def test_no_constant_columns(self, sample_sensor_data):
        sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
        for col in sensor_cols:
            assert sample_sensor_data[col].std() > 0.001, f"Column {col} appears constant"

    def test_variance_not_collapsed(self, sample_sensor_data):
        sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
        for col in sensor_cols:
            assert sample_sensor_data[col].var() > 0.01, f"Column {col} has collapsed variance"

    def test_no_infinite_values(self, sample_sensor_data):
        sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
        for col in sensor_cols:
            assert np.isinf(sample_sensor_data[col]).sum() == 0

    def test_sufficient_data_points(self, sample_sensor_data):
        assert len(sample_sensor_data) >= 200


class TestWindowCreation:
    def test_window_dimensions(self, sample_windows):
        n_windows, window_size, n_sensors = sample_windows.shape
        assert window_size == 200
        assert n_sensors == 6

    def test_window_values_normalized(self, sample_windows):
        assert not np.isnan(sample_windows).any()
        assert not np.isinf(sample_windows).any()

    def test_minimum_windows_created(self, sample_labeled_data):
        expected_windows = max(0, (len(sample_labeled_data) - 200) // 100 + 1)
        assert expected_windows > 0


# ── Validation gate (pipeline contract) ───────────────────────────────────────

def _make_pipeline() -> ProductionPipeline:
    return ProductionPipeline(pipeline_config=PipelineConfig())


def _invalid_artifact() -> DataValidationArtifact:
    return DataValidationArtifact(
        is_valid=False,
        errors=["Expected 9 sensor columns, got 3"],
        warnings=[],
    )


class TestValidationGate:
    @patch("src.components.data_validation.DataValidation")
    def test_invalid_data_raises_error_default(self, mock_cls):
        mock_cls.return_value.initiate_data_validation.return_value = _invalid_artifact()
        pipeline = _make_pipeline()
        with pytest.raises(DataValidationError) as exc_info:
            pipeline.run(stages=["validation"])
        msg = str(exc_info.value).lower()
        assert "error(s)" in msg or "validation failed" in msg

    @patch("src.components.data_validation.DataValidation")
    def test_invalid_data_raises_error_with_continue_on_failure(self, mock_cls):
        mock_cls.return_value.initiate_data_validation.return_value = _invalid_artifact()
        pipeline = _make_pipeline()
        with pytest.raises(DataValidationError):
            pipeline.run(stages=["validation"], continue_on_failure=True)

    @patch("src.components.data_validation.DataValidation")
    def test_valid_data_does_not_raise(self, mock_cls):
        mock_cls.return_value.initiate_data_validation.return_value = DataValidationArtifact(
            is_valid=True, errors=[], warnings=["low_sample_count"],
        )
        pipeline = _make_pipeline()
        try:
            pipeline.run(stages=["validation"])
        except DataValidationError:
            pytest.fail("Valid data must not raise DataValidationError")
        except Exception:
            pass

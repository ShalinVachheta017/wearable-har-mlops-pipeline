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

def test_sensor_columns_present(sample_sensor_data):
    required_columns = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
    for col in required_columns:
        assert col in sample_sensor_data.columns, f"Missing required column: {col}"


def test_no_missing_values(sample_sensor_data):
    sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
    for col in sensor_cols:
        missing_ratio = sample_sensor_data[col].isna().mean()
        assert missing_ratio == 0, f"Column {col} has {missing_ratio:.1%} missing values"


def test_accelerometer_range(sample_sensor_data):
    accel_cols = ['Ax_w', 'Ay_w', 'Az_w']
    for col in accel_cols:
        max_val = sample_sensor_data[col].abs().max()
        assert max_val < 50.0, f"Column {col} has unreasonable value: {max_val}"


def test_gyroscope_range(sample_sensor_data):
    gyro_cols = ['Gx_w', 'Gy_w', 'Gz_w']
    for col in gyro_cols:
        max_val = sample_sensor_data[col].abs().max()
        assert max_val < 500.0, f"Column {col} has unreasonable value: {max_val}"


def test_no_constant_columns(sample_sensor_data):
    sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
    for col in sensor_cols:
        assert sample_sensor_data[col].std() > 0.001, f"Column {col} appears constant"


def test_window_dimensions(sample_windows):
    n_windows, window_size, n_sensors = sample_windows.shape
    assert window_size == 200
    assert n_sensors == 6


# ── Validation gate (pipeline contract) ───────────────────────────────────────

def _make_pipeline() -> ProductionPipeline:
    return ProductionPipeline(pipeline_config=PipelineConfig())


def _invalid_artifact() -> DataValidationArtifact:
    return DataValidationArtifact(
        is_valid=False,
        errors=["Expected 9 sensor columns, got 3"],
        warnings=[],
    )


@patch("src.components.data_validation.DataValidation")
def test_invalid_data_raises_error_default(mock_cls):
    mock_cls.return_value.initiate_data_validation.return_value = _invalid_artifact()
    pipeline = _make_pipeline()
    with pytest.raises(DataValidationError) as exc_info:
        pipeline.run(stages=["validation"])
    msg = str(exc_info.value).lower()
    assert "error(s)" in msg or "validation failed" in msg


@patch("src.components.data_validation.DataValidation")
def test_valid_data_does_not_raise(mock_cls):
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

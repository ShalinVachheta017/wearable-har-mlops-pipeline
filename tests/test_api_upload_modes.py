from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.api.app import (
    _detect_columns,
    _detect_label_column,
    _maybe_convert_accel_units,
    _merge_upload_pair,
    _preserve_raw_physical_units,
)


def _raw_sensor_df(prefix: str, n: int = 500) -> pd.DataFrame:
    values = np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "timestamp": ["2025-07-17 03:26:55"] * n,
            "timestamp_ms": values * 10,
            "sample_index": values.astype(int),
            "sample_time_offset": 0,
            f"{prefix}_x": values + 1,
            f"{prefix}_y": values + 2,
            f"{prefix}_z": values + 3,
        }
    )


def test_detect_fused_columns_and_label():
    df = pd.DataFrame(
        {
            "accel_x": [1.0],
            "accel_y": [2.0],
            "accel_z": [3.0],
            "gyro_x": [4.0],
            "gyro_y": [5.0],
            "gyro_z": [6.0],
            "activity": ["walking"],
        }
    )

    assert _detect_columns(df) == [
        "accel_x",
        "accel_y",
        "accel_z",
        "gyro_x",
        "gyro_y",
        "gyro_z",
    ]
    assert _detect_label_column(df) == "activity"


def test_merge_accel_gyro_pair_to_six_channel_frame():
    fused, sensor_cols = _merge_upload_pair(
        _raw_sensor_df("accel"),
        _raw_sensor_df("gyro"),
    )

    assert sensor_cols == ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
    assert len(fused) >= 200
    assert not fused[sensor_cols].isna().any().any()


def test_millig_accelerometer_values_are_converted():
    df = pd.DataFrame(
        {
            "Ax": [1000.0, 1001.0],
            "Ay": [0.0, 1.0],
            "Az": [-1000.0, -1001.0],
            "Gx": [1.0, 2.0],
            "Gy": [3.0, 4.0],
            "Gz": [5.0, 6.0],
        }
    )

    converted, applied = _maybe_convert_accel_units(df, ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"])

    assert applied is True
    assert converted["Ax"].iloc[0] == pytest.approx(9.81)
    assert converted["Gx"].iloc[0] == 1.0


def test_api_preserves_raw_physical_units_without_external_scaler():
    values = np.array(
        [
            [9.81, 0.0, -9.81, 1.0, 2.0, 3.0],
            [9.82, 0.1, -9.80, 4.0, 5.0, 6.0],
        ],
        dtype=np.float32,
    )

    transformed, info = _preserve_raw_physical_units(values)

    np.testing.assert_allclose(transformed, values)
    assert info["normalization_applied"] is False
    assert info["normalization_variant"] == "none"
    assert info["scaler_config"] is None
    assert info["model_input_space"] == "raw_physical_units_ms2_dps"

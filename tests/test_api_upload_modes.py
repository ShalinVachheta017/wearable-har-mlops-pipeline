from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.api.app import (
    WINDOW_SIZE,
    _apply_final_model_scaler,
    _detect_columns,
    _detect_label_column,
    _evaluate_against_labels,
    _maybe_convert_accel_units,
    _maybe_evaluate,
    _merge_upload_pair,
    _resolve_label_ids,
    _smooth_predictions,
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
    assert converted["Ax"].iloc[0] == pytest.approx(9.80665)
    assert converted["Gx"].iloc[0] == 1.0


def test_api_applies_active_runtime_scaler(monkeypatch):
    values = np.array(
        [
            [9.81, 0.0, -9.81, 1.0, 2.0, 3.0],
            [9.82, 0.1, -9.80, 4.0, 5.0, 6.0],
        ],
        dtype=np.float32,
    )
    config = {
        "normalization_variant": "zscore",
        "scaler_mean": [9.0, 0.0, -9.0, 1.0, 2.0, 3.0],
        "scaler_scale": [0.9, 1.0, 0.9, 2.0, 2.0, 2.0],
    }
    monkeypatch.setattr("src.api.app._load_scaler_config", lambda: config)

    transformed, info = _apply_final_model_scaler(values)

    expected = (values - np.array(config["scaler_mean"], dtype=np.float32)) / np.array(
        config["scaler_scale"], dtype=np.float32
    )
    np.testing.assert_allclose(transformed, expected)
    assert info["normalization_applied"] is True
    assert info["normalization_variant"] == "zscore"
    assert info["scaler_config"]
    assert info["model_input_space"] == "zscore_scaled_garmin_train_only"


def test_resolve_label_ids_accepts_names_and_numeric_ids():
    assert set(_resolve_label_ids(pd.Series(["smoking"] * 4)).tolist()) == {9}
    assert set(_resolve_label_ids(pd.Series([9] * 4)).tolist()) == {9}
    # unknown values become -1 (excluded from evaluation)
    assert set(_resolve_label_ids(pd.Series(["not_a_class", None])).tolist()) == {-1}


def test_evaluate_against_labels_computes_accuracy_and_f1():
    # 400 rows of "smoking" (id 9) -> 3 windows under 200/100 geometry
    row_label_ids = _resolve_label_ids(pd.Series(["smoking"] * (2 * WINDOW_SIZE)))
    predicted = np.array([9, 9, 2])  # 2 correct, 1 wrong

    ev = _evaluate_against_labels(row_label_ids, predicted, "activity")

    assert ev["available"] is True
    assert ev["accuracy"] == pytest.approx(2 / 3, abs=1e-4)
    assert ev["macro_f1"] == pytest.approx(0.4, abs=1e-4)
    assert ev["n_evaluated_windows"] == 3
    assert {c["activity"] for c in ev["per_class"]} == {"smoking", "hair_pulling"}
    # confusion matrix is square over the labels present and totals the eval windows
    cm = ev["confusion_matrix"]
    assert len(cm["labels"]) == len(cm["matrix"]) == 2
    assert sum(sum(row) for row in cm["matrix"]) == 3


def test_maybe_evaluate_returns_none_without_label_column():
    assert _maybe_evaluate(pd.DataFrame({"x": [1]}), None, np.array([0])) is None
    assert _maybe_evaluate(pd.DataFrame({"x": [1]}), "activity", np.array([0])) is None


def test_evaluate_against_labels_flags_unmappable_labels():
    row_label_ids = _resolve_label_ids(pd.Series(["xyz"] * (2 * WINDOW_SIZE)))

    ev = _evaluate_against_labels(row_label_ids, np.array([9, 9, 2]), "activity")

    assert ev["available"] is False
    assert ev["label_column"] == "activity"


def test_smoothing_removes_isolated_single_window_flips():
    base = [9, 9, 9, 2, 9, 9, 2, 9, 9, 9]  # two isolated single-window flips
    probs = np.full((len(base), 11), 0.01, dtype=np.float32)
    for i, c in enumerate(base):
        probs[i, c] = 0.9
    raw = probs.argmax(axis=1)
    smoothed, _ = _smooth_predictions(probs, window=3)

    raw_tr = float(np.mean(raw[1:] != raw[:-1]))
    sm_tr = float(np.mean(smoothed[1:] != smoothed[:-1]))
    assert sm_tr < raw_tr  # isolated flips are absorbed by confident neighbours


def test_evaluate_adds_smoothed_metrics_only_when_smoothed_provided():
    row_label_ids = _resolve_label_ids(pd.Series(["smoking"] * (2 * WINDOW_SIZE)))
    preds = np.array([9, 9, 2])      # 2/3 correct
    smoothed = np.array([9, 9, 9])   # 3/3 correct after smoothing

    ev = _evaluate_against_labels(row_label_ids, preds, "activity", smoothed)
    assert ev["accuracy_smoothed"] == pytest.approx(1.0)
    assert ev["macro_f1_smoothed"] == pytest.approx(1.0)

    ev_no_smooth = _evaluate_against_labels(row_label_ids, preds, "activity")
    assert "accuracy_smoothed" not in ev_no_smooth

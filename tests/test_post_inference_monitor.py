"""A27/A28 — unit tests for Stage 6 monitoring thresholds.

A27: dominant-class collapse tier (warn at 85%, critical at 95%).
A28: tightened defaults — confidence 0.70, uncertain 20%, transition 35%, drift 1.8.
"""
from __future__ import annotations

from pathlib import Path
import json
import uuid

import numpy as np
import pandas as pd
import pytest

from src.entity.config_entity import PostInferenceMonitoringConfig, TriggerEvaluationConfig
from src.monitoring.post_inference_monitor import PostInferenceMonitor


CLASSES = [
    "ear_rubbing", "forehead_rubbing", "hair_pulling", "hand_scratching",
    "hand_tapping", "knuckles_cracking", "nail_biting", "nape_rubbing",
    "sitting", "standing", "smoking",
]


def _test_tmp_parent() -> Path:
    parent = Path.cwd() / "stage6_pytest_work"
    parent.mkdir(parents=True, exist_ok=True)
    return parent


def _make_predictions(dominant_pct: float, mean_conf: float, n: int = 1000,
                      uncertain_pct: float = 0.0) -> pd.DataFrame:
    """Synthetic predictions DataFrame with a target dominant-class share and mean confidence."""
    n_dominant = int(round(n * dominant_pct / 100.0))
    activities = [CLASSES[0]] * n_dominant
    remaining = n - n_dominant
    for i in range(remaining):
        activities.append(CLASSES[1 + (i % (len(CLASSES) - 1))])

    n_uncertain = int(round(n * uncertain_pct / 100.0))
    confidences = np.full(n, mean_conf, dtype=float)
    # Plant uncertain windows below 0.5 cutoff so is_uncertain=True for them
    low = 0.4
    for i in range(n_uncertain):
        confidences[i] = low
    # Rebalance remainder so mean equals the requested mean_conf as closely as possible
    if n - n_uncertain > 0:
        target_sum = mean_conf * n - low * n_uncertain
        confidences[n_uncertain:] = target_sum / (n - n_uncertain)

    df = pd.DataFrame({
        "predicted_activity": activities,
        "confidence": confidences,
        "is_uncertain": (confidences < 0.50).astype(int),
    })
    return df


def _run_monitor(df: pd.DataFrame, config: PostInferenceMonitoringConfig | None = None):
    cfg = config or PostInferenceMonitoringConfig()
    monitor = PostInferenceMonitor(
        confidence_warn_threshold=cfg.confidence_warn_threshold,
        confidence_threshold=cfg.uncertain_window_threshold,
        uncertain_threshold_pct=cfg.uncertain_pct_threshold,
        transition_rate_threshold=cfg.transition_rate_threshold,
        drift_threshold=cfg.drift_zscore_threshold,
        dominant_class_warn_threshold=cfg.dominant_class_warn_threshold,
        dominant_class_critical_threshold=cfg.dominant_class_critical_threshold,
        low_gyro_motion_threshold=cfg.low_gyro_motion_threshold,
        low_motion_dominance_threshold=cfg.low_motion_dominance_threshold,
        window_duration_seconds=cfg.window_duration_seconds,
        prediction_stride_seconds=cfg.prediction_stride_seconds,
    )
    run_id = uuid.uuid4().hex
    run_dir = _test_tmp_parent() / f"monitor_{run_id}"
    output_dir = run_dir / "out"
    run_dir.mkdir(parents=True, exist_ok=True)
    pred_csv = run_dir / "predictions.csv"
    df.to_csv(pred_csv, index=False)
    report = monitor.run(predictions_path=pred_csv, output_dir=output_dir)
    return report


# ---- A28: tightened defaults ------------------------------------------------


def test_a28_defaults_match_thesis_values():
    cfg = PostInferenceMonitoringConfig()
    assert cfg.confidence_warn_threshold == 0.70
    assert cfg.uncertain_pct_threshold == 20.0
    assert cfg.transition_rate_threshold == 35.0
    assert cfg.drift_zscore_threshold == 1.8
    assert cfg.window_duration_seconds == 4.0
    assert cfg.prediction_stride_seconds == 2.0
    assert cfg.low_gyro_motion_threshold == 1.1
    assert cfg.low_motion_dominance_threshold == 70.0


def test_a28_stage6_tighter_than_stage7_for_confidence():
    s6 = PostInferenceMonitoringConfig()
    s7 = TriggerEvaluationConfig()
    # Stage 6 must warn at HIGHER confidence than Stage 7 (tighter = earlier warn).
    assert s6.confidence_warn_threshold > s7.confidence_warn


def test_monitor_passes_on_healthy_084_confidence():
    df = _make_predictions(dominant_pct=25.0, mean_conf=0.84)
    report = _run_monitor(df)
    assert report.layer1_confidence["status"] == "HEALTHY"


def test_monitor_warns_on_production_like_067_confidence():
    # 0.67 is BELOW the new 0.70 warn threshold (was healthy under old 0.60 default).
    df = _make_predictions(dominant_pct=25.0, mean_conf=0.67)
    report = _run_monitor(df)
    assert report.layer1_confidence["status"] == "CRITICAL"


# ---- A27: dominant-class tier ----------------------------------------------


def test_a27_config_has_dominance_fields():
    cfg = PostInferenceMonitoringConfig()
    assert cfg.dominant_class_warn_threshold == 85.0
    assert cfg.dominant_class_critical_threshold == 95.0


def test_monitor_healthy_at_70_pct_dominance():
    df = _make_predictions(dominant_pct=70.0, mean_conf=0.85)
    report = _run_monitor(df)
    layer1 = report.layer1_confidence
    assert layer1["status"] == "HEALTHY"
    assert layer1["dominance_warning"] is False
    assert layer1["dominance_critical"] is False
    assert 65.0 <= layer1["dominant_pct"] <= 75.0


def test_monitor_warn_at_86_pct_dominance():
    df = _make_predictions(dominant_pct=86.0, mean_conf=0.85)
    report = _run_monitor(df)
    layer1 = report.layer1_confidence
    assert layer1["status"] == "WARNING", (
        f"Expected WARNING at 86% dominance with healthy confidence, got {layer1['status']}"
    )
    assert layer1["dominance_warning"] is True
    assert layer1["dominance_critical"] is False


def test_monitor_critical_at_96_pct_dominance():
    df = _make_predictions(dominant_pct=96.0, mean_conf=0.85)
    report = _run_monitor(df)
    layer1 = report.layer1_confidence
    assert layer1["status"] == "CRITICAL"
    assert layer1["dominance_warning"] is True
    assert layer1["dominance_critical"] is True


def test_monitor_dominance_thresholds_from_config():
    # Override thresholds via config: warn at 50%, critical at 80%.
    cfg = PostInferenceMonitoringConfig()
    cfg.dominant_class_warn_threshold = 50.0
    cfg.dominant_class_critical_threshold = 80.0
    df = _make_predictions(dominant_pct=60.0, mean_conf=0.85)
    report = _run_monitor(df, cfg)
    assert report.layer1_confidence["dominance_warning"] is True
    assert report.layer1_confidence["dominance_critical"] is False


def test_monitor_uses_stage4_entropy_and_top2_margin_columns():
    df = _make_predictions(dominant_pct=25.0, mean_conf=0.84, n=4)
    df["entropy"] = [0.1, 0.2, 0.3, 0.4]
    df["top2_margin"] = [0.9, 0.8, 0.7, 0.6]

    report = _run_monitor(df)
    layer1 = report.layer1_confidence

    assert layer1["entropy_source"] == "stage4_prediction_csv"
    assert layer1["mean_entropy"] == pytest.approx(0.25)
    assert layer1["top2_margin_mean"] == pytest.approx(0.75)


def test_monitor_temporal_dwell_uses_four_second_window_and_two_second_stride():
    monitor = PostInferenceMonitor(window_duration_seconds=4.0, prediction_stride_seconds=2.0)
    df = pd.DataFrame(
        {
            "predicted_activity": ["sitting", "sitting", "sitting"],
            "confidence": [0.9, 0.9, 0.9],
        }
    )

    temporal = monitor._analyze_temporal_patterns(df)

    assert temporal["mean_dwell_time_seconds"] == pytest.approx(8.0)
    assert temporal["window_duration_seconds"] == 4.0
    assert temporal["prediction_stride_seconds"] == 2.0


def test_monitor_motion_context_flags_low_gyro_collapse_risk():
    tmp_path = _test_tmp_parent() / f"motion_low_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=True)
    df = _make_predictions(dominant_pct=80.0, mean_conf=0.85, n=10)
    windows = np.zeros((10, 200, 6), dtype=np.float32)
    windows[:, :, 2] = -9.81
    windows[:, :, 3:6] = 0.2
    production_path = tmp_path / "production_X.npy"
    np.save(production_path, windows)

    pred_csv = tmp_path / "predictions.csv"
    df.to_csv(pred_csv, index=False)
    monitor = PostInferenceMonitor()
    report = monitor.run(predictions_path=pred_csv, production_data_path=production_path, output_dir=tmp_path / "out")

    motion = report.layer2_temporal["motion_context"]
    assert motion["low_gyro_motion"] is True
    assert motion["low_motion_collapse_risk"] is True
    assert motion["gravity_dominant_axis"] == "Az"
    assert report.layer2_temporal["status"] == "WARNING"


def test_monitor_motion_context_does_not_flag_active_session():
    tmp_path = _test_tmp_parent() / f"motion_active_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=True)
    df = _make_predictions(dominant_pct=80.0, mean_conf=0.85, n=10)
    rng = np.random.RandomState(42)
    windows = np.zeros((10, 200, 6), dtype=np.float32)
    windows[:, :, 1] = 9.81
    windows[:, :, 3:6] = rng.normal(0.0, 15.0, size=(10, 200, 3))
    production_path = tmp_path / "production_X.npy"
    np.save(production_path, windows)

    pred_csv = tmp_path / "predictions.csv"
    df.to_csv(pred_csv, index=False)
    monitor = PostInferenceMonitor()
    report = monitor.run(predictions_path=pred_csv, production_data_path=production_path, output_dir=tmp_path / "out")

    motion = report.layer2_temporal["motion_context"]
    assert motion["low_gyro_motion"] is False
    assert motion["low_motion_collapse_risk"] is False
    assert motion["gravity_dominant_axis"] == "Ay"

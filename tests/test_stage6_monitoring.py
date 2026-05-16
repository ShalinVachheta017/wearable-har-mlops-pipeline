"""Stage 6 — Post-Inference Monitoring Tests

Covers: confidence thresholds (A27/A28), dominance tiers, baseline-space
consistency, baseline age, drift detection, PSI, entropy, flip rate,
and motion-context collapse signals.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from src.entity.config_entity import PostInferenceMonitoringConfig, TriggerEvaluationConfig
from src.monitoring.baseline_builder import BaselineBuilder
from src.monitoring.post_inference_monitor import PostInferenceMonitor


CLASSES = [
    "ear_rubbing", "forehead_rubbing", "hair_pulling", "hand_scratching",
    "hand_tapping", "knuckles_cracking", "nail_biting", "nape_rubbing",
    "sitting", "standing", "smoking",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_predictions(dominant_pct: float, mean_conf: float, n: int = 1000,
                      uncertain_pct: float = 0.0) -> pd.DataFrame:
    n_dominant = int(round(n * dominant_pct / 100.0))
    activities = [CLASSES[0]] * n_dominant
    for i in range(n - n_dominant):
        activities.append(CLASSES[1 + (i % (len(CLASSES) - 1))])

    n_uncertain = int(round(n * uncertain_pct / 100.0))
    confidences = np.full(n, mean_conf, dtype=float)
    low = 0.4
    for i in range(n_uncertain):
        confidences[i] = low
    if n - n_uncertain > 0:
        target_sum = mean_conf * n - low * n_uncertain
        confidences[n_uncertain:] = target_sum / (n - n_uncertain)

    return pd.DataFrame({
        "predicted_activity": activities,
        "confidence": confidences,
        "is_uncertain": (confidences < 0.50).astype(int),
    })


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
    )
    with tempfile.TemporaryDirectory() as td:
        pred_csv = Path(td) / "predictions.csv"
        df.to_csv(pred_csv, index=False)
        report = monitor.run(predictions_path=pred_csv, output_dir=Path(td) / "out")
    return report


# ── A28: tightened defaults ───────────────────────────────────────────────────

def test_a28_defaults_match_thesis_values():
    cfg = PostInferenceMonitoringConfig()
    assert cfg.confidence_warn_threshold == 0.70
    assert cfg.uncertain_pct_threshold == 20.0
    assert cfg.transition_rate_threshold == 35.0
    assert cfg.drift_zscore_threshold == 1.8


def test_a28_stage6_tighter_than_stage7_for_confidence():
    s6 = PostInferenceMonitoringConfig()
    s7 = TriggerEvaluationConfig()
    assert s6.confidence_warn_threshold > s7.confidence_warn


def test_monitor_passes_on_healthy_084_confidence():
    df = _make_predictions(dominant_pct=25.0, mean_conf=0.84)
    report = _run_monitor(df)
    assert report.layer1_confidence["status"] == "HEALTHY"


def test_monitor_warns_on_production_like_067_confidence():
    df = _make_predictions(dominant_pct=25.0, mean_conf=0.67)
    report = _run_monitor(df)
    assert report.layer1_confidence["status"] == "CRITICAL"


# ── A27: dominant-class tier ──────────────────────────────────────────────────

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
    assert layer1["status"] == "WARNING", f"Expected WARNING, got {layer1['status']}"
    assert layer1["dominance_warning"] is True
    assert layer1["dominance_critical"] is False


def test_monitor_critical_at_96_pct_dominance():
    df = _make_predictions(dominant_pct=96.0, mean_conf=0.85)
    report = _run_monitor(df)
    layer1 = report.layer1_confidence
    assert layer1["status"] == "CRITICAL"
    assert layer1["dominance_warning"] is True
    assert layer1["dominance_critical"] is True


# ── Baseline-space consistency ────────────────────────────────────────────────

def _write_training_csv(csv_path: Path) -> None:
    rng = np.random.RandomState(7)
    n_rows = 450
    df = pd.DataFrame({
        "Ax_w": rng.normal(10.0, 2.0, n_rows),
        "Ay_w": rng.normal(-5.0, 1.5, n_rows),
        "Az_w": rng.normal(3.0, 0.8, n_rows),
        "Gx_w": rng.normal(100.0, 20.0, n_rows),
        "Gy_w": rng.normal(-50.0, 10.0, n_rows),
        "Gz_w": rng.normal(25.0, 5.0, n_rows),
        "activity": ["sitting"] * n_rows,
    })
    df.to_csv(csv_path, index=False)


def test_normalized_baseline_saved_in_transformed_space(tmp_path):
    csv_path = tmp_path / "train.csv"
    cfg_path = tmp_path / "config.json"
    norm_path = tmp_path / "normalized_baseline.json"
    _write_training_csv(csv_path)

    config = {
        "normalization_variant": "zscore",
        "scaler_mean": [10.0, -5.0, 3.0, 100.0, -50.0, 25.0],
        "scaler_scale": [2.0, 1.5, 0.8, 20.0, 10.0, 5.0],
        "fit_users": [1, 2, 3, 4],
    }
    cfg_path.write_text(json.dumps(config), encoding="utf-8")

    builder = BaselineBuilder(window_size=200, step_size=100, scaler_config_path=cfg_path)
    raw_baseline = builder.build_from_csv(csv_path)
    builder.save_normalized(norm_path)

    normalized_baseline = json.loads(norm_path.read_text(encoding="utf-8"))
    assert normalized_baseline["metadata"]["feature_space"] == "transformed"

    raw_std = np.array(raw_baseline["std"], dtype=np.float64)
    transformed_std = np.array(normalized_baseline["std"], dtype=np.float64)
    expected_std = raw_std / np.array(config["scaler_scale"], dtype=np.float64)
    np.testing.assert_allclose(transformed_std, expected_std, rtol=1e-5, atol=1e-5)


def test_monitor_accepts_transformed_space_baseline(tmp_path):
    production = np.random.RandomState(13).normal(0, 1, (10, 200, 6)).astype(np.float32)
    production_path = tmp_path / "production_X.npy"
    np.save(production_path, production)

    transformed_baseline = {
        "mean": production.mean(axis=(0, 1)).tolist(),
        "std": np.maximum(production.std(axis=(0, 1)), 1e-6).tolist(),
        "metadata": {"feature_space": "transformed"},
    }
    baseline_path = tmp_path / "transformed_baseline.json"
    baseline_path.write_text(json.dumps(transformed_baseline), encoding="utf-8")

    monitor = PostInferenceMonitor(drift_threshold=2.0)
    result = monitor._analyze_drift(production_path, baseline_path)
    assert result["status"] == "HEALTHY"
    assert result["max_drift"] < 1e-4


# ── Baseline age gauge ────────────────────────────────────────────────────────

def _compute_baseline_age(baseline_path: Path) -> float:
    if baseline_path.exists():
        return max(0.0, (time.time() - baseline_path.stat().st_mtime) / 86400)
    return -1


def test_baseline_age_reflects_known_mtime(tmp_path):
    baseline = tmp_path / "normalized_baseline.json"
    baseline.write_text("{}", encoding="utf-8")
    five_days_ago = time.time() - (5 * 86400)
    os.utime(baseline, (five_days_ago, five_days_ago))
    assert abs(_compute_baseline_age(baseline) - 5.0) < 0.01


# ── Drift detection ───────────────────────────────────────────────────────────

def test_different_distributions_detect_drift():
    np.random.seed(42)
    baseline = np.random.normal(0, 1, 1000)
    current = np.random.normal(2, 1, 1000)
    _, ks_pvalue = stats.ks_2samp(baseline, current)
    assert ks_pvalue < 0.01


def test_psi_major_shift():
    def compute_psi(baseline, current, n_bins=10):
        bin_edges = np.percentile(baseline, np.linspace(0, 100, n_bins + 1))
        bin_edges[0], bin_edges[-1] = -np.inf, np.inf
        baseline_props = np.histogram(baseline, bins=bin_edges)[0] / len(baseline) + 1e-10
        current_props = np.histogram(current, bins=bin_edges)[0] / len(current) + 1e-10
        return float(np.sum((current_props - baseline_props) * np.log(current_props / baseline_props)))

    np.random.seed(42)
    baseline = np.random.normal(0, 1, 1000)
    assert compute_psi(baseline, np.random.normal(3, 2, 1000)) > 0.25


# ── Confidence + temporal core ────────────────────────────────────────────────

def test_entropy_calculation(sample_predictions):
    probs = sample_predictions['probabilities']
    entropy = -np.sum(probs * np.log(probs + 1e-10), axis=1)
    assert np.mean(entropy) > 0
    assert np.mean(entropy) < 2.5


def test_unstable_predictions_high_flip_rate():
    predictions = np.array([0, 1] * 50)
    flip_rate = np.sum(predictions[1:] != predictions[:-1]) / (len(predictions) - 1)
    assert flip_rate > 0.9


# ── Motion-context collapse signal ────────────────────────────────────────────

def _test_tmp_parent() -> Path:
    parent = Path.cwd() / "stage6_pytest_work"
    parent.mkdir(parents=True, exist_ok=True)
    return parent


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

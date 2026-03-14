"""
Stage 6 baseline-space consistency regression tests.

Covers:
1) Normalized baseline is saved in transformed feature space.
2) Stage 6 rejects legacy/raw-space baselines.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.build_training_baseline import BaselineBuilder
from scripts.post_inference_monitoring import PostInferenceMonitor


def _write_training_csv(csv_path: Path) -> None:
    rng = np.random.RandomState(7)
    n_rows = 450
    df = pd.DataFrame(
        {
            "Ax_w": rng.normal(10.0, 2.0, n_rows),
            "Ay_w": rng.normal(-5.0, 1.5, n_rows),
            "Az_w": rng.normal(3.0, 0.8, n_rows),
            "Gx_w": rng.normal(100.0, 20.0, n_rows),
            "Gy_w": rng.normal(-50.0, 10.0, n_rows),
            "Gz_w": rng.normal(25.0, 5.0, n_rows),
            "activity": ["sitting"] * n_rows,
        }
    )
    df.to_csv(csv_path, index=False)


def test_normalized_baseline_saved_in_transformed_space(tmp_path):
    csv_path = tmp_path / "train.csv"
    cfg_path = tmp_path / "config.json"
    norm_path = tmp_path / "normalized_baseline.json"

    _write_training_csv(csv_path)

    # Canonical transformed space is defined by this scaler config.
    config = {
        "normalization_variant": "zscore",
        "scaler_mean": [10.0, -5.0, 3.0, 100.0, -50.0, 25.0],
        "scaler_scale": [2.0, 1.5, 0.8, 20.0, 10.0, 5.0],
    }
    cfg_path.write_text(json.dumps(config), encoding="utf-8")

    builder = BaselineBuilder(window_size=200, step_size=100, scaler_config_path=cfg_path)
    raw_baseline = builder.build_from_csv(csv_path)
    builder.save_normalized(norm_path)

    normalized_baseline = json.loads(norm_path.read_text(encoding="utf-8"))

    assert normalized_baseline["metadata"]["feature_space"] == "transformed"

    # For linear scaling: std_transformed = std_raw / scaler_scale
    raw_std = np.array(raw_baseline["std"], dtype=np.float64)
    transformed_std = np.array(normalized_baseline["std"], dtype=np.float64)
    expected_std = raw_std / np.array(config["scaler_scale"], dtype=np.float64)

    np.testing.assert_allclose(transformed_std, expected_std, rtol=1e-5, atol=1e-5)


def test_monitor_rejects_baseline_without_transformed_feature_space(tmp_path):
    production = np.random.RandomState(11).normal(0, 1, (8, 200, 6)).astype(np.float32)
    production_path = tmp_path / "production_X.npy"
    np.save(production_path, production)

    legacy_baseline = {
        "mean": [0.0] * 6,
        "std": [1.0] * 6,
        "metadata": {"feature_space": "raw"},
    }
    baseline_path = tmp_path / "legacy_baseline.json"
    baseline_path.write_text(json.dumps(legacy_baseline), encoding="utf-8")

    monitor = PostInferenceMonitor()
    result = monitor._analyze_drift(production_path, baseline_path)

    assert result["status"] == "ERROR"
    assert "feature-space mismatch" in result["error"].lower()


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

    assert result["status"] == "PASS"
    assert result["max_drift"] < 1e-4

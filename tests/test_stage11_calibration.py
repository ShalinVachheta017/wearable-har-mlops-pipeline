"""Stage 11 — Calibration Tests (optional / deferred stage)"""
import numpy as np
import pytest

from src.calibration import (
    CalibrationConfig,
    CalibrationEvaluator,
    TemperatureScaler,
    UnlabeledCalibrationAnalyzer,
)


@pytest.fixture
def mock_logits():
    return np.random.RandomState(42).randn(100, 11).astype(np.float32)


@pytest.fixture
def mock_labels():
    return np.random.RandomState(42).randint(0, 11, size=100)


@pytest.fixture
def mock_probs(mock_logits):
    exp = np.exp(mock_logits - np.max(mock_logits, axis=1, keepdims=True))
    return exp / exp.sum(axis=1, keepdims=True)


def test_fit_returns_positive_temperature(mock_logits, mock_labels):
    scaler = TemperatureScaler()
    T = scaler.fit(mock_logits, mock_labels)
    assert T > 0
    assert scaler.fitted


def test_transform_produces_valid_probs(mock_logits):
    probs = TemperatureScaler().transform(mock_logits)
    assert probs.shape == mock_logits.shape
    np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-5)
    assert np.all(probs >= 0) and np.all(probs <= 1)


def test_save_load(mock_logits, mock_labels, tmp_path):
    scaler = TemperatureScaler()
    scaler.fit(mock_logits, mock_labels)
    path = tmp_path / "temperature.json"
    scaler.save(path)
    scaler2 = TemperatureScaler()
    scaler2.load(path)
    assert abs(scaler2.temperature - scaler.temperature) < 1e-6


def test_ece_is_bounded(mock_probs, mock_labels):
    ece, bins = CalibrationEvaluator(n_bins=15).expected_calibration_error(mock_probs, mock_labels)
    assert 0 <= ece <= 1.0


def test_overconfident_model_flagged():
    probs = np.zeros((100, 5))
    probs[:, 0] = 0.98
    probs[:, 1:] = 0.005
    result = UnlabeledCalibrationAnalyzer().analyze(probs)
    assert result["overconfidence_ratio"] > 0.80
    assert len(result["calibration_warnings"]) > 0

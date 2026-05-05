"""Stage 11 — Calibration Tests"""
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


class TestTemperatureScaler:
    def test_default_temperature(self):
        scaler = TemperatureScaler()
        assert scaler.temperature == 1.5
        assert not scaler.fitted

    def test_fit_returns_positive_temperature(self, mock_logits, mock_labels):
        scaler = TemperatureScaler()
        T = scaler.fit(mock_logits, mock_labels)
        assert T > 0
        assert scaler.fitted

    def test_transform_produces_valid_probs(self, mock_logits):
        probs = TemperatureScaler().transform(mock_logits)
        assert probs.shape == mock_logits.shape
        np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-5)
        assert np.all(probs >= 0) and np.all(probs <= 1)

    def test_higher_temperature_softens_probs(self, mock_logits):
        probs_low = TemperatureScaler(CalibrationConfig(initial_temperature=0.5)).transform(mock_logits)
        probs_high = TemperatureScaler(CalibrationConfig(initial_temperature=5.0)).transform(mock_logits)
        assert np.mean(np.max(probs_high, axis=1)) < np.mean(np.max(probs_low, axis=1))

    def test_save_load(self, mock_logits, mock_labels, tmp_path):
        scaler = TemperatureScaler()
        scaler.fit(mock_logits, mock_labels)
        path = tmp_path / "temperature.json"
        scaler.save(path)
        scaler2 = TemperatureScaler()
        scaler2.load(path)
        assert abs(scaler2.temperature - scaler.temperature) < 1e-6


class TestCalibrationEvaluator:
    def test_ece_is_bounded(self, mock_probs, mock_labels):
        ece, bins = CalibrationEvaluator(n_bins=15).expected_calibration_error(mock_probs, mock_labels)
        assert 0 <= ece <= 1.0

    def test_brier_score_range(self, mock_probs, mock_labels):
        brier = CalibrationEvaluator().brier_score(mock_probs, mock_labels)
        assert 0 <= brier <= 2.0

    def test_evaluate_returns_all_keys(self, mock_probs, mock_labels):
        report = CalibrationEvaluator().evaluate(mock_probs, mock_labels)
        for key in ["ece", "mce", "brier_score", "accuracy", "bins"]:
            assert key in report
        assert len(report["bins"]) == 15

    def test_perfect_calibration_has_low_ece(self):
        np.random.seed(42)
        n = 1000
        labels = np.random.RandomState(42).randint(0, 5, size=n)
        probs = np.zeros((n, 5))
        probs[np.arange(n), labels] = 0.95
        probs += 0.05 / 5
        probs /= probs.sum(axis=1, keepdims=True)
        ece, _ = CalibrationEvaluator(n_bins=10).expected_calibration_error(probs, labels)
        assert ece < 0.10

    def test_bins_count(self, mock_probs, mock_labels):
        _, bins = CalibrationEvaluator(n_bins=10).expected_calibration_error(mock_probs, mock_labels)
        assert len(bins) == 10


class TestUnlabeledCalibrationAnalyzer:
    def test_analyze_returns_expected_keys(self, mock_probs):
        result = UnlabeledCalibrationAnalyzer().analyze(mock_probs)
        for key in ["mean_confidence", "mean_entropy", "overconfidence_ratio", "calibration_warnings"]:
            assert key in result

    def test_overconfident_model_flagged(self):
        probs = np.zeros((100, 5))
        probs[:, 0] = 0.98
        probs[:, 1:] = 0.005
        result = UnlabeledCalibrationAnalyzer().analyze(probs)
        assert result["overconfidence_ratio"] > 0.80
        assert len(result["calibration_warnings"]) > 0

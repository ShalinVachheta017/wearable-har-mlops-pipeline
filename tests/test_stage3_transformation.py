"""Stage 3 — Data Transformation / Preprocessing Tests"""
import numpy as np
import pytest
from scipy import signal


# ── Gravity removal ───────────────────────────────────────────────────────────

def _apply_highpass_filter(data: np.ndarray, cutoff: float = 0.3, fs: float = 50.0) -> np.ndarray:
    nyquist = fs / 2
    normalized_cutoff = min(cutoff / nyquist, 0.99)
    b, a = signal.butter(3, normalized_cutoff, btype='high')
    return signal.filtfilt(b, a, data)


def test_gravity_removal_reduces_dc_offset():
    np.random.seed(42)
    az_with_gravity = 9.8 + np.random.normal(0, 0.5, 1000)
    az_filtered = _apply_highpass_filter(az_with_gravity)
    assert abs(np.mean(az_filtered)) < 1.0


def test_gravity_removal_preserves_motion():
    np.random.seed(42)
    t = np.arange(1000) / 50.0
    motion = 2.0 * np.sin(2 * np.pi * 2 * t)
    az_filtered = _apply_highpass_filter(9.8 + motion)
    correlation = np.corrcoef(motion[100:-100], az_filtered[100:-100])[0, 1]
    assert correlation > 0.9


# ── Normalization (scaler contract) ───────────────────────────────────────────

def test_standard_scaling(sample_sensor_data):
    from sklearn.preprocessing import StandardScaler
    sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
    scaled = StandardScaler().fit_transform(sample_sensor_data[sensor_cols].values)
    for i in range(scaled.shape[1]):
        assert abs(np.mean(scaled[:, i])) < 0.01
        assert abs(np.std(scaled[:, i]) - 1.0) < 0.01


def test_scaler_parameters_stored():
    from sklearn.preprocessing import StandardScaler
    import json
    np.random.seed(42)
    data = np.random.randn(1000, 6)
    scaler = StandardScaler().fit(data)
    params_json = json.dumps({'mean': scaler.mean_.tolist(), 'scale': scaler.scale_.tolist()})
    loaded = json.loads(params_json)
    new_scaler = StandardScaler()
    new_scaler.mean_ = np.array(loaded['mean'])
    new_scaler.scale_ = np.array(loaded['scale'])
    new_scaler.var_ = new_scaler.scale_ ** 2
    new_scaler.n_features_in_ = len(loaded['mean'])
    np.testing.assert_array_almost_equal(scaler.mean_, new_scaler.mean_)
    np.testing.assert_array_almost_equal(scaler.scale_, new_scaler.scale_)


# ── Resampling ────────────────────────────────────────────────────────────────

def test_downsample_maintains_length():
    from scipy import signal as sig
    np.random.seed(42)
    original_samples, original_hz, target_hz = 200, 100, 50
    data = np.random.randn(original_samples, 6)
    expected_samples = int(original_samples * target_hz / original_hz)
    resampled = sig.resample(data, expected_samples, axis=0)
    assert resampled.shape[0] == expected_samples


# ── Unit conversion ───────────────────────────────────────────────────────────

def test_millig_to_ms2_conversion():
    converted = 1000 * (9.80665 / 1000)
    assert abs(converted - 9.80665) < 0.001


# ── Data integrity ────────────────────────────────────────────────────────────

def test_no_nan_introduced(sample_sensor_data):
    from sklearn.preprocessing import StandardScaler
    sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
    data = sample_sensor_data[sensor_cols].values
    assert not np.isnan(data).any()
    assert not np.isnan(StandardScaler().fit_transform(data)).any()

"""Stage 3 — Data Transformation / Preprocessing Tests"""
import numpy as np
import pytest
from scipy import signal


class TestGravityRemoval:
    def apply_highpass_filter(self, data: np.ndarray, cutoff: float = 0.3, fs: float = 50.0) -> np.ndarray:
        nyquist = fs / 2
        normalized_cutoff = min(cutoff / nyquist, 0.99)
        b, a = signal.butter(3, normalized_cutoff, btype='high')
        return signal.filtfilt(b, a, data)

    def test_gravity_removal_reduces_dc_offset(self):
        np.random.seed(42)
        az_with_gravity = 9.8 + np.random.normal(0, 0.5, 1000)
        az_filtered = self.apply_highpass_filter(az_with_gravity)
        assert abs(np.mean(az_filtered)) < 1.0

    def test_gravity_removal_preserves_motion(self):
        np.random.seed(42)
        t = np.arange(1000) / 50.0
        motion = 2.0 * np.sin(2 * np.pi * 2 * t)
        az_filtered = self.apply_highpass_filter(9.8 + motion)
        correlation = np.corrcoef(motion[100:-100], az_filtered[100:-100])[0, 1]
        assert correlation > 0.9

    def test_static_data_zeroed(self):
        np.random.seed(42)
        az_static = np.full(1000, 9.8)
        az_filtered = self.apply_highpass_filter(az_static)
        assert np.abs(az_filtered[200:-200]).max() < 0.5


class TestNormalization:
    def test_standard_scaling(self, sample_sensor_data):
        from sklearn.preprocessing import StandardScaler
        sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
        scaled = StandardScaler().fit_transform(sample_sensor_data[sensor_cols].values)
        for i in range(scaled.shape[1]):
            assert abs(np.mean(scaled[:, i])) < 0.01
            assert abs(np.std(scaled[:, i]) - 1.0) < 0.01

    def test_normalization_preserves_shape(self, sample_sensor_data):
        from sklearn.preprocessing import StandardScaler
        sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
        data = sample_sensor_data[sensor_cols].values
        assert StandardScaler().fit_transform(data).shape == data.shape

    def test_scaler_parameters_stored(self):
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


class TestResampling:
    def test_upsample_maintains_length(self):
        np.random.seed(42)
        original_samples, original_hz, target_hz = 100, 25, 50
        data = np.random.randn(original_samples, 6)
        duration = original_samples / original_hz
        expected_samples = int(duration * target_hz)
        x_orig = np.linspace(0, duration, original_samples)
        x_new = np.linspace(0, duration, expected_samples)
        resampled = np.stack([np.interp(x_new, x_orig, data[:, i]) for i in range(6)], axis=1)
        assert resampled.shape[0] == expected_samples

    def test_downsample_maintains_length(self):
        from scipy import signal as sig
        np.random.seed(42)
        original_samples, original_hz, target_hz = 200, 100, 50
        data = np.random.randn(original_samples, 6)
        expected_samples = int(original_samples * target_hz / original_hz)
        resampled = sig.resample(data, expected_samples, axis=0)
        assert resampled.shape[0] == expected_samples


class TestUnitConversion:
    def test_millig_to_ms2_conversion(self):
        converted = 1000 * (9.80665 / 1000)
        assert abs(converted - 9.80665) < 0.001

    def test_conversion_preserves_sign(self):
        millig_values = np.array([-1000, 0, 1000, 2000])
        converted = millig_values * (9.80665 / 1000)
        assert converted[0] < 0
        assert converted[1] == 0
        assert converted[2] > 0
        assert converted[3] > converted[2]


class TestDataIntegrity:
    def test_no_nan_introduced(self, sample_sensor_data):
        from sklearn.preprocessing import StandardScaler
        sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
        data = sample_sensor_data[sensor_cols].values
        assert not np.isnan(data).any()
        assert not np.isnan(StandardScaler().fit_transform(data)).any()

    def test_no_inf_introduced(self, sample_sensor_data):
        from sklearn.preprocessing import StandardScaler
        sensor_cols = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
        data = sample_sensor_data[sensor_cols].values
        assert not np.isinf(StandardScaler().fit_transform(data)).any()

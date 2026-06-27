"""
3-layer post-inference monitoring.

Canonical location: src/monitoring/post_inference_monitor.py
Moved from scripts/post_inference_monitoring.py (2026-04-17).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MonitoringReport:
    """Container for monitoring results."""

    def __init__(self):
        """
        Method Name :   __init__
        Description :   Initialize the in-memory Stage 6 monitoring report.

        Output      :   Creates empty layer dictionaries and report metadata.
        On Failure  :   Logs the error and raises the exception.
        """
        self.overall_status = "UNKNOWN"
        self.layer1_confidence = {}
        self.layer2_temporal = {}
        self.layer3_drift = {}
        self.alerts = []
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Method Name :   to_dict
        Description :   Convert the monitoring report to a JSON-safe dictionary.

        Output      :   Returns the report dictionary written to monitoring_report.json.
        On Failure  :   Logs the error and raises the exception.
        """
        return {
            "overall_status": self.overall_status,
            "layer1_confidence": self.layer1_confidence,
            "layer2_temporal": self.layer2_temporal,
            "layer3_drift": self.layer3_drift,
            "alerts": self.alerts,
            "metadata": self.metadata,
        }


class PostInferenceMonitor:
    """Three-layer monitoring system for production inference results."""

    def __init__(
        self,
        confidence_warn_threshold: float = 0.70,
        confidence_threshold: float = 0.50,
        uncertain_threshold_pct: float = 20.0,
        transition_rate_threshold: float = 35.0,
        drift_threshold: float = 1.8,
        drift_detector_mode: str = "zscore_mean_shift",
        mmd_reference_path: Optional[Path] = None,
        mmd_threshold: Optional[float] = None,
        mmd_sample_size: int = 384,
        mmd_bootstrap_iterations: int = 40,
        mmd_random_seed: int = 42,
        calibration_temperature: float = 1.0,
        dominant_class_warn_threshold: float = 85.0,
        dominant_class_critical_threshold: float = 95.0,
        low_gyro_motion_threshold: float = 1.1,
        low_motion_dominance_threshold: float = 70.0,
        window_duration_seconds: float = 4.0,
        prediction_stride_seconds: float = 2.0,
    ):
        """
        Method Name :   __init__
        Description :   Store thresholds and runtime options for Stage 6 monitoring.

        Output      :   Initializes the PostInferenceMonitor engine.
        On Failure  :   Logs the error and raises the exception.
        """
        self.confidence_warn_threshold = confidence_warn_threshold
        self.confidence_threshold = confidence_threshold
        self.uncertain_threshold_pct = uncertain_threshold_pct
        self.transition_rate_threshold = transition_rate_threshold
        self.drift_threshold = drift_threshold
        self.drift_detector_mode = drift_detector_mode
        self.mmd_reference_path = (
            Path(mmd_reference_path) if mmd_reference_path else None
        )
        self.mmd_threshold = mmd_threshold
        self.mmd_sample_size = int(mmd_sample_size)
        self.mmd_bootstrap_iterations = int(mmd_bootstrap_iterations)
        self.mmd_random_seed = int(mmd_random_seed)
        self.calibration_temperature = float(calibration_temperature)
        self.dominant_class_warn_threshold = float(dominant_class_warn_threshold)
        self.dominant_class_critical_threshold = float(
            dominant_class_critical_threshold
        )
        self.low_gyro_motion_threshold = float(low_gyro_motion_threshold)
        self.low_motion_dominance_threshold = float(low_motion_dominance_threshold)
        self.window_duration_seconds = float(window_duration_seconds)
        self.prediction_stride_seconds = float(prediction_stride_seconds)
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        predictions_path: Path,
        production_data_path: Optional[Path] = None,
        baseline_path: Optional[Path] = None,
        model_path: Optional[Path] = None,
        output_dir: Path = Path("outputs/monitoring"),
        baseline_missing_reason: Optional[str] = None,
    ) -> MonitoringReport:
        """
        Method Name :   run
        Description :   Run confidence, temporal, motion-context, and drift monitoring.

        Output      :   Returns MonitoringReport and writes monitoring_report.json.
        On Failure  :   Logs the error and raises the exception.
        """
        self.logger.info("=" * 60)
        self.logger.info("MONITORING PIPELINE - START")
        self.logger.info("=" * 60)

        report = MonitoringReport()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Loading predictions: {predictions_path}")
        predictions_df = pd.read_csv(predictions_path)

        # Apply post-hoc temperature scaling when T != 1.0
        if (
            self.calibration_temperature != 1.0
            and "confidence" in predictions_df.columns
        ):
            T = self.calibration_temperature
            p = predictions_df["confidence"].clip(1e-10, 1.0 - 1e-10).values
            p_cal = p ** (1.0 / T) / (p ** (1.0 / T) + (1.0 - p) ** (1.0 / T))
            predictions_df = predictions_df.copy()
            predictions_df["confidence"] = p_cal
            self.logger.info(
                "Temperature scaling applied: T=%.3f — mean confidence %.4f → %.4f",
                T,
                float(p.mean()),
                float(p_cal.mean()),
            )

        self.logger.info("\n" + "=" * 60)
        self.logger.info("LAYER 1: CONFIDENCE ANALYSIS")
        self.logger.info("=" * 60)
        report.layer1_confidence = self._analyze_confidence(predictions_df)

        self.logger.info("\n" + "=" * 60)
        self.logger.info("LAYER 2: TEMPORAL PATTERN ANALYSIS")
        self.logger.info("=" * 60)
        report.layer2_temporal = self._analyze_temporal_patterns(predictions_df)
        if production_data_path:
            motion_context = self._analyze_motion_context(
                production_data_path=production_data_path,
                dominant_pct=float(report.layer1_confidence.get("dominant_pct") or 0.0),
            )
            report.layer2_temporal["motion_context"] = motion_context
            if motion_context.get("low_motion_collapse_risk"):
                alert = (
                    "Low-motion collapse risk: "
                    f"G_mag_median={motion_context.get('g_mag_median'):.3f} deg/s, "
                    f"dominant_pct={report.layer1_confidence.get('dominant_pct', 0.0):.1f}%"
                )
                report.layer2_temporal["status"] = "WARNING"
                existing_alert = report.layer2_temporal.get("alert")
                report.layer2_temporal["alert"] = (
                    f"{existing_alert} | {alert}" if existing_alert else alert
                )
                self.logger.warning(alert)

        if production_data_path and baseline_path and Path(baseline_path).exists():
            self.logger.info("\n" + "=" * 60)
            self.logger.info("LAYER 3: DRIFT ANALYSIS")
            self.logger.info("=" * 60)
            report.layer3_drift = self._analyze_drift(
                production_data_path, baseline_path
            )
        elif baseline_missing_reason in (
            "DRIFT_BASELINE_MISSING",
            "DRIFT_BASELINE_MISMATCH_REVIEW",
        ):
            # The component resolved a unit-space mismatch or a missing raw baseline.
            # Do NOT compare raw production data against the normalized baseline —
            # that produces fake-critical z-scores (Az ≈ -9.8 m/s² vs baseline ≈ 0).
            self.logger.info("\n" + "=" * 60)
            self.logger.info("LAYER 3: DRIFT ANALYSIS - %s", baseline_missing_reason)
            self.logger.info("=" * 60)
            if baseline_missing_reason == "DRIFT_BASELINE_MISSING":
                alert = (
                    "Raw physical baseline not found. "
                    "Build it via src/monitoring/baseline_builder.py. "
                    "Drift severity cannot be trusted until baseline is available."
                )
            else:
                alert = (
                    "Baseline type mismatches the current preprocessing contract "
                    "(raw production data vs normalized baseline). "
                    "Rebuild the baseline with the correct script before trusting drift scores."
                )
            self.logger.warning(alert)
            report.layer3_drift = {
                "status": baseline_missing_reason,
                "reason": alert,
                "alert": alert,
            }
        else:
            self.logger.info("\n" + "=" * 60)
            self.logger.info("LAYER 3: DRIFT ANALYSIS - SKIPPED")
            self.logger.info("=" * 60)
            if not baseline_path:
                self.logger.warning("No baseline provided — drift analysis skipped")
            elif not Path(baseline_path).exists():
                self.logger.warning(f"Baseline not found: {baseline_path}")
            report.layer3_drift = {
                "status": "SKIPPED",
                "reason": "No baseline available",
            }

        report.overall_status = self._determine_overall_status(report)
        report.metadata = {
            "total_predictions": len(predictions_df),
            "predictions_path": str(predictions_path),
            "baseline_path": str(baseline_path) if baseline_path else None,
        }

        report_path = output_dir / "monitoring_report.json"
        with open(report_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        self.logger.info(f"Monitoring report saved: {report_path}")

        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"MONITORING RESULT: {report.overall_status}")
        self.logger.info("=" * 60)

        if report.alerts:
            self.logger.warning(f"{len(report.alerts)} alert(s) generated:")
            for alert in report.alerts:
                self.logger.warning(f"   - {alert}")

        return report

    def _analyze_confidence(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Method Name :   _analyze_confidence
        Description :   Analyze confidence, entropy, uncertainty, and class dominance.

        Output      :   Returns Layer 1 confidence and collapse metrics.
        On Failure  :   Logs the error and raises the exception.
        """
        results = {}

        mean_conf = df["confidence"].mean()
        std_conf = df["confidence"].std()
        min_conf = df["confidence"].min()
        max_conf = df["confidence"].max()

        results["mean_confidence"] = float(mean_conf)
        results["std_confidence"] = float(std_conf)
        results["min_confidence"] = float(min_conf)
        results["max_confidence"] = float(max_conf)
        results["confidence_warn_threshold"] = float(self.confidence_warn_threshold)
        results["uncertain_pct_threshold"] = float(self.uncertain_threshold_pct)

        if "is_uncertain" in df.columns:
            uncertain_count = df["is_uncertain"].sum()
        else:
            uncertain_count = (df["confidence"] < self.confidence_threshold).sum()
        uncertain_pct = 100 * uncertain_count / len(df)

        results["uncertain_count"] = int(uncertain_count)
        results["uncertain_percentage"] = float(uncertain_pct)

        if "entropy" in df.columns:
            entropy_vals = df["entropy"].astype(float).values
            mean_entropy = float(np.mean(entropy_vals))
            results["entropy_source"] = "stage4_prediction_csv"
        else:
            K = max(2, len([c for c in df.columns if c.startswith("prob_")]) or 11)
            eps = 1e-10
            confs = df["confidence"].clip(eps, 1.0 - eps).values
            entropy_vals = -(
                confs * np.log(confs)
                + (1 - confs) * np.log((1 - confs) / (K - 1) + eps)
            )
            mean_entropy = float(np.mean(entropy_vals))
            results["entropy_source"] = "approximated_from_max_confidence"
        results["mean_entropy"] = mean_entropy
        if "top2_margin" in df.columns:
            top2_margin = df["top2_margin"].astype(float)
            results["top2_margin_mean"] = float(top2_margin.mean())
            results["top2_margin_std"] = float(top2_margin.std())
            results["top2_margin_min"] = float(top2_margin.min())
            results["top2_margin_max"] = float(top2_margin.max())
        self.logger.info(
            f"Mean entropy ({results['entropy_source']}): {mean_entropy:.4f}"
        )
        self.logger.info(
            f"Uncertain predictions: {uncertain_count}/{len(df)} ({uncertain_pct:.1f}%)"
        )

        # Layer 1b: dominant-class collapse guard (A27)
        dominant_class: Optional[str] = None
        dominant_pct: float = 0.0
        if "predicted_activity" in df.columns and len(df) > 0:
            counts = df["predicted_activity"].value_counts(normalize=True)
            dominant_class = str(counts.index[0])
            dominant_pct = float(counts.iloc[0] * 100.0)
        results["dominant_class"] = dominant_class
        results["dominant_pct"] = dominant_pct
        results["dominant_class_warn_threshold"] = float(
            self.dominant_class_warn_threshold
        )
        results["dominant_class_critical_threshold"] = float(
            self.dominant_class_critical_threshold
        )
        results["dominance_warning"] = (
            dominant_pct >= self.dominant_class_warn_threshold
        )
        results["dominance_critical"] = (
            dominant_pct >= self.dominant_class_critical_threshold
        )
        if dominant_class is not None:
            self.logger.info(
                f"Dominant class: {dominant_class} at {dominant_pct:.1f}% "
                f"(warn {self.dominant_class_warn_threshold:.0f}, "
                f"critical {self.dominant_class_critical_threshold:.0f})"
            )

        alerts = []
        critical = False
        if mean_conf < self.confidence_warn_threshold:
            alerts.append(
                f"Low mean confidence: {mean_conf:.3f} < {self.confidence_warn_threshold:.3f}"
            )
            critical = True
        if uncertain_pct > self.uncertain_threshold_pct:
            alerts.append(
                f"High uncertainty rate: {uncertain_pct:.1f}% > {self.uncertain_threshold_pct}%"
            )
            critical = True
        if results["dominance_critical"]:
            alerts.append(
                f"Prediction collapse (critical): {dominant_class} at {dominant_pct:.1f}% "
                f">= {self.dominant_class_critical_threshold:.0f}%"
            )
            critical = True
        elif results["dominance_warning"]:
            alerts.append(
                f"Prediction collapse (warn): {dominant_class} at {dominant_pct:.1f}% "
                f">= {self.dominant_class_warn_threshold:.0f}%"
            )

        if alerts:
            results["status"] = "CRITICAL" if critical else "WARNING"
            results["alert"] = " | ".join(alerts)
            self.logger.warning(f"{results['alert']}")
        else:
            results["status"] = "HEALTHY"
            self.logger.info("Confidence check PASSED")

        return results

    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Method Name :   _analyze_temporal_patterns
        Description :   Analyze prediction sequence stability and dwell timing.

        Output      :   Returns Layer 2 temporal metrics.
        On Failure  :   Logs the error and raises the exception.
        """
        results = {}

        if "predicted_activity" not in df.columns:
            results["status"] = "SKIPPED"
            results["reason"] = "No activity column found"
            return results

        activities = df["predicted_activity"].values
        transitions = np.sum(activities[1:] != activities[:-1])
        transition_rate = (
            100 * transitions / (len(activities) - 1) if len(activities) > 1 else 0
        )

        results["total_windows"] = len(df)
        results["transitions"] = int(transitions)
        results["transition_rate"] = float(transition_rate)
        results["transition_rate_threshold"] = float(self.transition_rate_threshold)

        sequences = {}
        dwell_lengths = []
        current_activity = activities[0]
        current_length = 1

        for i in range(1, len(activities)):
            if activities[i] == current_activity:
                current_length += 1
            else:
                dwell_lengths.append(current_length)
                if current_activity not in sequences:
                    sequences[current_activity] = 0
                sequences[current_activity] = max(
                    sequences[current_activity], current_length
                )
                current_activity = activities[i]
                current_length = 1

        dwell_lengths.append(current_length)
        if current_activity not in sequences:
            sequences[current_activity] = 0
        sequences[current_activity] = max(sequences[current_activity], current_length)

        results["longest_sequences"] = sequences

        SHORT_DWELL_WINDOWS = 2
        if dwell_lengths:
            dwell_durations = [
                self.window_duration_seconds
                + max(0, d - 1) * self.prediction_stride_seconds
                for d in dwell_lengths
            ]
            mean_dwell_secs = float(np.mean(dwell_durations))
            short_dwell_ratio = float(
                sum(1 for d in dwell_lengths if d <= SHORT_DWELL_WINDOWS)
                / len(dwell_lengths)
            )
        else:
            mean_dwell_secs = 0.0
            short_dwell_ratio = 0.0
        results["mean_dwell_time_seconds"] = mean_dwell_secs
        results["window_duration_seconds"] = float(self.window_duration_seconds)
        results["prediction_stride_seconds"] = float(self.prediction_stride_seconds)
        results["short_dwell_ratio"] = short_dwell_ratio
        self.logger.info(
            f"Mean dwell time: {mean_dwell_secs:.1f}s  short_dwell_ratio: {short_dwell_ratio:.3f}"
        )
        self.logger.info(
            f"Activity transitions: {transitions} ({transition_rate:.1f}%)"
        )

        if transition_rate > self.transition_rate_threshold:
            alert = (
                f"High transition rate: {transition_rate:.1f}% > "
                f"{self.transition_rate_threshold:.1f}% (possible noise)"
            )
            results["status"] = "WARNING"
            results["alert"] = alert
            self.logger.warning(f"{alert}")
        else:
            results["status"] = "HEALTHY"
            self.logger.info("Temporal pattern check PASSED")

        return results

    def _analyze_motion_context(
        self, production_data_path: Path, dominant_pct: float
    ) -> Dict[str, Any]:
        """
        Method Name :   _analyze_motion_context
        Description :   Analyze gyro motion level and gravity-axis orientation from production_X.npy.

        Output      :   Returns G_mag, per-axis acceleration, and low-motion collapse-risk metrics.
        On Failure  :   Logs the error and returns an ERROR status dictionary.
        """
        try:
            windows = np.load(production_data_path)
            if windows.ndim != 3 or windows.shape[-1] != 6:
                raise ValueError(
                    f"Expected production_X.npy shape (n_windows, timesteps, 6), got {windows.shape}"
                )
            if not np.isfinite(windows).all():
                raise ValueError("production_X.npy contains NaN or inf values")

            accel = windows[:, :, :3].astype(np.float64, copy=False)
            gyro = windows[:, :, 3:6].astype(np.float64, copy=False)
            accel_flat = accel.reshape(-1, 3)
            gyro_flat = gyro.reshape(-1, 3)

            g_mag = np.sqrt(np.sum(gyro_flat * gyro_flat, axis=1))
            a_mag = np.sqrt(np.sum(accel_flat * accel_flat, axis=1))
            accel_axis_mean = accel_flat.mean(axis=0)
            accel_axis_std = accel_flat.std(axis=0)
            gyro_axis_mean = gyro_flat.mean(axis=0)
            gyro_axis_std = gyro_flat.std(axis=0)
            axis_names = ["Ax", "Ay", "Az"]
            dominant_idx = int(np.argmax(np.abs(accel_axis_mean)))

            g_mag_median = float(np.median(g_mag))
            low_gyro_motion = bool(g_mag_median < self.low_gyro_motion_threshold)
            low_motion_collapse_risk = bool(
                low_gyro_motion and dominant_pct >= self.low_motion_dominance_threshold
            )

            return {
                "status": "WARNING" if low_motion_collapse_risk else "HEALTHY",
                "production_data_path": str(production_data_path),
                "input_shape": list(windows.shape),
                "channel_order": ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"],
                "g_mag_median": g_mag_median,
                "g_mag_mean": float(np.mean(g_mag)),
                "g_mag_std": float(np.std(g_mag)),
                "g_mag_p05": float(np.percentile(g_mag, 5)),
                "g_mag_p95": float(np.percentile(g_mag, 95)),
                "a_mag_median": float(np.median(a_mag)),
                "a_mag_mean": float(np.mean(a_mag)),
                "accel_axis_mean": {
                    "Ax": float(accel_axis_mean[0]),
                    "Ay": float(accel_axis_mean[1]),
                    "Az": float(accel_axis_mean[2]),
                },
                "accel_axis_std": {
                    "Ax": float(accel_axis_std[0]),
                    "Ay": float(accel_axis_std[1]),
                    "Az": float(accel_axis_std[2]),
                },
                "gyro_axis_mean": {
                    "Gx": float(gyro_axis_mean[0]),
                    "Gy": float(gyro_axis_mean[1]),
                    "Gz": float(gyro_axis_mean[2]),
                },
                "gyro_axis_std": {
                    "Gx": float(gyro_axis_std[0]),
                    "Gy": float(gyro_axis_std[1]),
                    "Gz": float(gyro_axis_std[2]),
                },
                "gravity_dominant_axis": axis_names[dominant_idx],
                "gravity_dominant_axis_value": float(accel_axis_mean[dominant_idx]),
                "low_gyro_motion_threshold": float(self.low_gyro_motion_threshold),
                "low_motion_dominance_threshold": float(
                    self.low_motion_dominance_threshold
                ),
                "dominant_pct": float(dominant_pct),
                "low_gyro_motion": low_gyro_motion,
                "low_motion_collapse_risk": low_motion_collapse_risk,
                "threshold_note": (
                    "G_mag threshold is an empirical separator from the 28-session audit, "
                    "not a universal HAR constant."
                ),
            }
        except Exception as exc:
            self.logger.error("Motion-context analysis failed: %s", exc)
            return {
                "status": "ERROR",
                "error": str(exc),
                "production_data_path": str(production_data_path),
            }

    @staticmethod
    def _window_summary_features(windows: np.ndarray) -> np.ndarray:
        """
        Method Name :   _window_summary_features
        Description :   Represent each window by per-channel mean and std for MMD drift.

        Output      :   Returns a 2D feature matrix with channel means and standard deviations.
        On Failure  :   Logs the error and raises the exception.
        """
        if windows.ndim != 3:
            raise ValueError(
                f"Expected window tensor with shape (n, t, c), got {windows.shape}"
            )
        means = windows.mean(axis=1)
        stds = windows.std(axis=1)
        return np.concatenate([means, stds], axis=1).astype(np.float64, copy=False)

    @staticmethod
    def _sample_rows(
        values: np.ndarray, sample_size: int, rng: np.random.Generator
    ) -> np.ndarray:
        """
        Method Name :   _sample_rows
        Description :   Sample rows without replacement for efficient drift estimation.

        Output      :   Returns sampled rows or the original array when it is already small.
        On Failure  :   Logs the error and raises the exception.
        """
        if len(values) <= sample_size:
            return values
        idx = rng.choice(len(values), size=sample_size, replace=False)
        return values[idx]

    @staticmethod
    def _median_bandwidth(
        values: np.ndarray, rng: np.random.Generator, max_rows: int = 512
    ) -> float:
        """
        Method Name :   _median_bandwidth
        Description :   Estimate the RBF-kernel bandwidth using the median pairwise distance.

        Output      :   Returns a positive bandwidth value.
        On Failure  :   Logs the error and raises the exception.
        """
        sample = PostInferenceMonitor._sample_rows(values, max_rows, rng)
        if len(sample) < 2:
            return 1.0
        diffs = sample[:, None, :] - sample[None, :, :]
        dists = np.sqrt(np.sum(diffs * diffs, axis=2))
        upper = dists[np.triu_indices_from(dists, k=1)]
        positive = upper[upper > 0]
        if len(positive) == 0:
            return 1.0
        return float(np.median(positive))

    @staticmethod
    def _mmd2_rbf(x: np.ndarray, y: np.ndarray, bandwidth: float) -> float:
        """
        Method Name :   _mmd2_rbf
        Description :   Compute squared maximum mean discrepancy with an RBF kernel.

        Output      :   Returns the MMD^2 score between two samples.
        On Failure  :   Logs the error and raises the exception.
        """
        gamma = 1.0 / (2.0 * max(bandwidth, 1e-8) ** 2)
        xx = np.exp(-gamma * np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2))
        yy = np.exp(-gamma * np.sum((y[:, None, :] - y[None, :, :]) ** 2, axis=2))
        xy = np.exp(-gamma * np.sum((x[:, None, :] - y[None, :, :]) ** 2, axis=2))
        return float(xx.mean() + yy.mean() - 2.0 * xy.mean())

    def _analyze_zscore_mean_shift(
        self, production_data: np.ndarray, baseline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Method Name :   _analyze_zscore_mean_shift
        Description :   Compare production channel means against the transformed baseline.

        Output      :   Returns Layer 3 z-score mean-shift drift metrics.
        On Failure  :   Logs the error and raises the exception.
        """
        results: Dict[str, Any] = {}

        _required = {"mean", "std"}
        _missing = _required - set(baseline.keys())
        if _missing:
            raise ValueError(
                f"Baseline JSON is missing required keys: {_missing}. "
                f"Available keys: {list(baseline.keys())}. "
                f"Re-run Stage 10 (baseline update) to regenerate."
            )

        metadata = baseline.get("metadata", {}) if isinstance(baseline, dict) else {}
        # Support both a top-level "feature_space" key (future baselines) and the
        # legacy "metadata.feature_space" key (current baselines built by Stage 10 /
        # build_raw_physical_baseline.py).  Also accept "normalized_units" as an
        # alias for "transformed" so handwritten baselines still validate correctly.
        feature_space = baseline.get("feature_space") or metadata.get("feature_space")
        _valid_spaces = {"transformed", "raw_physical_units", "normalized_units", None}
        if feature_space not in _valid_spaces:
            raise ValueError(
                "Baseline feature-space mismatch: expected 'transformed', "
                "'raw_physical_units', or 'normalized_units', "
                f"got '{feature_space}'. Rebuild baseline."
            )

        prod_mean = production_data.mean(axis=(0, 1))
        prod_std = production_data.std(axis=(0, 1))

        baseline_mean = np.array(baseline["mean"])
        baseline_std = np.array(baseline["std"])

        if (
            baseline_mean.shape[0] != prod_mean.shape[0]
            or baseline_std.shape[0] != prod_std.shape[0]
        ):
            raise ValueError(
                "Baseline channel-shape mismatch: "
                f"baseline_mean={baseline_mean.shape[0]}, baseline_std={baseline_std.shape[0]}, "
                f"production={prod_mean.shape[0]}"
            )

        mean_diff = np.abs(prod_mean - baseline_mean) / (baseline_std + 1e-8)
        max_drift = float(np.max(mean_diff))
        channel_names = metadata.get("channel_names") or metadata.get("feature_names")
        if not channel_names or len(channel_names) != len(mean_diff):
            channel_names = [f"channel_{idx}" for idx in range(len(mean_diff))]
        per_channel_metrics = {
            str(name): {
                "drift_zscore": float(zscore),
                "psi": float(zscore),  # backward-compatible alias; value is not PSI
            }
            for name, zscore in zip(channel_names, mean_diff)
        }

        results["production_mean"] = prod_mean.tolist()
        results["production_std"] = prod_std.tolist()
        results["baseline_mean"] = baseline_mean.tolist()
        results["baseline_std"] = baseline_std.tolist()
        results["max_drift"] = max_drift
        results["aggregate_drift_score"] = max_drift
        results["per_channel_metrics"] = per_channel_metrics

        drift_channel_threshold = 1.0
        n_drifted_channels = int(np.sum(mean_diff > drift_channel_threshold))
        results["n_drifted_channels"] = n_drifted_channels
        self.logger.info(
            f"Max drift: {max_drift:.3f}  drifted channels: {n_drifted_channels}"
        )

        if max_drift > self.drift_threshold:
            alert = (
                f"Distribution drift detected: {max_drift:.3f} > {self.drift_threshold}"
            )
            results["status"] = "CRITICAL"
            results["alert"] = alert
            self.logger.warning(f"{alert}")
        else:
            results["status"] = "HEALTHY"
            self.logger.info("Drift check PASSED")
        return results

    def _analyze_mmd_drift(self, production_data: np.ndarray) -> Dict[str, Any]:
        """
        Method Name :   _analyze_mmd_drift
        Description :   Compare production and reference windows with MMD.

        Output      :   Returns Layer 3 MMD drift metrics.
        On Failure  :   Logs the error and raises the exception.
        """
        if self.mmd_reference_path is None:
            raise ValueError(
                "MMD drift mode requires mmd_reference_npy. "
                "Use transformed reference windows from the baseline replay set."
            )
        if not self.mmd_reference_path.exists():
            raise FileNotFoundError(
                f"MMD reference windows not found: {self.mmd_reference_path}"
            )

        reference_data = np.load(self.mmd_reference_path)
        ref_features = self._window_summary_features(reference_data)
        cur_features = self._window_summary_features(production_data)
        rng = np.random.default_rng(self.mmd_random_seed)
        sample_size = min(
            self.mmd_sample_size, max(32, len(ref_features)), max(32, len(cur_features))
        )
        ref_sample = self._sample_rows(ref_features, sample_size, rng)
        cur_sample = self._sample_rows(cur_features, sample_size, rng)
        combined = np.vstack([ref_sample, cur_sample])
        bandwidth = self._median_bandwidth(combined, rng)
        score = self._mmd2_rbf(ref_sample, cur_sample, bandwidth)

        if self.mmd_threshold is None:
            null_scores = []
            for _ in range(self.mmd_bootstrap_iterations):
                a = self._sample_rows(ref_features, sample_size, rng)
                b = self._sample_rows(ref_features, sample_size, rng)
                null_scores.append(self._mmd2_rbf(a, b, bandwidth))
            threshold = float(np.percentile(null_scores, 95))
            threshold_method = (
                "95th percentile of reference-vs-reference bootstrap MMD scores"
            )
        else:
            threshold = float(self.mmd_threshold)
            threshold_method = "configured mmd_threshold"

        ratio = float(score / threshold) if threshold > 0 else float("inf")
        results: Dict[str, Any] = {
            "drift_detector": "mmd",
            "mmd_score": float(score),
            "mmd_threshold": threshold,
            "mmd_threshold_ratio": ratio,
            "mmd_threshold_method": threshold_method,
            "mmd_bandwidth": float(bandwidth),
            "mmd_reference_path": str(self.mmd_reference_path),
            "mmd_reference_feature_level": "per-window summary features: channel means + channel stds",
            "mmd_sample_size": int(sample_size),
            "mmd_bootstrap_iterations": int(self.mmd_bootstrap_iterations),
            "aggregate_drift_score": ratio,
            "max_drift": float(score),
            "n_drifted_channels": 0,
            "per_channel_metrics": {},
        }

        if score > threshold:
            alert = f"MMD drift detected: {score:.6f} > {threshold:.6f}"
            results["status"] = "WARNING"
            results["alert"] = alert
            self.logger.warning(alert)
        else:
            results["status"] = "HEALTHY"
            self.logger.info("MMD drift check PASSED")

        return results

    def _analyze_drift(
        self, production_data_path: Path, baseline_path: Path
    ) -> Dict[str, Any]:
        """
        Method Name :   _analyze_drift
        Description :   Run the configured Layer 3 distribution-drift detector.

        Output      :   Returns drift status, scores, and per-channel metrics.
        On Failure  :   Logs the error and returns an ERROR status dictionary.
        """
        results = {}

        try:
            production_data = np.load(production_data_path)

            with open(baseline_path, "r") as f:
                baseline = json.load(f)

            zscore_results = self._analyze_zscore_mean_shift(production_data, baseline)
            if self.drift_detector_mode == "zscore_mean_shift":
                results = zscore_results
                results["drift_detector"] = "zscore_mean_shift"
            elif self.drift_detector_mode == "mmd":
                results = self._analyze_mmd_drift(production_data)
                results["secondary_zscore_mean_shift"] = {
                    "max_drift": zscore_results.get("max_drift"),
                    "status": zscore_results.get("status"),
                    "n_drifted_channels": zscore_results.get("n_drifted_channels"),
                    "per_channel_metrics": zscore_results.get(
                        "per_channel_metrics", {}
                    ),
                }
            else:
                raise ValueError(
                    f"Unknown drift_detector_mode '{self.drift_detector_mode}'. "
                    "Expected 'mmd' or 'zscore_mean_shift'."
                )

        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            self.logger.error(f"Drift analysis failed: {e}")

        return results

    def _determine_overall_status(self, report: MonitoringReport) -> str:
        """
        Method Name :   _determine_overall_status
        Description :   Combine layer statuses into the final Stage 6 health state.

        Output      :   Returns HEALTHY, WARNING, or CRITICAL.
        On Failure  :   Logs the error and raises the exception.
        """
        alerts = []

        if report.layer1_confidence.get("status") == "CRITICAL":
            alerts.append(report.layer1_confidence.get("alert"))

        if report.layer2_temporal.get("status") in ["CRITICAL", "WARNING"]:
            alerts.append(report.layer2_temporal.get("alert"))

        _drift_warn_statuses = {
            "WARNING",
            "DRIFT_BASELINE_MISSING",
            "DRIFT_BASELINE_MISMATCH_REVIEW",
        }
        if report.layer3_drift.get("status") in {"CRITICAL"} | _drift_warn_statuses:
            alerts.append(report.layer3_drift.get("alert"))

        report.alerts = alerts

        if (
            report.layer1_confidence.get("status") == "CRITICAL"
            or report.layer2_temporal.get("status") == "CRITICAL"
            or report.layer3_drift.get("status") == "CRITICAL"
        ):
            return "CRITICAL"
        elif (
            report.layer2_temporal.get("status") == "WARNING"
            or report.layer1_confidence.get("status") == "WARNING"
            or report.layer3_drift.get("status") in _drift_warn_statuses
        ):
            # DRIFT_BASELINE_MISSING / MISMATCH_REVIEW raise an alert but must NOT
            # escalate to CRITICAL — the monitoring system has no valid drift evidence.
            return "WARNING"
        return "HEALTHY"

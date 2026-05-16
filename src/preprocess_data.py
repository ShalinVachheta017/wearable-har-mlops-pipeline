"""
Production Data Preprocessing Pipeline (Unlabeled Only)
=======================================================
- Automatic unit detection (milliG vs m/s²)
- Automatic conversion when needed
- Comprehensive logging
- Sliding window creation for inference
Note: Training data preparation is intentionally excluded here. Use the
archived training pipeline if you need to retrain.

Author: Master Thesis MLOps Project
Date: December 7, 2025
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt  # type: ignore
from sklearn.preprocessing import RobustScaler, StandardScaler

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import (
    DATA_PREPARED,
    LOGS_DIR,
    MILLIG_TO_MS2,
    OVERLAP,
    PROJECT_ROOT,
    WINDOW_SIZE,
)

# ============================================================================
# LOGGING SETUP
# ============================================================================


class PreprocessLogger:
    """Configure comprehensive logging for preprocessing pipeline"""

    def __init__(self, log_name: str = "preprocessing"):
        self.log_dir = LOGS_DIR / "preprocessing"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers
        for handler in list(self.logger.handlers):
            self.logger.removeHandler(handler)

        # No need for own handlers — messages propagate to root logger
        # which already has console + file handlers configured in src.logger
        # This prevents duplicate log lines

        self.logger.info("=" * 80)
        self.logger.info("Preprocessing Pipeline Started")
        self.logger.info("=" * 80)

    def get_logger(self) -> logging.Logger:
        return self.logger


# ============================================================================
# UNIT DETECTION AND CONVERSION
# ============================================================================


class UnitDetector:
    """Automatically detect accelerometer units and convert if needed"""

    CONVERSION_FACTOR = MILLIG_TO_MS2

    # Expected ranges for unit detection
    MILLIG_RANGE = (-2000, 2000)  # Typical milliG range
    MS2_RANGE = (-20, 20)  # Typical m/s² range (±2g)

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def detect_units(self, df: pd.DataFrame, accel_cols: List[str]) -> str:
        """
        Detect if accelerometer data is in milliG or m/s²

        Args:
            df: DataFrame with accelerometer data
            accel_cols: List of accelerometer column names

        Returns:
            'milliG', 'm/s²', or 'unknown'
        """
        self.logger.info("Detecting accelerometer units...")

        # Get statistics (ignore NaN values)
        accel_data = df[accel_cols].values.flatten()
        accel_data = accel_data[~np.isnan(accel_data)]  # Remove NaN

        if len(accel_data) == 0:
            raise ValueError("All accelerometer values are NaN!")

        mean_val = np.abs(accel_data).mean()
        max_val = np.abs(accel_data).max()
        min_val = accel_data.min()
        max_abs = max(abs(min_val), max_val)

        self.logger.info("  Accelerometer statistics:")
        self.logger.info(f"    Mean (abs): {mean_val:.3f}")
        self.logger.info(f"    Max (abs):  {max_abs:.3f}")
        self.logger.info(f"    Range: [{min_val:.3f}, {max_val:.3f}]")

        # Decision logic
        if max_abs > 100:
            # Likely milliG (values > 100)
            unit = "milliG"
            confidence = "HIGH" if max_abs > 500 else "MEDIUM"
            self.logger.info(f"  ✓ Detected units: {unit} (confidence: {confidence})")
            self.logger.info(f"    Reason: Max absolute value {max_abs:.1f} >> 20 (m/s² range)")
        elif max_abs < 50:
            # Likely m/s² (values < 50)
            unit = "m/s²"
            confidence = "HIGH" if max_abs < 20 else "MEDIUM"
            self.logger.info(f"  ✓ Detected units: {unit} (confidence: {confidence})")
            self.logger.info(f"    Reason: Max absolute value {max_abs:.1f} < 50 (milliG range)")
        else:
            # Ambiguous range (50-100)
            unit = "unknown"
            self.logger.warning("  ⚠ Ambiguous units detected!")
            self.logger.warning(f"    Max absolute value {max_abs:.1f} in ambiguous range [50-100]")
            self.logger.warning("    Manual inspection recommended")

        return unit

    def convert_to_ms2(self, df: pd.DataFrame, accel_cols: List[str]) -> pd.DataFrame:
        """
        Convert accelerometer data from milliG to m/s²

        Args:
            df: DataFrame with accelerometer in milliG
            accel_cols: List of accelerometer column names

        Returns:
            DataFrame with accelerometer in m/s²
        """
        self.logger.info("Converting accelerometer units: milliG → m/s²")
        self.logger.info(f"  Conversion factor: {self.CONVERSION_FACTOR}")

        df_converted = df.copy()

        # Show BEFORE stats
        self.logger.info("  Before conversion (milliG):")
        for col in accel_cols:
            self.logger.info(f"    {col}: mean={df[col].mean():10.3f}, std={df[col].std():10.3f}")

        # Apply conversion
        for col in accel_cols:
            df_converted[col] = df[col] * self.CONVERSION_FACTOR

        # Show AFTER stats
        self.logger.info("  After conversion (m/s²):")
        for col in accel_cols:
            self.logger.info(
                f"    {col}: mean={df_converted[col].mean():10.3f}, std={df_converted[col].std():10.3f}"
            )

        # Validate conversion (Az should be ~-9.8 m/s² if stationary)
        if "Az" in accel_cols or "Az_w" in accel_cols:
            az_col = "Az" if "Az" in accel_cols else "Az_w"
            az_mean = df_converted[az_col].mean()
            expected_gravity = -9.8
            diff = abs(az_mean - expected_gravity)

            if diff < 5:
                self.logger.info(
                    f"  ✓ Validation: Az mean = {az_mean:.2f} m/s² (close to gravity -9.8)"
                )
            else:
                self.logger.warning(
                    f"  ⚠ Validation: Az mean = {az_mean:.2f} m/s² (differs from gravity -9.8)"
                )

        return df_converted

    def process_units(self, df: pd.DataFrame, accel_cols: List[str]) -> Tuple[pd.DataFrame, bool]:
        """
        Main entry point: detect units and convert if needed

        Returns:
            (processed_df, conversion_applied)
        """
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("UNIT DETECTION AND CONVERSION")
        self.logger.info("=" * 80)

        # Detect current units
        detected_units = self.detect_units(df, accel_cols)

        # Decision: convert or skip
        if detected_units == "milliG":
            self.logger.info("  → Decision: CONVERSION REQUIRED")
            df_processed = self.convert_to_ms2(df, accel_cols)
            conversion_applied = True
        elif detected_units == "m/s²":
            self.logger.info("  → Decision: CONVERSION NOT NEEDED (already in m/s²)")
            df_processed = df.copy()
            conversion_applied = False
        else:
            self.logger.error("  → Decision: CANNOT PROCEED (ambiguous units)")
            raise ValueError(
                "Cannot determine accelerometer units. "
                "Please verify data manually or specify units explicitly."
            )

        self.logger.info("=" * 80)
        return df_processed, conversion_applied


# ============================================================================
# GRAVITY REMOVAL (after unit conversion)
# ============================================================================


class GravityRemover:
    """
    Remove gravity component from accelerometer data using high-pass filter.
    Apply AFTER unit conversion (expects m/s² input).
    """

    ACCEL_COLUMNS = ["Ax", "Ay", "Az"]

    def __init__(
        self,
        logger: logging.Logger,
        cutoff_hz: float = 0.3,
        sampling_freq: float = 50.0,
        order: int = 3,
    ):
        self.logger = logger
        self.cutoff_hz = cutoff_hz
        self.sampling_freq = sampling_freq
        self.order = order

    def remove_gravity(self, df: pd.DataFrame, enable: bool = True) -> pd.DataFrame:
        """Apply high-pass Butterworth filter to remove gravity."""
        if not enable:
            self.logger.info("Gravity removal: DISABLED (skipping)")
            return df

        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("GRAVITY REMOVAL")
        self.logger.info("=" * 80)

        # Find available accel columns
        accel_cols = [c for c in self.ACCEL_COLUMNS if c in df.columns]
        if not accel_cols:
            self.logger.warning("No accelerometer columns found, skipping gravity removal")
            return df

        df_out = df.copy()

        # Design Butterworth high-pass filter
        nyquist = self.sampling_freq / 2
        normalized_cutoff = self.cutoff_hz / nyquist
        b, a = cast(
            Tuple[np.ndarray, np.ndarray],
            butter(self.order, normalized_cutoff, btype="high", output="ba"),
        )

        # Log before stats
        self.logger.info(
            f"  Filter: Butterworth high-pass, cutoff={self.cutoff_hz}Hz, order={self.order}"
        )
        for col in accel_cols:
            self.logger.info(f"  BEFORE {col}: mean={df[col].mean():.3f} m/s²")

        # Apply filter
        for col in accel_cols:
            values = df[col].values
            # Handle NaN by interpolating temporarily
            valid_mask = ~np.isnan(values)
            if valid_mask.sum() > self.order * 3:  # Need enough points for filter
                temp = np.interp(
                    np.arange(len(values)), np.where(valid_mask)[0], values[valid_mask]
                )
                filtered = filtfilt(b, a, temp)
                df_out[col] = filtered
            else:
                self.logger.warning(f"  Not enough valid points in {col} for filtering")

        # Log after stats
        for col in accel_cols:
            self.logger.info(f"  AFTER  {col}: mean={df_out[col].mean():.3f} m/s²")

        self.logger.info("  ✓ Gravity removal complete")
        self.logger.info("=" * 80)

        return df_out


# ============================================================================
# DOMAIN CALIBRATION (align production distribution to training)
# ============================================================================


class DomainCalibrator:
    """
    Calibrate production data to match training data distribution.
    This addresses domain shift when sensor orientations differ between
    training and production environments.

    Paper Support:
    - Domain Adaptation Survey (Chakma 2023)
    - Heterogeneity Activity Recognition Dataset (Stisen 2015)
    """

    SENSOR_COLUMNS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]

    def __init__(self, logger: logging.Logger, training_mean: Optional[np.ndarray] = None):
        self.logger = logger
        # Training data statistics from config.json (scaler was fit on this)
        # These are RAW values in m/s² (before normalization)
        if training_mean is None:
            # Default from all_users_data_labeled.csv training
            self.training_mean: np.ndarray = np.array(
                [3.22, 1.28, -3.53, 0.60, 0.23, 0.09], dtype=np.float64
            )
        else:
            self.training_mean = np.asarray(training_mean, dtype=np.float64)

    def calibrate(self, df: pd.DataFrame, enable: bool = True) -> pd.DataFrame:
        """
        Shift production data to match training distribution mean.

        This is simpler and more robust than gravity removal because:
        1. It preserves the relative motion patterns
        2. It aligns with what the model learned during training
        3. It handles arbitrary orientation differences, not just gravity
        """
        if not enable:
            self.logger.info("Domain calibration: DISABLED (skipping)")
            return df

        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("DOMAIN CALIBRATION")
        self.logger.info("=" * 80)

        # Find available sensor columns
        sensor_cols = [c for c in self.SENSOR_COLUMNS if c in df.columns]
        if not sensor_cols:
            self.logger.warning("No sensor columns found, skipping calibration")
            return df

        df_out = df.copy()

        self.logger.info("  Aligning production distribution to training distribution")
        self.logger.info(f"  {'Channel':<8} {'Prod Mean':<12} {'Train Mean':<12} {'Offset':<12}")
        self.logger.info("-" * 50)

        for i, col in enumerate(sensor_cols):
            if col in df.columns:
                prod_mean = df[col].mean()
                train_mean = self.training_mean[i]
                offset = prod_mean - train_mean

                # Apply calibration: shift production to match training mean
                df_out[col] = df[col] - offset

                self.logger.info(
                    f"  {col:<8} {prod_mean:<12.3f} {train_mean:<12.3f} {offset:<12.3f}"
                )

        self.logger.info("-" * 50)
        self.logger.info("  ✓ Calibration complete - production aligned to training")
        self.logger.info("=" * 80)

        return df_out


# ============================================================================
# DATA PREPROCESSING PIPELINE
# ============================================================================


class UnifiedPreprocessor:
    """Unified preprocessing for training and production data"""

    def __init__(
        self, logger: logging.Logger, window_size: int = WINDOW_SIZE, overlap: float = OVERLAP
    ):
        self.logger = logger
        self.window_size = window_size
        self.overlap = overlap
        self.step_size = int(window_size * (1 - overlap))
        self.scaler = StandardScaler()
        self.activity_to_label: Dict[str, int] = {}
        self.label_to_activity: Dict[int, str] = {}

        self.logger.info("Preprocessor initialized:")
        self.logger.info(f"  Window size: {window_size} samples")
        self.logger.info(f"  Overlap: {overlap*100:.0f}%")
        self.logger.info(f"  Step size: {self.step_size} samples")

    def detect_data_format(self, df: pd.DataFrame) -> Tuple[str, List[str]]:
        """
        Detect if data is labeled (training) or unlabeled (production)

        Returns:
            (format, sensor_columns)
        """
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("DATA FORMAT DETECTION")
        self.logger.info("=" * 80)

        has_activity = "activity" in df.columns
        has_user = "User" in df.columns

        # Check sensor column formats
        labeled_sensors = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
        unlabeled_sensors = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]

        has_labeled_format = all(col in df.columns for col in labeled_sensors)
        has_unlabeled_format = all(col in df.columns for col in unlabeled_sensors)

        if has_activity and has_user and has_labeled_format:
            self.logger.error("  ✗ Labeled training data is not supported in this script")
            self.logger.error("  Please use the archived training pipeline for retraining tasks")
            raise ValueError("Training (labeled) data is not supported here")
        elif has_unlabeled_format and has_activity:
            # Production CSV that also carries an 'activity' label column (e.g. synthetic data).
            # Use standard sensor columns but mark as labeled so create_windows extracts y.
            data_format = "labeled"
            sensor_cols = unlabeled_sensors
            self.logger.info("  Format: LABELED-PRODUCTION (standard sensors + activity column)")
            self.logger.info(f"  Columns: {', '.join(sensor_cols)} + activity + timestamp")
        elif has_unlabeled_format:
            data_format = "unlabeled"
            sensor_cols = unlabeled_sensors
            self.logger.info("  Format: UNLABELED (production data)")
            self.logger.info(f"  Columns: {', '.join(sensor_cols)} + timestamp")
        else:
            self.logger.error("  ✗ Unknown data format!")
            self.logger.error(f"  Available columns: {df.columns.tolist()}")
            raise ValueError(f"Cannot determine data format from columns: {df.columns.tolist()}")

        self.logger.info(f"  Samples: {len(df):,}")
        self.logger.info("=" * 80)

        return data_format, sensor_cols

    def create_activity_encoding(self, activities: pd.Series) -> Dict[str, int]:
        """Create mapping between activity names and numeric labels"""
        unique_activities = sorted(activities.unique())
        self.activity_to_label = {activity: idx for idx, activity in enumerate(unique_activities)}
        self.label_to_activity = {idx: activity for activity, idx in self.activity_to_label.items()}

        self.logger.info("")
        self.logger.info("Activity Encoding:")
        for activity, label in self.activity_to_label.items():
            count = (activities == activity).sum()
            self.logger.info(f"  {label:2d}: {activity:20s} ({count:6,} samples)")

        return self.activity_to_label

    def normalize_data(
        self, df: pd.DataFrame, sensor_cols: List[str], mode: str = "transform"
    ) -> pd.DataFrame:
        """
        Normalize sensor values using the scaler that was fit on training data.

        Reads ``normalization_variant`` from the canonical scaler file:
        ``data/prepared/scaler_train_only.json``.
          - ``"zscore"``  → StandardScaler (default; backward-compatible)
          - ``"robust"``  → RobustScaler (median / IQR)
          - ``"none"``    → passthrough — no amplitude normalization applied

        Args:
            df: DataFrame with sensor data
            sensor_cols: List of sensor column names
            mode: only 'transform' is supported (production)
        """
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("DATA NORMALIZATION")
        self.logger.info("=" * 80)

        df_normalized = df.copy()
        variant: str = "zscore"  # overwritten below; keeps linters happy
        nan_count = df[sensor_cols].isna().sum().sum()
        if nan_count > 0:
            self.logger.warning(f"  Found {nan_count} NaN values in sensor data")
            self.logger.warning("  Applying forward fill + backward fill")
            df_normalized[sensor_cols] = df_normalized[sensor_cols].ffill().bfill()

            # Check if any NaN remain
            remaining_nan = df_normalized[sensor_cols].isna().sum().sum()
            if remaining_nan > 0:
                self.logger.warning(f"  {remaining_nan} NaN values remain after filling")
                self.logger.warning("  Dropping rows with NaN")
                df_normalized = df_normalized.dropna(subset=sensor_cols).reset_index(drop=True)

            self.logger.info(f"  After NaN handling: {len(df_normalized):,} samples")

        if mode == "transform":
            # Canonical train-only scaler (fit on users 1-4).
            from src.utils.scaler import (
                CANONICAL_SCALER_PATH,
                assert_scaler_integrity,
            )

            config_path = CANONICAL_SCALER_PATH
            if not config_path.exists():
                raise FileNotFoundError(
                    f"Canonical scaler missing: {config_path}. "
                    "Run scripts/refit_scaler_train_only.py."
                )
            assert_scaler_integrity(config_path)

            with open(config_path, "r") as f:
                config = json.load(f)

            # Determine which variant was used during training (default: zscore for
            # backward compatibility with configs that pre-date this field)
            variant = config.get("normalization_variant", "zscore")
            self.logger.info("  Mode: TRANSFORM (production data with saved scaler)")
            self.logger.info(f"  Normalization variant: {variant}")

            if variant == "none":
                # Variant B — no amplitude normalization
                self.logger.info("  Skipping normalization (variant=none)")
            elif variant == "zscore":
                # Variant A — StandardScaler (z-score)
                self.scaler = StandardScaler()
                self.scaler.mean_ = np.array(config["scaler_mean"])
                self.scaler.scale_ = np.array(config["scaler_scale"])
                self.scaler.n_features_in_ = len(sensor_cols)
                self.logger.info("  Loaded z-score scaler from training:")
                self.logger.info(f"    Mean:  {self.scaler.mean_}")
                self.logger.info(f"    Scale: {self.scaler.scale_}")
                df_normalized[sensor_cols] = self.scaler.transform(df_normalized[sensor_cols])
            elif variant == "robust":
                # Variant C — RobustScaler (median / IQR)
                robust_scaler = RobustScaler()
                robust_scaler.center_ = np.array(config["scaler_center"])
                robust_scaler.scale_ = np.array(config["scaler_scale"])
                robust_scaler.n_features_in_ = len(sensor_cols)
                self.logger.info("  Loaded robust scaler from training:")
                self.logger.info(f"    Center (median): {robust_scaler.center_}")
                self.logger.info(f"    Scale (IQR):     {robust_scaler.scale_}")
                df_normalized[sensor_cols] = robust_scaler.transform(df_normalized[sensor_cols])
            else:
                raise ValueError(
                    f"Unknown normalization_variant '{variant}' in config. "
                    f"Expected 'zscore', 'robust', or 'none'."
                )
        else:
            raise ValueError(f"Invalid mode: {mode}. Only 'transform' (production) is supported.")

        # Log statistics (skipped for 'none' since data is unchanged)
        if variant != "none":
            self.logger.info("  After normalization:")
            self.logger.info(
                f"    Range: [{df_normalized[sensor_cols].values.min():.3f}, "
                f"{df_normalized[sensor_cols].values.max():.3f}]"
            )
            self.logger.info(f"    Mean:  {df_normalized[sensor_cols].values.mean():.3f}")
            self.logger.info(f"    Std:   {df_normalized[sensor_cols].values.std():.3f}")
        self.logger.info("=" * 80)

        return df_normalized

    def create_windows(
        self, df: pd.DataFrame, sensor_cols: List[str], data_format: str
    ) -> Tuple[np.ndarray, Optional[np.ndarray], List[Dict[str, Any]]]:
        """
        Create sliding windows from time series data

        Returns:
            X: (n_windows, window_size, n_sensors) array
            y: (n_windows,) array or None if unlabeled
            metadata: List of window info dicts
        """
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("SLIDING WINDOW CREATION")
        self.logger.info("=" * 80)

        n_samples = len(df)
        n_possible_windows = (n_samples - self.window_size) // self.step_size + 1

        self.logger.info(f"  Total samples: {n_samples:,}")
        self.logger.info(f"  Window size: {self.window_size}")
        self.logger.info(f"  Step size: {self.step_size}")
        self.logger.info(f"  Maximum possible windows: {n_possible_windows:,}")

        # ── Vectorized windowing (10-50x faster than Python loop) ──
        sensor_values = df[sensor_cols].values.astype(np.float32)  # (N, C)

        # Build index arrays for all windows at once
        start_indices = np.arange(n_possible_windows) * self.step_size
        valid_mask = (start_indices + self.window_size) <= n_samples
        start_indices = start_indices[valid_mask]

        # Use stride_tricks for zero-copy sliding window view
        from numpy.lib.stride_tricks import as_strided

        n_sensors = sensor_values.shape[1]
        stride_samples, stride_channels = sensor_values.strides
        all_windows = as_strided(
            sensor_values,
            shape=(len(start_indices), self.window_size, n_sensors),
            strides=(self.step_size * stride_samples, stride_samples, stride_channels),
        )
        # Copy to own memory (strided view is read-only)
        all_windows = np.array(all_windows)

        # Filter out windows containing NaN
        has_nan = np.isnan(all_windows).any(axis=(1, 2))
        good_idx = np.where(~has_nan)[0]

        X = all_windows[good_idx]

        # Build labels if labeled
        y_array: Optional[np.ndarray] = None
        if data_format == "labeled" and "activity" in df.columns:
            activities = df["activity"].astype(str).to_numpy()
            y_labels: List[int] = []
            for idx in good_idx:
                s = start_indices[idx]
                window_acts = np.asarray(activities[s : s + self.window_size], dtype=str)
                vals, counts = np.unique(window_acts, return_counts=True)
                majority = vals[counts.argmax()]
                y_labels.append(self.activity_to_label[majority])
            y_array = np.array(y_labels, dtype=np.int32)

        # Build metadata
        metadata: List[Dict[str, Any]] = []
        for j, idx in enumerate(good_idx):
            s = int(start_indices[idx])
            e = s + self.window_size
            meta: Dict[str, Any] = {
                "window_id": j,
                "start_idx": s,
                "end_idx": e,
            }
            if "timestamp_iso" in df.columns:
                meta["timestamp_start"] = str(df.iloc[s]["timestamp_iso"])
                meta["timestamp_end"] = str(df.iloc[e - 1]["timestamp_iso"])
            if "User" in df.columns:
                meta["user"] = str(df.iloc[s]["User"])
            metadata.append(meta)

        self.logger.info(f"  ✓ Created {len(X):,} windows")
        self.logger.info(f"  Shape: {X.shape}")
        self.logger.info(f"  Memory: {X.nbytes / 1024 / 1024:.2f} MB")

        if y_array is not None:
            self.logger.info(f"  Labels shape: {y_array.shape}")
            self.logger.info("  Label distribution:")
            for label_id in np.unique(y_array):
                count = (y_array == label_id).sum()
                activity = self.label_to_activity[int(label_id)]
                self.logger.info(f"    {label_id:2d} ({activity:20s}): {count:5,} windows")

        self.logger.info("=" * 80)

        return X, y_array, metadata

    def split_by_user(
        self,
        X: np.ndarray,
        y: np.ndarray,
        metadata: List[Dict[str, Any]],
        train_ratio: float = 0.66,
        val_ratio: float = 0.17,
    ) -> Dict[str, np.ndarray]:
        """
        Split data by user for train/val/test

        Ensures no user appears in multiple splits (prevents data leakage)
        """
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("TRAIN/VAL/TEST SPLIT BY USER")
        self.logger.info("=" * 80)

        # Get unique users
        users = np.array([str(m.get("user", "")) for m in metadata], dtype=str)
        unique_users = np.unique(users)
        n_users = len(unique_users)

        self.logger.info(f"  Total users: {n_users}")
        self.logger.info(
            f"  Split ratios: train={train_ratio:.2f}, val={val_ratio:.2f}, test={1-train_ratio-val_ratio:.2f}"
        )

        # Shuffle users
        np.random.seed(42)
        shuffled_users = np.random.permutation(unique_users)

        # Split users
        n_train = int(n_users * train_ratio)
        n_val = int(n_users * val_ratio)

        train_users = shuffled_users[:n_train]
        val_users = shuffled_users[n_train : n_train + n_val]
        test_users = shuffled_users[n_train + n_val :]

        self.logger.info(f"  Train users ({len(train_users)}): {list(train_users)}")
        self.logger.info(f"  Val users ({len(val_users)}): {list(val_users)}")
        self.logger.info(f"  Test users ({len(test_users)}): {list(test_users)}")

        # Split data
        train_mask = np.isin(users, train_users)
        val_mask = np.isin(users, val_users)
        test_mask = np.isin(users, test_users)

        splits: Dict[str, np.ndarray] = {
            "train_X": X[train_mask],
            "train_y": y[train_mask],
            "val_X": X[val_mask],
            "val_y": y[val_mask],
            "test_X": X[test_mask],
            "test_y": y[test_mask],
        }

        self.logger.info(f"  Train: {splits['train_X'].shape[0]:,} windows")
        self.logger.info(f"  Val:   {splits['val_X'].shape[0]:,} windows")
        self.logger.info(f"  Test:  {splits['test_X'].shape[0]:,} windows")
        self.logger.info("=" * 80)

        return splits

    def save_data(
        self,
        data: Dict[str, np.ndarray],
        metadata: List[Dict[str, Any]],
        data_format: str,
        conversion_applied: bool,
    ) -> None:
        """Save preprocessed production data and metadata"""
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("SAVING PREPROCESSED DATA")
        self.logger.info("=" * 80)

        DATA_PREPARED.mkdir(parents=True, exist_ok=True)

        # Save production data
        output_path = DATA_PREPARED / "production_X.npy"
        np.save(output_path, data["X"])
        self.logger.info(f"  Saved: {output_path.name} {data['X'].shape}")

        # Save metadata
        meta: Dict[str, Any] = {
            "created_date": datetime.now().isoformat(),
            "data_format": data_format,
            "window_size": self.window_size,
            "overlap": self.overlap,
            "total_windows": data["X"].shape[0],
            "conversion_applied": conversion_applied,
            "windows": metadata,
        }

        meta_path = DATA_PREPARED / "production_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        self.logger.info(f"  Saved: {meta_path.name}")

        self.logger.info("=" * 80)


# ============================================================================
# MAIN PIPELINE
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Production preprocessing pipeline (unit auto-detection)"
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Input CSV file path (relative to project root)"
    )
    parser.add_argument(
        "--gravity-removal",
        action="store_true",
        default=False,
        help="Enable gravity removal (high-pass filter at 0.3Hz)",
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        default=False,
        help="Enable domain calibration (align production to training distribution)",
    )
    args = parser.parse_args()

    # Validate options
    if args.gravity_removal and args.calibrate:
        print("ERROR: Cannot use both --gravity-removal and --calibrate. Choose one.")
        print("  --gravity-removal: Removes DC offset (gravity) using high-pass filter")
        print("  --calibrate: Shifts production distribution to match training (RECOMMENDED)")
        sys.exit(1)

    # Setup logging
    logger_setup = PreprocessLogger("production_preprocessing")
    logger = logger_setup.get_logger()

    try:
        logger.info("Mode: PRODUCTION")
        logger.info(f"Input: {args.input}")
        logger.info(f"Gravity removal: {'ENABLED' if args.gravity_removal else 'DISABLED'}")
        logger.info(f"Domain calibration: {'ENABLED' if args.calibrate else 'DISABLED'}")

        # Load data
        input_path = PROJECT_ROOT / args.input
        logger.info(f"Loading data from: {input_path}")
        df = pd.read_csv(input_path)
        logger.info(f"  Loaded: {len(df):,} rows, {len(df.columns)} columns")

        # Initialize components
        unit_detector = UnitDetector(logger)
        gravity_remover = GravityRemover(logger)
        calibrator = DomainCalibrator(logger)
        preprocessor = UnifiedPreprocessor(logger)

        # Detect data format
        data_format, sensor_cols = preprocessor.detect_data_format(df)

        # Detect and convert units (accelerometer only)
        accel_cols = [col for col in sensor_cols if col.startswith("A")]
        df, conversion_applied = unit_detector.process_units(df, accel_cols)

        # Apply gravity removal OR calibration (not both)
        if args.gravity_removal:
            df = gravity_remover.remove_gravity(df, enable=True)
        elif args.calibrate:
            df = calibrator.calibrate(df, enable=True)

        # Normalize data (production only)
        df_normalized = preprocessor.normalize_data(df, sensor_cols, mode="transform")

        # Create windows
        X, _, metadata = preprocessor.create_windows(df_normalized, sensor_cols, data_format)

        # Save production data
        data = {"X": X}
        preprocessor.save_data(data, metadata, data_format, conversion_applied)

        logger.info("")
        logger.info("=" * 80)
        logger.info("✓ PREPROCESSING COMPLETE!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"✗ PREPROCESSING FAILED: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

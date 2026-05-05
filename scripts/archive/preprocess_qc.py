#!/usr/bin/env python
"""
Preprocessing Quality Control (QC) Script
==========================================

Validates preprocessing contract between production data and training expectations.
Checks for common issues that cause low model accuracy.

Usage:
    python scripts/preprocess_qc.py --input data/processed/sensor_fused_50Hz.csv
    python scripts/preprocess_qc.py --input data/prepared/production_X.npy --type normalized
    python scripts/preprocess_qc.py --input data/prepared/garmin_labeled.csv --type labeled

Output:
    - JSON report: reports/preprocess_qc/<timestamp>.json
    - Console: PASS/FAIL summary

Author: MLOps Pipeline Audit
Date: January 9, 2026
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from config import (
    PROJECT_ROOT, DATA_PREPARED, DATA_PROCESSED,
    WINDOW_SIZE, OVERLAP, NUM_SENSORS, NUM_CLASSES,
    SENSOR_COLUMNS, ACTIVITY_LABELS
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CheckResult:
    """Result of a single QC check."""
    name: str
    passed: bool
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QCReport:
    """Complete QC report."""
    timestamp: str
    input_file: str
    input_type: str
    checks_passed: int
    checks_failed: int
    critical_failures: int
    overall_status: str  # PASS, WARN, FAIL
    checks: List[Dict]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# QC CHECKS
# ============================================================================

class PreprocessQC:
    """Preprocessing Quality Control validator."""
    
    # Column names
    TRAINING_COLS = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
    PRODUCTION_COLS = ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz']
    
    # Unit detection thresholds
    MILLIG_THRESHOLD = 100  # Values > 100 likely milliG
    MS2_THRESHOLD = 50  # Values < 50 likely m/s²
    
    # Gyroscope unit thresholds
    GYRO_DEGS_THRESHOLD = 50  # deg/s typical range
    GYRO_RADS_THRESHOLD = 1   # rad/s typical range
    
    def __init__(self):
        self.checks: List[CheckResult] = []
        self.summary: Dict[str, Any] = {}
        
        # Load scaler config if exists
        self.scaler_config = self._load_scaler_config()
    
    def _load_scaler_config(self) -> Optional[Dict]:
        """Load training scaler configuration."""
        config_path = DATA_PREPARED / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return None
    
    def _add_check(self, name: str, passed: bool, severity: str, 
                   message: str, details: Dict = None):
        """Add a check result."""
        self.checks.append(CheckResult(
            name=name,
            passed=bool(passed),  # Force conversion to Python bool
            severity=severity,
            message=message,
            details=details or {}
        ))
        
        status = "✅ PASS" if passed else f"❌ FAIL ({severity})"
        logger.info(f"  {status}: {name}")
        if not passed:
            logger.warning(f"    → {message}")
    
    # -------------------------------------------------------------------------
    # Schema Checks
    # -------------------------------------------------------------------------
    
    def check_schema(self, df: pd.DataFrame, data_type: str) -> None:
        """Check required columns exist."""
        logger.info("\n📋 SCHEMA CHECKS")
        
        if data_type == 'labeled':
            required = self.TRAINING_COLS + ['activity']
        else:
            required = self.PRODUCTION_COLS
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        missing = [c for c in required if c not in df.columns]
        
        self._add_check(
            name="Required columns exist",
            passed=len(missing) == 0,
            severity="CRITICAL",
            message=f"Missing columns: {missing}" if missing else "All required columns present",
            details={"required": required, "missing": missing, "actual": df.columns.tolist()}
        )
        
        # Check for extra whitespace in column names (common CSV issue)
        has_whitespace = any(' ' in c for c in df.columns)
        if has_whitespace:
            self._add_check(
                name="Column names clean",
                passed=False,
                severity="HIGH",
                message="Column names have extra whitespace - may cause matching issues",
                details={"columns": df.columns.tolist()}
            )
    
    # -------------------------------------------------------------------------
    # Missingness Checks
    # -------------------------------------------------------------------------
    
    def check_missingness(self, df: pd.DataFrame, sensor_cols: List[str]) -> None:
        """Check for NaN values and gaps in sensor data."""
        logger.info("\n📊 MISSINGNESS CHECKS")
        
        # Count NaNs per channel
        nan_counts = df[sensor_cols].isna().sum()
        total_samples = len(df)
        
        max_missing_pct = (nan_counts.max() / total_samples) * 100
        
        self._add_check(
            name="Missing values acceptable",
            passed=max_missing_pct < 5.0,  # Allow up to 5% missing
            severity="HIGH",
            message=f"Max missing: {max_missing_pct:.2f}%" if max_missing_pct >= 5.0 else f"Max missing: {max_missing_pct:.2f}%",
            details={
                "missing_per_channel": nan_counts.to_dict(),
                "total_samples": total_samples,
                "max_missing_pct": round(max_missing_pct, 2)
            }
        )
        
        # Check for large consecutive gaps
        for col in sensor_cols:
            if col in df.columns:
                is_nan = df[col].isna()
                # Find consecutive NaN sequences
                nan_groups = is_nan.ne(is_nan.shift()).cumsum()[is_nan]
                if len(nan_groups) > 0:
                    max_gap = nan_groups.value_counts().max()
                    if max_gap > 50:  # More than 1 second at 50Hz
                        self._add_check(
                            name=f"No large gaps in {col}",
                            passed=False,
                            severity="MEDIUM",
                            message=f"Max consecutive NaN: {max_gap} samples (>{max_gap/50:.1f}s at 50Hz)",
                            details={"column": col, "max_gap_samples": int(max_gap)}
                        )
        
        self.summary["missing_data"] = {
            "max_missing_pct": round(max_missing_pct, 2),
            "channels_with_missing": [col for col in sensor_cols if df[col].isna().sum() > 0]
        }
    
    # -------------------------------------------------------------------------
    # Timestamp Checks
    # -------------------------------------------------------------------------
    
    def check_timestamps(self, df: pd.DataFrame) -> None:
        """Check timestamp quality."""
        logger.info("\n⏱️ TIMESTAMP CHECKS")
        
        # Find timestamp column
        ts_col = None
        for col in ['timestamp', 'timestamp_ms', 'timestamp_iso']:
            if col in df.columns:
                ts_col = col
                break
        
        if ts_col is None:
            self._add_check(
                name="Timestamp column exists",
                passed=False,
                severity="HIGH",
                message="No timestamp column found",
                details={"columns": df.columns.tolist()}
            )
            return
        
        # Check monotonicity
        if df[ts_col].dtype in ['int64', 'float64']:
            is_monotonic = bool(df[ts_col].is_monotonic_increasing)
        else:
            try:
                ts_parsed = pd.to_datetime(df[ts_col])
                is_monotonic = bool(ts_parsed.is_monotonic_increasing)
            except:
                is_monotonic = False
        
        self._add_check(
            name="Timestamps monotonic",
            passed=is_monotonic,
            severity="HIGH",
            message="Timestamps are not strictly increasing" if not is_monotonic else "OK",
            details={}
        )
        
        # Check for duplicates
        n_dups = df[ts_col].duplicated().sum()
        self._add_check(
            name="No duplicate timestamps",
            passed=n_dups == 0,
            severity="MEDIUM",
            message=f"Found {n_dups} duplicate timestamps" if n_dups > 0 else "OK",
            details={"duplicates": int(n_dups)}
        )
    
    # -------------------------------------------------------------------------
    # Sampling Rate Checks
    # -------------------------------------------------------------------------
    
    def check_sampling_rate(self, df: pd.DataFrame, expected_hz: float = 50.0) -> None:
        """Check sampling rate consistency and verify resampling."""
        logger.info("\n📊 SAMPLING RATE CHECKS")
        
        # Find timestamp column
        ts_col = None
        for col in ['timestamp', 'timestamp_ms', 'timestamp_iso']:
            if col in df.columns:
                ts_col = col
                break
        
        if ts_col is None:
            return
        
        try:
            if df[ts_col].dtype in ['int64', 'float64']:
                # Assume milliseconds
                time_diffs = df[ts_col].diff().dropna()
                median_diff_ms = time_diffs.median()
                std_diff_ms = time_diffs.std()
                actual_hz = 1000.0 / median_diff_ms if median_diff_ms > 0 else 0
            else:
                ts_parsed = pd.to_datetime(df[ts_col])
                time_diffs = ts_parsed.diff().dropna()
                median_diff_sec = time_diffs.median().total_seconds()
                std_diff_sec = time_diffs.std().total_seconds()
                actual_hz = 1.0 / median_diff_sec if median_diff_sec > 0 else 0
                std_diff_ms = std_diff_sec * 1000
            
            tolerance = 0.1  # 10% tolerance
            hz_diff = abs(actual_hz - expected_hz) / expected_hz
            
            self._add_check(
                name="Sampling rate correct",
                passed=hz_diff < tolerance,
                severity="HIGH",
                message=f"Actual: {actual_hz:.1f}Hz, Expected: {expected_hz}Hz" if hz_diff >= tolerance else f"OK ({actual_hz:.1f}Hz)",
                details={"actual_hz": round(actual_hz, 2), "expected_hz": expected_hz, "deviation": round(hz_diff, 3)}
            )
            
            # Check resampling quality (std of time differences should be small)
            expected_interval_ms = 1000.0 / expected_hz
            jitter_pct = (std_diff_ms / expected_interval_ms) * 100 if expected_interval_ms > 0 else 0
            
            self._add_check(
                name="Resampling jitter acceptable",
                passed=jitter_pct < 5.0,  # Less than 5% jitter
                severity="MEDIUM",
                message=f"Jitter: {jitter_pct:.2f}% of interval" if jitter_pct >= 5.0 else f"OK (jitter: {jitter_pct:.2f}%)",
                details={
                    "std_interval_ms": round(std_diff_ms, 3),
                    "expected_interval_ms": round(expected_interval_ms, 2),
                    "jitter_pct": round(jitter_pct, 2)
                }
            )
            
            self.summary["sampling_rate_hz"] = round(actual_hz, 2)
            self.summary["resampling_jitter_pct"] = round(jitter_pct, 2)
            
        except Exception as e:
            self._add_check(
                name="Sampling rate calculation",
                passed=False,
                severity="MEDIUM",
                message=f"Could not compute sampling rate: {e}",
                details={}
            )
    
    # -------------------------------------------------------------------------
    # Unit Detection and Conversion Checks
    # -------------------------------------------------------------------------
    
    def check_units(self, df: pd.DataFrame, data_type: str) -> None:
        """Check accelerometer units (milliG vs m/s²)."""
        logger.info("\n📐 UNIT CHECKS")
        
        # Find accelerometer columns
        if data_type == 'labeled':
            accel_cols = ['Ax_w', 'Ay_w', 'Az_w']
        else:
            accel_cols = ['Ax', 'Ay', 'Az']
        
        available_cols = [c for c in accel_cols if c in df.columns]
        if not available_cols:
            self._add_check(
                name="Accelerometer columns exist",
                passed=False,
                severity="CRITICAL",
                message="No accelerometer columns found",
                details={}
            )
            return
        
        # Get max absolute value
        accel_data = df[available_cols].values.flatten()
        accel_data = accel_data[~np.isnan(accel_data)]
        
        max_abs = np.abs(accel_data).max()
        mean_abs = np.abs(accel_data).mean()
        
        # Determine units
        if max_abs > self.MILLIG_THRESHOLD:
            detected_units = "milliG"
            needs_conversion = True
        elif max_abs < self.MS2_THRESHOLD:
            detected_units = "m/s²"
            needs_conversion = False
        else:
            detected_units = "ambiguous"
            needs_conversion = None
        
        # Check Az for gravity (should be ~-9.8 m/s² or ~-1000 milliG)
        az_col = 'Az_w' if 'Az_w' in df.columns else ('Az' if 'Az' in df.columns else None)
        if az_col:
            az_mean = df[az_col].mean()
            gravity_check = (
                (detected_units == "m/s²" and -12 < az_mean < -7) or
                (detected_units == "milliG" and -1200 < az_mean < -800)
            )
        else:
            gravity_check = True
        
        self._add_check(
            name="Accelerometer units detected",
            passed=detected_units != "ambiguous",
            severity="CRITICAL",
            message=f"Detected: {detected_units} (max={max_abs:.1f})",
            details={"detected_units": detected_units, "max_abs": round(max_abs, 2), "gravity_check": bool(gravity_check)}
        )
    
    # -------------------------------------------------------------------------
    # Gyroscope Unit Checks
    # -------------------------------------------------------------------------
    
    def check_gyro_units(self, df: pd.DataFrame, data_type: str) -> None:
        """Check gyroscope units (deg/s vs rad/s)."""
        logger.info("\n🔄 GYROSCOPE UNIT CHECKS")
        
        # Find gyroscope columns
        if data_type == 'labeled':
            gyro_cols = ['Gx_w', 'Gy_w', 'Gz_w']
        else:
            gyro_cols = ['Gx', 'Gy', 'Gz']
        
        available_cols = [c for c in gyro_cols if c in df.columns]
        if not available_cols:
            self._add_check(
                name="Gyroscope columns exist",
                passed=False,
                severity="CRITICAL",
                message="No gyroscope columns found",
                details={}
            )
            return
        
        # Get max absolute value
        gyro_data = df[available_cols].values.flatten()
        gyro_data = gyro_data[~np.isnan(gyro_data)]
        
        max_abs = np.abs(gyro_data).max()
        mean_abs = np.abs(gyro_data).mean()
        
        # Determine units
        if max_abs > self.GYRO_DEGS_THRESHOLD:
            detected_units = "deg/s"
            expected = True
        elif max_abs < self.GYRO_RADS_THRESHOLD:
            detected_units = "rad/s"
            expected = False  # Should be deg/s
        else:
            detected_units = "ambiguous"
            expected = None
        
        self._add_check(
            name="Gyroscope units correct",
            passed=expected is True,
            severity="HIGH",
            message=f"Detected: {detected_units} (max={max_abs:.1f})" if expected is not True else f"OK (deg/s, max={max_abs:.1f})",
            details={
                "detected_units": detected_units,
                "max_abs": round(float(max_abs), 2),
                "mean_abs": round(float(mean_abs), 2),
                "expected_units": "deg/s"
            }
        )
        
        self.summary["gyro_units"] = detected_units
    
    # -------------------------------------------------------------------------
    # Normalization Checks
    # -------------------------------------------------------------------------
    
    def check_normalization(self, data: np.ndarray) -> None:
        """Check if normalized data has expected distribution."""
        logger.info("\n📈 NORMALIZATION CHECKS")
        
        # Compute per-channel statistics
        if len(data.shape) == 3:
            # Shape: (n_windows, timesteps, channels)
            mean_per_channel = data.mean(axis=(0, 1))
            std_per_channel = data.std(axis=(0, 1))
        else:
            # Shape: (n_samples, channels)
            mean_per_channel = data.mean(axis=0)
            std_per_channel = data.std(axis=0)
        
        # Load expected scaler from config (not hardcoded)
        expected_mean = None
        expected_scale = None
        if self.scaler_config:
            expected_mean = self.scaler_config.get('scaler_mean')
            expected_scale = self.scaler_config.get('scaler_scale')
        
        # Check mean close to 0
        mean_ok = bool(np.allclose(mean_per_channel, 0, atol=1.0))
        self._add_check(
            name="Normalized mean ≈ 0",
            passed=mean_ok,
            severity="CRITICAL",
            message=f"Mean per channel: {mean_per_channel.round(3).tolist()}" if not mean_ok else "OK",
            details={
                "mean_per_channel": mean_per_channel.round(4).tolist(),
                "scaler_mean_used": expected_mean
            }
        )
        
        # Check std close to 1
        std_ok = bool(np.allclose(std_per_channel, 1, atol=0.5))
        self._add_check(
            name="Normalized std ≈ 1",
            passed=std_ok,
            severity="CRITICAL",
            message=f"Std per channel: {std_per_channel.round(3).tolist()}" if not std_ok else "OK",
            details={
                "std_per_channel": std_per_channel.round(4).tolist(),
                "scaler_scale_used": expected_scale
            }
        )
        
        self.summary["normalized_mean"] = mean_per_channel.round(4).tolist()
        self.summary["normalized_std"] = std_per_channel.round(4).tolist()
        
        # ⚠️ THE KEY DIAGNOSTIC - Variance collapse detection
        if not std_ok and bool(np.all(std_per_channel < 0.5)):
            self._add_check(
                name="Variance collapse detected",
                passed=False,
                severity="CRITICAL",
                message="Production data has MUCH LOWER variance than training. "
                        "This indicates IDLE/STATIONARY data with no activity patterns. "
                        "Collect data with actual activities for valid inference.",
                details={
                    "issue": "variance_collapse",
                    "actual_std": std_per_channel.round(4).tolist(),
                    "expected_std": [1.0] * len(std_per_channel),
                    "likely_cause": "idle_data"
                }
            )
    
    # -------------------------------------------------------------------------
    # Channel Order Checks
    # -------------------------------------------------------------------------
    
    def check_channel_order(self, df: pd.DataFrame, data_type: str) -> None:
        """Validate channel order matches expected [Ax, Ay, Az, Gx, Gy, Gz]."""
        logger.info("\n🔤 CHANNEL ORDER CHECK")
        
        if data_type != "production":
            return
        
        expected_order = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
        
        # Get actual sensor columns (exclude timestamp columns)
        sensor_cols = [c for c in df.columns if c in expected_order]
        actual_order = sensor_cols
        
        order_matches = actual_order == expected_order
        
        self._add_check(
            name="Channel order correct",
            passed=order_matches,
            severity="CRITICAL",
            message=f"Expected {expected_order}, got {actual_order}" if not order_matches else "OK",
            details={"expected": expected_order, "actual": actual_order}
        )
    
    # -------------------------------------------------------------------------
    # Normalization Checks
    # -------------------------------------------------------------------------
    
    def check_normalization(self, data: np.ndarray) -> None:
        """Check if normalized data has expected distribution."""
        logger.info("\n📈 NORMALIZATION CHECKS")
        
        # Compute per-channel statistics
        if len(data.shape) == 3:
            # Shape: (n_windows, timesteps, channels)
            mean_per_channel = data.mean(axis=(0, 1))
            std_per_channel = data.std(axis=(0, 1))
        else:
            # Shape: (n_samples, channels)
            mean_per_channel = data.mean(axis=0)
            std_per_channel = data.std(axis=0)
        
        # Check mean close to 0
        mean_ok = bool(np.allclose(mean_per_channel, 0, atol=1.0))
        self._add_check(
            name="Normalized mean ≈ 0",
            passed=mean_ok,
            severity="CRITICAL",
            message=f"Mean per channel: {mean_per_channel.round(3).tolist()}" if not mean_ok else "OK",
            details={"mean_per_channel": mean_per_channel.round(4).tolist()}
        )
        
        # Check std close to 1
        std_ok = bool(np.allclose(std_per_channel, 1, atol=0.5))
        self._add_check(
            name="Normalized std ≈ 1",
            passed=std_ok,
            severity="CRITICAL",
            message=f"Std per channel: {std_per_channel.round(3).tolist()}" if not std_ok else "OK",
            details={"std_per_channel": std_per_channel.round(4).tolist()}
        )
        
        self.summary["normalized_mean"] = mean_per_channel.round(4).tolist()
        self.summary["normalized_std"] = std_per_channel.round(4).tolist()
        
        # ⚠️ THE KEY DIAGNOSTIC
        if not std_ok and bool(np.all(std_per_channel < 0.5)):
            self._add_check(
                name="Variance collapse detected",
                passed=False,
                severity="CRITICAL",
                message="Production data has MUCH LOWER variance than training. "
                        "This will cause near-random predictions. "
                        "Check: (1) unit conversion, (2) scaler mismatch, (3) data source",
                details={
                    "issue": "variance_collapse",
                    "actual_std": std_per_channel.round(4).tolist(),
                    "expected_std": [1.0] * len(std_per_channel)
                }
            )
    
    # -------------------------------------------------------------------------
    # Windowing Checks
    # -------------------------------------------------------------------------
    
    def check_windowing(self, data: np.ndarray) -> None:
        """Check window shape matches model expectations."""
        logger.info("\n🪟 WINDOWING CHECKS")
        
        if len(data.shape) != 3:
            self._add_check(
                name="Data is 3D",
                passed=False,
                severity="CRITICAL",
                message=f"Expected 3D array, got shape {data.shape}",
                details={"shape": data.shape}
            )
            return
        
        n_windows, timesteps, channels = data.shape
        
        # Check timesteps
        self._add_check(
            name="Window size correct",
            passed=timesteps == WINDOW_SIZE,
            severity="CRITICAL",
            message=f"Expected {WINDOW_SIZE} timesteps, got {timesteps}",
            details={"expected": WINDOW_SIZE, "actual": timesteps}
        )
        
        # Check channels
        self._add_check(
            name="Channel count correct",
            passed=channels == NUM_SENSORS,
            severity="CRITICAL",
            message=f"Expected {NUM_SENSORS} channels, got {channels}",
            details={"expected": NUM_SENSORS, "actual": channels}
        )
        
        self.summary["n_windows"] = n_windows
        self.summary["window_shape"] = list(data.shape)
    
    # -------------------------------------------------------------------------
    # Main Entry Points
    # -------------------------------------------------------------------------
    
    def validate_raw_csv(self, file_path: Path, data_type: str) -> QCReport:
        """Validate raw CSV file (production or labeled)."""
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 PREPROCESSING QC: {file_path.name}")
        logger.info(f"{'='*60}")
        
        # Load data
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()  # Clean column names
        
        logger.info(f"📂 Loaded {len(df):,} rows, {len(df.columns)} columns")
        
        # Get sensor columns for checks
        if data_type == 'labeled':
            sensor_cols = self.TRAINING_COLS
        else:
            sensor_cols = self.PRODUCTION_COLS
        
        # Run checks
        self.check_schema(df, data_type)
        self.check_missingness(df, sensor_cols)
        self.check_timestamps(df)
        self.check_sampling_rate(df)
        self.check_units(df, data_type)
        self.check_gyro_units(df, data_type)
        self.check_channel_order(df, data_type)
        
        return self._generate_report(str(file_path), data_type)
    
    def validate_normalized_npy(self, file_path: Path) -> QCReport:
        """Validate normalized numpy array after preprocessing."""
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 PREPROCESSING QC: {file_path.name}")
        logger.info(f"{'='*60}")
        
        # Load data
        data = np.load(file_path)
        logger.info(f"📂 Loaded array shape: {data.shape}, dtype: {data.dtype}")
        
        # Run checks
        self.check_windowing(data)
        self.check_normalization(data)
        
        return self._generate_report(str(file_path), 'normalized')
    
    def _generate_report(self, input_file: str, input_type: str) -> QCReport:
        """Generate final QC report."""
        n_passed = sum(1 for c in self.checks if c.passed)
        n_failed = sum(1 for c in self.checks if not c.passed)
        n_critical = sum(1 for c in self.checks if not c.passed and c.severity == "CRITICAL")
        
        if n_critical > 0:
            status = "FAIL"
        elif n_failed > 0:
            status = "WARN"
        else:
            status = "PASS"
        
        report = QCReport(
            timestamp=datetime.now().isoformat(),
            input_file=input_file,
            input_type=input_type,
            checks_passed=n_passed,
            checks_failed=n_failed,
            critical_failures=n_critical,
            overall_status=status,
            checks=[asdict(c) for c in self.checks],
            summary=self.summary
        )
        
        return report


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Preprocessing Quality Control")
    parser.add_argument('--input', type=str, required=True,
                       help='Input file path (CSV or NPY)')
    parser.add_argument('--type', type=str, default='production',
                       choices=['production', 'labeled', 'normalized'],
                       help='Data type: production (unlabeled CSV), labeled (CSV with activity), normalized (NPY)')
    parser.add_argument('--output-dir', type=str, default='reports/preprocess_qc',
                       help='Output directory for QC reports')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        # Try relative to project root
        input_path = PROJECT_ROOT / args.input
    
    if not input_path.exists():
        logger.error(f"❌ File not found: {args.input}")
        sys.exit(1)
    
    # Run QC
    qc = PreprocessQC()
    
    if args.type == 'normalized' or input_path.suffix == '.npy':
        report = qc.validate_normalized_npy(input_path)
    else:
        report = qc.validate_raw_csv(input_path, args.type)
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("📊 QC SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"  Status: {report.overall_status}")
    logger.info(f"  Checks passed: {report.checks_passed}")
    logger.info(f"  Checks failed: {report.checks_failed}")
    logger.info(f"  Critical failures: {report.critical_failures}")
    
    # Save report
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"qc_{timestamp}.json"
    
    with open(report_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    logger.info(f"\n💾 Report saved: {report_path}")
    
    # Exit code
    if report.overall_status == "FAIL":
        logger.error("\n❌ QC FAILED - Critical issues must be fixed before inference")
        sys.exit(1)
    elif report.overall_status == "WARN":
        logger.warning("\n⚠️ QC PASSED WITH WARNINGS - Review issues before proceeding")
        sys.exit(0)
    else:
        logger.info("\n✅ QC PASSED - Data ready for inference")
        sys.exit(0)


if __name__ == "__main__":
    main()

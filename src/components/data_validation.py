"""
Stage 2 - Data Validation.

This component validates the fused 50 Hz sensor CSV before Stage 3 transforms it
into model windows. It is intentionally small and explicit: one file, one stage,
one validation report.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from src.entity.config_entity import DataValidationConfig, PipelineConfig

logger = logging.getLogger(__name__)


MILLIG_TO_MS2 = 0.00980665
ACCEL_COLUMNS = ["Ax", "Ay", "Az"]
GYRO_COLUMNS = ["Gx", "Gy", "Gz"]
LABEL_COLUMNS = [
    "label",
    "activity",
    "activity_label",
    "class",
    "target",
    "y",
]


@dataclass
class ValidationResult:
    """Internal validation result used before building the stage artifact."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class DataValidation:
    """Validate fused IMU data before model preprocessing."""

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        config: DataValidationConfig,
        ingestion_artifact: DataIngestionArtifact,
    ):
        """
        Method Name :   __init__
        Description :   Stores pipeline config, validation thresholds, and Stage 1 artifact.

        Output      :   Initialized DataValidation component.
        On Failure  :   Raises the original exception.
        """
        self.pipeline_config = pipeline_config
        self.config = config
        self.ingestion_artifact = ingestion_artifact

    def initiate_data_validation(self) -> DataValidationArtifact:
        """
        Method Name :   initiate_data_validation
        Description :   Runs all Stage 2 checks on the fused CSV from Stage 1.

        Output      :   DataValidationArtifact with status, errors, warnings, and stats.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            logger.info("=" * 60)
            logger.info("STAGE 2 - Data Validation")
            logger.info("=" * 60)

            csv_path = Path(self.ingestion_artifact.fused_csv_path)
            logger.info("Validating fused CSV: %s", csv_path)

            df = self._read_data(csv_path)
            result = self._validate_dataframe(df, csv_path)

            logger.info(
                "Validation result: valid=%s errors=%d warnings=%d",
                result.is_valid,
                len(result.errors),
                len(result.warnings),
            )
            for warning in result.warnings:
                logger.warning("Validation warning: %s", warning)
            for error in result.errors:
                logger.error("Validation error: %s", error)

            return self._build_artifact(result)
        except Exception as exc:
            logger.exception("Stage 2 data validation failed: %s", exc)
            raise

    def _read_data(self, csv_path: Path) -> pd.DataFrame:
        """
        Method Name :   _read_data
        Description :   Reads the fused CSV file from disk and verifies it exists.

        Output      :   Pandas DataFrame loaded from the fused CSV.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            if not csv_path.exists():
                raise FileNotFoundError(f"Fused CSV does not exist: {csv_path}")
            if not csv_path.is_file():
                raise ValueError(f"Fused CSV path is not a file: {csv_path}")
            return pd.read_csv(csv_path)
        except Exception:
            logger.exception("Could not read validation CSV: %s", csv_path)
            raise

    def _validate_dataframe(self, df: pd.DataFrame, csv_path: Path) -> ValidationResult:
        """
        Method Name :   _validate_dataframe
        Description :   Coordinates schema, timestamp, range, and unit checks.

        Output      :   ValidationResult with all findings.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            errors: List[str] = []
            warnings: List[str] = []
            stats: Dict[str, Any] = {
                "input_csv_path": str(csv_path),
                "n_rows": int(len(df)),
                "n_columns": int(len(df.columns)),
                "columns": list(df.columns),
                "expected_sensor_columns": list(self.config.sensor_columns),
                "expected_frequency_hz": float(self.config.expected_frequency_hz),
                "sampling_rate_tolerance": float(self.config.sampling_rate_tolerance),
                "max_missing_ratio": float(self.config.max_missing_ratio),
                "max_acceleration_ms2": float(self.config.max_acceleration_ms2),
                "max_gyroscope_dps": float(self.config.max_gyroscope_dps),
            }

            if df.empty:
                errors.append("Fused CSV is empty.")
                return ValidationResult(False, errors, warnings, stats)

            label_column = self._detect_label_column(df)
            stats["label_column"] = label_column
            stats["has_labels"] = bool(label_column)

            self._validate_required_columns(df, errors)
            self._validate_numeric_sensor_columns(df, errors, warnings)
            self._validate_missing_values(df, errors, warnings, stats)
            self._compute_sensor_stats(df, stats)

            timestamp_col = self._detect_timestamp_column(df)
            stats["timestamp_column"] = timestamp_col
            if timestamp_col is None:
                errors.append(
                    "No usable timestamp column found. Expected one of: "
                    f"{self.config.timestamp_columns}"
                )
            else:
                self._validate_timestamps(df, timestamp_col, errors, warnings, stats)
                self._validate_sampling_frequency(df, timestamp_col, warnings, stats)

            accel_unit = self._detect_acceleration_unit(df, stats)
            stats["acceleration_unit_detected"] = accel_unit
            self._validate_sensor_ranges(df, accel_unit, errors, warnings, stats)

            return ValidationResult(len(errors) == 0, errors, warnings, stats)
        except Exception:
            logger.exception("DataFrame validation failed")
            raise

    def _validate_required_columns(self, df: pd.DataFrame, errors: List[str]) -> None:
        """
        Method Name :   _validate_required_columns
        Description :   Confirms all required IMU channels are present.

        Output      :   Updates the errors list in-place.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            missing = [col for col in self.config.sensor_columns if col not in df.columns]
            if missing:
                errors.append(f"Missing required sensor columns: {missing}")
        except Exception:
            logger.exception("Required-column validation failed")
            raise

    def _validate_numeric_sensor_columns(
        self,
        df: pd.DataFrame,
        errors: List[str],
        warnings: List[str],
    ) -> None:
        """
        Method Name :   _validate_numeric_sensor_columns
        Description :   Ensures sensor channels are numeric or safely coercible to numeric.

        Output      :   Updates DataFrame columns plus errors/warnings in-place.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            for col in self.config.sensor_columns:
                if col not in df.columns:
                    continue
                if pd.api.types.is_numeric_dtype(df[col]):
                    continue

                coerced = pd.to_numeric(df[col], errors="coerce")
                newly_missing = coerced.isna() & df[col].notna()
                if newly_missing.any():
                    errors.append(
                        f"Column '{col}' is not numeric; "
                        f"{int(newly_missing.sum())} values could not be parsed."
                    )
                else:
                    warnings.append(f"Column '{col}' was stored as text but parsed as numeric.")
                    df[col] = coerced
        except Exception:
            logger.exception("Numeric sensor-column validation failed")
            raise

    def _validate_missing_values(
        self,
        df: pd.DataFrame,
        errors: List[str],
        warnings: List[str],
        stats: Dict[str, Any],
    ) -> None:
        """
        Method Name :   _validate_missing_values
        Description :   Checks missing-value ratios for every sensor channel.

        Output      :   Updates errors, warnings, and stats in-place.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            row_count = max(len(df), 1)
            total_missing = 0
            checked_cells = 0
            for col in self.config.sensor_columns:
                if col not in df.columns:
                    continue
                missing_count = int(df[col].isna().sum())
                missing_ratio = missing_count / row_count
                total_missing += missing_count
                checked_cells += row_count
                stats[f"{col}_missing_count"] = missing_count
                stats[f"{col}_missing_ratio"] = float(missing_ratio)

                if missing_ratio > self.config.max_missing_ratio:
                    errors.append(
                        f"Column '{col}' has {missing_ratio:.2%} missing values "
                        f"(max allowed: {self.config.max_missing_ratio:.2%})."
                    )
                elif missing_count > 0:
                    warnings.append(f"Column '{col}' has {missing_ratio:.2%} missing values.")

            stats["sensor_missing_count_total"] = int(total_missing)
            stats["sensor_missing_ratio_total"] = (
                float(total_missing / checked_cells) if checked_cells else 0.0
            )
        except Exception:
            logger.exception("Missing-value validation failed")
            raise

    def _detect_timestamp_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Method Name :   _detect_timestamp_column
        Description :   Chooses the first configured timestamp column present in the CSV.

        Output      :   Timestamp column name or None.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            for col in self.config.timestamp_columns:
                if col in df.columns:
                    return col
            return None
        except Exception:
            logger.exception("Timestamp-column detection failed")
            raise

    def _parse_timestamps(self, df: pd.DataFrame, timestamp_col: str) -> pd.Series:
        """
        Method Name :   _parse_timestamps
        Description :   Parses ISO or numeric timestamp columns into pandas datetimes.

        Output      :   Pandas Series of parsed timestamps.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            values = df[timestamp_col]
            if pd.api.types.is_numeric_dtype(values):
                numeric = pd.to_numeric(values, errors="coerce")
                median_value = float(numeric.dropna().median()) if numeric.notna().any() else 0.0
                col_name = timestamp_col.lower()
                unit = "ms" if "ms" in col_name or abs(median_value) > 1e10 else "s"
                return pd.to_datetime(numeric, unit=unit, errors="coerce")
            return pd.to_datetime(values, errors="coerce")
        except Exception:
            logger.exception("Timestamp parsing failed for column: %s", timestamp_col)
            raise

    def _validate_timestamps(
        self,
        df: pd.DataFrame,
        timestamp_col: str,
        errors: List[str],
        warnings: List[str],
        stats: Dict[str, Any],
    ) -> None:
        """
        Method Name :   _validate_timestamps
        Description :   Checks timestamp parseability, duplicates, monotonicity, and gaps.

        Output      :   Updates errors, warnings, and stats in-place.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            timestamps = self._parse_timestamps(df, timestamp_col)
            invalid_count = int(timestamps.isna().sum())
            duplicate_count = int(timestamps.duplicated().sum())
            row_count = max(len(df), 1)

            stats["timestamp_invalid_count"] = invalid_count
            stats["timestamp_invalid_ratio"] = float(invalid_count / row_count)
            stats["duplicate_timestamp_count"] = duplicate_count
            stats["duplicate_timestamp_ratio"] = float(duplicate_count / row_count)

            if invalid_count == len(df):
                errors.append(f"Timestamp column '{timestamp_col}' could not be parsed.")
                return
            if invalid_count / row_count > self.config.max_missing_ratio:
                errors.append(
                    f"Timestamp column '{timestamp_col}' has "
                    f"{invalid_count / row_count:.2%} invalid values "
                    f"(max allowed: {self.config.max_missing_ratio:.2%})."
                )
            elif invalid_count > 0:
                warnings.append(
                    f"Timestamp column '{timestamp_col}' has {invalid_count} invalid values."
                )

            if duplicate_count > 0:
                errors.append(
                    f"Timestamp column '{timestamp_col}' has {duplicate_count} duplicate values."
                )

            diffs = timestamps.dropna().diff().dropna().dt.total_seconds()
            if diffs.empty:
                warnings.append("Not enough valid timestamps to check temporal stability.")
                return

            non_positive = int((diffs <= 0).sum())
            stats["non_positive_timestamp_gap_count"] = non_positive
            stats["timestamp_gap_seconds_mean"] = self._safe_float(diffs.mean())
            stats["timestamp_gap_seconds_median"] = self._safe_float(diffs.median())
            stats["timestamp_gap_seconds_min"] = self._safe_float(diffs.min())
            stats["timestamp_gap_seconds_max"] = self._safe_float(diffs.max())

            if non_positive > 0:
                errors.append(
                    f"Timestamp column '{timestamp_col}' is not strictly increasing "
                    f"({non_positive} non-positive gaps)."
                )

            expected_period = 1.0 / float(self.config.expected_frequency_hz)
            large_gap_count = int((diffs > expected_period * 2.5).sum())
            stats["large_timestamp_gap_count"] = large_gap_count
            if large_gap_count > 0:
                warnings.append(
                    f"Timestamp column '{timestamp_col}' has {large_gap_count} large gaps "
                    f"(> {expected_period * 2.5:.3f}s)."
                )
        except Exception:
            logger.exception("Timestamp validation failed")
            raise

    def _validate_sampling_frequency(
        self,
        df: pd.DataFrame,
        timestamp_col: str,
        warnings: List[str],
        stats: Dict[str, Any],
    ) -> None:
        """
        Method Name :   _validate_sampling_frequency
        Description :   Verifies the median timestamp gap is close to the expected Hz.

        Output      :   Updates warnings and stats in-place.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            timestamps = self._parse_timestamps(df, timestamp_col)
            diffs = timestamps.dropna().diff().dropna().dt.total_seconds()
            diffs = diffs[diffs > 0]
            if diffs.empty:
                warnings.append("Could not verify sampling frequency from timestamps.")
                return

            median_period = float(diffs.median())
            mean_period = float(diffs.mean())
            actual_frequency_hz = 1.0 / median_period if median_period > 0 else 0.0
            mean_frequency_hz = 1.0 / mean_period if mean_period > 0 else 0.0
            expected = float(self.config.expected_frequency_hz)
            deviation = abs(actual_frequency_hz - expected) / expected if expected else 0.0

            stats["actual_frequency_hz"] = float(actual_frequency_hz)
            stats["mean_frequency_hz"] = float(mean_frequency_hz)
            stats["sampling_frequency_deviation_ratio"] = float(deviation)

            if deviation > self.config.sampling_rate_tolerance:
                warnings.append(
                    f"Sampling frequency is {actual_frequency_hz:.2f} Hz "
                    f"(expected {expected:.2f} Hz, tolerance "
                    f"{self.config.sampling_rate_tolerance:.0%})."
                )
        except Exception:
            logger.exception("Sampling-frequency validation failed")
            raise

    def _detect_acceleration_unit(self, df: pd.DataFrame, stats: Dict[str, Any]) -> str:
        """
        Method Name :   _detect_acceleration_unit
        Description :   Detects whether accelerometer channels look like milliG or m/s2.

        Output      :   One of milliG, m/s2, ambiguous, or unknown.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            if not all(col in df.columns for col in ACCEL_COLUMNS):
                return "unknown"

            accel = df[ACCEL_COLUMNS].apply(pd.to_numeric, errors="coerce").dropna()
            if accel.empty:
                return "unknown"

            abs_max = float(accel.abs().max().max())
            magnitude = np.sqrt((accel.to_numpy(dtype=float) ** 2).sum(axis=1))
            median_magnitude = float(np.nanmedian(magnitude))
            max_magnitude = float(np.nanmax(magnitude))

            stats["accel_abs_max_for_unit_detection"] = abs_max
            stats["accel_magnitude_median_for_unit_detection"] = median_magnitude
            stats["accel_magnitude_max_for_unit_detection"] = max_magnitude

            if 6.0 <= median_magnitude <= 15.0 and abs_max <= 80.0:
                return "m/s2"
            if 500.0 <= median_magnitude <= 1500.0 or abs_max > 100.0:
                return "milliG"
            return "ambiguous"
        except Exception:
            logger.exception("Acceleration-unit detection failed")
            raise

    def _validate_sensor_ranges(
        self,
        df: pd.DataFrame,
        acceleration_unit: str,
        errors: List[str],
        warnings: List[str],
        stats: Dict[str, Any],
    ) -> None:
        """
        Method Name :   _validate_sensor_ranges
        Description :   Applies unit-aware accelerometer checks and deg/s gyro checks.

        Output      :   Updates errors, warnings, and stats in-place.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            accel_threshold_ms2 = float(self.config.max_acceleration_ms2)
            accel_threshold_millig = accel_threshold_ms2 / MILLIG_TO_MS2
            stats["max_acceleration_milliG_equivalent"] = float(accel_threshold_millig)

            for col in ACCEL_COLUMNS:
                if col not in df.columns:
                    continue
                col_max = self._safe_float(pd.to_numeric(df[col], errors="coerce").abs().max())
                stats[f"{col}_max_abs"] = col_max
                if col_max is None:
                    continue
                if acceleration_unit == "m/s2" and col_max > accel_threshold_ms2:
                    warnings.append(
                        f"Column '{col}' has extreme acceleration "
                        f"(max {col_max:.2f} m/s2, threshold {accel_threshold_ms2:.2f} m/s2)."
                    )
                elif acceleration_unit == "milliG" and col_max > accel_threshold_millig:
                    warnings.append(
                        f"Column '{col}' has extreme acceleration "
                        f"(max {col_max:.2f} milliG, threshold "
                        f"{accel_threshold_millig:.2f} milliG)."
                    )

            if acceleration_unit == "ambiguous":
                warnings.append(
                    "Accelerometer unit is ambiguous. Stage 3 must confirm whether "
                    "unit conversion should be applied."
                )
            elif acceleration_unit == "unknown":
                warnings.append("Accelerometer unit could not be detected.")

            self._check_gyro_clipping(df, errors, warnings, stats)
        except Exception:
            logger.exception("Sensor-range validation failed")
            raise

    def _check_gyro_clipping(
        self,
        df: pd.DataFrame,
        errors: List[str],
        warnings: List[str],
        stats: Dict[str, Any],
    ) -> None:
        """
        Method Name :   _check_gyro_clipping
        Description :   Checks each gyroscope channel for sensor FS ceiling violations.
                        Occasional spikes produce a warning; >10% clipped samples is an error.

        Output      :   Updates errors, warnings, and stats in-place.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            threshold = float(self.config.max_gyroscope_dps)
            for col in GYRO_COLUMNS:
                if col not in df.columns:
                    continue
                numeric_col = pd.to_numeric(df[col], errors="coerce")
                col_max = self._safe_float(numeric_col.abs().max())
                stats[f"{col}_max_abs"] = col_max
                if col_max is None or col_max <= threshold:
                    continue
                clipped = int((numeric_col.abs() > threshold).sum())
                clipped_ratio = clipped / max(len(df), 1)
                stats[f"{col}_clipped_count"] = clipped
                stats[f"{col}_clipped_ratio"] = float(clipped_ratio)
                if clipped_ratio > 0.10:
                    errors.append(
                        f"Column '{col}' has {clipped_ratio:.1%} of samples above "
                        f"{threshold:.0f} deg/s (sensor FS ceiling). "
                        f"Max={col_max:.2f} deg/s, {clipped} clipped rows. "
                        "Data is likely saturated — re-record with correct sensor range."
                    )
                else:
                    warnings.append(
                        f"Column '{col}' has occasional gyroscope spikes above "
                        f"{threshold:.0f} deg/s "
                        f"(max {col_max:.2f} deg/s, {clipped} samples = {clipped_ratio:.1%}). "
                        "Isolated spikes are tolerated; verify sensor FS range."
                    )
        except Exception:
            logger.exception("Gyro clipping check failed")
            raise

    def _compute_sensor_stats(self, df: pd.DataFrame, stats: Dict[str, Any]) -> None:
        """
        Method Name :   _compute_sensor_stats
        Description :   Computes per-channel min, max, mean, and standard deviation.

        Output      :   Updates stats in-place.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            for col in self.config.sensor_columns:
                if col not in df.columns:
                    continue
                values = pd.to_numeric(df[col], errors="coerce")
                stats[f"{col}_mean"] = self._safe_float(values.mean())
                stats[f"{col}_std"] = self._safe_float(values.std())
                stats[f"{col}_min"] = self._safe_float(values.min())
                stats[f"{col}_max"] = self._safe_float(values.max())
        except Exception:
            logger.exception("Sensor-stat calculation failed")
            raise

    def _detect_label_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Method Name :   _detect_label_column
        Description :   Detects whether the fused CSV carries an optional label column.

        Output      :   Label column name or None.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            lower_to_original = {str(col).lower(): col for col in df.columns}
            for candidate in LABEL_COLUMNS:
                if candidate in lower_to_original:
                    return str(lower_to_original[candidate])
            return None
        except Exception:
            logger.exception("Label-column detection failed")
            raise

    def _build_artifact(self, result: ValidationResult) -> DataValidationArtifact:
        """
        Method Name :   _build_artifact
        Description :   Converts the internal validation result into the pipeline artifact.

        Output      :   DataValidationArtifact.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            return DataValidationArtifact(
                is_valid=result.is_valid,
                errors=result.errors,
                warnings=result.warnings,
                stats=self._json_safe(result.stats),
            )
        except Exception:
            logger.exception("Could not build DataValidationArtifact")
            raise

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """
        Method Name :   _safe_float
        Description :   Converts numeric values to JSON-safe floats.

        Output      :   Float value or None for NaN/inf/unavailable values.
        On Failure  :   Returns None.
        """
        try:
            value = float(value)
            if np.isnan(value) or np.isinf(value):
                return None
            return value
        except Exception:
            return None

    @classmethod
    def _json_safe(cls, value: Any) -> Any:
        """
        Method Name :   _json_safe
        Description :   Recursively converts numpy/pandas objects into JSON-safe values.

        Output      :   JSON-serializable value.
        On Failure  :   Returns a string representation.
        """
        try:
            if isinstance(value, dict):
                return {str(k): cls._json_safe(v) for k, v in value.items()}
            if isinstance(value, list):
                return [cls._json_safe(v) for v in value]
            if isinstance(value, tuple):
                return [cls._json_safe(v) for v in value]
            if isinstance(value, (np.integer,)):
                return int(value)
            if isinstance(value, (np.floating,)):
                return cls._safe_float(value)
            if isinstance(value, pd.Timestamp):
                return value.isoformat()
            return value
        except Exception:
            return str(value)

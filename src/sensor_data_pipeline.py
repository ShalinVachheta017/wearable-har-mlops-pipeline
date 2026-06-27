"""
Docstring for sensor_data_pipeline
Purpose: Process RAW sensor data from Excel files (Garmin watch format)

Key Components:

ProcessingConfig: Configuration dataclass for processing parameters
LoggerSetup: Logging infrastructure with rotating file handler
SensorDataLoader: Load and validate Excel files with sensor data
Parse list columns (x, y, z stored as strings)
Normalize column names (vendor-specific → standardized)
Validate required columns exist
DataProcessor: Transform raw data to time series
Explode list columns to individual rows
Create precise timestamps (base_time + offset)
Handle native sampling rates (accelerometer ≠ gyroscope)
SensorFusion: Merge accelerometer + gyroscope data
Align timestamps with tolerance
Resample to target frequency (50Hz)
Interpolate missing values
MetadataTracker: Track data lineage and statistics
Input: Raw Excel files from Garmin watch
Output: sensor_fused_50Hz.csv (time-aligned, resampled sensor data)

Status: Used for initial raw data processing (not needed for preprocessed data)

"""

import argparse
import ast
import json
import logging
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml
from scipy.signal import butter, filtfilt

# ============================================================================
# CONFIGURATION CLASS
# ============================================================================


@dataclass
class ProcessingConfig:
    """Configuration for data processing pipeline."""

    target_hz: int = 50
    merge_tolerance_ms: int = 1
    log_max_bytes: int = 2_000_000
    log_backup_count: int = 3
    interpolation_limit: int = 2


# ============================================================================
# LOGGING INFRASTRUCTURE
# ============================================================================


class LoggerSetup:
    """Sets up logging to console and rotating file."""

    def __init__(self, log_dir: Path, logger_name: str = "preprocess"):
        self.log_dir = log_dir
        self.logger_name = logger_name
        self._setup_logging()

    def _setup_logging(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.INFO)

        for handler in list(self.logger.handlers):
            self.logger.removeHandler(handler)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        file_handler = RotatingFileHandler(
            self.log_dir / "pipeline.log",
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        return self.logger


# ============================================================================
# RAW FILE DISCOVERY
# ============================================================================


def find_latest_sensor_pair(raw_dir: Path) -> Tuple[Path, Path]:
    """Locate the newest matching accelerometer/gyroscope Excel pair in data/raw.

    Matching rule:
        - Look for filenames containing "accelerometer" and "gyroscope" (case-insensitive)
        - Prefer pairs that share the same prefix before the sensor keyword
        - If no exact prefix match is found, fall back to the newest accel + newest gyro

    Raises:
        FileNotFoundError: if either sensor type is missing.
    """
    accel_files = sorted(
        [p for p in raw_dir.glob("*accelerometer*.*") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    gyro_files = sorted(
        [p for p in raw_dir.glob("*gyroscope*.*") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not accel_files:
        raise FileNotFoundError(f"No accelerometer files found in {raw_dir}")
    if not gyro_files:
        raise FileNotFoundError(f"No gyroscope files found in {raw_dir}")

    # Try to pair by prefix (portion before the word 'accelerometer')
    for accel in accel_files:
        prefix = accel.name.split("accelerometer")[0]
        candidates = [
            g
            for g in gyro_files
            if g.name.startswith(prefix) and "gyroscope" in g.name.lower()
        ]
        if candidates:
            gyro = candidates[0]  # candidates are already time-sorted
            return accel, gyro

    # Fallback: newest accel with newest gyro
    return accel_files[0], gyro_files[0]


# ============================================================================
# DATA LOADING AND VALIDATION
# ============================================================================


class SensorDataLoader:
    """Loads, parses, and validates sensor data from Excel files."""

    # Required columns that must be present in input files
    # These are essential for timestamp creation and sensor alignment
    REQUIRED_COLUMNS = [
        "timestamp",
        "timestamp_ms",
        "sample_time_offset",
        "x",
        "y",
        "z",
    ]

    # Column name mappings to standardize across sensor types
    # Garmin uses verbose names, we simplify to x/y/z for processing
    ACCEL_RENAME_MAP = {
        "calibrated_accel_x": "x",
        "calibrated_accel_y": "y",
        "calibrated_accel_z": "z",
    }
    GYRO_RENAME_MAP = {
        "calibrated_gyro_x": "x",
        "calibrated_gyro_y": "y",
        "calibrated_gyro_z": "z",
    }

    def __init__(self, logger: logging.Logger):
        """
        Initialize data loader with logger.

        Args:
            logger: Configured logger instance for operation tracking
        """
        self.logger = logger

    def load_sensor_data(self, file_path: Path) -> pd.DataFrame:
        """
        Load sensor data from Excel file with error handling.

        Args:
            file_path: Path to Excel file containing sensor data

        Returns:
            pd.DataFrame: Raw sensor data as pandas DataFrame

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
            Exception: For other loading errors (propagated with context)

        Note:
            Uses openpyxl engine for .xlsx files (default in pandas)
        """
        try:
            data = pd.read_excel(file_path)
            self.logger.info(
                "Loaded %s: %d rows, %d cols",
                file_path.name,
                data.shape[0],
                data.shape[1],
            )
            return data
        except Exception as e:
            self.logger.error(f"Failed to load {file_path}: {e}")
            raise  # Re-raise with original traceback for debugging

    def normalize_column_names(
        self, df: pd.DataFrame, sensor_type: str
    ) -> pd.DataFrame:
        """
        Standardize column names based on sensor type.

        Args:
            df: Raw dataframe with vendor-specific column names
            sensor_type: Either "accelerometer" or "gyroscope"

        Returns:
            pd.DataFrame: DataFrame with standardized column names (x, y, z)

        Raises:
            ValueError: If sensor_type is not recognized

        Design Rationale:
            Standardizing column names allows the rest of the pipeline to be
            sensor-agnostic. We can process any sensor with x/y/z axes uniformly.
        """
        if sensor_type.lower() == "accelerometer":
            rename_map = self.ACCEL_RENAME_MAP
        elif sensor_type.lower() == "gyroscope":
            rename_map = self.GYRO_RENAME_MAP
        else:
            raise ValueError(f"Unknown sensor type: {sensor_type}")

        return df.rename(columns=rename_map)

    def validate_columns(self, df: pd.DataFrame, sensor_type: str) -> None:
        """
        Validate that all required columns are present.

        Args:
            df: DataFrame to validate
            sensor_type: Sensor type for error messaging

        Raises:
            ValueError: If any required columns are missing

        Design Pattern:
            Fail-fast validation. Better to catch schema errors early than
            experience cryptic errors deep in the pipeline.
        """
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns in {sensor_type}: {missing_cols}")

    def parse_list_cell(self, value) -> List:
        """
        Parse Excel cell containing array-like data into Python list.

        Handles multiple formats:
            1. Already a list/tuple/array → return as list
            2. JSON format: "[1.2, 3.4, 5.6]" → parse with json.loads()
            3. Python literal: "[1.2, 3.4, 5.6]" → parse with ast.literal_eval()
            4. Comma-separated: "1.2, 3.4, 5.6" or "1.2,3.4,5.6" → split and convert
            5. Empty/null → return empty list

        Args:
            value: Cell value (can be str, list, tuple, ndarray, or NaN)

        Returns:
            List: Parsed values as Python list (numeric when possible)

        Example:
            >>> loader.parse_list_cell("[1.2, 3.4, 5.6]")
            [1.2, 3.4, 5.6]
            >>> loader.parse_list_cell("1.2, 3.4, 5.6")
            [1.2, 3.4, 5.6]
            >>> loader.parse_list_cell("[1,2,3]")
            [1, 2, 3]

        Design Pattern:
            Progressive fallback - try most structured format first (JSON),
            then less structured (literal eval), finally least structured (CSV).
        """
        # Case 1: Already a Python collection
        if isinstance(value, (list, tuple, np.ndarray)):
            return list(value)

        # Case 2: Missing/null value
        if pd.isna(value):
            return []

        # Convert to string for parsing
        str_value = str(value).strip()

        # Case 3: Try JSON parsing (most reliable for well-formatted data)
        try:
            return json.loads(str_value)
        except (json.JSONDecodeError, ValueError):
            pass  # Not JSON, try next method

        # Case 4: Try Python literal evaluation (handles Python syntax)
        try:
            parsed_value = ast.literal_eval(str_value)
            if isinstance(parsed_value, (list, tuple, np.ndarray)):
                return list(parsed_value)
        except (ValueError, SyntaxError):
            pass  # Not a Python literal, try next method

        # Case 5: Fallback to comma-separated parsing
        # Remove brackets if present: "[1,2,3]" → "1,2,3"
        str_value = str_value.strip("[]")
        if not str_value:
            return []

        # Split by comma and convert to numeric (NaN if conversion fails)
        return [pd.to_numeric(x, errors="coerce") for x in str_value.split(",")]

    def parse_list_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply list parsing to all array-like columns in dataframe.

        Columns parsed:
            - sample_time_offset: Time offsets in milliseconds
            - x, y, z: Sensor measurements (3-axis data)

        Args:
            df: DataFrame with list-like string columns

        Returns:
            pd.DataFrame: DataFrame with actual Python lists in cells

        Note:
            This is a critical step - converts strings to lists for explosion
        """
        list_columns = ["sample_time_offset", "x", "y", "z"]
        for col in list_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.parse_list_cell)
        return df

    def validate_row_lengths(self, row) -> bool:
        """
        Check if all list columns in a row have matching lengths.

        Args:
            row: DataFrame row (pandas Series)

        Returns:
            bool: True if all lists have same length, False otherwise

        Rationale:
            Each row should have n samples. If sample_time_offset has 10 values
            but x has 12 values, the data is corrupted and should be excluded.
        """
        n = len(row["sample_time_offset"])
        return n == len(row["x"]) == len(row["y"]) == len(row["z"])

    def filter_valid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove rows where list columns have mismatched lengths.

        Args:
            df: DataFrame with parsed list columns

        Returns:
            pd.DataFrame: Filtered DataFrame with only valid rows

        Quality Metric:
            Logs the number of rows filtered vs. total rows
            (Success rate typically >99% for clean Garmin data)
        """
        valid_mask = df.apply(self.validate_row_lengths, axis=1)
        filtered_df = df.loc[valid_mask].reset_index(drop=True)
        self.logger.info(
            f"Filtered to {len(filtered_df)} valid rows from {len(df)} total rows"
        )
        return filtered_df


# ============================================================================
# DATA TRANSFORMATION
# ============================================================================


class DataProcessor:
    """Transforms and explodes sensor data, creates timestamps."""

    def __init__(self, logger: logging.Logger):
        """Initialize data processor with logger."""
        self.logger = logger

    def explode_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Explode list columns to create individual rows for each sample.

        Transformation:
            Before (1 row):
            | timestamp | x        | y        | z        |
            | 10:00:00  | [1,2,3]  | [4,5,6]  | [7,8,9]  |

            After (3 rows):
            | timestamp | x  | y  | z  |
            | 10:00:00  | 1  | 4  | 7  |
            | 10:00:00  | 2  | 5  | 8  |
            | 10:00:00  | 3  | 6  | 9  |

        Args:
            df: DataFrame with list columns

        Returns:
            pd.DataFrame: Exploded DataFrame with one sample per row

        Performance:
            Typical explosion: 14,536 rows → 363,400 rows (~25x increase)
        """
        list_columns = ["sample_time_offset", "x", "y", "z"]
        exploded_df = df.explode(list_columns, ignore_index=True).copy()
        self.logger.info(f"Exploded to {len(exploded_df)} individual samples")
        return exploded_df

    def create_base_time(self, df: pd.DataFrame) -> pd.Series:
        """
        Create base timestamp from timestamp and timestamp_ms columns.

        Args:
            df: DataFrame with timestamp and timestamp_ms columns

        Returns:
            pd.Series: Base timestamps with millisecond precision

        Implementation:
            1. Parse timestamp string to datetime (UTC timezone)
            2. Convert timestamp_ms to timedelta
            3. Add timedelta to datetime

        Note:
            UTC timezone ensures consistent handling across time zones
        """
        base_time = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        ms_offset = pd.to_timedelta(
            pd.to_numeric(df["timestamp_ms"], errors="coerce")
            .fillna(0)
            .astype("int64"),
            unit="ms",
        )
        return base_time + ms_offset

    def create_true_time(self, df: pd.DataFrame) -> pd.Series:
        """
        Create final timestamp by adding sample_time_offset to base_time.

        Args:
            df: DataFrame with timestamp, timestamp_ms, and sample_time_offset

        Returns:
            pd.Series: Final precise timestamps for each sample

        Precision:
            Achieves millisecond-level accuracy critical for sensor fusion
        """
        sample_offset = pd.to_timedelta(
            pd.to_numeric(df["sample_time_offset"], errors="coerce")
            .fillna(0)
            .astype("int64"),
            unit="ms",
        )
        return self.create_base_time(df) + sample_offset

    def process_sensor_data(self, df: pd.DataFrame, sensor_type: str) -> pd.DataFrame:
        """
        Complete processing pipeline for a single sensor.

        Steps:
            1. Create base_time and true_time timestamps
            2. Rename sensor columns (x/y/z → Ax/Ay/Az or Gx/Gy/Gz)
            3. Convert sensor values to numeric (handle any string remnants)
            4. Remove rows with invalid timestamps
            5. Sort chronologically

        Args:
            df: Exploded DataFrame with timestamp columns
            sensor_type: "accelerometer" or "gyroscope"

        Returns:
            pd.DataFrame: Processed sensor data ready for fusion

        Output Columns:
            Accelerometer: base_time, true_time, Ax, Ay, Az
            Gyroscope: base_time, true_time, Gx, Gy, Gz
        """
        # Create timestamp columns
        df["base_time"] = self.create_base_time(df)
        df["true_time"] = self.create_true_time(df)

        # Rename sensor columns based on sensor type
        if sensor_type.lower() == "accelerometer":
            column_mapping = {"x": "Ax", "y": "Ay", "z": "Az"}
        elif sensor_type.lower() == "gyroscope":
            column_mapping = {"x": "Gx", "y": "Gy", "z": "Gz"}
        else:
            raise ValueError(f"Unknown sensor type: {sensor_type}")

        # Select relevant columns and apply renaming
        processed_df = df[["base_time", "true_time", "x", "y", "z"]].rename(
            columns=column_mapping
        )

        # Ensure sensor columns are numeric (convert any remaining strings)
        sensor_columns = list(column_mapping.values())
        for col in sensor_columns:
            processed_df[col] = pd.to_numeric(processed_df[col], errors="coerce")

        # Remove rows with invalid timestamps (NaT) and sort chronologically
        processed_df = (
            processed_df.dropna(subset=["true_time"])
            .sort_values("true_time")
            .reset_index(drop=True)
        )

        self.logger.info(f"Processed {sensor_type}: {processed_df.shape}")
        return processed_df


# ============================================================================
# SENSOR FUSION (ALIGNMENT)
# ============================================================================


class SensorFusion:
    """Aligns and merges accelerometer and gyroscope data by timestamp."""

    def __init__(self, config: ProcessingConfig, logger: logging.Logger):
        """Initialize sensor fusion with config and logger."""
        self.config = config
        self.logger = logger

    def merge_sensor_data(
        self, accel_df: pd.DataFrame, gyro_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge accelerometer and gyroscope data based on timestamp alignment.

        Algorithm:
            1. For each accelerometer timestamp, find nearest gyroscope timestamp
            2. Accept match only if time difference ≤ tolerance (1ms)
            3. Keep only samples with complete sensor data (6 channels)

        Args:
            accel_df: Processed accelerometer data (true_time, Ax, Ay, Az)
            gyro_df: Processed gyroscope data (true_time, Gx, Gy, Gz)

        Returns:
            pd.DataFrame: Merged data with all 6 sensor channels
            Index: true_time (timestamp)
            Columns: base_time, Ax, Ay, Az, Gx, Gy, Gz

        Quality Assurance:
            Calls _analyze_merge_quality() to log alignment statistics
        """
        tolerance = pd.Timedelta(milliseconds=self.config.merge_tolerance_ms)

        # Prepare gyro data for merging
        # Drop base_time to avoid column suffix (_x, _y) after merge
        # Rename true_time to gyro_time to track alignment quality
        gyro_for_merge = gyro_df.drop(columns=["base_time"]).rename(
            columns={"true_time": "gyro_time"}
        )

        # Perform time-based merge
        # Direction="nearest": Find closest gyro time (before or after)
        # Tolerance: Maximum allowed time difference
        merged_df = pd.merge_asof(
            accel_df.sort_values("true_time"),  # Left: accelerometer (primary timeline)
            gyro_for_merge.sort_values(
                "gyro_time"
            ),  # Right: gyroscope (aligned to accel)
            left_on="true_time",
            right_on="gyro_time",
            direction="nearest",
            tolerance=tolerance,
        )

        # Analyze and log merge quality metrics
        self._analyze_merge_quality(merged_df)

        # Filter to rows with complete gyro data (all 3 channels non-null)
        # Rows with NaN in Gx/Gy/Gz had no matching gyro sample within tolerance
        has_gyro = merged_df[["Gx", "Gy", "Gz"]].notna().all(axis=1)
        complete_df = merged_df.loc[
            has_gyro, ["true_time", "base_time", "Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
        ]
        complete_df = complete_df.reset_index(drop=True)

        # Set true_time as index (chronological ordering)
        complete_df = complete_df.set_index("true_time").sort_index()
        complete_df.index.name = "true_time"

        self.logger.info(f"Merged data shape: {complete_df.shape}")
        return complete_df

    def _analyze_merge_quality(self, merged_df: pd.DataFrame):
        """
        Analyze and log the quality of sensor data alignment.

        Metrics:
            - Match rate: Percentage of accelerometer samples matched to gyroscope
            - Time lag statistics: Mean, standard deviation, max absolute difference

        Args:
            merged_df: DataFrame after merge_asof (includes gyro_time column)

        Interpretation:
            - High match rate (>90%): Good temporal alignment
            - Low mean lag (<1ms): Minimal time shift between sensors
            - Low std lag (<1ms): Consistent timing across session
            - Max lag ≤ tolerance: All matches within acceptable range

        Example Output:
            "Matched within 1 ms: 95.1% | lag_ms mean=-0.466 std=0.499 max_abs=1.000"
        """
        has_gyro = merged_df[["Gx", "Gy", "Gz"]].notna().all(axis=1)

        if has_gyro.any():
            # Calculate time lag in milliseconds
            # Negative lag: gyro timestamp before accel timestamp
            # Positive lag: gyro timestamp after accel timestamp
            lag_ms = (
                merged_df.loc[has_gyro, "true_time"].astype("int64")
                - merged_df.loc[has_gyro, "gyro_time"].astype("int64")
            ) / 1e6  # Convert nanoseconds to milliseconds

            self.logger.info(
                f"Matched within {self.config.merge_tolerance_ms} ms: "
                f"{has_gyro.mean()*100:.1f}% | "
                f"lag_ms mean={lag_ms.mean():.3f} std={lag_ms.std():.3f} max_abs={np.abs(lag_ms).max():.3f}"
            )
        else:
            # Warning: No successful matches (likely data quality issue)
            self.logger.warning(
                f"No matched samples within {self.config.merge_tolerance_ms} ms"
            )


# ============================================================================
# FREQUENCY RESAMPLING
# ============================================================================


class Resampler:
    """Resamples merged data to fixed frequency and adds timestamps."""

    # Columns containing actual sensor measurements
    # These are the only columns resampled (timestamps recalculated)
    SENSOR_COLUMNS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]

    def __init__(self, config: ProcessingConfig, logger: logging.Logger):
        """Initialize resampler with config and logger."""
        self.config = config
        self.logger = logger

    def resample_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample sensor data to exact target frequency.

        Process:
            1. Calculate resampling rule (e.g., "20ms" for 50Hz)
            2. Group data into time bins (every 20ms)
            3. Calculate mean of values within each bin
            4. Interpolate missing bins (up to interpolation_limit gaps)

        Args:
            df: Merged sensor data with true_time index

        Returns:
            pd.DataFrame: Resampled data at exact target frequency

        Example:
            target_hz=50 → rule="20ms" → samples every 20ms (exactly 50 per second)

        Performance:
            Typical resampling: 345,418 native samples → 181,699 @50Hz samples
        """
        # Calculate resampling rule from target frequency
        # 50Hz = 1000ms/50 = 20ms intervals
        # 100Hz = 1000ms/100 = 10ms intervals
        rule = f"{int(1000/self.config.target_hz)}ms"

        # Select only sensor columns for resampling
        # (Timestamps will be recalculated from index)
        sensor_cols = [col for col in self.SENSOR_COLUMNS if col in df.columns]
        sensor_data = df[sensor_cols]

        # Perform resampling with interpolation
        # .resample(rule): Group by time bins
        # .mean(): Aggregate multiple samples in same bin
        # .interpolate(): Fill missing bins with interpolated values
        resampled_data = (
            sensor_data.resample(rule)
            .mean()
            .interpolate(
                limit=self.config.interpolation_limit,  # Max consecutive gaps to fill
                limit_direction="both",  # Interpolate forward and backward
            )
        )

        self.logger.info(
            f"Resampled to {self.config.target_hz}Hz: {resampled_data.shape}"
        )
        return resampled_data

    def add_timestamp_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add standardized timestamp columns to resampled data.

        Creates two timestamp representations:
            1. timestamp_ms: Integer milliseconds since Unix epoch
               - Efficient for computation and storage
               - Used for time-based indexing in ML models

            2. timestamp_iso: ISO 8601 string format
               - Human-readable: "2025-03-23T15:23:10.500000Z"
               - Standardized format for data exchange
               - Sortable as strings

        Args:
            df: Resampled DataFrame with DatetimeIndex

        Returns:
            pd.DataFrame: DataFrame with timestamp columns added at front

        Note:
            Original index (true_time) is NOT preserved - converted to columns
        """
        # Convert index (datetime64[ns]) to nanoseconds since epoch
        idx_ns = df.index.astype("int64")

        # Convert nanoseconds to milliseconds (integer division)
        # 1 second = 1,000 milliseconds = 1,000,000 microseconds = 1,000,000,000 nanoseconds
        timestamp_ms = (idx_ns // 1_000_000).astype("int64")

        # Convert index to ISO 8601 string format with UTC timezone indicator
        # Format: YYYY-MM-DDTHH:MM:SS.ffffffZ
        timestamp_iso = df.index.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Create output dataframe with timestamp columns at front
        output_df = df.copy()
        output_df.insert(0, "timestamp_ms", timestamp_ms)
        output_df.insert(1, "timestamp_iso", timestamp_iso)

        return output_df


# ============================================================================
# GRAVITY REMOVAL PREPROCESSING
# ============================================================================


class GravityRemovalPreprocessor:
    """
    Removes gravity component from accelerometer data using high-pass filtering.

    This addresses domain shift when training data has gravity removed but
    production data still contains gravity. Uses a Butterworth high-pass filter
    following the approach from the UCI HAR dataset (Anguita et al., 2013).

    Theory:
        - Gravity is a constant (DC) component at ~9.81 m/s²
        - Human movement is dynamic (varying frequency)
        - High-pass filter removes low-frequency components (gravity)
        - Cutoff at 0.3 Hz captures gravity while preserving movement

    Example:
        >>> preprocessor = GravityRemovalPreprocessor(enable_gravity_removal=True)
        >>> df_processed = preprocessor.process_dataframe(df)
        >>> # Az mean will shift from ~-9.81 to ~0
    """

    ACCEL_COLUMNS = ["Ax", "Ay", "Az"]

    def __init__(
        self,
        enable_gravity_removal: bool = True,
        sampling_frequency: float = 50.0,
        cutoff_hz: float = 0.3,
        filter_order: int = 3,
        config_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize gravity removal preprocessor.

        Args:
            enable_gravity_removal: Toggle to enable/disable gravity removal.
                                    Set to False to skip processing (passthrough).
            sampling_frequency: Sampling rate of the data in Hz (default: 50 Hz)
            cutoff_hz: High-pass filter cutoff frequency in Hz (default: 0.3 Hz)
            filter_order: Butterworth filter order (default: 3)
            config_path: Optional path to YAML config file
            logger: Optional logger instance
        """
        # Load from config if provided
        if config_path and config_path.exists():
            self._load_config(config_path)
        else:
            self.enable_gravity_removal = enable_gravity_removal
            self.sampling_frequency = sampling_frequency
            self.cutoff_hz = cutoff_hz
            self.filter_order = filter_order

        self.logger = logger or logging.getLogger(__name__)

        # Pre-compute filter coefficients if enabled (for efficiency)
        if self.enable_gravity_removal:
            self._compute_filter_coefficients()

    def _load_config(self, config_path: Path) -> None:
        """Load settings from YAML config file."""
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        preprocessing = config.get("preprocessing", {})
        gravity_filter = preprocessing.get("gravity_filter", {})

        self.enable_gravity_removal = preprocessing.get("enable_gravity_removal", True)
        self.sampling_frequency = preprocessing.get("sampling_frequency_hz", 50.0)
        self.cutoff_hz = gravity_filter.get("cutoff_hz", 0.3)
        self.filter_order = gravity_filter.get("order", 3)

    def _compute_filter_coefficients(self) -> None:
        """
        Pre-compute Butterworth filter coefficients.

        Called once during initialization for efficiency.
        Uses Nyquist frequency for normalization as required by scipy.
        """
        # Nyquist frequency = half of sampling frequency
        nyquist = self.sampling_frequency / 2.0

        # Normalized cutoff (0 to 1 where 1 = Nyquist)
        normalized_cutoff = self.cutoff_hz / nyquist

        # Design high-pass Butterworth filter
        # btype='high': High-pass filter (removes frequencies below cutoff)
        self.b, self.a = butter(self.filter_order, normalized_cutoff, btype="high")

        self.logger.debug(
            f"Gravity filter initialized: cutoff={self.cutoff_hz}Hz, "
            f"order={self.filter_order}, fs={self.sampling_frequency}Hz"
        )

    def remove_gravity(self, acceleration_data: np.ndarray) -> np.ndarray:
        """
        Apply high-pass filter to remove gravity from acceleration data.

        Args:
            acceleration_data: Numpy array of shape (n_samples,) or (n_samples, 3)
                               Contains acceleration values in m/s²

        Returns:
            np.ndarray: Filtered data with gravity removed (body acceleration)

        Note:
            Uses filtfilt for zero-phase filtering (no time delay)
        """
        if not self.enable_gravity_removal:
            return acceleration_data

        # Handle 1D and 2D arrays
        if acceleration_data.ndim == 1:
            return filtfilt(self.b, self.a, acceleration_data)
        else:
            # Apply filter to each column (axis)
            return filtfilt(self.b, self.a, acceleration_data, axis=0)

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process DataFrame to remove gravity from accelerometer columns.

        Args:
            df: Input DataFrame with Ax, Ay, Az columns

        Returns:
            pd.DataFrame: DataFrame with gravity removed from accelerometer columns.
                          Gyroscope columns (Gx, Gy, Gz) are unchanged.

        Example:
            >>> df['Az'].mean()  # Before: -9.83
            >>> df_processed = preprocessor.process_dataframe(df)
            >>> df_processed['Az'].mean()  # After: ~0.0
        """
        if not self.enable_gravity_removal:
            self.logger.info("Gravity removal disabled - returning data unchanged")
            return df

        self.logger.info("Applying gravity removal to accelerometer data...")

        # Create copy to avoid modifying original
        df_processed = df.copy()

        # Track statistics for logging
        stats_before = {}
        stats_after = {}

        # Apply gravity removal to each accelerometer column
        for col in self.ACCEL_COLUMNS:
            if col in df_processed.columns:
                # Store before stats
                stats_before[col] = df_processed[col].mean()

                # Apply filter
                df_processed[col] = self.remove_gravity(df_processed[col].values)

                # Store after stats
                stats_after[col] = df_processed[col].mean()

        # Log transformation results
        self.logger.info(
            "Gravity removal complete: "
            f"Az mean: {stats_before.get('Az', 0):.2f} → {stats_after.get('Az', 0):.2f} m/s²"
        )

        return df_processed


def load_pipeline_config(config_path: Path) -> dict:
    """
    Load pipeline configuration from YAML file.

    Args:
        config_path: Path to pipeline_config.yaml

    Returns:
        Dictionary with configuration values
    """
    if not config_path.exists():
        logging.warning(f"Config file not found: {config_path}, using defaults")
        return {}

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ============================================================================
# DATA EXPORT
# ============================================================================


class DataExporter:
    """Saves processed data and metadata to disk."""

    def __init__(self, output_dir: Path, logger: logging.Logger):
        """
        Initialize data exporter.

        Args:
            output_dir: Directory for output files (created if doesn't exist)
            logger: Logger instance
        """
        self.output_dir = output_dir
        self.logger = logger
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_processed_data(
        self,
        native_df: pd.DataFrame,
        resampled_df: pd.DataFrame,
        config: ProcessingConfig,
        input_files: Dict[str, str],
    ) -> None:
        """
        Save all processed data and metadata.

        Args:
            native_df: Merged data at native sampling rate
            resampled_df: Resampled data at target frequency
            config: Processing configuration used
            input_files: Dictionary mapping sensor types to file paths

        Files Created:
            - sensor_merged_native_rate.csv (~50MB for typical session)
            - sensor_fused_{target_hz}Hz.csv (~25MB for 50Hz)
            - sensor_fused_meta.json (~1KB)

        Note:
            CSV format chosen for:
            - Human readability (can inspect in Excel/text editor)
            - Wide compatibility (works with any ML framework)
            - Git-friendly (text-based, can track changes)

            Future: Consider Parquet for larger datasets (10x compression, faster loading)
        """
        # Save native rate data (with index containing true_time)
        native_path = self.output_dir / "sensor_merged_native_rate.csv"
        native_df.to_csv(native_path)

        # Save resampled data (no index, timestamps are columns)
        resampled_path = self.output_dir / f"sensor_fused_{config.target_hz}Hz.csv"
        resampled_df.to_csv(resampled_path, index=False)

        # Create metadata for reproducibility and lineage tracking
        metadata = {
            "config": {
                "accel_file": input_files.get("accelerometer", ""),
                "gyro_file": input_files.get("gyroscope", ""),
                "target_hz": config.target_hz,
                "tolerance_ms": config.merge_tolerance_ms,
            },
            "rows": {
                "native": int(len(native_df)),
                "resampled": int(len(resampled_df)),
            },
        }

        # Save metadata as JSON (indent=2 for readability)
        metadata_path = self.output_dir / "sensor_fused_meta.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Log successful completion
        self.logger.info(f"Data saved to: {self.output_dir}")
        self.logger.info(
            f"Files created: {native_path.name}, {resampled_path.name}, {metadata_path.name}"
        )


# ============================================================================
# MAIN PIPELINE ORCHESTRATOR
# ============================================================================


class SensorDataPipeline:
    """Main orchestrator: runs the full preprocessing pipeline."""

    def __init__(self, base_dir: Path, config: Optional[ProcessingConfig] = None):
        """
        Initialize pipeline with all components.

        Args:
            base_dir: Project root directory (contains data/, logs/, etc.)
            config: Processing configuration (uses defaults if None)

        Setup Process:
            1. Store configuration (create default if not provided)
            2. Setup logging (creates logs/preprocessing/ directory)
            3. Initialize all processing components
            4. Load pipeline config from YAML
            5. Create output directories
        """
        self.base_dir = base_dir
        self.config = (
            config or ProcessingConfig()
        )  # Use default config if none provided

        # Setup centralized logging
        log_dir = base_dir / "logs" / "preprocessing"
        self.logger_setup = LoggerSetup(log_dir)
        self.logger = self.logger_setup.get_logger()

        # Load pipeline configuration from YAML
        self.config_path = base_dir / "config" / "pipeline_config.yaml"
        self.pipeline_config = load_pipeline_config(self.config_path)

        # Initialize all processing components (dependency injection pattern)
        self.data_loader = SensorDataLoader(self.logger)
        self.data_processor = DataProcessor(self.logger)
        self.sensor_fusion = SensorFusion(self.config, self.logger)
        self.resampler = Resampler(self.config, self.logger)

        # Initialize gravity removal preprocessor (config-controlled)
        self.gravity_preprocessor = GravityRemovalPreprocessor(
            config_path=self.config_path if self.config_path.exists() else None,
            logger=self.logger,
        )

        # Setup output directory and exporter (under data/preprocessed)
        self.output_dir = base_dir / "data" / "preprocessed"
        self.data_exporter = DataExporter(self.output_dir, self.logger)

        # Create log directories for future pipeline stages
        # (Anticipating training and evaluation stages)
        (base_dir / "logs" / "training").mkdir(parents=True, exist_ok=True)
        (base_dir / "logs" / "evaluation").mkdir(parents=True, exist_ok=True)

    def process_sensor_files(self, accel_path: Path, gyro_path: Path) -> None:
        """
        Process accelerometer and gyroscope files through complete pipeline.

        Complete Pipeline (11 steps):
            Step 1:  Load raw Excel files
            Step 2:  Normalize column names
            Step 3:  Validate required columns
            Step 4:  Parse list-like columns
            Step 5:  Filter valid rows
            Step 6:  Explode to individual samples
            Step 7:  Process sensor data (timestamps, data types)
            Step 8:  Merge sensors by timestamp alignment
            Step 9:  Resample to target frequency
            Step 10: Apply gravity removal (if enabled in config)
            Step 11: Export results with metadata

        Args:
            accel_path: Path to accelerometer Excel file
            gyro_path: Path to gyroscope Excel file

        Raises:
            FileNotFoundError: If input files don't exist
            ValueError: If data format is invalid
            Exception: For other processing errors

        Side Effects:
            - Creates logs/preprocessing/pipeline.log
            - Creates pre_processed_data/*.csv files
            - Creates pre_processed_data/*.json metadata

        Performance:
            Typical processing time: 8-10 seconds for 14K rows
        """
        try:
            self.logger.info("Starting sensor data preprocessing pipeline")

            # ================================================================
            # STEP 1-2: LOAD AND NORMALIZE
            # ================================================================
            accel_raw = self.data_loader.load_sensor_data(accel_path)
            gyro_raw = self.data_loader.load_sensor_data(gyro_path)

            accel_raw = self.data_loader.normalize_column_names(
                accel_raw, "accelerometer"
            )
            gyro_raw = self.data_loader.normalize_column_names(gyro_raw, "gyroscope")

            # ================================================================
            # STEP 3-5: VALIDATE, PARSE, FILTER
            # ================================================================
            self.data_loader.validate_columns(accel_raw, "accelerometer")
            self.data_loader.validate_columns(gyro_raw, "gyroscope")

            accel_raw = self.data_loader.parse_list_columns(accel_raw)
            gyro_raw = self.data_loader.parse_list_columns(gyro_raw)

            accel_raw = self.data_loader.filter_valid_rows(accel_raw)
            gyro_raw = self.data_loader.filter_valid_rows(gyro_raw)

            # ================================================================
            # STEP 6-7: EXPLODE AND PROCESS
            # ================================================================
            accel_exploded = self.data_processor.explode_dataframe(accel_raw)
            gyro_exploded = self.data_processor.explode_dataframe(gyro_raw)

            accel_processed = self.data_processor.process_sensor_data(
                accel_exploded, "accelerometer"
            )
            gyro_processed = self.data_processor.process_sensor_data(
                gyro_exploded, "gyroscope"
            )

            # ================================================================
            # STEP 8-9: MERGE AND RESAMPLE
            # ================================================================
            merged_data = self.sensor_fusion.merge_sensor_data(
                accel_processed, gyro_processed
            )

            resampled_data = self.resampler.resample_data(merged_data)
            resampled_data = self.resampler.add_timestamp_columns(resampled_data)

            # ================================================================
            # STEP 10: GRAVITY REMOVAL (if enabled in config)
            # ================================================================
            # Apply gravity removal to accelerometer data
            # Toggle controlled by config/pipeline_config.yaml
            resampled_data = self.gravity_preprocessor.process_dataframe(resampled_data)

            # ================================================================
            # STEP 11: EXPORT
            # ================================================================
            input_files = {
                "accelerometer": str(accel_path),
                "gyroscope": str(gyro_path),
            }
            self.data_exporter.save_processed_data(
                merged_data, resampled_data, self.config, input_files
            )

            self.logger.info("Pipeline completed successfully")

        except Exception as e:
            # Log error with full context and re-raise
            self.logger.error("Pipeline failed: %s", e)
            raise  # Preserve original traceback for debugging


# ============================================================================
# COMMAND-LINE ENTRY POINT
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Run sensor data preprocessing end-to-end"
    )
    parser.add_argument(
        "--accel", type=str, help="Path to accelerometer Excel file (optional)"
    )
    parser.add_argument(
        "--gyro", type=str, help="Path to gyroscope Excel file (optional)"
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    pipeline = SensorDataPipeline(base_dir)

    if args.accel and args.gyro:
        accel_path = Path(args.accel)
        gyro_path = Path(args.gyro)
        pipeline.logger.info(
            "Using provided sensor files: %s | %s", accel_path.name, gyro_path.name
        )
    else:
        raw_dir = base_dir / "data" / "raw"
        accel_path, gyro_path = find_latest_sensor_pair(raw_dir)
        pipeline.logger.info("Auto-selected latest raw pair from %s", raw_dir)
        pipeline.logger.info("  Accelerometer: %s", accel_path.name)
        pipeline.logger.info("  Gyroscope:     %s", gyro_path.name)

    pipeline.process_sensor_files(accel_path, gyro_path)


# ============================================================================
# SCRIPT EXECUTION
# ============================================================================

if __name__ == "__main__":
    main()

"""Stage 1 ingestion: selected input -> data/processed/fused_<dataset>_50Hz.csv."""

import ast
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.entity.artifact_entity import DataIngestionArtifact
from src.entity.config_entity import DataIngestionConfig, PipelineConfig
from src.utils.label_detection import LABEL_COLUMN_CANDIDATES, NON_GROUND_TRUTH_COLUMNS

logger = logging.getLogger(__name__)

DEFAULT_INTERPOLATION_LIMIT = 2
DEFAULT_TARGET_HZ = 50
DEFAULT_MERGE_TOLERANCE_MS = 1
SUPPORTED_INPUT_SUFFIXES = {".csv", ".xlsx", ".xls"}
SENSOR_COLUMNS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
RAW_SAMPLE_COLUMNS = ["sample_time_offset", "x", "y", "z"]

RAW_AXIS_ALIASES = {
    "accelerometer": {
        "x": {"x", "accelx", "accelerometerx", "calibratedaccelx"},
        "y": {"y", "accely", "accelerometery", "calibratedaccely"},
        "z": {"z", "accelz", "accelerometerz", "calibratedaccelz"},
    },
    "gyroscope": {
        "x": {"x", "gyrox", "gyroscopex", "calibratedgyrox"},
        "y": {"y", "gyroy", "gyroscopey", "calibratedgyroy"},
        "z": {"z", "gyroz", "gyroscopez", "calibratedgyroz"},
    },
}

DIRECT_SENSOR_ALIASES = {
    "Ax": {"ax", "axw", "accelx", "accelerometerx", "calibratedaccelx"},
    "Ay": {"ay", "ayw", "accely", "accelerometery", "calibratedaccely"},
    "Az": {"az", "azw", "accelz", "accelerometerz", "calibratedaccelz"},
    "Gx": {"gx", "gxw", "gyrox", "gyroscopex", "calibratedgyrox"},
    "Gy": {"gy", "gyw", "gyroy", "gyroscopey", "calibratedgyroy"},
    "Gz": {"gz", "gzw", "gyroz", "gyroscopez", "calibratedgyroz"},
}


def _normalize_key(name: str) -> str:
    """
    Method Name :   _normalize_key
    Description :   Converts a column name to a simple lowercase comparison key.

    Output      :   Normalized string key.
    On Failure  :   Returns a normalized representation of the provided value.
    """
    return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())


def _detect_label_column(columns: List[str]) -> Optional[str]:
    """
    Method Name :   _detect_label_column
    Description :   Detects a ground-truth label column from known candidate names.

    Output      :   Matching label column name, or None.
    On Failure  :   Returns None when no trusted label column is found.
    """
    normalized = {str(col).strip().lower(): str(col) for col in columns}
    for candidate in LABEL_COLUMN_CANDIDATES:
        key = str(candidate).strip().lower()
        if key in normalized and key not in NON_GROUND_TRUTH_COLUMNS:
            return normalized[key]
    return None


def _load_sensor_file(file_path: Path) -> pd.DataFrame:
    """
    Method Name :   _load_sensor_file
    Description :   Loads CSV, XLSX, or XLS input into a DataFrame.

    Output      :   pandas DataFrame loaded from disk.
    On Failure  :   Raises an exception for missing or unsupported files.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path)
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported input format: {file_path.suffix}")
    logger.info(
        "Loaded %s: %d rows x %d columns", file_path.name, len(df), len(df.columns)
    )
    return df


def _sensor_prefix(path: Path, marker: str) -> str:
    """
    Method Name :   _sensor_prefix
    Description :   Extracts the shared session prefix before accelerometer/gyroscope text.

    Output      :   Sanitized pairing prefix.
    On Failure  :   Returns a sanitized fallback derived from the filename.
    """
    return _sanitize_dataset_name(path.name.lower().split(marker, 1)[0])


def _find_latest_sensor_pair(raw_dir: Path) -> Tuple[Path, Path]:
    """
    Method Name :   _find_latest_sensor_pair
    Description :   Finds the newest accelerometer and gyroscope file pair in data/raw.

    Output      :   Tuple of accelerometer path and gyroscope path.
    On Failure  :   Raises FileNotFoundError when no valid pair is found.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    files = [
        p
        for p in raw_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_INPUT_SUFFIXES
    ]
    accel_files = [p for p in files if "accelerometer" in p.name.lower()]
    gyro_files = [p for p in files if "gyroscope" in p.name.lower()]

    gyro_by_prefix: Dict[str, List[Path]] = {}
    for gyro in gyro_files:
        gyro_by_prefix.setdefault(_sensor_prefix(gyro, "gyroscope"), []).append(gyro)

    pairs = [
        (accel, gyro)
        for accel in accel_files
        for gyro in gyro_by_prefix.get(_sensor_prefix(accel, "accelerometer"), [])
    ]
    if not pairs:
        raise FileNotFoundError(
            f"No accelerometer/gyroscope pairs found in {raw_dir}. "
            "Provide --accel-file/--gyro-file or --input-csv."
        )

    import re

    def _filename_recorded_ts(p: Path) -> str:
        # Extract YYYY-MM-DD-HH-MM-SS from filename so sort reflects recording date,
        # not when the file was last touched by the pipeline (st_mtime is unreliable).
        m = re.search(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}", p.stem)
        return m.group(0) if m else ""

    pairs.sort(key=lambda pair: _filename_recorded_ts(pair[0]), reverse=True)
    return pairs[0]


def find_latest_sensor_pair(raw_dir: Path) -> Tuple[Path, Path]:
    """
    Method Name :   find_latest_sensor_pair
    Description :   Backward-compatible wrapper around _find_latest_sensor_pair.

    Output      :   Tuple of accelerometer path and gyroscope path.
    On Failure  :   Raises the exception from _find_latest_sensor_pair.
    """
    return _find_latest_sensor_pair(raw_dir)


def _sanitize_dataset_name(raw_name: str) -> str:
    """
    Method Name :   _sanitize_dataset_name
    Description :   Converts a dataset/session name into a safe lowercase filename token.

    Output      :   Safe dataset name string.
    On Failure  :   Returns "dataset" when the cleaned name is empty.
    """
    name = (raw_name or "").strip().lower().replace(" ", "_").replace("-", "_")
    name = re.sub(r"[^a-z0-9_]", "", name)
    return re.sub(r"_+", "_", name).strip("_") or "dataset"


def _dataset_stem_from_source(source_path: Path) -> str:
    """
    Method Name :   _dataset_stem_from_source
    Description :   Removes accelerometer/gyroscope suffixes from a source filename.

    Output      :   Dataset stem before final sanitization.
    On Failure  :   Falls back to the source file stem.
    """
    suffixes = (
        "_accelerometer_data",
        "_gyroscope_data",
        "_accelerometer",
        "_gyroscope",
        "-accelerometer_data",
        "-gyroscope_data",
        "-accelerometer",
        "-gyroscope",
        "accelerometer_data",
        "gyroscope_data",
    )
    stem = source_path.stem
    lower = stem.lower()
    for suffix in suffixes:
        if lower.endswith(suffix):
            return stem[: -len(suffix)].rstrip("_- ") or source_path.stem
    return stem


def _build_fused_output_path(
    output_dir: Path, source_path: Path, target_hz: int
) -> Path:
    """
    Method Name :   _build_fused_output_path
    Description :   Builds the dataset-specific fused CSV output path.

    Output      :   Path like data/processed/fused_<dataset_name>_50Hz.csv.
    On Failure  :   Raises the exception from path/name construction.
    """
    dataset_name = _sanitize_dataset_name(_dataset_stem_from_source(source_path))
    return output_dir / f"fused_{dataset_name}_{target_hz}Hz.csv"


def _normalize_columns(df: pd.DataFrame, sensor_type: str) -> pd.DataFrame:
    """
    Method Name :   _normalize_columns
    Description :   Normalizes raw axis names or direct fused sensor column names.

    Output      :   DataFrame with canonical raw axes or Ax/Ay/Az/Gx/Gy/Gz columns.
    On Failure  :   Raises ValueError for unknown sensor_type.
    """
    out = df.copy()
    rename_map: Dict[str, str] = {}

    if sensor_type in RAW_AXIS_ALIASES:
        aliases = RAW_AXIS_ALIASES[sensor_type]
        for column in out.columns:
            key = _normalize_key(column)
            for target, accepted in aliases.items():
                if key in accepted and target not in out.columns:
                    rename_map[column] = target
                    break
    elif sensor_type == "direct":
        existing = {column for column in SENSOR_COLUMNS if column in out.columns}
        for column in out.columns:
            key = _normalize_key(column)
            for target, accepted in DIRECT_SENSOR_ALIASES.items():
                if target not in existing and key in accepted:
                    rename_map[column] = target
                    existing.add(target)
                    break
    else:
        raise ValueError(f"Unknown sensor_type: {sensor_type}")

    if rename_map:
        logger.info("Column normalization: %s", rename_map)
        out = out.rename(columns=rename_map)
    return out


def _parse_list_cell(value):
    """
    Method Name :   _parse_list_cell
    Description :   Parses Garmin list-like cell values into Python lists.

    Output      :   Parsed list, scalar list, or original value.
    On Failure  :   Returns the original value when parsing is not possible.
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(text)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        parts = [part.strip() for part in text.split(",") if part.strip()]
        if len(parts) > 1:
            try:
                return [float(part) for part in parts]
            except ValueError:
                return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return [value]
    return value


def _parse_list_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Method Name :   _parse_list_columns
    Description :   Parses Garmin sample offset and x/y/z list columns.

    Output      :   DataFrame with parsed list columns.
    On Failure  :   Raises the exception from pandas apply/parsing.
    """
    out = df.copy()
    for column in RAW_SAMPLE_COLUMNS:
        if column in out.columns:
            out[column] = out[column].apply(_parse_list_cell)
    return out


def _filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Method Name :   _filter_valid_rows
    Description :   Drops Garmin rows whose list columns have mismatched sample counts.

    Output      :   Filtered DataFrame with valid list rows only.
    On Failure  :   Raises the exception from row validation.
    """
    list_columns = [column for column in RAW_SAMPLE_COLUMNS if column in df.columns]
    if not list_columns:
        return df.dropna(how="all").reset_index(drop=True)

    lengths = df[list_columns].apply(
        lambda col: col.map(
            lambda value: len(value) if isinstance(value, list) else np.nan
        )
    )
    mask = (
        lengths.notna().all(axis=1)
        & lengths.nunique(axis=1).eq(1)
        & lengths.iloc[:, 0].gt(0)
    )
    dropped = int((~mask).sum())
    if dropped:
        logger.info("Dropped %d invalid list rows", dropped)
    return df.loc[mask].reset_index(drop=True)


def _explode_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Method Name :   _explode_rows
    Description :   Explodes Garmin list rows into one row per sample.

    Output      :   Sample-level DataFrame.
    On Failure  :   Raises the exception from pandas explode.
    """
    list_columns = [column for column in RAW_SAMPLE_COLUMNS if column in df.columns]
    return (
        df.explode(list_columns, ignore_index=True)
        if list_columns
        else df.reset_index(drop=True)
    )


def _parse_timestamp_series(series: pd.Series) -> pd.Series:
    """
    Method Name :   _parse_timestamp_series
    Description :   Parses timestamp values as seconds, milliseconds, or datetime strings.

    Output      :   UTC pandas datetime Series.
    On Failure  :   Returns NaT values where parsing fails.
    """
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().mean() > 0.95:
        unit = "ms" if float(numeric.dropna().median()) > 1e11 else "s"
        return pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce")
    return pd.to_datetime(series, utc=True, errors="coerce")


def _create_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Method Name :   _create_timestamps
    Description :   Creates true_time from timestamp fields and optional sample offsets.

    Output      :   DataFrame with true_time column.
    On Failure  :   Raises ValueError when no usable timestamp column exists.
    """
    out = df.copy()
    if "true_time" in out.columns:
        out["true_time"] = pd.to_datetime(out["true_time"], utc=True, errors="coerce")
        return out
    if "timestamp" in out.columns:
        base_time = _parse_timestamp_series(out["timestamp"])
    elif "timestamp_iso" in out.columns:
        base_time = pd.to_datetime(out["timestamp_iso"], utc=True, errors="coerce")
    elif "timestamp_ms" in out.columns:
        out["true_time"] = pd.to_datetime(
            pd.to_numeric(out["timestamp_ms"], errors="coerce"), unit="ms", utc=True
        )
        return out
    else:
        raise ValueError(
            "No timestamp, timestamp_iso, timestamp_ms, or true_time column found"
        )

    offset_ms = pd.Series(0.0, index=out.index)
    for column in ("timestamp_ms", "sample_time_offset"):
        if column in out.columns:
            offset_ms += pd.to_numeric(out[column], errors="coerce").fillna(0.0)
    out["true_time"] = base_time + pd.to_timedelta(offset_ms, unit="ms")
    return out


def _rename_axes(df: pd.DataFrame, sensor_type: str) -> pd.DataFrame:
    """
    Method Name :   _rename_axes
    Description :   Renames raw x/y/z axes into accelerometer or gyroscope channels.

    Output      :   DataFrame with Ax/Ay/Az or Gx/Gy/Gz columns.
    On Failure  :   Raises ValueError for unknown sensor_type.
    """
    rename_map = {
        "accelerometer": {"x": "Ax", "y": "Ay", "z": "Az"},
        "gyroscope": {"x": "Gx", "y": "Gy", "z": "Gz"},
    }
    if sensor_type not in rename_map:
        raise ValueError(f"Unknown sensor_type: {sensor_type}")
    return df.rename(columns=rename_map[sensor_type])


def _merge_and_resample(
    accel_df: pd.DataFrame,
    gyro_df: pd.DataFrame,
    target_hz: int,
    merge_tolerance_ms: int,
) -> pd.DataFrame:
    """
    Method Name :   _merge_and_resample
    Description :   Nearest-time merges accelerometer and gyroscope rows and resamples to target Hz.

    Output      :   Fused DataFrame with true_time, six sensor channels, and timestamp helpers.
    On Failure  :   Raises an exception when required columns or valid rows are missing.
    """
    required_accel = ["true_time", "Ax", "Ay", "Az"]
    required_gyro = ["true_time", "Gx", "Gy", "Gz"]
    missing_accel = [
        column for column in required_accel if column not in accel_df.columns
    ]
    missing_gyro = [column for column in required_gyro if column not in gyro_df.columns]
    if missing_accel or missing_gyro:
        raise ValueError(f"Missing columns: accel={missing_accel}, gyro={missing_gyro}")

    accel = accel_df[required_accel].copy()
    gyro = gyro_df[required_gyro].copy()
    accel[["Ax", "Ay", "Az"]] = accel[["Ax", "Ay", "Az"]].apply(
        pd.to_numeric, errors="coerce"
    )
    gyro[["Gx", "Gy", "Gz"]] = gyro[["Gx", "Gy", "Gz"]].apply(
        pd.to_numeric, errors="coerce"
    )
    accel = accel.dropna(subset=required_accel).sort_values("true_time")
    gyro = gyro.dropna(subset=required_gyro).sort_values("true_time")
    if accel.empty or gyro.empty:
        raise ValueError("No valid accelerometer or gyroscope rows after parsing")

    merged = pd.merge_asof(
        accel,
        gyro,
        on="true_time",
        tolerance=pd.Timedelta(milliseconds=merge_tolerance_ms),
        direction="nearest",
    )
    matched = int(merged[["Gx", "Gy", "Gz"]].notna().all(axis=1).sum())
    logger.info(
        "Merge matched %d/%d rows (%.1f%%)",
        matched,
        len(merged),
        100 * matched / max(len(merged), 1),
    )

    period_ms = int(round(1000 / target_hz))
    resampled = (
        merged.set_index("true_time")
        .resample(f"{period_ms}ms")
        .mean()
        .interpolate(method="linear", limit=DEFAULT_INTERPOLATION_LIMIT)
        .dropna()
        .reset_index()
    )
    resampled = resampled[["true_time", *SENSOR_COLUMNS]]
    resampled["timestamp_ms"] = resampled["true_time"].astype("int64") // 10**6
    resampled["timestamp_iso"] = resampled["true_time"].dt.strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    )
    resampled["true_time"] = resampled["timestamp_iso"]
    logger.info("Resampled to %d Hz: %d rows", target_hz, len(resampled))
    return resampled


class DataIngestion:
    """Stage 1 ingestion component."""

    def __init__(self, pipeline_config: PipelineConfig, config: DataIngestionConfig):
        """
        Method Name :   __init__
        Description :   Stores pipeline and Stage 1 ingestion configuration.

        Output      :   DataIngestion instance.
        On Failure  :   Raises the exception from object construction.
        """
        self.pipeline_config = pipeline_config
        self.config = config

    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        """
        Method Name :   initiate_data_ingestion
        Description :   Selects input mode and writes one dataset-specific fused CSV.

        Output      :   DataIngestionArtifact with fused_csv_path for Stage 2.
        On Failure  :   Raises the exception and stops Stage 1.
        """
        logger.info("=" * 60)
        logger.info("STAGE 1 - Data Ingestion")
        logger.info("=" * 60)
        output_dir = Path(
            self.config.output_dir or self.pipeline_config.data_processed_dir
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        if self.config.input_csv is not None:
            return self._ingest_input_csv(Path(self.config.input_csv), output_dir)
        if self.config.accel_file and self.config.gyro_file:
            return self._ingest_sensor_pair(
                Path(self.config.accel_file),
                Path(self.config.gyro_file),
                output_dir,
                source_type="sensor_pair",
            )

        accel_path, gyro_path = _find_latest_sensor_pair(
            Path(self.pipeline_config.data_raw_dir)
        )
        return self._ingest_sensor_pair(
            accel_path, gyro_path, output_dir, source_type="auto_discover"
        )

    def _ingest_input_csv(
        self, input_path: Path, output_dir: Path
    ) -> DataIngestionArtifact:
        """
        Method Name :   _ingest_input_csv
        Description :   Reads direct fused CSV/Excel input and writes fused_<dataset>_50Hz.csv.

        Output      :   DataIngestionArtifact for the written fused file.
        On Failure  :   Raises the exception for missing files, missing columns, or bad timestamps.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        df = _normalize_columns(_load_sensor_file(input_path), "direct")
        missing = [column for column in SENSOR_COLUMNS if column not in df.columns]
        if missing:
            raise ValueError(
                f"Direct input is missing required sensor columns: {missing}"
            )

        if "true_time" not in df.columns:
            df = _create_timestamps(df)
        df["true_time"] = pd.to_datetime(df["true_time"], utc=True, errors="coerce")
        df[SENSOR_COLUMNS] = df[SENSOR_COLUMNS].apply(pd.to_numeric, errors="coerce")

        label_column = _detect_label_column(df.columns.tolist())
        if "timestamp_ms" not in df.columns:
            df["timestamp_ms"] = df["true_time"].astype("int64") // 10**6
        df["timestamp_iso"] = df["true_time"].dt.strftime("%Y-%m-%dT%H:%M:%S.%f")
        df["true_time"] = df["timestamp_iso"]

        keep_columns = ["true_time", *SENSOR_COLUMNS, "timestamp_ms", "timestamp_iso"]
        if label_column and label_column not in keep_columns:
            keep_columns.append(label_column)

        fused_df = (
            df[keep_columns]
            .dropna(subset=["true_time", *SENSOR_COLUMNS])
            .reset_index(drop=True)
        )
        output_path = _build_fused_output_path(
            output_dir, input_path, self.config.target_hz
        )
        fused_df.to_csv(output_path, index=False)
        source_type = (
            "excel" if input_path.suffix.lower() in {".xlsx", ".xls"} else "csv"
        )
        logger.info("Direct input written: %s (%d rows)", output_path, len(fused_df))
        return self._build_artifact(
            output_path, fused_df, source_type, input_path, label_column
        )

    def _ingest_sensor_pair(
        self,
        accel_path: Path,
        gyro_path: Path,
        output_dir: Path,
        source_type: str = "sensor_pair",
    ) -> DataIngestionArtifact:
        """
        Method Name :   _ingest_sensor_pair
        Description :   Processes one accelerometer/gyroscope pair into a fused 50 Hz CSV.

        Output      :   DataIngestionArtifact for the written fused file.
        On Failure  :   Raises the exception for missing files, parse errors, or merge failures.
        """
        if not accel_path.exists():
            raise FileNotFoundError(f"Accelerometer file not found: {accel_path}")
        if not gyro_path.exists():
            raise FileNotFoundError(f"Gyroscope file not found: {gyro_path}")

        logger.info("Processing accelerometer: %s", accel_path)
        logger.info("Processing gyroscope:     %s", gyro_path)
        accel_df = self._prepare_raw_sensor(
            _load_sensor_file(accel_path), "accelerometer"
        )
        gyro_df = self._prepare_raw_sensor(_load_sensor_file(gyro_path), "gyroscope")
        fused_df = _merge_and_resample(
            accel_df,
            gyro_df,
            target_hz=self.config.target_hz,
            merge_tolerance_ms=self.config.merge_tolerance_ms,
        )

        output_path = _build_fused_output_path(
            output_dir, accel_path, self.config.target_hz
        )
        fused_df.to_csv(output_path, index=False)
        logger.info(
            "Fused sensor pair written: %s (%d rows)", output_path, len(fused_df)
        )
        return self._build_artifact(
            output_path, fused_df, source_type, accel_path, None
        )

    def _build_artifact(
        self,
        fused_csv_path: Path,
        fused_df: pd.DataFrame,
        source_type: str,
        source_path: Path,
        label_column: Optional[str],
    ) -> DataIngestionArtifact:
        """
        Method Name :   _build_artifact
        Description :   Builds the Stage 1 artifact passed to Stage 2.

        Output      :   DataIngestionArtifact.
        On Failure  :   Raises the exception from artifact construction.
        """
        return DataIngestionArtifact(
            fused_csv_path=fused_csv_path,
            n_rows=len(fused_df),
            n_columns=len(fused_df.columns),
            sampling_hz=self.config.target_hz,
            ingestion_timestamp=datetime.now().isoformat(),
            source_type=source_type,
            source_path=source_path,
            has_labels=bool(label_column),
            label_column=label_column,
        )

    @staticmethod
    def _prepare_raw_sensor(df: pd.DataFrame, sensor_type: str) -> pd.DataFrame:
        """
        Method Name :   _prepare_raw_sensor
        Description :   Runs raw sensor normalization, list parsing, timestamp creation, and axis renaming.

        Output      :   Prepared raw sensor DataFrame.
        On Failure  :   Raises the exception from the failing preparation step.
        """
        return _rename_axes(
            _create_timestamps(
                _explode_rows(
                    _filter_valid_rows(
                        _parse_list_columns(_normalize_columns(df, sensor_type))
                    )
                )
            ),
            sensor_type,
        )

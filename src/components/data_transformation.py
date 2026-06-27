"""Stage 3 data transformation: fused CSV to audited model input windows."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.entity.artifact_entity import (
    DataIngestionArtifact,
    DataTransformationArtifact,
    DataValidationArtifact,
)
from src.entity.config_entity import DataTransformationConfig, PipelineConfig

logger = logging.getLogger(__name__)

ACCEL_COLUMNS = ["Ax", "Ay", "Az"]
GYRO_COLUMNS = ["Gx", "Gy", "Gz"]
SENSOR_COLUMNS = [*ACCEL_COLUMNS, *GYRO_COLUMNS]
RAW_MODEL_INPUT_SPACE = "raw_physical_units_ms2_dps"
ZSCORE_MODEL_INPUT_SPACE = "zscore_scaled"


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _safe_float(value: Any) -> Optional[float]:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


class DataTransformation:
    """Transform a validated fused CSV into model-ready windows."""

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        config: DataTransformationConfig,
        ingestion_artifact: DataIngestionArtifact,
        validation_artifact: Optional[DataValidationArtifact] = None,
    ):
        """
        Method Name :   __init__
        Description :   Stores pipeline config, Stage 3 config, and upstream artifacts.

        Output      :   Initialized DataTransformation component.
        On Failure  :   Raises the original exception.
        """
        self.pipeline_config = pipeline_config
        self.config = config
        self.ingestion_artifact = ingestion_artifact
        self.validation_artifact = validation_artifact

    def initiate_data_transformation(self) -> DataTransformationArtifact:
        """
        Method Name :   initiate_data_transformation
        Description :   Runs Stage 3 preprocessing and writes audited model input artifacts.

        Output      :   DataTransformationArtifact pointing to production_X and reports.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            logger.info("=" * 60)
            logger.info("STAGE 3 - Data Transformation")
            logger.info("=" * 60)

            from src.preprocess_data import PreprocessLogger, UnifiedPreprocessor

            output_dir = Path(
                self.config.output_dir or self.pipeline_config.data_prepared_dir
            )
            output_dir.mkdir(parents=True, exist_ok=True)

            csv_path, df = self._load_input_csv()
            pre_stats = self._channel_stats(df, self.config.sensors)

            prep_logger = PreprocessLogger("preprocessing").get_logger()
            preprocessor = UnifiedPreprocessor(
                logger=prep_logger,
                window_size=self.config.window_size,
                overlap=self.config.overlap,
            )

            data_format, sensor_cols = self._detect_format(preprocessor, df)
            df, unit_summary = self._apply_unit_conversion(df, sensor_cols)
            unit_stats = self._channel_stats(df, sensor_cols)
            df, experimental_summary = self._apply_experimental_transforms(
                df, sensor_cols, prep_logger
            )
            experimental_stats = self._channel_stats(df, sensor_cols)
            df, norm_summary = self._apply_normalization_if_enabled(df, sensor_cols)
            post_stats = self._channel_stats(df, sensor_cols)

            X, y, metadata = self._create_windows(
                preprocessor, df, sensor_cols, data_format
            )
            output_summary = self._save_outputs(output_dir, X, y, metadata)
            quality_summary = self._quality_checks(X, sensor_cols)

            report_summary = {
                "created_at": datetime.now().isoformat(),
                "stage": "data_transformation",
                "input_csv": csv_path,
                "data_format": data_format,
                "model_input_space": norm_summary["model_input_space"],
                "feature_space": {
                    "name": norm_summary["model_input_space"],
                    "shape": "n_windows x window_size x 6_channels",
                    "description": (
                        "Raw physical units means accelerometer m/s^2 and gyroscope deg/s. "
                        "Z-score means the saved scaler was applied after unit conversion."
                    ),
                },
                "channel_order": sensor_cols,
                "accelerometer_output_unit": unit_summary["accelerometer_output_unit"],
                "gyroscope_output_unit": unit_summary["gyroscope_output_unit"],
                "unit_conversion": unit_summary,
                "experimental_preprocessing": experimental_summary,
                "normalization": norm_summary,
                "windowing": {
                    "window_size": int(self.config.window_size),
                    "overlap": float(self.config.overlap),
                    "step_size": int(
                        self.config.window_size * (1 - self.config.overlap)
                    ),
                    "n_windows": int(X.shape[0]),
                    "x_shape": list(X.shape),
                    "x_dtype": str(X.dtype),
                },
                "labels": {
                    "has_labels": bool(y is not None),
                    "production_y_path": output_summary.get("production_y_path"),
                    "stale_y_ignored": bool(
                        output_summary.get("stale_y_ignored", False)
                    ),
                    "stale_y_path": output_summary.get("stale_y_path"),
                    "stale_y_shape": output_summary.get("stale_y_shape"),
                },
                "quality_checks": quality_summary,
                "pre_transform_channel_stats": pre_stats,
                "post_unit_conversion_channel_stats": unit_stats,
                "post_experimental_channel_stats": experimental_stats,
                "post_transform_channel_stats": post_stats,
                "outputs": output_summary,
            }
            report_path = self._write_transformation_report(output_dir, report_summary)

            return self._build_artifact(
                output_summary=output_summary,
                report_path=report_path,
                X=X,
                y=y,
                unit_summary=unit_summary,
                experimental_summary=experimental_summary,
                norm_summary=norm_summary,
                sensor_cols=sensor_cols,
            )
        except Exception as exc:
            logger.exception("Stage 3 data transformation failed: %s", exc)
            raise

    def _load_input_csv(self) -> Tuple[Path, pd.DataFrame]:
        """
        Method Name :   _load_input_csv
        Description :   Loads the selected Stage 3 input CSV from config or Stage 1 artifact.

        Output      :   Tuple of input path and loaded DataFrame.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            csv_path = Path(
                self.config.input_csv or self.ingestion_artifact.fused_csv_path
            )
            if not csv_path.exists():
                raise FileNotFoundError(f"Stage 3 input CSV not found: {csv_path}")
            df = pd.read_csv(csv_path)
            logger.info("Input CSV: %s", csv_path)
            logger.info("Input shape: %s", df.shape)
            return csv_path, df
        except Exception:
            logger.exception("Could not load Stage 3 input CSV")
            raise

    def _detect_format(
        self, preprocessor: Any, df: pd.DataFrame
    ) -> Tuple[str, List[str]]:
        """
        Method Name :   _detect_format
        Description :   Detects labeled/unlabeled format and locks the sensor column order.

        Output      :   Tuple of data format and ordered sensor columns.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            data_format, detected_cols = preprocessor.detect_data_format(df)
            configured_cols = list(self.config.sensors or SENSOR_COLUMNS)
            if all(col in df.columns for col in configured_cols):
                sensor_cols = configured_cols
            else:
                sensor_cols = list(detected_cols)
            if len(sensor_cols) != 6:
                raise ValueError(f"Expected 6 sensor columns, got {sensor_cols}")
            logger.info(
                "Data format: %s | sensor columns: %s", data_format, sensor_cols
            )
            return data_format, sensor_cols
        except Exception:
            logger.exception("Could not detect Stage 3 data format")
            raise

    def _apply_unit_conversion(
        self, df: pd.DataFrame, sensor_cols: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Method Name :   _apply_unit_conversion
        Description :   Converts accelerometer channels from milliG to m/s^2 when required.

        Output      :   Converted DataFrame and unit-conversion summary.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            out = df.copy()
            accel_cols = [col for col in ACCEL_COLUMNS if col in sensor_cols]
            gyro_cols = [col for col in GYRO_COLUMNS if col in sensor_cols]

            detected_unit, max_abs = self._detect_accelerometer_unit(out, accel_cols)
            conversion_applied = False
            factor = float(self.config.unit_conversion_factor)

            if self.config.enable_unit_conversion:
                if detected_unit == "milliG":
                    out[accel_cols] = (
                        out[accel_cols].apply(pd.to_numeric, errors="coerce") * factor
                    )
                    conversion_applied = True
                elif detected_unit == "m/s^2":
                    out[accel_cols] = out[accel_cols].apply(
                        pd.to_numeric, errors="coerce"
                    )
                else:
                    raise ValueError(
                        "Ambiguous accelerometer unit. Stage 3 cannot safely convert input."
                    )
            else:
                logger.warning(
                    "Unit conversion disabled; accelerometer values pass through unchanged."
                )

            out[gyro_cols] = out[gyro_cols].apply(pd.to_numeric, errors="coerce")

            return out, {
                "enabled": bool(self.config.enable_unit_conversion),
                "conversion_applied": bool(conversion_applied),
                "conversion_factor": factor if conversion_applied else None,
                "accelerometer_input_unit_detected": detected_unit,
                "accelerometer_output_unit": (
                    "m/s^2"
                    if conversion_applied or detected_unit == "m/s^2"
                    else detected_unit
                ),
                "accelerometer_max_abs_before_conversion": _safe_float(max_abs),
                "gyroscope_input_unit_assumed": "deg/s",
                "gyroscope_output_unit": "deg/s",
                "gyroscope_conversion_applied": False,
            }
        except Exception:
            logger.exception("Could not apply Stage 3 unit conversion")
            raise

    def _detect_accelerometer_unit(
        self, df: pd.DataFrame, accel_cols: List[str]
    ) -> Tuple[str, float]:
        """
        Method Name :   _detect_accelerometer_unit
        Description :   Detects whether accelerometer channels look like milliG or m/s^2.

        Output      :   Unit label and maximum absolute acceleration value.
        On Failure  :   Raises ValueError when no accelerometer values are available.
        """
        values = (
            df[accel_cols].apply(pd.to_numeric, errors="coerce").to_numpy().reshape(-1)
        )
        values = values[np.isfinite(values)]
        if values.size == 0:
            raise ValueError(
                "No finite accelerometer values available for unit detection."
            )
        max_abs = float(np.abs(values).max())
        if max_abs > 100.0:
            return "milliG", max_abs
        if max_abs < 50.0:
            return "m/s^2", max_abs
        return "unknown", max_abs

    def _apply_normalization_if_enabled(
        self, df: pd.DataFrame, sensor_cols: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Method Name :   _apply_normalization_if_enabled
        Description :   Optionally applies the configured saved scaler for A/B testing.

        Output      :   Transformed DataFrame and normalization summary.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            if not self.config.enable_normalization:
                return df.copy(), {
                    "applied": False,
                    "mode": "paper_aligned_no_external_scaler",
                    "model_input_space": RAW_MODEL_INPUT_SPACE,
                    "normalization_variant": None,
                    "scaler_path": None,
                    "scaler_fit_users": None,
                }

            from src.utils.scaler import CANONICAL_SCALER_PATH

            scaler_path = Path(self.config.scaler_path or CANONICAL_SCALER_PATH)
            if not scaler_path.exists():
                raise FileNotFoundError(f"Scaler file not found: {scaler_path}")

            cfg = json.loads(scaler_path.read_text(encoding="utf-8"))
            requested_variant = str(self.config.normalization_variant or "zscore")
            scaler_variant = str(cfg.get("normalization_variant", requested_variant))
            if requested_variant != scaler_variant:
                raise ValueError(
                    "Normalization variant mismatch: "
                    f"config requests '{requested_variant}', scaler JSON says '{scaler_variant}'."
                )

            out = df.copy()
            values = (
                out[sensor_cols].apply(pd.to_numeric, errors="coerce").ffill().bfill()
            )

            if requested_variant == "none":
                return out, {
                    "applied": False,
                    "mode": "normalization_variant_none",
                    "model_input_space": RAW_MODEL_INPUT_SPACE,
                    "normalization_variant": "none",
                    "scaler_path": scaler_path,
                    "scaler_fit_users": cfg.get("fit_users"),
                }

            if requested_variant == "zscore":
                mean = np.asarray(
                    cfg.get("scaler_mean", cfg.get("mean")), dtype=np.float64
                )
                scale = np.asarray(
                    cfg.get("scaler_scale", cfg.get("scale")), dtype=np.float64
                )
                if mean.shape[0] != len(sensor_cols) or scale.shape[0] != len(
                    sensor_cols
                ):
                    raise ValueError(
                        f"Scaler dimension mismatch: mean={mean.shape}, scale={scale.shape}, "
                        f"sensor_cols={len(sensor_cols)}"
                    )
                safe_scale = np.where(scale == 0, 1.0, scale)
                out[sensor_cols] = (
                    values.to_numpy(dtype=np.float64) - mean
                ) / safe_scale
            elif requested_variant == "robust":
                center = np.asarray(cfg["scaler_center"], dtype=np.float64)
                scale = np.asarray(cfg["scaler_scale"], dtype=np.float64)
                safe_scale = np.where(scale == 0, 1.0, scale)
                out[sensor_cols] = (
                    values.to_numpy(dtype=np.float64) - center
                ) / safe_scale
            else:
                raise ValueError(
                    f"Unknown normalization_variant '{requested_variant}'. "
                    "Expected 'zscore', 'robust', or 'none'."
                )

            logger.info(
                "Normalization applied: variant=%s scaler=%s",
                requested_variant,
                scaler_path,
            )
            return out, {
                "applied": True,
                "mode": "external_saved_scaler",
                "model_input_space": (
                    ZSCORE_MODEL_INPUT_SPACE
                    if requested_variant == "zscore"
                    else f"{requested_variant}_scaled"
                ),
                "normalization_variant": requested_variant,
                "scaler_path": scaler_path,
                "scaler_fit_users": cfg.get("fit_users"),
                "scaler_fit_dataset": cfg.get("fit_dataset"),
            }
        except Exception:
            logger.exception("Could not apply Stage 3 normalization")
            raise

    def _apply_experimental_transforms(
        self, df: pd.DataFrame, sensor_cols: List[str], prep_logger: logging.Logger
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Method Name :   _apply_experimental_transforms
        Description :   Applies optional non-paper preprocessing only when explicitly enabled.

        Output      :   Transformed DataFrame and experimental preprocessing summary.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            out = df.copy()
            gravity_applied = False
            calibration_applied = False

            if self.config.enable_gravity_removal:
                from src.preprocess_data import GravityRemover

                remover = GravityRemover(logger=prep_logger, sampling_freq=50.0)
                out = remover.remove_gravity(out, enable=True)
                gravity_applied = True

            if self.config.enable_calibration:
                from src.preprocess_data import DomainCalibrator

                calibrator = DomainCalibrator(logger=prep_logger)
                out = calibrator.calibrate(out, enable=True)
                calibration_applied = True

            return out, {
                "gravity_removal_applied": gravity_applied,
                "calibration_applied": calibration_applied,
                "note": (
                    "Optional A/B preprocessing. Paper-aligned default keeps both disabled."
                ),
                "channel_order": sensor_cols,
            }
        except Exception:
            logger.exception("Could not apply Stage 3 experimental preprocessing")
            raise

    def _create_windows(
        self,
        preprocessor: Any,
        df: pd.DataFrame,
        sensor_cols: List[str],
        data_format: str,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], List[Dict[str, Any]]]:
        """
        Method Name :   _create_windows
        Description :   Converts the transformed time series into fixed-size model windows.

        Output      :   Tuple of X windows, optional y labels, and window metadata.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            if data_format == "labeled" and "activity" in df.columns:
                from src.utils.label_mapping import get_class_to_index

                activity_to_label = get_class_to_index()
                preprocessor.activity_to_label = activity_to_label
                preprocessor.label_to_activity = {
                    v: k for k, v in activity_to_label.items()
                }

            X, y, metadata = preprocessor.create_windows(df, sensor_cols, data_format)
            logger.info("Windows created: X shape=%s", X.shape)
            return X.astype(np.float32, copy=False), y, metadata
        except Exception:
            logger.exception("Could not create Stage 3 windows")
            raise

    def _save_outputs(
        self,
        output_dir: Path,
        X: np.ndarray,
        y: Optional[np.ndarray],
        metadata: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Method Name :   _save_outputs
        Description :   Saves production_X, metadata, and fresh labels when available.

        Output      :   Dictionary with output paths and label handling status.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            x_path = output_dir / "production_X.npy"
            metadata_path = output_dir / "production_metadata.json"
            y_path = output_dir / "production_y.npy"

            np.save(x_path, X)
            metadata_path.write_text(
                json.dumps(_json_safe(metadata), indent=2),
                encoding="utf-8",
            )

            production_y_path: Optional[Path] = None
            stale_y_ignored = False
            stale_y_shape = None
            if y is not None:
                np.save(y_path, y)
                production_y_path = y_path
                logger.info("Labels saved: y shape=%s", y.shape)
            elif y_path.exists():
                stale_y_ignored = True
                try:
                    stale_y_shape = list(np.load(y_path, mmap_mode="r").shape)
                except Exception:
                    stale_y_shape = ["unreadable"]
                logger.warning(
                    "Existing production_y.npy ignored because current Stage 3 input is unlabeled: %s",
                    y_path,
                )

            return {
                "production_X_path": x_path,
                "metadata_path": metadata_path,
                "production_y_path": production_y_path,
                "stale_y_ignored": stale_y_ignored,
                "stale_y_path": y_path if stale_y_ignored else None,
                "stale_y_shape": stale_y_shape,
            }
        except Exception:
            logger.exception("Could not save Stage 3 outputs")
            raise

    def _write_transformation_report(
        self, output_dir: Path, report_summary: Dict[str, Any]
    ) -> Path:
        """
        Method Name :   _write_transformation_report
        Description :   Writes the run-level Stage 3 audit report to JSON.

        Output      :   Path to transformation_report.json.
        On Failure  :   Logs the error and raises the exception.
        """
        try:
            report_path = output_dir / "transformation_report.json"
            report_path.write_text(
                json.dumps(_json_safe(report_summary), indent=2),
                encoding="utf-8",
            )
            logger.info("Transformation report saved: %s", report_path)
            return report_path
        except Exception:
            logger.exception("Could not write transformation report")
            raise

    def _build_artifact(
        self,
        output_summary: Dict[str, Any],
        report_path: Path,
        X: np.ndarray,
        y: Optional[np.ndarray],
        unit_summary: Dict[str, Any],
        experimental_summary: Dict[str, Any],
        norm_summary: Dict[str, Any],
        sensor_cols: List[str],
    ) -> DataTransformationArtifact:
        """
        Method Name :   _build_artifact
        Description :   Builds the Stage 3 artifact passed to downstream stages.

        Output      :   DataTransformationArtifact.
        On Failure  :   Raises the original exception.
        """
        return DataTransformationArtifact(
            production_X_path=Path(output_summary["production_X_path"]),
            metadata_path=Path(output_summary["metadata_path"]),
            transformation_report_path=report_path,
            n_windows=int(X.shape[0]),
            window_size=int(X.shape[1]),
            unit_conversion_applied=bool(unit_summary["conversion_applied"]),
            unit_conversion_factor=unit_summary.get("conversion_factor"),
            preprocessing_timestamp=datetime.now().isoformat(),
            channel_order=list(sensor_cols),
            has_labels=bool(y is not None),
            normalization_applied=bool(norm_summary["applied"]),
            scaler_path=(
                Path(norm_summary["scaler_path"])
                if norm_summary.get("scaler_path")
                else None
            ),
            model_input_space=str(norm_summary["model_input_space"]),
            gravity_removal_applied=bool(
                experimental_summary["gravity_removal_applied"]
            ),
            calibration_applied=bool(experimental_summary["calibration_applied"]),
            production_y_path=(
                Path(output_summary["production_y_path"])
                if output_summary.get("production_y_path")
                else None
            ),
        )

    def _channel_stats(
        self, df: pd.DataFrame, sensor_cols: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Method Name :   _channel_stats
        Description :   Computes min, max, mean, and std for available sensor columns.

        Output      :   Per-channel statistics dictionary.
        On Failure  :   Returns stats only for columns that can be read.
        """
        stats: Dict[str, Dict[str, Any]] = {}
        for col in sensor_cols:
            if col not in df.columns:
                continue
            series = pd.to_numeric(df[col], errors="coerce")
            stats[col] = {
                "mean": _safe_float(series.mean()),
                "std": _safe_float(series.std(ddof=0)),
                "min": _safe_float(series.min()),
                "max": _safe_float(series.max()),
                "missing": int(series.isna().sum()),
            }
        return stats

    def _quality_checks(self, X: np.ndarray, sensor_cols: List[str]) -> Dict[str, Any]:
        """
        Method Name :   _quality_checks
        Description :   Checks the final model tensor for NaN, inf, constant, or zero-only channels.

        Output      :   Dictionary of tensor quality checks.
        On Failure  :   Raises the original exception.
        """
        has_nan = bool(np.isnan(X).any())
        has_inf = bool(np.isinf(X).any())
        constant_channels: List[str] = []
        zero_only_channels: List[str] = []
        for idx, col in enumerate(sensor_cols):
            values = X[:, :, idx]
            if float(np.nanstd(values)) < 1e-8:
                constant_channels.append(col)
            if bool(np.allclose(values, 0.0)):
                zero_only_channels.append(col)

        return {
            "has_nan": has_nan,
            "has_inf": has_inf,
            "constant_channels": constant_channels,
            "zero_only_channels": zero_only_channels,
        }

"""Build pipeline config dataclasses from CLI arguments and YAML settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.entity.config_entity import (
    CalibrationUncertaintyConfig,
    DataIngestionConfig,
    DataTransformationConfig,
    DataValidationConfig,
    ModelEvaluationConfig,
    ModelInferenceConfig,
    ModelRegistrationConfig,
    ModelRetrainingConfig,
    PipelineConfig,
)
from src.logger import logging
from src.utils.config_loader import (
    apply_overrides,
    load_monitoring_config,
    load_trigger_config,
    load_yaml_overrides,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineRuntimeConfigs:
    """Container for all config objects needed to construct ProductionPipeline."""

    pipeline: PipelineConfig
    ingestion: DataIngestionConfig
    validation: DataValidationConfig
    transformation: DataTransformationConfig
    inference: ModelInferenceConfig
    evaluation: ModelEvaluationConfig
    retraining: ModelRetrainingConfig
    registration: ModelRegistrationConfig
    monitoring: Any
    trigger: Any
    calibration: CalibrationUncertaintyConfig


def load_preprocessing_config(config_path: str) -> dict:
    """
    Method Name :   load_preprocessing_config
    Description :   Load preprocessing toggles from the pipeline YAML file.

    Output      :   Returns the preprocessing dictionary or an empty dictionary.
    On Failure  :   Logs the error and raises the exception.
    """
    path = Path(config_path)
    if not path.exists():
        print(f"Config file not found: {path}, using defaults")
        return {}
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("preprocessing", {})


def load_validation_config(config_path: str) -> DataValidationConfig:
    """
    Method Name :   load_validation_config
    Description :   Load Stage 2 validation settings from the pipeline YAML file.

    Output      :   Returns DataValidationConfig.
    On Failure  :   Logs the error and raises the exception.
    """
    config = DataValidationConfig()
    path = Path(config_path)
    if not path.exists():
        print(f"Config file not found: {path}, using validation defaults")
        return config

    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    preprocessing = cfg.get("preprocessing", {})
    validation = cfg.get("validation", {})
    thresholds = validation.get("thresholds", {})

    if "sampling_frequency_hz" in preprocessing:
        config.expected_frequency_hz = float(preprocessing["sampling_frequency_hz"])
    if "max_missing_ratio" in thresholds:
        config.max_missing_ratio = float(thresholds["max_missing_ratio"])
    if "max_acceleration_ms2" in thresholds:
        config.max_acceleration_ms2 = float(thresholds["max_acceleration_ms2"])
    if "max_gyroscope_dps" in thresholds:
        config.max_gyroscope_dps = float(thresholds["max_gyroscope_dps"])
    if "sampling_rate_tolerance" in thresholds:
        config.sampling_rate_tolerance = float(thresholds["sampling_rate_tolerance"])

    return config


def build_runtime_configs(args) -> PipelineRuntimeConfigs:
    """
    Method Name :   build_runtime_configs
    Description :   Convert CLI arguments and YAML settings into pipeline config objects.

    Output      :   Returns PipelineRuntimeConfigs.
    On Failure  :   Logs the error and raises the exception.
    """
    yaml_preproc = load_preprocessing_config(args.config)
    validation_cfg = load_validation_config(args.config)

    enable_unit_conversion = yaml_preproc.get("enable_unit_conversion", True)
    enable_gravity_removal = yaml_preproc.get("enable_gravity_removal", False)
    enable_calibration = yaml_preproc.get(
        "enable_calibration", yaml_preproc.get("enable_domain_calibration", False)
    )
    unit_conversion_factor = float(yaml_preproc.get("unit_conversion_factor", 0.00980665))
    enable_normalization = yaml_preproc.get("enable_normalization", False)
    normalization_variant = yaml_preproc.get("normalization_variant", "zscore")
    scaler_path = yaml_preproc.get("scaler_path")

    if args.no_unit_conversion:
        enable_unit_conversion = False
    if args.gravity_removal:
        enable_gravity_removal = True
    if args.calibrate:
        enable_calibration = True
    if args.enable_normalization:
        enable_normalization = True
    if args.no_normalization:
        enable_normalization = False
    if args.normalization_variant:
        normalization_variant = args.normalization_variant

    pipeline_cfg = PipelineConfig()
    ingestion_cfg = DataIngestionConfig(
        input_csv=Path(args.input_csv) if args.input_csv else None,
        accel_file=Path(args.accel_file) if args.accel_file else None,
        gyro_file=Path(args.gyro_file) if args.gyro_file else None,
    )
    transformation_cfg = DataTransformationConfig(
        unit_conversion_factor=unit_conversion_factor,
        enable_unit_conversion=enable_unit_conversion,
        enable_gravity_removal=enable_gravity_removal,
        enable_calibration=enable_calibration,
        enable_normalization=enable_normalization,
        normalization_variant=normalization_variant,
        scaler_path=Path(scaler_path) if scaler_path else None,
    )
    inference_cfg = ModelInferenceConfig(model_path=Path(args.model) if args.model else None)
    evaluation_cfg = ModelEvaluationConfig(labels_path=Path(args.labels) if args.labels else None)
    retraining_cfg = ModelRetrainingConfig(
        enable_adaptation=(args.adapt != "none"),
        adaptation_method=args.adapt,
        epochs=args.epochs,
        skip_cv=args.skip_cv,
        labels_path=Path(args.labels) if args.labels else None,
    )
    registration_cfg = ModelRegistrationConfig(auto_deploy=args.auto_deploy)
    calibration_cfg = CalibrationUncertaintyConfig(mc_forward_passes=args.mc_dropout_passes)
    monitoring_cfg = load_monitoring_config()
    trigger_cfg = load_trigger_config()

    overrides = load_yaml_overrides()
    if overrides:
        apply_overrides(registration_cfg, overrides.get("registration", {}))
        apply_overrides(calibration_cfg, overrides.get("calibration", {}))
        logger.info("YAML overrides applied from config/pipeline_overrides.yaml")

    _log_config_summary(args.config, args.labels, validation_cfg, transformation_cfg)

    return PipelineRuntimeConfigs(
        pipeline=pipeline_cfg,
        ingestion=ingestion_cfg,
        validation=validation_cfg,
        transformation=transformation_cfg,
        inference=inference_cfg,
        evaluation=evaluation_cfg,
        retraining=retraining_cfg,
        registration=registration_cfg,
        monitoring=monitoring_cfg,
        trigger=trigger_cfg,
        calibration=calibration_cfg,
    )


def _log_config_summary(
    config_path: str,
    labels_path: str | None,
    validation_cfg: DataValidationConfig,
    transformation_cfg: DataTransformationConfig,
) -> None:
    logger.info("Preprocessing configuration (from %s):", config_path)
    logger.info(
        "  Unit Conversion (milliG->m/s^2): %s",
        "ON" if transformation_cfg.enable_unit_conversion else "OFF",
    )
    logger.info("  Unit conversion factor:         %.8f", transformation_cfg.unit_conversion_factor)
    logger.info(
        "  Gravity Removal:               %s",
        "ON" if transformation_cfg.enable_gravity_removal else "OFF",
    )
    logger.info(
        "  Domain Calibration:            %s",
        "ON" if transformation_cfg.enable_calibration else "OFF",
    )
    logger.info(
        "  Normalization:                 %s  (variant=%s)",
        "ON" if transformation_cfg.enable_normalization else "OFF",
        transformation_cfg.normalization_variant,
    )
    logger.info("  Labels file:                   %s", labels_path or "NOT PROVIDED")
    logger.info("Validation configuration (from %s):", config_path)
    logger.info("  Expected frequency:            %.2f Hz", validation_cfg.expected_frequency_hz)
    logger.info(
        "  Sampling tolerance:            %.0f%%", validation_cfg.sampling_rate_tolerance * 100
    )
    logger.info("  Max missing ratio:             %.2f%%", validation_cfg.max_missing_ratio * 100)
    logger.info("  Max acceleration:              %.2f m/s^2", validation_cfg.max_acceleration_ms2)
    logger.info("  Max gyroscope:                 %.2f deg/s", validation_cfg.max_gyroscope_dps)

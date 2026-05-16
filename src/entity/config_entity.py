"""
Configuration entities for HAR MLOps Production Pipeline.

Each pipeline stage gets a dataclass config.  The ProductionPipeline reads
these at init, and each Component receives only the config it needs.

Inspired by: vikashishere/YT-MLops-Proj1 (see docs/thesis/production refrencxe/)

Stages:
     1  Data Ingestion         (Excel/CSV Ã¢â€ â€™ fused CSV)
     2  Data Validation        (schema + range checks)
     3  Data Transformation    (CSV Ã¢â€ â€™ windowed .npy)
     4  Model Inference        (.npy + model Ã¢â€ â€™ predictions)
     5  Model Evaluation       (confidence / distribution / ECE)
     6  Post-Inference Monitoring (3-layer: confidence, temporal, drift)
     7  Trigger Evaluation     (retraining decision)
     8  Model Retraining       (unsupervised / supervised, AdaBN)
     9  Model Registration     (version, deploy, rollback)
    10  Baseline Update        (rebuild drift baselines)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from src.config import OVERLAP
from src.config import PROJECT_ROOT as CONFIG_PROJECT_ROOT
from src.config import WINDOW_SIZE
from src.utils.common import get_timestamp

TIMESTAMP: str = get_timestamp()


# ============================================================================
# Master Pipeline Config
# ============================================================================


@dataclass
class PipelineConfig:
    """Top-level pipeline settings shared by all stages."""

    pipeline_name: str = "har_mental_health_pipeline"
    artifact_dir: str = os.path.join("artifacts", TIMESTAMP)
    timestamp: str = TIMESTAMP

    # Paths Ã¢â‚¬â€ sensible defaults, override via run_pipeline.py CLI
    project_root: Path = CONFIG_PROJECT_ROOT
    data_raw_dir: Optional[Path] = field(default=None)
    data_processed_dir: Optional[Path] = field(default=None)
    data_prepared_dir: Optional[Path] = field(default=None)
    models_dir: Optional[Path] = field(default=None)
    models_pretrained_dir: Optional[Path] = field(default=None)
    outputs_dir: Optional[Path] = field(default=None)
    logs_dir: Optional[Path] = field(default=None)
    scripts_dir: Optional[Path] = field(default=None)  # legacy CLI-wrapper compatibility path

    def __post_init__(self):
        if self.data_raw_dir is None:
            self.data_raw_dir = self.project_root / "data" / "raw"
        if self.data_processed_dir is None:
            self.data_processed_dir = self.project_root / "data" / "processed"
        if self.data_prepared_dir is None:
            self.data_prepared_dir = self.project_root / "data" / "prepared"
        if self.models_dir is None:
            self.models_dir = self.project_root / "models"
        if self.models_pretrained_dir is None:
            self.models_pretrained_dir = self.project_root / "models" / "pretrained"
        if self.outputs_dir is None:
            self.outputs_dir = self.project_root / "outputs"
        if self.logs_dir is None:
            self.logs_dir = self.project_root / "logs"
        if self.scripts_dir is None:
            # Keep for backward-compatible script wrappers; runtime stages are src-owned.
            self.scripts_dir = self.project_root / "scripts"


# ============================================================================
# Stage 1 Data Ingestion
# ============================================================================


@dataclass
class DataIngestionConfig:
    """Configuration for raw-sensor-data ingestion (Excel/CSV fused CSV)."""

    accel_file: Optional[Path] = None  # auto-detect if None
    gyro_file: Optional[Path] = None  # auto-detect if None
    input_csv: Optional[Path] = None  # direct CSV (your own recording)
    target_hz: int = 50
    merge_tolerance_ms: int = 1
    output_dir: Optional[Path] = None


# ============================================================================
# Stage 2 Data Validation
# ============================================================================


@dataclass
class DataValidationConfig:
    """Configuration for data validation."""

    sensor_columns: List[str] = field(default_factory=lambda: ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"])
    timestamp_columns: List[str] = field(
        default_factory=lambda: ["true_time", "timestamp", "timestamp_iso", "timestamp_ms"]
    )
    expected_frequency_hz: float = 50.0
    sampling_rate_tolerance: float = 0.1
    max_acceleration_ms2: float = 50.0
    max_gyroscope_dps: float = 500.0
    max_missing_ratio: float = 0.05


# ============================================================================
# Stage 3 Ã¢â‚¬â€œ Data Transformation (Preprocessing)
# ============================================================================


@dataclass
class DataTransformationConfig:
    """Configuration for preprocessing (CSV to windowed .npy arrays)."""

    input_csv: Optional[Path] = None
    unit_conversion_factor: float = 0.00980665
    enable_unit_conversion: bool = True  # milliG to m/s^2 when input is raw Garmin milliG.
    enable_gravity_removal: bool = False  # Optional A/B only; not part of the paper path.
    enable_calibration: bool = False  # Optional A/B only; not part of the paper path.
    window_size: int = WINDOW_SIZE  # 4 seconds at 50 Hz
    overlap: float = OVERLAP  # 50 % overlap
    sensors: List[str] = field(default_factory=lambda: ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"])
    output_dir: Optional[Path] = None
    # Paper-aligned default is raw physical units. Enable normalization only for A/B checks.
    #   "zscore" -> StandardScaler with saved stats
    #   "none"   -> no amplitude normalization
    #   "robust" -> RobustScaler with saved stats
    enable_normalization: bool = False
    normalization_variant: str = "zscore"
    scaler_path: Optional[Path] = None


# ============================================================================
# Stage 4 Model Inference
# ============================================================================


@dataclass
class ModelInferenceConfig:
    """Configuration for model inference."""

    model_path: Optional[Path] = None  # defaults to pretrained
    input_npy: Optional[Path] = None  # defaults to prepared/production_X.npy
    batch_size: int = 32
    confidence_threshold: float = 0.50
    output_dir: Optional[Path] = None


# ============================================================================
# Stage 5 Model Evaluation
# ============================================================================


@dataclass
class ModelEvaluationConfig:
    """Configuration for prediction evaluation."""

    predictions_csv: Optional[Path] = None
    labels_path: Optional[Path] = None  # optional Ã¢â‚¬â€ unlabeled is fine
    output_dir: Optional[Path] = None
    confidence_bins: int = 10


# ============================================================================
# Stage 6 Post-Inference Monitoring
# ============================================================================


@dataclass
class PostInferenceMonitoringConfig:
    """Configuration for post-inference monitoring (3-layer)."""

    predictions_csv: Optional[Path] = None
    production_data_npy: Optional[Path] = None
    baseline_stats_json: Optional[Path] = None
    model_path: Optional[Path] = None
    output_dir: Optional[Path] = None

    # -- Thresholds (single source of truth; also read by src/api/app.py) --
    # NOTE: Stage 6 values are intentionally tighter than Stage 7 (TriggerEvaluationConfig):
    # Stage 6 warns early on unlabeled production data; Stage 7 escalates only under
    # voting. Do not unify these without reading thesis ch6 Threshold Calibration Gap.
    # A28 (2026-04-21): tightened from 0.60/30/50/2.0 for unlabeled production data.
    # Layer 1 -- confidence
    confidence_warn_threshold: float = 0.70  # mean confidence below this -> WARNING
    uncertain_pct_threshold: float = 20.0  # % of low-confidence windows -> WARNING
    uncertain_window_threshold: float = 0.50  # per-window cutoff: max_prob < this -> uncertain
    # Layer 1b -- dominant-class collapse guard (A27, 2026-04-21)
    dominant_class_warn_threshold: float = 85.0  # % of windows in one class -> WARNING
    dominant_class_critical_threshold: float = 95.0  # -> CRITICAL (review, no auto-retrain)
    # Layer 2 -- temporal
    transition_rate_threshold: float = 35.0  # % transition rate above this -> WARNING
    window_duration_seconds: float = 4.0  # 200 samples / 50 Hz
    prediction_stride_seconds: float = 2.0  # 50% overlap -> 100-sample stride / 50 Hz
    low_gyro_motion_threshold: float = 1.1  # deg/s median; empirical 28-session collapse separator
    low_motion_dominance_threshold: float = 70.0  # % dominance plus low G_mag -> collapse risk
    # Layer 3 -- drift
    drift_zscore_threshold: float = 1.8  # per-channel z-score above this -> WARNING
    # Defended runtime default is lightweight z-score mean-shift.
    # MMD remains available for calibrated offline/experimental audit runs.
    drift_detector_mode: str = "zscore_mean_shift"  # zscore_mean_shift | mmd
    mmd_reference_npy: Optional[Path] = None
    mmd_threshold: Optional[float] = None  # if None, calibrated from reference bootstrap
    mmd_sample_size: int = 384
    mmd_bootstrap_iterations: int = 40
    mmd_random_seed: int = 42

    # Temperature-scaling calibration (applied before Layer 1/3 analysis)
    # Set to the temperature T from Stage 11 (CalibrationUncertainty) output;
    # 1.0 means no rescaling.
    calibration_temperature: float = 1.0

    # Baseline quality guard
    max_baseline_age_days: int = 90  # warn if baseline file is older than this

    # Drift exclusion: skip Layer 3 when production data IS the training data
    # (self-comparison would give artificially low drift scores).
    is_training_session: bool = False

    # Baseline mode — must match the inference preprocessing contract.
    # Production inference uses raw physical units (no scaler), so the default
    # is raw_physical.  Changing this to "normalized" without a matching
    # scaler-enabled pipeline will produce fake critical drift (raw Az ≈ -9.8 m/s²
    # vs normalized baseline mean ≈ 0).
    #   "raw_physical"  → use models/raw_physical_baseline.json
    #   "normalized"    → use models/normalized_baseline.json (A/B only)
    baseline_mode: str = "raw_physical"
    raw_baseline_path: Optional[Path] = None  # default: models/raw_physical_baseline.json
    normalized_baseline_path: Optional[Path] = None  # default: models/normalized_baseline.json


# ============================================================================
# Stage 7  Trigger Evaluation
# ============================================================================


@dataclass
class TriggerEvaluationConfig:
    """Configuration for retraining-trigger evaluation."""

    confidence_warn: float = 0.65
    confidence_critical: float = 0.50
    # Drift metric is a z-score of mean-shift per channel, NOT PSI.
    # 2.0ÃÆ’ Ã¢â€°Ë† 95th percentile (warn), 3.0ÃÆ’ Ã¢â€°Ë† 99.7th percentile (critical).
    drift_zscore_warn: float = 2.0
    drift_zscore_critical: float = 3.0
    temporal_flip_warn: float = 0.35
    temporal_flip_critical: float = 0.50
    cooldown_hours: int = 24
    state_dir: Optional[Path] = None


# ============================================================================
# Stage 8 Model Retraining
# ============================================================================


@dataclass
class ModelRetrainingConfig:
    """Configuration for supervised model retraining on labeled data."""

    # Data paths
    source_data_path: Optional[Path] = None  # labeled training CSV
    labels_path: Optional[Path] = None  # user-provided labels (optional)

    # Training hyperparameters
    epochs: int = 100
    batch_size: int = 64
    learning_rate: float = 0.001
    n_folds: int = 5
    skip_cv: bool = False

    # Output
    output_dir: Optional[Path] = None
    experiment_name: str = "har-retraining"
    run_name: Optional[str] = None


# ============================================================================
# Stage 9 Model Registration
# ============================================================================


@dataclass
class ModelRegistrationConfig:
    """Configuration for model versioning and deployment."""

    registry_dir: Optional[Path] = None
    model_path: Optional[Path] = None  # new model to register
    version: Optional[str] = None  # auto-incremented if None
    auto_deploy: bool = False  # deploy immediately if better
    proxy_validation: bool = True  # validate before deployment
    # Governance gate: new accuracy must be within this many points of current.
    # Default 0.005 (0.5 %) tolerates normal retraining noise while blocking
    # genuine regressions.  Set to 0.0 for zero-tolerance strict mode.
    degradation_tolerance: float = 0.005
    # When True, block deployment if accuracy metrics are absent.
    # Default False preserves current behaviour (register but do NOT auto-deploy).
    block_if_no_metrics: bool = False


# ============================================================================
# Stage 10 Model Baseline Update
# ============================================================================


@dataclass
class BaselineUpdateConfig:
    """Configuration for rebuilding drift baselines after retraining."""

    training_data_path: Optional[Path] = None  # CSV with labeled data
    scaler_config_path: Optional[Path] = None  # scaler params for normalized baseline
    output_baseline_path: Optional[Path] = None  # where to save baseline JSON
    output_normalized_path: Optional[Path] = None  # where to save normalized baseline
    rebuild_embeddings: bool = False
    model_path: Optional[Path] = None  # for embedding baseline
    # Governance: False (default) = save baseline only as MLflow artifact.
    # True = promote to shared models/ path that monitoring reads at runtime.
    # Use --update-baseline CLI flag to set True explicitly.
    promote_to_shared: bool = False


# ============================================================================
# Stage 11 Model Calibration & Uncertainty Quantification
# ============================================================================


@dataclass
class CalibrationUncertaintyConfig:
    """Configuration for post-hoc calibration and MC Dropout UQ."""

    # Temperature scaling
    initial_temperature: float = 1.5
    temp_lr: float = 0.01
    temp_max_iter: int = 100

    # MC Dropout
    mc_forward_passes: int = 30
    mc_dropout_rate: float = 0.2

    # Thresholds
    confidence_warn_threshold: float = 0.65
    entropy_warn_threshold: float = 1.5
    ece_warn_threshold: float = 0.10

    # Evaluation bins
    n_bins: int = 15

    # Output
    save_reliability_diagram: bool = True
    temperature_path: Optional[Path] = None
    output_dir: Optional[Path] = None

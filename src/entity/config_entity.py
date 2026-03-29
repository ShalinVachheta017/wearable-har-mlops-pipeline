"""
Configuration entities for HAR MLOps Production Pipeline.

Each pipeline stage gets a dataclass config.  The ProductionPipeline reads
these at init, and each Component receives only the config it needs.

Inspired by: vikashishere/YT-MLops-Proj1 (see docs/thesis/production refrencxe/)

Stages:
     1  Data Ingestion         (Excel/CSV → fused CSV)
     2  Data Validation        (schema + range checks)
     3  Data Transformation    (CSV → windowed .npy)
     4  Model Inference        (.npy + model → predictions)
     5  Model Evaluation       (confidence / distribution / ECE)
     6  Post-Inference Monitoring (3-layer: confidence, temporal, drift)
     7  Trigger Evaluation     (retraining decision)
     8  Model Retraining       (unsupervised / supervised, AdaBN)
     9  Model Registration     (version, deploy, rollback)
    10  Baseline Update        (rebuild drift baselines)
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

TIMESTAMP: str = datetime.now().strftime("%Y%m%d_%H%M%S")


# ============================================================================
# Master Pipeline Config
# ============================================================================


@dataclass
class PipelineConfig:
    """Top-level pipeline settings shared by all stages."""

    pipeline_name: str = "har_mental_health_pipeline"
    artifact_dir: str = os.path.join("artifacts", TIMESTAMP)
    timestamp: str = TIMESTAMP

    # Paths — sensible defaults, override via run_pipeline.py CLI
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    data_raw_dir: Path = field(default=None)
    data_processed_dir: Path = field(default=None)
    data_prepared_dir: Path = field(default=None)
    models_dir: Path = field(default=None)
    models_pretrained_dir: Path = field(default=None)
    outputs_dir: Path = field(default=None)
    logs_dir: Path = field(default=None)
    scripts_dir: Path = field(default=None)

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
            self.scripts_dir = self.project_root / "scripts"


# ============================================================================
# Stage 1 – Data Ingestion
# ============================================================================


@dataclass
class DataIngestionConfig:
    """Configuration for raw-sensor-data ingestion (Excel/CSV → fused CSV)."""

    accel_file: Optional[Path] = None  # auto-detect if None
    gyro_file: Optional[Path] = None  # auto-detect if None
    input_csv: Optional[Path] = None  # direct CSV (your own recording)
    target_hz: int = 50
    merge_tolerance_ms: int = 1
    output_dir: Optional[Path] = None


# ============================================================================
# Stage 2 – Data Validation
# ============================================================================


@dataclass
class DataValidationConfig:
    """Configuration for data validation."""

    sensor_columns: List[str] = field(default_factory=lambda: ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"])
    expected_frequency_hz: float = 50.0
    max_acceleration_ms2: float = 50.0
    max_gyroscope_dps: float = 500.0
    max_missing_ratio: float = 0.05


# ============================================================================
# Stage 3 – Data Transformation (Preprocessing)
# ============================================================================


@dataclass
class DataTransformationConfig:
    """Configuration for preprocessing (CSV → windowed .npy arrays)."""

    input_csv: Optional[Path] = None
    enable_unit_conversion: bool = True  # milliG → m/s² (MUST match training)
    enable_gravity_removal: bool = False  # Keep False (training had gravity)
    enable_calibration: bool = False
    window_size: int = 200  # 4 seconds at 50 Hz
    overlap: float = 0.5  # 50 % overlap
    sensors: List[str] = field(default_factory=lambda: ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"])
    output_dir: Optional[Path] = None
    # Normalization variant — MUST match what was used during training:
    #   "zscore"  → StandardScaler with training stats (Variant A, default)
    #   "none"    → no amplitude normalization (Variant B)
    #   "robust"  → RobustScaler with training stats (Variant C)
    enable_normalization: bool = True  # toggle ON/OFF (like enable_gravity_removal)
    normalization_variant: str = "zscore"


# ============================================================================
# Stage 4 – Model Inference
# ============================================================================


@dataclass
class ModelInferenceConfig:
    """Configuration for model inference."""

    model_path: Optional[Path] = None  # defaults to pretrained
    input_npy: Optional[Path] = None  # defaults to prepared/production_X.npy
    batch_size: int = 32
    confidence_threshold: float = 0.50
    mode: str = "batch"  # "batch" or "realtime"
    output_dir: Optional[Path] = None


# ============================================================================
# Stage 5 – Model Evaluation
# ============================================================================


@dataclass
class ModelEvaluationConfig:
    """Configuration for prediction evaluation."""

    predictions_csv: Optional[Path] = None
    labels_path: Optional[Path] = None  # optional — unlabeled is fine
    output_dir: Optional[Path] = None
    confidence_bins: int = 10


# ============================================================================
# Stage 6 – Post-Inference Monitoring
# ============================================================================


@dataclass
class PostInferenceMonitoringConfig:
    """Configuration for post-inference monitoring (3-layer)."""

    predictions_csv: Optional[Path] = None
    production_data_npy: Optional[Path] = None
    baseline_stats_json: Optional[Path] = None
    model_path: Optional[Path] = None
    output_dir: Optional[Path] = None

    # ── Thresholds (single source of truth — also read by src/api/app.py) ──
    # Layer 1 — confidence
    confidence_warn_threshold: float = 0.60  # mean confidence below this → WARNING
    uncertain_pct_threshold: float = 30.0  # % of low-confidence windows → WARNING
    uncertain_window_threshold: float = 0.50  # per-window cutoff: max_prob < this → "uncertain"
    # Layer 2 — temporal
    transition_rate_threshold: float = 50.0  # % transition rate above this → WARNING
    # Layer 3 — drift
    drift_zscore_threshold: float = 2.0  # per-channel z-score above this → WARNING

    # Temperature-scaling calibration (applied before Layer 1/3 analysis)
    # Set to the temperature T from Stage 11 (CalibrationUncertainty) output;
    # 1.0 means no rescaling.
    calibration_temperature: float = 1.0

    # Baseline quality guard
    max_baseline_age_days: int = 90  # warn if baseline file is older than this

    # Drift exclusion: skip Layer 3 when production data IS the training data
    # (self-comparison would give artificially low drift scores).
    is_training_session: bool = False


# ============================================================================
# Stage 7 – Trigger Evaluation
# ============================================================================


@dataclass
class TriggerEvaluationConfig:
    """Configuration for retraining-trigger evaluation."""

    confidence_warn: float = 0.65
    confidence_critical: float = 0.50
    # Drift metric is a z-score of mean-shift per channel, NOT PSI.
    # 2.0σ ≈ 95th percentile (warn), 3.0σ ≈ 99.7th percentile (critical).
    drift_zscore_warn: float = 2.0
    drift_zscore_critical: float = 3.0
    temporal_flip_warn: float = 0.35
    temporal_flip_critical: float = 0.50
    cooldown_hours: int = 24
    state_dir: Optional[Path] = None


# ============================================================================
# Stage 8 – Model Retraining
# ============================================================================


@dataclass
class ModelRetrainingConfig:
    """Configuration for model retraining (including domain adaptation)."""

    # Data paths
    source_data_path: Optional[Path] = None  # labeled training CSV
    target_data_npy: Optional[Path] = None  # unlabeled production .npy
    labels_path: Optional[Path] = None  # user-provided labels (optional)

    # Training hyperparameters
    epochs: int = 100
    batch_size: int = 64
    learning_rate: float = 0.001
    n_folds: int = 5
    skip_cv: bool = False

    # Domain adaptation
    enable_adaptation: bool = False
    adaptation_method: str = "none"  # none | adabn | tent | adabn_tent | pseudo_label
    # NOTE: mmd and dann are NOT implemented.
    adabn_n_batches: int = 10  # batches for AdaBN / TENT steps

    # Output
    output_dir: Optional[Path] = None
    experiment_name: str = "har-retraining"
    run_name: Optional[str] = None


# ============================================================================
# Stage 9 – Model Registration
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
    # When True, block deployment if accuracy metrics are absent (e.g., AdaBN/TENT
    # unsupervised adaptation produces no labeled val_accuracy).
    # Default False preserves current behaviour (register but do NOT auto-deploy).
    block_if_no_metrics: bool = False


# ============================================================================
# Stage 10 – Baseline Update
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
# Stage 11 – Calibration & Uncertainty Quantification
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


# ============================================================================
# Stage 12 – Wasserstein Drift Detection
# ============================================================================


@dataclass
class WassersteinDriftConfig:
    """Configuration for Wasserstein-based distribution drift detection."""

    warn_threshold: float = 0.3
    critical_threshold: float = 0.5
    min_drifted_channels_warn: int = 2
    min_drifted_channels_critical: int = 4

    # Change-point detection
    cpd_window_size: int = 50
    cpd_threshold: float = 2.0

    # Multi-resolution
    enable_multi_resolution: bool = True

    sensor_columns: List[str] = field(default_factory=lambda: ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"])
    baseline_data_path: Optional[Path] = None
    output_dir: Optional[Path] = None


# ============================================================================
# Stage 13 – Curriculum Pseudo-Labeling
# ============================================================================


@dataclass
class CurriculumPseudoLabelingConfig:
    """Configuration for curriculum-style self-training."""

    initial_confidence_threshold: float = 0.95
    final_confidence_threshold: float = 0.80
    n_iterations: int = 5
    threshold_decay: str = "linear"  # linear or exponential

    max_samples_per_class: int = 20
    min_samples_per_class: int = 3

    use_teacher_student: bool = True
    ema_decay: float = 0.999

    # EWC regularization
    use_ewc: bool = True
    ewc_lambda: float = 1000.0
    ewc_n_samples: int = 200

    epochs_per_iteration: int = 10
    batch_size: int = 64
    learning_rate: float = 0.0005

    source_data_path: Optional[Path] = None
    unlabeled_data_path: Optional[Path] = None
    output_dir: Optional[Path] = None


# ============================================================================
# Stage 14 – Sensor Placement Robustness
# ============================================================================


@dataclass
class SensorPlacementConfig:
    """Configuration for sensor placement robustness (hand detection, mirroring)."""

    mirror_axes: List[int] = field(default_factory=lambda: [1, 2, 4, 5])
    mirror_probability: float = 0.5
    dominant_accel_threshold: float = 1.2

    sensor_columns: List[str] = field(default_factory=lambda: ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"])
    accel_indices: List[int] = field(default_factory=lambda: [0, 1, 2])
    gyro_indices: List[int] = field(default_factory=lambda: [3, 4, 5])
    output_dir: Optional[Path] = None

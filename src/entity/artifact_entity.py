"""
Artifact entities for HAR MLOps Production Pipeline.

Each pipeline component produces an artifact dataclass that is passed to the
next component.  This makes the data flow explicit and traceable.

Stages 1-7  : inference-cycle artifacts
Stages 8-10 : retraining-cycle artifacts
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# Stage 1 – Data Ingestion
# ============================================================================


@dataclass
class DataIngestionArtifact:
    """Output of sensor-data ingestion (Excel/CSV → fused CSV)."""

    fused_csv_path: Path
    n_rows: int
    n_columns: int
    sampling_hz: int
    ingestion_timestamp: str
    source_type: str = "unknown"
    source_path: Optional[Path] = None
    has_labels: bool = False
    label_column: Optional[str] = None


# ============================================================================
# Stage 2 – Data Validation
# ============================================================================


@dataclass
class DataValidationArtifact:
    """Output of data validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)


# ============================================================================
# Stage 3 – Data Transformation
# ============================================================================


@dataclass
class DataTransformationArtifact:
    """Output of preprocessing (CSV → windowed .npy)."""

    production_X_path: Path
    metadata_path: Path
    n_windows: int
    window_size: int
    unit_conversion_applied: bool
    preprocessing_timestamp: str
    transformation_report_path: Optional[Path] = None
    channel_order: List[str] = field(default_factory=list)
    has_labels: bool = False
    normalization_applied: bool = False
    scaler_path: Optional[Path] = None
    unit_conversion_factor: Optional[float] = None
    model_input_space: str = ""
    gravity_removal_applied: bool = False
    calibration_applied: bool = False
    production_y_path: Optional[Path] = None  # BUG-2 fix: set when label column present


# ============================================================================
# Stage 4 – Model Inference
# ============================================================================


@dataclass
class ModelInferenceArtifact:
    """Output of model inference."""

    predictions_csv_path: Path
    predictions_npy_path: Path
    probabilities_npy_path: Optional[Path] = None
    metadata_json_path: Optional[Path] = None
    inference_report_path: Optional[Path] = None
    n_predictions: int = 0
    inference_time_seconds: float = 0.0
    model_version: str = ""
    active_model_path: Optional[Path] = None  # full path of model used — fed to MLflow registration
    model_md5: str = ""
    activity_distribution: Dict = field(default_factory=dict)
    confidence_stats: Dict = field(default_factory=dict)
    entropy_stats: Dict = field(default_factory=dict)
    top2_margin_stats: Dict = field(default_factory=dict)
    dominant_class: Optional[str] = None
    dominant_pct: Optional[float] = None
    collapse_level: str = "NONE"


# ============================================================================
# Stage 5 – Model Evaluation
# ============================================================================


@dataclass
class ModelEvaluationArtifact:
    """Output of prediction evaluation."""

    report_json_path: Optional[Path] = None
    report_text_path: Optional[Path] = None
    distribution_summary: Dict = field(default_factory=dict)
    confidence_summary: Dict = field(default_factory=dict)
    has_labels: bool = False
    classification_metrics: Optional[Dict] = None
    # Informational flag: any single class > 95 % of predictions in this batch.
    # Does NOT trigger retraining — see docs/TRIGGER_POLICY_EXPLANATION.md.
    distribution_dominance_warning: bool = False
    dominant_pct: Optional[float] = None
    dominant_class: Optional[str] = None


# ============================================================================
# Stage 6 – Post-Inference Monitoring
# ============================================================================


@dataclass
class PostInferenceMonitoringArtifact:
    """Output of post-inference monitoring (3-layer)."""

    monitoring_report: Dict = field(default_factory=dict)
    overall_status: str = "UNKNOWN"  # HEALTHY / WARNING / CRITICAL
    layer1_confidence: Dict = field(default_factory=dict)
    layer2_temporal: Dict = field(default_factory=dict)
    layer3_drift: Dict = field(default_factory=dict)
    report_path: Optional[Path] = None


# ============================================================================
# Stage 7 – Trigger Evaluation
# ============================================================================


@dataclass
class TriggerEvaluationArtifact:
    """Output of retraining-trigger evaluation."""

    should_retrain: bool = False
    action: str = "NONE"  # NONE / MONITOR / QUEUE_RETRAIN / TRIGGER_RETRAIN / ROLLBACK
    alert_level: str = "INFO"  # INFO / WARNING / CRITICAL
    reasons: List[str] = field(default_factory=list)
    cooldown_active: bool = False
    # Governance fields — mirrors TriggerDecision governance contract.
    decision: str = "HEALTHY"  # HEALTHY / REVIEW_REQUIRED / DATA_QA_REQUIRED / etc.
    auto_retrain: bool = False  # always False for unlabeled production inference
    review_required: bool = False  # True when human review is required
    label_required: bool = False  # True when label/QA gate must be satisfied
    qa_required: bool = False  # True when data QA is required
    required_next_steps: List[str] = field(default_factory=list)


# ============================================================================
# Stage 8 – Model Retraining
# ============================================================================


@dataclass
class ModelRetrainingArtifact:
    """Output of supervised model retraining."""

    retrained_model_path: Optional[Path] = None
    scaler_config_path: Optional[Path] = None  # new scaler params
    training_report: Dict = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    n_source_samples: int = 0
    retraining_timestamp: str = ""


# ============================================================================
# Stage 9 – Model Registration
# ============================================================================


@dataclass
class ModelRegistrationArtifact:
    """Output of model registration and validation."""

    registered_version: str = ""
    is_deployed: bool = False
    is_better_than_current: bool = False
    proxy_metrics: Dict[str, float] = field(default_factory=dict)
    previous_version: Optional[str] = None
    registry_path: Optional[Path] = None


# ============================================================================
# Stage 10 – Baseline Update
# ============================================================================


@dataclass
class BaselineUpdateArtifact:
    """Output of baseline rebuild."""

    baseline_path: Optional[Path] = None
    normalized_baseline_path: Optional[Path] = None
    n_channels: int = 0
    stats_summary: Dict = field(default_factory=dict)
    update_timestamp: str = ""


# ============================================================================
# Stage 11 – Calibration & Uncertainty Quantification
# ============================================================================


@dataclass
class CalibrationUncertaintyArtifact:
    """Output of calibration and uncertainty quantification."""

    overall_status: str = "UNKNOWN"
    temperature: float = 1.0
    temperature_path: Optional[Path] = None
    ece: float = 0.0
    mce: float = 0.0
    brier_score: float = 0.0
    overconfidence_gap: float = 0.0
    reliability_diagram_path: Optional[Path] = None
    mc_dropout_run: bool = False
    mean_predictive_entropy: float = 0.0
    mean_mutual_information: float = 0.0
    calibration_report: Dict = field(default_factory=dict)
    calibration_warnings: List[str] = field(default_factory=list)


# ============================================================================
# Pipeline Result (aggregated)
# ============================================================================


@dataclass
class PipelineResult:
    """Aggregated result of the full pipeline run."""

    run_id: str = ""
    start_time: str = ""
    end_time: str = ""
    overall_status: str = "UNKNOWN"
    stages_completed: List[str] = field(default_factory=list)
    stages_skipped: List[str] = field(default_factory=list)
    stages_failed: List[str] = field(default_factory=list)
    dataset_has_labels: Optional[bool] = None
    dataset_label_source: Optional[str] = None
    dataset_label_column: Optional[str] = None

    mlflow_tracked: bool = False  # True only when MLflow init succeeded

    # Artifacts from each stage (None = stage did not run)
    ingestion: Optional[DataIngestionArtifact] = None
    validation: Optional[DataValidationArtifact] = None
    transformation: Optional[DataTransformationArtifact] = None
    inference: Optional[ModelInferenceArtifact] = None
    evaluation: Optional[ModelEvaluationArtifact] = None
    monitoring: Optional[PostInferenceMonitoringArtifact] = None
    trigger: Optional[TriggerEvaluationArtifact] = None
    retraining: Optional[ModelRetrainingArtifact] = None
    registration: Optional[ModelRegistrationArtifact] = None
    baseline_update: Optional[BaselineUpdateArtifact] = None
    calibration: Optional["CalibrationUncertaintyArtifact"] = None

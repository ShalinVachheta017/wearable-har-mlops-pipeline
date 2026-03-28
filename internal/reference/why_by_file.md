# File-by-File WHY Cards — HAR MLOps Pipeline
**Generated: 2026-03-03 | Repo: MasterArbeit_MLops (main)**

---

## Master File Table

| # | File | Purpose | WHY Bucket | Test Coverage |
|---|---|---|---|---|
| 1 | run_pipeline.py | CLI entry point — 14-stage orchestration | Reliability | test_pipeline_integration.py |
| 2 | src/pipeline/production_pipeline.py | Pipeline orchestrator class | Reliability / Governance | test_pipeline_integration.py |
| 3 | src/pipeline/inference_pipeline.py | Legacy 7-stage pipeline (alternative) | Maintainability | NONE |
| 4 | src/train.py | Model training + domain adaptation trainer | Reproducibility | test_retraining.py |
| 5 | src/api/app.py | FastAPI inference API + monitoring | Observability | PARTIAL (smoke) |
| 6 | src/mlflow_tracking.py | MLflow experiment tracking wrapper | Reproducibility | NONE |
| 7 | src/trigger_policy.py | 2-of-3 voting trigger + cooldown | Reliability | test_trigger_policy.py |
| 8 | src/model_rollback.py | Model registry + rollback | Governance | test_model_rollback.py |
| 9 | src/prometheus_metrics.py | Prometheus metrics exporter | Observability | test_prometheus_metrics.py |
| 10 | src/data_validator.py | Schema + range validation | Reliability | test_data_validation.py |
| 11 | src/preprocess_data.py | Unit conversion, normalization, windowing | Reproducibility | test_preprocessing.py |
| 12 | src/sensor_data_pipeline.py | Raw Garmin Excel → fused CSV | Reliability | NONE |
| 13 | src/calibration.py | Temperature scaling + MC Dropout | Reliability | test_calibration.py |
| 14 | src/wasserstein_drift.py | Wasserstein-1 drift + change-point | Observability | test_wasserstein_drift.py |
| 15 | src/ood_detection.py | Energy-based OOD detection | Reliability | test_ood_detection.py |
| 16 | src/config.py | Central path + model constants | Maintainability | NONE |
| 17 | src/run_inference.py | Batch inference engine | Reliability | NONE |
| 18 | src/robustness.py | Noise/jitter/saturation robustness eval | Reliability | test_robustness.py |
| 19 | src/deployment_manager.py | Container build + deploy strategies | Scalability/Cost | NONE |
| 20 | src/curriculum_pseudo_labeling.py | Iterative pseudo-label + EWC | Reliability | test_curriculum_pseudo_labeling.py |
| 21 | src/domain_adaptation/adabn.py | AdaBN statistics adaptation | Reliability | test_adabn.py |
| 22 | src/domain_adaptation/tent.py | TENT entropy minimization | Reliability | test_retraining.py |
| 23 | src/entity/config_entity.py | 14 dataclass configs (SoT) | Maintainability | test_threshold_consistency.py |
| 24 | src/entity/artifact_entity.py | 14 artifact dataclasses | Maintainability | NONE |
| 25 | src/utils/config_loader.py | YAML override loader (12-Factor) | Maintainability | test_config_loader.py |
| 26 | src/utils/temporal_metrics.py | Per-session flip rate | Observability | test_temporal_metrics.py |
| 27 | src/utils/artifacts_manager.py | Timestamped artifact directory mgmt | Governance | NONE |
| 28 | src/components/data_ingestion.py | Stage 1 component | Reliability | NONE (P0 gap) |
| 29 | src/components/data_validation.py | Stage 2 component | Reliability | test_data_validation.py |
| 30 | src/components/data_transformation.py | Stage 3 component | Reproducibility | test_preprocessing.py |
| 31 | src/components/model_inference.py | Stage 4 component | Reliability | NONE (P0 gap) |
| 32 | src/components/model_evaluation.py | Stage 5 component | Observability | NONE (P0 gap) |
| 33 | src/components/post_inference_monitoring.py | Stage 6 component | Observability | NONE (P0 gap) |
| 34 | src/components/trigger_evaluation.py | Stage 7 component | Reliability | test_trigger_policy.py |
| 35 | src/components/model_retraining.py | Stage 8 component | Reliability | test_retraining.py |
| 36 | src/components/model_registration.py | Stage 9 component | Governance | test_model_registration_gate.py |
| 37 | src/components/baseline_update.py | Stage 10 component | Governance | test_baseline_update.py |
| 38 | src/components/calibration_uncertainty.py | Stage 11 component | Reliability | test_calibration.py |
| 39 | src/components/wasserstein_drift.py | Stage 12 component | Observability | test_wasserstein_drift.py |
| 40 | src/components/curriculum_pseudo_labeling.py | Stage 13 component | Reliability | test_curriculum_pseudo_labeling.py |
| 41 | src/components/sensor_placement.py | Stage 14 component | Reliability | test_sensor_placement.py |
| 42 | config/pipeline_config.yaml | Preprocessing toggles (YAML) | Reproducibility | NONE |
| 43 | config/pipeline_overrides.yaml | Runtime threshold overrides | Maintainability | NONE |
| 44 | config/monitoring_thresholds.yaml | Threshold audit reference | Governance | test_threshold_consistency.py |
| 45 | config/prometheus.yml | Prometheus scrape config | Observability | verify_prometheus_metrics.py |
| 46 | config/alertmanager.yml | Alert routing + inhibition | Observability | NONE |
| 47 | config/alerts/har_alerts.yml | Prometheus alert rules | Observability | verify_prometheus_metrics.py |
| 48 | config/mlflow_config.yaml | MLflow experiment config | Reproducibility | NONE |
| 49 | config/grafana/datasources/datasource-prometheus.yaml | Grafana → Prometheus link | Observability | NONE |
| 50 | config/grafana/dashboards/dashboard-provider.yaml | Dashboard auto-provisioning | Observability | NONE |
| 51 | docker/Dockerfile.inference | Inference container image | Reproducibility | CI build job |
| 52 | docker/Dockerfile.training | Training container image | Reproducibility | NONE |
| 53 | docker-compose.yml | Service orchestration (7 services) | Reproducibility | CI integration-test |
| 54 | .github/workflows/ci-cd.yml | CI/CD pipeline (6 jobs) | Reliability | N/A (is the test) |
| 55 | .dvc/config | DVC remote storage config | Reproducibility | dvc status |

---

## Per-File WHY Cards

---

### Card 1: run_pipeline.py (545 lines)

**Purpose**: Single CLI entry point for the entire 14-stage production pipeline.

**Why this file exists**: Without a unified entry point, operators must chain 14 separate scripts manually, risking stage ordering errors, missing artifact handoffs, and inconsistent config. This file ensures a reproducible, auditable pipeline run with one command.

**Key design decisions**:
- CLI arg parsing with argparse (lines 70–200): stages, preprocessing toggles, adaptation method, governance flags (`--auto-deploy`, `--update-baseline`).
- YAML config loading with CLI override precedence (lines 330–370): `load_preprocessing_config()` loads from pipeline_config.yaml, CLI flags override.
- GPU detection with TF memory growth (lines 290–320): `_detect_gpu()` enables GPU memory growth to prevent OOM on Windows.
- Config composition (lines 380–430): Builds 14 config dataclasses, applies YAML overrides via `apply_overrides()`.
- Structured summary output (lines 460–540): `_print_pipeline_summary()` with Unicode-safe printing.

**Evidence type per decision**:
| Decision | Evidence |
|---|---|
| Single entry point | PROJECT_DECISION |
| CLI override precedence | OFFICIAL_DOC [REF_12FACTOR_CONFIG] |
| GPU memory growth | OFFICIAL_DOC [REF_TF_GPU_WSL] |

**Referenced from**: Docker CMD (`docker/Dockerfile.training`), CI model-validation job (`.github/workflows/ci-cd.yml:315`).

**How to verify**: `python run_pipeline.py --help` | `python run_pipeline.py --stages inference evaluation`

---

### Card 2: src/pipeline/production_pipeline.py (967 lines)

**Purpose**: Orchestrate all 14 pipeline stages with lazy imports, artifact handoff, and MLflow lifecycle.

**Why this file exists**: Centralizes stage sequencing, error handling (`continue_on_failure`), and governance (which stages run by default vs. opt-in). Without it, stage dependencies are implicit and artifact passing is manual.

**Key design decisions**:
- Stage list as constant `ALL_STAGES` (line 54): Defines canonical execution order.
- Lazy imports per stage (throughout `run()`): Avoids importing TensorFlow until needed — saves ~10s startup for non-TF stages.
- Fallback artifacts when stages are skipped (lines 665–730): `_make_fallback_ingestion_artifact()`, `_make_fallback_transformation_artifact()` create synthetic artifacts from expected file paths.
- MLflow lifecycle (lines 800–950): `_init_mlflow()` opens run, `_log_stage_to_mlflow()` logs per-stage metrics, `_end_mlflow()` closes.
- `continue_on_failure` flag (line 113): When True, logs errors and continues to next stage instead of aborting.

**Evidence type per decision**:
| Decision | Evidence |
|---|---|
| 14-stage decomposition | PROJECT_DECISION + [REF_GOOGLE_MLOPS] |
| Lazy imports | PROJECT_DECISION (startup performance) |
| Fallback artifacts | PROJECT_DECISION (skip-ingestion UX) |

**Referenced from**: run_pipeline.py:main() (line 430).

**How to verify**: `python run_pipeline.py` | `pytest tests/test_pipeline_integration.py -v`

---

### Card 3: src/train.py (1345 lines)

**Purpose**: Define model architecture, training loop, cross-validation, and domain adaptation strategies.

**Why this file exists**: Encapsulates the complete training contract — architecture, hyperparameters, data loading, training, and evaluation — so that both initial training and retraining use identical code paths, preventing training–inference parity drift.

**Key design decisions**:
- `TrainingConfig` dataclass (lines 82–130): window_size=200, step_size=100, n_sensors=6, n_classes=11, epochs=100, batch_size=64, lr=0.001, dropout=[0.1, 0.2, 0.2, 0.5], early_stopping_patience=15.
- `HARModelBuilder._build_v1()` (lines 260–320): 3×Conv1D(64/128/256) + BiLSTM(128) + Dense(256→11) with BatchNormalization + Dropout.
- 5-fold stratified CV (lines 380–450): `HARTrainer.run_cross_validation()` with `StratifiedKFold`.
- `DomainAdaptationTrainer` (lines 720–1200): Extends HARTrainer with `retrain_with_adaptation()` supporting adabn/tent/pseudo_label. Pseudo-labeling uses conf_threshold=0.70.
- Scaler factory (line 137): `_make_scaler()` → StandardScaler (zscore) or RobustScaler.

**Evidence type per decision**:
| Decision | Evidence |
|---|---|
| 1D-CNN-BiLSTM architecture | PAPER [REF_PAPER_CNN_BILSTM] |
| window_size=200 | EMPIRICAL_CALIBRATION (reports/ABLATION_WINDOWING.csv) + MENTOR_DECISION |
| 5-fold stratified CV | PAPER (standard ML practice) |
| dropout rates [0.1,0.2,0.2,0.5] | PROJECT_DECISION — no ablation artifact |
| pseudo-label threshold 0.70 | EMPIRICAL_CALIBRATION — needs calibration artifact (P0 gap) |

**Referenced from**: src/components/model_retraining.py, src/pipeline/production_pipeline.py.

**How to verify**: `pytest tests/test_retraining.py -v` | `python src/train.py --help`

---

### Card 4: src/api/app.py (892 lines)

**Purpose**: FastAPI REST API for inference, real-time monitoring, and Prometheus metrics export.

**Why this file exists**: The API is the production interface — it receives sensor data uploads, runs inference, executes inline 3-layer monitoring, exports Prometheus metrics, and serves a debugging dashboard. Without it, the pipeline is batch-only.

**Key design decisions**:
- Inline 3-layer monitoring on every upload (lines 220–300): `_run_monitoring()` computes confidence, flip rate, and drift z-score per request.
- 7 Prometheus metrics (lines 40–76): Counter, Gauges, and Histogram covering model health, drift, and latency.
- Monitoring thresholds hardcoded with config fallback (lines 80–90): confidence_warn=0.60, drift_zscore=2.0, etc.
- Embedded HTML dashboard (lines 500–890): ~400 lines of inline HTML/CSS/JS for debugging — no separate frontend build step.
- Model and baseline loaded on startup (lines 110–140): `_load_model()`, `_load_baseline()`.

**Evidence type per decision**:
| Decision | Evidence |
|---|---|
| FastAPI choice | OFFICIAL_DOC [REF_FASTAPI] |
| Prometheus metrics | OFFICIAL_DOC [REF_PROM_OVERVIEW] |
| Inline monitoring | PROJECT_DECISION |
| Embedded HTML | PROJECT_DECISION (thesis demo simplicity) |

**Referenced from**: docker/Dockerfile.inference CMD, docker-compose.yml inference service.

**How to verify**: `uvicorn src.api.app:app --port 8000` | `curl http://localhost:8000/api/health` | `curl http://localhost:8000/metrics`

---

### Card 5: src/mlflow_tracking.py (643 lines)

**Purpose**: Wrapper around MLflow API for experiment tracking, artifact logging, and model comparison.

**Why this file exists**: Raw MLflow API calls are verbose and error-prone. This wrapper provides: (a) context-manager run lifecycle, (b) safe artifact logging with error handling, (c) Keras model registration with API version compatibility (≥2.9 change), (d) run comparison utilities.

**Key design decisions**:
- Context manager pattern (line 80): `start_run()` as context manager ensures runs are always closed.
- MLflow ≥2.9 API compatibility (line 220): `log_keras_model()` handles breaking API change.
- Config from YAML (loaded from config/mlflow_config.yaml): experiment name, model name, default tags.
- `get_best_run()` (line 400): Finds best run by metric for model comparison.
- `quick_log_run()` (line 580): One-shot logging convenience for scripts.

**Evidence type**: OFFICIAL_DOC [REF_MLFLOW_TRACKING], [REF_MLFLOW_KERAS].

**Referenced from**: src/pipeline/production_pipeline.py, src/train.py, src/run_inference.py.

**How to verify**: `python -c "from src.mlflow_tracking import MLflowTracker; t = MLflowTracker(); print(t)"`

---

### Card 6: src/trigger_policy.py (830 lines)

**Purpose**: Multi-signal retraining trigger with 2-of-3 voting and cooldown to prevent alert fatigue and over-retraining.

**Why this file exists**: Single-signal triggers (e.g., confidence alone) have 13.9% false alarm rate (reports/TRIGGER_POLICY_EVAL.csv). The 2-of-3 voting scheme reduces this to 0.7% while maintaining 100% episode recall.

**Key design decisions**:
- 2-of-3 consensus (line 470): `_aggregate_signals()` requires at least 2 of {confidence, temporal, drift} to agree before triggering retraining.
- Tiered alert levels (lines 30–40): INFO → WARNING → CRITICAL with escalation via `consecutive_warnings_for_trigger=3`.
- Cooldown gate (line 520): `_apply_cooldowns()` with `retrain_cooldown_hours=24` suppresses repeated triggers during single drift episode.
- `TriggerThresholds` dataclass (lines 92–130): confidence_warn=0.55, entropy_warn=1.8, flip_rate_warn=0.25, drift_zscore_warn=2.0.
- `ProxyModelValidator` (lines 665–790): Compares old/new models without labels — improvement_threshold=0.05, requires 2/3 metric improvements.

**Evidence type per decision**:
| Decision | Evidence |
|---|---|
| 2-of-3 voting | EMPIRICAL_CALIBRATION (reports/TRIGGER_POLICY_EVAL.csv) |
| 24h cooldown | EMPIRICAL_CALIBRATION (reports/TRIGGER_POLICY_EVAL.md) |
| Threshold values | EMPIRICAL_CALIBRATION (reports/THRESHOLD_CALIBRATION.csv) |

**Referenced from**: src/components/trigger_evaluation.py.

**How to verify**: `pytest tests/test_trigger_policy.py -v` | `python scripts/trigger_policy_eval.py`

---

### Card 7: src/model_rollback.py (531 lines)

**Purpose**: File-based model registry with versioning, deployment, and rollback capabilities.

**Why this file exists**: MLflow model registry provides cloud-grade model management, but this file provides a local, zero-dependency fallback that works offline and enables fast rollback without MLflow server availability.

**Key design decisions**:
- SHA256 model hashing (line 100): `register_model()` computes hash for integrity verification.
- JSON-based registry state (line 75): Persistent state in `models/registry/registry.json`.
- `RollbackValidator` (lines 325–420): Validates model file loadability, output shape (1,11), probability sum ≈ 1.0 before deployment.
- Deployment history tracking (line 300): `get_deployment_history()` returns ordered list for audit.

**Evidence type**: PROJECT_DECISION (local-first governance).

**Referenced from**: src/components/model_registration.py.

**How to verify**: `pytest tests/test_model_rollback.py -v`

---

### Card 8: src/prometheus_metrics.py (584 lines)

**Purpose**: Define, collect, and export pipeline metrics in Prometheus text format.

**Why this file exists**: Prometheus scrapes metrics via HTTP. This module defines the canonical metric schema (16 metrics), provides thread-safe recording, and exports in Prometheus text exposition format.

**Key design decisions**:
- Singleton pattern (line 200): `MetricsExporter` is a singleton to prevent metric duplication.
- 16 metric definitions (lines 55–140): Covers model performance, drift, proxy validation, OOD, trigger state, and system metrics.
- Thread-safe `MetricValue` (line 145): `inc()`, `set()`, `observe()` with locking.
- Prometheus text format export (line 400): `export_prometheus()` generates scrape-compatible output.

**Evidence type**: OFFICIAL_DOC [REF_PROM_OVERVIEW].

**Referenced from**: src/api/app.py (`/metrics` endpoint).

**How to verify**: `pytest tests/test_prometheus_metrics.py -v` | `python scripts/verify_prometheus_metrics.py --offline`

---

### Card 9: src/data_validator.py (230 lines)

**Purpose**: Validate sensor data schema, value ranges, and missing data ratio before pipeline processing.

**Why this file exists**: Invalid sensor data (wrong columns, extreme values, excessive NaNs) silently corrupts downstream windowing and inference. This guard gate catches data quality issues early.

**Key design decisions**:
- Expected columns: ["Ax","Ay","Az","Gx","Gy","Gz"] (line 40).
- Range checks: max_acceleration=50.0 m/s², max_gyroscope=500.0 deg/s (line 50).
- Missing ratio: max_missing_ratio=0.05 (5%) (line 50).
- Sampling rate tolerance: 10% of expected 50 Hz (line 50).
- `validate_and_raise()` (line 180): Hard-fail alternative to soft `validate()`.

**Evidence type**: SENSOR_SPEC (Garmin IMU full-scale: ±8g = 78.4 m/s², ±2000 dps. Pipeline limits are conservative subset).

**Referenced from**: src/components/data_validation.py.

**How to verify**: `pytest tests/test_data_validation.py -v`

---

### Card 10: src/preprocess_data.py (855 lines)

**Purpose**: Unified preprocessing: unit conversion, gravity removal, normalization, and sliding-window creation.

**Why this file exists**: Training–inference parity requires identical preprocessing. This module is the single source of truth for all preprocessing transforms, used by both training (src/train.py) and inference (src/components/data_transformation.py).

**Key design decisions**:
- `UnitDetector` (line 60): CONVERSION_FACTOR=0.00981 (milliG→m/s²). Auto-detects units from range analysis.
- `GravityRemover` (line 150): Butterworth high-pass at cutoff_hz=0.3, order=3, sampling_freq=50.0.
- `DomainCalibrator` (line 230): training_mean=[3.22, 1.28, -3.53, 0.60, 0.23, 0.09] for mean-shift calibration.
- `UnifiedPreprocessor.create_windows()` (line 320): Vectorized with `np.lib.stride_tricks` for O(1) memory windowing.
- Normalization variants: zscore → StandardScaler, robust → RobustScaler, none.

**Evidence type per decision**:
| Decision | Evidence |
|---|---|
| milliG→m/s² conversion | SENSOR_SPEC (Garmin IMU units) |
| Gravity removal disabled | PROJECT_DECISION (training used gravity-included data) |
| Butterworth cutoff 0.3 Hz | PAPER [REF_UCI_HAR] |
| Vectorized windowing | PROJECT_DECISION (performance) |

**Referenced from**: src/components/data_transformation.py, src/train.py.

**How to verify**: `pytest tests/test_preprocessing.py -v`

---

### Card 11: src/sensor_data_pipeline.py (1192 lines)

**Purpose**: Convert raw Garmin accelerometer + gyroscope Excel exports into time-aligned, resampled 50 Hz CSV.

**Why this file exists**: Garmin SDK exports data as Excel files with nested list cells. This pipeline handles parsing, exploding, timestamp alignment, sensor fusion (merge_asof), and resampling — steps too complex for inline preprocessing.

**Key design decisions**:
- `SensorFusion.merge_sensor_data()` (line 510): `pd.merge_asof` with tolerance=1ms for time alignment.
- `Resampler.resample_data()` (line 650): scipy.interpolate linear interpolation to exact 50 Hz.
- 11-step pipeline (line 970): load → normalize → validate → parse → filter → explode → timestamp → merge → resample → (optional gravity removal) → export.
- Metadata JSON output (line 920): Saves processing parameters alongside CSV for reproducibility.

**Evidence type**: PROJECT_DECISION (Garmin SDK data format requirements).

**Referenced from**: src/components/data_ingestion.py.

**How to verify**: `python src/sensor_data_pipeline.py --help`

---

### Card 12: src/calibration.py (547 lines)

**Purpose**: Post-hoc model calibration (temperature scaling) and uncertainty quantification (MC Dropout).

**Why this file exists**: Softmax outputs are not calibrated probabilities. Temperature scaling (Guo et al. 2017) corrects overconfidence; MC Dropout (Gal & Ghahramani 2016) provides epistemic uncertainty estimates for OOD detection.

**Key design decisions**:
- Temperature T fit via NLL minimization (line 70): `scipy.optimize.minimize` with L-BFGS-B.
- MC Dropout: 30 forward passes (line 170): Balance between estimate quality and compute cost.
- 15 bins for ECE (line 260): Standard calibration evaluation resolution.
- Unlabeled proxy calibration (line 380): Analyzes confidence/entropy distributions without ground truth.

**Evidence type**: PAPER [REF_TEMP_SCALING], [REF_MC_DROPOUT].

**Referenced from**: src/components/calibration_uncertainty.py.

**How to verify**: `pytest tests/test_calibration.py -v`

---

### Card 13: src/wasserstein_drift.py (~470 lines)

**Purpose**: Per-channel Wasserstein-1 distance for distribution drift detection with change-point detection.

**Why this file exists**: Z-score drift (Stage 6 Layer 3) detects mean shift but misses distributional changes. Wasserstein-1 captures full distribution differences. Multi-resolution analysis (window/hourly/daily) identifies drift onset timing.

**Key design decisions**:
- Integrated drift report (line 340): `compute_integrated_drift_report()` combines PSI + KS + Wasserstein with 2-of-3 consensus.
- Consensus thresholds (line 420): wasserstein>0.3, ks_pvalue<0.01, psi>0.10.
- Change-point detection (line 160): Rolling z-score CPD with window=50, threshold=2.0.
- Multi-resolution (line 240): Window-level, hourly, daily aggregation.

**Evidence type**: PAPER [REF_WASSERSTEIN], EMPIRICAL_CALIBRATION (consensus thresholds).

**Referenced from**: src/components/wasserstein_drift.py.

**How to verify**: `pytest tests/test_wasserstein_drift.py -v`

---

### Card 14: src/entity/config_entity.py (~310 lines)

**Purpose**: Single source of truth for all pipeline stage configuration via Python dataclasses.

**Why this file exists**: Thresholds and parameters defined in scattered locations lead to inconsistency bugs. Centralizing all 14 stage configs as typed dataclasses with documented defaults enables: (a) YAML override, (b) threshold consistency tests, (c) defense audit.

**Key design decisions**:
- 14 `@dataclass` configs — one per pipeline stage.
- Default values documented with rationale comments.
- `PostInferenceMonitoringConfig` (line 143): All monitoring thresholds.
- `TriggerEvaluationConfig` (line 200): Intentionally higher thresholds than monitoring (tiered alerting).
- `ModelRegistrationConfig` (line 245): `degradation_tolerance=0.005`, `block_if_no_metrics=False`.

**Evidence type**: PROJECT_DECISION + OFFICIAL_DOC [REF_12FACTOR_CONFIG].

**Referenced from**: run_pipeline.py, src/utils/config_loader.py, src/pipeline/production_pipeline.py.

**How to verify**: `pytest tests/test_threshold_consistency.py -v`

---

### Card 15: src/utils/config_loader.py (~115 lines)

**Purpose**: Load YAML config overrides and apply them to dataclass instances at runtime.

**Why this file exists**: Implements 12-Factor App Factor III (config from environment). Operators can change thresholds without modifying Python source code. Supports env var `HAR_PIPELINE_OVERRIDES` for Docker/CI injection.

**Key design decisions**:
- `load_yaml_overrides()`: Reads from explicit path, env var, or default `config/pipeline_overrides.yaml`.
- `apply_overrides()`: Flat dict → dataclass field assignment, silently ignores unknown keys.
- `load_monitoring_config()` / `load_trigger_config()`: Factory functions with override support.

**Evidence type**: OFFICIAL_DOC [REF_12FACTOR_CONFIG].

**Referenced from**: run_pipeline.py:420–430.

**How to verify**: `pytest tests/test_config_loader.py -v`

---

### Card 16: src/domain_adaptation/adabn.py (~165 lines)

**Purpose**: Adapt BatchNormalization statistics to target domain without gradient updates.

**Why this file exists**: Production data distribution differs from training data (different users, sensor placement). AdaBN re-estimates BN running mean/var from target data — fast, gradient-free, and preserves model weights.

**Key design decisions**:
- `adapt_bn_statistics()` (line 55): Resets BN stats → forward pass `n_batches` → restore trainable flags.
- `adabn_score_confidence()` (line 140): Proxy validation — mean/median/min/std confidence + low_confidence_ratio.
- Reference: Li et al. 2018, arXiv:1603.04779.

**Evidence type**: PAPER [REF_ADABN_PAPER].

**Referenced from**: src/components/model_retraining.py:100.

**How to verify**: `pytest tests/test_adabn.py -v`

---

### Card 17: src/domain_adaptation/tent.py (~280 lines)

**Purpose**: Fine-tune BN affine parameters (gamma/beta) via entropy minimization at test time.

**Why this file exists**: AdaBN adapts statistics but not affine parameters. TENT provides an additional adaptation layer by minimizing prediction entropy — useful when distribution shift is large enough that statistics alone are insufficient.

**Key design decisions**:
- `tent_adapt()` (line 50): Optimizes BN gamma/beta via entropy loss.
- OOD guard (line ~50): Skips adaptation if mean entropy > 0.85 (out-of-distribution data would corrupt BN params).
- Two-gate rollback (line ~120): Rolls back if (a) entropy increases above `rollback_threshold=0.05`, OR (b) confidence drops below `confidence_drop_threshold=0.01`.
- BN running stats restoration per step: Preserves AdaBN calibration when used in two-stage pipeline.

**Evidence type**: PAPER [REF_TENT_PAPER].

**Referenced from**: src/components/model_retraining.py:160, :230.

**How to verify**: `pytest tests/test_retraining.py -v -k tent`

---

### Card 18: config/pipeline_config.yaml (83 lines)

**Purpose**: YAML configuration for preprocessing toggles with inline rationale.

**Why this file exists**: Preprocessing must match training exactly. This file documents the training pipeline's preprocessing decisions (from the thesis reference paper) and provides toggleable flags.

**Key design decisions**:
- `enable_unit_conversion: true` — Garmin outputs milliG, training data is m/s².
- `enable_gravity_removal: false` — Training data included gravity; toggling creates distribution shift.
- `enable_calibration: false` — Not part of original training.
- `sampling_frequency_hz: 50` — Garmin SDK default.
- `window_size: 200`, `window_overlap: 0.5` — 4s window at 50 Hz.

**Evidence type**: PAPER [REF_PAPER_CNN_BILSTM] + PROJECT_DECISION (supervisor requirement).

**Referenced from**: run_pipeline.py:330.

**How to verify**: Read comments inline — each toggle has WHY documentation.

---

### Card 19: config/alerts/har_alerts.yml (140 lines)

**Purpose**: Prometheus alerting rules with threshold alignment to Python config.

**Why this file exists**: Alerts must fire at thresholds consistent with the trigger policy code. This file defines 7 alert rules across 4 groups, with comments documenting which config_entity.py dataclass each threshold aligns to.

**Key design decisions**:
- Threshold alignment comments (lines 1–30): Documents which Python config field each Prometheus threshold maps to.
- `HARLowConfidence < 0.65 for 5m` — aligned with `TriggerEvaluationConfig.confidence_warn`.
- `HARHighEntropy > 1.8 for 5m` — aligned with `TriggerThresholds.entropy_warn`.
- `HARStaleDriftBaseline > 90 days` — aligned with `PostInferenceMonitoringConfig.max_baseline_age_days`.
- Inhibition: HARNoPredictions suppresses all warnings; HARMissingDriftBaseline suppresses stale warning.

**Evidence type**: EMPIRICAL_CALIBRATION (reports/THRESHOLD_CALIBRATION.csv) + PROJECT_DECISION (alignment discipline).

**Referenced from**: config/prometheus.yml rule_files.

**How to verify**: `python scripts/verify_prometheus_metrics.py --offline` | `pytest tests/test_threshold_consistency.py -v`

---

### Card 20: .github/workflows/ci-cd.yml (350 lines)

**Purpose**: GitHub Actions CI/CD with lint, test, build, integration-test, and scheduled model validation.

**Why this file exists**: Prevents broken code from reaching main branch. Automates Docker image builds, smoke tests against the live container, and weekly model health checks.

**Key design decisions**:
- Path filters (line 22): Only triggers on src/, tests/, docker/, config/ changes — avoids CI runs for docs-only changes.
- Test-slow `continue-on-error: true` (line 118): TF install flakiness should not block PRs.
- Docker build cache (`cache-from: type=gha`) (line 210): GitHub Actions cache reduces build time.
- Weekly model validation (line 280): Scheduled cron job (`0 6 * * 1`) runs `dvc pull` + pytest + drift check.
- Integration test pulls and runs the just-built Docker image (line 224): End-to-end smoke test.

**Evidence type**: OFFICIAL_DOC [REF_GHA_WORKFLOWS], [REF_DOCKER_BUILD_PUSH].

**Referenced from**: N/A (triggered by GitHub).

**How to verify**: Push to develop branch and observe CI run in GitHub Actions tab.

---

### Card 21: docker-compose.yml (223 lines)

**Purpose**: Orchestrate 7 services (MLflow, inference, training, preprocessing, Prometheus, Alertmanager, Grafana) with networking and volumes.

**Why this file exists**: Running 7 services manually is error-prone. Compose ensures consistent networking (bridge), volume mounting, dependency ordering, and health checks.

**Key design decisions**:
- Profiles for on-demand services (line 99, 119): `training` and `preprocessing` do not start by default.
- Health checks on all long-running services (lines 47, 74, 168): Ensures compose reports actual readiness.
- 15-day Prometheus retention (line 144): Covers ~2 sprint cycles of drift history.
- Named volumes (line 208): Persist data across `docker compose down/up` cycles.
- Single bridge network (line 203): All services communicate without port exposure to host (except mapped ports).

**Evidence type**: OFFICIAL_DOC [REF_DOCKER_COMPOSE].

**Referenced from**: CI integration-test job (.github/workflows/ci-cd.yml:252).

**How to verify**: `docker compose config` | `docker compose up -d` | `docker compose ps`

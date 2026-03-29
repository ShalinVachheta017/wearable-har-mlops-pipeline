# External Review File Report

Generated from workspace scan. Total documented files: 65

---
## FILE: .github/workflows/cd.yml
**Purpose:** CI/CD workflow configuration for validation, testing, and deployment automation.
**Stage:** utility
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: .github/workflows/ci.yml
**Purpose:** CI/CD workflow configuration for validation, testing, and deployment automation.
**Stage:** utility
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- config/requirements.txt
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: config/pipeline_config.yaml
**Purpose:** Main runtime configuration file used by pipeline stages and wrappers.
**Stage:** config
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- logs/preprocessing
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: docker-compose.yml
**Purpose:** Container orchestration definition for MLflow and inference/training/preprocessing services.
**Stage:** config
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- /app/config/pipeline_config.yaml
- /app/models/pretrained/fine_tuned_model_1dcnnbilstm.keras
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: run_pipeline.py
**Purpose:** Primary CLI entrypoint that orchestrates stage selection and executes the production pipeline.
**Stage:** utility
**Key functions/classes:**
- `parse_args` (function) - Function implementing processing or utility logic.
- `_detect_gpu` (function) - Detect GPU availability, enable memory growth, and return 'gpu' or 'cpu'.
- `load_preprocessing_config` (function) - Load preprocessing toggles from YAML config file.
- `main` (function) - Function implementing processing or utility logic.
- `_print_planned_stages` (function) - Print a clear stage manifest so the user (and thesis logs) know exactly which stages are scheduled to run before execution begins.
- `_will_run` (function) - Function implementing processing or utility logic.
- `_safe_print` (function) - Print text, replacing characters that can't be encoded on Windows cp1252.
- `_print_compact_run_summary` (function) - Print a compact boxed RUN SUMMARY block — one glance overview.
- `row` (function) - Function implementing processing or utility logic.
- `_print_pipeline_summary` (function) - Print a clean summary of key pipeline metrics.
**Inputs:**
- config/pipeline_config.yaml
- config/pipeline_overrides.yaml
- data/raw/my_recording.csv
- logs/pipeline/pipeline_result_
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.entity.config_entity
- src.logger
- src.pipeline.production_pipeline
- src.utils.config_loader
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/__init__.py
**Purpose:** HAR MLOps source package.
**Stage:** utility
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/_wave2_archive/core/exception.py
**Purpose:** Custom exception for HAR MLOps Pipeline.
**Stage:** utility
**Key functions/classes:**
- `PipelineException` (class) - Custom exception that captures the originating file and line number.
- `PipelineException.__init__` (function) - Function implementing processing or utility logic.
- `PipelineException.__str__` (function) - Function implementing processing or utility logic.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- Archived under src/_wave2_archive; retained for compatibility/manual review.
---

---
## FILE: src/_wave2_archive/core/logger.py
**Purpose:** Structured logging for HAR MLOps Pipeline.
**Stage:** utility
**Key functions/classes:**
- `get_pipeline_logger` (function) - Create / retrieve a pipeline logger with console + file handlers.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- Archived under src/_wave2_archive; retained for compatibility/manual review.
---

---
## FILE: src/_wave2_archive/exception/__init__.py
**Purpose:** Exception Module for HAR MLOps Production Pipeline Custom exception handling with detailed error tracking.
**Stage:** utility
**Key functions/classes:**
- `error_message_detail` (function) - Extracts detailed error information including file name, line number, and error message.
- `MLOpsException` (class) - Custom exception class for HAR MLOps pipeline errors.
- `MLOpsException.__init__` (function) - Initialize MLOpsException with detailed error message.
- `MLOpsException.__str__` (function) - Returns the string representation of the error message.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- Archived under src/_wave2_archive; retained for compatibility/manual review.
---

---
## FILE: src/_wave2_archive/pipeline/inference_pipeline.py
**Purpose:** HAR MLOps Production Inference Pipeline Single-file orchestrator that chains all pipeline components together.
**Stage:** utility
**Key functions/classes:**
- `InferencePipeline` (class) - Production inference pipeline — chains all stages with artifact passing.
- `InferencePipeline.__init__` (function) - Function implementing processing or utility logic.
- `InferencePipeline.start_data_ingestion` (function) - Load raw Garmin Excel files, fuse sensors, resample → CSV.
- `InferencePipeline.start_data_validation` (function) - Validate schema, ranges, missing values on the fused CSV.
- `InferencePipeline.start_preprocessing` (function) - Unit detection, optional gravity removal / calibration, normalization, windowing.
- `InferencePipeline.start_inference` (function) - Run batch inference with the pretrained 1D-CNN-BiLSTM model.
- `InferencePipeline.start_evaluation` (function) - Analyze prediction distribution, confidence, ECE.
- `InferencePipeline.start_monitoring` (function) - Run 3-layer monitoring: confidence, temporal, drift.
- `InferencePipeline.start_trigger_evaluation` (function) - Evaluate retraining triggers using 2-of-3 voting.
- `InferencePipeline.run` (function) - Execute the full production pipeline (or selected stages).
- `InferencePipeline._run_stage` (function) - Helper to run a stage with error handling.
- `InferencePipeline._print_summary` (function) - Print a human-readable pipeline summary.
- `InferencePipeline._save_result` (function) - Save pipeline result as JSON for traceability.
- `InferencePipeline._to_dict` (function) - Function implementing processing or utility logic.
**Inputs:**
- data/processed/.
**Outputs:**
- data/processed/.
**Dependencies:**
- src.core.exception
- src.core.logger
- src.entity.artifact_entity
- src.entity.config_entity
**Known issues or TODOs:**
- Archived under src/_wave2_archive; retained for compatibility/manual review.
---

---
## FILE: src/active_learning_export.py
**Purpose:** Active Learning Sample Export Implements sample selection and export for human labeling in the active learning pipeline.
**Stage:** utility
**Key functions/classes:**
- `ActiveLearningConfig` (class) - Configuration for active learning sample selection.
- `UncertaintySampler` (class) - Selects samples based on model uncertainty.
- `UncertaintySampler.__init__` (function) - Function implementing processing or utility logic.
- `UncertaintySampler.least_confidence` (function) - Least confidence sampling.
- `UncertaintySampler.margin_sampling` (function) - Margin sampling.
- `UncertaintySampler.entropy_sampling` (function) - Entropy-based sampling.
- `UncertaintySampler.combined_uncertainty` (function) - Combined uncertainty score.
- `UncertaintySampler.select_uncertain_samples` (function) - Select most uncertain samples.
- `UncertaintySampler._stratified_selection` (function) - Select with class balance constraint.
- `DiversitySampler` (class) - Selects diverse samples to avoid redundancy.
- `DiversitySampler.__init__` (function) - Function implementing processing or utility logic.
- `DiversitySampler.temporal_diversity` (function) - Select temporally diverse samples.
- `DiversitySampler.prediction_diversity` (function) - Select samples that represent all predicted classes.
- `ActiveLearningExporter` (class) - Main class for selecting and exporting samples for human labeling.
- `ActiveLearningExporter.__init__` (function) - Function implementing processing or utility logic.
- `ActiveLearningExporter.select_samples` (function) - Select samples for human labeling.
- `ActiveLearningExporter.export_for_labeling` (function) - Export selected samples for human labeling.
- `ActiveLearningExporter._create_labeling_instructions` (function) - Create labeling instructions file.
- `ActiveLearningExporter.import_labeled_data` (function) - Import human-labeled data from a batch.
- `ActiveLearningExporter.generate_retraining_dataset` (function) - Combine labeled data from multiple batches for retraining.
- `main` (function) - Command-line interface for active learning export.
**Inputs:**
- data/active_learning
**Outputs:**
- data/active_learning
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- python active_learning_export.py --import-labels batch_XXXXXX
---

---
## FILE: src/api/__init__.py
**Purpose:** Provides   init   logic for the utility part of the thesis MLOps pipeline.
**Stage:** utility
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/api/app.py
**Purpose:** Provides app logic for the api part of the thesis MLOps pipeline.
**Stage:** api
**Key functions/classes:**
- `_load_monitoring_thresholds` (function) - Function implementing processing or utility logic.
- `_MonCfg` (class) - Class implementing module logic.
- `_load_model` (function) - Load the Keras model (once).
- `_load_baseline` (function) - Load the normalized baseline JSON (once).
- `_detect_columns` (function) - Auto-detect the 6 sensor columns from a CSV DataFrame.
- `_create_windows` (function) - Vectorized sliding-window creation using stride_tricks.
- `_run_monitoring` (function) - Run 3-layer monitoring on inference results.
- `UploadResult` (class) - Class implementing module logic.
- `HealthResponse` (class) - Class implementing module logic.
- `lifespan` (function) - Async function implementing API or workflow logic.
- `health` (function) - Async function implementing API or workflow logic.
- `model_info` (function) - Async function implementing API or workflow logic.
- `metrics` (function) - Prometheus metrics endpoint — scraped by config/prometheus.yml.
- `upload_csv` (function) - Upload a CSV file with accelerometer + gyroscope data.
- `dashboard` (function) - Serve the interactive web dashboard.
**Inputs:**
- config/prometheus.yml
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.utils.config_loader
- src.utils.label_mapping
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/calibration.py
**Purpose:** Model Calibration & Uncertainty Quantification Implements post-hoc calibration and uncertainty estimation for the HAR inference pipeline.
**Stage:** calibration
**Key functions/classes:**
- `CalibrationConfig` (class) - Configuration for calibration and uncertainty quantification.
- `TemperatureScaler` (class) - Post-hoc temperature scaling for softmax calibration.
- `TemperatureScaler.__init__` (function) - Function implementing processing or utility logic.
- `TemperatureScaler.fit` (function) - Learn optimal temperature on a validation set using NLL minimisation.
- `TemperatureScaler.nll_with_temperature` (function) - Function implementing processing or utility logic.
- `TemperatureScaler.transform` (function) - Apply temperature scaling to logits and return calibrated probs.
- `TemperatureScaler.save` (function) - Persist the learned temperature.
- `TemperatureScaler.load` (function) - Load a previously learned temperature.
- `MCDropoutEstimator` (class) - Monte Carlo Dropout for epistemic uncertainty estimation.
- `MCDropoutEstimator.__init__` (function) - Function implementing processing or utility logic.
- `MCDropoutEstimator.estimate` (function) - Run MC Dropout forward passes and compute uncertainty metrics.
- `CalibrationEvaluator` (class) - Evaluate model calibration quality using standard metrics.
- `CalibrationEvaluator.__init__` (function) - Function implementing processing or utility logic.
- `CalibrationEvaluator.expected_calibration_error` (function) - Compute ECE and per-bin calibration data.
- `CalibrationEvaluator.brier_score` (function) - Compute multi-class Brier score = mean( sum( (p_c - y_c)^2 ) ).
- `CalibrationEvaluator.evaluate` (function) - Full calibration evaluation.
- `CalibrationEvaluator.save_reliability_diagram` (function) - Save a reliability diagram as PNG.
- `UnlabeledCalibrationAnalyzer` (class) - Calibration-style analysis for production data WITHOUT labels.
- `UnlabeledCalibrationAnalyzer.analyze` (function) - Analyze prediction confidence for calibration warning signs.
- `UnlabeledCalibrationAnalyzer._generate_warnings` (function) - Function implementing processing or utility logic.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/__init__.py
**Purpose:** src/components — Each pipeline stage as a self-contained component class.
**Stage:** utility
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/baseline_update.py
**Purpose:** Component 10 – Baseline Update Wraps:  scripts/build_training_baseline.py  →  BaselineBuilder
**Stage:** registration
**Key functions/classes:**
- `BaselineUpdate` (class) - Rebuild drift baselines after retraining.
- `BaselineUpdate.__init__` (function) - Function implementing processing or utility logic.
- `BaselineUpdate.initiate_baseline_update` (function) - Function implementing processing or utility logic.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/calibration_uncertainty.py
**Purpose:** Component 11 – Calibration & Uncertainty Quantification Wraps:  src/calibration.py  →  TemperatureScaler, CalibrationEvaluator, MCDropoutEstimator, UnlabeledCalibrationAnalyzer
**Stage:** calibration
**Key functions/classes:**
- `CalibrationUncertainty` (class) - Post-hoc calibration and uncertainty quantification for predictions.
- `CalibrationUncertainty.__init__` (function) - Function implementing processing or utility logic.
- `CalibrationUncertainty.initiate_calibration` (function) - Function implementing processing or utility logic.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- src.calibration
- src.entity.artifact_entity
- src.entity.config_entity
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/curriculum_pseudo_labeling.py
**Purpose:** Component 13 – Curriculum Pseudo-Labeling Wraps:  src/curriculum_pseudo_labeling.py  →  CurriculumTrainer
**Stage:** pseudo_labeling
**Key functions/classes:**
- `CurriculumPseudoLabeling` (class) - Self-training with progressive pseudo-labeling and EWC.
- `CurriculumPseudoLabeling.__init__` (function) - Function implementing processing or utility logic.
- `CurriculumPseudoLabeling.initiate_curriculum_training` (function) - Function implementing processing or utility logic.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.curriculum_pseudo_labeling
- src.entity.artifact_entity
- src.entity.config_entity
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/data_ingestion.py
**Purpose:** Component 1 – Data Ingestion Self-contained ingestion that handles ALL raw-data scenarios: A.
**Stage:** ingestion
**Key functions/classes:**
- `discover_sensor_files` (function) - Find ALL matching accelerometer/gyroscope file pairs.
- `find_latest_sensor_pair` (function) - Return the single newest accel/gyro pair (backward-compat helper).
- `_load_manifest` (function) - Function implementing processing or utility logic.
- `_save_manifest` (function) - Function implementing processing or utility logic.
- `_pair_key` (function) - Unique key for an accel/gyro pair.
- `_load_sensor_file` (function) - Load a sensor file (Excel or CSV).
- `_validate_sensor_file` (function) - Validate sensor file has required data.
- `_normalize_columns` (function) - Rename Garmin-specific column names to standard x/y/z.
- `_parse_list_cell` (function) - Parse a cell value that may contain a JSON/Python list.
- `_parse_list_columns` (function) - Parse list-encoded columns (sample_time_offset, x, y, z).
- `_filter_valid_rows` (function) - Keep only rows where x, y, z, offset are lists of same length.
- `_valid` (function) - Function implementing processing or utility logic.
- `_explode_rows` (function) - Expand list columns into individual rows.
- `_create_timestamps` (function) - Create precise timestamps using base_time + offset.
- `_rename_axes` (function) - Rename x/y/z → Ax/Ay/Az or Gx/Gy/Gz.
- `_merge_and_resample` (function) - Merge accelerometer and gyroscope data, then resample to target Hz.
- `DataIngestion` (class) - Ingest raw sensor files (Excel/CSV pairs or single CSV) into a fused CSV.
- `DataIngestion.__init__` (function) - Function implementing processing or utility logic.
- `DataIngestion.initiate_data_ingestion` (function) - Run data ingestion and return the artifact.
- `DataIngestion._ingest_csv` (function) - Copy / validate a user-provided CSV.
- `DataIngestion._ingest_sensor_pair` (function) - Process one specific accel/gyro pair.
- `DataIngestion._ingest_auto_discover` (function) - Auto-discover sensor files in data/raw/ (then Decoded/), skip processed.
- `DataIngestion._process_pair` (function) - Load, parse, merge, and resample one accel/gyro pair.
**Inputs:**
- data/processed/
- data/processed/sensor_fused_50Hz.csv
- data/raw/
- data/raw/Decoded/
**Outputs:**
- data/processed/
- data/processed/sensor_fused_50Hz.csv
- data/raw/
- data/raw/Decoded/
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/data_transformation.py
**Purpose:** Component 3 – Data Transformation (Preprocessing) Wraps:  src/preprocess_data.py  →  UnifiedPreprocessor (CSV → normalized, windowed .npy)
**Stage:** transformation
**Key functions/classes:**
- `DataTransformation` (class) - Preprocess the fused CSV into windowed .npy arrays.
- `DataTransformation.__init__` (function) - Function implementing processing or utility logic.
- `DataTransformation.initiate_data_transformation` (function) - Function implementing processing or utility logic.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
- src.preprocess_data
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/data_validation.py
**Purpose:** Component 2 – Data Validation Wraps:  src/data_validator.py  →  DataValidator.validate()
**Stage:** validation
**Key functions/classes:**
- `DataValidation` (class) - Validate the ingested sensor CSV (schema, ranges, completeness).
- `DataValidation.__init__` (function) - Function implementing processing or utility logic.
- `DataValidation.initiate_data_validation` (function) - Function implementing processing or utility logic.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.data_validator
- src.entity.artifact_entity
- src.entity.config_entity
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/model_evaluation.py
**Purpose:** Component 5 – Model Evaluation Wraps:  src/evaluate_predictions.py  →  EvaluationPipeline
**Stage:** evaluation
**Key functions/classes:**
- `ModelEvaluation` (class) - Evaluate predictions (confidence, distribution, ECE, class metrics).
- `ModelEvaluation.__init__` (function) - Function implementing processing or utility logic.
- `ModelEvaluation.initiate_model_evaluation` (function) - Function implementing processing or utility logic.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
- src.evaluate_predictions
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/model_inference.py
**Purpose:** Component 4 – Model Inference Wraps:  src/run_inference.py  →  InferencePipeline (renamed to avoid clash)
**Stage:** inference
**Key functions/classes:**
- `ModelInference` (class) - Run batch inference with the pretrained model.
- `ModelInference.__init__` (function) - Function implementing processing or utility logic.
- `ModelInference.initiate_model_inference` (function) - Function implementing processing or utility logic.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
- src.run_inference
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/model_registration.py
**Purpose:** Component 9 – Model Registration Wraps:  src/model_rollback.py  →  ModelRegistry
**Stage:** registration
**Key functions/classes:**
- `ModelRegistration` (class) - Register, validate, and (optionally) deploy the retrained model.
- `ModelRegistration.__init__` (function) - Function implementing processing or utility logic.
- `ModelRegistration.initiate_model_registration` (function) - Function implementing processing or utility logic.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
- src.model_rollback
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/model_retraining.py
**Purpose:** Component 8 – Model Retraining Wraps:  src/train.py  →  HARTrainer / DomainAdaptationTrainer src/domain_adaptation/adabn.py  →  adapt_bn_statistics
**Stage:** retraining
**Key functions/classes:**
- `ModelRetraining` (class) - Retrain the model — standard, AdaBN, TENT, AdaBN+TENT, or pseudo-label adaptation.
- `ModelRetraining.__init__` (function) - Function implementing processing or utility logic.
- `ModelRetraining.initiate_model_retraining` (function) - Function implementing processing or utility logic.
- `ModelRetraining._run_adabn` (function) - Unsupervised domain adaptation via AdaBN (no labels needed).
- `ModelRetraining._run_tent` (function) - Test-time adaptation via TENT (entropy minimisation on BN affine params).
- `ModelRetraining._run_adabn_then_tent` (function) - Two-stage: AdaBN (running stats) → TENT (affine fine-tuning).
- `ModelRetraining._run_pseudo_label` (function) - Semi-supervised: pseudo-label + fine-tune.
- `ModelRetraining._run_standard` (function) - Standard supervised retraining on labeled data.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.domain_adaptation.adabn
- src.domain_adaptation.tent
- src.entity.artifact_entity
- src.entity.config_entity
- src.train
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/post_inference_monitoring.py
**Purpose:** Component 6 – Post-Inference Monitoring Wraps:  scripts/post_inference_monitoring.py  →  PostInferenceMonitor
**Stage:** monitoring
**Key functions/classes:**
- `PostInferenceMonitoring` (class) - Run 3-layer monitoring (confidence, temporal, drift).
- `PostInferenceMonitoring.__init__` (function) - Function implementing processing or utility logic.
- `PostInferenceMonitoring.initiate_post_inference_monitoring` (function) - Function implementing processing or utility logic.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/sensor_placement.py
**Purpose:** Component 14 – Sensor Placement Robustness Wraps:  src/sensor_placement.py  →  AxisMirrorAugmenter, HandDetector, HandPerformanceReporter
**Stage:** sensor_placement
**Key functions/classes:**
- `SensorPlacement` (class) - Sensor placement detection, axis mirroring augmentation, and per-hand reporting.
- `SensorPlacement.__init__` (function) - Function implementing processing or utility logic.
- `SensorPlacement.initiate_sensor_placement` (function) - Function implementing processing or utility logic.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
- src.sensor_placement
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/trigger_evaluation.py
**Purpose:** Component 7 – Trigger Evaluation Wraps:  src/trigger_policy.py  →  TriggerPolicyEngine
**Stage:** trigger
**Key functions/classes:**
- `TriggerEvaluation` (class) - Evaluate whether retraining should be triggered.
- `TriggerEvaluation.__init__` (function) - Function implementing processing or utility logic.
- `TriggerEvaluation.initiate_trigger_evaluation` (function) - Function implementing processing or utility logic.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
- src.trigger_policy
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/components/wasserstein_drift.py
**Purpose:** Component 12 – Wasserstein Drift Detection Wraps:  src/wasserstein_drift.py  →  WassersteinDriftDetector, WassersteinChangePointDetector, compute_integrated_drift_report
**Stage:** drift
**Key functions/classes:**
- `WassersteinDrift` (class) - Wasserstein distance-based distribution drift detection.
- `WassersteinDrift.__init__` (function) - Function implementing processing or utility logic.
- `WassersteinDrift.initiate_wasserstein_drift` (function) - Function implementing processing or utility logic.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
- src.wasserstein_drift
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/config.py
**Purpose:** Path Configuration for MLOps Pipeline Simplified structure without numbered prefixes
**Stage:** config
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/core/__init__.py
**Purpose:** Core utilities — exception handling and structured logging.
**Stage:** utility
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/curriculum_pseudo_labeling.py
**Purpose:** Curriculum Pseudo-Labeling (Self-Training Loop) Implements progressive pseudo-labeling for semi-supervised retraining on unlabeled production data.
**Stage:** pseudo_labeling
**Key functions/classes:**
- `CurriculumConfig` (class) - Configuration for curriculum pseudo-labeling.
- `PseudoLabelSelector` (class) - Select high-confidence pseudo-labels with class balancing.
- `PseudoLabelSelector.__init__` (function) - Function implementing processing or utility logic.
- `PseudoLabelSelector.get_threshold_for_iteration` (function) - Compute the confidence threshold for a given iteration.
- `PseudoLabelSelector.select` (function) - Select pseudo-labeled samples for the current iteration.
- `EWCRegularizer` (class) - Elastic Weight Consolidation to prevent catastrophic forgetting.
- `EWCRegularizer.__init__` (function) - Function implementing processing or utility logic.
- `EWCRegularizer.compute_fisher` (function) - Compute diagonal Fisher Information Matrix using labeled data.
- `EWCRegularizer.penalty` (function) - Compute the EWC penalty term.
- `CurriculumTrainer` (class) - Complete curriculum pseudo-labeling training loop.
- `CurriculumTrainer.__init__` (function) - Function implementing processing or utility logic.
- `CurriculumTrainer.train` (function) - Run the full curriculum pseudo-labeling loop.
- `CurriculumTrainer._ema_update` (function) - Exponential Moving Average update: teacher ← decay*teacher + (1-decay)*student.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/data_validator.py
**Purpose:** Data Validator Module Production-grade data validation for sensor data preprocessing.
**Stage:** validation
**Key functions/classes:**
- `ValidationResult` (class) - Result of data validation.
- `ValidationResult.__str__` (function) - Function implementing processing or utility logic.
- `DataValidator` (class) - Production-grade data validation for sensor data.
- `DataValidator.__init__` (function) - Initialize DataValidator with validation parameters.
- `DataValidator._load_config` (function) - Load validation settings from YAML config file.
- `DataValidator.validate` (function) - Validate sensor data DataFrame.
- `DataValidator.validate_and_raise` (function) - Validate data and raise exception if invalid.
- `load_validator_from_config` (function) - Factory function to create DataValidator from config file.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/deployment_manager.py
**Purpose:** Provides deployment manager logic for the utility part of the thesis MLOps pipeline.
**Stage:** utility
**Key functions/classes:**
- `DeploymentConfig` (class) - Deployment configuration.
- `DeploymentConfig.full_image_name` (function) - Get full image name with registry.
- `ContainerBuilder` (class) - Builds Docker containers for model serving.
- `ContainerBuilder.__init__` (function) - Function implementing processing or utility logic.
- `ContainerBuilder.check_docker` (function) - Check if Docker is available.
- `ContainerBuilder.build_inference_image` (function) - Build inference Docker image.
- `ContainerBuilder.push_image` (function) - Push image to registry.
- `DeploymentManager` (class) - Manages model deployment lifecycle.
- `DeploymentManager.__init__` (function) - Function implementing processing or utility logic.
- `DeploymentManager._load_state` (function) - Load deployment state.
- `DeploymentManager._save_state` (function) - Save deployment state.
- `DeploymentManager.deploy` (function) - Deploy a model version.
- `DeploymentManager._rolling_deploy` (function) - Rolling deployment using docker-compose.
- `DeploymentManager._blue_green_deploy` (function) - Blue-green deployment.
- `DeploymentManager._canary_deploy` (function) - Canary deployment.
- `DeploymentManager.promote_canary` (function) - Promote canary to full deployment.
- `DeploymentManager.rollback` (function) - Rollback to previous version.
- `DeploymentManager._wait_for_healthy` (function) - Wait for service to be healthy.
- `DeploymentManager._stop_color` (function) - Stop blue or green deployment.
- `DeploymentManager._switch_traffic` (function) - Switch traffic to target color (nginx/load balancer config).
- `DeploymentManager.status` (function) - Get current deployment status.
- `main` (function) - Command-line interface for deployment manager.
**Inputs:**
- config/requirements.txt
- models/pretrained
**Outputs:**
- config/requirements.txt
- models/pretrained
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/diagnostic_pipeline_check.py
**Purpose:** Pipeline Contract Diagnostic Tool This script checks for preprocessing mismatches between training and inference that could explain low accuracy (14-15% = near-random for 11 classes).
**Stage:** utility
**Key functions/classes:**
- `PipelineDiagnostic` (class) - Diagnose preprocessing contract mismatches.
- `PipelineDiagnostic.__init__` (function) - Function implementing processing or utility logic.
- `PipelineDiagnostic._load_json` (function) - Load JSON file.
- `PipelineDiagnostic.run_full_diagnostic` (function) - Run all diagnostic checks.
- `PipelineDiagnostic.check_window_size` (function) - Check if window size matches between training and production.
- `PipelineDiagnostic.check_overlap` (function) - Check if overlap percentage matches.
- `PipelineDiagnostic.check_sampling_rate` (function) - Check if target sampling rate matches.
- `PipelineDiagnostic.check_sensor_channels` (function) - Check if sensor channel order matches.
- `PipelineDiagnostic.check_normalization_stats` (function) - Check if normalization statistics are consistent.
- `PipelineDiagnostic.check_label_mapping` (function) - Check label mapping consistency.
- `PipelineDiagnostic.check_data_shape` (function) - Check production data shape consistency.
- `PipelineDiagnostic.check_feature_distributions` (function) - Compare feature distributions between training stats and production data.
- `PipelineDiagnostic._print_summary` (function) - Print diagnostic summary.
- `main` (function) - Run diagnostic on current pipeline.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/domain_adaptation/__init__.py
**Purpose:** Domain adaptation package for HAR MLOps.
**Stage:** utility
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.domain_adaptation.adabn
- src.domain_adaptation.tent
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/domain_adaptation/adabn.py
**Purpose:** Adaptive Batch Normalization (AdaBN) for unsupervised domain adaptation.
**Stage:** retraining
**Key functions/classes:**
- `_find_bn_layers` (function) - Return all BatchNormalization layers in the model.
- `adapt_bn_statistics` (function) - Adapt Batch Normalization running statistics to a target domain.
- `adabn_score_confidence` (function) - Run inference on target data with the adapted model and return confidence statistics.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/domain_adaptation/tent.py
**Purpose:** TENT: Test-Time Entropy Minimization for domain adaptation.
**Stage:** retraining
**Key functions/classes:**
- `tent_adapt` (function) - Adapt BN affine parameters by minimising prediction entropy.
- `tent_score` (function) - Compute entropy-based quality metrics on target data after adaptation.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/entity/__init__.py
**Purpose:** Entity module — dataclass configs and artifacts for pipeline stages.
**Stage:** utility
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.entity.artifact_entity
- src.entity.config_entity
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/entity/artifact_entity.py
**Purpose:** Artifact entities for HAR MLOps Production Pipeline.
**Stage:** utility
**Key functions/classes:**
- `DataIngestionArtifact` (class) - Output of sensor-data ingestion (Excel/CSV → fused CSV).
- `DataValidationArtifact` (class) - Output of data validation.
- `DataTransformationArtifact` (class) - Output of preprocessing (CSV → windowed .npy).
- `ModelInferenceArtifact` (class) - Output of model inference.
- `ModelEvaluationArtifact` (class) - Output of prediction evaluation.
- `PostInferenceMonitoringArtifact` (class) - Output of post-inference monitoring (3-layer).
- `TriggerEvaluationArtifact` (class) - Output of retraining-trigger evaluation.
- `ModelRetrainingArtifact` (class) - Output of model retraining (standard or domain-adapted).
- `ModelRegistrationArtifact` (class) - Output of model registration and validation.
- `BaselineUpdateArtifact` (class) - Output of baseline rebuild.
- `CalibrationUncertaintyArtifact` (class) - Output of calibration and uncertainty quantification.
- `WassersteinDriftArtifact` (class) - Output of Wasserstein-based drift detection.
- `CurriculumPseudoLabelingArtifact` (class) - Output of curriculum pseudo-labeling training.
- `SensorPlacementArtifact` (class) - Output of sensor placement analysis.
- `PipelineResult` (class) - Aggregated result of the full pipeline run.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/entity/config_entity.py
**Purpose:** Configuration entities for HAR MLOps Production Pipeline.
**Stage:** utility
**Key functions/classes:**
- `PipelineConfig` (class) - Top-level pipeline settings shared by all stages.
- `PipelineConfig.__post_init__` (function) - Function implementing processing or utility logic.
- `DataIngestionConfig` (class) - Configuration for raw-sensor-data ingestion (Excel/CSV → fused CSV).
- `DataValidationConfig` (class) - Configuration for data validation.
- `DataTransformationConfig` (class) - Configuration for preprocessing (CSV → windowed .npy arrays).
- `ModelInferenceConfig` (class) - Configuration for model inference.
- `ModelEvaluationConfig` (class) - Configuration for prediction evaluation.
- `PostInferenceMonitoringConfig` (class) - Configuration for post-inference monitoring (3-layer).
- `TriggerEvaluationConfig` (class) - Configuration for retraining-trigger evaluation.
- `ModelRetrainingConfig` (class) - Configuration for model retraining (including domain adaptation).
- `ModelRegistrationConfig` (class) - Configuration for model versioning and deployment.
- `BaselineUpdateConfig` (class) - Configuration for rebuilding drift baselines after retraining.
- `CalibrationUncertaintyConfig` (class) - Configuration for post-hoc calibration and MC Dropout UQ.
- `WassersteinDriftConfig` (class) - Configuration for Wasserstein-based distribution drift detection.
- `CurriculumPseudoLabelingConfig` (class) - Configuration for curriculum-style self-training.
- `SensorPlacementConfig` (class) - Configuration for sensor placement robustness (hand detection, mirroring).
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/evaluate_predictions.py
**Purpose:** Prediction Evaluation for Mental Health Activity Recognition This script evaluates inference predictions using classification metrics.
**Stage:** evaluation
**Key functions/classes:**
- `EvaluationConfig` (class) - Configuration for evaluation pipeline.
- `EvaluationConfig.__post_init__` (function) - Ensure paths are Path objects.
- `EvaluationLogger` (class) - Centralized logging for evaluation pipeline.
- `EvaluationLogger.__init__` (function) - Initialize logger with file and console handlers.
- `EvaluationLogger.get_logger` (function) - Function implementing processing or utility logic.
- `PredictionAnalyzer` (class) - Analyze predictions when ground truth is NOT available.
- `PredictionAnalyzer.__init__` (function) - Function implementing processing or utility logic.
- `PredictionAnalyzer.load_predictions` (function) - Load predictions from CSV file.
- `PredictionAnalyzer.analyze_distribution` (function) - Analyze activity distribution.
- `PredictionAnalyzer.analyze_confidence` (function) - Analyze confidence score distribution.
- `PredictionAnalyzer.analyze_uncertainty` (function) - Deep analysis of uncertain predictions.
- `PredictionAnalyzer.analyze_temporal_patterns` (function) - Analyze temporal patterns in predictions.
- `ClassificationEvaluator` (class) - Evaluate predictions against ground truth labels.
- `ClassificationEvaluator.__init__` (function) - Function implementing processing or utility logic.
- `ClassificationEvaluator.compute_metrics` (function) - Compute classification metrics.
- `ClassificationEvaluator.compute_calibration` (function) - Compute calibration metrics.
- `ReportGenerator` (class) - Generate evaluation reports.
- `ReportGenerator.__init__` (function) - Function implementing processing or utility logic.
- `ReportGenerator.generate_json_report` (function) - Save results as JSON.
- `ReportGenerator.generate_text_report` (function) - Generate human-readable text report.
- `EvaluationPipeline` (class) - Complete evaluation pipeline orchestrator.
- `EvaluationPipeline.__init__` (function) - Function implementing processing or utility logic.
- `EvaluationPipeline.run` (function) - Execute evaluation pipeline.
- `parse_args` (function) - Parse command line arguments.
- `main` (function) - Main entry point.
**Inputs:**
- logs/evaluation/evaluation_YYYYMMDD_HHMMSS.log
**Outputs:**
- logs/evaluation/evaluation_YYYYMMDD_HHMMSS.log
**Dependencies:**
- src.utils.label_mapping
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/exceptions.py
**Purpose:** src/exceptions.py Custom exception classes for the HAR MLOps pipeline.
**Stage:** utility
**Key functions/classes:**
- `DataValidationError` (class) - Raised when Stage 2 data validation fails.
- `ModelLoadError` (class) - Raised when Stage 4 cannot load or verify the pretrained model.
- `ConfigurationError` (class) - Raised when a pipeline configuration is invalid or self-contradictory.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/logger/__init__.py
**Purpose:** Logger Module for HAR MLOps Production Pipeline Provides centralized logging configuration for the entire pipeline.
**Stage:** utility
**Key functions/classes:**
- `get_logger` (function) - Configure and return the root logger.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/mlflow_tracking.py
**Purpose:** MLflow Experiment Tracking Module This module provides centralized MLflow integration for the MLOps pipeline.
**Stage:** utility
**Key functions/classes:**
- `MLflowTracker` (class) - Centralized MLflow tracking for the HAR MLOps pipeline.
- `MLflowTracker.__init__` (function) - Initialize MLflow tracker.
- `MLflowTracker._load_config` (function) - Load configuration from YAML file.
- `MLflowTracker._setup_experiment` (function) - Create experiment if it doesn't exist.
- `MLflowTracker.start_run` (function) - Context manager for MLflow runs.
- `MLflowTracker.log_params` (function) - Log parameters to the current run.
- `MLflowTracker.log_metrics` (function) - Log metrics to the current run.
- `MLflowTracker.log_artifact` (function) - Log a file or directory as an artifact.
- `MLflowTracker.log_dict` (function) - Log a dictionary as a JSON artifact.
- `MLflowTracker.log_dataframe` (function) - Log a pandas DataFrame as a CSV artifact.
- `MLflowTracker.log_figure` (function) - Log a matplotlib figure as an artifact.
- `MLflowTracker.log_keras_model` (function) - Log a Keras model to MLflow.
- `MLflowTracker.log_training_history` (function) - Log Keras training history (metrics per epoch).
- `MLflowTracker.log_confusion_matrix` (function) - Log confusion matrix as an artifact.
- `MLflowTracker.log_classification_report` (function) - Log classification report and return key metrics.
- `MLflowTracker.get_best_run` (function) - Get the best run from the current experiment.
- `MLflowTracker.compare_runs` (function) - Compare multiple runs by their metrics.
- `get_or_create_tracker` (function) - Get or create a singleton MLflow tracker.
- `quick_log_run` (function) - Quickly log a complete run with params, metrics, and artifacts.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/model_rollback.py
**Purpose:** Model Rollback Manager Safe model rollback functionality for the HAR MLOps pipeline.
**Stage:** registration
**Key functions/classes:**
- `ModelVersion` (class) - Represents a model version with metadata.
- `ModelVersion.to_dict` (function) - Function implementing processing or utility logic.
- `ModelVersion.from_dict` (function) - Function implementing processing or utility logic.
- `ModelRegistry` (class) - Local model registry for tracking deployed models.
- `ModelRegistry.__init__` (function) - Function implementing processing or utility logic.
- `ModelRegistry._load_registry` (function) - Load registry from file.
- `ModelRegistry._save_registry` (function) - Save registry to file.
- `ModelRegistry._compute_hash` (function) - Compute SHA256 hash of a file.
- `ModelRegistry.register_model` (function) - Register a new model version.
- `ModelRegistry.deploy_model` (function) - Deploy a specific model version.
- `ModelRegistry.rollback` (function) - Rollback to a previous model version.
- `ModelRegistry.list_versions` (function) - List all registered model versions.
- `ModelRegistry.get_current_version` (function) - Get currently deployed version.
- `ModelRegistry.get_deployment_history` (function) - Get recent deployment history.
- `RollbackValidator` (class) - Validate model before and after rollback.
- `RollbackValidator.__init__` (function) - Function implementing processing or utility logic.
- `RollbackValidator.validate_model_file` (function) - Check that model file exists and is loadable.
- `RollbackValidator.validate_inference` (function) - Run a quick inference test.
- `main` (function) - Function implementing processing or utility logic.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/ood_detection.py
**Purpose:** Energy-Based Out-of-Distribution Detection Implements energy-based OOD detection for the HAR monitoring pipeline.
**Stage:** utility
**Key functions/classes:**
- `OODConfig` (class) - Configuration for OOD detection.
- `OODConfig.__post_init__` (function) - Function implementing processing or utility logic.
- `EnergyOODDetector` (class) - Energy-based Out-of-Distribution detector.
- `EnergyOODDetector.__init__` (function) - Function implementing processing or utility logic.
- `EnergyOODDetector.compute_energy` (function) - Compute energy scores from logits.
- `EnergyOODDetector.compute_energy_from_probs` (function) - Compute approximate energy from softmax probabilities.
- `EnergyOODDetector.calibrate` (function) - Calibrate thresholds using in-distribution validation data.
- `EnergyOODDetector.detect_ood` (function) - Detect OOD samples based on energy scores.
- `EnsembleOODDetector` (class) - Ensemble OOD detector combining multiple signals: - Energy score - Entropy - Max confidence - (Optional) Reconstruction error Multiple signals reduce false positives.
- `EnsembleOODDetector.__init__` (function) - Function implementing processing or utility logic.
- `EnsembleOODDetector.compute_all_scores` (function) - Compute all OOD scores.
- `EnsembleOODDetector.compute_ensemble_score` (function) - Compute weighted ensemble OOD score.
- `EnsembleOODDetector.detect` (function) - Full OOD detection pipeline.
- `add_ood_metrics_to_monitoring` (function) - Add OOD detection metrics to existing monitoring report.
- `main` (function) - Demo of OOD detection.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/pipeline/__init__.py
**Purpose:** Pipeline module — production pipeline orchestration.
**Stage:** utility
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.pipeline.inference_pipeline
- src.pipeline.production_pipeline
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/pipeline/production_pipeline.py
**Purpose:** HAR MLOps — Production Pipeline Orchestrator Clean ~200-line orchestrator that delegates ALL work to component classes.
**Stage:** utility
**Key functions/classes:**
- `ProductionPipeline` (class) - Orchestrates the full HAR MLOps pipeline.
- `ProductionPipeline.__init__` (function) - Function implementing processing or utility logic.
- `ProductionPipeline.run` (function) - Execute the pipeline.
- `ProductionPipeline._make_fallback_ingestion_artifact` (function) - Create a synthetic ingestion artifact pointing to existing CSV.
- `ProductionPipeline._make_fallback_transformation_artifact` (function) - Create a synthetic transformation artifact pointing to existing .npy.
- `ProductionPipeline._save_result` (function) - Persist pipeline result as JSON.
- `ProductionPipeline._convert` (function) - Function implementing processing or utility logic.
- `ProductionPipeline._init_mlflow` (function) - Function implementing processing or utility logic.
- `ProductionPipeline._log_stage_to_mlflow` (function) - Function implementing processing or utility logic.
- `ProductionPipeline._end_mlflow` (function) - Function implementing processing or utility logic.
- `ProductionPipeline._register_model_to_mlflow` (function) - Register the production model in MLflow Model Registry.
- `ProductionPipeline._load_keras_model` (function) - Load a Keras model (lazy import to avoid TF startup cost).
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- src.components.baseline_update
- src.components.calibration_uncertainty
- src.components.curriculum_pseudo_labeling
- src.components.data_ingestion
- src.components.data_transformation
- src.components.data_validation
- src.components.model_evaluation
- src.components.model_inference
- src.components.model_registration
- src.components.model_retraining
- src.components.post_inference_monitoring
- src.components.sensor_placement
- src.components.trigger_evaluation
- src.components.wasserstein_drift
- src.entity.artifact_entity
- src.entity.config_entity
- src.exceptions
- src.logger
- src.mlflow_tracking
- src.utils.artifacts_manager
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/preprocess_data.py
**Purpose:** Provides preprocess data logic for the transformation part of the thesis MLOps pipeline.
**Stage:** transformation
**Key functions/classes:**
- `PreprocessLogger` (class) - Configure comprehensive logging for preprocessing pipeline
- `PreprocessLogger.__init__` (function) - Function implementing processing or utility logic.
- `PreprocessLogger.get_logger` (function) - Function implementing processing or utility logic.
- `UnitDetector` (class) - Automatically detect accelerometer units and convert if needed
- `UnitDetector.__init__` (function) - Function implementing processing or utility logic.
- `UnitDetector.detect_units` (function) - Detect if accelerometer data is in milliG or m/s² Args: df: DataFrame with accelerometer data accel_cols: List of accelerometer column names Returns: 'milliG', 'm/s²', or 'unknown'
- `UnitDetector.convert_to_ms2` (function) - Convert accelerometer data from milliG to m/s² Args: df: DataFrame with accelerometer in milliG accel_cols: List of accelerometer column names Returns: DataFrame with accelerometer in m/s²
- `UnitDetector.process_units` (function) - Main entry point: detect units and convert if needed Returns: (processed_df, conversion_applied)
- `GravityRemover` (class) - Remove gravity component from accelerometer data using high-pass filter.
- `GravityRemover.__init__` (function) - Function implementing processing or utility logic.
- `GravityRemover.remove_gravity` (function) - Apply high-pass Butterworth filter to remove gravity.
- `DomainCalibrator` (class) - Calibrate production data to match training data distribution.
- `DomainCalibrator.__init__` (function) - Function implementing processing or utility logic.
- `DomainCalibrator.calibrate` (function) - Shift production data to match training distribution mean.
- `UnifiedPreprocessor` (class) - Unified preprocessing for training and production data
- `UnifiedPreprocessor.__init__` (function) - Function implementing processing or utility logic.
- `UnifiedPreprocessor.detect_data_format` (function) - Detect if data is labeled (training) or unlabeled (production) Returns: (format, sensor_columns)
- `UnifiedPreprocessor.create_activity_encoding` (function) - Create mapping between activity names and numeric labels
- `UnifiedPreprocessor.normalize_data` (function) - Normalize sensor values using the scaler that was fit on training data.
- `UnifiedPreprocessor.create_windows` (function) - Create sliding windows from time series data Returns: X: (n_windows, window_size, n_sensors) array y: (n_windows,) array or None if unlabeled metadata: List of window info dicts
- `UnifiedPreprocessor.split_by_user` (function) - Split data by user for train/val/test Ensures no user appears in multiple splits (prevents data leakage)
- `UnifiedPreprocessor.save_data` (function) - Save preprocessed production data and metadata
- `main` (function) - Function implementing processing or utility logic.
**Inputs:**
- data/prepared/config.json
**Outputs:**
- data/prepared/config.json
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/robustness.py
**Purpose:** Robustness & Noise Injection Test Suite Systematic robustness evaluation framework for the HAR pipeline.
**Stage:** utility
**Key functions/classes:**
- `RobustnessConfig` (class) - Configuration for robustness evaluation.
- `GaussianNoiseInjector` (class) - Add Gaussian noise at a specified fraction of signal std.
- `GaussianNoiseInjector.inject` (function) - Add Gaussian noise to sensor data.
- `MissingDataInjector` (class) - Simulate missing data by zeroing random segments.
- `MissingDataInjector.inject` (function) - Simulate missing data.
- `SamplingJitterInjector` (class) - Simulate sampling rate jitter by resampling with slight distortion.
- `SamplingJitterInjector.inject` (function) - Simulate sampling rate jitter.
- `SaturationInjector` (class) - Simulate sensor saturation / clipping.
- `SaturationInjector.inject` (function) - Clip values to [-threshold, threshold].
- `RobustnessEvaluator` (class) - Comprehensive robustness evaluation framework.
- `RobustnessEvaluator.__init__` (function) - Function implementing processing or utility logic.
- `RobustnessEvaluator._predict` (function) - Run inference and return (predictions, confidences).
- `RobustnessEvaluator._evaluate_accuracy` (function) - Compute accuracy and confidence metrics.
- `RobustnessEvaluator.evaluate_noise_robustness` (function) - Test accuracy across Gaussian noise levels.
- `RobustnessEvaluator.evaluate_missing_data_robustness` (function) - Test accuracy across missing data ratios.
- `RobustnessEvaluator.evaluate_jitter_robustness` (function) - Test accuracy across sampling rate jitter levels.
- `RobustnessEvaluator.full_evaluation` (function) - Run complete robustness evaluation across all degradation types.
- `RobustnessEvaluator.save_report` (function) - Save robustness report as JSON.
- `RobustnessEvaluator.save_degradation_curves` (function) - Save degradation curves as PNG plots.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/run_inference.py
**Purpose:** Inference Pipeline for Mental Health Activity Recognition This script performs inference using the pre-trained 1D-CNN-BiLSTM model on preprocessed production sensor data.
**Stage:** inference
**Key functions/classes:**
- `InferenceConfig` (class) - Configuration for inference pipeline.
- `InferenceConfig.__post_init__` (function) - Ensure paths are Path objects.
- `InferenceLogger` (class) - Centralized logging for inference pipeline.
- `InferenceLogger.__init__` (function) - Initialize logger with file and console handlers.
- `InferenceLogger.get_logger` (function) - Return the configured logger.
- `ModelLoader` (class) - Load and validate the pre-trained Keras model.
- `ModelLoader.__init__` (function) - Initialize model loader.
- `ModelLoader.load` (function) - Load the Keras model from disk.
- `DataLoader` (class) - Load preprocessed sensor data for inference.
- `DataLoader.__init__` (function) - Initialize data loader.
- `DataLoader.load` (function) - Load preprocessed data from .npy file.
- `InferenceEngine` (class) - Core inference engine for activity recognition.
- `InferenceEngine.__init__` (function) - Initialize inference engine.
- `InferenceEngine.predict_batch` (function) - Perform batch inference on all windows.
- `InferenceEngine.predict_realtime` (function) - Perform real-time inference on a single window.
- `InferenceEngine.predict_with_details` (function) - Perform inference and return detailed results as DataFrame.
- `ResultsExporter` (class) - Export inference results to CSV and JSON formats.
- `ResultsExporter.__init__` (function) - Initialize exporter.
- `ResultsExporter.export` (function) - Export all results to files.
- `InferencePipeline` (class) - Complete inference pipeline orchestrator.
- `InferencePipeline.__init__` (function) - Initialize pipeline.
- `InferencePipeline.run` (function) - Execute the complete inference pipeline.
- `parse_args` (function) - Parse command line arguments.
- `main` (function) - Main entry point.
**Inputs:**
- data/prepared/production_X.npy
- logs/inference/
- logs/inference/inference_YYYYMMDD_HHMMSS.log
**Outputs:**
- data/prepared/production_X.npy
- logs/inference/
- logs/inference/inference_YYYYMMDD_HHMMSS.log
**Dependencies:**
- src.utils.label_mapping
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/sensor_data_pipeline.py
**Purpose:** Provides sensor data pipeline logic for the ingestion part of the thesis MLOps pipeline.
**Stage:** ingestion
**Key functions/classes:**
- `ProcessingConfig` (class) - Configuration for data processing pipeline.
- `LoggerSetup` (class) - Sets up logging to console and rotating file.
- `LoggerSetup.__init__` (function) - Function implementing processing or utility logic.
- `LoggerSetup._setup_logging` (function) - Function implementing processing or utility logic.
- `LoggerSetup.get_logger` (function) - Function implementing processing or utility logic.
- `find_latest_sensor_pair` (function) - Locate the newest matching accelerometer/gyroscope Excel pair in data/raw.
- `SensorDataLoader` (class) - Loads, parses, and validates sensor data from Excel files.
- `SensorDataLoader.__init__` (function) - Initialize data loader with logger.
- `SensorDataLoader.load_sensor_data` (function) - Load sensor data from Excel file with error handling.
- `SensorDataLoader.normalize_column_names` (function) - Standardize column names based on sensor type.
- `SensorDataLoader.validate_columns` (function) - Validate that all required columns are present.
- `SensorDataLoader.parse_list_cell` (function) - Parse Excel cell containing array-like data into Python list.
- `SensorDataLoader.parse_list_columns` (function) - Apply list parsing to all array-like columns in dataframe.
- `SensorDataLoader.validate_row_lengths` (function) - Check if all list columns in a row have matching lengths.
- `SensorDataLoader.filter_valid_rows` (function) - Remove rows where list columns have mismatched lengths.
- `DataProcessor` (class) - Transforms and explodes sensor data, creates timestamps.
- `DataProcessor.__init__` (function) - Initialize data processor with logger.
- `DataProcessor.explode_dataframe` (function) - Explode list columns to create individual rows for each sample.
- `DataProcessor.create_base_time` (function) - Create base timestamp from timestamp and timestamp_ms columns.
- `DataProcessor.create_true_time` (function) - Create final timestamp by adding sample_time_offset to base_time.
- `DataProcessor.process_sensor_data` (function) - Complete processing pipeline for a single sensor.
- `SensorFusion` (class) - Aligns and merges accelerometer and gyroscope data by timestamp.
- `SensorFusion.__init__` (function) - Initialize sensor fusion with config and logger.
- `SensorFusion.merge_sensor_data` (function) - Merge accelerometer and gyroscope data based on timestamp alignment.
- `SensorFusion._analyze_merge_quality` (function) - Analyze and log the quality of sensor data alignment.
- `Resampler` (class) - Resamples merged data to fixed frequency and adds timestamps.
- `Resampler.__init__` (function) - Initialize resampler with config and logger.
- `Resampler.resample_data` (function) - Resample sensor data to exact target frequency.
- `Resampler.add_timestamp_columns` (function) - Add standardized timestamp columns to resampled data.
- `GravityRemovalPreprocessor` (class) - Removes gravity component from accelerometer data using high-pass filtering.
- `GravityRemovalPreprocessor.__init__` (function) - Initialize gravity removal preprocessor.
- `GravityRemovalPreprocessor._load_config` (function) - Load settings from YAML config file.
- `GravityRemovalPreprocessor._compute_filter_coefficients` (function) - Pre-compute Butterworth filter coefficients.
- `GravityRemovalPreprocessor.remove_gravity` (function) - Apply high-pass filter to remove gravity from acceleration data.
- `GravityRemovalPreprocessor.process_dataframe` (function) - Process DataFrame to remove gravity from accelerometer columns.
- `load_pipeline_config` (function) - Load pipeline configuration from YAML file.
- `DataExporter` (class) - Saves processed data and metadata to disk.
- `DataExporter.__init__` (function) - Initialize data exporter.
- `DataExporter.save_processed_data` (function) - Save all processed data and metadata.
- `SensorDataPipeline` (class) - Main orchestrator: runs the full preprocessing pipeline.
- `SensorDataPipeline.__init__` (function) - Initialize pipeline with all components.
- `SensorDataPipeline.process_sensor_files` (function) - Process accelerometer and gyroscope files through complete pipeline.
- `main` (function) - Function implementing processing or utility logic.
**Inputs:**
- config/pipeline_config.yaml
- data/preprocessed
- data/raw.
- logs/preprocessing/
- logs/preprocessing/pipeline.log
**Outputs:**
- config/pipeline_config.yaml
- data/preprocessed
- data/raw.
- logs/preprocessing/
- logs/preprocessing/pipeline.log
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/sensor_placement.py
**Purpose:** Sensor Placement Robustness Module Handles the problem of dominant vs.
**Stage:** sensor_placement
**Key functions/classes:**
- `SensorPlacementConfig` (class) - Configuration for sensor placement robustness.
- `AxisMirrorAugmenter` (class) - Augment training data by simulating hand-swap via axis mirroring.
- `AxisMirrorAugmenter.__init__` (function) - Function implementing processing or utility logic.
- `AxisMirrorAugmenter.mirror` (function) - Apply axis mirroring to a batch of windows.
- `AxisMirrorAugmenter.augment` (function) - Augment dataset by randomly applying axis mirroring.
- `HandDetector` (class) - Detect whether the sensor is on the dominant or non-dominant hand.
- `HandDetector.__init__` (function) - Function implementing processing or utility logic.
- `HandDetector.detect` (function) - Attempt to classify whether sensor is on dominant or non-dominant hand.
- `HandPerformanceReporter` (class) - Track and report model performance split by detected hand placement.
- `HandPerformanceReporter.report` (function) - Generate per-hand performance report.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/train.py
**Purpose:** HAR Model Training Module Production training module for Human Activity Recognition MLOps pipeline.
**Stage:** retraining
**Key functions/classes:**
- `TrainingConfig` (class) - Configuration for model training.
- `TrainingConfig.__post_init__` (function) - Function implementing processing or utility logic.
- `_make_scaler` (function) - Return a fresh scaler instance for the given normalization variant.
- `DataLoader` (class) - Load and prepare training data for HAR model.
- `DataLoader.__init__` (function) - Function implementing processing or utility logic.
- `DataLoader.load_training_data` (function) - Load labeled training data.
- `DataLoader.create_windows` (function) - Create sliding windows from sensor data.
- `DataLoader.prepare_data` (function) - Prepare data for training: extract features, encode labels, create windows.
- `DataLoader.get_scaler_config` (function) - Get scaler parameters for inference.
- `DataLoader.get_label_mapping` (function) - Get label index to activity name mapping.
- `HARModelBuilder` (class) - Build HAR model architectures.
- `HARModelBuilder.__init__` (function) - Function implementing processing or utility logic.
- `HARModelBuilder.create_1dcnn_bilstm` (function) - Create 1D-CNN-BiLSTM model matching the deployed pretrained checkpoint.
- `HARModelBuilder._build_v1` (function) - Architecture identical to the deployed pretrained model (499 K params).
- `HARModelBuilder._build_v2` (function) - Larger paper-inspired architecture (kept for future experimentation).
- `HARModelBuilder.get_callbacks` (function) - Get training callbacks.
- `HARTrainer` (class) - Main training pipeline for HAR model.
- `HARTrainer.__init__` (function) - Function implementing processing or utility logic.
- `HARTrainer.run_cross_validation` (function) - Run 5-fold stratified cross-validation.
- `HARTrainer.train_final_model` (function) - Train final model on all data.
- `HARTrainer._save_training_artifacts` (function) - Save all training artifacts.
- `HARTrainer.train` (function) - Full training pipeline.
- `DomainAdaptationTrainer` (class) - Extended trainer with domain adaptation for retraining scenarios.
- `DomainAdaptationTrainer.__init__` (function) - Function implementing processing or utility logic.
- `DomainAdaptationTrainer.retrain_with_adaptation` (function) - Retrain model with domain adaptation.
- `DomainAdaptationTrainer._retrain_pseudo_labeling` (function) - Robust pseudo-labeling with calibration, entropy gating, and class-balanced top-k.
- `DomainAdaptationTrainer._hist` (function) - Function implementing processing or utility logic.
- `DomainAdaptationTrainer._estimate_temperature` (function) - Simple temperature scaling via grid search on a source holdout.
- `DomainAdaptationTrainer._get_logits` (function) - Return pre-softmax logits from the final Dense layer.
- `DomainAdaptationTrainer.get_pre_dense` (function) - Function implementing processing or utility logic.
- `DomainAdaptationTrainer._retrain_mmd` (function) - Retrain with Maximum Mean Discrepancy loss.
- `DomainAdaptationTrainer._retrain_dann` (function) - Retrain with Domain-Adversarial Neural Network approach.
- `parse_args` (function) - Parse command line arguments.
- `main` (function) - Main entry point.
**Inputs:**
- data/prepared/config.json
- data/prepared/drift_samples.npy
- models/pretrained/fine_tuned_model_1dcnnbilstm.keras
**Outputs:**
- data/prepared/config.json
- data/prepared/drift_samples.npy
- models/pretrained/fine_tuned_model_1dcnnbilstm.keras
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/trigger_policy.py
**Purpose:** Automated Retraining Trigger Policy Module This module implements the decision logic for when to trigger model retraining based on monitoring metrics.
**Stage:** trigger
**Key functions/classes:**
- `AlertLevel` (class) - Alert severity levels.
- `TriggerAction` (class) - Possible trigger actions.
- `TriggerThresholds` (class) - Thresholds for triggering retraining decisions.
- `CooldownConfig` (class) - Cooldown configuration to prevent rapid successive triggers.
- `TriggerDecision` (class) - Result of trigger evaluation.
- `TriggerDecision.to_dict` (function) - Convert to dictionary for JSON serialization.
- `TriggerPolicyEngine` (class) - Main engine for evaluating retraining trigger policies.
- `TriggerPolicyEngine.__init__` (function) - Initialize trigger policy engine.
- `TriggerPolicyEngine._load_state` (function) - Load persistent state from file.
- `TriggerPolicyEngine._save_state` (function) - Save state to file.
- `TriggerPolicyEngine.evaluate` (function) - Evaluate monitoring report and decide on trigger action.
- `TriggerPolicyEngine._extract_confidence_metrics` (function) - Extract confidence metrics from monitoring report.
- `TriggerPolicyEngine._extract_temporal_metrics` (function) - Extract temporal metrics from monitoring report.
- `TriggerPolicyEngine._extract_drift_metrics` (function) - Extract drift metrics from monitoring report.
- `TriggerPolicyEngine._evaluate_confidence` (function) - Evaluate confidence metrics against thresholds.
- `TriggerPolicyEngine._evaluate_temporal` (function) - Evaluate temporal metrics against thresholds.
- `TriggerPolicyEngine._evaluate_drift` (function) - Evaluate drift metrics against thresholds.
- `TriggerPolicyEngine._aggregate_signals` (function) - Aggregate individual signals using voting logic.
- `TriggerPolicyEngine._apply_cooldowns` (function) - Apply cooldown logic to prevent rapid successive triggers.
- `TriggerPolicyEngine._update_state` (function) - Update persistent state after evaluation.
- `TriggerPolicyEngine.get_trigger_summary` (function) - Get summary of trigger state for reporting.
- `TriggerPolicyEngine.reset_state` (function) - Reset state (use after successful retraining).
- `ProxyModelValidator` (class) - Validate retrained model against old model using proxy metrics.
- `ProxyModelValidator.__init__` (function) - Initialize validator.
- `ProxyModelValidator.compare_models` (function) - Compare old and new model predictions using proxy metrics.
- `ProxyModelValidator._compute_proxy_metrics` (function) - Compute proxy metrics from predictions.
- `main` (function) - CLI for trigger policy evaluation.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/utils/__init__.py
**Purpose:** Utility modules for the HAR MLOps Pipeline.
**Stage:** utility
**Key functions/classes:**
- No functions/classes declared in this file.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.utils.common
- src.utils.main_utils
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/utils/artifacts_manager.py
**Purpose:** Artifacts Manager for HAR MLOps Production Pipeline Manages creation and organization of experiment artifacts.
**Stage:** utility
**Key functions/classes:**
- `ArtifactsManager` (class) - Manages experiment artifacts for each pipeline run.
- `ArtifactsManager.__init__` (function) - Initialize artifacts manager.
- `ArtifactsManager.initialize` (function) - Create all artifact directories for this run.
- `ArtifactsManager.get_stage_dir` (function) - Get directory for a specific stage.
- `ArtifactsManager.save_file` (function) - Copy a file to the appropriate stage directory.
- `ArtifactsManager.save_json` (function) - Save JSON data to stage directory.
- `ArtifactsManager.json_serializer` (function) - Handle non-serializable types.
- `ArtifactsManager.log_stage_completion` (function) - Log completion of a pipeline stage.
- `ArtifactsManager.finalize` (function) - Save final run metadata.
- `ArtifactsManager.get_latest_run_dir` (function) - Get the most recent run directory.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/utils/common.py
**Purpose:** Provides common logic for the utility part of the thesis MLOps pipeline.
**Stage:** utility
**Key functions/classes:**
- `ensure_dir` (function) - Create directory (and parents) if they don't exist.
- `read_yaml` (function) - Read a YAML file and return its contents as a dictionary.
- `write_yaml` (function) - Write a dictionary to a YAML file.
- `read_json` (function) - Read a JSON file and return its contents.
- `write_json` (function) - Write data to a JSON file.
- `load_numpy` (function) - Load a `.npy` file.
- `save_numpy` (function) - Save a NumPy array to a `.npy` file.
- `get_timestamp` (function) - Return current UTC-naive timestamp string.
- `validate_file_exists` (function) - Raise ``FileNotFoundError`` if *path* does not exist.
- `get_file_size` (function) - Return human-readable file size string.
**Inputs:**
- Reads runtime-provided files/paths (not hardcoded in this file).
**Outputs:**
- Writes runtime-generated files/artifacts (paths configured at runtime).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/utils/config_loader.py
**Purpose:** src/utils/config_loader.py Load runtime config overrides from a YAML file (or $HAR_PIPELINE_OVERRIDES env var) and apply them to pipeline config dataclass instances.
**Stage:** utility
**Key functions/classes:**
- `load_yaml_overrides` (function) - Load YAML overrides from *path*, $HAR_PIPELINE_OVERRIDES, or the default path.
- `apply_overrides` (function) - Apply a flat dict of field-name → value overrides to a dataclass instance.
- `load_monitoring_config` (function) - Return PostInferenceMonitoringConfig with YAML/env overrides applied.
- `load_trigger_config` (function) - Return TriggerEvaluationConfig with YAML/env overrides applied.
**Inputs:**
- /config/pipeline_overrides.yaml
- config/pipeline_overrides.yaml
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.entity.config_entity
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/utils/label_mapping.py
**Purpose:** Shared activity label mapping utilities.
**Stage:** utility
**Key functions/classes:**
- `_default_metadata_path` (function) - Function implementing processing or utility logic.
- `_validate_mapping` (function) - Function implementing processing or utility logic.
- `_load_mapping_from_metadata` (function) - Function implementing processing or utility logic.
- `load_activity_mapping` (function) - Load canonical mappings.
- `get_activity_classes` (function) - Return id -> activity mapping.
- `get_class_to_index` (function) - Return activity -> id mapping.
**Inputs:**
- data/prepared/config.json
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/utils/main_utils.py
**Purpose:** Provides main utils logic for the utility part of the thesis MLOps pipeline.
**Stage:** utility
**Key functions/classes:**
- `get_activity_labels` (function) - Return the canonical list of 11 HAR activity labels.
- `get_sensor_columns` (function) - Return the 6 sensor-axis column names used throughout the pipeline.
- `load_model` (function) - Load a Keras ``.keras`` (or ``.h5``) model with error handling.
- `save_model` (function) - Save a Keras model to *path* (creates parent dirs).
- `load_predictions` (function) - Load a predictions CSV in the standardised pipeline format.
- `load_config_from_yaml` (function) - Load pipeline configuration from a YAML file.
- `compute_class_distribution` (function) - Compute class frequency distribution from integer predictions.
- `setup_stage_logger` (function) - Create a logger that writes to both console and a stage-specific file.
- `archive_file` (function) - Copy *src* into *archive_dir* with a timestamp suffix.
**Inputs:**
- config/pipeline_config.yaml
- models/retrained.keras
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- src.utils.common
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/utils/production_optimizations.py
**Purpose:** Provides production optimizations logic for the utility part of the thesis MLOps pipeline.
**Stage:** utility
**Key functions/classes:**
- `load_model_cached` (function) - Load a Keras model with caching.
- `clear_model_cache` (function) - Clear all cached models (e.g., after retraining).
- `predict_batch_optimized` (function) - Run vectorized batch prediction with optimal batch size.
- `convert_to_tflite` (function) - Convert Keras model to TF-Lite with optional INT8 quantization.
- `representative_dataset` (function) - Function implementing processing or utility logic.
- `TFLitePredictor` (class) - Fast inference using TF-Lite runtime.
- `TFLitePredictor.__init__` (function) - Function implementing processing or utility logic.
- `TFLitePredictor.predict` (function) - Run inference on batch of windows.
- `TFLitePredictor.predict_batch` (function) - Predict in batches (memory-friendly for large datasets).
- `benchmark_models` (function) - Benchmark model inference speed and caching performance.
- `main` (function) - Function implementing processing or utility logic.
**Inputs:**
- models/pretrained/fine_tuned_model_1dcnnbilstm.keras
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/utils/temporal_metrics.py
**Purpose:** Utilities for strict temporal metrics computed on ordered session streams.
**Stage:** utility
**Key functions/classes:**
- `_validate_shapes` (function) - Function implementing processing or utility logic.
- `_validate_strict_session_order` (function) - Ensure records are grouped by session and strictly ordered by timestamp.
- `flip_rate_per_session` (function) - Compute strict per-session flip rate.
- `summarize_rates` (function) - Aggregate session-level rates for reporting.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

---
## FILE: src/wasserstein_drift.py
**Purpose:** Wasserstein-Based Drift Detection Implements Wasserstein (Earth Mover's) distance for distribution drift detection, complementing PSI and KS-test in the monitoring pipeline.
**Stage:** drift
**Key functions/classes:**
- `WassersteinDriftConfig` (class) - Configuration for Wasserstein-based drift detection.
- `WassersteinDriftDetector` (class) - Detects distribution drift using the 1-Wasserstein (Earth Mover's) distance.
- `WassersteinDriftDetector.__init__` (function) - Function implementing processing or utility logic.
- `WassersteinDriftDetector.wasserstein_1d` (function) - Compute 1-Wasserstein distance between two 1D samples.
- `WassersteinDriftDetector.detect` (function) - Run per-channel Wasserstein drift detection.
- `WassersteinChangePointDetector` (class) - Detect change points in a stream of Wasserstein distances.
- `WassersteinChangePointDetector.__init__` (function) - Function implementing processing or utility logic.
- `WassersteinChangePointDetector.detect_change_points` (function) - Detect change points in a Wasserstein distance time series.
- `MultiResolutionDriftAnalyzer` (class) - Analyze drift at multiple time resolutions: - Window-level  (per inference batch) - Hourly        (aggregate over 1 hour) - Daily         (aggregate over 1 day) Useful for distinguishing transient noise from persistent drift.
- `MultiResolutionDriftAnalyzer.__init__` (function) - Function implementing processing or utility logic.
- `MultiResolutionDriftAnalyzer.analyze` (function) - Compute drift at window-level, then aggregate to coarser resolutions.
- `MultiResolutionDriftAnalyzer._compute_trend` (function) - Simple linear trend classification.
- `compute_integrated_drift_report` (function) - Compute a combined drift report using PSI, KS-test, and Wasserstein.
- `_compute_psi` (function) - Population Stability Index.
- `_consensus` (function) - Simple 2-of-3 consensus across drift signals.
**Inputs:**
- No explicit file inputs detected (may rely on runtime parameters).
**Outputs:**
- No explicit file outputs detected (may return values or log only).
**Dependencies:**
- No internal src dependencies imported explicitly.
**Known issues or TODOs:**
- No explicit TODO/FIXME markers detected.
---

## PIPELINE GAPS FOUND
### Imported internal modules missing on disk
- `src.core.exception` imported by: src/_wave2_archive/pipeline/inference_pipeline.py
- `src.core.logger` imported by: src/_wave2_archive/pipeline/inference_pipeline.py
- `src.pipeline.inference_pipeline` imported by: src/pipeline/__init__.py

### Stages with no corresponding mapped file
- None. Every requested stage category has at least one mapped file.

### Obvious missing connections between stages
- src/deployment_manager.py still references prometheus_metrics.py in its image build include list, while observability modules were removed from active runtime.

### dvc.yaml check
- dvc.yaml does not exist in this repository snapshot.
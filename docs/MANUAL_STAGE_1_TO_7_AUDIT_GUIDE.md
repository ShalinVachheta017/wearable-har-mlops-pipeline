# Manual Stage 1 To 7 Audit Guide

This guide is for manually inspecting the first seven stages of the wearable IMU HAR MLOps pipeline when predictions collapse toward `hand_tapping`.

Do not start with retraining. First prove whether the data reaching the model is correct.

## Core Contracts To Keep In Mind

- Sensor channel order must be: `Ax, Ay, Az, Gx, Gy, Gz`
- Accelerometer should be in `m/s^2` by the time scaling/model input is prepared.
- Gyroscope should stay in `deg/s` unless a training artifact proves otherwise.
- Sampling rate should be `50 Hz`.
- Window size should be `200` samples.
- Overlap should be `50%`, so step size should be `100` samples.
- Model input shape should be `(N, 200, 6)`.
- Model output shape should be `(N, 11)`.
- Class index `4` should map only to `hand_tapping`.
- `production_X.npy` and `production_y.npy`, if both exist, must have the same first dimension.

## Evidence Folder

Before changing or deleting anything, save copies or screenshots of:

- `logs/pipeline/`
- `artifacts/`
- `outputs/`
- `data/processed/fused_<dataset_name>_50Hz.csv`
- `data/prepared/production_X.npy`
- `data/prepared/production_y.npy`, if present
- latest prediction CSV in `data/prepared/predictions/`
- latest monitoring report in `outputs/monitoring/`
- trigger decision JSON/log output

Do not clean generated files until the audit is complete.

---

## Stage 1: Data Ingestion

### 1. Stage Purpose

Convert raw accelerometer and gyroscope files, or one already-fused input CSV, into a dataset-specific fused sensor CSV for downstream stages.

### 2. Main Component File

- `src/components/data_ingestion.py`

### 3. Connected Config, Entity, Artifact Files

- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`
- `config/pipeline_config.yaml`
- `src/pipeline/production_pipeline.py`
- `run_pipeline.py`

### 4. Input Files

- Raw accelerometer file
- Raw gyroscope file
- Or a direct fused CSV passed through `--input-csv`
- Common labeled CSV: `data/all_users_data_labeled.csv`

### 5. Output Files

- `data/processed/fused_<dataset_name>_50Hz.csv`

Stage 1 should not create or refresh `data/processed/sensor_fused_50Hz.csv`. If that file exists, treat it as legacy evidence unless a current command explicitly uses it.

Current Stage 1 status:

- Stage 1 refactor is complete as of 2026-04-30.
- Active component file: `src/components/data_ingestion.py`.
- Current file length: `573` lines, including thesis-style method docstrings.
- Latest verified fused output: `data/processed/fused_2025_03_23_15_23_10_50Hz.csv`.
- Latest verified shape: `(181509, 9)`.
- Latest verified median timestamp gap: `0.020000` seconds.
- Next manual audit stage: Stage 2 Data Validation.

### 6. Expected Columns Or Shapes

Expected sensor columns after ingestion:

- `Ax`
- `Ay`
- `Az`
- `Gx`
- `Gy`
- `Gz`

Useful timestamp columns may include:

- `timestamp`
- `true_time`
- `timestamp_ms`
- `timestamp_iso`

If labeled input is used, expected label/user columns may include:

- `activity`
- `User`

### 7. Expected Units

- Accelerometer may arrive as `milliG` or `m/s^2`.
- Gyroscope should remain `deg/s`.
- Ingestion should not silently change gyroscope units.

### 8. What The Stage Does Internally

Stage 1 chooses one input mode: direct fused CSV/Excel, explicit accelerometer plus gyroscope files, or the newest matched accelerometer/gyroscope pair from `data/raw/`. For raw pairs it normalizes axes, parses timestamps/list cells, aligns streams with nearest-time `merge_asof` using the configured tolerance, resamples to `50 Hz`, and writes one dataset-specific `fused_<dataset_name>_50Hz.csv`.

For direct CSV/Excel input, it normalizes existing sensor columns and rewrites the file to the dataset-specific fused path, but it does not truly resample the direct input. The path passed to Stage 2 is always `DataIngestionArtifact.fused_csv_path`.

### 9. What Can Go Wrong

The main failure risk is bad input identity: the wrong accel/gyro pair can be selected or an explicit pair can be mismatched, because the code trusts the provided files and only auto-pairs by filename prefix. Timestamp parsing, `merge_asof` tolerance, direct-input bypass of resampling, and column alias detection can also produce a fused file that looks valid but is temporally or semantically wrong.

Label handling can go wrong if a non-ground-truth column is accepted as a label, although the current code uses shared label-candidate filters to reduce that risk.

### 10. Symptoms If This Stage Is Wrong

Downstream symptoms are usually abnormal window counts, large timestamp gaps, NaNs, constant/near-constant channels, or sensor values that are in the wrong physical range before Stage 2/3. Later stages may show class collapse, high-confidence impossible predictions, or strong drift alerts even when the model code itself is not the root cause.

### 11. Manual Checks

Open the exact `DataIngestionArtifact.fused_csv_path` from the current run, not the legacy `sensor_fused_50Hz.csv`, and verify the six channels, row count, timestamp ordering, duplicate timestamps, median gap near `20 ms`, maximum gap, and basic min/max/mean/std for every sensor channel. Also check the run log for the input mode, source file path, merge match percentage for raw pairs, and whether a label column was detected.

### 12. Questions To Ask While Reading The Code

- How does the code choose the accelerometer file? Explicit `--accel-file` wins; otherwise `_find_latest_sensor_pair()` searches only `data/raw/` for filenames containing `accelerometer`.
- How does the code choose the gyroscope file? Explicit `--gyro-file` wins; otherwise the code matches gyroscope files by the sanitized filename prefix before `gyroscope`.
- Does it guarantee both files belong to the same recording/session? Only partly: auto-discovery pairs by filename prefix, but explicit files are trusted and must be manually checked.
- Which timestamp column is trusted? `true_time` is used if already present; otherwise the code derives it from `timestamp`, `timestamp_iso`, or `timestamp_ms`, with optional `sample_time_offset`.
- Is `merge_asof` using a reasonable tolerance? The configured default is `merge_tolerance_ms = 1`, which is strict and should be checked against the raw device timestamp jitter.
- Is the merge direction `nearest`, `backward`, or `forward`? The current raw-pair merge uses `direction="nearest"`.
- Is the resampling period exactly `20 ms`? Yes for raw pairs at the default `target_hz = 50`, because `period_ms = round(1000 / target_hz)`.
- Does direct CSV input bypass important validation? Yes, direct input is normalized and rewritten but not resampled, so its real sampling rate must be manually verified before Stage 2/3.
- Does ingestion preserve labels only when labels are real ground truth? It preserves one detected label column using shared label-candidate filters, but the audit still must confirm the label is real ground truth and not metadata or pseudo-label output.

### 13. Evidence To Save Before Moving On

- Row count of fused CSV.
- Column list.
- Timestamp gap summary.
- Duplicate timestamp count.
- Sensor min/max/mean/std before transformation.
- Merge match percentage from logs.
- Path of the exact fused CSV passed to Stage 2.

---

## Stage 2: Data Validation

### 1. Stage Purpose

Check that the fused sensor CSV is safe to transform and send to the model.

### 2. Main Component File

- `src/components/data_validation.py`

### 3. Connected Config, Entity, Artifact Files

- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`
- `config/pipeline_config.yaml`
- `src/pipeline/production_pipeline.py`

### 4. Input Files

- The fused CSV path carried by `DataIngestionArtifact.fused_csv_path`.
- After the Stage 1 refactor, this should be dataset-specific:
  - `data/processed/fused_<dataset_name>_50Hz.csv`
  - Example: `data/processed/fused_2025_03_23_15_23_10_50Hz.csv`
- Do not treat `data/processed/sensor_fused_50Hz.csv` as the main Stage 2 input. If it exists, it is legacy evidence unless a current run explicitly points to it.

### 5. Output Files

- Validation artifact in pipeline result.
- Validation report in `artifacts/` for the run.
- Logs under `logs/pipeline/`.

Folders to check:

- `data/processed/` for the exact fused CSV from Stage 1.
- `artifacts/<run_id>/data_ingestion/` for the saved Stage 1 evidence copy.
- `artifacts/<run_id>/validation/validation_report.json` for Stage 2 result evidence.
- `logs/` or console output for validation warnings and abort messages.

### 6. Expected Columns Or Shapes

Required columns:

- `Ax`
- `Ay`
- `Az`
- `Gx`
- `Gy`
- `Gz`

Stage 1 currently writes timestamp evidence as:

- `true_time`
- `timestamp_ms`
- `timestamp_iso`

Important audit point:

- Stage 2 now detects timestamp columns in this order: `true_time`, `timestamp`, `timestamp_iso`, `timestamp_ms`.
- The validation report should include `timestamp_column`, `actual_frequency_hz`, timestamp gap stats, duplicate timestamp count, and acceleration unit detection.
- If `actual_frequency_hz` is missing from the report, stop and inspect Stage 2 before moving forward.

### 7. Expected Units

Validation thresholds usually assume:

- Accelerometer in `m/s^2`
- Gyroscope in `deg/s`

This matters because raw `milliG` acceleration can look like broken extreme values if it is checked as `m/s^2`. Stage 2 should now detect whether accelerometer data looks like `milliG` or `m/s^2` and report `acceleration_unit_detected`.

Threshold evidence note:

- `max_missing_ratio = 0.05`: use as a conservative data-quality rule. Missing-data literature does not define a universal cutoff, but 5% is commonly treated as low missingness; cite Dong and Peng (2013) summarizing Schafer (1999), not as a sensor-specific law.
- `max_acceleration_ms2 = 50.0`: use as a sensor sanity guard, not a mentor-paper threshold. `50 m/s^2` is about `5.1 g`; Garmin acceleration arrives in `milliG`, and common IMU full-scale ranges include `+/-2g`, `+/-4g`, `+/-8g`, and `+/-16g`.
- `max_gyroscope_dps = 500.0`: use as a conservative gyro sanity guard. Garmin gyroscope data is in `deg/sec`, and common IMU full-scale ranges include `+/-250`, `+/-500`, `+/-1000`, and `+/-2000 dps`.
- `sampling_rate_tolerance = 0.1`: use as a project QA tolerance around the expected `50 Hz` rate. The `50 Hz` target is defensible from train/serve parity and HAR literature; the `10%` band is an engineering tolerance to catch wrong-rate data while tolerating small timestamp jitter.

Do not write that these exact four thresholds were taken from the mentor paper. The defensible wording is: "The validation thresholds are configurable engineering guardrails supported by sensor documentation, common HAR sampling practice, and general missing-data practice."

### 8. What The Stage Does Internally

- Loads the fused CSV.
- Checks required sensor columns.
- Checks numeric dtypes.
- Checks missing-value ratio.
- Detects accelerometer unit (`milliG` vs `m/s^2`).
- Checks accelerometer range using the detected unit.
- Checks gyroscope range.
- Checks timestamp parseability, duplicates, monotonic gaps, large gaps, and sampling frequency.
- Returns valid/invalid status.
- Pipeline aborts if validation is invalid.

### 9. What Can Go Wrong

- Sampling frequency problems are treated as warnings, so large deviations still require manual review.
- Extreme value ranges are warnings instead of hard failures.
- Timestamp column is missing or not parseable, so frequency cannot be checked.
- Wrong units pass because thresholds are too loose.
- Broken data passes if values are numeric but physically impossible.
- Accelerometer and gyroscope extreme ranges are warnings, not hard errors.
- Stage 2 can pass while Stage 3 still receives wrong-unit data.

### 10. Symptoms If This Stage Is Wrong

- Stage 3 processes wrong-unit data.
- Windowed data has huge or tiny values.
- Model becomes overconfident in one class.
- Monitoring detects drift but root cause is actually invalid input.

### 11. Manual Checks

- Confirm validator sees the same file produced by Stage 1.
- Confirm the file path is `fused_<dataset_name>_50Hz.csv`, not stale `sensor_fused_50Hz.csv`.
- Confirm required columns match transformation expectations.
- Confirm missing-value ratio for each channel.
- Confirm accelerometer max absolute value is realistic.
- Confirm gyroscope max absolute value is realistic.
- Confirm `timestamp_column` is `true_time` for Stage 1 fused output.
- Confirm `actual_frequency_hz` is close to `50`.
- Confirm `acceleration_unit_detected` matches the file you are validating.
- Confirm invalid data aborts the pipeline.

### 12. Questions To Ask While Reading The Code

- Does validation fail or only warn for bad sampling rate?
- Does validation fail or only warn for impossible sensor ranges?
- Which timestamp column is used?
- What happens when timestamp parsing fails?
- Are NaNs filled before validation or after validation?
- Are unit assumptions documented near thresholds?
- Does Stage 2 detect `milliG` correctly before applying the acceleration threshold?
- Are range warnings strong enough for tomorrow's audit, or do they only warn and continue?

### 13. Evidence To Save Before Moving On

- Validation status.
- Validation errors.
- Validation warnings.
- Per-channel missing ratios.
- Per-channel max absolute values.
- Actual detected frequency.
- Exact fused CSV path passed from Stage 1 to Stage 2.
- Whether the frequency check used `timestamp`, `true_time`, or was skipped.

---

## Stage 3: Data Transformation

### 1. Stage Purpose

Convert validated fused sensor data into model-ready windows.

This is the most important stage for the `hand_tapping` collapse audit.

### 2. Main Component File

- `src/components/data_transformation.py`
- `src/preprocess_data.py`
- `src/utils/scaler.py`

### 3. Connected Config, Entity, Artifact Files

- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`
- `config/pipeline_config.yaml`
- `data/prepared/scaler_train_only.json`
- `data/prepared/config.json`
- `src/config.py`
- `src/utils/label_mapping.py`
- `src/pipeline/production_pipeline.py`

Concrete Stage 3 connections:

- Input artifact:
  - `DataIngestionArtifact.fused_csv_path`
  - optional `DataValidationArtifact`, mainly for traceability
- Config object:
  - `DataTransformationConfig`
  - `PipelineConfig.data_prepared_dir`
- Output artifact:
  - `DataTransformationArtifact.production_X_path`
  - `DataTransformationArtifact.production_y_path`, only when labels are present
  - `DataTransformationArtifact.metadata_path`
- Runtime helpers:
  - `src.preprocess_data.UnitDetector`
  - `src.preprocess_data.GravityRemover`
  - `src.preprocess_data.DomainCalibrator`
  - `src.preprocess_data.UnifiedPreprocessor`
  - `src.utils.scaler.assert_scaler_integrity`
  - `src.utils.label_mapping.get_class_to_index`

### 4. Input Files

- Fused CSV from Stage 1:
  - `data/processed/fused_<dataset_name>_50Hz.csv`
  - Example: `data/processed/fused_2025_03_23_15_23_10_50Hz.csv`
- Canonical scaler JSON:
  - `data/prepared/scaler_train_only.json`
- Optional direct override:
  - `DataTransformationConfig.input_csv`
  - If this is set, it overrides `DataIngestionArtifact.fused_csv_path`.

Folders to check:

- `data/processed/` for Stage 1 fused input.
- `data/prepared/` for `production_X.npy`, optional `production_y.npy`, `production_metadata.json`, and scaler files.
- `artifacts/<run_id>/data_transformation/` for saved Stage 3 evidence copies.
- `logs/preprocessing/` or console output for unit detection, normalization, window count, and warnings.

### 5. Output Files

- `data/prepared/production_X.npy`
- `data/prepared/production_y.npy`, only if labels are present
- `data/prepared/production_metadata.json`

### 6. Expected Columns Or Shapes

Input sensor columns:

- `Ax, Ay, Az, Gx, Gy, Gz`

Output:

- `production_X.npy`: `(N, 200, 6)`
- `production_y.npy`: `(N,)`, if labeled
- `production_metadata.json`: one entry per window

Channel order must be:

1. `Ax`
2. `Ay`
3. `Az`
4. `Gx`
5. `Gy`
6. `Gz`

### 7. Expected Units

Before normalization:

- Accelerometer: `m/s^2`
- Gyroscope: `deg/s`

After normalization:

- By default, z-score scaled values using the train-only scaler.
- Still verify `normalization_variant` inside `data/prepared/scaler_train_only.json`; that JSON decides the actual runtime variant.

Gyroscope should not be converted to radians unless the model was trained that way.

Important audit point:

- Stage 3 unit detection converts accelerometer only.
- Gyroscope channels should remain in `deg/s`.
- If `enable_gravity_removal` or `enable_calibration` is enabled, the code also runs accelerometer unit detection before those operations.
- `DataTransformationConfig.normalization_variant` is logged, but the actual scaler variant is read from `data/prepared/scaler_train_only.json`.

### 8. What The Stage Does Internally

- Loads the fused CSV.
- Detects data format and sensor columns.
- Optionally detects accelerometer units.
- Converts accelerometer from `milliG` to `m/s^2` when needed.
- Does not convert gyroscope units by default.
- Optionally removes gravity.
- Optionally applies domain calibration.
- Optionally applies StandardScaler/Z-score normalization.
- Encodes activity labels if labeled data is present.
- Creates windows of 200 samples.
- Uses 50% overlap, step size 100 samples.
- Saves X, y, and metadata.

Current default settings to verify tomorrow:

- `enable_unit_conversion=True`
- `enable_gravity_removal=False`
- `enable_calibration=False`
- `enable_normalization=True`
- `window_size=200`
- `overlap=0.5`
- `sensors=["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]`

### 9. What Can Go Wrong

- Unit conversion is applied twice.
- Unit conversion is skipped when raw acceleration is actually `milliG`.
- Gyroscope is converted even though model expects `deg/s`.
- Gravity removal is enabled but model was trained with gravity included.
- Gravity removal is disabled but model was trained with gravity removed.
- Calibration shifts production data away from the training distribution.
- Wrong scaler is loaded.
- Scaler was fit on all users instead of train-only users.
- Normalization is applied twice.
- Normalization is skipped when model expects scaled input.
- Channel order changes.
- Window size is not 200.
- Overlap is not 50%.
- Labels are windowed differently from features.
- `production_X.npy` and `production_y.npy` lengths differ.
- `DataTransformationConfig.input_csv` points to a different CSV than the Stage 1 artifact.
- A stale `production_y.npy` remains from an older labeled run even though the current run is unlabeled.
- The scaler integrity check passes dimensions but the input has already been normalized once before Stage 3.
- The fused CSV contains `true_time` but no `timestamp_iso`, so metadata loses timestamp start/end fields.

### 10. Symptoms If This Stage Is Wrong

- Model predicts mostly `hand_tapping`.
- Mean confidence is high but accuracy is low.
- `production_X.npy` channel means/stds look raw when expected scaled.
- `production_X.npy` channel means/stds look scaled twice.
- One or more channels are all zero or constant.
- NaN or inf exists in prepared windows.
- Evaluation accuracy is meaningless because X and y lengths differ.

### 11. Manual Checks

- Open `config/pipeline_config.yaml`.
- Open `src/entity/config_entity.py` and check `DataTransformationConfig`.
- Open `src/components/data_transformation.py` and confirm `csv_path = self.config.input_csv or self.ingestion_artifact.fused_csv_path`.
- Check `enable_unit_conversion`.
- Check `enable_gravity_removal`.
- Check `enable_calibration`.
- Check `enable_normalization`.
- Open `data/prepared/scaler_train_only.json`.
- Confirm scaler has six means and six scales.
- Confirm scaler sensor order matches `Ax, Ay, Az, Gx, Gy, Gz`.
- Confirm scaler was fit on intended training users only.
- Load `production_X.npy` and print shape.
- Load `production_y.npy`, if present, and print shape.
- Flatten X to `(N * 200, 6)` and calculate min/max/mean/std per channel.
- Confirm no NaN.
- Confirm no inf.
- Confirm no constant channel.
- Confirm window metadata count equals number of windows.
- Confirm `production_y.npy` timestamp and length belong to the current run before using it for evaluation.
- Confirm `DataTransformationArtifact.production_y_path` is `None` for unlabeled data.

### 12. Questions To Ask While Reading The Code

- Which scaler file is actually loaded?
- Does code use `scaler_train_only.json` or old `config.json`?
- Does the model expect raw, unit-converted, or z-score scaled input?
- Does the code know whether acceleration is `milliG` or `m/s^2`?
- Does unit detection only touch accelerometer columns?
- Is gyroscope left in `deg/s`?
- Are gravity removal and calibration disabled by default?
- Is channel order preserved from CSV to NumPy?
- Is windowing deterministic?
- Is the label for a window assigned by majority vote?
- Is `production_y.npy` overwritten only when the current run is labeled?
- Is stale `production_y.npy` ignored when the artifact says the current run has no labels?
- Does `DataTransformationConfig.input_csv` accidentally bypass the Stage 1 fused output?

### 13. Evidence To Save Before Moving On

- Transformation config values.
- Scaler path and scaler statistics.
- `production_X.npy` shape.
- `production_y.npy` shape, if present.
- Per-channel stats after transformation.
- NaN/inf counts.
- Window size and step size.
- First five metadata entries.
- Exact source CSV path used by Stage 3.
- `DataTransformationArtifact` values:
  - `production_X_path`
  - `production_y_path`
  - `metadata_path`
  - `n_windows`
  - `unit_conversion_applied`
  - `gravity_removal_applied`
  - `calibration_applied`

### 14. Tomorrow Start Pack For Stages 2 And 3

Start from the exact Stage 1 output created yesterday:

- `data/processed/fused_2025_03_23_15_23_10_50Hz.csv`

Stage 2 first checks:

- Open `src/components/data_validation.py`.
- Confirm it reads `self.ingestion_artifact.fused_csv_path`.
- Confirm required columns are `Ax, Ay, Az, Gx, Gy, Gz`.
- Confirm range thresholds are:
  - acceleration max abs `50.0`
  - gyroscope max abs `500.0`
  - missing ratio `0.05`
  - expected frequency `50.0`
- Check whether frequency validation is actually running from `true_time`.
- Check whether `acceleration_unit_detected` is `milliG` for raw Garmin fused output, or `m/s2` for already converted data.

Stage 3 first checks:

- Open `src/components/data_transformation.py`.
- Confirm Stage 3 input path is the Stage 1 fused CSV unless `DataTransformationConfig.input_csv` overrides it.
- Open `src/preprocess_data.py`.
- Confirm `UnitDetector` touches only accelerometer columns.
- Confirm `UnifiedPreprocessor.detect_data_format()` accepts standard production columns `Ax, Ay, Az, Gx, Gy, Gz`.
- Confirm `UnifiedPreprocessor.normalize_data()` loads `data/prepared/scaler_train_only.json`.
- Confirm `UnifiedPreprocessor.create_windows()` uses `window_size=200` and `step_size=100`.

Do not begin Stage 4 until these are saved:

- Stage 2 validation report.
- Timestamp gap summary from `true_time`.
- Fused CSV per-channel stats before Stage 3.
- `production_X.npy` shape.
- `production_X.npy` per-channel stats after Stage 3.
- `production_metadata.json` row count.
- `production_y.npy` status: current valid labels, or stale/ignore.

---

## Stage 4: Model Inference

### 1. Stage Purpose

Load the model and run predictions on `production_X.npy`.

### 2. Main Component File

- `src/components/model_inference.py`
- `src/run_inference.py`

### 3. Connected Config, Entity, Artifact Files

- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`
- `src/config.py`
- `src/utils/label_mapping.py`
- `config/pipeline_config.yaml`

### 4. Input Files

- `data/prepared/production_X.npy`
- Model file, commonly `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`

### 5. Output Files

- Prediction CSV in `data/prepared/predictions/`
- Probability `.npy` file in `data/prepared/predictions/`
- Prediction metadata JSON in `data/prepared/predictions/`
- `production_predictions_fresh.npy`

### 6. Expected Columns Or Shapes

Input:

- `production_X.npy`: `(N, 200, 6)`

Model:

- input shape: `(None, 200, 6)`
- output shape: `(None, 11)`

Prediction CSV should contain:

- `window_id`
- `predicted_class`
- `predicted_activity`
- `confidence`
- probability columns for all 11 classes

### 7. Expected Units

The model input must match the training input space exactly:

- same unit conversion
- same gravity setting
- same calibration setting
- same scaler
- same channel order

### 8. What The Stage Does Internally

- Loads `production_X.npy`.
- Loads Keras model.
- Checks model input/output shape.
- Runs `model.predict`.
- Applies `argmax` over class probabilities.
- Extracts max probability as confidence.
- Maps class index to activity name.
- Saves predictions and probabilities.

### 9. What Can Go Wrong

- Wrong model file is loaded.
- Model expects a different scaler.
- Model expects raw input but receives scaled input.
- Model expects scaled input but receives raw input.
- Model output class order differs from local mapping.
- Probability columns are mislabeled.
- Batch inference receives wrong shape.
- Prediction CSV and probability `.npy` disagree.

### 10. Symptoms If This Stage Is Wrong

- Most predictions become `hand_tapping`.
- Model is confidently wrong.
- Probability shape is not `(N, 11)`.
- Predicted class index does not match predicted activity name.
- Confidence is high but entropy is low and one class dominates.

### 11. Manual Checks

- Confirm model path in config and logs.
- Confirm file size and timestamp of model file.
- Print model input shape.
- Print model output shape.
- Print `production_X.npy` shape.
- Confirm probability matrix shape.
- Confirm `argmax(probabilities)` equals `predicted_class`.
- Confirm `predicted_class == 4` maps to only `hand_tapping`.
- Count prediction distribution.
- Calculate dominant class percentage.
- Print top-3 probabilities for first 20 windows.

### 12. Questions To Ask While Reading The Code

- Which model path is selected by default?
- Can CLI `--model` override it?
- Does inference validate `(N, 200, 6)` strictly or only warn?
- Does it use softmax output directly?
- Are class names loaded from one canonical mapping?
- Are probabilities saved before any post-processing?
- Is confidence simply max probability?

### 13. Evidence To Save Before Moving On

- Loaded model path.
- Model input/output shape.
- `production_X.npy` shape.
- Probability matrix shape.
- Prediction distribution.
- Dominant class and percentage.
- Mean confidence.
- Top-3 probabilities for first 20 windows.

---

## Stage 5: Model Evaluation

### 1. Stage Purpose

Summarize Stage 4 predictions, expose dominant-class collapse, report confidence/uncertainty/temporal behavior, and compute supervised metrics only when a proven paired label array exists.

### 2. Main Component File

- `src/components/model_evaluation.py`

Current state: Stage 5 runtime logic lives only in `src/components/model_evaluation.py`. The older `src/evaluate_predictions.py` file has been removed.

### 3. Connected Config, Entity, Artifact Files

- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`
- `src/pipeline/production_pipeline.py`
- `src/utils/label_mapping.py`

### 4. Input Files

- Prediction CSV from Stage 4.
- Optional labels, usually `data/prepared/production_y.npy`.
- Stage 4 artifact paths, especially:
  - `ModelInferenceArtifact.predictions_csv_path`
  - `ModelInferenceArtifact.predictions_npy_path`
  - `ModelInferenceArtifact.probabilities_npy_path`
  - `ModelInferenceArtifact.inference_report_path`

### 5. Output Files

- Evaluation JSON report.
- Evaluation text report.
- Evaluation summary in artifacts.
- `ModelEvaluationArtifact` with:
  - `distribution_summary`
  - `confidence_summary`
  - `has_labels`
  - `classification_metrics`
  - `dominant_class`
  - `dominant_pct`
  - `distribution_dominance_warning`

### 6. Expected Columns Or Shapes

Prediction CSV should include:

- `predicted_class`
- `predicted_activity`
- `confidence`
- `confidence_level`
- `is_uncertain`
- `entropy`
- `top2_margin`
- probability columns such as `prob_hand_tapping`

If labels exist:

- number of labels must equal number of predictions.
- labels should be one-dimensional integer class IDs.
- label IDs should be in the same mapping as `src/utils/label_mapping.py`.

### 7. Expected Units

No physical units are used here. This stage operates on predictions and labels.

### 8. What The Stage Does Internally

- Loads prediction CSV.
- Computes prediction distribution.
- Computes confidence statistics.
- Detects dominant class.
- Computes uncertainty summary.
- Computes temporal transition summary.
- If labels exist, computes classification metrics.
- Passes collapse signals forward.
- Uses the shared label mapping from `src/utils/label_mapping.py`.
- Writes reports through the evaluation backend.

### 9. What Can Go Wrong

- Labels do not match windows.
- Old `production_y.npy` is reused accidentally.
- Distribution is calculated from wrong column.
- Dominant class warning threshold is too high.
- Evaluation reports accuracy even when labels are stale.
- Label/prediction length mismatch must stay a hard failure.
- `evaluation_summary.json` must include `dominant_class`, `dominant_pct`, and `distribution_dominance_warning`.
- Temporal duration must use `4 + (length - 1) * 2` seconds for 50% overlap.
- Stage 5 should remain a single-component implementation without a second evaluation script.

### 10. Symptoms If This Stage Is Wrong

- Accuracy looks extremely low or high for the wrong reason.
- `hand_tapping` collapse is hidden in a long report.
- Dominant class percentage is missing.
- Labeled metrics are trusted even when X/y lengths differ.
- Stage 6/7 receive weak or missing collapse signals.
- A one-class batch appears only as "high confidence" instead of "unsafe prediction collapse."

### 11. Manual Checks

- Confirm prediction count.
- Confirm label count if labels exist.
- Confirm labels are from the same run as `production_X.npy`.
- Count `predicted_activity`.
- Count `predicted_class`.
- Confirm both counts agree.
- Calculate dominant class percentage manually.
- Check mean confidence.
- Check whether report clearly says when one class dominates.
- Confirm `has_labels=false` for unlabeled production replay.
- Confirm `classification_metrics=null` for unlabeled replay.
- Confirm `dominant_class` and `dominant_pct` are preserved in `ModelEvaluationArtifact`.
- Confirm `distribution_dominance_warning=True` when one class is at or above the critical dominance threshold.
- Confirm Stage 5 does not call model inference again; it should analyze Stage 4 artifacts only.
- Confirm class names resolve through the canonical label mapping.

### 12. Questions To Ask While Reading The Code

- Does Stage 5 auto-detect labels from Stage 3?
- Does it reject length mismatch?
- Does it preserve dominant class and dominant percentage?
- Does it use class names or raw indices for distribution?
- Does it make collapse obvious enough for Stage 6 and Stage 7?
- Does the artifact summary include every field needed by Stage 6/7?
- Does the JSON report say clearly that production replay is unlabeled?
- Does it compute confidence from Stage 4 output, not recompute probabilities?
- Does the text report hide internal collapse keys by mistake?
- Does the code still have only one Stage 5 implementation file?

### 13. Evidence To Save Before Moving On

- Evaluation JSON.
- Evaluation text report.
- Prediction distribution.
- Dominant class percentage.
- Mean confidence.
- Accuracy/F1 only if labels are proven paired.
- `artifacts/<run_id>/evaluation/evaluation_summary.json`.
- Stage 5 log lines showing `UNLABELED` or `LABELED` mode.
- Manual count from the prediction CSV proving the dominant class percentage.
- A note saying whether labels were absent, present and paired, or rejected.

### 14. Stage 5 Refactor Target

Stage 5 has been simplified to one runtime logic file:

- Runtime logic: `src/components/model_evaluation.py`.
- Public class: `ModelEvaluation`.
- Private helpers inside the component:
  - `_load_predictions`
  - `_validate_prediction_columns`
  - `_load_labels`
  - `_validate_label_alignment`
  - `_analyze_distribution`
  - `_analyze_confidence`
  - `_analyze_uncertainty`
  - `_analyze_temporal`
  - `_compute_classification_metrics`
  - `_write_reports`
  - `_build_artifact`
- Same thesis docstring style used in Stages 1-4:
  - `Method Name`
  - `Description`
  - `Output`
  - `On Failure`
- Label length mismatch is a hard error, not truncation.
- `dominant_class`, `dominant_pct`, and `distribution_dominance_warning` are written into the artifact summary JSON.
- Temporal duration uses the 50% overlap formula `4 + (length - 1) * 2`.

---

## Stage 6: Post-Inference Monitoring

### 1. Stage Purpose

Detect unhealthy model behavior after inference using confidence, temporal, and drift signals.

### 2. Main Component File

- `src/components/post_inference_monitoring.py`
- `src/monitoring/post_inference_monitor.py`

### 3. Connected Config, Entity, Artifact Files

- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`
- `config/pipeline_config.yaml`
- `config/pipeline_overrides.yaml`, if used
- `models/normalized_baseline.json`
- `models/drift_reference.json`

### 4. Input Files

- Prediction CSV from Stage 4.
- `production_X.npy` from Stage 3.
- Baseline statistics JSON.

### 5. Output Files

- `outputs/monitoring/monitoring_report.json`
- Monitoring artifact summary.

### 6. Expected Columns Or Shapes

Prediction CSV:

- `predicted_activity`
- `confidence`

Production data:

- `(N, 200, 6)`

Baseline:

- should be generated from the same feature space as `production_X.npy`.

### 7. Expected Units

Monitoring drift comparisons only make sense if baseline and production data are in the same feature space:

- both raw/unit-converted, or
- both normalized.

Do not compare raw production windows to normalized baseline windows.

### 8. What The Stage Does Internally

- Loads predictions.
- Computes confidence metrics.
- Computes entropy estimate.
- Computes uncertain-window ratio.
- Computes dominant class percentage.
- Computes temporal transition rate.
- Computes dwell time.
- Loads baseline statistics.
- Computes drift metrics.
- Combines monitoring layers into overall status.

### 9. What Can Go Wrong

- Baseline file is missing.
- Baseline exists but is from a different feature space.
- Confidence is high during wrong collapse, so low-confidence checks miss the problem.
- Entropy is low during wrong collapse, so entropy alone does not catch it.
- Dominant-class warning threshold is too high.
- Drift is skipped or interpreted incorrectly.

### 10. Symptoms If This Stage Is Wrong

- Monitoring says OK while predictions are mostly `hand_tapping`.
- Drift score is huge because baseline and production spaces differ.
- Drift score is tiny because baseline accidentally equals current production.
- Confidence looks healthy even when predictions are wrong.

### 11. Manual Checks

- Open monitoring report JSON.
- Check mean confidence.
- Check entropy.
- Check dominant class and dominant percentage.
- Check transition rate.
- Check mean dwell time.
- Check baseline path.
- Check baseline feature-space metadata.
- Compare baseline channel means/stds with current `production_X.npy`.

### 12. Questions To Ask While Reading The Code

- What happens if baseline is missing?
- Does monitoring receive collapse signals from Stage 5?
- Is high-confidence one-class behavior treated as unhealthy?
- Is entropy calculated from full probabilities or approximate confidence only?
- Is drift comparing the right feature space?
- Does monitoring status become WARNING/CRITICAL for dominant-class collapse?

### 13. Evidence To Save Before Moving On

- Monitoring report JSON.
- Confidence metrics.
- Entropy metrics.
- Temporal metrics.
- Drift metrics.
- Baseline path and metadata.
- Collapse signal section.

---

## Stage 7: Trigger Evaluation

### 1. Stage Purpose

Decide whether the system should approve, deny, review, or trigger retraining based on monitoring output.

### 2. Main Component File

- `src/components/trigger_evaluation.py`
- `src/trigger_policy.py`

### 3. Connected Config, Entity, Artifact Files

- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`
- `config/pipeline_config.yaml`
- `config/pipeline_overrides.yaml`, if used
- `logs/trigger/trigger_state.json`

### 4. Input Files

- Monitoring report from Stage 6.
- Trigger state file.

### 5. Output Files

- Trigger artifact.
- Trigger decision in pipeline result JSON.
- Trigger state JSON.

### 6. Expected Columns Or Shapes

No sensor columns. Trigger receives structured metrics:

- mean confidence
- entropy
- uncertain ratio
- flip rate
- drift score
- dominant class
- dominant class percentage
- collapse warning

### 7. Expected Units

No physical units. Threshold units are:

- confidence: 0 to 1
- entropy: scalar
- dominant percentage: 0 to 100
- flip rate: ratio or percentage depending on conversion point
- drift z-score: scalar

### 8. What The Stage Does Internally

- Converts monitoring report into trigger-policy input.
- Checks collapse guard.
- Checks confidence thresholds.
- Checks temporal thresholds.
- Checks drift thresholds.
- Applies cooldown logic.
- Produces final action and reasons.

### 9. What Can Go Wrong

- Collapse signals are not passed from monitoring.
- Dominant percentage unit is confused between ratio and percent.
- Cooldown hides a serious failure.
- Trigger allows retraining from collapsed pseudo-labels.
- Reason text does not explain the failure.

### 10. Symptoms If This Stage Is Wrong

- Trigger says OK when predictions are mostly `hand_tapping`.
- Trigger starts retraining on collapsed unlabeled predictions.
- Trigger decision gives no useful reason.
- Cooldown suppresses the only warning.

### 11. Manual Checks

- Open trigger decision output.
- Confirm dominant class is included.
- Confirm dominant percentage is included.
- Confirm collapse guard returns `REVIEW` for severe dominance.
- Confirm automatic retraining is blocked for collapse.
- Confirm cooldown status is visible.
- Confirm reasons mention the actual unhealthy signal.

### 12. Questions To Ask While Reading The Code

- Is collapse guard evaluated before ordinary drift/confidence rules?
- What threshold causes REVIEW?
- Does `>95%` single-class dominance become warning or review?
- Can high-confidence collapse bypass trigger?
- Does cooldown apply to REVIEW decisions?
- Does trigger distinguish data/path failure from model drift?

### 13. Evidence To Save Before Moving On

- Trigger action.
- Alert level.
- `should_retrain` value.
- Cooldown state.
- Trigger reasons.
- Collapse guard details.

---

## Cross-Stage Checks

Use this section after reading all seven stages.

### Train/Serve Parity

Check these one by one:

- Same sensor order during training and serving?
- Same accelerometer unit?
- Same gyroscope unit?
- Same gravity-removal setting?
- Same calibration setting?
- Same scaler file?
- Same scaler fitting users?
- Same window size?
- Same overlap?
- Same class mapping?
- Same model file as expected?

### `hand_tapping` Collapse Checks

Save the answers:

- What percentage of windows are predicted as `hand_tapping`?
- Is `hand_tapping` class index exactly `4`?
- Do other class indices map correctly?
- Is mean confidence high?
- Is entropy low?
- Does the top-3 probability list show realistic alternatives?
- Does the model ever predict all 11 classes?
- Is collapse present before monitoring/trigger?

### Artifact Consistency Checks

Confirm:

- `len(production_X) == len(predictions)`
- If labels exist, `len(production_X) == len(production_y)`
- `len(production_metadata) == len(production_X)`
- `probabilities.shape == (len(production_X), 11)`
- prediction CSV rows equal probability rows

---

## Specific Tests To Add Later

Do not add these during manual inspection unless you decide to start a coding task later.

- Test class mapping consistency.
- Test `production_X.npy` shape is exactly `(N, 200, 6)`.
- Test channel order from CSV to NumPy.
- Test scaler length, sensor order, and fitting users.
- Test accelerometer conversion is not double-applied.
- Test gyroscope is not converted unexpectedly.
- Test gravity removal config matches model contract.
- Test fake one-class predictions trigger collapse guard.
- Test broken timestamp data fails validation.
- Test normal 50 Hz data passes validation.
- Test inference probabilities have shape `(N, 11)`.
- Test resampling output median gap is `20 ms`.

---

## Manual Debug Order for Shalin

Follow this exact order.

### 1. Freeze Current Evidence

- Do not delete generated files.
- Save current logs, artifacts, predictions, monitoring report, and trigger output.
- Record current `production_X.npy` shape.
- Record current prediction distribution.
- Record current `hand_tapping` percentage.

### 2. Inspect `run_pipeline.py`

Check:

- Which stages run by default?
- Which CLI flags override model, input CSV, normalization, unit conversion, gravity removal, and calibration?
- Whether `--continue-on-failure` was used.
- Whether the run used `--input-csv`, raw accel/gyro files, or default discovery.

### 3. Inspect `config/pipeline_config.yaml`

Check:

- unit conversion setting
- gravity removal setting
- calibration setting
- normalization setting
- target sampling frequency
- window size
- overlap
- validation thresholds
- model path
- trigger thresholds

### 4. Inspect Artifact And Config Dataclasses

Open:

- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`

Check:

- Which paths are passed between stages?
- Which fields are optional?
- Whether labels are optional or always expected.
- Whether `production_y_path` can be stale or missing.

### 5. Inspect Stage 1

Open:

- `src/components/data_ingestion.py`

Check:

- raw file discovery
- accel/gyro pairing
- timestamp parsing
- `merge_asof` tolerance
- 50 Hz resampling
- canonical output path

Save:

- fused CSV path
- row count
- timestamp gap summary
- sensor stats before transformation

### 6. Inspect Stage 2

Open:

- `src/components/data_validation.py`

Check:

- schema checks
- missing-value checks
- range checks
- acceleration unit detection
- sampling-frequency checks
- whether failures are warnings or errors

Save:

- validation status
- validation warnings/errors
- actual frequency
- max absolute value per channel

### 7. Inspect Stage 3 Deeply

Open:

- `src/components/data_transformation.py`
- `src/preprocess_data.py`
- `src/utils/scaler.py`

Check:

- accelerometer unit detection
- gyroscope unit handling
- gravity removal
- calibration
- scaler path
- scaler sensor order
- normalization on/off
- window size 200
- 50% overlap
- channel order
- X/y pairing

Save:

- `production_X.npy` shape
- `production_y.npy` shape
- per-channel stats after transformation
- scaler file content summary
- first few metadata entries

### 8. Inspect Stage 4

Open:

- `src/components/model_inference.py`
- `src/run_inference.py`
- `src/utils/label_mapping.py`

Check:

- model path
- model input shape
- model output shape
- probability shape
- class mapping
- confidence extraction
- prediction export consistency

Save:

- model path
- input/output shape
- prediction distribution
- top-3 probabilities for first 20 windows
- mean confidence

### 9. Inspect Stage 5

Open:

- `src/components/model_evaluation.py`

Check:

- prediction distribution
- dominant class percentage
- confidence summary
- label loading
- X/y/prediction length equality
- whether collapse signal is preserved

Save:

- evaluation JSON
- dominant class
- dominant percentage
- labeled metrics only if labels are paired

### 10. Inspect Stage 6

Open:

- `src/components/post_inference_monitoring.py`
- `src/monitoring/post_inference_monitor.py`

Check:

- confidence
- entropy
- temporal stability
- flip rate
- dwell time
- drift baseline path
- baseline feature space
- collapse signal propagation

Save:

- monitoring report JSON
- entropy statistics
- transition rate
- dwell time
- drift score
- baseline metadata

### 11. Inspect Stage 7

Open:

- `src/components/trigger_evaluation.py`
- `src/trigger_policy.py`

Check:

- collapse guard
- dominant class threshold
- `REVIEW` behavior
- cooldown behavior
- retraining block on collapsed predictions
- decision reason text

Save:

- trigger action
- alert level
- `should_retrain`
- reasons
- cooldown state

### 12. Only Then Clean Generated Files

Only after the evidence is saved and the stage-by-stage notes are complete:

- clean old generated predictions if needed
- clean stale prepared artifacts if needed
- rerun the pipeline from Stage 1

Do not clean first. Cleaning first destroys the evidence needed to understand the `hand_tapping` collapse.

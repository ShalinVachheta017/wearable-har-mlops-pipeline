Below is a compact but complete explanation of the notebook. You can paste this into another chat or into the notebook as documentation.

---

# Notebook Explanation: HAR Inference, Confidence, and Drift Monitoring

This notebook runs inference for a trained **1D-CNN-BiLSTM Human Activity Recognition model** on raw Garmin Venu 3 accelerometer and gyroscope data. It also produces prediction confidence outputs and drift reports comparing production/unlabeled data against labeled/reference data.

The notebook follows the preprocessing described in the ICTH paper: Garmin Venu 3 IMU data is converted to CSV, accelerometer data is converted from milli-g to m/s², accelerometer and gyroscope streams are synchronized by timestamp, data is downsampled to **50 Hz**, and the model uses **200-sample windows** with **50% overlap**. This gives one 4-second window per prediction. The paper states that the final model uses wrist accelerometer and gyroscope only, giving **6 input features**, and predicts **11 activity classes**. 

The second paper places this HAR model inside a larger mental-health monitoring pipeline, where activity predictions become behavioral biomarkers and can later be used for bout analysis and report generation. 

---

## Notebook Inputs

The notebook expects these files:

```text
fine_tuned_model_1dcnnbilstm.keras
all_users_data_labeled.csv
2025-07-16-21-46-56_accelerometer.csv
2025-07-16-21-46-56_gyroscope.csv
```

### 1. `fine_tuned_model_1dcnnbilstm.keras`

This is the trained Keras model. It expects:

```python
X.shape = (n_windows, 200, 6)
```

where:

```text
200 = time steps per window
6 = Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w
```

The output shape is:

```python
(n_windows, 11)
```

meaning one probability per activity class.

### 2. `all_users_data_labeled.csv`

This is the labeled/reference dataset. It is already mostly preprocessed. The notebook uses it only as:

```text
reference data for drift
optional reference agreement check
activity distribution baseline
```

It is **not used for training or fine-tuning** in this notebook.

### 3. Raw production accelerometer and gyroscope CSVs

These are the real inference inputs. They are unlabeled production data from Garmin. They require full preprocessing before being passed to the model.

---

# Cell-by-Cell Explanation

## Cell 1: Configuration and Model Loading

This cell imports required libraries, defines file paths, defines model settings, defines the activity class names, and loads the Keras model.

Important settings:

```python
TARGET_HZ = 50
RESAMPLE_MS = 20
MERGE_TOLERANCE_MS = 1
WINDOW_SIZE = 200
STRIDE_SIZE = 100
```

These match the paper preprocessing:

```text
50 Hz sampling
20 ms resampling interval
200-sample windows
4-second windows
50% overlap
```

The feature order is fixed as:

```python
FEATURE_COLS = [
    "Ax_w", "Ay_w", "Az_w",
    "Gx_w", "Gy_w", "Gz_w",
]
```

This order is important because the model was trained on these six wrist IMU channels.

The activity classes are:

```python
CLASS_NAMES = [
    "ear_rubbing",
    "forehead_rubbing",
    "hair_pulling",
    "hand_scratching",
    "hand_tapping",
    "knuckles_cracking",
    "nail_biting",
    "nape_rubbing",
    "sitting",
    "smoking",
    "standing",
]
```

This order is inferred from the activity order reported in the ICTH paper’s classification table. The paper confirms these 11 classes, but the original `LabelEncoder` was not available, so this mapping should be documented as a strongly supported assumption. 

Cell 1 also checks whether the model input shape and output shape match the expected notebook settings.

Expected:

```python
model.input_shape == (None, 200, 6)
model.output_shape[-1] == 11
```

---

## Cell 2: Preprocessing Helper Functions

This cell defines helper functions for reading, cleaning, and transforming data.

### `parse_timestamp_series`

This converts timestamps into pandas datetime format. It supports:

```text
Unix seconds
Unix milliseconds
datetime strings
```

This is needed because Garmin CSV timestamps can appear in different formats.

### `expand_list_columns_fast`

Some Garmin CSV rows may contain multiple samples inside list-like cells, for example:

```text
[10, 20, 30]
```

This function expands those rows so each sensor sample becomes its own row. This matches the logic used in the original `processing.ipynb`.

### `normalize_reference_columns`

This prepares `all_users_data_labeled.csv`.

It:

```text
renames columns to Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w
keeps activity labels if available
parses timestamps
removes invalid rows
does not downsample
does not convert accelerometer units again
```

This is important because the labeled/reference CSV is already processed. Downsampling it again would be slow and could distort the reference.

### `parse_prod_sensor_csv`

This prepares one raw production sensor file, either accelerometer or gyroscope.

For accelerometer:

```text
reads raw accel CSV
expands list-like rows
reconstructs precise timestamp
converts milli-g to m/s² using × 0.00981
renames to Ax_w, Ay_w, Az_w
```

For gyroscope:

```text
reads raw gyro CSV
expands list-like rows
reconstructs precise timestamp
renames to Gx_w, Gy_w, Gz_w
```

The accelerometer conversion is based on the paper and preprocessing notebook, where Garmin accelerometer data is converted from milli-g to m/s². 

### `build_production_from_two_files`

This merges raw accelerometer and gyroscope streams.

It uses:

```python
pd.merge_asof(..., tolerance=pd.Timedelta(milliseconds=1))
```

This means accel and gyro samples are matched only if their timestamps are within **1 ms**. This follows the original preprocessing logic.

The output contains:

```text
timestamp
Ax_w
Ay_w
Az_w
Gx_w
Gy_w
Gz_w
```

### `downsample_production`

This downsamples production data to **50 Hz** using 20 ms bins:

```python
.resample("20ms").mean()
```

This matches the paper, which says Garmin raw data was recorded at 100 Hz and downsampled to 50 Hz. 

### `build_windows`

This creates model input windows.

Each window has shape:

```python
(200, 6)
```

and the full model input has shape:

```python
(n_windows, 200, 6)
```

No handcrafted statistical features are created. This is correct because the model is a CNN-BiLSTM that expects raw time-series windows, not RandomForest-style feature vectors.

---

## Cell 3: Segment-Aware Windowing

This cell prevents the notebook from creating invalid windows across breaks in the data.

### Why this matters

If there is a sensor dropout or time gap, normal windowing could create one 200-sample window that crosses the gap. That would give the model a fake continuous sequence.

### `add_segment_id`

This creates segments based on:

```text
user/session boundaries
activity changes in labeled data
large timestamp gaps
```

A new segment starts if the timestamp gap is larger than:

```python
RESAMPLE_MS * 3
```

So for 20 ms data, a gap larger than 60 ms starts a new segment.

### `build_windows_segment_aware`

This builds windows inside each segment only. It does not allow windows to cross gaps.

It also preserves **global row indices**:

```text
start_idx
end_idx
```

This matters later for row-level soft-vote predictions. Without global indices, row-level output could be wrong if production data has multiple segments.

---

## Cell 4: Load Reference and Production Data

This cell actually prepares the data.

### Reference path

The reference data is loaded from:

```python
all_users_data_labeled.csv
```

Steps:

```text
load CSV
normalize column names
remove unknown labels
do not downsample
create segment-aware reference windows
```

Outputs:

```python
reference_ds
X_ref
y_ref
meta_ref
```

Where:

```text
reference_ds = cleaned reference dataframe
X_ref = reference windows, shape (n_ref_windows, 200, 6)
y_ref = reference labels
meta_ref = window metadata
```

### Production path

The production data is loaded from two raw files:

```python
accelerometer CSV
gyroscope CSV
```

Steps:

```text
parse raw accel
parse raw gyro
expand list rows
timestamp + timestamp_ms + sample_time_offset
convert accel milli-g to m/s²
merge accel/gyro with 1 ms tolerance
downsample to 50 Hz
create gap-aware 200x6 windows
```

Outputs:

```python
prod_raw
prod_ds
X_prod
meta_prod
```

Where:

```text
prod_raw = merged raw accel/gyro data
prod_ds = 50 Hz processed production data
X_prod = model input, shape (n_windows, 200, 6)
meta_prod = production window metadata
```

The notebook then validates that:

```python
X_prod.shape[1:] == (200, 6)
```

This is the correct model input shape.

---

## Cell 5: Model Inference and Window-Level Confidence

This cell runs the trained Keras model on production windows.

```python
pred_probs = model.predict(X_prod)
```

The output is a probability matrix:

```python
pred_probs.shape = (n_windows, 11)
```

For every window, the notebook calculates:

```text
top-1 predicted activity
top-1 confidence
top-2 activity
top-2 confidence
top1-top2 margin
confidence band
uncertain flag
probability for every class
```

The confidence bands are:

```text
high: confidence >= 0.80
medium: confidence >= 0.60 and < 0.80
low: confidence < 0.60
```

The output file is:

```text
production_window_predictions.csv
```

This is the main inference result. It contains one row per 4-second window.

---

## Cell 6: Confidence Summaries

This cell creates summary tables from the window-level predictions.

### `activity_confidence_summary.csv`

This gives one row per predicted activity, including:

```text
number of windows predicted as that activity
mean confidence
median confidence
min confidence
max confidence
mean top-2 confidence
mean top1-top2 margin
number of uncertain windows
percentage of all windows
high/medium/low confidence counts
```

This helps answer:

```text
Which activities dominate production predictions?
How confident is the model for each activity?
Which activities are uncertain?
```

### `class_probability_summary.csv`

This summarizes probability mass across all windows for each class.

It includes:

```text
mean probability across all windows
median probability
maximum probability
number of windows where the class was top-1
percentage of windows where the class was top-1
```

This is useful because a class may not often be top-1 but may still receive meaningful probability mass.

---

## Cell 7: Row-Level Soft-Vote Predictions

The model predicts windows, not individual rows. But sometimes we need row-level predictions for timeline plotting or later bout analysis.

Because windows overlap by 50%, most rows belong to two windows. Instead of simply assigning the latest window prediction, this notebook uses **soft voting**.

For each row:

```text
find all windows that contain this row
average their class probabilities
choose the class with highest averaged probability
```

The output file is:

```text
production_row_predictions.csv
```

It contains:

```text
timestamp
sensor features
predicted_activity
confidence
overlap_vote_count
probability for each activity
confidence band
uncertain flag
```

This is smoother and more defensible than hard assignment from a single window.

---

## Cell 8: Optional Reference Agreement Check

This cell runs the model on `X_ref`, the labeled/reference windows.

It calculates:

```text
reference-data agreement
classification report
```

Important note:

This is **not test accuracy** unless the reference CSV is truly held-out. Since `all_users_data_labeled.csv` may overlap with training/fine-tuning data, the notebook calls it “reference-data agreement,” not validation accuracy.

This cell is useful mainly as a sanity check.

A low reference agreement may indicate:

```text
class index mapping uncertainty
reference data mismatch
model version mismatch
preprocessing/unit mismatch
```

---

## Cell 9: Feature Drift Functions

This cell defines drift metrics.

The notebook compares production data against reference data using:

```text
PSI
KS statistic
mean shift z-score
standard deviation ratio
```

It also adds two magnitude features:

```python
accel_mag = sqrt(Ax_w² + Ay_w² + Az_w²)
gyro_mag = sqrt(Gx_w² + Gy_w² + Gz_w²)
```

So drift is checked on 8 features:

```text
Ax_w
Ay_w
Az_w
Gx_w
Gy_w
Gz_w
accel_mag
gyro_mag
```

Magnitude features are useful because they help separate:

```text
axis/orientation drift
overall motion-intensity drift
```

A feature is flagged as drifted if any of these are true:

```text
PSI > 0.25
KS > 0.20
mean shift z-score > 2.0
std ratio < 0.5
std ratio > 2.0
```

---

## Cell 10: Activity Distribution Drift Functions

This cell compares the activity distribution in reference labels against the activity distribution in production predictions.

It computes:

```text
activity distribution PSI
total variation distance
per-class percentage difference
```

This answers:

```text
Is the model predicting activities in a very different distribution than the reference/labeled data?
```

For example, if reference data is balanced across 11 classes but production predictions collapse mostly to two classes, this drift report will show it.

---

## Cell 11: Run Drift Reports

This cell executes the drift calculations and saves the final drift outputs.

### `feature_drift_report.csv`

Contains one row per feature:

```text
feature
PSI
KS statistic
reference mean
production mean
mean shift z-score
reference std
production std
std ratio
is_drift
```

### `activity_distribution_drift.csv`

Contains one row per class:

```text
activity
reference count
production count
reference percentage
production percentage
percentage difference
PSI component
```

### `drift_summary.csv`

Compact summary with:

```text
overall feature drift score
number of drifted features
activity distribution PSI
activity total variation distance
drift flags
```

This gives a quick view of whether production data is in-distribution or out-of-distribution.

---

# Final Output Files

The notebook produces:

```text
production_window_predictions.csv
production_row_predictions.csv
activity_confidence_summary.csv
class_probability_summary.csv
feature_drift_report.csv
activity_distribution_drift.csv
drift_summary.csv
```

## Main output meaning

### `production_window_predictions.csv`

One prediction per 4-second window.

Use this for:

```text
main model inference result
window-level analysis
bout analysis
confidence review
```

### `production_row_predictions.csv`

One prediction per timestamp row using soft-vote.

Use this for:

```text
timeline plots
merging with other sensors
row-level visualization
```

### `activity_confidence_summary.csv`

Use this to see:

```text
which activities dominate
how confident the model is
how many uncertain windows exist
```

### `feature_drift_report.csv`

Use this to see whether production sensor signals differ from the labeled/reference data.

### `activity_distribution_drift.csv`

Use this to see whether predicted activity distribution differs from the reference activity distribution.

### `drift_summary.csv`

Use this for quick reporting.

---

# How the Notebook Matches the Papers

The ICTH paper states that the model uses a **1DCNN-BiLSTM architecture** for anxiety-related HAR on Garmin Venu 3 data, using only wrist accelerometer and gyroscope. The notebook uses exactly those six features: `Ax_w`, `Ay_w`, `Az_w`, `Gx_w`, `Gy_w`, and `Gz_w`. 

The paper states that Garmin raw data was downsampled to **50 Hz** by resampling to **20 ms intervals**, and the notebook does this using:

```python
.resample("20ms").mean()
```

The paper states that fixed-size windows of **200 time steps** were used, equal to **4 seconds at 50 Hz**, with **50% overlap**. The notebook uses:

```python
WINDOW_SIZE = 200
STRIDE_SIZE = 100
```

The paper lists 11 activity classes. The notebook uses the same 11 classes in the same order shown in the classification table. 

The mental-health pipeline paper explains that the HAR model outputs activity labels and confidence scores for short overlapping IMU windows, which are then used for temporal/bout analysis and later report generation. The notebook produces exactly those outputs: window-level activity labels, confidence scores, and row-level timelines. 

---

# Current Limitation

The main limitation is the class-index mapping.

The papers confirm the 11 class names and their reported order, but the original training `LabelEncoder` is unavailable. Therefore, the notebook uses the class order inferred from the ICTH paper. This is strongly supported but not mathematically proven from the saved model file.

Recommended note:

```text
The class-index mapping is inferred from the activity order reported in the ICTH paper. The original LabelEncoder was unavailable; therefore, the mapping is treated as a documented assumption.
```

---

# Final Assessment

The notebook is now a complete inference and monitoring pipeline:

```text
raw Garmin production data
→ preprocessing matching the paper
→ model-ready 200x6 windows
→ Keras inference
→ confidence and probability outputs
→ soft-vote row-level predictions
→ feature drift monitoring
→ activity distribution drift monitoring
```

The code is technically solid. The main interpretive caution is that if drift is high, production predictions should be described as **domain-shifted inference outputs**, not guaranteed ground-truth activity labels.

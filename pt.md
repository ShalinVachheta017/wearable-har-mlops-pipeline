Below is the full Markdown content. You can copy everything from here into a file named:

```text
MLOps_Wearable_Sensor_Guide.md
```

Then you can convert it to PDF later using VS Code, Typora, Obsidian, Pandoc, or any Markdown editor.

---

````markdown
# MLOps Guide for Multiclass Wearable-Sensor Activity Recognition

## Practical Notes for Offline / Local MLOps, Drift Monitoring, Multiclass Metrics, Time-Series Data, and Unlabeled Production Data

---

## Table of Contents

1. What is MLOps?
2. Why do we use MLOps?
3. Types of MLOps pipelines
4. General MLOps stages
5. Case 1: Model trained on labeled dataset
6. Case 2: Labeled training data, unlabeled production data
7. Case 3: Labeled training data, labeled production data
8. Drift, monitoring, retraining, deployment, and scalability
9. Offline/local MLOps on one PC
10. Multiclass classification metrics
11. Time-series classification and regression metrics
12. Monitoring parameters and thresholds
13. Wearable-sensor activity recognition case
14. Offline pipeline design for accelerometer and gyroscope data
15. Drift metrics for unlabeled wearable-sensor data
16. What to do with severe gyroscope-axis drift
17. Can unlabeled data improve the model?
18. Retraining strategy with labeled and unlabeled data
19. Final practical checklist

---

# 1. What is MLOps?

**MLOps means Machine Learning Operations.**

It is the process of taking a machine learning model from:

```text
data → training → testing → deployment → monitoring → retraining
````

in a repeatable, automated, production-ready way.

MLOps is similar to DevOps, but it is designed for machine learning systems.

A normal software system usually behaves the same after deployment unless the code changes.
But a machine learning model can become worse even if the code stays exactly the same.

Why?

Because the world changes.

Examples:

```text
User behavior changes
Sensor device changes
Data distribution changes
Business rules change
New classes appear
Input values shift
The model sees data it was not trained for
```

So MLOps helps us manage the full lifecycle of ML systems.

---

# 2. Why do we use MLOps?

We use MLOps to make machine learning systems:

## 1. Repeatable

The same code, same data, and same configuration should produce the same result.

```text
same data + same code + same config = same model
```

## 2. Deployable

The trained model should not stay only inside a notebook.
It should be usable in production or in a local application.

## 3. Monitorable

After deployment, we should know:

```text
Is the model still working?
Is the input data still valid?
Is the model confident?
Are predictions changing strangely?
Is the system slow or failing?
```

## 4. Retrainable

If the model becomes bad, we should be able to retrain it using a controlled pipeline.

## 5. Scalable

The system should handle more data, more predictions, or more users if needed.

## 6. Reliable

We should track:

```text
model versions
data versions
training metrics
prediction logs
errors
drift reports
deployment history
```

---

# 3. Types of MLOps pipelines

A complete MLOps system can contain several pipelines.

| Pipeline Type       | Purpose                                          |
| ------------------- | ------------------------------------------------ |
| Data pipeline       | Collect, clean, validate, transform data         |
| Feature pipeline    | Create model-ready features                      |
| Training pipeline   | Train model using labeled data                   |
| Evaluation pipeline | Test model before deployment                     |
| Deployment pipeline | Move model into production/local use             |
| Inference pipeline  | Use model to make predictions                    |
| Monitoring pipeline | Track data, predictions, drift, errors           |
| Retraining pipeline | Retrain model when needed                        |
| CI/CD pipeline      | Automatically test and deploy code/model changes |

In simple projects, some of these are combined into one script.
In mature production systems, they are usually separate automated pipelines.

---

# 4. General MLOps stages

A typical MLOps lifecycle looks like this:

```text
Raw Data
   ↓
Data Validation
   ↓
Feature Engineering / Preprocessing
   ↓
Model Training
   ↓
Model Evaluation
   ↓
Model Registry / Versioning
   ↓
Deployment
   ↓
Inference / Prediction
   ↓
Monitoring
   ↓
Drift Detection
   ↓
Retraining Trigger
   ↓
New Model
```

Or as a diagram:

```text
[Data Collection]
        ↓
[Data Validation]
        ↓
[Feature Engineering]
        ↓
[Model Training]
        ↓
[Model Evaluation]
        ↓
[Model Registry]
        ↓
[Deployment]
        ↓
[Prediction / Inference]
        ↓
[Monitoring]
        ↓
[Drift Detection]
        ↓
[Retraining]
        ↺
```

The most important stages are:

```text
1. Data collection
2. Data validation
3. Feature engineering
4. Model training
5. Model evaluation
6. Model versioning
7. Deployment
8. Monitoring
9. Drift detection
10. Retraining
```

---

# 5. Case 1: Model trained on labeled dataset

This is the basic supervised learning case.

You have:

```text
Training data = X + y
```

Where:

```text
X = input features
y = true label
```

Example:

```text
X = accelerometer and gyroscope signals
y = walking, sitting, running, standing, stairs, etc.
```

Pipeline:

```text
[Labeled Training Data]
        ↓
[Preprocessing]
        ↓
[Train Model]
        ↓
[Evaluate on Validation/Test Data]
        ↓
[Register Best Model]
        ↓
[Deploy Model]
        ↓
[Make Predictions]
        ↓
[Monitor Inputs and Predictions]
```

In this case, you can calculate offline supervised metrics because labels exist.

For classification:

```text
accuracy
precision
recall
F1-score
macro F1
weighted F1
confusion matrix
log loss
ROC-AUC
```

For regression:

```text
MAE
MSE
RMSE
MAPE
SMAPE
WAPE
R²
```

Important note:

Before production, you are mostly measuring offline model quality.
You are not truly measuring production drift yet, because production data has not arrived.

---

# 6. Case 2: Labeled training data, unlabeled production data

This is very common in real-world ML.

You trained using:

```text
Training = X + y
```

But production gives only:

```text
Production = X only
```

There is no true label.

Example:

```text
Training:
window_001 → walking
window_002 → sitting
window_003 → running

Production:
window_901 → unknown
window_902 → unknown
window_903 → unknown
```

The model can predict labels, but you do not know if those predictions are correct.

Pipeline:

```text
[Labeled Training Data]
        ↓
[Train Model]
        ↓
[Evaluate Offline]
        ↓
[Deploy Model]
        ↓
[Unlabeled Production Data]
        ↓
[Predictions]
        ↓
[Monitor Input Drift]
        ↓
[Monitor Prediction Drift]
        ↓
[Alert / Human Review / Label Sampling]
```

In this case, you cannot directly calculate:

```text
accuracy
F1-score
precision
recall
confusion matrix
RMSE
MAE
```

because those require true labels.

But you can monitor:

```text
input data drift
feature drift
prediction drift
confidence drift
out-of-distribution score
data quality
latency
error rate
```

For unlabeled production, you are not measuring true performance.
You are measuring whether the data and model behavior look suspicious.

---

# 7. Case 3: Labeled training data, labeled production data

This is the best monitoring case.

You trained with:

```text
Training = X + y
```

And production eventually gives:

```text
Production = X + y
```

Example:

```text
Model predicts activity now.
Later, human annotation confirms the real activity.
```

Pipeline:

```text
[Labeled Training Data]
        ↓
[Train Model]
        ↓
[Evaluate Model]
        ↓
[Deploy]
        ↓
[Production Predictions]
        ↓
[Collect True Labels]
        ↓
[Measure Production Performance]
        ↓
[Detect Model Drift]
        ↓
[Retrain if Needed]
```

Here, you can monitor actual production performance.

For multiclass classification:

```text
accuracy
macro F1
weighted F1
per-class precision
per-class recall
confusion matrix
log loss
calibration
```

For regression:

```text
MAE
RMSE
MAPE
SMAPE
WAPE
bias
residual distribution
```

For time-series forecasting:

```text
rolling MAE
rolling RMSE
WAPE
MASE
forecast bias
coverage
error by horizon
```

Important note:

Even if production labels exist, they may arrive late.

Examples:

```text
fraud labels may arrive after investigation
churn labels may arrive after 30 days
medical outcome labels may arrive later
activity labels may require manual annotation
```

So Case 3 is strongest, but not always instant.

---

# 8. Drift, monitoring, retraining, deployment, and scalability

## 8.1 Main types of drift

| Drift Type        | What Changes?                        | Labels Needed? |
| ----------------- | ------------------------------------ | -------------- |
| Data drift        | Input features change                | No             |
| Feature drift     | Engineered features change           | No             |
| Prediction drift  | Model output distribution changes    | No             |
| Label drift       | True label distribution changes      | Yes            |
| Concept drift     | Relationship between X and y changes | Yes            |
| Performance drift | Accuracy/F1/RMSE gets worse          | Yes            |

---

## 8.2 Data drift

Data drift means the input data has changed.

Example:

```text
Training gyro_x mean = 0.2
Production gyro_x mean = 3.5
```

Or:

```text
Training walking windows have low gyro magnitude
Production walking-like windows have very high gyro magnitude
```

This does not always mean the model is wrong, but it is a warning.

---

## 8.3 Prediction drift

Prediction drift means the model output distribution has changed.

Example:

Training/fine-tuning predictions:

```text
walking: 20%
sitting: 20%
standing: 15%
running: 10%
stairs: 8%
...
```

Production predictions:

```text
walking: 70%
sitting: 3%
standing: 2%
running: 1%
stairs: 1%
...
```

This suggests something changed.

Possible causes:

```text
real activity distribution changed
sensor data changed
preprocessing changed
model is confused
unit mismatch
axis mismatch
production data is out-of-distribution
```

---

## 8.4 Concept drift

Concept drift means the relationship between input and label changed.

Example:

In training:

```text
certain wrist movement pattern = walking
```

In production:

```text
same pattern appears during another activity
```

Concept drift usually requires labels to confirm.

---

## 8.5 Retraining triggers

Retraining can be triggered by:

```text
scheduled retraining
data drift threshold
performance drop
new labeled data volume
business KPI degradation
manual review
```

Examples:

```text
Retrain every month
Retrain if macro F1 drops below 0.80
Retrain if critical class recall drops below 0.90
Retrain if PSI > 0.2 for important features
Retrain after 10,000 new labeled samples
```

---

## 8.6 Deployment strategies

Common deployment methods:

| Strategy              | Meaning                                                 |
| --------------------- | ------------------------------------------------------- |
| Shadow deployment     | New model runs in parallel but does not affect users    |
| Canary deployment     | Small percentage of traffic uses new model              |
| Blue-green deployment | Switch from old model to new model with rollback option |
| Batch deployment      | New model processes files/batches offline               |
| Local deployment      | Model runs on a single PC or edge device                |

For your offline/local case, deployment may simply mean:

```text
replace model_v1.pkl with model_v2.pkl
update config file
run batch inference
save logs and reports
```

---

# 9. Offline/local MLOps on one PC

Yes, a pipeline running only on one PC can still be called MLOps.

MLOps is a practice, not only a cloud setup.

If your local system does this:

```text
loads data automatically
validates data
preprocesses data
runs model
logs predictions
checks drift
generates reports
supports retraining
tracks versions
```

then it is a local/offline MLOps pipeline.

Cloud is not required.

However, local MLOps has limitations.

| Cloud MLOps                 | Local/Offline MLOps     |
| --------------------------- | ----------------------- |
| Scales to many users        | Usually one machine     |
| Central monitoring          | Local reports/logs      |
| High availability           | Single point of failure |
| Easy collaboration          | Limited                 |
| Auto-scaling                | Not available           |
| More complex infrastructure | Simpler setup           |

Useful local tools:

```text
Python
pandas
NumPy
scikit-learn
PyTorch or TensorFlow
MLflow local
DVC
SQLite
DuckDB
Evidently AI
matplotlib
cron / Windows Task Scheduler
Docker
Git
```

Example local project structure:

```text
project/
  data/
    raw/
    processed/
    production_unlabeled/
    labeled_samples/

  models/
    model_v1.pkl
    model_v2.pkl

  scalers/
    scaler_v1.pkl

  reports/
    data_quality_report.html
    drift_report.html
    prediction_report.html

  logs/
    predictions.sqlite
    monitoring_metrics.csv

  pipelines/
    ingest.py
    preprocess.py
    window.py
    predict.py
    monitor.py
    drift.py
    retrain.py
```

---

# 10. Multiclass classification metrics

Your problem is multiclass classification.

You have 11 activity classes.

Example:

```text
walking
sitting
standing
running
stairs up
stairs down
lying
cycling
typing
eating
unknown/other
```

For multiclass classification, use multiple metrics.

---

## 10.1 Accuracy

Accuracy means:

```text
correct predictions / total predictions
```

Use accuracy when classes are balanced.

Problem:

If one class dominates, accuracy can be misleading.

Example:

```text
Class A = 90%
Class B = 5%
Class C = 3%
Class D = 2%
```

A model that always predicts Class A can get 90% accuracy but fail completely on other classes.

---

## 10.2 Precision per class

Precision answers:

```text
Of all windows predicted as Class A, how many were really Class A?
```

Use precision when false positives matter.

Example:

```text
If model predicts "fall detected", how often is it actually a fall?
```

---

## 10.3 Recall per class

Recall answers:

```text
Of all actual Class A windows, how many did the model catch?
```

Use recall when false negatives matter.

Example:

```text
If the actual activity is "fall", did the model detect it?
```

---

## 10.4 F1-score

F1 balances precision and recall.

```text
F1 = harmonic mean of precision and recall
```

Use F1 when both false positives and false negatives matter.

---

## 10.5 Macro F1

Macro F1 calculates F1 for each class and then averages all classes equally.

Use macro F1 when minority classes are important.

Example:

```text
Class A F1 = 0.90
Class B F1 = 0.85
Class C F1 = 0.40

Macro F1 = average of all class F1 scores
```

Macro F1 punishes poor minority-class performance.

---

## 10.6 Weighted F1

Weighted F1 averages class F1 scores based on class frequency.

It is useful, but it can hide bad performance on rare classes.

---

## 10.7 Micro F1

Micro F1 combines all predictions globally.

In single-label multiclass classification, micro F1 is often similar to accuracy.

---

## 10.8 Confusion matrix

A confusion matrix shows which classes are confused with each other.

Example:

```text
                Predicted
              A    B    C    D
Actual A     80   10    5    5
Actual B     12   70   10    8
Actual C      3    8   85    4
Actual D      7    5    9   79
```

This is very important for activity recognition.

It can show:

```text
walking confused with stairs
standing confused with sitting
typing confused with sitting
running confused with walking
```

---

## 10.9 Top-k accuracy

Top-k accuracy checks whether the correct class is inside the top k predictions.

Example:

```text
Top-1 prediction: walking
Top-2 prediction: stairs
Top-3 prediction: running
```

If the true label is stairs, Top-1 is wrong but Top-3 is correct.

Useful when the model gives ranked probabilities.

---

## 10.10 Log loss / cross-entropy

Log loss measures probability quality.

A model can be correct but badly calibrated.

Example:

```text
True label = walking
Model says walking with probability 0.51
```

versus:

```text
True label = walking
Model says walking with probability 0.95
```

Both are correct, but the second is more confident.

---

## 10.11 Calibration

Calibration asks:

```text
When the model says 80% confidence, is it correct about 80% of the time?
```

Calibration is important if you use probabilities to make decisions.

---

# 11. Time-series classification and regression metrics

Your wearable-sensor data is time-series data.

That means each sample is connected to time.

You should not treat every row as independent without thinking about temporal structure.

---

## 11.1 Time-series classification

In time-series classification, the model predicts a class from a time window.

Example:

```text
2-second window → walking
2-second window → sitting
2-second window → running
```

Metrics:

```text
accuracy
macro F1
weighted F1
per-class precision
per-class recall
confusion matrix
ROC-AUC one-vs-rest
log loss
top-k accuracy
```

But also track time-aware metrics:

```text
F1 by day
F1 by session
F1 by user
recall by activity over time
false alarms per minute
missed events per minute
detection delay
class switch rate
average predicted activity duration
```

---

## 11.2 Time-series regression

Time-series regression predicts continuous future values.

Example:

```text
heart rate forecast
energy expenditure
step count
sensor value reconstruction
demand forecast
```

Common metrics:

| Metric        | Meaning                                            |
| ------------- | -------------------------------------------------- |
| MAE           | Mean absolute error                                |
| MSE           | Mean squared error                                 |
| RMSE          | Root mean squared error                            |
| MAPE          | Mean absolute percentage error                     |
| SMAPE         | Symmetric MAPE                                     |
| WAPE          | Weighted absolute percentage error                 |
| MASE          | Mean absolute scaled error                         |
| Forecast bias | Whether predictions are systematically high or low |
| Coverage      | Whether prediction intervals contain true values   |

---

## 11.3 MAPE warning

MAPE can fail when actual values are zero or near zero.

Example:

```text
actual = 0
predicted = 10
```

Percentage error becomes undefined or huge.

For time-series with zeros, prefer:

```text
MAE
RMSE
SMAPE
WAPE
MASE
```

---

## 11.4 Forecast horizon metrics

If forecasting multiple future steps, measure error by horizon.

Example:

```text
t+1 error
t+2 error
t+3 error
...
t+10 error
```

A model may be good for the next second but bad for the next minute.

---

# 12. Monitoring parameters and thresholds

In production or local offline use, monitor several groups.

```text
1. Data quality
2. Data drift
3. Prediction drift
4. Model performance
5. Business performance
6. Infrastructure performance
```

---

## 12.1 Data quality metrics

| Parameter            | Meaning                      | Example Threshold                |
| -------------------- | ---------------------------- | -------------------------------- |
| Missing values       | Null sensor readings         | Alert if > 1–2%                  |
| Schema               | Required columns exist       | Fail if missing                  |
| Data type            | Numeric columns are numeric  | Fail if wrong                    |
| Range                | Sensor values in valid range | Alert if outside 99th percentile |
| Duplicate timestamps | Same timestamp repeated      | Alert if high                    |
| Freshness            | Data is recent               | Alert if delayed                 |
| Volume               | Expected number of rows      | Alert if < 70% normal            |
| Sampling rate        | Expected Hz                  | Alert if > 5–10% deviation       |

---

## 12.2 Data drift metrics

For numerical features:

```text
KS test
Wasserstein distance
PSI
mean/std shift
robust z-score
Mahalanobis distance
```

For categorical features:

```text
Chi-square test
Jensen-Shannon divergence
distribution comparison
```

For embeddings:

```text
centroid distance
nearest-neighbor distance
MMD
Mahalanobis distance
```

---

## 12.3 Prediction drift metrics

For multiclass classification:

```text
class distribution shift
confidence distribution shift
entropy increase
top-1/top-2 margin decrease
prediction switching rate
```

For regression:

```text
prediction mean shift
prediction standard deviation shift
prediction min/max shift
outlier prediction rate
```

For time-series:

```text
forecast level shift
forecast volatility shift
prediction interval width change
seasonal pattern change
```

---

## 12.4 Performance metrics

These require labels.

For multiclass classification:

```text
accuracy
macro F1
weighted F1
per-class precision
per-class recall
confusion matrix
log loss
calibration error
```

For regression:

```text
MAE
RMSE
MAPE
SMAPE
WAPE
bias
residual drift
```

For time-series:

```text
rolling MAE
rolling RMSE
WAPE
MASE
forecast bias
coverage
error by horizon
```

---

## 12.5 Infrastructure metrics

```text
latency
throughput
error rate
CPU usage
GPU usage
memory usage
disk usage
queue length
crash count
runtime
```

For local/offline MLOps, you still monitor these.

Example:

```text
prediction script failed
batch took 45 minutes instead of 5 minutes
memory usage too high
input file corrupted
```

---

## 12.6 Threshold examples

There is no universal threshold.
Thresholds depend on business risk, sensor quality, label delay, and use case.

But starting points:

| Metric                  |           Warning |          Critical |
| ----------------------- | ----------------: | ----------------: |
| Feature mean shift      |           > 1 std |           > 2 std |
| Feature std ratio       |            > 1.5x |              > 3x |
| Robust z-score          |               > 3 |               > 5 |
| PSI                     |             > 0.1 |             > 0.2 |
| Prediction class shift  |          > 10–20% |             > 30% |
| Confidence drop         |             > 10% |             > 20% |
| OOD score               | > 95th percentile | > 99th percentile |
| Missing values          |            > 1–2% |              > 5% |
| Sampling-rate deviation |              > 5% |             > 10% |

For classification performance:

```text
accuracy drop > 3–5 percentage points → warning
macro F1 drop > 3–5 percentage points → warning
critical class recall below business threshold → critical
```

For regression:

```text
MAE increase > 10–20% → warning
RMSE increase > 10–20% → warning
bias outside acceptable range → warning
```

---

# 13. Wearable-sensor activity recognition case

Now we come to your exact case.

You have:

```text
Task: multiclass activity recognition
Classes: 11 activities
Sensors: accelerometer x/y/z + gyroscope x/y/z
Training 1: research-grade sensor, labeled
Fine-tuning: smartwatch/manual recording, labeled
Production/testing: smartwatch, unlabeled
Sampling: watch records around 100 Hz
Model input: convert to 50 Hz
Data: time-series windows
Problem: production is around 1.7 standard deviations different
Major issue: one gyro axis is 7x to 17x larger than training
System: local/offline ML pipeline
```

This is a combination of:

```text
domain shift
device shift
sensor placement shift
unlabeled production data
time-series classification
offline MLOps
```

This is not just a normal model monitoring problem.

---

# 14. Offline pipeline design for accelerometer and gyroscope data

Your offline pipeline should look like this:

```text
[Raw Watch Sensor Files]
        ↓
[Data Ingestion]
        ↓
[Schema + Unit Validation]
        ↓
[Timestamp Cleaning]
        ↓
[Resample 100 Hz to 50 Hz]
        ↓
[Unit Conversion]
        ↓
[Axis Alignment / Calibration]
        ↓
[Accelerometer + Gyroscope Synchronization]
        ↓
[Windowing]
        ↓
[Feature Extraction / Model Input]
        ↓
[Model Prediction]
        ↓
[Monitoring Logs]
        ↓
[Drift Reports]
        ↓
[Human Review / Label Sampling]
        ↓
[Retraining Candidate]
```

Important principle:

**Do not send raw production data directly into the model.**

First validate whether it is physically and statistically compatible with the training/fine-tuning data.

---

## 14.1 Data ingestion checks

At ingestion, measure:

```text
file format
required columns
data types
timestamp order
duplicate timestamps
missing values
raw sampling rate
recording duration
number of rows
sensor min/max
sensor units
```

Required columns:

```text
timestamp
acc_x
acc_y
acc_z
gyro_x
gyro_y
gyro_z
```

Example ingestion log:

```text
file_id
start_time
end_time
duration_seconds
raw_sampling_rate
rows_before_cleaning
rows_after_cleaning
missing_rate_acc_x
missing_rate_gyro_x
max_gyro_x
unit_conversion_applied
resampling_success
```

---

## 14.2 Resampling from 100 Hz to 50 Hz

At 50 Hz, one sample occurs every:

```text
20 ms
```

Do not simply drop every second row without checking.

Better process:

```text
1. sort by timestamp
2. remove duplicate timestamps
3. check timestamp gaps
4. interpolate to a uniform time grid if needed
5. apply low-pass filter
6. downsample to 50 Hz
```

Why low-pass filter?

Because if you downsample from 100 Hz to 50 Hz without filtering, you can create aliasing.

Practical rule:

```text
100 Hz raw signal
↓
low-pass filter below 25 Hz
↓
resample to 50 Hz
```

---

## 14.3 Unit conversion

Accelerometer may be recorded in:

```text
g
mg
m/s²
raw sensor units
```

Conversions:

```text
m/s² = g × 9.80665

m/s² = mg × 9.80665 / 1000
```

Gyroscope may be recorded in:

```text
degrees/second
radians/second
raw sensor units
```

Conversion:

```text
rad/s = deg/s × π / 180
```

A unit mismatch can easily create huge drift.

For example:

```text
deg/s vs rad/s
mg vs m/s²
g vs m/s²
```

Always log:

```text
acc_unit_before
acc_unit_after
gyro_unit_before
gyro_unit_after
conversion_applied
```

---

## 14.4 Axis alignment

The watch coordinate system may not match the training sensor coordinate system.

Possible problems:

```text
x/y/z axes swapped
axis sign reversed
left hand vs right hand
watch worn differently
device orientation changed
API coordinate system different
```

Example transformation:

```text
gyro_x_new = gyro_y_old
gyro_y_new = -gyro_x_old
gyro_z_new = gyro_z_old
```

Do not assume the watch axes match the research-grade sensor axes.

You should check:

```text
axis orientation
sign direction
dominant axis per activity
magnitude consistency
left/right wrist wearing
device coordinate documentation
```

---

## 14.5 Synchronizing accelerometer and gyroscope

You need to combine:

```text
acc_x, acc_y, acc_z
gyro_x, gyro_y, gyro_z
```

into:

```text
timestamp, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z
```

You mentioned around 1 millisecond tolerance.

At 50 Hz:

```text
one sample interval = 20 ms
```

A 1 ms tolerance is strict and can be okay, but you must monitor how many rows are matched.

Track:

```text
percentage of accelerometer rows matched with gyroscope
percentage of gyroscope rows matched with accelerometer
mean timestamp difference
max timestamp difference
number of dropped rows
missing synchronized rows
```

If many rows are dropped, your windows become unreliable.

---

## 14.6 Windowing

The model usually does not classify one row.
It classifies a time window.

Example:

```text
50 Hz data
2-second window
100 samples per window
```

or:

```text
50 Hz data
5-second window
250 samples per window
```

You may use overlap:

```text
50% overlap
```

Each window becomes one prediction:

```text
window_001 → walking
window_002 → walking
window_003 → sitting
```

For each window, log:

```text
window_id
start_time
end_time
number_of_samples
missing_rate
sensor statistics
prediction
class probabilities
confidence
entropy
drift score
OOD score
```

---

# 15. Drift metrics for unlabeled wearable-sensor data

Because the production/testing data is unlabeled, you cannot calculate true classification metrics.

You cannot calculate:

```text
accuracy
macro F1
weighted F1
per-class precision
per-class recall
confusion matrix
```

But you can calculate many useful proxy metrics.

---

## 15.1 Raw-axis drift

For every axis:

```text
acc_x
acc_y
acc_z
gyro_x
gyro_y
gyro_z
```

Measure:

```text
mean
standard deviation
min
max
median
IQR
skewness
kurtosis
missing rate
zero rate
clipping rate
spike rate
```

Compare production to fine-tuned baseline.

Example:

```text
gyro_x training std = 0.8
gyro_x production std = 8.5
```

This is severe drift.

---

## 15.2 Signal magnitude drift

For accelerometer:

```text
acc_magnitude = sqrt(acc_x² + acc_y² + acc_z²)
```

For gyroscope:

```text
gyro_magnitude = sqrt(gyro_x² + gyro_y² + gyro_z²)
```

Magnitude is useful because it is less sensitive to axis rotation.

Track:

```text
mean acc magnitude
std acc magnitude
max acc magnitude
mean gyro magnitude
std gyro magnitude
max gyro magnitude
```

If only gyro_x is strange but gyro magnitude is normal, maybe axis mapping is the issue.

If gyro magnitude is also huge, unit mismatch or sensor corruption is more likely.

---

## 15.3 Window-level feature drift

For each time window, extract features:

```text
mean per axis
std per axis
min/max per axis
RMS
energy
signal magnitude area
jerk features
dominant frequency
spectral entropy
correlation between axes
zero crossing rate
```

Then compare production window-feature distributions to fine-tuned training window-feature distributions.

Useful metrics:

```text
KS test
Wasserstein distance
PSI
Jensen-Shannon divergence
Mahalanobis distance
MMD
```

For your case, I would prioritize:

```text
robust z-score per feature
Wasserstein distance
PSI
Mahalanobis distance
embedding drift
```

---

## 15.4 Embedding drift

If your model is a neural network, take the second-last layer representation.

For each window:

```text
embedding = model_hidden_layer(window)
```

Then compare production embeddings with training/fine-tuning embeddings.

Use:

```text
PCA visualization
UMAP visualization
centroid distance
nearest-neighbor distance
Mahalanobis distance
MMD
```

If production embeddings are far from training embeddings, the model likely sees unfamiliar data.

---

## 15.5 Prediction drift

After running the model, track:

```text
predicted class distribution
average confidence
confidence per class
entropy
top-1 vs top-2 margin
class switching rate
```

Example:

```text
Fine-tuned validation:
walking = 20%
sitting = 15%
standing = 15%

Production:
walking = 70%
sitting = 3%
standing = 2%
```

This is prediction drift.

---

## 15.6 Confidence drift

Track:

```text
average max probability
median max probability
percentage of windows with confidence < 0.5
percentage of windows with confidence > 0.9
entropy
top-1/top-2 probability margin
```

Example:

```text
fine-tuned validation average confidence = 0.86
production average confidence = 0.52
```

This suggests the model is uncertain.

---

## 15.7 Temporal consistency

Activities usually do not change every few milliseconds.

Bad pattern:

```text
walking → sitting → running → lying → stairs → walking
```

within a few seconds.

Track:

```text
class switch rate per minute
average predicted activity duration
impossible transition count
prediction smoothing effect
```

You can smooth predictions using:

```text
majority vote over last N windows
rolling probability average
Hidden Markov Model smoothing
transition constraints
```

---

## 15.8 Out-of-distribution detection

Useful OOD methods:

```text
Mahalanobis distance on features
autoencoder reconstruction error
isolation forest
one-class SVM
deep embedding distance
softmax entropy
energy score
```

Practical local approach:

```text
1. Extract window features from fine-tuned labeled data
2. Fit a scaler
3. Fit covariance/PCA model
4. Compute Mahalanobis distance for production windows
5. Alert if distance is above 95th or 99th percentile of validation data
```

---

# 16. What to do with severe gyroscope-axis drift

You said one gyro axis is 7x to 17x larger than training.

This is not small drift.

This is a critical warning.

Before retraining, assume a possible:

```text
unit mismatch
axis mapping mismatch
sensor calibration issue
sensor saturation
timestamp alignment problem
bad recording session
watch wearing-position difference
```

Do not immediately retrain on this data.

---

## 16.1 Investigation sequence

Use this sequence:

```text
1. Quarantine the suspicious data
2. Validate gyroscope units
3. Validate axis orientation
4. Check sensor range and clipping
5. Compare gyro magnitude
6. Check timestamp alignment
7. Check whether this happens in all files or only some
8. Run model with and without gyro_x
9. Compare confidence, entropy, OOD score, and prediction stability
10. Collect small labeled sample
11. Decide whether retraining is needed
```

---

## 16.2 Run ablation tests

Run inference using:

```text
A. accelerometer only
B. gyroscope only
C. all six channels
D. all six channels except gyro_x
E. all six channels with gyro_x clipped/normalized
```

Since you do not have labels, compare proxy signals:

```text
average confidence
entropy
prediction stability
OOD score
embedding distance
prediction distribution
temporal smoothness
```

If removing gyro_x makes the model more stable, gyro_x is likely damaging the model.

But remember: without labels, this is still only indirect evidence.

---

## 16.3 Do not hide broken data with normalization

Do not simply normalize everything and assume it is fixed.

Bad idea:

```text
gyro_x is 17x larger → just scale it down and trust predictions
```

Why?

Because the problem may be:

```text
wrong units
wrong axis
bad sensor
wrong timestamp
wrong wearing position
```

Normalization may hide the symptom while leaving the cause.

---

# 17. Can unlabeled data improve the model?

Yes, but carefully.

Unlabeled data can help with:

```text
normalization recalibration
self-supervised learning
unsupervised domain adaptation
pseudo-labeling
test-time adaptation
representation learning
cluster analysis
active learning sample selection
```

But unlabeled data cannot fully replace labels.

It cannot reliably tell you:

```text
this window is walking
this window is sitting
this window is stairs
```

unless you use risky assumptions.

---

## 17.1 Normalization recalibration

You can update normalization statistics using production data.

Example:

```text
training mean/std
production mean/std
```

But this is risky if production data contains corrupted values.

Safer method:

```text
use robust scaler
clip extreme values
exclude OOD windows
update slowly with rolling statistics
keep old scaler version
compare before/after predictions
```

---

## 17.2 Pseudo-labeling

Pseudo-labeling means using the model’s own confident predictions as labels.

Example rule:

```text
if confidence > 0.95
and entropy is low
and OOD score is low
and prediction is temporally stable
then accept pseudo-label
```

Then train with:

```text
original labeled data + high-confidence pseudo-labeled production data
```

Risk:

If the model is confidently wrong, it will reinforce its own mistakes.

Use strict filters:

```text
high confidence
low entropy
low OOD score
temporal consistency
class-balance control
human review of sample
```

---

## 17.3 Self-supervised learning

Self-supervised learning is often very useful for unlabeled sensor data.

Possible tasks:

```text
predict masked sensor values
reconstruct sensor windows
contrastive learning between augmented windows
predict future segment
detect transformed signals
learn invariant embeddings
```

Then fine-tune the classifier using labeled data.

This can improve representation without needing labels for every production window.

---

## 17.4 Unsupervised domain adaptation

You can align source and target distributions.

Source:

```text
fine-tuned labeled dataset
```

Target:

```text
unlabeled production dataset
```

Methods:

```text
CORAL
MMD alignment
adversarial domain adaptation
feature normalization alignment
domain-invariant representation learning
```

This can help when the production device/domain is different but the activity classes are the same.

---

## 17.5 Active learning

This is usually the best practical strategy.

Instead of labeling everything, label the most useful samples.

Choose samples with:

```text
high uncertainty
high OOD score
high drift
rare predicted classes
unstable class transitions
representative clusters
abnormal gyro_x behavior
```

Then manually label a small set.

Example:

```text
50–100 windows per class
5–10 minutes per activity
a few sessions from different users
```

This gives much better value than random labeling.

---

# 18. Retraining strategy with labeled and unlabeled data

## 18.1 Do you need labels for retraining?

For proper supervised retraining:

```text
Yes, you need labels.
```

For unsupervised adaptation:

```text
No, but it is riskier and should be validated.
```

Comparison:

| Method                      |  Needs Labels? |        Risk | Purpose                   |
| --------------------------- | -------------: | ----------: | ------------------------- |
| Supervised retraining       |            Yes |  Low/medium | Best real improvement     |
| Fine-tuning classifier      |            Yes |  Low/medium | Improve decision boundary |
| Pseudo-labeling             | No true labels | Medium/high | Use confident predictions |
| Self-supervised pretraining |             No |  Low/medium | Improve representation    |
| Domain adaptation           |  No or partial |      Medium | Align source and target   |
| Normalization recalibration |             No |      Medium | Adjust sensor scale       |
| Active learning             |   Small labels |         Low | Efficient labeling        |

---

## 18.2 Recommended retraining workflow

Use this:

```text
1. Detect drift or OOD behavior
2. Verify preprocessing and units
3. Quarantine suspicious data
4. Select a small sample for labeling
5. Label important production windows
6. Evaluate current model using real labels
7. If performance is bad, retrain/fine-tune
8. Compare new model against old model
9. Deploy only if new model is better
10. Continue monitoring
```

---

## 18.3 Do not retrain only because drift exists

Drift is a warning, not proof of bad performance.

Example:

Production activity distribution may really be different:

```text
training had many running samples
production has mostly sitting samples
```

That is data drift, but the model may still be correct.

So retrain when:

```text
drift is high
AND/OR confidence is low
AND/OR OOD score is high
AND/OR labeled sample confirms performance drop
```

Best condition:

```text
labeled production sample confirms macro F1 or per-class recall dropped
```

---

# 19. Final practical checklist

## 19.1 For your offline wearable-sensor MLOps pipeline

Use this pipeline:

```text
Raw files
↓
Ingestion validation
↓
Timestamp cleaning
↓
Unit conversion
↓
Resampling 100 Hz → 50 Hz
↓
Axis alignment
↓
Accelerometer + gyroscope synchronization
↓
Windowing
↓
Feature/model input creation
↓
Prediction
↓
Logging
↓
Drift/OOD monitoring
↓
Report generation
↓
Human labeling sample selection
↓
Retraining decision
```

---

## 19.2 What to log per window

Log:

```text
window_id
file_id
start_time
end_time
model_version
scaler_version
sampling_rate_after_resample
acc_x_mean
acc_y_mean
acc_z_mean
gyro_x_mean
gyro_y_mean
gyro_z_mean
acc_magnitude_mean
gyro_magnitude_mean
drift_score
ood_score
predicted_class
class_probability_1
class_probability_2
...
class_probability_11
max_probability
entropy
top2_margin
processing_status
```

If labels arrive later, add:

```text
true_label
correct_or_not
```

---

## 19.3 Monitoring report sections

Your local report should include:

```text
1. Data quality
2. Sensor statistics
3. Sampling-rate report
4. Unit-conversion report
5. Synchronization report
6. Raw-axis drift
7. Magnitude drift
8. Window-feature drift
9. Embedding drift
10. Prediction distribution
11. Confidence distribution
12. Temporal consistency
13. OOD window rate
14. Recommended action
```

---

## 19.4 Decision rules

Example rules:

```text
If schema missing:
    fail pipeline

If sampling rate badly wrong:
    fail or quarantine

If unit or axis scale abnormal:
    quarantine and inspect

If one sensor axis is > 5x training range:
    critical alert

If OOD windows > 20%:
    do not fully trust predictions

If average confidence drops > 20%:
    request labeling sample

If prediction distribution changes > 30%:
    investigate drift

If pseudo-labeling:
    only use confidence > 0.95 and low OOD score

If labeled sample confirms performance drop:
    retrain
```

For your specific gyro-x issue:

```text
gyro_x 7x–17x larger than training
```

Decision:

```text
Critical alert.
Check unit, axis, calibration, and timestamp pipeline before retraining.
```

---

## 19.5 Best metrics for your exact case

Because production is unlabeled, use:

### Data quality

```text
missing rate
timestamp gaps
sampling rate
duplicate timestamps
invalid values
sensor min/max
```

### Raw sensor drift

```text
mean/std shift per axis
robust z-score
Wasserstein distance
PSI
KS test
```

### Magnitude drift

```text
accelerometer magnitude drift
gyroscope magnitude drift
```

### Window-feature drift

```text
RMS drift
energy drift
frequency drift
jerk drift
correlation drift
```

### Embedding drift

```text
Mahalanobis distance
nearest-neighbor distance
MMD
centroid shift
```

### Prediction drift

```text
class distribution shift
confidence drop
entropy increase
top-2 margin decrease
class switching rate
```

### OOD detection

```text
autoencoder reconstruction error
isolation forest score
Mahalanobis OOD score
softmax entropy
```

---

# 20. Final summary

Your case is:

```text
multiclass time-series classification
wearable-sensor data
accelerometer + gyroscope
11 activities
labeled source/fine-tuning data
unlabeled production/testing data
domain shift
offline/local MLOps
```

The most important point:

```text
Without production labels, you cannot calculate real accuracy, F1, recall, or confusion matrix.
```

But you can monitor:

```text
data quality
sensor validity
unit correctness
axis alignment
sampling rate
input drift
feature drift
embedding drift
prediction drift
confidence drift
temporal consistency
OOD score
```

For your severe gyro-x shift:

```text
7x–17x larger than training
```

Do not immediately retrain.

First check:

```text
unit mismatch
axis mismatch
sensor calibration
sensor saturation
timestamp synchronization
watch wearing position
recording bug
```

Unlabeled data can help, but mainly for:

```text
drift detection
OOD detection
normalization checks
self-supervised learning
domain adaptation
pseudo-labeling with strict filters
active learning sample selection
```

For reliable retraining, you should get at least a small labeled production sample.

Best strategy:

```text
1. Build strong offline preprocessing validation
2. Compare production data to fine-tuned baseline
3. Detect severe axis/device drift
4. Use confidence, OOD, embedding, and prediction drift metrics
5. Select suspicious/uncertain samples for manual labeling
6. Evaluate real metrics on that labeled sample
7. Retrain only if performance drop is confirmed
8. Deploy the new model only if it beats the old model
```

The practical rule:

```text
Unlabeled data can warn you.
Labeled data confirms performance.
Retraining should be based on confirmation, not only suspicion.
```

---

# 21. One-page cheat sheet

## If labels are available

Use:

```text
accuracy
macro F1
per-class recall
confusion matrix
MAE/RMSE for regression
WAPE/MASE for forecasting
```

## If labels are not available

Use:

```text
data drift
feature drift
prediction drift
confidence drift
OOD detection
temporal consistency
data quality
```

## For multiclass activity recognition

Prioritize:

```text
macro F1
per-class recall
confusion matrix
prediction distribution
confidence distribution
class-switching rate
```

## For sensor drift

Prioritize:

```text
axis-level mean/std shift
magnitude drift
window-feature drift
embedding drift
Mahalanobis/OOD score
```

## For your gyro-x problem

Treat as:

```text
critical preprocessing/sensor/domain issue
```

Check before retraining:

```text
units
axis orientation
calibration
clipping
timestamp alignment
watch position
```

## For retraining

Best:

```text
small labeled production sample + original labeled data
```

Possible but risky:

```text
pseudo-labeling
domain adaptation
self-supervised learning
normalization recalibration
```

---

# End of Guide

```
```

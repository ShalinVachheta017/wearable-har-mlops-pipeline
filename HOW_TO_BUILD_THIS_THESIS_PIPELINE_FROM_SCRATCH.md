# How to Build This Thesis Pipeline from Scratch

**Author:** Shalin Vachheta  
**Thesis topic:** Developing a MLOps Pipeline for Continuous Mental Health Monitoring using Wearable Sensor Data  
**Last updated:** 2026-04-23  

---

## 1. Document Purpose

This guide answers one question: if you had to rebuild the entire thesis project from zero, with nothing but an empty folder and a Python install, what would you code, in what order, and why?

It is not a summary of what the code does. It is a construction manual — the kind you wish you had at the start, written now that you know how the whole system fits together.

Use it if:
- You need to rebuild the pipeline after a catastrophic loss
- You want to explain the architecture to someone new
- You are preparing for the thesis defense and want to retrace every design decision
- You want to understand why the repository is structured the way it is

It covers every layer in concrete terms: what file you create, what goes inside it, what inputs and outputs it handles, and how it connects forward to the next stage.

---

## 2. Final System Overview

### What problem does it solve?

Mental health conditions like anxiety and chronic stress affect quality of life but are difficult to monitor continuously. Wearable sensors — smartwatches, fitness trackers — generate accelerometer and gyroscope data constantly. If a machine learning model can classify physical activities from these sensors reliably and continuously, it creates a passive monitoring signal that clinicians and researchers can use alongside other evidence.

The thesis does not attempt clinical diagnosis. It builds the MLOps infrastructure that would make continuous, governed, and reproducible ML-based HAR possible at the research scale.

### What data does it use?

Raw wrist-worn accelerometer and gyroscope signals sampled at 50 Hz. Each row is a timestamped 3-axis reading (x, y, z). A session is one recording from one participant. Labels (activity class per time window) may or may not be present at inference time. Training always uses labeled data. Production inference runs unlabeled.

Activity classes in the dataset: hand tapping, knuckle cracking, hand writing, phone use, sitting idle, walking, running, and others — a total of 11 classes.

### What does the pipeline do?

It takes raw sensor files as input and produces, in sequence:

1. **Ingestion** — reads and merges raw CSV files, or accepts a pre-fused file
2. **Validation** — checks schema, types, ranges, timestamp alignment, label presence
3. **Transformation** — resamples to 50 Hz, applies unit conversion, z-score normalization, sliding window segmentation
4. **Inference** — loads the trained model, produces class predictions and confidence scores per window
5. **Evaluation** — computes accuracy and F1 if labels exist; computes confidence/dominance distributions always
6. **Monitoring** — three-layer runtime health check: confidence layer, temporal instability layer, drift layer
7. **Trigger policy** — governed decision using 2-of-3 voting, cooldown, and collapse routing
8. **Optional retraining** — model retraining with candidate validation, only when governance conditions are met
9. **Optional registration** — promote retrained model into the registry if it passes quality checks
10. **Optional baseline update** — update the monitoring baseline distribution when retraining is accepted
11. **Optional calibration/UQ** — temperature scaling or MC Dropout for confidence calibration

### What does "offline-first MLOps" mean here?

The entire pipeline runs on a single machine, driven by a CLI entrypoint (`run_pipeline.py`). There is no cloud scheduler, no streaming pipeline, no always-on training server. A user points the CLI at a data file, selects which stages to run, and the pipeline executes sequentially. All artifacts are written to local disk. MLflow tracks experiments locally.

This is a deliberate scope decision. The thesis claims a production-*like* governance architecture, not a production-scale distributed system. The governance contracts — trigger voting, cooldown, collapse guard, opt-in deployment — are identical to what a real system would require. The infrastructure scale is not.

### Where do monitoring and retraining governance fit?

Monitoring (Stage 6) observes each inference run and produces a structured report. It does not decide anything. The trigger policy (Stage 7) reads the monitoring report plus evaluation signals, applies a 2-of-3 voting rule, checks a 24h cooldown, and routes the decision to one of: `NONE`, `MONITOR`, `QUEUE_RETRAIN`, `TRIGGER_RETRAIN`, or `ROLLBACK`. Retraining (Stages 8–10) only executes if the trigger fires and the user explicitly invokes the retraining stages.

---

## 3. Build Order Overview

Build in this order. Each layer depends on the ones above it.

```
Phase 0: Environment and repo skeleton
  - Python + conda environment
  - Folder structure
  - requirements files
  - Git + DVC init
  - CI skeleton

Phase 1: Config and artifact contracts
  - src/config.py           (paths and constants)
  - src/entity/config_entity.py   (stage-level dataclasses)
  - src/entity/artifact_entity.py (stage-level output contracts)
  - src/logger/__init__.py
  - src/utils/artifacts_manager.py

Phase 2: Data layer
  - src/components/data_ingestion.py
  - src/components/data_validation.py
  - src/components/data_transformation.py
  - src/preprocess_data.py (standalone preprocessing utilities)

Phase 3: Model and training
  - src/train.py
  - src/domain_adaptation/adabn.py  (optional, implement last)
  - src/domain_adaptation/tent.py   (optional, implement last)

Phase 4: Inference and evaluation
  - src/run_inference.py
  - src/components/model_inference.py
  - src/evaluate_predictions.py
  - src/components/model_evaluation.py

Phase 5: Monitoring and trigger
  - src/monitoring/post_inference_monitor.py
  - src/monitoring/baseline_builder.py
  - src/components/post_inference_monitoring.py
  - src/trigger_policy.py
  - src/components/trigger_evaluation.py

Phase 6: Retraining, registration, baseline update
  - src/components/model_retraining.py
  - src/components/model_registration.py
  - src/components/baseline_update.py
  - src/model_rollback.py
  - src/mlflow_tracking.py

Phase 7: Orchestration
  - src/pipeline/production_pipeline.py
  - run_pipeline.py
  - src/cli.py

Phase 8: API
  - src/api/app.py

Phase 9: Docker
  - docker/Dockerfile.inference
  - docker/Dockerfile.training
  - docker-compose.yml

Phase 10: Tests
  - tests/ (build tests alongside each layer)

Phase 11: Experiment scripts and thesis evidence
  - scripts/ and outputs/
```

---

## 4. Environment Setup

### Python version

Use Python 3.10. It is the last version with stable support for TensorFlow 2.11 on Windows without GPU complications. Avoid 3.11+ unless you test TF compatibility carefully.

### Conda environment

```bash
conda create -n thesis-mlops python=3.10 -y
conda activate thesis-mlops
```

Name it something explicit (`thesis-mlops`, not `env` or `ml`). You will use this name in every script, CI config, and Docker build instruction.

### Package installation strategy

Split your dependencies into three files from day one:

**`requirements.txt`** — everything needed to run the full pipeline locally:
```
tensorflow==2.11.0
numpy>=1.23
pandas>=1.5
scikit-learn>=1.1
scipy>=1.9
mlflow>=2.0
fastapi>=0.100
uvicorn[standard]>=0.22
python-multipart>=0.0.6
pyyaml>=6.0
matplotlib>=3.6
seaborn>=0.12
tqdm>=4.64
```

**`requirements-inference.txt`** — minimal set for the Docker inference image (no training, no MLflow):
```
tensorflow==2.11.0
numpy>=1.23
pandas>=1.5
scikit-learn>=1.1
scipy>=1.9
fastapi>=0.100
uvicorn[standard]>=0.22
python-multipart>=0.0.6
```

**`requirements-dev.txt`** — linting, testing, formatting:
```
pytest>=7.0
pytest-cov>=4.0
flake8>=6.0
black>=23.0
isort>=5.12
```

Install all at once for local dev:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### Basic folders to create first

```bash
mkdir -p src/entity src/components src/monitoring src/domain_adaptation src/pipeline src/utils src/logger src/api
mkdir -p config data/raw data/processed data/prepared models/retrained models/pretrained
mkdir -p artifacts reports outputs scripts tests docs/thesis thesis/chapters thesis/reference thesis/figures
touch src/__init__.py src/entity/__init__.py src/components/__init__.py
touch src/monitoring/__init__.py src/domain_adaptation/__init__.py src/pipeline/__init__.py
touch src/utils/__init__.py src/logger/__init__.py src/api/__init__.py
```

Create these `__init__.py` files on day one. Python module imports will fail silently or with confusing errors without them.

### Tools for development vs inference vs training

| Tool | Training | Inference | Development |
|---|---|---|---|
| TensorFlow | YES | YES (for model.predict) | YES |
| MLflow | YES | NO | YES |
| FastAPI | NO | YES | YES |
| pytest | NO | NO | YES |
| black/flake8 | NO | NO | YES |

---

## 5. Recommended Repository Structure

```
MasterArbeit_MLops/
│
├── run_pipeline.py              # Main CLI entrypoint (single file)
├── src/
│   ├── config.py                # PROJECT_ROOT, model paths, constants
│   ├── cli.py                   # Installed CLI wrapper (optional)
│   ├── entity/
│   │   ├── config_entity.py     # All stage config dataclasses
│   │   └── artifact_entity.py   # All stage output dataclasses
│   ├── components/              # One file per pipeline stage
│   │   ├── data_ingestion.py
│   │   ├── data_validation.py
│   │   ├── data_transformation.py
│   │   ├── model_inference.py
│   │   ├── model_evaluation.py
│   │   ├── post_inference_monitoring.py
│   │   ├── trigger_evaluation.py
│   │   ├── model_retraining.py
│   │   ├── model_registration.py
│   │   └── baseline_update.py
│   ├── pipeline/
│   │   └── production_pipeline.py   # Orchestrator
│   ├── monitoring/
│   │   ├── post_inference_monitor.py  # Monitor logic
│   │   └── baseline_builder.py        # Build/load baselines
│   ├── domain_adaptation/
│   │   ├── adabn.py
│   │   └── tent.py
│   ├── utils/
│   │   └── artifacts_manager.py       # Save/load artifacts to disk
│   ├── logger/
│   │   └── __init__.py                # Centralized logger
│   ├── api/
│   │   └── app.py                     # FastAPI service
│   ├── sensor_data_pipeline.py        # Fused preprocessing pipeline
│   ├── preprocess_data.py             # Standalone preprocessing (unit conversion, normalizer, windowing)
│   ├── run_inference.py               # Standalone inference runner
│   ├── evaluate_predictions.py        # Standalone evaluation runner
│   ├── trigger_policy.py              # Trigger engine
│   ├── mlflow_tracking.py             # MLflow helper
│   └── model_rollback.py              # Rollback helper
│
├── config/
│   ├── pipeline_config.yaml           # Preprocessing knobs
│   └── pipeline_overrides.yaml        # Monitoring/trigger threshold overrides
│
├── data/
│   ├── raw/                           # Original sensor CSVs — never modified
│   ├── processed/                     # Merged/resampled but not normalized
│   └── prepared/
│       ├── X_train.npy
│       ├── y_train.npy
│       ├── config.json                # Label mapping and window config
│       └── scaler_params.json
│
├── models/
│   ├── pretrained/                    # Original downloaded/given model
│   └── retrained/
│       ├── har_model_<timestamp>.keras
│       └── scaler_config.json
│
├── artifacts/                         # One folder per pipeline run
│   └── <run_id>/
│       ├── ingestion/
│       ├── validation/
│       ├── transformation/
│       ├── inference/
│       ├── evaluation/
│       ├── monitoring/
│       └── trigger/
│
├── tests/
│   ├── conftest.py
│   ├── test_data_ingestion.py
│   ├── test_data_validation.py
│   ├── test_post_inference_monitor.py
│   ├── test_trigger_policy.py
│   ├── test_api_upload_modes.py
│   └── test_threshold_consistency.py
│
├── scripts/                           # Experiment runners, diagnostics, utilities
│   └── archive/                       # Superseded scripts — never delete without evidence
│
├── reports/                           # Human-readable evidence outputs
│   ├── repo_audit/
│   ├── before_vs_after_model_change/
│   └── api_operational_smoke_*.md
│
├── outputs/                           # Charts, CSVs, experiment summaries
│   └── charts_26runs/
│
├── thesis/                            # LaTeX thesis document
│   ├── main.tex
│   ├── references.bib
│   ├── chapters/
│   ├── figures/
│   └── reference/
│       └── THRESHOLD_CITATIONS.md
│
├── docs/                              # Architecture and planning docs
│   └── thesis/
│
├── docker/
│   ├── Dockerfile.inference
│   └── Dockerfile.training
├── docker-compose.yml
├── .github/workflows/
│   ├── ci.yml
│   └── cd.yml
├── requirements.txt
├── requirements-inference.txt
├── requirements-dev.txt
├── setup.py                           # For `har-pipeline` CLI install
├── WORKLOG.md
└── README.md
```

**Rule:** `src/` contains production logic only. `scripts/` contains experiments, diagnostics, and one-off runners. Never import from `scripts/` inside `src/`. The boundary is a one-way door.

---

## 6. Configuration-First Design

Build the config system before writing a single pipeline stage. Every stage reads a config object. If the config system is clean, every stage is independently testable.

### Why config-first?

When you hard-code a value like `window_size = 200` in a preprocessing function, you cannot sweep it, override it from CLI, or document it in the thesis. When you define it in a config dataclass, you get all of these for free.

### `src/config.py` — paths and constants

This is the single source of truth for paths. Every file that needs to know the project root imports it from here.

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRETRAINED_MODEL = PROJECT_ROOT / "models" / "pretrained" / "har_model_base.keras"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "retrained" / "har_model_20260327_223917.keras"
DEFAULT_SCALER_CONFIG = PROJECT_ROOT / "models" / "retrained" / "scaler_config.json"
LABEL_CONFIG_PATH = PROJECT_ROOT / "data" / "prepared" / "config.json"
BASELINE_DIR = PROJECT_ROOT / "models" / "retrained"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
```

Never compute `Path(__file__).parent.parent` in any other file. Always import from here.

### `src/entity/config_entity.py` — stage config dataclasses

Define one dataclass per stage. Use Python `@dataclass` with typed fields and documented defaults. This file is the single place where all operational thresholds live.

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass
class DataIngestionConfig:
    raw_data_dir: Path
    processed_data_dir: Path
    expected_sampling_rate: int = 50
    timestamp_column: str = "timestamp"

@dataclass
class DataValidationConfig:
    required_accel_columns: list = field(default_factory=lambda: ["timestamp", "x", "y", "z"])
    required_gyro_columns: list = field(default_factory=lambda: ["timestamp", "x", "y", "z"])
    min_rows: int = 500
    max_timestamp_gap_seconds: float = 2.0

@dataclass
class DataTransformationConfig:
    window_size: int = 200          # 4 seconds at 50 Hz
    overlap: float = 0.5            # 50% overlap
    normalization: str = "zscore"   # "zscore" | "minmax" | "none"
    target_sampling_rate: int = 50
    gravity_removal: bool = True
    unit_conversion: bool = True

@dataclass
class PostInferenceMonitoringConfig:
    # Layer 1 — confidence
    confidence_warn_threshold: float = 0.70
    uncertain_pct_threshold: float = 20.0
    per_window_uncertain_cutoff: float = 0.50
    # Layer 1b — dominant-class collapse
    dominant_class_warn_threshold: float = 85.0
    dominant_class_critical_threshold: float = 95.0
    # Layer 2 — temporal
    transition_rate_threshold: float = 35.0
    # Layer 3 — drift
    drift_zscore_threshold: float = 1.8
    drift_zscore_critical: float = 3.0
    drift_detector_mode: str = "zscore_mean_shift"
    max_baseline_age_days: int = 90

@dataclass
class TriggerEvaluationConfig:
    # Stage 7 thresholds — intentionally tighter than Stage 6 early-warning values
    confidence_warn: float = 0.65
    flip_rate_warn: float = 0.35
    flip_rate_critical: float = 0.50
    drift_zscore_warn: float = 2.0
    drift_zscore_critical: float = 3.0
    required_votes_to_trigger: int = 2   # 2-of-3
    cooldown_hours: int = 24

@dataclass
class ModelRetrainingConfig:
    epochs: int = 50
    batch_size: int = 32
    adaptation_method: str = "none"   # "adabn" | "tent" | "adabn_tent" | "pseudo_label" | "none"
    min_labeled_windows: int = 100
    auto_deploy: bool = False         # never auto-deploy by default
    promote_to_shared: bool = False   # baseline promotion is opt-in
```

**Design rule:** Stage 6 (monitoring) and Stage 7 (trigger) intentionally have different threshold values. Stage 6 warns earlier. Stage 7 escalates under voting. Never merge them into one block or a reviewer will find it in five minutes.

### `config/pipeline_overrides.yaml` — runtime overrides

Operators who want to change thresholds without editing code write YAML here. The pipeline reads this file and merges it over the dataclass defaults.

```yaml
monitoring:
  confidence_warn_threshold: 0.70
  drift_zscore_threshold: 1.8

trigger:
  cooldown_hours: 24
  required_votes_to_trigger: 2
```

---

## 7. Data Layer

### Inputs

The pipeline accepts two input formats:

1. **Fused CSV** — a single file containing both accelerometer and gyroscope columns plus a timestamp. Column names: `timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z`.
2. **Raw pair** — two separate files, one accelerometer and one gyroscope, each with `timestamp, x, y, z` columns. The pipeline merges them by aligning timestamps.

### Why two formats?

Different sensor platforms export differently. Garmin exports a fused CSV. Some research datasets export separate files. Supporting both avoids requiring the user to manually preprocess data before using the pipeline — that preprocessing belongs inside the pipeline under version control.

### `src/components/data_ingestion.py`

This component owns reading, merging, and resampling.

```python
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config

    def initiate_data_ingestion(self, accel_path, gyro_path=None) -> DataIngestionArtifact:
        if gyro_path is None:
            df = self._load_fused(accel_path)
        else:
            df = self._merge_pair(accel_path, gyro_path)
        df = self._resample(df, target_hz=self.config.expected_sampling_rate)
        output_path = self.config.processed_data_dir / "fused_session.csv"
        df.to_csv(output_path, index=False)
        return DataIngestionArtifact(fused_csv_path=output_path, total_rows=len(df))

    def _load_fused(self, path) -> pd.DataFrame:
        df = pd.read_csv(path)
        # rename columns to canonical names if needed
        return df

    def _merge_pair(self, accel_path, gyro_path) -> pd.DataFrame:
        accel = pd.read_csv(accel_path).rename(columns={"x":"accel_x","y":"accel_y","z":"accel_z"})
        gyro  = pd.read_csv(gyro_path).rename(columns={"x":"gyro_x","y":"gyro_y","z":"gyro_z"})
        # merge on nearest timestamp
        df = pd.merge_asof(accel.sort_values("timestamp"),
                           gyro.sort_values("timestamp"),
                           on="timestamp", tolerance=20, direction="nearest")
        return df.dropna()

    def _resample(self, df, target_hz) -> pd.DataFrame:
        # convert timestamp to datetime index, resample to target_hz using linear interpolation
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("timestamp").resample(f"{1000//target_hz}ms").mean().interpolate()
        return df.reset_index()
```

**Output:** `DataIngestionArtifact` — a dataclass holding `fused_csv_path`, `total_rows`, `sampling_rate`, `has_labels`.

### Unit conversion

Garmin and some research sensors export accelerometer data in milliG (mG), not m/s². You must detect which unit is present and convert before normalization.

```python
def convert_units(df: pd.DataFrame) -> pd.DataFrame:
    # Garmin milliG → m/s²: divide by 1000, multiply by 9.81
    for col in ["accel_x", "accel_y", "accel_z"]:
        if df[col].abs().max() > 50:   # heuristic: real m/s² accel rarely exceeds 50
            df[col] = df[col] / 1000.0 * 9.81
    return df
```

Document this heuristic in the thesis. It is an engineering assumption that must be acknowledged.

---

## 8. Validation Layer

### What to validate and why

Validation exists to catch bad data before it silently corrupts downstream outputs. A pipeline that crashes with a KeyError at window generation is worse than one that validates early and emits a clear error.

### `src/components/data_validation.py`

```python
class DataValidation:
    def __init__(self, config: DataValidationConfig):
        self.config = config

    def initiate_data_validation(self, artifact: DataIngestionArtifact) -> DataValidationArtifact:
        df = pd.read_csv(artifact.fused_csv_path)
        errors = []

        # Schema check
        for col in self.config.required_fused_columns:
            if col not in df.columns:
                errors.append(f"Missing column: {col}")

        # Row count sanity
        if len(df) < self.config.min_rows:
            errors.append(f"Too few rows: {len(df)} < {self.config.min_rows}")

        # Range check — acceleration in m/s² should not exceed ~20 under normal activity
        for col in ["accel_x", "accel_y", "accel_z"]:
            if col in df.columns:
                if df[col].abs().max() > 100:
                    errors.append(f"Suspicious range in {col}: max={df[col].abs().max():.1f}")

        # Timestamp monotonicity
        if "timestamp" in df.columns:
            if not df["timestamp"].is_monotonic_increasing:
                errors.append("Timestamps are not monotonically increasing")

        # Label check (soft — not an error if absent for inference)
        has_labels = "activity_label" in df.columns and df["activity_label"].notna().any()

        validation_status = "VALID" if not errors else "INVALID"
        return DataValidationArtifact(
            validation_status=validation_status,
            errors=errors,
            has_labels=has_labels,
            row_count=len(df)
        )
```

**Save the validation report as JSON** to the artifacts directory. This becomes thesis evidence that your pipeline self-checks its inputs.

---

## 9. Preprocessing Layer

### What preprocessing must do

The preprocessing layer takes validated raw sensor data and produces the fixed-shape windows the model expects. Every decision here must be made identically at training time and at inference time. This is called **train/serve parity** and it is the most common source of silent bugs in ML pipelines.

### Steps in order

1. **Gravity removal** — optional high-pass filter to remove the static gravity component from the accelerometer signal
2. **Unit conversion** — milliG to m/s² if needed (done before normalization)
3. **Z-score normalization** — subtract mean, divide by std, computed on training data and applied to new data using the same parameters
4. **Sliding window segmentation** — 200-sample windows (4 seconds at 50 Hz), 50% overlap by default
5. **Feature tensor construction** — output shape: `(n_windows, 200, 6)` — 6 channels: accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z

### Why 200 samples?

4 seconds captures most HAR activities in one window. Activities like hand tapping and walking have cycle lengths well under 4 seconds. Longer windows risk spanning activity transitions. Shorter windows lose temporal context for the BiLSTM. 200 is a standard choice in the HAR literature (Bulling et al., 2014).

### `src/preprocess_data.py` — core preprocessing utilities

```python
import numpy as np
import json
from pathlib import Path

class ZScoreNormalizer:
    def __init__(self):
        self.mean = None
        self.std = None

    def fit(self, X: np.ndarray):
        # X shape: (n_samples, n_channels)
        self.mean = X.mean(axis=0)
        self.std  = X.std(axis=0) + 1e-8   # avoid divide-by-zero

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (X - self.mean) / self.std

    def save(self, path: Path):
        json.dump({"mean": self.mean.tolist(), "std": self.std.tolist()}, open(path, "w"))

    def load(self, path: Path):
        params = json.load(open(path))
        self.mean = np.array(params["mean"])
        self.std  = np.array(params["std"])
```

**Critical rule:** fit the normalizer on training data only. Save the parameters. Load them at inference time. Never refit on production data. The model was trained on a specific scale — inference must use that exact scale.

### Sliding window function

```python
def sliding_windows(data: np.ndarray, window_size: int, overlap: float):
    step = int(window_size * (1 - overlap))
    windows = []
    for start in range(0, len(data) - window_size + 1, step):
        windows.append(data[start : start + window_size])
    return np.array(windows)   # shape: (n_windows, window_size, n_channels)
```

### Saving scaler parameters for serve-time use

At training time:
```python
normalizer = ZScoreNormalizer()
normalizer.fit(X_train_flat)   # flatten to (n_samples, 6) before fitting
normalizer.save(DEFAULT_SCALER_CONFIG)
```

At inference time (in the API or the inference component):
```python
normalizer = ZScoreNormalizer()
normalizer.load(DEFAULT_SCALER_CONFIG)
X_normalized = normalizer.transform(raw_windows)
```

If you skip saving the scaler and refit at inference time, your normalized values will differ from training — and the model will silently produce wrong predictions with high confidence.

---

## 10. Model Development

### Why 1D-CNN + BiLSTM?

- **1D-CNN** extracts local temporal patterns from each sensor channel — heartbeat-like rhythms in the accelerometer signal, short-duration impulses from hand tapping
- **BiLSTM** captures long-range temporal dependencies across the 4-second window, looking forward and backward simultaneously
- **Combined:** CNN acts as a learnable feature extractor; BiLSTM reads the feature map across time. This architecture is standard for raw sensor HAR (see Ordóñez & Roggen 2016)

### Input shape

`(batch_size, 200, 6)` — 200 timesteps, 6 channels (accel xyz + gyro xyz)

### Architecture definition in `src/train.py`

```python
import tensorflow as tf

def build_model(input_shape=(200, 6), n_classes=11):
    inputs = tf.keras.Input(shape=input_shape)

    # Convolutional feature extraction
    x = tf.keras.layers.Conv1D(64, kernel_size=5, activation="relu", padding="same")(inputs)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Conv1D(128, kernel_size=3, activation="relu", padding="same")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.MaxPooling1D(pool_size=2)(x)
    x = tf.keras.layers.Dropout(0.3)(x)

    # Temporal sequence modeling
    x = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(128, return_sequences=False))(x)
    x = tf.keras.layers.Dropout(0.3)(x)

    # Classification head
    x = tf.keras.layers.Dense(64, activation="relu")(x)
    outputs = tf.keras.layers.Dense(n_classes, activation="softmax")(x)

    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model
```

### Callbacks

```python
callbacks = [
    tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True),
    tf.keras.callbacks.ModelCheckpoint(
        filepath=str(model_save_path),
        monitor="val_accuracy",
        save_best_only=True
    ),
    tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6)
]
```

### Cross-validation strategy

For a small dataset (26 sessions, ~11 participants), use **Leave-One-Session-Out (LOSO) cross-validation** or at minimum stratified k-fold where each fold preserves class balance. LOSO is the thesis-appropriate choice because it tests generalization across participants, not just across shuffled windows from the same session.

```python
from sklearn.model_selection import GroupKFold

gkf = GroupKFold(n_splits=n_sessions)
for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=session_ids)):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
    model = build_model()
    model.fit(X_train, y_train, validation_data=(X_val, y_val), callbacks=callbacks, ...)
```

### Saving the trained model

```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = BASELINE_DIR / f"har_model_{timestamp}.keras"
model.save(str(model_path))
```

Use the `.keras` format (not `.h5`). It stores architecture + weights + optimizer state in one file and is the recommended format from Keras 3.

---

## 11. Inference Layer

### What inference does

Inference takes the trained model and a preprocessed tensor and returns per-window class predictions and confidence scores. Nothing else. It does not update weights, does not retrain, does not write to MLflow.

### `src/run_inference.py` — standalone inference

```python
import numpy as np
import tensorflow as tf
import json

class InferencePipeline:
    def __init__(self, model_path, scaler_config_path, label_config_path):
        self.model = tf.keras.models.load_model(str(model_path))
        self.scaler = ZScoreNormalizer()
        self.scaler.load(scaler_config_path)
        with open(label_config_path) as f:
            config = json.load(f)
        self.label_map = config["label_map"]          # int -> class name
        self.n_classes = len(self.label_map)

    def predict(self, X_windows: np.ndarray) -> dict:
        # X_windows: (n_windows, 200, 6), already normalized
        probabilities = self.model.predict(X_windows, verbose=0)
        predicted_classes = np.argmax(probabilities, axis=1)
        confidence_scores = probabilities.max(axis=1)
        return {
            "predicted_labels": [self.label_map[str(c)] for c in predicted_classes],
            "predicted_indices": predicted_classes.tolist(),
            "confidence_scores": confidence_scores.tolist(),
            "probabilities": probabilities.tolist()
        }
```

### What must remain identical between training and inference

| What | Training | Inference |
|---|---|---|
| Window size | 200 | 200 |
| Overlap | 0.5 | 0.5 |
| Channel order | accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z | same |
| Normalization | fit on train data, save params | load params, transform |
| Label mapping | built from training labels | load from `data/prepared/config.json` |

If any of these diverge between training and inference, the model predicts on differently scaled input and produces systematically wrong outputs — with no error message.

---

## 12. Evaluation Layer

### When labels are present (training, ablation, comparison experiments)

```python
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

def evaluate_with_labels(y_true, y_pred, confidence_scores):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "mean_confidence": float(np.mean(confidence_scores)),
        "n_windows": len(y_pred)
    }
```

### When labels are absent (production inference, API uploads)

You cannot compute accuracy. You still compute:
- Mean confidence score across all windows
- Percentage of windows with confidence below the uncertain cutoff (0.50)
- Class distribution: which activity is predicted most often
- Dominant class percentage: if one class accounts for >85% of windows, that is suspicious

```python
def evaluate_unlabeled(predicted_labels, confidence_scores):
    dominant_class = pd.Series(predicted_labels).value_counts().index[0]
    dominant_pct = pd.Series(predicted_labels).value_counts(normalize=True).max() * 100
    uncertain_pct = (np.array(confidence_scores) < 0.50).mean() * 100
    return {
        "mean_confidence": float(np.mean(confidence_scores)),
        "uncertain_pct": float(uncertain_pct),
        "dominant_class": dominant_class,
        "dominant_pct": float(dominant_pct),
        "distribution_dominance_warning": dominant_pct > 95.0
    }
```

The `distribution_dominance_warning` flag feeds forward into the monitoring layer as a collapse signal. A session where one class accounts for 99% of windows is a signal of model failure, not of the subject genuinely doing the same thing for four hours straight.

---

## 13. Monitoring Layer

### Design principle

Monitoring is observational only. It reads inference outputs and writes a structured report. It does not decide whether to retrain. That decision belongs to the trigger policy.

### Three-layer structure

The monitoring layer is designed as three independent inspection layers, each looking at a different signal:

| Layer | What it checks | Metric | Threshold |
|---|---|---|---|
| L1 — Confidence | Are predictions certain? | Mean confidence | WARN < 0.70 |
| L1b — Collapse | Is one class dominating? | Dominant class % | WARN > 85%, CRITICAL > 95% |
| L2 — Temporal | Are predictions stable over time? | Flip/transition rate | WARN > 35% |
| L3 — Drift | Has distribution shifted from baseline? | z-score of mean shift | WARN > 1.8σ, CRITICAL > 3.0σ |

### `src/monitoring/post_inference_monitor.py`

```python
class PostInferenceMonitor:
    def __init__(self, config: PostInferenceMonitoringConfig, baseline: dict):
        self.config = config
        self.baseline = baseline   # pre-computed from training data

    def run(self, inference_artifact) -> MonitoringReport:
        df_pred = pd.DataFrame({
            "label": inference_artifact.predicted_labels,
            "confidence": inference_artifact.confidence_scores
        })

        layer1 = self._analyze_confidence(df_pred)
        layer2 = self._analyze_temporal(df_pred)
        layer3 = self._analyze_drift(df_pred)

        overall = self._aggregate_status([layer1, layer2, layer3])
        return MonitoringReport(
            layer1_confidence=layer1,
            layer2_temporal=layer2,
            layer3_drift=layer3,
            overall_status=overall
        )

    def _analyze_confidence(self, df):
        mean_conf = df["confidence"].mean()
        uncertain_pct = (df["confidence"] < self.config.per_window_uncertain_cutoff).mean() * 100
        dominant_pct = df["label"].value_counts(normalize=True).max() * 100
        dominant_class = df["label"].value_counts().index[0]

        alerts = []
        status = "HEALTHY"
        if mean_conf < self.config.confidence_warn_threshold:
            alerts.append(f"Low mean confidence: {mean_conf:.3f}")
            status = "WARNING"
        if dominant_pct >= self.config.dominant_class_critical_threshold:
            alerts.append(f"Prediction collapse: {dominant_class} at {dominant_pct:.1f}%")
            status = "CRITICAL"
        elif dominant_pct >= self.config.dominant_class_warn_threshold:
            alerts.append(f"Dominant class elevated: {dominant_class} at {dominant_pct:.1f}%")
            if status == "HEALTHY":
                status = "WARNING"

        return {
            "status": status,
            "mean_confidence": float(mean_conf),
            "uncertain_pct": float(uncertain_pct),
            "dominant_class": dominant_class,
            "dominant_pct": float(dominant_pct),
            "dominance_warning": dominant_pct >= self.config.dominant_class_warn_threshold,
            "dominance_critical": dominant_pct >= self.config.dominant_class_critical_threshold,
            "alerts": alerts
        }

    def _analyze_drift(self, df):
        # Compare current session confidence mean vs baseline
        current_mean = df["confidence"].mean()
        baseline_mean = self.baseline.get("mean_confidence", current_mean)
        baseline_std  = self.baseline.get("std_confidence", 0.1)
        zscore = (current_mean - baseline_mean) / (baseline_std + 1e-8)

        status = "HEALTHY"
        alerts = []
        if abs(zscore) >= self.config.drift_zscore_critical:
            status = "CRITICAL"
            alerts.append(f"Critical drift: z={zscore:.2f}")
        elif abs(zscore) >= self.config.drift_zscore_threshold:
            status = "WARNING"
            alerts.append(f"Drift warning: z={zscore:.2f}")

        return {
            "status": status,
            "drift_zscore": float(zscore),
            "current_mean": float(current_mean),
            "baseline_mean": float(baseline_mean),
            "alerts": alerts
        }
```

### Saving monitoring artifacts

Every monitoring run writes a `monitoring_report.json` to the run's artifact directory. This file is consumed by: the trigger policy engine, the CI test suite (for regression tests), the thesis chapters (as evidence of monitoring behavior), and dashboard visualizations.

Never rename the keys in this file once the thesis is written. The LaTeX chapters reference the key names by description if not by name — changing `layer1_confidence` to `confidence_layer` breaks the narrative.

---

## 14. Trigger Policy Layer

### Design principle

The trigger policy is the most important governance component. It answers: "given what monitoring saw, should we retrain?" The answer must be explainable, auditable, and conservative.

### 2-of-3 voting structure

Three independent signals vote:

```
Vote 1: confidence_layer status is WARNING or CRITICAL
Vote 2: temporal_layer status is WARNING or CRITICAL
Vote 3: drift_layer status is WARNING or CRITICAL
```

If 2 or more votes fire, the trigger escalates. This prevents any single noisy signal from forcing a retrain. It is the same principle as Byzantine fault tolerance in distributed systems — you need a quorum.

### `src/trigger_policy.py` — core decision logic

```python
class TriggerPolicyEngine:
    def __init__(self, config: TriggerEvaluationConfig):
        self.config = config

    def evaluate(self, monitoring_report: dict, last_retrain_time=None) -> TriggerDecision:
        votes = self._cast_votes(monitoring_report)
        n_votes = sum(votes.values())

        # Cooldown check — no retrain within 24h of last retrain
        in_cooldown = self._check_cooldown(last_retrain_time)

        # Collapse guard — route to REVIEW, not auto-retrain
        collapse_signal = monitoring_report.get("layer1_confidence", {}).get("dominance_critical", False)
        if collapse_signal:
            return TriggerDecision(action="REVIEW", reason="Prediction collapse detected", votes=votes)

        if n_votes >= self.config.required_votes_to_trigger:
            if in_cooldown:
                return TriggerDecision(action="QUEUE_RETRAIN", reason="Trigger voted but in cooldown", votes=votes)
            return TriggerDecision(action="TRIGGER_RETRAIN", reason=f"{n_votes}/3 signals exceeded threshold", votes=votes)

        if n_votes == 1:
            return TriggerDecision(action="MONITOR", reason="One signal elevated — continue monitoring", votes=votes)

        return TriggerDecision(action="NONE", reason="All signals healthy", votes=votes)

    def _cast_votes(self, report):
        return {
            "confidence_vote": report.get("layer1_confidence", {}).get("status") in ("WARNING", "CRITICAL"),
            "temporal_vote":   report.get("layer2_temporal", {}).get("status") in ("WARNING", "CRITICAL"),
            "drift_vote":      report.get("layer3_drift", {}).get("status") in ("WARNING", "CRITICAL"),
        }

    def _check_cooldown(self, last_retrain_time) -> bool:
        if last_retrain_time is None:
            return False
        hours_since = (datetime.now() - last_retrain_time).total_seconds() / 3600
        return hours_since < self.config.cooldown_hours
```

### Why separate drift visibility from retraining justification

Drift tells you something has changed. It does not tell you that retraining will help. A session with high confidence drift might be a different participant using the sensor correctly — retraining on their data might actually hurt the model on the original population. The trigger policy requires multiple signals to agree before escalating. Drift alone is a monitoring signal, not a retrain trigger.

This distinction is critical for the thesis. It separates an **observation** (drift detected) from an **action** (retrain model). Always frame them separately in writing.

---

## 15. Retraining Branch

### When retraining is allowed

Retraining only activates when all of the following are true:

1. The trigger policy returned `TRIGGER_RETRAIN` (not `MONITOR`, not `QUEUE_RETRAIN`)
2. The data file contains valid activity labels (detected in validation)
3. The labeled window count meets the minimum threshold (`min_labeled_windows = 100`)
4. The user explicitly invokes the retraining stages via `--stages retraining`

Auto-retraining on unlabeled production data is never the default. It must be opt-in.

### Candidate model training and comparison

```python
class ModelRetraining:
    def retrain_and_compare(self, X_new, y_new, baseline_model_path) -> RetrainingDecision:
        candidate = build_model()
        candidate.fit(X_new, y_new, ...)
        
        baseline = tf.keras.models.load_model(baseline_model_path)
        
        baseline_f1 = self._evaluate_f1(baseline, X_new, y_new)
        candidate_f1 = self._evaluate_f1(candidate, X_new, y_new)
        
        if candidate_f1 > baseline_f1 + 0.02:   # minimum improvement threshold
            return RetrainingDecision(accept=True, candidate=candidate, delta_f1=candidate_f1 - baseline_f1)
        return RetrainingDecision(accept=False, reason="Candidate did not improve baseline")
```

**Never promote a model that performs worse than the current baseline.** The minimum improvement threshold (here 0.02 F1) is an engineering choice — document it in `THRESHOLD_CITATIONS.md`.

### Domain adaptation as optional experiment, not core

AdaBN and TENT are implemented (`src/domain_adaptation/`) and wired through `adaptation_method` config. They are activated only when a user explicitly passes `--adapt adabn` or `--adapt tent`. They are optional experiments, not the defended production path. Frame them in the thesis as: "we implemented and evaluated these methods as Stage 8 extensions; the core governance contribution is the stage-based lifecycle, not the adaptation method choice."

---

## 16. Baseline Update and Model Registration

### Baseline update

The monitoring baseline is a statistical summary of what a healthy session looks like: mean confidence, std confidence, typical class distribution. When a retrained model is accepted, the baseline should be updated to reflect the new model's output distribution.

```python
class BaselineUpdate:
    def update_baseline(self, inference_artifact, new_baseline_path):
        stats = {
            "mean_confidence": float(np.mean(inference_artifact.confidence_scores)),
            "std_confidence":  float(np.std(inference_artifact.confidence_scores)),
            "class_distribution": pd.Series(inference_artifact.predicted_labels)
                                    .value_counts(normalize=True).to_dict(),
            "updated_at": datetime.now().isoformat()
        }
        json.dump(stats, open(new_baseline_path, "w"), indent=2)
```

### Model registration

Registration means making the candidate model the new default — copying it to `models/retrained/`, updating the `DEFAULT_MODEL_PATH` reference, and logging the change in MLflow.

```python
class ModelRegistration:
    def __init__(self, config: ModelRegistrationConfig):
        self.config = config   # auto_deploy defaults to False

    def register(self, candidate_model_path, metrics):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = BASELINE_DIR / f"har_model_{timestamp}.keras"
        shutil.copy(candidate_model_path, dest)
        # Log to MLflow
        mlflow.log_artifact(str(dest))
        mlflow.log_metrics(metrics)
        if self.config.auto_deploy:
            self._update_default_path(dest)   # only if explicitly enabled
```

**`auto_deploy=False` is the default.** The user must explicitly pass `--auto-deploy` to the CLI to promote a new model to the live default. This is a core governance claim of the thesis — deployment is opt-in, not automatic.

### Rollback

Keep the previous model path before overwriting. If a promoted model produces worse results on the next session, rolling back means pointing `DEFAULT_MODEL_PATH` back to the previous checkpoint.

---

## 17. API Layer

### What the API does

The FastAPI service exposes a local HTTP interface for submitting sensor data and receiving predictions. It does not orchestrate the full 11-stage CLI pipeline. It runs a shorter path: upload → optional merge/resample → unit conversion → normalization → windowing → inference → monitoring response.

This is an important scope distinction. State it clearly in the thesis: the API is a local inference and upload service, not a replacement for the governed CLI pipeline.

### `src/api/app.py` — essential endpoints

```python
from fastapi import FastAPI, File, UploadFile, HTTPException
from contextlib import asynccontextmanager
import tensorflow as tf

_model = None
_scaler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model, _scaler
    _model = tf.keras.models.load_model(str(DEFAULT_MODEL_PATH))
    _scaler = ZScoreNormalizer()
    _scaler.load(DEFAULT_SCALER_CONFIG)
    yield

app = FastAPI(lifespan=lifespan, title="HAR MLOps Inference API")

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model_loaded": _model is not None,
        "baseline_loaded": True
    }

@app.get("/api/model/info")
def model_info():
    return {
        "model_path": str(DEFAULT_MODEL_PATH),
        "output_classes": _model.output_shape[-1]
    }

@app.post("/api/upload")
async def upload(
    file: UploadFile = File(None),
    accelerometer_file: UploadFile = File(None),
    gyroscope_file: UploadFile = File(None)
):
    if file is not None:
        upload_mode = "fused_csv"
        df = _load_fused_upload(file)
    elif accelerometer_file is not None and gyroscope_file is not None:
        upload_mode = "accel_gyro_pair"
        df = _merge_pair_upload(accelerometer_file, gyroscope_file)
    else:
        raise HTTPException(status_code=400, detail="Provide either 'file' or both 'accelerometer_file' and 'gyroscope_file'")

    df = convert_units(df)
    windows = sliding_windows(df[SENSOR_COLUMNS].values, window_size=200, overlap=0.5)
    windows_norm = _scaler.transform(windows.reshape(-1, 6)).reshape(windows.shape)
    result = _run_inference_and_monitor(windows_norm)

    return {
        "upload_mode": upload_mode,
        "total_rows": len(df),
        "windows_created": len(windows),
        "has_labels": "activity_label" in df.columns,
        **result
    }
```

### What the API must NOT do

- It must not retrain the model from an upload — that path requires labels, governance approval, and CLI invocation
- It must not write permanent artifacts to the run database — it is a stateless service for quick inference
- It must not load a different model per request — the model is loaded once at startup

---

## 18. Docker and Deployment-Like Packaging

### Two images, two purposes

| Image | Purpose | Base | Size target |
|---|---|---|---|
| `har-inference` | Runs FastAPI API | python:3.10-slim | ~500 MB |
| `har-training`  | Runs retraining loops | python:3.10 | ~4 GB (TF + training deps) |

Keeping them separate means the inference container does not carry training-only dependencies (MLflow, matplotlib, seaborn, scikit-learn full, etc.). This is the most impactful Docker size optimization.

### `docker/Dockerfile.inference`

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements-inference.txt .
RUN pip install --no-cache-dir -r requirements-inference.txt

COPY src/ ./src/
COPY models/retrained/ ./models/retrained/
COPY data/prepared/config.json ./data/prepared/config.json

EXPOSE 8000

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `docker/Dockerfile.training`

```dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/
COPY run_pipeline.py .

CMD ["python", "run_pipeline.py", "--stages", "retraining", "registration"]
```

### Image size control

The biggest layer in the training image is always the pip install — typically 3+ GB due to TensorFlow. You cannot avoid this for training. For inference, you can reduce it significantly by:

1. Using `requirements-inference.txt` instead of `requirements.txt`
2. Using `python:3.10-slim` instead of `python:3.10`
3. Using `--no-cache-dir` in pip install

Target: inference image under 1 GB, training image accepted at 4 GB.

### `docker-compose.yml`

```yaml
version: "3.9"
services:
  inference:
    build:
      context: .
      dockerfile: docker/Dockerfile.inference
    image: har-inference:latest
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models:ro
    environment:
      - PYTHONUNBUFFERED=1

  training:
    build:
      context: .
      dockerfile: docker/Dockerfile.training
    image: har-training:latest
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./artifacts:/app/artifacts
```

### What to test manually

After building both images:
1. `docker run --rm -p 8000:8000 har-inference:latest` → open `localhost:8000/docs`
2. Submit a fused CSV to `/api/upload` and verify HTTP 200
3. Check `/api/health` returns `model_loaded: true`
4. Check `/api/model/info` returns the correct class count

---

## 19. Testing Strategy

### Test alongside each layer, not at the end

The biggest testing mistake in a thesis project is writing all tests after the code is done. By that point, the code has no clear input/output contracts and tests become structural rather than functional. Build each test as you build each component.

### Test pyramid for this project

```
Unit tests (fast, isolated)
  - test each config dataclass default values
  - test normalizer fit/transform/save/load round-trip
  - test sliding window shape
  - test unit conversion heuristic
  - test label map lookup

Component tests (per-stage)
  - test data validation correctly flags missing columns
  - test monitoring layer emits WARN at 85% dominance
  - test monitoring layer emits CRITICAL at 95% dominance
  - test trigger 2-of-3 voting logic
  - test cooldown prevents immediate re-trigger

Integration tests (multi-stage, slower)
  - test stages 1-7 complete on synthetic data
  - test monitoring report keys are present after pipeline run
  - test trigger report keys are present after pipeline run

API smoke tests
  - test POST /api/upload with fused CSV returns 200
  - test POST /api/upload with raw pair returns 200
  - test POST /api/upload with missing files returns 400

Threshold consistency tests
  - assert Stage 6 confidence warn (0.70) <= Stage 7 confidence warn (0.65) is false — they are intentionally different
  - assert Stage 6 drift warn (1.8) < Stage 7 drift warn (2.0) — Stage 6 is earlier
```

### `tests/conftest.py` — shared fixtures

```python
import pytest
import numpy as np

@pytest.fixture
def synthetic_windows():
    return np.random.rand(50, 200, 6).astype(np.float32)

@pytest.fixture
def healthy_monitoring_report():
    return {
        "layer1_confidence": {"status": "HEALTHY", "mean_confidence": 0.88, "dominant_pct": 40.0, "dominance_critical": False},
        "layer2_temporal": {"status": "HEALTHY"},
        "layer3_drift": {"status": "HEALTHY", "drift_zscore": 0.5}
    }

@pytest.fixture
def two_vote_monitoring_report():
    return {
        "layer1_confidence": {"status": "WARNING", "mean_confidence": 0.61, "dominant_pct": 40.0, "dominance_critical": False},
        "layer2_temporal": {"status": "WARNING"},
        "layer3_drift": {"status": "HEALTHY", "drift_zscore": 0.5}
    }
```

### Running tests

```bash
pytest tests/ -q --tb=short                    # full suite
pytest tests/ -m "not slow" -q                  # skip integration tests
pytest tests/test_trigger_policy.py -v          # specific component
pytest --cov=src --cov-report=term-missing      # with coverage
```

---

## 20. Experiment and Ablation Scripts

### Principle: separate one-off experiments from core runtime code

The `src/` directory contains the production pipeline. The `scripts/` directory contains anything you run once or occasionally for a research question. Never import from `scripts/` inside `src/`.

### What belongs in `scripts/`

- `scripts/compare_models_26sessions.py` — runs inference with two models on 26 sessions, produces comparison CSV and charts
- `scripts/batch_inference_all_sessions.py` — runs all sessions through the pipeline and aggregates results
- `scripts/preprocessing_ablation.py` — sweeps over normalization variants (none, zscore, minmax) and records accuracy

### Experiment output format

Every experiment script should produce:
1. A summary CSV in `outputs/<experiment_name>/results.csv`
2. A markdown summary in `outputs/<experiment_name>/summary.md`
3. Charts in `outputs/<experiment_name>/charts/`

The CSV becomes a thesis table. The charts become thesis figures. The markdown becomes evidence for the worklog.

### Example ablation structure

```python
# scripts/preprocessing_ablation.py

VARIANTS = {
    "zscore":  {"normalization": "zscore"},
    "minmax":  {"normalization": "minmax"},
    "none":    {"normalization": "none"},
}

results = []
for name, config_override in VARIANTS.items():
    config = DataTransformationConfig(**config_override)
    X, y = preprocess_with_config(config, DATA_PATH)
    model = tf.keras.models.load_model(DEFAULT_MODEL_PATH)
    predictions = model.predict(X)
    f1 = f1_score(y, predictions.argmax(1), average="macro")
    results.append({"variant": name, "macro_f1": f1})

pd.DataFrame(results).to_csv("outputs/preprocessing_ablation/results.csv", index=False)
```

---

## 21. Artifact and Evidence Design

### Artifacts are your thesis evidence

Every run of the pipeline should produce a time-stamped folder under `artifacts/<run_id>/` containing JSON files at each stage. These files are:
- Proof that the pipeline ran
- Input to the next stage
- Source material for thesis tables and figures
- Regression fixtures for tests

### What to always save

| Stage | Artifact file | Key fields |
|---|---|---|
| Ingestion | `ingestion_artifact.json` | `fused_csv_path`, `total_rows`, `has_labels` |
| Validation | `validation_report.json` | `validation_status`, `errors`, `row_count` |
| Transformation | `transformation_artifact.json` | `n_windows`, `window_shape`, `normalization_applied` |
| Inference | `inference_artifact.json` | `predicted_labels`, `confidence_scores`, `model_path` |
| Evaluation | `evaluation_summary.json` | `accuracy`, `macro_f1`, `mean_confidence`, `dominant_pct` |
| Monitoring | `monitoring_report.json` | `layer1_confidence`, `layer2_temporal`, `layer3_drift`, `overall_status` |
| Trigger | `trigger_report.json` | `action`, `votes`, `reason`, `cooldown_remaining` |

### Artifact manager

```python
import json
from pathlib import Path
from datetime import datetime

class ArtifactsManager:
    def __init__(self, artifacts_dir: Path):
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = artifacts_dir / self.run_id

    def save(self, stage_name: str, data: dict):
        stage_dir = self.run_dir / stage_name
        stage_dir.mkdir(parents=True, exist_ok=True)
        path = stage_dir / f"{stage_name}_report.json"
        json.dump(data, open(path, "w"), indent=2)
        return path
```

---

## 22. Thesis-Writing Integration

### How code artifacts map to thesis chapters

**Chapter 4 — Data and Model Development**
- Evidence from: `data/prepared/config.json` (label mapping, window counts), training history JSON (accuracy/loss curves), confusion matrix from labeled evaluation
- Claims supported: dataset composition (n sessions, n windows, n classes), model architecture choice, cross-validation methodology, baseline accuracy and F1

**Chapter 5 — Pipeline Implementation**
- Evidence from: `run_pipeline.py --help` output (stage names, flags), CI workflow YAML (automated checks), Docker build commands (containerization)
- Claims supported: 11-stage architecture, CLI design, CI automation scope, opt-in deployment governance

**Chapter 6 — Monitoring, Drift, and Trigger Governance**
- Evidence from: `monitoring_report.json` from representative runs, `THRESHOLD_CITATIONS.md` (numerical justifications), `config_entity.py` (actual defaults)
- Claims supported: 3-layer monitoring structure, 2-of-3 trigger voting, threshold calibration rationale, collapse guard behavior

**Chapter 7 — Experiments and Evaluation**
- Evidence from: `outputs/charts_26runs/` (comparison charts), `outputs/experiments/*/before_vs_after_26datasets.csv` (per-session table), ablation CSVs
- Claims supported: 26-session model comparison, confidence behavior, trigger decision distribution, pseudo-label vs raw model comparison

**Chapter 8 — Discussion and Future Work**
- Evidence from: `trigger_report.json` decisions, monitoring status distributions, current threshold settings
- Claims supported: governance limitations, threshold calibration gap as known limitation, future OOD detection and cloud scaling as out-of-scope

### How to write numbers in the thesis

Every number in the thesis must trace to:
1. A code default in `config_entity.py`, OR
2. A measurement from an artifact JSON, OR
3. A citation in `references.bib`

If a number exists only in the thesis text with no code or artifact backing, it is an unsupported claim. A reviewer will find it. Before submission, read `THRESHOLD_CITATIONS.md` against the actual config defaults and close any gaps.

---

## 23. Common Mistakes and How to Avoid Them

### 1. Train/serve mismatch

**Mistake:** Normalizing training data with a fresh `StandardScaler().fit_transform(X_train)` and then at inference time fitting a new scaler on production data.

**Effect:** The model receives values on a completely different scale. Predictions are confidently wrong.

**Fix:** Save scaler parameters at training time. Load and apply them at inference time. Never refit.

### 2. Wrong model loaded by default

**Mistake:** `DEFAULT_MODEL_PATH` points to a timestamp-named file that has been moved, deleted, or never existed in the Docker image.

**Effect:** Every inference call fails with `FileNotFoundError`, often silently swallowed as a 500 error.

**Fix:** Implement a fallback chain: pinned default → latest retrained → pretrained base. Check existence at startup and log loudly.

### 3. Claiming thresholds without backing

**Mistake:** Writing "the confidence warn threshold is 0.70 because it represents the deployment-safe operating range" without a citation or experiment backing that number.

**Effect:** A reviewer asks "why 0.70 and not 0.65?" and the thesis has no answer.

**Fix:** Every threshold in the thesis must appear in `THRESHOLD_CITATIONS.md` with a rationale (citation, empirical result, or SPC convention). Stage 6 and Stage 7 thresholds must be listed separately.

### 4. Overclaiming drift as retraining justification

**Mistake:** "Drift was detected, therefore we retrained the model."

**Effect:** Conflates an observation with a decision. Drift in one signal does not prove retraining will help. The thesis makes a governance claim, not an automatic-trigger claim.

**Fix:** Always write: "drift was detected by Stage 6 monitoring. The Stage 7 trigger policy required N-of-3 signals before escalating. In this run, [N] signals voted, resulting in action [X]."

### 5. Mixing runtime and experiment logic

**Mistake:** Importing from `scripts/compare_models_26sessions.py` inside `src/pipeline/production_pipeline.py`.

**Effect:** Experiment code that was never reviewed is silently part of the production pipeline. Breaking the experiment script breaks the pipeline.

**Fix:** `src/` is one-way. It never imports from `scripts/`. Experiments import from `src/`.

### 6. Using unverified citations

**Mistake:** Citing `gama2014drift` for the 2σ drift threshold, but `gama2014drift` is not about z-score SPC thresholds — it is about concept drift detection frameworks.

**Effect:** A reviewer checks the citation and finds it does not support the claim.

**Fix:** Shewhart (1931) and Montgomery (2009) are the canonical citations for 2σ/3σ SPC thresholds. Use them.

### 7. Confusing the API path with the full CLI pipeline

**Mistake:** Claiming in the thesis that "the FastAPI endpoint runs the full 11-stage pipeline."

**Effect:** A reviewer checks `src/api/app.py` and finds it calls `model.predict()` directly, not `ProductionPipeline.run()`.

**Fix:** The thesis should clearly state: "The FastAPI service runs an inference-only subset of the pipeline (upload → preprocessing → inference → monitoring response). The full 11-stage governance pipeline is CLI-only."

### 8. Auto-deploying without governance

**Mistake:** Setting `auto_deploy=True` as the default in `ModelRegistrationConfig`.

**Effect:** Every accepted retrain automatically becomes the live model. No human review. This contradicts the thesis governance claims.

**Fix:** `auto_deploy=False` is the permanent default. Deployment requires an explicit `--auto-deploy` flag.

---

## 24. If I Had to Rebuild It Today

### What I would code first

1. `src/config.py` — paths and constants, five minutes
2. `src/entity/config_entity.py` — all stage dataclasses, one hour
3. `src/entity/artifact_entity.py` — all output contracts, one hour
4. `src/preprocess_data.py` — normalizer and windowing, two hours
5. `src/train.py` — model definition and training loop, three hours
6. Tests for normalizer and windowing — thirty minutes alongside

### What I would postpone

- AdaBN and TENT — implement after the baseline pipeline is stable and tested
- Docker — containerize only after the local pipeline runs end-to-end cleanly
- FastAPI — implement after CLI inference works; the API is a thin wrapper
- Experiment scripts — write alongside each experiment, not upfront
- The full thesis LaTeX — write chapter by chapter as each system layer produces evidence

### What I would simplify

- The `sys.path` mutation pattern — I would use `setup.py` with `pip install -e .` from day one so all imports work without path hacks
- The standalone module + component duplication — I would put logic only in components and make standalone scripts thin wrappers that import from components
- The multiple `Path(__file__).parent.parent` computations in different files — import from `src/config.py` every time

### What I would keep identical

- The 2-of-3 trigger voting structure — it is explainable and defensible
- The `Stage 6 warns earlier / Stage 7 votes for action` tiering — this is the core governance narrative
- The `auto_deploy=False` and `promote_to_shared=False` defaults — every governance claim rests on these
- The separate `requirements.txt` and `requirements-inference.txt` — critical for Docker size

### What I would do differently

- Add a schema freeze test for `monitoring_report.json` and `trigger_report.json` on day one — before the first thesis chapter is written
- Name the drift metric key `drift_zscore` from the start, not `psi`
- Write `THRESHOLD_CITATIONS.md` alongside each threshold definition in `config_entity.py`, not as a post-hoc documentation task

---

## 25. Final Checklist

Use this before thesis submission.

### Environment
- [ ] `thesis-mlops` conda environment documented and reproducible from `requirements.txt`
- [ ] `requirements-inference.txt` is a strict subset of `requirements.txt`
- [ ] `pip install -e .` installs `har-pipeline` CLI correctly

### Configuration
- [ ] All operational thresholds are in `config_entity.py` dataclass fields, not hardcoded in logic
- [ ] Stage 6 and Stage 7 thresholds are in separate dataclasses with separate names
- [ ] `THRESHOLD_CITATIONS.md` rows reference the correct `config_entity.py` line numbers
- [ ] Every threshold in the thesis text has a row in `THRESHOLD_CITATIONS.md`

### Data
- [ ] Raw data is in `data/raw/` and never modified in place
- [ ] `data/prepared/config.json` contains the label map used at training time
- [ ] The same label map is loaded at inference time
- [ ] Scaler parameters saved in `models/retrained/scaler_config.json`

### Preprocessing
- [ ] Normalizer fit on training data, saved, loaded at inference — not refit
- [ ] Window size (200), overlap (0.5), and channel order identical at train and serve time
- [ ] Unit conversion applied before normalization, consistently

### Model
- [ ] Baseline model saved in `.keras` format with timestamp in filename
- [ ] Training history saved as JSON artifact
- [ ] Model architecture defined once in `src/train.py`, not duplicated elsewhere

### Inference
- [ ] Inference loads scaler from `scaler_config.json`, does not refit
- [ ] Label mapping loaded from `data/prepared/config.json`
- [ ] `DEFAULT_MODEL_PATH` points to an existing file

### Monitoring
- [ ] Monitoring runs on every inference, even for unlabeled data
- [ ] `monitoring_report.json` contains `layer1_confidence`, `layer2_temporal`, `layer3_drift`, `overall_status`
- [ ] Dominant class percentage and collapse flags are in `layer1_confidence`
- [ ] Drift metric key is `drift_zscore`, not `psi`

### Trigger policy
- [ ] 2-of-3 voting logic tested with unit tests
- [ ] Cooldown logic prevents re-trigger within 24h
- [ ] Collapse guard routes to `REVIEW`, not `TRIGGER_RETRAIN`
- [ ] `trigger_report.json` contains `action`, `votes`, `reason`

### Retraining
- [ ] Retraining only activates with labeled data and explicit CLI flag
- [ ] Candidate model compared against baseline before promotion
- [ ] `auto_deploy=False` is the default and unchanged
- [ ] Rollback mechanism documented and testable

### API
- [ ] `/api/health` returns `model_loaded: true`
- [ ] `/api/upload` accepts fused CSV and raw pair
- [ ] API does not retrain from uploads
- [ ] API uses the same scaler and label map as the CLI pipeline

### Docker
- [ ] Inference image builds from `requirements-inference.txt`
- [ ] Training image builds from `requirements.txt`
- [ ] Both images smoke-tested after build
- [ ] Model file and scaler config are inside the inference image

### Tests
- [ ] `pytest tests/ -q` passes with 0 failures
- [ ] Test for dominant-class WARN at 85% dominance
- [ ] Test for dominant-class CRITICAL at 95% dominance
- [ ] Test for 2-of-3 trigger voting
- [ ] Test for API upload modes
- [ ] Test for Stage 6 warn threshold ≤ Stage 7 trigger threshold for each metric

### Evidence and artifacts
- [ ] `reports/api_operational_smoke_*.md` documents API smoke with HTTP 200 responses
- [ ] 26-session experiment charts are in `outputs/charts_26runs/`
- [ ] `thesis/tables/before_vs_after_26datasets.csv` exists and is referenced in Ch7
- [ ] `thesis/main.pdf` builds cleanly from `thesis/main.tex`
- [ ] `thesis/main.log` contains no undefined citation warnings
- [ ] `references.bib` contains all citations referenced in `.tex` files

### Thesis chapter mapping
- [ ] Chapter 4 evidence: label map, training history, confusion matrix
- [ ] Chapter 5 evidence: CLI --help output, CI YAML, Docker build commands
- [ ] Chapter 6 evidence: monitoring_report JSON example, THRESHOLD_CITATIONS.md
- [ ] Chapter 7 evidence: 26-session comparison CSV and charts
- [ ] Chapter 8 evidence: trigger_report decisions, monitoring status distributions

---

*End of guide. This document describes the system as actually built and defended, not an idealized version. Every design decision recorded here has a reason — and most of the reasons were learned by getting it wrong first.*

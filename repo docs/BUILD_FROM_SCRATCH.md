# Build This Project From Scratch — Step-by-Step

> **What this is:** A recipe. Every step is an action. Every "why" is one sentence.
> Read `PROJECT_DEEP_DIVE.md` for the full explanation behind each decision.

---

## The Big Picture — 11 Phases

You are going to build the system in this order. Each phase produces something the next one needs.

```
 Phase 0  Prereqs        install the tools
    │
 Phase 1  Skeleton       git + folders + venv + DVC
    │
 Phase 2  Config         pipeline_config.yaml (the control panel)
    │
 Phase 3  Data           track raw sensor files with DVC
    │
 Phase 4  Training  ─────────────────▶ produces the RUNTIME CONTRACT
    │                                   (model + scaler + baseline + labels)
    │                                          │
 Phase 5  Pipeline  ◀──────── needs ──────────┘
    │     (the 7 stages — the heart of the project)
    │
    ├──▶ Phase 6  MLflow      log every run        ┐
    ├──▶ Phase 7  WebUI       FastAPI dashboard    │  these four are
    ├──▶ Phase 8  Docker      package it           │  independent —
    └──▶ Phase 9  Tests       pytest + contract    ┘  build in any order
    │
 Phase 10 Thesis         write it up in LaTeX
    │
 Phase 11 Submission     squash → tag → ship
```

### Rough effort guide

| Phase | What you're doing | Relative effort | You'll know it works when… |
|---|---|:---:|---|
| 0 | Install tools | ▰▱▱▱▱ | `python --version` ≥ 3.10 |
| 1 | Project skeleton | ▰▰▱▱▱ | `pip install -e .` succeeds |
| 2 | Config file | ▰▱▱▱▱ | YAML loads without error |
| 3 | Track data | ▰▰▱▱▱ | `dvc status` is clean |
| 4 | **Train model** | ▰▰▰▰▰ | contract folder has 5 files |
| 5 | **7-stage pipeline** | ▰▰▰▰▰ | `run_pipeline.py` → SUCCESS |
| 6 | MLflow | ▰▰▱▱▱ | runs appear in `mlflow ui` |
| 7 | WebUI | ▰▰▰▱▱ | upload works in browser |
| 8 | Docker | ▰▰▱▱▱ | container serves on :8000 |
| 9 | Tests | ▰▰▱▱▱ | `pytest` all green |
| 10 | Thesis | ▰▰▰▱▱ | PDF builds, 0 errors |
| 11 | Submission | ▰▱▱▱▱ | tag pushed |

> 🎯 **The two phases that matter most are 4 (training) and 5 (pipeline).** Everything else supports them. If you're short on time, get these two rock-solid first.

---

## Phase −1 — Think Before You Code (Design First)

> The single biggest mistake is opening a notebook and starting to train. Spend a day in this phase; it saves a month later. **None of these steps involve writing pipeline code** — they are the decisions that make the code writable.

### Step −1.1 — Write your thesis statement in ONE sentence

Before any code, complete this template:

> *"I claim that **\_\_\_**, and I will demonstrate it by **\_\_\_**."*

Ours became:

> *"I claim that a HAR model good in-distribution fails silently on unseen users, and I will demonstrate it by building an MLOps pipeline with label-free monitoring and governance that detects and manages that failure."*

**Why:** every file, figure, and experiment must serve this sentence. When you're unsure whether to build something, ask "does it serve the claim?" If no, cut it. This sentence also becomes your abstract and your defense opener.

### Step −1.2 — Choose your architecture shape, and reject the alternatives on purpose

For each fork, write down the choice **and why not the others.** This *is* your "Design" chapter.

| Fork | Your choice | Why not the alternative |
|---|---|---|
| Batch or streaming? | Batch | Research is about lifecycle, not latency |
| Notebook, monolith, or modular? | Modular | Testable, reproducible, auditable |
| Local or cloud? | Local | Reproducible on examiner's laptop, no bills |
| Auto-retrain or human-gated? | Human-gated | Safety in a health domain |

**Why:** examiners probe *why not X?* far more than *what is X?* Deciding deliberately (not by accident) is the difference between engineering and research. (The full catalog of 14 such decisions is in `PROJECT_DEEP_DIVE.md` → "Design Decisions.")

### Step −1.3 — Adopt the modular template (the 4 building blocks)

Every stage you will ever write follows this shape:

```
   CONFIG  ──▶  COMPONENT  ──▶  ARTIFACT          (ORCHESTRATOR runs them in order)
   the "what"   the "how"      the "result"
   settings     one job        typed output
```

| Block | Job | Rule |
|---|---|---|
| **Config** | holds settings (paths, thresholds) | data only, no logic |
| **Component** | does the work of ONE stage | logic only, one responsibility |
| **Artifact** | carries the stage's output | typed data only, no logic |
| **Orchestrator** | decides the order | flow only, no stage logic |

**Why:** committing to this pattern *before* coding means every stage looks the same, every stage is testable in isolation, and any stage can be swapped without breaking the others.

### Step −1.4 — Lock your conventions before writing a line

Decide these once, follow them everywhere:

| Convention | Rule |
|---|---|
| File names | `snake_case.py`, one stage per file in `components/` |
| Class names | `PascalCase`: `DataTransformation` |
| Method names | `initiate_<stage>()`: `initiate_data_transformation()` |
| Config/Artifact names | `<Stage>Config`, `<Stage>Artifact` |
| Constants | never hardcoded — always in `config/pipeline_config.yaml` |
| Tests | every component gets `tests/test_<stage>.py` |

**Why:** conventions decided once cost nothing; conventions decided ad-hoc create an inconsistent codebase you fight for months and can't explain in a defense.

### Step −1.5 — Sketch the end-to-end data contract (shapes at every boundary)

Draw what the data looks like as it crosses each stage. This lets you build stages independently and still have them fit:

```
 raw CSVs           fused CSV        windows           predictions       decision
 ┌────────┐         ┌────────┐       ┌──────────┐      ┌──────────┐      ┌────────┐
 │accel.csv│        │ 50 Hz   │       │[N,200,6] │      │class+conf│      │NO_ACTION│
 │gyro.csv │ ──S1──▶│ merged  │─S2/3─▶│ .npy     │─S4──▶│ per win  │─S5/6/7▶│…RETRAIN│
 └────────┘         └────────┘       └──────────┘      └──────────┘      └────────┘
   strings           DataFrame        np.ndarray        np.ndarray        enum/string
```

**Why:** once you know the *shape* at each boundary, two people can build Stage 1 and Stage 4 on the same day without talking — the artifact contract is the agreement between them.

> ✅ **Checkpoint:** before Phase 0, you should have: a one-sentence thesis claim, a filled-in decision table, the 4-block pattern memorized, your conventions written down, and a data-contract sketch. *Now* you may install tools.

---

## Phase 0 — Prerequisites

Before you write a single line of code, install these on your machine:

| Tool | Version | Why |
|---|---|---|
| Python | 3.10+ | TensorFlow 2.14 requires ≥ 3.10 |
| Git | any | version control |
| DVC | 3.50+ | data + model versioning |
| Docker Desktop | any | containerized deployment |
| LaTeX (MiKTeX / TexLive) | any | thesis PDF compilation |
| VS Code or PyCharm | any | IDE |

---

## Phase 1 — Project Skeleton

### Step 1.1 — Create the git repo
```bash
mkdir har-mlops-pipeline
cd har-mlops-pipeline
git init
```
**Why:** Everything starts with git. DVC and MLflow both rely on git being initialized.

---

### Step 1.2 — Create the folder structure
```
mkdir src src/components src/pipeline src/api src/monitoring
mkdir config models/runtime_contract docker tests notebooks docs scripts thesis
```
**Why:** One folder per concern. `src/components/` maps one-to-one with pipeline stages. Nothing bleeds into each other.

---

### Step 1.3 — Create `pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68.0", "wheel>=0.41"]
build-backend = "setuptools.build_meta"

[project]
name = "har-mlops-pipeline"
version = "1.0.0"
requires-python = ">=3.10"
dynamic = ["dependencies"]

[tool.setuptools]
packages = {find = {include = ["src*"]}}

[tool.setuptools.dynamic]
dependencies = {file = "config/requirements.txt"}

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --strict-markers -ra"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
filterwarnings = ["ignore::DeprecationWarning"]
```
**Why:** Lets you do `pip install -e .` so all `src.*` imports work everywhere without path hacks.

---

### Step 1.4 — Create `config/requirements.txt`
```
numpy>=1.24
pandas>=2.0
scipy>=1.10
tensorflow-cpu>=2.14
scikit-learn>=1.3
mlflow>=2.11
dvc>=3.50
fastapi>=0.109
uvicorn[standard]>=0.27
pydantic>=2.5
python-multipart>=0.0.6
matplotlib>=3.8
seaborn>=0.13
pyyaml>=6.0.1
pytest>=8.0
pytest-cov>=4.1
flake8>=7.0
black>=24.1
mypy>=1.8
```
**Why:** Single source of truth for all dependencies. `pyproject.toml` reads from this file.

---

### Step 1.5 — Create the virtual environment and install
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -e .
```
**Why:** `-e` (editable install) means changes to `src/` are live without reinstalling.

---

### Step 1.6 — Initialize DVC
```bash
dvc init
git add .dvc .dvcignore
git commit -m "init: project skeleton with DVC"
```
**Why:** DVC creates a `.dvc/` folder that tracks your data cache. Commit this so collaborators get the same DVC setup on clone.

---

### Step 1.7 — Create `.gitignore`
```
venv/
__pycache__/
*.pyc
mlruns/
artifacts/
*.npy
*.csv
*.keras
*.h5
.dvc/cache
```
**Why:** Keep the repo clean. Data, model weights, and run artifacts are tracked by DVC/MLflow — not git.

---

## Phase 2 — Configuration

### Step 2.1 — Create `config/pipeline_config.yaml`
```yaml
data:
  accel_path: "data/raw/accel.csv"
  gyro_path: "data/raw/gyro.csv"
  output_path: "artifacts/"

transformation:
  window_size: 200        # samples — 4 seconds at 50 Hz
  stride: 100             # samples — 50% overlap, 2-second cadence
  sampling_rate: 50       # Hz

model:
  contract_dir: "models/runtime_contract/model_d1_final/"
  model_filename: "model_d1.keras"
  scaler_filename: "garmin_train_scaler.json"
  label_order_filename: "label_order.json"

monitoring:
  baseline_path: "models/runtime_contract/model_d1_final/raw_physical_baseline.json"
  confidence_threshold: 0.70
  temporal_threshold: 0.30
  drift_z_threshold: 2.0
  smoothing_k: 3

governance:
  should_retrain: false    # NEVER auto-retrain
```
**Why:** All thresholds and paths in one file. Change a threshold here — it propagates everywhere. No magic numbers in code.

---

### Step 2.2 — Create the config loader (`src/pipeline/pipeline_config_factory.py`)

Write a class that reads `pipeline_config.yaml` and exposes typed config objects for each stage.

```python
import yaml
from pathlib import Path
from dataclasses import dataclass

@dataclass
class TransformationConfig:
    window_size: int
    stride: int
    sampling_rate: int

def load_config(path="config/pipeline_config.yaml"):
    with open(path) as f:
        raw = yaml.safe_load(f)
    return raw
```
**Why:** Type-safe config objects catch wrong field names at import time, not at runtime.

---

## Phase 3 — Data Preparation

### Step 3.1 — Track raw data with DVC
```bash
dvc add data/raw/accel.csv
dvc add data/raw/gyro.csv
git add data/raw/accel.csv.dvc data/raw/gyro.csv.dvc
git commit -m "data: track raw sensor files with DVC"
```
**Why:** Raw data never goes in git. DVC creates tiny pointer files that git tracks instead.

---

### Step 3.2 — Understand your data

Open a notebook and inspect the CSV:
```python
import pandas as pd
df = pd.read_csv("data/raw/accel.csv")
print(df.columns)   # expect: timestamp, x, y, z, label (optional)
print(df.head())
print(df["timestamp"].diff().describe())  # verify 50 Hz = 20ms between rows
```
**Why:** Garbage in = garbage out. Verify sampling rate and column names before building the pipeline.

---

## Phase 4 — Model Training (offline, in a notebook)

### Step 4.1 — Fuse and window the training data
```python
import numpy as np

WINDOW = 200   # 4 seconds at 50 Hz
STRIDE = 100   # 50% overlap

def make_windows(X, y, window=WINDOW, stride=STRIDE):
    windows, labels = [], []
    for i in range(0, len(X) - window, stride):
        windows.append(X[i:i+window])
        labels.append(y[i+window//2])   # label from the center of the window
    return np.array(windows), np.array(labels)

X_windows, y_windows = make_windows(sensor_data, labels)
# X_windows shape: [n_windows, 200, 6]
```

What the loop does, visually:

```
 sensor_data (thousands of rows)
 ┌──────────────────────────────────────────────────────────▶
 │
 │ i=0    [████ 200 rows ████]                  → window 0, label = row 100
 │ i=100         [████ 200 rows ████]           → window 1, label = row 200
 │ i=200                [████ 200 rows ████]     → window 2, label = row 300
 │               ◀─stride 100─▶
 │
 │ result: X_windows = [n_windows, 200, 6]   (a stack of fixed blocks)
```

**Why:** The model needs fixed-size inputs. 200 samples × 6 features. Label from window center avoids boundary ambiguity.

---

### Step 4.2 — Decide your input space (we use unit conversion + a z-score scaler)

**The decision that matters most here:** does the model consume *raw physical units* or *z-score-scaled* values? The deployed Model D1 uses **both steps in order**: milliG → m/s² (unit conversion), **then** a z-score `StandardScaler` fit on **training users only**. (The *paper baseline* used no scaler — that's a different, A/B configuration; the deployed contract adds the scaler.)

Fit the scaler on TRAIN only and save it to JSON — it becomes part of the runtime contract:

```python
from sklearn.preprocessing import StandardScaler
import json

scaler = StandardScaler()
scaler.fit(X_train_windows.reshape(-1, 6))   # fit on TRAIN users only (never on test/inference)

scaler_data = {
    "scaler_mean": scaler.mean_.tolist(),
    "scaler_scale": scaler.scale_.tolist(),
    "normalization_variant": "zscore",
    "fit_rule": "Apply after unit conversion to m/s^2. Never fit on inference data.",
}
with open("models/runtime_contract/model_d1_final/garmin_train_scaler.json", "w") as f:
    json.dump(scaler_data, f, indent=2)
```
**Why JSON not pickle:** JSON is human-readable and version-stable. Pickle breaks across sklearn versions.
**The parity rule:** whatever space you train in, inference must match exactly. Train on scaled windows → scale at inference too (Stage 3 + the WebUI both do). Fit once on train, *load* everywhere else.

---

### Step 4.3 — Build and train the 1DCNNBiLSTM
```python
from tensorflow import keras
from tensorflow.keras import layers

def build_model(window=200, features=6, classes=11):
    inp = keras.Input(shape=(window, features))
    x = layers.Conv1D(64, 3, activation='relu', padding='same')(inp)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Bidirectional(layers.LSTM(64))(x)
    x = layers.Dense(64, activation='relu')(x)
    out = layers.Dense(classes, activation='softmax')(x)
    return keras.Model(inp, out)

model = build_model()
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_val, y_val))
```
**Why 1D CNN + BiLSTM:** CNN extracts local patterns (one step, one gesture). BiLSTM sees the sequence in both directions for long-range context. Together they outperform either alone on wrist HAR.

---

### Step 4.4 — Evaluate with 5-fold CV and LOUO
```python
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score

# 5-fold CV — measures in-distribution performance
kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for train_idx, val_idx in kfold.split(X_windows, y_windows):
    # train and evaluate...
    pass

# LOUO — measures cross-person generalization
# Train on users 1-6, test on user 7
X_train_louo = data_from_users([1,2,3,4,5,6])
X_test_louo = data_from_user(7)
# train, evaluate...
```
**Why both?** 5-fold shows in-distribution capability. LOUO shows the personalization gap — the real-world problem this MLOps pipeline addresses.

---

### Step 4.5 — Save everything to the runtime contract folder
```python
import hashlib, json
from pathlib import Path

CONTRACT = Path("models/runtime_contract/model_d1_final/")
CONTRACT.mkdir(parents=True, exist_ok=True)

# Save model
model.save(CONTRACT / "model_d1.keras")

# Save label order
label_order = {
    0: "ear_rubbing", 1: "forehead_rubbing", 2: "hair_pulling", 3: "hand_scratching",
    4: "hand_tapping", 5: "knuckles_cracking", 6: "nail_biting", 7: "nape_rubbing",
    8: "sitting", 9: "smoking", 10: "standing",
}
with open(CONTRACT / "label_order.json", "w") as f:
    json.dump(label_order, f)

# Save monitoring baseline (training distribution)
baseline = {
    "mean": sensor_data.mean(axis=0).tolist(),
    "std": sensor_data.std(axis=0).tolist()
}
with open(CONTRACT / "raw_physical_baseline.json", "w") as f:
    json.dump(baseline, f)

# Compute and save MD5s
def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()

checksums = {
    "model_d1.keras": md5(CONTRACT / "model_d1.keras"),
    "garmin_train_scaler.json": md5(CONTRACT / "garmin_train_scaler.json"),
    "raw_physical_baseline.json": md5(CONTRACT / "raw_physical_baseline.json"),
    "label_order.json": md5(CONTRACT / "label_order.json"),
}
with open(CONTRACT / "artifact_md5.json", "w") as f:
    json.dump(checksums, f, indent=2)
```
**Why MD5s?** The pipeline checks these at startup. If anyone accidentally overwrites a file, the pipeline fails loudly instead of silently serving wrong predictions.

---

## Phase 5 — The 7-Stage Pipeline

For each stage, the pattern is the same — learn it once, repeat 7 times:

```
   Previous stage's Artifact ──┐
                               ▼
   ┌─────────────────────────────────────────┐
   │  class StageX:                           │
   │    def __init__(self, config: StageXConfig)│   ← Config = settings in
   │    def initiate_stage_x(self, prev_artifact):│
   │        # 1. read prev_artifact            │
   │        # 2. do the work                   │
   │        # 3. write outputs to disk         │
   │        return StageXArtifact(...)         │   ← Artifact = outputs out
   └─────────────────────────────────────────┘
                               │
                               ▼
                  This stage's Artifact ──▶ next stage
```

The recipe per stage:
1. Define a `Config` dataclass (inputs, paths, thresholds)
2. Define an `Artifact` dataclass (outputs)
3. Write a class with an `initiate_<stage_name>()` method
4. Method reads the previous stage's artifact, does the work, returns its own artifact

### Step 5.0 — The canonical stage (copy this skeleton 7 times)

Before the 7 stages, here is **one complete stage end to end** — Config, Artifact, Component, and its test. Every other stage is this exact shape with different logic inside. Internalize this and the other 6 are mechanical.

**The config object** — `src/pipeline/config_entity.py`:
```python
from dataclasses import dataclass

@dataclass
class DataIngestionConfig:
    accel_path: str
    gyro_path: str
    output_dir: str
    sampling_rate: int = 50
```

**The artifact object** — `src/pipeline/artifact_entity.py`:
```python
from dataclasses import dataclass

@dataclass
class DataIngestionArtifact:
    fused_csv_path: str
    n_rows: int
```

**The component** — `src/components/data_ingestion.py`:
```python
import pandas as pd
from pathlib import Path
from src.pipeline.config_entity import DataIngestionConfig
from src.pipeline.artifact_entity import DataIngestionArtifact

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config                      # ← dependency injection: config passed IN

    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        # 1. READ inputs (named by config, never hardcoded)
        accel = pd.read_csv(self.config.accel_path)
        gyro = pd.read_csv(self.config.gyro_path)

        # 2. DO THE WORK (this stage's one job: fuse the two streams)
        fused = pd.merge_asof(
            accel.sort_values("timestamp"),
            gyro.sort_values("timestamp"),
            on="timestamp",
            direction="nearest",
        )

        # 3. WRITE output to disk
        out = Path(self.config.output_dir) / "sensor_fused_50Hz.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        fused.to_csv(out, index=False)

        # 4. RETURN a typed artifact (the baton for the next stage)
        return DataIngestionArtifact(fused_csv_path=str(out), n_rows=len(fused))
```

**The test** — `tests/test_data_ingestion.py`:
```python
import pandas as pd
from src.pipeline.config_entity import DataIngestionConfig
from src.components.data_ingestion import DataIngestion

def test_ingestion_fuses_streams(tmp_path):
    # build tiny fake inputs
    (tmp_path / "a.csv").write_text("timestamp,ax\n0,1.0\n1,2.0\n")
    (tmp_path / "g.csv").write_text("timestamp,gx\n0,0.1\n1,0.2\n")

    cfg = DataIngestionConfig(
        accel_path=str(tmp_path / "a.csv"),
        gyro_path=str(tmp_path / "g.csv"),
        output_dir=str(tmp_path),
    )
    artifact = DataIngestion(cfg).initiate_data_ingestion()

    assert artifact.n_rows == 2
    fused = pd.read_csv(artifact.fused_csv_path)
    assert {"ax", "gx"}.issubset(fused.columns)   # both streams present
```

**Why this is the whole game:**
- The component never reads a hardcoded path — everything comes from `config`. → reproducible.
- It returns a *typed* artifact, not a loose dict. → the next stage can't misread it.
- The test builds fake inputs and checks the output **without running the pipeline**. → fast, isolated.
- To build Stage 2, you copy these 4 files, rename `Ingestion`→`Validation`, and change only the "DO THE WORK" block.

> 🔁 **Repeat this skeleton for all 7 stages.** Same shape, different middle. That sameness is what makes the codebase readable and the orchestrator trivial.

---

### Step 5.1 — Stage 1: Data Ingestion (`src/components/data_ingestion.py`)
- Read accel CSV + gyro CSV
- Resample both to 50 Hz if needed
- Merge on timestamp → fused CSV
- Return `DataIngestionArtifact(fused_csv_path=...)`

**Why a separate ingestion stage?** Different data sources (fused CSV vs raw pair) need to produce the same output. Isolating this lets you swap in a Kafka stream later without touching Stage 2.

---

### Step 5.2 — Stage 2: Data Validation (`src/components/data_validation.py`)
- Check column names match expected schema
- Check value ranges (accel: ±50 m/s², gyro: ±2000 deg/s)
- Check sampling rate (20ms between rows ± tolerance)
- Raise `DataValidationError` if anything fails
- Return `DataValidationArtifact(validation_status="PASSED", report_path=...)`

**Why validate?** Bad sensor data produces confident wrong predictions. Fail fast here, not silently at inference.

---

### Step 5.3 — Stage 3: Transformation (`src/components/data_transformation.py`)
- Unit conversion if needed (raw ADC → m/s², raw → deg/s)
- Sliding window: `[n_windows, 200, 6]`
- Save as `production_X.npy`
- Return `DataTransformationArtifact(windows_path=..., n_windows=...)`

**Why `.npy` not CSV?** 3D tensor can't be stored in 2D CSV. `.npy` is fast binary format for arrays.

---

### Step 5.4 — Stage 4: Inference (`src/components/model_inference.py`)
```python
import numpy as np, json
from tensorflow import keras
from pathlib import Path

# Load runtime contract
contract = Path(config.contract_dir)
model = keras.models.load_model(contract / config.model_filename)

with open(contract / "label_order.json") as f:
    label_order = json.load(f)

# Record the model MD5 for provenance (logged with the run + MLflow)
# ... compute md5(contract / model_filename) ...

# Load windows produced by Stage 3 (already unit-converted AND z-score-scaled in production)
X = np.load(transformation_artifact.windows_path)   # [n_windows, 200, 6]

# Predict — Stage 3 already applied unit conversion + the z-score scaler, so feed straight in.
probabilities = model.predict(X)                 # [n_windows, 11]
predictions = np.argmax(probabilities, axis=1)   # [n_windows]
confidence = np.max(probabilities, axis=1)        # [n_windows]
```
**Where does scaling happen?** Not in Stage 4 — in **Stage 3** (and, on the serving side, in the WebUI's `_apply_final_model_scaler`). The deployed Model D1 was trained on z-score-scaled windows, so Stage 3 applies `garmin_train_scaler.json` after unit conversion; Stage 4 just runs the already-scaled tensor through the model. The parity rule: scale at inference exactly as you scaled at training — using the *same* saved scaler, never a re-fit one.

---

### Step 5.5 — Stage 5: Evaluation (`src/components/model_evaluation.py`)
- Compute mean confidence, confidence histogram
- If labels present: accuracy, macro-F1, confusion matrix
- Save evaluation report JSON
- Return `ModelEvaluationArtifact(...)`

**Why optional labels?** Production data is often unlabeled. The pipeline must work either way.

---

### Step 5.6 — Stage 6: Monitoring (`src/components/post_inference_monitoring.py`)

Three layers:
```python
# Layer 1: Mean confidence
mean_conf = confidence.mean()
conf_status = "WARNING" if mean_conf < threshold else "HEALTHY"

# Layer 2: Temporal consistency.
# Raw transition rate is the PRIMARY signal:
raw_flips = np.sum(np.diff(predictions) != 0) / (len(predictions) - 1)
temporal_status = "WARNING" if raw_flips > temporal_threshold else "HEALTHY"

# Additive SOFT-VOTE smoothing (k=3): average the softmax vectors over a
# 3-window neighbourhood, then argmax. Reported ALONGSIDE the raw rate, never
# instead of it — so smoothing can't hide a genuinely unstable model.
def smooth_softvote(probabilities, k=3):
    n, half = len(probabilities), k // 2
    out = np.empty_like(probabilities)
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        out[i] = probabilities[lo:hi].mean(axis=0)
    return out.argmax(axis=1)

smoothed = smooth_softvote(probabilities, k=3)
smoothed_flips = np.sum(np.diff(smoothed) != 0) / (len(smoothed) - 1)  # reported beside raw

# Layer 3: Drift detection (z-score)
with open(baseline_path) as f:
    baseline = json.load(f)
current_mean = X.reshape(-1, 6).mean(axis=0)
z_scores = np.abs((current_mean - np.array(baseline["mean"])) / np.array(baseline["std"]))
drift_z = z_scores.max()
drift_status = "WARNING" if drift_z > drift_z_threshold else "HEALTHY"
```
**Why three layers?** Each catches a different failure mode. One layer can be healthy while another fails.

---

### Step 5.7 — Stage 7: Trigger (`src/components/trigger_evaluation.py`)
```python
warning_count = sum([
    conf_status == "WARNING",
    temporal_status == "WARNING",
    drift_status == "WARNING"
])

if warning_count == 0:
    decision = "NO_ACTION"
elif warning_count == 1:
    decision = "MONITOR"
elif warning_count == 2:
    decision = "REVIEW"
else:
    decision = "RETRAIN"   # all 3 layers failed — but still requires human approval
```
**Why this scale?** Progressive escalation. One warning alone could be a one-off. All three failing simultaneously is a strong signal.

---

### Step 5.8 — Orchestrate all stages (`src/pipeline/production_pipeline.py`)
```python
class ProductionPipeline:
    def run(self):
        ingestion_artifact = DataIngestion(self.config.ingestion).initiate_data_ingestion()
        validation_artifact = DataValidation(self.config.validation).initiate_data_validation(ingestion_artifact)
        transformation_artifact = DataTransformation(self.config.transformation).initiate_data_transformation(validation_artifact)
        inference_artifact = ModelInference(self.config.inference).initiate_model_inference(transformation_artifact)
        evaluation_artifact = ModelEvaluation(self.config.evaluation).initiate_model_evaluation(inference_artifact)
        monitoring_artifact = PostInferenceMonitoring(self.config.monitoring).initiate_monitoring(inference_artifact, evaluation_artifact)
        trigger_artifact = TriggerEvaluation(self.config.trigger).initiate_trigger_evaluation(monitoring_artifact)
        return trigger_artifact
```
**Why chain artifact objects?** Type safety. If you rename a field in an artifact, the next stage fails at import — not silently at runtime.

---

## Phase 6 — Experiment Tracking

### Step 6.1 — Add MLflow logging to the pipeline
```python
import mlflow

mlflow.set_experiment("har-production-pipeline")

with mlflow.start_run():
    # Log one or two metrics per stage
    mlflow.log_metric("n_windows", transformation_artifact.n_windows)
    mlflow.log_metric("mean_confidence", monitoring_artifact.mean_confidence)
    mlflow.log_metric("drift_z_score", monitoring_artifact.drift_z)

    # Log run parameters
    mlflow.log_param("trigger_decision", trigger_artifact.decision)
    mlflow.log_param("overall_status", "SUCCESS")
    mlflow.log_param("should_retrain", False)

    # Log artifact
    mlflow.log_artifact("artifacts/run_info.json")
    mlflow.set_tag("model_type", "1DCNNBiLSTM")
```

---

### Step 6.2 — Add MLflow logging to the WebUI serving path
```python
def _log_inference_mlflow(session_result):
    mlflow.set_experiment("inference-production")
    with mlflow.start_run():
        mlflow.log_metric("mean_confidence", session_result.mean_confidence)
        mlflow.log_metric("total_windows", session_result.n_windows)
        mlflow.log_param("model_md5", session_result.model_md5)
        mlflow.log_param("runtime_mode", session_result.mode)
```
**Why two separate experiments?** WebUI runs are interactive and frequent. Batch pipeline runs are governed and rare. Mixing them makes it hard to audit either.

---

## Phase 7 — WebUI (FastAPI)

### Step 7.1 — Create `src/api/app.py`
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse

app = FastAPI(title="HAR MLOps Dashboard")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return "<html>...</html>"   # render upload form

@app.post("/upload")
async def upload_session(
    accel_file: UploadFile = File(...),
    gyro_file: UploadFile = File(None),
    label_file: UploadFile = File(None),
):
    # 1. Save uploaded files to temp
    # 2. Run ingestion → transformation → inference → evaluation → monitoring → trigger
    # 3. Log to MLflow
    # 4. Return result as HTML dashboard
    should_retrain = False   # HARDCODED — never auto-retrain from WebUI
    ...
```

### Step 7.2 — Run the WebUI
```bash
uvicorn src.api.app:app --reload --port 8000
```
Open `http://localhost:8000`.

---

## Phase 8 — Docker

### Step 8.1 — Create `config/requirements-runtime.txt` (slim)
```
numpy>=1.24
pandas>=2.0
scipy>=1.10
tensorflow-cpu>=2.14
scikit-learn>=1.3
mlflow>=2.11
fastapi>=0.109
uvicorn[standard]>=0.27
pydantic>=2.5
python-multipart>=0.0.6
matplotlib>=3.8
seaborn>=0.13
pyyaml>=6.0.1
```
**Why separate from requirements.txt?** No dev tools (pytest, black, mypy, flake8) in production. Smaller image, smaller attack surface.

---

### Step 8.2 — Create `docker/Dockerfile.inference`
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY config/requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt
COPY src/ ./src/
COPY models/runtime_contract/ ./models/runtime_contract/
COPY config/ ./config/
EXPOSE 8000
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 8.3 — Create `docker/Dockerfile.training`
```dockerfile
FROM python:3.10
WORKDIR /app
COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pip install -e .
CMD ["python", "run_pipeline.py"]
```

### Step 8.4 — Build and test
```bash
docker build -f docker/Dockerfile.inference -t har-inference .
docker run -p 8000:8000 har-inference
# open http://localhost:8000 — should see the dashboard
```

---

## Phase 9 — Tests

### Step 9.1 — Write contract tests (`tests/test_contract.py`)
```python
import json, hashlib
from pathlib import Path

CONTRACT = Path("models/runtime_contract/model_d1_final/")

def test_contract_files_exist():
    for f in ["model_d1.keras", "garmin_train_scaler.json",
              "raw_physical_baseline.json", "label_order.json", "artifact_md5.json"]:
        assert (CONTRACT / f).exists(), f"{f} missing from runtime contract"

def test_contract_md5s_match():
    with open(CONTRACT / "artifact_md5.json") as f:
        expected = json.load(f)
    for filename, expected_md5 in expected.items():
        actual_md5 = hashlib.md5((CONTRACT / filename).read_bytes()).hexdigest()
        assert actual_md5 == expected_md5, f"{filename} MD5 mismatch — file may have changed"
```
**Why these tests?** They are the automated guard against someone accidentally overwriting a model file. Run them in CI before every deployment.

---

### Step 9.2 — Run tests
```bash
pytest tests/ -v
pytest tests/ -m unit
pytest tests/ --cov=src --cov-report=html
```

---

## Phase 10 — Thesis (LaTeX)

### Step 10.1 — Folder structure
```
thesis/
├── main.tex           # master document — includes all chapters
├── references.bib     # BibTeX references
├── chapters/
│   ├── ch1_introduction.tex
│   ├── ch2_background.tex
│   ├── ch3_related_work.tex
│   ├── ch4_methodology.tex
│   ├── ch5_pipeline_implementation.tex
│   ├── ch6_monitoring_governance.tex
│   ├── ch7_experiments_evaluation.tex
│   └── ch8_discussion_conclusion.tex
├── appendices/
│   ├── appendix_a_...tex
│   └── appendix_e_system_walkthrough.tex
└── figures/
```

### Step 10.2 — `main.tex` minimum setup
```latex
\documentclass[12pt,a4paper]{report}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage[hidelinks,pdfpagelabels]{hyperref}
\hypersetup{
  pdftitle={Your Thesis Title},
  pdfauthor={Your Name}
}
\usepackage[backend=biber,style=ieee]{biblatex}
\addbibresource{references.bib}

\begin{document}
\include{chapters/ch1_introduction}
% ...
\printbibliography
\end{document}
```

### Step 10.3 — Build the PDF
```bash
cd thesis
latexmk -pdf main.tex
```
**Why `latexmk`?** Automatically runs LaTeX + BibTeX/Biber the right number of times. You don't have to manually run `pdflatex → biber → pdflatex → pdflatex`.

---

## Phase 11 — Submission

### Step 11.1 — Squash-merge your working branch to main
```bash
git checkout main
git merge --squash your-branch-name
git commit -m "feat: complete MLOps HAR pipeline thesis submission"
```
**Why squash?** Collapses hundreds of development commits into one clean submission commit. The tag marks this exact state.

---

### Step 11.2 — Tag the submission
```bash
git tag -a v1.0-submission -m "Final thesis submission — June 2026"
git push origin main --tags
```

---

### Step 11.3 — Delete stale branches
```bash
git branch -d branch-name          # local
git push origin --delete branch-name  # remote
```

---

### Step 11.4 — Final checklist before submitting

- [ ] `pytest tests/ -v` — all pass
- [ ] `latexmk -pdf main.tex` — 0 errors, 0 undefined references
- [ ] `python run_pipeline.py` — 7 stages complete, `overall_status=SUCCESS`
- [ ] `uvicorn src.api.app:app` — dashboard loads, file upload works
- [ ] `mlflow ui` — both experiments visible with logged runs
- [ ] `docker build -f docker/Dockerfile.inference -t har-inference . && docker run -p 8000:8000 har-inference` — container runs
- [ ] Git tag `v1.0-submission` pushed
- [ ] Thesis PDF exported and signed

---

## Common Pitfalls (learn from these, don't repeat them)

| ⚠️ Mistake | What happens | The fix |
|---|---|---|
| Fitting a *new* scaler at inference | Predictions become garbage — model sees an unfamiliar scale | **Load** the saved `scaler.json`, never re-fit |
| Different window/stride in train vs inference | Silent accuracy collapse | Keep `WINDOW`/`STRIDE` in one config, used by both |
| Committing data/models to git | Repo bloats to GBs, clones crawl | Track with DVC; gitignore `*.npy *.keras *.csv` |
| Reporting only 5-fold accuracy | Hides the personalization gap — misleading | Always report **LOUO too** |
| Auto-retraining on production data | One bad session corrupts the model | Keep `should_retrain=False`; require human approval |
| Overwriting a contract file by hand | Pipeline serves wrong predictions silently | MD5 check catches it — *update the MD5 too* |
| Putting dev tools in the inference image | Bloated, slower, bigger attack surface | Slim image uses `requirements-runtime.txt` only |
| `yaml.load()` instead of `safe_load()` | Security hole (arbitrary code execution) | Always `yaml.safe_load()` |
| Forgetting `pip install -e .` | `import src.*` fails everywhere | Editable install once, after creating venv |

---

## Mini-Glossary

| Term | Plain-English meaning |
|---|---|
| **Window** | A fixed 4-second (200-sample) slice of sensor data fed to the model |
| **Stride** | How far the window jumps each step (100 samples = 2 seconds) |
| **Scaler** | The saved mean/std that normalizes data the same way as in training |
| **Runtime contract** | The 4 files (model, scaler, baseline, labels) that must travel together |
| **Artifact** | A typed object one stage passes to the next |
| **Drift** | When incoming data looks statistically different from training data |
| **LOUO** | Leave-One-User-Out — test on a person the model never trained on |
| **Trigger** | The governance decision: NO_ACTION / MONITOR / REVIEW / RETRAIN |
| **MLflow run** | One recorded execution, with its params, metrics, and artifacts |
| **DVC pointer** | A tiny `.dvc` file in git that points to a big file in storage |

---

*This guide builds the project from zero to submission. For the reasoning behind every decision, see `PROJECT_DEEP_DIVE.md`.*

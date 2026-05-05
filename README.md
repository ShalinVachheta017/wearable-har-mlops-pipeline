# HAR MLOps Pipeline for Wearable Anxiety Recognition

This repository contains an offline-first MLOps pipeline for anxiety-related human activity recognition (HAR) from wearable accelerometer and gyroscope data.

Primary goals:

- reproducible end-to-end pipeline execution
- explicit stage-by-stage workflow for thesis defense
- monitoring and trigger-based retraining decisions
- artifact and evidence tracking for research reproducibility

## Project Workflow Summary

The production entrypoint is [run_pipeline.py](run_pipeline.py), which orchestrates the following stages:

1. ingestion
2. validation
3. transformation
4. inference
5. evaluation
6. monitoring
7. trigger
8. retraining (optional)
9. registration (optional)
10. baseline_update (optional)
11. calibration (optional advanced mode)

## Visual Overview

### Pipeline Flow (End-to-End)

```mermaid
flowchart LR
    A[Raw Sensor Data<br/>Accel + Gyro] --> B[1. Ingestion]
    B --> C[2. Validation]
    C --> D[3. Transformation]
    D --> E[4. Inference]
    E --> F[5. Evaluation]
    F --> G[6. Monitoring]
    G --> H[7. Trigger]

    H --> I{should_retrain?}
    I -- Yes --> J[8. Retraining]
    J --> K[9. Registration]
    K --> L[10. Baseline Update]
    I -- No --> M[Stop: Keep Current Model]

    H -. optional .-> N[11. Calibration<br/>Advanced Mode]
```

### Stage Composition Chart

```mermaid
pie showData
    title Pipeline Stage Groups (11 total)
    "Core Inference and Monitoring (Stages 1-7)" : 7
    "Retraining Cycle (Stages 8-10)" : 3
    "Advanced Calibration (Stage 11)" : 1
```

### Project Graphic

![HAR MLOps Graphic](docs/images/unnamed.jpg)

## Project Setup and Structure

### Step 1: Create Environment

Option A (recommended, conda):

```powershell
conda create -n thesis-mlops python=3.11 -y
conda activate thesis-mlops
python -m pip install --upgrade pip
python -m pip install -r config/requirements.txt
```

Option B (editable install):

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -e .[dev]
```

After editable install, you can run the CLI command:

```powershell
har-pipeline
```

### Step 2: Verify Required Artifacts

Expected core files include:

- [models/pretrained/fine_tuned_model_1dcnnbilstm.keras](models/pretrained/fine_tuned_model_1dcnnbilstm.keras)
- [models/normalized_baseline.json](models/normalized_baseline.json)
- one accel/gyro pair in [data/raw](data/raw)

If DVC-tracked assets are missing:

```powershell
dvc pull
```

### Defended Model Lineage

The default runtime uses the pretrained baseline model
[models/pretrained/fine_tuned_model_1dcnnbilstm.keras](models/pretrained/fine_tuned_model_1dcnnbilstm.keras).
Any retrained model should be selected only after labeled-data evaluation
demonstrates it is better than the pretrained baseline.

### Model Promotion Policy

Hard rule for this repository:
- Default model for pipeline/API/Docker is the mentor-provided pretrained model.
- Drift/monitoring alerts alone do not justify promotion.
- Retraining/fine-tuning can run only when labeled data is available for evaluation.
- Promotion to new default is allowed only if labeled comparison proves better performance than the current default model under defined acceptance criteria.
- If the candidate is equal or worse, keep the current default model.

Canonical policy document: [docs/MODEL_PROMOTION_POLICY.md](docs/MODEL_PROMOTION_POLICY.md)

### Monitoring Evidence Scope

Prometheus/Grafana are treated as optional future-work infrastructure; the defended implementation uses offline-first pipeline monitoring artifacts and trigger reports. Monitoring evidence for the thesis comes from pipeline-generated JSON/CSV artifacts, trigger-decision reports, logs, MLflow/DVC evidence, and saved run artifacts.

### Step 3: Run the Main Pipeline (Stages 1-7)

```powershell
python run_pipeline.py
```

### Step 4: Reproduce Thesis Main Result Path

Run an explicit stage sequence on a known data session:

```powershell
python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger --accel-file data/raw/2025-08-19-08-58-40_accelerometer.csv --gyro-file data/raw/2025-08-19-08-58-40_gyroscope.csv
```

Detailed reproducibility instructions: [REPRODUCE.md](REPRODUCE.md)

### Step 5: Verify Outputs

You should see:

- run summaries in [logs/pipeline](logs/pipeline)
- stage artifacts in [artifacts](artifacts)
- tracking runs in [mlruns](mlruns)

## Common Pipeline Commands

Run only selected stages:

```powershell
python run_pipeline.py --stages inference evaluation monitoring trigger
```

Enable retraining path (trigger-gated stages 8-10):

```powershell
python run_pipeline.py --retrain --adapt adabn
```

Note: retraining stages execute only when Stage 7 decides `should_retrain=true`.

Run advanced calibration stage:

```powershell
python run_pipeline.py --advanced
```

Use a custom input file:

```powershell
python run_pipeline.py --input-csv data/raw/my_recording.csv
```

## Optional Services

### Docker Compose Services

```powershell
docker-compose up -d
docker-compose logs -f
docker-compose down
```

Container definitions and service notes are in [docker-compose.yml](docker-compose.yml).

### FastAPI Inference Service (Local)

```powershell
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Useful local endpoints:

- `GET /docs`: interactive FastAPI documentation.
- `GET /api/health`: model/service health check.
- `GET /api/model/info`: active model metadata.
- `POST /api/upload`: upload raw sensor data for inference.

## Thesis Handbook Dashboard Preview (No npm Install)

If you only want to preview the already-built dashboard app, serve the static [thesis/handbook-dashboard/dist](thesis/handbook-dashboard/dist) folder directly:

```powershell
Set-Location "thesis/handbook-dashboard/dist"
python -m http.server 4173
```

Then open <http://localhost:4173>.

This avoids adding Node dependencies to your thesis Python environment.

## Testing and Sanity Checks

Quick smoke tests:

```powershell
pytest -q --maxfail=1
```

Non-slow subset used in reproducibility checks:

```powershell
python -m pytest tests/ -m "not slow and not integration" -q --tb=short
```

Import/runtime sanity:

```powershell
python -m compileall src scripts run_pipeline.py
```

## Repository Map

- [run_pipeline.py](run_pipeline.py): single entrypoint orchestrating pipeline stages
- [src](src): core implementation (pipeline, components, API, utilities)
- [config](config): config and dependency manifests
- [tests](tests): test suite
- [scripts](scripts): support and maintenance scripts
- [docs](docs): technical and thesis-oriented documentation
- [thesis](thesis): thesis sources and related materials
- [internal](internal): non-core historical/working support materials

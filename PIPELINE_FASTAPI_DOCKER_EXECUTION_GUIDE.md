# Pipeline, FastAPI, and Docker Execution Guide

This guide is the practical runbook for the thesis defense. It explains how to run the offline-first HAR MLOps pipeline, how to use the FastAPI inference service, how to run Docker/MLflow, and how to capture evidence without changing the defended runtime story.

## Current Defended Runtime Story

- Preprocessing baseline: z-score normalization.
- Default model: `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`.
- Runtime monitoring/governance: confidence, uncertainty, dominant-class share, temporal behavior, and lightweight drift monitoring.
- MMD: calibrated experimental/offline drift-audit signal, not the defended runtime retraining trigger.
- FastAPI: inference service for fused CSV upload or accelerometer+gyroscope pair upload.
- Retraining: requires labels plus governance gates; the API upload path does not mutate the deployed model.
- Docker: local reproducibility and image-smoke evidence, not production CD.
- Prometheus/Grafana/alert rules: historical/optional/future-work only, not active defended evidence.

Defended monitoring evidence comes from pipeline artifacts, trigger reports, logs, MLflow/DVC evidence, and saved run outputs.

## Prerequisites

Run commands from the repository root:

```powershell
cd "D:\study apply\ML Ops\MasterArbeit_MLops"
```

Use the thesis environment:

```powershell
conda activate thesis-mlops
```

If you run through `conda run`, use:

```powershell
conda run -n thesis-mlops python run_pipeline.py --help
```

## Baseline Verification

Run these before a defense demo or before collecting new evidence:

```powershell
conda run -n thesis-mlops python run_pipeline.py --help
conda run -n thesis-mlops pytest tests/ -q --tb=short
```

Current known branch evidence:

- Regression baseline: `181 passed + 2 skipped`.
- API upload smoke: fused CSV and accelerometer+gyroscope pair tested.
- Raw-pair smoke example: `121050` merged samples, `1209` windows.
- Docker image finding: inference image works but is heavy; current image is about `4.5GB`, with the dependency install layer about `3.3GB`.

## Pipeline Stage Map

| Stage | Name | Purpose | Mutates model? |
|---|---|---|---|
| 1 | Ingestion | Load raw/fused sensor CSV data | No |
| 2 | Validation | Check schema, ranges, missing values, sampling assumptions | No |
| 3 | Transformation | Merge/resample/window/normalize into model-ready tensors | No |
| 4 | Inference | Load retained model and predict activity windows | No |
| 5 | Evaluation | Evaluate if labels are available | No |
| 6 | Monitoring | Confidence, uncertainty, temporal behavior, drift/collapse checks | No |
| 7 | Trigger | Decide `NONE`, `REVIEW`, or retraining queue path | No |
| 8 | Retraining | Candidate model training/adaptation, label-gated | Candidate only |
| 9 | Registration | Register candidate if quality is sufficient | Controlled |
| 10 | Baseline update | Update monitoring baseline after approved promotion | Controlled |
| 11 | Calibration | Optional calibration/uncertainty stage | No direct mutation |

## Run the Default Pipeline

Default execution runs stages 1-7:

```powershell
conda run -n thesis-mlops python run_pipeline.py
```

Explicit stage list:

```powershell
conda run -n thesis-mlops python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger
```

Run with one fused processed CSV:

```powershell
conda run -n thesis-mlops python run_pipeline.py --input-csv data/processed/fused_2025_07_16_21_46_56_50Hz.csv
```

Run with raw accelerometer and gyroscope CSVs:

```powershell
conda run -n thesis-mlops python run_pipeline.py --accel-file data/raw/2025-07-16-21-46-56_accelerometer.csv --gyro-file data/raw/2025-07-16-21-46-56_gyroscope.csv
```

Run a specific subset:

```powershell
conda run -n thesis-mlops python run_pipeline.py --stages inference evaluation monitoring trigger
```

Run the defended operational path plus optional calibration:

```powershell
conda run -n thesis-mlops python run_pipeline.py --advanced
```

Run all label-gated lifecycle stages only when labels and promotion evidence are available:

```powershell
conda run -n thesis-mlops python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger retraining registration baseline_update calibration --labels path/to/labels.csv --auto-deploy --update-baseline
```

Do not use the all-stage command as a casual smoke test. Stages 8-10 are governed mutation stages and should only be run when the candidate model can be evaluated against labels.

## Preprocessing Switches

The defended baseline uses z-score normalization. Use these only for ablation or debugging:

```powershell
conda run -n thesis-mlops python run_pipeline.py --normalization-variant zscore
conda run -n thesis-mlops python run_pipeline.py --normalization-variant robust
conda run -n thesis-mlops python run_pipeline.py --normalization-variant none
conda run -n thesis-mlops python run_pipeline.py --no-normalization
```

Defense wording: z-score is the baseline preprocessing choice. Robust/no-normalization are ablation variants, not the submitted default.

## Retraining, Registration, and Baseline Update

Retraining is label-gated. Do not describe unlabeled API uploads as retraining data.

Example labeled retraining command:

```powershell
conda run -n thesis-mlops python run_pipeline.py --retrain --labels path/to/labels.csv
```

Candidate registration is controlled:

```powershell
conda run -n thesis-mlops python run_pipeline.py --retrain --labels path/to/labels.csv --auto-deploy
```

Baseline update is also opt-in:

```powershell
conda run -n thesis-mlops python run_pipeline.py --retrain --labels path/to/labels.csv --auto-deploy --update-baseline
```

Defense rule: a candidate is not promoted because drift exists. Promotion requires labels, evaluation, governance approval, and better candidate quality.

## FastAPI: Local Development Server

Start the API locally:

```powershell
$env:MODEL_PATH="models/pretrained/fine_tuned_model_1dcnnbilstm.keras"
conda run -n thesis-mlops uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Open:

- UI: `http://127.0.0.1:8000/`
- Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`
- Model info: `http://127.0.0.1:8000/api/model/info`

Health check:

```powershell
curl.exe http://127.0.0.1:8000/api/health
```

Model info:

```powershell
curl.exe http://127.0.0.1:8000/api/model/info
```

## FastAPI Upload Modes

### Mode 1: Fused CSV

Use this when the CSV already contains all six sensor channels:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/upload" -F "file=@data/processed/fused_2025_07_16_21_46_56_50Hz.csv"
```

Expected fused columns:

- `acc_x`, `acc_y`, `acc_z`
- `gyro_x`, `gyro_y`, `gyro_z`

### Mode 2: Raw Accelerometer + Gyroscope Pair

Use this when the dataset is split into two raw files:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/upload" -F "accelerometer_file=@data/raw/2025-07-16-21-46-56_accelerometer.csv" -F "gyroscope_file=@data/raw/2025-07-16-21-46-56_gyroscope.csv"
```

This mode merges/resamples the raw pair before windowing and inference.

### Important API Boundary

The API upload path performs inference and monitoring. It does not run the whole pipeline, retrain a model, register a candidate, or update the baseline. Retraining remains a pipeline/governance path because it needs labels and candidate-quality checks.

## Common Upload Error

If you upload only an accelerometer CSV as a fused CSV, the API may report:

```text
Could not find gyro_x column
```

That means the file is not a fused six-channel input. Use one of these fixes:

- upload the matching gyroscope CSV together with it using two-file mode, or
- upload a processed fused file from `data/processed/`.

## Docker Compose

Build and run inference + MLflow:

```powershell
docker compose build inference
docker compose up -d mlflow inference
docker compose ps
curl.exe http://127.0.0.1:8000/api/health
```

Open:

- FastAPI UI: `http://127.0.0.1:8000/`
- FastAPI docs: `http://127.0.0.1:8000/docs`
- MLflow UI: `http://127.0.0.1:5000`

View logs:

```powershell
docker compose logs -f inference
docker compose logs -f mlflow
```

Stop services:

```powershell
docker compose down
```

Run the on-demand training container:

```powershell
docker compose --profile training build training
docker compose --profile training run --rm training
```

## Standalone Inference Image

Build:

```powershell
docker build -t har-inference:phase2 -f docker/Dockerfile.inference .
```

Run:

```powershell
docker run --rm -p 8000:8000 -v "${PWD}\models:/app/models:ro" -v "${PWD}\config:/app/config:ro" -e MODEL_PATH=/app/models/pretrained/fine_tuned_model_1dcnnbilstm.keras har-inference:phase2
```

Health check:

```powershell
curl.exe http://127.0.0.1:8000/api/health
```

## Docker Image Size Checks

List image sizes:

```powershell
docker images
```

Show container disk use:

```powershell
docker ps -s
```

Show Docker storage summary:

```powershell
docker system df
```

Find which layer is large:

```powershell
docker history har-inference:phase2 --format "table {{.Size}}\t{{.CreatedBy}}"
```

Current finding: the inference image is dependency-layer dominated, not source-code dominated. The next optimization step is to create a smaller inference-only requirements file and avoid training-only dependencies in `docker/Dockerfile.inference`.

## Evidence Capture Commands

Create the report folder:

```powershell
New-Item -ItemType Directory -Force reports
```

Save CLI help:

```powershell
conda run -n thesis-mlops python run_pipeline.py --help > reports/phase2_cli_help.txt
```

Save API health:

```powershell
curl.exe http://127.0.0.1:8000/api/health > reports/phase2_api_health.json
```

Save model info:

```powershell
curl.exe http://127.0.0.1:8000/api/model/info > reports/phase2_api_model_info.json
```

Save Docker service status:

```powershell
docker compose ps > reports/phase2_docker_compose_ps.txt
docker images > reports/phase2_docker_images.txt
docker system df > reports/phase2_docker_system_df.txt
```

Save image-layer history:

```powershell
docker history har-inference:phase2 --format "table {{.Size}}\t{{.CreatedBy}}" > reports/phase2_docker_history_har_inference.txt
```

## Defense-Safe Statements

Use these lines in writing or oral defense:

- The pipeline supports both fused processed CSVs and raw accelerometer+gyroscope pairs for inference.
- Labeled data is required for retraining and candidate evaluation.
- The API is an inference and monitoring surface, not an automatic retraining surface.
- Docker demonstrates local reproducibility and service isolation.
- CI and image smoke evidence support engineering quality, but production CD is outside scope.
- MMD remains an experimental/offline drift-audit signal in the submitted runtime story.

## Next Optimization Task

After the API evidence is stable, reduce the inference image size:

1. Create `config/requirements-inference.txt`.
2. Move training-only packages out of the inference image.
3. Rebuild `har-inference:phase2`.
4. Compare `docker images` and `docker history` before/after.
5. Save the results under `reports/`.

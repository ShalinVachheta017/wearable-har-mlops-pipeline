# Reproducing the Pipeline

Step-by-step guide to run the full Stage 1–7 pipeline on a fresh machine.

---

## Step 1 — Clone the repository

```powershell
git clone <repo-url>
cd MasterArbeit_MLops
```

---

## Step 2 — Create the environment

```powershell
conda create -n thesis-mlops python=3.11 -y
conda activate thesis-mlops
pip install -r config/requirements.txt
```

---

## Step 3 — Restore model and data

The model and example data are DVC-tracked. Pull them:

```powershell
dvc pull
```

**If DVC is not available:** unzip the release artifact bundle over the repo root. It contains:

```
data/raw/                                         ← example sensor session
models/runtime_contract/model_d1_final_20260528/  ← defended D1 model package
artifacts/20260528_122625/                        ← defended evidence run
logs/pipeline/pipeline_result_20260528_122625.json
```

After unzipping, continue to Step 4.

Required files check — these must exist before running:

```
models/runtime_contract/model_d1_final_20260528/finetuned_1DCNNBILSTM_HAR_model.keras
models/runtime_contract/model_d1_final_20260528/garmin_train_scaler.json
models/runtime_contract/model_d1_final_20260528/garmin_train_scaled_baseline.json
models/runtime_contract/model_d1_final_20260528/label_order.json
data/raw/2025-08-19-08-58-40_accelerometer.csv
data/raw/2025-08-19-08-58-40_gyroscope.csv
```

---

## Step 4 — Run the pipeline

Run stages 1–7 on the included example session:

```powershell
python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger --accel-file data/raw/2025-08-19-08-58-40_accelerometer.csv --gyro-file data/raw/2025-08-19-08-58-40_gyroscope.csv
```

Or simply run with defaults (picks up the session automatically):

```powershell
python run_pipeline.py
```

---

## Step 5 — Check outputs

After a successful run you will see:

```
logs/pipeline/pipeline_result_<run_id>.json       ← overall result
artifacts/<run_id>/run_info.json                  ← stage statuses
artifacts/<run_id>/data_ingestion/fused_<timestamp>_50Hz.csv
artifacts/<run_id>/data_transformation/production_X.npy
artifacts/<run_id>/inference/predictions_<timestamp>.csv
artifacts/<run_id>/evaluation/evaluation_summary.json
artifacts/<run_id>/monitoring/monitoring_report.json
artifacts/<run_id>/trigger/trigger_decision.json
```

Reference defended run for comparison: `artifacts/20260528_122625/`

---

## Step 6 — Run tests (optional)

```powershell
python -m pytest tests/ -m "not slow and not integration" -q --tb=short
```

---

## Docker alternative (environment only)

Docker reproduces the software environment. Data and model must still be provided via DVC or the bundle above.

```powershell
docker compose build
docker compose run training python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger --accel-file data/raw/2025-08-19-08-58-40_accelerometer.csv --gyro-file data/raw/2025-08-19-08-58-40_gyroscope.csv
```

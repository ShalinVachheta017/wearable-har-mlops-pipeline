# Reproduce the Main Pipeline Result

This guide reproduces the main offline inference cycle (stages 1-7) used for thesis evidence.

## 1) Environment Setup

Option A (recommended, conda):

```powershell
conda create -n thesis-mlops python=3.11 -y
conda activate thesis-mlops
python -m pip install --upgrade pip
python -m pip install -r config/requirements.txt
```

Option B (pip editable install):

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -e .[dev]
```

## 2) Data and Model Prerequisites

Required files:

- `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`
- `models/normalized_baseline.json`
- one accel/gyro pair under `data/raw/`

Example pair already present in this repo:

- `data/raw/2025-08-19-08-58-40_accelerometer.csv`
- `data/raw/2025-08-19-08-58-40_gyroscope.csv`

If running from a fresh clone and DVC assets are missing, restore DVC-tracked data/model artifacts first (if remote is accessible):

```powershell
dvc pull
```

## 3) Exact Reproduction Command (Main Result Path)

Run stages 1-7 explicitly on one concrete session:

```powershell
python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger --accel-file data/raw/2025-08-19-08-58-40_accelerometer.csv --gyro-file data/raw/2025-08-19-08-58-40_gyroscope.csv
```

## 4) Expected Outputs

After a successful run, expect:

- Pipeline result summary:
  - `logs/pipeline/pipeline_result_<run_id>.json`
- Run artifact folder:
  - `artifacts/<run_id>/run_info.json`
  - `artifacts/<run_id>/data_ingestion/sensor_fused_50Hz.csv`
  - `artifacts/<run_id>/data_transformation/production_X.npy`
  - `artifacts/<run_id>/inference/predictions_<timestamp>.csv`
  - `artifacts/<run_id>/evaluation/evaluation_summary.json`
  - `artifacts/<run_id>/monitoring/monitoring_report.json`
  - `artifacts/<run_id>/trigger/trigger_decision.json`

Observed reference shape in current repo (example):

- `artifacts/20260329_212835/` contains stage 1-7 outputs with SUCCESS statuses in `run_info.json`.

## 5) Where Thesis Evidence Lives

- Evidence index: `docs/thesis/THESIS_EVIDENCE.md`
- 26-session negative-result table: `thesis/tables/before_vs_after_26datasets.csv`
- 26-session interpretation note: `thesis/chapters/before_vs_after_26datasets.md`
- Trigger logic explanation: `docs/TRIGGER_POLICY_EXPLANATION.md`

## 6) Quick Validation Command (Optional)

```powershell
python -m pytest tests/ -m "not slow and not integration" -q --tb=short
```

This does not reproduce pipeline outputs, but validates core non-slow behavior.

# Defense Video TODO

Last updated: 2026-05-28

Purpose: prepare a short recorded defense/demo video using the working Model D1 runtime path. This is a runbook/checklist, not final narration.

## Current Demo Contract

```text
Environment:      thesis-mlops
Model:            models/runtime_contract/model_d1_final_20260528/finetuned_1DCNNBILSTM_HAR_model.keras
Scaler:           models/runtime_contract/model_d1_final_20260528/garmin_train_scaler.json
Baseline:         models/runtime_contract/model_d1_final_20260528/garmin_train_scaled_baseline.json
Expected result:  Stage 1-7 SUCCESS
Known warning:    temporal transition warning can remain
MLflow:           tracked in thesis-mlops pipeline runs
```

## Prep Checklist

- Verify environment:

  ```powershell
  conda run -n thesis-mlops python -c "import tensorflow as tf; print(tf.__version__)"
  ```

- Run one clean pipeline smoke before recording:

  ```powershell
  conda run -n thesis-mlops python run_pipeline.py
  ```

- Confirm expected lines:
  - `Device: CPU`
  - `Runtime contract OK: model and scaler both from model_d1_final_20260528`
  - `Normalization: ON`
  - `Stage 'inference' completed`
  - `Drift check PASSED`
  - `Pipeline finished: SUCCESS`

- Open fallback artifacts before recording:
  - latest `logs/pipeline/pipeline_result_*.json`
  - latest `outputs/monitoring/monitoring_report.json`
  - latest prediction CSV under `data/prepared/predictions/`
  - `models/runtime_contract/model_d1_final_20260528/model_contract.json`
  - `models/runtime_contract/model_d1_final_20260528/garmin_train_scaler.json`

## Video Structure

1. Thesis scope, 30-45 seconds
   - Offline-first MLOps lifecycle for wearable HAR.
   - Not a clinical diagnosis system.
   - Not a production-ready deployment claim.

2. Runtime contract, 30-45 seconds
   - Raw Garmin files.
   - Unit conversion.
   - D1 train-only scaler.
   - Windowing to `(N, 200, 6)`.
   - D1 inference.

3. Live demo, 60-90 seconds
   - Run `python run_pipeline.py`.
   - Point out Stage 1-7.
   - Show the D1 runtime contract line.
   - Show inference distribution.

4. Monitoring and governance, 45-60 seconds
   - Confidence passes.
   - Drift passes after correct normalization.
   - Temporal warning routes to review.
   - `should_retrain=false` because data are unlabeled and QA/label gate is required.

5. Limitations, 30 seconds
   - Cross-user robustness remains limited.
   - High-confidence wrong-class cases motivate monitoring beyond softmax confidence.
   - Future work: calibration and more external labeled subjects.

## Do Not Say

- Do not say production-ready.
- Do not say clinical diagnosis.
- Do not say automatic retraining is active.
- Do not say GPU run proves model quality.
- Do not say MLflow is required for the demo.
- Do not hide the temporal warning; explain it as review-gated behavior.

## Tomorrow Tasks

- Dry-run the video once without recording.
- Trim terminal output or use a prepared terminal size.
- Record final video.
- Save final script notes next to this file.
- If the live run fails, use the fallback artifacts and say the demo is being shown from a saved successful run.

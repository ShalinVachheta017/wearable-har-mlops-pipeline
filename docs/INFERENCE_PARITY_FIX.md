# Inference Parity Fix

Purpose: record the final production inference contract and prevent the old scaler-normalization story from returning.

## Final Contract

- Accelerometer: convert raw Garmin milli-g values to m/s^2 when needed.
- Gyroscope: keep raw deg/s.
- Sampling rate: 50 Hz.
- Window size: 200 samples.
- Stride: 100 samples.
- Input tensor: `(N, 200, 6)` with channel order `Ax, Ay, Az, Gx, Gy, Gz`.
- Output tensor: 11 activity classes.
- Normalization: disabled.
- External StandardScaler: not applied during final production inference.
- Gravity removal: disabled.
- Calibration: disabled.

## Current Runtime Evidence

- `config/pipeline_config.yaml` sets `enable_normalization: False`, `normalization_variant: "none"`, and an empty scaler path.
- `src/components/data_transformation.py` writes metadata for `raw_physical_units_ms2_dps` with normalization disabled.
- `src/api/app.py` preserves raw physical units after accelerometer unit conversion and does not load `scaler_train_only.json`.
- `models/raw_physical_baseline.json` is the Stage 6 runtime baseline.

## Boundary

`data/prepared/scaler_train_only.json` remains useful for training, leakage checks, legacy transformed baselines, and controlled A/B diagnostics. It is not a final production inference requirement.

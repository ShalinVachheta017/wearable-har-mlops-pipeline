# Inference Parity Fix

Purpose: record the final production inference contract and prevent old scaler/layout stories from returning.

## Final Contract

- Model: `models/production_contract/model_a_final_20260508/fine_tuned_clean_model.keras`.
- Accelerometer: convert raw Garmin milli-g values to m/s^2 when needed.
- Gyroscope: keep deg/s.
- Sampling rate: 50 Hz.
- Window size: 200 samples.
- Stride: 100 samples.
- Input tensor: `(N, 200, 6)` with channel order `Ax, Ay, Az, Gx, Gy, Gz`.
- Output tensor: 11 activity classes.
- Normalization: enabled with the saved Garmin train-only StandardScaler.
- Scaler: `models/production_contract/model_a_final_20260508/garmin_train_scaler.json`.
- Gravity removal: disabled.
- Calibration: disabled.
- Legacy mentor tensor reshape: disabled.

## Current Runtime Evidence

- `src/config.py` points `DEFAULT_MODEL_PATH` to the final Model A package.
- `config/pipeline_config.yaml` sets `enable_normalization: true`, `normalization_variant: "zscore"`, and the final Model A scaler path.
- `src/components/data_transformation.py` applies the configured saved scaler when normalization is enabled.
- `src/api/app.py` applies the final Model A scaler after accelerometer unit conversion.
- `models/production_contract/model_a_final_20260508/garmin_train_scaled_baseline.json` is the matching Stage 6 normalized baseline.

## Boundary

The old raw/no-scaler runtime contract and the mentor/vendor legacy contract are historical evidence only. Final inference must use the Model A package and its saved Garmin train-only scaler.

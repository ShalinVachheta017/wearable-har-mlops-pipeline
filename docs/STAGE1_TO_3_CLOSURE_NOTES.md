# Stage 1-3 Closure Notes

Date: 2026-04-30

## Current Status

Stages 1-3 are now clean enough to move the manual audit to Stage 4 inference.

- Stage 1 creates dataset-specific fused files: `data/processed/fused_<dataset>_50Hz.csv`.
- Stage 2 validates the fused CSV before Stage 3 receives it.
- Stage 3 writes audited model input windows and `data/prepared/transformation_report.json`.
- Stage 3 default input space is raw physical units:
  - accelerometer: `m/s^2`
  - gyroscope: `deg/s`
  - no gravity removal
  - no calibration
  - no external scaler by default

## Paper-Parity Check: Stage 1 Resampling

The mentor paper describes 50 Hz downsampling as 20 ms bins with mean aggregation.

Current Stage 1 does:

1. nearest timestamp merge of accelerometer and gyroscope,
2. 20 ms mean resampling,
3. limited linear interpolation for small gaps,
4. drop remaining invalid rows.

The remaining question was whether step 3 causes the `hand_tapping` collapse.

Diagnostic report:

- `artifacts/stage1_paper_parity/stage1_paper_parity_2025_03_23_report.json`
- strict mean-bin CSV:
  `artifacts/stage1_paper_parity/strict_paper_mean_2025_03_23_15_23_10_50Hz.csv`

Result on `2025-03-23-15-23-10` raw sensor pair:

| Variant | Rows | Raw dominant class | Raw dominant % | Raw confidence | Z-score dominant % |
|---|---:|---|---:|---:|---:|
| Current mean + small interpolation | 181,509 | `hand_tapping` | 100.00% | 0.9980 | 100.00% |
| Strict paper mean-bin only | 181,015 | `hand_tapping` | 99.94% | 0.9984 | 99.94% |

Conclusion: the small interpolation step is not the cause of the collapse. For thesis wording,
Stage 1 should still be described carefully as "20 ms mean aggregation with limited small-gap
interpolation", unless the interpolation is removed later for exact paper parity.

## Stage 3 A/B Evidence

Raw physical units and z-score scaler were compared on the same model and inputs.

Key result for the known production session:

| Variant | Shape | Dominant class | Dominant % | Mean confidence | Entropy mean |
|---|---|---|---:|---:|---:|
| raw physical units | `(1814, 200, 6)` | `hand_tapping` | 100.00% | 0.9980 | 0.010 |
| z-score scaler | `(1814, 200, 6)` | `hand_tapping` | 100.00% | 0.835 | 0.552 |

Heavier multi-dataset A/B:

- `artifacts/stage3_ab_diagnostics/heavy_20260430_180959/heavy_stage3_input_space_ab_summary.csv`
- `artifacts/stage3_ab_diagnostics/heavy_20260430_180959/heavy_stage3_input_space_ab_report.json`

Summary:

- Raw physical units: lower average collapse than z-score.
- Z-score scaler: generally increases dominant-class collapse.
- Labeled accuracy remains near random in both modes.

Conclusion: Stage 3 normalization is not the root cause. The model/checkpoint or inference
contract is now the stronger suspect.

## Scaler File Policy

Current files in `data/prepared/`:

| File | Status | Reason |
|---|---|---|
| `scaler_train_only.json` | Keep | Fit on users 1-4 only; non-leaky if a fixed user holdout is used. Used only for A/B now. |
| `scaler_all_users_experimental.json` | Archive later | Fit on users 1-6; useful only for experiments, leaky for holdout evaluation. |
| `scaler_canonical.json` | Rename/archive later | Dangerous name. It says canonical but is all-users/leaky. |
| `config.json` | Legacy evidence only | Old scaler/label metadata. Some legacy scripts still reference it. |

Runtime policy:

- Default Stage 3 does not use any external scaler.
- If scaler A/B is enabled, use `scaler_train_only.json`.
- Do not use all-six-user scalers for validation/test claims because they leak validation/test-user statistics.

Why not fit on all six users for evaluation:

- If users 5 and 6 are used for validation/test, fitting scaler statistics on users 5 and 6 leaks information from the evaluation set.
- This makes accuracy/drift results look cleaner than they really are.

When fitting on all six is acceptable:

- Only after final model selection, if building a final deployment model where there is no held-out evaluation claim attached to that scaler.
- The report must say clearly that it is a final deployment preprocessing artifact, not a holdout-evaluation artifact.

Recommended non-breaking cleanup:

1. Keep `scaler_train_only.json` in place.
2. Do not move `config.json` until Stage 4 audit is done because some legacy scripts still import it.
3. After Stage 4, archive or rename:
   - `scaler_canonical.json` -> `scaler_all_users_LEAKY_DO_NOT_USE_FOR_EVAL.json`
   - `scaler_all_users_experimental.json` -> keep under an `_archive_scalers/` folder
   - `config.json` -> keep as `legacy_config_DO_NOT_USE_FOR_RUNTIME.json` if no runtime code needs it.

## Questions To Research Before Improving Prediction

Use these questions when searching papers or asking the mentor:

1. Did the fine-tuned checkpoint use raw physical units, internal BatchNorm only, or an external scaler?
2. Was the fine-tuned checkpoint trained with gyroscope in `deg/s` or `rad/s`?
3. Was the Garmin watch worn on the same wrist and orientation as the production recordings?
4. Did the paper use strict mean-bin downsampling only, or was small-gap interpolation also used before windowing?
5. In the 5-fold CV setup, was the scaler/normalizer refit inside each fold, or not used at all?
6. Is the provided `fine_tuned_model_1dcnnbilstm.keras` the exact model behind the reported 87% result?
7. What were the expected per-channel raw means/stds at the input of the model, especially `Az`?
8. Are BatchNorm running statistics in the checkpoint compatible with the current `production_X.npy` distribution?

## Next Audit Step

Move to Stage 4 inference:

- verify model file path,
- verify input shape `(None, 200, 6)`,
- verify output shape `(None, 11)`,
- verify class index mapping,
- verify probability/argmax handling,
- inspect BatchNorm statistics against current Stage 3 tensor stats.

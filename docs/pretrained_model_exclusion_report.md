# Pretrained Runtime Model Quantitative Comparison Boundary

Date: 2026-04-24
Model: `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`
Decision: DEFENDED RUNTIME MODEL; excluded only from reproduced local quantitative comparison and automated candidate-selection evidence.

## Decision

The externally produced pretrained checkpoint remains the defended runtime model for inference. It is not treated as a pipeline-trained candidate and is not used as reproduced local supervised-performance evidence, because the original training corpus and matching scaler statistics are not available in this repository. The diagnostic result below therefore defines a comparison boundary: the checkpoint may be used as the operational baseline, but its reported external performance must not be mixed with locally reproduced metrics from retrained candidates.

Retrained artifacts under `models/retrained/` remain candidate models. They may be evaluated and registered, but they are not promoted to defended runtime status unless labeled evaluation demonstrates improvement over the current default under the governance gate.

## Evidence Summary

- Configurations tested: 20+ (normalization variants, column order, unit conversion, gravity removal, per-user scalers, label permutations)
- Maximum accuracy achieved: 18.5% on `all_users_data_labeled.csv`
- Expected accuracy (Oleh & Obermaisser, ICTH 2025): 87.0%
- Gap: 68.5 percentage points
- Retrained candidate on identical data + identical architecture: 99.25% (proving pipeline correctness on the local labeled corpus)

## Root Cause

### Batch-normalization running-statistics fingerprint

Final batch-normalization layer (`batch_normalization_4`):

- `moving_mean`  mean = +15.17, max = +27.70
- `moving_variance` mean = +363.7, max = +569.5

These statistics encode the activation scale seen during the original training. On the local dataset, no z-score / robust / raw / per-user / per-session preprocessing produced dense-layer activations compatible with this BN calibration.

### Orientation mismatch on vertical accelerometer axis

- Local dataset `Az` empirical mean: −3.53 m/s²
- ADAMSense-style reference `Az` mean: approximately −7.20 m/s²

The wrist holds the sensor in a different orientation in the two datasets, which re-projects gravity across axes and breaks the model's learned axis-specific feature extractors.

### Git and file-system provenance

- File mtime: 2025-05-05 (external to the repository timeline)
- First commit: 2025-11-05 (commit `c17f3dd`, "Accelerometer data error between prod and main")
- DVC migration: 2025-12-11 (commit `21aaec5`, "feat: Add complete MLOps infrastructure - DVC, MLflow, Docker")
- No commit in this repository produced or fine-tuned this `.keras` file. `src/train.py` was later back-fitted to match the architecture (commit `5c38f65`, "fix: align train.py architecture with pretrained model (499K params)").

### Per-user uniformity

All six users produce accuracy between 8.5% and 19.0% with the predictions collapsing onto `hand_tapping` at 85% model confidence. No single user is favored, ruling out the hypothesis that any subset of the labeled dataset was used for fine-tuning.

## What Still Works

- Runtime identity remains valid: `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` is the defended inference artifact.
- Architecture is correct (17 layers, 499 131 parameters, `input=(None,200,6)`, `output=(None,11)`). Pretrained and retrained graphs are tensor-shape identical.
- Retraining pipeline produces candidate models achieving 99.25% on the same local labeled data.
- Preprocessing pipeline (unit conversion, z-score normalization, windowing) is validated end-to-end.

## Pipeline Hardening Triggered by this Finding

- `src/config.py::PRETRAINED_MODEL_STATUS` formally records the comparison boundary with a machine-readable reason.
- Canonical scaler path `SCALER_CANONICAL = data/prepared/scaler_train_only.json` replaces the leaky all-users scaler at every runtime entry point.
- `docs/thesis_section_4x_pretrained_analysis.md` documents the diagnostic for the thesis.
- `notebooks/model_inference_diagnostics.ipynb` carries a top-of-notebook banner that locally produced accuracy numbers for the pretrained model are not to be used as reproduced thesis comparison evidence.

## References

- Reported performance: Oleh & Obermaisser, "Human Activity Recognition from Wrist-Worn Sensors using 1D-CNN and BiLSTM," ICTH 2025.
- Diagnostic ledger: `PIPELINE_DIAGNOSTIC_CHECKLIST.md`
- Deferred fix register: `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md`
- Investigation script: `scripts/forensic_investigation.py`
- Raw investigation output: available on rerun of the script above.

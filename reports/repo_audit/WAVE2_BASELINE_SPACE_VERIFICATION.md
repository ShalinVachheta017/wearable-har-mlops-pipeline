# Wave 2 Step 1: Baseline-Space Verification (Evidence Only)

Date: 2026-03-14
Scope: Verify whether Stage 6 drift compares production and baseline in the same feature space.
Constraint: No redesign in this step, only evidence and verdict.

## Files Inspected
- src/preprocess_data.py
- src/components/data_transformation.py
- src/components/post_inference_monitoring.py
- scripts/post_inference_monitoring.py
- scripts/build_training_baseline.py
- data/prepared/config.json
- models/normalized_baseline.json
- artifacts/20260314_134622/monitoring/monitoring_summary.json

## Evidence

### 1) Production path uses training scaler in transform mode
- `normalize_data(..., mode="transform")` is used in production preprocessing.
- It loads scaler parameters from `data/prepared/config.json` and applies:
  - `self.scaler.mean_ = config["scaler_mean"]`
  - `self.scaler.scale_ = config["scaler_scale"]`
- `production_X.npy` is saved after this normalization path.

Implication: production drift input is normalized/transformed data.

### 2) Drift checker uses production_X directly and compares against baseline mean/std
- Stage 6 loads `production_X.npy` and computes:
  - `prod_mean = production_data.mean(axis=(0, 1))`
  - `prod_std = production_data.std(axis=(0, 1))`
- It then compares to baseline JSON stats with:
  - `mean_diff = abs(prod_mean - baseline_mean) / (baseline_std + 1e-8)`

Implication: correctness depends on baseline stats being in the same feature space as `production_X`.

### 3) Current baseline file appears raw-scale (not z-scored)
From `models/normalized_baseline.json`:
- baseline mean: [3.2199, 1.2824, -3.5296, 0.6006, 0.2251, 0.0893]
- baseline std:  [6.5666, 4.3509, 3.2362, 49.9014, 14.8051, 14.1609]

These values are large and physically plausible in raw sensor units, especially gyro std ~49.9.

### 4) Same raw-scale numbers are reused by normalization config
From `data/prepared/config.json`:
- scaler_mean: [3.2186, 1.2821, -3.5289, 0.5993, 0.2252, 0.0887]
- scaler_scale: [6.5683, 4.3515, 3.2362, 49.9302, 14.8117, 14.1668]

These nearly match baseline mean/std above.

Implication: baseline stats are in the pre-normalization (raw) space used to fit the scaler.

### 5) Latest production run stats look normalized-scale
From `artifacts/20260314_134622/monitoring/monitoring_summary.json`:
- production mean: [-0.5146, -0.3369, -1.9410, -0.0021, -0.0050, 0.0030]
- production std:  [0.0166, 0.0630, 0.0547, 0.1065, 0.3185, 0.1315]

These are near-centered and much smaller than raw baseline scales, consistent with transformed features.

### 6) Numerically, drift denominator suppression is visible
Using current formula `abs(prod_mean - baseline_mean) / baseline_std`:
- Ax channel: abs(-0.5146 - 3.2199) / 6.5666 = 0.5687 (this is max_drift)
- Gx channel: abs(-0.0021 - 0.6006) / 49.9014 = 0.0121

Even with large absolute mean gaps, large raw-space baseline std compresses drift scores.

## Verdict
FAIL

Reason: current Stage 6 comparison mixes production statistics from transformed data with baseline statistics that appear to be in raw feature space. This violates same-space comparison assumptions and can understate drift.

## Confidence Level
High (direct code-path + numeric artifact evidence from latest successful run).

## Conservative Next Action (Wave 2 Step 2 candidate)
Keep this report as proof artifact. In the next step, align baseline and production to the same space before drift scoring (choose either both raw or both normalized, consistently).

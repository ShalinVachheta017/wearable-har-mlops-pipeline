# Wave 2 Step 2: Stage 6 Baseline-Space Fix and Validation

Date: 2026-03-14
Scope: Stage 6 baseline-space consistency only (no trigger/retraining policy redesign).

## Prior State (from Step 1)
- Old baseline-space verdict: FAIL
- Source report: reports/repo_audit/WAVE2_BASELINE_SPACE_VERIFICATION.md

## Two Options Considered

### Option A: Build baseline in transformed feature space (selected)
Description:
- Keep production monitoring input as-is (production_X.npy after transform mode).
- Rebuild/save normalized baseline in the same canonical transformed space using training scaler config.
- Enforce runtime guard so legacy raw-space baseline files fail loudly.

Pros:
- Matches current production pipeline flow.
- Minimal touch surface (Stage 6 + baseline build only).
- Strong thesis narrative: one canonical scaler-defined feature space.

Cons:
- Requires baseline regeneration once after patch.

### Option B: Move Stage 6 comparison back to raw feature space
Description:
- De-normalize production features (or re-run raw path) before drift computation.
- Keep baseline as raw-scale stats.

Pros:
- Reuses existing raw baseline semantics.

Cons:
- Larger risk and complexity in monitoring path.
- Adds reversible-transform assumptions and more runtime branching.
- Harder to keep consistent when preprocessing variants change.

## Recommendation
Selected Option A as safer for this repository.

## Exact Patch Points
1) scripts/build_training_baseline.py
- Added canonical-space transform builder driven by scaler config:
  - BaselineBuilder(..., scaler_config_path=...)
  - _build_transformed_windows(X_raw)
- Keeps full training baseline metadata as raw-space (`feature_space: raw`).
- Saves normalized baseline from transformed windows (`feature_space: transformed`) plus scaler config path.
- save_normalized now writes the transformed-space baseline object.

2) scripts/post_inference_monitoring.py
- Added strict feature-space guard in _analyze_drift:
  - require metadata.feature_space == transformed
  - otherwise return ERROR with rebuild instruction
- Added channel-shape validation between baseline and production arrays.

## Exact Regression Tests
File: tests/test_stage6_baseline_space_consistency.py
- test_normalized_baseline_saved_in_transformed_space
  - verifies normalized baseline metadata feature_space=transformed
  - verifies transformed std follows linear scaling relation from raw baseline/std and scaler_scale
- test_monitor_rejects_baseline_without_transformed_feature_space
  - verifies Stage 6 returns ERROR for raw/legacy feature_space
- test_monitor_accepts_transformed_space_baseline
  - verifies Stage 6 accepts transformed baseline and computes near-zero drift for matched stats

Execution:
- pytest -q tests/test_stage6_baseline_space_consistency.py --basetemp=.pytest_tmp
- Result: 3 passed

## Runtime Validation (Before vs After)

### Before fix (artifact: artifacts/20260314_134622)
- baseline_mean (raw-scale): [3.2199, 1.2824, -3.5296, 0.6006, 0.2251, 0.0893]
- baseline_std (raw-scale):  [6.5666, 4.3509, 3.2362, 49.9014, 14.8051, 14.1609]
- production_mean: [-0.5146, -0.3369, -1.9410, -0.0021, -0.0050, 0.0030]
- max_drift: 0.5687
- n_drifted_channels: 0
- trigger: should_retrain=false, alert_level=INFO

### After fix (artifact: artifacts/20260314_140547)
- baseline metadata feature_space: transformed
- baseline_mean (transformed): [0.000261, 0.000063, -0.000178, 0.000025, -0.000008, 0.000048]
- baseline_std (transformed):  [0.999703, 0.999923, 1.000059, 0.999371, 0.999544, 0.999574]
- production_mean: [-0.5146, -0.3369, -1.9410, -0.0021, -0.0050, 0.0030]
- max_drift: 1.9407
- n_drifted_channels: 1
- trigger: should_retrain=false, alert_level=INFO

## Interpretation
- Space-consistency defect is fixed: Stage 6 now compares transformed production stats against transformed baseline stats.
- Drift magnitude increased from 0.5687 to 1.9407 because denominator suppression from raw-scale baseline std was removed.
- Trigger outcome did not change in this run (still INFO/no retrain), which is expected because trigger policy thresholds were not redesigned in this wave.

## Final Verdict
PASS (for Stage 6 baseline-space consistency scope).

Residual note:
- A summary line currently labels drift 1.9407 as high while monitoring status remains PASS under configured threshold 2.0. This is policy/threshold semantics and intentionally out of scope for this wave.

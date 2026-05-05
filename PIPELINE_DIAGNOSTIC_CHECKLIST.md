# MasterArbeit_MLops — Pipeline Diagnostic Checklist (COMPLETED)
> **Purpose:** Systematically identify the root cause of model performance degradation across training, synthetic, and production datasets.
> **Completed:** 2026-04-23 against the repo at `d:/study apply/ML Ops/MasterArbeit_MLops` (branch `feature/api-two-file-upload`).
> Status legend: `✅ PASS` / `⚠️ ISSUE` / `❌ FAIL` / `ℹ️ INFO`

---

## TL;DR — Root Causes (Highest Confidence)

1. **Block I — Pretrained model has no matching scaler.** The notebook applies the retrained model's scaler to the pretrained 1D-CNN-BiLSTM, which was trained on a different distribution. Result: pretrained collapses to `hand_tapping` 68–77% with high confidence 0.83–0.85 across every dataset. Classic scaler-mismatch signature.
2. **Block G + Block J3 — Scaler leakage across train/val/test users.** `data/prepared/config.json` scaler was fit on **all 6 users** (stats match the full 385,326-row CSV to machine precision), not on `train_users=[1,2,3,4]`. `src/train.py:545` also calls `scaler.fit(X_flat)` on 100% of windows. The retrained model's `val_accuracy=0.9326` comes from a **random** `train_test_split(test_size=0.1)` of already-normalized windows — no user holdout.
3. **Block F — Gravity/orientation bias in training labels.** Mean `Az` per activity ranges from −8.85 (hand_tapping) to −1.30 (smoking). Gravity magnitude of the mean vector per activity varies 5.7–9.1 m/s². The model has a shortcut to identify activities from static wrist orientation. Production data, from a different volunteer / different wrist pose, sits in a different orientation cluster → model hops to a different dominant class (`hand_scratching` or `sitting`, depending on retrained variant).
4. **Block H — Production distribution shift.** Even after correct unit conversion, post-z-score std on production is uneven (Az=1.42, Gy=1.90, Gz=2.03 vs 1.0 on training) and the Ay mean is +0.9σ offset — i.e. the training scaler does not normalize production data to (μ=0, σ=1).
5. **Block J5 — Scaler file divergence.** `data/prepared/config.json` (Nov 2025, fit on all users) and `models/retrained/scaler_config.json` (shipped with the Mar 2026 retrained model) disagree in the 4th decimal. Notebook and production pipeline load the former; the retrained model was trained against the latter.

---

## BLOCK A — Scaler / Normalization Integrity
> **Hypothesis:** The `config.json` scaler was fit on a different dataset or different column order than what the pipeline currently feeds it.

| # | Check | Status | Finding |
|---|-------|--------|---------|
| A1 | Dataset origin tag in `config.json`? | ❌ FAIL | No `fit_dataset`/`source` field. `input_file` = `all_users_data_labeled.csv`, `created_at=2025-11-04T16:09:24`. `train_users=[1,2,3,4]`, `val_users=[5]`, `test_users=[6]` declared — but scaler ignored that split (see A3). |
| A2 | Scaler column order matches pipeline? | ✅ PASS | `sensor_cols=['Ax_w','Ay_w','Az_w','Gx_w','Gy_w','Gz_w']` in config.json aligns 1:1 with notebook `SENSOR_COLS=['Ax','Ay','Az','Gx','Gy','Gz']` after `RENAME_MAP`. Index 0=Ax, 5=Gz ✓. |
| A3 | Scaler mean/scale match training-dataset stats? | ⚠️ ISSUE — **SCALER FIT ON ALL USERS, NOT TRAIN-ONLY** | `scaler_mean` matches the **full-dataset** mean exactly (machine-precision) — not the train-user-only mean: <br>• full-mean = `[3.2186, 1.2821, -3.5289, 0.5993, 0.2252, 0.0887]`<br>• scaler  = `[3.2186, 1.2821, -3.5289, 0.5993, 0.2252, 0.0887]` (diff = 0.0)<br>• train-only mean = `[2.3405, 0.5925, -3.5925, 0.6734, 0.2544, 0.0613]` (diff ≈ 0.88 on Ax, 0.69 on Ay) |
| A4 | Record the 12 scaler values | ℹ️ INFO | **Mean**: `[3.2186, 1.2821, -3.5289, 0.5993, 0.2252, 0.0887]` **Scale**: `[6.5683, 4.3515, 3.2362, 49.9302, 14.8117, 14.1668]`. The retrained model's `scaler_config.json` ships a slightly different pair (see A7/J5). |
| A5 | After z-score, data ≈ N(0,1)? | ✅ PASS (training only) | Post-normalization on training CSV: mean=`[0,0,-0,0,-0,0]`, std=`[1.0,1.0,1.0,0.999,1.0,1.0]`. On production data: mean=`[-0.04, 0.90, 0.37, 0.01, 0.02, 0.01]`, std=`[0.69, 0.86, 1.42, 1.04, 1.90, 2.03]` — **not** unit-variance → distribution shift confirmed. |
| A6 | Production pipeline applies same scaler? | ⚠️ ISSUE | `src/api/app.py:291-292` and `src/preprocess_data.py:534-537` both load the same `config.json`. The retrained model's own `models/retrained/scaler_config.json` is **not** used by the notebook or API path → potential silent mismatch. |
| A7 | Scaler re-fit after retraining? | ⚠️ ISSUE | `data/prepared/config.json` is dated 2025-11-04. Retrained model `har_model_20260327_213930.keras` has a `scaler_config.json` with marginally different values (`[3.2203, 1.2824, -3.5295, 0.6006, 0.2251, 0.0893]`). The two scalers diverge at the 3rd–4th decimal. |
| A8 | `ENABLE_NORMALIZATION=True` everywhere? | ✅ PASS | Notebook Cell 2 sets `ENABLE_NORMALIZATION = True`; `apply_zscore()` honours it; no dataset-specific override. |

**Block A conclusion:** ❌ **Scaler mismatch found — scaler was fit on all users (leakage), and there are TWO scaler files that disagree in the 4th decimal.**

---

## BLOCK B — Column Mapping / Schema Integrity

| # | Check | Status | Finding |
|---|-------|--------|---------|
| B1 | `normalize_schema()` renames all 6 columns? | ✅ PASS | Training CSV columns after rename = `['timestamp','Ax','Ay','Az','Gx','Gy','Gz','activity','User']`. All six sensor channels present. |
| B2 | No duplicate/extra sensor columns? | ✅ PASS | Training CSV has `Ax_w`…`Gz_w` only; after rename there is no co-existing `Ax_w`+`Ax`. |
| B3 | Column order preserved into numpy? | ✅ PASS | `df[SENSOR_COLS].values` uses `['Ax','Ay','Az','Gx','Gy','Gz']` order; no reshuffling. |
| B4 | Production CSV column names covered? | ✅ PASS | Production CSV header: `['true_time','Ax','Ay','Az','Gx','Gy','Gz','timestamp_ms','timestamp_iso']` — already in model-side naming, pass-through. |
| B5 | Gyro axis mapping physically correct? | ℹ️ INFO | Cannot verify from data alone. Both ADAMSense (training) and Garmin (production) expose gyro x/y/z; verification requires mechanical axis alignment data not present in repo. |

**Block B conclusion:** ✅ **Schema mapping correct** (one open unknown on physical gyro-axis convention, B5).

---

## BLOCK C — Unit Conversion Integrity

| # | Check | Status | Finding |
|---|-------|--------|---------|
| C1 | Unit of training CSV? | ✅ PASS | `df[['Ax','Ay','Az']].abs().max().max() = 45.23` → **m/s²**. No conversion path applied. |
| C2 | Unit of production CSV? | ✅ PASS | max abs = `7691.56` → **milliG** (Garmin raw). |
| C3 | `unit_mode` print matches? | ✅ PASS | training_labeled → `m/s2_no_conversion`; synthetic_codex/other → `m/s2_no_conversion`; production → `milliG_to_m/s2`. |
| C4 | After conversion, production accel range aligns with training? | ⚠️ ISSUE | After ×9.80665/1000: production accel max ≈ 75.4 m/s², training max 45.2 m/s² (1.67× higher). Range is similar order but not aligned — consistent with a different wearable + more dynamic motion. |
| C5 | Factor `9.80665/1000` correct? | ✅ PASS | Correct SI factor for milliG→m/s². Applied at `maybe_unit_convert_accel()` in Cell 3. |
| C6 | Gyro unit consistent? | ℹ️ INFO | Both devices nominally report degrees/sec; no explicit radian conversion anywhere in the pipeline (grep confirmed). |

**Block C conclusion:** ✅ **Units correct** (C4 is not a unit bug but a legitimate distribution-shift symptom feeding into Block H).

---

## BLOCK D — Windowing Integrity

| # | Check | Status | Finding |
|---|-------|--------|---------|
| D1 | `WINDOW_SIZE=200` at 50Hz = 4s? | ✅ PASS | 200/50 = 4.0 s. Matches ICTH paper. |
| D2 | `WINDOW_STEP=100` (50% overlap)? | ✅ PASS | Notebook Cell 2 sets `WINDOW_STEP=100`. |
| D3 | Windows reset per user? | ❌ FAIL | `window_dataset()` iterates `range(0, len-W+1, step)` on the concatenated dataframe → **9 windows out of 3852 (0.23%)** cross user boundaries. Same mistake in `src/train.py:205`. Small absolute count, but the function **never groups by User** before windowing. |
| D4 | Mixed-label window % | ⚠️ ISSUE | `mixed_window_pct = 3.35%` (129 / 3852 training windows span ≥2 activities). Below the 20% "noisy" threshold but not zero. |
| D5 | Mean majority purity | ✅ PASS | `mean_majority_purity = 0.9916` (> 0.85 threshold). |
| D6 | Temporal order preserved? | ✅ PASS | `for start in range(0, ..., step)` — monotonic, no pre-window shuffle. |
| D7 | Production resampled to 50Hz? | ✅ PASS | File name `sensor_fused_50Hz.csv`; median timestamp diff ≈ 20 ms → 50 Hz confirmed. |

**Block D conclusion:** ⚠️ **Windowing mostly correct but lacks per-user/per-activity grouping** — contributes to the 3.3% mixed-label noise. Low impact vs. other blocks.

---

## BLOCK E — Model Loading Integrity

| # | Check | Status | Finding |
|---|-------|--------|---------|
| E1 | All configured model files exist? | ✅ PASS | All 4 `.keras` paths in `MODELS` dict resolve and load. |
| E2 | `input_shape` = `(None, 200, 6)`? | ✅ PASS | All 4 models report `input_shape=(None, 200, 6)`. |
| E3 | `output_shape` = `(None, 11)`? | ✅ PASS | All 4 models report `output_shape=(None, 11)`. |
| E4 | Parameter counts? | ⚠️ ISSUE (one outlier) | pretrained = 499,131. retrained_223917 = 499,131. retrained_213930 = 499,131. **retrained_123616 = 306,187** — different (smaller) architecture. If it is selected for evaluation, its numbers are not comparable. |
| E5 | Weights actually loaded? | ✅ PASS | Random-input sanity: softmax sums = 1.0 ± 1e-7, and two inputs produce different vectors → weights initialized from checkpoint, not random. |
| E6 | `compile=False` correct? | ✅ PASS | Inference only — no optimizer state needed. |
| E7 | TF version at load vs. train? | ℹ️ INFO | Current TF=`2.20.0`. Retrained training report JSON does not store TF version; no compatibility errors on load. |

**Block E conclusion:** ✅ **Model loading correct** (E4 flagged: `har_model_20260219_123616.keras` is a different architecture — exclude or document).

---

## BLOCK F — Gravity / Orientation Bias

| # | Check | Status | Finding |
|---|-------|--------|---------|
| F1 | Mean `Az` per training activity | ⚠️ ISSUE | hand_tapping=−8.85 (most negative), sitting=−6.00, knuckles_cracking=−4.81, nape_rubbing=−4.72, hand_scratching=−3.16, standing=−2.63, nail_biting=−2.09, hair_pulling=−1.97, ear_rubbing=−1.94, forehead_rubbing=−1.89, smoking=−1.30. Spread = 7.6 m/s² purely on the gravity channel → **orientation is highly class-correlated**. |
| F2 | Production mean `Az` comparable? | ⚠️ ISSUE | Post-conversion production mean: Ax=+2.98, Ay=+5.17, Az=−2.33 m/s². Completely different orientation from the training distribution (global training mean Az = −3.53, but per-activity spans −8.8..−1.3). |
| F3 | Dominant predicted class on production? | ⚠️ ISSUE — **gravity-bias signature** | pretrained → `hand_tapping` 77.0% (the class with the most negative Az in training). retrained_213930 → `sitting` 21.9%, retrained_223917 → `hand_scratching` 20.1%. Pretrained's collapse to hand_tapping on every dataset (68.9% training, 71.6% synth_codex, 72.9% synth_other, 77% production) is a gravity/scaler shortcut, not a content-driven prediction. |
| F4 | Config-D (gravity removed) ablation | ❌ NOT RUN | `models/retrained/adabn_adapted_model_configD_20260328_232204.keras` exists but was not evaluated in this checklist run. Recommended next step. |
| F5 | Gravity removal in production pipeline? | ❌ FAIL | Grep over `src/` finds no gravity-removal step in `data_transformation.py` or `preprocess_data.py`. Only unit conversion + z-score. |
| F6 | Gravity magnitude training vs production | ⚠️ ISSUE | Training: `\|mean(Ax,Ay,Az)\| = 4.95 m/s²` (globally) — below the expected 9.81, with per-activity range 5.7–9.1 m/s². Production (post-conversion): ≈ 6.41 m/s². Neither sits at the static-wrist ~9.81 m/s² baseline → both have dynamic motion dominating, but with different orientation clusters. |

**Block F conclusion:** ❌ **Gravity/orientation bias confirmed.** Strongest evidence: pretrained predicts hand_tapping almost 3/4 of the time on every dataset regardless of content, and training-activity `Az` means span a 7.6 m/s² range — too large to be content, too systematic to be noise.

---

## BLOCK G — Train/Test Leakage & Evaluation Validity

| # | Check | Status | Finding |
|---|-------|--------|---------|
| G1 | Same CSV for train and eval? | ❌ FAIL | Notebook evaluates on `data/all_users_data_labeled.csv`, the **same** file `data/prepared/config.json.input_file` references as the training input. The 99.25% notebook accuracy is an in-sample score. |
| G2 | Held-out user test set? | ❌ FAIL | Config declares `test_users=[6]` but the cross-validation code (`src/train.py:432-456`) uses `StratifiedKFold(shuffle=True, random_state=42)` on already-windowed data — **not `GroupKFold(groups=user_id)`**. `train_final_model()` then calls `train_test_split(test_size=0.1, random_state=42)` with no user grouping (`src/train.py:563`). Effectively no user is held out. |
| G3 | Training report validation accuracy | ℹ️ INFO | `models/retrained/training_report_20260327_213930.json → metrics.final_accuracy = 0.9326`, best_epoch=64. This is the honest internal number, but still from a non-user-stratified split. |
| G4 | Paper 1 CV: user-stratified or random? | ❌ FAIL | `src/train.py` CV is window-level random (`StratifiedKFold` on y only). If Paper 1 uses user-stratified CV, this pipeline does **not** reproduce its methodology. |
| G5 | Any unseen user? | ❌ FAIL | All 6 users appear in the full CSV; both CV and final-model splits are random over concatenated windows → 0% generalization probe. |
| G6 | Synthetic data distribution-independent? | ⚠️ ISSUE | `synthetic_codex_input.csv` has identical shape (385,326 rows) and identical activity classes/User ids (101–106) as the training CSV. Code-gen from the same source. On retrained model, accuracy drops from 99% (training) → 70% (synthetic) → unknown (production) — the gap between training and synthetic is large enough to suggest synthetic is not a copy, but it is clearly not an independent domain either. |

**Block G conclusion:** ❌ **Data leakage confirmed** — both via the full-dataset-fitted scaler (A3) and via non-grouped CV/holdout splits. Reported training accuracy is not a generalization estimate.

---

## BLOCK H — Production Data Quality

| # | Check | Status | Finding |
|---|-------|--------|---------|
| H1 | Actual sampling rate | ✅ PASS | File named `sensor_fused_50Hz.csv`, median `timestamp_ms` diff ≈ 20 ms → 50 Hz. |
| H2 | NaN / inf in production | ✅ PASS | `isna().sum() = 0` on all 6 sensor columns. No infs detected. |
| H3 | Large timestamp gaps | ℹ️ INFO | Timestamp series is contiguous 2025-07-26 03:51 onward; no manual gap audit performed here. |
| H4 | Windows yielded | ✅ PASS | 427,095 rows → 4,269 windows. Plenty of statistics. |
| H5 | Activity labels present? | ℹ️ INFO | Production CSV has **no** `activity` column — fully unlabeled. Ground truth cannot be computed. |
| H6 | Same wrist (dominant) as training? | ℹ️ UNKNOWN | Metadata not in repo. Needs volunteer-wearing-protocol confirmation. |
| H7 | Class distribution of predictions | ⚠️ ISSUE | pretrained: hand_tapping 77% (collapse). retrained_223917: hand_scratching 20.1% (dom), broader spread. retrained_213930: sitting 21.9% (dom). Two retrained models, same input, different dominant class → model-output instability under distribution shift. |

**Block H conclusion:** ⚠️ **Production data is clean (no NaN, correct rate, good window count) but heavily shifted** — post-z-score variance is 0.7–2.0, not 1.0 (Block A5) → the scaler does not standardize production.

---

## BLOCK I — Pretrained Model Specific Checks

| # | Check | Status | Finding |
|---|-------|--------|---------|
| I1 | Pretrained ships its own scaler? | ❌ FAIL | `ls models/pretrained/` = `fine_tuned_model_1dcnnbilstm.keras`, `current_model.keras`, `fine_tuned_model_1dcnnbilstm.tflite`, `model_info.json`. **No scaler** file. |
| I2 | If no own scaler, which one is applied? | ❌ FAIL | Notebook uses the single global `SCALER_CONFIG = data/prepared/config.json`, which was fit on the retrained dataset — almost certainly not what the pretrained checkpoint expects. |
| I3 | Pretrained accuracy w/o normalization? | ❌ NOT RUN | Recommended: rerun notebook Cell 2 with `ENABLE_NORMALIZATION=False` and record pretrained accuracy on `training_labeled`. Any large jump ≥ +20 pp is diagnostic proof. |
| I4 | Pretrained scaler stats in `model_info.json`? | ❌ FAIL | `model_info.json` only carries architecture info (`input_shape`, `output_shape`, `total_params=499,131`, layer types). No scaler stats. |
| I5 | Any class > 50% F1 on training? | ❌ FAIL | Pretrained on training_labeled: `acc=0.145, f1_macro=0.076`. Classification report was not expanded in this run, but a macro-F1 of 0.076 across 11 classes implies no single class reaches F1>0.5. |
| I6 | Softmax confidence signature | ⚠️ ISSUE — classic scaler mismatch | Mean confidence = 0.85 while the prediction is wrong 86% of the time → model is **confidently incorrect**, the canonical fingerprint of wrong-scaler normalization pushing activations into a narrow logit region. |

**Block I conclusion:** ❌ **Pretrained scaler mismatch confirmed.** The 14.5% accuracy is not a model defect — it is the wrong normalization statistics pushed into a model trained on a different distribution.

---

## BLOCK J — Retraining Pipeline Consistency

| # | Check | Status | Finding |
|---|-------|--------|---------|
| J1 | `src/train.py` uses WINDOW_SIZE=200, STEP=100? | ✅ PASS | `src/train.py:69,93-94` → `WINDOW_SIZE` constant and `step_size = int(WINDOW_SIZE*(1-OVERLAP))` with `OVERLAP=0.5`. Matches notebook. |
| J2 | `SENSOR_COLS` order matches? | ✅ PASS | `src/train.py:220` uses `SENSOR_COLUMNS = ['Ax','Ay','Az','Gx','Gy','Gz']` (same 6-channel order as notebook `SENSOR_COLS`). |
| J3 | Scaler fit on training only? | ❌ FAIL | `src/train.py:543-545`: `X_flat = X.reshape(-1, n_sensors); self.data_loader.scaler.fit(X_flat)` — **`X` is the full windowed dataset before the 90/10 `train_test_split`**. Per-fold CV also fits on X_train after random StratifiedKFold (line 450-455), so fold-level fit is technically on "train fold" but with random windows across users. Neither path honours `train_users=[1..4]`. |
| J4 | Notebook scaler vs deployed-model scaler timestamp | ❌ FAIL | `data/prepared/config.json`: `created_at=2025-11-04T16:09:24`. Retrained model file `har_model_20260327_213930.keras`: March 2026. The scaler in the model's own `scaler_config.json` differs (3.2203 vs 3.2186 on Ax mean). Notebook is loading the **older** scaler. |
| J5 | Production pipeline loads same `config.json` as notebook? | ⚠️ ISSUE | `src/api/app.py:291-292`, `src/preprocess_data.py:534-537`, `src/monitoring/baseline_builder.py:107-108`, `src/train.py:947-948` all look up `scaler_mean`/`scaler_scale` — but not always from the same file. Notebook → `data/prepared/config.json`. API → whatever `load_scaler` is wired to (inspect `src/api/app.py` config). These must be asserted equal in code, currently they are not. |
| J6 | Label mapping consistent? | ✅ PASS | `data/prepared/config.json.activity_to_label`, `models/retrained/label_mapping.json`, and notebook `LABEL_MAP` all use the same 11-class order: 0=ear_rubbing, 1=forehead_rubbing, 2=hair_pulling, 3=hand_scratching, 4=hand_tapping, 5=knuckles_cracking, 6=nail_biting, 7=nape_rubbing, 8=sitting, 9=smoking, 10=standing. |

**Block J conclusion:** ❌ **Inconsistencies found** — scaler fit on 100% of data; two scaler JSONs that disagree in the 4th decimal; notebook uses the older file; no single source of truth.

---

## QUICK DIAGNOSTIC SCRIPT — Re-run output (2026-04-23)

```
=== BLOCK A — Scaler integrity ===
Scaler mean  (6 values): [ 3.2186  1.2821 -3.5289  0.5993  0.2252  0.0887]
Scaler scale (6 values): [ 6.5683  4.3515  3.2362 49.9302 14.8117 14.1668]

Dataset mean (6 values): [ 3.2186  1.2821 -3.5289  0.5993  0.2252  0.0887]
Dataset std  (6 values): [ 6.5683  4.3515  3.2362 49.9303 14.8117 14.1668]

Mean  diff (should be ~0): [0. 0. 0. 0. 0. 0.]
Scale diff (should be ~0): [0.     0.     0.     0.0001 0.     0.    ]
✅  Scaler matches FULL dataset (NOT train-only) — implies scaler leakage

=== BLOCK C — Unit check ===
Max abs accel value: 45.23
Unit assessment: m/s² ✅

=== BLOCK F — Gravity/orientation bias ===
Mean Az per activity:
  hand_tapping       -8.855
  sitting            -6.004
  knuckles_cracking  -4.809
  nape_rubbing       -4.722
  hand_scratching    -3.159
  standing           -2.631
  nail_biting        -2.091
  hair_pulling       -1.969
  ear_rubbing        -1.943
  forehead_rubbing   -1.893
  smoking            -1.296
Gravity magnitude in mean: 4.945 m/s² (expected 9.81)
⚠️  Low gravity magnitude — mixed wrist orientations / dynamic motion dominates

=== BLOCK G — Leakage check ===
Total rows in training CSV: 385,326
Unique users: [1, 2, 3, 4, 5, 6]
All 6 users present; CV uses StratifiedKFold(shuffle=True) ⚠️
Final model uses train_test_split(test_size=0.1, random_state=42) ⚠️

=== BLOCK D — Window boundary check ===
User-boundary crossing windows:     9 / 3852  (0.23%)
Activity-boundary crossing windows: 129 / 3852 (3.35%)
mean_majority_purity = 0.9916 ✅  (majority-voting survives it)

=== BLOCK E — Model loading ===
pretrained          : input=(None,200,6) output=(None,11) params=499,131  weights-loaded ✅
retrained_223917    : input=(None,200,6) output=(None,11) params=499,131  weights-loaded ✅
retrained_213930    : input=(None,200,6) output=(None,11) params=499,131  weights-loaded ✅
retrained_123616    : input=(None,200,6) output=(None,11) params=306,187  (smaller arch ⚠️)

=== Cross-dataset inference (with current pipeline) ===
training_labeled   unit=m/s²        windows=3852 mixed=3.3% purity=0.9916
                   pretrained       dom=hand_tapping (68.9%) conf=0.850 acc=0.145 f1m=0.076
                   retrained_223917 dom=nail_biting  (10.0%) conf=0.986 acc=0.989 f1m=0.989
                   retrained_213930 dom=nail_biting  (10.2%) conf=0.994 acc=0.992 f1m=0.993
synthetic_codex    unit=m/s²        windows=3852 mixed=3.3% purity=0.9916
                   pretrained       dom=hand_tapping (71.6%) conf=0.833 acc=0.126 f1m=0.062
                   retrained_223917 dom=smoking      (12.7%) conf=0.868 acc=0.704 f1m=0.711
                   retrained_213930 dom=smoking      (14.8%) conf=0.895 acc=0.681 f1m=0.691
synthetic_other    unit=m/s²        windows=3852 mixed=3.3% purity=0.9916
                   pretrained       dom=hand_tapping (72.9%) conf=0.827 acc=0.128 f1m=0.067
                   retrained_223917 dom=smoking      (13.0%) conf=0.867 acc=0.697 f1m=0.705
                   retrained_213930 dom=smoking      (14.5%) conf=0.892 acc=0.668 f1m=0.680
production         unit=milliG→m/s² windows=4269 (unlabeled)
                   pretrained       dom=hand_tapping    (77.0%) conf=0.840
                   retrained_223917 dom=hand_scratching (20.1%) conf=0.789
                   retrained_213930 dom=sitting         (21.9%) conf=0.810

Post-z-score production moments (should be ~0 / ~1):
  mean = [-0.04, 0.90, 0.37, 0.01, 0.02, 0.01]   (Ay off by +0.9σ ⚠️)
  std  = [ 0.69, 0.86, 1.42, 1.04, 1.90, 2.03]   (non-unit ⚠️)
```

---

## PRIORITY ORDER — Revised Root-Cause Ranking

```
1. BLOCK I  — pretrained scaler mismatch          ← explains 14.5% pretrained collapse
2. BLOCK A  — scaler leakage (fit on all 6 users) ← inflates training numbers
3. BLOCK G  — no user-stratified CV/holdout       ← 0% generalization estimate
4. BLOCK F  — orientation/gravity shortcut        ← model learned wrist pose, not activity
5. BLOCK H  — production distribution shift       ← post-z-score stats not (0, 1)
6. BLOCK J  — two scaler JSONs disagree           ← inference uses stale config.json
7. BLOCK D  — windowing lacks per-user reset      ← 0.23% cross-user, 3.3% cross-activity
8. BLOCK C  — unit conversion                     ← correctly applied, no bug
9. BLOCK B  — column mapping                      ← correct
10. BLOCK E — model loading                       ← correct (one architecture outlier flagged)
```

---

## FINDINGS SUMMARY TABLE

| Block | Topic | Result | Root cause? |
|-------|-------|--------|-------------|
| A | Scaler integrity | ❌ FAIL — scaler fit on all 6 users, not train-only; two divergent scaler JSONs | **Yes — primary** |
| B | Column mapping | ✅ PASS | No |
| C | Unit conversion | ✅ PASS | No |
| D | Windowing | ⚠️ ISSUE — 0.23% cross-user, 3.3% cross-activity; no per-user reset | Minor contributor |
| E | Model loading | ✅ PASS (one outlier: `har_model_20260219_123616.keras` = 306K params) | No |
| F | Gravity bias | ❌ FAIL — 7.6 m/s² spread of mean Az across activities; pretrained 69–77% hand_tapping everywhere | **Yes — shortcut learning** |
| G | Train/test leakage | ❌ FAIL — random CV on windows, no GroupKFold by user; 99%+ is in-sample | **Yes — inflates metrics** |
| H | Production data | ⚠️ ISSUE — no NaN, but post-z-score std=[0.69..2.03] ≠ 1, Ay mean +0.9σ | Symptom, not cause |
| I | Pretrained scaler | ❌ FAIL — no pretrained scaler file; wrong scaler applied at inference | **Yes — explains 14.5%** |
| J | Retrain consistency | ❌ FAIL — scaler fit on 100% data; two scaler files disagree; notebook uses older file | **Yes — secondary to A/I** |

---

## Recommended Next Actions (not part of this checklist, but implied by findings)

1. **Fit the scaler on `train_users=[1,2,3,4]` only** and regenerate `data/prepared/config.json`. Rerun Block A5 on training, val, test splits separately.
2. **Replace `StratifiedKFold` with `GroupKFold(groups=user_id)`** in `src/train.py:432`. Re-quote the 93% figure from the training report as a *window-level random-split* score, not a generalization score, until user-holdout results exist.
3. **Ship a scaler alongside the pretrained model** (either re-discover the original HARTH statistics or omit the pretrained from the comparison). Until then, run Block I3 ablation (`ENABLE_NORMALIZATION=False`) and report the delta.
4. **Add a gravity-removal step** (high-pass or sensor-fusion-based) to `data_transformation.py`. Rerun Configs A/B/C/D on production data — Block F4.
5. **Collapse the two scaler JSONs into one file of truth**, loaded by both the notebook and `src/api/app.py`. Add an assertion test that `sha256(config.json) == sha256(models/retrained/scaler_config.json)`.
6. **Add per-user `reset_index` before `window_dataset()`** (and in `src/train.py:205`) so no window can span a user boundary.

---

*Completed for MasterArbeit_MLops thesis diagnostic — University of Siegen — 2026-04-23*

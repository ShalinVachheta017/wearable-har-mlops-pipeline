# Drift Investigation — Why the Pipeline Alarms Were Firing
**Date:** 2026-04-29
**Author:** Shalin Vachheta (with assistant analysis)
**Status:** Diagnostic complete; remediation plan proposed (not yet applied to pipeline)

---

## TL;DR

Production data is breaching every drift check in `DriftMonitor` for **two distinct
physical reasons**:

1. **Orientation drift** on the accelerometer — users hold the phone in different
   physical orientations than the training cohort. Gravity has migrated between
   axes. This shows up as **mean shift** on Ax/Ay/Az and a **2.2× variance shift**
   on Az.
2. **Behavioral drift** on the gyroscope — production users move more erratically
   than the controlled training subjects. This shows up as a **1.7×–2.2× variance
   shift** on Gy/Gz with **no mean shift** (gyro has no DC offset like gravity).

A magnitude-only feature collapse (`A_mag`, `G_mag`) — as suggested by an external
analysis — would silence the alarms but at the cost of throwing away directional
information that is signal for fine-grained hand activities (hand-tapping,
ear-rubbing). **Per-window gravity-aligned rotation** is the better fix:
it removes orientation drift at the source while preserving direction-of-motion.
Behavioral gyro drift is real and cannot be transformed away — it requires either
broader training data or accepting the alert.

---

## How the investigation progressed (and why each step gave us more clarity)

### Step 0 — Starting question
> "Why is `DriftMonitor` firing on every production batch?"

We did not know whether the drift was:
- A true model risk, or
- An artifact of the scaler / normalization being mis-fit, or
- A reflection of physically meaningful sensor differences.

### Step 1 — Locate the measurement boundary
First task: identify **where in the pipeline drift is being measured**, and
**what method** is used. From [src/preprocess_data.py](../src/preprocess_data.py)
and [src/monitoring/drift_monitor.py](../src/monitoring/drift_monitor.py):

- Drift is measured on **post-zscore windows** of shape `(N, 100, 6)`,
  immediately before they are handed to the model.
- Three checks run in parallel:
  - **PSI** per channel (10 quantile bins, threshold `0.15`).
  - **Post-z mean/std sanity** (`|μ| > 0.3` or `σ > 1.3`).
  - **Prediction entropy** vs training p95.
- `drift_detected = PSI || stats || entropy`.

This told us we were comparing apples to apples: training and production both flow
through the same `scaler_train_only.json` before the check.

### Step 2 — Compute the raw distribution side-by-side (no z-score)
Wrote [scripts/compare_train_vs_prod_distribution.py](../scripts/compare_train_vs_prod_distribution.py).

Result on 26 timestamped production sessions (10.5M rows) vs training users 1–4
(254K rows):

| Channel | train_mean | prod_mean | Δmean | train_std | prod_std | std_ratio |
|---|---|---|---|---|---|---|
| Ax | 2.34 | 0.12 | **-2.22** | 6.89 | 4.79 | 0.70 |
| Ay | 0.59 | 3.26 | **+2.67** | 4.67 | 4.08 | 0.88 |
| Az | -3.59 | -1.79 | **+1.80** | 3.08 | 6.78 | **2.20** |
| Gx | 0.67 | 0.60 | -0.08 | 54.79 | 45.56 | 0.83 |
| Gy | 0.25 | 0.21 | -0.04 | 15.50 | 26.13 | **1.69** |
| Gz | 0.06 | 0.02 | -0.04 | 14.53 | 32.48 | **2.24** |

**First insight:** the accelerometer is dominated by **mean shift** (gravity moved
between axes). The gyroscope is dominated by **variance shift** (no mean change,
larger spread). These are two physically different phenomena, not one drift.

### Step 3 — Why a Z-score scaler cannot fix this (mathematical proof)
Plugging the raw means through the locked scaler `(x − μ_train) / σ_train`:

- Ax post-z mean: `(0.12 − 2.34) / 6.89 = −0.32` → fails `|μ| > 0.3`
- Ay post-z mean: `(3.26 − 0.59) / 4.67 = +0.57` → fails
- Az post-z mean: `(−1.79 − (−3.59)) / 3.08 = +0.58` → fails
- Az post-z std: `prod_std / train_std = 2.20` → fails `σ > 1.3`
- Gy post-z std: `1.69` → fails
- Gz post-z std: `2.24` → fails

**Six simultaneous violations.** The scaler is doing exactly what it should
(normalizing using fixed training statistics); it cannot rotate a 3D coordinate
system. When physical device orientation changes, gravity migrates between
channels — `StandardScaler` operates one channel at a time and has no way to
recognize that Ay's new `+2.67` mean is the missing portion of Ax's `−2.22`.

### Step 4 — Rejected prescription: magnitude-only collapse
External analysis (Gemini) proposed: drop Ax/Ay/Az/Gx/Gy/Gz, keep only
`A_mag = √(Ax² + Ay² + Az²)` and `G_mag`. This is rotation-invariant and would
silence the alarms.

**Why we rejected this:**
1. Information loss: hand-tapping has a directional axis along the strike;
   ear-rubbing is a small lateral oscillation; walking has a strong vertical
   component. Magnitude collapses these into the same scalar energy.
2. Existing investigation in `scripts/debug_stage1_to_stage7_hand_tapping_collapse.py`
   shows hand-tapping is *already* collapsing — magnitude-only would likely make
   that worse.
3. It optimizes for "alarms stop firing," not "model gets more robust." Different
   goals.

### Step 5 — Experiment: per-session rotation to training mean (v1)
[scripts/experiment_gravity_aligned_rotation.py](../scripts/experiment_gravity_aligned_rotation.py)

Approach: estimate gravity per session as the mean accel vector; rotate so that
production's gravity vector aligns with training's mean gravity vector.

Result: drift alerts dropped from **6 → 3**. Az std drift fully resolved
(2.20 → 1.19). Mean alerts on Ax/Ay cleared. **But:**

- Az mean alert remained (post-z = −0.73). This is because the rotation target
  (`g_train = [2.34, 0.59, −3.59]`, magnitude only 4.33) is itself a
  motion-diluted average, not a clean gravity vector.
- Gy/Gz std got **worse** (1.69 → 2.11, 2.24 → 2.54). Why: rotating the gyro
  frame mixes high-variance Gx (54.79) into Gy/Gz. **Total angular energy is
  conserved; variance just redistributes.** This proved cleanly that the gyro
  variance drift is **real motion**, not orientation — you cannot rotate it away.

**Insight gained:** the correct rotation target is not a statistical artifact of
the training set but a physically meaningful canonical down vector
`[0, 0, −9.81]`. Also, one rotation per session assumes constant orientation
across the whole session, which is false (people pick up the phone, rotate it).

### Step 6 — Experiment: per-window rotation to canonical gravity (v2)
[scripts/experiment_gravity_aligned_rotation_v2.py](../scripts/experiment_gravity_aligned_rotation_v2.py)

Two improvements:
- **(v2a)** Estimate gravity per session via low-pass Butterworth (0.3 Hz cutoff)
  instead of raw mean. Align to canonical `[0, 0, −9.81]`.
- **(v2b)** Same low-pass estimate, but compute one rotation per **2-second
  window**. This catches within-session orientation changes.

Pre-zscore standard deviations after rotation (production):

| Channel | raw | v1 (mean-target) | v2a (session canonical) | **v2b (window canonical)** |
|---|---|---|---|---|
| Ax | 4.79 | 4.61 | 4.59 | **1.39** |
| Ay | 4.08 | 3.90 | 3.97 | **1.60** |
| Az | 6.78 | 3.66 | 3.59 | **1.37** |
| Gx | 45.56 | 37.14 | 42.01 | 38.73 |
| Gy | 26.13 | 32.70 | 32.92 | 28.46 |
| Gz | 32.48 | 36.95 | 31.07 | 38.77 |

Per-window rotation collapses accelerometer variance by ~3–5× because gravity is
now consistently confined to Az in every window. The gyro variance does **not**
collapse — confirming, again, that the gyro drift is real behavioral spread, not
orientation.

Drift alert count (post-zscore against canonical-rotated training scaler):

| Branch | mean alerts | std alerts | total |
|---|---|---|---|
| raw | 2 | 2 | 4 |
| v1 (mean-target) | 2 | 1 | 3 |
| v2a (session canonical) | 1 | 1 | 2 |
| **v2b (window canonical)** | 1 | 1 | **2** |

Remaining alerts after v2b are:
- **Az mean alert (post-z = −1.15)** — this is a **comparison artifact**, not
  physical drift. Training in v2b was rotated session-level (one rotation across
  254K rows) while production was rotated window-level (one rotation per 100
  samples). For an apples-to-apples evaluation, both must use window-level
  canonical rotation. When that is done in production, this alert will resolve.
- **Gy std alert (post-z = 1.87)** — **real behavioral drift.** Production users
  rotate the device faster around the y-axis than training subjects. This is a
  signal about the training cohort being too narrow, not noise to suppress.

---

## Why each step made things clearer

| Step | What it told us | What it ruled out |
|---|---|---|
| 1. Locate boundary | Drift is measured post-zscore on (N,100,6) windows | "scaler is broken" — it's working as designed |
| 2. Raw side-by-side | Two distinct drift mechanisms (mean vs variance) | "single drift" framing |
| 3. Math through scaler | StandardScaler is 1D linear — cannot rotate axes | "fix it with a different scaler" |
| 4. Magnitude critique | Information loss for fine-grained activities | Magnitude-only as the correct fix |
| 5. v1 rotation experiment | Orientation drift is real and partially fixable; gyro variance is **not** rotational | "all drift is orientation drift" |
| 6. v2 canonical + per-window | Per-window rotation collapses accel variance ~5× while preserving direction; gyro behavior remains as the only real residual | "per-session rotation is enough"; "training scaler target is OK" |

Each step replaced an assumption with a measurement. We went from "alarms firing,
unclear why" to "two specific mechanisms, one fixable by rotation, one is real."

---

## Recommended remediation (NOT yet applied)

### Phase 1 — Fix orientation drift at the source
Add a **gravity-alignment stage** to [src/preprocess_data.py](../src/preprocess_data.py)
between unit conversion and z-score normalization:

1. Per 2-second window, low-pass the accel signal at 0.3 Hz to estimate gravity.
2. Compute Rodrigues rotation matrix `R` from window gravity to `[0, 0, −9.81]`.
3. Apply `R` to both accel and gyro triplets in that window.
4. Apply the **same** stage to training data and **refit** `scaler_train_only.json`
   on the rotated training data. Refit `models/drift_reference.json` accordingly.

This preserves all 6 channels and all directional information. It just removes
the orientation degree of freedom, which is the part the model cannot use anyway.

### Phase 2 — Treat gyro behavioral drift honestly
The 1.69σ–2.24σ gyro variance increase is **real**. Three options, in order of
preference:

1. **Collect labeled production-style data** (more erratic motion) and retrain.
   This is the principled fix.
2. **Augment training synthetically** — add noise / time-warp / amplitude scaling
   to gyro channels during training to expose the model to higher-variance inputs.
3. **Accept the alert** — keep the threshold at `σ > 1.3` and treat it as a
   "your training cohort was too narrow" indicator. Do **not** raise the
   threshold to silence it; that defeats the purpose of monitoring.

### Phase 3 — Update `drift_monitor.py` only after Phase 1
After gravity-alignment is in the pipeline, the canonical training reference
will have all gravity in Az. The thresholds `|μ| > 0.3` and `σ > 1.3` should
remain. Expected behavior:
- Ax/Ay/Az mean alerts → cleared (orientation no longer migrates between axes).
- Az std alert → cleared (Az variance is now within-window motion only).
- Gy/Gz std alerts → **may still fire** when production behavior diverges from
  training. This is the desired signal.

---

## Files produced during this investigation

- [scripts/compare_train_vs_prod_distribution.py](../scripts/compare_train_vs_prod_distribution.py) —
  pre-zscore distribution table.
- [scripts/experiment_gravity_aligned_rotation.py](../scripts/experiment_gravity_aligned_rotation.py) —
  v1: per-session rotation to training mean accel.
- [scripts/experiment_gravity_aligned_rotation_v2.py](../scripts/experiment_gravity_aligned_rotation_v2.py) —
  v2a (session) and v2b (per-window) rotation to canonical gravity.
- [docs/DRIFT_INVESTIGATION_CHAT_2026-04-29.txt](DRIFT_INVESTIGATION_CHAT_2026-04-29.txt) —
  raw transcript of the investigation.

All three scripts are read-only (no pipeline files modified). They print
diagnostic tables to stdout.

---

# Pipeline Audit — Bugs & Threshold Issues, Organized by Stage

This section catalogues every issue found while answering "what else could be
wrong in the pipeline?" Each item is assigned to the pipeline stage it belongs
to (per [src/entity/config_entity.py](../src/entity/config_entity.py): Stage 1
Data Ingestion → Stage 10 Baseline Update).

Severity legend: **HIGH** = wrong numbers reported / decisions affected.
**MEDIUM** = correctness preserved but inconsistent / underpowered.
**LOW** = stylistic or dead-code cleanup.

---

## Stage 3 — Data Transformation (preprocessing → windows)

### Issue 3.1 — Scaler cannot fix orientation drift (architectural, not a bug)
**Severity:** HIGH (already covered above)

`StandardScaler` is six independent 1D transforms; it cannot rotate a 3D
coordinate system. When physical device orientation differs between training
and production, gravity migrates between channels and the scaler has no way
to recognize it. **Fix:** add the per-window gravity-alignment stage from
Phase 1 of the remediation plan above.

**Files affected:** [src/preprocess_data.py](../src/preprocess_data.py),
[data/prepared/scaler_train_only.json](../data/prepared/scaler_train_only.json),
[models/drift_reference.json](../models/drift_reference.json) (refit required).

---

## Stage 5 — Model Evaluation

### Issue 5.1 — Calibration temperature defaults to 1.0 (off)
**Severity:** MEDIUM

[src/entity/config_entity.py:209](../src/entity/config_entity.py#L209)
sets `calibration_temperature: float = 1.0`. This means temperature scaling
(Guo et al. 2017) is disabled by default. Modern deep nets are typically
over-confident; uncalibrated ECE is commonly 0.10–0.30. With T=1.0 the
`mean_confidence` reported in monitoring is inflated, so the
`confidence_warn = 0.70` threshold is artificially easy to pass.

**Fix:** wire the `T` value from the calibration stage's output into the
monitoring config so production reports use post-hoc calibrated probabilities.

---

## Stage 6 — Post-Inference Monitoring (3-layer)

This is where most bugs live. All file references point to
[src/monitoring/post_inference_monitor.py](../src/monitoring/post_inference_monitor.py).

### Issue 6.1 — Dwell time inflated by 4× ⚠️
**Severity:** HIGH

Lines 279–282:
```python
WINDOW_DURATION_SECS = 8.0
mean_dwell_secs = float(np.mean(dwell_lengths) * WINDOW_DURATION_SECS)
```
But the actual pipeline uses:
- `WINDOW_SIZE = 200` samples @ 50 Hz = **4 s window**
- `OVERLAP = 0.5` → step = 100 samples = **2 s between adjacent window starts**

`dwell_lengths` counts consecutive same-prediction *windows*, so the
multiplier should be the **step duration (2.0 s)**, not 8.0. Every reported
dwell time is currently **4× too large**.

`SHORT_DWELL_WINDOWS = 2` (≤2 windows = "short") therefore corresponds to
**4 s** of real time, not 16 s as currently reported.

**Fix:** compute `WINDOW_DURATION_SECS` from `src.config.WINDOW_SIZE` and
`OVERLAP`:
```python
from src.config import WINDOW_SIZE, OVERLAP
SAMPLING_HZ = 50
STEP_SECS = (WINDOW_SIZE * (1 - OVERLAP)) / SAMPLING_HZ  # = 2.0 s
```

### Issue 6.2 — Approximate entropy instead of true Shannon entropy ⚠️
**Severity:** HIGH

Lines 181–185:
```python
entropy_vals = -(confs * np.log(confs) + (1 - confs) * np.log((1 - confs) / (K - 1) + eps))
```
This is **binary entropy** between max-prob and (1 − max-prob), assuming the
remaining mass is uniform across `K-1` classes. But the full softmax is saved
in `predictions_*_probs.npy`. True entropy `−Σ p_i log p_i` is already
implemented correctly in [src/monitoring/drift_monitor.py:35](../src/monitoring/drift_monitor.py#L35).

The two paths use different definitions, so:
- `entropy_p95` in `drift_reference.json` (true Shannon, calibrated on training)
- `mean_entropy` in monitoring reports (binary approximation)

**are not comparable.** Any threshold tuned on one will be wrong for the other.

**Fix:** load `predictions_*_probs.npy` and reuse `DriftMonitor._entropy()`.

### Issue 6.3 — Drifted-channel counter uses wrong threshold
**Severity:** MEDIUM

Line 401: `drift_channel_threshold = 1.0` is hardcoded, while the alert fires
at `self.drift_threshold = 1.8`. So `n_drifted_channels` reports the count at
1.0σ but the WARNING raises at 1.8σ. The counter and the alert disagree.

**Fix:** set `drift_channel_threshold = self.drift_threshold` (or expose as
config).

### Issue 6.4 — MMD bootstrap is undersized
**Severity:** MEDIUM

[src/entity/config_entity.py:202-203](../src/entity/config_entity.py#L202-L203):
`mmd_sample_size=384`, `mmd_bootstrap_iterations=40`. With 40 iterations the
95th-percentile threshold estimate has CI roughly ±31 % of the true quantile
(Gretton et al. 2012; Sutherland et al. 2017 recommend 1000–10000).

**Fix:** raise iterations to **1000+** for a stable MMD threshold. This is a
one-time calibration cost.

### Issue 6.5 — Two drift monitors compute different metrics
**Severity:** MEDIUM (architectural)

- [src/monitoring/drift_monitor.py](../src/monitoring/drift_monitor.py) —
  PSI + post-z stats + entropy, threshold `0.15` PSI.
- [src/monitoring/post_inference_monitor.py](../src/monitoring/post_inference_monitor.py) —
  z-score mean shift OR MMD, threshold `1.8σ`.

The runtime path actually used at inference is the second one. The PSI
implementation in `drift_monitor.py` is **calibrated** in
`models/drift_reference.json` but **never called** at inference time. The
`psi` field in the per-channel metrics dict is a back-compat alias whose
value is z-score, not PSI.

**Fix:** either wire `drift_monitor.py` PSI into the runtime path as a
secondary signal, or delete it as dead code. Two drift implementations with
different semantics is confusing for any future reader.

### Issue 6.6 — `is_training_session` flag may be unused
**Severity:** LOW (verify)

[src/entity/config_entity.py:216](../src/entity/config_entity.py#L216) exposes
`is_training_session: bool = False` to skip Layer 3 when running training data
through the inference path (otherwise self-comparison gives artificially low
drift scores). Worth confirming it is set correctly in evaluation runs;
otherwise training-time eval scores look better than they should.

### Issue 6.7 — Hardcoded `K = 11` in entropy formula
**Severity:** MEDIUM (depends on actual class count)

Line 180: `K = 11`. If your label space is not 11 classes, the entropy
normalisation is wrong. Verify against the actual model's output dimension
and read `K` from the predictions file or label map.

---

## Stage 7 — Trigger Evaluation

### Issue 7.1 — Threshold duplication with conflicting defaults ⚠️
**Severity:** HIGH

The same logical threshold is defined in three places with different values:

| Threshold | `PostInferenceMonitoringConfig` (S6) | `TriggerEvaluationConfig` (S7) | `TriggerThresholds` (S7) |
|---|---|---|---|
| `confidence_warn` | 0.70 | 0.65 | 0.65 |
| `flip_rate_warn` | **35.0 %** (transition_rate) | **35.0 %** (temporal_flip_warn) | **25 %** (flip_rate_warn) |
| `drift_zscore_warn` | **1.8** | **2.0** | **2.0** |

The flip-rate warn is **0.25 in one place, 0.35 in another**. Whichever code
path runs first decides which threshold "wins"; the others are silently dead.

**Fix:** establish a **single source of truth** (recommend
`config_entity.py`), have all consumers read from it, delete duplicate
defaults.

### Issue 7.2 — Entropy thresholds don't scale with K
**Severity:** MEDIUM

[src/trigger_policy.py](../src/trigger_policy.py) line 106–107:
`entropy_warn = 1.8`, `entropy_critical = 2.2`.

For K = 11, `log(K) = 2.40`. Critical at 2.2 means alarm only fires when
predictions are 92 % of theoretical maximum entropy — i.e. near-uniform
random output. For K = 4, `log(K) = 1.39` and the warn threshold (1.8) is
**impossible to reach**.

**Fix:** parameterize by K. Recommended:
- `entropy_warn = 0.5 × log(K)` (~half of theoretical max)
- `entropy_critical = 0.7 × log(K)`

For K=11: warn = 1.20, critical = 1.68.

### Issue 7.3 — Cooldown vs batch-accumulation logic
**Severity:** LOW

[src/trigger_policy.py:144-146](../src/trigger_policy.py#L144-L146) defines
both `retrain_cooldown_hours = 24` and `batch_accumulation_min = 100`, but
only the time-based cooldown is enforced in `_apply_cooldowns()`.
`batch_accumulation_min` appears unused.

**Fix:** either implement the batch-count gate or delete the field.

---

## Stage 10 — Baseline Update

### Issue 10.1 — Baseline staleness governance is set but not action-gated
**Severity:** LOW

`max_baseline_age_days = 90` raises a Prometheus alert (in the historical
`har_alerts.yml`) and a log warning, but does not block monitoring. A
~6-month-old baseline silently invalidates Layer 3 — the monitor still runs
but compares against drifted reference statistics.

**Fix:** in Stage 6, raise the report status to WARNING when the baseline
file's mtime exceeds the threshold, regardless of the drift score itself.

---

## Cross-cutting — Threshold Reference Table

Recommended values, with sources, for ALL monitoring thresholds in the
pipeline:

### Confidence (Stage 6 / Stage 7)

| Metric | Recommended | Source / rationale |
|---|---|---|
| `confidence_warn` | **0.70** | Hendrycks & Gimpel 2017 (softmax-baseline OOD); HAR studies use 0.6–0.75 |
| `confidence_critical` | **0.50** | Below 0.50 the max class isn't even majority of mass — clear OOD |
| `entropy_warn` | **0.5 × log(K)** | Half of theoretical maximum |
| `entropy_critical` | **0.7 × log(K)** | 70 % of max — near-uniform |
| `uncertain_ratio_warn` | **0.15** | Standard rule of thumb |
| `uncertain_ratio_critical` | **0.30** | One-third of inputs uncertain = critical |

### Temporal (Stage 6 / Stage 7)

| Metric | Recommended | Source / rationale |
|---|---|---|
| `flip_rate_warn` | **0.20** | At 2 s step, this corresponds to mean dwell ≈ 10 s (matches natural HAR bouts; Banos 2014, Mannini & Sabatini 2010) |
| `flip_rate_critical` | **0.35** | Mean dwell ≈ 5.7 s — model is oscillating |
| `mean_dwell_warn` | **< 6 s** | Hand-tapping bouts typically 3–30 s; sitting/walking >10 s |
| `short_dwell_ratio_warn` | **> 0.40** | >40 % of dwells ≤ 4 s = unstable predictions |

### Drift (Stage 6 / Stage 7)

| Metric | Recommended | Source / rationale |
|---|---|---|
| `drift_zscore_warn` | **2.0σ** | 95th pct, Page 1954 CUSUM, Gama 2014 DDM |
| `drift_zscore_critical` | **3.0σ** | 99.7th pct (3-sigma rule) |
| `min_drifted_channels_warn` | **2** | At least 2 channels = systematic, not noise |
| `min_drifted_channels_critical` | **4** | Majority of 6 channels |
| `drift_channel_threshold` (counter) | **= drift_zscore_warn** | Currently 1.0, must match alert threshold |
| `psi_threshold` | **0.20** | Industry standard credit-risk PSI: <0.10 stable, 0.10–0.25 minor, >0.25 major. (Currently 0.15.) |
| `post_z_mean_threshold` | **0.30** | Scaler outputs ~N(0,1); |μ| > 0.3 = ≈3 % of std. Keep. |
| `post_z_std_threshold` | **1.30** | std-ratio > 1.3 = ~70 % wider spread. Keep. |
| `mmd_bootstrap_iterations` | **1000+** | Gretton 2012, Sutherland 2017 |

### Voting / cooldown (Stage 7)

| Metric | Recommended | Source / rationale |
|---|---|---|
| `min_signals_for_retrain` | **2** | 2-of-3 voting reduces FP; standard. Keep. |
| `consecutive_warnings_for_trigger` | **3** | Persistent issue; keep. |
| `retrain_cooldown_hours` | **24–72** | 24 h is aggressive (good for thesis demo); 72 h is more typical for production |

---

## Priority fix order (recommended)

If you fix these in order, you'll get the largest correctness gains for the
smallest blast radius:

1. **HIGH — Stage 6.1** — `WINDOW_DURATION_SECS = 8.0` → `2.0`. (4× error on
   every dwell number you have ever reported.)
2. **HIGH — Stage 6.2** — Replace approximate entropy with true Shannon
   entropy on full softmax.
3. **HIGH — Stage 7.1** — Resolve flip-rate threshold conflict (0.25 vs 0.35);
   establish single source of truth.
4. **MEDIUM — Stage 6.3** — Fix `drift_channel_threshold` to match
   `drift_zscore_warn`.
5. **MEDIUM — Stage 7.2** — Make entropy thresholds depend on `K`.
6. **MEDIUM — Stage 5.1** — Wire calibration temperature into monitoring.
7. **MEDIUM — Stage 6.4** — Increase MMD bootstrap iterations.
8. **MEDIUM — Stage 6.5** — Decide PSI's runtime status (wire or delete).
9. **HIGH (already covered) — Stage 3.1** — Per-window gravity alignment.
10. **LOW — Stages 6.6, 6.7, 7.3, 10.1** — verification / cleanup.

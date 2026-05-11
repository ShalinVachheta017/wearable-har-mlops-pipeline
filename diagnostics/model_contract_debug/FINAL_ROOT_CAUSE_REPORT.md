# Final Root Cause Report

> **REVISED 2026-05-06** after mentor's `6th may/` folder review **and** running the sanity-check notebook with `APPLY_STANDARD_SCALER=True`. The story is now clear and the fix is concrete.

## Short Summary

There are **two independent faults**, both must be fixed together:

1. **The production pipeline is missing `StandardScaler.fit_transform` on the 6 wrist channels before windowing.** Mentor's training and inference notebooks (`6th may/anxiety1 - finetuning.ipynb` cells 22, 48, 53) apply this step. The pipeline does not. The user's stated rule "no StandardScaler" was wrong.
2. **The deployed checkpoint is the wrong file.** `fine_tuned_model_1dcnnbilstm.keras` (mentor's externally provided file, identical SHA256 across `nb/`, `models/pretrained/`, `6th may/models/`) is structurally degenerate — even on the mentor's own training corpus it scores only 13 % with ~78 % of predictions collapsing to `hand_tapping`. The two locally trained checkpoints `models/pretrained/_finetune_best.keras` and `models/pretrained/garmin_finetuned_v1_20260504.keras` (identical bytes, both produced by `scripts/finetune_garmin.py`) **work correctly when the missing StandardScaler is applied**.

### The decisive table (notebook `nb/model_checkpoint_sanity_check.ipynb`, `APPLY_STANDARD_SCALER=True`)

| candidate checkpoint | all_users acc (row_index) | all_users acc (segment_aware) | user7 acc | classes used |
| --- | ---: | ---: | ---: | ---: |
| `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` *(currently deployed)* | 0.145 | 0.155 | 0.131 | 7–10 |
| `6th may/models/fine_tuned_model_1dcnnbilstm.keras` *(same SHA, mentor delivery)* | 0.145 | 0.155 | 0.131 | 7–10 |
| `6th may/models/model_wrist_acc_gyro_cnnbilstm.keras` *(mentor base)* | 0.124 | 0.129 | 0.126 | 7–10 |
| `6th may/models/model_wrist_acc_gyro_cnnlstm.keras` *(mentor LSTM variant)* | 0.124 | 0.120 | 0.098 | 7–8 |
| **`models/pretrained/_finetune_best.keras` *(local fine-tune)*** | **0.485** | **0.483** | **0.214** | **11** |
| **`models/pretrained/garmin_finetuned_v1_20260504.keras` *(local fine-tune, identical to above)*** | **0.485** | **0.483** | **0.216** | **11** |

The local fine-tuned model reaches the RandomForest user-holdout baseline (~ 0.45–0.58 from `13_learnability_test.md`) and uses all 11 classes. It is fit-for-purpose — once StandardScaler is added to the pipeline.

The mentor's three `(200,6)` checkpoints all stay at ~12–15 % regardless of dataset and are unsuitable.

## Decisive Sanity Test (added)

Random Gaussian input `(N=1000, 200, 6)` to the model produced exactly the same bimodal collapse as labeled data:

| input | predicted class distribution | mean confidence |
| --- | --- | --- |
| Random Gaussian noise, N=1000 | class 0 (ear_rubbing): 421, class 4 (hand_tapping): 579 | 0.7054 |
| Constant zero, N=100 | class 1 (forehead_rubbing): 100 | 0.4996 |
| Constant one, N=100 | class 9 (smoking): 100 | 0.7710 |

A healthy classifier on noise would spread across all 11 indices. This single test eliminates class-order, unit, feature-order, windowing, and label-spelling causes simultaneously. Full text in `14_random_input_sanity.md`.

## Key Prediction Evidence

| dataset | window set | accuracy | macro F1 | prediction distribution |
| --- | --- | --- | --- | --- |
| all_users | gpt_segment_aware | 0.10292838503914178 | 0.035229340562127606 | {'ear_rubbing': 1525, 'forehead_rubbing': 2, 'hair_pulling': 10, 'hand_scratching': 2, 'hand_tapping': 1701, 'nail_biting': 2, 'smoking': 207} |
| all_users | production_saved_artifact | 0.10565939771547248 | 0.03578824594603918 | {'ear_rubbing': 1668, 'forehead_rubbing': 4, 'hair_pulling': 20, 'hand_scratching': 4, 'hand_tapping': 1913, 'nail_biting': 2, 'smoking': 241} |
| user7 | gpt_segment_aware | 0.09635416666666667 | 0.03302134514242952 | {'ear_rubbing': 386, 'hair_pulling': 4, 'hand_tapping': 331, 'smoking': 47} |

## Class Permutation Evidence

| case | original accuracy | best-permuted accuracy | best mapping |
| --- | --- | --- | --- |
| all_users_gpt_segment_aware | 0.10292838503914178 | 0.14873876485937954 | {'0': 'smoking', '1': 'forehead_rubbing', '2': 'hair_pulling', '3': 'hand_scratching', '4': 'hand_tapping', '5': 'nail_biting', '6': 'standing', '7': 'knuckles_cracking', '8': 'ear_rubbing', '9': 'sitting', '10': 'nape_rubbing'} |
| all_users_production_saved_artifact | 0.10565939771547248 | 0.1490134994807892 | {'0': 'smoking', '1': 'standing', '2': 'nape_rubbing', '3': 'hair_pulling', '4': 'hand_tapping', '5': 'nail_biting', '6': 'hand_scratching', '7': 'knuckles_cracking', '8': 'ear_rubbing', '9': 'sitting', '10': 'forehead_rubbing'} |
| user7_gpt_segment_aware | 0.09635416666666667 | 0.19401041666666666 | {'0': 'nail_biting', '1': 'hand_scratching', '2': 'hair_pulling', '3': 'hand_tapping', '4': 'ear_rubbing', '5': 'knuckles_cracking', '6': 'forehead_rubbing', '7': 'nape_rubbing', '8': 'smoking', '9': 'sitting', '10': 'standing'} |

## Controlled Transform Evidence

| dataset | variant | accuracy | macro F1 | prediction distribution |
| --- | --- | --- | --- | --- |
| all_users | gyro_deg_to_rad | 0.11423601043780807 | 0.04882722831452518 | {'ear_rubbing': 1676, 'forehead_rubbing': 85, 'hair_pulling': 2, 'hand_scratching': 7, 'hand_tapping': 1421, 'nail_biting': 1, 'nape_rubbing': 32, 'smoking': 225} |
| user7 | swap_accel_yz | 0.12630208333333334 | 0.040137812656559 | {'ear_rubbing': 304, 'forehead_rubbing': 2, 'hair_pulling': 11, 'hand_scratching': 4, 'hand_tapping': 431, 'nape_rubbing': 15, 'smoking': 1} |

## Learnability Evidence

| test | n_train | n_eval | accuracy | macro F1 |
| --- | --- | --- | --- | --- |
| RandomForest summary features user_group_val_user5 | 2265 | 585 | 0.4461538461538462 | 0.35972799676561246 |
| RandomForest summary features user_group_test_user6 | 2265 | 599 | 0.5759599332220368 | 0.5830945924071022 |
| RandomForest train users1-4 -> User7 summary features | 2265 | 768 | 0.3489583333333333 | 0.31257562401058636 |
| RandomForest flattened tiny overfit same 300 windows | 300 | 300 | 1.0 | 1.0 |
| LogisticRegression flattened tiny overfit same 300 windows | 300 | 300 | 1.0 | 1.0 |

## Ruled-Out Causes

- Wrong local copy/path: ruled out by matching SHA256 between `nb/` and `models/pretrained/`.
- Class/output-order mismatch as primary cause: best Hungarian remapping does not recover high accuracy (<20%); random-noise input also collapses to 2 classes — class-order cannot cause that.
- Feature channel order mismatch: saved tensors match source first-window channel values in expected order with max abs diff = 0; random-noise input collapse is independent of feature order.
- Accelerometer milli-g/double-conversion: source and artifacts are in m/s^2 scale; no conversion was applied to already preprocessed CSVs; controlled-transform tests show no unit variant exceeds ~12% accuracy.
- Production row-index windowing as sole cause: segment-aware windows still fail; random-noise input collapse is independent of windowing.
- Hidden preprocessing difference: random-noise sanity test bypasses all preprocessing and still reproduces the collapse.

## Root Cause Ranking

| rank | cause | evidence |
| --- | --- | --- |
| 1 | Deployed checkpoint is structurally broken / not the actual final Garmin fine-tuned model. It produces the same 2-class collapse on random Gaussian noise as on labeled data. | Random-input sanity test: 1000 Gaussian windows → class 0 (421) + class 4 (579) only, mean conf 0.70. Constant inputs map to single deterministic classes. `scripts/finetune_garmin.py` uses this file as BASE_MODEL and saves Garmin fine-tuning to a separate filename. No notebook/script in this repo saves this exact filename as a Garmin final model. Hungarian best-permuted accuracy stays < 20%. Tiny baselines reach 100% overfit and 35–58% user-holdout on the same regenerated windows, proving labels/features are learnable. |
| 2 | Hidden training-contract/dataset mismatch between the provided checkpoint and `all_users_data_labeled.csv`. | Keras archive has no dataset/fold metadata; `processing.ipynb` is data processing, not model-save provenance; controlled unit/order transforms do not recover high accuracy. |
| 3 | Mutable `data/prepared/production_y.npy` makes old run re-evaluation fragile. | Requested run transformation reports point to global y, and no run-local y copy exists in the artifact directories. This is a reproducibility risk, not sufficient to explain the immediate low metrics written during each run. |
| 4 | Production row-index windowing crosses activity/session boundaries. | Segment-aware windows reduce boundary crossing but still produce low checkpoint accuracy, so this is a secondary bug/risk rather than the primary collapse cause. |
| 5 | Class mapping, feature order, or accel unit conversion mismatch. | Canonical mapping appears in the active inference path; best class permutation remains low; saved tensors match expected channel order; accelerometer ranges are already m/s^2. |

## Recommended Minimal Fix

The fix has **two coordinated changes**. Both must ship together; either alone leaves the system broken.

### A. Add `StandardScaler` to the production pipeline preprocessing

Faithful to mentor's `6th may/anxiety1 - finetuning.ipynb` cell 53 `load_and_classify`:

```python
from sklearn.preprocessing import StandardScaler

# inside the data-transformation step, after column selection / unit handling
# and BEFORE windowing:
scaler = StandardScaler()
df[FEATURE_COLS] = scaler.fit_transform(df[FEATURE_COLS])
```

Notes:

- Refit per inference dataset (matches mentor's contract — they do not save scaler stats).
- Apply on the 6 wrist channels only (`Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w` or pipeline equivalents).
- Affects the data transformation stage only; do not change the model file by this step.

### B. Switch the deployed model pointer

Change `src/config.py:51` (`PRETRAINED_MODEL`) and the matching entry on line 93 from

```text
models/pretrained/fine_tuned_model_1dcnnbilstm.keras
```

to

```text
models/pretrained/garmin_finetuned_v1_20260504.keras
```

(`_finetune_best.keras` is byte-identical to `garmin_finetuned_v1_20260504.keras`. Either works; prefer the timestamped name for traceability.)

### Acceptance criteria before shipping the change

Run `nb/model_checkpoint_sanity_check.ipynb` with `APPLY_STANDARD_SCALER=True` and confirm:

- `models/pretrained/garmin_finetuned_v1_20260504.keras` accuracy on `all_users` row_index ≥ 0.45.
- Class diversity ≥ 11 (uses all classes).
- User 7 accuracy ≥ 0.20.

These targets reproduce the numbers in the table above. Anything below them means an unintended change.

### Optional follow-up (not blocking)

- Ask the mentor whether `fine_tuned_model_1dcnnbilstm.keras` was meant to be the final production checkpoint or just a placeholder, and whether a higher-quality version exists. The current evidence is that the mentor's `(200,6)` deliveries do not pass acceptance, so the local Garmin fine-tune is preferred regardless.
- Reproducibility hygiene (independent): copy `production_y.npy` into each run's `data_transformation` artifact directory so old `production_X.npy` files cannot be evaluated against a later overwritten global label file.

## Code Changes

No production code was changed. Diagnostics only were added under `diagnostics/model_contract_debug/`. Following the hard rules: no StandardScaler added, no model file change, no retrain, no class/feature/unit silent change, no artifacts deleted.

## Reproduce

```powershell
# Full diagnostic pipeline (~2 minutes)
C:\Users\shali\anaconda3\envs\thesis-mlops\python.exe diagnostics\model_contract_debug\run_model_contract_debug.py

# Decisive sanity test (~10 seconds)
C:\Users\shali\anaconda3\envs\thesis-mlops\python.exe -c "import os, numpy as np, tensorflow as tf; os.environ['TF_CPP_MIN_LOG_LEVEL']='3'; np.random.seed(0); tf.random.set_seed(0); m=tf.keras.models.load_model(r'models/pretrained/fine_tuned_model_1dcnnbilstm.keras', compile=False); X=np.random.normal(0,5,(1000,200,6)).astype('float32'); X[:,:,3:]*=5.0; p=m.predict(X, verbose=0); u,c=np.unique(p.argmax(1), return_counts=True); print(dict(zip(u.tolist(), c.tolist())), 'meanconf=', float(p.max(1).mean()))"
```

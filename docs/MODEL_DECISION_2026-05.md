# Model Decision - May 2026

Date: 2026-05-08

Status: final Model A package selected after bounded sprint and one User 7 external evaluation.

## 1. Final Chosen Model

The selected clean-contract model is:

```text
model_a_sprint_gamma05_weak3_x4_noaug
```

Package:

```text
models/production_contract/model_a_final_20260508/
```

Training route:

```text
ADAMSense pretrained CNN-BiLSTM
+ Garmin all_users fine-tuning
+ Garmin train-only StandardScaler
+ weak-class oversampling
+ class-balanced focal loss, gamma = 0.5
```

This is not a high-performing model. It is selected because it is the best current clean-contract candidate after the bounded Model A sprint, keeps all 11 classes active, avoids the mentor legacy tensor/scaler path, and is reproducible as a production package.

## 2. Final Input Contract

The defended Model A contract is:

```text
normal row-wise IMU windows
6 wrist channels: Ax, Ay, Az, Gx, Gy, Gz
window size: 200 samples
stride: 100 samples
expected sampling rate: 50 Hz
fixed 11-class label order
Garmin train-only StandardScaler
User 7 external evaluation only after model freeze
no legacy mentor tensor reshape
no scaler fitted on validation, User 7, or production input
```

Final label order:

```text
ear_rubbing
forehead_rubbing
hair_pulling
hand_scratching
hand_tapping
knuckles_cracking
nail_biting
nape_rubbing
sitting
smoking
standing
```

## 3. Why Vendor Legacy Model Is Not Final

The vendor notebooks are useful forensic evidence, but they are not the final production proof.

They use:

```text
full-data StandardScaler before train/test split
random overlapping window split
legacy tensor reshape
fresh StandardScaler fitted on each inference file
accuracy-focused validation
```

The vendor checkpoint can reproduce high accuracy only under its legacy notebook contract. Diagnostics showed the same checkpoint performs well with the vendor scaler/layout, but collapses under normal row-wise production windows. Therefore, the thesis defends the clean production contract, not the hidden legacy notebook contract.

## 4. Bounded Model A Sprint

The final sprint tested only controlled Model A improvements:

```text
focal gamma: 0.5, 1.0, 1.5
weak-class oversampling: 3x, 4x, 5x
weak-5 recovery sampling
equal-per-class sampling
very-low augmentation
one full-unfreeze variant
```

Best sprint candidate:

```text
model_a_sprint_gamma05_weak3_x4_noaug
```

Garmin validation:

```text
accuracy:          0.3116
balanced accuracy: 0.3117
macro F1:          0.3101
weighted F1:       0.3136
classes used:      11 / 11
mean confidence:   0.4558
dominant class:    nape_rubbing
dominant class %:  23.5%
dead-class mean F1: 0.1229
```

Per-class F1 for the selected run:

```text
ear_rubbing:       0.2947
forehead_rubbing:  0.2888
hair_pulling:      0.4444
hand_scratching:   0.1290
hand_tapping:      0.7530
knuckles_cracking: 0.2383
nail_biting:       0.4084
nape_rubbing:      0.1489
sitting:           0.3907
smoking:           0.0909
standing:          0.2234
```

## 5. User 7 External Result

User 7 was evaluated once after Model A was frozen.

Window audit:

```text
total windows:    974
kept windows:     958
rejected windows: 16
segments:         11
```

User 7 external metrics:

```text
accuracy:          0.3810
balanced accuracy: 0.3769
macro F1:          0.3397
weighted F1:       0.3426
classes used:      11 / 11
mean confidence:   0.3622
dominant class:    nape_rubbing
dominant class %:  17.2%
```

This is an external self-recorded evaluation session, not a blind test used for tuning.

## 6. A/B/C Decision

Final comparison:

```text
A = Clean-contract Model A
B = Mentor/vendor legacy model
C = Previous current pipeline/default model
```

Decision:

```text
Model A is selected for the final clean-contract package.
Model B is kept as historical/forensic evidence only.
Model C is rejected because it performs poorly under the current clean row-wise pipeline.
```

Rationale:

```text
Model A has lower headline accuracy than the vendor legacy route, but it has a documented deployable contract.
Model B has stronger reported metrics only under a legacy scaler/layout contract with leakage risk.
Model C shows severe contract mismatch/collapse under clean row-wise evaluation.
```

The A/B/C table is saved at:

```text
models/production_contract/model_a_final_20260508/abc_model_comparison.csv
```

## 7. Weak Classes And Limitations

The main limitation remains cross-user and class-level generalization.

Weak classes improved compared with the earlier base model but remain weak:

```text
hand_scratching: 0.1290 F1
smoking:         0.0909 F1
nape_rubbing:    0.1489 F1
```

The thesis-safe conclusion is:

```text
The clean-contract model removed collapse and improved weak-class recovery, but cross-user Garmin validation remains limited.
```

## 8. Final Package Contents

The final Model A package contains:

```text
fine_tuned_clean_model.keras
garmin_train_scaler.joblib
garmin_train_scaler.json
model_contract.json
label_order.json
metrics_summary.json
training_report.md
abc_model_comparison.csv
garmin_train_scaled_baseline.json
```

The package records:

```text
model route: ADAMSense pretraining -> Garmin class-recovery fine-tuning
selected run: model_a_sprint_gamma05_weak3_x4_noaug
input shape: (200, 6)
features: Ax, Ay, Az, Gx, Gy, Gz
window size: 200
stride: 100
scaler: Garmin train-only StandardScaler
loss: class-balanced focal loss, gamma = 0.5
weak-class oversampling: hand_scratching, smoking, nape_rubbing, standing, knuckles_cracking
selection metric: Garmin validation macro F1
external evaluation: User 7, reported after selection
```

## Decision Sentence

The final defended Model A uses a clean production contract: ADAMSense is used for pretraining, Garmin all_users is used for fine-tuning with weak-class recovery, the deployed scaler is fitted only on Garmin training data, and User 7 is used only as an external evaluation session.

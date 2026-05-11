# 15 Mentor "6th may" Folder Forensic Audit

This report audits the contents of `6th may/` provided by the mentor and answers two questions:

1. Is `fine_tuned_model_1dcnnbilstm.keras` in our deployment the same file the mentor delivered?
2. Does the mentor's documented training contract differ from what the production pipeline implements?

## Folder Inventory

| path | size | sha256 (16 hex) | notes |
| --- | --- | --- | --- |
| `6th may/models/fine_tuned_model_1dcnnbilstm.keras` | 6,095,608 | `3a35f3bd6f74293b...` | **Same SHA256 as `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` and `nb/fine_tuned_model_1dcnnbilstm.keras`. Confirmed identical file.** |
| `6th may/models/model_wrist_acc_gyro_cnnbilstm.keras` | 6,096,210 | `d42d76e6f07d9304...` | Mentor BASE CNN-BiLSTM before fine-tuning. Same architecture, input `(200,6)`, output `(11)`. |
| `6th may/models/model_wrist_acc_gyro_cnnlstm.keras` | 10,105,270 | `031bd28ba525fd20...` | CNN-LSTM variant. Same input/output. |
| `6th may/models/model_all.keras` | 77,931,448 | `c05d3050f45c7313...` | 18-channel model (pocket+wrist), `input_shape=(200,18,1)`. **NOT compatible with the wrist-only pipeline contract.** |
| `6th may/models/model_all.h5` | 25,986,616 | `1b9ed405a929834e...` | Weights-only `.h5`, no model config — cannot be loaded standalone. |
| `6th may/anxiety1 - CNNBiLSTM.ipynb` | 936,817 | — | Trains BASE CNN-BiLSTM on `anxiety_dataset.csv`, saves to `models/model_wrist_acc_gyro_cnnbilstm.keras`. |
| `6th may/anxiety1 - finetuning.ipynb` | 1,065,958 | — | Same base training **plus** fine-tuning on `f/g/h/i/j_data_labeled.csv`, saves to `models/fine_tuned_model_1dcnnbilstm.keras`. |
| `6th may/anxiety_all.ipynb` | 720,711 | — | Trains the 18-channel pocket+wrist `model_all.keras`. |
| `6th may/data/anxiety_dataset.csv` | 134.9 MB | — | 709,582 rows. ADAMSense-style 26-column dataset, users `[2,3,5,6,7,8,10,14,15,16]`, 11 activities. **Mentor's training corpus.** Accel range `[-2, 2]` (g units). Gyro range `[-786, 783]` (deg/s). |
| `6th may/data/anxietycollected50hz.csv` | 10.1 MB | — | Unlabeled wrist-only test data, 7 cols (`timestamp, Ax_w..Gz_w`). |
| `6th may/data/anxietycollected24.csv` | 19.1 MB | — | Same shape as above, 24 Hz. |
| `f_data_labeled.csv` ... `j_data_labeled.csv` | — | — | **NOT PRESENT in repo.** Referenced by the fine-tuning cell as the 5 user CSVs used to produce `fine_tuned_model_1dcnnbilstm.keras`. Without these files we cannot reproduce or verify the fine-tuning step. |

## Mentor's Training Contract (Confirmed by `anxiety1 - finetuning.ipynb`)

Cells 0–34 build the base model; cells 45–51 fine-tune it.

```python
# Cell 22 — base training preprocessing
columns = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
x = df_acc_gyro[columns]
scaler = StandardScaler()
x = scaler.fit_transform(x)            # <-- StandardScaler IS APPLIED
scaled_x = pd.DataFrame(data=x, columns=columns)
scaled_x['label'] = y.values
```

```python
# Cell 23 — windowing
window_size = 200
slide_size = 100                       # 50% overlap
```

```python
# Cell 31 — model
Conv1D(16, kernel_size=2, activation='relu', input_shape=x_train[0].shape) ...
Dense(11, activation='softmax')        # 11 classes
loss = 'sparse_categorical_crossentropy'
optimizer = Adam(learning_rate=0.001)
```

```python
# Cell 48 — fine-tuning preprocessing (identical recipe)
feature_columns = ["Ax_w","Ay_w","Az_w","Gx_w","Gy_w","Gz_w"]
X_features = full_df[feature_columns]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_features)   # <-- StandardScaler again
```

```python
# Cell 53 — INFERENCE pipeline
def load_and_classify(file_path, model_path, window_size, slide_size):
    new_df = pd.read_csv(file_path)
    label_classes = ['ear_rubbing','forehead_rubbing','hair_pulling',
                     'hand_scratching','hand_tapping','knuckles_cracking',
                     'nail_biting','nape_rubbing','sitting','smoking','standing']
    columns = ["Ax_w","Ay_w","Az_w","Gx_w","Gy_w","Gz_w"]
    new_df_acc_gyro = new_df[columns]
    scaler = StandardScaler()
    scaler.fit(new_df_acc_gyro)               # <-- Refits scaler on each new dataset
    new_df_scaled = pd.DataFrame(scaler.transform(new_df_acc_gyro), columns=columns)
    ...
```

### Confirmed contract bullet points

| item | mentor | this repo's pipeline (`src/pipeline/production_pipeline.py`) |
| --- | --- | --- |
| Class order | `['ear_rubbing','forehead_rubbing','hair_pulling','hand_scratching','hand_tapping','knuckles_cracking','nail_biting','nape_rubbing','sitting','smoking','standing']` | matches |
| Feature order | `['Ax_w','Ay_w','Az_w','Gx_w','Gy_w','Gz_w']` | matches (`Ax,Ay,Az,Gx,Gy,Gz` after rename) |
| Window size | 200 | matches |
| Stride | 100 (50% overlap) | matches |
| **StandardScaler** | **Applied (fit on the inference dataset itself)** | **NOT APPLIED** ← contract mismatch |
| Accel unit | g (range ±2 in `anxiety_dataset.csv`) | m/s² (range ±30 in `all_users_data_labeled.csv`) ← scale mismatch (StandardScaler removes this difference) |
| Gyro unit | deg/s | deg/s | matches |

## Empirical Verification

### Test 1 — Apply StandardScaler in the notebook and re-evaluate

Same labeled `all_users_data_labeled.csv` windows, deployed `fine_tuned_model_1dcnnbilstm.keras`:

| pipeline | accuracy | macro F1 | classes used | top predictions |
| --- | --- | --- | --- | --- |
| Without StandardScaler (current contract) | 0.1057 | 0.0358 | 7 | hand_tapping:1913, ear_rubbing:1668, smoking:241 |
| With StandardScaler (mentor's contract) | **0.1449** | **0.0760** | **10** | hand_tapping:2654, forehead_rubbing:610, nape_rubbing:263 |

StandardScaler **does** improve accuracy and class diversity — confirming it is part of the missing contract — but accuracy stays far below useful (≪ RandomForest baseline ~50%).

### Test 2 — Run the same models on the mentor's own training data

Datasets the mentor trained on, with mentor's StandardScaler recipe:

| model | tested on | accuracy | macro F1 | top prediction (count of N=7094) | mean conf |
| --- | --- | --- | --- | --- | --- |
| `mentor_base_cnnbilstm` | `anxiety_dataset.csv` (training corpus) | **0.1207** | 0.0584 | hand_tapping: 5508 | 0.901 |
| `mentor_fine_tuned_1dcnnbilstm` | `anxiety_dataset.csv` | **0.1317** | 0.0717 | hand_tapping: 5563 | 0.858 |
| `mentor_cnnlstm` | `anxiety_dataset.csv` | **0.1170** | 0.0544 | hand_tapping: 4682 | 0.959 |

11-class random baseline = 9.09 %. "Always predict `hand_tapping`" baseline ≈ 9–13 %. The mentor's checkpoints predict `hand_tapping` for ~78 % of windows even on the data they were trained on. This is barely above chance.

### Test 3 — Cross-check with all 6th-may candidates on local labeled data

Same evaluation harness as `nb/model_checkpoint_sanity_check.ipynb`, with StandardScaler applied per mentor's contract:

| model | all_users acc (scaled) | user7 acc (scaled) |
| --- | --- | --- |
| `mentor_fine_tuned_1dcnnbilstm` | 0.145 | 0.131 |
| `mentor_base_cnnbilstm` | 0.124 | 0.126 |
| `mentor_cnnlstm` | 0.124 | 0.098 |

All three are near-random regardless of dataset.

## Key Conclusions

1. **The user's stated rule "no StandardScaler" was incorrect.** The mentor's training and inference notebooks both apply `StandardScaler.fit_transform`. The production pipeline omits this step, which is a real contract mismatch and explains part of the gap (10.6 % → 14.5 % when added).

2. **However, StandardScaler is not the dominant cause.** Even with the mentor's full contract correctly applied, all three mentor `(200,6)` checkpoints stay at ~12–14 % on **the mentor's own training corpus**, with predictions collapsed onto `hand_tapping`. A model that was actually trained successfully would not produce this output on its own training data.

3. **The deployed `fine_tuned_model_1dcnnbilstm.keras` is the SAME FILE the mentor provided** (SHA256 match across all three locations). The provenance question is settled — but the file itself appears to be a checkpoint that was never properly trained, or was saved at an early epoch before convergence, or was corrupted.

4. **The 18-channel `model_all.keras` (input `(200,18,1)`) is the only mentor model with substantially different architecture.** It cannot be used in the current 6-channel wrist-only pipeline without restructuring.

5. **The 5 fine-tuning CSVs (`f/g/h/i/j_data_labeled.csv`) are not in the repo.** Without them we cannot reproduce the fine-tuning step or verify whether it ever produced a model that learned.

## Recommended Next Steps

1. **Ask the mentor directly:** "Can you share the saved test accuracy / training history JSON / classification report for `fine_tuned_model_1dcnnbilstm.keras`? Or rerun cells 38–43 of `anxiety1 - finetuning.ipynb` and send the output of `model_cnnbilstm.evaluate(x_test, y_test)`?"

2. **Ask for the 5 fine-tuning CSVs** (`f/g/h/i/j_data_labeled.csv`) so the fine-tuning step can be reproduced and a working checkpoint built.

3. **Update the production pipeline contract** to include StandardScaler (only after the mentor confirms a working checkpoint and the contract is validated end-to-end). The simplest mentor-faithful implementation is to refit `StandardScaler` on the windowed inference dataset, matching `load_and_classify` in cell 53. Do not promote any change without first proving an accuracy improvement against the mentor's own confusion matrix.

4. **Treat the current deployment as not-fit-for-purpose** until a model can be produced that exceeds the RandomForest user-holdout baseline (~50 %) on the same labeled windows. The diagnostic notebook `nb/model_checkpoint_sanity_check.ipynb` is the regression test for any future replacement.

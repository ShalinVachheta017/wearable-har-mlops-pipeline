# 18 Paper vs Notebook vs Pipeline Contract Matrix

Diagnostic-only comparison of `ICTH_16.pdf`, the two mentor notebooks, and the current production pipeline. Production code was not modified.

Primary paper source inspected: `internal/papers/ICTH_16.pdf`. Text evidence was read from the existing extraction `internal/papers/triage/ICTH_16_extracted.txt`.

## Contract Matrix

| Contract row | ICTH_16.pdf methodology | `6th may/anxiety1 - CNNBiLSTM.ipynb` | `6th may/anxiety1 - finetuning.ipynb` | Current production pipeline | Contract verdict |
| --- | --- | --- | --- | --- | --- |
| feature columns | Six wrist IMU streams: three-axis accelerometer and three-axis gyroscope from the wrist-worn sensor. ADAMSense pocket and magnetometer streams are discarded. | `["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]`. | Same six columns in both base/fine-tune and inference helpers: `["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]`. | Stage 3 canonical pipeline columns are `["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]`; repo-level training constants also contain `Ax_w...Gz_w`. | Semantically aligned six channels, but notebook names use `_w`; production names use canonical non-suffixed names after ingestion/renaming. |
| accelerometer unit | Garmin accelerometer converted from milli-g to m/s^2 after timestamp synchronization and 50 Hz resampling. | Not explicit in the notebook code around model training; it consumes already prepared `Ax_w/Ay_w/Az_w` values, then applies `StandardScaler`. | Same: consumes prepared `Ax_w/Ay_w/Az_w`, then applies `StandardScaler`; `load_and_classify` consumes CSV columns directly and scales them. | Stage 3 detects accelerometer unit; if raw milliG, converts using `0.00980665`; if already m/s^2, no double conversion. | Production matches paper unit contract. Notebooks assume the input CSV is already in the expected physical unit before z-scoring. |
| gyroscope unit | PDF does not state an explicit gyroscope conversion. It only documents accelerometer conversion; gyroscope stream is collected and synchronized. | Consumes `Gx_w/Gy_w/Gz_w` as-is before `StandardScaler`. | Same. | Gyroscope is left unchanged and validated as deg/s (`max_gyroscope_dps`). | Aligned in practice: no gyro conversion documented in paper or notebooks; production treats gyro as deg/s/raw unchanged. |
| sampling rate | Garmin raw recorded at 100 Hz, downsampled to 50 Hz by resampling to 20 ms intervals and taking the mean. ADAMSense consistency target is 50 Hz. | The notebook uses `window_size = 200` as "4 seconds", implying 50 Hz; no raw FIT downsampling code is in this notebook section. | Same; fine-tuning function assumes input files are already at the working rate. | Ingestion config target is 50 Hz; pipeline config has `sampling_frequency_hz: 50` and resampling `target_hz: 50`. For already preprocessed labeled CSVs, it should not downsample again. | Paper and production align for raw Garmin ingestion; notebooks operate on already-prepared 50 Hz-style CSVs. |
| StandardScaler | Not documented in the paper methodology. The PDF describes physical-unit conversion and windowing, not external z-score scaling. | Yes. Applies `StandardScaler().fit_transform(x)` to the six-column full dataframe before windowing. | Yes. Base section uses `fit_transform`; `fine_tune_model` uses `scaler.fit_transform(X_features)` on full concatenated fine-tuning data. Inference helper fits a fresh scaler on each inference CSV. | Disabled by default. `enable_normalization: False`, `normalization_variant: "none"`, and Stage 3 reports `paper_aligned_no_external_scaler`. Saved-scaler normalization exists only for A/B diagnostics. | Notebook diverges from paper and production. This is a major training/inference contract difference. |
| scaler fit location | Not applicable / not specified. | Full labeled dataframe before train/test split. | Full labeled dataframe before split; fine-tuning: full concatenated fine-tuning dataframe before validation split; inference: full inference CSV. | If normalization is disabled: none. If enabled for diagnostics: external saved scaler stats from JSON, not freshly fitted on inference batch. | Notebook has data leakage in validation/test and batch-dependent inference. Production deliberately avoids this by default. |
| window size | 200 time steps, equivalent to 4 seconds at 50 Hz. | `window_size = 200`. | `window_size = 200`. | `window_size = 200`. | Aligned. |
| stride | 50% overlap; at 200 samples this means 100-sample stride. | `slide_size = 100`. Loop uses `range(0, len(df)-window_size, slide_size)`. | Same. | `overlap = 0.5`; step size computed as `window_size * (1 - overlap)` = 100. Production window count uses inclusive possible windows via `(n_samples - window_size) // step + 1`. | Mostly aligned. Small boundary-count difference: notebook loop excludes the final exact-end window because it uses `len(df)-window_size`, production includes valid exact-end windows. |
| tensor layout | The paper states fixed-size segments are used as model input. It does not specify memory/channel layout. Its prose says the 1D CNN accepts time-series data without requiring data reshaping. | `get_window` appends six channel arrays as `[Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w]` and then does `np.asarray(windows).reshape(-1, window_size, N_features)`. This is literal channel-major flattening into shape `(200, 6)`, not normal `(time, channel)`. Some later cells reshape to `(n, 200, 6, 1)`. | Same `get_window` pattern. Report 16 showed deployed `fine_tuned_model_1dcnnbilstm.keras` reaches `0.907840` accuracy only under this literal mentor reshape. | `UnifiedPreprocessor.create_windows` takes `df[sensor_cols].values` as `(N, C)` and uses `as_strided` with shape `(n_windows, window_size, n_sensors)` and strides preserving normal row-wise `(time, channel)` layout. | Major mismatch. The deployed checkpoint appears trained/evaluated against the notebook's literal reshape, while production creates normal row-wise windows. |
| label encoding | Paper class names: ear rubbing/scratching, forehead rubbing/scratching, hair pulling, hand rubbing/scratching, hand tapping, knuckle cracking, nail biting, nape rubbing/scratching, smoking, idle sitting, idle standing. | Base notebook uses `LabelEncoder().fit_transform(df_acc_gyro["Activity"])`, which sorts observed labels lexicographically; inference helper uses explicit `label_classes = ["ear_rubbing", ..., "standing"]` then `LabelEncoder().fit(label_classes)`. | Fine-tuning function uses explicit class list in expected order and one-hot encodes via `LabelEncoder().fit(label_classes)`. Earlier base section still uses `LabelEncoder` on `Activity`. | `src/utils/label_mapping.py` hard-codes expected ids 0..10: `ear_rubbing`, `forehead_rubbing`, `hair_pulling`, `hand_scratching`, `hand_tapping`, `knuckles_cracking`, `nail_biting`, `nape_rubbing`, `sitting`, `smoking`, `standing`. | Production and fine-tuning helper align on canonical order. Paper naming is semantic, not exact slug spelling. Earlier base notebook `LabelEncoder` can be risky if raw activity spellings differ. |
| model checkpoint | Describes a base 1DCNNBiLSTM pretrained on ADAMSense and a fine-tuned model evaluated with 5-fold CV on Garmin. Does not name a `.keras` file. Reports base wrist-source accuracy 89.11%, Garmin before fine-tuning 48.7/49%, after fine-tuning 87.0% +/- 1.2%. | Saves `models/model_wrist_acc_gyro_cnnbilstm.keras`; inference loads that path. | Loads `models/model_wrist_acc_gyro_cnnbilstm.keras` as base, then saves `models/fine_tuned_model_1dcnnbilstm.keras`. Later inference loads `models/fine_tuned_model_1dcnnbilstm.keras`. | Default model path is `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`; same SHA as `nb/` and `6th may/models/` copy. | Filename matches notebook fine-tuned save, but production preprocessing/layout did not match the notebook contract. |
| validation split / cross-validation | 5-fold cross-validation on custom Garmin dataset: four folds fine-tune, one fold test, repeated five times; final metrics are mean/std. | Uses `train_test_split(... test_size=0.3, random_state=0, stratify=y)` after scaling/windowing. No 5-fold CV in the inspected base path. | Fine-tuning function uses `train_test_split(... test_size=val_split, random_state=42, stratify=y_encoded)` after scaling/windowing. No 5-fold CV in the shown `fine_tune_model` function. | Production inference pipeline does not train or cross-validate. Separate repo training scripts support grouped CV, but that is not the active production inference path. | Paper and mentor notebooks diverge. The notebooks use holdout validation with scaler leakage; the paper reports 5-fold CV. |

## Paper Evidence From `ICTH_16.pdf`

Evidence was extracted from `internal/papers/triage/ICTH_16_extracted.txt`:

| Topic | Evidence |
| --- | --- |
| two-stage adaptation | Lines 100-103: model pretrained on public ADAMSense, then fine-tuned/evaluated on custom Garmin Venu 3 with cross-validation. |
| feature subset | Lines 128-134: ADAMSense full dataset has 25 features; only wrist accelerometer and gyroscope are extracted, discarding pocket and magnetometer streams, yielding six features. |
| Garmin raw processing | Lines 135-141: Garmin raw FIT to CSV; raw recorded at 100 Hz; downsampled to 50 Hz by 20 ms mean aggregation; streams synchronized; accelerometer converted from milli-g to m/s^2. |
| windowing | Lines 142-147: window size 200 time steps, 4 seconds at 50 Hz, 50% overlap. |
| validation | Lines 169-174: fine-tuning validated with 5-fold cross-validation, four folds for fine-tuning and one fold for testing. |
| reported performance | Lines 197-203 and 428-431: before fine-tuning about 48.7/49%; after fine-tuning 87.0% +/- 1.2%. |

## Notebook Evidence

| Topic | Evidence |
| --- | --- |
| feature columns | Both notebooks use `["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]`. |
| StandardScaler before windowing | `anxiety1 - CNNBiLSTM.ipynb` cell 21 and `anxiety1 - finetuning.ipynb` cell 22 use `scaler = StandardScaler(); x = scaler.fit_transform(x); scaled_x[...]`; `get_window(scaled_x, ...)` is called later. |
| full-data scaler leakage | `train_test_split(...)` is called after `get_window(...)`, so scaling occurs before split. Fine-tuning cell 48 does the same with concatenated `full_df`. |
| tensor layout | All inspected mentor `get_window` definitions append `[Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w]` arrays and call `.reshape(-1, window_size, N_features)`. Report 16 shows this is not row-wise equivalent. |
| notebook checkpoints | `CNNBiLSTM.ipynb` saves `models/model_wrist_acc_gyro_cnnbilstm.keras`; `finetuning.ipynb` saves `models/fine_tuned_model_1dcnnbilstm.keras`. |

## Production Evidence

| Topic | Evidence |
| --- | --- |
| default checkpoint | `src/config.py` sets `PRETRAINED_MODEL = models/pretrained/fine_tuned_model_1dcnnbilstm.keras` and `DEFAULT_MODEL_PATH = PRETRAINED_MODEL`. |
| production sensor columns | `DataTransformationConfig.sensors` defaults to `["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]`; `ModelInference.CHANNEL_ORDER` matches this order. |
| unit conversion | `DataTransformationConfig.enable_unit_conversion = True`, factor `0.00980665`; Stage 3 detects milliG vs m/s^2 and avoids double conversion. |
| no default StandardScaler | `config/pipeline_config.yaml` says paper-aligned preprocessing is milliG to m/s^2 to windowing, with no external StandardScaler; `enable_normalization: False`; Stage 3 returns `paper_aligned_no_external_scaler` when disabled. |
| production tensor layout | `src/preprocess_data.py` uses `sensor_values = df[sensor_cols].values.astype(np.float32)` and `as_strided(... shape=(n_windows, window_size, n_sensors), strides=(step*sample_stride, sample_stride, channel_stride))`. |
| label mapping | `src/utils/label_mapping.py` defines the canonical 0..10 order used by inference/evaluation. |

## High-Impact Mismatches

1. **Notebook vs paper/production scaler contract:** the mentor notebooks use a fresh `StandardScaler` fit on the full dataframe before windowing. The paper does not document this, and production disables it by default.
2. **Notebook vs production tensor layout:** the mentor `get_window` implementation creates channel-major flattened windows. Production creates normal row-wise `(time, channel)` windows. Report 16 showed this is decisive for `fine_tuned_model_1dcnnbilstm.keras`.
3. **Paper vs notebooks validation protocol:** the paper reports 5-fold cross-validation. The inspected notebooks use holdout `train_test_split` after full-data scaling/windowing.
4. **Window boundary difference:** notebook loops use `range(0, len(df)-window_size, stride)`; production includes every valid exact-end window. This is minor compared with scaler/layout.

## Practical Contract Implication

There are two different valid-looking contracts in the repo:

| Contract | Components |
| --- | --- |
| Paper / current production contract | physical units; accelerometer milliG to m/s^2 if needed; gyroscope unchanged; no external StandardScaler; window size 200; stride 100; normal row-wise `(time, channel)` tensor; canonical 11-class mapping. |
| Mentor notebook / deployed checkpoint contract | full-dataframe `StandardScaler` before windowing; literal channel-major `get_window(...).reshape(-1, 200, 6)` layout; same six wrist channels; same nominal class list; holdout split in notebooks, despite paper claiming 5-fold CV. |

The deployed `fine_tuned_model_1dcnnbilstm.keras` appears to belong to the mentor notebook contract, not the current production/paper-aligned contract. That explains why production row-wise physical-unit windows collapse, while report 16 recovers high accuracy only with the notebook scaler plus literal reshape layout.

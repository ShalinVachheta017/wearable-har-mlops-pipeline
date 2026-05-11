# 16 Tensor Layout Forensic

Diagnostic-only check for mentor notebook tensor memory/channel layout versus production pipeline layout. Production code and model files were not modified.

## Dataset And Scaling

| dataset | rows | feature_cols | label_col | window_size | stride | window_loop | n_windows | true_distribution | scaling |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| data\all_users_data_labeled.csv | 385326 | ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"] | activity | 200 | 100 | range(0, len(df) - window_size, slide_size) | 3852 | {"ear_rubbing": 346, "forehead_rubbing": 353, "hair_pulling": 355, "hand_scratching": 349, "hand_tapping": 333, "knuckles_cracking": 349, "nail_biting": 390, "nape_rubbing": 327, "sitting": 351, "smoking": 361, "standing": 338} | StandardScaler.fit_transform on all_users six wrist channels before windowing |

StandardScaler parameters fitted on `all_users_data_labeled.csv` before windowing:

| channel | mean | scale |
| --- | --- | --- |
| Ax_w | 3.218580 | 6.568332 |
| Ay_w | 1.282084 | 4.351464 |
| Az_w | -3.528949 | 3.236165 |
| Gx_w | 0.599312 | 49.930206 |
| Gy_w | 0.225205 | 14.811710 |
| Gz_w | 0.088668 | 14.166767 |

## Exact Mentor `get_window` Function

Selected exact mentor source: `6th may\anxiety1 - CNNBiLSTM.ipynb` cell `19`.


```python
def get_window(df, window_size, slide_size):
    '''
    Function that creates a window frame for the dataset
    
    Parameters:
    df: dataframe
    window_size: int, size of the window
    slide_size: int, size of the overlap
    
    Returns:
    windows: array, array of windows
    labels: array, array of labels
    '''
    N_features = 6
    
    windows = []
    labels = []
    for i in range(0, len(df)-window_size, slide_size):
        Ax_w = df['Ax_w'].values[i: i + window_size]
        Ay_w = df['Ay_w'].values[i: i + window_size]
        Az_w = df['Az_w'].values[i: i + window_size]
        Gx_w = df['Gx_w'].values[i: i + window_size]
        Gy_w = df['Gy_w'].values[i: i + window_size]
        Gz_w = df['Gz_w'].values[i: i + window_size]
        
        label = stats.mode(df['label'][i:i+window_size])[0]
        windows.append([Ax_w ,Ay_w ,Az_w,Gx_w ,Gy_w ,Gz_w ])
        labels.append(label)
        
    windows = np.asarray(windows).reshape(-1, window_size, N_features)
    labels = np.asarray(labels)
    
    return windows, labels
```

All discovered `get_window` definitions:

| file | cell | function | uses_channel_list_append | uses_plain_reshape |
| --- | --- | --- | --- | --- |
| 6th may\anxiety1 - CNNBiLSTM.ipynb | 19 | get_window | True | True |
| 6th may\anxiety1 - CNNBiLSTM.ipynb | 38 | get_window | True | True |
| 6th may\anxiety1 - finetuning.ipynb | 19 | get_window | True | True |
| 6th may\anxiety1 - finetuning.ipynb | 38 | get_window | True | True |
| 6th may\anxiety1 - finetuning.ipynb | 44 | get_window | True | True |

Other notebook window builders inspected:

| file | cell | function | uses_rowwise_assignment | uses_standard_scaler_helper |
| --- | --- | --- | --- | --- |
| nb\model_checkpoint_sanity_check.ipynb | 4 | build_windows_row_index | True | True |
| nb\model_checkpoint_sanity_check.ipynb | 4 | build_windows_segment_aware | True | True |

## Production Window Evidence

The production path is row-wise time-by-channel. `UnifiedPreprocessor.create_windows` takes `df[sensor_cols].values` with shape `(N, C)` and uses strides that preserve `(window, channel)` order.

| file | line | evidence |
| --- | --- | --- |
| src\components\data_transformation.py | 445 | X, y, metadata = preprocessor.create_windows(df, sensor_cols, data_format) |
| src\pipeline\production_pipeline.py | 302 | if art.production_X_path.exists(): |
| src\pipeline\production_pipeline.py | 303 | self.artifacts_manager.save_file(art.production_X_path, "data_transformation") |
| src\preprocess_data.py | 581 | def create_windows( |
| src\preprocess_data.py | 606 | sensor_values = df[sensor_cols].values.astype(np.float32)  # (N, C) |
| src\preprocess_data.py | 614 | from numpy.lib.stride_tricks import as_strided |
| src\preprocess_data.py | 618 | all_windows = as_strided( |
| src\preprocess_data.py | 620 | shape=(len(start_indices), self.window_size, n_sensors), |
| src\preprocess_data.py | 621 | strides=(self.step_size * stride_samples, stride_samples, stride_channels), |
| src\preprocess_data.py | 854 | X, _, metadata = preprocessor.create_windows(df_normalized, sensor_cols, data_format) |

## Layout Equivalence

| left | right | shape_left | shape_right | max_abs_diff | first_window_equal |
| --- | --- | --- | --- | --- | --- |
| A_normal_rowwise | B_mentor_exact_reshape | [3852, 200, 6] | [3852, 200, 6] | 28.113731 | False |
| A_normal_rowwise | C_mentor_transpose_safe | [3852, 200, 6] | [3852, 200, 6] | 0.000000 | True |
| B_mentor_exact_reshape | C_mentor_transpose_safe | [3852, 200, 6] | [3852, 200, 6] | 28.113731 | False |

Interpretation: mode `C_mentor_transpose_safe` is equivalent to normal row-wise layout. Mode `B_mentor_exact_reshape` is the literal mentor notebook memory layout and is not equivalent; it packs channel-major values into a `(200, 6)` tensor.

## Candidate Models

| model | path | input_shape | output_shape | parameters |
| --- | --- | --- | --- | --- |
| fine_tuned_model_1dcnnbilstm.keras | models\pretrained\fine_tuned_model_1dcnnbilstm.keras | [null, 200, 6] | [null, 11] | 499131 |
| garmin_finetuned_v1_20260504.keras | models\pretrained\garmin_finetuned_v1_20260504.keras | [null, 200, 6] | [null, 11] | 499131 |
| _finetune_best.keras | models\pretrained\_finetune_best.keras | [null, 200, 6] | [null, 11] | 499131 |

## Metrics By Model And Window Mode

| model | window_mode | accuracy | macro_F1 | classes_used | prediction_distribution |
| --- | --- | --- | --- | --- | --- |
| fine_tuned_model_1dcnnbilstm.keras | A_normal_rowwise | 0.144860 | 0.076023 | 10 | {"ear_rubbing": 119, "forehead_rubbing": 610, "hair_pulling": 28, "hand_scratching": 114, "hand_tapping": 2654, "knuckles_cracking": 5, "nail_biting": 5, "nape_rubbing": 263, "smoking": 53, "standing": 1} |
| fine_tuned_model_1dcnnbilstm.keras | B_mentor_exact_reshape | 0.907840 | 0.908931 | 11 | {"ear_rubbing": 287, "forehead_rubbing": 360, "hair_pulling": 386, "hand_scratching": 349, "hand_tapping": 336, "knuckles_cracking": 357, "nail_biting": 395, "nape_rubbing": 336, "sitting": 344, "smoking": 362, "standing": 340} |
| fine_tuned_model_1dcnnbilstm.keras | C_mentor_transpose_safe | 0.144860 | 0.076023 | 10 | {"ear_rubbing": 119, "forehead_rubbing": 610, "hair_pulling": 28, "hand_scratching": 114, "hand_tapping": 2654, "knuckles_cracking": 5, "nail_biting": 5, "nape_rubbing": 263, "smoking": 53, "standing": 1} |
| garmin_finetuned_v1_20260504.keras | A_normal_rowwise | 0.485462 | 0.454159 | 11 | {"ear_rubbing": 281, "forehead_rubbing": 716, "hair_pulling": 177, "hand_scratching": 372, "hand_tapping": 571, "knuckles_cracking": 150, "nail_biting": 410, "nape_rubbing": 313, "sitting": 414, "smoking": 64, "standing": 384} |
| garmin_finetuned_v1_20260504.keras | B_mentor_exact_reshape | 0.447300 | 0.390129 | 11 | {"ear_rubbing": 160, "forehead_rubbing": 115, "hair_pulling": 382, "hand_scratching": 385, "hand_tapping": 12, "knuckles_cracking": 170, "nail_biting": 69, "nape_rubbing": 322, "sitting": 762, "smoking": 941, "standing": 534} |
| garmin_finetuned_v1_20260504.keras | C_mentor_transpose_safe | 0.485462 | 0.454159 | 11 | {"ear_rubbing": 281, "forehead_rubbing": 716, "hair_pulling": 177, "hand_scratching": 372, "hand_tapping": 571, "knuckles_cracking": 150, "nail_biting": 410, "nape_rubbing": 313, "sitting": 414, "smoking": 64, "standing": 384} |
| _finetune_best.keras | A_normal_rowwise | 0.485462 | 0.454159 | 11 | {"ear_rubbing": 281, "forehead_rubbing": 716, "hair_pulling": 177, "hand_scratching": 372, "hand_tapping": 571, "knuckles_cracking": 150, "nail_biting": 410, "nape_rubbing": 313, "sitting": 414, "smoking": 64, "standing": 384} |
| _finetune_best.keras | B_mentor_exact_reshape | 0.447300 | 0.390129 | 11 | {"ear_rubbing": 160, "forehead_rubbing": 115, "hair_pulling": 382, "hand_scratching": 385, "hand_tapping": 12, "knuckles_cracking": 170, "nail_biting": 69, "nape_rubbing": 322, "sitting": 762, "smoking": 941, "standing": 534} |
| _finetune_best.keras | C_mentor_transpose_safe | 0.485462 | 0.454159 | 11 | {"ear_rubbing": 281, "forehead_rubbing": 716, "hair_pulling": 177, "hand_scratching": 372, "hand_tapping": 571, "knuckles_cracking": 150, "nail_biting": 410, "nape_rubbing": 313, "sitting": 414, "smoking": 64, "standing": 384} |

## Forensic Decision

| model | best_window_mode | best_accuracy | best_macro_F1 | mentor_exact_minus_normal_accuracy | transpose_safe_minus_normal_accuracy | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| fine_tuned_model_1dcnnbilstm.keras | B_mentor_exact_reshape | 0.907840 | 0.908931 | 0.762980 | 0.000000 | strong evidence this checkpoint expects mentor literal channel-major reshape |
| garmin_finetuned_v1_20260504.keras | A_normal_rowwise | 0.485462 | 0.454159 | -0.038162 | 0.000000 | no evidence this checkpoint benefits from mentor literal reshape |
| _finetune_best.keras | A_normal_rowwise | 0.485462 | 0.454159 | -0.038162 | 0.000000 | no evidence this checkpoint benefits from mentor literal reshape |

The deployed `fine_tuned_model_1dcnnbilstm.keras` improves from `0.144860` accuracy under normal row-wise scaled windows to `0.907840` under the literal mentor reshape. Because `C_mentor_transpose_safe` is bit-identical to normal row-wise layout, StandardScaler alone is not enough to recover the deployed checkpoint; the memory layout is the decisive difference in this test.

## First Window, First 5 Time Steps

### A_normal_rowwise

| t | Ax_w | Ay_w | Az_w | Gx_w | Gy_w | Gz_w |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.804146 | -1.417386 | 0.705015 | -0.375547 | 0.116961 | -0.031814 |
| 1 | 0.823678 | -1.378281 | 0.705015 | -0.427768 | 0.277646 | -0.113345 |
| 2 | 0.814997 | -1.333744 | 0.791669 | -0.388859 | 0.274105 | -0.125704 |
| 3 | 0.816444 | -1.314192 | 0.793163 | -0.343302 | 0.267011 | -0.129402 |
| 4 | 0.775210 | -1.304415 | 0.794657 | -0.469807 | 0.190228 | 0.049688 |

### B_mentor_exact_reshape

| t | Ax_w | Ay_w | Az_w | Gx_w | Gy_w | Gz_w |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.804146 | 0.823678 | 0.814997 | 0.816444 | 0.775210 | 0.770146 |
| 1 | 0.786785 | 0.767976 | 0.752061 | 0.814997 | 0.867805 | 0.891677 |
| 2 | 0.876486 | 0.838146 | 0.799082 | 0.754232 | 0.744827 | 0.708175 |
| 3 | 0.702870 | 0.691296 | 0.761466 | 1.068187 | 1.108697 | 1.006698 |
| 4 | 0.972698 | 0.962571 | 0.927847 | 0.830189 | 0.821508 | 0.826572 |

### C_mentor_transpose_safe

| t | Ax_w | Ay_w | Az_w | Gx_w | Gy_w | Gz_w |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.804146 | -1.417386 | 0.705015 | -0.375547 | 0.116961 | -0.031814 |
| 1 | 0.823678 | -1.378281 | 0.705015 | -0.427768 | 0.277646 | -0.113345 |
| 2 | 0.814997 | -1.333744 | 0.791669 | -0.388859 | 0.274105 | -0.125704 |
| 3 | 0.816444 | -1.314192 | 0.793163 | -0.343302 | 0.267011 | -0.129402 |
| 4 | 0.775210 | -1.304415 | 0.794657 | -0.469807 | 0.190228 | 0.049688 |

## Conclusion

- The mentor notebooks do contain a real tensor-layout bug/risk: `windows.append([Ax_w, ..., Gz_w])` followed by `.reshape(-1, 200, 6)` creates a channel-major flattened tensor, not normal time-by-channel windows.

- The production pipeline does not use that memory layout; it creates normal row-wise `(time, channel)` windows.

- `C_mentor_transpose_safe` exactly matches production/normal row-wise layout, while `B_mentor_exact_reshape` is different by construction.

- The deployed `fine_tuned_model_1dcnnbilstm.keras` was almost certainly trained/evaluated against the literal mentor reshape layout: it reaches `0.907840` accuracy and `0.908931` macro F1 only in that mode.

- `garmin_finetuned_v1_20260504.keras` and `_finetune_best.keras` do not show the same benefit from the literal mentor reshape; their best result in this diagnostic is the normal/transposed-safe layout at `0.485462` accuracy.

- Minimal production implication: do not guess-patch blindly, but the proven contract mismatch is now mentor literal channel-major reshape plus StandardScaler versus production normal row-wise layout without that notebook scaler.

# 17 Scaler Contract Forensic

Diagnostic-only audit of where `StandardScaler` is fitted/transformed relative to windowing in the mentor notebooks and the diagnostic sanity notebook. Production code was not modified.

## Short Answer

The mentor training/fine-tuning notebooks use contract **A: scale the full dataframe first, then create windows**.

They do **not** window first and then scale windows. They also do **not** fit the scaler on the train split only and transform validation/test with train-only statistics.

For validation/test inside the mentor notebooks, this creates feature-statistics leakage because validation/test rows contribute to the scaler mean and standard deviation before the split. For inference, the notebooks fit a fresh `StandardScaler` on the inference CSV itself, not a saved training scaler.

## Evidence Table

| notebook / function | scaler.fit source data | scaler.transform source data | fit scope | scaling placement | split placement | leakage risk |
| --- | --- | --- | --- | --- | --- | --- |
| `6th may/anxiety1 - CNNBiLSTM.ipynb`, cells 21, 24, 25 | `x = df_acc_gyro[["Ax_w","Ay_w","Az_w","Gx_w","Gy_w","Gz_w"]]` | same `x` through `scaler.fit_transform(x)` | full labeled dataframe before split | before `get_window(scaled_x, ...)` | `train_test_split(x, y, ...)` after windowing | yes; test rows shape scaler stats |
| `6th may/anxiety1 - finetuning.ipynb`, cells 22, 25, 26 | `x = df_acc_gyro[["Ax_w","Ay_w","Az_w","Gx_w","Gy_w","Gz_w"]]` | same `x` through `scaler.fit_transform(x)` | full labeled dataframe before split | before `get_window(scaled_x, ...)` | `train_test_split(x, y, ...)` after windowing | yes; test rows shape scaler stats |
| `6th may/anxiety1 - finetuning.ipynb`, `fine_tune_model`, cell 48 | `X_features = full_df[feature_columns]` after concatenating all `file_paths` | same `X_features` through `scaler.fit_transform(X_features)` | full concatenated fine-tuning dataframe before validation split | before `get_window(X_scaled_df, ...)` | `train_test_split(X, y_categorical, ...)` after windowing | yes; validation rows shape scaler stats |
| `6th may/anxiety1 - CNNBiLSTM.ipynb`, `load_and_classify`, cells 45-46 | `new_df_acc_gyro = new_df[columns]` | same `new_df_acc_gyro` through `scaler.transform(new_df_acc_gyro)` after `scaler.fit(new_df_acc_gyro)` | full inference CSV | before `get_window(new_df_scaled, ...)` | no train/test split in inference | not label leakage, but batch-dependent inference |
| `6th may/anxiety1 - finetuning.ipynb`, `load_and_classify`, cells 53-54 | `new_df_acc_gyro = new_df[columns]` | same `new_df_acc_gyro` through `scaler.transform(new_df_acc_gyro)` after `scaler.fit(new_df_acc_gyro)` | full inference CSV | before `get_window(new_df_scaled, ...)` | no train/test split in inference | not label leakage, but batch-dependent inference |
| `nb/model_checkpoint_sanity_check.ipynb`, `_maybe_scale` / window builders, cells 2 and 10 | full evaluation/inference feature matrix passed as `values` | same `values` through `sc.fit_transform(values)` | full evaluated dataset | before row-index or segment-aware window builders | no train/test split in that notebook | leaks evaluation-set feature stats if used as validation evidence |

## Exact Mentor Training Pattern

Both mentor notebooks contain the same core ordering:

```python
columns = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
x = df_acc_gyro[columns]
scaler = StandardScaler()
x = scaler.fit_transform(x)
scaled_x = pd.DataFrame(data=x, columns=columns)

y = df_acc_gyro["label"]
scaled_x["label"] = y.values

x, y = get_window(scaled_x, window_size, slide_size)
x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.3, random_state=0, stratify=y
)
```

This is full-dataframe scaling before windowing and before splitting.

## Exact Mentor Fine-Tuning Pattern

The fine-tuning function does the same thing after concatenating all labeled CSVs:

```python
full_df = pd.concat(dfs, ignore_index=True)
feature_columns = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
X_features = full_df[feature_columns]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_features)
X_scaled_df = pd.DataFrame(X_scaled, columns=feature_columns)
X_scaled_df["label"] = full_df["activity"].values

windows, labels, _ = get_window(X_scaled_df, window_size, slide_size)
X = windows.reshape(-1, window_size, 6, 1)

X_train, X_val, y_train, y_val = train_test_split(
    X, y_categorical, test_size=val_split, random_state=42, stratify=y_encoded
)
```

Again, this is full-dataset scaling before windowing and before validation split.

## Exact Mentor Inference Pattern

The inference helper does not reuse saved training scaler statistics. It fits a new scaler on the inference file:

```python
new_df_acc_gyro = new_df[columns]

scaler = StandardScaler()
scaler.fit(new_df_acc_gyro)
new_df_scaled = pd.DataFrame(scaler.transform(new_df_acc_gyro), columns=columns)

new_df_scaled["label"] = 0
windows, _, start_indices = get_window(new_df_scaled, window_size, slide_size)
```

This means inference predictions depend on the whole batch/file being classified. Adding or removing rows can change every standardized row and therefore every window prediction.

## Diagnostic Notebook Pattern

`nb/model_checkpoint_sanity_check.ipynb` mirrors the mentor scaler placement but uses row-wise diagnostic windows:

```python
def _maybe_scale(values: np.ndarray) -> np.ndarray:
    if APPLY_STANDARD_SCALER:
        sc = StandardScaler()
        return sc.fit_transform(values).astype(np.float32)
    return values.astype(np.float32)
```

The helper is called before `build_windows_row_index` and `build_windows_segment_aware` assign `feats[s:e]` into windows. So the diagnostic notebook also scales the full evaluated dataframe before windowing.

## A / B / C Classification

| option | description | found? | evidence |
| --- | --- | --- | --- |
| A | scale full dataframe first, then window | yes | `scaler.fit_transform(...)` produces `scaled_x` / `X_scaled_df`; `get_window(...)` is called afterward |
| B | window first, then scale windows | no | no requested notebook fits a scaler on `windows`, flattened windows, or `X_train.reshape(...)` before model input |
| C | scale train/test separately or train-only then transform val/test | no | the split happens after scaling and windowing; no requested mentor code fits `StandardScaler` on `X_train` only |

## Leakage Assessment

The mentor validation/test metrics have scaler leakage. The scaler is unsupervised, but it still uses validation/test feature distribution to compute mean and standard deviation before those rows are held out. This can inflate validation/test performance and makes metrics less representative of a true deployment setting.

The leakage is separate from the tensor-layout issue in `16_tensor_layout_forensic.md`. There are two contracts involved:

1. `StandardScaler` fitted on the full current dataframe before windowing.
2. For `fine_tuned_model_1dcnnbilstm.keras`, the literal mentor channel-major `get_window` reshape, not normal row-wise `(time, channel)` layout.

The scaler alone is not sufficient to reproduce the deployed model's mentor metrics. In `16_tensor_layout_forensic.md`, scaled normal row-wise windows still scored only `0.144860` accuracy for `fine_tuned_model_1dcnnbilstm.keras`, while scaled mentor-exact reshape scored `0.907840`.

## Exact Production-Equivalent Implementation

To reproduce the mentor scaler contract in production-style code, scaling must occur after unit conversion / column canonicalization and before window creation:

```python
from sklearn.preprocessing import StandardScaler

FEATURE_COLS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
WINDOW_SIZE = 200
STRIDE = 100


def mentor_scale_dataframe_before_windowing(df):
    out = df.copy()
    scaler = StandardScaler()
    out[FEATURE_COLS] = scaler.fit_transform(out[FEATURE_COLS])
    return out, scaler
```

For the deployed `fine_tuned_model_1dcnnbilstm.keras`, the full mentor-equivalent tensor builder is:

```python
def mentor_exact_windows_for_deployed_checkpoint(df):
    scaled_df, scaler = mentor_scale_dataframe_before_windowing(df)
    windows = []
    for start in range(0, len(scaled_df) - WINDOW_SIZE, STRIDE):
        end = start + WINDOW_SIZE
        channel_windows = [
            scaled_df["Ax_w"].values[start:end],
            scaled_df["Ay_w"].values[start:end],
            scaled_df["Az_w"].values[start:end],
            scaled_df["Gx_w"].values[start:end],
            scaled_df["Gy_w"].values[start:end],
            scaled_df["Gz_w"].values[start:end],
        ]
        windows.append(channel_windows)
    X = np.asarray(windows, dtype=np.float32).reshape(-1, WINDOW_SIZE, 6)
    return X, scaler
```

If the goal is a statistically clean production contract instead, the scaler should be fitted on training data only, saved with the model, and reused at inference. That is not what the mentor notebooks do, and it would not be a faithful reproduction of the current `fine_tuned_model_1dcnnbilstm.keras` contract without retraining or explicit model/scaler provenance.

## Conclusion

The scaler placement is confirmed: mentor training and fine-tuning scale the full six-channel dataframe first, then create windows, then split into train/test or train/validation. Mentor inference fits a fresh scaler on the full inference CSV before windowing. This explains part of the production mismatch, but the decisive recovery for `fine_tuned_model_1dcnnbilstm.keras` requires both the mentor scaler placement and the mentor literal tensor layout from report 16.

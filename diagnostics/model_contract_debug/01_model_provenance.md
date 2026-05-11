# 01 Model Provenance

## File Identity

| path | exists | size_bytes | sha256 | modified_time |
| --- | --- | --- | --- | --- |
| nb\fine_tuned_model_1dcnnbilstm.keras | True | 6095608 | 3a35f3bd6f74293bfe5e5a7599d1741430a6f76db26b46c0023355d09c1a5bc2 | 2025-05-05T14:04:56 |
| models\pretrained\fine_tuned_model_1dcnnbilstm.keras | True | 6095608 | 3a35f3bd6f74293bfe5e5a7599d1741430a6f76db26b46c0023355d09c1a5bc2 | 2025-05-05T14:04:56 |

Same SHA256 between notebook and deployed copies: `True`.

## Loaded Model

- Input shape: `[None, 200, 6]`
- Output shape: `[None, 11]`
- Parameter count: `499131`
- TensorFlow version: `2.20.0`
- Keras version: `3.11.3`
- Keras save metadata: `{"keras_version": "3.6.0", "date_saved": "2025-05-05@14:04:55"}`
- Compile/optimizer/loss metadata available: `True`

## Layer Summary

```text
Model: "sequential_1"
+--------------------------------------------------------------------------+
| Layer (type)                    | Output Shape           |       Param # |
|---------------------------------+------------------------+---------------|
| conv1d_2 (Conv1D)               | (None, 199, 16)        |           208 |
|---------------------------------+------------------------+---------------|
| batch_normalization             | (None, 199, 16)        |            64 |
| (BatchNormalization)            |                        |               |
|---------------------------------+------------------------+---------------|
| dropout_4 (Dropout)             | (None, 199, 16)        |             0 |
|---------------------------------+------------------------+---------------|
| conv1d_3 (Conv1D)               | (None, 198, 32)        |         1,056 |
|---------------------------------+------------------------+---------------|
| batch_normalization_1           | (None, 198, 32)        |           128 |
| (BatchNormalization)            |                        |               |
|---------------------------------+------------------------+---------------|
| dropout_5 (Dropout)             | (None, 198, 32)        |             0 |
|---------------------------------+------------------------+---------------|
| bidirectional (Bidirectional)   | (None, 198, 128)       |        49,664 |
|---------------------------------+------------------------+---------------|
| batch_normalization_2           | (None, 198, 128)       |           512 |
| (BatchNormalization)            |                        |               |
|---------------------------------+------------------------+---------------|
| dropout_6 (Dropout)             | (None, 198, 128)       |             0 |
|---------------------------------+------------------------+---------------|
| bidirectional_1 (Bidirectional) | (None, 198, 64)        |        41,216 |
|---------------------------------+------------------------+---------------|
| batch_normalization_3           | (None, 198, 64)        |           256 |
| (BatchNormalization)            |                        |               |
|---------------------------------+------------------------+---------------|
| dropout_7 (Dropout)             | (None, 198, 64)        |             0 |
|---------------------------------+------------------------+---------------|
| flatten_1 (Flatten)             | (None, 12672)          |             0 |
|---------------------------------+------------------------+---------------|
| dense_2 (Dense)                 | (None, 32)             |       405,536 |
|---------------------------------+------------------------+---------------|
| batch_normalization_4           | (None, 32)             |           128 |
| (BatchNormalization)            |                        |               |
|---------------------------------+------------------------+---------------|
| dropout_8 (Dropout)             | (None, 32)             |             0 |
|---------------------------------+------------------------+---------------|
| dense_3 (Dense)                 | (None, 11)             |           363 |
+--------------------------------------------------------------------------+
 Total params: 499,131 (1.90 MB)
 Trainable params: 498,587 (1.90 MB)
 Non-trainable params: 544 (2.12 KB)
```

## Provenance Classification

Most consistent with an externally supplied ADAMSense / ICTH-family base checkpoint, not the local Garmin fine-tuned final artifact. Evidence: `scripts/finetune_garmin.py` uses this file as BASE_MODEL and saves Garmin fine-tuning to `garmin_finetuned_v1_<date>.keras`; no searched notebook/script saves this exact deployed filename as a Garmin final model; the Keras archive metadata does not encode the training dataset or fold identity.

## Search Evidence

### Pattern `fine_tuned_model_1dcnnbilstm\.keras`

| file | line | snippet |
| --- | --- | --- |
| nb\batch_inference.py | 22 | MODEL_PATH   = Path("fine_tuned_model_1dcnnbilstm.keras") |
| nb\gpt explain.md | 20 | fine_tuned_model_1dcnnbilstm.keras |
| nb\gpt explain.md | 26 | ### 1. `fine_tuned_model_1dcnnbilstm.keras` |
| nb\gpt.ipynb | 57 | "MODEL_PATH = Path(\"fine_tuned_model_1dcnnbilstm.keras\")\n", |
| nb\INFERENCE_ANALYSIS_REPORT.md | 4 | **Model:** `fine_tuned_model_1dcnnbilstm.keras` — 1D CNN-BiLSTM, input `(200, 6)`, output `(11,)` |
| nb\INFERENCE_ANALYSIS_REPORT.md | 120 | **Why:** The model (`fine_tuned_model_1dcnnbilstm.keras`) was trained on raw physical units — accel in m/s², gyro in °/s. No StandardScaler was applied during training (`processing.ipynb` confirms this). The scaler transforms the input into |
| nb\INFERENCE_ANALYSIS_REPORT.md | 130 | nb/fine_tuned_model_1dcnnbilstm.keras |
| nb\INFERENCE_ANALYSIS_REPORT.md | 135 | models/pretrained/fine_tuned_model_1dcnnbilstm.keras |
| src\config.py | 51 | PRETRAINED_MODEL = MODELS_PRETRAINED / "fine_tuned_model_1dcnnbilstm.keras" |
| src\config.py | 93 | "path": "models/pretrained/fine_tuned_model_1dcnnbilstm.keras", |
| src\README.md | 92 | PRETRAINED_MODEL = MODELS_PRETRAINED / "fine_tuned_model_1dcnnbilstm.keras" |
| src\train.py | 345 | # v1 — matches  models/pretrained/fine_tuned_model_1dcnnbilstm.keras |
| data\prepared\predictions\predictions_20260503_161740_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_161757_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_161805_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_184619_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_185027_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_185035_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190649_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190653_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190655_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190658_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191407_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191410_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191412_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191415_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_114755_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_115019_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_115208_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_115422_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_140842_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_223017_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_224010_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230352_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230449_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230532_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230614_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230656_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230738_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_231101_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
### Pattern `model\.save`

| file | line | snippet |
| --- | --- | --- |
| src\train.py | 750 | model.save(model_path) |
| src\train.py | 755 | model.save(latest_path) |
| src\train.py | 1142 | base_model.save(_tmp_path) |
| src\components\model_retraining.py | 128 | model.save(save_path) |
| src\components\model_retraining.py | 201 | model.save(save_path) |
| src\components\model_retraining.py | 282 | model.save(save_path) |
| src\components\model_retraining.py | 359 | model.save(save_path) |
| src\components\model_retraining.py | 426 | model.save(save_path) |
| src\utils\main_utils.py | 129 | model.save(str(path)) |
| scripts\finetune_garmin.py | 253 | model.save(str(save_path)) |
| scripts\retrain_user_holdout_fast.py | 109 | model.save(model_path) |
### Pattern `save_model`

| file | line | snippet |
| --- | --- | --- |
| src\utils\main_utils.py | 112 | def save_model(model: Any, path: Union[str, Path]) -> Path: |
| src\utils\__init__.py | 28 | save_model, |
| reports\repo_audit\EXTERNAL_REVIEW_FILE_REPORT.md | 1579 | - `save_model` (function) - Save a Keras model to *path* (creates parent dirs). |
### Pattern `1DCNNBiLSTM|1dcnn.?bilstm`

| file | line | snippet |
| --- | --- | --- |
| nb\batch_inference.py | 22 | MODEL_PATH   = Path("fine_tuned_model_1dcnnbilstm.keras") |
| nb\gpt explain.md | 20 | fine_tuned_model_1dcnnbilstm.keras |
| nb\gpt explain.md | 26 | ### 1. `fine_tuned_model_1dcnnbilstm.keras` |
| nb\gpt explain.md | 737 | The ICTH paper states that the model uses a **1DCNN-BiLSTM architecture** for anxiety-related HAR on Garmin Venu 3 data, using only wrist accelerometer and gyroscope. The notebook uses exactly those six features: `Ax_w`, `Ay_w`, `Az_w`, `Gx |
| nb\gpt.ipynb | 57 | "MODEL_PATH = Path(\"fine_tuned_model_1dcnnbilstm.keras\")\n", |
| nb\INFERENCE_ANALYSIS_REPORT.md | 4 | **Model:** `fine_tuned_model_1dcnnbilstm.keras` — 1D CNN-BiLSTM, input `(200, 6)`, output `(11,)` |
| nb\INFERENCE_ANALYSIS_REPORT.md | 120 | **Why:** The model (`fine_tuned_model_1dcnnbilstm.keras`) was trained on raw physical units — accel in m/s², gyro in °/s. No StandardScaler was applied during training (`processing.ipynb` confirms this). The scaler transforms the input into |
| nb\INFERENCE_ANALYSIS_REPORT.md | 130 | nb/fine_tuned_model_1dcnnbilstm.keras |
| nb\INFERENCE_ANALYSIS_REPORT.md | 135 | models/pretrained/fine_tuned_model_1dcnnbilstm.keras |
| src\config.py | 51 | PRETRAINED_MODEL = MODELS_PRETRAINED / "fine_tuned_model_1dcnnbilstm.keras" |
| src\config.py | 93 | "path": "models/pretrained/fine_tuned_model_1dcnnbilstm.keras", |
| src\README.md | 92 | PRETRAINED_MODEL = MODELS_PRETRAINED / "fine_tuned_model_1dcnnbilstm.keras" |
| src\train.py | 333 | def create_1dcnn_bilstm(self) -> keras.Model: |
| src\train.py | 345 | # v1 — matches  models/pretrained/fine_tuned_model_1dcnnbilstm.keras |
| src\train.py | 534 | model = self.model_builder.create_1dcnn_bilstm() |
| src\train.py | 681 | model = self.model_builder.create_1dcnn_bilstm() |
| src\train.py | 889 | model, artifact_path="har_model", registered_model_name="har-1dcnn-bilstm" |
| src\train.py | 978 | base_model = self.model_builder.create_1dcnn_bilstm() |
| src\pipeline\pipeline_mlflow_logger.py | 124 | registered_model_name="har-1dcnn-bilstm", |
| src\pipeline\pipeline_mlflow_logger.py | 130 | logger.info("Model registered in MLflow Model Registry as 'har-1dcnn-bilstm'") |
| config\mlflow_config.yaml | 21 | model_name: "har-1dcnn-bilstm" |
| data\prepared\predictions\predictions_20260503_161740_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_161757_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_161805_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_184619_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_185027_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_185035_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190649_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190653_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190655_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190658_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191407_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191410_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191412_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191415_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_114755_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_115019_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_115208_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_115422_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_140842_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
### Pattern `fine_tuned`

| file | line | snippet |
| --- | --- | --- |
| nb\batch_inference.py | 22 | MODEL_PATH   = Path("fine_tuned_model_1dcnnbilstm.keras") |
| nb\gpt explain.md | 20 | fine_tuned_model_1dcnnbilstm.keras |
| nb\gpt explain.md | 26 | ### 1. `fine_tuned_model_1dcnnbilstm.keras` |
| nb\gpt.ipynb | 57 | "MODEL_PATH = Path(\"fine_tuned_model_1dcnnbilstm.keras\")\n", |
| nb\INFERENCE_ANALYSIS_REPORT.md | 4 | **Model:** `fine_tuned_model_1dcnnbilstm.keras` — 1D CNN-BiLSTM, input `(200, 6)`, output `(11,)` |
| nb\INFERENCE_ANALYSIS_REPORT.md | 120 | **Why:** The model (`fine_tuned_model_1dcnnbilstm.keras`) was trained on raw physical units — accel in m/s², gyro in °/s. No StandardScaler was applied during training (`processing.ipynb` confirms this). The scaler transforms the input into |
| nb\INFERENCE_ANALYSIS_REPORT.md | 130 | nb/fine_tuned_model_1dcnnbilstm.keras |
| nb\INFERENCE_ANALYSIS_REPORT.md | 135 | models/pretrained/fine_tuned_model_1dcnnbilstm.keras |
| src\config.py | 51 | PRETRAINED_MODEL = MODELS_PRETRAINED / "fine_tuned_model_1dcnnbilstm.keras" |
| src\config.py | 93 | "path": "models/pretrained/fine_tuned_model_1dcnnbilstm.keras", |
| src\README.md | 92 | PRETRAINED_MODEL = MODELS_PRETRAINED / "fine_tuned_model_1dcnnbilstm.keras" |
| src\train.py | 345 | # v1 — matches  models/pretrained/fine_tuned_model_1dcnnbilstm.keras |
| data\prepared\predictions\predictions_20260503_161740_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_161757_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_161805_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_184619_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_185027_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_185035_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190649_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190653_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190655_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_190658_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191407_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191410_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191412_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260503_191415_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_114755_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_115019_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_115208_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_115422_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_140842_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_223017_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_224010_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230352_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230449_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230532_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230614_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230656_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_230738_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
| data\prepared\predictions\predictions_20260504_231101_metadata.json | 3 | "model_path": "D:\\study apply\\ML Ops\\MasterArbeit_MLops\\models\\pretrained\\fine_tuned_model_1dcnnbilstm.keras", |
### Pattern `5-fold|5 fold`

| file | line | snippet |
| --- | --- | --- |
| src\train.py | 12 | - 5-Fold Stratified Cross-Validation (per ICTH_16 methodology) |
| src\train.py | 493 | self.logger.info("5-FOLD GROUPED CROSS-VALIDATION (USER HOLDOUT)") |
| reports\repo_audit\EXTERNAL_REVIEW_FILE_REPORT.md | 1391 | - `HARTrainer.run_cross_validation` (function) - Run 5-fold grouped cross-validation using user IDs as groups. |
| reports\repo_audit\FULL_REPOSITORY_AUDIT_2026-03-29.md | 109 | \| **Purpose** \| 5-fold grouped CV training with MLflow \| |
| docs\STAGE1_TO_3_CLOSURE_NOTES.md | 118 | 5. In the 5-fold CV setup, was the scaler/normalizer refit inside each fold, or not used at all? |
| docs\thesis\DATAFLOW_MAP_A15.md | 113 | \| **Logic** \| Supervised: cross-validation (5-fold) → train on full data → save model. Adaptation: AdaBN or TENT (off by default) \| |
| scripts\finetune_garmin.py | 128 | print(f"5-FOLD CROSS-VALIDATION (group=user)") |
| scripts\generate_chapter4_assets.py | 1576 | "Cross-validation    & 5-fold stratified (window-level) & Random seed: 42; not participant-wise", |
| scripts\generate_chapter4_assets.py | 1577 | "Cross-validation    & 5-fold grouped by participant & \\texttt{GroupKFold}; user IDs define held-out groups", |
| scripts\generate_chapter4_assets.py | 1580 | "Offline model development & Fused labeled CSV, then windowed and split 5-fold & Window-level folds & Yes & Model fitting, fold metrics, scaler fitting, and retained-model selection", |
| scripts\generate_chapter4_assets.py | 1584 | "5-fold stratified CV training & In scope & Internal window-level estimate under matched collection conditions", |
| scripts\generate_chapter4_assets.py | 1585 | "5-fold grouped CV training & In scope & Internal grouped-user estimate under matched collection conditions", |
| scripts\generate_chapter4_assets.py | 1592 | "\\texttt{src/train.py}, 5-fold \\texttt{StratifiedKFold} on windows with seed 42", |
| scripts\generate_chapter4_assets.py | 1593 | "\\texttt{src/train.py}, 5-fold \\texttt{GroupKFold} with participant IDs as groups", |
### Pattern `Garmin`

| file | line | snippet |
| --- | --- | --- |
| nb\gpt explain.md | 7 | This notebook runs inference for a trained **1D-CNN-BiLSTM Human Activity Recognition model** on raw Garmin Venu 3 accelerometer and gyroscope data. It also produces prediction confidence outputs and drift reports comparing production/unlab |
| nb\gpt explain.md | 9 | The notebook follows the preprocessing described in the ICTH paper: Garmin Venu 3 IMU data is converted to CSV, accelerometer data is converted from milli-g to m/s², accelerometer and gyroscope streams are synchronized by timestamp, data is |
| nb\gpt explain.md | 63 | These are the real inference inputs. They are unlabeled production data from Garmin. They require full preprocessing before being passed to the model. |
| nb\gpt explain.md | 149 | This is needed because Garmin CSV timestamps can appear in different formats. |
| nb\gpt explain.md | 153 | Some Garmin CSV rows may contain multiple samples inside list-like cells, for example: |
| nb\gpt explain.md | 201 | The accelerometer conversion is based on the paper and preprocessing notebook, where Garmin accelerometer data is converted from milli-g to m/s². |
| nb\gpt explain.md | 235 | This matches the paper, which says Garmin raw data was recorded at 100 Hz and downsampled to 50 Hz. |
| nb\gpt explain.md | 737 | The ICTH paper states that the model uses a **1DCNN-BiLSTM architecture** for anxiety-related HAR on Garmin Venu 3 data, using only wrist accelerometer and gyroscope. The notebook uses exactly those six features: `Ax_w`, `Ay_w`, `Az_w`, `Gx |
| nb\gpt explain.md | 739 | The paper states that Garmin raw data was downsampled to **50 Hz** by resampling to **20 ms intervals**, and the notebook does this using: |
| nb\gpt explain.md | 777 | raw Garmin production data |
| nb\gpt.ipynb | 52 | "# Raw production/unlabeled Garmin files.\n", |
| nb\gpt.ipynb | 97 | "# Based on your processing.ipynb: raw Garmin accelerometer is converted by 0.00981.\n", |
| nb\gpt.ipynb | 226 | "    Expands Garmin rows where one row contains multiple sample values as lists.\n", |
| nb\gpt.ipynb | 362 | "    Parses raw Garmin accelerometer or gyroscope production CSV.\n", |
| src\README.md | 124 | **Purpose:** STEP 1 - Process raw Garmin Excel files → Combined CSV |
| src\README.md | 139 | # Garmin stores [x,y,z] as strings like "[1.2, 3.4, 5.6]" |
| src\README.md | 230 | units = 'milliG'  # Garmin format |
| src\sensor_data_pipeline.py | 3 | Purpose: Process RAW sensor data from Excel files (Garmin watch format) |
| src\sensor_data_pipeline.py | 22 | Input: Raw Excel files from Garmin watch |
| src\sensor_data_pipeline.py | 158 | # Garmin uses verbose names, we simplify to x/y/z for processing |
| src\sensor_data_pipeline.py | 364 | (Success rate typically >99% for clean Garmin data) |
| src\api\app.py | 257 | look like raw Garmin milliG. Gyroscope channels are left unchanged. |
| src\components\data_ingestion.py | 232 | Description :   Parses Garmin list-like cell values into Python lists. |
| src\components\data_ingestion.py | 262 | Description :   Parses Garmin sample offset and x/y/z list columns. |
| src\components\data_ingestion.py | 277 | Description :   Drops Garmin rows whose list columns have mismatched sample counts. |
| src\components\data_ingestion.py | 297 | Description :   Explodes Garmin list rows into one row per sample. |
| src\entity\config_entity.py | 124 | enable_unit_conversion: bool = True  # milliG to m/s^2 when input is raw Garmin milliG. |
| src\pipeline\pipeline_console_reporter.py | 79 | ("1", "ingestion", "Raw Garmin CSV/XLSX -> fused_<dataset>_50Hz.csv"), |
| config\pipeline_config.yaml | 23 | # WHY: Raw Garmin accelerometer data can arrive as milliG. |
| reports\DECISION_REGISTER.csv | 7 | DEC-006    , Sampling frequency = 50 Hz                       , 50                                                               , Reproducibility , "config/pipeline_config.yaml:50, src/entity/config_entity.py:83"    , "SENSOR_SPEC"         |
| reports\EXTERNAL_REFERENCES.txt | 109 | REF_GARMIN_SDK       = https://developer.garmin.com/connect-iq/api-docs/ |
| reports\PAPER_SUPPORT_MAP.json | 18 | "claim": "Raw Garmin accelerometer and gyroscope sensor data at 50 Hz is fused via time-aligned merge with 1 ms tolerance into a single CSV.", |
| reports\PAPER_SUPPORT_MAP.json | 27 | "sensor_spec_note": "Garmin wearable IMU full-scale range: accel ±8g (~78.4 m/s²), gyro ±2000 dps. Chosen limits are conservative subset of hardware full-scale.", |
| reports\pipeline_stages_1-7_2026-04-27.txt | 383 | [  queue ] Stage  1: ingestion                       Raw Garmin CSV/XLSX -> fused_<dataset>_50Hz.csv (+ canonical sensor_fused_50Hz.csv) |
| reports\chapter4\ch4_channel_statistics.csv | 2 | labeled_garmin,Ax,385326,0,0.0,3.2185799853877644,6.568340538223167,-26.846117611083983,-1.534742832183838,6.371795654296875,8.757061004638672,31.954008098144527,10.29180383682251,-0.8175041675567627,-0.7471001744270325,m/s^2,raw |
| reports\chapter4\ch4_channel_statistics.csv | 3 | labeled_garmin,Ay,385326,0,0.0,1.2820835645532682,4.351469875708306,-16.560816405029293,-1.575284719467163,2.2045795917510986,4.109479904174805,41.8577024597168,5.684764623641968,-0.45323479175567627,-0.17863598465919495,m/s^2,raw |
| reports\chapter4\ch4_channel_statistics.csv | 4 | labeled_garmin,Az,385326,0,0.0,-3.5289485580602276,3.2361689464561727,-45.23043422790527,-6.072627067565918,-2.95412015914917,-1.5036520957946777,24.15029620056152,4.56897497177124,-0.2669643461704254,0.07725182175636292,m/s^2,raw |
| reports\chapter4\ch4_channel_statistics.csv | 5 | labeled_garmin,Gx,385326,0,0.0,0.5993119609628061,49.930270784056646,-818.9515686035156,-6.1182475090026855,0.6726930737495422,7.4766740798950195,835.1721496582031,13.594921588897705,-0.41319018602371216,23.447830200195312,deg/s,raw |
| reports\chapter4\ch4_channel_statistics.csv | 6 | labeled_garmin,Gy,385326,0,0.0,0.225205241641916,14.811729270912698,-302.4221649169922,-2.697268486022949,0.23731020092964172,3.037865400314331,206.9326705932617,5.73513388633728,-0.25359848141670227,23.923099517822266,deg/s,raw |
| reports\chapter4\ch4_channel_statistics.csv | 7 | labeled_garmin,Gz,385326,0,0.0,0.0886675181312073,14.166785138266743,-242.40753936767572,-2.919034957885742,0.059321194887161255,2.987071990966797,231.83546447753903,5.906106948852539,-0.22318929433822632,21.268369674682617,deg/s,raw |
### Pattern `ADAMSense|ADAM-sense`

| file | line | snippet |
| --- | --- | --- |
| reports\SYNTHETIC_PRODUCTION_DATASET_REPORT_2026-04-27.md | 4 | **Source**: Production unlabeled ADAMSENSE data (5 sessions, 669,159 samples) |
| reports\repo_audit\ARCHIVE_DUPLICATES.csv | 50 | 5b760ba8d47929d7504bf5cdd0f84126146ff591bb3ee45e05bd7d1c3ce2155a,ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf,archive/papers/by_topic/misc/ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf,952840,930.5 KB,4,YES,Cross-tree d |
| reports\repo_audit\ARCHIVE_DUPLICATES.csv | 51 | 5b760ba8d47929d7504bf5cdd0f84126146ff591bb3ee45e05bd7d1c3ce2155a,ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf,archive/papers/research_papers/76 papers/ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf,952840,930.5 KB,4,YES, |
| reports\repo_audit\ARCHIVE_DUPLICATES.csv | 52 | 5b760ba8d47929d7504bf5cdd0f84126146ff591bb3ee45e05bd7d1c3ce2155a,ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf,archive/research_papers/76 papers/ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf,952840,930.5 KB,4,YES,Cross-t |
| reports\repo_audit\ARCHIVE_DUPLICATES.csv | 53 | 5b760ba8d47929d7504bf5cdd0f84126146ff591bb3ee45e05bd7d1c3ce2155a,ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf,thesis/refs/papers_all/06_mental_health_anxiety/ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf,952840,930.5 KB |
| reports\repo_audit\ARCHIVE_DUPLICATES_REPORT.md | 186 | ### 10. ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf `[CROSS-TREE]` |
| reports\repo_audit\ARCHIVE_DUPLICATES_REPORT.md | 197 | - `archive\papers\by_topic\misc\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` |
| reports\repo_audit\ARCHIVE_DUPLICATES_REPORT.md | 198 | - `archive\papers\research_papers\76 papers\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` |
| reports\repo_audit\ARCHIVE_DUPLICATES_REPORT.md | 199 | - `archive\research_papers\76 papers\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` |
| reports\repo_audit\ARCHIVE_DUPLICATES_REPORT.md | 200 | - `thesis\refs\papers_all\06_mental_health_anxiety\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` |
| reports\repo_audit\ARCHIVE_DUPLICATES_REPORT.md | 1711 | ### 10. ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf |
| reports\repo_audit\ARCHIVE_DUPLICATES_REPORT.md | 1722 | - `archive\papers\by_topic\misc\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` |
| reports\repo_audit\ARCHIVE_DUPLICATES_REPORT.md | 1723 | - `archive\papers\research_papers\76 papers\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` |
| reports\repo_audit\ARCHIVE_DUPLICATES_REPORT.md | 1724 | - `archive\research_papers\76 papers\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` |
| reports\repo_audit\ARCHIVE_DUPLICATES_REPORT.md | 1728 | - `thesis\refs\papers_all\06_mental_health_anxiety\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` |
| reports\repo_audit\ARCHIVE_PAPERS_AUDIT.md | 116 | \| 2 \| `ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` \| |
| reports\repo_audit\ARCHIVE_SCAN_RAW.json | 27 | "('ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf', 952840)": [ |
| reports\repo_audit\ARCHIVE_SCAN_RAW.json | 28 | "archive\\papers\\by_topic\\misc\\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf", |
| reports\repo_audit\ARCHIVE_SCAN_RAW.json | 29 | "archive\\papers\\research_papers\\76 papers\\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf", |
| reports\repo_audit\ARCHIVE_SCAN_RAW.json | 30 | "archive\\research_papers\\76 papers\\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf" |
| reports\repo_audit\ARCHIVE_SCAN_RAW.json | 958 | "path": "archive\\papers\\by_topic\\misc\\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf", |
| reports\repo_audit\ARCHIVE_SCAN_RAW.json | 959 | "name": "ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf", |
| reports\repo_audit\ARCHIVE_SCAN_RAW.json | 1883 | "path": "archive\\papers\\research_papers\\76 papers\\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf", |
| reports\repo_audit\ARCHIVE_SCAN_RAW.json | 1884 | "name": "ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf", |
| reports\repo_audit\ARCHIVE_SCAN_RAW.json | 2268 | "path": "archive\\research_papers\\76 papers\\ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf", |
| reports\repo_audit\ARCHIVE_SCAN_RAW.json | 2269 | "name": "ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf", |
| reports\repo_inventory\REPO_INVENTORY_2026_05_05.md | 22 | 4. **`notebooks/` and `nb/` contain very large data files** — `nb/model_artifacts/model.joblib` is ~94 MB, `nb/ADAMSENSE.csv` is ~128 MB, `notebooks/synthetic_labeled.csv` is ~57 MB, and multiple raw CSVs in `nb/` exceed 50 MB each. These a |
| reports\repo_inventory\REPO_INVENTORY_2026_05_05.md | 160 | \| `nb/ADAMSENSE.csv` \| ~128.7 \| Gitignored \| KEEP_LOCAL_IGNORED \| |
| reports\repo_inventory\REPO_INVENTORY_2026_05_05.md | 289 | \| `ADAMSENSE.csv` (~128 MB), multiple raw CSVs \| gitignored data \| Local raw data copies \| |
| outputs\thesis_branch_comparison\current_branch_baseline\config_snapshot\pipeline_config.yaml | 33 | #      - ADAMSense wrist magnitude = 0.995 (approx 1g in g-units) |
| outputs\thesis_branch_comparison\mmd_governance_eval\config_snapshot\pipeline_config.yaml | 33 | #      - ADAMSense wrist magnitude = 0.995 (approx 1g in g-units) |
| outputs\thesis_branch_comparison\mmd_runtime_branch\config_snapshot\pipeline_config.yaml | 33 | #      - ADAMSense wrist magnitude = 0.995 (approx 1g in g-units) |
| outputs\thesis_branch_comparison\mmd_threshold_calibration\config_snapshot\pipeline_config.yaml | 33 | #      - ADAMSense wrist magnitude = 0.995 (approx 1g in g-units) |
| models\pretrained\garmin_finetuned_v1_20260504_report.json | 60 | "note": "Fine-tuned from ADAMSense base (ICTH_16 protocol). Use garmin_finetuned_v1_<date>.keras + this scaler for inference." |
| docs\FLEXIBLE_COLUMN_DETECTOR_2026-04-27.md | 61 | \| Training (ADAM-SENSE labeled) \| `Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w` \| ✓ Passes \| |
| docs\pretrained_model_exclusion_report.md | 35 | - ADAMSense-style reference `Az` mean: approximately −7.20 m/s² |
| docs\thesis\thesis_masterplan_v2_FINAL.md | 252 | ##### 4.2.1 Training data: ADAMSense (labeled, controlled lab) |
| docs\thesis\thesis_masterplan_v2_FINAL.md | 416 | Khan et al. (2021)            — ADAMSense dataset |
| scripts\finetune_garmin.py | 2 | Fine-tune the ADAMSense pre-trained model on Garmin Venu 3 labeled data. |
| scripts\finetune_garmin.py | 5 | 1. Load ADAMSense base  (fine_tuned_model_1dcnnbilstm.keras) |

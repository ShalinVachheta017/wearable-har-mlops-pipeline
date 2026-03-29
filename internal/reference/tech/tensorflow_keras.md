# TensorFlow / Keras

## What it is

TensorFlow with Keras is the deep learning framework used for model training and inference.

## Why it is used in this thesis

The HAR classifier architecture and adaptation/retraining logic are implemented around TensorFlow/Keras model loading, prediction, and training workflows.

## Repository locations

- `src/train.py`
- `src/run_inference.py`
- `src/components/model_retraining.py`
- `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`
- `pyproject.toml` (dependency)

## Role in this project

- Core:
  - Main model training/inference stack.
- Optional:
  - None for the core ML path; this is foundational.
- Future work:
  - Potential runtime optimization/export variants (for example TFLite and deployment-specific tuning).

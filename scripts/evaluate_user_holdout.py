"""
Honest user-holdout evaluation for the retrained HAR model.

Protocol:
  Train users: [1,2,3,4]
  Val user:    [5]
  Test user:   [6]

This script uses the canonical train-only scaler and creates windows per user
to avoid cross-user contamination.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, classification_report, f1_score

from src.utils.label_mapping import get_activity_classes, get_class_to_index
from src.utils.scaler import CANONICAL_SCALER_PATH, assert_scaler_integrity


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "all_users_data_labeled.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "retrained" / "har_model_20260327_213930.keras"
OUT_PATH = PROJECT_ROOT / "reports" / "honest_evaluation.json"

WINDOW_SIZE = 200
STEP_SIZE = 100
SENSOR_COLS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
TRAIN_USERS = [1, 2, 3, 4]
VAL_USERS = [5]
TEST_USERS = [6]


def _load_scaler_cfg() -> Dict:
    assert_scaler_integrity(CANONICAL_SCALER_PATH)
    return json.loads(CANONICAL_SCALER_PATH.read_text(encoding="utf-8"))


def _window_by_user(
    df: pd.DataFrame,
    sensor_cols: List[str],
    label_col: str,
    user_col: str = "User",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    X_all: List[np.ndarray] = []
    y_all: List[int] = []
    g_all: List[int] = []

    for user_id in sorted(df[user_col].dropna().unique()):
        df_u = df[df[user_col] == user_id].reset_index(drop=True)
        X_u = df_u[sensor_cols].values.astype(np.float32)
        y_u = df_u[label_col].values.astype(np.int32)

        for start in range(0, len(df_u) - WINDOW_SIZE + 1, STEP_SIZE):
            w = X_u[start : start + WINDOW_SIZE]
            yw = y_u[start : start + WINDOW_SIZE]
            majority = int(np.bincount(yw).argmax())
            X_all.append(w)
            y_all.append(majority)
            g_all.append(int(user_id))

    return np.array(X_all), np.array(y_all), np.array(g_all)


def _evaluate_split(
    model: tf.keras.Model,
    X: np.ndarray,
    y: np.ndarray,
    label_to_activity: Dict[int, str],
) -> Dict:
    probs = model.predict(X, verbose=0)
    pred = np.argmax(probs, axis=1)
    return {
        "n_windows": int(len(y)),
        "accuracy": float(accuracy_score(y, pred)),
        "f1_macro": float(f1_score(y, pred, average="macro")),
        "classification_report": classification_report(
            y,
            pred,
            labels=list(range(len(label_to_activity))),
            target_names=[label_to_activity[i] for i in range(len(label_to_activity))],
            zero_division=0,
            output_dict=True,
        ),
    }


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing dataset: {DATA_PATH}")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing model: {MODEL_PATH}")

    df = pd.read_csv(DATA_PATH)
    missing = [c for c in [*SENSOR_COLS, "activity", "User"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    label_to_activity = get_activity_classes()
    activity_to_label = get_class_to_index()
    unknown = sorted(set(df["activity"].unique()) - set(activity_to_label.keys()))
    if unknown:
        raise ValueError(f"Unknown activities in dataset: {unknown}")
    df["label_idx"] = df["activity"].map(activity_to_label).astype(int)

    scaler_cfg = _load_scaler_cfg()
    mean = np.asarray(scaler_cfg["scaler_mean"], dtype=np.float32)
    scale = np.asarray(scaler_cfg["scaler_scale"], dtype=np.float32)
    raw = df[SENSOR_COLS].values.astype(np.float32)
    df.loc[:, SENSOR_COLS] = (raw - mean) / np.where(scale == 0, 1.0, scale)

    X, y, groups = _window_by_user(df, sensor_cols=SENSOR_COLS, label_col="label_idx")
    train_mask = np.isin(groups, TRAIN_USERS)
    val_mask = np.isin(groups, VAL_USERS)
    test_mask = np.isin(groups, TEST_USERS)

    model = tf.keras.models.load_model(str(MODEL_PATH), compile=False)
    res_train = _evaluate_split(model, X[train_mask], y[train_mask], label_to_activity)
    res_val = _evaluate_split(model, X[val_mask], y[val_mask], label_to_activity)
    res_test = _evaluate_split(model, X[test_mask], y[test_mask], label_to_activity)

    print("\nSplit     Users    Windows    Accuracy    F1_macro    Note")
    print("---------------------------------------------------------------")
    print(
        f"Train     1-4      {res_train['n_windows']:>7}    "
        f"{res_train['accuracy']*100:>7.2f}%    {res_train['f1_macro']:>7.3f}    IN-SAMPLE"
    )
    print(
        f"Val       5        {res_val['n_windows']:>7}    "
        f"{res_val['accuracy']*100:>7.2f}%    {res_val['f1_macro']:>7.3f}    HONEST"
    )
    print(
        f"Test      6        {res_test['n_windows']:>7}    "
        f"{res_test['accuracy']*100:>7.2f}%    {res_test['f1_macro']:>7.3f}    HONEST"
    )

    print("\nValidation (User 5) classification report:")
    print(
        classification_report(
            y[val_mask],
            np.argmax(model.predict(X[val_mask], verbose=0), axis=1),
            labels=list(range(len(label_to_activity))),
            target_names=[label_to_activity[i] for i in range(len(label_to_activity))],
            zero_division=0,
        )
    )
    print("Test (User 6) classification report:")
    print(
        classification_report(
            y[test_mask],
            np.argmax(model.predict(X[test_mask], verbose=0), axis=1),
            labels=list(range(len(label_to_activity))),
            target_names=[label_to_activity[i] for i in range(len(label_to_activity))],
            zero_division=0,
        )
    )

    payload = {
        "dataset": str(DATA_PATH),
        "model_path": str(MODEL_PATH),
        "scaler_path": str(CANONICAL_SCALER_PATH),
        "window_size": WINDOW_SIZE,
        "step_size": STEP_SIZE,
        "train_users": TRAIN_USERS,
        "val_users": VAL_USERS,
        "test_users": TEST_USERS,
        "results": {
            "train": res_train,
            "val": res_val,
            "test": res_test,
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()

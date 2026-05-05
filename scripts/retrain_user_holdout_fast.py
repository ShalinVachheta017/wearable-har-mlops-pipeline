"""Direct user-holdout retraining (no MLflow, no checkpoint callbacks)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from src.train import HARModelBuilder, TrainingConfig
from src.utils.common import get_timestamp
from src.utils.label_mapping import get_class_to_index
from src.utils.scaler import CANONICAL_SCALER_PATH, assert_scaler_integrity


WINDOW_SIZE = 200
STEP_SIZE = 100
SENSOR_COLS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
TRAIN_USERS = [1, 2, 3, 4]
VAL_USERS = [5]
TEST_USERS = [6]


def _window_by_user(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    X_all, y_all, g_all = [], [], []
    for user_id in sorted(df["User"].dropna().unique()):
        d = df[df["User"] == user_id].reset_index(drop=True)
        X_u = d[SENSOR_COLS].values.astype(np.float32)
        y_u = d["label_idx"].values.astype(np.int32)
        for start in range(0, len(d) - WINDOW_SIZE + 1, STEP_SIZE):
            w = X_u[start : start + WINDOW_SIZE]
            yw = y_u[start : start + WINDOW_SIZE]
            X_all.append(w)
            y_all.append(int(np.bincount(yw).argmax()))
            g_all.append(int(user_id))
    return np.array(X_all), np.array(y_all), np.array(g_all)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--learning-rate", type=float, default=0.001)
    p.add_argument("--data", type=str, default="data/all_users_data_labeled.csv")
    p.add_argument("--output-dir", type=str, default="models/retrained")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    assert_scaler_integrity(CANONICAL_SCALER_PATH)
    scaler_cfg = json.loads(CANONICAL_SCALER_PATH.read_text(encoding="utf-8"))
    mean = np.asarray(scaler_cfg["scaler_mean"], dtype=np.float32)
    scale = np.asarray(scaler_cfg["scaler_scale"], dtype=np.float32)

    df = pd.read_csv(data_path)
    activity_to_label = get_class_to_index()
    df["label_idx"] = df["activity"].map(activity_to_label).astype(int)
    raw = df[SENSOR_COLS].values.astype(np.float32)
    df.loc[:, SENSOR_COLS] = (raw - mean) / np.where(scale == 0, 1.0, scale)

    X, y, groups = _window_by_user(df)
    train_mask = np.isin(groups, TRAIN_USERS)
    val_mask = np.isin(groups, VAL_USERS)
    test_mask = np.isin(groups, TEST_USERS)

    X_train, y_train = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    cfg = TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        output_dir=out_dir,
    )
    model = HARModelBuilder(cfg).create_1dcnn_bilstm()

    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        verbose=2,
    )

    val_probs = model.predict(X_val, verbose=0)
    test_probs = model.predict(X_test, verbose=0)
    val_pred = np.argmax(val_probs, axis=1)
    test_pred = np.argmax(test_probs, axis=1)

    metrics = {
        "val_accuracy": float(accuracy_score(y_val, val_pred)),
        "test_accuracy": float(accuracy_score(y_test, test_pred)),
        "f1_macro_val": float(f1_score(y_val, val_pred, average="macro")),
        "f1_macro_test": float(f1_score(y_test, test_pred, average="macro")),
    }

    ts = get_timestamp()
    model_path = out_dir / f"har_model_fixed_{ts}.keras"
    model.save(model_path)

    report = {
        "timestamp": ts,
        "model_path": str(model_path),
        "fit_users": TRAIN_USERS,
        "val_users": VAL_USERS,
        "test_users": TEST_USERS,
        "scaler_path": str(CANONICAL_SCALER_PATH),
        "window_size": WINDOW_SIZE,
        "step_size": STEP_SIZE,
        "gravity_removal_applied": False,
        "val_accuracy": metrics["val_accuracy"],
        "test_accuracy": metrics["test_accuracy"],
        "f1_macro_val": metrics["f1_macro_val"],
        "f1_macro_test": metrics["f1_macro_test"],
        "history": {
            "accuracy": [float(x) for x in history.history.get("accuracy", [])],
            "val_accuracy": [float(x) for x in history.history.get("val_accuracy", [])],
            "loss": [float(x) for x in history.history.get("loss", [])],
            "val_loss": [float(x) for x in history.history.get("val_loss", [])],
        },
    }
    report_path = out_dir / f"training_report_fixed_{ts}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

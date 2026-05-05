"""
Gravity-removal ablation on all_users_data_labeled.csv.

Configs tested:
  A: No gravity removal + zscore
  B: Gravity removal + zscore
  C: No gravity removal + no zscore
  D: Gravity removal + no zscore
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, f1_score

from src.components.data_transformation import remove_gravity_highpass
from src.utils.label_mapping import get_activity_classes, get_class_to_index
from src.utils.scaler import CANONICAL_SCALER_PATH, assert_scaler_integrity


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "all_users_data_labeled.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "retrained" / "har_model_20260327_213930.keras"

WINDOW_SIZE = 200
STEP_SIZE = 100
SENSOR_COLS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]


@dataclass
class Config:
    name: str
    gravity: bool
    zscore: bool


CONFIGS = [
    Config("A", gravity=False, zscore=True),
    Config("B", gravity=True, zscore=True),
    Config("C", gravity=False, zscore=False),
    Config("D", gravity=True, zscore=False),
]


def _window_by_user(
    X_rows: np.ndarray,
    y_rows: np.ndarray,
    users: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    X_out: List[np.ndarray] = []
    y_out: List[int] = []
    for u in sorted(np.unique(users)):
        idx = np.where(users == u)[0]
        X_u = X_rows[idx]
        y_u = y_rows[idx]
        for start in range(0, len(X_u) - WINDOW_SIZE + 1, STEP_SIZE):
            w = X_u[start : start + WINDOW_SIZE]
            yw = y_u[start : start + WINDOW_SIZE]
            X_out.append(w)
            y_out.append(int(np.bincount(yw).argmax()))
    return np.array(X_out), np.array(y_out)


def _run_config(
    model: tf.keras.Model,
    X_raw: np.ndarray,
    y_rows: np.ndarray,
    users: np.ndarray,
    scaler_cfg: Dict,
    cfg: Config,
    label_to_activity: Dict[int, str],
) -> Dict:
    X_proc = X_raw.copy()
    if cfg.gravity:
        X_proc = remove_gravity_highpass(X_proc, fs=50.0, cutoff=0.3)
    if cfg.zscore:
        mean = np.asarray(scaler_cfg["scaler_mean"], dtype=np.float32)
        scale = np.asarray(scaler_cfg["scaler_scale"], dtype=np.float32)
        X_proc = (X_proc - mean) / np.where(scale == 0, 1.0, scale)

    X_w, y_w = _window_by_user(X_proc, y_rows, users)
    probs = model.predict(X_w, verbose=0)
    pred = np.argmax(probs, axis=1)
    conf = probs.max(axis=1)
    counts = np.bincount(pred, minlength=len(label_to_activity))
    dom_idx = int(np.argmax(counts))

    return {
        "name": cfg.name,
        "gravity": cfg.gravity,
        "zscore": cfg.zscore,
        "n_windows": int(len(y_w)),
        "accuracy": float(accuracy_score(y_w, pred)),
        "f1_macro": float(f1_score(y_w, pred, average="macro")),
        "dominant_class": label_to_activity[dom_idx],
        "dominant_pct": float(counts[dom_idx] / len(pred) * 100.0),
        "mean_confidence": float(np.mean(conf)),
    }


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(DATA_PATH)
    if not MODEL_PATH.exists():
        raise FileNotFoundError(MODEL_PATH)

    assert_scaler_integrity(CANONICAL_SCALER_PATH)
    scaler_cfg = json.loads(CANONICAL_SCALER_PATH.read_text(encoding="utf-8"))

    df = pd.read_csv(DATA_PATH)
    missing = [c for c in [*SENSOR_COLS, "activity", "User"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    activity_to_label = get_class_to_index()
    label_to_activity = get_activity_classes()
    df["label_idx"] = df["activity"].map(activity_to_label).astype(int)

    X_raw = df[SENSOR_COLS].values.astype(np.float32)
    y_rows = df["label_idx"].values.astype(np.int32)
    users = df["User"].values.astype(np.int32)

    # Az per activity before/after gravity removal.
    az_before = df.groupby("activity")["Az_w"].mean().sort_index()
    X_gravity = remove_gravity_highpass(X_raw, fs=50.0, cutoff=0.3)
    df_after = df.copy()
    df_after["Az_after"] = X_gravity[:, 2]
    az_after = df_after.groupby("activity")["Az_after"].mean().sort_index()
    spread_before = float(az_before.max() - az_before.min())
    spread_after = float(az_after.max() - az_after.min())

    print("Mean Az per activity BEFORE gravity removal:")
    for act, val in az_before.items():
        print(f"  {act:22s} {val: .4f}")
    print("Mean Az per activity AFTER gravity removal:")
    for act, val in az_after.items():
        print(f"  {act:22s} {val: .4f}")
    print(f"Spread reduction: {spread_before:.4f} -> {spread_after:.4f}")

    model = tf.keras.models.load_model(str(MODEL_PATH), compile=False)
    results = [
        _run_config(model, X_raw, y_rows, users, scaler_cfg, cfg, label_to_activity)
        for cfg in CONFIGS
    ]

    print("\nConfig   Gravity   Zscore   Windows   Accuracy   F1_macro   Dominant      Conf")
    print("-------------------------------------------------------------------------")
    for r in results:
        print(
            f"{r['name']:5s}   {str(r['gravity']):7s}   {str(r['zscore']):6s}   "
            f"{r['n_windows']:7d}   {r['accuracy']*100:7.2f}%   {r['f1_macro']:8.3f}   "
            f"{r['dominant_class'][:12]:12s} {r['mean_confidence']*100:6.2f}%"
        )

    best_with = max([r for r in results if r["gravity"]], key=lambda r: r["f1_macro"])
    best_without = max([r for r in results if not r["gravity"]], key=lambda r: r["f1_macro"])
    gain = best_with["f1_macro"] - best_without["f1_macro"]
    recommendation = "YES" if gain > 0.02 else "NO"
    print(
        f"\nUse gravity removal: {recommendation} "
        f"(best with gravity F1={best_with['f1_macro']:.3f}, "
        f"best without F1={best_without['f1_macro']:.3f}, gain={gain:.3f})"
    )


if __name__ == "__main__":
    main()

"""Calibrate and sanity-check DriftMonitor thresholds."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import tensorflow as tf

from src.monitoring.drift_monitor import CHANNELS, DriftMonitor
from src.utils.scaler import CANONICAL_SCALER_PATH, assert_scaler_integrity


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "all_users_data_labeled.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "retrained" / "har_model_20260327_213930.keras"
PRODUCTION_X_PATH = PROJECT_ROOT / "data" / "prepared" / "production_X.npy"
REFERENCE_PATH = PROJECT_ROOT / "models" / "drift_reference.json"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "drift_calibration_summary.json"

WINDOW_SIZE = 200
STEP_SIZE = 100
SENSOR_COLS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]


def _window_by_user(X_rows: np.ndarray, users: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    X_out: List[np.ndarray] = []
    g_out: List[int] = []
    for u in sorted(np.unique(users)):
        idx = np.where(users == u)[0]
        X_u = X_rows[idx]
        for start in range(0, len(X_u) - WINDOW_SIZE + 1, STEP_SIZE):
            X_out.append(X_u[start : start + WINDOW_SIZE])
            g_out.append(int(u))
    return np.array(X_out), np.array(g_out)


def _format(v: float) -> str:
    return "nan" if np.isnan(v) else f"{v:.3f}"


def main() -> None:
    assert_scaler_integrity(CANONICAL_SCALER_PATH)
    scaler_cfg = json.loads(CANONICAL_SCALER_PATH.read_text(encoding="utf-8"))

    if not DATA_PATH.exists():
        raise FileNotFoundError(DATA_PATH)
    if not MODEL_PATH.exists():
        raise FileNotFoundError(MODEL_PATH)

    df = pd.read_csv(DATA_PATH)
    missing = [c for c in [*SENSOR_COLS, "User"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    X_rows = df[SENSOR_COLS].values.astype(np.float32)
    users = df["User"].values.astype(np.int32)
    mean = np.asarray(scaler_cfg["scaler_mean"], dtype=np.float32)
    scale = np.asarray(scaler_cfg["scaler_scale"], dtype=np.float32)
    X_rows = (X_rows - mean) / np.where(scale == 0, 1.0, scale)

    X_w, groups = _window_by_user(X_rows, users)
    train_mask = np.isin(groups, [1, 2, 3, 4])
    user5_mask = groups == 5
    user6_mask = groups == 6

    X_train = X_w[train_mask]
    X_user5 = X_w[user5_mask]
    X_user6 = X_w[user6_mask]

    model = tf.keras.models.load_model(str(MODEL_PATH), compile=False)
    p_train = model.predict(X_train, verbose=0)
    p_user5 = model.predict(X_user5, verbose=0)

    monitor = DriftMonitor(reference_path=REFERENCE_PATH)
    monitor.calibrate(X_train, train_probabilities=p_train, save=True)
    user5_result = monitor.check(X_user5, probabilities=p_user5)

    if PRODUCTION_X_PATH.exists():
        X_prod = np.load(PRODUCTION_X_PATH)
        prod_source = str(PRODUCTION_X_PATH)
    else:
        X_prod = X_user6
        prod_source = "fallback:user6_windows (production_X.npy not found)"
    p_prod = model.predict(X_prod, verbose=0)
    prod_result = monitor.check(X_prod, probabilities=p_prod)

    print("\nChannel   Train->User5 PSI   Train->Production PSI   Flag?")
    print("-------------------------------------------------------------")
    for ch in CHANNELS:
        p_u5 = float(user5_result["psi_per_channel"][ch])
        p_pr = float(prod_result["psi_per_channel"][ch])
        flag = "Y" if (p_u5 > monitor.psi_threshold or p_pr > monitor.psi_threshold) else "N"
        print(f"{ch:7s} {_format(p_u5):>16s} {_format(p_pr):>22s}   {flag}")

    summary = {
        "reference_path": str(REFERENCE_PATH),
        "production_source": prod_source,
        "psi_threshold": monitor.psi_threshold,
        "user5": user5_result,
        "production": prod_result,
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSaved: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()

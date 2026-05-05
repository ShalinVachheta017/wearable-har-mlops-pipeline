"""Refit StandardScaler using train users (1-4) only.

Writes data/prepared/scaler_train_only.json with explicit provenance fields
(fit_users, val_users, test_users, fit_dataset, created_at). Prints before/
after diffs against the leaky all-users scaler at data/prepared/config.json.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path("D:/study apply/ML Ops/MasterArbeit_MLops")
DATA_CSV = ROOT / "data/all_users_data_labeled.csv"
OUT_PATH = ROOT / "data/prepared/scaler_train_only.json"
OLD_PATH = ROOT / "data/prepared/config.json"

SENSOR_COLS_CSV = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
SENSOR_COLS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
TRAIN_USERS = [1, 2, 3, 4]
VAL_USERS = [5]
TEST_USERS = [6]


def main() -> None:
    df = pd.read_csv(DATA_CSV)
    df = df.rename(columns=dict(zip(SENSOR_COLS_CSV, SENSOR_COLS)))
    print(f"Loaded {len(df):,} rows from {DATA_CSV.name}")

    mask_train = df["User"].isin(TRAIN_USERS)
    df_train = df[mask_train]
    print(f"Train slice: {len(df_train):,} rows, users={sorted(df_train['User'].unique().tolist())}")

    sc = StandardScaler().fit(df_train[SENSOR_COLS].values)
    new_mean = sc.mean_
    new_scale = sc.scale_

    with open(OLD_PATH) as f:
        old_cfg = json.load(f)
    old_mean = np.array(old_cfg["scaler_mean"])
    old_scale = np.array(old_cfg["scaler_scale"])

    print("\nBefore vs After (channel-wise):")
    print(f"{'ch':<4} {'old mean':>12} {'new mean':>12} {'Δ mean':>10} "
          f"{'old scale':>12} {'new scale':>12} {'Δ scale':>10}")
    for i, c in enumerate(SENSOR_COLS):
        print(f"{c:<4} {old_mean[i]:>12.6f} {new_mean[i]:>12.6f} "
              f"{new_mean[i] - old_mean[i]:>+10.6f} {old_scale[i]:>12.6f} "
              f"{new_scale[i]:>12.6f} {new_scale[i] - old_scale[i]:>+10.6f}")

    payload = {
        "scaler_mean": new_mean.tolist(),
        "scaler_scale": new_scale.tolist(),
        "sensor_cols": SENSOR_COLS,
        "fit_dataset": str(DATA_CSV.relative_to(ROOT)).replace("\\", "/"),
        "fit_users": TRAIN_USERS,
        "val_users": VAL_USERS,
        "test_users": TEST_USERS,
        "n_train_rows": int(len(df_train)),
        "n_train_rows_source": "count of rows where User in fit_users from data/all_users_data_labeled.csv",
        "fit_users_policy": (
            "fit_users are the training split only. val/test users must stay out of scaler fitting "
            "to avoid data leakage and optimistic metrics."
        ),
        "if_fit_users_change_then_refit": (
            "Changing fit_users (for example 4 users vs 6 users) will change scaler_mean and "
            "scaler_scale. Refit the scaler and retrain/re-evaluate for a fair comparison."
        ),
        "normalization_variant": "zscore",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Fit on users 1-4 only. Leakage-safe. Replaces the leaky "
            "data/prepared/config.json which was fit on all 6 users."
        ),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nWrote {OUT_PATH}")

    # Post-normalization sanity per user
    print("\nPost-normalization per-channel mean / std (using new train-only scaler):")
    for uset, label in [(TRAIN_USERS, "train"), (VAL_USERS, "val"), (TEST_USERS, "test")]:
        sub = df[df["User"].isin(uset)][SENSOR_COLS].values
        z = (sub - new_mean) / new_scale
        print(f"  {label} users={uset}: n={len(sub):,}")
        for i, c in enumerate(SENSOR_COLS):
            print(f"    {c}: mean={z[:, i].mean():+.4f} std={z[:, i].std():.4f}")


if __name__ == "__main__":
    main()

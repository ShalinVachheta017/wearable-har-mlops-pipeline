"""Rebuild correctly paired HAR windows and labels from a labeled CSV.

This intentionally does not read data/prepared/production_y.npy. That file can
be stale or from a different run; the only reliable label source is the labeled
row-level CSV used to create the windows.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.label_mapping import get_class_to_index
from src.utils.scaler import CANONICAL_SCALER_PATH, assert_scaler_integrity


DEFAULT_INPUT = PROJECT_ROOT / "data" / "all_users_data_labeled.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "prepared" / "paired_windows"
SENSOR_COLS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
WINDOW_SIZE = 200
STEP_SIZE = 100


def _parse_users(raw: str) -> list[int]:
    if raw.strip().lower() in {"all", "*"}:
        return []
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def _load_scaler() -> tuple[np.ndarray, np.ndarray]:
    assert_scaler_integrity(CANONICAL_SCALER_PATH)
    cfg = json.loads(CANONICAL_SCALER_PATH.read_text(encoding="utf-8"))
    mean = np.asarray(cfg["scaler_mean"], dtype=np.float32)
    scale = np.asarray(cfg["scaler_scale"], dtype=np.float32)
    return mean, np.where(scale == 0, 1.0, scale).astype(np.float32)


def _majority_label(labels: np.ndarray) -> int:
    vals, counts = np.unique(labels, return_counts=True)
    return int(vals[counts.argmax()])


def build_windows(
    df: pd.DataFrame,
    users: Iterable[int],
    normalize: bool,
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    required = [*SENSOR_COLS, "activity", "User"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {missing}")

    activity_to_label = get_class_to_index()
    unknown = sorted(set(df["activity"].astype(str)) - set(activity_to_label))
    if unknown:
        raise ValueError(f"Unknown activity labels in input CSV: {unknown}")

    selected_users = list(users)
    if selected_users:
        df = df[df["User"].isin(selected_users)].copy()
        if df.empty:
            raise ValueError(f"No rows found for users={selected_users}")
    else:
        selected_users = sorted(int(u) for u in df["User"].dropna().unique())

    df["label_idx"] = df["activity"].map(activity_to_label).astype(np.int32)
    df[SENSOR_COLS] = df[SENSOR_COLS].apply(pd.to_numeric, errors="coerce").astype(np.float32)
    nan_count = int(df[SENSOR_COLS].isna().sum().sum())
    if nan_count:
        print(f"Found {nan_count} NaN sensor values; applying ffill + bfill per selected frame.")
        df[SENSOR_COLS] = df[SENSOR_COLS].ffill().bfill()
        df = df.dropna(subset=SENSOR_COLS).reset_index(drop=True)

    if normalize:
        mean, scale = _load_scaler()
        df.loc[:, SENSOR_COLS] = (
            (df[SENSOR_COLS].to_numpy(dtype=np.float32) - mean) / scale
        ).astype(np.float32)

    X_parts: list[np.ndarray] = []
    y_parts: list[int] = []
    metadata: list[dict] = []

    for user_id in selected_users:
        user_df = df[df["User"] == user_id].reset_index(drop=True)
        values = user_df[SENSOR_COLS].to_numpy(dtype=np.float32)
        labels = user_df["label_idx"].to_numpy(dtype=np.int32)

        if len(user_df) < WINDOW_SIZE:
            print(f"Skipping user {user_id}: {len(user_df)} rows < window_size={WINDOW_SIZE}")
            continue

        for start in range(0, len(user_df) - WINDOW_SIZE + 1, STEP_SIZE):
            end = start + WINDOW_SIZE
            window = values[start:end]
            if np.isnan(window).any():
                continue
            X_parts.append(window)
            y_parts.append(_majority_label(labels[start:end]))
            metadata.append(
                {
                    "window_id": len(metadata),
                    "user": int(user_id),
                    "start_idx": int(start),
                    "end_idx": int(end),
                }
            )

    if not X_parts:
        raise RuntimeError("No windows were created.")

    return (
        np.asarray(X_parts, dtype=np.float32),
        np.asarray(y_parts, dtype=np.int32),
        metadata,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--users", default="6", help='Comma list like "6" or "1,2,3,4"; use "all" for all users.')
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--raw", action="store_true", help="Save raw windows without canonical scaler normalization.")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    users = _parse_users(args.users)
    normalize = not args.raw
    X, y, metadata = build_windows(df, users=users, normalize=normalize)

    user_tag = "all" if not users else "users_" + "_".join(str(u) for u in users)
    space_tag = "canonical_scaled" if normalize else "raw"
    prefix = args.prefix or f"{args.input.stem}_{user_tag}_{space_tag}"

    args.output_dir.mkdir(parents=True, exist_ok=True)
    x_path = args.output_dir / f"{prefix}_X.npy"
    y_path = args.output_dir / f"{prefix}_y.npy"
    meta_path = args.output_dir / f"{prefix}_metadata.json"
    summary_path = args.output_dir / f"{prefix}_summary.json"

    np.save(x_path, X)
    np.save(y_path, y)
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    unique, counts = np.unique(y, return_counts=True)
    summary = {
        "input": str(args.input),
        "users": "all" if not users else users,
        "normalized_with_canonical_scaler": normalize,
        "window_size": WINDOW_SIZE,
        "step_size": STEP_SIZE,
        "sensor_cols": SENSOR_COLS,
        "x_path": str(x_path),
        "y_path": str(y_path),
        "metadata_path": str(meta_path),
        "x_shape": list(X.shape),
        "y_shape": list(y.shape),
        "label_counts": {str(int(k)): int(v) for k, v in zip(unique, counts)},
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Rebuilt paired windows")
    print(f"  X: {x_path}  shape={X.shape} dtype={X.dtype}")
    print(f"  y: {y_path}  shape={y.shape} dtype={y.dtype}")
    print(f"  metadata: {meta_path}")
    print(f"  summary:  {summary_path}")
    print(f"  label counts: {summary['label_counts']}")
    if len(X) != len(y):
        raise AssertionError(f"X/y length mismatch: {len(X)} != {len(y)}")


if __name__ == "__main__":
    main()

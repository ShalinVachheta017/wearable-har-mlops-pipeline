"""
Compare training vs production distribution at the pre-NumPy boundary,
WITHOUT z-score normalization. Reports raw mean/std per channel after
unit conversion (and optional gravity removal / calibration), exactly
as the data looks before it would be passed to the scaler.

Read-only: prints a side-by-side table. No files written.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.preprocess_data import (  # noqa: E402
    GravityRemover,
    PreprocessLogger,
    UnifiedPreprocessor,
    UnitDetector,
)

CHANNELS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
TRAIN_CSV = ROOT / "data" / "all_users_data_labeled.csv"
TRAIN_USERS = [1, 2, 3, 4]  # match scaler_train_only.json fit_users


def load_training_users(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Labeled file uses *_w columns; map to Ax..Gz to match production naming
    rename = {
        "Ax_w": "Ax", "Ay_w": "Ay", "Az_w": "Az",
        "Gx_w": "Gx", "Gy_w": "Gy", "Gz_w": "Gz",
    }
    df = df.rename(columns=rename)
    if "User" in df.columns:
        df = df[df["User"].isin(TRAIN_USERS)].reset_index(drop=True)
    return df


def channel_stats(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=CHANNELS)
    out["mean"] = [df[c].mean() for c in CHANNELS]
    out["std"] = [df[c].std() for c in CHANNELS]
    out["min"] = [df[c].min() for c in CHANNELS]
    out["max"] = [df[c].max() for c in CHANNELS]
    return out


import re

_TIMESTAMP_RE = re.compile(r"^fused_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}.*_50Hz\.csv$")


def find_production_csvs() -> list[Path]:
    """Real production = fused_<YYYY_MM_DD_HH_MM_SS>...50Hz.csv (timestamped sessions)."""
    all_csvs = sorted((ROOT / "data" / "processed").glob("fused_*_50Hz.csv"))
    prod = [p for p in all_csvs if _TIMESTAMP_RE.match(p.name)]
    if not prod:
        raise FileNotFoundError("No timestamped production fused files found")
    return prod


def preprocess_no_zscore(df: pd.DataFrame, logger) -> pd.DataFrame:
    """Run unit detection + conversion only (no scaling, no windowing)."""
    accel_cols = [c for c in ["Ax", "Ay", "Az"] if c in df.columns]
    detector = UnitDetector(logger)
    df_out, _ = detector.process_units(df, accel_cols)
    return df_out


def main() -> None:
    logger = PreprocessLogger("dist_compare").get_logger()

    print(f"\nTraining file:   {TRAIN_CSV}")
    print(f"Train users:     {TRAIN_USERS}")
    train_df_raw = load_training_users(TRAIN_CSV)
    print(f"Train rows:      {len(train_df_raw):,}")

    prod_csvs = find_production_csvs()
    print(f"\nProduction files ({len(prod_csvs)}):")
    for p in prod_csvs:
        print(f"  - {p.name}")

    # Per-file: read, coerce numeric, unit-detect+convert, then concat.
    print("\n--- Preprocessing TRAINING (unit check only) ---")
    train_df = preprocess_no_zscore(train_df_raw, logger)

    print("\n--- Preprocessing PRODUCTION (per-file unit check) ---")
    per_file_dfs: list[pd.DataFrame] = []
    for p in prod_csvs:
        df = pd.read_csv(p)
        for c in CHANNELS:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=[c for c in CHANNELS if c in df.columns]).reset_index(drop=True)
        if len(df) == 0:
            continue
        per_file_dfs.append(preprocess_no_zscore(df, logger))
    prod_df = pd.concat(per_file_dfs, ignore_index=True)
    print(f"\nProd rows (combined, post unit-conversion): {len(prod_df):,}")

    train_stats = channel_stats(train_df)
    prod_stats = channel_stats(prod_df)

    cmp = pd.DataFrame(
        {
            "train_mean": train_stats["mean"],
            "prod_mean": prod_stats["mean"],
            "delta_mean": prod_stats["mean"] - train_stats["mean"],
            "train_std": train_stats["std"],
            "prod_std": prod_stats["std"],
            "std_ratio": prod_stats["std"] / train_stats["std"],
        }
    )

    print("\n" + "=" * 80)
    print("RAW DISTRIBUTION COMPARISON (post unit-conversion, pre z-score)")
    print("=" * 80)
    print(cmp.round(4).to_string())
    print("=" * 80)
    print("Notes:")
    print("  - Units: Ax/Ay/Az in m/s², Gx/Gy/Gz in deg/s")
    print("  - delta_mean: production_mean - training_mean")
    print("  - std_ratio:  production_std / training_std (1.0 = identical spread)")


if __name__ == "__main__":
    main()

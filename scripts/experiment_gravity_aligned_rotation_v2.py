"""
Read-only experiment v2: gravity-aligned rotation with proper gravity estimation.

Improvements over v1:
  (a) Per-session: estimate gravity via low-pass filter (0.3 Hz Butterworth)
      instead of using the raw mean accel vector. Aligns to canonical [0,0,-9.81].
  (b) Per-window: same low-pass estimate, but compute one rotation per
      2-second window (100 samples @ 50Hz) and apply it window-locally.

Both branches operate on production data only. Training is also rotated
into the same canonical frame for fair comparison.

Outputs:
  Five comparison columns side-by-side:
    1. train (rotated to canonical)
    2. prod raw
    3. prod v1 (per-session, mean-accel target)        ← from previous script
    4. prod v2a (per-session, low-pass gravity → canonical)
    5. prod v2b (per-window, low-pass gravity → canonical)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.preprocess_data import PreprocessLogger, UnitDetector  # noqa: E402

CHANNELS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
ACCEL = ["Ax", "Ay", "Az"]
GYRO = ["Gx", "Gy", "Gz"]
TRAIN_CSV = ROOT / "data" / "all_users_data_labeled.csv"
TRAIN_USERS = [1, 2, 3, 4]
SAMPLING_HZ = 50.0
WINDOW_SAMPLES = 100  # 2 seconds @ 50Hz
GRAVITY_CUTOFF_HZ = 0.3
CANONICAL_GRAVITY = np.array([0.0, 0.0, -9.81])

_TIMESTAMP_RE = re.compile(r"^fused_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}.*_50Hz\.csv$")


# ---------- helpers ----------


def load_training_users(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    rename = {
        "Ax_w": "Ax", "Ay_w": "Ay", "Az_w": "Az",
        "Gx_w": "Gx", "Gy_w": "Gy", "Gz_w": "Gz",
    }
    df = df.rename(columns=rename)
    if "User" in df.columns:
        df = df[df["User"].isin(TRAIN_USERS)].reset_index(drop=True)
    return df


def find_production_csvs() -> list[Path]:
    all_csvs = sorted((ROOT / "data" / "processed").glob("fused_*_50Hz.csv"))
    return [p for p in all_csvs if _TIMESTAMP_RE.match(p.name)]


def unit_convert(df: pd.DataFrame, logger) -> pd.DataFrame:
    detector = UnitDetector(logger)
    accel_present = [c for c in ACCEL if c in df.columns]
    df_out, _ = detector.process_units(df, accel_present)
    return df_out


def channel_stats(arr: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"mean": arr.mean(axis=0), "std": arr.std(axis=0)}, index=CHANNELS)


def rodrigues(v_from: np.ndarray, v_to: np.ndarray) -> np.ndarray:
    a = v_from / (np.linalg.norm(v_from) + 1e-12)
    b = v_to / (np.linalg.norm(v_to) + 1e-12)
    cos_t = float(np.clip(np.dot(a, b), -1.0, 1.0))
    if cos_t > 1.0 - 1e-9:
        return np.eye(3)
    if cos_t < -1.0 + 1e-9:
        perp = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        axis = np.cross(a, perp)
        axis = axis / (np.linalg.norm(axis) + 1e-12)
    else:
        axis = np.cross(a, b)
        axis = axis / (np.linalg.norm(axis) + 1e-12)
    angle = np.arccos(cos_t)
    K = np.array(
        [[0.0, -axis[2], axis[1]], [axis[2], 0.0, -axis[0]], [-axis[1], axis[0], 0.0]]
    )
    return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)


def lowpass_gravity(accel: np.ndarray, cutoff_hz: float = GRAVITY_CUTOFF_HZ) -> np.ndarray:
    """Estimate per-sample gravity vector via Butterworth low-pass on each axis."""
    nyq = SAMPLING_HZ / 2.0
    b, a = butter(3, cutoff_hz / nyq, btype="low")
    g = np.zeros_like(accel, dtype=np.float64)
    for i in range(3):
        g[:, i] = filtfilt(b, a, accel[:, i])
    return g


def rotate_array(arr6: np.ndarray, R: np.ndarray) -> np.ndarray:
    A = arr6[:, :3] @ R.T
    G = arr6[:, 3:] @ R.T
    return np.hstack([A, G])


# ---------- v2a: per-session, low-pass gravity → canonical ----------


def rotate_session_canonical(arr6: np.ndarray) -> np.ndarray:
    g = lowpass_gravity(arr6[:, :3]).mean(axis=0)
    R = rodrigues(g, CANONICAL_GRAVITY)
    return rotate_array(arr6, R)


# ---------- v2b: per-window, low-pass gravity → canonical ----------


def rotate_per_window_canonical(arr6: np.ndarray, win: int = WINDOW_SAMPLES) -> np.ndarray:
    g_full = lowpass_gravity(arr6[:, :3])
    n = len(arr6)
    out = np.empty_like(arr6, dtype=np.float64)
    for s in range(0, n, win):
        e = min(s + win, n)
        g_win = g_full[s:e].mean(axis=0)
        R = rodrigues(g_win, CANONICAL_GRAVITY)
        out[s:e] = rotate_array(arr6[s:e], R)
    return out


# ---------- v1 (kept for comparison): per-session, mean-accel target ----------


def rotate_session_to_train_mean(arr6: np.ndarray, g_train_mean: np.ndarray) -> np.ndarray:
    g_prod = arr6[:, :3].mean(axis=0)
    R = rodrigues(g_prod, g_train_mean)
    return rotate_array(arr6, R)


# ---------- main ----------


def main() -> None:
    logger = PreprocessLogger("gravity_align_v2").get_logger()

    # Training: rotate into canonical frame too, for fair comparison
    train_df = unit_convert(load_training_users(TRAIN_CSV), logger)
    train_arr = train_df[CHANNELS].to_numpy(dtype=np.float64)
    g_train_mean = train_arr[:, :3].mean(axis=0)
    train_canonical = rotate_session_canonical(train_arr)

    print(f"Train rows: {len(train_arr):,}")
    print(f"Train raw gravity (mean accel): {g_train_mean}")
    print(f"Train low-pass gravity (mean):  {lowpass_gravity(train_arr[:, :3]).mean(axis=0)}")

    # Production
    prod_csvs = find_production_csvs()
    print(f"\nProduction sessions: {len(prod_csvs)}")

    raw_chunks = []
    v1_chunks = []
    v2a_chunks = []
    v2b_chunks = []

    for p in prod_csvs:
        df = pd.read_csv(p)
        for c in CHANNELS:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=[c for c in CHANNELS if c in df.columns]).reset_index(drop=True)
        if len(df) == 0:
            continue
        df = unit_convert(df, logger)
        arr6 = df[CHANNELS].to_numpy(dtype=np.float64)

        raw_chunks.append(arr6)
        v1_chunks.append(rotate_session_to_train_mean(arr6, g_train_mean))
        v2a_chunks.append(rotate_session_canonical(arr6))
        v2b_chunks.append(rotate_per_window_canonical(arr6))

    prod_raw = np.vstack(raw_chunks)
    prod_v1 = np.vstack(v1_chunks)
    prod_v2a = np.vstack(v2a_chunks)
    prod_v2b = np.vstack(v2b_chunks)
    print(f"Total production rows: {len(prod_raw):,}")

    # Stats
    train_stats = channel_stats(train_canonical)
    raw_stats = channel_stats(prod_raw)
    v1_stats = channel_stats(prod_v1)
    v2a_stats = channel_stats(prod_v2a)
    v2b_stats = channel_stats(prod_v2b)

    pd.set_option("display.float_format", lambda x: f"{x:.3f}")

    means = pd.DataFrame(
        {
            "train_canon": train_stats["mean"],
            "prod_raw": raw_stats["mean"],
            "prod_v1": v1_stats["mean"],
            "prod_v2a_session": v2a_stats["mean"],
            "prod_v2b_window": v2b_stats["mean"],
        }
    )
    stds = pd.DataFrame(
        {
            "train_canon": train_stats["std"],
            "prod_raw": raw_stats["std"],
            "prod_v1": v1_stats["std"],
            "prod_v2a_session": v2a_stats["std"],
            "prod_v2b_window": v2b_stats["std"],
        }
    )

    print("\n" + "=" * 100)
    print("MEAN per channel (m/s² for A, deg/s for G) — pre-zscore, post unit-conversion")
    print("=" * 100)
    print(means.to_string())
    print("\n" + "=" * 100)
    print("STD per channel — pre-zscore")
    print("=" * 100)
    print(stds.to_string())

    # Simulated post-zscore alarms vs canonical-train scaler
    print("\n" + "=" * 100)
    print("SIMULATED DRIFT ALERTS (post-zscore using CANONICAL-rotated training)")
    print("=" * 100)
    canon_mean = train_canonical.mean(axis=0)
    canon_std = train_canonical.std(axis=0)

    def alerts(arr: np.ndarray) -> tuple[int, int, np.ndarray, np.ndarray]:
        z = (arr - canon_mean) / canon_std
        mu = z.mean(axis=0)
        sd = z.std(axis=0)
        return int((np.abs(mu) > 0.3).sum()), int((sd > 1.3).sum()), mu, sd

    branches = {
        "raw": prod_raw,
        "v1 (mean-accel)": prod_v1,
        "v2a (session canonical)": prod_v2a,
        "v2b (window canonical)": prod_v2b,
    }

    rows = []
    for name, arr in branches.items():
        n_mu, n_sd, mu, sd = alerts(arr)
        rows.append((name, n_mu, n_sd, n_mu + n_sd, mu, sd))

    print(f"\n{'Branch':<28} {'mean alerts':>12} {'std alerts':>11} {'total':>7}")
    print("-" * 60)
    for name, n_mu, n_sd, tot, _, _ in rows:
        print(f"{name:<28} {n_mu:>12d} {n_sd:>11d} {tot:>7d}")

    print("\nPer-channel post-z mean/std for v2b (window canonical):")
    _, _, mu_v2b, sd_v2b = alerts(prod_v2b)
    detail = pd.DataFrame(
        {"post_z_mean": mu_v2b, "post_z_std": sd_v2b}, index=CHANNELS
    )
    detail["mean_alert"] = np.abs(detail["post_z_mean"]) > 0.3
    detail["std_alert"] = detail["post_z_std"] > 1.3
    print(detail.to_string())


if __name__ == "__main__":
    main()

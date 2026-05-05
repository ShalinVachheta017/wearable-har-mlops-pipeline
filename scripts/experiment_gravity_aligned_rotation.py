"""
Read-only experiment: gravity-aligned rotation as a drift remedy.

Goal
----
Test whether rotating each production session into the training gravity frame
collapses the accelerometer mean shift WITHOUT discarding directional info
(unlike A_mag / G_mag collapse).

Approach
--------
1. Compute mean accel vector for training (users 1-4): g_train.
2. For each production file, compute mean accel vector: g_prod.
3. Build rotation matrix R (Rodrigues) such that R @ g_prod ≈ g_train.
4. Apply R to every (Ax, Ay, Az) and (Gx, Gy, Gz) sample in that file.
5. Concatenate rotated production data, compute mean/std per channel.
6. Print three side-by-side tables:
     - Train (raw)
     - Prod (raw, post unit-conversion)
     - Prod (raw, post unit-conversion, post gravity-alignment)

Outputs (stdout only, no files written):
  Three tables + a summary of how much the orientation drift collapsed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.preprocess_data import PreprocessLogger, UnitDetector  # noqa: E402

CHANNELS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
ACCEL = ["Ax", "Ay", "Az"]
GYRO = ["Gx", "Gy", "Gz"]
TRAIN_CSV = ROOT / "data" / "all_users_data_labeled.csv"
TRAIN_USERS = [1, 2, 3, 4]

_TIMESTAMP_RE = re.compile(r"^fused_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}.*_50Hz\.csv$")


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


def channel_stats(arr: np.ndarray) -> pd.DataFrame:
    """arr shape (N, 6) → DataFrame indexed by CHANNELS with mean/std."""
    return pd.DataFrame(
        {
            "mean": arr.mean(axis=0),
            "std": arr.std(axis=0),
            "min": arr.min(axis=0),
            "max": arr.max(axis=0),
        },
        index=CHANNELS,
    )


def rodrigues_rotation_matrix(v_from: np.ndarray, v_to: np.ndarray) -> np.ndarray:
    """
    Build a 3x3 rotation matrix R such that R @ v_from is parallel to v_to,
    preserving the magnitude of v_from. Uses Rodrigues' rotation formula.

    Edge cases:
      - If v_from and v_to are already parallel (same direction): identity.
      - If antiparallel: rotate 180° about any axis perpendicular to v_from.
    """
    a = v_from / (np.linalg.norm(v_from) + 1e-12)
    b = v_to / (np.linalg.norm(v_to) + 1e-12)
    cos_t = float(np.clip(np.dot(a, b), -1.0, 1.0))

    if cos_t > 1.0 - 1e-9:
        return np.eye(3)
    if cos_t < -1.0 + 1e-9:
        # 180° rotation: pick any axis perpendicular to a
        perp = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        axis = np.cross(a, perp)
        axis = axis / (np.linalg.norm(axis) + 1e-12)
    else:
        axis = np.cross(a, b)
        axis = axis / (np.linalg.norm(axis) + 1e-12)

    angle = np.arccos(cos_t)
    K = np.array(
        [
            [0.0, -axis[2], axis[1]],
            [axis[2], 0.0, -axis[0]],
            [-axis[1], axis[0], 0.0],
        ]
    )
    R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)
    return R


def unit_convert(df: pd.DataFrame, logger) -> pd.DataFrame:
    detector = UnitDetector(logger)
    accel_present = [c for c in ACCEL if c in df.columns]
    df_out, _ = detector.process_units(df, accel_present)
    return df_out


def gather_production_per_file(prod_csvs, logger):
    """Yield (filename, df_post_unit_conversion) for each timestamped session."""
    for p in prod_csvs:
        df = pd.read_csv(p)
        for c in CHANNELS:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=[c for c in CHANNELS if c in df.columns]).reset_index(drop=True)
        if len(df) == 0:
            continue
        yield p.name, unit_convert(df, logger)


def rotate_session(df: pd.DataFrame, R: np.ndarray) -> np.ndarray:
    """Apply R to accel and gyro triplets. Return (N, 6) array."""
    A = df[ACCEL].to_numpy(dtype=np.float64)  # (N, 3)
    G = df[GYRO].to_numpy(dtype=np.float64)
    A_rot = A @ R.T
    G_rot = G @ R.T
    return np.hstack([A_rot, G_rot])


def main() -> None:
    logger = PreprocessLogger("gravity_align_experiment").get_logger()

    print(f"Training file:   {TRAIN_CSV}")
    train_df_raw = load_training_users(TRAIN_CSV)
    train_df = unit_convert(train_df_raw, logger)
    g_train = train_df[ACCEL].mean().to_numpy()
    print(f"Train rows:      {len(train_df):,}")
    print(f"Train gravity vector (mean Ax,Ay,Az): {g_train}")
    print(f"Train |gravity|: {np.linalg.norm(g_train):.3f} m/s²")

    train_arr = train_df[CHANNELS].to_numpy(dtype=np.float64)
    train_stats = channel_stats(train_arr)

    prod_csvs = find_production_csvs()
    print(f"\nProduction sessions: {len(prod_csvs)}")

    raw_chunks: list[np.ndarray] = []
    rot_chunks: list[np.ndarray] = []
    rotation_summary: list[dict] = []

    for name, df in gather_production_per_file(prod_csvs, logger):
        g_prod = df[ACCEL].mean().to_numpy()
        R = rodrigues_rotation_matrix(g_prod, g_train)

        raw = df[CHANNELS].to_numpy(dtype=np.float64)
        rotated = rotate_session(df, R)

        raw_chunks.append(raw)
        rot_chunks.append(rotated)

        # Verify: R @ g_prod should ≈ g_train
        g_after = R @ g_prod
        rotation_summary.append(
            {
                "file": name,
                "rows": len(df),
                "g_prod": g_prod,
                "g_after_rotation": g_after,
                "angle_deg": np.degrees(
                    np.arccos(
                        np.clip(
                            np.dot(g_prod, g_train)
                            / (np.linalg.norm(g_prod) * np.linalg.norm(g_train) + 1e-12),
                            -1.0,
                            1.0,
                        )
                    )
                ),
            }
        )

    prod_raw = np.vstack(raw_chunks)
    prod_rot = np.vstack(rot_chunks)
    print(f"Total production rows: {len(prod_raw):,}")

    raw_stats = channel_stats(prod_raw)
    rot_stats = channel_stats(prod_rot)

    cmp = pd.DataFrame(
        {
            "train_mean": train_stats["mean"],
            "prod_raw_mean": raw_stats["mean"],
            "prod_rot_mean": rot_stats["mean"],
            "train_std": train_stats["std"],
            "prod_raw_std": raw_stats["std"],
            "prod_rot_std": rot_stats["std"],
        }
    )

    cmp["mean_shift_raw"] = cmp["prod_raw_mean"] - cmp["train_mean"]
    cmp["mean_shift_rot"] = cmp["prod_rot_mean"] - cmp["train_mean"]
    cmp["std_ratio_raw"] = cmp["prod_raw_std"] / cmp["train_std"]
    cmp["std_ratio_rot"] = cmp["prod_rot_std"] / cmp["train_std"]

    pd.set_option("display.float_format", lambda x: f"{x:.4f}")
    print("\n" + "=" * 100)
    print("DISTRIBUTION COMPARISON (raw, post-unit-conversion, NO z-score)")
    print("=" * 100)
    print(
        cmp[
            [
                "train_mean",
                "prod_raw_mean",
                "prod_rot_mean",
                "mean_shift_raw",
                "mean_shift_rot",
            ]
        ].to_string()
    )
    print("\n" + "-" * 100)
    print(
        cmp[
            ["train_std", "prod_raw_std", "prod_rot_std", "std_ratio_raw", "std_ratio_rot"]
        ].to_string()
    )
    print("=" * 100)

    print("\n--- ROTATION SUMMARY (per session) ---")
    print(f"{'File':<55} {'rows':>8} {'angle°':>8}")
    print("-" * 75)
    for r in rotation_summary:
        print(f"{r['file']:<55} {r['rows']:>8} {r['angle_deg']:>8.2f}")

    # Sanity check: simulated post-zscore alarms
    print("\n--- WHAT DRIFT MONITOR WOULD SEE (simulated post-zscore mean & std) ---")
    # Use the canonical scaler params from scaler_train_only.json
    scaler_mean = np.array(
        [2.3404667753619552, 0.5924839221453878, -3.592547569952467,
         0.6734150500172092, 0.2543884558319425, 0.0612584716839078]
    )
    scaler_scale = np.array(
        [6.8854626962149785, 4.665460399965496, 3.0805675087589415,
         54.79051678948113, 15.500414721145665, 14.530287853459674]
    )

    def post_z(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        z = (arr - scaler_mean) / scaler_scale
        return z.mean(axis=0), z.std(axis=0)

    raw_mu_z, raw_sd_z = post_z(prod_raw)
    rot_mu_z, rot_sd_z = post_z(prod_rot)

    sim = pd.DataFrame(
        {
            "raw_post_z_mean": raw_mu_z,
            "rot_post_z_mean": rot_mu_z,
            "raw_post_z_std": raw_sd_z,
            "rot_post_z_std": rot_sd_z,
        },
        index=CHANNELS,
    )
    sim["raw_mean_alert"] = np.abs(sim["raw_post_z_mean"]) > 0.3
    sim["rot_mean_alert"] = np.abs(sim["rot_post_z_mean"]) > 0.3
    sim["raw_std_alert"] = sim["raw_post_z_std"] > 1.3
    sim["rot_std_alert"] = sim["rot_post_z_std"] > 1.3
    print(sim.to_string())

    n_raw_alerts = int(sim["raw_mean_alert"].sum() + sim["raw_std_alert"].sum())
    n_rot_alerts = int(sim["rot_mean_alert"].sum() + sim["rot_std_alert"].sum())
    print(f"\nDrift alerts (raw):           {n_raw_alerts}")
    print(f"Drift alerts (rotated):       {n_rot_alerts}")
    print(
        "\nInterpretation: a drop in mean alerts after rotation = orientation drift"
        " was the cause.\nAny remaining std alerts = behavioral drift (real motion"
        " variance, not orientation)."
    )


if __name__ == "__main__":
    main()

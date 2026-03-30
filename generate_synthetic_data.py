#!/usr/bin/env python3
"""
Synthetic HAR data generator.

Creates a synthetic labeled dataset that mirrors the structure of
`data/all_users_data_labeled.csv` without modifying the original files.

Outputs are written only under `data/codex_synth/`.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


SENSOR_COLS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
OUTPUT_DIRNAME = "codex_synth"
DEFAULT_SOURCE = Path("data/all_users_data_labeled.csv")
DEFAULT_OUTPUT = Path("data") / OUTPUT_DIRNAME
DEFAULT_OUTPUT_CSV = "synthetic_all_users_labeled_v1.csv"
REFERENCE_PROFILES_JSON = "reference_profiles.json"
GENERATION_MANIFEST_JSON = "generation_manifest.json"
QUALITY_REPORT_MD = "quality_report.md"

DEFAULT_SAMPLE_RATE_HZ = 50
DEFAULT_STEP_MS = 1000 // DEFAULT_SAMPLE_RATE_HZ
DEFAULT_GAP_MS = 2000


@dataclass
class GroupProfile:
    """Reference statistics for one (user, activity) group."""

    mean: np.ndarray
    cov: np.ndarray
    innovation_cov: np.ndarray
    lag1_rho: np.ndarray
    min_vals: np.ndarray
    max_vals: np.ndarray
    count: int
    first_timestamp: str | None
    last_timestamp: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a synthetic HAR dataset under data/codex_synth/."
    )
    parser.add_argument(
        "--source-csv",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Reference labeled CSV (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default=DEFAULT_OUTPUT_CSV,
        help=f"Output CSV filename (default: {DEFAULT_OUTPUT_CSV})",
    )
    parser.add_argument(
        "--scale-factor",
        type=float,
        default=1.0,
        help="Scale rows per user/activity. 1.0 = exact-match row counts.",
    )
    parser.add_argument(
        "--user-id-offset",
        type=int,
        default=100,
        help="Offset added to original user ids for synthetic user ids.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260330,
        help="Base RNG seed.",
    )
    return parser.parse_args()


def stabilize_covariance(matrix: np.ndarray, floor: float = 1e-6) -> np.ndarray:
    """Project a covariance-like matrix to positive semi-definite form."""

    sym = (matrix + matrix.T) / 2.0
    eigvals, eigvecs = np.linalg.eigh(sym)
    eigvals = np.clip(eigvals, floor, None)
    return eigvecs @ np.diag(eigvals) @ eigvecs.T


def compute_lag1_rho(values: np.ndarray) -> np.ndarray:
    """Per-channel lag-1 autocorrelation with conservative clipping."""

    if len(values) < 3:
        return np.full(values.shape[1], 0.85, dtype=np.float64)

    prev_vals = values[:-1]
    next_vals = values[1:]
    rho = []
    for idx in range(values.shape[1]):
        x = prev_vals[:, idx]
        y = next_vals[:, idx]
        if np.std(x) < 1e-8 or np.std(y) < 1e-8:
            rho.append(0.85)
            continue
        corr = np.corrcoef(x, y)[0, 1]
        if np.isnan(corr):
            corr = 0.85
        rho.append(float(np.clip(corr, 0.20, 0.995)))
    return np.asarray(rho, dtype=np.float64)


def build_group_profiles(df: pd.DataFrame) -> Dict[Tuple[int, str], GroupProfile]:
    """Compute per-user, per-activity reference profiles."""

    profiles: Dict[Tuple[int, str], GroupProfile] = {}

    for (user, activity), group in df.groupby(["User", "activity"], sort=False):
        sensor = group[SENSOR_COLS].to_numpy(dtype=np.float64)
        mean = sensor.mean(axis=0)
        cov = np.cov(sensor, rowvar=False)
        cov = stabilize_covariance(cov)

        lag1_rho = compute_lag1_rho(sensor)
        rho_outer = np.outer(lag1_rho, lag1_rho)
        innovation_cov = cov * (1.0 - rho_outer)
        innovation_cov = stabilize_covariance(innovation_cov)

        profiles[(int(user), str(activity))] = GroupProfile(
            mean=mean,
            cov=cov,
            innovation_cov=innovation_cov,
            lag1_rho=lag1_rho,
            min_vals=sensor.min(axis=0),
            max_vals=sensor.max(axis=0),
            count=int(len(group)),
            first_timestamp=str(group["timestamp"].iloc[0]) if "timestamp" in group.columns else None,
            last_timestamp=str(group["timestamp"].iloc[-1]) if "timestamp" in group.columns else None,
        )

    return profiles


def extract_activity_order(df: pd.DataFrame) -> Dict[int, List[str]]:
    """Contiguous activity order per user."""

    order_map: Dict[int, List[str]] = {}
    for user, group in df.groupby("User", sort=False):
        activities = group["activity"].tolist()
        ordered: List[str] = []
        prev = None
        for activity in activities:
            if activity != prev:
                ordered.append(str(activity))
            prev = activity
        order_map[int(user)] = ordered
    return order_map


def sample_group_sequence(
    profile: GroupProfile,
    n_rows: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate one synthetic sequence using a diagonal AR(1) process."""

    if n_rows <= 0:
        return np.empty((0, len(SENSOR_COLS)), dtype=np.float32)

    state = np.empty((n_rows, len(SENSOR_COLS)), dtype=np.float64)
    state[0] = rng.multivariate_normal(profile.mean, profile.cov)

    innovation = rng.multivariate_normal(
        mean=np.zeros(len(SENSOR_COLS), dtype=np.float64),
        cov=profile.innovation_cov,
        size=max(n_rows - 1, 1),
    )
    rho = profile.lag1_rho

    for idx in range(1, n_rows):
        state[idx] = profile.mean + rho * (state[idx - 1] - profile.mean) + innovation[idx - 1]

    # Align generated sequence back to the target first-order moments per channel.
    target_std = np.sqrt(np.clip(np.diag(profile.cov), 1e-8, None))
    current_mean = state.mean(axis=0)
    current_std = np.clip(state.std(axis=0), 1e-8, None)
    state = ((state - current_mean) / current_std) * target_std + profile.mean

    state = np.clip(state, profile.min_vals, profile.max_vals)
    return state.astype(np.float32)


def make_timestamps(start_dt: datetime, n_rows: int) -> List[str]:
    """Generate millisecond timestamps at 50 Hz."""

    return [
        (start_dt + timedelta(milliseconds=i * DEFAULT_STEP_MS)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        for i in range(n_rows)
    ]


def generate_synthetic_dataframe(
    source_df: pd.DataFrame,
    profiles: Dict[Tuple[int, str], GroupProfile],
    scale_factor: float,
    user_id_offset: int,
    seed: int,
) -> Tuple[pd.DataFrame, Dict[int, int]]:
    """Generate the synthetic labeled CSV with exact or scaled counts."""

    user_order = [int(u) for u in source_df["User"].drop_duplicates().tolist()]
    activity_order_map = extract_activity_order(source_df)
    synthetic_user_map = {real_user: real_user + user_id_offset for real_user in user_order}

    chunks: List[pd.DataFrame] = []
    base_dt = datetime(2016, 1, 1, 9, 0, 0)

    for user_idx, real_user in enumerate(user_order):
        synthetic_user = synthetic_user_map[real_user]
        current_dt = base_dt + timedelta(days=user_idx)
        user_rng = np.random.default_rng(seed + synthetic_user * 1000)

        for activity_idx, activity in enumerate(activity_order_map[real_user]):
            profile = profiles[(real_user, activity)]
            n_rows = int(np.ceil(profile.count * scale_factor))
            if n_rows <= 0:
                continue

            seq_rng = np.random.default_rng(seed + synthetic_user * 1000 + activity_idx * 97)
            data = sample_group_sequence(profile, n_rows=n_rows, rng=seq_rng)
            chunk = pd.DataFrame(data, columns=SENSOR_COLS)
            chunk["timestamp"] = make_timestamps(current_dt, n_rows)
            chunk["activity"] = activity
            chunk["User"] = synthetic_user
            chunks.append(chunk)

            current_dt += timedelta(milliseconds=n_rows * DEFAULT_STEP_MS + DEFAULT_GAP_MS)

            # Use user_rng to advance state deterministically per block and avoid identical seeds
            _ = user_rng.integers(0, 1_000_000)

    synthetic_df = pd.concat(chunks, ignore_index=True)
    synthetic_df = synthetic_df[
        ["timestamp", "Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w", "activity", "User"]
    ]
    return synthetic_df, synthetic_user_map


def wasserstein_1d(a: np.ndarray, b: np.ndarray) -> float:
    """Compute 1D Wasserstein distance with scipy fallback."""

    try:
        from scipy.stats import wasserstein_distance

        return float(wasserstein_distance(a, b))
    except Exception:
        all_vals = np.sort(np.concatenate([a, b]))
        cdf_a = np.searchsorted(np.sort(a), all_vals, side="right") / len(a)
        cdf_b = np.searchsorted(np.sort(b), all_vals, side="right") / len(b)
        return float(np.mean(np.abs(cdf_a - cdf_b)))


def summarize_profiles(
    source_csv: Path,
    source_df: pd.DataFrame,
    profiles: Dict[Tuple[int, str], GroupProfile],
) -> Dict[str, object]:
    """Serialize compact reference profiles to JSON."""

    summary: Dict[str, object] = {
        "source_csv": str(source_csv),
        "n_rows": int(len(source_df)),
        "n_users": int(source_df["User"].nunique()),
        "n_activities": int(source_df["activity"].nunique()),
        "sensor_columns": SENSOR_COLS,
        "per_user_activity": {},
    }

    for (user, activity), profile in profiles.items():
        key = f"user_{user}"
        summary["per_user_activity"].setdefault(key, {})
        summary["per_user_activity"][key][activity] = {
            "count": profile.count,
            "mean": [round(float(v), 6) for v in profile.mean],
            "std": [round(float(v), 6) for v in np.sqrt(np.diag(profile.cov))],
            "lag1_rho": [round(float(v), 6) for v in profile.lag1_rho],
            "min": [round(float(v), 6) for v in profile.min_vals],
            "max": [round(float(v), 6) for v in profile.max_vals],
            "first_timestamp": profile.first_timestamp,
            "last_timestamp": profile.last_timestamp,
        }

    return summary


def build_manifest(
    source_csv: Path,
    source_df: pd.DataFrame,
    synthetic_df: pd.DataFrame,
    synthetic_user_map: Dict[int, int],
    scale_factor: float,
    seed: int,
    output_csv: Path,
) -> Dict[str, object]:
    """Create a generation manifest."""

    return {
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source_csv": str(source_csv),
        "output_csv": str(output_csv),
        "generation_method": "per-user per-activity diagonal-ar1 with covariance-matched innovations",
        "scale_factor": scale_factor,
        "seed": seed,
        "row_counts": {
            "reference_rows": int(len(source_df)),
            "synthetic_rows": int(len(synthetic_df)),
        },
        "user_counts": {
            "reference_users": int(source_df["User"].nunique()),
            "synthetic_users": int(synthetic_df["User"].nunique()),
        },
        "activity_counts_reference": {
            k: int(v) for k, v in source_df["activity"].value_counts().sort_index().items()
        },
        "activity_counts_synthetic": {
            k: int(v) for k, v in synthetic_df["activity"].value_counts().sort_index().items()
        },
        "synthetic_user_map": {str(k): int(v) for k, v in synthetic_user_map.items()},
        "sensor_columns": SENSOR_COLS,
        "notes": [
            "Original datasets were used as reference only.",
            "All generated artifacts are isolated under data/codex_synth.",
            "Synthetic user ids are offset from real ids.",
            "Counts are matched exactly when scale_factor=1.0.",
        ],
    }


def build_quality_report(source_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> str:
    """Render a compact markdown quality report."""

    lines: List[str] = []
    lines.append("# Synthetic Dataset Quality Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Reference rows: `{len(source_df):,}`")
    lines.append(f"- Synthetic rows: `{len(synthetic_df):,}`")
    lines.append(f"- Reference users: `{source_df['User'].nunique()}`")
    lines.append(f"- Synthetic users: `{synthetic_df['User'].nunique()}`")
    lines.append(f"- Activities: `{source_df['activity'].nunique()}`")
    lines.append("")
    lines.append("## Overall Sensor Comparison")
    lines.append("")
    lines.append("| Sensor | Real mean | Synth mean | Real std | Synth std | Wasserstein |")
    lines.append("|---|---:|---:|---:|---:|---:|")

    for col in SENSOR_COLS:
        real_col = source_df[col].to_numpy(dtype=np.float64)
        synth_col = synthetic_df[col].to_numpy(dtype=np.float64)
        lines.append(
            "| {col} | {rmean:.4f} | {smean:.4f} | {rstd:.4f} | {sstd:.4f} | {wd:.4f} |".format(
                col=col,
                rmean=float(real_col.mean()),
                smean=float(synth_col.mean()),
                rstd=float(real_col.std()),
                sstd=float(synth_col.std()),
                wd=wasserstein_1d(real_col, synth_col),
            )
        )

    lines.append("")
    lines.append("## Activity Counts")
    lines.append("")
    lines.append("| Activity | Real rows | Synthetic rows |")
    lines.append("|---|---:|---:|")
    real_counts = source_df["activity"].value_counts().sort_index()
    synth_counts = synthetic_df["activity"].value_counts().sort_index()
    for activity in real_counts.index:
        lines.append(
            f"| {activity} | {int(real_counts[activity]):,} | {int(synth_counts.get(activity, 0)):,} |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Synthetic data was generated per user and per activity block.")
    lines.append("- Row counts were matched to the reference dataset at `scale_factor = 1.0`.")
    lines.append("- Temporal structure was approximated with a per-channel AR(1) process.")
    lines.append("- Sensor values were clipped to the observed reference min/max per group.")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    if args.scale_factor <= 0:
        raise ValueError("--scale-factor must be > 0.")

    source_csv = args.source_csv.resolve()
    if not source_csv.exists():
        raise FileNotFoundError(f"Reference CSV not found: {source_csv}")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_csv = output_dir / args.output_name
    reference_profiles_path = output_dir / REFERENCE_PROFILES_JSON
    manifest_path = output_dir / GENERATION_MANIFEST_JSON
    quality_report_path = output_dir / QUALITY_REPORT_MD

    print(f"Loading reference data: {source_csv}")
    source_df = pd.read_csv(source_csv)

    required_cols = {"timestamp", "activity", "User", *SENSOR_COLS}
    missing = sorted(required_cols.difference(source_df.columns))
    if missing:
        raise ValueError(f"Reference CSV is missing required columns: {missing}")

    profiles = build_group_profiles(source_df)
    synthetic_df, synthetic_user_map = generate_synthetic_dataframe(
        source_df=source_df,
        profiles=profiles,
        scale_factor=args.scale_factor,
        user_id_offset=args.user_id_offset,
        seed=args.seed,
    )

    synthetic_df.to_csv(output_csv, index=False)

    reference_profiles = summarize_profiles(source_csv, source_df, profiles)
    reference_profiles_path.write_text(
        json.dumps(reference_profiles, indent=2),
        encoding="utf-8",
    )

    manifest = build_manifest(
        source_csv=source_csv,
        source_df=source_df,
        synthetic_df=synthetic_df,
        synthetic_user_map=synthetic_user_map,
        scale_factor=args.scale_factor,
        seed=args.seed,
        output_csv=output_csv,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    quality_report = build_quality_report(source_df, synthetic_df)
    quality_report_path.write_text(quality_report, encoding="utf-8")

    print("Generation complete")
    print(f"  Output CSV:          {output_csv}")
    print(f"  Reference profiles:  {reference_profiles_path}")
    print(f"  Manifest:            {manifest_path}")
    print(f"  Quality report:      {quality_report_path}")
    print(f"  Synthetic rows:      {len(synthetic_df):,}")
    print(f"  Synthetic users:     {synthetic_df['User'].nunique()}")
    print(f"  Activities:          {synthetic_df['activity'].nunique()}")


if __name__ == "__main__":
    main()

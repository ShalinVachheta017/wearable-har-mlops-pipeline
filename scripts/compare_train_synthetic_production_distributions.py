#!/usr/bin/env python3
"""Compare train, synthetic, and production sensor distributions.

The report is intentionally simple: raw physical sensor space after the same
basic Stage 1-3 compatibility rules used by the pipeline:

- canonical columns: Ax, Ay, Az, Gx, Gy, Gz
- accelerometer in m/s^2
- gyroscope in deg/s
- no z-score scaling, no gravity removal

Large production accelerometer values are treated as milli-g and converted to
m/s^2 using 9.80665 / 1000.
"""

from __future__ import annotations

import json
import math
import re
import zlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "data_distribution_comparison"

SENSOR_COLS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
ACCEL_COLS = ["Ax", "Ay", "Az"]
GYRO_COLS = ["Gx", "Gy", "Gz"]
FEATURE_COLS = SENSOR_COLS + ["A_mag", "G_mag"]

MILLI_G_TO_MPS2 = 9.80665 / 1000.0
CHUNK_SIZE = 200_000
MAX_SAMPLE_PER_DATASET = 260_000
MAX_SAMPLE_PER_FILE = 12_000
RNG_SEED = 20260502

COLUMN_ALIASES = {
    "Ax": ["Ax", "Ax_w", "accel_x", "x_accel", "acceleration_x"],
    "Ay": ["Ay", "Ay_w", "accel_y", "y_accel", "acceleration_y"],
    "Az": ["Az", "Az_w", "accel_z", "z_accel", "acceleration_z"],
    "Gx": ["Gx", "Gx_w", "gyro_x", "x_gyro", "gyroscope_x"],
    "Gy": ["Gy", "Gy_w", "gyro_y", "y_gyro", "gyroscope_y"],
    "Gz": ["Gz", "Gz_w", "gyro_z", "z_gyro", "gyroscope_z"],
}


@dataclass
class RunningStats:
    count: Dict[str, int] = field(default_factory=lambda: {c: 0 for c in FEATURE_COLS})
    missing: Dict[str, int] = field(default_factory=lambda: {c: 0 for c in FEATURE_COLS})
    total: Dict[str, float] = field(default_factory=lambda: {c: 0.0 for c in FEATURE_COLS})
    total_sq: Dict[str, float] = field(default_factory=lambda: {c: 0.0 for c in FEATURE_COLS})
    min_val: Dict[str, float] = field(default_factory=lambda: {c: math.inf for c in FEATURE_COLS})
    max_val: Dict[str, float] = field(default_factory=lambda: {c: -math.inf for c in FEATURE_COLS})

    def update(self, frame: pd.DataFrame) -> None:
        for col in FEATURE_COLS:
            values = pd.to_numeric(frame[col], errors="coerce")
            n_missing = int(values.isna().sum())
            valid = values.dropna().to_numpy(dtype=np.float64)
            self.missing[col] += n_missing
            if len(valid) == 0:
                continue
            self.count[col] += int(len(valid))
            self.total[col] += float(valid.sum())
            self.total_sq[col] += float(np.dot(valid, valid))
            self.min_val[col] = min(self.min_val[col], float(valid.min()))
            self.max_val[col] = max(self.max_val[col], float(valid.max()))

    def merge(self, other: "RunningStats") -> None:
        for col in FEATURE_COLS:
            self.count[col] += other.count[col]
            self.missing[col] += other.missing[col]
            self.total[col] += other.total[col]
            self.total_sq[col] += other.total_sq[col]
            self.min_val[col] = min(self.min_val[col], other.min_val[col])
            self.max_val[col] = max(self.max_val[col], other.max_val[col])

    def to_rows(self, dataset: str, sample: pd.DataFrame) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for col in FEATURE_COLS:
            n = self.count[col]
            mean = self.total[col] / n if n else np.nan
            var = (self.total_sq[col] / n) - (mean * mean) if n else np.nan
            std = math.sqrt(max(var, 0.0)) if n else np.nan
            q = _quantiles(sample[col]) if col in sample else {}
            rows.append(
                {
                    "dataset": dataset,
                    "feature": col,
                    "count": n,
                    "missing": self.missing[col],
                    "mean": mean,
                    "std": std,
                    "min": self.min_val[col] if n else np.nan,
                    "p05": q.get("p05", np.nan),
                    "p25": q.get("p25", np.nan),
                    "median": q.get("p50", np.nan),
                    "p75": q.get("p75", np.nan),
                    "p95": q.get("p95", np.nan),
                    "max": self.max_val[col] if n else np.nan,
                }
            )
        return rows


def _quantiles(series: pd.Series) -> Dict[str, float]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {}
    qs = values.quantile([0.05, 0.25, 0.50, 0.75, 0.95])
    return {
        "p05": float(qs.loc[0.05]),
        "p25": float(qs.loc[0.25]),
        "p50": float(qs.loc[0.50]),
        "p75": float(qs.loc[0.75]),
        "p95": float(qs.loc[0.95]),
    }


def discover_production_files() -> List[Path]:
    processed = ROOT / "data" / "processed"
    files = []
    for path in processed.glob("fused_20*.csv"):
        name = path.name.lower()
        if any(skip in name for skip in ("synthetic", "all_users", "train", "test", "val")):
            continue
        files.append(path)
    return sorted(files)


def discover_synthetic_production_files() -> List[Path]:
    return sorted((ROOT / "data" / "synthetic_production").glob("synthetic_production_*.csv"))


def canonical_column_map(path: Path) -> Dict[str, str]:
    header = pd.read_csv(path, nrows=0)
    cols = {str(c).strip(): c for c in header.columns}
    lower_to_original = {str(c).strip().lower(): c for c in header.columns}

    mapping: Dict[str, str] = {}
    for canonical, candidates in COLUMN_ALIASES.items():
        found = None
        for candidate in candidates:
            if candidate in cols:
                found = cols[candidate]
                break
            lowered = candidate.lower()
            if lowered in lower_to_original:
                found = lower_to_original[lowered]
                break
        if found is None:
            raise ValueError(f"{path} is missing sensor column for {canonical}")
        mapping[found] = canonical
    return mapping


def needs_accel_conversion(path: Path, usecols: List[str], rename_map: Dict[str, str]) -> bool:
    preview = pd.read_csv(path, usecols=usecols, nrows=5000)
    preview = preview.rename(columns=rename_map)
    for col in SENSOR_COLS:
        preview[col] = pd.to_numeric(preview[col], errors="coerce")
    a_mag = np.sqrt(np.square(preview[ACCEL_COLS]).sum(axis=1))
    median_mag = float(np.nanmedian(a_mag))
    # Physical acceleration usually centers near ~9.8 m/s^2. Raw production
    # milli-g centers near ~1000, so the separation is large.
    return median_mag > 80.0


def clean_chunk(chunk: pd.DataFrame, rename_map: Dict[str, str], convert_accel: bool) -> pd.DataFrame:
    frame = chunk.rename(columns=rename_map)[SENSOR_COLS].copy()
    for col in SENSOR_COLS:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    if convert_accel:
        frame[ACCEL_COLS] = frame[ACCEL_COLS] * MILLI_G_TO_MPS2
    frame["A_mag"] = np.sqrt(np.square(frame[ACCEL_COLS]).sum(axis=1))
    frame["G_mag"] = np.sqrt(np.square(frame[GYRO_COLS]).sum(axis=1))
    return frame


def sample_frame(frame: pd.DataFrame, n: int, rng: np.random.Generator) -> pd.DataFrame:
    if len(frame) <= n:
        return frame
    random_state = int(rng.integers(0, 2**31 - 1))
    return frame.sample(n=n, random_state=random_state)


def process_dataset(
    name: str,
    files: Iterable[Path],
    *,
    per_file: bool = False,
) -> Tuple[RunningStats, pd.DataFrame, Dict[str, RunningStats], List[Dict[str, object]]]:
    rng = np.random.default_rng(RNG_SEED + zlib.crc32(name.encode("utf-8")) % 100_000)
    aggregate = RunningStats()
    aggregate_samples: List[pd.DataFrame] = []
    per_file_stats: Dict[str, RunningStats] = {}
    file_meta: List[Dict[str, object]] = []

    for path in files:
        rename_map = canonical_column_map(path)
        usecols = list(rename_map.keys())
        convert_accel = needs_accel_conversion(path, usecols, rename_map)
        file_stats = RunningStats()
        file_samples: List[pd.DataFrame] = []

        for raw_chunk in pd.read_csv(path, usecols=usecols, chunksize=CHUNK_SIZE):
            chunk = clean_chunk(raw_chunk, rename_map, convert_accel)
            file_stats.update(chunk)

            if sum(len(s) for s in file_samples) < MAX_SAMPLE_PER_FILE:
                remaining = MAX_SAMPLE_PER_FILE - sum(len(s) for s in file_samples)
                target = min(remaining, max(500, MAX_SAMPLE_PER_FILE // 8), len(chunk))
                file_samples.append(sample_frame(chunk, target, rng))

        aggregate.merge(file_stats)
        if file_samples:
            file_sample = pd.concat(file_samples, ignore_index=True)
            aggregate_samples.append(file_sample)

        file_meta.append(
            {
                "dataset": name,
                "file": str(path.relative_to(ROOT)),
                "rows": file_stats.count["Ax"],
                "accel_converted_millig_to_mps2": convert_accel,
            }
        )
        if per_file:
            per_file_stats[path.stem] = file_stats

    if aggregate_samples:
        sample = pd.concat(aggregate_samples, ignore_index=True)
        if len(sample) > MAX_SAMPLE_PER_DATASET:
            sample = sample_frame(sample, MAX_SAMPLE_PER_DATASET, rng).reset_index(drop=True)
    else:
        sample = pd.DataFrame(columns=FEATURE_COLS)
    return aggregate, sample, per_file_stats, file_meta


def stats_lookup(stats_df: pd.DataFrame) -> Dict[str, Dict[str, Dict[str, float]]]:
    lookup: Dict[str, Dict[str, Dict[str, float]]] = {}
    for _, row in stats_df.iterrows():
        lookup.setdefault(str(row["dataset"]), {})[str(row["feature"])] = {
            "mean": float(row["mean"]),
            "std": float(row["std"]),
            "p05": float(row["p05"]),
            "p95": float(row["p95"]),
        }
    return lookup


def wasserstein_approx(a: np.ndarray, b: np.ndarray, n: int = 5000) -> float:
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) == 0 or len(b) == 0:
        return np.nan
    if len(a) > n:
        idx = np.linspace(0, len(a) - 1, n).astype(int)
        a = np.sort(a)[idx]
    else:
        a = np.sort(a)
    if len(b) > n:
        idx = np.linspace(0, len(b) - 1, n).astype(int)
        b = np.sort(b)[idx]
    else:
        b = np.sort(b)
    m = min(len(a), len(b))
    if m == 0:
        return np.nan
    qa = np.interp(np.linspace(0, 1, m), np.linspace(0, 1, len(a)), a)
    qb = np.interp(np.linspace(0, 1, m), np.linspace(0, 1, len(b)), b)
    return float(np.mean(np.abs(qa - qb)))


def psi(ref: np.ndarray, cur: np.ndarray, bins: int = 10) -> float:
    ref = ref[np.isfinite(ref)]
    cur = cur[np.isfinite(cur)]
    if len(ref) == 0 or len(cur) == 0:
        return np.nan
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf
    ref_counts, _ = np.histogram(ref, bins=edges)
    cur_counts, _ = np.histogram(cur, bins=edges)
    ref_pct = np.clip(ref_counts / max(ref_counts.sum(), 1), 1e-6, None)
    cur_pct = np.clip(cur_counts / max(cur_counts.sum(), 1), 1e-6, None)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def pairwise_shift(
    stats_df: pd.DataFrame,
    samples: Dict[str, pd.DataFrame],
    baseline: str = "train_all_users",
) -> pd.DataFrame:
    lookup = stats_lookup(stats_df)
    rows = []
    datasets = [d for d in samples if d != baseline]
    for dataset in datasets:
        for feature in FEATURE_COLS:
            ref = lookup[baseline][feature]
            cur = lookup[dataset][feature]
            ref_std = ref["std"] if ref["std"] > 1e-12 else np.nan
            std_ratio = cur["std"] / ref["std"] if ref["std"] > 1e-12 else np.nan
            rows.append(
                {
                    "reference": baseline,
                    "dataset": dataset,
                    "feature": feature,
                    "mean_delta": cur["mean"] - ref["mean"],
                    "mean_delta_in_train_std": abs(cur["mean"] - ref["mean"]) / ref_std,
                    "std_ratio": std_ratio,
                    "wasserstein_approx": wasserstein_approx(
                        samples[baseline][feature].to_numpy(dtype=np.float64),
                        samples[dataset][feature].to_numpy(dtype=np.float64),
                    ),
                    "psi_vs_train": psi(
                        samples[baseline][feature].to_numpy(dtype=np.float64),
                        samples[dataset][feature].to_numpy(dtype=np.float64),
                    ),
                }
            )
    out = pd.DataFrame(rows)
    out["simple_shift_score"] = (
        out["mean_delta_in_train_std"].fillna(0)
        + np.abs(np.log(out["std_ratio"].replace(0, np.nan))).fillna(0)
        + out["psi_vs_train"].fillna(0)
    )
    return out


def composite_distance(row_stats: Dict[str, Dict[str, float]], ref_stats: Dict[str, Dict[str, float]]) -> float:
    parts = []
    for feature in SENSOR_COLS:
        ref_std = ref_stats[feature]["std"]
        cur_mean = row_stats[feature]["mean"]
        cur_std = row_stats[feature]["std"]
        if ref_std > 1e-12 and cur_std > 1e-12:
            parts.append(abs(cur_mean - ref_stats[feature]["mean"]) / ref_std)
            parts.append(abs(math.log(cur_std / ref_std)))
    return float(np.mean(parts)) if parts else np.nan


def make_session_stats(
    per_file_stats: Dict[str, RunningStats],
    ref_stats_df: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    ref_lookup = stats_lookup(ref_stats_df)
    train_ref = ref_lookup["train_all_users"]
    synth_ref = ref_lookup.get("synthetic_codex")
    for stem, stat in per_file_stats.items():
        stat_rows = stat.to_rows(stem, pd.DataFrame(columns=FEATURE_COLS))
        row_lookup = {
            r["feature"]: {"mean": float(r["mean"]), "std": float(r["std"])}
            for r in stat_rows
        }
        session_id = re.sub(r"^fused_", "", stem).replace("_50Hz", "")
        rows.append(
            {
                "session_id": session_id,
                "rows": stat.count["Ax"],
                "distance_to_train": composite_distance(row_lookup, train_ref),
                "distance_to_synthetic_codex": (
                    composite_distance(row_lookup, synth_ref) if synth_ref else np.nan
                ),
                "Ax_mean": row_lookup["Ax"]["mean"],
                "Ay_mean": row_lookup["Ay"]["mean"],
                "Az_mean": row_lookup["Az"]["mean"],
                "Gx_std": row_lookup["Gx"]["std"],
                "Gy_std": row_lookup["Gy"]["std"],
                "Gz_std": row_lookup["Gz"]["std"],
            }
        )
    return pd.DataFrame(rows).sort_values("distance_to_train", ascending=False)


def plot_grouped_bars(stats_df: pd.DataFrame, metric: str, features: List[str], path: Path, title: str) -> None:
    pivot = stats_df[stats_df["feature"].isin(features)].pivot(
        index="feature", columns="dataset", values=metric
    )
    ax = pivot.plot(kind="bar", figsize=(12, 6), width=0.82)
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel(metric)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_hist_overlay(samples: Dict[str, pd.DataFrame], feature: str, path: Path, title: str) -> None:
    plt.figure(figsize=(11, 6))
    for dataset, sample in samples.items():
        values = pd.to_numeric(sample[feature], errors="coerce").dropna()
        if values.empty:
            continue
        lo, hi = np.nanpercentile(values, [1, 99])
        clipped = values.clip(lo, hi)
        plt.hist(clipped, bins=80, density=True, histtype="step", linewidth=1.6, label=dataset)
    plt.title(title)
    plt.xlabel(feature)
    plt.ylabel("density")
    plt.grid(alpha=0.2)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_shift_heatmap(shift_df: pd.DataFrame, path: Path) -> None:
    pivot = shift_df.pivot(index="dataset", columns="feature", values="psi_vs_train")
    fig, ax = plt.subplots(figsize=(11, 4.8))
    im = ax.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("Distribution Shift vs Train (PSI-like, lower is closer)")
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            value = pivot.iloc[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.85)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_session_similarity(session_df: pd.DataFrame, path: Path) -> None:
    if session_df.empty:
        return
    show = session_df.sort_values("distance_to_train", ascending=False)
    labels = show["session_id"].str.replace("_", "-", regex=False)
    x = np.arange(len(show))
    width = 0.42
    plt.figure(figsize=(14, 6))
    plt.bar(x - width / 2, show["distance_to_train"], width, label="distance to train")
    plt.bar(x + width / 2, show["distance_to_synthetic_codex"], width, label="distance to synthetic_codex")
    plt.xticks(x, labels, rotation=75, ha="right", fontsize=7)
    plt.ylabel("composite mean/std distance")
    plt.title("Production Sessions: Distance to Train vs Synthetic Codex")
    plt.grid(axis="y", alpha=0.25)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_magnitude_scatter(stats_df: pd.DataFrame, path: Path) -> None:
    means = stats_df.pivot(index="dataset", columns="feature", values="mean")
    stds = stats_df.pivot(index="dataset", columns="feature", values="std")
    plt.figure(figsize=(8, 6))
    for dataset in means.index:
        plt.scatter(means.loc[dataset, "A_mag"], stds.loc[dataset, "G_mag"], s=90)
        plt.text(means.loc[dataset, "A_mag"], stds.loc[dataset, "G_mag"], f" {dataset}", fontsize=9)
    plt.xlabel("mean accelerometer magnitude (m/s^2)")
    plt.ylabel("gyro magnitude std (deg/s)")
    plt.title("Simple Sensor Energy Map")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def markdown_table(df: pd.DataFrame, columns: List[str], max_rows: int = 20) -> str:
    view = df[columns].head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: f"{x:.4g}" if pd.notna(x) else "")
    rows = [[str(value) for value in row] for row in view.to_numpy()]
    headers = [str(col) for col in view.columns]
    widths = [
        max(len(headers[idx]), *(len(row[idx]) for row in rows)) if rows else len(headers[idx])
        for idx in range(len(headers))
    ]
    header_line = "| " + " | ".join(headers[idx].ljust(widths[idx]) for idx in range(len(headers))) + " |"
    sep_line = "| " + " | ".join("-" * widths[idx] for idx in range(len(headers))) + " |"
    body = [
        "| " + " | ".join(row[idx].ljust(widths[idx]) for idx in range(len(headers))) + " |"
        for row in rows
    ]
    return "\n".join([header_line, sep_line, *body])


def build_report(
    stats_df: pd.DataFrame,
    shift_df: pd.DataFrame,
    session_df: pd.DataFrame,
    file_meta: List[Dict[str, object]],
    output_paths: Dict[str, Path],
) -> str:
    dataset_summary = (
        stats_df[stats_df["feature"].eq("Ax")]
        .loc[:, ["dataset", "count", "missing"]]
        .rename(columns={"count": "rows_with_Ax", "missing": "missing_Ax"})
    )

    mag = stats_df[stats_df["feature"].isin(["A_mag", "G_mag"])][
        ["dataset", "feature", "mean", "std", "p05", "median", "p95"]
    ]

    top_shift = (
        shift_df.sort_values("simple_shift_score", ascending=False)
        .loc[:, ["dataset", "feature", "mean_delta_in_train_std", "std_ratio", "psi_vs_train"]]
        .head(12)
    )

    session_top = session_df.head(10)[
        ["session_id", "rows", "distance_to_train", "distance_to_synthetic_codex", "Ax_mean", "Ay_mean", "Az_mean"]
    ]

    converted = pd.DataFrame(file_meta)
    converted_summary = converted.groupby("dataset")["accel_converted_millig_to_mps2"].agg(["sum", "count"]).reset_index()
    converted_summary["note"] = converted_summary.apply(
        lambda r: f"{int(r['sum'])}/{int(r['count'])} file(s) converted from milli-g", axis=1
    )

    lines = [
        "# Train vs Synthetic vs Production Distribution Comparison",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Scope",
        "",
        "- Train: all users labeled data, not only users 1-4.",
        "- Synthetic: all labeled synthetic candidates found in processed form, plus synthetic-production stress files.",
        "- Production: all processed `fused_20*_50Hz.csv` production sessions.",
        "- Sensor space: raw physical space after Stage 1-3 compatible column normalization and accelerometer unit conversion.",
        "",
        "## Dataset Row Counts",
        "",
        markdown_table(dataset_summary, ["dataset", "rows_with_Ax", "missing_Ax"], 20),
        "",
        "## Unit Conversion Check",
        "",
        markdown_table(converted_summary, ["dataset", "note"], 20),
        "",
        "## Magnitude Summary",
        "",
        markdown_table(mag, ["dataset", "feature", "mean", "std", "p05", "median", "p95"], 20),
        "",
        "## Largest Differences vs Train",
        "",
        markdown_table(
            top_shift,
            ["dataset", "feature", "mean_delta_in_train_std", "std_ratio", "psi_vs_train"],
            12,
        ),
        "",
        "## Production Sessions Furthest From Train",
        "",
        markdown_table(
            session_top,
            [
                "session_id",
                "rows",
                "distance_to_train",
                "distance_to_synthetic_codex",
                "Ax_mean",
                "Ay_mean",
                "Az_mean",
            ],
            10,
        ),
        "",
        "## Charts",
        "",
    ]
    for label, path in output_paths.items():
        lines.append(f"- {label}: `{path.relative_to(ROOT)}`")
    lines.extend(
        [
            "",
            "## Interpretation Guide",
            "",
            "- PSI-like values near 0 are close; above ~0.25 is a visible shift; above ~1 is a large shift.",
            "- `mean_delta_in_train_std` says how many train standard deviations the dataset mean moved.",
            "- `std_ratio` above 1 means the dataset is more variable than train; below 1 means less variable.",
            "- `synthetic_codex` is the raw-like labeled synthetic all-users file generated from the real all-users profile.",
            "- `synthetic_other` is another labeled synthetic candidate and is kept in the report because its distribution differs strongly.",
            "- `synthetic_production` is unlabeled stress-test data generated from production statistics, not class-labeled training-like data.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chart_dir = OUT_DIR / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)

    datasets = {
        "train_all_users": [ROOT / "data" / "processed" / "fused_all_users_data_labeled_50Hz.csv"],
        "synthetic_codex": [ROOT / "data" / "processed" / "fused_synthetic_codex_input_50Hz.csv"],
        "synthetic_other": [ROOT / "data" / "processed" / "fused_synthetic_labeled_50Hz.csv"],
        "synthetic_production": discover_synthetic_production_files(),
        "production_all": discover_production_files(),
    }

    missing = [str(p) for files in datasets.values() for p in files if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing expected input files:\n" + "\n".join(missing))

    all_stats_rows: List[Dict[str, object]] = []
    samples: Dict[str, pd.DataFrame] = {}
    all_file_meta: List[Dict[str, object]] = []
    production_per_file: Dict[str, RunningStats] = {}

    for dataset, files in datasets.items():
        stats, sample, per_file_stats, meta = process_dataset(
            dataset, files, per_file=(dataset == "production_all")
        )
        samples[dataset] = sample
        all_file_meta.extend(meta)
        all_stats_rows.extend(stats.to_rows(dataset, sample))
        if dataset == "production_all":
            production_per_file = per_file_stats

    stats_df = pd.DataFrame(all_stats_rows)
    stats_path = OUT_DIR / "distribution_stats.csv"
    stats_df.to_csv(stats_path, index=False)

    shift_df = pairwise_shift(stats_df, samples, baseline="train_all_users")
    shift_path = OUT_DIR / "shift_vs_train.csv"
    shift_df.to_csv(shift_path, index=False)

    session_df = make_session_stats(production_per_file, stats_df)
    session_path = OUT_DIR / "production_session_similarity.csv"
    session_df.to_csv(session_path, index=False)

    file_meta_path = OUT_DIR / "source_files_and_unit_conversion.json"
    file_meta_path.write_text(json.dumps(all_file_meta, indent=2), encoding="utf-8")

    corr_dir = OUT_DIR / "correlations"
    corr_dir.mkdir(exist_ok=True)
    for dataset, sample in samples.items():
        corr = sample[SENSOR_COLS].corr()
        corr.to_csv(corr_dir / f"{dataset}_correlation.csv")

    chart_paths = {
        "Sensor means": chart_dir / "chart_01_sensor_means.png",
        "Sensor standard deviations": chart_dir / "chart_02_sensor_stds.png",
        "Acceleration magnitude overlay": chart_dir / "chart_03_accel_magnitude_overlay.png",
        "Gyroscope magnitude overlay": chart_dir / "chart_04_gyro_magnitude_overlay.png",
        "Shift heatmap vs train": chart_dir / "chart_05_shift_heatmap_vs_train.png",
        "Production session similarity": chart_dir / "chart_06_production_session_similarity.png",
        "Simple sensor energy map": chart_dir / "chart_07_sensor_energy_map.png",
    }
    plot_grouped_bars(stats_df, "mean", SENSOR_COLS, chart_paths["Sensor means"], "Sensor Means by Dataset")
    plot_grouped_bars(stats_df, "std", SENSOR_COLS, chart_paths["Sensor standard deviations"], "Sensor Standard Deviations by Dataset")
    plot_hist_overlay(samples, "A_mag", chart_paths["Acceleration magnitude overlay"], "Acceleration Magnitude Distribution")
    plot_hist_overlay(samples, "G_mag", chart_paths["Gyroscope magnitude overlay"], "Gyroscope Magnitude Distribution")
    plot_shift_heatmap(shift_df, chart_paths["Shift heatmap vs train"])
    plot_session_similarity(session_df, chart_paths["Production session similarity"])
    plot_magnitude_scatter(stats_df, chart_paths["Simple sensor energy map"])

    report = build_report(stats_df, shift_df, session_df, all_file_meta, chart_paths)
    report_path = OUT_DIR / "README.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"Wrote report: {report_path}")
    print(f"Wrote stats: {stats_path}")
    print(f"Wrote shift table: {shift_path}")
    print(f"Wrote session similarity: {session_path}")
    print(f"Wrote charts: {chart_dir}")


if __name__ == "__main__":
    main()

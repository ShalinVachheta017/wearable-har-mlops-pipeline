#!/usr/bin/env python3
"""Generate evidence assets for thesis Chapter 4.

The script is intentionally self-contained: it scans the repository data
artifacts, computes channel summaries with robust column detection, creates
tables and figures, writes thesis text snippets, and inserts the statistical
comparison section into the Chapter 4 LaTeX source.
"""

from __future__ import annotations

import csv
import json
import math
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patches


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "chapter4"
TABLE_DIR = ROOT / "thesis" / "tables"
FIGURE_DIR = ROOT / "thesis" / "figures"
TEX_DIR = ROOT / "thesis" / "tex"
CH4_PATH = ROOT / "thesis" / "chapters" / "ch4_data_model_development.tex"
CH4_BACKUP = CH4_PATH.with_suffix(CH4_PATH.suffix + ".bak")

CHANNELS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
ACC_CHANNELS = {"Ax", "Ay", "Az"}
GYRO_CHANNELS = {"Gx", "Gy", "Gz"}
COLORS = {
    "deep_blue": "#2F5D8A",
    "teal": "#4FA3A5",
    "soft_gold": "#D9A441",
    "warm_white": "#F8FAFC",
    "charcoal": "#263238",
    "light_blue": "#D7E6F5",
    "light_teal": "#DDF1F1",
    "light_gold": "#F5E5BE",
    "gray": "#78909C",
}
MS2_PER_MILLIG = 0.00980665
CHUNKSIZE = 200_000
MAX_SAMPLE_PER_CHANNEL = 250_000
RNG = np.random.default_rng(42)


def ensure_dirs() -> None:
    for path in [REPORT_DIR, TABLE_DIR, FIGURE_DIR, TEX_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def normalized_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


CHANNEL_PATTERNS = {
    "Ax": {
        "ax",
        "axw",
        "accx",
        "accelx",
        "accelerometerx",
        "accelerationx",
        "accelerometeraxisx",
    },
    "Ay": {
        "ay",
        "ayw",
        "accy",
        "accely",
        "accelerometery",
        "accelerationy",
        "accelerometeraxisy",
    },
    "Az": {
        "az",
        "azw",
        "accz",
        "accelz",
        "accelerometerz",
        "accelerationz",
        "accelerometeraxisz",
    },
    "Gx": {
        "gx",
        "gxw",
        "gyrox",
        "gyrx",
        "angularvelocityx",
        "gyroscopex",
        "gyroscopeaxisx",
    },
    "Gy": {
        "gy",
        "gyw",
        "gyroy",
        "gyry",
        "angularvelocityy",
        "gyroscopey",
        "gyroscopeaxisy",
    },
    "Gz": {
        "gz",
        "gzw",
        "gyroz",
        "gyrz",
        "angularvelocityz",
        "gyroscopez",
        "gyroscopeaxisz",
    },
}


def detect_channel_columns(columns: Iterable[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    normalized = {normalized_name(c): c for c in columns}
    for canonical, patterns in CHANNEL_PATTERNS.items():
        for pattern in patterns:
            if pattern in normalized:
                mapping[canonical] = normalized[pattern]
                break
        if canonical not in mapping:
            for norm, original in normalized.items():
                if norm.endswith(canonical.lower()) or canonical.lower() in norm:
                    mapping[canonical] = original
                    break
    return mapping


def detect_column(columns: Iterable[str], candidates: Iterable[str]) -> str:
    normalized = {normalized_name(c): c for c in columns}
    for cand in candidates:
        n = normalized_name(cand)
        if n in normalized:
            return normalized[n]
    for norm, original in normalized.items():
        if any(normalized_name(c) in norm for c in candidates):
            return original
    return ""


def read_columns(path: Path) -> list[str]:
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path, nrows=0).columns.tolist()
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path, nrows=0).columns.tolist()
    except Exception:
        return []
    return []


def csv_line_count(path: Path, max_size_for_count: int = 150_000_000) -> tuple[str, str]:
    if path.stat().st_size > max_size_for_count:
        return "", "row count skipped for large raw file"
    try:
        with path.open("rb") as f:
            lines = sum(1 for _ in f)
        return str(max(0, lines - 1)), ""
    except Exception as exc:
        return "", f"row count failed: {exc}"


def xlsx_row_count(path: Path) -> tuple[str, str]:
    try:
        from openpyxl import load_workbook

        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.max_row or 0
        wb.close()
        return str(max(0, rows - 1)), ""
    except Exception as exc:
        return "", f"xlsx row count failed: {exc}"


def npy_shape(path: Path) -> tuple[str, str]:
    try:
        arr = np.load(path, mmap_mode="r")
        return "x".join(map(str, arr.shape)), ""
    except Exception as exc:
        return "", f"npy shape failed: {exc}"


def json_shape(path: Path) -> tuple[str, str]:
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        if isinstance(obj, list):
            return str(len(obj)), "json list entries"
        if isinstance(obj, dict):
            return str(len(obj.keys())), "json top-level keys"
    except Exception as exc:
        return "", f"json read failed: {exc}"
    return "", ""


def classify_file(path: Path) -> tuple[str, str, str]:
    rp = rel(path).lower()
    name = path.name.lower()
    labels = "unknown"
    group = "other"
    notes = ""
    if "all_users_data_labeled" in name:
        group = "labeled_garmin_development"
        labels = "yes"
    elif "synthetic_codex" in rp or "codex_synth" in rp:
        group = "synthetic_codex"
        labels = "yes" if "unlabeled" not in name else "no"
    elif "synthetic_other" in rp or "synthetic_cluade" in rp or "synthetic_claude" in rp:
        group = "synthetic_other"
        labels = "yes"
    elif "raw_backup" in rp or "/raw/" in rp or "\\raw\\" in str(path).lower():
        if "accelerometer" in name or "gyroscope" in name or "record" in name:
            group = "production_replay_raw"
            labels = "mostly no"
    elif "processed/fused_2025" in rp or "processed\\fused_2025" in str(path).lower():
        group = "production_replay_fused_50hz"
        labels = "mostly no"
    elif "prepared" in rp and path.suffix.lower() == ".npy":
        group = "prepared_numpy_array"
        labels = "depends"
    elif "model_info" in name:
        group = "model_metadata"
        labels = "n/a"
    elif name in {"pipeline_config.yaml", "config.py", "train.py"}:
        group = "config_or_code_reference"
        labels = "n/a"
    elif "training_report_" in name:
        group = "model_training_report"
        labels = "yes"
    elif (
        "ch7" in rp
        or "chapter7" in rp
        or "pipeline_runs" in rp
        or "thesis_branch_comparison" in rp
        or "charts_26runs" in rp
    ):
        group = "chapter7_results_or_reports"
        labels = "depends"
    if "raw_backup" in rp:
        notes = "backup copy of raw production replay source"
    return group, labels, notes


def build_inventory() -> pd.DataFrame:
    patterns = [
        ROOT / "data" / "all_users_data_labeled.csv",
        ROOT / "data" / "raw" / "*",
        ROOT / "data" / "raw_backup" / "*",
        ROOT / "data" / "processed" / "*.csv",
        ROOT / "data" / "synthetic_runs" / "*.csv",
        ROOT / "data" / "codex_synth" / "*",
        ROOT / "data" / "synthetic_cluade" / "*",
        ROOT / "data" / "prepared" / "*.npy",
        ROOT / "data" / "prepared" / "*.json",
        ROOT / "config" / "pipeline_config.yaml",
        ROOT / "src" / "config.py",
        ROOT / "src" / "train.py",
        ROOT / "models" / "pretrained" / "model_info.json",
        ROOT / "models" / "retrained" / "training_report_*.json",
        ROOT / "thesis" / "chapters" / "ch7_experiments_evaluation.tex",
        ROOT
        / "thesis"
        / "april_report"
        / "chapters"
        / "ch7_experiments_robustness_evaluation.tex",
        ROOT / "reports" / "pipeline_runs" / "labeled_synthetic_vs_unlabeled_raw_20260417.*",
        ROOT / "reports" / "pipeline_runs" / "batch_28_full" / "SUMMARY.md",
        ROOT / "reports" / "pipeline_runs" / "batch_28_full" / "all_runs_metrics.*",
        ROOT
        / "outputs"
        / "thesis_branch_comparison"
        / "mmd_runtime_branch"
        / "THESIS_ABLATION_SUMMARY.md",
        ROOT
        / "outputs"
        / "thesis_branch_comparison"
        / "mmd_runtime_branch"
        / "preprocessing_ablation_summary.csv",
        ROOT
        / "outputs"
        / "thesis_branch_comparison"
        / "mmd_runtime_branch"
        / "drift_monitor_ablation_summary.csv",
        ROOT
        / "outputs"
        / "thesis_branch_comparison"
        / "mmd_trigger_redesign"
        / "mmd_staged_policy_summary.csv",
        ROOT / "outputs" / "charts_26runs" / "model_comparison_results.csv",
        ROOT / "models" / "mmd_reference_windows.npy",
        ROOT / "outputs" / "thesis_branch_comparison" / "mmd_runtime_branch" / "*.npy",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(pattern.parent.glob(pattern.name)))

    rows: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for path in files:
        if not path.is_file() or path in seen:
            continue
        seen.add(path)
        group, labels, base_notes = classify_file(path)
        columns = read_columns(path)
        mapping = detect_channel_columns(columns)
        timestamp_col = detect_column(columns, ["timestamp", "time", "true_time", "timestamp_iso"])
        activity_col = detect_column(columns, ["activity", "label", "class"])
        participant_col = detect_column(columns, ["user", "participant", "subject"])
        detected = ""
        notes = base_notes
        suffix = path.suffix.lower().lstrip(".") or "unknown"
        extra_note = ""
        if suffix == "csv":
            detected, extra_note = csv_line_count(path)
        elif suffix in {"xlsx", "xls"}:
            detected, extra_note = xlsx_row_count(path)
        elif suffix == "npy":
            detected, extra_note = npy_shape(path)
        elif suffix == "json":
            detected, extra_note = json_shape(path)
        if extra_note:
            notes = "; ".join([n for n in [notes, extra_note] if n])
        rows.append(
            {
                "dataset_group": group,
                "file_path": rel(path),
                "file_type": suffix,
                "labels_available": labels,
                "detected_rows_or_windows": detected,
                "detected_columns": "; ".join(map(str, columns)),
                "sensor_channels_found": "; ".join(
                    f"{k}:{v}" for k, v in mapping.items()
                ),
                "timestamp_column_found": timestamp_col,
                "activity_column_found": activity_col,
                "participant_column_found": participant_col,
                "notes": notes,
            }
        )
    return pd.DataFrame(rows)


@dataclass
class ChannelAccumulator:
    count: int = 0
    missing_count: int = 0
    total_seen: int = 0
    sum_value: float = 0.0
    sum_square: float = 0.0
    min_value: float = math.inf
    max_value: float = -math.inf
    samples: list[np.ndarray] = field(default_factory=list)

    def update(self, values: pd.Series | np.ndarray) -> None:
        arr = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(dtype=float)
        self.total_seen += len(arr)
        missing = np.isnan(arr)
        self.missing_count += int(missing.sum())
        arr = arr[~missing]
        if arr.size == 0:
            return
        self.count += int(arr.size)
        self.sum_value += float(arr.sum())
        self.sum_square += float(np.square(arr).sum())
        self.min_value = min(self.min_value, float(arr.min()))
        self.max_value = max(self.max_value, float(arr.max()))
        if arr.size > MAX_SAMPLE_PER_CHANNEL:
            arr = RNG.choice(arr, size=MAX_SAMPLE_PER_CHANNEL, replace=False)
        self.samples.append(arr.astype(np.float32))
        self._trim_samples()

    def _trim_samples(self) -> None:
        total = sum(len(a) for a in self.samples)
        if total <= MAX_SAMPLE_PER_CHANNEL:
            return
        merged = np.concatenate(self.samples)
        if len(merged) > MAX_SAMPLE_PER_CHANNEL:
            merged = RNG.choice(merged, size=MAX_SAMPLE_PER_CHANNEL, replace=False)
        self.samples = [merged.astype(np.float32)]

    def sample_array(self) -> np.ndarray:
        if not self.samples:
            return np.array([], dtype=np.float32)
        return np.concatenate(self.samples)

    def row(self, dataset_group: str, channel: str, unit_guess: str, state: str) -> dict[str, Any]:
        sample = self.sample_array()
        mean = self.sum_value / self.count if self.count else float("nan")
        if self.count > 1:
            variance = max(0.0, (self.sum_square - self.count * mean * mean) / (self.count - 1))
            std = math.sqrt(variance)
        else:
            std = float("nan")
        q25 = float(np.percentile(sample, 25)) if sample.size else float("nan")
        median = float(np.percentile(sample, 50)) if sample.size else float("nan")
        q75 = float(np.percentile(sample, 75)) if sample.size else float("nan")
        skew = float(pd.Series(sample).skew()) if sample.size > 2 else float("nan")
        kurt = float(pd.Series(sample).kurtosis()) if sample.size > 3 else float("nan")
        total = self.count + self.missing_count
        return {
            "dataset_group": dataset_group,
            "channel": channel,
            "count": self.count,
            "missing_count": self.missing_count,
            "missing_percent": 100.0 * self.missing_count / total if total else 0.0,
            "mean": mean,
            "std": std,
            "min": self.min_value if self.count else float("nan"),
            "25_percentile": q25,
            "median": median,
            "75_percentile": q75,
            "max": self.max_value if self.count else float("nan"),
            "IQR": q75 - q25 if sample.size else float("nan"),
            "skewness": skew,
            "kurtosis": kurt,
            "unit_guess": unit_guess,
            "preprocessing_state_guess": state,
        }


def likely_millig(df: pd.DataFrame, mapping: dict[str, str]) -> bool:
    present = [mapping[c] for c in ACC_CHANNELS if c in mapping]
    if not present:
        return False
    sample = df[present].head(1000).apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    sample = sample[~np.isnan(sample)]
    if sample.size == 0:
        return False
    return float(np.nanpercentile(np.abs(sample), 90)) > 50.0


def iter_csv_chunks(path: Path, usecols: list[str] | None = None) -> Iterable[pd.DataFrame]:
    yield from pd.read_csv(
        path,
        usecols=usecols,
        chunksize=CHUNKSIZE,
        low_memory=False,
        on_bad_lines="skip",
    )


def get_dataset_files() -> dict[str, list[Path]]:
    production = sorted((ROOT / "data" / "processed").glob("fused_2025*_50Hz.csv"))
    return {
        "labeled_garmin": [ROOT / "data" / "all_users_data_labeled.csv"],
        "production_replay": production,
        "synthetic_codex": [ROOT / "data" / "synthetic_runs" / "synthetic_codex_input.csv"],
        "synthetic_other": [ROOT / "data" / "synthetic_runs" / "synthetic_other_input.csv"],
    }


def compute_channel_statistics() -> tuple[pd.DataFrame, dict[str, dict[str, np.ndarray]], dict[str, int]]:
    files_by_group = get_dataset_files()
    stats_rows: list[dict[str, Any]] = []
    samples_by_group: dict[str, dict[str, np.ndarray]] = {}
    rows_by_group: dict[str, int] = {}

    for group, files in files_by_group.items():
        accs = {ch: ChannelAccumulator() for ch in CHANNELS}
        total_rows = 0
        state_by_channel = {ch: "raw" for ch in CHANNELS}
        unit_by_channel = {
            "Ax": "m/s^2",
            "Ay": "m/s^2",
            "Az": "m/s^2",
            "Gx": "deg/s",
            "Gy": "deg/s",
            "Gz": "deg/s",
        }
        if group == "production_replay":
            state_by_channel.update({ch: "unit_harmonized_from_raw" for ch in ACC_CHANNELS})
            state_by_channel.update({ch: "raw_or_resampled" for ch in GYRO_CHANNELS})

        for path in files:
            if not path.exists():
                continue
            columns = read_columns(path)
            mapping = detect_channel_columns(columns)
            if not mapping:
                continue
            usecols = sorted(set(mapping.values()))
            first = True
            convert_acc = False
            for chunk in iter_csv_chunks(path, usecols=usecols):
                if first:
                    convert_acc = group == "production_replay" and likely_millig(chunk, mapping)
                    if convert_acc:
                        for ch in ACC_CHANNELS:
                            unit_by_channel[ch] = "m/s^2 (converted from milliG)"
                    first = False
                total_rows += len(chunk)
                for ch in CHANNELS:
                    if ch not in mapping:
                        continue
                    values = pd.to_numeric(chunk[mapping[ch]], errors="coerce")
                    if convert_acc and ch in ACC_CHANNELS:
                        values = values * MS2_PER_MILLIG
                    accs[ch].update(values)

        rows_by_group[group] = total_rows
        samples_by_group[group] = {ch: accs[ch].sample_array() for ch in CHANNELS}
        for ch in CHANNELS:
            stats_rows.append(accs[ch].row(group, ch, unit_by_channel[ch], state_by_channel[ch]))

    stats_df = pd.DataFrame(stats_rows)
    return stats_df, samples_by_group, rows_by_group


def compute_comparison_metrics(
    stats_df: pd.DataFrame, samples_by_group: dict[str, dict[str, np.ndarray]]
) -> pd.DataFrame:
    pairs = [
        ("labeled_garmin", "production_replay"),
        ("labeled_garmin", "synthetic_codex"),
        ("labeled_garmin", "synthetic_other"),
    ]
    has_self = "self_recorded_final" in set(stats_df["dataset_group"])
    if has_self:
        pairs.extend(
            [
                ("production_replay", "self_recorded_final"),
                ("labeled_garmin", "self_recorded_final"),
            ]
        )
    try:
        from scipy.stats import ks_2samp, wasserstein_distance

        scipy_available = True
    except Exception:
        scipy_available = False

    rows = []
    indexed = stats_df.set_index(["dataset_group", "channel"])
    for a, b in pairs:
        for ch in CHANNELS:
            if (a, ch) not in indexed.index or (b, ch) not in indexed.index:
                continue
            ar = indexed.loc[(a, ch)]
            br = indexed.loc[(b, ch)]
            a_s = samples_by_group.get(a, {}).get(ch, np.array([]))
            b_s = samples_by_group.get(b, {}).get(ch, np.array([]))
            wasserstein = np.nan
            ks_stat = np.nan
            if scipy_available and len(a_s) and len(b_s):
                limit = min(len(a_s), len(b_s), 100_000)
                aa = RNG.choice(a_s, size=limit, replace=False) if len(a_s) > limit else a_s
                bb = RNG.choice(b_s, size=limit, replace=False) if len(b_s) > limit else b_s
                wasserstein = float(wasserstein_distance(aa, bb))
                ks_stat = float(ks_2samp(aa, bb).statistic)
            rows.append(
                {
                    "dataset_a": a,
                    "dataset_b": b,
                    "channel": ch,
                    "mean_difference": float(br["mean"] - ar["mean"]),
                    "std_ratio": float(br["std"] / ar["std"]) if ar["std"] else np.nan,
                    "median_difference": float(br["median"] - ar["median"]),
                    "IQR_ratio": float(br["IQR"] / ar["IQR"]) if ar["IQR"] else np.nan,
                    "wasserstein_distance": wasserstein,
                    "ks_statistic": ks_stat,
                    "comparison_note": (
                        "accelerometer values harmonized to m/s^2 for production replay"
                        if b == "production_replay" or a == "production_replay"
                        else "same nominal channel units"
                    ),
                }
            )
    return pd.DataFrame(rows)


def compute_class_and_windowing() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    path = ROOT / "data" / "all_users_data_labeled.csv"
    usecols = ["activity", "User"]
    df = pd.read_csv(path, usecols=usecols)
    window_size = 200
    step_size = 100
    sampling_rate = 50
    raw_counts = df["activity"].value_counts().sort_index()
    total_rows = len(df)

    def windows_for_frame(frame: pd.DataFrame, offset: int = 0) -> list[dict[str, Any]]:
        rows = []
        values = frame["activity"].to_numpy()
        users = frame["User"].to_numpy() if "User" in frame.columns else np.array([])
        for start in range(0, len(frame) - window_size + 1, step_size):
            end = start + window_size
            labels = values[start:end]
            user_vals = users[start:end] if users.size else np.array([])
            majority = Counter(labels).most_common(1)[0][0]
            rows.append(
                {
                    "start_idx": offset + start,
                    "end_idx": offset + end,
                    "activity": majority,
                    "activity_boundary_crossing": len(set(labels.tolist())) > 1,
                    "participant_crossing": len(set(user_vals.tolist())) > 1
                    if user_vals.size
                    else False,
                }
            )
        return rows

    sequential_windows = windows_for_frame(df)
    user_isolated_windows: list[dict[str, Any]] = []
    for user_id, user_df in df.groupby("User", sort=True):
        user_isolated_windows.extend(windows_for_frame(user_df.reset_index(drop=True)))

    seq_counts = Counter(row["activity"] for row in sequential_windows)
    user_counts = Counter(row["activity"] for row in user_isolated_windows)
    activities = sorted(set(raw_counts.index) | set(seq_counts.keys()) | set(user_counts.keys()))
    class_rows = []
    for activity in activities:
        raw = int(raw_counts.get(activity, 0))
        seq = int(seq_counts.get(activity, 0))
        usr = int(user_counts.get(activity, 0))
        class_rows.append(
            {
                "activity": activity,
                "raw_row_count": raw,
                "raw_row_share_percent": 100.0 * raw / total_rows if total_rows else 0.0,
                "sequential_window_count": seq,
                "sequential_window_share_percent": 100.0 * seq / len(sequential_windows)
                if sequential_windows
                else 0.0,
                "user_isolated_window_count": usr,
                "user_isolated_window_share_percent": 100.0 * usr / len(user_isolated_windows)
                if user_isolated_windows
                else 0.0,
            }
        )

    summary_values = {
        "sampling_rate_hz": sampling_rate,
        "window_size_samples": window_size,
        "window_duration_seconds": window_size / sampling_rate,
        "step_size_samples": step_size,
        "step_duration_seconds": step_size / sampling_rate,
        "overlap_percent": 100.0 * (1 - step_size / window_size),
        "raw_row_count": total_rows,
        "participant_count": int(df["User"].nunique()),
        "activity_class_count": int(df["activity"].nunique()),
        "sequential_window_count": len(sequential_windows),
        "sequential_activity_boundary_crossing_windows": int(
            sum(row["activity_boundary_crossing"] for row in sequential_windows)
        ),
        "sequential_participant_crossing_windows": int(
            sum(row["participant_crossing"] for row in sequential_windows)
        ),
        "user_isolated_window_count": len(user_isolated_windows),
        "user_isolated_activity_boundary_crossing_windows": int(
            sum(row["activity_boundary_crossing"] for row in user_isolated_windows)
        ),
        "user_isolated_participant_crossing_windows": int(
            sum(row["participant_crossing"] for row in user_isolated_windows)
        ),
    }
    summary_rows = [{"metric": k, "value": v} for k, v in summary_values.items()]
    return pd.DataFrame(class_rows), pd.DataFrame(summary_rows), summary_values


def write_excel(df: pd.DataFrame, path: Path) -> str:
    try:
        df.to_excel(path, index=False)
        return "created"
    except Exception as exc:
        return f"failed: {exc}"


def latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for key, repl in replacements.items():
        text = text.replace(key, repl)
    return text


def fmt_num(value: Any, digits: int = 2) -> str:
    try:
        if pd.isna(value):
            return "--"
        value = float(value)
        if abs(value) >= 1000:
            return f"{value:,.0f}"
        return f"{value:.{digits}f}"
    except Exception:
        return latex_escape(value)


def latex_unit(value: Any) -> str:
    text = str(value)
    if "m/s^2" in text:
        suffix = ""
        if "converted from milliG" in text:
            suffix = " (converted from milliG)"
        return r"m\,s$^{-2}$" + suffix
    if text == "deg/s":
        return r"deg\,s$^{-1}$"
    return latex_escape(text)


def write_latex_channel_table(stats_df: pd.DataFrame) -> None:
    cols = [
        "dataset_group",
        "channel",
        "count",
        "missing_percent",
        "mean",
        "std",
        "median",
        "IQR",
        "unit_guess",
        "preprocessing_state_guess",
    ]
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Channel-wise descriptive statistics used for the Chapter 4 data comparison. Production replay accelerometer values are reported after internal unit harmonization to m\,s$^{-2}$; the raw files are not overwritten. These statistics describe distributional alignment and do not provide classification accuracy evidence.}",
        r"\label{tab:ch4_channel_statistics}",
        r"\scriptsize",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{llrrrrrrll}",
        r"\hline",
        r"\textbf{Dataset} & \textbf{Ch.} & \textbf{Count} & \textbf{Missing \%} & \textbf{Mean} & \textbf{Std.} & \textbf{Median} & \textbf{IQR} & \textbf{Unit} & \textbf{State} \\",
        r"\hline",
    ]
    for _, row in stats_df[cols].iterrows():
        lines.append(
            " & ".join(
                [
                    latex_escape(row["dataset_group"]),
                    latex_escape(row["channel"]),
                    fmt_num(row["count"], 0),
                    fmt_num(row["missing_percent"], 3),
                    fmt_num(row["mean"], 3),
                    fmt_num(row["std"], 3),
                    fmt_num(row["median"], 3),
                    fmt_num(row["IQR"], 3),
                    latex_unit(row["unit_guess"]),
                    latex_escape(row["preprocessing_state_guess"]),
                ]
            )
            + r" \\"
        )
    lines.extend([r"\hline", r"\end{tabular}%", r"}", r"\end{table}", ""])
    (TABLE_DIR / "ch4_channel_statistics.tex").write_text("\n".join(lines), encoding="utf-8")


def write_latex_shift_table(shift_df: pd.DataFrame) -> None:
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Pairwise channel-shift comparison across Chapter 4 data sources. The metrics are descriptive indicators of train--serve distribution alignment; because the replay sessions are mostly unlabeled and synthetic data are generated by construction, the table must not be interpreted as deployment accuracy evidence.}",
        r"\label{tab:ch4_dataset_shift_comparison}",
        r"\scriptsize",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lllrrrrr}",
        r"\hline",
        r"\textbf{Dataset A} & \textbf{Dataset B} & \textbf{Ch.} & \textbf{Mean diff.} & \textbf{Std. ratio} & \textbf{Median diff.} & \textbf{IQR ratio} & \textbf{KS stat.} \\",
        r"\hline",
    ]
    for _, row in shift_df.iterrows():
        lines.append(
            " & ".join(
                [
                    latex_escape(row["dataset_a"]),
                    latex_escape(row["dataset_b"]),
                    latex_escape(row["channel"]),
                    fmt_num(row["mean_difference"], 3),
                    fmt_num(row["std_ratio"], 3),
                    fmt_num(row["median_difference"], 3),
                    fmt_num(row["IQR_ratio"], 3),
                    fmt_num(row["ks_statistic"], 3),
                ]
            )
            + r" \\"
        )
    lines.extend([r"\hline", r"\end{tabular}%", r"}", r"\end{table}", ""])
    (TABLE_DIR / "ch4_dataset_shift_comparison.tex").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def write_latex_class_table(class_df: pd.DataFrame) -> None:
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Raw-row and window-level class distribution of the labeled Garmin development corpus. The sequential 3,852-window view matches the full-corpus baseline reference, while the user-isolated count reflects the leakage-safe training window construction in \texttt{src/train.py}.}",
        r"\label{tab:window_class_distribution}",
        r"\small",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lrrrrrr}",
        r"\hline",
        r"\textbf{Activity} & \textbf{Raw rows} & \textbf{Raw \%} & \textbf{Seq. windows} & \textbf{Seq. \%} & \textbf{User-isolated windows} & \textbf{User-isolated \%} \\",
        r"\hline",
    ]
    for _, row in class_df.sort_values("activity").iterrows():
        lines.append(
            " & ".join(
                [
                    latex_escape(row["activity"]),
                    fmt_num(row["raw_row_count"], 0),
                    fmt_num(row["raw_row_share_percent"], 2),
                    fmt_num(row["sequential_window_count"], 0),
                    fmt_num(row["sequential_window_share_percent"], 2),
                    fmt_num(row["user_isolated_window_count"], 0),
                    fmt_num(row["user_isolated_window_share_percent"], 2),
                ]
            )
            + r" \\"
        )
    lines.extend([r"\hline", r"\end{tabular}%", r"}", r"\end{table}", ""])
    (TABLE_DIR / "ch4_class_distribution.tex").write_text("\n".join(lines), encoding="utf-8")


def write_latex_windowing_table(summary: dict[str, Any]) -> None:
    display = [
        ("Sampling rate", f"{summary['sampling_rate_hz']} Hz"),
        ("Window size", f"{summary['window_size_samples']} samples"),
        ("Window duration", f"{summary['window_duration_seconds']:.1f} seconds"),
        ("Step size", f"{summary['step_size_samples']} samples"),
        ("Overlap", f"{summary['overlap_percent']:.0f}\\%"),
        ("Sequential full-corpus windows", f"{summary['sequential_window_count']:,}"),
        (
            "Sequential activity-boundary windows",
            f"{summary['sequential_activity_boundary_crossing_windows']:,}",
        ),
        (
            "Sequential participant-crossing windows",
            f"{summary['sequential_participant_crossing_windows']:,}",
        ),
        ("User-isolated training windows", f"{summary['user_isolated_window_count']:,}"),
        (
            "User-isolated participant-crossing windows",
            f"{summary['user_isolated_participant_crossing_windows']:,}",
        ),
    ]
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Windowing summary for the labeled Garmin development corpus. The sequential view preserves the 3,852-window baseline reference; the user-isolated view documents the current training implementation boundary.}",
        r"\label{tab:ch4_windowing_summary}",
        r"\begin{tabular}{lr}",
        r"\hline",
        r"\textbf{Quantity} & \textbf{Value} \\",
        r"\hline",
    ]
    for k, v in display:
        lines.append(f"{latex_escape(k)} & {v} " + r"\\")
    lines.extend([r"\hline", r"\end{tabular}", r"\end{table}", ""])
    (TABLE_DIR / "ch4_windowing_summary.tex").write_text("\n".join(lines), encoding="utf-8")


def save_figure(fig: plt.Figure, name: str) -> None:
    png = FIGURE_DIR / f"{name}.png"
    pdf = FIGURE_DIR / f"{name}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_box(ax: plt.Axes, x: float, y: float, w: float, h: float, text: str, color: str) -> None:
    rect = patches.Rectangle((x, y), w, h, linewidth=1.2, edgecolor=COLORS["charcoal"], facecolor=color)
    ax.add_patch(rect)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=9,
        color=COLORS["charcoal"],
        wrap=True,
    )


def draw_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle="->", color=COLORS["charcoal"], lw=1.3),
    )


def figure_dataset_source_overview() -> None:
    fig, ax = plt.subplots(figsize=(13.5, 7.2))
    ax.axis("off")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    sources = [
        (
            "Labeled Garmin\ndevelopment data",
            "Supports training and\nmatched labeled reference",
            "Cannot prove broad\nsubject-independent deployment",
            COLORS["light_blue"],
        ),
        (
            "Production replay\nsessions",
            "Supports offline inference,\nmonitoring and governance",
            "Mostly unlabeled, so not\naccuracy evidence",
            COLORS["light_teal"],
        ),
        (
            "Synthetic stress-test\ndata",
            "Supports controlled\nrealism stress testing",
            "Generated data are not\nreal deployment proof",
            COLORS["light_gold"],
        ),
        (
            "Self-recorded final\ndata",
            "Pending final usability\nvalidation source",
            "Accuracy only if reliable\nlabels are collected",
            "#ECEFF1",
        ),
    ]
    x_positions = [0.3, 3.3, 6.3, 9.3]
    for x, (title, supports, cannot, color) in zip(x_positions, sources):
        draw_box(ax, x, 5.4, 2.4, 1.0, title, color)
        draw_box(ax, x, 3.7, 2.4, 1.0, supports, "#FFFFFF")
        draw_box(ax, x, 2.0, 2.4, 1.0, cannot, "#FFFFFF")
        draw_arrow(ax, (x + 1.2, 5.4), (x + 1.2, 4.7))
        draw_arrow(ax, (x + 1.2, 3.7), (x + 1.2, 3.0))
    ax.text(6, 7.35, "Chapter 4 Data Sources and Evidence Boundaries", ha="center", va="center", fontsize=15, weight="bold", color=COLORS["charcoal"])
    ax.text(2.9, 0.9, "Training / labeled reference evidence", ha="center", va="center", fontsize=11, color=COLORS["deep_blue"], weight="bold")
    ax.text(8.9, 0.9, "Monitoring / governance evidence", ha="center", va="center", fontsize=11, color=COLORS["teal"], weight="bold")
    ax.plot([0.2, 5.8], [1.25, 1.25], color=COLORS["deep_blue"], lw=3)
    ax.plot([6.2, 11.8], [1.25, 1.25], color=COLORS["teal"], lw=3)
    save_figure(fig, "ch4_dataset_source_overview")


def figure_mean_std(stats_df: pd.DataFrame, metric: str, name: str, ylabel: str) -> None:
    groups = ["labeled_garmin", "production_replay", "synthetic_codex", "synthetic_other"]
    labels = ["Labeled", "Replay", "Synth Codex", "Synth Other"]
    x = np.arange(len(groups))
    width = 0.12
    fig, ax = plt.subplots(figsize=(13.5, 6.5))
    palette = [COLORS["deep_blue"], COLORS["teal"], COLORS["soft_gold"], "#607D8B", "#90A4AE", "#455A64"]
    for i, ch in enumerate(CHANNELS):
        values = []
        for g in groups:
            row = stats_df[(stats_df["dataset_group"] == g) & (stats_df["channel"] == ch)]
            values.append(float(row.iloc[0][metric]) if not row.empty else np.nan)
        ax.bar(x + (i - 2.5) * width, values, width=width, label=ch, color=palette[i])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel)
    ax.set_title(ylabel + " by Dataset Group", color=COLORS["charcoal"], weight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.08))
    save_figure(fig, name)


def figure_boxplots(samples_by_group: dict[str, dict[str, np.ndarray]]) -> None:
    groups = ["labeled_garmin", "production_replay", "synthetic_codex", "synthetic_other"]
    group_labels = ["Labeled", "Replay", "Synth Codex", "Synth Other"]
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=False)
    for ax, channels, title in [
        (axes[0], ["Ax", "Ay", "Az"], "Accelerometer channels"),
        (axes[1], ["Gx", "Gy", "Gz"], "Gyroscope channels"),
    ]:
        data = []
        labels = []
        colors = []
        for ch in channels:
            for g, gl in zip(groups, group_labels):
                arr = samples_by_group.get(g, {}).get(ch, np.array([]))
                if len(arr) > 20_000:
                    arr = RNG.choice(arr, size=20_000, replace=False)
                data.append(arr)
                labels.append(f"{ch}\n{gl}")
                colors.append(COLORS["light_blue"] if "labeled" in g else COLORS["light_teal"] if "production" in g else COLORS["light_gold"])
        bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, showfliers=False)
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_edgecolor(COLORS["charcoal"])
        for med in bp["medians"]:
            med.set_color(COLORS["charcoal"])
            med.set_linewidth(1.2)
        ax.set_title(title, color=COLORS["charcoal"], weight="bold")
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("m/s^2")
    axes[1].set_ylabel("deg/s")
    fig.suptitle("Channel Distributions by Dataset Group", fontsize=14, weight="bold", color=COLORS["charcoal"])
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    save_figure(fig, "ch4_channel_boxplots")


def figure_raw_signal_examples() -> None:
    path = ROOT / "data" / "all_users_data_labeled.csv"
    cols = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w", "activity"]
    df = pd.read_csv(path, usecols=cols)
    examples = []
    for activity in ["hand_tapping", "sitting"]:
        sub = df[df["activity"] == activity].head(400).reset_index(drop=True)
        examples.append((activity, sub))
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 7.8), sharex=True)
    t = np.arange(400) / 50.0
    for row, (activity, sub) in enumerate(examples):
        axes[row, 0].plot(t[: len(sub)], sub[["Ax_w", "Ay_w", "Az_w"]].to_numpy(), lw=1.0)
        axes[row, 1].plot(t[: len(sub)], sub[["Gx_w", "Gy_w", "Gz_w"]].to_numpy(), lw=1.0)
        axes[row, 0].set_ylabel(activity.replace("_", " "))
        axes[row, 0].set_title("Accelerometer", weight="bold", color=COLORS["charcoal"])
        axes[row, 1].set_title("Gyroscope", weight="bold", color=COLORS["charcoal"])
        axes[row, 0].grid(alpha=0.25)
        axes[row, 1].grid(alpha=0.25)
    for ax in axes[-1]:
        ax.set_xlabel("Time (s)")
    axes[0, 0].legend(["Ax", "Ay", "Az"], loc="upper right", ncol=3, fontsize=8)
    axes[0, 1].legend(["Gx", "Gy", "Gz"], loc="upper right", ncol=3, fontsize=8)
    fig.suptitle("Raw Four-to-Eight Second Signal Examples", fontsize=14, weight="bold", color=COLORS["charcoal"])
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    save_figure(fig, "ch4_raw_signal_examples")


def figure_preprocessing_flow() -> None:
    fig, ax = plt.subplots(figsize=(13.5, 4.8))
    ax.axis("off")
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5)
    steps = [
        "Raw accel/gyro",
        "Validation",
        "Unit conversion",
        "Sync/resample\n50 Hz",
        "Norm state\nnone",
        "Windowing",
        "Model input",
    ]
    x = 0.3
    for i, step in enumerate(steps):
        draw_box(ax, x, 2.6, 1.55, 0.85, step, COLORS["light_blue"] if i in {0, 6} else "#FFFFFF")
        if i < len(steps) - 1:
            draw_arrow(ax, (x + 1.55, 3.02), (x + 1.95, 3.02))
        x += 1.95
    optional = [
        ("Gravity removal\noptional / disabled", 4.2),
        ("Calibration\noptional / disabled", 6.2),
    ]
    for text, ox in optional:
        rect = patches.Rectangle((ox, 1.0), 2.2, 0.8, linewidth=1.2, linestyle="--", edgecolor=COLORS["gray"], facecolor=COLORS["warm_white"])
        ax.add_patch(rect)
        ax.text(ox + 1.1, 1.4, text, ha="center", va="center", fontsize=9, color=COLORS["charcoal"])
    ax.text(7, 4.35, "Baseline Preprocessing Flow", ha="center", fontsize=14, weight="bold", color=COLORS["charcoal"])
    save_figure(fig, "ch4_preprocessing_flow")


def figure_windowing_diagram() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 4.8))
    ax.set_xlim(-10, 430)
    ax.set_ylim(0, 4)
    ax.set_yticks([])
    ax.set_xlabel("Samples at 50 Hz")
    ax.set_title("Sliding Window Configuration", weight="bold", color=COLORS["charcoal"])
    ax.hlines(0.8, 0, 400, color=COLORS["charcoal"], lw=1.5)
    for start, color, label in [(0, COLORS["light_blue"], "Window 1"), (100, COLORS["light_teal"], "Window 2"), (200, COLORS["light_gold"], "Window 3")]:
        rect = patches.Rectangle((start, 1.2 + start / 180), 200, 0.55, facecolor=color, edgecolor=COLORS["charcoal"], lw=1.2)
        ax.add_patch(rect)
        ax.text(start + 100, 1.48 + start / 180, label, ha="center", va="center", color=COLORS["charcoal"])
        ax.vlines([start, start + 200], 0.65, 3.0, colors=COLORS["gray"], linestyles="dashed", lw=0.8)
    ax.annotate("200 samples = 4 seconds", xy=(0, 3.55), xytext=(200, 3.55), arrowprops=dict(arrowstyle="<->", color=COLORS["deep_blue"]), ha="center", color=COLORS["deep_blue"])
    ax.annotate("step 100 samples = 2 seconds", xy=(0, 0.25), xytext=(100, 0.25), arrowprops=dict(arrowstyle="<->", color=COLORS["teal"]), ha="center", color=COLORS["teal"])
    ax.text(205, 0.25, "50% overlap", color=COLORS["charcoal"], fontsize=10)
    save_figure(fig, "ch4_windowing_diagram")


def figure_input_tensor() -> None:
    df = pd.read_csv(ROOT / "data" / "all_users_data_labeled.csv", usecols=["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"], nrows=200)
    arr = df.to_numpy(dtype=float)
    arr = (arr - np.nanmean(arr, axis=0)) / np.nanstd(arr, axis=0)
    fig, ax = plt.subplots(figsize=(6.5, 8.2))
    im = ax.imshow(arr, aspect="auto", cmap="viridis", interpolation="nearest")
    ax.set_title("Input Tensor Shape: (200, 6)", weight="bold", color=COLORS["charcoal"])
    ax.set_xlabel("Sensor channel")
    ax.set_ylabel("Time sample")
    ax.set_xticks(range(6))
    ax.set_xticklabels(CHANNELS)
    fig.colorbar(im, ax=ax, shrink=0.8, label="standardized value")
    save_figure(fig, "ch4_input_tensor_shape")


def figure_model_architecture() -> None:
    fig, ax = plt.subplots(figsize=(14, 4.7))
    ax.axis("off")
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 4)
    blocks = [
        ("Input\n(200, 6)", COLORS["light_blue"]),
        ("Conv1D\n16 filters", "#FFFFFF"),
        ("Conv1D\n32 filters", "#FFFFFF"),
        ("BiLSTM\n64", COLORS["light_teal"]),
        ("BiLSTM\n32", COLORS["light_teal"]),
        ("Dense\n32", COLORS["light_gold"]),
        ("Softmax\n11 classes", COLORS["light_gold"]),
    ]
    x = 0.35
    for i, (text, color) in enumerate(blocks):
        draw_box(ax, x, 1.8, 1.65, 0.95, text, color)
        if i < len(blocks) - 1:
            draw_arrow(ax, (x + 1.65, 2.28), (x + 2.05, 2.28))
        x += 2.05
    ax.text(7.3, 3.45, "Baseline 1D-CNN + BiLSTM Architecture", ha="center", fontsize=14, weight="bold", color=COLORS["charcoal"])
    ax.text(7.3, 0.75, "Local temporal feature extraction followed by bidirectional sequence modeling; architecture novelty is outside the thesis scope.", ha="center", fontsize=10, color=COLORS["charcoal"])
    save_figure(fig, "ch4_model_architecture")


def figure_training_workflow() -> None:
    fig, ax = plt.subplots(figsize=(14, 5.0))
    ax.axis("off")
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 5)
    blocks = [
        "Raw labeled\ndata",
        "Windowing",
        "Grouped fold\nsplit",
        "Scaler fit on\ntraining fold",
        "Train model",
        "Validate fold",
        "Save model\nand artifacts",
    ]
    x = 0.35
    for i, text in enumerate(blocks):
        color = COLORS["light_blue"] if i == 0 else COLORS["light_teal"] if i in {2, 3} else "#FFFFFF"
        draw_box(ax, x, 2.2, 1.65, 0.9, text, color)
        if i < len(blocks) - 1:
            draw_arrow(ax, (x + 1.65, 2.65), (x + 2.05, 2.65))
        x += 2.05
    ax.text(7.3, 4.05, "Training Workflow and Leakage Boundary", ha="center", fontsize=14, weight="bold", color=COLORS["charcoal"])
    ax.text(7.3, 1.25, "The scaler is fitted only on training users/folds before validation or test transformation.", ha="center", fontsize=10, color=COLORS["charcoal"])
    save_figure(fig, "ch4_training_workflow")


def make_all_figures(stats_df: pd.DataFrame, samples_by_group: dict[str, dict[str, np.ndarray]]) -> None:
    figure_dataset_source_overview()
    figure_mean_std(stats_df, "mean", "ch4_channel_mean_comparison", "Channel Mean")
    figure_mean_std(stats_df, "std", "ch4_channel_std_comparison", "Channel Standard Deviation")
    figure_boxplots(samples_by_group)
    figure_raw_signal_examples()
    figure_preprocessing_flow()
    figure_windowing_diagram()
    figure_input_tensor()
    figure_model_architecture()
    figure_training_workflow()


def write_figure_snippets() -> None:
    figures = [
        (
            "ch4_dataset_source_overview",
            "fig:ch4_dataset_source_overview",
            "Data-source overview for Chapter 4. The figure separates the labeled Garmin development corpus, production-style replay sessions, synthetic stress-test data, and planned self-recorded validation data by the kind of claim each source can support. This matters because only labeled data can support accuracy claims, while unlabeled replay and synthetic data support monitoring, stress-testing, and governance analysis under bounded assumptions.",
        ),
        (
            "ch4_channel_mean_comparison",
            "fig:ch4_channel_mean_comparison",
            "Channel-wise mean comparison across the main Chapter 4 data groups. Production replay accelerometer values are shown after internal unit harmonization to m\\,s$^{-2}$. The figure is descriptive evidence for train--serve consistency checks and should not be read as a supervised performance result.",
        ),
        (
            "ch4_channel_std_comparison",
            "fig:ch4_channel_std_comparison",
            "Channel-wise standard-deviation comparison across the main Chapter 4 data groups. Differences in dispersion indicate potential distribution shift or realism gaps, but the figure does not establish classification accuracy because most replay sessions are unlabeled and synthetic data are generated by construction.",
        ),
        (
            "ch4_channel_boxplots",
            "fig:ch4_channel_boxplots",
            "Distributional boxplots for accelerometer and gyroscope channels across the available data groups. The plot complements mean and standard-deviation summaries by showing range and spread. The claim boundary is descriptive: it supports discussion of shift and preprocessing sensitivity, not deployment robustness.",
        ),
        (
            "ch4_raw_signal_examples",
            "fig:ch4_raw_signal_examples",
            "Example labeled raw traces for a dynamic activity and a baseline activity. The figure shows why HAR is treated as multivariate temporal classification rather than static tabular classification. The examples are illustrative and are not used as standalone evidence of model accuracy.",
        ),
        (
            "ch4_preprocessing_flow",
            "fig:ch4_preprocessing_flow",
            "Baseline preprocessing flow from raw accelerometer and gyroscope recordings to model-ready windows. External scaling, gravity removal, and calibration are marked as optional but disabled in the defended baseline, which preserves train--serve consistency and keeps adaptation experiments outside the default claim.",
        ),
        (
            "ch4_windowing_diagram",
            "fig:ch4_windowing_diagram",
            "Sliding-window construction used by the baseline representation. At 50 Hz, 200 samples correspond to four seconds and the 100-sample step gives 50 percent overlap. This defines the temporal latency and context boundary for every model prediction.",
        ),
        (
            "ch4_input_tensor_shape",
            "fig:ch4_input_tensor_shape",
            "Heatmap-style view of the model input tensor with shape $(200,6)$. Rows correspond to time samples and columns to the six IMU channels. The figure documents the train--serve input contract rather than a learned feature representation.",
        ),
        (
            "ch4_model_architecture",
            "fig:ch4_model_architecture",
            "Baseline 1D-CNN + BiLSTM architecture used in the thesis. Convolutional layers capture local temporal motion patterns, BiLSTM layers model window-level sequence dependencies, and the softmax head outputs eleven activity probabilities. The thesis contribution is the governed MLOps lifecycle around this baseline, not architectural novelty.",
        ),
        (
            "ch4_training_workflow",
            "fig:ch4_training_workflow",
            "Training workflow for the baseline model. Windowing is followed by grouped splitting, scaler fitting on training data only, model training, validation, and artifact saving. This workflow matters because it defines the reproducibility and leakage boundary for downstream pipeline experiments.",
        ),
    ]
    lines: list[str] = []
    for filename, label, caption in figures:
        lines.extend(
            [
                r"\begin{figure}[htbp]",
                r"\centering",
                rf"\includegraphics[width=0.95\textwidth]{{figures/{filename}.pdf}}",
                rf"\caption{{{caption}}}",
                rf"\label{{{label}}}",
                r"\end{figure}",
                "",
            ]
        )
    (TEX_DIR / "ch4_generated_figures.tex").write_text("\n".join(lines), encoding="utf-8")


def citation_keys() -> set[str]:
    bib = (ROOT / "thesis" / "references.bib").read_text(encoding="utf-8")
    return set(re.findall(r"@\w+\{([^,]+),", bib))


def write_missing_citations() -> list[str]:
    required = {
        "lara2013survey": "Lara and Labrador wearable HAR survey",
        "bulling2014tutorial": "Bulling body-worn inertial HAR tutorial",
        "bao2004activity": "Bao and Intille activity recognition",
        "khan2021adamsense": "ADAM-sense anxiety-displaying activities",
        "dhekane2024transfer": "HAR transfer/deployment shift boundary",
        "akbari2020personalizing": "personalization and uncertainty in wearable HAR",
        "wang2024enhancing": "sensor displacement in wrist-worn HAR",
        "guo2017calibration": "calibration of modern neural networks",
        "gal2016dropout": "MC Dropout uncertainty",
        "kreuzberger2023mlops": "MLOps overview",
        "amershi2019mlops": "software engineering for ML",
        "paleyes2022challenges": "ML deployment challenges",
        "kuprieiev2023dvc": "DVC reproducibility",
        "zaharia2018mlflow": "MLflow lifecycle tracking",
        "ordonez2016deep": "CNN-LSTM HAR baseline",
        "kingma2014adam": "Adam optimizer",
    }
    keys = citation_keys()
    missing = [f"- `{key}`: {desc}" for key, desc in required.items() if key not in keys]
    if missing:
        text = "# Missing Chapter 4 Citations\n\n" + "\n".join(missing) + "\n"
    else:
        text = "# Missing Chapter 4 Citations\n\nNo missing citation keys were detected for the planned Chapter 4 insertions.\n"
    (REPORT_DIR / "ch4_missing_citations.md").write_text(text, encoding="utf-8")
    return missing


def get_stat(stats_df: pd.DataFrame, group: str, channel: str, metric: str) -> float:
    row = stats_df[(stats_df["dataset_group"] == group) & (stats_df["channel"] == channel)]
    if row.empty:
        return float("nan")
    return float(row.iloc[0][metric])


def write_generated_sections(
    stats_df: pd.DataFrame,
    rows_by_group: dict[str, int],
    window_summary: dict[str, Any],
) -> None:
    labeled_rows = rows_by_group.get("labeled_garmin", 0)
    production_rows = rows_by_group.get("production_replay", 0)
    codex_rows = rows_by_group.get("synthetic_codex", 0)
    other_rows = rows_by_group.get("synthetic_other", 0)
    ax_mean = get_stat(stats_df, "labeled_garmin", "Ax", "mean")
    az_mean = get_stat(stats_df, "labeled_garmin", "Az", "mean")
    replay_az_mean = get_stat(stats_df, "production_replay", "Az", "mean")
    seq_windows = window_summary["sequential_window_count"]
    user_windows = window_summary["user_isolated_window_count"]
    activity_cross = window_summary["sequential_activity_boundary_crossing_windows"]
    participant_cross = window_summary["sequential_participant_crossing_windows"]
    sections = rf"""
\section{{Exploratory Statistical Comparison Across Data Sources}}
\label{{sec:ch4_statistical_comparison}}

The data-source overview in Section~\ref{{sec:dataset}} defines what each dataset can be used for, but it does not by itself show whether the sources occupy similar numerical ranges. For wearable IMU systems, this descriptive check is necessary because small changes in units, sampling, channel ordering, or preprocessing can silently change the distribution seen by the model. The comparison in this section therefore reports channel-wise statistics for $A_x$, $A_y$, $A_z$, $G_x$, $G_y$, and $G_z$ across the available thesis data sources. It is used as evidence for train--serve consistency and dataset-shift discussion, not as proof of true classification accuracy.

The labeled Garmin development corpus contributes {labeled_rows:,} raw rows. The production-style replay group contributes {production_rows:,} fused 50~Hz rows across the discovered replay sessions after internal accelerometer unit harmonization from milliG to m\,s$^{{-2}}$. The two synthetic stress-test sources contribute {codex_rows:,} and {other_rows:,} rows, corresponding to the flattened representation of the generated window sets. The self-recorded final validation dataset was not found in the repository at generation time and is therefore treated as pending rather than assigned invented statistics.

\input{{tables/ch4_channel_statistics.tex}}

The channel summaries show the scale of the train--serve consistency problem. In the labeled Garmin corpus, the accelerometer means are not centered at zero in raw physical units, for example $A_x={ax_mean:.2f}$ and $A_z={az_mean:.2f}$ in m\,s$^{{-2}}$. This is expected because gravity remains present in the baseline signal. The production replay group shows a different but comparable physical scale after unit harmonization, including $A_z={replay_az_mean:.2f}$ in m\,s$^{{-2}}$. These differences are not automatically errors; they are descriptive evidence that inference-time preprocessing must preserve the same unit conversion, resampling, normalization state, and windowing assumptions used by the model.

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{{figures/ch4_channel_mean_comparison.pdf}}
\caption{{Channel-wise mean comparison across the main Chapter 4 data groups. The figure matters because channel means reveal offsets caused by unit handling, gravity, device orientation, or synthetic-data generation. It is descriptive train--serve evidence and not supervised accuracy evidence.}}
\label{{fig:ch4_channel_mean_comparison}}
\end{{figure}}

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{{figures/ch4_channel_std_comparison.pdf}}
\caption{{Channel-wise standard-deviation comparison across the main Chapter 4 data groups. The figure shows whether signal dispersion differs between the labeled reference, replay sessions, and synthetic sources. The claim boundary is limited to distributional comparison because replay labels are mostly unavailable and synthetic data are not real deployment evidence.}}
\label{{fig:ch4_channel_std_comparison}}
\end{{figure}}

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{{figures/ch4_channel_boxplots.pdf}}
\caption{{Boxplot comparison of accelerometer and gyroscope channel distributions across dataset groups. This complements the mean and standard-deviation tables by showing spread and outlier-resistant structure. It supports discussion of shift and realism but does not validate subject-independent deployment performance.}}
\label{{fig:ch4_channel_boxplots}}
\end{{figure}}

\input{{tables/ch4_dataset_shift_comparison.tex}}

The pairwise comparison table reports mean differences, standard-deviation ratios, median differences, IQR ratios, and, where SciPy is available, sample-based Wasserstein and Kolmogorov--Smirnov statistics. These values make the discussion of dataset shift auditable: they show which channels differ and by how much before later chapters interpret confidence, uncertainty, drift indicators, and trigger decisions. The comparison remains descriptive. A low shift statistic does not prove that the model is accurate, and a high shift statistic does not identify the causal failure mode by itself. It only indicates that the source distribution and target distribution differ in measurable ways that the MLOps pipeline must monitor.

The windowing check gives a second form of evidence. The full-corpus sequential baseline creates {seq_windows:,} windows, matching the reference count used in earlier experiments, and {activity_cross:,} of those windows cross an activity boundary while {participant_cross:,} cross a participant boundary. The current training implementation additionally supports user-isolated window construction, producing {user_windows:,} windows and eliminating participant-crossing windows by construction. This distinction is important for thesis safety: the 3,852-window view is useful as a full-corpus reference, while the user-isolated training path better reflects the leakage boundary of the current code.

\input{{tables/ch4_windowing_summary.tex}}

\section{{Data Characteristics and Challenges}}
\label{{sec:ch4_generated_challenges}}

Wearable IMU data are multivariate time series. Each time step contains six coupled sensor channels, and the class-discriminative information lies not only in the value of one channel but also in the temporal pattern across axes and across sensors. This is why the thesis treats preprocessing, windowing, and temporal modeling as part of a single input contract rather than as independent implementation details \cite{{lara2013survey,bulling2014tutorial,bao2004activity}}.

The first practical challenge is sensor noise. Wrist-worn accelerometer and gyroscope signals contain measurement noise, non-target motion, and device-specific bias. A short repeated activity such as hand tapping can therefore appear as a high-frequency pattern superimposed on orientation and gravity components, while a baseline posture can still contain small wrist adjustments. Noise does not only affect model accuracy; it affects monitoring because confidence, entropy, and drift signals can change when the raw signal distribution changes.

The second challenge is sampling irregularity. The thesis baseline assumes 50~Hz input, a 200-sample window, and a 100-sample step. If production data arrive with timestamp jitter or a different effective sampling rate, the same physical motion is represented by a different number of samples and the trained temporal filters no longer see the same time scale. Resampling to a fixed 50~Hz grid is therefore a train--serve consistency requirement rather than a cosmetic preprocessing step.

The third challenge is inter-subject and inter-session variability. Even when the same activity label is used, users differ in movement speed, arm length, dominant hand, and wearing tightness. Prior HAR work shows that such variation can reduce generalization across users and motivates careful personalization and uncertainty treatment \cite{{akbari2020personalizing,dhekane2024transfer}}. In this thesis, that risk is acknowledged by limiting claims to the tested corpus and by avoiding unsupported claims of subject-independent deployment robustness.

The fourth challenge is wrist placement. Wrist-worn sensors are practical but sensitive to displacement and orientation changes. A small shift of the watch on the wrist can alter the distribution of the three accelerometer axes and gyroscope axes even when the underlying activity is unchanged \cite{{wang2024enhancing}}. This is one reason why the thesis emphasizes monitoring and governed retraining rather than assuming that a fixed offline classifier remains reliable indefinitely.

\section{{Preprocessing Methodology}}
\label{{sec:ch4_generated_preprocessing}}

Preprocessing converts raw sensor files into the exact representation expected by the baseline model. The baseline path consists of input validation, unit standardization, synchronization and resampling, explicit normalization-state control, and windowing. Each step has a distinct role, and each can introduce risk if it differs between training and inference.

Input validation checks that required channels are present, timestamps are usable, missingness remains within the configured tolerance, and sensor values remain within plausible physical bounds. This step prevents structurally invalid sessions from entering inference and contaminating monitoring summaries.

Unit standardization handles the accelerometer scale mismatch between Garmin raw replay files and model-ready training values. Production accelerometer values are converted from milliG to m\,s$^{{-2}}$ before windowing, while gyroscope values are retained in degrees per second. The risk is straightforward: if this conversion is skipped or applied twice, the model receives a systematically shifted input distribution.

Synchronization and resampling align accelerometer and gyroscope streams to a fixed 50~Hz representation. This is necessary because the model input tensor has a fixed temporal meaning: 200 samples correspond to four seconds. Resampling changes raw timestamps into a regular grid, but it must be performed consistently so that training and inference windows represent the same physical duration.

The defended final production path disables external normalization and preserves raw physical IMU units after accelerometer unit conversion. Scaler artifacts remain available for training, leakage checks, and explicitly labeled A/B diagnostics, but they are not a final production inference dependency. Gravity removal and calibration exist as optional experimental controls, but they are disabled in the defended baseline because enabling those transformations by default would create a different input distribution and weaken the evidence chain.

\section{{Windowing and Input Representation}}
\label{{sec:ch4_generated_windowing}}

The classifier operates on fixed-length windows rather than on individual sensor rows. Sliding windows are used because activities such as rubbing, tapping, scratching, and biting-related hand movement are temporal patterns: a single time step cannot capture repetition, direction changes, or movement rhythm. With a 50~Hz sampling rate, the baseline window size of 200 samples represents four seconds of motion. The step size is 100 samples, giving 50\% overlap and one prediction every two seconds for a continuous stream.

Labels are assigned at the window level by majority vote when row-level activity labels are available. This rule is simple and reproducible, but it also exposes a boundary condition: windows that cross activity transitions may contain more than one true activity. The generated windowing summary therefore reports both activity-boundary crossing and participant-crossing windows. At inference time, labels are usually unavailable, so the same windowing rule produces unlabeled tensors for prediction and monitoring rather than supervised metrics.

The model input tensor has shape $(200,6)$, with columns $A_x$, $A_y$, $A_z$, $G_x$, $G_y$, and $G_z$. This shape is a contract between preprocessing and the model. Changing channel order, window size, overlap, or sampling rate would change the meaning of the input even if the array dimensions still look valid. The four-second window provides enough temporal context for repeated wrist motion, but it also creates a latency trade-off: a larger window gives the classifier more context while delaying each prediction.

\section{{Model Architecture and Rationale}}
\label{{sec:ch4_generated_model}}

The baseline classifier is a 1D-CNN + BiLSTM model. The 1D convolutional blocks learn local temporal patterns in the six-channel IMU sequence, such as short bursts, direction changes, and local oscillations. This is appropriate for wrist-worn HAR because many target activities contain repeated short movements rather than long semantic sequences \cite{{ordonez2016deep,wang2019sensorhar,zhang2022wearablehar}}.

The BiLSTM layers model dependencies across the full four-second window. Bidirectional recurrence lets the representation use both earlier and later samples inside the fixed window, which is useful because the model classifies a completed offline window rather than producing a strictly causal real-time prediction. The dense layer and softmax head then map the learned sequence representation to eleven activity probabilities.

This architecture is deliberately treated as a baseline. The thesis contribution is not a new neural architecture; it is the governed offline-first lifecycle around a stable HAR model. Keeping the baseline fixed makes later monitoring, trigger-policy, and retraining-governance experiments interpretable because changes in operational behavior can be traced to data and pipeline conditions rather than to uncontrolled architecture search.

\section{{Training Setup and Baseline Assumptions}}
\label{{sec:ch4_generated_training}}

The training configuration in \texttt{{src/train.py}} uses Adam with an initial learning rate of 0.001, sparse categorical cross-entropy, a maximum of 100 epochs, and a batch size of 64 \cite{{kingma2014adam}}. Early stopping monitors validation accuracy with patience 15 and restores the best weights. Learning-rate reduction monitors validation loss with patience 5, factor 0.5, and a minimum learning rate of $10^{{-6}}$. These callbacks provide practical regularization without claiming exhaustive hyperparameter optimization.

The current canonical training path creates windows per user and uses five-fold grouped cross-validation with user IDs as groups. This is stronger than ordinary window-level splitting because it prevents the same participant from appearing in both training and validation folds within a fold. The final-model path uses an explicit user holdout: users 1--4 for scaler fitting and model fitting, user 5 for validation, and user 6 for test evaluation when all six users are available. The scaler is fitted only on the training users or training folds before being applied to validation and test data.

The baseline assumptions are therefore fixed: 50~Hz sampling, 200-sample windows, 100-sample step, six sensor channels in the documented order, raw physical production input units with no external StandardScaler, and an eleven-class softmax output. The thesis does not claim that these are globally optimal hyperparameters. They are the controlled baseline assumptions that make the later MLOps experiments reproducible.

\section{{Baseline Scope and Adaptation Boundary}}
\label{{sec:ch4_generated_scope}}

The defended baseline includes the fixed preprocessing path, the windowing configuration, the 1D-CNN + BiLSTM classifier, raw physical production inference, and governed execution through the offline pipeline. Optional adaptation mechanisms are outside the default claim. Gravity removal, calibration, and external scaling are available for ablation, but they are disabled in the baseline. AdaBN, TENT, pseudo-labeling, and uncertainty-based adaptation are treated as experimental or future-work mechanisms rather than as default inference behavior \cite{{li2016adabn,wang2021tent,gal2016dropout,guo2017calibration}}.

This boundary protects the thesis argument. If adaptation were enabled automatically, later improvements or failures could not be attributed cleanly to the offline-first MLOps pipeline, monitoring logic, or retraining governance. Keeping adaptation conditional allows Chapter~6 and Chapter~7 to discuss trigger policies and candidate retraining without implying that unlabeled target data automatically produce a better model.

\section{{Reproducibility and Consistency Considerations}}
\label{{sec:ch4_generated_reproducibility}}

Reproducibility is enforced through configuration-driven execution, saved artifacts, and explicit provenance checks. The preprocessing configuration is stored in \texttt{{config/pipeline\_config.yaml}}, while model constants and paths are defined in \texttt{{src/config.py}}. Training hyperparameters and the model architecture are defined in \texttt{{src/train.py}}, and the model metadata are recorded in \texttt{{models/pretrained/model\_info.json}}.

Input-contract reproducibility is especially important. The final production path records that no external scaler is applied, while scaler files remain provenance-checked for training and A/B diagnostics. This prevents leakage from validation or test users into normalization parameters when scaler experiments are run. MLflow and DVC-related artifacts support experiment and data traceability where available, but the core thesis claim does not depend on an external service being online \cite{{kuprieiev2023dvc,zaharia2018mlflow,kreuzberger2023mlops,amershi2019mlops,paleyes2022challenges}}.

The operational consistency requirement is train--serve parity. The same channel order, unit convention, sampling rate, normalization state, and window shape must be reproduced during offline inference. If any of these assumptions changes, monitoring may still produce numbers, but those numbers would describe behavior under a different input contract. Chapter~5 therefore operationalizes the assumptions from this chapter as pipeline stages rather than leaving them as notebook-only logic.

\section{{Chapter Summary}}
\label{{sec:ch4_generated_summary}}

This chapter establishes the data and model foundation for the offline-first MLOps pipeline. It separates the labeled Garmin development corpus, production-style replay sessions, synthetic stress-test datasets, and pending self-recorded validation data by the claims each can support. The statistical comparison provides descriptive evidence about channel scale, spread, and dataset shift, while preserving the boundary that unlabeled replay sessions and synthetic data do not prove accuracy.

The preprocessing path validates inputs, harmonizes units, resamples to 50~Hz, preserves the explicit no-normalization runtime state, and constructs four-second overlapping windows. The resulting input tensor has shape $(200,6)$ and feeds a fixed 1D-CNN + BiLSTM baseline with an eleven-class softmax output. The baseline is intentionally stable: optional gravity removal, calibration, external scaling, and adaptation methods remain outside the default defended path.

The chapter therefore links the architecture of Chapter~3 to the implementation of Chapter~5. Chapter~5 can treat preprocessing, model input shape, artifacts, and train--serve consistency as defined contracts rather than as unresolved modeling choices.
"""
    (TEX_DIR / "ch4_generated_sections.tex").write_text(sections.strip() + "\n", encoding="utf-8")


def statistical_section_for_chapter(
    stats_df: pd.DataFrame,
    rows_by_group: dict[str, int],
    window_summary: dict[str, Any],
) -> str:
    labeled_rows = rows_by_group.get("labeled_garmin", 0)
    production_rows = rows_by_group.get("production_replay", 0)
    codex_rows = rows_by_group.get("synthetic_codex", 0)
    other_rows = rows_by_group.get("synthetic_other", 0)
    seq_windows = window_summary["sequential_window_count"]
    user_windows = window_summary["user_isolated_window_count"]
    activity_cross = window_summary["sequential_activity_boundary_crossing_windows"]
    participant_cross = window_summary["sequential_participant_crossing_windows"]
    return rf"""
\section{{Exploratory Statistical Comparison Across Data Sources}}
\label{{sec:ch4_statistical_comparison}}

The descriptive dataset inventory in Section~\ref{{sec:dataset}} establishes what each source is for. A second question is whether the sources occupy comparable numerical ranges after the unit assumptions of the pipeline are applied. This matters in wearable HAR because channel units, sampling rate, axis order, gravity handling, and normalization can silently alter the input distribution seen by the model. The comparison in this section is therefore evidence for train--serve consistency and dataset-shift interpretation; it is not evidence of true classification accuracy.

The generated inventory and statistics were produced from the repository artifacts listed in \path{{reports/chapter4/ch4_data_inventory.csv}}. The labeled Garmin development corpus contributes {labeled_rows:,} rows. The production-style replay group contributes {production_rows:,} fused 50~Hz rows across the discovered replay sessions, with accelerometer values internally harmonized from milliG to m\,s$^{{-2}}$ for comparison. The synthetic Codex and synthetic Other groups contribute {codex_rows:,} and {other_rows:,} rows, respectively. No self-recorded final validation dataset was found at generation time, so that source remains pending and is not assigned invented statistics.

\input{{tables/ch4_channel_statistics.tex}}

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{{figures/ch4_channel_mean_comparison.pdf}}
\caption{{Channel-wise mean comparison across the main Chapter 4 data groups. The figure matters because channel means reveal offsets caused by unit handling, gravity, device orientation, or synthetic-data generation. It is descriptive train--serve evidence and not supervised accuracy evidence.}}
\label{{fig:ch4_channel_mean_comparison}}
\end{{figure}}

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{{figures/ch4_channel_std_comparison.pdf}}
\caption{{Channel-wise standard-deviation comparison across the main Chapter 4 data groups. The figure shows whether signal dispersion differs between the labeled reference, replay sessions, and synthetic sources. The claim boundary is limited to distributional comparison because replay labels are mostly unavailable and synthetic data are not real deployment evidence.}}
\label{{fig:ch4_channel_std_comparison}}
\end{{figure}}

\begin{{figure}}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{{figures/ch4_channel_boxplots.pdf}}
\caption{{Boxplot comparison of accelerometer and gyroscope channel distributions across dataset groups. This complements the mean and standard-deviation tables by showing spread and outlier-resistant structure. It supports discussion of shift and realism but does not validate subject-independent deployment performance.}}
\label{{fig:ch4_channel_boxplots}}
\end{{figure}}

\input{{tables/ch4_dataset_shift_comparison.tex}}

The pairwise shift metrics make the comparison auditable. Mean differences, standard-deviation ratios, median differences, IQR ratios, and optional two-sample statistics identify which channels diverge between the labeled reference and the replay or synthetic sources. These values should be interpreted conservatively. A small difference does not prove that a classifier is accurate, and a large difference does not by itself identify the cause of failure. The table only shows that distributional differences exist and that later confidence, uncertainty, drift, and trigger results should be interpreted relative to these differences.

Windowing provides a second evidence check. The full-corpus sequential view produces {seq_windows:,} windows, matching the historical baseline reference. In that view, {activity_cross:,} windows cross activity boundaries and {participant_cross:,} windows cross participant boundaries. The current training implementation also supports user-isolated windowing, producing {user_windows:,} windows and eliminating participant-crossing windows by construction. This distinction is thesis-relevant: the 3,852-window view is useful for full-corpus reference comparisons, while the user-isolated view reflects the leakage boundary of the current training code.

\input{{tables/ch4_windowing_summary.tex}}
"""


def replace_table_by_caption(text: str, caption_fragment: str, replacement: str) -> str:
    pattern = re.compile(
        r"\\begin\{table\}\[htbp\](?:(?!\\end\{table\}).)*"
        + re.escape(caption_fragment)
        + r"(?:(?!\\end\{table\}).)*\\end\{table\}",
        re.DOTALL,
    )
    return pattern.sub(lambda _match: replacement, text, count=1)


def update_chapter4(
    stats_df: pd.DataFrame,
    rows_by_group: dict[str, int],
    window_summary: dict[str, Any],
) -> None:
    if not CH4_BACKUP.exists():
        shutil.copy2(CH4_PATH, CH4_BACKUP)
    text = CH4_PATH.read_text(encoding="utf-8")
    section = statistical_section_for_chapter(stats_df, rows_by_group, window_summary)
    if r"\section{Exploratory Statistical Comparison Across Data Sources}" not in text:
        marker = r"\section{Data Characteristics and Challenges}"
        text = text.replace(marker, section + "\n" + marker, 1)

    text = text.replace(
        r"\includegraphics[width=0.92\textwidth]{fig_dataset_input_overview.png}",
        r"\includegraphics[width=0.92\textwidth]{figures/ch4_dataset_source_overview.pdf}",
    )
    text = text.replace(
        r"\includegraphics[width=0.94\textwidth]{fig_raw_signal_examples.png}",
        r"\includegraphics[width=0.94\textwidth]{figures/ch4_raw_signal_examples.pdf}",
    )
    text = text.replace(
        r"\includegraphics[width=0.94\textwidth]{fig_06_data_pipeline.png}",
        r"\includegraphics[width=0.94\textwidth]{figures/ch4_preprocessing_flow.pdf}",
    )
    text = text.replace(
        r"\includegraphics[width=0.92\textwidth]{fig_windowing_diagram.png}",
        r"\includegraphics[width=0.92\textwidth]{figures/ch4_windowing_diagram.pdf}",
    )
    text = text.replace(
        r"\includegraphics[width=0.82\textwidth]{fig_input_tensor_heatmap.png}",
        r"\includegraphics[width=0.82\textwidth]{figures/ch4_input_tensor_shape.pdf}",
    )
    text = text.replace(
        r"\includegraphics[width=0.92\textwidth]{fig_model_architecture.png}",
        r"\includegraphics[width=0.92\textwidth]{figures/ch4_model_architecture.pdf}",
    )
    text = text.replace(
        r"\includegraphics[width=0.92\textwidth]{fig_training_workflow.png}",
        r"\includegraphics[width=0.92\textwidth]{figures/ch4_training_workflow.pdf}",
    )

    text = replace_table_by_caption(
        text,
        "Window-level class distribution of the labeled development corpus.",
        r"\input{tables/ch4_class_distribution.tex}",
    )

    text = text.replace(
        "However, participant identity is still re-used across the window-level folds described later in this chapter.",
        "The current training code creates user-isolated windows and grouped validation folds, while the full-corpus sequential window count is retained as a reproducible reference for pipeline-level comparisons.",
    )
    text = text.replace(
        "Five-fold stratified cross-validation is used for generalization estimation.",
        "Five-fold grouped cross-validation is used for internal generalization estimation.",
    )
    text = text.replace(
        "five-fold stratified cross-validation over the 3,852 windowed samples derived from the fused labeled corpus",
        "five-fold grouped cross-validation with participant IDs as groups over the user-isolated windows derived from the fused labeled corpus",
    )
    old_para = (
        "Stratification preserves the class distribution across all five folds, which remains useful even though the window-level class composition is relatively even. "
        "In the canonical training path implemented in \\texttt{src/train.py}, the held-out fold itself is passed to the training loop as \\texttt{validation\\_data}. "
        "It therefore serves both as the callback-monitoring signal and as the fold-level evaluation set; there is no additional nested 10\\% validation subset in the baseline training path. "
        "A fixed random seed of 42 is used to ensure reproducible fold assignments across runs."
    )
    new_para = (
        "The canonical training path implemented in \\texttt{src/train.py} uses \\texttt{GroupKFold}, with participant IDs as the grouping variable. "
        "The held-out group fold is passed to the training loop as \\texttt{validation\\_data}; it therefore serves both as the callback-monitoring signal and as the fold-level evaluation set. "
        "Within each fold, the scaler is fitted only on the training fold before being applied to the held-out fold. "
        "The configuration retains a fixed seed of 42 for reproducible operations where stochastic splitting or training behavior is used."
    )
    text = text.replace(old_para, new_para)
    text = text.replace(
        "The split is applied after window construction at the window level, so windows from the same participant can appear in both the training folds and the held-out fold.",
        "The split is applied after user-isolated window construction, and grouped folds prevent the same participant from appearing in both the training and held-out fold in the current canonical code.",
    )
    text = text.replace(
        "this variability is an inherent property of the dataset that motivates the use of stratified cross-validation during training and careful normalization during preprocessing.",
        "this variability is an inherent property of the dataset that motivates grouped validation, train-only normalization, and careful preprocessing consistency.",
    )
    text = text.replace(
        "The choice of stratified cross-validation follows established evaluation practice for wearable HAR, as discussed in Dhekane and Plötz~\\cite{dhekane2024transfer}, where the authors note that cross-validation with appropriate stratification is necessary to produce reliable generalization estimates from small-to-medium wearable datasets. At the same time, the estimate is intentionally narrower than a leave-one-subject-out or session-wise protocol. The split is applied after user-isolated window construction, and grouped folds prevent the same participant from appearing in both the training and held-out fold in the current canonical code. The resulting scores are therefore best interpreted as an internal estimate of performance under matched collection conditions, not as proof of subject-independent deployment behavior.",
        "The grouped validation choice follows the broader HAR evaluation concern discussed by Dhekane and Plötz~\\cite{dhekane2024transfer}: estimates from small wearable datasets are sensitive to how subjects and sessions are split. The current implementation uses participant IDs as groups, so the same participant is not present in both the training and held-out fold for a given fold. At the same time, the evidence base remains small and collection-specific, so the resulting scores are best interpreted as an internal estimate under matched collection conditions, not as proof of subject-independent deployment behavior.",
    )
    text = text.replace(
        "Cross-validation    & 5-fold stratified (window-level) & Random seed: 42; not participant-wise",
        "Cross-validation    & 5-fold grouped by participant & \\texttt{GroupKFold}; user IDs define held-out groups",
    )
    text = text.replace(
        "Offline model development & Fused labeled CSV, then windowed and split 5-fold & Window-level folds & Yes & Model fitting, fold metrics, scaler fitting, and retained-model selection",
        "Offline model development & Fused labeled CSV, then user-isolated windowing and grouped splitting & Grouped user folds & Yes & Model fitting, fold metrics, scaler fitting, and retained-model selection",
    )
    text = text.replace(
        "5-fold stratified CV training & In scope & Internal window-level estimate under matched collection conditions",
        "5-fold grouped CV training & In scope & Internal grouped-user estimate under matched collection conditions",
    )
    text = text.replace(
        "Windowed corpus size & 3,852 windows   & Generated from fused labeled CSV",
        "Windowed corpus size & 3,852 reference / 3,845 training windows & Sequential reference vs. user-isolated training view",
    )
    text = text.replace(
        "\\texttt{src/train.py}, 5-fold \\texttt{StratifiedKFold} on windows with seed 42",
        "\\texttt{src/train.py}, 5-fold \\texttt{GroupKFold} with participant IDs as groups",
    )
    text = text.replace(
        "five-fold stratified cross-validation at the window level",
        "five-fold grouped cross-validation with participant IDs as groups",
    )
    text = text.replace(
        "the canonical cross-validation is window-level rather than participant-wise",
        "the canonical cross-validation is grouped by participant but still limited to six participants",
    )
    text = text.replace(
        "Total: 3,852 windows from the baseline 200-sample / 50\\% overlap configuration.",
        "Total: 3,852 windows in the sequential full-corpus reference view; see Table~\\ref{tab:ch4_windowing_summary} for the user-isolated training view.",
    )

    CH4_PATH.write_text(text, encoding="utf-8")


def write_summary(
    inventory: pd.DataFrame,
    stats_df: pd.DataFrame,
    shift_df: pd.DataFrame,
    class_df: pd.DataFrame,
    window_summary: dict[str, Any],
    missing_citations: list[str],
    excel_status: dict[str, str],
) -> None:
    production_files = get_dataset_files()["production_replay"]
    figures = sorted(p.name for p in FIGURE_DIR.glob("ch4_*.png"))
    tables = [
        "reports/chapter4/ch4_data_inventory.csv",
        "reports/chapter4/ch4_channel_statistics.csv",
        "reports/chapter4/ch4_channel_statistics.xlsx",
        "reports/chapter4/ch4_dataset_shift_comparison.csv",
        "reports/chapter4/ch4_dataset_shift_comparison.xlsx",
        "reports/chapter4/ch4_class_distribution.csv",
        "reports/chapter4/ch4_windowing_summary.csv",
        "thesis/tables/ch4_channel_statistics.tex",
        "thesis/tables/ch4_dataset_shift_comparison.tex",
        "thesis/tables/ch4_class_distribution.tex",
        "thesis/tables/ch4_windowing_summary.tex",
    ]
    text = [
        "# Chapter 4 Generation Summary",
        "",
        "## Files Scanned",
        f"- Inventory entries: {len(inventory):,}",
        f"- Production fused replay files used for channel statistics: {len(production_files)}",
        f"- Chapter 7/report-result artifacts found: {int((inventory['dataset_group'] == 'chapter7_results_or_reports').sum())}",
        "- Config/code sources checked: `config/pipeline_config.yaml`, `src/config.py`, `src/train.py`, `models/pretrained/model_info.json`, `thesis/references.bib`.",
        "",
        "## Datasets Found",
        f"- Labeled Garmin development: {int(stats_df[stats_df.dataset_group == 'labeled_garmin']['count'].max()):,} channel values per complete channel.",
        f"- Production replay fused rows: {window_summary.get('production_rows', 'see statistics file')}",
        f"- Synthetic Codex rows: {int(stats_df[stats_df.dataset_group == 'synthetic_codex']['count'].max()):,} channel values per complete channel.",
        f"- Synthetic Other rows: {int(stats_df[stats_df.dataset_group == 'synthetic_other']['count'].max()):,} channel values per complete channel.",
        "",
        "## Datasets Missing",
        "- Self-recorded final validation dataset: not found. It remains TODO/pending and no statistics were invented.",
        "",
        "## Tables Generated",
        *[f"- `{t}`" for t in tables],
        "",
        "## Figures Generated",
        *[f"- `thesis/figures/{f}` and `thesis/figures/{f.replace('.png', '.pdf')}`" for f in figures],
        "",
        "## LaTeX Files Updated",
        f"- Chapter updated: `{rel(CH4_PATH)}`",
        f"- Backup created: `{rel(CH4_BACKUP)}`",
        "- Snippets: `thesis/tex/ch4_generated_figures.tex`, `thesis/tex/ch4_generated_sections.tex`",
        "",
        "## Citations Found",
        "- Required keys for Chapter 4 insertions were found in `thesis/references.bib` unless listed below.",
        "",
        "## Citations Missing",
    ]
    if missing_citations:
        text.extend(missing_citations)
    else:
        text.append("- None.")
    text.extend(
        [
            "",
            "## Warnings and Claim Boundaries",
            "- Production replay sessions are mostly unlabeled; use them for monitoring, trigger, preprocessing-sensitivity, and governance analysis, not direct accuracy claims.",
            "- Synthetic datasets are useful stress tests, but they are not proof of real deployment performance.",
            "- The self-recorded validation dataset is pending and must not be described with invented counts.",
            "- Production replay accelerometer statistics were internally unit-harmonized to m/s^2 for comparison. Raw files were not modified.",
            "- Quantiles and two-sample statistics use deterministic bounded samples for large groups; counts, means, standard deviations, minima, and maxima are computed over all processed rows.",
            "- Current `src/train.py` uses grouped user folds and train-only scaler fitting, so ordinary window-level stratified CV should not be claimed as the current canonical implementation.",
            "",
            "## Excel Export Status",
            *[f"- {k}: {v}" for k, v in excel_status.items()],
            "",
            "## Unresolved TODOs",
            "- Collect or place the self-recorded final validation dataset if it should be included in Chapter 4 evidence.",
            "- Re-run this script after new data are added so inventory, statistics, figures, and tables remain synchronized.",
        ]
    )
    (REPORT_DIR / "ch4_generation_summary.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    inventory = build_inventory()
    inventory.to_csv(REPORT_DIR / "ch4_data_inventory.csv", index=False)

    stats_df, samples_by_group, rows_by_group = compute_channel_statistics()
    stats_df.to_csv(REPORT_DIR / "ch4_channel_statistics.csv", index=False)
    excel_status = {
        "ch4_channel_statistics.xlsx": write_excel(
            stats_df, REPORT_DIR / "ch4_channel_statistics.xlsx"
        )
    }

    shift_df = compute_comparison_metrics(stats_df, samples_by_group)
    shift_df.to_csv(REPORT_DIR / "ch4_dataset_shift_comparison.csv", index=False)
    excel_status["ch4_dataset_shift_comparison.xlsx"] = write_excel(
        shift_df, REPORT_DIR / "ch4_dataset_shift_comparison.xlsx"
    )

    class_df, window_df, window_summary = compute_class_and_windowing()
    window_summary["production_rows"] = rows_by_group.get("production_replay", 0)
    class_df.to_csv(REPORT_DIR / "ch4_class_distribution.csv", index=False)
    window_df.to_csv(REPORT_DIR / "ch4_windowing_summary.csv", index=False)

    write_latex_channel_table(stats_df)
    write_latex_shift_table(shift_df)
    write_latex_class_table(class_df)
    write_latex_windowing_table(window_summary)
    make_all_figures(stats_df, samples_by_group)
    write_figure_snippets()
    missing_citations = write_missing_citations()
    write_generated_sections(stats_df, rows_by_group, window_summary)
    update_chapter4(stats_df, rows_by_group, window_summary)
    write_summary(
        inventory,
        stats_df,
        shift_df,
        class_df,
        window_summary,
        missing_citations,
        excel_status,
    )

    print("Chapter 4 assets generated.")
    print(f"Inventory rows: {len(inventory)}")
    print(f"Channel statistic rows: {len(stats_df)}")
    print(f"Shift comparison rows: {len(shift_df)}")
    print(f"Sequential windows: {window_summary['sequential_window_count']}")
    print(f"User-isolated windows: {window_summary['user_isolated_window_count']}")


if __name__ == "__main__":
    main()

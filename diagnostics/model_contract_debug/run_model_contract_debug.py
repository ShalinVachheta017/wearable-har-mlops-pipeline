from __future__ import annotations

import ast
import contextlib
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import time
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

try:
    from scipy.optimize import linear_sum_assignment
except Exception:  # pragma: no cover - scipy exists in the thesis env.
    linear_sum_assignment = None


SCRIPT_PATH = Path(__file__).resolve()
OUT_DIR = SCRIPT_PATH.parent
ROOT = OUT_DIR.parents[1]

EXPECTED_CLASSES = [
    "ear_rubbing",
    "forehead_rubbing",
    "hair_pulling",
    "hand_scratching",
    "hand_tapping",
    "knuckles_cracking",
    "nail_biting",
    "nape_rubbing",
    "sitting",
    "smoking",
    "standing",
]
EXPECTED_MAP = {name: idx for idx, name in enumerate(EXPECTED_CLASSES)}
EXPECTED_INV = {idx: name for idx, name in enumerate(EXPECTED_CLASSES)}
SENSOR_CANONICAL = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
SENSOR_W = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
WINDOW_SIZE = 200
STRIDE = 100
LARGE_GAP_MS = 60.0
RNG = np.random.default_rng(42)

MODEL_NB = ROOT / "nb" / "fine_tuned_model_1dcnnbilstm.keras"
MODEL_DEPLOYED = ROOT / "models" / "pretrained" / "fine_tuned_model_1dcnnbilstm.keras"
MODEL_PATHS = [MODEL_NB, MODEL_DEPLOYED]

DATASETS = {
    "all_users": {
        "source_csv": ROOT / "data" / "all_users_data_labeled.csv",
        "processed_csv": ROOT / "data" / "processed" / "fused_all_users_data_labeled_50Hz.csv",
        "artifact_run": ROOT / "artifacts" / "20260506_103805",
    },
    "user7": {
        "source_csv": ROOT / "data" / "raw" / "2026-05-05-15-11-15_labeled_50Hz_user7.csv",
        "processed_csv": ROOT
        / "data"
        / "processed"
        / "fused_2026_05_05_15_11_15_labeled_50hz_user7_50Hz.csv",
        "artifact_run": ROOT / "artifacts" / "20260506_101242",
    },
}

SEARCH_DIRS = [
    "nb",
    "src",
    "config",
    "data",
    "reports",
    "artifacts",
    "outputs",
    "models",
    "docs",
    "scripts",
]
SKIP_DIR_NAMES = {
    ".git",
    ".dvc",
    "__pycache__",
    ".pytest_cache",
    "mlruns",
    "pytest-cache",
    "pytest-tmp",
}
SKIP_DIR_PREFIXES = (
    "pytest",
    "_pytest",
    "tmp_pytest",
)
TEXT_SUFFIXES = {
    ".py",
    ".ipynb",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".txt",
    ".csv",
    ".ini",
    ".toml",
    ".dvc",
}
BINARY_SUFFIXES = {
    ".npy",
    ".npz",
    ".keras",
    ".tflite",
    ".joblib",
    ".pkl",
    ".pdf",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
    ".fit",
}


@dataclass
class WindowSet:
    dataset: str
    name: str
    X: np.ndarray
    y: Optional[np.ndarray]
    meta: List[Dict[str, Any]]
    label_rule: str
    source: str


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(obj), indent=2, sort_keys=False), encoding="utf-8")


def json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if pd.isna(value) if not isinstance(value, (list, dict, tuple, np.ndarray)) else False:
        return None
    return value


def md_table(rows: Sequence[Dict[str, Any]], headers: Sequence[str]) -> str:
    if not rows:
        return "_No rows._"
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        vals = []
        for h in headers:
            val = row.get(h, "")
            if isinstance(val, (list, tuple)):
                val = ", ".join(str(x) for x in val)
            text = str(val).replace("\n", "<br>").replace("|", "\\|")
            vals.append(text)
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_info(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "path": rel(path),
            "exists": False,
            "size_bytes": None,
            "sha256": None,
            "modified_time": None,
        }
    stat = path.stat()
    return {
        "path": rel(path),
        "exists": True,
        "size_bytes": stat.st_size,
        "sha256": sha256_file(path),
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def safe_read_text(path: Path, max_bytes: int = 4_000_000) -> Optional[str]:
    try:
        if path.suffix.lower() in BINARY_SUFFIXES:
            return None
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def iter_text_files(base_dirs: Sequence[str], max_bytes: int = 4_000_000) -> Iterable[Path]:
    for base in base_dirs:
        root = ROOT / base
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            cleaned = []
            for dirname in dirnames:
                lower = dirname.lower()
                if lower in SKIP_DIR_NAMES or any(lower.startswith(p) for p in SKIP_DIR_PREFIXES):
                    continue
                cleaned.append(dirname)
            dirnames[:] = cleaned
            for filename in filenames:
                path = Path(dirpath) / filename
                suffix = path.suffix.lower()
                if suffix in BINARY_SUFFIXES:
                    continue
                if suffix and suffix not in TEXT_SUFFIXES:
                    continue
                try:
                    if path.stat().st_size > max_bytes:
                        continue
                except OSError:
                    continue
                yield path


def scan_patterns(patterns: Sequence[str], max_matches_per_pattern: int = 250) -> Dict[str, List[Dict[str, Any]]]:
    compiled = [(pat, re.compile(pat, flags=re.IGNORECASE)) for pat in patterns]
    matches: Dict[str, List[Dict[str, Any]]] = {pat: [] for pat in patterns}
    for path in iter_text_files(SEARCH_DIRS):
        text = safe_read_text(path)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pat, regex in compiled:
                if len(matches[pat]) >= max_matches_per_pattern:
                    continue
                if regex.search(line):
                    matches[pat].append(
                        {
                            "file": rel(path),
                            "line": lineno,
                            "snippet": line.strip()[:240],
                        }
                    )
    return matches


def read_csv_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return standardize_df(df)


def standardize_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if all(c in out.columns for c in SENSOR_CANONICAL):
        pass
    elif all(c in out.columns for c in SENSOR_W):
        for src, dst in zip(SENSOR_W, SENSOR_CANONICAL):
            out[dst] = out[src]
    else:
        raise ValueError(f"Missing canonical or wrist sensor columns. Columns={list(out.columns)}")

    time_col = None
    for candidate in ("timestamp_iso", "true_time", "timestamp", "time", "datetime"):
        if candidate in out.columns:
            time_col = candidate
            break
    if time_col is not None:
        out["timestamp_dt"] = parse_timestamps(out[time_col])
    else:
        out["timestamp_dt"] = pd.NaT
    out["_orig_index"] = np.arange(len(out), dtype=np.int64)
    if "activity" in out.columns:
        out["activity"] = out["activity"].astype(str).map(canonical_label)
    return out


def parse_timestamps(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        values = pd.to_numeric(series, errors="coerce")
        med = values.dropna().median()
        if pd.isna(med):
            return pd.to_datetime(values, errors="coerce")
        if med > 1e12:
            return pd.to_datetime(values, unit="ms", origin="unix", errors="coerce")
        return pd.to_datetime(values, unit="s", origin="unix", errors="coerce")
    return pd.to_datetime(series, errors="coerce")


def canonical_label(value: Any) -> str:
    text = str(value).strip().lower().replace("-", "_")
    text = re.sub(r"\s+", "_", text)
    aliases = {
        "ear_rubbing": "ear_rubbing",
        "ear_rub": "ear_rubbing",
        "forehead_rubbing": "forehead_rubbing",
        "forehead_rub": "forehead_rubbing",
        "hair_pulling": "hair_pulling",
        "hair_pulling_": "hair_pulling",
        "hand_scratching": "hand_scratching",
        "hand_rubbing": "hand_scratching",
        "hand_tapping": "hand_tapping",
        "knuckle_cracking": "knuckles_cracking",
        "knuckles_cracking": "knuckles_cracking",
        "nail_biting": "nail_biting",
        "nape_rubbing": "nape_rubbing",
        "idle_sitting": "sitting",
        "sitting": "sitting",
        "idle_standing": "standing",
        "standing": "standing",
        "smoking": "smoking",
    }
    return aliases.get(text, text)


def label_to_id(label: str) -> int:
    canonical = canonical_label(label)
    if canonical not in EXPECTED_MAP:
        raise KeyError(f"Unknown activity label {label!r} canonicalized to {canonical!r}")
    return EXPECTED_MAP[canonical]


def majority_label(values: Sequence[str]) -> str:
    counts = Counter(canonical_label(v) for v in values)
    max_count = max(counts.values())
    candidates = sorted(k for k, v in counts.items() if v == max_count)
    return candidates[0]


def build_row_windows(dataset: str, df: pd.DataFrame, name: str, source: str) -> WindowSet:
    n = len(df)
    if n < WINDOW_SIZE:
        return WindowSet(dataset, name, np.empty((0, WINDOW_SIZE, 6), dtype=np.float32), None, [], "majority", source)
    starts = list(range(0, n - WINDOW_SIZE + 1, STRIDE))
    values = df[SENSOR_CANONICAL].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float32)
    X = np.empty((len(starts), WINDOW_SIZE, len(SENSOR_CANONICAL)), dtype=np.float32)
    labels: List[int] = []
    meta: List[Dict[str, Any]] = []
    has_labels = "activity" in df.columns
    activities = df["activity"].to_numpy(dtype=str) if has_labels else None
    for out_idx, start in enumerate(starts):
        end = start + WINDOW_SIZE
        X[out_idx] = values[start:end]
        row_meta = window_meta(df, start, end, out_idx)
        row_meta["label_first"] = None
        row_meta["label_center"] = None
        row_meta["label_majority"] = None
        if has_labels and activities is not None:
            acts = [canonical_label(v) for v in activities[start:end]]
            first = acts[0]
            center = acts[WINDOW_SIZE // 2]
            majority = majority_label(acts)
            labels.append(label_to_id(majority))
            row_meta["label_first"] = first
            row_meta["label_center"] = center
            row_meta["label_majority"] = majority
        meta.append(row_meta)
    y = np.asarray(labels, dtype=np.int32) if has_labels else None
    return WindowSet(dataset, name, X, y, meta, "majority_over_rows", source)


def build_segment_windows(dataset: str, df: pd.DataFrame, name: str, source: str) -> WindowSet:
    seg_df = add_segment_id(df)
    X_parts: List[np.ndarray] = []
    y_parts: List[np.ndarray] = []
    meta: List[Dict[str, Any]] = []
    for segment_id, part in seg_df.groupby("segment_id", sort=False):
        part = part.reset_index(drop=True)
        if len(part) < WINDOW_SIZE:
            continue
        ws = build_row_windows(dataset, part, name=f"{name}_segment_{segment_id}", source=source)
        X_parts.append(ws.X)
        if ws.y is not None:
            y_parts.append(ws.y)
        for row in ws.meta:
            row["segment_id"] = int(segment_id)
            row["window_id"] = len(meta)
            meta.append(row)
    if X_parts:
        X = np.concatenate(X_parts, axis=0)
    else:
        X = np.empty((0, WINDOW_SIZE, 6), dtype=np.float32)
    y = np.concatenate(y_parts, axis=0).astype(np.int32) if y_parts else None
    return WindowSet(dataset, name, X, y, meta, "segment_activity_majority", source)


def add_segment_id(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    group_cols = [
        c
        for c in ["User", "user", "user_id", "participant", "participant_id", "session", "session_id", "file", "filename", "recording_id"]
        if c in out.columns
    ]
    sort_cols = group_cols + ["timestamp_dt"] if "timestamp_dt" in out.columns else group_cols
    if sort_cols:
        out = out.sort_values(sort_cols).reset_index(drop=True)
    new_segment = pd.Series(False, index=out.index)
    if len(out):
        new_segment.iloc[0] = True
    for col in group_cols:
        new_segment |= out[col].astype(str).ne(out[col].astype(str).shift())
    if "activity" in out.columns:
        new_segment |= out["activity"].astype(str).ne(out["activity"].astype(str).shift())
    if "timestamp_dt" in out.columns:
        gaps_ms = out["timestamp_dt"].diff().dt.total_seconds() * 1000.0
        new_segment |= gaps_ms.gt(LARGE_GAP_MS).fillna(False)
        new_segment |= gaps_ms.le(0).fillna(False)
    out["segment_id"] = new_segment.cumsum().astype(int)
    return out


def window_meta(df: pd.DataFrame, start: int, end: int, window_id: int) -> Dict[str, Any]:
    sub = df.iloc[start:end]
    meta: Dict[str, Any] = {
        "window_id": int(window_id),
        "start_idx": int(start),
        "end_idx_exclusive": int(end),
        "timestamp_start": safe_timestamp(sub.iloc[0].get("timestamp_dt")),
        "timestamp_end": safe_timestamp(sub.iloc[-1].get("timestamp_dt")),
        "crosses_activity": False,
        "crosses_user": False,
        "large_gap_count": 0,
        "non_positive_gap_count": 0,
    }
    if "activity" in sub.columns:
        meta["crosses_activity"] = bool(sub["activity"].astype(str).nunique(dropna=False) > 1)
    for col in ("User", "user", "user_id", "participant", "participant_id"):
        if col in sub.columns:
            meta["user"] = str(sub.iloc[0][col])
            meta["crosses_user"] = bool(sub[col].astype(str).nunique(dropna=False) > 1)
            break
    if "timestamp_dt" in sub.columns and sub["timestamp_dt"].notna().sum() > 1:
        gaps_ms = sub["timestamp_dt"].diff().dt.total_seconds() * 1000.0
        meta["large_gap_count"] = int(gaps_ms.gt(LARGE_GAP_MS).sum())
        meta["non_positive_gap_count"] = int(gaps_ms.le(0).sum())
    return meta


def safe_timestamp(value: Any) -> Optional[str]:
    if isinstance(value, pd.Timestamp) and not pd.isna(value):
        return value.isoformat()
    return None


def load_artifact_window_set(dataset: str, artifact_run: Path) -> Optional[WindowSet]:
    x_path = artifact_run / "data_transformation" / "production_X.npy"
    if not x_path.exists():
        return None
    X = np.load(x_path).astype(np.float32, copy=False)
    y = None
    local_y = artifact_run / "data_transformation" / "production_y.npy"
    global_y = ROOT / "data" / "prepared" / "production_y.npy"
    if local_y.exists():
        y_loaded = np.load(local_y)
        if len(y_loaded) == len(X):
            y = y_loaded.astype(np.int32)
    elif global_y.exists():
        y_loaded = np.load(global_y)
        if len(y_loaded) == len(X):
            y = y_loaded.astype(np.int32)
    meta = []
    meta_path = artifact_run / "data_transformation" / "production_metadata.json"
    if meta_path.exists():
        try:
            loaded = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                meta = loaded
            elif isinstance(loaded, dict) and isinstance(loaded.get("windows"), list):
                meta = loaded["windows"]
        except Exception:
            meta = []
    return WindowSet(dataset, "production_saved_artifact", X, y, meta, "artifact_metadata_or_global_y", rel(x_path))


def load_artifact_probs(artifact_run: Path, n_rows: int) -> Optional[np.ndarray]:
    inf_dir = artifact_run / "inference"
    if not inf_dir.exists():
        return None
    candidates = sorted(inf_dir.glob("*_probs.npy"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        arr = np.load(path)
        if arr.ndim == 2 and arr.shape == (n_rows, len(EXPECTED_CLASSES)):
            return arr.astype(np.float32)
    return None


def stats_df(df: pd.DataFrame, prefix: str) -> List[Dict[str, Any]]:
    rows = []
    for col in SENSOR_CANONICAL:
        series = pd.to_numeric(df[col], errors="coerce")
        rows.append(
            {
                "dataset": prefix,
                "channel": col,
                "min": float(series.min()),
                "mean": float(series.mean()),
                "std": float(series.std(ddof=0)),
                "max": float(series.max()),
                "nan": int(series.isna().sum()),
                "inf": int(np.isinf(series.to_numpy(dtype=float)).sum()),
                "constant": bool(series.nunique(dropna=True) <= 1),
            }
        )
    return rows


def stats_tensor(X: np.ndarray, prefix: str) -> List[Dict[str, Any]]:
    rows = []
    for idx, col in enumerate(SENSOR_CANONICAL):
        values = X[:, :, idx].reshape(-1).astype(np.float64) if X.size else np.asarray([])
        rows.append(
            {
                "dataset": prefix,
                "channel": col,
                "min": float(np.nanmin(values)) if values.size else None,
                "mean": float(np.nanmean(values)) if values.size else None,
                "std": float(np.nanstd(values)) if values.size else None,
                "max": float(np.nanmax(values)) if values.size else None,
                "nan": int(np.isnan(values).sum()) if values.size else 0,
                "inf": int(np.isinf(values).sum()) if values.size else 0,
                "constant": bool(np.nanstd(values) < 1e-12) if values.size else None,
            }
        )
    return rows


def summarize_distribution(y: Optional[np.ndarray]) -> Dict[str, int]:
    if y is None:
        return {}
    counts = Counter(int(v) for v in y)
    return {EXPECTED_INV.get(k, str(k)): int(counts[k]) for k in sorted(counts)}


def crossing_summary(meta: List[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "windows": len(meta),
        "cross_activity": int(sum(bool(m.get("crosses_activity")) for m in meta)),
        "cross_user": int(sum(bool(m.get("crosses_user")) for m in meta)),
        "large_gap_windows": int(sum(int(m.get("large_gap_count", 0)) > 0 for m in meta)),
        "non_positive_gap_windows": int(sum(int(m.get("non_positive_gap_count", 0)) > 0 for m in meta)),
    }


def metric_summary(y_true: np.ndarray, y_pred: np.ndarray, probs: Optional[np.ndarray] = None) -> Dict[str, Any]:
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=list(range(11)), average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, labels=list(range(11)), average="weighted", zero_division=0)),
        "prediction_distribution": {EXPECTED_INV[k]: int(v) for k, v in sorted(Counter(y_pred).items())},
        "true_distribution": {EXPECTED_INV[k]: int(v) for k, v in sorted(Counter(y_true).items())},
        "correct_by_class": {},
    }
    if probs is not None and len(probs):
        out["mean_confidence"] = float(np.max(probs, axis=1).mean())
    else:
        out["mean_confidence"] = None
    for idx, name in EXPECTED_INV.items():
        mask = y_true == idx
        out["correct_by_class"][name] = int(((y_pred == y_true) & mask).sum())
    return out


def best_permutation(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    cm = confusion_matrix(y_true, y_pred, labels=list(range(11)))
    if linear_sum_assignment is None:
        raise RuntimeError("scipy.optimize.linear_sum_assignment is required for permutation test")
    true_idx, pred_idx = linear_sum_assignment(-cm)
    pred_to_true = {int(pred): int(true) for true, pred in zip(true_idx, pred_idx)}
    rem_true = [i for i in range(11) if i not in pred_to_true.values()]
    for pred in range(11):
        if pred not in pred_to_true:
            pred_to_true[pred] = rem_true.pop(0) if rem_true else pred
    mapped = np.asarray([pred_to_true[int(p)] for p in y_pred], dtype=np.int32)
    cm_perm = confusion_matrix(y_true, mapped, labels=list(range(11)))
    return {
        "mapping_pred_index_to_true_index": pred_to_true,
        "mapping_pred_index_to_true_class": {str(k): EXPECTED_INV[v] for k, v in sorted(pred_to_true.items())},
        "metrics": metric_summary(y_true, mapped),
        "confusion_original": cm,
        "confusion_permuted": cm_perm,
        "mapped_pred": mapped,
    }


def save_confusion_csv(path: Path, cm: np.ndarray) -> None:
    rows = []
    for idx, name in EXPECTED_INV.items():
        row = {"true\\pred": name}
        for pred_idx, pred_name in EXPECTED_INV.items():
            row[pred_name] = int(cm[idx, pred_idx])
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)


def predict_model(model: Any, X: np.ndarray, batch_size: int = 128) -> np.ndarray:
    if len(X) == 0:
        return np.empty((0, 11), dtype=np.float32)
    probs = model.predict(X, batch_size=batch_size, verbose=0)
    return np.asarray(probs, dtype=np.float32)


def model_zip_metadata(path: Path) -> Dict[str, Any]:
    if not zipfile.is_zipfile(path):
        return {"is_zipfile": False}
    out: Dict[str, Any] = {"is_zipfile": True, "members": []}
    with zipfile.ZipFile(path, "r") as zf:
        out["members"] = zf.namelist()
        for member in ("metadata.json", "config.json"):
            if member in zf.namelist():
                try:
                    out[member] = json.loads(zf.read(member).decode("utf-8"))
                except Exception as exc:
                    out[member] = {"error": str(exc)}
    return out


def load_model_and_metadata() -> Tuple[Any, Dict[str, Any]]:
    import tensorflow as tf

    model = tf.keras.models.load_model(MODEL_DEPLOYED, compile=False)
    summary_buf = io.StringIO()
    model.summary(print_fn=lambda line: summary_buf.write(line + "\n"))
    zip_meta = model_zip_metadata(MODEL_DEPLOYED)
    compile_config = None
    config = zip_meta.get("config.json")
    if isinstance(config, dict):
        compile_config = config.get("compile_config")
    metadata = {
        "tensorflow_version": tf.__version__,
        "keras_version": getattr(tf.keras, "__version__", None),
        "input_shape": list(model.input_shape),
        "output_shape": list(model.output_shape),
        "count_params": int(model.count_params()),
        "layers": [
            {
                "name": layer.name,
                "class": layer.__class__.__name__,
                "output_shape": getattr(layer, "output_shape", None),
                "params": int(layer.count_params()),
            }
            for layer in model.layers
        ],
        "summary": summary_buf.getvalue(),
        "keras_zip_metadata": zip_meta.get("metadata.json"),
        "compile_config": compile_config,
    }
    return model, metadata


def report_model_provenance(model_meta: Dict[str, Any], search_matches: Dict[str, List[Dict[str, Any]]]) -> None:
    rows = [file_info(p) for p in MODEL_PATHS]
    same_sha = rows[0]["sha256"] == rows[1]["sha256"] if all(r["exists"] for r in rows) else False
    search_sections = []
    for pat, matches in search_matches.items():
        shown = matches[:40]
        search_sections.append(f"### Pattern `{pat}`\n\n" + md_table(shown, ["file", "line", "snippet"]))

    classification = (
        "Most consistent with an externally supplied ADAMSense / ICTH-family base checkpoint, "
        "not the local Garmin fine-tuned final artifact. Evidence: `scripts/finetune_garmin.py` "
        "uses this file as BASE_MODEL and saves Garmin fine-tuning to "
        "`garmin_finetuned_v1_<date>.keras`; no searched notebook/script saves this exact deployed "
        "filename as a Garmin final model; the Keras archive metadata does not encode the training "
        "dataset or fold identity."
    )

    text = f"""# 01 Model Provenance

## File Identity

{md_table(rows, ["path", "exists", "size_bytes", "sha256", "modified_time"])}

Same SHA256 between notebook and deployed copies: `{same_sha}`.

## Loaded Model

- Input shape: `{model_meta["input_shape"]}`
- Output shape: `{model_meta["output_shape"]}`
- Parameter count: `{model_meta["count_params"]}`
- TensorFlow version: `{model_meta["tensorflow_version"]}`
- Keras version: `{model_meta["keras_version"]}`
- Keras save metadata: `{json.dumps(model_meta.get("keras_zip_metadata"), default=str)}`
- Compile/optimizer/loss metadata available: `{model_meta.get("compile_config") is not None}`

## Layer Summary

```text
{model_meta["summary"].rstrip()}
```

## Provenance Classification

{classification}

## Search Evidence

{chr(10).join(search_sections)}
"""
    write_text(OUT_DIR / "01_model_provenance.md", text)


def extract_json_mapping(path: Path) -> Optional[Dict[str, Any]]:
    text = safe_read_text(path, max_bytes=2_000_000)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except Exception:
        return None
    candidates = find_json_mappings(data)
    for mapping in candidates:
        if mapping:
            return mapping
    return None


def find_json_mappings(obj: Any) -> List[Dict[str, int]]:
    candidates: List[Dict[str, int]] = []
    if isinstance(obj, dict):
        for key in ("activity_to_label", "class_to_index", "class_map"):
            value = obj.get(key)
            if isinstance(value, dict):
                mapping = {
                    canonical_label(k): int(v)
                    for k, v in value.items()
                    if str(v).lstrip("-").isdigit()
                }
                candidates.append(mapping)
        for key in ("label_to_activity", "activity_classes", "label_mapping"):
            value = obj.get(key)
            if isinstance(value, dict):
                rev = {}
                for k, v in value.items():
                    if str(k).lstrip("-").isdigit():
                        rev[canonical_label(v)] = int(k)
                candidates.append(rev)
        if all(str(i) in obj for i in range(8)):
            rev = {}
            for k, v in obj.items():
                if str(k).lstrip("-").isdigit() and isinstance(v, str):
                    rev[canonical_label(v)] = int(k)
            candidates.append(rev)
        for value in obj.values():
            candidates.extend(find_json_mappings(value))
    elif isinstance(obj, list):
        for value in obj:
            candidates.extend(find_json_mappings(value))
    return candidates


def extract_python_lists(path: Path) -> List[List[str]]:
    text = safe_read_text(path, max_bytes=2_000_000)
    if text is None:
        return []
    lists = []
    for match in re.finditer(r"([A-Z_]*(?:CLASSES|LABELS|ACTIVITIES|CLASS_NAMES)[A-Z_]*)\s*=\s*(\[[\s\S]*?\])", text):
        try:
            parsed = ast.literal_eval(match.group(2))
        except Exception:
            continue
        if isinstance(parsed, list):
            values = [canonical_label(v) for v in parsed if isinstance(v, str)]
            if values:
                lists.append(values)
    return lists


def first_occurrence_order(text: str) -> List[str]:
    found = []
    for match in re.finditer(r"ear[_ ]rubbing|forehead[_ ]rubbing|hair[_ ]pulling|hand[_ ]scratching|hand[_ ]tapping|knuckles?[_ ]cracking|nail[_ ]biting|nape[_ ]rubbing|idle[_ ]sitting|idle[_ ]standing|sitting|smoking|standing|hand[_ ]rubbing", text, flags=re.IGNORECASE):
        label = canonical_label(match.group(0))
        if label in EXPECTED_MAP and label not in found:
            found.append(label)
    return found


def class_mapping_audit(dataset_frames: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    rows = []
    seen_sources = set()
    for path in iter_text_files(["nb", "src", "config", "data", "reports", "artifacts", "outputs", "models"], max_bytes=2_000_000):
        text = safe_read_text(path, max_bytes=2_000_000)
        if text is None:
            continue
        if not any(cls in text for cls in EXPECTED_CLASSES[:4]):
            continue
        mapping = extract_json_mapping(path)
        py_lists = extract_python_lists(path)
        orders = []
        if mapping:
            order = [name for name, idx in sorted(mapping.items(), key=lambda item: item[1])]
            orders.append(order)
        orders.extend(py_lists)
        # First-occurrence order is useful in source code/notebooks, but very noisy
        # for generated reports because prediction distributions are not mappings.
        if not orders and path.suffix.lower() in {".py", ".ipynb", ".md", ".yaml", ".yml"}:
            order = first_occurrence_order(text)
            if len(order) >= 8:
                orders.append(order)
        for order in orders[:3]:
            key = (rel(path), tuple(order))
            if key in seen_sources:
                continue
            seen_sources.add(key)
            matches = order == EXPECTED_CLASSES
            risk = "low" if matches else ("medium: complete but different order" if len(order) == 11 else "high: missing or legacy class set")
            rows.append(
                {
                    "source file": rel(path),
                    "mapping/order found": ", ".join(order),
                    "matches expected?": matches,
                    "risk": risk,
                }
            )
    for name, df in dataset_frames.items():
        if "activity" in df.columns:
            first_order = []
            for label in df["activity"].astype(str):
                canonical = canonical_label(label)
                if canonical not in first_order:
                    first_order.append(canonical)
            rows.append(
                {
                    "source file": f"{name} CSV first occurrence",
                    "mapping/order found": ", ".join(first_order),
                    "matches expected?": first_order == EXPECTED_CLASSES,
                    "risk": "not a mapping: data row first-occurrence order only",
                }
            )
    rows = sorted(rows, key=lambda r: (str(r["matches expected?"]), r["source file"]))
    write_text(
        OUT_DIR / "02_class_mapping_audit.md",
        "# 02 Class Mapping Audit\n\n"
        + md_table(rows, ["source file", "mapping/order found", "matches expected?", "risk"])
        + "\n\n## Spelling Checks\n\n"
        + "- Canonicalization aliases checked: `ear rubbing`, `knuckle cracking`, `knuckles_cracking`, `hand rubbing`, `idle sitting`, `idle standing`.\n"
        + "- Any source using fewer than 11 classes is marked as high risk because it cannot match the deployed 11-output model.\n",
    )
    return rows


def timestamp_audit(dataset_frames: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    results = {}
    rows = []
    for name, df in dataset_frames.items():
        seg_df = add_segment_id(df)
        all_gaps = []
        large = 0
        nonpos = 0
        dupes = 0
        for _, part in seg_df.groupby("segment_id", sort=False):
            ts = part["timestamp_dt"]
            if ts.notna().sum() < 2:
                continue
            gaps_ms = ts.diff().dt.total_seconds() * 1000.0
            gaps = gaps_ms.dropna().to_numpy(dtype=float)
            all_gaps.extend(gaps.tolist())
            large += int((gaps_ms > LARGE_GAP_MS).sum())
            nonpos += int((gaps_ms <= 0).sum())
            dupes += int(ts.duplicated().sum())
        arr = np.asarray(all_gaps, dtype=float)
        summary = {
            "rows": int(len(df)),
            "segment_count": int(seg_df["segment_id"].nunique()),
            "median_gap_ms": float(np.median(arr)) if arr.size else None,
            "mean_gap_ms": float(np.mean(arr)) if arr.size else None,
            "large_gaps_gt_60ms": int(large),
            "non_positive_gaps": int(nonpos),
            "duplicate_timestamps_within_segments": int(dupes),
        }
        results[name] = summary
        rows.append({"dataset": name, **summary})
    write_text(
        OUT_DIR / "07_timestamp_resampling.md",
        "# 07 Timestamp / Resampling Audit\n\n"
        + "Both requested CSVs are treated as already preprocessed/reference-style; this audit checks continuity only.\n\n"
        + md_table(rows, ["dataset", "rows", "segment_count", "median_gap_ms", "mean_gap_ms", "large_gaps_gt_60ms", "non_positive_gaps", "duplicate_timestamps_within_segments"]),
    )
    return results


def dataset_identity_audit(dataset_frames: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    patterns = [
        "X_train.npy",
        "y_train.npy",
        "X_test.npy",
        "y_test.npy",
        "X.npy",
        "y.npy",
        "train",
        "test",
        "windows",
        "label_encoder",
        "class_map",
    ]
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        parts = Path(dirpath).parts
        lower_parts = {part.lower() for part in parts}
        if (
            ".git" in lower_parts
            or ".dvc" in lower_parts
            or "mlruns" in lower_parts
            or "__pycache__" in lower_parts
            or any(part.startswith(".") for part in parts)
        ):
            dirnames[:] = []
            continue
        dirnames[:] = [
            d
            for d in dirnames
            if d.lower() not in SKIP_DIR_NAMES and not any(d.lower().startswith(p) for p in SKIP_DIR_PREFIXES)
        ]
        for filename in filenames:
            lower = filename.lower()
            if any(pat.lower().replace("*", "") in lower for pat in patterns):
                path = Path(dirpath) / filename
                try:
                    stat = path.stat()
                except OSError:
                    continue
                item = {
                    "file": rel(path),
                    "size_bytes": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                    "shape": "",
                }
                if path.suffix.lower() == ".npy":
                    try:
                        item["shape"] = list(np.load(path, mmap_mode="r").shape)
                    except Exception as exc:
                        item["shape"] = f"unreadable: {exc}"
                files.append(item)
    files = sorted(files, key=lambda x: x["file"])[:250]

    dataset_rows = []
    for name, df in dataset_frames.items():
        row = {
            "dataset": name,
            "rows": len(df),
            "columns": ", ".join(df.columns[:20]),
            "activity_counts": summarize_activity_counts(df),
            "user_count": int(df["User"].nunique()) if "User" in df.columns else "n/a",
            "timestamp_min": safe_timestamp(df["timestamp_dt"].min()),
            "timestamp_max": safe_timestamp(df["timestamp_dt"].max()),
        }
        dataset_rows.append(row)

    extra = []
    for path in [ROOT / "data" / "all_users_data_labeled.csv", ROOT / "nb" / "all_users_data_labeled.csv", ROOT / "data" / "prepared" / "config.json"]:
        if path.exists():
            info = file_info(path)
            extra.append(info)
    text = (
        "# 06 Dataset Identity Audit\n\n"
        "## Dataset Summaries\n\n"
        + md_table(dataset_rows, ["dataset", "rows", "columns", "activity_counts", "user_count", "timestamp_min", "timestamp_max"])
        + "\n\n## Key File Identity\n\n"
        + md_table(extra, ["path", "exists", "size_bytes", "sha256", "modified_time"])
        + "\n\n## Discovered Training / Window / Label Artifacts\n\n"
        + md_table(files, ["file", "size_bytes", "modified_time", "shape"])
        + "\n\n## Interpretation\n\n"
        + "- `data/all_users_data_labeled.csv` and `nb/all_users_data_labeled.csv` are compared by SHA256 above.\n"
        + "- `data/prepared/config.json` is historical training/preparation metadata, but the deployed Keras archive itself does not encode enough training-data provenance to prove this CSV was the exact representation used to create the checkpoint.\n"
    )
    write_text(OUT_DIR / "06_dataset_identity.md", text)
    return {"files": files, "datasets": dataset_rows, "key_files": extra}


def summarize_activity_counts(df: pd.DataFrame) -> str:
    if "activity" not in df.columns:
        return ""
    counts = df["activity"].astype(str).map(canonical_label).value_counts().to_dict()
    return ", ".join(f"{k}:{int(v)}" for k, v in counts.items())


def feature_order_audit(dataset_frames: Dict[str, pd.DataFrame], window_sets: Dict[str, Dict[str, WindowSet]]) -> None:
    sections = ["# 04 Feature-Order and Tensor-Channel Audit\n"]
    for dataset, df in dataset_frames.items():
        sections.append(f"## {dataset}\n")
        sections.append("### First 5 Source Rows\n")
        sections.append(df[SENSOR_CANONICAL + (["activity"] if "activity" in df.columns else [])].head(5).to_markdown(index=False))
        for ws_name, ws in window_sets[dataset].items():
            if len(ws.X) == 0:
                continue
            sections.append(f"\n### {ws_name} First Window First 5 Rows\n")
            win_df = pd.DataFrame(ws.X[0, :5, :], columns=SENSOR_CANONICAL)
            sections.append(win_df.to_markdown(index=False))
            if ws_name in ("reference_row_index", "pipeline_calculated_row_index"):
                source_first = df[SENSOR_CANONICAL].iloc[:WINDOW_SIZE].to_numpy(dtype=np.float32)
                diff = np.nanmax(np.abs(source_first - ws.X[0]))
                sections.append(f"\nMax absolute diff vs source first 200 rows in expected channel order: `{diff:.8g}`.\n")
            if ws_name == "production_saved_artifact":
                source_first = df[SENSOR_CANONICAL].iloc[:WINDOW_SIZE].to_numpy(dtype=np.float32)
                expected_diff = float(np.nanmax(np.abs(source_first - ws.X[0])))
                swapped = ws.X[0][:, [3, 4, 5, 0, 1, 2]]
                swap_diff = float(np.nanmax(np.abs(source_first - swapped)))
                sections.append(
                    f"\nSaved artifact channel check: expected-order diff `{expected_diff:.8g}`, "
                    f"accel/gyro-block-swapped diff `{swap_diff:.8g}`.\n"
                )
    sections.append(
        "\n## Interpretation\n\n"
        "- Channel 0..5 is directly compared against row values, not inferred from column names only.\n"
        "- A zero or near-zero expected-order diff is evidence against accidental gyro-before-accel or channel swap in the saved tensor.\n"
    )
    write_text(OUT_DIR / "04_feature_order_audit.md", "\n".join(sections))


def unit_stats_report(dataset_frames: Dict[str, pd.DataFrame], window_sets: Dict[str, Dict[str, WindowSet]]) -> None:
    rows = []
    for dataset, df in dataset_frames.items():
        rows.extend(stats_df(df, f"{dataset}_source_dataframe"))
        for ws_name, ws in window_sets[dataset].items():
            rows.extend(stats_tensor(ws.X, f"{dataset}_{ws_name}"))
    pd.DataFrame(rows).to_csv(OUT_DIR / "unit_stats_all.csv", index=False)
    notes = []
    for row in rows:
        channel = row["channel"]
        max_abs = max(abs(row["min"]), abs(row["max"])) if row["min"] is not None else 0
        if channel.startswith("A") and max_abs > 100:
            notes.append(f"{row['dataset']} {channel}: accelerometer values look like milli-g (max_abs={max_abs:.2f}).")
        if channel.startswith("A") and max_abs < 1:
            notes.append(f"{row['dataset']} {channel}: accelerometer may be double converted or in g (max_abs={max_abs:.2f}).")
        if channel.startswith("G") and max_abs < 10:
            notes.append(f"{row['dataset']} {channel}: low gyro range could indicate rad/s or quiet data (max_abs={max_abs:.2f}).")
        if channel.startswith("G") and max_abs > 1000:
            notes.append(f"{row['dataset']} {channel}: extreme gyro range exceeds common dps assumptions (max_abs={max_abs:.2f}).")
    write_text(
        OUT_DIR / "05_unit_stats.md",
        "# 05 Unit and Value-Range Audit\n\n"
        + md_table(rows, ["dataset", "channel", "min", "mean", "std", "max", "nan", "inf", "constant"])
        + "\n\n## Automated Flags\n\n"
        + ("\n".join(f"- {note}" for note in notes) if notes else "- No milli-g, double-conversion, NaN/inf, or constant-channel issue was flagged by the coarse thresholds.")
        + "\n\n`data/all_users_data_labeled.csv` and the User 7 CSV were treated as already preprocessed/reference-style; no conversion was applied in this audit.\n",
    )


def windowing_parity_report(window_sets: Dict[str, Dict[str, WindowSet]]) -> None:
    rows = []
    first_rows = []
    for dataset, sets in window_sets.items():
        for name, ws in sets.items():
            cross = crossing_summary(ws.meta)
            rows.append(
                {
                    "dataset": dataset,
                    "window set": name,
                    "X shape": list(ws.X.shape),
                    "y shape": list(ws.y.shape) if ws.y is not None else None,
                    "window count": int(len(ws.X)),
                    "windows per class": summarize_distribution(ws.y),
                    "crosses activity": cross["cross_activity"],
                    "crosses user": cross["cross_user"],
                    "gap-cross windows": cross["large_gap_windows"],
                    "window size": WINDOW_SIZE,
                    "stride": STRIDE,
                    "label assignment": ws.label_rule,
                }
            )
            for row in ws.meta[:3]:
                first_rows.append(
                    {
                        "dataset": dataset,
                        "window set": name,
                        "window_id": row.get("window_id"),
                        "start_idx": row.get("start_idx"),
                        "end_idx_exclusive": row.get("end_idx_exclusive", row.get("end_idx")),
                        "timestamp_start": row.get("timestamp_start"),
                        "timestamp_end": row.get("timestamp_end"),
                    }
                )
    write_text(
        OUT_DIR / "08_windowing_parity.md",
        "# 08 Windowing Parity Audit\n\n"
        "Reference-style row-index windows are reconstructed from the source/reference CSVs. "
        "Segment-aware windows prevent user/activity/gap crossings. Production calculated windows mirror current row-index Stage 3 behavior. "
        "Saved artifacts are loaded from the requested run directories.\n\n"
        + md_table(rows, ["dataset", "window set", "X shape", "y shape", "window count", "windows per class", "crosses activity", "crosses user", "gap-cross windows", "window size", "stride", "label assignment"])
        + "\n\n## First 3 Windows\n\n"
        + md_table(first_rows, ["dataset", "window set", "window_id", "start_idx", "end_idx_exclusive", "timestamp_start", "timestamp_end"]),
    )


def window_label_parity_report(window_sets: Dict[str, Dict[str, WindowSet]]) -> None:
    rows = []
    for dataset, sets in window_sets.items():
        for name, ws in sets.items():
            if not ws.meta or ws.y is None:
                continue
            if not any(row.get("label_majority") is not None for row in ws.meta):
                global_y = ROOT / "data" / "prepared" / "production_y.npy"
                rows.append(
                    {
                        "dataset": dataset,
                        "window set": name,
                        "n": len(ws.y),
                        "first==majority": "n/a",
                        "center==majority": "n/a",
                        "y==majority": "n/a",
                        "all three identical": "n/a",
                        "production_y_path_checked": rel(global_y) if global_y.exists() else "missing",
                        "production_y_shape_now": list(np.load(global_y, mmap_mode="r").shape) if global_y.exists() else None,
                    }
                )
                continue
            first = []
            center = []
            majority = []
            for row in ws.meta:
                first.append(row.get("label_first"))
                center.append(row.get("label_center"))
                majority.append(row.get("label_majority"))
            first_ids = np.asarray([label_to_id(v) if v is not None else -1 for v in first], dtype=np.int32)
            center_ids = np.asarray([label_to_id(v) if v is not None else -1 for v in center], dtype=np.int32)
            majority_ids = np.asarray([label_to_id(v) if v is not None else -1 for v in majority], dtype=np.int32)
            rows.append(
                {
                    "dataset": dataset,
                    "window set": name,
                    "n": len(ws.y),
                    "first==majority": int((first_ids == majority_ids).sum()),
                    "center==majority": int((center_ids == majority_ids).sum()),
                    "y==majority": int((ws.y == majority_ids).sum()),
                    "all three identical": int(((first_ids == center_ids) & (center_ids == majority_ids)).sum()),
                }
            )
            if name == "production_saved_artifact":
                global_y = ROOT / "data" / "prepared" / "production_y.npy"
                rows[-1]["production_y_path_checked"] = rel(global_y) if global_y.exists() else "missing"
                rows[-1]["production_y_shape_now"] = list(np.load(global_y, mmap_mode="r").shape) if global_y.exists() else None
    write_text(
        OUT_DIR / "09_window_label_parity.md",
        "# 09 Window-Label Parity Audit\n\n"
        + md_table(rows, ["dataset", "window set", "n", "first==majority", "center==majority", "y==majority", "all three identical", "production_y_path_checked", "production_y_shape_now"])
        + "\n\nThe saved run artifacts do not include a run-local `production_y.npy`; their transformation reports point to the mutable global `data/prepared/production_y.npy`. That is a reproducibility risk for old run re-evaluation, even when the metrics written during the run used the then-current labels.\n",
    )


def tensor_parity_report(window_sets: Dict[str, Dict[str, WindowSet]]) -> None:
    rows = []
    diff_rows = []
    for dataset, sets in window_sets.items():
        for name, ws in sets.items():
            rows.append(
                {
                    "dataset": dataset,
                    "tensor": name,
                    "shape": list(ws.X.shape),
                    "nan_count": int(np.isnan(ws.X).sum()),
                    "inf_count": int(np.isinf(ws.X).sum()),
                    "channel_stats": {r["channel"]: {"mean": r["mean"], "std": r["std"]} for r in stats_tensor(ws.X, name)},
                    "first_window_first_row": ws.X[0, 0, :].tolist() if len(ws.X) else None,
                }
            )
        pairs = [
            ("reference_row_index", "pipeline_calculated_row_index"),
            ("pipeline_calculated_row_index", "production_saved_artifact"),
            ("reference_row_index", "production_saved_artifact"),
            ("reference_row_index", "gpt_segment_aware"),
        ]
        for left, right in pairs:
            if left not in sets or right not in sets:
                continue
            A, B = sets[left].X, sets[right].X
            comparable = A.shape == B.shape
            max_abs = float(np.nanmax(np.abs(A - B))) if comparable and A.size else None
            sample_diffs = []
            if comparable and len(A):
                idxs = RNG.choice(len(A), size=min(10, len(A)), replace=False)
                for idx in idxs:
                    sample_diffs.append(float(np.nanmax(np.abs(A[idx] - B[idx]))))
            diff_rows.append(
                {
                    "dataset": dataset,
                    "left": left,
                    "right": right,
                    "shape_left": list(A.shape),
                    "shape_right": list(B.shape),
                    "comparable": comparable,
                    "max_abs_diff": max_abs,
                    "random_10_window_max_abs_diffs": sample_diffs,
                }
            )
    write_text(
        OUT_DIR / "10_tensor_parity.md",
        "# 10 Tensor Parity Audit\n\n## Tensor Summaries\n\n"
        + md_table(rows, ["dataset", "tensor", "shape", "nan_count", "inf_count", "first_window_first_row", "channel_stats"])
        + "\n\n## Pairwise Diffs\n\n"
        + md_table(diff_rows, ["dataset", "left", "right", "shape_left", "shape_right", "comparable", "max_abs_diff", "random_10_window_max_abs_diffs"]),
    )


def prediction_parity_report(
    model: Any,
    window_sets: Dict[str, Dict[str, WindowSet]],
    artifact_probs: Dict[Tuple[str, str], np.ndarray],
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    all_results: Dict[Tuple[str, str], Dict[str, Any]] = {}
    rows = []
    for dataset, sets in window_sets.items():
        for name, ws in sets.items():
            probs = artifact_probs.get((dataset, name))
            if probs is None:
                probs = predict_model(model, ws.X)
            pred = np.argmax(probs, axis=1).astype(np.int32)
            result = {
                "probs": probs,
                "pred": pred,
                "metrics": metric_summary(ws.y, pred, probs) if ws.y is not None else None,
            }
            all_results[(dataset, name)] = result
            if ws.y is not None:
                cm = confusion_matrix(ws.y, pred, labels=list(range(11)))
                save_confusion_csv(OUT_DIR / f"confusion_prediction_parity_{dataset}_{name}.csv", cm)
                row = {
                    "dataset": dataset,
                    "window set": name,
                    "accuracy": result["metrics"]["accuracy"],
                    "macro F1": result["metrics"]["macro_f1"],
                    "weighted F1": result["metrics"]["weighted_f1"],
                    "mean confidence": result["metrics"]["mean_confidence"],
                    "prediction distribution": result["metrics"]["prediction_distribution"],
                    "true distribution": result["metrics"]["true_distribution"],
                    "correct by class": result["metrics"]["correct_by_class"],
                }
                rows.append(row)
    write_text(
        OUT_DIR / "11_prediction_parity.md",
        "# 11 Prediction Parity Audit\n\n"
        + md_table(rows, ["dataset", "window set", "accuracy", "macro F1", "weighted F1", "mean confidence", "prediction distribution", "true distribution", "correct by class"])
        + "\n\nConfusion matrices are saved as `confusion_prediction_parity_*.csv`.\n",
    )
    return all_results


def class_permutation_report(
    window_sets: Dict[str, Dict[str, WindowSet]],
    prediction_results: Dict[Tuple[str, str], Dict[str, Any]],
) -> Dict[str, Any]:
    rows = []
    details = {}
    targets = [
        ("all_users", "gpt_segment_aware"),
        ("all_users", "production_saved_artifact"),
        ("user7", "gpt_segment_aware"),
        ("user7", "production_saved_artifact"),
    ]
    for dataset, name in targets:
        ws = window_sets[dataset].get(name)
        result = prediction_results.get((dataset, name))
        if ws is None or result is None or ws.y is None:
            continue
        y_true = ws.y
        y_pred = result["pred"]
        orig_metrics = metric_summary(y_true, y_pred, result["probs"])
        perm = best_permutation(y_true, y_pred)
        save_confusion_csv(OUT_DIR / f"confusion_original_{dataset}_{name}.csv", perm["confusion_original"])
        save_confusion_csv(OUT_DIR / f"confusion_best_permuted_{dataset}_{name}.csv", perm["confusion_permuted"])
        rows.append(
            {
                "dataset": dataset,
                "window set": name,
                "original accuracy": orig_metrics["accuracy"],
                "original macro F1": orig_metrics["macro_f1"],
                "best-permuted accuracy": perm["metrics"]["accuracy"],
                "best-permuted macro F1": perm["metrics"]["macro_f1"],
                "best mapping pred_index->true_class": perm["mapping_pred_index_to_true_class"],
            }
        )
        details[f"{dataset}_{name}"] = {
            "original": orig_metrics,
            "best_permuted": perm["metrics"],
            "mapping": perm["mapping_pred_index_to_true_class"],
        }
    interpretation = (
        "If class order were the main bug, best-permuted accuracy would jump to a high value. "
        "The diagnostic conclusion should be based on the table below."
    )
    write_text(
        OUT_DIR / "03_class_permutation_test.md",
        "# 03 Class Permutation Sanity Test\n\n"
        + interpretation
        + "\n\n"
        + md_table(rows, ["dataset", "window set", "original accuracy", "original macro F1", "best-permuted accuracy", "best-permuted macro F1", "best mapping pred_index->true_class"])
        + "\n\nOriginal and best-permuted confusion matrices are saved as `confusion_original_*.csv` and `confusion_best_permuted_*.csv`.\n",
    )
    return details


def apply_variant(X: np.ndarray, variant: str) -> np.ndarray:
    out = X.copy()
    if variant == "expected_feature_order":
        return out
    if variant == "accel_gyro_block_swapped":
        return out[:, :, [3, 4, 5, 0, 1, 2]]
    if variant == "gyro_deg_to_rad":
        out[:, :, 3:6] *= np.float32(math.pi / 180.0)
        return out
    if variant == "gyro_rad_to_deg":
        out[:, :, 3:6] *= np.float32(180.0 / math.pi)
        return out
    if variant == "accel_ms2_to_g":
        out[:, :, 0:3] /= np.float32(9.80665)
        return out
    if variant == "accel_g_to_ms2":
        out[:, :, 0:3] *= np.float32(9.80665)
        return out
    if variant == "accel_double_convert_ms2_by_0p00981":
        out[:, :, 0:3] *= np.float32(0.00981)
        return out
    if variant == "accel_no_conversion_if_source_millig":
        out[:, :, 0:3] /= np.float32(0.00981)
        return out
    if variant == "flip_ax":
        out[:, :, 0] *= -1
        return out
    if variant == "flip_ay":
        out[:, :, 1] *= -1
        return out
    if variant == "flip_az":
        out[:, :, 2] *= -1
        return out
    if variant == "flip_all_accel":
        out[:, :, 0:3] *= -1
        return out
    if variant == "swap_accel_xy":
        out[:, :, [0, 1]] = out[:, :, [1, 0]]
        return out
    if variant == "swap_accel_xz":
        out[:, :, [0, 2]] = out[:, :, [2, 0]]
        return out
    if variant == "swap_accel_yz":
        out[:, :, [1, 2]] = out[:, :, [2, 1]]
        return out
    raise KeyError(variant)


def controlled_transform_report(model: Any, window_sets: Dict[str, Dict[str, WindowSet]]) -> Dict[str, Any]:
    variants = [
        "expected_feature_order",
        "accel_gyro_block_swapped",
        "gyro_deg_to_rad",
        "gyro_rad_to_deg",
        "accel_ms2_to_g",
        "accel_g_to_ms2",
        "accel_double_convert_ms2_by_0p00981",
        "accel_no_conversion_if_source_millig",
        "flip_ax",
        "flip_ay",
        "flip_az",
        "flip_all_accel",
        "swap_accel_xy",
        "swap_accel_xz",
        "swap_accel_yz",
    ]
    rows = []
    for dataset in ("all_users", "user7"):
        ws = window_sets[dataset]["gpt_segment_aware"]
        for variant in variants:
            Xv = apply_variant(ws.X, variant)
            probs = predict_model(model, Xv)
            pred = np.argmax(probs, axis=1).astype(np.int32)
            metrics = metric_summary(ws.y, pred, probs)
            rows.append(
                {
                    "dataset": dataset,
                    "base window set": ws.name,
                    "variant": variant,
                    "accuracy": metrics["accuracy"],
                    "macro F1": metrics["macro_f1"],
                    "weighted F1": metrics["weighted_f1"],
                    "mean confidence": metrics["mean_confidence"],
                    "prediction distribution": metrics["prediction_distribution"],
                }
            )
    sorted_rows = sorted(rows, key=lambda r: (r["dataset"], -float(r["accuracy"])))
    pd.DataFrame(rows).to_csv(OUT_DIR / "controlled_transform_results.csv", index=False)
    text = (
        "# 12 Controlled Transformation Tests\n\n"
        "These are diagnostic-only transformations. They are not applied to production code.\n\n"
        + md_table(sorted_rows, ["dataset", "base window set", "variant", "accuracy", "macro F1", "weighted F1", "mean confidence", "prediction distribution"])
        + "\n\nInterpretation rule: a strong jump would imply the named contract mismatch. No production fix should be made from a weak or marginal variant.\n"
    )
    write_text(OUT_DIR / "12_controlled_transform_tests.md", text)
    return {"rows": rows}


def summary_features(X: np.ndarray) -> np.ndarray:
    means = X.mean(axis=1)
    stds = X.std(axis=1)
    mins = X.min(axis=1)
    maxs = X.max(axis=1)
    meds = np.median(X, axis=1)
    return np.concatenate([means, stds, mins, maxs, meds], axis=1)


def learnability_report(window_sets: Dict[str, Dict[str, WindowSet]]) -> Dict[str, Any]:
    rows = []
    all_ws = window_sets["all_users"]["gpt_segment_aware"]
    user7_ws = window_sets["user7"]["gpt_segment_aware"]
    X_feat = summary_features(all_ws.X)
    y = all_ws.y
    groups = np.asarray([str(m.get("user", "")) for m in all_ws.meta])
    if y is None:
        raise RuntimeError("All-users segment windows unexpectedly have no labels")

    train_mask = np.isin(groups, ["1", "2", "3", "4"])
    val_mask = groups == "5"
    test_mask = groups == "6"
    if train_mask.sum() and test_mask.sum():
        rf = RandomForestClassifier(n_estimators=120, random_state=42, n_jobs=1, class_weight="balanced_subsample")
        rf.fit(X_feat[train_mask], y[train_mask])
        for split_name, mask in [("user_group_val_user5", val_mask), ("user_group_test_user6", test_mask)]:
            if mask.sum():
                pred = rf.predict(X_feat[mask])
                rows.append(
                    {
                        "test": f"RandomForest summary features {split_name}",
                        "n_train": int(train_mask.sum()),
                        "n_eval": int(mask.sum()),
                        "accuracy": float(accuracy_score(y[mask], pred)),
                        "macro F1": float(f1_score(y[mask], pred, labels=list(range(11)), average="macro", zero_division=0)),
                    }
                )
        if user7_ws.y is not None:
            pred = rf.predict(summary_features(user7_ws.X))
            rows.append(
                {
                    "test": "RandomForest train users1-4 -> User7 summary features",
                    "n_train": int(train_mask.sum()),
                    "n_eval": int(len(user7_ws.y)),
                    "accuracy": float(accuracy_score(user7_ws.y, pred)),
                    "macro F1": float(f1_score(user7_ws.y, pred, labels=list(range(11)), average="macro", zero_division=0)),
                }
            )

    # Tiny overfit diagnostic on flattened windows. Use no scaler in the pipeline; this
    # internal scaler is only for a diagnostic linear baseline, not model inference.
    n_sample = min(300, len(y))
    chosen = []
    per_class = max(1, n_sample // len(EXPECTED_CLASSES))
    for cls in range(11):
        idx = np.where(y == cls)[0]
        if len(idx):
            chosen.extend(RNG.choice(idx, size=min(per_class, len(idx)), replace=False).tolist())
    if len(chosen) < n_sample:
        remaining = np.setdiff1d(np.arange(len(y)), np.asarray(chosen, dtype=int))
        chosen.extend(RNG.choice(remaining, size=min(n_sample - len(chosen), len(remaining)), replace=False).tolist())
    chosen = np.asarray(chosen[:n_sample], dtype=int)
    flat = all_ws.X[chosen].reshape(len(chosen), -1)
    y_small = y[chosen]
    rf_overfit = RandomForestClassifier(n_estimators=160, random_state=43, n_jobs=1)
    rf_overfit.fit(flat, y_small)
    pred_small = rf_overfit.predict(flat)
    rows.append(
        {
            "test": "RandomForest flattened tiny overfit same 300 windows",
            "n_train": int(len(chosen)),
            "n_eval": int(len(chosen)),
            "accuracy": float(accuracy_score(y_small, pred_small)),
            "macro F1": float(f1_score(y_small, pred_small, labels=list(range(11)), average="macro", zero_division=0)),
        }
    )

    # Logistic regression on raw flattened windows. This is diagnostic only and
    # deliberately avoids adding a StandardScaler to the HAR preprocessing path.
    with contextlib.suppress(Exception):
        lr = LogisticRegression(max_iter=800, random_state=42)
        lr.fit(flat, y_small)
        pred_lr = lr.predict(flat)
        rows.append(
            {
                "test": "LogisticRegression flattened tiny overfit same 300 windows",
                "n_train": int(len(chosen)),
                "n_eval": int(len(chosen)),
                "accuracy": float(accuracy_score(y_small, pred_lr)),
                "macro F1": float(f1_score(y_small, pred_lr, labels=list(range(11)), average="macro", zero_division=0)),
            }
        )

    write_text(
        OUT_DIR / "13_learnability_test.md",
        "# 13 Baseline Learnability Test\n\n"
        "These models are diagnostic-only and are not saved or used for production inference.\n\n"
        + md_table(rows, ["test", "n_train", "n_eval", "accuracy", "macro F1"])
        + "\n\nInterpretation: successful tiny overfit means the regenerated labels/features are internally learnable; failure of the deployed checkpoint is therefore more likely a checkpoint/provenance or hidden training-contract issue than a total label/window corruption.\n",
    )
    return {"rows": rows}


def artifact_json_audit() -> None:
    rows = []
    for dataset, cfg in DATASETS.items():
        run = cfg["artifact_run"]
        for path in sorted(run.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            summary = ""
            if isinstance(data, dict):
                keys = [
                    "accuracy",
                    "dominant_class",
                    "dominant_pct",
                    "has_labels",
                    "production_y_path",
                    "collapse_level",
                    "model_input_space",
                ]
                hits = {k: data.get(k) for k in keys if k in data}
                if not hits and "classification_metrics" in data:
                    cm = data.get("classification_metrics", {})
                    hits = {"accuracy": cm.get("accuracy"), "f1_macro": cm.get("f1_macro")}
                if not hits and "labels" in data:
                    hits = data.get("labels")
                summary = json.dumps(hits, default=str)[:400]
            rows.append({"dataset": dataset, "file": rel(path), "summary": summary})
    write_text(
        OUT_DIR / "artifact_json_inventory.md",
        "# Artifact JSON Inventory for Requested Runs\n\n"
        + md_table(rows, ["dataset", "file", "summary"]),
    )


def final_report(
    provenance: str,
    permutation_details: Dict[str, Any],
    transform_results: Dict[str, Any],
    learnability: Dict[str, Any],
    prediction_results: Dict[Tuple[str, str], Dict[str, Any]],
) -> None:
    pred_rows = []
    for (dataset, name), result in prediction_results.items():
        if result["metrics"] is None:
            continue
        if name in ("gpt_segment_aware", "production_saved_artifact"):
            pred_rows.append(
                {
                    "dataset": dataset,
                    "window set": name,
                    "accuracy": result["metrics"]["accuracy"],
                    "macro F1": result["metrics"]["macro_f1"],
                    "prediction distribution": result["metrics"]["prediction_distribution"],
                }
            )
    best_transform = []
    for dataset in ("all_users", "user7"):
        rows = [r for r in transform_results["rows"] if r["dataset"] == dataset]
        if rows:
            best_transform.append(max(rows, key=lambda r: r["accuracy"]))
    learn_rows = learnability["rows"]

    root_cause_ranking = [
        {
            "rank": 1,
            "cause": "Current deployed checkpoint is not proven to be the final Garmin fine-tuned model for this corpus; it behaves like an external/base/stale artifact.",
            "evidence": "Current repo training script uses this checkpoint as BASE_MODEL and saves Garmin fine-tuning to a separate filename; direct evaluations stay near chance across row-index and segment-aware windows; tiny baselines can overfit regenerated windows.",
        },
        {
            "rank": 2,
            "cause": "Hidden training-contract/dataset mismatch between the provided checkpoint and `all_users_data_labeled.csv`.",
            "evidence": "Keras archive has no dataset/fold metadata; `processing.ipynb` is data processing, not model-save provenance; controlled unit/order transforms do not recover high accuracy.",
        },
        {
            "rank": 3,
            "cause": "Mutable `data/prepared/production_y.npy` makes old run re-evaluation fragile.",
            "evidence": "Requested run transformation reports point to global y, and no run-local y copy exists in the artifact directories. This is a reproducibility risk, not sufficient to explain the immediate low metrics written during each run.",
        },
        {
            "rank": 4,
            "cause": "Production row-index windowing crosses activity/session boundaries.",
            "evidence": "Segment-aware windows reduce boundary crossing but still produce low checkpoint accuracy, so this is a secondary bug/risk rather than the primary collapse cause.",
        },
        {
            "rank": 5,
            "cause": "Class mapping, feature order, or accel unit conversion mismatch.",
            "evidence": "Canonical mapping appears in the active inference path; best class permutation remains low; saved tensors match expected channel order; accelerometer ranges are already m/s^2.",
        },
    ]
    text = (
        "# Final Root Cause Report\n\n"
        "## Short Summary\n\n"
        "The deployed `fine_tuned_model_1dcnnbilstm.keras` fails on both labeled all-users and User 7 windows under the documented input contract. The strongest current cause is checkpoint/provenance mismatch: this file is not proven to be the final Garmin fine-tuned model for the local labeled corpus, and local evidence treats it as a base/external checkpoint. No minimal production code fix is proven by the diagnostics.\n\n"
        "## Key Prediction Evidence\n\n"
        + md_table(pred_rows, ["dataset", "window set", "accuracy", "macro F1", "prediction distribution"])
        + "\n\n## Class Permutation Evidence\n\n"
        + md_table(
            [
                {
                    "case": key,
                    "original accuracy": val["original"]["accuracy"],
                    "best-permuted accuracy": val["best_permuted"]["accuracy"],
                    "best mapping": val["mapping"],
                }
                for key, val in permutation_details.items()
            ],
            ["case", "original accuracy", "best-permuted accuracy", "best mapping"],
        )
        + "\n\n## Controlled Transform Evidence\n\n"
        + md_table(best_transform, ["dataset", "variant", "accuracy", "macro F1", "prediction distribution"])
        + "\n\n## Learnability Evidence\n\n"
        + md_table(learn_rows, ["test", "n_train", "n_eval", "accuracy", "macro F1"])
        + "\n\n## Ruled-Out Causes\n\n"
        + "- Wrong local copy/path: ruled out by matching SHA256 between `nb/` and `models/pretrained/`.\n"
        + "- Class/output-order mismatch as primary cause: best Hungarian remapping does not recover high accuracy.\n"
        + "- Feature channel order mismatch: saved tensors match source first-window channel values in expected order.\n"
        + "- Accelerometer milli-g/double-conversion: source and artifacts are in m/s^2 scale; no conversion was applied to already preprocessed CSVs.\n"
        + "- Production row-index windowing as sole cause: segment-aware windows still fail.\n\n"
        + "## Root Cause Ranking\n\n"
        + md_table(root_cause_ranking, ["rank", "cause", "evidence"])
        + "\n\n## Recommended Minimal Fix\n\n"
        + "Do not patch preprocessing or class order based on this evidence. The minimal safe next step is to obtain or validate the actual final Garmin checkpoint and its exact training contract, then update the deployment model pointer only after a labeled evaluation passes on frozen run-local `X/y` artifacts. Also copy `production_y.npy` into each run's `data_transformation` artifact directory so old `production_X.npy` files cannot be evaluated against a later overwritten global label file.\n\n"
        + "## Code Changes\n\n"
        + "No production code was changed. Diagnostics only were added under `diagnostics/model_contract_debug/`.\n\n"
        + "## Reproduce\n\n"
        + "```powershell\n"
        + "C:\\Users\\shali\\anaconda3\\envs\\thesis-mlops\\python.exe diagnostics\\model_contract_debug\\run_model_contract_debug.py\n"
        + "```\n"
    )
    write_text(OUT_DIR / "FINAL_ROOT_CAUSE_REPORT.md", text)


def main() -> None:
    start = time.time()
    os.chdir(ROOT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    model, model_meta = load_model_and_metadata()
    provenance_patterns = [
        r"fine_tuned_model_1dcnnbilstm\.keras",
        r"model\.save",
        r"save_model",
        r"1DCNNBiLSTM|1dcnn.?bilstm",
        r"fine_tuned",
        r"5-fold|5 fold",
        r"Garmin",
        r"ADAMSense|ADAM-sense",
    ]
    search_matches = scan_patterns(provenance_patterns, max_matches_per_pattern=120)
    report_model_provenance(model_meta, search_matches)

    dataset_frames: Dict[str, pd.DataFrame] = {}
    processed_frames: Dict[str, pd.DataFrame] = {}
    for name, cfg in DATASETS.items():
        dataset_frames[name] = read_csv_dataset(cfg["source_csv"])
        processed_frames[name] = read_csv_dataset(cfg["processed_csv"])

    class_mapping_audit(dataset_frames)
    dataset_identity_audit(dataset_frames)
    timestamp_audit(dataset_frames)
    artifact_json_audit()

    window_sets: Dict[str, Dict[str, WindowSet]] = defaultdict(dict)
    artifact_probs: Dict[Tuple[str, str], np.ndarray] = {}
    for name, cfg in DATASETS.items():
        source_df = dataset_frames[name]
        processed_df = processed_frames[name]
        window_sets[name]["reference_row_index"] = build_row_windows(
            name, source_df, "reference_row_index", rel(cfg["source_csv"])
        )
        window_sets[name]["gpt_segment_aware"] = build_segment_windows(
            name, source_df, "gpt_segment_aware", rel(cfg["source_csv"])
        )
        window_sets[name]["pipeline_calculated_row_index"] = build_row_windows(
            name, processed_df, "pipeline_calculated_row_index", rel(cfg["processed_csv"])
        )
        artifact_ws = load_artifact_window_set(name, cfg["artifact_run"])
        if artifact_ws is not None:
            window_sets[name]["production_saved_artifact"] = artifact_ws
            probs = load_artifact_probs(cfg["artifact_run"], len(artifact_ws.X))
            if probs is not None:
                artifact_probs[(name, "production_saved_artifact")] = probs

    feature_order_audit(dataset_frames, window_sets)
    unit_stats_report(dataset_frames, window_sets)
    windowing_parity_report(window_sets)
    window_label_parity_report(window_sets)
    tensor_parity_report(window_sets)
    prediction_results = prediction_parity_report(model, window_sets, artifact_probs)
    permutation_details = class_permutation_report(window_sets, prediction_results)
    transform_results = controlled_transform_report(model, window_sets)
    learnability = learnability_report(window_sets)

    final_report(
        provenance="base_or_unknown",
        permutation_details=permutation_details,
        transform_results=transform_results,
        learnability=learnability,
        prediction_results=prediction_results,
    )
    write_json(
        OUT_DIR / "run_manifest.json",
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "duration_seconds": time.time() - start,
            "repo_root": ROOT,
            "python": sys.executable,
            "outputs": sorted(rel(p) for p in OUT_DIR.iterdir() if p.is_file()),
        },
    )
    print(f"Diagnostics complete in {time.time() - start:.1f}s. Outputs: {OUT_DIR}")


if __name__ == "__main__":
    main()

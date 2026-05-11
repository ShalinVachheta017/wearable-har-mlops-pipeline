"""Compare mentor notebook contracts with the production pipeline contract.

Diagnostic-only. This script does not modify production code, retrain models, or
delete artifacts. It writes:

  nb/mentor_vs_pipeline_contract_comparison.ipynb
  diagnostics/model_contract_debug/20_mentor_vs_pipeline_dataset_comparison.md
  diagnostics/model_contract_debug/contract_comparison_labeled_summary.csv
  diagnostics/model_contract_debug/contract_comparison_unlabeled_summary.csv
  diagnostics/model_contract_debug/contract_prediction_agreement.csv
  diagnostics/model_contract_debug/confusion_<dataset>_<model>_<contract>.csv

Run from repo root with the thesis env Python.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score
from sklearn.preprocessing import StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "diagnostics" / "model_contract_debug"
NOTEBOOK_PATH = REPO_ROOT / "nb" / "mentor_vs_pipeline_contract_comparison.ipynb"
REPORT_PATH = OUT_DIR / "20_mentor_vs_pipeline_dataset_comparison.md"
LABELED_SUMMARY_PATH = OUT_DIR / "contract_comparison_labeled_summary.csv"
UNLABELED_SUMMARY_PATH = OUT_DIR / "contract_comparison_unlabeled_summary.csv"
AGREEMENT_PATH = OUT_DIR / "contract_prediction_agreement.csv"
CANDIDATE_PATH = OUT_DIR / "contract_comparison_unlabeled_candidates.csv"

WINDOW_SIZE = 200
STRIDE = 100
UNIT_FACTOR = 0.00980665
MAX_UNLABELED_DATASETS = 5
MAX_UNLABELED_FILE_BYTES = 65 * 1024 * 1024
PRIMARY_PAIRINGS = [
    ("current_pipeline_contract", "legacy_mentor_contract"),
    ("current_pipeline_contract", "clean_local_scaled_contract"),
    ("legacy_mentor_contract", "clean_local_scaled_contract"),
]

CLASS_NAMES = [
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
CLASS_TO_IDX = {name: idx for idx, name in enumerate(CLASS_NAMES)}
IDX_TO_CLASS = {idx: name for name, idx in CLASS_TO_IDX.items()}

LABEL_COLUMNS = [
    "activity",
    "Activity",
    "label",
    "Label",
    "class",
    "Class",
    "target",
    "Target",
    "y",
]
FEATURE_SETS = [
    ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"],
    ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"],
]


@dataclass(frozen=True)
class ModelSpec:
    key: str
    path: Path
    role: str


@dataclass(frozen=True)
class ContractSpec:
    name: str
    model_key: str
    scaler: str
    layout: str
    section: str
    description: str


@dataclass
class DatasetBundle:
    name: str
    path: Path
    kind: str
    df: pd.DataFrame
    feature_cols: List[str]
    label_col: Optional[str]
    unit_summary: Dict[str, Any]


@dataclass
class PredictionBundle:
    dataset: str
    contract: str
    model_key: str
    model_path: str
    y_pred: np.ndarray
    confidence: np.ndarray
    probabilities: np.ndarray
    labels: Optional[np.ndarray]


MODEL_SPECS = [
    ModelSpec(
        "pretrained_fine_tuned",
        REPO_ROOT / "models" / "pretrained" / "fine_tuned_model_1dcnnbilstm.keras",
        "deployed_default",
    ),
    ModelSpec(
        "pretrained_garmin_finetuned",
        REPO_ROOT / "models" / "pretrained" / "garmin_finetuned_v1_20260504.keras",
        "local_scaled_candidate",
    ),
    ModelSpec(
        "pretrained_finetune_best",
        REPO_ROOT / "models" / "pretrained" / "_finetune_best.keras",
        "local_scaled_candidate",
    ),
    ModelSpec(
        "sixth_may_fine_tuned",
        REPO_ROOT / "6th may" / "models" / "fine_tuned_model_1dcnnbilstm.keras",
        "mentor_folder_copy",
    ),
    ModelSpec(
        "sixth_may_cnnbilstm",
        REPO_ROOT / "6th may" / "models" / "model_wrist_acc_gyro_cnnbilstm.keras",
        "mentor_base_cnnbilstm",
    ),
    ModelSpec(
        "sixth_may_cnnlstm",
        REPO_ROOT / "6th may" / "models" / "model_wrist_acc_gyro_cnnlstm.keras",
        "mentor_base_cnnlstm",
    ),
]

PRIMARY_CONTRACTS = [
    ContractSpec(
        "current_pipeline_contract",
        "pretrained_fine_tuned",
        "none",
        "normal_rowwise",
        "primary",
        "Production default: physical units, no StandardScaler, normal time-by-channel windows.",
    ),
    ContractSpec(
        "current_plus_scaler",
        "pretrained_fine_tuned",
        "standard_full_dataset",
        "normal_rowwise",
        "primary",
        "Current deployed model with mentor full-dataframe StandardScaler but production row-wise layout.",
    ),
    ContractSpec(
        "legacy_mentor_contract",
        "pretrained_fine_tuned",
        "standard_full_dataset",
        "legacy_mentor_tensor_layout",
        "primary",
        "Mentor notebook contract: full-dataframe StandardScaler plus literal channel-major reshape.",
    ),
    ContractSpec(
        "clean_local_scaled_contract",
        "pretrained_garmin_finetuned",
        "standard_full_dataset",
        "normal_rowwise",
        "primary",
        "Local Garmin fine-tuned candidate with scaled normal row-wise windows.",
    ),
    ContractSpec(
        "local_model_with_mentor_layout",
        "pretrained_garmin_finetuned",
        "standard_full_dataset",
        "legacy_mentor_tensor_layout",
        "primary",
        "Local Garmin fine-tuned candidate forced through the mentor literal layout.",
    ),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonish(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def md_table(rows: List[Dict[str, Any]], columns: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        vals = []
        for col in columns:
            val = row.get(col, "")
            if isinstance(val, float):
                text = f"{val:.6f}"
            elif isinstance(val, (dict, list, tuple)):
                text = json.dumps(val, ensure_ascii=False, sort_keys=True)
            else:
                text = str(val)
            text = text.replace("\n", "<br>").replace("|", "\\|")
            vals.append(text)
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out) + "\n"


def normalize_label(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[\s\-/]+", "_", text)
    text = re.sub(r"[^a-z0-9_]+", "", text)
    aliases = {
        "ear_rubbing": "ear_rubbing",
        "ear_rubbing_scratching": "ear_rubbing",
        "ear_scratching": "ear_rubbing",
        "forehead_rubbing": "forehead_rubbing",
        "forehead_rubbing_scratching": "forehead_rubbing",
        "forehead_scratching": "forehead_rubbing",
        "hair_pulling": "hair_pulling",
        "hand_scratching": "hand_scratching",
        "hand_rubbing": "hand_scratching",
        "hand_rubbing_scratching": "hand_scratching",
        "hand_tapping": "hand_tapping",
        "knuckle_cracking": "knuckles_cracking",
        "knuckles_cracking": "knuckles_cracking",
        "nail_biting": "nail_biting",
        "nape_rubbing": "nape_rubbing",
        "nape_rubbing_scratching": "nape_rubbing",
        "nape_scratching": "nape_rubbing",
        "idle_sitting": "sitting",
        "sitting": "sitting",
        "smoking": "smoking",
        "idle_standing": "standing",
        "standing": "standing",
    }
    return aliases.get(text, text)


def mode_label(values: Iterable[Any]) -> str:
    counts = Counter(normalize_label(v) for v in values)
    if not counts:
        raise ValueError("Cannot compute mode of empty label window")
    return counts.most_common(1)[0][0]


def find_feature_cols(columns: Iterable[str]) -> Optional[List[str]]:
    colset = set(columns)
    for feature_cols in FEATURE_SETS:
        if all(c in colset for c in feature_cols):
            return list(feature_cols)
    return None


def find_label_col(columns: Iterable[str]) -> Optional[str]:
    colset = set(columns)
    for col in LABEL_COLUMNS:
        if col in colset:
            return col
    return None


def apply_unit_harmonization(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    out = df.copy()
    accel_cols = feature_cols[:3]
    gyro_cols = feature_cols[3:]
    out[feature_cols] = out[feature_cols].apply(pd.to_numeric, errors="coerce").ffill().bfill()
    accel_values = out[accel_cols].to_numpy(dtype=np.float64)
    max_abs = float(np.nanmax(np.abs(accel_values))) if accel_values.size else math.nan
    converted = False
    detected_unit = "unknown"
    if np.isfinite(max_abs) and max_abs > 100.0:
        out[accel_cols] = out[accel_cols] * UNIT_FACTOR
        converted = True
        detected_unit = "milliG"
    elif np.isfinite(max_abs) and max_abs < 50.0:
        detected_unit = "m/s^2"
    out[gyro_cols] = out[gyro_cols].apply(pd.to_numeric, errors="coerce").ffill().bfill()
    return out, {
        "accelerometer_max_abs_before": max_abs,
        "accelerometer_detected_unit": detected_unit,
        "accelerometer_conversion_applied": converted,
        "accelerometer_conversion_factor": UNIT_FACTOR if converted else None,
        "gyroscope_unit_assumption": "unchanged, deg/s-style",
    }


def load_dataset(path: Path, name: str, kind: str) -> DatasetBundle:
    df_raw = pd.read_csv(path)
    feature_cols = find_feature_cols(df_raw.columns)
    if feature_cols is None:
        raise ValueError(f"No six-channel feature set found in {path}")
    label_col = find_label_col(df_raw.columns)
    if kind == "labeled" and label_col is None:
        raise ValueError(f"Labeled dataset has no label column: {path}")
    if kind == "unlabeled" and label_col is not None:
        raise ValueError(f"Unlabeled dataset unexpectedly has label column {label_col}: {path}")
    df, unit_summary = apply_unit_harmonization(df_raw, feature_cols)
    return DatasetBundle(name, path, kind, df, feature_cols, label_col, unit_summary)


def build_starts(n_rows: int) -> np.ndarray:
    if n_rows < WINDOW_SIZE:
        return np.array([], dtype=np.int64)
    # Common valid-window starts for all contracts. This is production-compatible
    # and matches the mentor loop except for exact-end edge cases.
    return np.arange(0, n_rows - WINDOW_SIZE + 1, STRIDE, dtype=np.int64)


def prepare_values(bundle: DatasetBundle, scaler: str) -> np.ndarray:
    values = bundle.df[bundle.feature_cols].to_numpy(dtype=np.float32)
    if scaler == "none":
        return values
    if scaler == "standard_full_dataset":
        return StandardScaler().fit_transform(values.astype(np.float64)).astype(np.float32)
    raise ValueError(f"Unknown scaler mode: {scaler}")


def build_windows_from_values(values: np.ndarray, starts: np.ndarray, layout: str) -> np.ndarray:
    n_windows = len(starts)
    if n_windows == 0:
        return np.zeros((0, WINDOW_SIZE, 6), dtype=np.float32)
    if layout == "normal_rowwise" or layout == "transpose_safe":
        X = np.empty((n_windows, WINDOW_SIZE, 6), dtype=np.float32)
        for idx, start in enumerate(starts):
            X[idx] = values[start : start + WINDOW_SIZE]
        if layout == "transpose_safe":
            # Deliberate sanity path: transpose of six channel vectors should
            # equal the row-wise assignment above.
            X2 = np.empty_like(X)
            for idx, start in enumerate(starts):
                channel_windows = [values[start : start + WINDOW_SIZE, c] for c in range(6)]
                X2[idx] = np.asarray(channel_windows, dtype=np.float32).T
            if not np.allclose(X, X2):
                raise AssertionError("transpose_safe does not match normal_rowwise")
        return X
    if layout == "legacy_mentor_tensor_layout":
        windows = []
        for start in starts:
            channel_windows = [values[start : start + WINDOW_SIZE, c] for c in range(6)]
            windows.append(channel_windows)
        return np.asarray(windows, dtype=np.float32).reshape(-1, WINDOW_SIZE, 6)
    raise ValueError(f"Unknown layout: {layout}")


def build_labels(bundle: DatasetBundle, starts: np.ndarray) -> Optional[np.ndarray]:
    if bundle.label_col is None:
        return None
    labels_raw = bundle.df[bundle.label_col].to_numpy()
    labels = []
    for start in starts:
        label = mode_label(labels_raw[start : start + WINDOW_SIZE])
        if label not in CLASS_TO_IDX:
            raise ValueError(f"Unknown label {label!r} in {bundle.path}")
        labels.append(CLASS_TO_IDX[label])
    return np.asarray(labels, dtype=np.int32)


def load_compatible_models() -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    import tensorflow as tf

    models: Dict[str, Any] = {}
    rows: List[Dict[str, Any]] = []
    for spec in MODEL_SPECS:
        row: Dict[str, Any] = {
            "model_key": spec.key,
            "path": rel(spec.path),
            "role": spec.role,
            "exists": spec.path.exists(),
            "loaded": False,
            "compatible": False,
            "skip_reason": "",
        }
        if not spec.path.exists():
            row["skip_reason"] = "missing"
            rows.append(row)
            continue
        try:
            model = tf.keras.models.load_model(spec.path, compile=False)
            input_shape = model.input_shape[0] if isinstance(model.input_shape, list) else model.input_shape
            output_shape = model.output_shape[0] if isinstance(model.output_shape, list) else model.output_shape
            row.update(
                {
                    "loaded": True,
                    "input_shape": list(input_shape),
                    "output_shape": list(output_shape),
                    "parameters": int(model.count_params()),
                    "sha256": file_sha256(spec.path),
                }
            )
            rank = len(input_shape)
            compatible = (
                output_shape[-1] == 11
                and ((rank == 3 and input_shape[1] == 200 and input_shape[2] == 6)
                     or (rank == 4 and input_shape[1] == 200 and input_shape[2] == 6))
            )
            if compatible:
                models[spec.key] = model
                row["compatible"] = True
            else:
                row["skip_reason"] = "not 6-channel 200-step 11-class input/output"
        except Exception as exc:  # pragma: no cover - diagnostic robustness
            row["skip_reason"] = f"load failed: {exc}"
        rows.append(row)
    return models, rows


def adapt_input(model: Any, X: np.ndarray) -> np.ndarray:
    input_shape = model.input_shape[0] if isinstance(model.input_shape, list) else model.input_shape
    rank = len(input_shape)
    if rank == 3:
        return X
    if rank == 4:
        return X[..., np.newaxis]
    raise ValueError(f"Unsupported input rank for model: {input_shape}")


def predict_model(model: Any, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    probs = model.predict(adapt_input(model, X), verbose=0, batch_size=256)
    y_pred = probs.argmax(axis=1).astype(np.int32)
    conf = probs.max(axis=1).astype(np.float64)
    return y_pred, conf, probs.astype(np.float64)


def distribution(indices: np.ndarray) -> Dict[str, int]:
    counts = Counter(IDX_TO_CLASS[int(i)] for i in indices)
    return {name: int(counts[name]) for name in CLASS_NAMES if counts.get(name, 0) > 0}


def correct_by_class(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for idx, name in enumerate(CLASS_NAMES):
        out[name] = int(((y_true == idx) & (y_pred == idx)).sum())
    return out


def per_class_recall(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    recalls = recall_score(
        y_true,
        y_pred,
        labels=list(range(len(CLASS_NAMES))),
        average=None,
        zero_division=0,
    )
    return {name: float(recalls[idx]) for idx, name in enumerate(CLASS_NAMES)}


def confidence_stats(probs: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    conf = probs.max(axis=1) if len(probs) else np.array([], dtype=np.float64)
    entropy = -np.sum(np.clip(probs, 1e-12, 1.0) * np.log(np.clip(probs, 1e-12, 1.0)), axis=1) if len(probs) else np.array([])
    pred_dist = distribution(y_pred)
    dominant_class = max(pred_dist, key=pred_dist.get) if pred_dist else ""
    dominant_count = pred_dist.get(dominant_class, 0) if dominant_class else 0
    transition_flip_rate = float(np.mean(y_pred[1:] != y_pred[:-1])) if len(y_pred) > 1 else 0.0
    return {
        "mean_confidence": float(np.mean(conf)) if len(conf) else math.nan,
        "median_confidence": float(np.median(conf)) if len(conf) else math.nan,
        "entropy_mean": float(np.mean(entropy)) if len(entropy) else math.nan,
        "n_predicted_classes": int(len(pred_dist)),
        "dominant_class": dominant_class,
        "dominant_class_percentage": float(dominant_count / len(y_pred)) if len(y_pred) else math.nan,
        "prediction_distribution": pred_dist,
        "transition_flip_rate": transition_flip_rate,
    }


def save_confusion(dataset: str, model_key: str, contract: str, y_true: np.ndarray, y_pred: np.ndarray) -> Path:
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(CLASS_NAMES))))
    df_cm = pd.DataFrame(cm, index=CLASS_NAMES, columns=CLASS_NAMES)
    path = OUT_DIR / f"confusion_{safe_name(dataset)}_{safe_name(model_key)}_{safe_name(contract)}.csv"
    df_cm.to_csv(path)
    return path


def discover_unlabeled_candidates() -> Tuple[List[Path], List[Dict[str, Any]]]:
    roots = [REPO_ROOT / "data" / "raw", REPO_ROOT / "data" / "processed", REPO_ROOT / "outputs", REPO_ROOT / "artifacts"]
    candidates: List[Dict[str, Any]] = []
    seen_names: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            try:
                size = path.stat().st_size
                if size > MAX_UNLABELED_FILE_BYTES:
                    continue
                cols = list(pd.read_csv(path, nrows=0).columns)
            except Exception:
                continue
            feature_cols = find_feature_cols(cols)
            label_col = find_label_col(cols)
            if feature_cols is None or label_col is not None:
                continue
            rel_path = rel(path)
            # Avoid duplicate session_fused files in artifacts/outputs when a
            # canonical data/processed file exists.
            stem_key = path.name
            score = 0
            if "data\\processed" in rel_path or "data/processed" in rel_path:
                score += 100
            if "data\\raw" in rel_path or "data/raw" in rel_path:
                score += 90
            if "fused" in path.name.lower() or "sensor_fused" in path.name.lower():
                score += 20
            if "50hz" in path.name.lower():
                score += 15
            if "production" in rel_path.lower() or "unlabeled" in rel_path.lower():
                score += 10
            if "pytest" in rel_path.lower():
                score -= 100
            score -= int(size / (1024 * 1024))
            candidates.append(
                {
                    "path": path,
                    "rel_path": rel_path,
                    "feature_cols": feature_cols,
                    "size_bytes": int(size),
                    "score": int(score),
                    "selected": False,
                    "duplicate_name_key": stem_key,
                }
            )
    candidates.sort(key=lambda r: (-int(r["score"]), int(r["size_bytes"]), str(r["rel_path"])))
    selected: List[Path] = []
    selected_session_tokens: set[str] = set()
    for row in candidates:
        if len(selected) >= MAX_UNLABELED_DATASETS:
            break
        path = Path(row["path"])
        token = path.stem.replace("sensor_fused_50Hz", path.parent.parent.name if path.parent.name == "ingestion" else path.stem)
        if token in selected_session_tokens:
            continue
        selected.append(path)
        selected_session_tokens.add(token)
        row["selected"] = True
    candidate_rows = []
    for row in candidates[:80]:
        row_copy = dict(row)
        row_copy["path"] = rel(Path(row_copy["path"]))
        candidate_rows.append(row_copy)
    return selected, candidate_rows


def build_contracts_for_models(models: Dict[str, Any]) -> List[ContractSpec]:
    contracts = [c for c in PRIMARY_CONTRACTS if c.model_key in models]
    for spec in MODEL_SPECS:
        if spec.key not in models:
            continue
        for scaler, scaler_label in [("none", "raw"), ("standard_full_dataset", "scaled")]:
            contracts.append(
                ContractSpec(
                    f"model_sweep_{spec.key}_{scaler_label}_normal",
                    spec.key,
                    scaler,
                    "normal_rowwise",
                    "requested_model_sweep",
                    f"Requested model sweep: {spec.key}, scaler={scaler}, layout=normal_rowwise.",
                )
            )
        contracts.append(
            ContractSpec(
                f"model_sweep_{spec.key}_scaled_mentor_layout",
                spec.key,
                "standard_full_dataset",
                "legacy_mentor_tensor_layout",
                "requested_model_sweep",
                f"Requested model sweep: {spec.key}, scaler=standard_full_dataset, layout=legacy_mentor_tensor_layout.",
            )
        )
    # Stable de-duplication by (name, model, scaler, layout).
    seen = set()
    out = []
    for c in contracts:
        key = (c.name, c.model_key, c.scaler, c.layout)
        if key not in seen:
            out.append(c)
            seen.add(key)
    return out


def evaluate_dataset(
    bundle: DatasetBundle,
    contracts: List[ContractSpec],
    models: Dict[str, Any],
    model_rows_by_key: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, PredictionBundle], Dict[str, Any]]:
    starts = build_starts(len(bundle.df))
    labels = build_labels(bundle, starts) if bundle.kind == "labeled" else None
    values_cache: Dict[str, np.ndarray] = {}
    windows_cache: Dict[Tuple[str, str], np.ndarray] = {}
    summary_rows: List[Dict[str, Any]] = []
    predictions: Dict[str, PredictionBundle] = {}
    transpose_safe_ok = False
    if len(starts):
        scaled = prepare_values(bundle, "standard_full_dataset")
        normal = build_windows_from_values(scaled, starts[: min(len(starts), 5)], "normal_rowwise")
        safe = build_windows_from_values(scaled, starts[: min(len(starts), 5)], "transpose_safe")
        transpose_safe_ok = bool(np.allclose(normal, safe))

    for contract in contracts:
        model = models.get(contract.model_key)
        if model is None:
            continue
        values = values_cache.get(contract.scaler)
        if values is None:
            values = prepare_values(bundle, contract.scaler)
            values_cache[contract.scaler] = values
        window_key = (contract.scaler, contract.layout)
        X = windows_cache.get(window_key)
        if X is None:
            X = build_windows_from_values(values, starts, contract.layout)
            windows_cache[window_key] = X
        if len(X) == 0:
            continue
        y_pred, conf, probs = predict_model(model, X)
        pred_bundle = PredictionBundle(
            dataset=bundle.name,
            contract=contract.name,
            model_key=contract.model_key,
            model_path=model_rows_by_key[contract.model_key].get("path", ""),
            y_pred=y_pred,
            confidence=conf,
            probabilities=probs,
            labels=labels,
        )
        predictions[contract.name] = pred_bundle
        stats = confidence_stats(probs, y_pred)
        row: Dict[str, Any] = {
            "dataset": bundle.name,
            "dataset_path": rel(bundle.path),
            "dataset_kind": bundle.kind,
            "section": contract.section,
            "contract": contract.name,
            "model": contract.model_key,
            "model_path": model_rows_by_key[contract.model_key].get("path", ""),
            "scaler": contract.scaler,
            "scaler_yes_no": "yes" if contract.scaler != "none" else "no",
            "layout": contract.layout,
            "n_rows": int(len(bundle.df)),
            "n_windows": int(len(X)),
            "feature_cols": bundle.feature_cols,
            "unit_summary": bundle.unit_summary,
            "transpose_safe_equals_normal": transpose_safe_ok,
            **stats,
        }
        if labels is not None:
            row.update(
                {
                    "accuracy": float(accuracy_score(labels, y_pred)),
                    "macro_F1": float(
                        f1_score(labels, y_pred, labels=list(range(len(CLASS_NAMES))), average="macro", zero_division=0)
                    ),
                    "weighted_F1": float(
                        f1_score(labels, y_pred, labels=list(range(len(CLASS_NAMES))), average="weighted", zero_division=0)
                    ),
                    "true_distribution": distribution(labels),
                    "correct_by_class": correct_by_class(labels, y_pred),
                    "per_class_recall": per_class_recall(labels, y_pred),
                }
            )
            cm_path = save_confusion(bundle.name, contract.model_key, contract.name, labels, y_pred)
            row["confusion_matrix_csv"] = rel(cm_path)
        summary_rows.append(row)
    return summary_rows, predictions, {
        "n_windows": int(len(starts)),
        "n_rows": int(len(bundle.df)),
        "feature_cols": bundle.feature_cols,
        "label_col": bundle.label_col,
        "unit_summary": bundle.unit_summary,
        "transpose_safe_equals_normal": transpose_safe_ok,
    }


def disagreement_pairs(a_pred: np.ndarray, b_pred: np.ndarray, top_n: int = 8) -> Dict[str, int]:
    mask = a_pred != b_pred
    pairs = Counter(
        f"{IDX_TO_CLASS[int(a)]} -> {IDX_TO_CLASS[int(b)]}" for a, b in zip(a_pred[mask], b_pred[mask])
    )
    return dict(pairs.most_common(top_n))


def agreement_rows_for_dataset(dataset: str, predictions: Dict[str, PredictionBundle]) -> List[Dict[str, Any]]:
    rows = []
    for left, right in PRIMARY_PAIRINGS:
        if left not in predictions or right not in predictions:
            continue
        a = predictions[left]
        b = predictions[right]
        n = min(len(a.y_pred), len(b.y_pred))
        if n == 0:
            continue
        agree = a.y_pred[:n] == b.y_pred[:n]
        rows.append(
            {
                "dataset": dataset,
                "left_contract": left,
                "left_model": a.model_key,
                "right_contract": right,
                "right_model": b.model_key,
                "n_comparable_windows": int(n),
                "agreement_percentage": float(np.mean(agree)),
                "top_disagreement_pairs": disagreement_pairs(a.y_pred[:n], b.y_pred[:n]),
                "mean_left_confidence": float(np.mean(a.confidence[:n])),
                "mean_right_confidence": float(np.mean(b.confidence[:n])),
                "mean_confidence_difference_left_minus_right": float(np.mean(a.confidence[:n] - b.confidence[:n])),
                "mean_abs_confidence_difference": float(np.mean(np.abs(a.confidence[:n] - b.confidence[:n]))),
            }
        )
    return rows


def add_unlabeled_reference_agreements(
    unlabeled_rows: List[Dict[str, Any]],
    predictions_by_dataset: Dict[str, Dict[str, PredictionBundle]],
) -> None:
    for row in unlabeled_rows:
        dataset = row["dataset"]
        contract = row["contract"]
        preds = predictions_by_dataset.get(dataset, {})
        cur = preds.get(contract)
        if cur is None:
            continue
        for ref_name in ("legacy_mentor_contract", "clean_local_scaled_contract"):
            ref = preds.get(ref_name)
            col = f"agreement_with_{ref_name}"
            if ref is None:
                row[col] = ""
                continue
            n = min(len(cur.y_pred), len(ref.y_pred))
            row[col] = float(np.mean(cur.y_pred[:n] == ref.y_pred[:n])) if n else ""


def dataframe_for_csv(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    serializable_rows = []
    for row in rows:
        out = {}
        for key, value in row.items():
            if isinstance(value, (dict, list, tuple)):
                out[key] = json.dumps(value, ensure_ascii=False, sort_keys=True)
            else:
                out[key] = value
        serializable_rows.append(out)
    return pd.DataFrame(serializable_rows)


def markdown_summary(
    labeled_df: pd.DataFrame,
    unlabeled_df: pd.DataFrame,
    agreement_df: pd.DataFrame,
    model_rows: List[Dict[str, Any]],
    dataset_meta: Dict[str, Dict[str, Any]],
    candidate_rows: List[Dict[str, Any]],
) -> str:
    def top_primary(df: pd.DataFrame, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        if df.empty:
            return []
        sub = df[df["section"] == "primary"].copy()
        if dataset is not None:
            sub = sub[sub["dataset"] == dataset]
        cols = [
            "dataset",
            "contract",
            "model",
            "scaler",
            "layout",
            "n_windows",
            "accuracy",
            "macro_F1",
            "weighted_F1",
            "mean_confidence",
            "n_predicted_classes",
            "dominant_class",
            "dominant_class_percentage",
        ]
        return sub[[c for c in cols if c in sub.columns]].to_dict("records")

    def unlabeled_primary() -> List[Dict[str, Any]]:
        if unlabeled_df.empty:
            return []
        sub = unlabeled_df[unlabeled_df["section"] == "primary"].copy()
        cols = [
            "dataset",
            "contract",
            "model",
            "scaler",
            "layout",
            "n_windows",
            "mean_confidence",
            "median_confidence",
            "entropy_mean",
            "n_predicted_classes",
            "dominant_class",
            "dominant_class_percentage",
            "transition_flip_rate",
            "agreement_with_legacy_mentor_contract",
            "agreement_with_clean_local_scaled_contract",
        ]
        return sub[[c for c in cols if c in sub.columns]].to_dict("records")

    model_table_rows = [
        {
            "model_key": r.get("model_key"),
            "path": r.get("path"),
            "role": r.get("role"),
            "compatible": r.get("compatible"),
            "input_shape": r.get("input_shape", ""),
            "output_shape": r.get("output_shape", ""),
            "skip_reason": r.get("skip_reason", ""),
        }
        for r in model_rows
    ]

    dataset_rows = [
        {
            "dataset": name,
            "rows": meta.get("n_rows"),
            "windows": meta.get("n_windows"),
            "features": meta.get("feature_cols"),
            "label_col": meta.get("label_col"),
            "unit_summary": meta.get("unit_summary"),
            "transpose_safe_equals_normal": meta.get("transpose_safe_equals_normal"),
        }
        for name, meta in dataset_meta.items()
    ]

    candidate_table = [
        {
            "selected": row.get("selected"),
            "path": row.get("path"),
            "size_MB": round(int(row.get("size_bytes", 0)) / (1024 * 1024), 2),
            "feature_cols": row.get("feature_cols"),
            "score": row.get("score"),
        }
        for row in candidate_rows[:25]
    ]

    all_users_rows = top_primary(labeled_df, "all_users")
    user7_rows = top_primary(labeled_df, "user7")
    agreement_rows = (
        agreement_df[
            [
                "dataset",
                "left_contract",
                "right_contract",
                "agreement_percentage",
                "top_disagreement_pairs",
                "mean_confidence_difference_left_minus_right",
                "mean_abs_confidence_difference",
            ]
        ].to_dict("records")
        if not agreement_df.empty
        else []
    )

    best_labeled = []
    if not labeled_df.empty:
        primary = labeled_df[labeled_df["section"] == "primary"].copy()
        for dataset, group in primary.groupby("dataset"):
            best = group.sort_values("accuracy", ascending=False).iloc[0]
            best_labeled.append(
                {
                    "dataset": dataset,
                    "best_primary_contract": best["contract"],
                    "accuracy": best["accuracy"],
                    "macro_F1": best["macro_F1"],
                    "note": (
                        "All-users may be close to the mentor training representation"
                        if dataset == "all_users"
                        else "External/self-recorded evaluation"
                    ),
                }
            )

    parts = [
        "# 20 Mentor vs Pipeline Dataset Comparison\n",
        "## Short Summary\n",
        (
            "This diagnostic compares the paper/current production contract against the hidden mentor notebook contract "
            "on labeled and unlabeled datasets. The main result remains contract-specific: the deployed "
            "`fine_tuned_model_1dcnnbilstm.keras` is only strong on `all_users` when using the explicitly named "
            "`legacy_mentor_tensor_layout` plus full-dataframe `StandardScaler`. That does not automatically make it "
            "the best deployable contract, because `all_users` may be close to the mentor training representation, "
            "the scaler leaks validation distribution, and the paper does not document the hidden scaler or channel-major reshape.\n"
        ),
        "Best primary labeled result per dataset:\n",
        md_table(best_labeled, ["dataset", "best_primary_contract", "accuracy", "macro_F1", "note"]),
        "## What Was Tested\n",
        "Primary deployable contracts:\n",
        md_table(
            [
                {
                    "contract": c.name,
                    "model": c.model_key,
                    "scaler": c.scaler,
                    "layout": c.layout,
                    "description": c.description,
                }
                for c in PRIMARY_CONTRACTS
            ],
            ["contract", "model", "scaler", "layout", "description"],
        ),
        "Compatible requested models:\n",
        md_table(model_table_rows, ["model_key", "path", "role", "compatible", "input_shape", "output_shape", "skip_reason"]),
        "`6th may/models/model_all.keras` was intentionally not tested in the primary or sweep tables because it expects the ADAMSense-style 18-channel input and is not compatible with the six-channel production pipeline contract.\n",
        "Datasets and preprocessing metadata:\n",
        md_table(dataset_rows, ["dataset", "rows", "windows", "features", "label_col", "unit_summary", "transpose_safe_equals_normal"]),
        "Unlabeled CSV discovery candidates, selected rows included in scoring:\n",
        md_table(candidate_table, ["selected", "path", "size_MB", "feature_cols", "score"]),
        "## Labeled Data Results\n",
        "Primary-contract results for `data/all_users_data_labeled.csv`:\n",
        md_table(
            all_users_rows,
            [
                "dataset",
                "contract",
                "model",
                "scaler",
                "layout",
                "n_windows",
                "accuracy",
                "macro_F1",
                "weighted_F1",
                "mean_confidence",
                "n_predicted_classes",
                "dominant_class",
                "dominant_class_percentage",
            ],
        ),
        "## User 7 External Evaluation Results\n",
        "Primary-contract results for `data/raw/2026-05-05-15-11-15_labeled_50Hz_user7.csv`:\n",
        md_table(
            user7_rows,
            [
                "dataset",
                "contract",
                "model",
                "scaler",
                "layout",
                "n_windows",
                "accuracy",
                "macro_F1",
                "weighted_F1",
                "mean_confidence",
                "n_predicted_classes",
                "dominant_class",
                "dominant_class_percentage",
            ],
        ),
        (
            "User 7 is an external/self-recorded labeled evaluation. Its result should carry more weight for deployment "
            "risk than `all_users` when judging generalization, even though it is smaller and may have its own collection differences.\n"
        ),
        "## Unlabeled / Production Confidence Results\n",
        "No accuracy is calculated for unlabeled data. These rows report confidence, entropy, class spread, temporal flip rate, and agreement with reference contracts:\n",
        md_table(
            unlabeled_primary(),
            [
                "dataset",
                "contract",
                "model",
                "scaler",
                "layout",
                "n_windows",
                "mean_confidence",
                "median_confidence",
                "entropy_mean",
                "n_predicted_classes",
                "dominant_class",
                "dominant_class_percentage",
                "transition_flip_rate",
                "agreement_with_legacy_mentor_contract",
                "agreement_with_clean_local_scaled_contract",
            ],
        ),
        "## Contract Agreement / Disagreement\n",
        md_table(
            agreement_rows,
            [
                "dataset",
                "left_contract",
                "right_contract",
                "agreement_percentage",
                "top_disagreement_pairs",
                "mean_confidence_difference_left_minus_right",
                "mean_abs_confidence_difference",
            ],
        ),
        "## What Is Right In Production Pipeline\n",
        "- It matches the paper-level physical-unit path: Garmin accelerometer milliG is converted to m/s^2 when needed, gyroscope is unchanged, sampling target is 50 Hz, window size is 200, and stride is 100.\n"
        "- It creates normal row-wise `(time, channel)` tensors, which is the standard 1D time-series representation.\n"
        "- It has a fixed canonical 11-class mapping and does not silently fit a scaler on the current inference batch by default.\n",
        "## What Is Wrong In Production Pipeline\n",
        "- The active model pointer currently targets `fine_tuned_model_1dcnnbilstm.keras`, but that checkpoint behaves as if it expects the mentor notebook contract, not the production tensor contract.\n"
        "- Therefore, production is internally coherent relative to the paper, but incoherent relative to the deployed checkpoint.\n"
        "- If the goal is to deploy this specific checkpoint, the production tensor builder/scaler contract does not match it.\n",
        "## What Is Right In Mentor Notebook Contract\n",
        "- It reproduces the high `all_users` accuracy for `fine_tuned_model_1dcnnbilstm.keras` when implemented literally as `legacy_mentor_tensor_layout` plus full-dataframe `StandardScaler`.\n"
        "- It uses the same six wrist accelerometer/gyroscope channels and the same 200/100 window geometry.\n",
        "## What Is Wrong / Risky In Mentor Notebook Contract\n",
        "- The hidden `StandardScaler.fit_transform` on the full dataframe is not documented in the paper and leaks validation/test feature statistics when used before splitting.\n"
        "- The literal channel-major reshape is not normal row-wise time-series layout. If used, it must be named explicitly as `legacy_mentor_tensor_layout`; pretending it is normal `(time, channel)` would hide the root cause.\n"
        "- Mentor inference fits a fresh scaler on the inference CSV, making predictions batch-dependent. Adding/removing rows can change all standardized windows.\n"
        "- Paper results report 5-fold CV, while the inspected notebooks use holdout splits after scaling/windowing.\n",
        "## Pros / Cons Of Each Deployable Choice\n",
        md_table(
            [
                {
                    "choice": "Keep current production contract and current model",
                    "pros": "Paper-aligned preprocessing; normal tensor layout; clean production semantics.",
                    "cons": "Known low accuracy/collapse with current checkpoint.",
                },
                {
                    "choice": "Patch production to legacy_mentor_tensor_layout for current checkpoint",
                    "pros": "Recovers high all_users accuracy for this checkpoint.",
                    "cons": "Uses undocumented scaler and nonstandard tensor layout; batch-dependent if scaler is fit per inference file; may not generalize to User 7/production.",
                },
                {
                    "choice": "Use local Garmin fine-tuned model with scaled normal layout",
                    "pros": "Normal row-wise layout; less hidden tensor behavior; often broader class usage.",
                    "cons": "Requires explicit scaler contract/provenance and validation; may still underperform reported paper metric.",
                },
                {
                    "choice": "Retrain/export a model for the paper/current production contract",
                    "pros": "Best long-term MLOps contract: normal tensors, physical units, saved provenance, clean train/val split.",
                    "cons": "Requires retraining and mentor/training-data confirmation; not a diagnostic-only change.",
                },
            ],
            ["choice", "pros", "cons"],
        ),
        "## Recommended Solution\n",
        (
            "Do not silently rename the mentor layout as normal time-series preprocessing. The safest production solution is to "
            "train or obtain a checkpoint whose documented input contract is the paper/current production contract: six wrist "
            "features in physical units, no hidden per-file scaler, normal row-wise `(time, channel)` windows, fixed class mapping, "
            "and validation without scaler leakage. If deadlines require using `fine_tuned_model_1dcnnbilstm.keras`, add an explicit "
            "legacy compatibility mode named `legacy_mentor_tensor_layout` and document the full-dataframe StandardScaler behavior as "
            "a checkpoint-specific legacy contract, then gate it on User 7 and additional labeled external recordings before deployment.\n"
        ),
        "## Output Files\n",
        md_table(
            [
                {"file": rel(LABELED_SUMMARY_PATH), "description": "All labeled summary rows, including primary contracts and requested model sweep."},
                {"file": rel(UNLABELED_SUMMARY_PATH), "description": "All unlabeled summary rows; no accuracy fields."},
                {"file": rel(AGREEMENT_PATH), "description": "Contract prediction agreement/disagreement rows."},
                {"file": rel(CANDIDATE_PATH), "description": "Unlabeled CSV discovery candidates."},
                {"file": "diagnostics/model_contract_debug/confusion_<dataset>_<model>_<contract>.csv", "description": "Confusion matrices for labeled rows."},
                {"file": rel(NOTEBOOK_PATH), "description": "Reproducible diagnostic notebook."},
            ],
            ["file", "description"],
        ),
    ]
    return "\n".join(parts)


def write_notebook() -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    script_rel = rel(Path(__file__))
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Mentor vs Pipeline Contract Comparison\n",
                "\n",
                "Diagnostic notebook for comparing the hidden mentor notebook contract with the production pipeline contract across labeled and unlabeled datasets.\n",
                "\n",
                "This notebook is diagnostic-only: no production code changes, no retraining, and no artifact deletion.\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## Re-run The Diagnostic\n",
                "\n",
                "Run the cell below from this notebook to regenerate the CSVs, confusion matrices, and markdown report.\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from pathlib import Path\n",
                "import runpy\n",
                "\n",
                "REPO_ROOT = Path.cwd()\n",
                "if REPO_ROOT.name == 'nb':\n",
                "    REPO_ROOT = REPO_ROOT.parent\n",
                "\n",
                f"runpy.run_path(str(REPO_ROOT / {script_rel!r}), run_name='__main__')\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Inspect Generated Tables\n"],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from pathlib import Path\n",
                "import pandas as pd\n",
                "from IPython.display import Markdown, display\n",
                "\n",
                "REPO_ROOT = Path.cwd()\n",
                "if REPO_ROOT.name == 'nb':\n",
                "    REPO_ROOT = REPO_ROOT.parent\n",
                "OUT = REPO_ROOT / 'diagnostics' / 'model_contract_debug'\n",
                "\n",
                "labeled = pd.read_csv(OUT / 'contract_comparison_labeled_summary.csv')\n",
                "unlabeled = pd.read_csv(OUT / 'contract_comparison_unlabeled_summary.csv')\n",
                "agreement = pd.read_csv(OUT / 'contract_prediction_agreement.csv')\n",
                "\n",
                "display(labeled[labeled['section'].eq('primary')])\n",
                "display(unlabeled[unlabeled['section'].eq('primary')])\n",
                "display(agreement)\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Markdown Report\n"],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from pathlib import Path\n",
                "from IPython.display import Markdown, display\n",
                "\n",
                "REPO_ROOT = Path.cwd()\n",
                "if REPO_ROOT.name == 'nb':\n",
                "    REPO_ROOT = REPO_ROOT.parent\n",
                "report_path = REPO_ROOT / 'diagnostics' / 'model_contract_debug' / '20_mentor_vs_pipeline_dataset_comparison.md'\n",
                "display(Markdown(report_path.read_text(encoding='utf-8')))\n",
            ],
        },
    ]
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK_PATH.write_text(json.dumps(nb, indent=2), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_notebook()

    models, model_rows = load_compatible_models()
    model_rows_by_key = {row["model_key"]: row for row in model_rows}
    contracts = build_contracts_for_models(models)

    labeled_specs = [
        ("all_users", REPO_ROOT / "data" / "all_users_data_labeled.csv"),
        ("user7", REPO_ROOT / "data" / "raw" / "2026-05-05-15-11-15_labeled_50Hz_user7.csv"),
    ]
    selected_unlabeled, candidate_rows = discover_unlabeled_candidates()
    dataframe_for_csv(candidate_rows).to_csv(CANDIDATE_PATH, index=False)

    dataset_specs: List[Tuple[str, Path, str]] = []
    for name, path in labeled_specs:
        if path.exists():
            dataset_specs.append((name, path, "labeled"))
    for idx, path in enumerate(selected_unlabeled, 1):
        dataset_specs.append((f"unlabeled_{idx}_{safe_name(path.stem)}", path, "unlabeled"))

    labeled_rows: List[Dict[str, Any]] = []
    unlabeled_rows: List[Dict[str, Any]] = []
    agreement_rows: List[Dict[str, Any]] = []
    dataset_meta: Dict[str, Dict[str, Any]] = {}
    predictions_by_dataset: Dict[str, Dict[str, PredictionBundle]] = {}

    for dataset_name, path, kind in dataset_specs:
        print(f"Evaluating {dataset_name}: {rel(path)} [{kind}]")
        bundle = load_dataset(path, dataset_name, kind)
        rows, preds, meta = evaluate_dataset(bundle, contracts, models, model_rows_by_key)
        dataset_meta[dataset_name] = meta
        predictions_by_dataset[dataset_name] = preds
        if kind == "labeled":
            labeled_rows.extend(rows)
        else:
            unlabeled_rows.extend(rows)
        agreement_rows.extend(agreement_rows_for_dataset(dataset_name, preds))

    add_unlabeled_reference_agreements(unlabeled_rows, predictions_by_dataset)

    labeled_df = dataframe_for_csv(labeled_rows)
    unlabeled_df = dataframe_for_csv(unlabeled_rows)
    agreement_df = dataframe_for_csv(agreement_rows)
    labeled_df.to_csv(LABELED_SUMMARY_PATH, index=False)
    unlabeled_df.to_csv(UNLABELED_SUMMARY_PATH, index=False)
    agreement_df.to_csv(AGREEMENT_PATH, index=False)

    report = markdown_summary(labeled_df, unlabeled_df, agreement_df, model_rows, dataset_meta, candidate_rows)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Wrote {NOTEBOOK_PATH}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {LABELED_SUMMARY_PATH}")
    print(f"Wrote {UNLABELED_SUMMARY_PATH}")
    print(f"Wrote {AGREEMENT_PATH}")


if __name__ == "__main__":
    main()

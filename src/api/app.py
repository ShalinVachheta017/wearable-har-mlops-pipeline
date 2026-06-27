"""
HAR MLOps FastAPI Application
==============================

Full-featured REST API + Web UI for Human Activity Recognition:
  - CSV upload with automatic preprocessing & windowing
  - Real-time inference with 1D-CNN-BiLSTM model
  - 3-layer post-inference monitoring (confidence, temporal, drift)
  - Interactive dashboard with visualizations

Run:
    python -m src.api.app                 # localhost:8000
    uvicorn src.api.app:app --reload      # with auto-reload
"""

import io
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from src.components.data_ingestion import (
    DEFAULT_MERGE_TOLERANCE_MS,
    DEFAULT_TARGET_HZ,
    _create_timestamps,
    _explode_rows,
    _filter_valid_rows,
    _merge_and_resample,
    _normalize_columns,
    _parse_list_columns,
    _rename_axes,
)
from src.config import DEFAULT_MODEL_PATH as _DEFAULT_MODEL_PATH
from src.config import MODEL_D1_FINAL_DIR as _MODEL_D1_FINAL_DIR
from src.config import SCALER_CANONICAL as _SCALER_CANONICAL
from src.config import MILLIG_TO_MS2 as _MILLIG_TO_MS2
from src.config import OVERLAP as _OVERLAP
from src.config import PROJECT_ROOT as _PROJECT_ROOT
from src.config import WINDOW_SIZE as _WINDOW_SIZE
from src.utils.label_detection import LABEL_COLUMN_CANDIDATES, NON_GROUND_TRUTH_COLUMNS
from src.utils.label_mapping import get_activity_classes, get_class_to_index


# Single source of truth for monitoring thresholds â€” shared with the pipeline.
def _load_monitoring_thresholds():
    try:
        from src.utils.config_loader import load_monitoring_config

        return load_monitoring_config()
    except Exception:  # pragma: no cover â€” standalone startup without src/ on path

        class _MonCfg:  # type: ignore
            confidence_warn_threshold: float = 0.70
            uncertain_pct_threshold: float = 20.0
            uncertain_window_threshold: float = 0.50
            transition_rate_threshold: float = 35.0
            drift_zscore_threshold: float = 1.8
            dominant_class_warn_threshold: float = 85.0
            dominant_class_critical_threshold: float = 95.0
            max_baseline_age_days: int = 90

        return _MonCfg()


_MON_T = _load_monitoring_thresholds()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("har_api")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = _PROJECT_ROOT
MODEL_PATH = Path(os.environ.get("MODEL_PATH", str(_DEFAULT_MODEL_PATH)))
# Default scaler tracks SCALER_CANONICAL in src/config.py (Model D1 since
# 2026-05-26). Override via SCALER_CONFIG_PATH env var if you need to load a
# different contract (e.g. Model A rollback evidence).
SCALER_CONFIG_PATH = Path(os.environ.get("SCALER_CONFIG_PATH", str(_SCALER_CANONICAL)))
# Monitoring baseline travels with the same runtime contract folder as the
# scaler. Override via BASELINE_PATH env var for rollback scenarios.
BASELINE_PATH = Path(
    os.environ.get(
        "BASELINE_PATH",
        str(_MODEL_D1_FINAL_DIR / "garmin_train_scaled_baseline.json"),
    )
)
WINDOW_SIZE = _WINDOW_SIZE
OVERLAP = _OVERLAP
STEP_SIZE = int(WINDOW_SIZE * (1 - OVERLAP))
# Temporal smoothing of the per-window prediction stream â€” the decision stage of
# the Activity Recognition Chain (Bulling et al., 2014). Soft majority vote over
# a small neighbourhood of windows. Applied ADDITIVELY: raw predictions still
# drive monitoring and the served output; the smoothed view is reported alongside
# so the monitoring signal stays honest. Window of 3 â‰ˆ 6 s of context.
SMOOTHING_WINDOW = 3

ACTIVITY_CLASSES: Dict[int, str] = get_activity_classes()

# Possible column-name patterns for the 6 sensor channels
ACC_PATTERNS = {
    "x": ["acc_x", "ax", "ax_w", "accel_x", "accelerometer_x", "accx"],
    "y": ["acc_y", "ay", "ay_w", "accel_y", "accelerometer_y", "accy"],
    "z": ["acc_z", "az", "az_w", "accel_z", "accelerometer_z", "accz"],
}
GYRO_PATTERNS = {
    "x": ["gyro_x", "gx", "gx_w", "gyroscope_x", "gyrox"],
    "y": ["gyro_y", "gy", "gy_w", "gyroscope_y", "gyroy"],
    "z": ["gyro_z", "gz", "gz_w", "gyroscope_z", "gyroz"],
}

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_model = None
_model_info: Dict = {}
_baseline: Optional[Dict] = None
_scaler_config: Optional[Dict] = None
_start_time = datetime.now()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_model():
    """Load the Keras model (once)."""
    global _model, _model_info
    if _model is not None:
        return
    import tensorflow as tf

    tf.get_logger().setLevel("ERROR")
    if not MODEL_PATH.exists():
        logger.warning("Model file not found: %s", MODEL_PATH)
        return
    logger.info("Loading model from %s â€¦", MODEL_PATH)
    _model = tf.keras.models.load_model(str(MODEL_PATH), compile=False)
    _model_info = {
        "name": "1D-CNN-BiLSTM HAR",
        "version": "1.0.0",
        "input_shape": list(_model.input_shape[1:]),
        "output_classes": int(_model.output_shape[-1]),
        "params": int(_model.count_params()),
        "loaded_at": datetime.now().isoformat(),
    }
    # warm-up
    _model.predict(np.zeros((1, WINDOW_SIZE, 6), dtype=np.float32), verbose=0)
    logger.info("Model ready â€“ %s params", f"{_model_info['params']:,}")


def _load_baseline():
    """Load the active runtime scaled baseline JSON once."""
    global _baseline
    if _baseline is not None or not BASELINE_PATH.exists():
        return
    with open(BASELINE_PATH) as f:
        _baseline = json.load(f)
    logger.info("Baseline loaded from %s", BASELINE_PATH)


def _load_scaler_config() -> Dict:
    """Load the active Garmin train-only scaler JSON."""
    global _scaler_config
    if _scaler_config is not None:
        return _scaler_config
    if not SCALER_CONFIG_PATH.exists():
        raise RuntimeError(f"Scaler config not found: {SCALER_CONFIG_PATH}")
    cfg = json.loads(SCALER_CONFIG_PATH.read_text(encoding="utf-8"))
    mean = cfg.get("scaler_mean")
    scale = cfg.get("scaler_scale")
    if (
        not isinstance(mean, list)
        or not isinstance(scale, list)
        or len(mean) != 6
        or len(scale) != 6
    ):
        raise RuntimeError(f"Scaler config has invalid dimensions: {SCALER_CONFIG_PATH}")
    _scaler_config = cfg
    return cfg


def _detect_columns(df: pd.DataFrame) -> List[str]:
    """
    Auto-detect the 6 sensor columns from a CSV DataFrame.
    Returns [acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z].
    Raises if not all 6 are found.
    """
    lower_cols = {c.lower().strip(): c for c in df.columns}
    found = []

    for axis_set, patterns in [(ACC_PATTERNS, "acc"), (GYRO_PATTERNS, "gyro")]:
        for axis, names in axis_set.items():
            matched = None
            for name in names:
                if name in lower_cols:
                    matched = lower_cols[name]
                    break
            if matched is None:
                raise ValueError(
                    f"Could not find {patterns}_{axis} column. "
                    f"Tried: {names}. Available: {list(df.columns)}"
                )
            found.append(matched)
    return found  # length == 6


def _detect_label_column(df: pd.DataFrame) -> Optional[str]:
    """Return a ground-truth label column if the uploaded CSV contains one."""
    lower_to_original = {c.lower().strip(): c for c in df.columns}
    excluded = {c.lower().strip() for c in NON_GROUND_TRUTH_COLUMNS}
    for candidate in LABEL_COLUMN_CANDIDATES:
        key = candidate.lower().strip()
        if key in lower_to_original and key not in excluded:
            return lower_to_original[key]
    return None


async def _read_upload_csv(upload: UploadFile, role: str) -> pd.DataFrame:
    """Read an uploaded CSV file into a DataFrame with a role-specific error."""
    if upload is None:
        raise HTTPException(400, f"Missing {role} file")
    if not (upload.filename or "").lower().endswith(".csv"):
        raise HTTPException(400, f"{role} file must be a CSV file")
    try:
        contents = await upload.read()
        return pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"Failed to read {role} CSV: {e}")


def _prepare_sensor_frame(df: pd.DataFrame, sensor_type: str) -> pd.DataFrame:
    """Normalize one raw accelerometer or gyroscope CSV to true_time + Ax/Ay/Az or Gx/Gy/Gz."""
    if len(df) == 0:
        raise ValueError(f"{sensor_type} CSV is empty")
    if "timestamp" not in {c.lower().strip() for c in df.columns}:
        raise ValueError(f"{sensor_type} CSV must contain a timestamp column")

    out = _normalize_columns(df.copy(), sensor_type)
    out = _parse_list_columns(out)
    out = _filter_valid_rows(out)
    out = _explode_rows(out)
    out = _create_timestamps(out)
    out = _rename_axes(out, sensor_type)

    expected = ["Ax", "Ay", "Az"] if sensor_type == "accelerometer" else ["Gx", "Gy", "Gz"]
    missing = [c for c in expected if c not in out.columns]
    if missing:
        raise ValueError(f"{sensor_type} CSV missing required columns after parsing: {missing}")
    for col in expected:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["true_time", *expected]).reset_index(drop=True)
    if len(out) == 0:
        raise ValueError(f"{sensor_type} CSV has no valid sensor rows after parsing")
    return out


def _merge_upload_pair(
    accel_df: pd.DataFrame, gyro_df: pd.DataFrame
) -> Tuple[pd.DataFrame, List[str]]:
    """Merge uploaded accel+gyro CSVs into the same six-channel frame expected by inference."""
    accel = _prepare_sensor_frame(accel_df, "accelerometer")
    gyro = _prepare_sensor_frame(gyro_df, "gyroscope")
    fused = _merge_and_resample(
        accel,
        gyro,
        target_hz=DEFAULT_TARGET_HZ,
        merge_tolerance_ms=DEFAULT_MERGE_TOLERANCE_MS,
    )
    sensor_cols = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
    if len(fused) < WINDOW_SIZE:
        raise ValueError(
            f"Merged sensor pair has {len(fused)} rows after resampling; "
            f"at least {WINDOW_SIZE} are needed for one window."
        )
    return fused, sensor_cols


def _maybe_convert_accel_units(
    df: pd.DataFrame, sensor_cols: List[str]
) -> Tuple[pd.DataFrame, bool]:
    """
    Convert accelerometer channels from milliG to m/s^2 when the uploaded values
    look like raw Garmin milliG. Gyroscope channels are left unchanged.
    """
    out = df.copy()
    accel_cols = sensor_cols[:3]
    accel_abs_mean = float(np.nanmean(np.abs(out[accel_cols].values.astype(np.float32))))
    if accel_abs_mean > 50.0:
        out[accel_cols] = out[accel_cols] * _MILLIG_TO_MS2
        return out, True
    return out, False


def _apply_final_model_scaler(values: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """Apply the active Garmin train-only StandardScaler."""
    cfg = _load_scaler_config()
    mean = np.asarray(cfg["scaler_mean"], dtype=np.float32)
    scale = np.asarray(cfg["scaler_scale"], dtype=np.float32)
    safe_scale = np.where(scale == 0, 1.0, scale)
    scaled = (values.astype(np.float32) - mean) / safe_scale
    info = {
        "normalization_applied": True,
        "normalization_variant": cfg.get("normalization_variant", "zscore"),
        "scaler_config": str(SCALER_CONFIG_PATH),
        "model_input_space": "zscore_scaled_garmin_train_only",
        "note": "API upload path applies the active Garmin train-only scaler after accelerometer unit conversion.",
    }
    return scaled.astype(np.float32), info


def _create_windows(values: np.ndarray) -> np.ndarray:
    """Vectorized sliding-window creation using stride_tricks."""
    from numpy.lib.stride_tricks import as_strided

    n_samples, n_channels = values.shape
    n_windows = (n_samples - WINDOW_SIZE) // STEP_SIZE + 1
    if n_windows <= 0:
        raise ValueError(f"Not enough samples ({n_samples}) for window_size={WINDOW_SIZE}")
    stride_s, stride_c = values.strides
    windows = as_strided(
        values,
        shape=(n_windows, WINDOW_SIZE, n_channels),
        strides=(STEP_SIZE * stride_s, stride_s, stride_c),
    )
    return np.array(windows)  # own memory


def _smooth_predictions(
    probabilities: np.ndarray, window: int = SMOOTHING_WINDOW
) -> Tuple[np.ndarray, np.ndarray]:
    """Soft-vote temporal smoothing of the prediction stream.

    Averages the softmax vectors over a neighbourhood of ``window`` windows and
    takes the argmax, so an isolated low-confidence flip is outvoted by its
    confident neighbours. Returns ``(smoothed_classes, smoothed_confidence)``.
    """
    n = len(probabilities)
    if window <= 1 or n == 0:
        return probabilities.argmax(axis=1), probabilities.max(axis=1)
    half = window // 2
    averaged = np.empty_like(probabilities)
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        averaged[i] = probabilities[lo:hi].mean(axis=0)
    return averaged.argmax(axis=1), averaged.max(axis=1)


def _run_monitoring(
    predictions: np.ndarray,
    probabilities: np.ndarray,
    windows: np.ndarray,
    smoothed_predictions: Optional[np.ndarray] = None,
) -> Dict:
    """
    Run 3-layer monitoring on inference results.

    Layer 1 â€“ Confidence analysis
    Layer 2 â€“ Temporal pattern analysis
    Layer 3 â€“ Drift detection (if baseline available)
    """
    n = len(predictions)

    # Layer 1: Confidence
    max_probs = probabilities.max(axis=1)
    mean_conf = float(np.mean(max_probs))
    uncertain_mask = max_probs < _MON_T.uncertain_window_threshold
    uncertain_pct = float(np.sum(uncertain_mask) / n * 100)
    l1_status = (
        "HEALTHY"
        if mean_conf >= _MON_T.confidence_warn_threshold
        and uncertain_pct <= _MON_T.uncertain_pct_threshold
        else "WARNING"
    )

    # Layer 2: Temporal â€” status is judged on the RAW stream (additive design).
    transitions = int(np.sum(predictions[1:] != predictions[:-1]))
    transition_rate = float(transitions / max(n - 1, 1) * 100)
    l2_status = "HEALTHY" if transition_rate <= _MON_T.transition_rate_threshold else "WARNING"
    if smoothed_predictions is not None and n > 1:
        transition_rate_smoothed = float(
            np.sum(smoothed_predictions[1:] != smoothed_predictions[:-1]) / (n - 1) * 100
        )
    else:
        transition_rate_smoothed = transition_rate

    # Layer 3: Drift
    l3_status = "SKIPPED"
    drift_scores = {}
    if _baseline is not None:
        baseline_mean = np.array(_baseline.get("mean", []))
        baseline_std = np.array(_baseline.get("std", []))
        if len(baseline_mean) == windows.shape[2] and len(baseline_std) == windows.shape[2]:
            current_mean = np.mean(windows, axis=(0, 1))
            safe_std = np.where(baseline_std > 0, baseline_std, 1.0)
            drift = np.abs(current_mean - baseline_mean) / safe_std
            for i, d in enumerate(drift):
                drift_scores[f"channel_{i}"] = round(float(d), 4)
            max_drift = float(np.max(drift))
            l3_status = "HEALTHY" if max_drift < _MON_T.drift_zscore_threshold else "WARNING"

    overall = (
        "HEALTHY"
        if all(s in ("HEALTHY", "SKIPPED") for s in [l1_status, l2_status, l3_status])
        else "WARNING"
    )

    # Trigger decision â€” derive reasons from each layer
    reasons = []
    if l1_status != "HEALTHY":
        reasons.append(
            f"mean confidence {mean_conf:.1%} below threshold "
            f"{_MON_T.confidence_warn_threshold:.1%}"
        )
    if uncertain_pct > _MON_T.uncertain_pct_threshold:
        reasons.append(
            f"uncertain windows {uncertain_pct:.1f}% above threshold "
            f"{_MON_T.uncertain_pct_threshold:.1f}%"
        )
    if l2_status != "HEALTHY":
        reasons.append(
            f"transition rate {transition_rate:.1f}% above threshold "
            f"{_MON_T.transition_rate_threshold:.1f}%"
        )
    if l3_status == "WARNING" and drift_scores:
        max_d = float(np.max(list(drift_scores.values())))
        reasons.append(
            f"drift z-score {max_d:.3f} above threshold "
            f"{_MON_T.drift_zscore_threshold:.1f}"
        )

    action = "REVIEW" if reasons else "NO_ACTION"
    alert_level = (
        "CRITICAL" if uncertain_pct > 50
        else ("WARNING" if reasons else "HEALTHY")
    )

    return {
        "overall_status": overall,
        "layer1_confidence": {
            "status": l1_status,
            "mean_confidence": round(mean_conf, 4),
            "uncertain_pct": round(uncertain_pct, 2),
            "threshold_conf": _MON_T.confidence_warn_threshold,
            "threshold_uncertain": _MON_T.uncertain_pct_threshold,
        },
        "layer2_temporal": {
            "status": l2_status,
            "transitions": transitions,
            "transition_rate_pct": round(transition_rate, 2),
            "transition_rate_smoothed_pct": round(transition_rate_smoothed, 2),
            "smoothing_window": SMOOTHING_WINDOW,
            "threshold_pct": _MON_T.transition_rate_threshold,
        },
        "layer3_drift": {
            "status": l3_status,
            "channel_drift": drift_scores,
            "max_drift": round(
                float(np.max(list(drift_scores.values()))) if drift_scores else 0.0, 4
            ),
        },
        "trigger": {
            "action": action,
            "should_retrain": False,
            "alert_level": alert_level,
            "reasons": reasons,
            "n_reasons": len(reasons),
        },
    }


# ---------------------------------------------------------------------------
# Serving-path MLflow logging (best-effort, non-fatal)
# ---------------------------------------------------------------------------


def _log_inference_mlflow(
    monitoring: Dict,
    evaluation: Optional[Dict],
    activity_summary: Dict[str, int],
    total_windows: int,
    mean_confidence: float,
    source_files: List[str],
) -> None:
    """Log the serving-path proxy metrics to the ``inference-production`` run.

    Writes confidence, drift, temporal (raw + smoothed), per-activity counts, and
    â€” when labels are present â€” accuracy/macro-F1, so WebUI/API uploads are tracked
    alongside the batch pipeline. Best-effort: any failure (MLflow absent, tracking
    server down) is logged and ignored so serving never breaks.
    """
    try:
        import mlflow

        l2 = monitoring.get("layer2_temporal", {})
        l3 = monitoring.get("layer3_drift", {})
        mlflow.set_experiment("inference-production")
        with mlflow.start_run(run_name=f"inference_{datetime.now():%Y%m%d_%H%M%S}"):
            mlflow.log_params(
                {
                    "model_path": MODEL_PATH.name,
                    "input": " + ".join(source_files) if source_files else "unknown.csv",
                    "has_labels": bool(evaluation and evaluation.get("available")),
                }
            )
            metrics = {
                "total_windows": total_windows,
                "mean_confidence": round(float(mean_confidence), 4),
                "transition_rate": l2.get("transition_rate_pct", 0.0),
                "transition_rate_smoothed": l2.get("transition_rate_smoothed_pct", 0.0),
            }
            if l3.get("status") != "SKIPPED" and l3.get("max_drift") is not None:
                metrics["drift_score"] = float(l3.get("max_drift", 0.0))
            if evaluation and evaluation.get("available"):
                metrics["accuracy"] = evaluation.get("accuracy", 0.0)
                metrics["macro_f1"] = evaluation.get("macro_f1", 0.0)
                metrics["weighted_f1"] = evaluation.get("weighted_f1", 0.0)
                if "accuracy_smoothed" in evaluation:
                    metrics["accuracy_smoothed"] = evaluation["accuracy_smoothed"]
                    metrics["macro_f1_smoothed"] = evaluation["macro_f1_smoothed"]
            mlflow.log_metrics(metrics)
            for activity, count in activity_summary.items():
                mlflow.log_metric(f"count_{activity}", int(count))
    except Exception as exc:  # pragma: no cover - MLflow is auxiliary
        logger.warning("MLflow inference logging skipped: %s", exc)


# ---------------------------------------------------------------------------
# Label evaluation (only when the upload carries ground-truth labels)
# ---------------------------------------------------------------------------


def _resolve_label_ids(label_series: pd.Series) -> np.ndarray:
    """Map a ground-truth label column to class ids.

    Accepts either activity names (e.g. ``smoking``) or numeric ids. Values that
    do not match a known class become -1 and are excluded from evaluation.
    """
    class_to_index = get_class_to_index()
    valid_ids = set(ACTIVITY_CLASSES.keys())
    ids = np.full(len(label_series), -1, dtype=np.int64)
    for i, value in enumerate(label_series.tolist()):
        key = str(value).strip().lower()
        if key in class_to_index:
            ids[i] = class_to_index[key]
            continue
        try:
            numeric = int(float(value))
        except (TypeError, ValueError):
            continue
        if numeric in valid_ids:
            ids[i] = numeric
    return ids


def _evaluate_against_labels(
    row_label_ids: np.ndarray,
    predicted_classes: np.ndarray,
    label_column: str,
    smoothed_classes: Optional[np.ndarray] = None,
) -> Dict:
    """Window-level accuracy / F1 against ground truth.

    Each window's true label is the majority of the per-sample labels it spans,
    matching the sliding-window geometry used for inference. Windows whose span
    has no resolvable label are skipped.
    """
    n_windows = len(predicted_classes)
    y_true = np.full(n_windows, -1, dtype=np.int64)
    for i in range(n_windows):
        start = i * STEP_SIZE
        segment = row_label_ids[start : start + WINDOW_SIZE]
        segment = segment[segment >= 0]
        if segment.size:
            y_true[i] = int(np.bincount(segment).argmax())

    mask = y_true >= 0
    if not mask.any():
        return {
            "available": False,
            "label_column": label_column,
            "note": "Label column found but no values matched known activity classes.",
        }

    yt = y_true[mask]
    yp = predicted_classes[mask].astype(np.int64)

    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_recall_fscore_support,
    )

    smoothed_metrics: Dict = {}
    if smoothed_classes is not None:
        yps = smoothed_classes[mask].astype(np.int64)
        smoothed_metrics = {
            "accuracy_smoothed": round(float(accuracy_score(yt, yps)), 4),
            "macro_f1_smoothed": round(
                float(f1_score(yt, yps, average="macro", zero_division=0)), 4
            ),
        }

    labels_present = sorted(set(yt.tolist()) | set(yp.tolist()))
    precision, recall, f1, support = precision_recall_fscore_support(
        yt, yp, labels=labels_present, zero_division=0
    )
    per_class = [
        {
            "activity": ACTIVITY_CLASSES.get(int(c), str(c)),
            "precision": round(float(precision[j]), 4),
            "recall": round(float(recall[j]), 4),
            "f1": round(float(f1[j]), 4),
            "support": int(support[j]),
        }
        for j, c in enumerate(labels_present)
    ]
    return {
        "available": True,
        "label_column": label_column,
        "accuracy": round(float(accuracy_score(yt, yp)), 4),
        "macro_f1": round(float(f1_score(yt, yp, average="macro", zero_division=0)), 4),
        "weighted_f1": round(
            float(f1_score(yt, yp, average="weighted", zero_division=0)), 4
        ),
        "n_evaluated_windows": int(mask.sum()),
        "n_total_windows": int(n_windows),
        "label_basis": "majority vote of per-sample labels within each window",
        "per_class": per_class,
        "confusion_matrix": {
            "labels": [ACTIVITY_CLASSES.get(int(c), str(c)) for c in labels_present],
            "matrix": confusion_matrix(yt, yp, labels=labels_present).tolist(),
        },
        **smoothed_metrics,
    }


def _maybe_evaluate(
    df: pd.DataFrame,
    label_column: Optional[str],
    predicted_classes: np.ndarray,
    smoothed_classes: Optional[np.ndarray] = None,
) -> Optional[Dict]:
    """Return evaluation metrics if the upload carries a usable label column."""
    if not label_column or label_column not in df.columns:
        return None
    row_label_ids = _resolve_label_ids(df[label_column])
    return _evaluate_against_labels(
        row_label_ids, predicted_classes, label_column, smoothed_classes
    )


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class UploadResult(BaseModel):
    filename: str
    source_files: List[str] = Field(default_factory=list)
    upload_mode: str = "fused_csv"
    total_rows: int
    sensor_columns: List[str]
    has_labels: bool = False
    label_column: Optional[str] = None
    retraining_eligible: bool = False
    preprocessing: Dict = Field(default_factory=dict)
    windows_created: int
    processing_time_ms: float
    predictions: List[Dict]
    activity_summary: Dict[str, int]
    monitoring: Dict
    evaluation: Optional[Dict] = None
    confidence_stats: Dict


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    baseline_loaded: bool
    timestamp: str
    uptime_seconds: float


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_model()
    _load_baseline()
    yield


app = FastAPI(
    title="HAR MLOps API",
    description="Human Activity Recognition â€“ Inference, Monitoring & Dashboard",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================== API Endpoints ==================================


@app.get("/health", response_model=HealthResponse, tags=["System"])
@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health():
    return HealthResponse(
        status="healthy" if _model else "model_not_loaded",
        model_loaded=_model is not None,
        baseline_loaded=_baseline is not None,
        timestamp=datetime.now().isoformat(),
        uptime_seconds=(datetime.now() - _start_time).total_seconds(),
    )


@app.get("/api/model/info", tags=["System"])
async def model_info():
    if not _model_info:
        raise HTTPException(503, "Model not loaded")
    return {**_model_info, "activity_classes": ACTIVITY_CLASSES}


@app.post("/api/upload", response_model=UploadResult, tags=["Inference"])
async def upload_csv(
    file: Optional[UploadFile] = File(
        None,
        description="Single fused CSV containing accelerometer and gyroscope columns.",
    ),
    accelerometer_file: Optional[UploadFile] = File(
        None,
        description="Raw accelerometer CSV for two-file upload mode.",
    ),
    gyroscope_file: Optional[UploadFile] = File(
        None,
        description="Raw gyroscope CSV for two-file upload mode.",
    ),
):
    """
    Upload sensor data for inference.

    Accepted modes:
    - one fused CSV containing all six sensor channels
    - one accelerometer CSV plus one gyroscope CSV

    The API will:
    1. Auto-detect or fuse sensor columns
    2. Apply production unit conversion and the active Garmin scaler
    3. Create sliding windows (200 samples, 50 % overlap)
    4. Run inference (1D-CNN-BiLSTM)
    5. Run 3-layer monitoring (confidence, temporal, drift)
    6. Evaluate against ground-truth labels when the upload includes them
    7. Return full results
    """
    if _model is None:
        raise HTTPException(503, "Model not loaded â€“ check /api/health")

    t0 = time.perf_counter()

    has_fused = file is not None
    has_accel = accelerometer_file is not None
    has_gyro = gyroscope_file is not None
    if has_fused and (has_accel or has_gyro):
        raise HTTPException(
            400,
            "Choose one upload mode: either a single fused CSV or an accelerometer+gyroscope pair.",
        )
    if not has_fused and not (has_accel and has_gyro):
        raise HTTPException(
            400,
            "Upload either one fused CSV or both accelerometer_file and gyroscope_file.",
        )
    if has_accel != has_gyro:
        raise HTTPException(
            400,
            "Two-file mode requires both accelerometer_file and gyroscope_file.",
        )

    upload_mode = "fused_csv"
    source_files: List[str] = []
    label_column: Optional[str] = None

    try:
        if has_fused:
            assert file is not None
            df = await _read_upload_csv(file, "fused")
            upload_mode = "fused_csv"
            source_files = [file.filename or "fused.csv"]
            label_column = _detect_label_column(df)
            sensor_cols = _detect_columns(df)
        else:
            assert accelerometer_file is not None and gyroscope_file is not None
            accel_df = await _read_upload_csv(accelerometer_file, "accelerometer")
            gyro_df = await _read_upload_csv(gyroscope_file, "gyroscope")
            upload_mode = "accel_gyro_pair"
            source_files = [
                accelerometer_file.filename or "accelerometer.csv",
                gyroscope_file.filename or "gyroscope.csv",
            ]
            df, sensor_cols = _merge_upload_pair(accel_df, gyro_df)
    except ValueError as e:
        raise HTTPException(400, str(e))

    for col in sensor_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=sensor_cols).reset_index(drop=True)

    if len(df) < WINDOW_SIZE:
        raise HTTPException(
            400,
            f"Prepared data has {len(df)} rows but at least {WINDOW_SIZE} are needed "
            f"for one window.",
        )

    # --- Unit conversion + active runtime scaler contract ---
    df, unit_conversion_applied = _maybe_convert_accel_units(df, sensor_cols)
    raw_values = df[sensor_cols].values.astype(np.float32)
    values, scaler_info = _apply_final_model_scaler(raw_values)
    preprocessing_info = {
        "unit_conversion_applied": unit_conversion_applied,
        **scaler_info,
    }

    # --- Create windows ---
    try:
        windows = _create_windows(values)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # --- Inference ---
    probabilities = _model.predict(windows, verbose=0, batch_size=64)
    predicted_classes = np.argmax(probabilities, axis=1)
    max_probs = probabilities.max(axis=1)
    # Temporal smoothing (additive): raw predictions remain the served output.
    smoothed_classes, _ = _smooth_predictions(probabilities)

    # --- Per-window results ---
    predictions = []
    for i in range(len(predicted_classes)):
        cls_id = int(predicted_classes[i])
        predictions.append(
            {
                "window": i,
                "activity": ACTIVITY_CLASSES[cls_id],
                "activity_id": cls_id,
                "confidence": round(float(max_probs[i]), 4),
            }
        )

    # --- Summary ---
    from collections import Counter

    counts = Counter(ACTIVITY_CLASSES[int(c)] for c in predicted_classes)
    activity_summary = dict(sorted(counts.items(), key=lambda x: -x[1]))

    # --- Monitoring ---
    monitoring = _run_monitoring(predicted_classes, probabilities, windows, smoothed_classes)

    # --- Evaluation (only when the upload carries ground-truth labels) ---
    evaluation = _maybe_evaluate(df, label_column, predicted_classes, smoothed_classes)

    # --- MLflow (best-effort; never breaks serving) ---
    _log_inference_mlflow(
        monitoring,
        evaluation,
        activity_summary,
        len(windows),
        float(np.mean(max_probs)),
        source_files,
    )

    elapsed = (time.perf_counter() - t0) * 1000
    has_labels = label_column is not None
    retraining_eligible = bool(has_labels)

    return UploadResult(
        filename=" + ".join(source_files) if source_files else "unknown.csv",
        source_files=source_files,
        upload_mode=upload_mode,
        total_rows=len(df),
        sensor_columns=sensor_cols,
        has_labels=has_labels,
        label_column=label_column,
        retraining_eligible=retraining_eligible,
        preprocessing=preprocessing_info,
        windows_created=len(windows),
        processing_time_ms=round(elapsed, 1),
        predictions=predictions,
        activity_summary=activity_summary,
        monitoring=monitoring,
        evaluation=evaluation,
        confidence_stats={
            "mean": round(float(np.mean(max_probs)), 4),
            "std": round(float(np.std(max_probs)), 4),
            "min": round(float(np.min(max_probs)), 4),
            "max": round(float(np.max(max_probs)), 4),
        },
    )


# ========================== Web UI =========================================

_DASHBOARD_PATH = Path(__file__).parent / "templates" / "dashboard.html"


@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def dashboard():
    """Serve the interactive web dashboard."""
    return _DASHBOARD_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )

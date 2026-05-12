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
from src.config import FINAL_MODEL_A_SCALER_JSON as _FINAL_MODEL_A_SCALER_JSON
from src.config import OVERLAP as _OVERLAP
from src.config import PROJECT_ROOT as _PROJECT_ROOT
from src.config import WINDOW_SIZE as _WINDOW_SIZE
from src.utils.label_detection import LABEL_COLUMN_CANDIDATES, NON_GROUND_TRUTH_COLUMNS
from src.utils.label_mapping import get_activity_classes


# Single source of truth for monitoring thresholds — shared with the pipeline.
def _load_monitoring_thresholds():
    try:
        from src.utils.config_loader import load_monitoring_config

        return load_monitoring_config()
    except Exception:  # pragma: no cover — standalone startup without src/ on path

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
SCALER_CONFIG_PATH = Path(os.environ.get("SCALER_CONFIG_PATH", str(_FINAL_MODEL_A_SCALER_JSON)))
BASELINE_PATH = Path(
    os.environ.get(
        "BASELINE_PATH",
        str(
            PROJECT_ROOT
            / "models"
            / "production_contract"
            / "model_a_final_20260508"
            / "garmin_train_scaled_baseline.json"
        ),
    )
)
WINDOW_SIZE = _WINDOW_SIZE
OVERLAP = _OVERLAP
STEP_SIZE = int(WINDOW_SIZE * (1 - OVERLAP))

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
    logger.info("Loading model from %s …", MODEL_PATH)
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
    logger.info("Model ready – %s params", f"{_model_info['params']:,}")


def _load_baseline():
    """Load the final Model A scaled baseline JSON (once)."""
    global _baseline
    if _baseline is not None or not BASELINE_PATH.exists():
        return
    with open(BASELINE_PATH) as f:
        _baseline = json.load(f)
    logger.info("Baseline loaded from %s", BASELINE_PATH)


def _load_scaler_config() -> Dict:
    """Load the final Model A Garmin train-only scaler JSON."""
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
        out[accel_cols] = out[accel_cols] * 0.00981
        return out, True
    return out, False


def _apply_final_model_scaler(values: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """Apply the final Model A Garmin train-only StandardScaler."""
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
        "note": "API upload path applies the final Model A Garmin train-only scaler after accelerometer unit conversion.",
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


def _run_monitoring(
    predictions: np.ndarray,
    probabilities: np.ndarray,
    windows: np.ndarray,
) -> Dict:
    """
    Run 3-layer monitoring on inference results.

    Layer 1 – Confidence analysis
    Layer 2 – Temporal pattern analysis
    Layer 3 – Drift detection (if baseline available)
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

    # Layer 2: Temporal
    transitions = int(np.sum(predictions[1:] != predictions[:-1]))
    transition_rate = float(transitions / max(n - 1, 1) * 100)
    l2_status = "HEALTHY" if transition_rate <= _MON_T.transition_rate_threshold else "WARNING"

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
            "threshold_pct": _MON_T.transition_rate_threshold,
        },
        "layer3_drift": {
            "status": l3_status,
            "channel_drift": drift_scores,
            "max_drift": round(
                float(np.max(list(drift_scores.values()))) if drift_scores else 0.0, 4
            ),
        },
    }


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
    description="Human Activity Recognition – Inference, Monitoring & Dashboard",
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
    2. Apply production unit conversion and the final Model A Garmin scaler
    3. Create sliding windows (200 samples, 50 % overlap)
    4. Run inference (1D-CNN-BiLSTM)
    5. Run 3-layer monitoring (confidence, temporal, drift)
    6. Return full results
    """
    if _model is None:
        raise HTTPException(503, "Model not loaded – check /api/health")

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

    # --- Unit conversion + final Model A scaler contract ---
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
    monitoring = _run_monitoring(predicted_classes, probabilities, windows)

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
        confidence_stats={
            "mean": round(float(np.mean(max_probs)), 4),
            "std": round(float(np.std(max_probs)), 4),
            "min": round(float(np.min(max_probs)), 4),
            "max": round(float(np.max(max_probs)), 4),
        },
    )


# ========================== Web UI =========================================


@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def dashboard():
    """Serve the interactive web dashboard."""
    return _DASHBOARD_HTML


# ---------------------------------------------------------------------------
# Embedded HTML dashboard (single-file, no external templates needed)
# ---------------------------------------------------------------------------

_DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HAR MLOps Dashboard</title>
<style>
  :root {
    --bg: #0f172a; --surface: #1e293b; --surface2: #334155;
    --border: #475569; --text: #e2e8f0; --muted: #94a3b8;
    --primary: #3b82f6; --primary-hover: #2563eb;
    --green: #22c55e; --yellow: #eab308; --red: #ef4444;
    --radius: 12px;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.6;
    min-height: 100vh;
  }
  .container { max-width: 1200px; margin: 0 auto; padding: 24px; }

  /* Header */
  header {
    background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
    border-bottom: 1px solid var(--border); padding: 32px 0;
    text-align: center;
  }
  header h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }
  header h1 span { color: var(--primary); }
  header p { color: var(--muted); margin-top: 8px; font-size: 0.95rem; }

  /* Cards */
  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 24px; margin-bottom: 20px;
  }
  .card h2 {
    font-size: 1.1rem; font-weight: 600; margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
  }
  .card h2 .icon { font-size: 1.3rem; }

  /* Upload area */
  .upload-zone {
    border: 2px dashed var(--border); border-radius: var(--radius);
    padding: 48px 24px; text-align: center; cursor: pointer;
    transition: all 0.25s ease;
  }
  .upload-zone:hover, .upload-zone.dragover {
    border-color: var(--primary); background: rgba(59,130,246,0.05);
  }
  .upload-zone .big-icon { font-size: 3rem; margin-bottom: 12px; }
  .upload-zone p { color: var(--muted); }
  .upload-zone .filename { color: var(--primary); font-weight: 600; margin-top: 8px; }
  #fileInput { display: none; }

  .btn {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--primary); color: #fff; border: none;
    padding: 12px 28px; border-radius: 8px; font-size: 1rem;
    font-weight: 600; cursor: pointer; margin-top: 16px;
    transition: background 0.2s;
  }
  .btn:hover { background: var(--primary-hover); }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }

  /* Status bar */
  .status-bar {
    display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 20px;
  }
  .status-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--surface2); border-radius: 20px;
    padding: 6px 14px; font-size: 0.85rem;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot.green { background: var(--green); }
  .dot.yellow { background: var(--yellow); }
  .dot.red { background: var(--red); }
  .dot.gray { background: var(--muted); }

  /* Grid */
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }

  /* Monitoring pills */
  .monitor-layers { display: flex; gap: 12px; flex-wrap: wrap; }
  .layer-pill {
    flex: 1; min-width: 200px; background: var(--surface2);
    border-radius: 8px; padding: 16px;
  }
  .layer-pill .label { font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
  .layer-pill .value { font-size: 1.5rem; font-weight: 700; margin-top: 4px; }
  .layer-pill .detail { font-size: 0.85rem; color: var(--muted); margin-top: 4px; }

  /* Table */
  table { width: 100%; border-collapse: collapse; }
  th, td {
    padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--surface2);
    font-size: 0.9rem;
  }
  th { color: var(--muted); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; }
  tr:hover { background: rgba(59,130,246,0.04); }
  .conf-bar {
    height: 6px; border-radius: 3px; background: var(--surface2);
    position: relative; overflow: hidden; min-width: 60px;
  }
  .conf-bar .fill { height: 100%; border-radius: 3px; transition: width 0.3s; }

  /* Activity summary bars */
  .activity-bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
  .activity-bar-row .name { min-width: 140px; font-size: 0.85rem; }
  .activity-bar-row .bar-bg {
    flex: 1; height: 20px; background: var(--surface2); border-radius: 4px;
    overflow: hidden;
  }
  .activity-bar-row .bar-fill { height: 100%; border-radius: 4px; transition: width 0.4s; }
  .activity-bar-row .count { min-width: 40px; text-align: right; font-size: 0.85rem; color: var(--muted); }

  /* Spinner */
  .spinner { display: none; margin: 20px auto; }
  .spinner.active { display: block; }
  .spinner svg { animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Hidden */
  .hidden { display: none; }

  /* Info text */
  .info-box {
    background: rgba(59,130,246,0.1); border-left: 3px solid var(--primary);
    border-radius: 0 8px 8px 0; padding: 12px 16px; margin-top: 16px;
    font-size: 0.9rem; color: var(--muted);
  }

  /* Footer */
  footer {
    text-align: center; padding: 24px; color: var(--muted);
    font-size: 0.8rem; border-top: 1px solid var(--surface2); margin-top: 40px;
  }

  /* Pipeline stage track */
  .pipeline-track {
    display: flex; gap: 0; flex-wrap: wrap; align-items: center;
    margin-bottom: 20px;
  }
  .stage-box {
    display: flex; flex-direction: column; align-items: center;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 10px 12px; min-width: 80px;
    text-align: center; position: relative; cursor: default;
    transition: border-color 0.3s;
  }
  .stage-box.active   { border-color: var(--primary); }
  .stage-box.pass     { border-color: var(--green); }
  .stage-box.warn     { border-color: var(--yellow); }
  .stage-box.fail     { border-color: var(--red); }
  .stage-box.gated    { opacity: 0.5; }
  .stage-box .snum    { font-size: 0.7rem; color: var(--muted); }
  .stage-box .sname   { font-size: 0.75rem; font-weight: 600; margin-top: 2px; }
  .stage-box .sdot    { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); margin-top: 6px; }
  .stage-box.pass .sdot { background: var(--green); }
  .stage-box.warn .sdot { background: var(--yellow); }
  .stage-box.fail .sdot { background: var(--red); }
  .stage-box.active .sdot { background: var(--primary); }
  .pipe-arrow { color: var(--muted); padding: 0 4px; font-size: 0.85rem; align-self: center; }
</style>
</head>
<body>

<header>
  <div class="container">
    <h1>&#x1F3AF; HAR <span>MLOps</span> Dashboard</h1>
    <p>Upload sensor CSV &rarr; Inference &rarr; 3-Layer Monitoring &rarr; Results</p>
  </div>
</header>

<div class="container">

  <!-- Status Bar -->
  <div class="status-bar" id="statusBar">
    <div class="status-chip"><div class="dot gray" id="dotModel"></div><span id="statusModel">Checking model…</span></div>
    <div class="status-chip"><div class="dot gray" id="dotBaseline"></div><span id="statusBaseline">Checking baseline…</span></div>
    <div class="status-chip"><div class="dot gray" id="dotApi"></div><span id="statusApi">API</span></div>
  </div>

  <!-- Pipeline Stage Track -->
  <div class="card" style="padding:16px 20px;">
    <h2 style="margin-bottom:12px;"><span class="icon">&#x26A1;</span> Pipeline Stages</h2>
    <div class="pipeline-track" id="stageTrack">
      <div class="stage-box gated" id="s1"><span class="snum">S1</span><span class="sname">Ingest</span><span class="sdot"></span></div>
      <span class="pipe-arrow">&#8594;</span>
      <div class="stage-box gated" id="s2"><span class="snum">S2</span><span class="sname">Validate</span><span class="sdot"></span></div>
      <span class="pipe-arrow">&#8594;</span>
      <div class="stage-box gated" id="s3"><span class="snum">S3</span><span class="sname">Transform</span><span class="sdot"></span></div>
      <span class="pipe-arrow">&#8594;</span>
      <div class="stage-box" id="s4"><span class="snum">S4</span><span class="sname">Inference</span><span class="sdot"></span></div>
      <span class="pipe-arrow">&#8594;</span>
      <div class="stage-box" id="s5"><span class="snum">S5</span><span class="sname">Evaluate</span><span class="sdot"></span></div>
      <span class="pipe-arrow">&#8594;</span>
      <div class="stage-box" id="s6"><span class="snum">S6</span><span class="sname">Monitor</span><span class="sdot"></span></div>
      <span class="pipe-arrow">&#8594;</span>
      <div class="stage-box" id="s7"><span class="snum">S7</span><span class="sname">Trigger</span><span class="sdot"></span></div>
      <span class="pipe-arrow" id="arrowRetrain" style="opacity:0.3">&#8594;</span>
      <div class="stage-box gated" id="s8"><span class="snum">S8</span><span class="sname">Retrain</span><span class="sdot"></span></div>
      <span class="pipe-arrow" style="opacity:0.3">&#8594;</span>
      <div class="stage-box gated" id="s9"><span class="snum">S9</span><span class="sname">Register</span><span class="sdot"></span></div>
      <span class="pipe-arrow" style="opacity:0.3">&#8594;</span>
      <div class="stage-box gated" id="s10"><span class="snum">S10</span><span class="sname">Baseline</span><span class="sdot"></span></div>
    </div>
    <p style="font-size:0.78rem;color:var(--muted);margin-top:6px;">S1-S3 run via full pipeline CLI &middot; this API call executes S4-S7 (so 4/4 requested stages is correct) &middot; S8-S10 require review, labels, and QA outside this request &middot; S11 is optional via run_pipeline.py --advanced</p>
  </div>

  <!-- Upload Card -->
  <div class="card">
    <h2><span class="icon">&#128228;</span> Upload Sensor Data</h2>
    <div class="upload-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
      <div class="big-icon">&#128196;</div>
      <p><strong>Click or drag & drop</strong> a fused CSV file here</p>
      <p style="font-size:0.85rem;">Fused CSV requires accelerometer + gyroscope columns in one file.</p>
      <div class="filename" id="fileName"></div>
    </div>
    <input type="file" id="fileInput" accept=".csv">
    <div style="margin:16px 0;color:var(--muted);text-align:center;">or upload a raw sensor pair</div>
    <div class="grid">
      <div>
        <label style="font-size:0.8rem;color:var(--muted);">Accelerometer CSV</label>
        <input type="file" id="accelInput" accept=".csv" style="width:100%;margin-top:6px;">
        <div class="filename" id="accelName"></div>
      </div>
      <div>
        <label style="font-size:0.8rem;color:var(--muted);">Gyroscope CSV</label>
        <input type="file" id="gyroInput" accept=".csv" style="width:100%;margin-top:6px;">
        <div class="filename" id="gyroName"></div>
      </div>
    </div>
    <div class="info-box" style="margin-top:14px;">
      Inference accepts one fused CSV or one accelerometer + gyroscope pair.
      Retraining remains gated and requires labels plus a qualifying trigger decision.
    </div>
    <div style="text-align:center;">
      <button class="btn" id="runBtn" disabled onclick="runInference()">
        &#9654; Run Inference &amp; Monitoring
      </button>
    </div>
    <div class="spinner" id="spinner">
      <svg width="40" height="40" viewBox="0 0 40 40"><circle cx="20" cy="20" r="16" stroke="#3b82f6" stroke-width="4" fill="none" stroke-dasharray="80" stroke-dashoffset="60"/></svg>
    </div>
  </div>

  <!-- Results (hidden until inference runs) -->
  <div id="results" class="hidden">

    <!-- Summary chips -->
    <div class="card">
      <h2><span class="icon">&#x1F4CA;</span> Summary</h2>
      <div style="display:flex;gap:16px;flex-wrap:wrap;" id="summaryChips"></div>
    </div>

    <!-- Monitoring -->
    <div class="card">
      <h2><span class="icon">&#x1F6E1;</span> 3-Layer Monitoring</h2>
      <div class="monitor-layers" id="monitorLayers"></div>
    </div>

    <!-- Grid: Activity Distribution + Confidence -->
    <div class="grid">
      <div class="card">
        <h2><span class="icon">&#x1F3C3;</span> Activity Distribution</h2>
        <div id="activityBars"></div>
      </div>
      <div class="card">
        <h2><span class="icon">&#x1F4C8;</span> Confidence Statistics</h2>
        <div id="confStats"></div>
      </div>
    </div>

    <!-- Predictions table -->
    <div class="card">
      <h2><span class="icon">&#x1F4DD;</span> Window Predictions</h2>
      <div style="max-height:400px;overflow-y:auto;">
        <table>
          <thead><tr><th>#</th><th>Activity</th><th>ID</th><th>Confidence</th><th></th></tr></thead>
          <tbody id="predTable"></tbody>
        </table>
      </div>
    </div>

    <!-- Info -->
    <div class="info-box">
      <strong>How it works:</strong> Your CSV is split into sliding windows of 200 samples
      (50% overlap). Each window is classified by a 1D-CNN-BiLSTM model. Then 3-layer
      monitoring checks confidence, temporal consistency, and distribution drift.
      Labeled uploads are marked as retraining-eligible, but model mutation remains gated outside this API call.
    </div>
  </div>

</div>

<footer>
  HAR MLOps Pipeline &middot; Master Thesis &middot; 1D-CNN-BiLSTM &middot; TensorFlow/Keras
</footer>

<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const accelInput = document.getElementById('accelInput');
const gyroInput = document.getElementById('gyroInput');
const runBtn = document.getElementById('runBtn');
const spinner = document.getElementById('spinner');
let selectedFusedFile = null;
let selectedAccelFile = null;
let selectedGyroFile = null;

// Drag & drop
['dragenter','dragover'].forEach(e => dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add('dragover'); }));
['dragleave','drop'].forEach(e => dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.remove('dragover'); }));
dropZone.addEventListener('drop', ev => { if (ev.dataTransfer.files.length) selectFusedFile(ev.dataTransfer.files[0]); });
fileInput.addEventListener('change', () => { if (fileInput.files.length) selectFusedFile(fileInput.files[0]); });
accelInput.addEventListener('change', () => { if (accelInput.files.length) selectPairFile('accel', accelInput.files[0]); });
gyroInput.addEventListener('change', () => { if (gyroInput.files.length) selectPairFile('gyro', gyroInput.files[0]); });

function selectFusedFile(f) {
  selectedFusedFile = f;
  selectedAccelFile = null;
  selectedGyroFile = null;
  accelInput.value = '';
  gyroInput.value = '';
  document.getElementById('accelName').textContent = '';
  document.getElementById('gyroName').textContent = '';
  document.getElementById('fileName').textContent = f.name + ' (' + (f.size/1024).toFixed(1) + ' KB)';
  updateRunButton();
}

function selectPairFile(kind, f) {
  selectedFusedFile = null;
  fileInput.value = '';
  document.getElementById('fileName').textContent = '';
  if (kind === 'accel') {
    selectedAccelFile = f;
    document.getElementById('accelName').textContent = f.name + ' (' + (f.size/1024).toFixed(1) + ' KB)';
  } else {
    selectedGyroFile = f;
    document.getElementById('gyroName').textContent = f.name + ' (' + (f.size/1024).toFixed(1) + ' KB)';
  }
  updateRunButton();
}

function updateRunButton() {
  runBtn.disabled = !(selectedFusedFile || (selectedAccelFile && selectedGyroFile));
}

// Health check on load
fetch('/api/health').then(r=>r.json()).then(d => {
  set('dotModel', d.model_loaded ? 'green' : 'red');
  set('statusModel', d.model_loaded ? 'Model loaded' : 'Model missing');
  set('dotBaseline', d.baseline_loaded ? 'green' : 'yellow');
  set('statusBaseline', d.baseline_loaded ? 'Baseline loaded' : 'No baseline');
  set('dotApi', 'green'); document.getElementById('statusApi').textContent = 'API ready';
}).catch(() => {
  set('dotApi', 'red'); document.getElementById('statusApi').textContent = 'API error';
});

function set(id, cls) {
  const el = document.getElementById(id);
  el.className = el.className.replace(/green|yellow|red|gray/g, '').trim() + ' ' + cls;
}

async function runInference() {
  if (!(selectedFusedFile || (selectedAccelFile && selectedGyroFile))) return;
  runBtn.disabled = true;
  spinner.classList.add('active');
  document.getElementById('results').classList.add('hidden');

  const fd = new FormData();
  if (selectedFusedFile) {
    fd.append('file', selectedFusedFile);
  } else {
    fd.append('accelerometer_file', selectedAccelFile);
    fd.append('gyroscope_file', selectedGyroFile);
  }

  try {
    const res = await fetch('/api/upload', { method: 'POST', body: fd });
    if (!res.ok) {
      const err = await res.json();
      alert('Error: ' + (err.detail || res.statusText));
      return;
    }
    const data = await res.json();
    renderResults(data);
  } catch (e) {
    alert('Request failed: ' + e.message);
  } finally {
    updateRunButton();
    spinner.classList.remove('active');
  }
}

function updateStages(d) {
  const m = d.monitoring;
  const stateOf = status => status === 'HEALTHY' ? 'pass' : status === 'PASS' ? 'pass' : status === 'WARNING' ? 'warn' : status === 'SKIPPED' ? '' : 'fail';

  // S4 Inference — always runs if we got results
  setStage('s4', 'pass');
  // S5 Evaluate — always runs alongside inference in the API
  setStage('s5', 'pass');
  // S6 Monitor
  setStage('s6', stateOf(m.overall_status) || 'pass');
  // S7 Trigger — infer from monitoring outcome
  const needsAction = m.overall_status !== 'HEALTHY';
  setStage('s7', needsAction ? 'warn' : 'pass');
  // S8-S10 stay gated in the API. Review, labels, and QA are required outside this request.
  document.getElementById('arrowRetrain').style.opacity = '0.3';
  ['s8','s9','s10'].forEach(id => setStage(id, 'gated'));
}

function setStage(id, cls) {
  const el = document.getElementById(id);
  el.classList.remove('gated','pass','warn','fail','active');
  if (cls) el.classList.add(cls);
}

function resetStages() {
  ['s4','s5','s6','s7'].forEach(id => setStage(id, ''));
  ['s8','s9','s10'].forEach(id => { setStage(id, 'gated'); });
  document.getElementById('arrowRetrain').style.opacity = '0.3';
}

function renderResults(d) {
  document.getElementById('results').classList.remove('hidden');
  updateStages(d);

  // Summary chips
  const chips = [
    { label: 'File', value: d.filename },
    { label: 'Mode', value: d.upload_mode },
    { label: 'Rows', value: d.total_rows.toLocaleString() },
    { label: 'Windows', value: d.windows_created },
    { label: 'Time', value: d.processing_time_ms.toFixed(0) + ' ms' },
    { label: 'Labels', value: d.has_labels ? d.label_column : 'none' },
    { label: 'Input', value: d.preprocessing.model_input_space || 'raw physical' },
    { label: 'Monitoring', value: d.monitoring.overall_status, color: d.monitoring.overall_status === 'HEALTHY' ? 'var(--green)' : d.monitoring.overall_status === 'CRITICAL' ? 'var(--red)' : 'var(--yellow)' },
  ];
  document.getElementById('summaryChips').innerHTML = chips.map(c =>
    `<div class="status-chip"><strong>${c.label}:</strong>&nbsp;` +
    `<span style="color:${c.color||'var(--text)'}">${c.value}</span></div>`
  ).join('');

  // Monitoring layers
  const m = d.monitoring;
  const layers = [
    { name: 'Confidence', status: m.layer1_confidence.status,
      value: (m.layer1_confidence.mean_confidence * 100).toFixed(1) + '%',
      detail: m.layer1_confidence.uncertain_pct.toFixed(1) + '% uncertain' },
    { name: 'Temporal', status: m.layer2_temporal.status,
      value: m.layer2_temporal.transition_rate_pct.toFixed(1) + '%',
      detail: m.layer2_temporal.transitions + ' transitions' },
    { name: 'Drift', status: m.layer3_drift.status,
      value: m.layer3_drift.status === 'SKIPPED' ? 'N/A' : m.layer3_drift.max_drift.toFixed(4),
      detail: m.layer3_drift.status === 'SKIPPED' ? 'No baseline' : 'max drift z-score' },
  ];
  document.getElementById('monitorLayers').innerHTML = layers.map(l => {
    const color = l.status === 'HEALTHY' ? 'var(--green)' : l.status === 'WARNING' ? 'var(--yellow)' : l.status === 'CRITICAL' ? 'var(--red)' : 'var(--muted)';
    return `<div class="layer-pill"><div class="label">${l.name}</div>` +
           `<div class="value" style="color:${color}">${l.value}</div>` +
           `<div class="detail">${l.detail} &middot; ${l.status}</div></div>`;
  }).join('');

  // Activity bars
  const maxCount = Math.max(...Object.values(d.activity_summary));
  document.getElementById('activityBars').innerHTML = Object.entries(d.activity_summary).map(([name, count]) => {
    const pct = (count / maxCount * 100).toFixed(0);
    const hue = (Object.keys(d.activity_summary).indexOf(name) * 32) % 360;
    return `<div class="activity-bar-row"><span class="name">${name}</span>` +
           `<div class="bar-bg"><div class="bar-fill" style="width:${pct}%;background:hsl(${hue},60%,55%)"></div></div>` +
           `<span class="count">${count}</span></div>`;
  }).join('');

  // Confidence stats
  const cs = d.confidence_stats;
  document.getElementById('confStats').innerHTML =
    `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">` +
    ['mean','std','min','max'].map(k =>
      `<div class="layer-pill"><div class="label">${k}</div><div class="value">${(cs[k]*100).toFixed(1)}%</div></div>`
    ).join('') + `</div>`;

  // Predictions table
  const rows = d.predictions.slice(0, 200);  // show first 200
  document.getElementById('predTable').innerHTML = rows.map(p => {
    const pct = (p.confidence * 100).toFixed(1);
    const barColor = p.confidence >= 0.8 ? 'var(--green)' : p.confidence >= 0.5 ? 'var(--yellow)' : 'var(--red)';
    return `<tr><td>${p.window}</td><td>${p.activity}</td><td>${p.activity_id}</td>` +
           `<td>${pct}%</td><td><div class="conf-bar"><div class="fill" style="width:${pct}%;background:${barColor}"></div></div></td></tr>`;
  }).join('') + (d.predictions.length > 200 ? `<tr><td colspan="5" style="text-align:center;color:var(--muted)">… ${d.predictions.length - 200} more windows</td></tr>` : '');
}
</script>
</body>
</html>
"""


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

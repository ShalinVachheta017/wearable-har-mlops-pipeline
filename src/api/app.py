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
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from src.utils.label_mapping import get_activity_classes

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

    _PROM_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PROM_AVAILABLE = False

if _PROM_AVAILABLE:
    _prom_requests_total = Counter(
        "har_api_requests_total",
        "Total /api/upload requests",
    )
    _prom_confidence_mean = Gauge(
        "har_confidence_mean",
        "Mean prediction confidence of last batch",
    )
    _prom_entropy_mean = Gauge(
        "har_entropy_mean",
        "Mean normalised prediction entropy of last batch",
    )
    _prom_flip_rate = Gauge(
        "har_flip_rate",
        "Activity transition rate (flip rate) of last batch",
    )
    _prom_drift_detected = Gauge(
        "har_drift_detected",
        "1 if Layer 3 drift WARNING was raised, else 0",
    )
    _prom_baseline_age_days = Gauge(
        "har_baseline_age_days",
        "Age of the drift baseline file in days (-1 = file missing, 0+ = days old)",
    )
    _prom_latency_ms = Histogram(
        "har_inference_latency_ms",
        "End-to-end /api/upload latency in milliseconds",
        buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
    )


# Single source of truth for monitoring thresholds — shared with the pipeline.
def _load_monitoring_thresholds():
    try:
        from src.utils.config_loader import load_monitoring_config

        return load_monitoring_config()
    except Exception:  # pragma: no cover — standalone startup without src/ on path

        class _MonCfg:  # type: ignore
            confidence_warn_threshold: float = 0.60
            uncertain_pct_threshold: float = 30.0
            uncertain_window_threshold: float = 0.50
            transition_rate_threshold: float = 50.0
            drift_zscore_threshold: float = 2.0
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
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "pretrained" / "fine_tuned_model_1dcnnbilstm.keras"
BASELINE_PATH = PROJECT_ROOT / "models" / "normalized_baseline.json"
WINDOW_SIZE = 200
OVERLAP = 0.5
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
    _model = tf.keras.models.load_model(str(MODEL_PATH))
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
    """Load the normalized baseline JSON (once)."""
    global _baseline
    if _baseline is not None or not BASELINE_PATH.exists():
        return
    with open(BASELINE_PATH) as f:
        _baseline = json.load(f)
    logger.info("Baseline loaded from %s", BASELINE_PATH)


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
        "PASS"
        if mean_conf >= _MON_T.confidence_warn_threshold
        and uncertain_pct <= _MON_T.uncertain_pct_threshold
        else "WARNING"
    )

    # Layer 2: Temporal
    transitions = int(np.sum(predictions[1:] != predictions[:-1]))
    transition_rate = float(transitions / max(n - 1, 1) * 100)
    l2_status = "PASS" if transition_rate <= _MON_T.transition_rate_threshold else "WARNING"

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
            l3_status = "PASS" if max_drift < _MON_T.drift_zscore_threshold else "WARNING"

    overall = (
        "PASS"
        if all(s in ("PASS", "SKIPPED") for s in [l1_status, l2_status, l3_status])
        else "WARNING"
    )

    # ---- Update Prometheus gauges (best-effort) ----
    if _PROM_AVAILABLE:
        _prom_confidence_mean.set(mean_conf)
        n_classes = probabilities.shape[1]
        probs_clipped = np.clip(probabilities, 1e-9, 1.0)
        entropy = -np.sum(probs_clipped * np.log(probs_clipped), axis=1) / np.log(n_classes)
        _prom_entropy_mean.set(float(np.mean(entropy)))
        _prom_flip_rate.set(transition_rate / 100.0)
        _prom_drift_detected.set(0.0 if l3_status in ("PASS", "SKIPPED") else 1.0)
        # Baseline age gauge: -1 = file missing, else age in fractional days
        if BASELINE_PATH.exists():
            _prom_baseline_age_days.set((time.time() - BASELINE_PATH.stat().st_mtime) / 86400)
        else:
            _prom_baseline_age_days.set(-1)

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
            "threshold_pct": 50,
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
    total_rows: int
    sensor_columns: List[str]
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


@app.get("/metrics", tags=["System"], include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint — scraped by config/prometheus.yml."""
    if not _PROM_AVAILABLE:
        raise HTTPException(503, "prometheus_client not installed")
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/upload", response_model=UploadResult, tags=["Inference"])
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file with accelerometer + gyroscope data.

    The API will:
    1. Auto-detect sensor columns
    2. Create sliding windows (200 samples, 50 % overlap)
    3. Run inference (1D-CNN-BiLSTM)
    4. Run 3-layer monitoring (confidence, temporal, drift)
    5. Return full results
    """
    if _model is None:
        raise HTTPException(503, "Model not loaded – check /api/health")

    t0 = time.perf_counter()

    # --- Read CSV ---
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"Failed to read CSV: {e}")

    if len(df) < WINDOW_SIZE:
        raise HTTPException(
            400,
            f"CSV has {len(df)} rows but at least {WINDOW_SIZE} are needed " f"for one window.",
        )

    # --- Detect columns ---
    try:
        sensor_cols = _detect_columns(df)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # --- Create windows ---
    values = df[sensor_cols].values.astype(np.float32)
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

    # ---- Update Prometheus request counters ----
    if _PROM_AVAILABLE:
        _prom_requests_total.inc()
        _prom_latency_ms.observe(elapsed)

    return UploadResult(
        filename=file.filename or "unknown.csv",
        total_rows=len(df),
        sensor_columns=sensor_cols,
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

  <!-- Upload Card -->
  <div class="card">
    <h2><span class="icon">&#128228;</span> Upload Sensor Data</h2>
    <div class="upload-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
      <div class="big-icon">&#128196;</div>
      <p><strong>Click or drag & drop</strong> a CSV file here</p>
      <p style="font-size:0.85rem;">Requires columns: acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z</p>
      <div class="filename" id="fileName"></div>
    </div>
    <input type="file" id="fileInput" accept=".csv">
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
    </div>
  </div>

</div>

<footer>
  HAR MLOps Pipeline &middot; Master Thesis &middot; 1D-CNN-BiLSTM &middot; TensorFlow/Keras
</footer>

<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const runBtn = document.getElementById('runBtn');
const spinner = document.getElementById('spinner');
let selectedFile = null;

// Drag & drop
['dragenter','dragover'].forEach(e => dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add('dragover'); }));
['dragleave','drop'].forEach(e => dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.remove('dragover'); }));
dropZone.addEventListener('drop', ev => { if (ev.dataTransfer.files.length) selectFile(ev.dataTransfer.files[0]); });
fileInput.addEventListener('change', () => { if (fileInput.files.length) selectFile(fileInput.files[0]); });

function selectFile(f) {
  selectedFile = f;
  document.getElementById('fileName').textContent = f.name + ' (' + (f.size/1024).toFixed(1) + ' KB)';
  runBtn.disabled = false;
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
  if (!selectedFile) return;
  runBtn.disabled = true;
  spinner.classList.add('active');
  document.getElementById('results').classList.add('hidden');

  const fd = new FormData();
  fd.append('file', selectedFile);

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
    runBtn.disabled = false;
    spinner.classList.remove('active');
  }
}

function renderResults(d) {
  document.getElementById('results').classList.remove('hidden');

  // Summary chips
  const chips = [
    { label: 'File', value: d.filename },
    { label: 'Rows', value: d.total_rows.toLocaleString() },
    { label: 'Windows', value: d.windows_created },
    { label: 'Time', value: d.processing_time_ms.toFixed(0) + ' ms' },
    { label: 'Monitoring', value: d.monitoring.overall_status, color: d.monitoring.overall_status === 'PASS' ? 'var(--green)' : 'var(--yellow)' },
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
      detail: m.layer3_drift.status === 'SKIPPED' ? 'No baseline' : 'max normalized drift' },
  ];
  document.getElementById('monitorLayers').innerHTML = layers.map(l => {
    const color = l.status === 'PASS' ? 'var(--green)' : l.status === 'WARNING' ? 'var(--yellow)' : 'var(--muted)';
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

#!/usr/bin/env python3
"""
Build Training Baseline
=======================

Provides ``BaselineBuilder`` — a class used by Stage 10 (BaselineUpdate) to
rebuild drift-detection baselines from the labeled training CSV after retraining.

Also exposes a CLI for one-off baseline regeneration:

    python scripts/build_training_baseline.py
    python scripts/build_training_baseline.py \
        --data data/raw/all_users_data_labeled.csv \
        --output models/training_baseline.json \
        --output-normalized models/normalized_baseline.json

Output format:
    Compatible with Stage 6 (post_inference_monitoring.py) which reads
    ``normalized_baseline.json`` via ``PostInferenceMonitor._analyze_drift()``.
    The training-baseline JSON additionally carries per-class statistics for
    richer reporting.
"""

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Project paths (resolved from this file's location) ───────────────────────
_SCRIPTS_DIR = Path(__file__).parent
_PROJECT_ROOT = _SCRIPTS_DIR.parent

# Add src to path so we can import config constants
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

try:
    from config import SENSOR_COLUMNS, WINDOW_SIZE, NUM_SENSORS, ACTIVITY_LABELS
    _OVERLAP = 0.5
    _STEP = int(WINDOW_SIZE * (1 - _OVERLAP))
except ImportError:
    # Fallback constants if src.config is not importable
    SENSOR_COLUMNS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
    WINDOW_SIZE    = 200
    NUM_SENSORS    = 6
    ACTIVITY_LABELS = []
    _STEP          = 100

_CHANNEL_NAMES = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]


# ── Core statistics builder ───────────────────────────────────────────────────

def _compute_stats(X: np.ndarray, channel_names: list) -> dict:
    """
    Compute per-channel statistics from a windowed array (N, T, C).
    Returns a dict compatible with PostInferenceMonitor._analyze_drift().
    """
    n_windows, _, n_channels = X.shape
    flat = X.reshape(-1, n_channels)

    mean    = flat.mean(axis=0).tolist()
    std     = flat.std(axis=0).tolist()
    min_val = flat.min(axis=0).tolist()
    max_val = flat.max(axis=0).tolist()
    p5      = np.percentile(flat,  5, axis=0).tolist()
    p25     = np.percentile(flat, 25, axis=0).tolist()
    p50     = np.percentile(flat, 50, axis=0).tolist()
    p75     = np.percentile(flat, 75, axis=0).tolist()
    p95     = np.percentile(flat, 95, axis=0).tolist()

    per_channel = {}
    for i, ch in enumerate(channel_names[:n_channels]):
        per_channel[ch] = {
            "mean": mean[i], "std": std[i],
            "min": min_val[i], "max": max_val[i],
            "p5": p5[i], "p25": p25[i], "p50": p50[i], "p75": p75[i], "p95": p95[i],
        }

    return {
        # Flat arrays used by PostInferenceMonitor._analyze_drift()
        "mean": mean,
        "std":  std,
        "min":  min_val,
        "max":  max_val,
        "percentiles": {"p5": p5, "p25": p25, "p50": p50, "p75": p75, "p95": p95},
        "per_channel": per_channel,
        "channel_names": channel_names[:n_channels],
    }


# ── BaselineBuilder ───────────────────────────────────────────────────────────

class BaselineBuilder:
    """
    Build and persist drift-detection baselines from labeled training data.

    Usage (from Stage 10 - BaselineUpdate component)::

        builder = BaselineBuilder()
        baseline = builder.build_from_csv("data/raw/all_users_data_labeled.csv")
        builder.save("models/training_baseline.json")
        builder.save_normalized("models/normalized_baseline.json")
    """

    def __init__(
        self,
        sensor_columns: Optional[list] = None,
        window_size: int = WINDOW_SIZE,
        step_size: Optional[int] = None,
        scaler_config_path: Optional[Path] = None,
    ):
        self.sensor_columns  = sensor_columns or SENSOR_COLUMNS
        self.window_size     = window_size
        self.step_size       = step_size or _STEP
        self.scaler_config_path = Path(scaler_config_path) if scaler_config_path else (
            _PROJECT_ROOT / "data" / "prepared" / "config.json"
        )
        self._baseline: Optional[dict] = None   # populated by build_from_csv()
        self._normalized_baseline: Optional[dict] = None

    def _build_transformed_windows(self, X_raw: np.ndarray) -> np.ndarray:
        """
        Map raw windows into the canonical monitoring feature space.

        Canonical space is defined by the training scaler config used by production
        transform mode (data/prepared/config.json).
        """
        if not self.scaler_config_path.exists():
            raise FileNotFoundError(
                f"Scaler config not found: {self.scaler_config_path}. "
                "Cannot build transformed-space normalized baseline."
            )

        with open(self.scaler_config_path, "r", encoding="utf-8") as fh:
            scaler_cfg = json.load(fh)

        variant = scaler_cfg.get("normalization_variant", "zscore")
        X_transformed = X_raw.astype(np.float32, copy=True)

        if variant == "none":
            logger.info("Baseline transform variant: none (passthrough)")
            return X_transformed

        if variant == "zscore":
            center = np.asarray(scaler_cfg["scaler_mean"], dtype=np.float32)
            scale = np.asarray(scaler_cfg["scaler_scale"], dtype=np.float32)
        elif variant == "robust":
            center = np.asarray(scaler_cfg["scaler_center"], dtype=np.float32)
            scale = np.asarray(scaler_cfg["scaler_scale"], dtype=np.float32)
        else:
            raise ValueError(
                f"Unknown normalization_variant '{variant}'. "
                "Expected one of: zscore, robust, none."
            )

        if center.shape[0] != X_transformed.shape[2] or scale.shape[0] != X_transformed.shape[2]:
            raise ValueError(
                "Scaler config shape mismatch for baseline transform: "
                f"center={center.shape[0]}, scale={scale.shape[0]}, channels={X_transformed.shape[2]}"
            )

        if np.any(scale == 0):
            raise ValueError("Scaler config has zero scale values; cannot normalize baseline safely.")

        X_transformed = (X_transformed - center.reshape(1, 1, -1)) / scale.reshape(1, 1, -1)
        logger.info("Baseline transform variant: %s (canonical transformed space)", variant)
        return X_transformed

    # ------------------------------------------------------------------
    def build_from_csv(self, data_path) -> dict:
        """
        Load labeled CSV, create sliding windows, compute baseline statistics.

        Parameters
        ----------
        data_path : str | Path
            Path to the labeled CSV (must have sensor columns + 'activity' column).

        Returns
        -------
        dict
            Full baseline dict (also stored in ``self._baseline``).
        """
        data_path = Path(data_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Training data not found: {data_path}")

        logger.info("Loading training CSV: %s", data_path)
        df = pd.read_csv(data_path)
        logger.info("  Rows: %d  |  Columns: %s", len(df), list(df.columns[:8]))

        # Validate sensor columns
        missing = [c for c in self.sensor_columns if c not in df.columns]
        if missing:
            raise ValueError(
                f"Expected sensor columns not found in CSV: {missing}\n"
                f"Available columns: {list(df.columns)}"
            )

        X_raw = df[self.sensor_columns].values.astype(np.float32)
        y_raw = df["activity"].values if "activity" in df.columns else None

        # ── Sliding windows ───────────────────────────────────────────────
        windows, win_labels = [], []
        for i in range(0, len(X_raw) - self.window_size + 1, self.step_size):
            windows.append(X_raw[i : i + self.window_size])
            if y_raw is not None:
                chunk = y_raw[i : i + self.window_size]
                majority = Counter(chunk).most_common(1)[0][0]
                win_labels.append(majority)

        if not windows:
            raise ValueError(
                f"No windows created — data length {len(X_raw)} < window size {self.window_size}"
            )

        X = np.array(windows)           # (N, T, C)
        logger.info("  Windows: %d  shape: %s", len(X), X.shape)

        ch_names = _CHANNEL_NAMES[: X.shape[2]]
        stats    = _compute_stats(X, ch_names)

        # ── Per-class statistics ──────────────────────────────────────────
        per_class = {}
        if win_labels:
            unique_labels = sorted(set(win_labels))
            win_labels_arr = np.array(win_labels)
            for lbl in unique_labels:
                mask = win_labels_arr == lbl
                cls_stats = _compute_stats(X[mask], ch_names)
                per_class[str(lbl)] = {
                    "n_windows": int(mask.sum()),
                    "mean":      cls_stats["mean"],
                    "std":       cls_stats["std"],
                }

        self._baseline = {
            "schema_version": 1,
            **stats,
            "n_channels": int(X.shape[2]),
            "n_samples":  int(X.shape[0]),
            "per_class":  per_class,
            "metadata": {
                "n_windows":    int(X.shape[0]),
                "window_size":  self.window_size,
                "step_size":    self.step_size,
                "n_channels":   int(X.shape[2]),
                "source_csv":   str(data_path),
                "created_at":   datetime.now().isoformat(),
                "sensor_columns": self.sensor_columns,
                "feature_space": "raw",
            },
        }

        # Build Stage-6 baseline in canonical transformed feature space.
        X_transformed = self._build_transformed_windows(X)
        normalized_stats = _compute_stats(X_transformed, ch_names)
        self._normalized_baseline = {
            "schema_version": 1,
            **normalized_stats,
            "n_channels": int(X_transformed.shape[2]),
            "n_samples": int(X_transformed.shape[0]),
            "metadata": {
                "n_windows": int(X_transformed.shape[0]),
                "window_size": self.window_size,
                "step_size": self.step_size,
                "n_channels": int(X_transformed.shape[2]),
                "source_csv": str(data_path),
                "created_at": datetime.now().isoformat(),
                "sensor_columns": self.sensor_columns,
                "feature_space": "transformed",
                "scaler_config_path": str(self.scaler_config_path),
            },
        }
        return self._baseline

    # ------------------------------------------------------------------
    def save(self, path) -> None:
        """Save the full training baseline JSON (includes per-class stats)."""
        if self._baseline is None:
            raise RuntimeError("Call build_from_csv() before save().")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self._baseline, fh, indent=2)
        logger.info("Training baseline saved: %s", path)

    def save_normalized(self, path) -> None:
        """
        Save the normalized baseline JSON used by Stage 6 drift detection.

        This is the same flat-stats format as ``build_normalized_baseline.py``
        produces — it omits per-class detail to keep the file compact.
        """
        if self._normalized_baseline is None:
            raise RuntimeError("Call build_from_csv() before save_normalized().")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self._normalized_baseline, fh, indent=2)
        logger.info("Normalized baseline saved: %s", path)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build training baseline for drift detection (Stage 10)"
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=_PROJECT_ROOT / "data" / "raw" / "all_users_data_labeled.csv",
        help="Labeled training CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_PROJECT_ROOT / "models" / "training_baseline.json",
        help="Full training baseline output path",
    )
    parser.add_argument(
        "--output-normalized",
        type=Path,
        default=_PROJECT_ROOT / "models" / "normalized_baseline.json",
        help="Normalized baseline output path (used by Stage 6 drift detection)",
    )
    args = parser.parse_args()

    builder  = BaselineBuilder()
    baseline = builder.build_from_csv(args.data)
    builder.save(args.output)
    builder.save_normalized(args.output_normalized)

    logger.info(
        "Done — %d windows, %d channels, %d classes",
        baseline["n_samples"],
        baseline["n_channels"],
        len(baseline["per_class"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

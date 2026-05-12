"""
Drift-detection baseline builder.

Canonical location: src/monitoring/baseline_builder.py
Moved from scripts/build_training_baseline.py (2026-04-17).
"""

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.config import ACTIVITY_LABELS, NUM_SENSORS, SENSOR_COLUMNS, WINDOW_SIZE
from src.utils.scaler import CANONICAL_SCALER_PATH, assert_scaler_integrity

logger = logging.getLogger(__name__)

_OVERLAP = 0.5
_STEP = int(WINDOW_SIZE * (1 - _OVERLAP))
_CHANNEL_NAMES = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]


def _compute_stats(X: np.ndarray, channel_names: list) -> dict:
    """Per-channel statistics from a windowed array (N, T, C)."""
    n_windows, _, n_channels = X.shape
    flat = X.reshape(-1, n_channels)

    mean = flat.mean(axis=0).tolist()
    std = flat.std(axis=0).tolist()
    min_val = flat.min(axis=0).tolist()
    max_val = flat.max(axis=0).tolist()
    p5 = np.percentile(flat, 5, axis=0).tolist()
    p25 = np.percentile(flat, 25, axis=0).tolist()
    p50 = np.percentile(flat, 50, axis=0).tolist()
    p75 = np.percentile(flat, 75, axis=0).tolist()
    p95 = np.percentile(flat, 95, axis=0).tolist()

    per_channel = {}
    for i, ch in enumerate(channel_names[:n_channels]):
        per_channel[ch] = {
            "mean": mean[i], "std": std[i],
            "min": min_val[i], "max": max_val[i],
            "p5": p5[i], "p25": p25[i], "p50": p50[i], "p75": p75[i], "p95": p95[i],
        }

    return {
        "mean": mean,
        "std": std,
        "min": min_val,
        "max": max_val,
        "percentiles": {"p5": p5, "p25": p25, "p50": p50, "p75": p75, "p95": p95},
        "per_channel": per_channel,
        "channel_names": channel_names[:n_channels],
    }


class BaselineBuilder:
    """
    Build and persist drift-detection baselines from labeled training data.

    Usage (from Stage 10 — BaselineUpdate component)::

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
        self.sensor_columns = sensor_columns or SENSOR_COLUMNS
        self.window_size = window_size
        self.step_size = step_size or _STEP
        self.scaler_config_path = (
            Path(scaler_config_path) if scaler_config_path else CANONICAL_SCALER_PATH
        )
        self._baseline: Optional[dict] = None
        self._normalized_baseline: Optional[dict] = None

    def _build_transformed_windows(self, X_raw: np.ndarray) -> np.ndarray:
        if not self.scaler_config_path.exists():
            raise FileNotFoundError(
                f"Scaler config not found: {self.scaler_config_path}. "
                "Cannot build transformed-space normalized baseline."
            )
        assert_scaler_integrity(self.scaler_config_path)

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

    def build_from_csv(self, data_path) -> dict:
        data_path = Path(data_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Training data not found: {data_path}")

        logger.info("Loading training CSV: %s", data_path)
        df = pd.read_csv(data_path)
        logger.info("  Rows: %d  |  Columns: %s", len(df), list(df.columns[:8]))

        missing = [c for c in self.sensor_columns if c not in df.columns]
        if missing:
            raise ValueError(
                f"Expected sensor columns not found in CSV: {missing}\n"
                f"Available columns: {list(df.columns)}"
            )

        X_raw = df[self.sensor_columns].values.astype(np.float32)
        y_raw = df["activity"].values if "activity" in df.columns else None

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

        X = np.array(windows)
        logger.info("  Windows: %d  shape: %s", len(X), X.shape)

        ch_names = _CHANNEL_NAMES[: X.shape[2]]
        stats = _compute_stats(X, ch_names)

        per_class = {}
        if win_labels:
            unique_labels = sorted(set(win_labels))
            win_labels_arr = np.array(win_labels)
            for lbl in unique_labels:
                mask = win_labels_arr == lbl
                cls_stats = _compute_stats(X[mask], ch_names)
                per_class[str(lbl)] = {
                    "n_windows": int(mask.sum()),
                    "mean": cls_stats["mean"],
                    "std": cls_stats["std"],
                }

        self._baseline = {
            "schema_version": 1,
            **stats,
            "n_channels": int(X.shape[2]),
            "n_samples": int(X.shape[0]),
            "per_class": per_class,
            "metadata": {
                "n_windows": int(X.shape[0]),
                "window_size": self.window_size,
                "step_size": self.step_size,
                "n_channels": int(X.shape[2]),
                "source_csv": str(data_path),
                "created_at": datetime.now().isoformat(),
                "sensor_columns": self.sensor_columns,
                "feature_space": "raw",
            },
        }

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

    def save(self, path) -> None:
        if self._baseline is None:
            raise RuntimeError("Call build_from_csv() before save().")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self._baseline, fh, indent=2)
        logger.info("Training baseline saved: %s", path)

    def save_normalized(self, path) -> None:
        if self._normalized_baseline is None:
            raise RuntimeError("Call build_from_csv() before save_normalized().")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self._normalized_baseline, fh, indent=2)
        logger.info("Normalized baseline saved: %s", path)

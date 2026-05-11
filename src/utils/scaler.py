"""Canonical scaler loading and integrity assertions.

The final Model A runtime uses the Garmin train-only scaler packaged under
models/production_contract/model_a_final_20260508. Legacy scalers under
data/prepared remain historical/A-B evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


CANONICAL_SCALER_PATH = (
    Path(__file__).resolve().parents[2]
    / "models"
    / "production_contract"
    / "model_a_final_20260508"
    / "garmin_train_scaler.json"
)

LEGACY_ALL_USERS_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "prepared" / "config.json"
)


def assert_scaler_integrity(scaler_path: Path | str) -> bool:
    """Raise AssertionError if a scaler file does not carry the required
    provenance fields. Returns True on success.
    """
    scaler_path = Path(scaler_path)
    if not scaler_path.exists():
        raise FileNotFoundError(f"Scaler file not found: {scaler_path}")

    with open(scaler_path) as f:
        cfg = json.load(f)

    fit_rule = str(cfg.get("fit_rule", "")).lower()
    if "fit_users" not in cfg and "train-only" not in fit_rule:
        raise AssertionError(
            f"{scaler_path} missing train-only provenance. "
            "Expected either fit_users or a train-only fit_rule."
        )
    if "fit_users" in cfg and cfg["fit_users"] != [1, 2, 3, 4]:
        raise AssertionError(
            f"{scaler_path} fit_users={cfg['fit_users']} — expected [1,2,3,4]. "
            "Using a leaky scaler fit on test users will inflate metrics."
        )
    if len(cfg.get("scaler_mean", [])) != 6:
        raise AssertionError(
            f"{scaler_path} scaler_mean has wrong dimension "
            f"(got {len(cfg.get('scaler_mean', []))}, expected 6)."
        )
    if len(cfg.get("scaler_scale", [])) != 6:
        raise AssertionError(
            f"{scaler_path} scaler_scale has wrong dimension "
            f"(got {len(cfg.get('scaler_scale', []))}, expected 6)."
        )
    print(f"Scaler integrity OK: {scaler_path}")
    return True


def load_canonical_scaler() -> Tuple[np.ndarray, np.ndarray, Dict]:
    """Load the final Model A train-only scaler after integrity check.

    Returns:
        mean (6,), scale (6,), full config dict.
    """
    assert_scaler_integrity(CANONICAL_SCALER_PATH)
    with open(CANONICAL_SCALER_PATH) as f:
        cfg = json.load(f)
    mean = np.asarray(cfg["scaler_mean"], dtype=np.float32)
    scale = np.asarray(cfg["scaler_scale"], dtype=np.float32)
    return mean, scale, cfg

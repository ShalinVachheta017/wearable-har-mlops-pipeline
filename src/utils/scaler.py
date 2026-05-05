"""Canonical scaler loading and integrity assertions.

All runtime code paths (train, preprocess, API, monitoring) must go through
`load_canonical_scaler()` or `assert_scaler_integrity()` so that the scaler
used to normalize inputs is provably the same everywhere.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


CANONICAL_SCALER_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "prepared" / "scaler_train_only.json"
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

    if "fit_users" not in cfg:
        raise AssertionError(
            f"{scaler_path} missing required field 'fit_users'. "
            "Refit with scripts/refit_scaler_train_only.py."
        )
    if cfg["fit_users"] != [1, 2, 3, 4]:
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
    """Load the canonical train-only scaler after integrity check.

    Returns:
        mean (6,), scale (6,), full config dict.
    """
    assert_scaler_integrity(CANONICAL_SCALER_PATH)
    with open(CANONICAL_SCALER_PATH) as f:
        cfg = json.load(f)
    mean = np.asarray(cfg["scaler_mean"], dtype=np.float32)
    scale = np.asarray(cfg["scaler_scale"], dtype=np.float32)
    return mean, scale, cfg

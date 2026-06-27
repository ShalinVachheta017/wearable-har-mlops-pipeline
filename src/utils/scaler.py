"""Canonical scaler loading and integrity assertions.

The runtime default is the Garmin train-only scaler packaged with whichever
final runtime contract is currently pointed at by ``src.config.SCALER_CANONICAL``.
As of 2026-05-26 that is the Model D1 freeze; Model A from 2026-05-08 remains
the documented rollback target. Legacy scalers under data/prepared are
historical A/B evidence only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np

# Read the canonical scaler path from the project-level config so we never
# drift from src/config.py when the runtime contract is swapped.
try:
    from src.config import SCALER_CANONICAL as _SCALER_CANONICAL_FROM_CONFIG

    CANONICAL_SCALER_PATH = Path(_SCALER_CANONICAL_FROM_CONFIG)
except Exception:
    # Fallback for environments that import this module before src/config.py
    # is importable (e.g. some test harnesses); keeps a working default.
    CANONICAL_SCALER_PATH = (
        Path(__file__).resolve().parents[2]
        / "models"
        / "runtime_contract"
        / "model_d1_final_20260528"
        / "garmin_train_scaler.json"
    )

LEGACY_ALL_USERS_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "prepared" / "config.json"
)

# Train-only fit_users sets accepted by the integrity check. Extend this tuple
# (and only this tuple) when a new runtime contract is promoted.
_ACCEPTED_FIT_USERS = (
    [1, 2, 3, 4],  # Model A (2026-05-08) — Garmin train users 1-4
    [1, 2, 3, 4, 5, 6],  # Model D1 (2026-05-24, 2026-05-26) — Garmin train users 1-6
)


def _has_train_only_provenance(cfg: Dict) -> bool:
    """Return True if the scaler JSON carries any of the accepted provenance
    signals identifying it as a train-only (non-leaky) Garmin scaler."""
    fit_rule = str(cfg.get("fit_rule", "")).lower()
    fit_scope = str(cfg.get("fit_scope", "")).lower()
    if "fit_users" in cfg:
        return True
    if "train-only" in fit_rule:
        return True
    # Model D1 documents provenance under fit_scope ("Garmin users 1-6 only;
    # User 7 excluded") rather than fit_users. Accept that shape too.
    if "garmin users" in fit_scope and "excluded" in fit_scope:
        return True
    return False


def assert_scaler_integrity(scaler_path: Path | str) -> bool:
    """Raise AssertionError if a scaler file does not carry the required
    provenance fields. Returns True on success.
    """
    scaler_path = Path(scaler_path)
    if not scaler_path.exists():
        raise FileNotFoundError(f"Scaler file not found: {scaler_path}")

    with open(scaler_path) as f:
        cfg = json.load(f)

    if not _has_train_only_provenance(cfg):
        raise AssertionError(
            f"{scaler_path} missing train-only provenance. Expected one of: "
            "(a) fit_users key, (b) 'train-only' in fit_rule, "
            "(c) 'Garmin users …; User 7 excluded' in fit_scope."
        )
    if "fit_users" in cfg and cfg["fit_users"] not in _ACCEPTED_FIT_USERS:
        raise AssertionError(
            f"{scaler_path} fit_users={cfg['fit_users']} — not in accepted set "
            f"{_ACCEPTED_FIT_USERS}. Using a leaky scaler will inflate metrics."
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
    """Load the active train-only scaler after integrity check.

    Returns:
        mean (6,), scale (6,), full config dict.
    """
    assert_scaler_integrity(CANONICAL_SCALER_PATH)
    with open(CANONICAL_SCALER_PATH) as f:
        cfg = json.load(f)
    mean = np.asarray(cfg["scaler_mean"], dtype=np.float32)
    scale = np.asarray(cfg["scaler_scale"], dtype=np.float32)
    return mean, scale, cfg

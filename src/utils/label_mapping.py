"""Shared activity label mapping utilities.

This module provides a single source of truth for class/id mappings used by
inference, evaluation, and API entrypoints.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple


_CANONICAL_ACTIVITY_CLASSES = {
    0: "ear_rubbing",
    1: "forehead_rubbing",
    2: "hair_pulling",
    3: "hand_scratching",
    4: "hand_tapping",
    5: "knuckles_cracking",
    6: "nail_biting",
    7: "nape_rubbing",
    8: "sitting",
    9: "smoking",
    10: "standing",
}


def _default_metadata_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "prepared" / "config.json"


def _validate_mapping(
    activity_to_label: Dict[str, int],
    label_to_activity: Dict[int, str],
) -> None:
    if not activity_to_label or not label_to_activity:
        raise ValueError("Activity mapping cannot be empty.")

    if len(activity_to_label) != len(label_to_activity):
        raise ValueError(
            "Mapping length mismatch between activity_to_label and label_to_activity."
        )

    n_classes = len(activity_to_label)
    expected_ids = set(range(n_classes))
    actual_ids = set(label_to_activity.keys())
    if actual_ids != expected_ids:
        raise ValueError(
            f"Label ids must be contiguous 0..{n_classes - 1}; got {sorted(actual_ids)}"
        )

    for activity, label in activity_to_label.items():
        if label_to_activity.get(label) != activity:
            raise ValueError(
                f"Inconsistent reverse mapping for '{activity}' -> {label}."
            )


def _load_mapping_from_metadata(metadata_path: Path) -> Optional[Tuple[Dict[int, str], Dict[str, int]]]:
    if not metadata_path.exists():
        return None

    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    a2l = data.get("activity_to_label")
    l2a = data.get("label_to_activity")
    if not isinstance(a2l, dict) or not isinstance(l2a, dict):
        return None

    activity_to_label = {str(k): int(v) for k, v in a2l.items()}
    label_to_activity = {int(k): str(v) for k, v in l2a.items()}
    _validate_mapping(activity_to_label, label_to_activity)
    return label_to_activity, activity_to_label


def load_activity_mapping(
    metadata_path: Optional[Path] = None,
) -> Tuple[Dict[int, str], Dict[str, int]]:
    """Load canonical mappings.

    Priority:
    1) data/prepared/config.json mapping if present and valid.
    2) Canonical static fallback defined in this module.
    """

    path = Path(metadata_path) if metadata_path else _default_metadata_path()
    loaded = _load_mapping_from_metadata(path)
    if loaded is not None:
        return loaded

    label_to_activity = dict(_CANONICAL_ACTIVITY_CLASSES)
    activity_to_label = {v: k for k, v in label_to_activity.items()}
    _validate_mapping(activity_to_label, label_to_activity)
    return label_to_activity, activity_to_label


def get_activity_classes(metadata_path: Optional[Path] = None) -> Dict[int, str]:
    """Return id -> activity mapping."""
    label_to_activity, _ = load_activity_mapping(metadata_path=metadata_path)
    return label_to_activity


def get_class_to_index(metadata_path: Optional[Path] = None) -> Dict[str, int]:
    """Return activity -> id mapping."""
    _, activity_to_label = load_activity_mapping(metadata_path=metadata_path)
    return activity_to_label

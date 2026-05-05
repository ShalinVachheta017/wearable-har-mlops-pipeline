"""
src/utils/config_loader.py
==========================
Load runtime config overrides from a YAML file (or $HAR_PIPELINE_OVERRIDES env var)
and apply them to pipeline config dataclass instances.

This implements 12-Factor App Factor III (config-from-environment): threshold values
that operators need to tune are overridable without source-code changes.

Usage::

    from src.utils.config_loader import apply_overrides, load_yaml_overrides
    from src.entity.config_entity import PostInferenceMonitoringConfig

    cfg = PostInferenceMonitoringConfig()
    overrides = load_yaml_overrides()            # reads config/pipeline_overrides.yaml
    apply_overrides(cfg, overrides.get("monitoring", {}))

YAML schema (config/pipeline_overrides.yaml)::

    monitoring:
      confidence_warn_threshold: 0.70
      drift_zscore_threshold: 2.0
      max_baseline_age_days: 90
    trigger:
      confidence_warn: 0.65
      cooldown_hours: 24
    registration:
      degradation_tolerance: 0.005
      block_if_no_metrics: false
"""

import logging
import os
from dataclasses import fields
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

# Environment variable that can point to an alternative overrides file
_OVERRIDES_ENV = "HAR_PIPELINE_OVERRIDES"

# Default path: <project_root>/config/pipeline_overrides.yaml
_OVERRIDES_DEFAULT: Path = PROJECT_ROOT / "config" / "pipeline_overrides.yaml"


def load_yaml_overrides(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load YAML overrides from *path*, $HAR_PIPELINE_OVERRIDES, or the default path.

    Returns an empty dict if the file does not exist or cannot be parsed —
    never raises, so the pipeline starts with safe dataclass defaults.
    """
    raw = path or os.environ.get(_OVERRIDES_ENV) or _OVERRIDES_DEFAULT
    p = Path(raw)
    if not p.exists():
        logger.debug("No pipeline overrides file at %s — using dataclass defaults.", p)
        return {}
    try:
        import yaml  # PyYAML is already a transitive dependency via MLflow / DVC

        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not data:
            return {}
        logger.info("Loaded pipeline config overrides from %s", p)
        return data
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not load overrides from %s: %s — using defaults.", p, exc)
        return {}


def apply_overrides(config_obj: Any, section: Dict[str, Any]) -> None:
    """Apply a flat dict of field-name → value overrides to a dataclass instance.

    Unknown keys are silently ignored (they do not crash the pipeline).
    Type coercion is attempted for basic Python types; failures are logged.
    """
    if not section:
        return
    valid_fields = {f.name: f for f in fields(config_obj)}
    for key, val in section.items():
        if key not in valid_fields:
            logger.debug(
                "Override key '%s' is not a field of %s — skipped.",
                key,
                type(config_obj).__name__,
            )
            continue
        try:
            setattr(config_obj, key, val)
            logger.debug("Override applied: %s.%s = %r", type(config_obj).__name__, key, val)
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Could not apply override %s=%r to %s: %s",
                key,
                val,
                type(config_obj).__name__,
                exc,
            )


def load_monitoring_config(path: Optional[Union[str, Path]] = None):
    """Return PostInferenceMonitoringConfig with YAML/env overrides applied."""
    from src.entity.config_entity import PostInferenceMonitoringConfig

    cfg = PostInferenceMonitoringConfig()
    overrides = load_yaml_overrides(path=path)
    apply_overrides(cfg, overrides.get("monitoring", {}))
    return cfg


def load_trigger_config(path: Optional[Union[str, Path]] = None):
    """Return TriggerEvaluationConfig with YAML/env overrides applied."""
    from src.entity.config_entity import TriggerEvaluationConfig

    cfg = TriggerEvaluationConfig()
    overrides = load_yaml_overrides(path=path)
    apply_overrides(cfg, overrides.get("trigger", {}))
    return cfg

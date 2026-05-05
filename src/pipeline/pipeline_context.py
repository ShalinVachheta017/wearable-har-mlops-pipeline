"""Typed runtime state passed between production-pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class PipelineContext:
    """Stores artifacts and run flags shared by pipeline stages."""

    ingestion_art: Optional[Any] = None
    validation_art: Optional[Any] = None
    transformation_art: Optional[Any] = None
    inference_art: Optional[Any] = None
    evaluation_art: Optional[Any] = None
    monitoring_art: Optional[Any] = None
    trigger_art: Optional[Any] = None
    retraining_art: Optional[Any] = None
    registration_art: Optional[Any] = None
    baseline_art: Optional[Any] = None
    collapse_signals: Dict[str, Any] = field(default_factory=dict)
    dataset_has_labels: bool = False
    dataset_label_column: Optional[str] = None
    dataset_label_source: Optional[str] = None
    update_baseline: bool = False

    def to_safety_dict(self) -> Dict[str, Any]:
        """
        Method Name :   to_safety_dict
        Description :   Convert context to the dictionary shape used by safety helpers.

        Output      :   Returns a plain dictionary.
        On Failure  :   Logs the error and raises the exception.
        """
        return {
            "ingestion_art": self.ingestion_art,
            "validation_art": self.validation_art,
            "transformation_art": self.transformation_art,
            "inference_art": self.inference_art,
            "evaluation_art": self.evaluation_art,
            "monitoring_art": self.monitoring_art,
            "trigger_art": self.trigger_art,
            "retraining_art": self.retraining_art,
            "registration_art": self.registration_art,
            "baseline_art": self.baseline_art,
            "collapse_signals": self.collapse_signals,
            "dataset_has_labels": self.dataset_has_labels,
            "dataset_label_column": self.dataset_label_column,
            "dataset_label_source": self.dataset_label_source,
            "update_baseline": self.update_baseline,
        }

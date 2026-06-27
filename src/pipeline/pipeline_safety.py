"""Collapse-signal and retraining-safety helpers for ProductionPipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.logger import logging

logger = logging.getLogger(__name__)


class PipelineSafetyGate:
    """Centralizes collapse-signal routing and unlabeled retraining safety."""

    def extract_collapse_signals(self, evaluation_art) -> Dict[str, Any]:
        """
        Method Name :   extract_collapse_signals
        Description :   Extract collapse fields from Stage 5 artifact/report evidence.

        Output      :   Returns a collapse-signal dictionary.
        On Failure  :   Logs the error and raises the exception.
        """
        signals: Dict[str, Any] = {
            "dominance_warning": False,
            "dominant_class": None,
            "dominant_pct": None,
            "mean_confidence": None,
            "transition_rate": None,
            "longest_sequence_length": None,
        }
        signals["dominance_warning"] = as_bool(
            getattr(evaluation_art, "distribution_dominance_warning", False)
        )
        dist = getattr(evaluation_art, "distribution_summary", {}) or {}
        conf = getattr(evaluation_art, "confidence_summary", {}) or {}
        signals["dominant_pct"] = getattr(evaluation_art, "dominant_pct", None)
        signals["dominant_class"] = getattr(evaluation_art, "dominant_class", None)
        if signals["dominant_class"] is None:
            signals["dominant_class"] = dist.get("_dominant_class") or dist.get(
                "dominant_class"
            )
        if signals["dominant_pct"] is None:
            signals["dominant_pct"] = dist.get("_dominant_pct") or dist.get(
                "dominant_pct"
            )
        signals["mean_confidence"] = conf.get("mean") or conf.get("mean_confidence")

        self._fill_from_distribution_entries(signals, dist)
        self._fill_from_report_json(
            signals, getattr(evaluation_art, "report_json_path", None)
        )
        self._coerce_numeric(signals)
        return signals

    def augment_collapse_signals(
        self,
        collapse_signals: Optional[Dict[str, Any]],
        monitoring_art,
        ctx: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Method Name :   augment_collapse_signals
        Description :   Merge Stage 4 and Stage 6 collapse evidence for Stage 7.

        Output      :   Returns a merged collapse-signal dictionary.
        On Failure  :   Logs the error and raises the exception.
        """
        signals = dict(collapse_signals or {})
        inference_art = ctx.get("inference_art")
        if inference_art is not None:
            signals["collapse_level"] = getattr(
                inference_art, "collapse_level", signals.get("collapse_level")
            )
            signals["top2_margin_mean"] = (
                getattr(inference_art, "top2_margin_stats", {}) or {}
            ).get("mean", signals.get("top2_margin_mean"))
            if signals.get("dominant_class") is None:
                signals["dominant_class"] = getattr(
                    inference_art, "dominant_class", None
                )
            if signals.get("dominant_pct") is None:
                signals["dominant_pct"] = getattr(inference_art, "dominant_pct", None)

        layer2 = getattr(monitoring_art, "layer2_temporal", {}) or {}
        motion = layer2.get("motion_context", {}) if isinstance(layer2, dict) else {}
        for key in (
            "low_gyro_motion",
            "low_motion_collapse_risk",
            "g_mag_median",
            "g_mag_mean",
            "gravity_dominant_axis",
            "gravity_dominant_axis_value",
        ):
            if key in motion:
                signals[key] = motion[key]
        return signals

    @staticmethod
    def _fill_from_distribution_entries(
        signals: Dict[str, Any], dist: Dict[str, Any]
    ) -> None:
        if signals["dominant_class"] is not None or not dist:
            return
        class_entries = {
            k: v for k, v in dist.items() if isinstance(v, dict) and "percentage" in v
        }
        if not class_entries:
            return
        dominant = max(
            class_entries.items(), key=lambda kv: kv[1].get("percentage", 0.0)
        )
        signals["dominant_class"] = dominant[0]
        if signals["dominant_pct"] is None:
            signals["dominant_pct"] = dominant[1].get("percentage")

    def _fill_from_report_json(self, signals: Dict[str, Any], report_path) -> None:
        if not report_path or not Path(report_path).exists():
            return
        try:
            payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
            d = payload.get("distribution", {})
            t = payload.get("temporal", {})
            c = payload.get("confidence", {})
            self._fill_distribution_from_json(signals, d)
            if signals["mean_confidence"] is None:
                signals["mean_confidence"] = c.get("mean") or c.get("mean_confidence")
            signals["transition_rate"] = t.get(
                "transition_rate", signals["transition_rate"]
            )
            if "longest_sequence_length" in t:
                signals["longest_sequence_length"] = t["longest_sequence_length"]
            elif "longest_sequences" in t and isinstance(t["longest_sequences"], dict):
                values = [
                    v
                    for v in t["longest_sequences"].values()
                    if isinstance(v, (int, float))
                ]
                if values:
                    signals["longest_sequence_length"] = max(values)
        except Exception as exc:
            logger.warning(
                "Could not parse Stage 5 evaluation report for collapse signals: %s",
                exc,
            )

    @staticmethod
    def _fill_distribution_from_json(
        signals: Dict[str, Any], d: Dict[str, Any]
    ) -> None:
        if "_distribution_dominance_warning" in d:
            signals["dominance_warning"] = as_bool(d["_distribution_dominance_warning"])
        elif "distribution_dominance_warning" in d:
            signals["dominance_warning"] = as_bool(d["distribution_dominance_warning"])
        if signals["dominant_class"] is None:
            signals["dominant_class"] = d.get("_dominant_class") or d.get(
                "dominant_class"
            )
        if signals["dominant_pct"] is None:
            signals["dominant_pct"] = d.get("_dominant_pct") or d.get("dominant_pct")

    @staticmethod
    def _coerce_numeric(signals: Dict[str, Any]) -> None:
        for key in (
            "dominant_pct",
            "mean_confidence",
            "transition_rate",
            "longest_sequence_length",
        ):
            try:
                if signals[key] is not None:
                    signals[key] = float(signals[key])
            except Exception:
                pass


def as_bool(value) -> bool:
    """Convert bool-like strings and values into a strict boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)

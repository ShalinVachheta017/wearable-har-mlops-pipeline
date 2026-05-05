"""Optional chunked drift-monitor runner used by the production pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from src.logger import logging

logger = logging.getLogger(__name__)


class PipelineChunkedDriftMonitor:
    """Runs drift checks over production windows in fixed-size chunks."""

    def __init__(self, pipeline_config, *, chunk_size: int = 500):
        self.pipeline_config = pipeline_config
        self.chunk_size = chunk_size

    def run(self, transformation_artifact, inference_artifact) -> Optional[Dict[str, Any]]:
        """
        Method Name :   run
        Description :   Run drift monitor checks in chunks when a reference exists.

        Output      :   Returns a chunked drift summary or None when not applicable.
        On Failure  :   Logs the error and returns an ERROR summary.
        """
        if transformation_artifact is None or inference_artifact is None:
            return None
        x_path = getattr(transformation_artifact, "production_X_path", None)
        if not x_path or not Path(x_path).exists():
            return None
        try:
            from src.monitoring.drift_monitor import DriftMonitor

            reference_path = self.pipeline_config.models_dir / "drift_reference.json"
            if not reference_path.exists():
                return {
                    "status": "SKIPPED",
                    "reason": f"missing drift reference: {reference_path}",
                }

            monitor = DriftMonitor(
                reference_path=reference_path,
                log_path=self.pipeline_config.project_root / "reports" / "drift_log.json",
            )
            windows = np.load(Path(x_path))
            probabilities = self._load_probabilities(inference_artifact, len(windows))
            entries = self._run_chunks(monitor, windows, probabilities)
            max_psi_overall = max(
                (entry.get("max_psi", 0.0) for entry in entries),
                default=0.0,
            )
            any_drift = any(bool(entry.get("drift_detected")) for entry in entries)
            return {
                "status": "OK",
                "chunk_size": self.chunk_size,
                "n_chunks": len(entries),
                "max_psi_overall": float(max_psi_overall),
                "drift_detected": any_drift,
                "action_recommended": (
                    "TRIGGER_RETRAINING_GATE" if any_drift else "CONTINUE_MONITORING"
                ),
                "chunks": entries,
            }
        except Exception as exc:
            logger.warning("Chunked drift monitor check failed: %s", exc)
            return {"status": "ERROR", "reason": str(exc)}

    def _load_probabilities(self, inference_artifact, expected_len: int):
        probs_path = getattr(inference_artifact, "probabilities_npy_path", None)
        if not probs_path or not Path(probs_path).exists():
            return None
        probabilities = np.load(Path(probs_path))
        if len(probabilities) != expected_len:
            return None
        return probabilities

    def _run_chunks(self, monitor, windows, probabilities) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        for start in range(0, len(windows), self.chunk_size):
            end = min(start + self.chunk_size, len(windows))
            chunk_windows = windows[start:end]
            chunk_probs = probabilities[start:end] if probabilities is not None else None
            output = monitor.check(chunk_windows, probabilities=chunk_probs)
            output["chunk_start"] = int(start)
            output["chunk_end"] = int(end)
            entries.append(output)
        return entries

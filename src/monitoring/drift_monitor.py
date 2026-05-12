"""Lightweight drift monitor with PSI, entropy, and post-zscore checks."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

CHANNELS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]


class DriftMonitor:
    def __init__(
        self,
        reference_path: Optional[Path] = None,
        log_path: Optional[Path] = None,
        psi_threshold: float = 0.15,
        post_z_mean_threshold: float = 0.3,
        post_z_std_threshold: float = 1.3,
    ) -> None:
        self.reference_path = Path(reference_path or "models/drift_reference.json")
        self.log_path = Path(log_path or "reports/drift_log.json")
        self.psi_threshold = psi_threshold
        self.post_z_mean_threshold = post_z_mean_threshold
        self.post_z_std_threshold = post_z_std_threshold
        self.reference: Optional[Dict] = None
        if self.reference_path.exists():
            self.reference = json.loads(self.reference_path.read_text(encoding="utf-8"))

    @staticmethod
    def _entropy(probs: np.ndarray) -> np.ndarray:
        p = np.clip(probs, 1e-12, 1.0)
        return -np.sum(p * np.log(p), axis=1)

    @staticmethod
    def _hist_probs(values: np.ndarray, edges: np.ndarray) -> np.ndarray:
        counts, _ = np.histogram(values, bins=edges)
        probs = counts.astype(np.float64) / max(counts.sum(), 1.0)
        return np.clip(probs, 1e-8, 1.0)

    @staticmethod
    def _psi(ref: np.ndarray, cur: np.ndarray) -> float:
        return float(np.sum((cur - ref) * np.log(cur / ref)))

    def calibrate(
        self,
        X_train_windows: np.ndarray,
        train_probabilities: Optional[np.ndarray] = None,
        save: bool = True,
    ) -> Dict:
        """Calibrate reference distributions and thresholds from training windows."""
        if X_train_windows.ndim != 3 or X_train_windows.shape[2] != 6:
            raise ValueError(f"Expected windows shape (N,T,6), got {X_train_windows.shape}")

        flat = X_train_windows.reshape(-1, X_train_windows.shape[2])
        refs: Dict[str, Dict[str, List[float]]] = {}
        means = flat.mean(axis=0).tolist()
        stds = flat.std(axis=0).tolist()

        for i, ch in enumerate(CHANNELS):
            # Quantile bins produce stable PSI even when tails are sparse.
            edges = np.quantile(flat[:, i], np.linspace(0.0, 1.0, 11))
            edges = np.unique(edges)
            if len(edges) < 3:
                edges = np.array(
                    [flat[:, i].min() - 1e-6, flat[:, i].mean(), flat[:, i].max() + 1e-6]
                )
            ref_probs = self._hist_probs(flat[:, i], edges)
            refs[ch] = {
                "bin_edges": edges.tolist(),
                "ref_probs": ref_probs.tolist(),
            }

        if train_probabilities is not None:
            entropy_train = self._entropy(train_probabilities)
            entropy_p95 = float(np.percentile(entropy_train, 95))
        else:
            entropy_p95 = float("nan")

        self.reference = {
            "created_at": datetime.now().isoformat(),
            "channels": CHANNELS,
            "psi_threshold": self.psi_threshold,
            "post_z_mean_threshold": self.post_z_mean_threshold,
            "post_z_std_threshold": self.post_z_std_threshold,
            "entropy_p95": entropy_p95,
            "train_mean": means,
            "train_std": stds,
            "refs": refs,
        }
        if save:
            self.reference_path.parent.mkdir(parents=True, exist_ok=True)
            self.reference_path.write_text(json.dumps(self.reference, indent=2), encoding="utf-8")
        return self.reference

    def check(
        self,
        windows: np.ndarray,
        probabilities: Optional[np.ndarray] = None,
    ) -> Dict:
        """Check drift on incoming windows and append report entry."""
        if self.reference is None:
            raise RuntimeError(
                f"Drift reference not loaded. Run calibrate() first: {self.reference_path}"
            )
        if windows.ndim != 3 or windows.shape[2] != 6:
            raise ValueError(f"Expected windows shape (N,T,6), got {windows.shape}")

        flat = windows.reshape(-1, windows.shape[2])
        per_channel_psi: Dict[str, float] = {}
        per_channel_mean: Dict[str, float] = {}
        per_channel_std: Dict[str, float] = {}
        mean_std_flags: Dict[str, bool] = {}

        for i, ch in enumerate(CHANNELS):
            ref_ch = self.reference["refs"][ch]
            edges = np.asarray(ref_ch["bin_edges"], dtype=np.float64)
            ref_probs = np.asarray(ref_ch["ref_probs"], dtype=np.float64)
            cur_probs = self._hist_probs(flat[:, i], edges)
            psi_val = self._psi(ref_probs, cur_probs)
            per_channel_psi[ch] = float(psi_val)

            mu = float(np.mean(flat[:, i]))
            sd = float(np.std(flat[:, i]))
            per_channel_mean[ch] = mu
            per_channel_std[ch] = sd
            mean_std_flags[ch] = (
                abs(mu) > self.post_z_mean_threshold or sd > self.post_z_std_threshold
            )

        max_psi = float(max(per_channel_psi.values()))
        psi_drift = max_psi > self.psi_threshold
        stats_drift = any(mean_std_flags.values())

        entropy_mean = float("nan")
        entropy_drift = False
        mean_conf = float("nan")
        if probabilities is not None and len(probabilities) > 0:
            entropy = self._entropy(probabilities)
            entropy_mean = float(np.mean(entropy))
            mean_conf = float(np.mean(np.max(probabilities, axis=1)))
            entropy_p95 = self.reference.get("entropy_p95")
            if isinstance(entropy_p95, (int, float)) and not np.isnan(entropy_p95):
                entropy_drift = entropy_mean > float(entropy_p95)

        drift_detected = bool(psi_drift or stats_drift or entropy_drift)
        action = "TRIGGER_RETRAINING_GATE" if drift_detected else "CONTINUE_MONITORING"

        payload = {
            "timestamp": datetime.now().isoformat(),
            "n_windows_checked": int(windows.shape[0]),
            "max_psi": max_psi,
            "psi_per_channel": per_channel_psi,
            "post_z_mean_per_channel": per_channel_mean,
            "post_z_std_per_channel": per_channel_std,
            "post_z_alert_per_channel": mean_std_flags,
            "mean_confidence": mean_conf,
            "entropy_mean": entropy_mean,
            "entropy_threshold_p95": self.reference.get("entropy_p95"),
            "drift_detected": drift_detected,
            "action_recommended": action,
        }
        self._append_log(payload)
        return payload

    def _append_log(self, entry: Dict) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if self.log_path.exists():
            try:
                current = json.loads(self.log_path.read_text(encoding="utf-8"))
                if not isinstance(current, list):
                    current = [current]
            except Exception:
                current = []
        else:
            current = []
        current.append(entry)
        self.log_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

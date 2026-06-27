"""
Model Calibration & Uncertainty Quantification
===============================================

Implements post-hoc calibration and uncertainty estimation for the
HAR inference pipeline.  Raw softmax confidence is known to be
overconfident — this module adds principled uncertainty measures.

Methods implemented:
    1. Temperature Scaling  (Guo et al., 2017)
    2. MC Dropout           (Gal & Ghahramani, 2016)
    3. ECE / Brier Score    (Naeini et al., 2015)
    4. Reliability Diagrams

References:
    - XAI-BayesHAR: Kalman-based UQ for wearable HAR
    - MC Dropout / Ensemble / Evidential comparison papers
    - "When Does Optimizing a Proper Loss Yield Calibration"

Usage:
    from src.calibration import TemperatureScaler, CalibrationEvaluator

    # Post-hoc calibration
    scaler = TemperatureScaler()
    scaler.fit(val_logits, val_labels)
    calibrated_probs = scaler.transform(test_logits)

    # Evaluate calibration quality
    evaluator = CalibrationEvaluator(n_bins=15)
    report = evaluator.evaluate(probs, labels)

Author: HAR MLOps Pipeline
Date: February 2026
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class CalibrationConfig:
    """Configuration for calibration and uncertainty quantification."""

    # Temperature scaling
    initial_temperature: float = 1.5
    lr: float = 0.01
    max_iter: int = 100

    # MC Dropout
    mc_forward_passes: int = 30
    mc_dropout_rate: float = 0.2

    # Evaluation
    n_bins: int = 15
    confidence_warn_threshold: float = 0.65
    entropy_warn_threshold: float = 1.5

    # Output
    save_reliability_diagram: bool = True
    output_dir: Optional[Path] = None


# ============================================================================
# TEMPERATURE SCALING
# ============================================================================


class TemperatureScaler:
    """
    Post-hoc temperature scaling for softmax calibration.

    Learns a single scalar T that divides logits before softmax:
        p_calibrated = softmax(z / T)

    T > 1 → softens (less confident)
    T < 1 → sharpens (more confident)
    T = 1 → no change

    Reference:
        Guo et al. (2017). "On Calibration of Modern Neural Networks."
    """

    def __init__(self, config: CalibrationConfig = None):
        self.config = config or CalibrationConfig()
        self.temperature: float = self.config.initial_temperature
        self.fitted: bool = False

    def fit(
        self,
        logits: np.ndarray,
        labels: np.ndarray,
    ) -> float:
        """
        Learn optimal temperature on a validation set using NLL minimisation.

        Parameters
        ----------
        logits : np.ndarray, shape (N, C)
            Raw logits (pre-softmax outputs) from the model.
        labels : np.ndarray, shape (N,)
            Ground-truth integer labels.

        Returns
        -------
        float
            Optimal temperature.
        """
        from scipy.optimize import minimize_scalar

        def nll_with_temperature(t: float) -> float:
            if t <= 0:
                return 1e10
            scaled = logits / t
            # Numerically stable log-softmax
            max_logits = np.max(scaled, axis=1, keepdims=True)
            log_sum_exp = max_logits.squeeze() + np.log(
                np.sum(np.exp(scaled - max_logits), axis=1)
            )
            log_probs = scaled[np.arange(len(labels)), labels] - log_sum_exp
            return -np.mean(log_probs)

        result = minimize_scalar(
            nll_with_temperature,
            bounds=(0.1, 10.0),
            method="bounded",
            options={"maxiter": self.config.max_iter},
        )
        self.temperature = result.x
        self.fitted = True
        logger.info(
            "Temperature scaling fitted: T=%.4f  (NLL=%.4f)",
            self.temperature,
            result.fun,
        )
        return self.temperature

    def transform(self, logits: np.ndarray) -> np.ndarray:
        """Apply temperature scaling to logits and return calibrated probs."""
        scaled = logits / self.temperature
        # Stable softmax
        exp_scaled = np.exp(scaled - np.max(scaled, axis=1, keepdims=True))
        return exp_scaled / exp_scaled.sum(axis=1, keepdims=True)

    def save(self, path: Path):
        """Persist the learned temperature."""
        import json

        data = {"temperature": self.temperature, "fitted": self.fitted}
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info("Temperature saved: %s", path)

    def load(self, path: Path):
        """Load a previously learned temperature."""
        import json

        with open(path) as f:
            data = json.load(f)
        self.temperature = data["temperature"]
        self.fitted = data.get("fitted", True)
        logger.info("Temperature loaded: T=%.4f from %s", self.temperature, path)


# ============================================================================
# MC DROPOUT UNCERTAINTY
# ============================================================================


class MCDropoutEstimator:
    """
    Monte Carlo Dropout for epistemic uncertainty estimation.

    Runs N stochastic forward passes with dropout enabled, then
    computes predictive entropy and mutual information.

    Reference:
        Gal, Y. & Ghahramani, Z. (2016).
        "Dropout as a Bayesian Approximation: Representing Model Uncertainty
         in Deep Learning."  ICML 2016.
    """

    def __init__(self, config: CalibrationConfig = None):
        self.config = config or CalibrationConfig()

    def estimate(
        self,
        model,
        X: np.ndarray,
        n_passes: int = None,
        batch_size: int = 64,
    ) -> Dict[str, np.ndarray]:
        """
        Run MC Dropout forward passes and compute uncertainty metrics.

        Parameters
        ----------
        model : keras.Model
            The trained model (must contain Dropout layers).
        X : np.ndarray, shape (N, T, C)
            Input windows.
        n_passes : int
            Number of stochastic forward passes (default from config).
        batch_size : int
            Batch size for prediction.

        Returns
        -------
        dict with keys:
            mean_probs      : (N, C) — mean softmax across passes
            predictive_entropy : (N,) — total uncertainty
            mutual_information : (N,) — epistemic uncertainty
            std_probs       : (N, C) — std of softmax across passes
            all_probs       : (n_passes, N, C) — raw stochastic outputs
        """
        try:
            import tensorflow  # noqa: F401
        except ImportError:
            raise ImportError("TensorFlow required for MC Dropout.")

        n = n_passes or self.config.mc_forward_passes
        logger.info("MC Dropout: %d forward passes on %d samples", n, len(X))

        all_probs = []
        for i in range(n):
            # training=True keeps dropout active
            preds = model(X.astype(np.float32), training=True)
            if hasattr(preds, "numpy"):
                preds = preds.numpy()
            all_probs.append(preds)

        all_probs = np.array(all_probs)  # (n_passes, N, C)
        mean_probs = np.mean(all_probs, axis=0)  # (N, C)
        std_probs = np.std(all_probs, axis=0)  # (N, C)

        # Predictive entropy = -sum(mean_p * log(mean_p))
        predictive_entropy = -np.sum(
            mean_probs * np.log(mean_probs + 1e-10), axis=1
        )  # (N,)

        # Expected entropy (aleatoric) = mean[-sum(p * log(p))]
        per_pass_entropy = -np.sum(
            all_probs * np.log(all_probs + 1e-10), axis=2
        )  # (n_passes, N)
        expected_entropy = np.mean(per_pass_entropy, axis=0)  # (N,)

        # Mutual information (epistemic) = predictive - expected
        mutual_information = predictive_entropy - expected_entropy  # (N,)

        return {
            "mean_probs": mean_probs,
            "predictive_entropy": predictive_entropy,
            "mutual_information": mutual_information,
            "expected_entropy": expected_entropy,
            "std_probs": std_probs,
            "all_probs": all_probs,
        }


# ============================================================================
# CALIBRATION EVALUATOR (ECE, Brier, Reliability Diagram)
# ============================================================================


class CalibrationEvaluator:
    """
    Evaluate model calibration quality using standard metrics.

    Metrics:
        ECE  — Expected Calibration Error   (lower is better, 0 = perfect)
        MCE  — Maximum Calibration Error
        Brier Score — Mean squared error of probabilities
        Reliability diagram data for plotting
    """

    def __init__(self, n_bins: int = 15):
        self.n_bins = n_bins

    def expected_calibration_error(
        self,
        probs: np.ndarray,
        labels: np.ndarray,
    ) -> Tuple[float, List[Dict]]:
        """
        Compute ECE and per-bin calibration data.

        ECE = sum_b (n_b / N) * |accuracy_b - confidence_b|

        Parameters
        ----------
        probs : np.ndarray, shape (N, C)
            Predicted probabilities (softmax output).
        labels : np.ndarray, shape (N,)
            Ground-truth integer labels.

        Returns
        -------
        ece : float
        bins : list of dicts with keys
            {bin_lower, bin_upper, n_samples, accuracy, confidence, gap}
        """
        confidences = np.max(probs, axis=1)
        predictions = np.argmax(probs, axis=1)
        accuracies = (predictions == labels).astype(float)

        bin_boundaries = np.linspace(0.0, 1.0, self.n_bins + 1)
        bins = []
        ece = 0.0
        N = len(labels)

        for i in range(self.n_bins):
            lo, hi = bin_boundaries[i], bin_boundaries[i + 1]
            mask = (confidences > lo) & (confidences <= hi)
            n_in_bin = mask.sum()

            if n_in_bin == 0:
                bins.append(
                    {
                        "bin_lower": float(lo),
                        "bin_upper": float(hi),
                        "n_samples": 0,
                        "accuracy": 0.0,
                        "confidence": 0.0,
                        "gap": 0.0,
                    }
                )
                continue

            bin_acc = accuracies[mask].mean()
            bin_conf = confidences[mask].mean()
            gap = abs(bin_acc - bin_conf)
            ece += (n_in_bin / N) * gap

            bins.append(
                {
                    "bin_lower": float(lo),
                    "bin_upper": float(hi),
                    "n_samples": int(n_in_bin),
                    "accuracy": float(bin_acc),
                    "confidence": float(bin_conf),
                    "gap": float(gap),
                }
            )

        return float(ece), bins

    def brier_score(
        self,
        probs: np.ndarray,
        labels: np.ndarray,
    ) -> float:
        """
        Compute multi-class Brier score = mean( sum( (p_c - y_c)^2 ) ).
        """
        n_classes = probs.shape[1]
        one_hot = np.zeros_like(probs)
        one_hot[np.arange(len(labels)), labels] = 1.0
        return float(np.mean(np.sum((probs - one_hot) ** 2, axis=1)))

    def evaluate(
        self,
        probs: np.ndarray,
        labels: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Full calibration evaluation.

        Returns dict with ECE, MCE, Brier, per-bin data, and summary stats.
        """
        ece, bins = self.expected_calibration_error(probs, labels)
        brier = self.brier_score(probs, labels)

        # MCE = max gap across bins
        non_empty = [b for b in bins if b["n_samples"] > 0]
        mce = max(b["gap"] for b in non_empty) if non_empty else 0.0

        confidences = np.max(probs, axis=1)
        predictions = np.argmax(probs, axis=1)
        accuracy = float(np.mean(predictions == labels))

        return {
            "ece": ece,
            "mce": mce,
            "brier_score": brier,
            "accuracy": accuracy,
            "mean_confidence": float(np.mean(confidences)),
            "overconfidence": float(np.mean(confidences)) - accuracy,
            "n_samples": int(len(labels)),
            "n_bins": self.n_bins,
            "bins": bins,
        }

    def save_reliability_diagram(
        self,
        bins: List[Dict],
        output_path: Path,
        title: str = "Reliability Diagram",
    ):
        """Save a reliability diagram as PNG."""
        try:
            import matplotlib.pyplot as plt

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # --- Left: reliability diagram ---
            accs = [b["accuracy"] for b in bins if b["n_samples"] > 0]
            confs = [b["confidence"] for b in bins if b["n_samples"] > 0]
            gaps = [b["gap"] for b in bins if b["n_samples"] > 0]

            ax1.bar(
                confs,
                accs,
                width=1.0 / self.n_bins,
                alpha=0.6,
                label="Accuracy",
                edgecolor="black",
            )
            ax1.bar(
                confs,
                gaps,
                bottom=accs,
                width=1.0 / self.n_bins,
                alpha=0.3,
                color="red",
                label="Gap",
            )
            ax1.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
            ax1.set_xlabel("Mean Predicted Confidence")
            ax1.set_ylabel("Fraction of Positives (Accuracy)")
            ax1.set_title(title)
            ax1.legend()
            ax1.set_xlim(0, 1)
            ax1.set_ylim(0, 1)

            # --- Right: sample count histogram ---
            lowers = [b["bin_lower"] for b in bins]
            counts = [b["n_samples"] for b in bins]
            ax2.bar(lowers, counts, width=1.0 / self.n_bins, edgecolor="black")
            ax2.set_xlabel("Confidence Bin")
            ax2.set_ylabel("Sample Count")
            ax2.set_title("Prediction Distribution")

            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close()
            logger.info("Reliability diagram saved: %s", output_path)

        except ImportError:
            logger.warning("matplotlib not available — skipping diagram.")


# ============================================================================
# UNLABELED CALIBRATION (no ground truth needed)
# ============================================================================


class UnlabeledCalibrationAnalyzer:
    """
    Calibration-style analysis for production data WITHOUT labels.

    Computes proxy calibration signals:
    - Confidence distribution skewness
    - Entropy distribution
    - Softmax margin statistics
    - Temperature-scaled confidence shift

    These don't give true ECE but flag when the model is likely mis-calibrated.
    """

    def analyze(
        self,
        probs: np.ndarray,
        temperature: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Analyze prediction confidence for calibration warning signs.

        Parameters
        ----------
        probs : np.ndarray, shape (N, C)
            Softmax probabilities.
        temperature : float
            Current temperature for reference.

        Returns
        -------
        dict with calibration analysis metrics.
        """
        confidences = np.max(probs, axis=1)
        entropies = -np.sum(probs * np.log(probs + 1e-10), axis=1)

        sorted_probs = np.sort(probs, axis=1)[:, ::-1]
        margins = sorted_probs[:, 0] - sorted_probs[:, 1]

        # Flag: overconfidence warning if >80% of predictions have conf > 0.95
        overconf_ratio = float(np.mean(confidences > 0.95))

        # Flag: underconfidence if mean confidence < 0.5
        underconf_flag = float(np.mean(confidences)) < 0.5

        return {
            "mean_confidence": float(np.mean(confidences)),
            "std_confidence": float(np.std(confidences)),
            "median_confidence": float(np.median(confidences)),
            "mean_entropy": float(np.mean(entropies)),
            "std_entropy": float(np.std(entropies)),
            "mean_margin": float(np.mean(margins)),
            "overconfidence_ratio": overconf_ratio,
            "underconfidence_flag": underconf_flag,
            "high_entropy_ratio": float(np.mean(entropies > 1.5)),
            "low_confidence_ratio": float(np.mean(confidences < 0.65)),
            "temperature": temperature,
            "n_samples": int(len(probs)),
            "calibration_warnings": self._generate_warnings(
                overconf_ratio, underconf_flag, np.mean(entropies)
            ),
        }

    def _generate_warnings(
        self,
        overconf_ratio: float,
        underconf_flag: bool,
        mean_entropy: float,
    ) -> List[str]:
        warnings = []
        if overconf_ratio > 0.80:
            warnings.append(
                f"OVERCONFIDENCE: {overconf_ratio:.0%} of predictions have "
                "confidence > 0.95 — likely mis-calibrated. "
                "Apply temperature scaling."
            )
        if underconf_flag:
            warnings.append(
                "UNDERCONFIDENCE: Mean confidence < 0.50 — model may be "
                "experiencing domain shift or data quality issues."
            )
        if mean_entropy > 1.5:
            warnings.append(
                f"HIGH ENTROPY: Mean entropy = {mean_entropy:.2f} > 1.5 — "
                "model is highly uncertain. Check for OOD data."
            )
        return warnings

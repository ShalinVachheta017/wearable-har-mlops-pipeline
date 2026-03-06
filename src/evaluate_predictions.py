"""
Prediction Evaluation for Mental Health Activity Recognition
==============================================================

This script evaluates inference predictions using classification metrics.
Since production data is UNLABELED, this provides:

1. ANALYSIS (always available):
   - Prediction distribution
   - Confidence analysis
   - Temporal patterns

2. EVALUATION (when labels available):
   - Accuracy, Precision, Recall, F1
   - Confusion matrix
   - Per-class performance

Classification Metrics Explained
--------------------------------

**Accuracy** = (Correct Predictions) / (Total Predictions)
- Simple but can be misleading with imbalanced classes
- If 90% of data is "sitting", predicting all "sitting" gives 90% accuracy

**Precision** = TP / (TP + FP)
- "Of all predictions for class X, how many were correct?"
- High precision = few false positives
- Important when false positives are costly

**Recall** (Sensitivity) = TP / (TP + FN)
- "Of all actual class X samples, how many did we find?"
- High recall = few false negatives
- Important when missing positives is costly

**F1 Score** = 2 * (Precision * Recall) / (Precision + Recall)
- Harmonic mean of precision and recall
- Balanced metric when both matter equally
- Range: 0 (worst) to 1 (best)

**Confusion Matrix**
- Rows = Actual class
- Columns = Predicted class
- Diagonal = Correct predictions
- Off-diagonal = Errors

Confidence Score Analysis
-------------------------

Neural network confidence (softmax output) should be interpreted carefully:

**Calibration**: Is the model's confidence reliable?
- Well-calibrated: 80% confidence → 80% accuracy
- Overconfident: 80% confidence → 60% accuracy (common!)
- Underconfident: 80% confidence → 95% accuracy

**Expected Calibration Error (ECE)**:
- Measures calibration quality
- ECE = Σ |accuracy_i - confidence_i| * (n_i / N)
- Lower is better (0 = perfect calibration)

Author: MLOps Pipeline
Date: December 8, 2025
Version: 1.0.0
"""

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_PREPARED, LOGS_DIR, OUTPUTS_DIR

# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class EvaluationConfig:
    """
    Configuration for evaluation pipeline.

    Attributes:
        predictions_path: Path to predictions CSV
        labels_path: Optional path to ground truth labels
        output_dir: Directory for evaluation reports
        confidence_bins: Number of bins for calibration analysis
    """

    predictions_path: Path = DATA_PREPARED / "predictions"
    labels_path: Optional[Path] = None  # None for unlabeled production data
    output_dir: Path = OUTPUTS_DIR / "evaluation"
    confidence_bins: int = 10

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.predictions_path = Path(self.predictions_path)
        self.output_dir = Path(self.output_dir)
        if self.labels_path:
            self.labels_path = Path(self.labels_path)


# Activity classes (same as inference)
ACTIVITY_CLASSES: Dict[int, str] = {
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


# ============================================================================
# LOGGING SETUP
# ============================================================================


class EvaluationLogger:
    """
    Centralized logging for evaluation pipeline.

    Logs are saved to: logs/evaluation/evaluation_YYYYMMDD_HHMMSS.log
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize logger with file and console handlers."""
        self.log_dir = log_dir or LOGS_DIR / "evaluation"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"evaluation_{timestamp}.log"

        # Configure logger — no own handlers, propagates to root logger
        # which already has console + file handlers (configured in src.logger)
        self.logger = logging.getLogger("evaluation")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        self.logger.info("📝 Evaluation pipeline logging to main pipeline log")

    def get_logger(self) -> logging.Logger:
        return self.logger


# ============================================================================
# PREDICTION ANALYZER (Unlabeled Data)
# ============================================================================


class PredictionAnalyzer:
    """
    Analyze predictions when ground truth is NOT available.

    This is the primary use case for production data.
    Provides insights into:
    - Activity distribution
    - Confidence patterns
    - Temporal behavior
    """

    def __init__(self, config: EvaluationConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def load_predictions(self, csv_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Load predictions from CSV file.

        Args:
            csv_path: Path to predictions CSV. If None, finds latest.

        Returns:
            DataFrame with predictions
        """
        if csv_path is None:
            # Find latest predictions file
            pred_dir = self.config.predictions_path
            csv_files = list(pred_dir.glob("predictions_*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No prediction files found in {pred_dir}")
            csv_path = max(csv_files, key=lambda x: x.stat().st_mtime)

        self.logger.info(f"📂 Loading predictions: {csv_path}")
        df = pd.read_csv(csv_path)
        self.logger.info(f"   Loaded {len(df)} predictions")
        return df

    def analyze_distribution(self, df: pd.DataFrame) -> Dict:
        """
        Analyze activity distribution.

        Returns:
            Dictionary with distribution statistics
        """
        self.logger.info("=" * 60)
        self.logger.info("📊 ACTIVITY DISTRIBUTION")
        self.logger.info("=" * 60)

        dist = df["predicted_activity"].value_counts()
        dist_pct = df["predicted_activity"].value_counts(normalize=True) * 100

        results = {}
        for activity in dist.index:
            count = dist[activity]
            pct = dist_pct[activity]
            results[activity] = {"count": int(count), "percentage": float(pct)}
            self.logger.info(f"   {activity:20s}: {count:5d} ({pct:5.1f}%)")

        # Identify dominant activity
        dominant = dist.idxmax()
        dominant_pct = dist_pct[dominant]

        if dominant_pct > 50:
            self.logger.warning(
                f"⚠️ '{dominant}' dominates ({dominant_pct:.1f}%) - possible imbalance"
            )

        # Structured dominance flag (>95%): informational, does not trigger retraining
        distribution_dominance_warning = dominant_pct > 95.0
        if distribution_dominance_warning:
            self.logger.warning(
                f"⚠️ distribution_dominance_warning=True: '{dominant}' at {dominant_pct:.1f}%"
                " — single-class batch detected (see docs/TRIGGER_POLICY_EXPLANATION.md)"
            )

        results["_dominant_class"] = dominant
        results["_dominant_pct"] = float(dominant_pct)
        results["_distribution_dominance_warning"] = distribution_dominance_warning
        return results

    def analyze_confidence(self, df: pd.DataFrame) -> Dict:
        """
        Analyze confidence score distribution.

        Returns:
            Dictionary with confidence statistics
        """
        self.logger.info("=" * 60)
        self.logger.info("📈 CONFIDENCE ANALYSIS")
        self.logger.info("=" * 60)

        conf = df["confidence"]

        stats = {
            "mean": float(conf.mean()),
            "std": float(conf.std()),
            "min": float(conf.min()),
            "max": float(conf.max()),
            "median": float(conf.median()),
            "q25": float(conf.quantile(0.25)),
            "q75": float(conf.quantile(0.75)),
        }

        self.logger.info(f"   Mean:   {stats['mean']:.3f} ({100*stats['mean']:.1f}%)")
        self.logger.info(f"   Std:    {stats['std']:.3f}")
        self.logger.info(f"   Min:    {stats['min']:.3f} ({100*stats['min']:.1f}%)")
        self.logger.info(f"   Max:    {stats['max']:.3f} ({100*stats['max']:.1f}%)")
        self.logger.info(f"   Median: {stats['median']:.3f}")

        # Confidence level distribution
        levels = df["confidence_level"].value_counts()
        self.logger.info("\n   Confidence Levels:")
        for level in ["HIGH", "MODERATE", "LOW", "UNCERTAIN"]:
            if level in levels.index:
                count = levels[level]
                pct = 100 * count / len(df)
                self.logger.info(f"      {level:10s}: {count:5d} ({pct:5.1f}%)")

        # Per-class confidence
        self.logger.info("\n   Per-Activity Mean Confidence:")
        per_class = (
            df.groupby("predicted_activity")["confidence"].mean().sort_values(ascending=False)
        )
        for activity, mean_conf in per_class.items():
            self.logger.info(f"      {activity:20s}: {100*mean_conf:.1f}%")

        stats["per_class"] = per_class.to_dict()
        stats["levels"] = levels.to_dict()

        return stats

    def analyze_uncertainty(self, df: pd.DataFrame) -> Dict:
        """
        Deep analysis of uncertain predictions.

        Uncertain predictions (confidence < threshold) might indicate:
        1. Ambiguous activities (similar movement patterns)
        2. Transition between activities
        3. Out-of-distribution data
        4. Noise or sensor issues

        Returns:
            Dictionary with uncertainty analysis
        """
        self.logger.info("=" * 60)
        self.logger.info("⚠️ UNCERTAINTY ANALYSIS")
        self.logger.info("=" * 60)

        uncertain = df[df["is_uncertain"] == True]
        n_uncertain = len(uncertain)
        pct_uncertain = 100 * n_uncertain / len(df)

        self.logger.info(f"   Uncertain predictions: {n_uncertain} ({pct_uncertain:.1f}%)")

        if n_uncertain == 0:
            self.logger.info("   ✅ No uncertain predictions!")
            return {"count": 0, "percentage": 0.0}

        # Which activities are uncertain?
        uncertain_by_class = uncertain["predicted_activity"].value_counts()
        self.logger.info("\n   Uncertain by predicted activity:")
        for activity, count in uncertain_by_class.head(5).items():
            self.logger.info(f"      {activity}: {count}")

        # Where are uncertain predictions located?
        if n_uncertain > 10:
            self.logger.info(
                f"\n   First 5 uncertain windows: {uncertain['window_id'].head().tolist()}"
            )
            self.logger.info(
                f"   Last 5 uncertain windows: {uncertain['window_id'].tail().tolist()}"
            )

        # Competing classes (what's the 2nd highest probability?)
        # This requires probability columns
        prob_cols = [c for c in df.columns if c.startswith("prob_")]
        if prob_cols and n_uncertain > 0:
            # For uncertain predictions, show top 2 classes
            self.logger.info("\n   Top competing classes for uncertain predictions:")
            sample_uncertain = uncertain.head(5)
            for idx, row in sample_uncertain.iterrows():
                probs = {col: row[col] for col in prob_cols}
                top2 = sorted(probs.items(), key=lambda x: -x[1])[:2]
                c1 = top2[0][0].replace("prob_", "")
                c2 = top2[1][0].replace("prob_", "")
                p1, p2 = top2[0][1], top2[1][1]
                self.logger.info(
                    f"      Window {row['window_id']}: {c1}({100*p1:.0f}%) vs {c2}({100*p2:.0f}%)"
                )

        return {
            "count": n_uncertain,
            "percentage": pct_uncertain,
            "by_class": uncertain_by_class.to_dict(),
        }

    def analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Analyze temporal patterns in predictions.

        Looking for:
        - Activity transitions
        - Sustained activities
        - Irregular switching

        Returns:
            Dictionary with temporal analysis
        """
        self.logger.info("=" * 60)
        self.logger.info("⏱️ TEMPORAL PATTERN ANALYSIS")
        self.logger.info("=" * 60)

        activities = df["predicted_activity"].tolist()

        # Count transitions
        transitions = sum(
            1 for i in range(1, len(activities)) if activities[i] != activities[i - 1]
        )
        transition_rate = transitions / (len(activities) - 1) if len(activities) > 1 else 0

        self.logger.info(f"   Total windows: {len(activities)}")
        self.logger.info(f"   Activity transitions: {transitions}")
        self.logger.info(f"   Transition rate: {100*transition_rate:.1f}%")

        if transition_rate > 0.5:
            self.logger.warning("   ⚠️ High transition rate - possible instability")

        # Find sustained sequences
        sequences = []
        current_activity = activities[0]
        current_length = 1

        for i in range(1, len(activities)):
            if activities[i] == current_activity:
                current_length += 1
            else:
                sequences.append((current_activity, current_length))
                current_activity = activities[i]
                current_length = 1
        sequences.append((current_activity, current_length))

        # Longest sequences per activity
        longest = {}
        for activity, length in sequences:
            if activity not in longest or length > longest[activity]:
                longest[activity] = length

        self.logger.info("\n   Longest sustained sequences:")
        for activity, length in sorted(longest.items(), key=lambda x: -x[1])[:5]:
            duration_sec = length * 4  # 4 seconds per window (50% overlap @ 200 samples, 50Hz)
            self.logger.info(f"      {activity}: {length} windows ({duration_sec}s)")

        return {
            "n_windows": len(activities),
            "transitions": transitions,
            "transition_rate": transition_rate,
            "longest_sequences": longest,
        }


# ============================================================================
# CLASSIFICATION EVALUATOR (Labeled Data)
# ============================================================================


class ClassificationEvaluator:
    """
    Evaluate predictions against ground truth labels.

    Use this when you have labeled data for validation.
    """

    def __init__(self, config: EvaluationConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def compute_metrics(
        self, y_true: np.ndarray, y_pred: np.ndarray, y_prob: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Compute classification metrics.

        Args:
            y_true: Ground truth labels (n_samples,)
            y_pred: Predicted labels (n_samples,)
            y_prob: Optional probability matrix (n_samples, n_classes)

        Returns:
            Dictionary with all metrics
        """
        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            confusion_matrix,
            f1_score,
            precision_score,
            recall_score,
        )

        self.logger.info("=" * 60)
        self.logger.info("📊 CLASSIFICATION METRICS")
        self.logger.info("=" * 60)

        # Overall metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision_macro = precision_score(y_true, y_pred, average="macro", zero_division=0)
        recall_macro = recall_score(y_true, y_pred, average="macro", zero_division=0)
        f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)

        self.logger.info(f"   Accuracy:  {100*accuracy:.2f}%")
        self.logger.info(f"   Precision: {100*precision_macro:.2f}% (macro)")
        self.logger.info(f"   Recall:    {100*recall_macro:.2f}% (macro)")
        self.logger.info(f"   F1 Score:  {100*f1_macro:.2f}% (macro)")

        # Per-class metrics
        self.logger.info("\n   Per-Class Metrics:")
        report = classification_report(
            y_true,
            y_pred,
            target_names=[ACTIVITY_CLASSES[i] for i in range(11)],
            zero_division=0,
            output_dict=True,
        )

        for class_name in ACTIVITY_CLASSES.values():
            if class_name in report:
                m = report[class_name]
                self.logger.info(
                    f"      {class_name:20s}: P={100*m['precision']:.1f}%, "
                    f"R={100*m['recall']:.1f}%, F1={100*m['f1-score']:.1f}%"
                )

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)

        return {
            "accuracy": accuracy,
            "precision_macro": precision_macro,
            "recall_macro": recall_macro,
            "f1_macro": f1_macro,
            "per_class": report,
            "confusion_matrix": cm.tolist(),
        }

    def compute_calibration(self, y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> Dict:
        """
        Compute calibration metrics.

        Calibration measures how well confidence scores match actual accuracy.

        Args:
            y_true: Ground truth labels
            y_prob: Probability matrix
            n_bins: Number of confidence bins

        Returns:
            Dictionary with calibration metrics
        """
        self.logger.info("=" * 60)
        self.logger.info("📏 CALIBRATION ANALYSIS")
        self.logger.info("=" * 60)

        # Get predicted classes and their confidences
        y_pred = np.argmax(y_prob, axis=1)
        confidences = np.max(y_prob, axis=1)
        correct = (y_pred == y_true).astype(float)

        # Bin by confidence
        bins = np.linspace(0, 1, n_bins + 1)
        ece = 0.0  # Expected Calibration Error

        self.logger.info(
            f"   {'Confidence Range':20s} {'Accuracy':10s} {'Avg Conf':10s} {'Count':8s}"
        )
        self.logger.info("   " + "-" * 50)

        bin_data = []
        for i in range(n_bins):
            bin_lower, bin_upper = bins[i], bins[i + 1]
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)

            if in_bin.sum() > 0:
                bin_accuracy = correct[in_bin].mean()
                bin_confidence = confidences[in_bin].mean()
                bin_count = in_bin.sum()

                # ECE contribution
                ece += (abs(bin_accuracy - bin_confidence) * bin_count) / len(y_true)

                self.logger.info(
                    f"   {bin_lower:.1f} - {bin_upper:.1f}:          "
                    f"{100*bin_accuracy:5.1f}%     {100*bin_confidence:5.1f}%     {bin_count}"
                )

                bin_data.append(
                    {
                        "range": f"{bin_lower:.1f}-{bin_upper:.1f}",
                        "accuracy": bin_accuracy,
                        "avg_confidence": bin_confidence,
                        "count": int(bin_count),
                    }
                )

        self.logger.info("   " + "-" * 50)
        self.logger.info(f"   Expected Calibration Error (ECE): {100*ece:.2f}%")

        if ece < 0.05:
            self.logger.info("   ✅ Model is well-calibrated!")
        elif ece < 0.15:
            self.logger.info("   ⚠️ Model is moderately calibrated")
        else:
            self.logger.warning("   ❌ Model is poorly calibrated - confidence unreliable")

        return {"ece": ece, "bins": bin_data}


# ============================================================================
# REPORT GENERATOR
# ============================================================================


class ReportGenerator:
    """
    Generate evaluation reports.
    """

    def __init__(self, config: EvaluationConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_json_report(self, results: Dict) -> Path:
        """Save results as JSON."""
        output_path = self.config.output_dir / f"evaluation_{self.timestamp}.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        self.logger.info(f"📄 JSON report saved: {output_path}")
        return output_path

    def generate_text_report(self, results: Dict) -> Path:
        """Generate human-readable text report."""
        output_path = self.config.output_dir / f"evaluation_{self.timestamp}.txt"

        with open(output_path, "w") as f:
            f.write("=" * 70 + "\n")
            f.write("PREDICTION EVALUATION REPORT\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 70 + "\n\n")

            # Activity Distribution
            if "distribution" in results:
                f.write("ACTIVITY DISTRIBUTION\n")
                f.write("-" * 40 + "\n")
                for activity, data in results["distribution"].items():
                    f.write(f"{activity:20s}: {data['count']:5d} ({data['percentage']:5.1f}%)\n")
                f.write("\n")

            # Confidence Stats
            if "confidence" in results:
                conf = results["confidence"]
                f.write("CONFIDENCE STATISTICS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Mean:   {100*conf['mean']:.1f}%\n")
                f.write(f"Std:    {100*conf['std']:.1f}%\n")
                f.write(f"Min:    {100*conf['min']:.1f}%\n")
                f.write(f"Max:    {100*conf['max']:.1f}%\n")
                f.write("\n")

            # Uncertainty
            if "uncertainty" in results:
                unc = results["uncertainty"]
                f.write("UNCERTAINTY ANALYSIS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Uncertain predictions: {unc['count']} ({unc['percentage']:.1f}%)\n")
                f.write("\n")

            f.write("=" * 70 + "\n")

        self.logger.info(f"📄 Text report saved: {output_path}")
        return output_path


# ============================================================================
# MAIN PIPELINE
# ============================================================================


class EvaluationPipeline:
    """
    Complete evaluation pipeline orchestrator.
    """

    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.config = config or EvaluationConfig()

        self.log_setup = EvaluationLogger()
        self.logger = self.log_setup.get_logger()

        self.logger.info("=" * 60)
        self.logger.info("📊 EVALUATION PIPELINE INITIALIZED")
        self.logger.info("=" * 60)

    def run(self, predictions_csv: Optional[Path] = None) -> Dict:
        """
        Execute evaluation pipeline.

        Args:
            predictions_csv: Path to predictions CSV (optional)

        Returns:
            Dictionary with all results
        """
        try:
            # Initialize components
            analyzer = PredictionAnalyzer(self.config, self.logger)
            report_gen = ReportGenerator(self.config, self.logger)

            # Load predictions
            df = analyzer.load_predictions(predictions_csv)

            # Run analyses
            results = {
                "timestamp": datetime.now().isoformat(),
                "n_predictions": len(df),
                "distribution": analyzer.analyze_distribution(df),
                "confidence": analyzer.analyze_confidence(df),
                "uncertainty": analyzer.analyze_uncertainty(df),
                "temporal": analyzer.analyze_temporal_patterns(df),
            }

            # Generate reports
            results["output_files"] = {
                "json": str(report_gen.generate_json_report(results)),
                "txt": str(report_gen.generate_text_report(results)),
            }

            self.logger.info("=" * 60)
            self.logger.info("✅ EVALUATION COMPLETE")
            self.logger.info("=" * 60)

            return {"success": True, "results": results}

        except Exception as e:
            self.logger.error(f"❌ Evaluation failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate inference predictions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate latest predictions
  python evaluate_predictions.py

  # Evaluate specific file
  python evaluate_predictions.py --input predictions_20251208.csv
        """,
    )

    parser.add_argument("--input", "-i", type=str, default=None, help="Path to predictions CSV")

    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output directory for reports"
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    config = EvaluationConfig()
    if args.output:
        config.output_dir = Path(args.output)

    pipeline = EvaluationPipeline(config)

    input_path = Path(args.input) if args.input else None
    result = pipeline.run(input_path)

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()

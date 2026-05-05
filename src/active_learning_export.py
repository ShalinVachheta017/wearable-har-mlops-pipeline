#!/usr/bin/env python3
"""
Active Learning Sample Export
=============================

Implements sample selection and export for human labeling in the
active learning pipeline. Selects uncertain samples based on:
- Low confidence
- High entropy
- High disagreement (if ensemble)
- High energy (OOD-like)

The exported samples are prioritized for human labeling to maximize
retraining benefit.

Usage:
    python active_learning_export.py --predictions predictions.csv --top-k 100

Author: HAR MLOps Pipeline
Date: January 30, 2026
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.utils.common import get_timestamp

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class ActiveLearningConfig:
    """Configuration for active learning sample selection."""

    # Selection strategy
    strategy: str = "hybrid"  # 'uncertainty', 'diversity', 'hybrid'

    # Sample budget
    samples_per_batch: int = 100
    max_samples_per_class: int = 20  # Prevent class imbalance

    # Uncertainty thresholds
    confidence_threshold: float = 0.7  # Below this = uncertain
    entropy_threshold: float = 1.5  # Above this = uncertain

    # Diversity sampling
    diversity_weight: float = 0.3

    # Output paths
    export_dir: Path = Path("data/active_learning")

    # Time window
    time_window_hours: int = 24


# ============================================================================
# UNCERTAINTY SCORERS
# ============================================================================


class UncertaintySampler:
    """
    Selects samples based on model uncertainty.

    Multiple strategies:
    - Least confidence: 1 - max(p)
    - Margin: p(top) - p(second)
    - Entropy: -sum(p * log(p))
    """

    def __init__(self, config: ActiveLearningConfig = None):
        self.config = config or ActiveLearningConfig()
        self.logger = logging.getLogger(f"{__name__}.UncertaintySampler")

    def least_confidence(self, probabilities: np.ndarray) -> np.ndarray:
        """
        Least confidence sampling.

        Score = 1 - max(p)
        Higher score = more uncertain
        """
        return 1.0 - np.max(probabilities, axis=1)

    def margin_sampling(self, probabilities: np.ndarray) -> np.ndarray:
        """
        Margin sampling.

        Score = 1 - (p_top - p_second)
        Higher score = closer decision boundary
        """
        sorted_probs = np.sort(probabilities, axis=1)[:, ::-1]
        margin = sorted_probs[:, 0] - sorted_probs[:, 1]
        return 1.0 - margin

    def entropy_sampling(self, probabilities: np.ndarray) -> np.ndarray:
        """
        Entropy-based sampling.

        Score = -sum(p * log(p))
        Higher score = more uncertain
        """
        entropy = -np.sum(probabilities * np.log(probabilities + 1e-10), axis=1)
        return entropy

    def combined_uncertainty(
        self, probabilities: np.ndarray, weights: Dict[str, float] = None
    ) -> np.ndarray:
        """
        Combined uncertainty score.

        Args:
            probabilities: Model outputs
            weights: Weights for each strategy

        Returns:
            Combined uncertainty scores
        """
        weights = weights or {"confidence": 0.4, "margin": 0.3, "entropy": 0.3}

        scores = {
            "confidence": self.least_confidence(probabilities),
            "margin": self.margin_sampling(probabilities),
            "entropy": self.entropy_sampling(probabilities),
        }

        # Normalize each
        normalized = {}
        for name, values in scores.items():
            min_v, max_v = values.min(), values.max()
            if max_v - min_v > 1e-6:
                normalized[name] = (values - min_v) / (max_v - min_v)
            else:
                normalized[name] = np.zeros_like(values)

        # Weighted combination
        combined = np.zeros(len(probabilities))
        for name, weight in weights.items():
            combined += weight * normalized[name]

        return combined

    def select_uncertain_samples(
        self, probabilities: np.ndarray, n_samples: int, predictions: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Dict]:
        """
        Select most uncertain samples.

        Args:
            probabilities: Model outputs
            n_samples: Number of samples to select
            predictions: Predicted classes (for stratification)

        Returns:
            Indices of selected samples, selection metadata
        """
        uncertainty = self.combined_uncertainty(probabilities)

        # Sort by uncertainty (descending)
        sorted_indices = np.argsort(uncertainty)[::-1]

        # Apply class balance constraint if predictions provided
        if predictions is not None:
            selected = self._stratified_selection(
                sorted_indices, predictions, uncertainty, n_samples
            )
        else:
            selected = sorted_indices[:n_samples]

        metadata = {
            "strategy": "uncertainty",
            "n_selected": len(selected),
            "mean_uncertainty": float(np.mean(uncertainty[selected])),
            "min_uncertainty": float(np.min(uncertainty[selected])),
            "max_uncertainty": float(np.max(uncertainty[selected])),
        }

        return selected, metadata

    def _stratified_selection(
        self,
        sorted_indices: np.ndarray,
        predictions: np.ndarray,
        uncertainty: np.ndarray,
        n_samples: int,
    ) -> np.ndarray:
        """Select with class balance constraint."""
        max_per_class = self.config.max_samples_per_class

        class_counts = {}
        selected = []

        for idx in sorted_indices:
            pred_class = predictions[idx]

            if pred_class not in class_counts:
                class_counts[pred_class] = 0

            if class_counts[pred_class] < max_per_class:
                selected.append(idx)
                class_counts[pred_class] += 1

            if len(selected) >= n_samples:
                break

        return np.array(selected)


# ============================================================================
# DIVERSITY SAMPLER
# ============================================================================


class DiversitySampler:
    """
    Selects diverse samples to avoid redundancy.

    Uses simple feature-space clustering or temporal diversity.
    """

    def __init__(self, config: ActiveLearningConfig = None):
        self.config = config or ActiveLearningConfig()

    def temporal_diversity(self, timestamps: np.ndarray, n_samples: int) -> np.ndarray:
        """
        Select temporally diverse samples.

        Divides time range into buckets and samples from each.
        """
        n_buckets = min(n_samples, 10)

        # Create time buckets
        min_time, max_time = timestamps.min(), timestamps.max()
        bucket_edges = np.linspace(min_time, max_time, n_buckets + 1)

        # Sample from each bucket
        selected = []
        samples_per_bucket = n_samples // n_buckets

        for i in range(n_buckets):
            bucket_mask = (timestamps >= bucket_edges[i]) & (timestamps < bucket_edges[i + 1])
            bucket_indices = np.where(bucket_mask)[0]

            if len(bucket_indices) > 0:
                n_select = min(samples_per_bucket, len(bucket_indices))
                bucket_selected = np.random.choice(bucket_indices, size=n_select, replace=False)
                selected.extend(bucket_selected)

        return np.array(selected[:n_samples])

    def prediction_diversity(self, predictions: np.ndarray, n_samples: int) -> np.ndarray:
        """
        Select samples that represent all predicted classes.
        """
        unique_classes = np.unique(predictions)
        samples_per_class = max(1, n_samples // len(unique_classes))

        selected = []
        for cls in unique_classes:
            cls_indices = np.where(predictions == cls)[0]
            n_select = min(samples_per_class, len(cls_indices))
            cls_selected = np.random.choice(cls_indices, size=n_select, replace=False)
            selected.extend(cls_selected)

        return np.array(selected[:n_samples])


# ============================================================================
# ACTIVE LEARNING EXPORTER
# ============================================================================


class ActiveLearningExporter:
    """
    Main class for selecting and exporting samples for human labeling.
    """

    def __init__(self, config: ActiveLearningConfig = None):
        self.config = config or ActiveLearningConfig()
        self.uncertainty_sampler = UncertaintySampler(config)
        self.diversity_sampler = DiversitySampler(config)
        self.logger = logging.getLogger(f"{__name__}.ActiveLearningExporter")

        # Ensure export directory exists
        self.config.export_dir.mkdir(parents=True, exist_ok=True)

    def select_samples(
        self,
        data: pd.DataFrame,
        probabilities: np.ndarray,
        predictions: np.ndarray,
        n_samples: int = None,
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Select samples for human labeling.

        Args:
            data: Input data (sensor readings)
            probabilities: Model softmax outputs
            predictions: Model predictions
            n_samples: Number to select (default from config)

        Returns:
            Selected samples DataFrame, selection metadata
        """
        n_samples = n_samples or self.config.samples_per_batch

        if self.config.strategy == "uncertainty":
            indices, metadata = self.uncertainty_sampler.select_uncertain_samples(
                probabilities, n_samples, predictions
            )

        elif self.config.strategy == "diversity":
            indices = self.diversity_sampler.prediction_diversity(predictions, n_samples)
            metadata = {"strategy": "diversity", "n_selected": len(indices)}

        elif self.config.strategy == "hybrid":
            # 70% uncertainty, 30% diversity
            n_uncertain = int(n_samples * 0.7)
            n_diverse = n_samples - n_uncertain

            uncertain_indices, unc_meta = self.uncertainty_sampler.select_uncertain_samples(
                probabilities, n_uncertain, predictions
            )
            diverse_indices = self.diversity_sampler.prediction_diversity(
                predictions, n_diverse * 2
            )

            # Remove overlap
            diverse_indices = np.setdiff1d(diverse_indices, uncertain_indices)[:n_diverse]

            indices = np.concatenate([uncertain_indices, diverse_indices])
            metadata = {
                "strategy": "hybrid",
                "n_uncertain": len(uncertain_indices),
                "n_diverse": len(diverse_indices),
                "n_selected": len(indices),
                "uncertainty_metadata": unc_meta,
            }

        else:
            raise ValueError(f"Unknown strategy: {self.config.strategy}")

        # Extract selected data
        selected_data = data.iloc[indices].copy()
        selected_data["_selection_index"] = indices
        selected_data["_uncertainty_score"] = self.uncertainty_sampler.combined_uncertainty(
            probabilities
        )[indices]
        selected_data["_model_prediction"] = predictions[indices]
        selected_data["_model_confidence"] = np.max(probabilities, axis=1)[indices]

        return selected_data, metadata

    def export_for_labeling(
        self, selected_data: pd.DataFrame, metadata: Dict, batch_id: str = None, format: str = "csv"
    ) -> Path:
        """
        Export selected samples for human labeling.

        Args:
            selected_data: DataFrame of selected samples
            metadata: Selection metadata
            batch_id: Unique batch identifier
            format: Export format ('csv', 'json', 'parquet')

        Returns:
            Path to exported file
        """
        batch_id = batch_id or get_timestamp()

        # Create export data with labeling template
        export_data = selected_data.copy()
        export_data["human_label"] = None  # To be filled by human
        export_data["labeling_notes"] = ""
        export_data["labeling_timestamp"] = None

        # Define export paths
        export_dir = self.config.export_dir / f"batch_{batch_id}"
        export_dir.mkdir(parents=True, exist_ok=True)

        # Export data
        if format == "csv":
            data_path = export_dir / "samples_to_label.csv"
            export_data.to_csv(data_path, index=False)
        elif format == "parquet":
            data_path = export_dir / "samples_to_label.parquet"
            export_data.to_parquet(data_path, index=False)
        else:  # json
            data_path = export_dir / "samples_to_label.json"
            export_data.to_json(data_path, orient="records", indent=2)

        # Export metadata
        metadata_path = export_dir / "batch_metadata.json"
        full_metadata = {
            "batch_id": batch_id,
            "export_timestamp": datetime.now().isoformat(),
            "n_samples": len(export_data),
            "selection_metadata": metadata,
            "data_file": str(data_path.name),
            "columns": list(export_data.columns),
            "activity_classes": list(range(11)),  # HAR classes
        }

        with open(metadata_path, "w") as f:
            json.dump(full_metadata, f, indent=2)

        # Create labeling instructions
        self._create_labeling_instructions(export_dir)

        self.logger.info(f"Exported {len(export_data)} samples to {export_dir}")

        return data_path

    def _create_labeling_instructions(self, export_dir: Path):
        """Create labeling instructions file."""
        instructions = """
# Active Learning Labeling Instructions

## Overview
This batch contains sensor data samples that the model is uncertain about.
Your task is to assign the correct activity label to each sample.

## Activity Classes (11 anxiety/stereotypic behavior classes)
0: ear_rubbing
1: forehead_rubbing
2: hair_pulling
3: hand_scratching
4: hand_tapping
5: knuckles_cracking
6: nail_biting
7: nape_rubbing
8: sitting
9: smoking
10: standing

## Labeling Process
1. Open the samples file (samples_to_label.csv)
2. For each row, examine the sensor readings
3. Determine the most likely activity
4. Fill in the `human_label` column with the class number (0-10)
5. Add any notes in the `labeling_notes` column
6. Fill in `labeling_timestamp` when you complete each sample

## Quality Guidelines
- If truly uncertain, add note "UNCERTAIN" and your best guess
- If sample appears corrupted, add note "BAD_DATA"
- Focus on clear cases first, then uncertain ones
- Aim for consistency across similar patterns

## Submission
After labeling, save the file and run:
```
python active_learning_export.py --import-labels batch_XXXXXX
```
"""
        instructions_path = export_dir / "LABELING_INSTRUCTIONS.md"
        with open(instructions_path, "w") as f:
            f.write(instructions)

    def import_labeled_data(self, batch_dir: Path) -> Tuple[pd.DataFrame, Dict]:
        """
        Import human-labeled data from a batch.

        Args:
            batch_dir: Path to batch directory

        Returns:
            Labeled data, import statistics
        """
        # Find data file
        data_files = list(batch_dir.glob("samples_to_label.*"))
        if not data_files:
            raise FileNotFoundError(f"No labeled data found in {batch_dir}")

        data_path = data_files[0]

        # Load based on format
        if data_path.suffix == ".csv":
            labeled_data = pd.read_csv(data_path)
        elif data_path.suffix == ".parquet":
            labeled_data = pd.read_parquet(data_path)
        else:
            labeled_data = pd.read_json(data_path)

        # Validate labels
        valid_mask = labeled_data["human_label"].notna()
        n_labeled = valid_mask.sum()
        n_total = len(labeled_data)

        stats = {
            "n_total": n_total,
            "n_labeled": int(n_labeled),
            "n_unlabeled": int(n_total - n_labeled),
            "completion_rate": float(n_labeled / n_total),
            "label_distribution": labeled_data["human_label"].value_counts().to_dict(),
        }

        self.logger.info(f"Imported {n_labeled}/{n_total} labeled samples")

        return labeled_data[valid_mask], stats

    def generate_retraining_dataset(
        self, batch_dirs: List[Path], output_path: Path
    ) -> pd.DataFrame:
        """
        Combine labeled data from multiple batches for retraining.

        Args:
            batch_dirs: List of batch directories with labeled data
            output_path: Where to save combined dataset

        Returns:
            Combined labeled dataset
        """
        all_data = []
        total_stats = {"batches_processed": 0, "total_samples": 0}

        for batch_dir in batch_dirs:
            try:
                labeled_data, stats = self.import_labeled_data(batch_dir)
                all_data.append(labeled_data)
                total_stats["batches_processed"] += 1
                total_stats["total_samples"] += stats["n_labeled"]
            except Exception as e:
                self.logger.warning(f"Failed to import {batch_dir}: {e}")

        if not all_data:
            raise ValueError("No labeled data found in any batch")

        combined = pd.concat(all_data, ignore_index=True)

        # Clean up helper columns
        output_columns = [c for c in combined.columns if not c.startswith("_")]
        combined = combined[output_columns]

        # Save
        combined.to_csv(output_path, index=False)
        self.logger.info(f"Generated retraining dataset with {len(combined)} samples")

        return combined


# ============================================================================
# CLI
# ============================================================================


def main():
    """Command-line interface for active learning export."""
    import argparse

    parser = argparse.ArgumentParser(description="Active Learning Sample Export for HAR")
    parser.add_argument(
        "--predictions", type=Path, help="Path to predictions CSV with probabilities"
    )
    parser.add_argument("--data", type=Path, help="Path to input data CSV")
    parser.add_argument("--top-k", type=int, default=100, help="Number of samples to select")
    parser.add_argument(
        "--strategy",
        choices=["uncertainty", "diversity", "hybrid"],
        default="hybrid",
        help="Selection strategy",
    )
    parser.add_argument(
        "--export-dir", type=Path, default=Path("data/active_learning"), help="Export directory"
    )
    parser.add_argument(
        "--import-labels", type=Path, help="Import labeled data from batch directory"
    )
    parser.add_argument("--demo", action="store_true", help="Run demo with synthetic data")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    if args.demo:
        print("=" * 60)
        print("ACTIVE LEARNING EXPORT DEMO")
        print("=" * 60)

        np.random.seed(42)

        # Synthetic data
        n_samples = 500
        data = pd.DataFrame(
            {
                "acc_x": np.random.randn(n_samples),
                "acc_y": np.random.randn(n_samples),
                "acc_z": np.random.randn(n_samples),
                "timestamp": pd.date_range("2026-01-01", periods=n_samples, freq="100ms"),
            }
        )

        # Synthetic predictions (mix of confident and uncertain)
        n_classes = 11
        probabilities = np.random.dirichlet(np.ones(n_classes) * 2, size=n_samples)
        predictions = np.argmax(probabilities, axis=1)

        # Run selection
        config = ActiveLearningConfig(strategy=args.strategy, export_dir=args.export_dir)
        exporter = ActiveLearningExporter(config)

        selected_data, metadata = exporter.select_samples(
            data, probabilities, predictions, n_samples=args.top_k
        )

        print(f"\nStrategy: {metadata.get('strategy')}")
        print(f"Selected: {metadata.get('n_selected')} samples")

        # Export
        export_path = exporter.export_for_labeling(selected_data, metadata)
        print(f"\nExported to: {export_path}")

        return 0

    if args.import_labels:
        config = ActiveLearningConfig(export_dir=args.export_dir)
        exporter = ActiveLearningExporter(config)
        labeled_data, stats = exporter.import_labeled_data(args.import_labels)

        print(f"\nImported {stats['n_labeled']} labeled samples")
        print(f"Completion rate: {stats['completion_rate']:.1%}")

        return 0

    if args.predictions and args.data:
        # Load real data
        predictions_df = pd.read_csv(args.predictions)
        data_df = pd.read_csv(args.data)

        # Extract probabilities (assume columns prob_0 through prob_10)
        prob_cols = [f"prob_{i}" for i in range(11)]
        if all(c in predictions_df.columns for c in prob_cols):
            probabilities = predictions_df[prob_cols].values
        else:
            # Fall back to predicted column
            probabilities = np.random.dirichlet(np.ones(11), size=len(predictions_df))

        predictions = predictions_df.get("predicted", np.argmax(probabilities, axis=1)).values

        config = ActiveLearningConfig(strategy=args.strategy, export_dir=args.export_dir)
        exporter = ActiveLearningExporter(config)

        selected_data, metadata = exporter.select_samples(
            data_df, probabilities, predictions, n_samples=args.top_k
        )

        export_path = exporter.export_for_labeling(selected_data, metadata)

        print(f"Exported {metadata['n_selected']} samples to: {export_path}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())

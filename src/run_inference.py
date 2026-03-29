"""
Inference Pipeline for Mental Health Activity Recognition
==========================================================

This script performs inference using the pre-trained 1D-CNN-BiLSTM model
on preprocessed production sensor data.

Scientific Background
---------------------
The model uses softmax activation in the final layer, which converts raw 
logits into probability distributions. The softmax function:

    P(class_i) = exp(z_i) / Σ exp(z_j)

where z_i is the raw output (logit) for class i. This gives us:
- Probabilities that sum to 1.0
- Interpretable confidence scores
- Higher probability = higher model confidence

Confidence Interpretation
-------------------------
Neural network confidence scores should be interpreted carefully:

| Confidence | Interpretation | Recommendation |
|------------|----------------|----------------|
| > 90%      | HIGH           | Trust prediction |
| 70-90%     | MODERATE       | Likely correct |
| 50-70%     | LOW            | Review manually |
| < 50%      | VERY LOW       | Uncertain, flag |

Note: High confidence doesn't guarantee correctness (overconfident models).
Calibration analysis in evaluate_predictions.py helps assess reliability.

Inference Modes
---------------
1. BATCH MODE: Process all windows at once (faster, higher throughput)
   - Best for: Offline analysis, weekly data processing
   - Pros: GPU optimization, faster overall
   - Cons: Requires all data upfront

2. REAL-TIME MODE: Process windows one at a time
   - Best for: Streaming data, live monitoring
   - Pros: Immediate predictions, lower latency
   - Cons: Less efficient, more overhead

For weekly data collection (your case), BATCH MODE is recommended.

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

import mlflow
import numpy as np
import pandas as pd
from mlflow.tracking import MlflowClient

from src.utils.label_mapping import get_activity_classes, get_class_to_index

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_PREPARED, LOGS_DIR, PRETRAINED_MODEL, PROJECT_ROOT

# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class InferenceConfig:
    """
    Configuration for inference pipeline.

    Attributes:
        model_path: Path to the trained Keras model
        input_path: Path to preprocessed .npy file
        output_dir: Directory for saving predictions
        batch_size: Batch size for inference (larger = faster, more memory)
        confidence_threshold: Below this, flag as uncertain
        mode: 'batch' or 'realtime'
    """

    model_path: Path = PRETRAINED_MODEL
    input_path: Path = DATA_PREPARED / "production_X.npy"
    output_dir: Path = DATA_PREPARED / "predictions"
    batch_size: int = 32
    confidence_threshold: float = 0.50  # 50% threshold for uncertainty
    mode: str = "batch"  # 'batch' or 'realtime'

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.model_path = Path(self.model_path)
        self.input_path = Path(self.input_path)
        self.output_dir = Path(self.output_dir)


# Activity class mapping (single source of truth)
ACTIVITY_CLASSES: Dict[int, str] = get_activity_classes()

# Reverse mapping for convenience
CLASS_TO_INDEX: Dict[str, int] = get_class_to_index()


# ============================================================================
# LOGGING SETUP
# ============================================================================


class InferenceLogger:
    """
    Centralized logging for inference pipeline.

    Logs are saved to: logs/inference/inference_YYYYMMDD_HHMMSS.log

    Log Levels:
        DEBUG: Detailed information for debugging
        INFO: General operational information
        WARNING: Something unexpected but not critical
        ERROR: Something failed
        CRITICAL: System cannot continue
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize logger with file and console handlers.

        Args:
            log_dir: Directory for log files (default: logs/inference/)
        """
        self.log_dir = log_dir or LOGS_DIR / "inference"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create unique log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"inference_{timestamp}.log"

        # Configure logger — no own handlers, propagates to root logger
        # which already has console + file handlers (configured in src.logger)
        self.logger = logging.getLogger("inference")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        self.logger.info("📝 Inference pipeline logging to main pipeline log")

    def get_logger(self) -> logging.Logger:
        """Return the configured logger."""
        return self.logger


# ============================================================================
# MODEL LOADER
# ============================================================================


class ModelLoader:
    """
    Load and validate the pre-trained Keras model.

    The model architecture (1D-CNN-BiLSTM):
    - Input: (batch_size, 200, 6) - 200 timesteps, 6 sensors
    - Conv1D layers: Extract local patterns
    - BiLSTM layers: Capture temporal dependencies
    - Dense layers: Classification
    - Output: (batch_size, 11) - probabilities for 11 classes
    """

    def __init__(self, config: InferenceConfig, logger: logging.Logger):
        """
        Initialize model loader.

        Args:
            config: Inference configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.model = None

    def load(self):
        """
        Load the Keras model from disk.

        Returns:
            Loaded Keras model

        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If model has unexpected architecture
        """
        self.logger.info("=" * 60)
        self.logger.info("🧠 LOADING MODEL")
        self.logger.info("=" * 60)

        if not self.config.model_path.exists():
            self.logger.error(f"❌ Model not found: {self.config.model_path}")
            raise FileNotFoundError(f"Model file not found: {self.config.model_path}")

        self.logger.info(f"📂 Model path: {self.config.model_path}")

        # Import TensorFlow here to avoid slow startup if not needed
        try:
            import tensorflow as tf

            self.logger.debug(f"TensorFlow version: {tf.__version__}")
        except ImportError as e:
            self.logger.error("❌ TensorFlow not installed!")
            raise ImportError("TensorFlow is required. Install with: pip install tensorflow") from e

        # Load model
        self.logger.info("⏳ Loading model (this may take a moment)...")
        self.model = tf.keras.models.load_model(self.config.model_path)

        # Validate architecture
        input_shape = self.model.input_shape
        output_shape = self.model.output_shape

        self.logger.info("✅ Model loaded successfully!")
        self.logger.info(f"   Input shape: {input_shape}")
        self.logger.info(f"   Output shape: {output_shape}")
        self.logger.info(f"   Parameters: {self.model.count_params():,}")

        # Validate expected shapes
        expected_input = (None, 200, 6)
        expected_output = (None, 11)

        if input_shape != expected_input:
            self.logger.warning(
                f"⚠️ Unexpected input shape: {input_shape}, expected {expected_input}"
            )

        if output_shape != expected_output:
            self.logger.warning(
                f"⚠️ Unexpected output shape: {output_shape}, expected {expected_output}"
            )

        return self.model


# ============================================================================
# DATA LOADER
# ============================================================================


class DataLoader:
    """
    Load preprocessed sensor data for inference.

    Expected input format:
    - NumPy array with shape (n_windows, 200, 6)
    - Already normalized using training scaler
    - 6 channels: Ax, Ay, Az, Gx, Gy, Gz
    """

    def __init__(self, config: InferenceConfig, logger: logging.Logger):
        """
        Initialize data loader.

        Args:
            config: Inference configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.data = None
        self.metadata = {}

    def load(self) -> np.ndarray:
        """
        Load preprocessed data from .npy file.

        Returns:
            NumPy array of shape (n_windows, 200, 6)

        Raises:
            FileNotFoundError: If data file doesn't exist
            ValueError: If data has unexpected shape
        """
        self.logger.info("=" * 60)
        self.logger.info("📊 LOADING DATA")
        self.logger.info("=" * 60)

        if not self.config.input_path.exists():
            self.logger.error(f"❌ Data not found: {self.config.input_path}")
            raise FileNotFoundError(f"Data file not found: {self.config.input_path}")

        self.logger.info(f"📂 Data path: {self.config.input_path}")

        # Load data
        self.data = np.load(self.config.input_path)

        self.logger.info("✅ Data loaded successfully!")
        self.logger.info(f"   Shape: {self.data.shape}")
        self.logger.info(f"   Dtype: {self.data.dtype}")
        self.logger.info(f"   Memory: {self.data.nbytes / 1024 / 1024:.2f} MB")

        # Validate shape
        if len(self.data.shape) != 3:
            raise ValueError(f"Expected 3D array, got shape {self.data.shape}")

        n_windows, timesteps, channels = self.data.shape

        if timesteps != 200:
            self.logger.warning(f"⚠️ Unexpected timesteps: {timesteps}, expected 200")

        if channels != 6:
            self.logger.warning(f"⚠️ Unexpected channels: {channels}, expected 6")

        # Store metadata
        self.metadata = {
            "n_windows": n_windows,
            "timesteps": timesteps,
            "channels": channels,
            "source_file": str(self.config.input_path),
            "load_time": datetime.now().isoformat(),
        }

        # Quick stats
        self.logger.debug(f"   Mean: {self.data.mean():.4f}")
        self.logger.debug(f"   Std: {self.data.std():.4f}")
        self.logger.debug(f"   Min: {self.data.min():.4f}")
        self.logger.debug(f"   Max: {self.data.max():.4f}")

        return self.data


# ============================================================================
# INFERENCE ENGINE
# ============================================================================


class InferenceEngine:
    """
    Core inference engine for activity recognition.

    Supports two modes:
    1. Batch inference: Process all data at once
    2. Real-time inference: Process one window at a time

    Scientific Note on Confidence Scores
    ------------------------------------
    The softmax output gives us P(class|input), but this is NOT calibrated
    probability. A model might say 90% confidence but only be correct 70%
    of the time. This is called "overconfidence."

    For well-calibrated models:
    - If model says 80% confidence, it should be correct 80% of the time

    We use a conservative threshold (50%) and recommend manual review
    for low-confidence predictions.
    """

    def __init__(self, model, config: InferenceConfig, logger: logging.Logger):
        """
        Initialize inference engine.

        Args:
            model: Loaded Keras model
            config: Inference configuration
            logger: Logger instance
        """
        self.model = model
        self.config = config
        self.logger = logger

    def predict_batch(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform batch inference on all windows.

        This is the RECOMMENDED mode for your use case (weekly data).

        Args:
            data: Array of shape (n_windows, 200, 6)

        Returns:
            Tuple of:
            - predictions: Array of predicted class indices (n_windows,)
            - probabilities: Array of class probabilities (n_windows, 11)
        """
        self.logger.info("=" * 60)
        self.logger.info("🚀 BATCH INFERENCE")
        self.logger.info("=" * 60)

        n_windows = len(data)
        self.logger.info(f"📊 Processing {n_windows} windows...")
        self.logger.info(f"   Batch size: {self.config.batch_size}")

        start_time = datetime.now()

        # Get raw probabilities from softmax layer
        self.logger.debug("Running model.predict()...")
        probabilities = self.model.predict(data, batch_size=self.config.batch_size, verbose=0)

        # Get predicted class (highest probability)
        predictions = np.argmax(probabilities, axis=1)

        # Calculate confidences (max probability for each window)
        confidences = np.max(probabilities, axis=1)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.logger.info("✅ Inference complete!")
        self.logger.info(f"   Duration: {duration:.2f} seconds")
        self.logger.info(f"   Speed: {n_windows / duration:.1f} windows/sec")

        # Confidence analysis
        high_conf = np.sum(confidences > 0.90)
        mod_conf = np.sum((confidences > 0.70) & (confidences <= 0.90))
        low_conf = np.sum((confidences > 0.50) & (confidences <= 0.70))
        very_low = np.sum(confidences <= 0.50)

        self.logger.info("📈 Confidence Distribution:")
        self.logger.info(f"   HIGH (>90%):     {high_conf:5d} ({100*high_conf/n_windows:.1f}%)")
        self.logger.info(f"   MODERATE (70-90%): {mod_conf:5d} ({100*mod_conf/n_windows:.1f}%)")
        self.logger.info(f"   LOW (50-70%):    {low_conf:5d} ({100*low_conf/n_windows:.1f}%)")
        self.logger.info(f"   UNCERTAIN (<50%): {very_low:5d} ({100*very_low/n_windows:.1f}%) ⚠️")

        if very_low > 0:
            self.logger.warning(f"⚠️ {very_low} windows have low confidence - review recommended!")

        return predictions, probabilities

    def predict_realtime(self, window: np.ndarray) -> Tuple[int, np.ndarray, float]:
        """
        Perform real-time inference on a single window.

        Use this mode for streaming data / live monitoring.

        Args:
            window: Single window of shape (200, 6)

        Returns:
            Tuple of:
            - prediction: Predicted class index
            - probabilities: All class probabilities (11,)
            - confidence: Confidence score (0-1)
        """
        # Add batch dimension
        window_batch = np.expand_dims(window, axis=0)

        # Get probabilities
        probabilities = self.model.predict(window_batch, verbose=0)[0]

        # Get prediction
        prediction = int(np.argmax(probabilities))
        confidence = float(np.max(probabilities))

        # Log result
        activity = ACTIVITY_CLASSES[prediction]
        self.logger.debug(f"Real-time: {activity} (conf={confidence:.2%})")

        return prediction, probabilities, confidence

    def predict_with_details(self, data: np.ndarray) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Perform inference and return detailed results as DataFrame.

        This is the main method for generating the output CSV.

        Args:
            data: Array of shape (n_windows, 200, 6)

        Returns:
            Tuple of:
            - DataFrame with columns:
                - window_id: Window index
                - predicted_class: Class index (0-10)
                - predicted_activity: Activity name
                - confidence: Confidence score (0-1)
                - confidence_level: HIGH/MODERATE/LOW/UNCERTAIN
                - is_uncertain: Boolean flag
                - [prob_0 ... prob_10]: Per-class probabilities
            - probabilities: Raw probability array (n_windows, 11)
        """
        predictions, probabilities = self.predict_batch(data)

        # Build results DataFrame
        n_windows = len(predictions)
        results = []

        for i in range(n_windows):
            pred = predictions[i]
            probs = probabilities[i]
            conf = probs[pred]

            # Determine confidence level
            if conf > 0.90:
                conf_level = "HIGH"
            elif conf > 0.70:
                conf_level = "MODERATE"
            elif conf > self.config.confidence_threshold:
                conf_level = "LOW"
            else:
                conf_level = "UNCERTAIN"

            row = {
                "window_id": i,
                "predicted_class": int(pred),
                "predicted_activity": ACTIVITY_CLASSES[pred],
                "confidence": float(conf),
                "confidence_pct": f"{100*conf:.1f}%",
                "confidence_level": conf_level,
                "is_uncertain": conf <= self.config.confidence_threshold,
            }

            # Add per-class probabilities
            for j, activity in ACTIVITY_CLASSES.items():
                row[f"prob_{activity}"] = float(probs[j])

            results.append(row)

        return pd.DataFrame(results), probabilities


# ============================================================================
# RESULTS EXPORTER
# ============================================================================


class ResultsExporter:
    """
    Export inference results to CSV and JSON formats.

    Output Files:
    1. predictions_YYYYMMDD_HHMMSS.csv - Human-readable predictions
    2. predictions_YYYYMMDD_HHMMSS_metadata.json - Detailed metadata
    3. predictions_YYYYMMDD_HHMMSS_probabilities.npy - Raw probabilities
    """

    def __init__(self, config: InferenceConfig, logger: logging.Logger):
        """
        Initialize exporter.

        Args:
            config: Inference configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create output directory
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self, results_df: pd.DataFrame, probabilities: np.ndarray, data_metadata: Dict
    ) -> Dict[str, Path]:
        """
        Export all results to files.

        Args:
            results_df: DataFrame with predictions
            probabilities: Raw probability matrix
            data_metadata: Metadata about input data

        Returns:
            Dictionary of output file paths
        """
        self.logger.info("=" * 60)
        self.logger.info("💾 EXPORTING RESULTS")
        self.logger.info("=" * 60)

        output_files = {}

        # 1. Export CSV (human-readable)
        csv_path = self.config.output_dir / f"predictions_{self.timestamp}.csv"
        results_df.to_csv(csv_path, index=False)
        output_files["csv"] = csv_path
        self.logger.info(f"📄 CSV saved: {csv_path}")

        # 2. Export metadata JSON
        metadata = {
            "timestamp": self.timestamp,
            "model_path": str(self.config.model_path),
            "input_path": str(self.config.input_path),
            "mode": self.config.mode,
            "batch_size": self.config.batch_size,
            "confidence_threshold": self.config.confidence_threshold,
            "data": data_metadata,
            "results_summary": {
                "total_windows": len(results_df),
                "activity_distribution": results_df["predicted_activity"].value_counts().to_dict(),
                "confidence_stats": {
                    "mean": float(results_df["confidence"].mean()),
                    "std": float(results_df["confidence"].std()),
                    "min": float(results_df["confidence"].min()),
                    "max": float(results_df["confidence"].max()),
                },
                "confidence_levels": results_df["confidence_level"].value_counts().to_dict(),
                "uncertain_count": int(results_df["is_uncertain"].sum()),
            },
            "activity_classes": ACTIVITY_CLASSES,
            "export_time": datetime.now().isoformat(),
        }

        json_path = self.config.output_dir / f"predictions_{self.timestamp}_metadata.json"
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)
        output_files["json"] = json_path
        self.logger.info(f"📋 JSON metadata saved: {json_path}")

        # 3. Export raw probabilities (for advanced analysis)
        npy_path = self.config.output_dir / f"predictions_{self.timestamp}_probs.npy"
        np.save(npy_path, probabilities)
        output_files["npy"] = npy_path
        self.logger.info(f"🔢 Probabilities saved: {npy_path}")

        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("📊 RESULTS SUMMARY")
        self.logger.info("=" * 60)

        self.logger.info(f"Total windows: {len(results_df)}")
        self.logger.info(f"Uncertain predictions: {metadata['results_summary']['uncertain_count']}")

        self.logger.info("\n📈 Activity Distribution:")
        for activity, count in sorted(
            metadata["results_summary"]["activity_distribution"].items(), key=lambda x: -x[1]
        ):
            pct = 100 * count / len(results_df)
            self.logger.info(f"   {activity:20s}: {count:5d} ({pct:5.1f}%)")

        return output_files


# ============================================================================
# MAIN PIPELINE
# ============================================================================


class InferencePipeline:
    """
    Complete inference pipeline orchestrator.

    This class coordinates all components:
    1. Logger setup
    2. Model loading
    3. Data loading
    4. Inference execution
    5. Results export
    """

    def __init__(self, config: Optional[InferenceConfig] = None):
        """
        Initialize pipeline.

        Args:
            config: Inference configuration (uses defaults if None)
        """
        self.config = config or InferenceConfig()

        # Initialize logger
        self.log_setup = InferenceLogger()
        self.logger = self.log_setup.get_logger()

        self.logger.info("=" * 60)
        self.logger.info("🎯 INFERENCE PIPELINE INITIALIZED")
        self.logger.info("=" * 60)
        self.logger.info(f"Mode: {self.config.mode.upper()}")
        self.logger.info(f"Confidence threshold: {100*self.config.confidence_threshold:.0f}%")

    def run(self) -> Dict:
        """
        Execute the complete inference pipeline.

        Returns:
            Dictionary with results and file paths
        """
        try:
            # Initialize MLflow experiment
            mlflow.set_experiment("inference-production")

            with mlflow.start_run(
                run_name=f"inference_{datetime.now().strftime('%Y%m%d_%H%M%S')}", nested=True
            ):
                # Log configuration
                mlflow.log_params(
                    {
                        "mode": self.config.mode,
                        "batch_size": self.config.batch_size,
                        "confidence_threshold": self.config.confidence_threshold,
                        "input_path": str(self.config.input_path),
                        "model_path": str(self.config.model_path),
                    }
                )

                # 1. Load model
                model_loader = ModelLoader(self.config, self.logger)
                model = model_loader.load()
                mlflow.log_param("model_params", model.count_params())

                # 2. Load data
                data_loader = DataLoader(self.config, self.logger)
                data = data_loader.load()
                mlflow.log_param("n_windows", data_loader.metadata["n_windows"])
                mlflow.log_param("timesteps", data_loader.metadata["timesteps"])
                mlflow.log_param("channels", data_loader.metadata["channels"])

                # 3. Run inference
                engine = InferenceEngine(model, self.config, self.logger)
                results_df, probabilities = engine.predict_with_details(data)

                # Log inference metrics
                mlflow.log_metrics(
                    {
                        "total_windows": len(results_df),
                        "uncertain_count": int(results_df["is_uncertain"].sum()),
                        "avg_confidence": float(results_df["confidence"].mean()),
                        "std_confidence": float(results_df["confidence"].std()),
                    }
                )

                # Log activity distribution
                activity_dist = results_df["predicted_activity"].value_counts().to_dict()
                for activity, count in activity_dist.items():
                    mlflow.log_metric(f"count_{activity}", count)

                # 4. Export results
                exporter = ResultsExporter(self.config, self.logger)
                output_files = exporter.export(results_df, probabilities, data_loader.metadata)

                # Log output artifacts
                for file_path in output_files.values():
                    if file_path.exists():
                        mlflow.log_artifact(str(file_path))

                # Final summary
                self.logger.info("=" * 60)
                self.logger.info("✅ PIPELINE COMPLETE")
                self.logger.info("=" * 60)
                self.logger.info(f"📂 Output directory: {self.config.output_dir}")
                for name, path in output_files.items():
                    self.logger.info(f"   {name.upper()}: {path.name}")

                self.logger.info(f"📊 MLflow run ID: {mlflow.active_run().info.run_id}")

                return {
                    "success": True,
                    "results": results_df,
                    "probabilities": probabilities,
                    "output_files": output_files,
                    "config": asdict(self.config),
                    "mlflow_run_id": mlflow.active_run().info.run_id,
                }

        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {str(e)}", exc_info=True)
            try:
                mlflow.log_param("error", str(e))
            except Exception:
                pass  # No active run to log to
            return {"success": False, "error": str(e), "config": asdict(self.config)}


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run inference on preprocessed sensor data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with defaults (batch mode)
  python run_inference.py

  # Specify input file
  python run_inference.py --input data/prepared/production_X.npy

  # Change confidence threshold
  python run_inference.py --threshold 0.6

  # Run in real-time mode (for streaming)
  python run_inference.py --mode realtime
        """,
    )

    parser.add_argument(
        "--input", "-i", type=str, default=None, help="Path to preprocessed .npy file"
    )

    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output directory for predictions"
    )

    parser.add_argument(
        "--model", "-m", type=str, default=None, help="Path to trained model (.keras)"
    )

    parser.add_argument(
        "--mode",
        choices=["batch", "realtime"],
        default="batch",
        help="Inference mode (default: batch)",
    )

    parser.add_argument(
        "--batch-size", type=int, default=32, help="Batch size for inference (default: 32)"
    )

    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=0.50,
        help="Confidence threshold for uncertainty flag (default: 0.50)",
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Build configuration
    config = InferenceConfig(
        mode=args.mode, batch_size=args.batch_size, confidence_threshold=args.threshold
    )

    if args.input:
        config.input_path = Path(args.input)

    if args.output:
        config.output_dir = Path(args.output)

    if args.model:
        config.model_path = Path(args.model)

    # Run pipeline
    pipeline = InferencePipeline(config)
    result = pipeline.run()

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()

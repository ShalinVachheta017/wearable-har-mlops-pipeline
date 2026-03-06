"""
MLflow Experiment Tracking Module
=================================

This module provides centralized MLflow integration for the MLOps pipeline.
It handles experiment setup, run management, metric logging, and model registry.

Usage:
    from mlflow_tracking import MLflowTracker

    tracker = MLflowTracker()
    with tracker.start_run(run_name="training_v1"):
        tracker.log_params({"learning_rate": 0.001, "epochs": 50})
        tracker.log_metrics({"accuracy": 0.95, "loss": 0.12})
        tracker.log_model(model, "har_model")

Author: MLOps Pipeline
Date: December 11, 2025
"""

import json
import logging
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import mlflow
import numpy as np
import pandas as pd
import yaml
from mlflow.models.signature import infer_signature
from mlflow.tracking import MlflowClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLflowTracker:
    """
    Centralized MLflow tracking for the HAR MLOps pipeline.

    This class provides a clean interface for:
    - Experiment management
    - Run lifecycle (start, end, nested runs)
    - Parameter and metric logging
    - Artifact storage
    - Model registry integration

    Attributes:
        tracking_uri: MLflow tracking server URI
        experiment_name: Name of the experiment
        run_id: Current active run ID
    """

    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "mlflow_config.yaml"

    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        experiment_name: Optional[str] = None,
        config_path: Optional[Path] = None,
    ):
        """
        Initialize MLflow tracker.

        Args:
            tracking_uri: MLflow server URI (default: from config)
            experiment_name: Experiment name (default: from config)
            config_path: Path to YAML config file
        """
        # Load configuration
        self.config = self._load_config(config_path or self.DEFAULT_CONFIG_PATH)

        # Set tracking URI
        self.tracking_uri = tracking_uri or self.config.get("mlflow", {}).get(
            "tracking_uri", "mlruns"
        )
        mlflow.set_tracking_uri(self.tracking_uri)

        # Set experiment
        self.experiment_name = experiment_name or self.config.get("mlflow", {}).get(
            "experiment_name", "default"
        )
        self._setup_experiment()

        # Initialize client for registry operations
        self.client = MlflowClient()

        # Current run tracking
        self.run_id = None
        self.run = None

        logger.info(f"MLflow Tracker initialized: experiment='{self.experiment_name}'")

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        logger.warning(f"Config not found: {config_path}, using defaults")
        return {}

    def _setup_experiment(self) -> None:
        """Create experiment if it doesn't exist."""
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(
                    self.experiment_name,
                    artifact_location=self.config.get("mlflow", {}).get("artifact_location"),
                )
                logger.info(f"Created new experiment: {self.experiment_name} (ID: {experiment_id})")
            else:
                logger.info(
                    f"Using existing experiment: {self.experiment_name} (ID: {experiment.experiment_id})"
                )
            mlflow.set_experiment(self.experiment_name)
        except Exception as e:
            logger.error(f"Error setting up experiment: {e}")
            raise

    @contextmanager
    def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        nested: bool = False,
    ):
        """
        Context manager for MLflow runs.

        Args:
            run_name: Name for this run (default: auto-generated)
            tags: Additional tags to apply
            nested: Whether this is a nested run

        Yields:
            Self for method chaining

        Example:
            with tracker.start_run("training_v1") as run:
                run.log_params({"lr": 0.001})
                run.log_metrics({"accuracy": 0.95})
        """
        # Generate run name if not provided
        if run_name is None:
            run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Merge default tags with provided tags
        default_tags = self.config.get("run_defaults", {}).get("tags", {})
        all_tags = {**default_tags, **(tags or {})}

        try:
            self.run = mlflow.start_run(run_name=run_name, nested=nested, tags=all_tags)
            self.run_id = self.run.info.run_id
            logger.info(f"Started MLflow run: {run_name} (ID: {self.run_id})")
            yield self
        except Exception as e:
            logger.error(f"Error in MLflow run: {e}")
            raise
        finally:
            mlflow.end_run()
            logger.info(f"Ended MLflow run: {run_name}")
            self.run = None
            self.run_id = None

    def log_params(self, params: Dict[str, Any]) -> None:
        """
        Log parameters to the current run.

        Args:
            params: Dictionary of parameter names and values
        """
        if self.run is None:
            logger.warning("No active run. Call start_run() first.")
            return

        for key, value in params.items():
            try:
                mlflow.log_param(key, value)
            except Exception as e:
                logger.warning(f"Failed to log param {key}: {e}")

        logger.debug(f"Logged {len(params)} parameters")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """
        Log metrics to the current run.

        Args:
            metrics: Dictionary of metric names and values
            step: Optional step number (for time-series metrics)
        """
        if self.run is None:
            logger.warning("No active run. Call start_run() first.")
            return

        for key, value in metrics.items():
            try:
                mlflow.log_metric(key, value, step=step)
            except Exception as e:
                logger.warning(f"Failed to log metric {key}: {e}")

        logger.debug(f"Logged {len(metrics)} metrics at step {step}")

    def log_artifact(
        self, local_path: Union[str, Path], artifact_path: Optional[str] = None
    ) -> None:
        """
        Log a file or directory as an artifact.

        Args:
            local_path: Path to the file or directory
            artifact_path: Optional subdirectory in artifact store
        """
        if self.run is None:
            logger.warning("No active run. Call start_run() first.")
            return

        try:
            mlflow.log_artifact(str(local_path), artifact_path)
            logger.info(f"Logged artifact: {local_path}")
        except Exception as e:
            logger.error(f"Failed to log artifact {local_path}: {e}")

    def log_dict(
        self, dictionary: Dict[str, Any], filename: str, artifact_path: Optional[str] = None
    ) -> None:
        """
        Log a dictionary as a JSON artifact.

        Args:
            dictionary: Dictionary to log
            filename: Name for the JSON file
            artifact_path: Optional subdirectory
        """
        if self.run is None:
            logger.warning("No active run. Call start_run() first.")
            return

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(dictionary, f, indent=2, default=str)
                temp_path = f.name

            mlflow.log_artifact(temp_path, artifact_path)
            os.unlink(temp_path)
            logger.info(f"Logged dict as {filename}")
        except Exception as e:
            logger.error(f"Failed to log dict {filename}: {e}")

    def log_dataframe(
        self, df: pd.DataFrame, filename: str, artifact_path: Optional[str] = None
    ) -> None:
        """
        Log a pandas DataFrame as a CSV artifact.

        Args:
            df: DataFrame to log
            filename: Name for the CSV file
            artifact_path: Optional subdirectory
        """
        if self.run is None:
            logger.warning("No active run. Call start_run() first.")
            return

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
                df.to_csv(f, index=False)
                temp_path = f.name

            mlflow.log_artifact(temp_path, artifact_path)
            os.unlink(temp_path)
            logger.info(f"Logged DataFrame as {filename}")
        except Exception as e:
            logger.error(f"Failed to log DataFrame {filename}: {e}")

    def log_figure(self, figure, filename: str, artifact_path: Optional[str] = None) -> None:
        """
        Log a matplotlib figure as an artifact.

        Args:
            figure: Matplotlib figure object
            filename: Name for the image file
            artifact_path: Optional subdirectory
        """
        if self.run is None:
            logger.warning("No active run. Call start_run() first.")
            return

        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                figure.savefig(f.name, dpi=150, bbox_inches="tight")
                temp_path = f.name

            mlflow.log_artifact(temp_path, artifact_path)
            os.unlink(temp_path)
            logger.info(f"Logged figure as {filename}")
        except Exception as e:
            logger.error(f"Failed to log figure {filename}: {e}")

    def log_keras_model(
        self,
        model,
        artifact_path: str = "model",
        input_example: Optional[np.ndarray] = None,
        registered_model_name: Optional[str] = None,
    ) -> None:
        """
        Log a Keras model to MLflow.

        Args:
            model: Keras model to log
            artifact_path: Path in artifact store
            input_example: Example input for signature inference
            registered_model_name: If provided, register model in registry
        """
        if self.run is None:
            logger.warning("No active run. Call start_run() first.")
            return

        try:
            # Infer signature if example provided
            signature = None
            if input_example is not None:
                predictions = model.predict(input_example[:1], verbose=0)
                signature = infer_signature(input_example[:1], predictions)

            # Log model (handle artifact_path→name rename in MLflow >=2.9).
            # input_example is intentionally NOT passed to log_model: the signature
            # already captures input/output shape, and passing input_example triggers
            # an mlflow.keras serialisation bug (input_example.json written to a temp
            # path that is cleaned up before MLflow reads it back — FileNotFoundError).
            try:
                mlflow.keras.log_model(
                    model,
                    name=artifact_path,
                    signature=signature,
                    registered_model_name=registered_model_name,
                )
            except TypeError:
                # Older MLflow still uses artifact_path= as positional
                mlflow.keras.log_model(
                    model,
                    artifact_path,
                    signature=signature,
                    registered_model_name=registered_model_name,
                )
            logger.info(f"Logged Keras model to {artifact_path}")

            if registered_model_name:
                logger.info(f"Registered model as: {registered_model_name}")

        except Exception as e:
            logger.error(f"Failed to log Keras model: {e}")

    def log_training_history(self, history) -> None:
        """
        Log Keras training history (metrics per epoch).

        Args:
            history: Keras History object from model.fit()
        """
        if self.run is None:
            logger.warning("No active run. Call start_run() first.")
            return

        try:
            # Log metrics for each epoch
            for epoch, metrics in enumerate(zip(*[history.history[k] for k in history.history])):
                metric_dict = {k: v for k, v in zip(history.history.keys(), metrics)}
                self.log_metrics(metric_dict, step=epoch)

            # Log history as artifact
            self.log_dict(history.history, "training_history.json", "training")
            logger.info("Logged training history")
        except Exception as e:
            logger.error(f"Failed to log training history: {e}")

    def log_confusion_matrix(
        self, y_true: np.ndarray, y_pred: np.ndarray, class_names: Optional[List[str]] = None
    ) -> None:
        """
        Log confusion matrix as an artifact.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            class_names: Optional list of class names
        """
        if self.run is None:
            logger.warning("No active run. Call start_run() first.")
            return

        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            from sklearn.metrics import confusion_matrix

            cm = confusion_matrix(y_true, y_pred)

            # Create figure
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.heatmap(
                cm,
                annot=True,
                fmt="d",
                cmap="Blues",
                xticklabels=class_names or range(cm.shape[1]),
                yticklabels=class_names or range(cm.shape[0]),
                ax=ax,
            )
            ax.set_xlabel("Predicted")
            ax.set_ylabel("Actual")
            ax.set_title("Confusion Matrix")
            plt.tight_layout()

            self.log_figure(fig, "confusion_matrix.png", "evaluation")
            plt.close(fig)

            # Also log as CSV
            cm_df = pd.DataFrame(
                cm,
                index=class_names or [f"class_{i}" for i in range(cm.shape[0])],
                columns=class_names or [f"class_{i}" for i in range(cm.shape[1])],
            )
            self.log_dataframe(cm_df, "confusion_matrix.csv", "evaluation")

            logger.info("Logged confusion matrix")
        except Exception as e:
            logger.error(f"Failed to log confusion matrix: {e}")

    def log_classification_report(
        self, y_true: np.ndarray, y_pred: np.ndarray, class_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Log classification report and return key metrics.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            class_names: Optional list of class names

        Returns:
            Dictionary of key metrics (accuracy, f1, precision, recall)
        """
        if self.run is None:
            logger.warning("No active run. Call start_run() first.")
            return {}

        try:
            from sklearn.metrics import accuracy_score, classification_report

            # Generate report
            report = classification_report(
                y_true, y_pred, target_names=class_names, output_dict=True
            )

            # Log as artifact
            self.log_dict(report, "classification_report.json", "evaluation")

            # Extract and log key metrics
            metrics = {
                "accuracy": accuracy_score(y_true, y_pred),
                "f1_macro": report["macro avg"]["f1-score"],
                "precision_macro": report["macro avg"]["precision"],
                "recall_macro": report["macro avg"]["recall"],
                "f1_weighted": report["weighted avg"]["f1-score"],
            }
            self.log_metrics(metrics)

            logger.info("Logged classification report")
            return metrics
        except Exception as e:
            logger.error(f"Failed to log classification report: {e}")
            return {}

    def get_best_run(self, metric: str = "accuracy", ascending: bool = False) -> Optional[Dict]:
        """
        Get the best run from the current experiment.

        Args:
            metric: Metric to optimize
            ascending: If True, lower is better

        Returns:
            Dictionary with run info or None
        """
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=[f"metrics.{metric} {'ASC' if ascending else 'DESC'}"],
                max_results=1,
            )

            if len(runs) > 0:
                return runs.iloc[0].to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get best run: {e}")
            return None

    def compare_runs(self, run_ids: List[str], metrics: List[str]) -> pd.DataFrame:
        """
        Compare multiple runs by their metrics.

        Args:
            run_ids: List of run IDs to compare
            metrics: List of metrics to include

        Returns:
            DataFrame with comparison
        """
        try:
            results = []
            for run_id in run_ids:
                run = mlflow.get_run(run_id)
                row = {"run_id": run_id, "run_name": run.info.run_name}
                for metric in metrics:
                    row[metric] = run.data.metrics.get(metric)
                results.append(row)
            return pd.DataFrame(results)
        except Exception as e:
            logger.error(f"Failed to compare runs: {e}")
            return pd.DataFrame()


# ============================================================================
# Convenience Functions
# ============================================================================


def get_or_create_tracker(experiment_name: str = "anxiety-activity-recognition") -> MLflowTracker:
    """
    Get or create a singleton MLflow tracker.

    Args:
        experiment_name: Name of the experiment

    Returns:
        MLflowTracker instance
    """
    return MLflowTracker(experiment_name=experiment_name)


def quick_log_run(
    run_name: str,
    params: Dict[str, Any],
    metrics: Dict[str, float],
    artifacts: Optional[Dict[str, Union[str, Path]]] = None,
    experiment_name: str = "anxiety-activity-recognition",
) -> str:
    """
    Quickly log a complete run with params, metrics, and artifacts.

    Args:
        run_name: Name for the run
        params: Parameters to log
        metrics: Metrics to log
        artifacts: Optional dict of {name: path} for artifacts
        experiment_name: Experiment name

    Returns:
        Run ID
    """
    tracker = MLflowTracker(experiment_name=experiment_name)

    with tracker.start_run(run_name=run_name) as run:
        run.log_params(params)
        run.log_metrics(metrics)

        if artifacts:
            for name, path in artifacts.items():
                run.log_artifact(path)

    return tracker.run_id


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MLflow Tracking Utilities")
    parser.add_argument("--list-experiments", action="store_true", help="List all experiments")
    parser.add_argument("--list-runs", type=str, help="List runs for an experiment")
    parser.add_argument("--ui", action="store_true", help="Start MLflow UI")

    args = parser.parse_args()

    if args.list_experiments:
        client = MlflowClient()
        experiments = client.search_experiments()
        print("\n📊 MLflow Experiments:")
        for exp in experiments:
            print(f"  - {exp.name} (ID: {exp.experiment_id})")

    elif args.list_runs:
        tracker = MLflowTracker(experiment_name=args.list_runs)
        experiment = mlflow.get_experiment_by_name(args.list_runs)
        if experiment:
            runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
            print(f"\n📊 Runs for '{args.list_runs}':")
            print(runs[["run_id", "start_time", "status"]].to_string())
        else:
            print(f"Experiment '{args.list_runs}' not found")

    elif args.ui:
        import subprocess

        print("Starting MLflow UI at http://localhost:5000")
        subprocess.run(["mlflow", "ui"])

    else:
        # Demo run
        print("\n🔬 MLflow Tracker Demo\n")

        tracker = MLflowTracker()

        with tracker.start_run("demo_run") as run:
            # Log parameters
            run.log_params(
                {
                    "learning_rate": 0.001,
                    "batch_size": 32,
                    "epochs": 50,
                    "model_type": "1D-CNN-BiLSTM",
                }
            )

            # Log metrics
            run.log_metrics({"accuracy": 0.85, "loss": 0.42, "f1_score": 0.83})

            print("✅ Demo run completed!")
            print(f"   Run ID: {run.run_id}")
            print("   View at: mlflow ui")

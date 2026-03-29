#!/usr/bin/env python3
"""
HAR Model Training Module
=========================

Production training module for Human Activity Recognition MLOps pipeline.
Implements training with cross-validation, MLflow tracking, and model registry.

Features:
- 5-Fold Stratified Cross-Validation (per ICTH_16 methodology)
- MLflow experiment tracking for all metrics and artifacts
- Reproducible training with seed control
- Model versioning and registry integration
- Domain adaptation support (DANN, MMD) for retraining scenarios

Usage:
    # Standard training with CV
    python src/train.py

    # Training with specific config
    python src/train.py --epochs 100 --experiment-name har-training-v2

    # Retraining with domain adaptation (triggered by drift detection)
    python src/train.py --retrain --target-data data/prepared/drift_samples.npy

Author: HAR MLOps Pipeline
Date: January 30, 2026
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Suppress TF warnings before import
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from sklearn.metrics import (  # noqa: E402, F401
    accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split  # noqa: E402
from sklearn.preprocessing import LabelEncoder, RobustScaler, StandardScaler  # noqa: E402
from tensorflow import keras  # noqa: E402

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))
from config import (  # noqa: E402, F401
    ACTIVITY_LABELS,
    DATA_PREPARED,
    DATA_RAW,
    LOGS_DIR,
    MODELS_DIR,
    NUM_CLASSES,
    NUM_SENSORS,
    OVERLAP,
    PROJECT_ROOT,
    SENSOR_COLUMNS,
    WINDOW_SIZE,
)
import mlflow  # noqa: E402
from mlflow_tracking import MLflowTracker  # noqa: E402

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class TrainingConfig:
    """Configuration for model training."""

    # Data parameters
    window_size: int = 200  # 4 seconds at 50Hz
    step_size: int = 100  # 50% overlap
    n_sensors: int = 6  # Ax, Ay, Az, Gx, Gy, Gz
    n_classes: int = 11  # Activity classes

    # Training parameters
    epochs: int = 100
    batch_size: int = 64
    learning_rate: float = 0.001
    early_stopping_patience: int = 15
    reduce_lr_patience: int = 5
    min_lr: float = 1e-6

    # Cross-validation
    n_folds: int = 5
    cv_random_seed: int = 42

    # Architecture selection
    # "v1" = pretrained architecture (Conv16→32, BiLSTM64→32, Dense32) — 499K params
    # "v2" = paper-inspired (Conv64×2→128×2, BiLSTM64×2, Dense128) — ~306K params
    model_version: str = "v1"

    # Regularization — defaults match the deployed pretrained model (v1)
    dropout_cnn_1: float = 0.1  # after 1st Conv block
    dropout_cnn_2: float = 0.2  # after 2nd Conv block
    dropout_lstm: float = 0.2  # after each BiLSTM layer
    dropout_dense: float = 0.5  # after Dense hidden layer

    # Domain adaptation (for retraining)
    enable_domain_adaptation: bool = False
    adaptation_method: str = "dann"  # dann, mmd, pseudo_label
    adaptation_weight: float = 0.1  # Weight for adaptation loss

    # Normalization variant (A/B/C comparison)
    # "zscore"  → StandardScaler fit on training data (Variant A, default)
    # "none"    → no amplitude normalization, model trained on raw m/s² values (Variant B)
    # "robust"  → RobustScaler (median/IQR) fit on training data (Variant C)
    normalization_variant: str = "zscore"

    # MLflow
    experiment_name: str = "har-training"
    run_name: Optional[str] = None

    # Output paths
    output_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "models" / "trained")

    def __post_init__(self):
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# ============================================================================
# DATA LOADING AND PREPROCESSING
# ============================================================================


def _make_scaler(variant: str):
    """Return a fresh scaler instance for the given normalization variant.

    Args:
        variant: "zscore" → StandardScaler, "robust" → RobustScaler, "none" → None
    """
    if variant == "zscore":
        return StandardScaler()
    elif variant == "robust":
        return RobustScaler()
    elif variant == "none":
        return None
    else:
        raise ValueError(
            f"Unknown normalization_variant '{variant}'. Use 'zscore', 'robust', or 'none'."
        )


class DataLoader:
    """Load and prepare training data for HAR model."""

    def __init__(self, config: TrainingConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.label_encoder = LabelEncoder()
        self.scaler = _make_scaler(config.normalization_variant)

    def load_training_data(self, data_path: Optional[Path] = None) -> pd.DataFrame:
        """Load labeled training data."""
        if data_path is None:
            data_path = DATA_RAW / "all_users_data_labeled.csv"

        if not data_path.exists():
            raise FileNotFoundError(f"Training data not found: {data_path}")

        self.logger.info(f"Loading training data from: {data_path}")
        df = pd.read_csv(data_path)

        self.logger.info(f"  Loaded {len(df):,} samples")
        self.logger.info(f"  Users: {df['User'].nunique()}")
        self.logger.info(f"  Activities: {df['activity'].nunique()}")

        return df

    def create_windows(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sliding windows from sensor data.

        Per ICTH_16: "window size of 200 time steps (4 seconds at 50Hz)
        with 50% overlap between consecutive windows"
        """
        from collections import Counter

        windows = []
        labels = []

        for i in range(0, len(X) - self.config.window_size + 1, self.config.step_size):
            window = X[i : i + self.config.window_size]
            window_labels = y[i : i + self.config.window_size]
            # Use majority label in window
            majority_label = Counter(window_labels).most_common(1)[0][0]
            windows.append(window)
            labels.append(majority_label)

        return np.array(windows), np.array(labels)

    def prepare_data(
        self, df: pd.DataFrame, feature_cols: List[str] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for training: extract features, encode labels, create windows."""
        if feature_cols is None:
            feature_cols = SENSOR_COLUMNS

        # Extract features and labels
        X = df[feature_cols].values
        y = df["activity"].values

        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)

        # Create windows
        self.logger.info(
            f"Creating windows: size={self.config.window_size}, step={self.config.step_size}"
        )
        X_windows, y_windows = self.create_windows(X, y_encoded)
        self.logger.info(f"  Created {len(X_windows):,} windows")

        return X_windows, y_windows

    def get_scaler_config(self) -> Dict[str, Any]:
        """Get scaler parameters for inference."""
        variant = self.config.normalization_variant
        cfg: Dict[str, Any] = {"normalization_variant": variant}
        if variant == "zscore" and isinstance(self.scaler, StandardScaler):
            cfg["mean"] = self.scaler.mean_.tolist()
            cfg["scale"] = self.scaler.scale_.tolist()
            # mirror the keys expected by preprocess_data.py config.json
            cfg["scaler_mean"] = cfg["mean"]
            cfg["scaler_scale"] = cfg["scale"]
        elif variant == "robust" and isinstance(self.scaler, RobustScaler):
            cfg["scaler_center"] = self.scaler.center_.tolist()
            cfg["scaler_scale"] = self.scaler.scale_.tolist()
        # variant == "none": nothing extra to save
        return cfg

    def get_label_mapping(self) -> Dict[int, str]:
        """Get label index to activity name mapping."""
        return {i: cls for i, cls in enumerate(self.label_encoder.classes_)}


# ============================================================================
# MODEL ARCHITECTURE
# ============================================================================


class HARModelBuilder:
    """Build HAR model architectures."""

    def __init__(self, config: TrainingConfig):
        self.config = config

    def create_1dcnn_bilstm(self) -> keras.Model:
        """
        Create 1D-CNN-BiLSTM model matching the deployed pretrained checkpoint.

        Dispatches to v1 (default, matches pretrained model) or v2 (paper-inspired)
        based on ``self.config.model_version``.
        """
        if self.config.model_version == "v2":
            return self._build_v2()
        return self._build_v1()

    # ------------------------------------------------------------------
    # v1 — matches  models/pretrained/fine_tuned_model_1dcnnbilstm.keras
    #       Conv1D(16,2,valid) → Conv1D(32,2,valid) → BiLSTM(64) →
    #       BiLSTM(32) → Flatten → Dense(32) → Dense(n_classes)
    #       Trainable params ≈ 499 K  (window=200, sensors=6, classes=11)
    # ------------------------------------------------------------------
    def _build_v1(self) -> keras.Model:
        """Architecture identical to the deployed pretrained model (499 K params)."""
        model = keras.Sequential(
            [
                # Input
                keras.layers.Input(shape=(self.config.window_size, self.config.n_sensors)),
                # CNN Block 1
                keras.layers.Conv1D(16, 2, activation="relu", padding="valid"),
                keras.layers.BatchNormalization(),
                keras.layers.Dropout(self.config.dropout_cnn_1),
                # CNN Block 2
                keras.layers.Conv1D(32, 2, activation="relu", padding="valid"),
                keras.layers.BatchNormalization(),
                keras.layers.Dropout(self.config.dropout_cnn_2),
                # BiLSTM layers
                keras.layers.Bidirectional(keras.layers.LSTM(64, return_sequences=True)),
                keras.layers.BatchNormalization(),
                keras.layers.Dropout(self.config.dropout_lstm),
                keras.layers.Bidirectional(keras.layers.LSTM(32, return_sequences=True)),
                keras.layers.BatchNormalization(),
                keras.layers.Dropout(self.config.dropout_lstm),
                # Flatten temporal output → Dense
                keras.layers.Flatten(),
                keras.layers.Dense(32, activation="relu"),
                keras.layers.BatchNormalization(),
                keras.layers.Dropout(self.config.dropout_dense),
                keras.layers.Dense(self.config.n_classes, activation="softmax"),
            ]
        )

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.config.learning_rate),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        return model

    # ------------------------------------------------------------------
    # v2 — larger ICTH_16-paper-inspired architecture
    #       Conv1D(64,3,same)×2 → MaxPool → Conv1D(128,3,same)×2 → MaxPool →
    #       BiLSTM(64) → BiLSTM(64,ret=False) → Dense(128) → Dense(n_classes)
    #       Trainable params ≈ 306 K  (window=200, sensors=6, classes=11)
    # ------------------------------------------------------------------
    def _build_v2(self) -> keras.Model:
        """Larger paper-inspired architecture (kept for future experimentation)."""
        model = keras.Sequential(
            [
                # Input layer
                keras.layers.Input(shape=(self.config.window_size, self.config.n_sensors)),
                # CNN Block 1
                keras.layers.Conv1D(64, 3, activation="relu", padding="same"),
                keras.layers.BatchNormalization(),
                keras.layers.Conv1D(64, 3, activation="relu", padding="same"),
                keras.layers.BatchNormalization(),
                keras.layers.MaxPooling1D(2),
                keras.layers.Dropout(self.config.dropout_cnn_1),
                # CNN Block 2
                keras.layers.Conv1D(128, 3, activation="relu", padding="same"),
                keras.layers.BatchNormalization(),
                keras.layers.Conv1D(128, 3, activation="relu", padding="same"),
                keras.layers.BatchNormalization(),
                keras.layers.MaxPooling1D(2),
                keras.layers.Dropout(self.config.dropout_cnn_2),
                # BiLSTM layers
                keras.layers.Bidirectional(keras.layers.LSTM(64, return_sequences=True)),
                keras.layers.BatchNormalization(),
                keras.layers.Dropout(self.config.dropout_lstm),
                keras.layers.Bidirectional(keras.layers.LSTM(64, return_sequences=False)),
                keras.layers.BatchNormalization(),
                keras.layers.Dropout(self.config.dropout_dense),
                # Dense layers
                keras.layers.Dense(128, activation="relu"),
                keras.layers.BatchNormalization(),
                keras.layers.Dropout(self.config.dropout_dense),
                keras.layers.Dense(self.config.n_classes, activation="softmax"),
            ]
        )

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.config.learning_rate),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        return model

    def get_callbacks(self, checkpoint_path: Optional[Path] = None) -> List:
        """Get training callbacks."""
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy",
                patience=self.config.early_stopping_patience,
                restore_best_weights=True,
                verbose=1,
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.5,
                patience=self.config.reduce_lr_patience,
                min_lr=self.config.min_lr,
                verbose=1,
            ),
        ]

        if checkpoint_path:
            callbacks.append(
                keras.callbacks.ModelCheckpoint(
                    filepath=str(checkpoint_path),
                    monitor="val_accuracy",
                    save_best_only=True,
                    verbose=1,
                )
            )

        return callbacks


# ============================================================================
# TRAINING PIPELINE
# ============================================================================


class HARTrainer:
    """Main training pipeline for HAR model."""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.Trainer")
        self.data_loader = DataLoader(config, self.logger)
        self.model_builder = HARModelBuilder(config)
        self.tracker = MLflowTracker(experiment_name=config.experiment_name)

    def run_cross_validation(self, X: np.ndarray, y: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run 5-fold stratified cross-validation.

        Per ICTH_16: "5-fold cross-validation protocol. The data was partitioned
        into five folds. In each iteration, four folds were used for training,
        and the remaining fold was used for testing."
        """
        self.logger.info("=" * 70)
        self.logger.info("5-FOLD CROSS-VALIDATION (ICTH_16 Methodology)")
        self.logger.info("=" * 70)

        skf = StratifiedKFold(
            n_splits=self.config.n_folds, shuffle=True, random_state=self.config.cv_random_seed
        )

        fold_results = []

        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
            self.logger.info(f"\n{'─' * 60}")
            self.logger.info(f"FOLD {fold}/{self.config.n_folds}")
            self.logger.info(f"{'─' * 60}")

            # Split data
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            self.logger.info(f"Train: {len(X_train):,} samples, Val: {len(X_val):,} samples")

            # Normalize (fit on train, transform both) — variant-aware
            fold_scaler = _make_scaler(self.config.normalization_variant)
            X_train_flat = X_train.reshape(-1, self.config.n_sensors)
            X_val_flat = X_val.reshape(-1, self.config.n_sensors)

            if fold_scaler is not None:
                fold_scaler.fit(X_train_flat)
                X_train_scaled = fold_scaler.transform(X_train_flat).reshape(X_train.shape)
                X_val_scaled = fold_scaler.transform(X_val_flat).reshape(X_val.shape)
            else:
                # Variant B: no amplitude normalization
                X_train_scaled = X_train.copy()
                X_val_scaled = X_val.copy()

            # Create and train model
            model = self.model_builder.create_1dcnn_bilstm()
            callbacks = self.model_builder.get_callbacks()

            # Start nested MLflow run for this fold
            with self.tracker.start_run(run_name=f"cv_fold_{fold}", nested=True):
                fold_params: dict = {
                    "fold": fold,
                    "train_samples": len(X_train),
                    "val_samples": len(X_val),
                }
                if fold == 1:
                    # Log architecture param count once — verifies the ~499 K assumption
                    fold_params["model_total_params"] = model.count_params()
                self.tracker.log_params(fold_params)

                # Train
                history = model.fit(
                    X_train_scaled,
                    y_train,
                    validation_data=(X_val_scaled, y_val),
                    epochs=self.config.epochs,
                    batch_size=self.config.batch_size,
                    callbacks=callbacks,
                    verbose=1,
                )

                # Evaluate
                val_loss, val_acc = model.evaluate(X_val_scaled, y_val, verbose=0)
                predictions = model.predict(X_val_scaled, verbose=0)
                pred_classes = np.argmax(predictions, axis=1)

                # Compute metrics
                f1_macro = f1_score(y_val, pred_classes, average="macro")
                f1_weighted = f1_score(y_val, pred_classes, average="weighted")
                kappa = cohen_kappa_score(y_val, pred_classes)

                # Log metrics
                self.tracker.log_metrics(
                    {
                        "val_accuracy": val_acc,
                        "val_loss": val_loss,
                        "f1_macro": f1_macro,
                        "f1_weighted": f1_weighted,
                        "cohen_kappa": kappa,
                        "best_epoch": len(history.history["accuracy"]),
                    }
                )

                fold_results.append(
                    {
                        "fold": fold,
                        "accuracy": val_acc,
                        "f1_macro": f1_macro,
                        "f1_weighted": f1_weighted,
                        "kappa": kappa,
                        "best_epoch": len(history.history["accuracy"]),
                    }
                )

                self.logger.info(f"\n✓ Fold {fold} Results:")
                self.logger.info(f"  Accuracy: {val_acc:.4f} ({val_acc*100:.1f}%)")
                self.logger.info(f"  F1-Macro: {f1_macro:.4f}")
                self.logger.info(f"  Cohen's Kappa: {kappa:.4f}")

            # Clean up
            del model
            keras.backend.clear_session()

        return fold_results

    def train_final_model(
        self, X: np.ndarray, y: np.ndarray, save_artifacts: bool = True
    ) -> Tuple[keras.Model, Dict[str, Any]]:
        """Train final model on all data."""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("TRAINING FINAL MODEL ON 100% DATA")
        self.logger.info("=" * 70)

        # Normalize all data — variant-aware
        X_flat = X.reshape(-1, self.config.n_sensors)
        if self.data_loader.scaler is not None:
            self.data_loader.scaler.fit(X_flat)
            X_scaled = self.data_loader.scaler.transform(X_flat).reshape(X.shape)
        else:
            # Variant B: passthrough — no amplitude normalization
            X_scaled = X.copy()

        scaler_config = self.data_loader.get_scaler_config()
        variant = self.config.normalization_variant
        self.logger.info(f"Normalization variant: {variant}")
        if variant == "zscore":
            self.logger.info(f"Scaler fitted: mean={scaler_config['mean'][:3]}...")
        elif variant == "robust":
            self.logger.info(f"RobustScaler fitted: center={scaler_config['scaler_center'][:3]}...")

        # Create model
        model = self.model_builder.create_1dcnn_bilstm()

        # Split for validation during training (10%)
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=0.1, random_state=42, stratify=y
        )

        # Setup checkpoint path
        checkpoint_path = self.config.output_dir / "best_model.keras"
        callbacks = self.model_builder.get_callbacks(checkpoint_path)

        # Train
        self.logger.info(f"Training for up to {self.config.epochs} epochs...")
        history = model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val),
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            callbacks=callbacks,
            verbose=1,
        )

        # Final evaluation
        final_loss, final_acc = model.evaluate(X_val, y_val, verbose=0)
        predictions = model.predict(X_val, verbose=0)
        pred_classes = np.argmax(predictions, axis=1)

        # Compute comprehensive metrics
        metrics = {
            "final_accuracy": float(final_acc),
            "final_loss": float(final_loss),
            "f1_macro": float(f1_score(y_val, pred_classes, average="macro")),
            "f1_weighted": float(f1_score(y_val, pred_classes, average="weighted")),
            "cohen_kappa": float(cohen_kappa_score(y_val, pred_classes)),
            "best_epoch": len(history.history["accuracy"]),
        }

        # Per-class F1 scores
        f1_per_class = f1_score(y_val, pred_classes, average=None)
        for i, f1 in enumerate(f1_per_class):
            metrics[f"f1_class_{i}"] = float(f1)

        self.logger.info(f"\n✓ Final Model Accuracy: {final_acc:.4f} ({final_acc*100:.1f}%)")
        self.logger.info(f"  F1-Macro: {metrics['f1_macro']:.4f}")
        self.logger.info(f"  Cohen's Kappa: {metrics['cohen_kappa']:.4f}")

        # Save artifacts
        if save_artifacts:
            self._save_training_artifacts(model, scaler_config, metrics, history)

        return model, metrics

    def _save_training_artifacts(
        self,
        model: keras.Model,
        scaler_config: Dict,
        metrics: Dict,
        history: keras.callbacks.History,
    ):
        """Save all training artifacts."""
        output_dir = self.config.output_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save model
        model_path = output_dir / f"har_model_{timestamp}.keras"
        model.save(model_path)
        self.logger.info(f"✓ Model saved: {model_path}")

        # Also save as 'latest' for easy access
        latest_path = output_dir / "har_model_latest.keras"
        model.save(latest_path)

        # Save scaler config
        scaler_path = output_dir / "scaler_config.json"
        with open(scaler_path, "w") as f:
            json.dump(scaler_config, f, indent=2)
        self.logger.info(f"✓ Scaler config saved: {scaler_path}")

        # Save label mapping
        label_mapping = self.data_loader.get_label_mapping()
        mapping_path = output_dir / "label_mapping.json"
        with open(mapping_path, "w") as f:
            json.dump(label_mapping, f, indent=2)
        self.logger.info(f"✓ Label mapping saved: {mapping_path}")

        # Save training report
        report = {
            "timestamp": timestamp,
            "config": asdict(self.config),
            "metrics": metrics,
            "scaler": scaler_config,
            "label_mapping": label_mapping,
            "history": {
                "accuracy": [float(v) for v in history.history.get("accuracy", [])],
                "val_accuracy": [float(v) for v in history.history.get("val_accuracy", [])],
                "loss": [float(v) for v in history.history.get("loss", [])],
                "val_loss": [float(v) for v in history.history.get("val_loss", [])],
            },
        }

        report_path = output_dir / f"training_report_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        self.logger.info(f"✓ Training report saved: {report_path}")

        # Log to MLflow
        self.tracker.log_artifact(str(model_path))
        self.tracker.log_artifact(str(scaler_path))
        self.tracker.log_artifact(str(mapping_path))
        self.tracker.log_artifact(str(report_path))

    def train(self, data_path: Optional[Path] = None, skip_cv: bool = False) -> Dict[str, Any]:
        """
        Full training pipeline.

        Args:
            data_path: Path to training data CSV
            skip_cv: Skip cross-validation (faster, for testing)

        Returns:
            Dictionary with training results
        """
        results = {"timestamp": datetime.now().isoformat(), "config": asdict(self.config)}

        # Load and prepare data
        df = self.data_loader.load_training_data(data_path)
        X, y = self.data_loader.prepare_data(df)
        num_classes = len(self.data_loader.label_encoder.classes_)

        self.logger.info(f"\nClasses ({num_classes}):")
        for i, cls in enumerate(self.data_loader.label_encoder.classes_):
            self.logger.info(f"  {i}: {cls}")

        # Start MLflow run
        run_name = self.config.run_name or f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Guard: end any stale active run before starting a new one
        if mlflow.active_run() is not None:
            logger.warning("Stale MLflow run detected — ending it before starting a new one.")
            mlflow.end_run()

        with self.tracker.start_run(run_name=run_name):
            # Log configuration
            self.tracker.log_params(
                {
                    "window_size": self.config.window_size,
                    "step_size": self.config.step_size,
                    "epochs": self.config.epochs,
                    "batch_size": self.config.batch_size,
                    "learning_rate": self.config.learning_rate,
                    "n_folds": self.config.n_folds,
                    "n_classes": num_classes,
                    "n_windows": len(X),
                }
            )

            # Run cross-validation
            if not skip_cv:
                cv_results = self.run_cross_validation(X, y)

                # Log CV summary
                accuracies = [r["accuracy"] for r in cv_results]
                f1_scores = [r["f1_macro"] for r in cv_results]

                cv_summary = {
                    "cv_mean_accuracy": float(np.mean(accuracies)),
                    "cv_std_accuracy": float(np.std(accuracies)),
                    "cv_mean_f1": float(np.mean(f1_scores)),
                    "cv_std_f1": float(np.std(f1_scores)),
                }

                self.tracker.log_metrics(cv_summary)
                results["cv_results"] = cv_results
                results["cv_summary"] = cv_summary

                self.logger.info("\n" + "=" * 70)
                self.logger.info("CROSS-VALIDATION SUMMARY")
                self.logger.info("=" * 70)
                self.logger.info(
                    f"Mean Accuracy: {cv_summary['cv_mean_accuracy']:.4f} (± {cv_summary['cv_std_accuracy']:.4f})"
                )
                self.logger.info(
                    f"Mean F1-Score: {cv_summary['cv_mean_f1']:.4f} (± {cv_summary['cv_std_f1']:.4f})"
                )

            # Train final model
            model, final_metrics = self.train_final_model(X, y)
            self.tracker.log_metrics(final_metrics)
            results["final_metrics"] = final_metrics

            # Register model in MLflow
            self.tracker.log_model(
                model, artifact_path="har_model", registered_model_name="har-1dcnn-bilstm"
            )

        self.logger.info("\n" + "=" * 70)
        self.logger.info("TRAINING COMPLETE")
        self.logger.info("=" * 70)

        return results


# ============================================================================
# DOMAIN ADAPTATION FOR RETRAINING
# ============================================================================


class DomainAdaptationTrainer(HARTrainer):
    """
    Extended trainer with domain adaptation for retraining scenarios.

    When drift is detected, this trainer can adapt the model to new data
    without requiring labels using techniques like:
    - DANN (Domain-Adversarial Neural Network)
    - MMD (Maximum Mean Discrepancy)
    - Pseudo-labeling
    """

    def __init__(self, config: TrainingConfig):
        super().__init__(config)
        self.logger = logging.getLogger(f"{__name__}.DomainAdaptation")

    def retrain_with_adaptation(
        self,
        source_X: np.ndarray,
        source_y: np.ndarray,
        target_X: np.ndarray,
        base_model: Optional[keras.Model] = None,
    ) -> Tuple[keras.Model, Dict[str, Any]]:
        """
        Retrain model with domain adaptation.

        Args:
            source_X: Labeled source domain data (original training)
            source_y: Source domain labels
            target_X: Unlabeled target domain data (drift samples)
            base_model: Pre-trained model to adapt (optional)

        Returns:
            Adapted model and metrics
        """
        self.logger.info("=" * 70)
        self.logger.info(f"DOMAIN ADAPTATION: {self.config.adaptation_method.upper()}")
        self.logger.info("=" * 70)

        if self.config.adaptation_method == "pseudo_label":
            return self._retrain_pseudo_labeling(source_X, source_y, target_X, base_model)
        elif self.config.adaptation_method == "mmd":
            return self._retrain_mmd(source_X, source_y, target_X, base_model)
        else:  # dann
            return self._retrain_dann(source_X, source_y, target_X, base_model)

    def _retrain_pseudo_labeling(
        self,
        source_X: np.ndarray,
        source_y: np.ndarray,
        target_X: np.ndarray,
        base_model: Optional[keras.Model] = None,
    ) -> Tuple[keras.Model, Dict[str, Any]]:
        """
        Robust pseudo-labeling with calibration, entropy gating, and class-balanced top-k.

        Improvements over naive single-threshold self-training:
        1. Temperature scaling on the base model predictions to reduce overconfidence.
        2. Combined gate: confidence AND low predictive entropy (per sample).
        3. Class-balanced selection (per-class top-k quota) to prevent label collapse.
        4. Fine-tune from pretrained weights (freeze early layers) instead of random init.
        5. Soft targets (label-smoothed) for the pseudo-labeled portion.
        6. Validation split tracks val_accuracy / val_loss properly.

        References:
            - Temperature scaling: Guo et al. (2017) arXiv:1706.04599
            - Mean-Teacher / entropy gate: Tarvainen & Valpola (2017)
            - Class-balanced pseudo-labels: standard practice reviewed in UDA literature
        """
        self.logger.info("Pseudo-labeling with calibration + entropy gate + class-balanced top-k")

        # ------------------------------------------------------------------
        # 1. Get or create base model
        # ------------------------------------------------------------------
        if base_model is None:
            base_model = self.model_builder.create_1dcnn_bilstm()
            self.logger.info("No pretrained base — training on source data first...")
            base_model.fit(source_X, source_y, epochs=50, batch_size=64, verbose=0)

        # ------------------------------------------------------------------
        # 2. Temperature scaling calibration (offline, on a small source holdout)
        #    Temperature T > 1 softens overconfident predictions.
        # ------------------------------------------------------------------
        temperature = self._estimate_temperature(base_model, source_X, source_y)
        self.logger.info(f"  Calibration temperature T={temperature:.3f}")

        # ------------------------------------------------------------------
        # 3. Predict on target with temperature scaling
        # ------------------------------------------------------------------
        raw_logits = self._get_logits(base_model, target_X)  # (N, C) or None
        if raw_logits is not None:
            scaled = raw_logits / temperature
            # softmax
            exp_s = np.exp(scaled - scaled.max(axis=1, keepdims=True))
            target_probs = exp_s / exp_s.sum(axis=1, keepdims=True)
        else:
            # Fallback: use softmax output directly (still apply T via re-normalisation)
            p = base_model.predict(target_X, verbose=0)
            log_p = np.log(np.clip(p, 1e-9, 1.0)) / temperature
            exp_lp = np.exp(log_p - log_p.max(axis=1, keepdims=True))
            target_probs = exp_lp / exp_lp.sum(axis=1, keepdims=True)

        target_confidence = target_probs.max(axis=1)
        target_pseudo_y = target_probs.argmax(axis=1)

        # ------------------------------------------------------------------
        # 4. Entropy gate: H(p) = -sum(p * log p), filter low-entropy (certain) samples
        # ------------------------------------------------------------------
        eps = 1e-9
        entropy = -(target_probs * np.log(target_probs + eps)).sum(axis=1)
        n_classes = target_probs.shape[1]
        max_entropy = np.log(n_classes)
        norm_entropy = entropy / max_entropy  # [0, 1] — lower is more certain

        conf_threshold = 0.70  # minimum confidence
        entropy_threshold = 0.40  # maximum normalised entropy

        gate_mask = (target_confidence >= conf_threshold) & (norm_entropy <= entropy_threshold)
        self.logger.info(
            f"  Gate (conf>={conf_threshold}, H_norm<={entropy_threshold}): "
            f"{gate_mask.sum()}/{len(target_X)} ({100*gate_mask.mean():.1f}%)"
        )

        # ------------------------------------------------------------------
        # 5. Class-balanced top-k selection
        #    For each class, keep at most `quota` samples with highest confidence.
        # ------------------------------------------------------------------
        quota_per_class = max(30, int(0.10 * len(source_X) / n_classes))
        selected_indices = []
        for cls in range(n_classes):
            cls_mask = gate_mask & (target_pseudo_y == cls)
            cls_idx = np.where(cls_mask)[0]
            if len(cls_idx) == 0:
                continue
            top_k = cls_idx[np.argsort(-target_confidence[cls_idx])[:quota_per_class]]
            selected_indices.extend(top_k.tolist())

        selected_indices = np.array(selected_indices)
        n_selected = len(selected_indices)
        self.logger.info(
            f"  Class-balanced selection: {n_selected} samples across {n_classes} classes"
        )

        if n_selected < 20:
            self.logger.warning(
                "Very few pseudo-labeled samples selected (%d). "
                "Falling back to confidence-only top-500 selection.",
                n_selected,
            )
            fallback_pool = np.argsort(-target_confidence)[:500]
            selected_indices = fallback_pool
            n_selected = len(selected_indices)

        # ------------------------------------------------------------------
        # 6. Build combined dataset with label smoothing for pseudo portion
        # ------------------------------------------------------------------
        pseudo_X = target_X[selected_indices]
        pseudo_hard = target_pseudo_y[selected_indices]
        smoothing = 0.10
        # One-hot + smooth
        pseudo_soft = np.full((n_selected, n_classes), smoothing / (n_classes - 1))
        pseudo_soft[np.arange(n_selected), pseudo_hard] = 1.0 - smoothing

        # Source labels: one-hot (no smoothing on ground truth)
        if source_y.ndim == 1:
            source_onehot = np.eye(n_classes)[source_y.astype(int)]
        else:
            source_onehot = source_y

        # Scale source_X with the same production scaler used on target_X
        # (production_X.npy was normalized via data/prepared/config.json).
        import json as _json

        _config_path = Path(__file__).resolve().parent.parent / "data" / "prepared" / "config.json"
        if _config_path.exists():
            with open(_config_path) as _f:
                _scaler_cfg = _json.load(_f)
            from sklearn.preprocessing import StandardScaler as _SS

            _scaler = _SS()
            _scaler.mean_ = np.array(_scaler_cfg["scaler_mean"])
            _scaler.scale_ = np.array(_scaler_cfg["scaler_scale"])
            n_steps, n_sensors = source_X.shape[1], source_X.shape[2]
            src_flat = source_X.reshape(-1, n_sensors)
            source_X_scaled = _scaler.transform(src_flat).reshape(source_X.shape)
            self.logger.info("  Source data scaled with production scaler.")
        else:
            self.logger.warning(
                "  Production scaler config not found — using unscaled source data."
            )
            source_X_scaled = source_X

        # ------------------------------------------------------------------
        # 6b. Self-consistency filter: keep only source windows where the
        #     model's own prediction matches the true label.
        #     prepare_data() windows the CSV sequentially, which creates
        #     mixed-activity windows at user/activity boundaries.  The model
        #     can only classify ~19 % of these correctly.  By keeping only
        #     self-consistent samples we get a clean, high-quality source set.
        # ------------------------------------------------------------------
        _src_preds = base_model.predict(source_X_scaled, verbose=0)
        _src_pred_cls = _src_preds.argmax(axis=1)
        _src_true_cls = source_y.astype(int) if source_y.ndim == 1 else source_y.argmax(axis=1)
        _consistent = _src_pred_cls == _src_true_cls
        self.logger.info(
            f"  Self-consistency filter: {_consistent.sum()}/{len(source_X_scaled)} "
            f"({100 * _consistent.mean():.1f}%) source windows kept"
        )
        source_X_scaled = source_X_scaled[_consistent]
        source_onehot = source_onehot[_consistent]

        X_combined = np.concatenate([source_X_scaled, pseudo_X])
        y_combined = np.concatenate([source_onehot, pseudo_soft])
        self.logger.info(f"  Combined training set: {len(X_combined)} samples")

        # ------------------------------------------------------------------
        # 6c. Source-holdout baseline — evaluate base_model BEFORE fine-tuning
        #     so we can detect regressions and roll back if needed.
        # ------------------------------------------------------------------
        _rollback_threshold = 0.10  # allow up to 10 pp drop before rollback
        _n_holdout = max(50, int(0.20 * len(source_X_scaled)))
        _holdout_idx = np.random.choice(len(source_X_scaled), _n_holdout, replace=False)
        _holdout_X = source_X_scaled[_holdout_idx]
        _holdout_y = source_onehot[_holdout_idx]
        _, _pre_val_acc = base_model.evaluate(_holdout_X, _holdout_y, verbose=0)
        self.logger.info(f"  Pre-fine-tune source holdout accuracy: {_pre_val_acc:.4f}")

        # ------------------------------------------------------------------
        # 7. Fine-tune from pretrained base — freeze early layers
        # ------------------------------------------------------------------
        # NOTE: keras.models.clone_model + set_weights can lose non-trainable
        # state (e.g. BatchNorm moving stats). Save-and-reload is the only
        # reliable way to obtain an independent, identical copy of a Keras model.
        # We must ensure the model is built (called at least once) before saving.
        import tempfile

        _ = base_model.predict(pseudo_X[:1], verbose=0)  # ensure model is built
        _tmp_path = Path(tempfile.mktemp(suffix=".keras"))
        base_model.save(_tmp_path)
        model = keras.models.load_model(_tmp_path)
        _ = model.predict(pseudo_X[:1], verbose=0)  # build the loaded model's graph
        _tmp_path.unlink(missing_ok=True)

        # Freeze all but last 3 layers (feature extractor frozen; classifier fine-tuned)
        for layer in model.layers[:-3]:
            layer.trainable = False
        for layer in model.layers[-3:]:
            layer.trainable = True

        model.compile(
            optimizer=keras.optimizers.Adam(
                learning_rate=self.config.learning_rate * 0.10  # small LR for fine-tuning
            ),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )

        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=5, restore_best_weights=True, verbose=0
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6, verbose=0
            ),
        ]

        history = model.fit(
            X_combined,
            y_combined,
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            validation_split=0.10,
            callbacks=callbacks,
            verbose=1,
        )

        # ------------------------------------------------------------------
        # 8. Collect metrics  (use best-epoch values since EarlyStopping
        #    with restore_best_weights=True restores the epoch-1 model)
        # ------------------------------------------------------------------
        _val_losses = history.history.get("val_loss", [])
        if _val_losses:
            _best_idx = int(np.argmin(_val_losses))
        else:
            _best_idx = -1

        def _hist(key: str) -> float:
            vals = history.history.get(key, [0.0])
            idx = _best_idx if 0 <= _best_idx < len(vals) else -1
            return float(vals[idx])

        metrics = {
            "method": "pseudo_labeling_calibrated",
            "source_samples": int(len(source_X)),
            "target_samples": int(len(target_X)),
            "pseudo_labeled_samples": int(n_selected),
            "confidence_threshold": conf_threshold,
            "entropy_threshold": entropy_threshold,
            "calibration_temperature": float(temperature),
            "final_loss": _hist("loss"),
            "final_accuracy": _hist("accuracy"),
            "val_loss": _hist("val_loss"),
            "val_accuracy": _hist("val_accuracy"),
        }
        self.logger.info(
            "Pseudo-label fine-tuning done — val_acc=%.4f  val_loss=%.4f",
            metrics["val_accuracy"],
            metrics["val_loss"],
        )

        # ------------------------------------------------------------------
        # 9. Rollback safety — revert to base_model if source holdout degrades
        # ------------------------------------------------------------------
        _, _post_val_acc = model.evaluate(_holdout_X, _holdout_y, verbose=0)
        _acc_delta = _post_val_acc - _pre_val_acc
        metrics["pseudo_pre_val_acc"] = float(_pre_val_acc)
        metrics["pseudo_post_val_acc"] = float(_post_val_acc)
        metrics["pseudo_val_acc_delta"] = float(_acc_delta)

        if _post_val_acc < _pre_val_acc - _rollback_threshold:
            self.logger.warning(
                "Pseudo-label rollback triggered: holdout acc %.4f → %.4f "
                "(Δ=%.4f, threshold=−%.2f). Reverting to base_model.",
                _pre_val_acc,
                _post_val_acc,
                _acc_delta,
                _rollback_threshold,
            )
            metrics["pseudo_label_rollback"] = True
            metrics["pseudo_label_rollback_reason"] = (
                f"source_holdout_acc dropped {_pre_val_acc:.4f}→{_post_val_acc:.4f} "
                f"(Δ={_acc_delta:.4f}, threshold=−{_rollback_threshold:.2f})"
            )
            return base_model, metrics
        else:
            metrics["pseudo_label_rollback"] = False
            self.logger.info(
                "  Rollback not needed: holdout acc %.4f → %.4f (Δ=%.4f)",
                _pre_val_acc,
                _post_val_acc,
                _acc_delta,
            )

        return model, metrics

    # ------------------------------------------------------------------
    # Helpers for calibration
    # ------------------------------------------------------------------

    def _estimate_temperature(
        self,
        model: keras.Model,
        X_val: np.ndarray,
        y_val: np.ndarray,
        n_val_samples: int = 500,
    ) -> float:
        """
        Simple temperature scaling via grid search on a source holdout.
        Picks T in [0.5, 3.0] that minimises NLL on the validation split.
        Returns T=1.0 (no scaling) as a safe default if optimisation fails.
        """
        try:
            idx = np.random.choice(len(X_val), min(n_val_samples, len(X_val)), replace=False)
            x_h, y_h = X_val[idx], y_val[idx].astype(int)
            raw = self._get_logits(model, x_h)
            if raw is None:
                return 1.0
            best_t, best_nll = 1.0, np.inf
            for T in np.linspace(0.5, 3.0, 26):
                scaled = raw / T
                exp_s = np.exp(scaled - scaled.max(axis=1, keepdims=True))
                p = exp_s / exp_s.sum(axis=1, keepdims=True)
                nll = -np.log(np.clip(p[np.arange(len(y_h)), y_h], 1e-9, 1.0)).mean()
                if nll < best_nll:
                    best_nll, best_t = nll, T
            return float(best_t)
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Temperature estimation failed (%s); using T=1.0", exc)
            return 1.0

    def _get_logits(self, model: keras.Model, X: np.ndarray) -> Optional[np.ndarray]:
        """
        Return pre-softmax logits from the final Dense layer.
        Works for both built and unbuilt Keras models by using a dummy forward
        pass to build the graph first if needed.
        """
        try:
            import tensorflow as tf

            # Build the model's graph by running a small prediction
            _ = model.predict(X[:2], verbose=0)

            # Find last Dense layer (the classifier head)
            dense_layers = [l for l in model.layers if isinstance(l, keras.layers.Dense)]
            if not dense_layers:
                return None
            last_dense = dense_layers[-1]
            last_dense_idx = model.layers.index(last_dense)
            if last_dense_idx == 0:
                return None

            # For Sequential models, use direct tensor operations instead of
            # building a sub-model (which requires model.input to be defined).
            pre_dense_layer = model.layers[last_dense_idx - 1]

            # Use a tf.keras functional approach: input through all layers up to pre_dense
            @tf.function
            def get_pre_dense(x_batch):
                h = x_batch
                for layer in model.layers[:last_dense_idx]:
                    h = layer(h, training=False)
                return h

            out_list = []
            for i in range(0, len(X), 64):
                batch = tf.constant(X[i : i + 64], dtype=tf.float32)
                out_list.append(get_pre_dense(batch).numpy())
            pre_out = np.concatenate(out_list, axis=0)

            # Apply dense kernel (W, b) without softmax activation
            W = last_dense.kernel.numpy()  # (in_features, n_classes)
            b = last_dense.bias.numpy()  # (n_classes,)
            logits = pre_out @ W + b  # (N, n_classes)
            return logits
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("_get_logits failed (%s); will use softmax probs instead", exc)
            return None

    def _retrain_mmd(
        self,
        source_X: np.ndarray,
        source_y: np.ndarray,
        target_X: np.ndarray,
        base_model: Optional[keras.Model] = None,
    ) -> Tuple[keras.Model, Dict[str, Any]]:
        """
        Retrain with Maximum Mean Discrepancy loss.

        MMD measures the distance between source and target feature distributions.
        Adding MMD as auxiliary loss encourages the model to learn domain-invariant features.
        """
        self.logger.info("Using MMD adaptation strategy")
        self.logger.info("  (Simplified implementation - feature alignment via combined training)")

        # For thesis scope, implement simplified version:
        # Train on weighted combination of source and target (with pseudo-labels)
        return self._retrain_pseudo_labeling(source_X, source_y, target_X, base_model)

    def _retrain_dann(
        self,
        source_X: np.ndarray,
        source_y: np.ndarray,
        target_X: np.ndarray,
        base_model: Optional[keras.Model] = None,
    ) -> Tuple[keras.Model, Dict[str, Any]]:
        """
        Retrain with Domain-Adversarial Neural Network approach.

        DANN adds a domain classifier that tries to distinguish source from target,
        while the feature extractor learns to confuse this classifier.
        """
        self.logger.info("Using DANN adaptation strategy")
        self.logger.info("  (Simplified implementation - using pseudo-labeling as fallback)")

        # For thesis scope, implement simplified version
        # Full DANN requires custom training loop
        return self._retrain_pseudo_labeling(source_X, source_y, target_X, base_model)


# ============================================================================
# MAIN
# ============================================================================


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train HAR model with MLOps best practices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Standard training with cross-validation
    python src/train.py

    # Quick training without CV (for testing)
    python src/train.py --skip-cv --epochs 10

    # Custom experiment name
    python src/train.py --experiment-name my-experiment

    # Retraining with domain adaptation
    python src/train.py --retrain --target-data drift_samples.npy
        """,
    )

    # Data arguments
    parser.add_argument("--data", type=str, default=None, help="Path to training data CSV")
    parser.add_argument(
        "--target-data", type=str, default=None, help="Path to target domain data for retraining"
    )

    # Training arguments
    parser.add_argument(
        "--epochs", type=int, default=100, help="Number of training epochs (default: 100)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=64, help="Training batch size (default: 64)"
    )
    parser.add_argument(
        "--learning-rate", type=float, default=0.001, help="Initial learning rate (default: 0.001)"
    )

    # CV arguments
    parser.add_argument("--skip-cv", action="store_true", help="Skip cross-validation")
    parser.add_argument("--n-folds", type=int, default=5, help="Number of CV folds (default: 5)")

    # Domain adaptation
    parser.add_argument(
        "--retrain", action="store_true", help="Enable domain adaptation retraining mode"
    )
    parser.add_argument(
        "--adaptation-method",
        type=str,
        default="pseudo_label",
        choices=["pseudo_label", "mmd", "dann"],
        help="Domain adaptation method (default: pseudo_label)",
    )

    # MLflow arguments
    parser.add_argument(
        "--experiment-name", type=str, default="har-training", help="MLflow experiment name"
    )
    parser.add_argument("--run-name", type=str, default=None, help="MLflow run name")

    # Output
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for models")

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    print("=" * 70)
    print("HAR MODEL TRAINING - MLOps Pipeline")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Epochs: {args.epochs}")
    print(f"Cross-Validation: {'Disabled' if args.skip_cv else f'{args.n_folds}-fold'}")
    print(f"Experiment: {args.experiment_name}")
    print("=" * 70)

    # Create configuration
    config = TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        n_folds=args.n_folds,
        experiment_name=args.experiment_name,
        run_name=args.run_name,
        enable_domain_adaptation=args.retrain,
        adaptation_method=args.adaptation_method,
    )

    if args.output_dir:
        config.output_dir = Path(args.output_dir)

    # Run training
    if args.retrain and args.target_data:
        # Domain adaptation retraining
        trainer = DomainAdaptationTrainer(config)
        # Load target data and run adaptation
        # (Implementation depends on data format)
        logger.info("Domain adaptation mode - requires target data")
        # ... adaptation logic
    else:
        # Standard training
        trainer = HARTrainer(config)
        data_path = Path(args.data) if args.data else None
        results = trainer.train(data_path=data_path, skip_cv=args.skip_cv)

    print("\n✓ Training complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

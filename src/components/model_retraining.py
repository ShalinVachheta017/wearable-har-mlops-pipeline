"""
Component 8 – Model Retraining

Wraps:  src/train.py  →  HARTrainer / DomainAdaptationTrainer
        src/domain_adaptation/adabn.py  →  adapt_bn_statistics
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

from src.config import DEFAULT_MODEL_PATH
from src.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelRetrainingArtifact,
    TriggerEvaluationArtifact,
)
from src.entity.config_entity import ModelRetrainingConfig, PipelineConfig

logger = logging.getLogger(__name__)


class ModelRetraining:
    """Retrain the model — standard, AdaBN, TENT, AdaBN+TENT, or pseudo-label adaptation.

    Implemented adaptation methods:
        adabn         — Unsupervised BN statistics adaptation (no labels needed).
        tent          — TENT entropy minimisation of BN affine parameters.
        adabn_tent    — Two-stage: AdaBN then TENT fine-tuning.
        pseudo_label  — Self-training with confidence-filtered pseudo-labels.

    NOTE: DANN (domain-adversarial) and MMD (maximum mean discrepancy) are referenced
    in literature but are NOT implemented in this codebase.  Passing those strings
    will raise a NotImplementedError.
    """

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        config: ModelRetrainingConfig,
        trigger_artifact: Optional[TriggerEvaluationArtifact] = None,
        transformation_artifact: Optional[DataTransformationArtifact] = None,
    ):
        self.pipeline_config = pipeline_config
        self.config = config
        self.trigger_artifact = trigger_artifact
        self.transformation_artifact = transformation_artifact

    # ------------------------------------------------------------------ #
    def initiate_model_retraining(self) -> ModelRetrainingArtifact:
        logger.info("=" * 60)
        logger.info("STAGE 8 — Model Retraining")
        logger.info("=" * 60)

        output_dir = Path(self.config.output_dir or self.pipeline_config.models_dir / "retrained")
        output_dir.mkdir(parents=True, exist_ok=True)

        method = self.config.adaptation_method if self.config.enable_adaptation else "none"
        logger.info("Retraining method: %s", method)

        if method == "adabn":
            return self._run_adabn(output_dir)
        elif method == "tent":
            return self._run_tent(output_dir)
        elif method == "adabn_tent":
            # Two-stage: AdaBN first, then TENT fine-tunes BN affine params
            return self._run_adabn_then_tent(output_dir)
        elif method == "pseudo_label":
            return self._run_pseudo_label(output_dir)
        elif method in ("mmd", "dann"):
            raise NotImplementedError(
                f"Adaptation method '{method}' (MMD / DANN) is referenced in literature "
                "but is NOT implemented in this pipeline.  "
                "Use one of: adabn | tent | adabn_tent | pseudo_label."
            )
        else:
            return self._run_standard(output_dir)

    # ------------------------------------------------------------------ #
    def _run_adabn(self, output_dir: Path) -> ModelRetrainingArtifact:
        """Unsupervised domain adaptation via AdaBN (no labels needed)."""
        from src.domain_adaptation.adabn import adabn_score_confidence, adapt_bn_statistics

        try:
            from tensorflow import keras
        except ImportError:
            raise ImportError("TensorFlow is required for AdaBN retraining.")

        # Load base model
        model_path = self.config.source_data_path  # repurposed or from pretrained
        base_model_path = (
            DEFAULT_MODEL_PATH
        )
        logger.info("Loading base model: %s", base_model_path)
        model = keras.models.load_model(base_model_path)

        # Load target data
        target_npy = self.config.target_data_npy
        if target_npy is None and self.transformation_artifact:
            target_npy = self.transformation_artifact.production_X_path
        if target_npy is None:
            raise ValueError("AdaBN requires target_data_npy (production data).")

        target_X = np.load(target_npy)
        logger.info("Target data: %s", target_X.shape)

        # Before-adaptation confidence
        before = adabn_score_confidence(model, target_X)
        logger.info("Before AdaBN — mean confidence: %.4", before["mean_confidence"])

        # Adapt
        model = adapt_bn_statistics(
            model,
            target_X,
            n_batches=self.config.adabn_n_batches,
            batch_size=self.config.batch_size,
        )

        # After-adaptation confidence
        after = adabn_score_confidence(model, target_X)
        logger.info("After AdaBN — mean confidence: %.4", after["mean_confidence"])

        # Save adapted model
        save_path = output_dir / "adabn_adapted_model.keras"
        model.save(save_path)
        logger.info("Adapted model saved: %s", save_path)

        metrics = {
            "before_mean_confidence": before["mean_confidence"],
            "after_mean_confidence": after["mean_confidence"],
            "confidence_improvement": after["mean_confidence"] - before["mean_confidence"],
            "before_low_conf_ratio": before["low_confidence_ratio"],
            "after_low_conf_ratio": after["low_confidence_ratio"],
        }

        return ModelRetrainingArtifact(
            retrained_model_path=save_path,
            training_report={"before": before, "after": after},
            adaptation_method="adabn",
            metrics=metrics,
            n_target_samples=int(target_X.shape[0]),
            retraining_timestamp=datetime.now().isoformat(),
        )

    # ------------------------------------------------------------------ #
    def _run_tent(self, output_dir: Path) -> ModelRetrainingArtifact:
        """Test-time adaptation via TENT (entropy minimisation on BN affine params)."""
        from src.domain_adaptation.tent import tent_adapt, tent_score

        try:
            from tensorflow import keras
        except ImportError:
            raise ImportError("TensorFlow is required for TENT.")

        base_model_path = (
            DEFAULT_MODEL_PATH
        )
        logger.info("Loading base model: %s", base_model_path)
        model = keras.models.load_model(base_model_path)

        target_npy = self.config.target_data_npy
        if target_npy is None and self.transformation_artifact:
            target_npy = self.transformation_artifact.production_X_path
        if target_npy is None:
            raise ValueError("TENT requires target_data_npy (production data).")

        target_X = np.load(target_npy)
        logger.info("Target data: %s", target_X.shape)

        before = tent_score(model, target_X)
        logger.info(
            "Before TENT — mean confidence: %.4f  norm_entropy: %.4f",
            before["mean_confidence"],
            before["mean_normalised_entropy"],
        )

        model, tent_meta = tent_adapt(
            model,
            target_X,
            n_steps=self.config.adabn_n_batches or 10,
            learning_rate=self.config.learning_rate or 1e-4,
            batch_size=self.config.batch_size,
        )

        after = tent_score(model, target_X)
        logger.info(
            "After TENT  — mean confidence: %.4f  norm_entropy: %.4f",
            after["mean_confidence"],
            after["mean_normalised_entropy"],
        )
        if tent_meta["tent_rollback"]:
            logger.warning(
                "TENT rollback applied — affine weights reverted (entropy increased %.3f)",
                tent_meta["tent_entropy_delta"],
            )

        save_path = output_dir / "tent_adapted_model.keras"
        model.save(save_path)
        logger.info("TENT model saved: %s", save_path)

        metrics = {
            "before_mean_confidence": before["mean_confidence"],
            "after_mean_confidence": after["mean_confidence"],
            "confidence_improvement": after["mean_confidence"] - before["mean_confidence"],
            "before_norm_entropy": before["mean_normalised_entropy"],
            "after_norm_entropy": after["mean_normalised_entropy"],
            "entropy_reduction": before["mean_normalised_entropy"]
            - after["mean_normalised_entropy"],
            "tent_rollback": int(tent_meta["tent_rollback"]),
            "tent_entropy_delta": tent_meta["tent_entropy_delta"],
        }

        return ModelRetrainingArtifact(
            retrained_model_path=save_path,
            training_report={"before": before, "after": after},
            adaptation_method="tent",
            metrics=metrics,
            n_target_samples=int(target_X.shape[0]),
            retraining_timestamp=datetime.now().isoformat(),
        )

    # ------------------------------------------------------------------ #
    def _run_adabn_then_tent(self, output_dir: Path) -> ModelRetrainingArtifact:
        """Two-stage: AdaBN (running stats) → TENT (affine fine-tuning)."""
        from src.domain_adaptation.adabn import adabn_score_confidence, adapt_bn_statistics
        from src.domain_adaptation.tent import tent_adapt, tent_score

        try:
            from tensorflow import keras
        except ImportError:
            raise ImportError("TensorFlow is required.")

        base_model_path = (
            DEFAULT_MODEL_PATH
        )
        model = keras.models.load_model(base_model_path)

        target_npy = self.config.target_data_npy
        if target_npy is None and self.transformation_artifact:
            target_npy = self.transformation_artifact.production_X_path
        if target_npy is None:
            raise ValueError("adabn_tent requires target_data_npy.")

        target_X = np.load(target_npy)

        before = adabn_score_confidence(model, target_X)
        logger.info("Before AdaBN+TENT — mean confidence: %.4", before["mean_confidence"])

        # Stage 1: AdaBN
        model = adapt_bn_statistics(
            model,
            target_X,
            n_batches=self.config.adabn_n_batches,
            batch_size=self.config.batch_size,
        )

        # Stage 2: TENT — freeze BN running stats so AdaBN calibration is preserved
        model, tent_meta = tent_adapt(
            model,
            target_X,
            n_steps=10,
            learning_rate=self.config.learning_rate or 1e-4,
            batch_size=self.config.batch_size,
        )

        after = tent_score(model, target_X)
        logger.info(
            "After AdaBN+TENT — mean confidence: %.4f  norm_entropy: %.4f",
            after["mean_confidence"],
            after["mean_normalised_entropy"],
        )
        if tent_meta["tent_rollback"]:
            logger.warning(
                "TENT rollback applied — affine weights reverted (entropy increased %.3f)",
                tent_meta["tent_entropy_delta"],
            )

        save_path = output_dir / "adabn_tent_adapted_model.keras"
        model.save(save_path)

        metrics = {
            "before_mean_confidence": before["mean_confidence"],
            "after_mean_confidence": after["mean_confidence"],
            "confidence_improvement": after["mean_confidence"] - before["mean_confidence"],
            "after_norm_entropy": after["mean_normalised_entropy"],
            "tent_rollback": int(tent_meta["tent_rollback"]),
            "tent_entropy_delta": tent_meta["tent_entropy_delta"],
        }

        return ModelRetrainingArtifact(
            retrained_model_path=save_path,
            training_report={"before": before, "after": after},
            adaptation_method="adabn_tent",
            metrics=metrics,
            n_target_samples=int(target_X.shape[0]),
            retraining_timestamp=datetime.now().isoformat(),
        )

    # ------------------------------------------------------------------ #
    def _run_pseudo_label(self, output_dir: Path) -> ModelRetrainingArtifact:
        """Semi-supervised: pseudo-label + fine-tune."""
        from src.train import DomainAdaptationTrainer, TrainingConfig

        try:
            from tensorflow import keras
        except ImportError:
            raise ImportError("TensorFlow is required for pseudo-label retraining.")

        train_cfg = TrainingConfig(
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            enable_domain_adaptation=True,
            adaptation_method="pseudo_label",
            output_dir=str(output_dir),
            experiment_name=self.config.experiment_name,
        )

        trainer = DomainAdaptationTrainer(train_cfg)

        # Source data
        source_path = self.config.source_data_path or (
            self.pipeline_config.data_raw_dir.parent / "all_users_data_labeled.csv"
        )
        from src.train import DataLoader as _DataLoader

        data_loader = _DataLoader(train_cfg, logger)

        # Load and prepare labeled data
        df_source = data_loader.load_training_data(Path(source_path))
        source_X, source_y = data_loader.prepare_data(df_source)

        # Share fitted data_loader so label_encoder.classes_ is available
        trainer.data_loader = data_loader

        # Target data
        target_npy = self.config.target_data_npy
        if target_npy is None and self.transformation_artifact:
            target_npy = self.transformation_artifact.production_X_path
        target_X = np.load(target_npy) if target_npy else None

        # Base model
        base_model_path = (
            DEFAULT_MODEL_PATH
        )
        base_model = keras.models.load_model(base_model_path)

        model, metrics = trainer.retrain_with_adaptation(
            source_X,
            source_y,
            target_X,
            base_model,
        )

        save_path = output_dir / "pseudo_label_model.keras"
        model.save(save_path)

        # DomainAdaptationTrainer returns final_accuracy / final_loss at top level
        artifact_metrics = {
            k: metrics[k]
            for k in (
                "final_accuracy",
                "final_loss",
                "val_accuracy",
                "val_loss",
                "pseudo_labeled_samples",
                "confidence_threshold",
                "entropy_threshold",
            )
            if k in metrics
        }
        return ModelRetrainingArtifact(
            retrained_model_path=save_path,
            training_report=metrics,
            adaptation_method="pseudo_label",
            metrics=artifact_metrics,
            n_source_samples=int(source_X.shape[0]),
            n_target_samples=int(target_X.shape[0]) if target_X is not None else 0,
            retraining_timestamp=datetime.now().isoformat(),
        )

    # ------------------------------------------------------------------ #
    def _run_standard(self, output_dir: Path) -> ModelRetrainingArtifact:
        """Standard supervised retraining on labeled data."""
        from src.train import HARTrainer, TrainingConfig

        train_cfg = TrainingConfig(
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            n_folds=self.config.n_folds,
            output_dir=str(output_dir),
            experiment_name=self.config.experiment_name,
        )

        trainer = HARTrainer(train_cfg)

        source_path = self.config.source_data_path or (
            self.pipeline_config.data_raw_dir.parent / "all_users_data_labeled.csv"
        )

        from src.train import DataLoader as _DataLoader

        data_loader = _DataLoader(train_cfg, logger)

        # Load and prepare labeled data
        df_source = data_loader.load_training_data(Path(source_path))
        X, y = data_loader.prepare_data(df_source)

        # Share fitted data_loader so label_encoder.classes_ is available
        # inside train_final_model -> _save_training_artifacts
        trainer.data_loader = data_loader

        # Cross-validation (optional)
        if not self.config.skip_cv:
            cv_results = trainer.run_cross_validation(X, y)
            logger.info("CV results: %s", cv_results)

        # Final model
        model, metrics = trainer.train_final_model(X, y, save_artifacts=True)

        save_path = output_dir / "retrained_model.keras"
        model.save(save_path)

        return ModelRetrainingArtifact(
            retrained_model_path=save_path,
            training_report=metrics,
            adaptation_method="none",
            metrics=metrics,
            n_source_samples=int(X.shape[0]),
            retraining_timestamp=datetime.now().isoformat(),
        )

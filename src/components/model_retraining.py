"""
Component 8 – Model Retraining (supervised, labeled-data only)

Wraps: src/train.py → HARTrainer

The defended runtime supports supervised retraining only. Unsupervised
domain-adaptation methods (AdaBN, TENT, pseudo-label) were evaluated during
development but excluded from the defended pipeline under the auto-retrain=false
governance freeze. The archived implementation is in _archive/domain_adaptation/.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelRetrainingArtifact,
    TriggerEvaluationArtifact,
)
from src.entity.config_entity import ModelRetrainingConfig, PipelineConfig

logger = logging.getLogger(__name__)


class ModelRetraining:
    """Supervised retraining on labeled data."""

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

    def initiate_model_retraining(self) -> ModelRetrainingArtifact:
        logger.info("=" * 60)
        logger.info("STAGE 8 — Model Retraining (supervised)")
        logger.info("=" * 60)

        output_dir = Path(
            self.config.output_dir or self.pipeline_config.models_dir / "retrained"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        return self._run_standard(output_dir)

    def _run_standard(self, output_dir: Path) -> ModelRetrainingArtifact:
        """Fine-tune the current deployed model (Model D1) on labeled data.

        Loads the active runtime model and continues training it with the D1
        recipe (two-phase fine-tune, train-only augmentation, balanced class
        weights, user-holdout validation) rather than training a fresh model
        from scratch, so the candidate keeps the deployed architecture. The
        saved train-only scaler is reused for train--serve parity. The candidate
        is compared against the current model in Stage 9 (registration).
        """
        import json

        from src.config import DEFAULT_MODEL_PATH, SCALER_CANONICAL
        from src.train import DataLoader as _DataLoader
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
        data_loader = _DataLoader(train_cfg, logger)
        df_source = data_loader.load_training_data(Path(source_path))
        X, y, groups = data_loader.prepare_data(df_source)
        trainer.data_loader = data_loader

        # Resolve the current deployed model and its train-only scaler.
        base_model_path = Path(self.config.base_model_path or DEFAULT_MODEL_PATH)
        scaler_mean = scaler_scale = None
        scaler_path = Path(SCALER_CANONICAL)
        if scaler_path.exists():
            cfg = json.loads(scaler_path.read_text())
            scaler_mean = cfg.get("scaler_mean", cfg.get("mean"))
            scaler_scale = cfg.get("scaler_scale", cfg.get("scale"))
        elif self.config.allow_unscaled_finetune:
            logger.warning(
                "Canonical scaler not found at %s; allow_unscaled_finetune=True — "
                "fine-tuning unscaled (experimental, candidate is NOT contract-valid).",
                scaler_path,
            )
        else:
            raise RuntimeError(
                f"Canonical scaler not found at {scaler_path}. The deployed D1 model "
                "expects z-score scaled windows; fine-tuning unscaled would produce a "
                "candidate incompatible with the runtime contract. Restore the scaler "
                "or set allow_unscaled_finetune=True for explicit experiments."
            )

        model, metrics = trainer.finetune_from_current(
            X,
            y,
            groups,
            base_model_path=base_model_path,
            scaler_mean=scaler_mean,
            scaler_scale=scaler_scale,
            augment_multiplier=self.config.augment_multiplier,
            allow_unscaled=self.config.allow_unscaled_finetune,
        )

        save_path = output_dir / "retrained_model.keras"
        model.save(save_path)

        return ModelRetrainingArtifact(
            retrained_model_path=save_path,
            training_report=metrics,
            metrics=metrics,
            n_source_samples=int(X.shape[0]),
            n_target_samples=int(X.shape[0]),
            retraining_timestamp=datetime.now().isoformat(),
        )

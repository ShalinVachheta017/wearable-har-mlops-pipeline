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

        output_dir = Path(self.config.output_dir or self.pipeline_config.models_dir / "retrained")
        output_dir.mkdir(parents=True, exist_ok=True)

        return self._run_standard(output_dir)

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
        df_source = data_loader.load_training_data(Path(source_path))
        X, y = data_loader.prepare_data(df_source)
        trainer.data_loader = data_loader

        if not self.config.skip_cv:
            cv_results = trainer.run_cross_validation(X, y)
            logger.info("CV results: %s", cv_results)

        model, metrics = trainer.train_final_model(X, y, save_artifacts=True)

        save_path = output_dir / "retrained_model.keras"
        model.save(save_path)

        return ModelRetrainingArtifact(
            retrained_model_path=save_path,
            training_report=metrics,
            metrics=metrics,
            n_source_samples=int(X.shape[0]),
            retraining_timestamp=datetime.now().isoformat(),
        )

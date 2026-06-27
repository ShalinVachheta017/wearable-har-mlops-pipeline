"""
Component 9 – Model Registration

Wraps:  src/model_rollback.py  →  ModelRegistry
"""

import logging
from pathlib import Path
from typing import Optional

from src.entity.artifact_entity import (
    ModelEvaluationArtifact,
    ModelRegistrationArtifact,
    ModelRetrainingArtifact,
)
from src.entity.config_entity import ModelRegistrationConfig, PipelineConfig

logger = logging.getLogger(__name__)


class ModelRegistration:
    """Register, validate, and (optionally) deploy the retrained model."""

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        config: ModelRegistrationConfig,
        retraining_artifact: ModelRetrainingArtifact,
        evaluation_artifact: Optional[ModelEvaluationArtifact] = None,
    ):
        self.pipeline_config = pipeline_config
        self.config = config
        self.retraining_artifact = retraining_artifact
        self.evaluation_artifact = evaluation_artifact

    # ------------------------------------------------------------------ #
    def initiate_model_registration(self) -> ModelRegistrationArtifact:
        logger.info("=" * 60)
        logger.info("STAGE 9 — Model Registration")
        logger.info("=" * 60)

        from src.model_rollback import ModelRegistry

        registry_dir = self.config.registry_dir or (
            self.pipeline_config.models_dir / "registry"
        )
        registry = ModelRegistry(registry_dir=Path(registry_dir))

        model_path = Path(
            self.config.model_path or self.retraining_artifact.retrained_model_path
        )
        version = self.config.version  # None → auto-increment
        metrics = self.retraining_artifact.metrics or {}

        # Register
        model_version = registry.register_model(
            model_path=model_path,
            version=version or "auto",
            metrics=metrics,
        )
        logger.info("Registered model version: %s", model_version.version)

        # Proxy validation (compare metrics with current deployed)
        is_better = True  # default: first registration is always "better"
        if self.config.proxy_validation:
            current = registry.get_current_version()
            if current:
                logger.info("Current deployed version: %s", current)
                # Find metrics for the current deployed version
                all_versions = registry.list_versions()
                current_metrics = next(
                    (v["metrics"] for v in all_versions if v["version"] == current),
                    {},
                )
                # Compare using val_accuracy or accuracy
                new_acc = metrics.get("val_accuracy", metrics.get("accuracy"))
                cur_acc = current_metrics.get(
                    "val_accuracy", current_metrics.get("accuracy")
                )
                tol = getattr(self.config, "degradation_tolerance", 0.005)
                if new_acc is not None and cur_acc is not None:
                    is_better = float(new_acc) >= float(cur_acc) - tol
                    if not is_better:
                        logger.warning(
                            "Model REGRESSION detected: new_acc=%.4f < cur_acc=%.4f - tol=%.4f "
                            "(%s). Model registered but NOT deployed.",
                            float(new_acc),
                            float(cur_acc),
                            tol,
                            "use --degradation-tolerance to adjust",
                        )
                    else:
                        logger.info(
                            "Model comparison: new_acc=%.4f vs current_acc=%.4f (tol=%.4f) "
                            "→ is_better=%s",
                            float(new_acc),
                            float(cur_acc),
                            tol,
                            is_better,
                        )
                else:
                    # Unsupervised TTA (AdaBN/TENT) — no labeled val_accuracy.
                    # Governance is enforced at the deploy gate (auto_deploy=False
                    # by default). If block_if_no_metrics=True, block deployment.
                    block = getattr(self.config, "block_if_no_metrics", False)
                    if block:
                        is_better = False
                        logger.warning(
                            "block_if_no_metrics=True and accuracy key missing. "
                            "New metrics keys: %s | Current metrics keys: %s. "
                            "Model registered but deployment BLOCKED.",
                            list(metrics.keys()),
                            list(current_metrics.keys()),
                        )
                    else:
                        is_better = True
                        logger.info(
                            "Accuracy key missing (unsupervised TTA). "
                            "New metrics keys: %s | Current metrics keys: %s. "
                            "Registering as is_better=True; deployment gate controls shipping "
                            "(auto_deploy=%s). "
                            "Set block_if_no_metrics=True for strict mode.",
                            list(metrics.keys()),
                            list(current_metrics.keys()),
                            self.config.auto_deploy,
                        )

        # Deploy if auto_deploy is on and model is better (or first time)
        deployed = False
        if self.config.auto_deploy and is_better:
            deployed = registry.deploy_model(model_version.version)
            if deployed:
                logger.info("Model v%s deployed.", model_version.version)
            else:
                logger.warning("Deployment of v%s failed.", model_version.version)

        previous = registry.get_current_version() if not deployed else None

        return ModelRegistrationArtifact(
            registered_version=model_version.version,
            is_deployed=deployed,
            is_better_than_current=is_better,
            proxy_metrics=metrics,
            previous_version=previous,
            registry_path=Path(registry_dir),
        )

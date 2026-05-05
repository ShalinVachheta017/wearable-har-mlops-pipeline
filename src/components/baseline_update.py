"""
Component 10 – Baseline Update
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.entity.artifact_entity import (
    BaselineUpdateArtifact,
    ModelRetrainingArtifact,
)
from src.entity.config_entity import BaselineUpdateConfig, PipelineConfig
from src.utils.common import get_timestamp

logger = logging.getLogger(__name__)


class BaselineUpdate:
    """Rebuild drift baselines after retraining."""

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        config: BaselineUpdateConfig,
        retraining_artifact: Optional[ModelRetrainingArtifact] = None,
    ):
        self.pipeline_config = pipeline_config
        self.config = config
        self.retraining_artifact = retraining_artifact

    # ------------------------------------------------------------------ #
    def initiate_baseline_update(self) -> BaselineUpdateArtifact:
        logger.info("=" * 60)
        logger.info("STAGE 10 — Baseline Update")
        logger.info("=" * 60)

        from src.monitoring.baseline_builder import BaselineBuilder

        builder = BaselineBuilder()

        # Determine data source for baseline
        data_path = self.config.training_data_path or (
            self.pipeline_config.data_raw_dir.parent / "all_users_data_labeled.csv"
        )
        logger.info("Building baseline from: %s", data_path)

        # Build
        baseline = builder.build_from_csv(data_path)

        # Save paths
        output_baseline = self.config.output_baseline_path or (
            self.pipeline_config.models_dir / "training_baseline.json"
        )
        output_normalized = self.config.output_normalized_path or (
            self.pipeline_config.models_dir / "normalized_baseline.json"
        )

        promote = getattr(self.config, "promote_to_shared", False)

        # Artifact dir is always prepared so we have somewhere to write
        artifact_models = Path(self.pipeline_config.artifact_dir) / "models"
        artifact_models.mkdir(parents=True, exist_ok=True)

        if promote:
            # Write to shared paths that monitoring reads at runtime.
            # Also save a versioned copy so the change is reversible.
            save_baseline_path = Path(output_baseline)
            save_normalized_path = Path(output_normalized)

            builder.save(str(save_baseline_path))
            logger.info("Baseline PROMOTED to shared path: %s", save_baseline_path)

            builder.save_normalized(str(save_normalized_path))
            logger.info("Normalised baseline PROMOTED to shared path: %s", save_normalized_path)

            # Versioned archive (e.g. training_baseline_20260219_130000.json)
            ts = get_timestamp()
            versioned_dir = save_baseline_path.parent / "baseline_versions"
            versioned_dir.mkdir(parents=True, exist_ok=True)
            for src_p, dst_name in [
                (save_baseline_path, f"training_baseline_{ts}.json"),
                (save_normalized_path, f"normalized_baseline_{ts}.json"),
            ]:
                shutil.copy2(str(src_p), versioned_dir / dst_name)
                logger.info("Versioned archive saved: %s", versioned_dir / dst_name)

            # Copy promoted baselines into artifact dir for traceability
            for src_p in (save_baseline_path, save_normalized_path):
                if src_p.exists():
                    dst = artifact_models / src_p.name
                    shutil.copy2(str(src_p), dst)
                    logger.info("Baseline copied to artifact: %s", dst)
        else:
            # Governance: write ONLY to the artifact dir — NEVER touch models/
            # so monitoring's shared baseline is not silently overwritten.
            save_baseline_path = artifact_models / Path(output_baseline).name
            save_normalized_path = artifact_models / Path(output_normalized).name

            builder.save(str(save_baseline_path))
            builder.save_normalized(str(save_normalized_path))
            logger.info(
                "Baseline NOT promoted to shared path (promote_to_shared=False). "
                "Saved to artifact only: %s. Re-run with --update-baseline to promote.",
                save_baseline_path,
            )

        # Log baseline files as MLflow artifacts if a run is active
        try:
            import mlflow

            if mlflow.active_run():
                mlflow.log_artifact(str(save_baseline_path), artifact_path="baseline")
                mlflow.log_artifact(str(save_normalized_path), artifact_path="baseline")
                mlflow.log_param("baseline_promoted", promote)
                logger.info("Baseline files logged as MLflow artifacts.")
        except Exception as _mlflow_err:
            logger.debug("MLflow baseline artifact logging skipped: %s", _mlflow_err)

        # Stats summary
        stats = {
            "n_channels": baseline.get("n_channels", 6),
            "n_samples": baseline.get("n_samples", 0),
            "activities": (
                list(baseline.get("per_class", {}).keys()) if "per_class" in baseline else []
            ),
        }

        return BaselineUpdateArtifact(
            baseline_path=save_baseline_path,
            normalized_baseline_path=save_normalized_path,
            n_channels=stats["n_channels"],
            stats_summary=stats,
            update_timestamp=datetime.now().isoformat(),
        )

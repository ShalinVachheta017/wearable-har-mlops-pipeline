"""
Component 5 – Model Evaluation

Wraps:  src/evaluate_predictions.py  →  EvaluationPipeline
"""

import logging
from pathlib import Path
from typing import Optional

from src.entity.artifact_entity import ModelEvaluationArtifact, ModelInferenceArtifact
from src.entity.config_entity import ModelEvaluationConfig, PipelineConfig

logger = logging.getLogger(__name__)


class ModelEvaluation:
    """Evaluate predictions (confidence, distribution, ECE, class metrics)."""

    def __init__(
        self,
        pipeline_config: PipelineConfig,
        config: ModelEvaluationConfig,
        inference_artifact: ModelInferenceArtifact,
    ):
        self.pipeline_config = pipeline_config
        self.config = config
        self.inference_artifact = inference_artifact

    # ------------------------------------------------------------------ #
    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
        logger.info("=" * 60)
        logger.info("STAGE 5 — Model Evaluation")
        logger.info("=" * 60)

        from src.evaluate_predictions import EvaluationConfig as _EvalConfig
        from src.evaluate_predictions import EvaluationPipeline as _EvalPipeline

        predictions_csv = Path(
            self.config.predictions_csv or self.inference_artifact.predictions_csv_path
        )
        output_dir = Path(self.config.output_dir or self.pipeline_config.outputs_dir / "evaluation")
        output_dir.mkdir(parents=True, exist_ok=True)

        eval_cfg = _EvalConfig(
            predictions_path=predictions_csv.parent,
            labels_path=self.config.labels_path,
            output_dir=output_dir,
            confidence_bins=self.config.confidence_bins,
        )

        pipe = _EvalPipeline(config=eval_cfg)
        result = pipe.run(predictions_csv=predictions_csv)

        dist = result.get("distribution", {})
        dominance_warning = bool(dist.pop("_distribution_dominance_warning", False))
        # Remove internal keys added by analyze_distribution before storing.
        dist.pop("_dominant_class", None)
        dist.pop("_dominant_pct", None)

        return ModelEvaluationArtifact(
            report_json_path=result.get("report_json"),
            report_text_path=result.get("report_text"),
            distribution_summary=dist,
            confidence_summary=result.get("confidence", {}),
            has_labels=result.get("has_labels", False),
            classification_metrics=result.get("classification_metrics"),
            distribution_dominance_warning=dominance_warning,
        )

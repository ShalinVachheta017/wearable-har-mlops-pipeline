"""Stage names and stage selection rules for the production pipeline."""

from __future__ import annotations

from typing import List, Optional

from src.entity.artifact_entity import PipelineResult


ALL_STAGES = [
    "ingestion",
    "validation",
    "transformation",
    "inference",
    "evaluation",
    "monitoring",
    "trigger",
    "retraining",
    "registration",
    "baseline_update",
    "calibration",
]

RETRAIN_STAGES = {"retraining", "registration", "baseline_update"}
ADVANCED_STAGES = {"calibration"}


def resolve_run_stages(
    stages: Optional[List[str]],
    *,
    enable_retrain: bool,
    enable_advanced: bool,
    skip_ingestion: bool,
    skip_validation: bool,
    result: PipelineResult,
) -> List[str]:
    """
    Method Name :   resolve_run_stages
    Description :   Build the ordered list of stages for this pipeline run.

    Output      :   Returns the selected stage names in execution order.
    On Failure  :   Logs the error and raises the exception.
    """
    if stages is not None:
        run_stages = [stage for stage in ALL_STAGES if stage in stages]
    else:
        run_stages = [
            stage
            for stage in ALL_STAGES
            if stage not in RETRAIN_STAGES and stage not in ADVANCED_STAGES
        ]
        if enable_retrain:
            run_stages.extend(stage for stage in ALL_STAGES if stage in RETRAIN_STAGES)
        if enable_advanced:
            run_stages.extend(stage for stage in ALL_STAGES if stage in ADVANCED_STAGES)

    if skip_ingestion and "ingestion" in run_stages:
        run_stages.remove("ingestion")
        result.stages_skipped.append("ingestion")
    if skip_validation and "validation" in run_stages:
        run_stages.remove("validation")
        result.stages_skipped.append("validation")
    return run_stages

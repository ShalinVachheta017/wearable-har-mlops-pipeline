# SRC/SCRIPTS Simplification Plan (Analysis-Only)

Guardrails: no deletion/refactor in this phase; runtime-protected files are frozen; uncertain items are manual review.

## Keep As-Is (Protected Runtime/Orchestrator/API)

- scripts/build_training_baseline.py
- scripts/post_inference_monitoring.py
- src/api/app.py
- src/calibration.py
- src/components/baseline_update.py
- src/components/calibration_uncertainty.py
- src/components/curriculum_pseudo_labeling.py
- src/components/data_ingestion.py
- src/components/data_transformation.py
- src/components/data_validation.py
- src/components/model_evaluation.py
- src/components/model_inference.py
- src/components/model_registration.py
- src/components/model_retraining.py
- src/components/post_inference_monitoring.py
- src/components/sensor_placement.py
- src/components/trigger_evaluation.py
- src/components/wasserstein_drift.py
- src/config.py
- src/curriculum_pseudo_labeling.py
- src/data_validator.py
- src/domain_adaptation/adabn.py
- src/domain_adaptation/tent.py
- src/entity/artifact_entity.py
- src/entity/config_entity.py
- src/evaluate_predictions.py
- src/exceptions.py
- src/logger/__init__.py
- src/mlflow_tracking.py
- src/model_rollback.py
- src/pipeline/production_pipeline.py
- src/preprocess_data.py
- src/run_inference.py
- src/sensor_placement.py
- src/train.py
- src/trigger_policy.py
- src/utils/artifacts_manager.py
- src/utils/config_loader.py
- src/utils/label_mapping.py
- src/wasserstein_drift.py

## Wrappers Only (Do Not Remove Now)

- scripts/preprocess.py
- scripts/train.py
- src/components/baseline_update.py
- src/components/post_inference_monitoring.py

## Legacy Candidates (Archive-Later Bias)

- src/pipeline/inference_pipeline.py
- src/core/logger.py
- src/core/exception.py
- src/exception/__init__.py
- src/diagnostic_pipeline_check.py
- scripts/preprocess.py
- scripts/train.py

## Manual Review Queue

- scripts/batch_process_all_datasets.py
- scripts/generate_summary_report.py
- src/active_learning_export.py
- src/core/exception.py
- src/core/logger.py
- src/deployment_manager.py
- src/diagnostic_pipeline_check.py
- src/exception/__init__.py
- src/ood_detection.py
- src/pipeline/inference_pipeline.py
- src/robustness.py
- src/utils/production_optimizations.py
- src/utils/temporal_metrics.py

## Top 10 Simplification Opportunities

1. Consolidate training entrypoints: keep src/train.py as implementation, keep scripts/train.py as thin wrapper or archive later.
2. Consolidate preprocessing entrypoints: keep src/preprocess_data.py as implementation, keep scripts/preprocess.py as thin wrapper or archive later.
3. Decide single orchestrator policy between src/pipeline/production_pipeline.py and src/pipeline/inference_pipeline.py.
4. Normalize exception surface across src/exceptions.py and src/core/exception.py after orchestrator decision.
5. Normalize logger surface across src/logger/__init__.py and src/core/logger.py after orchestrator decision.
6. Evaluate need for src/diagnostic_pipeline_check.py; if only ad-hoc diagnostics, archive later.
7. Evaluate standalone monitoring extensions in src/ood_detection.py; integrate or archive later.
8. Review src/active_learning_export.py lifecycle; if thesis-only utility, archive later with docs pointer.
9. Review src/robustness.py lifecycle; keep for evaluation track or archive later if inactive.
10. Evaluate overlap between scripts/build_normalized_baseline.py and scripts/build_training_baseline.py for a unified baseline CLI.

## Recommended Cleanup Order (Safest First)

1. Freeze protected runtime set and add review guard for these files.
2. Convert confirmed wrappers (scripts/train.py, scripts/preprocess.py) to explicit wrapper status in docs/comments only; no behavior change.
3. Manual-review legacy orchestrator path (src/pipeline/inference_pipeline.py) and dependent core modules before any archive decision.
4. Manual-review standalone analysis utilities (ood_detection, robustness, active_learning_export, diagnostic_pipeline_check).
5. Resolve baseline builder overlap with compatibility checks; then merge later or keep both with clear ownership.
6. Archive-later candidates only after two checks: no runtime import path and no operational dependency in scripts/automation.

## Counts Used In This Plan

- src maintained files: 62
- scripts maintained files: 34
- protected runtime files in scope: 40
- duplication groups listed: 10
- legacy candidates listed: 7

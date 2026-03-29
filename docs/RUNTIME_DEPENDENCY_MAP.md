<!-- markdownlint-disable MD032 MD060 -->

# Runtime Dependency Map (Stages 1-7 First)

Generated: 2026-03-30
Branch context: chore/repo-cleanup

## Scope

This map is limited to git-tracked files under src/ and scripts/ and focuses on real runtime paths for stages 1-7.

Source evidence used:
- run_pipeline.py imports and stage wiring
- src/pipeline/production_pipeline.py stage imports
- src/components stage wrappers and their implementation imports
- scripts imported directly by src components

## 1) Stage 1-7 Call Graph

Stage 0 entrypoint:
- run_pipeline.py -> src/pipeline/production_pipeline.py

Stage 1-7 orchestration chain:
- src/pipeline/production_pipeline.py
  - Stage 1: src/components/data_ingestion.py
  - Stage 2: src/components/data_validation.py
  - Stage 3: src/components/data_transformation.py
  - Stage 4: src/components/model_inference.py
  - Stage 5: src/components/model_evaluation.py
  - Stage 6: src/components/post_inference_monitoring.py
  - Stage 7: src/components/trigger_evaluation.py

Stage wrapper -> implementation dependencies:
- src/components/data_validation.py -> src/data_validator.py
- src/components/data_transformation.py -> src/preprocess_data.py
- src/components/model_inference.py -> src/run_inference.py
- src/components/model_evaluation.py -> src/evaluate_predictions.py
- src/components/post_inference_monitoring.py -> scripts/post_inference_monitoring.py
- src/components/trigger_evaluation.py -> src/trigger_policy.py

Shared runtime infrastructure:
- src/entity/config_entity.py
- src/entity/artifact_entity.py
- src/utils/config_loader.py
- src/utils/artifacts_manager.py
- src/logger/__init__.py
- src/exceptions.py

## 2) Runtime-Critical Files (Do Not Move in Current Cleanup Window)

Highest criticality (direct Stage 1-7 path):
- src/pipeline/production_pipeline.py
- src/components/data_ingestion.py
- src/components/data_validation.py
- src/components/data_transformation.py
- src/components/model_inference.py
- src/components/model_evaluation.py
- src/components/post_inference_monitoring.py
- src/components/trigger_evaluation.py
- src/data_validator.py
- src/preprocess_data.py
- src/run_inference.py
- src/evaluate_predictions.py
- src/trigger_policy.py

High supporting criticality (contract/config/logging):
- src/entity/config_entity.py
- src/entity/artifact_entity.py
- src/utils/config_loader.py
- src/utils/artifacts_manager.py
- src/logger/__init__.py
- src/exceptions.py

## 3) Scripts Imported by src (Hard Runtime Dependency)

Direct imports from src code:
- scripts/post_inference_monitoring.py
  - imported by src/components/post_inference_monitoring.py
  - used in Stage 6 runtime monitoring path
- scripts/build_training_baseline.py
  - imported by src/components/baseline_update.py
  - used in Stage 10 (outside Stage 1-7, but still runtime for retraining cycle)

Implication:
- scripts/post_inference_monitoring.py cannot be archived yet without first migrating implementation into src and preserving interface parity.
- scripts/build_training_baseline.py cannot be archived yet without equivalent migration in baseline update component.

## 4) scripts/ Files by Operational Role

Manual wrappers (overlap with pipeline orchestrator):
- scripts/preprocess.py
- scripts/train.py

Research/experiment runners:
- scripts/run_ablation_experiment.py
- scripts/run_ab_comparison.py
- scripts/threshold_sweep.py
- scripts/windowing_ablation.py
- scripts/trigger_policy_eval.py
- scripts/per_dataset_inference.py
- scripts/generate_thesis_figures.py
- scripts/data_analysis/analyze_datasets.py

Utilities and diagnostics:
- scripts/audit_artifacts.py
- scripts/preprocess_qc.py
- scripts/inference_smoke.py
- scripts/run_tests.py
- scripts/analyze_drift_across_datasets.py
- scripts/build_normalized_baseline.py

Archive placeholder:
- scripts/archive_candidates/.gitkeep

## 5) Files Safe as Later Archive Candidates (Not This Pass)

Likely archive-later after explicit verification:
- src/train.py
- src/sensor_data_pipeline.py
- scripts/preprocess.py
- scripts/train.py
- scripts/build_normalized_baseline.py
- scripts/analyze_drift_across_datasets.py

Reason to defer:
- some are documented in thesis workflows/history,
- some may still be used manually by ad-hoc reproducibility steps,
- wrapper replacement should be explicit and tested.

## 6) Files That Must Remain Until After Thesis Submission

By governance and evidence traceability:
- Stage 1-7 runtime chain listed in Section 2
- scripts/post_inference_monitoring.py (current Stage 6 implementation module)
- scripts/build_training_baseline.py (baseline runtime support)
- experiment runners that produce thesis evidence:
  - scripts/run_ablation_experiment.py
  - scripts/threshold_sweep.py
  - scripts/windowing_ablation.py
  - scripts/trigger_policy_eval.py
  - scripts/generate_thesis_figures.py

## 7) Uncertainty Notes

Items that should be verified before any move/delete:
- External/manual usage frequency of scripts/preprocess.py and scripts/train.py.
- Whether src/train.py is referenced in any thesis reproducibility procedure not captured in tests.
- Whether src/sensor_data_pipeline.py is still referenced by older but still-needed ingestion pathways.

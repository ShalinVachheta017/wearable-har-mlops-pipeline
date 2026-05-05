<!-- markdownlint-disable MD032 MD060 -->

# src/scripts Rigorous Audit

Generated: 2026-03-30
Branch: chore/repo-cleanup

## Scope and Method

Inventory basis:
- git-tracked files under src/ and scripts/
- plus untracked placeholder files currently present under scripts/

Evidence sources:
- run_pipeline.py and src/pipeline/production_pipeline.py stage imports
- component-level wrapper imports
- src <- scripts direct import checks
- tests/ import/name references

Classification categories used:
- canonical runtime logic
- wrapper / entrypoint
- experiment runner
- utility/helper
- duplicate / overlap candidate
- stale / legacy candidate
- unknown / needs manual review

Status fields:
- Stage 1-7 usage: Direct / Indirect / No
- Test usage: Direct / Indirect / No evidence
- Thesis criticality: High / Medium / Low

## Inventory Summary

- src tracked files: 51
- scripts tracked files: 19
- scripts untracked placeholders: 1

## A) src/ File Classification

| File path | Category | Purpose | Stage 1-7 | Used by tests | Thesis criticality | Safe decision |
|---|---|---|---|---|---|---|
| src/README.md | utility/helper | Internal source-package notes | No | No evidence | Low | Keep |
| src/__init__.py | utility/helper | Package marker | Indirect | Indirect | Low | Keep |
| src/active_learning_export.py | utility/helper | Active-learning export/import helper | No | Direct | Medium | Keep |
| src/api/__init__.py | utility/helper | API package marker | No | Indirect | Low | Keep |
| src/api/app.py | wrapper / entrypoint | FastAPI inference/monitoring service path | No | Direct | High | Keep |
| src/calibration.py | canonical runtime logic | Calibration algorithms (stage 11 backend) | No | Direct | Medium | Keep |
| src/components/__init__.py | utility/helper | Components package marker | Indirect | Indirect | Low | Keep |
| src/components/baseline_update.py | wrapper / entrypoint | Stage 10 wrapper | No | Direct | Medium | Keep |
| src/components/calibration_uncertainty.py | wrapper / entrypoint | Stage 11 wrapper | No | No evidence | Medium | Keep |
| src/components/curriculum_pseudo_labeling.py | wrapper / entrypoint | Stage 13 wrapper | No | Indirect | Medium | Keep |
| src/components/data_ingestion.py | wrapper / entrypoint | Stage 1 runtime component | Direct | Indirect | High | Keep |
| src/components/data_transformation.py | wrapper / entrypoint | Stage 3 runtime component | Direct | Indirect | High | Keep |
| src/components/data_validation.py | wrapper / entrypoint | Stage 2 runtime component | Direct | Direct | High | Keep |
| src/components/model_evaluation.py | wrapper / entrypoint | Stage 5 runtime component | Direct | Direct | High | Keep |
| src/components/model_inference.py | wrapper / entrypoint | Stage 4 runtime component | Direct | Indirect | High | Keep |
| src/components/model_registration.py | wrapper / entrypoint | Stage 9 runtime component | No | Direct | Medium | Keep |
| src/components/model_retraining.py | wrapper / entrypoint | Stage 8 runtime component | No | Direct | Medium | Keep |
| src/components/post_inference_monitoring.py | wrapper / entrypoint | Stage 6 runtime component, wraps script implementation | Direct | Direct | High | Keep |
| src/components/sensor_placement.py | wrapper / entrypoint | Stage 14 runtime component | No | Indirect | Medium | Keep |
| src/components/trigger_evaluation.py | wrapper / entrypoint | Stage 7 runtime component | Direct | Direct | High | Keep |
| src/components/wasserstein_drift.py | wrapper / entrypoint | Stage 12 runtime component | No | Indirect | Medium | Keep |
| src/config.py | utility/helper | Shared constants and path defaults | Indirect | Indirect | Medium | Keep |
| src/core/__init__.py | utility/helper | Core package marker | No | No evidence | Low | Keep |
| src/curriculum_pseudo_labeling.py | canonical runtime logic | Stage 13 algorithm implementation | No | Direct | Medium | Keep |
| src/data_validator.py | canonical runtime logic | Validation engine used by Stage 2 component | Direct | Indirect | High | Keep |
| src/deployment_manager.py | wrapper / entrypoint | Deployment CLI/ops manager | No | No evidence | Low | Unknown/manual review |
| src/domain_adaptation/__init__.py | utility/helper | Domain adaptation package marker | No | Indirect | Low | Keep |
| src/domain_adaptation/adabn.py | canonical runtime logic | AdaBN adaptation backend | No | Direct | Medium | Keep |
| src/domain_adaptation/tent.py | canonical runtime logic | TENT adaptation backend | No | No evidence | Medium | Keep |
| src/entity/__init__.py | utility/helper | Entity package marker | Indirect | Indirect | Low | Keep |
| src/entity/artifact_entity.py | canonical runtime logic | Artifact contracts across stages | Indirect | Direct | High | Keep |
| src/entity/config_entity.py | canonical runtime logic | Config contracts across stages | Indirect | Direct | High | Keep |
| src/evaluate_predictions.py | removed | Former Stage 5 backend; logic moved into `src/components/model_evaluation.py` | No | No | Low | Removed |
| src/exceptions.py | canonical runtime logic | Pipeline exception contracts | Indirect | Direct | Medium | Keep |
| src/logger/__init__.py | utility/helper | Centralized logging setup | Indirect | No evidence | Medium | Keep |
| src/mlflow_tracking.py | utility/helper | MLflow tracking wrapper | Indirect | No evidence | Medium | Keep |
| src/model_rollback.py | canonical runtime logic | Model registry/rollback backend | No | Direct | Medium | Keep |
| src/pipeline/__init__.py | utility/helper | Pipeline package marker | Indirect | Indirect | Low | Keep |
| src/pipeline/production_pipeline.py | canonical runtime logic | Main orchestrator for stages 1-14 | Direct | Direct | High | Keep |
| src/preprocess_data.py | canonical runtime logic | Stage 3 preprocessing backend | Direct | No evidence | High | Keep |
| src/run_inference.py | canonical runtime logic | Stage 4 inference backend | Direct | Direct | High | Keep |
| src/sensor_data_pipeline.py | stale / legacy candidate | Historical ingestion path, overlaps Stage 1 stack | No | No evidence | Low-Medium | Archive later candidate |
| src/sensor_placement.py | canonical runtime logic | Stage 14 sensor placement backend | No | Indirect | Medium | Keep |
| src/train.py | stale / legacy candidate | Standalone trainer, overlaps Stage 8 path | No | No evidence | Medium | Archive later candidate |
| src/trigger_policy.py | canonical runtime logic | Stage 7 trigger engine | Direct | Direct | High | Keep |
| src/utils/__init__.py | utility/helper | Utilities package marker | Indirect | Indirect | Low | Keep |
| src/utils/artifacts_manager.py | canonical runtime logic | Artifact persistence layer for orchestrator | Indirect | No evidence | High | Keep |
| src/utils/common.py | utility/helper | General utility helpers | No | No evidence | Low | Unknown/manual review |
| src/utils/config_loader.py | canonical runtime logic | Runtime override loader for monitoring/trigger configs | Indirect | Direct | High | Keep |
| src/utils/label_mapping.py | canonical runtime logic | Shared activity label mapping used by inference/eval/api | Direct | Direct | High | Keep |
| src/utils/main_utils.py | utility/helper | Miscellaneous utility functions | No | No evidence | Low | Unknown/manual review |
| src/utils/temporal_metrics.py | utility/helper | Temporal metrics used by analysis/experiments | No | Direct | Medium | Keep |
| src/wasserstein_drift.py | canonical runtime logic | Stage 12 drift backend | No | Direct | Medium | Keep |

## B) scripts/ File Classification

| File path | Category | Purpose | Stage 1-7 | Used by tests | Thesis criticality | Safe decision |
|---|---|---|---|---|---|---|
| scripts/__init__.py | utility/helper | Scripts package marker | No | No evidence | Low | Keep |
| scripts/analyze_drift_across_datasets.py | experiment runner | Cross-dataset drift analysis utility | No | No evidence | Medium | Keep (archive-later candidate) |
| scripts/audit_artifacts.py | utility/helper | Artifact completeness/consistency checks | No | No evidence | Medium | Keep |
| scripts/build_normalized_baseline.py | duplicate / overlap candidate | Alternative baseline builder overlapping Stage 10 baseline path | No | No evidence | Low-Medium | Archive later candidate |
| scripts/build_training_baseline.py | utility/helper | BaselineBuilder used by Stage 10 component | No | Direct | High | Keep |
| scripts/data_analysis/analyze_datasets.py | experiment runner | Dataset EDA and descriptive analysis | No | No evidence | Medium | Keep |
| scripts/generate_thesis_figures.py | experiment runner | Thesis figure generation | No | No evidence | High | Keep |
| scripts/inference_smoke.py | utility/helper | API inference smoke check | No | No evidence | Medium | Keep |
| scripts/per_dataset_inference.py | experiment runner | Per-dataset inference diagnostics | No | No evidence | Medium | Keep |
| scripts/post_inference_monitoring.py | canonical runtime logic | Stage 6 implementation module imported by src component | Direct | Direct | High | Keep |
| scripts/preprocess.py | wrapper / entrypoint | Legacy standalone stages 1-3 wrapper | No | No evidence | Medium | Convert wrapper later (deprecated) |
| scripts/preprocess_qc.py | utility/helper | Preprocessing QC diagnostics | No | No evidence | Low-Medium | Keep |
| scripts/run_ab_comparison.py | experiment runner | A/B comparison experiments | No | No evidence | Medium | Keep |
| scripts/run_ablation_experiment.py | experiment runner | Ablation orchestration used for thesis evidence | No | No evidence | High | Keep |
| scripts/run_tests.py | utility/helper | Local test-run helper | No | No evidence | Low | Keep (archive-later candidate) |
| scripts/threshold_sweep.py | experiment runner | Threshold sweep/calibration experiments | No | No evidence | High | Keep |
| scripts/train.py | wrapper / entrypoint | Legacy standalone stages 8-10 wrapper | No | No evidence | Medium | Convert wrapper later (deprecated) |
| scripts/trigger_policy_eval.py | experiment runner | Offline trigger-policy evaluation | No | No evidence | High | Keep |
| scripts/windowing_ablation.py | experiment runner | Window-size/overlap ablation | No | No evidence | High | Keep |
| scripts/archive_candidates/.gitkeep (untracked) | utility/helper | Placeholder for future archive moves | No | No evidence | Low | Keep placeholder only |

## C) Direct src <- scripts Import Dependencies

Runtime-impacting script dependencies currently imported by src:
- src/components/post_inference_monitoring.py -> scripts/post_inference_monitoring.py
- src/components/baseline_update.py -> scripts/build_training_baseline.py

These two script modules are not safe to archive or remove in current state.

## D) High-Risk Cleanup Areas to Postpone

- Any move/refactor touching Stage 1-7 files listed as Direct in Section A.
- Moving scripts/post_inference_monitoring.py before implementation migration and parity tests.
- Wrapper deletion for scripts/preprocess.py and scripts/train.py without compatibility communication and replacement mapping.

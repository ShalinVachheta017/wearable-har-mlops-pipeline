# Python File Importance And Cleanup Audit (2026-04-17)

## Scope

This audit classifies Python files as:

- Important (keep)
- Safe to archive now
- Safe to delete after migration window

The classification is based on static import reachability from these entrypoints:

- run_pipeline.py
- src/api/app.py
- src/cli.py
- src/deployment_manager.py

## Key Runtime Facts

- Stage 12, 13, 14 are removed from runtime orchestration.
- Current runtime stage graph is 11 stages (1 to 11).
- Prometheus is still active in API runtime via src/api/app.py.
- Grafana runtime config is not present in current active compose/config set.
- Runtime stage execution is self-contained under src/; stage logic no longer imports scripts/ modules.

---

## Important Files (Keep)

These are actively used by current runtime entrypoints and should be kept.

### Pipeline Runtime Core

- run_pipeline.py
  - Why important: Primary orchestrator entrypoint for the thesis pipeline.
- src/pipeline/production_pipeline.py
  - Why important: Executes stage scheduling, dispatch, and lifecycle.
- src/components/data_ingestion.py
- src/components/data_validation.py
- src/components/data_transformation.py
- src/components/model_inference.py
- src/components/model_evaluation.py
- src/components/post_inference_monitoring.py
- src/components/trigger_evaluation.py
- src/components/model_retraining.py
- src/components/model_registration.py
- src/components/baseline_update.py
- src/components/calibration_uncertainty.py
  - Why important: These are the active stage implementations for stages 1 to 11.

### Pipeline Support Modules

- src/config.py
- src/entity/config_entity.py
- src/entity/artifact_entity.py
- src/logger/__init__.py
- src/utils/common.py
- src/utils/config_loader.py
- src/utils/artifacts_manager.py
- src/utils/label_mapping.py
- src/preprocess_data.py
- src/run_inference.py
- src/evaluate_predictions.py
- src/train.py
- src/trigger_policy.py
- src/calibration.py
- src/data_validator.py
- src/mlflow_tracking.py
- src/model_rollback.py
- src/domain_adaptation/adabn.py
- src/domain_adaptation/tent.py
- src/exceptions.py
  - Why important: Imported by the current pipeline path and required for successful execution.

### Script Wrappers Kept For CLI Compatibility

- scripts/post_inference_monitoring.py
  - Why important: Thin CLI entrypoint that imports canonical src.monitoring.post_inference_monitor.PostInferenceMonitor.
- scripts/build_training_baseline.py
  - Why important: Thin CLI entrypoint that imports canonical src.monitoring.baseline_builder.BaselineBuilder.

### Important Outside run_pipeline (Still Keep)

- src/api/app.py
  - Why important: FastAPI serving entrypoint; includes monitoring and Prometheus metrics endpoint.
- src/cli.py
  - Why important: Installed CLI entrypoint (har-pipeline).
- src/deployment_manager.py
  - Why important: Deployment utility entrypoint (if deployment workflows are used).

---

## Safe To Archive Now (Not Used By Current Pipeline Runtime)

These files are not reachable from the active pipeline entrypoint and are good archive candidates.

### src Candidates

| File | Why safe to archive now |
| --- | --- |
| src/active_learning_export.py | Standalone active-learning utility, not imported by pipeline/api/cli/deployment entrypoints. |
| src/sensor_data_pipeline.py | Legacy ingestion stack; functionality is already in src/components/data_ingestion.py. |
| src/utils/main_utils.py | Convenience helper module, not used by current runtime path. |
| src/utils/temporal_metrics.py | Used only by experiment scripts, not current production pipeline runtime. |

### scripts Candidates

| File | Why safe to archive now |
| --- | --- |
| scripts/analyze_drift_across_datasets.py | Standalone analysis script, not imported by runtime entrypoints. |
| scripts/audit_artifacts.py | Repository audit helper only, not runtime pipeline logic. |
| scripts/batch_process_all_datasets.py | Batch utility script, not part of run_pipeline path. |
| scripts/build_normalized_baseline.py | Standalone baseline generator; not used after baseline builder integration path. |
| scripts/data_analysis/analyze_datasets.py | Exploratory analysis script only. |
| scripts/generate_synthetic_data.py | Synthetic data helper, not part of runtime production execution. |
| scripts/generate_thesis_figures.py | Thesis figure generation utility only. |
| scripts/inference_smoke.py | Manual smoke test script only. |
| scripts/mlops_audit.py | Static repo audit script, not runtime pipeline logic. |
| scripts/per_dataset_inference.py | Ad-hoc inference helper, not core runtime path. |
| scripts/preprocess_qc.py | QC experiment utility, not active runtime entrypoint. |
| scripts/run_ab_comparison.py | Ablation/experiment utility. |
| scripts/run_ablation_experiment.py | Ablation/experiment utility. |
| scripts/run_tests.py | Test launcher helper only. |
| scripts/threshold_sweep.py | Experiment utility; references temporal metrics helpers. |
| scripts/trigger_policy_eval.py | Manual policy evaluation helper, not active orchestrator path. |
| scripts/windowing_ablation.py | Experiment utility. |

---

## Safe To Delete After Migration Window

| File | Why delete can be safe |
| --- | --- |
| scripts/preprocess.py | Already converted to hard-fail deprecated wrapper; no runtime function except migration notice. |
| scripts/train.py | Already converted to hard-fail deprecated wrapper; no runtime function except migration notice. |

Recommended policy:

- Keep these for one transition cycle if users still call old commands.
- Then remove permanently once operational migration is confirmed.

---

## Duplicate/Overlap Cleanup Targets (Status)

### Monitoring Logic Split Between src And scripts

- Status: Completed.
- Current: src/components/post_inference_monitoring.py imports src.monitoring.post_inference_monitor.

### Baseline Builder Split Between src And scripts

- Status: Completed.
- Current: src/components/baseline_update.py imports src.monitoring.baseline_builder.

### Script Wrappers

- Status: Converted to thin wrappers.
- Current: scripts/post_inference_monitoring.py and scripts/build_training_baseline.py are CLI shims only.

### Legacy Ingestion Overlap

- Current: src/sensor_data_pipeline.py overlaps with src/components/data_ingestion.py.
- Action: Archive or delete src/sensor_data_pipeline.py after confirming no manual users depend on it.

---

## Stale Reference Fixes (Not Delete, But Correct)

- Status: Completed.
- src/deployment_manager.py stale missing-file references were removed.
- Current deployment packaging copies src/monitoring/ into the image build context.

---

## Notes And Limits

- This audit uses static import reachability and does not detect manual shell usage.
- Before deletion, check CI jobs, notebooks, and personal scripts that may call utilities directly.
- Recommended flow: archive first, run smoke tests, then delete.

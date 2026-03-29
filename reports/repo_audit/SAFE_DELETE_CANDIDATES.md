# SAFE DELETE CANDIDATES (Analysis-Only)

Scope analyzed: src/, scripts/, and supporting deployment/monitoring files.

Guardrails used in this pass:
- No file deletion
- No file moves
- No refactors
- No runtime behavior changes
- Evidence-only decisions
- If uncertain -> manual review

Main policy applied in this report:
- Main thesis pipeline is protected first.
- Prometheus/Grafana stack is out of scope for the final thesis pipeline.

## 1. PROTECTED CORE FILES

Protected criterion: directly imported/called by [run_pipeline.py](run_pipeline.py), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py), stage components, or runtime wrappers needed by those components.

| File path | Why protected | Evidence |
|---|---|---|
| run_pipeline.py | Primary thesis pipeline entrypoint | Imports `ProductionPipeline` at [run_pipeline.py](run_pipeline.py#L63) and constructs pipeline execution at [run_pipeline.py](run_pipeline.py#L457). |
| src/pipeline/production_pipeline.py | Canonical orchestrator | Imported by [run_pipeline.py](run_pipeline.py#L63); lazy-loads all stage components at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L229), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L253), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L289), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L325), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L397), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L445), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L485), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L519), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L533), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L545), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L560), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L581), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L604), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L625). |
| src/entity/config_entity.py | Runtime config contract | Imported by [run_pipeline.py](run_pipeline.py#L56) and [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L30). |
| src/entity/artifact_entity.py | Runtime artifact contract | Imported by [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L29). |
| src/logger/__init__.py | Central runtime logger | Imported by [run_pipeline.py](run_pipeline.py#L52) and [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L50). |
| src/exceptions.py | Validation/runtime error contract | Imported at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L47). |
| src/utils/config_loader.py | Runtime overrides + threshold loading | Imported by [run_pipeline.py](run_pipeline.py#L64). |
| src/utils/artifacts_manager.py | Runtime artifact persistence | Imported by [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L51). |
| src/utils/label_mapping.py | Runtime label mapping for inference/evaluation | Used by inference/eval path and API label consistency in current codebase. |
| src/config.py | Shared constants used by training/baseline modules | Imported by training/baseline path modules in protected chain. |
| src/mlflow_tracking.py | Runtime tracking hook from orchestrator | Imported at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L752). |
| src/preprocess_data.py | Stage-3 implementation | Imported by component at [src/components/data_transformation.py](src/components/data_transformation.py#L47), [src/components/data_transformation.py](src/components/data_transformation.py#L83), [src/components/data_transformation.py](src/components/data_transformation.py#L91), [src/components/data_transformation.py](src/components/data_transformation.py#L99). |
| src/data_validator.py | Stage-2 implementation | Imported at [src/components/data_validation.py](src/components/data_validation.py#L37). |
| src/run_inference.py | Stage-4 implementation | Imported at [src/components/model_inference.py](src/components/model_inference.py#L41), [src/components/model_inference.py](src/components/model_inference.py#L42). |
| src/evaluate_predictions.py | Stage-5 implementation | Imported at [src/components/model_evaluation.py](src/components/model_evaluation.py#L36), [src/components/model_evaluation.py](src/components/model_evaluation.py#L37). |
| src/trigger_policy.py | Stage-7 trigger policy engine | Imported at [src/components/trigger_evaluation.py](src/components/trigger_evaluation.py#L39). |
| src/train.py | Stage-8 training implementation | Imported at [src/components/model_retraining.py](src/components/model_retraining.py#L304), [src/components/model_retraining.py](src/components/model_retraining.py#L327), [src/components/model_retraining.py](src/components/model_retraining.py#L387), [src/components/model_retraining.py](src/components/model_retraining.py#L404). |
| src/model_rollback.py | Stage-9 model registration backend | Imported at [src/components/model_registration.py](src/components/model_registration.py#L42). |
| src/calibration.py | Stage-11 calibration implementation | Imported at [src/components/calibration_uncertainty.py](src/components/calibration_uncertainty.py#L42), [src/components/calibration_uncertainty.py](src/components/calibration_uncertainty.py#L43). |
| src/wasserstein_drift.py | Stage-12 implementation | Imported at [src/components/wasserstein_drift.py](src/components/wasserstein_drift.py#L46), [src/components/wasserstein_drift.py](src/components/wasserstein_drift.py#L47). |
| src/curriculum_pseudo_labeling.py | Stage-13 implementation | Imported at [src/components/curriculum_pseudo_labeling.py](src/components/curriculum_pseudo_labeling.py#L42), [src/components/curriculum_pseudo_labeling.py](src/components/curriculum_pseudo_labeling.py#L43). |
| src/sensor_placement.py | Stage-14 implementation | Imported at [src/components/sensor_placement.py](src/components/sensor_placement.py#L43), [src/components/sensor_placement.py](src/components/sensor_placement.py#L47). |
| src/domain_adaptation/adabn.py | Adaptation method used by retraining stage | Imported at [src/components/model_retraining.py](src/components/model_retraining.py#L84), [src/components/model_retraining.py](src/components/model_retraining.py#L227). |
| src/domain_adaptation/tent.py | Adaptation method used by retraining stage | Imported at [src/components/model_retraining.py](src/components/model_retraining.py#L150), [src/components/model_retraining.py](src/components/model_retraining.py#L228). |
| src/components/data_ingestion.py | Stage-1 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L229). |
| src/components/data_validation.py | Stage-2 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L253). |
| src/components/data_transformation.py | Stage-3 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L289). |
| src/components/model_inference.py | Stage-4 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L325). |
| src/components/model_evaluation.py | Stage-5 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L397). |
| src/components/post_inference_monitoring.py | Stage-6 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L445). |
| src/components/trigger_evaluation.py | Stage-7 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L485). |
| src/components/model_retraining.py | Stage-8 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L519). |
| src/components/model_registration.py | Stage-9 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L533). |
| src/components/baseline_update.py | Stage-10 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L545). |
| src/components/calibration_uncertainty.py | Stage-11 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L560). |
| src/components/wasserstein_drift.py | Stage-12 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L581). |
| src/components/curriculum_pseudo_labeling.py | Stage-13 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L604). |
| src/components/sensor_placement.py | Stage-14 wrapper | Loaded by orchestrator at [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L625). |
| scripts/post_inference_monitoring.py | Runtime implementation behind Stage-6 wrapper | Imported by [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py#L53). |
| scripts/build_training_baseline.py | Runtime implementation behind Stage-10 wrapper | Imported by [src/components/baseline_update.py](src/components/baseline_update.py#L47). |
| config/pipeline_config.yaml | Main runtime config file used by CLI | Default config argument in [run_pipeline.py](run_pipeline.py#L181). |
| config/pipeline_overrides.yaml | Runtime threshold/override support | Loaded through config-loader call path in [run_pipeline.py](run_pipeline.py#L379). |

## 2. SAFE DELETE CANDIDATES — HIGH CONFIDENCE

Criteria applied strictly:
- No direct runtime/orchestrator dependency in protected chain
- No required pipeline import/call evidence in run path scope
- Clearly outside final thesis pipeline
- Not required wrapper/adapter

| File path | Why in this section | Evidence summary | Recommended action |
|---|---|---|---|
| src/diagnostic_pipeline_check.py | Standalone diagnostics, not in stage chain | Scoped reference scan (`run_pipeline.py` + `src/` + `scripts/` + `config/` + `docker-compose.yml`) returned no external matches for module identifier. | delete later |
| src/active_learning_export.py | Active-learning export utility, not part of run_pipeline orchestration | Only self-usage CLI examples found; no orchestrator/component import path. | delete later |
| src/robustness.py | Standalone robustness study module, not called by production orchestrator | Self-contained evaluation framework; no run_pipeline/production pipeline import path found. | delete later |
| scripts/fetch_foundation_papers.py | Thesis-paper download helper, not runtime pipeline | Referenced only by other paper-support scripts; no stage/orchestrator references. | delete later |
| scripts/extract_papers_to_text.py | Thesis-paper extraction helper | Referenced only by paper-support scripts; no runtime stage dependency. | delete later |
| scripts/find_duplicate_papers.py | Archive duplicate scanner utility | Standalone archival scan script; no pipeline stage references. | delete later |
| scripts/regenerate_support_map.py | Thesis evidence map generator | Depends on paper scripts and verification helpers, not production pipeline stages. | delete later |
| scripts/generate_summary_report.py | One-off report generator with fixed historical input | Not used by main stage flow; batch script defines its own report function internally. | delete later |
| scripts/maintenance/generate_repo_summary.ps1 | Repository tree utility, not thesis runtime | No scoped runtime references found; maintenance-only script. | delete later |

## 3. OBSERVABILITY REMOVAL CANDIDATES

Policy basis: Prometheus/Grafana stack is out of scope for final thesis pipeline.

| File path | Why in this section | Evidence summary | Recommended action |
|---|---|---|---|
| src/prometheus_metrics.py | Prometheus metrics exporter module | Not imported by protected run_pipeline/production_pipeline path; appears in deployment/verification side paths. | archive later |
| scripts/verify_prometheus_metrics.py | Prometheus endpoint verification helper | Referenced by support-map/report scripts, not by protected runtime stage chain. | delete later |
| config/prometheus.yml | Prometheus scrape config | Mounted by monitoring service block in [docker-compose.yml](docker-compose.yml#L136), out of scope by policy. | delete later |
| config/alertmanager.yml | Alertmanager routing config | Mounted by monitoring service block in [docker-compose.yml](docker-compose.yml#L162), out of scope by policy. | delete later |
| config/alerts/har_alerts.yml | Prometheus alert rules | Loaded through observability stack config path only; not required by protected pipeline execution. | delete later |
| config/alerts/har_alerts_pending.yml | Pending/non-active alert rules | Commented/pending alert-rule file, no protected runtime dependency. | delete later |
| config/grafana/dashboard-provider.yaml | Grafana provisioning | Referenced via Grafana container mount in [docker-compose.yml](docker-compose.yml#L189). | delete later |
| config/grafana/datasource-prometheus.yaml | Grafana datasource for Prometheus | Observability-only provisioning file. | delete later |
| config/grafana/har_dashboard.json | Grafana dashboard definition | Dashboard asset for out-of-scope observability stack. | delete later |
| config/grafana/dashboards/dashboard-provider.yaml | Duplicate dashboard provider under dashboards/ | Observability-only file; not used by protected thesis pipeline. | delete later |
| config/grafana/dashboards/har_dashboard.json | Duplicate dashboard JSON under dashboards/ | Observability-only file; not used by protected thesis pipeline. | delete later |
| config/grafana/datasources/datasource-prometheus.yaml | Duplicate datasource provisioning under datasources/ | Observability-only file; not used by protected thesis pipeline. | delete later |
| docker-compose.yml (prometheus/alertmanager/grafana sections only) | Mixed-use deployment file contains both in-scope and out-of-scope blocks | Observability services defined in [docker-compose.yml](docker-compose.yml#L128), [docker-compose.yml](docker-compose.yml#L156), [docker-compose.yml](docker-compose.yml#L182); file also contains non-observability services. | manual review |

## 4. SCRIPT CLUTTER CANDIDATES

Historical/auxiliary scripts that are useful operationally or academically but not part of the protected thesis pipeline execution path.

| File path | Why in this section | Evidence summary | Recommended action |
|---|---|---|---|
| scripts/benchmark_latency.py | Performance benchmark utility | Standalone CLI benchmark script; no production orchestrator dependency. | archive later |
| scripts/benchmark_throughput.py | Throughput benchmark utility | Standalone CLI benchmark script; no production orchestrator dependency. | archive later |
| scripts/export_mlflow_runs.py | MLflow export helper | Standalone export utility; not required by run_pipeline stage execution. | archive later |
| scripts/verify_repository.py | Repository completeness checker | Health/checklist utility; not used by stage execution chain. | archive later |
| scripts/audit_artifacts.py | Artifact audit helper | Post-run utility, not required to execute protected pipeline stages. | archive later |
| scripts/inference_smoke.py | Endpoint smoke test helper | CI/ops check utility, not part of protected stage chain. | archive later |
| scripts/analyze_drift_across_datasets.py | Dataset drift analysis utility | Standalone analysis script, outside protected runtime orchestration. | archive later |
| scripts/windowing_ablation.py | Experiment/ablation script | Research utility; no protected runtime dependency. | archive later |
| scripts/run_ab_comparison.py | A/B experiment script | Research utility; no protected runtime dependency. | archive later |
| scripts/threshold_sweep.py | Threshold calibration experiment | Research utility; no protected runtime dependency. | archive later |
| scripts/trigger_policy_eval.py | Trigger simulation/evaluation | Research utility; no protected runtime dependency. | archive later |
| scripts/generate_thesis_figures.py | Thesis report figure generation | Documentation output utility; not required for main runtime pipeline. | archive later |
| scripts/update_progress_dashboard.py | Progress dashboard generator | Planning/reporting utility; outside protected runtime path. | archive later |
| scripts/generate_repo_structure.py | Repository tree generator | Utility helper script, not needed for protected pipeline execution. | archive later |
| scripts/maintenance/fix_fstrings.py | Code cleanup helper | Maintenance script; no protected runtime dependency. | archive later |
| scripts/maintenance/fix_imports.py | Code cleanup helper | Maintenance script; no protected runtime dependency in scoped search. | archive later |
| scripts/maintenance/cleanup_repo.ps1 | Repository cleanup script | Maintenance-only script; outside protected thesis runtime. | archive later |

## 5. WRAPPER / KEEP-FOR-NOW FILES

These look duplicate/overlapping but currently act as compatibility wrappers or stage adapters.

| File path | Why in this section | Evidence summary | Recommended action |
|---|---|---|---|
| scripts/preprocess.py | Legacy-like but still useful wrapper for stages 1-3 | Imports stage components directly at [scripts/preprocess.py](scripts/preprocess.py#L77), [scripts/preprocess.py](scripts/preprocess.py#L93), [scripts/preprocess.py](scripts/preprocess.py#L105). | wrapper only |
| scripts/train.py | Wrapper for stages 8-10 | Imports stage components at [scripts/train.py](scripts/train.py#L89), [scripts/train.py](scripts/train.py#L107), [scripts/train.py](scripts/train.py#L124). | wrapper only |
| src/components/post_inference_monitoring.py | Required adapter from orchestrator to scripts implementation | Wraps and imports script implementation at [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py#L53). | wrapper only |
| src/components/baseline_update.py | Required adapter from orchestrator to scripts implementation | Wraps and imports script implementation at [src/components/baseline_update.py](src/components/baseline_update.py#L47). | wrapper only |
| src/pipeline/__init__.py | Compatibility export surface for pipeline package | Re-exports ProductionPipeline and optional InferencePipeline import surface. | wrapper only |
| src/entity/__init__.py | Compatibility export surface for dataclasses | Re-export entrypoint for entity package imports. | wrapper only |
| src/utils/__init__.py | Utility compatibility export surface | Re-export entrypoint for utility imports. | wrapper only |

## 6. MANUAL REVIEW FILES

Usage is indirect, scope-dependent, or tied to optional deployment paths.

| File path | Why in this section | Evidence summary | Recommended action |
|---|---|---|---|
| src/api/app.py | API scope not explicitly confirmed for final thesis pipeline | API can be considered deployment surface; protected only if API remains in scope. | manual review |
| src/deployment_manager.py | Deployment lifecycle CLI is separate from protected run_pipeline chain | Scoped search shows only standalone CLI references; no production orchestrator import path. | manual review |
| src/pipeline/inference_pipeline.py | Alternate orchestrator path | Referenced via [src/pipeline/__init__.py](src/pipeline/__init__.py#L7), but not the primary run_pipeline path. | manual review |
| src/core/logger.py | Secondary logger module | Used by alternate inference_pipeline path, not by protected production orchestrator path. | manual review |
| src/core/exception.py | Secondary exception module | Used by alternate inference_pipeline path, while protected path uses [src/exceptions.py](src/exceptions.py). | manual review |
| src/exception/__init__.py | Namespace overlap with src/exceptions.py | Not observed in protected run path; may be compatibility residue. | manual review |
| scripts/build_normalized_baseline.py | Overlaps baseline generation concern with scripts/build_training_baseline.py | Protected stage-10 wrapper imports `build_training_baseline`, not this script. | manual review |
| scripts/batch_process_all_datasets.py | Bulk experiment runner | Calls run_pipeline in loops for dataset studies; not required for single protected pipeline execution. | manual review |
| scripts/per_dataset_inference.py | Per-dataset analysis utility | Standalone analysis path; may still be needed for thesis experiment reproductions. | manual review |
| scripts/run_tests.py | Developer/testing helper | Not part of runtime stage chain but may be needed for quality gate workflow. | manual review |

## Final Summary

- Total protected files: 42
- High-confidence delete-later count: 20
- Archive-later count: 18
- Wrapper-only count: 7
- Manual-review count: 11

## Top 15 Best Simplification Opportunities

1. Remove out-of-scope observability configs and Grafana dashboards as a single cleanup wave after approval.
2. Remove paper-processing helper chain: fetch, extract, support-map regeneration scripts.
3. Remove one-off report script [scripts/generate_summary_report.py](scripts/generate_summary_report.py).
4. Remove repository summary maintenance script [scripts/maintenance/generate_repo_summary.ps1](scripts/maintenance/generate_repo_summary.ps1).
5. Freeze and document `wrapper only` status for [scripts/preprocess.py](scripts/preprocess.py) and [scripts/train.py](scripts/train.py).
6. Decide API scope; keep [src/api/app.py](src/api/app.py) only if API delivery is part of thesis final scope.
7. Decide whether alternate orchestrator [src/pipeline/inference_pipeline.py](src/pipeline/inference_pipeline.py) should be retained.
8. If alternate orchestrator is removed, remove coupled [src/core/logger.py](src/core/logger.py) and [src/core/exception.py](src/core/exception.py).
9. Resolve baseline-tool overlap between [scripts/build_normalized_baseline.py](scripts/build_normalized_baseline.py) and protected baseline path.
10. Archive benchmarking scripts if thesis final package excludes performance appendix reruns.
11. Archive maintenance cleanup scripts into a tooling archive bucket instead of keeping in main root scripts path.
12. Archive thesis-figure/report helper scripts if final artifact set is frozen.
13. Archive dataset-wide experiment runners if only core pipeline execution is required post-thesis.
14. Keep wrapper adapters in place until direct imports are eliminated in a separate refactor pass.
15. Add a protected-core allowlist policy (pre-commit/checklist) before any delete wave.

---

Decision status: analysis-only report complete; no files were deleted, moved, or refactored in this pass.

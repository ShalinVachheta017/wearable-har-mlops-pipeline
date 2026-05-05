<!-- markdownlint-disable MD032 MD060 -->

# src vs scripts Overlap Matrix

Generated: 2026-04-17

## Method

Overlap cases were identified by comparing:
- runtime stage wiring in src/pipeline/production_pipeline.py
- wrapper/component relationships in src/components/*
- script entrypoints in scripts/*
- constructor compatibility evidence for wrapper scripts

## Overlap Cases

| File A | File B | Overlap Type | Canonical Owner | Risk if merged/removed now | Evidence | Recommendation |
|---|---|---|---|---|---|---|
| scripts/preprocess.py | run_pipeline.py + src/pipeline/production_pipeline.py + src/components/data_ingestion.py + src/components/data_validation.py + src/components/data_transformation.py | Legacy orchestration wrapper for stages 1-3 | src + run_pipeline | High (wrapper currently uses older constructor style) | scripts/preprocess.py instantiates DataIngestion/DataValidation/DataTransformation directly; component constructors now require pipeline_config and artifacts | Keep file for compatibility, mark deprecated, migrate later to thin CLI wrapper around run_pipeline |
| scripts/train.py | run_pipeline.py --retrain + src/pipeline/production_pipeline.py + src/components/model_retraining.py + src/components/model_registration.py + src/components/baseline_update.py | Legacy orchestration wrapper for stages 8-10 | src + run_pipeline | High (constructor drift risk) | scripts/train.py directly instantiates Stage 8-10 components with old signature style | Keep file for compatibility, mark deprecated, convert to thin wrapper later |
| src/monitoring/post_inference_monitor.py | scripts/post_inference_monitoring.py | Canonical module + thin CLI wrapper (Stage 6) | src/monitoring/post_inference_monitor.py | Low (wrapper removable after migration window) | Stage 6 component imports src.monitoring.post_inference_monitor directly; script imports same canonical class | Keep wrapper for CLI compatibility, then archive/delete when wrapper usage is retired |
| src/monitoring/baseline_builder.py | scripts/build_training_baseline.py | Canonical module + thin CLI wrapper (Stage 10) | src/monitoring/baseline_builder.py | Low (wrapper removable after migration window) | Stage 10 component imports src.monitoring.baseline_builder directly; script imports same canonical class | Keep wrapper for CLI compatibility, then archive/delete when wrapper usage is retired |
| src/train.py | src/components/model_retraining.py | Parallel training paths (standalone trainer vs stage component) | src/components/model_retraining.py for pipeline runtime | Medium (potential historical usage) | production pipeline uses component path; src/train.py is standalone path | Treat src/train.py as legacy candidate; archive only after workflow confirmation |
| src/sensor_data_pipeline.py | src/components/data_ingestion.py + src/preprocess_data.py | Historical ingestion overlap | src/components/data_ingestion.py + src/preprocess_data.py | Medium (unknown legacy/manual usage) | data_ingestion docstring references merged logic; sensor_data_pipeline not in stage imports | Do not delete now; mark as legacy candidate after manual verification |
| src/run_inference.py | scripts/per_dataset_inference.py | Inference capability overlap (production inference vs dataset analysis runner) | src/run_inference.py for runtime; script for research utility | Low-Medium | component model_inference imports src/run_inference.py; script appears standalone analysis | Keep both, clearly label script as analysis-only |
| src/trigger_policy.py | scripts/trigger_policy_eval.py | Runtime trigger engine vs offline policy evaluation runner | src/trigger_policy.py for runtime | Low | Stage 7 uses src/trigger_policy.py; script is evaluation tool | Keep script as research runner, not runtime |
| src/wasserstein_drift.py | scripts/analyze_drift_across_datasets.py | Drift analytics overlap (runtime component backend vs ad-hoc analysis) | src/wasserstein_drift.py | Low-Medium | Stage 12 component wraps src/wasserstein_drift.py; script is standalone analysis | Keep script as utility, potential archive later |
| scripts/build_normalized_baseline.py | scripts/build_training_baseline.py + src/components/baseline_update.py | Baseline generation overlap | scripts/build_training_baseline.py + src/components/baseline_update.py | Medium | normalized baseline functionality overlaps broader baseline builder path | Mark build_normalized_baseline as archive-later candidate |

## Wrapper Drift Evidence (Constructor Mismatch Risk)

Wrapper call sites:
- scripts/preprocess.py: DataIngestion(config=...), DataValidation(config=..., prev_artifact=...), DataTransformation(config=..., prev_artifact=...)
- scripts/train.py: ModelRetraining(config=...), ModelRegistration(config=..., prev_artifact=...), BaselineUpdate(config=...)

Current component constructor expectations include pipeline_config and typed artifacts:
- src/components/data_ingestion.py
- src/components/data_validation.py
- src/components/data_transformation.py
- src/components/model_retraining.py
- src/components/model_registration.py
- src/components/baseline_update.py

Conclusion:
- wrappers are high-risk for silent drift and should be treated as compatibility entrypoints, not canonical orchestration.

## Canonical Ownership Decision

For cleanup and defense narrative:
- Canonical production system: src/ + run_pipeline.py
- scripts/: wrappers, experiments, and utilities only
- No src runtime dependency on scripts for Stage 6/10 logic; scripts are now compatibility wrappers

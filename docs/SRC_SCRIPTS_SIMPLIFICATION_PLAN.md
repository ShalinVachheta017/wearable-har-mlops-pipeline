<!-- markdownlint-disable MD032 MD060 -->

# src/scripts Simplification Plan (Conservative)

Generated: 2026-03-30

## Objective

Reduce ambiguity between src/ and scripts/ while preserving:
- stages 1-7 runtime stability,
- thesis reproducibility,
- experiment traceability,
- backward compatibility where practical.

## Target Architecture

- src/: canonical production/runtime logic and component orchestration.
- scripts/: thin wrappers, experiment runners, diagnostics, and utilities.
- archive_candidates/: staging locations only, no blind moves.

## Keep/Convert/Archive Matrix

### Keep as canonical runtime

- run_pipeline.py
- src/pipeline/production_pipeline.py
- src/components/*
- src/entity/config_entity.py
- src/entity/artifact_entity.py
- src/trigger_policy.py
- src/preprocess_data.py
- src/run_inference.py
- src/evaluate_predictions.py
- src/data_validator.py
- src/utils/config_loader.py
- src/utils/artifacts_manager.py

### Keep but classify as wrapper implementation dependency

- scripts/post_inference_monitoring.py
- scripts/build_training_baseline.py

### Convert to thin wrappers (not now, after explicit verification)

- scripts/preprocess.py
  - target behavior: call run_pipeline.py with stages ingestion validation transformation
- scripts/train.py
  - target behavior: call run_pipeline.py with retraining flow options

### Archive later candidates (post-thesis or after compatibility checks)

- src/train.py
- src/sensor_data_pipeline.py
- scripts/build_normalized_baseline.py
- scripts/analyze_drift_across_datasets.py
- scripts/run_tests.py (if superseded by CI docs and pytest commands)

### Keep as thesis/experiment tooling

- scripts/run_ablation_experiment.py
- scripts/run_ab_comparison.py
- scripts/threshold_sweep.py
- scripts/windowing_ablation.py
- scripts/trigger_policy_eval.py
- scripts/generate_thesis_figures.py
- scripts/per_dataset_inference.py
- scripts/data_analysis/analyze_datasets.py

## Wave Plan

### Wave 1 (Zero-risk cleanup)

- Add explicit deprecation headers to stale wrappers:
  - scripts/preprocess.py
  - scripts/train.py
- Add docs index links for new audit artifacts.
- Keep archive placeholders only:
  - scripts/archive_candidates/
  - internal/archive_candidates/
- Do not move or delete runtime files.

### Wave 2 (Safe wrapper consolidation)

- Refactor scripts/preprocess.py into a thin run_pipeline.py delegator.
- Refactor scripts/train.py into a thin run_pipeline.py delegator.
- Preserve CLI flags where possible, map legacy flags to current equivalents.
- Validate with targeted stage tests and one stage-chain smoke run.

### Wave 3 (Archive old/stale scripts)

- Archive candidates with low observed usage and clear replacements.
- Maintain a move ledger doc with old -> new path mapping.
- Keep fallback stubs for one release cycle if needed.

### Wave 4 (Post-thesis structural refactor, optional)

- Migrate script implementation modules currently imported by src components into src namespaces:
  - scripts/post_inference_monitoring.py -> src/monitoring/...
  - scripts/build_training_baseline.py -> src/baseline/...
- Add compatibility imports/shims to avoid breaking existing tooling.

## Guardrails

Do not do in cleanup waves until explicitly validated:
- any behavior change in stages 1-7 thresholds, gating, or artifact contracts,
- deletion of files referenced by thesis experiments/evidence,
- migration of Stage 6 or Stage 10 script dependencies without parity tests.

## Validation Gates for Future Waves

Required before each move/merge/archive action:
1. Usage verification across src/, scripts/, docs/, tests/.
2. Targeted tests for affected stage(s).
3. Full pytest pass in thesis environment.
4. At least one lightweight pipeline run for affected path.
5. Documentation update in overlap/dependency map.

## This Iteration (Applied Low-Risk Changes)

- P0 fixes already implemented and validated:
  - Stage 6 threshold pass-through consistency.
  - Trigger cooldown precedence over same-cycle escalation.
- Added/refreshed architecture docs (audit, overlap, dependency, plan).
- Added deprecation notices only (no runtime file moves/deletions).

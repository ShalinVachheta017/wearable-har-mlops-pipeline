# src/scripts Cleanup Plan (Conservative, Repo-Aware)

Generated: 2026-03-30

## 0) Current iteration status

This plan is now aligned with the latest consistency fixes completed in this branch:

- Stage 6 threshold pass-through is fixed in runtime wiring.
- Trigger cooldown precedence is fixed so same-cycle escalation cannot override cooldown.
- Regression coverage exists for both fixes in tests.

Archive placeholders already exist and remain empty:

- scripts/archive_candidates/.gitkeep
- internal/archive_candidates/.gitkeep

No files were moved as part of this iteration.

## Goal

Provide a safe cleanup roadmap for `src/` and `scripts/` without breaking thesis runtime behavior.

Principles used:

- No destructive moves before classification and validation.
- Keep stages 1-7 stable as highest priority.
- Treat stages 8-14 and research scripts carefully (thesis evidence dependencies).
- Prefer documentation, deprecation notices, and wrappers before removals.

## 1) Classification

### A. Core runtime files (keep as canonical)

These define production behavior and are directly used by `run_pipeline.py` and `src/pipeline/production_pipeline.py`.

- `run_pipeline.py`
- `src/pipeline/production_pipeline.py`
- `src/components/*` (stages 1-14 wrappers)
- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`
- `src/trigger_policy.py`
- `src/preprocess_data.py`
- `src/utils/config_loader.py`

For stage-level focus:

- Stages 1-7 (highest stability priority): keep unchanged except explicit bug fixes.
- Stages 8-10 (retraining cycle): keep, but only adjust with explicit governance checks.
- Stages 11-14 (advanced/research): keep; avoid structural moves during thesis write-up window.

### B. Intentional wrapper dependencies (keep for now)

These are script modules currently imported by stage components at runtime:

- `scripts/post_inference_monitoring.py` imported by `src/components/post_inference_monitoring.py`
- `scripts/build_training_baseline.py` imported by `src/components/baseline_update.py`

Status:

- Not archive candidates right now.
- They are implementation modules behind `src/components` wrappers.

### C. Wrapper entrypoints with overlap and API drift risk

These look like legacy standalone orchestrators and are likely out-of-sync with current component constructors.

- `scripts/preprocess.py`
- `scripts/train.py`

Observed risk signal:

- They instantiate component classes with older signatures (for example missing `pipeline_config` argument).
- Keeping them as-is risks confusion and runtime failures if used directly.

Plan:

- Mark as legacy wrappers.
- Prefer `run_pipeline.py --stages ...` and `run_pipeline.py --retrain ...` for canonical execution.
- Do not remove yet; first add deprecation note and reference replacement commands.

### D. Research and thesis support scripts (keep)

These are useful for experiments, evidence generation, and diagnostics.

- `scripts/run_ablation_experiment.py`
- `scripts/run_ab_comparison.py`
- `scripts/threshold_sweep.py`
- `scripts/windowing_ablation.py`
- `scripts/generate_thesis_figures.py`
- `scripts/per_dataset_inference.py`
- `scripts/trigger_policy_eval.py`

Plan:

- Keep visible through thesis completion.
- Label clearly as research/analysis utilities, not production orchestrators.

### E. Legacy/archive candidates (defer, do not move yet)

Candidates to revisit after thesis milestone freeze:

- `scripts/preprocess.py` (legacy wrapper)
- `scripts/train.py` (legacy wrapper)
- `src/train.py` (standalone training module not part of canonical orchestrator path)
- `src/sensor_data_pipeline.py` (historical raw-processing path; keep until verified unused by external docs/workflows)

## 2) Duplicate/Overlap Notes

### Stage 6

- `src/components/post_inference_monitoring.py` is the orchestration wrapper.
- `scripts/post_inference_monitoring.py` is the current implementation module.

Conclusion:

- This is intentional layering, not immediate duplicate deletion territory.

### Stage 10

- `src/components/baseline_update.py` wraps baseline build operations.
- `scripts/build_training_baseline.py` provides baseline-building functionality used by the component.

Conclusion:

- Keep both until baseline logic is migrated into `src/` with parity tests.

### Legacy standalone wrappers vs orchestrator

- `scripts/preprocess.py` overlaps with stages 1-3 orchestration.
- `scripts/train.py` overlaps with stages 8-10 orchestration.
- Canonical orchestrator is `run_pipeline.py` + `src/pipeline/production_pipeline.py`.

## 3) Risk Map (What not to touch now)

High risk to modify during cleanup window:

- `src/components/data_ingestion.py`
- `src/components/data_transformation.py`
- `src/preprocess_data.py`
- `src/components/post_inference_monitoring.py`
- `src/trigger_policy.py`
- `src/components/trigger_evaluation.py`

Reason:

- These files directly affect stages 1-7 governance path and thesis-defensible behavior.

## 4) Proposed Cleanup Waves

### Wave 0 (now, safe)

- Keep runtime code stable.
- Update docs to mark canonical path and legacy wrappers.
- Add placeholder archive targets only.

### Wave 1 (after thesis freeze checkpoint)

- Add deprecation headers to `scripts/preprocess.py` and `scripts/train.py`.
- Replace their internals with thin wrappers calling `run_pipeline.py` stage options.
- Validate with smoke tests and docs update.

### Wave 2 (post-defense hardening)

- Evaluate archiving of `src/train.py` and `src/sensor_data_pipeline.py`.
- Consider moving script implementation modules used at runtime into `src/monitoring` and `src/baseline` namespaces.
- Preserve backward-compatible import shims if moved.

## 5) Suggested Archive Targets (placeholders only)

Planned targets:

- `scripts/archive_candidates/`
- `internal/archive_candidates/`

Rule:

- Do not move any runtime-critical file to archive candidates without usage verification and tests.

## 6) Validation Gates Before Any Future Move

Before archiving/moving any candidate file, require:

1. `git grep` usage check in repo docs and code.
2. Replacement path documented.
3. Targeted tests pass for affected stages.
4. Full `pytest tests/ -v` pass.
5. One lightweight pipeline run for stages 4-7 to confirm no behavior drift.

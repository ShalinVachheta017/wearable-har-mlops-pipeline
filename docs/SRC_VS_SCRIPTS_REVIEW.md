# src vs scripts Review (Thesis/Defense)

## Purpose

This document clarifies which files are runtime-critical (`src/` path), which files are utility/research scripts (`scripts/` path), and where overlap exists.

Scope: documentation only (no runtime code changes).

## 1) Canonical Runtime Path (Core)

The primary production execution path is:

1. `run_pipeline.py`
2. `src/pipeline/production_pipeline.py`
3. `src/components/*` stage components
4. underlying implementation modules in `src/*` (and selected imported script modules where explicitly wrapped)

For defense framing: `src/` is the runtime source of truth.

## 2) Confirmed Overlap Areas

| Area | Canonical path (keep) | Overlap path | Current status | Recommendation |
|---|---|---|---|---|
| Stages 1-3 orchestration | `run_pipeline.py` + `src/pipeline/production_pipeline.py` + `src/components/{data_ingestion,data_validation,data_transformation}.py` | `scripts/preprocess.py` | Wrapper overlap; script re-orchestrates stage subset. Also appears out-of-sync with current component constructor signatures. | Mark as legacy wrapper; either refactor to call `run_pipeline.py --stages ...` or archive later. |
| Stages 8-10 orchestration | `run_pipeline.py` + `src/pipeline/production_pipeline.py` + `src/components/{model_retraining,model_registration,baseline_update}.py` | `scripts/train.py` | Wrapper overlap; script re-orchestrates stage subset. Also appears out-of-sync with current component constructor signatures. | Mark as legacy wrapper; either refactor to call `run_pipeline.py --retrain ...` or archive later. |
| Stage 6 monitoring implementation | `src/components/post_inference_monitoring.py` | `scripts/post_inference_monitoring.py` | Intentional split: component wraps script module (`PostInferenceMonitor`). | Keep both for now; optional future move of monitor module under `src/monitoring/`. |
| Stage 10 baseline implementation | `src/components/baseline_update.py` | `scripts/build_training_baseline.py` | Intentional split: component imports `BaselineBuilder`. | Keep both for now; this is an active runtime dependency. |
| Trigger policy | `src/trigger_policy.py` + `src/components/trigger_evaluation.py` | `scripts/trigger_policy_eval.py` | Not true duplication; script is simulation/evaluation utility for policy comparisons. | Keep as research/analysis utility. |

## 3) Core Files to Keep (No Debate)

- `run_pipeline.py`
- `src/pipeline/production_pipeline.py`
- `src/components/*.py` (stage wrappers used by orchestrator)
- `src/preprocess_data.py`
- `src/train.py`
- `src/trigger_policy.py`
- `src/model_rollback.py`

These files define and execute the thesis pipeline behavior.

## 4) Scripts to Keep (Active Utility Value)

Keep as utility/research/support scripts:

- `scripts/post_inference_monitoring.py` (runtime dependency via stage 6 component)
- `scripts/build_training_baseline.py` (runtime dependency via stage 10 component)
- `scripts/inference_smoke.py` (API smoke check)
- `scripts/preprocess_qc.py` (preprocessing quality checks)
- `scripts/trigger_policy_eval.py` (policy simulation/evaluation)
- `scripts/generate_thesis_figures.py` (thesis figure generation)
- `scripts/run_ablation_experiment.py` (ablation workflow)
- `scripts/per_dataset_inference.py` (dataset-level inference diagnostics)

## 5) Future Merge/Archive Candidates (Low Risk, After Verification)

1. `scripts/preprocess.py`
   - Candidate because functionality overlaps with orchestrator-driven stages 1-3.
   - Suggested destination: archive as legacy CLI wrapper, or refactor into a thin `run_pipeline.py` argument wrapper.

2. `scripts/train.py`
   - Candidate because functionality overlaps with orchestrator-driven stages 8-10.
   - Suggested destination: archive as legacy CLI wrapper, or refactor into a thin `run_pipeline.py` argument wrapper.

Before archiving either file, verify no automation/docs still depend on direct invocation.

## 6) Defense-Ready One-Liner

`src/` contains the canonical production pipeline logic; `scripts/` contains utility/research entry points plus a small number of modules intentionally wrapped by `src/components`.

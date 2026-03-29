# WAVE 2 SIMPLIFICATION PLAN (Executed + Evidence)

Scope: manual-review and duplicate/alternate-path files in `src/` and `scripts/`, using Wave 1 outputs and prior audit reports as source of truth.

## A. Protected Runtime Files Confirmed

These remain in place and were smoke-checked/import-checked after Wave 2 high-confidence archival:

- `run_pipeline.py`
- `src/pipeline/production_pipeline.py`
- `src/api/app.py`
- `src/components/model_inference.py`
- `src/components/baseline_update.py`
- `scripts/build_training_baseline.py`
- `scripts/build_normalized_baseline.py`
- `scripts/preprocess.py`
- `scripts/train.py`
- `scripts/post_inference_monitoring.py`
- `src/exceptions.py`
- `src/logger/__init__.py`
- `src/trigger_policy.py`

Additional runtime evidence:

- `run_pipeline.py` imports `ProductionPipeline` from `src/pipeline/production_pipeline.py` (line 63).
- `src/components/model_inference.py` imports inference implementation from `src/run_inference.py` (line 42), not from `src/pipeline/inference_pipeline.py`.
- `src/components/baseline_update.py` imports `BaselineBuilder` from `build_training_baseline` (line 47).

## B. Wrapper-Only Files

Keep as wrappers/adapters for now (no behavior changes in Wave 2):

- `scripts/preprocess.py`
- `scripts/train.py`
- `src/components/post_inference_monitoring.py`
- `src/components/baseline_update.py`
- `src/pipeline/__init__.py` (compatibility export with guarded optional `InferencePipeline` import)

## C. Archive-Later Files

### C1) Archived now in Wave 2 (high confidence)

- `src/pipeline/inference_pipeline.py` -> `src/_wave2_archive/pipeline/inference_pipeline.py`
- `src/core/logger.py` -> `src/_wave2_archive/core/logger.py`
- `src/core/exception.py` -> `src/_wave2_archive/core/exception.py`
- `src/exception/__init__.py` -> `src/_wave2_archive/exception/__init__.py`

### C2) Archive later (not executed in this wave)

- `scripts/run_tests.py` (convenience CLI around `pytest`, not runtime-critical)

### C3) Keep for now (explicit decision update)

- `scripts/build_normalized_baseline.py`
  - rationale: thesis baseline support
  - review later only if replaced by an equivalent normalized-baseline path

## D. Delete-Later Files

No new high-confidence delete-later actions were executed in Wave 2.

Decision policy in this wave: archive-first bias for uncertain/non-runtime files.

## E. Manual-Review Files

These remain manual-review because they may still be needed for thesis reproducibility or deployment workflows:

- `src/deployment_manager.py`
- `scripts/batch_process_all_datasets.py`
- `scripts/per_dataset_inference.py`

## F. Exact Evidence For Each Decision

| File | Decision | Evidence | Wave 2 Action |
| --- | --- | --- | --- |
| `src/pipeline/inference_pipeline.py` | archive later | Only compatibility import found in `src/pipeline/__init__.py` line 7 (`try`/`except ImportError` guard). No protected runtime call path imports it. | Archived now |
| `src/core/logger.py` | archive later | `from src.core.logger import ...` found only inside archived `inference_pipeline` chain; no production runtime imports. | Archived now |
| `src/core/exception.py` | archive later | `from src.core.exception import ...` found only inside archived `inference_pipeline` chain; no production runtime imports. | Archived now |
| `src/exception/__init__.py` | archive later | No imports/usages found in active runtime paths; protected pipeline uses `src/exceptions.py` (`src/pipeline/production_pipeline.py` line 47). | Archived now |
| `src/deployment_manager.py` | manual review still needed | Contains active deployment CLI behavior (`DeploymentManager()` line 666) and docker-compose deployment commands (lines 343, 352, 357, 402, 464, 582). Also references removed observability file `prometheus_metrics.py` (line 150). | Kept for manual review |
| `scripts/build_normalized_baseline.py` | keep for now | Supports thesis baseline workflows and provides explicit normalized-baseline generation path. Runtime baseline update uses `build_training_baseline` via `src/components/baseline_update.py` line 47. Review later only if replaced by an equivalent normalized-baseline path. | Restored to `scripts/build_normalized_baseline.py` |
| `scripts/batch_process_all_datasets.py` | manual review still needed | Explicitly shells out to `run_pipeline.py` (`sys.executable, "run_pipeline.py"` lines 86-87), indicating thesis experiment orchestration utility. | Kept for manual review |
| `scripts/per_dataset_inference.py` | manual review still needed | Standalone dataset-level evaluation utility with model path `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` (line 37) and report output `reports/per_dataset_inference_analysis.json` (line 223). | Kept for manual review |
| `scripts/run_tests.py` | archive later | Developer helper wrapper around `pytest` (`python -m pytest`, argparse flags). Not part of protected runtime path. | Deferred (not executed) |

Protected-path confirmation evidence:

- `run_pipeline.py` imports `src/pipeline/production_pipeline.py` at line 63.
- `src/components/model_inference.py` imports from `src.run_inference` at line 42.
- `src/components/baseline_update.py` imports from `build_training_baseline` at line 47.
- Post-change smoke checks succeeded: `import run_pipeline`, `from src.api.app import app`, `python run_pipeline.py --help`, and `docker compose config`.

## G. Safest Cleanup Order

1. Keep protected runtime/orchestrator files frozen.
2. Archive isolated alternate-path modules first (done in Wave 2 high-confidence set).
3. Verify import smoke checks for main pipeline and FastAPI path (done).
4. Keep deployment and experiment orchestration scripts in manual-review until thesis reproducibility checklist is frozen.
5. Only then consider archive-later convenience scripts (for example `scripts/run_tests.py`).
6. Defer delete-later actions to post-thesis hardening pass.

## H. Files That Should Not Be Touched Before Thesis Submission

- `run_pipeline.py`
- `src/pipeline/production_pipeline.py`
- `src/api/app.py`
- `src/components/` runtime stage adapters
- `src/run_inference.py`
- `src/exceptions.py`
- `src/logger/__init__.py`
- `src/trigger_policy.py`
- `scripts/build_training_baseline.py`
- `scripts/build_normalized_baseline.py`
- `scripts/post_inference_monitoring.py`
- `scripts/preprocess.py`
- `scripts/train.py`
- `src/domain_adaptation/`
- `src/entity/`
- `src/utils/config_loader.py`
- `src/utils/artifacts_manager.py`

These remain critical for thesis-scope runtime, FastAPI/inference serving, retraining trigger, and baseline update continuity.

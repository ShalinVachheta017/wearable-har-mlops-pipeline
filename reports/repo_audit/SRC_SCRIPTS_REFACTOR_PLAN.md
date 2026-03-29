# src/ & scripts/ Refactor Plan

> Generated: 2026-03-05
> Scope: Consolidate `src/` into `src/har/` package, thin scripts, fix reversed deps
> Safety: No deletions; deprecated code → `archive/code_old/`

---

## 1. Current Inventory

### 1.1 src/ — 57 Python files (12,500+ lines)

```
src/
├── __init__.py                         (1L)
├── active_learning_export.py           (522L)  ← loose, active-learning sample selection
├── calibration.py                      (450L)  ← loose, temperature scaling + MC Dropout
├── config.py                           (62L)   ← loose, project-level config paths
├── curriculum_pseudo_labeling.py       (384L)  ← loose, teacher-student curriculum
├── data_validator.py                   (251L)  ← loose, schema + range validation
├── deployment_manager.py               (575L)  ← loose, container build/canary deploy
├── diagnostic_pipeline_check.py        (276L)  ← loose, diagnostic runner
├── evaluate_predictions.py             (592L)  ← loose, metric computation
├── exceptions.py                       (20L)   ← loose, DataValidationError
├── mlflow_tracking.py                  (533L)  ← loose, MLflow wrapper
├── model_rollback.py                   (410L)  ← loose, version rollback
├── ood_detection.py                    (343L)  ← loose, energy-based OOD
├── preprocess_data.py                  (693L)  ← loose, windowing/normalization
├── prometheus_metrics.py               (480L)  ← loose, metrics exporter
├── robustness.py                       (354L)  ← loose, noise injection tests
├── run_inference.py                    (677L)  ← loose, standalone inference (OLD)
├── sensor_data_pipeline.py             (935L)  ← loose, raw Excel → fused CSV
├── sensor_placement.py                 (273L)  ← loose, axis mirror + hand detect
├── train.py                            (1146L) ← loose, training + cross-validation
├── trigger_policy.py                   (683L)  ← loose, retraining decision
├── wasserstein_drift.py                (351L)  ← loose, drift detection
├── api/
│   ├── __init__.py
│   └── app.py                          (761L)  FastAPI serving app
├── components/                         (14 stage wrappers, each ~100L)
│   ├── baseline_update.py              ⚠ imports from scripts/ (REVERSED DEP)
│   ├── calibration_uncertainty.py      wraps src/calibration.py
│   ├── curriculum_pseudo_labeling.py   wraps src/curriculum_pseudo_labeling.py
│   ├── data_ingestion.py               standalone component
│   ├── data_transformation.py          standalone component
│   ├── data_validation.py              standalone component
│   ├── model_evaluation.py             standalone component
│   ├── model_inference.py              standalone component
│   ├── model_registration.py           standalone component
│   ├── model_retraining.py             standalone component
│   ├── post_inference_monitoring.py    ⚠ imports from scripts/ (REVERSED DEP)
│   ├── sensor_placement.py             wraps src/sensor_placement.py
│   ├── trigger_evaluation.py           standalone component
│   └── wasserstein_drift.py            wraps src/wasserstein_drift.py
├── core/                               exception + logger
├── domain_adaptation/                  adabn.py + tent.py
├── entity/                             artifact_entity.py + config_entity.py
├── logger/                             logging setup
├── exception/                          PipelineException
├── pipeline/
│   ├── inference_pipeline.py           (658L) standalone orchestrator (ALTERNATE)
│   └── production_pipeline.py          (893L) MAIN 14-stage pipeline
└── utils/                              common, config_loader, artifacts_manager, etc.
```

### 1.2 scripts/ — 25 Python files (6,350+ lines)

| Script | Lines | Type | Imports src? |
|--------|-------|------|-------------|
| `preprocess.py` | 104 | thin CLI → src/components stages 1-3 | ✅ entity |
| `train.py` | 118 | thin CLI → src/components stages 8-10 | ✅ entity |
| `preprocess_qc.py` | 780 | **business logic** — QC checks | ✗ |
| `run_ab_comparison.py` | 553 | **business logic** — A/B test normalization | ✗ |
| `generate_thesis_figures.py` | 502 | **business logic** — thesis plots | ✗ |
| `threshold_sweep.py` | 472 | **business logic** — sweep drift thresholds | ✅ temporal_metrics |
| `post_inference_monitoring.py` | 378 | **business logic** — 3-layer monitor | ✗ (but IMPORTED BY src!) |
| `regenerate_support_map.py` | 328 | **business logic** — thesis paper map | ✗ |
| `verify_repository.py` | 316 | **business logic** — repo audit | ✗ |
| `windowing_ablation.py` | 300 | **business logic** — window size search | ✅ temporal_metrics |
| `trigger_policy_eval.py` | 290 | **business logic** — policy comparison | ✗ |
| `build_training_baseline.py` | 239 | **business logic** — baseline builder | ✗ (but IMPORTED BY src!) |
| `inference_smoke.py` | 207 | **business logic** — API smoke test | ✗ |
| `per_dataset_inference.py` | 191 | **business logic** — per-dataset eval | ✗ |
| `export_mlflow_runs.py` | 186 | **business logic** — MLflow export | ✗ |
| `audit_artifacts.py` | 178 | **business logic** — artifact checker | ✗ |
| `benchmark_throughput.py` | 161 | **business logic** — load test | ✗ |
| `benchmark_latency.py` | 154 | **business logic** — latency bench | ✗ |
| `update_progress_dashboard.py` | 150 | **business logic** — thesis TRS | ✗ |
| `extract_papers_to_text.py` | 139 | **business logic** — PDF→text | ✗ |
| `fetch_foundation_papers.py` | 132 | **business logic** — arxiv download | ✗ |
| `build_normalized_baseline.py` | 116 | **business logic** — norm baseline | ✗ |
| `run_tests.py` | 112 | **utility** — pytest launcher | ✗ |
| `analyze_drift_across_datasets.py` | 110 | **business logic** — drift analysis | ✗ |

### 1.3 Root entrypoints — 3 files

| File | Lines | Type |
|------|-------|------|
| `run_pipeline.py` | 499 | thin CLI → `ProductionPipeline` |
| `batch_process_all_datasets.py` | 497 | **business logic** — multi-dataset loop |
| `generate_summary_report.py` | 181 | **business logic** — batch report |

---

## 2. Dependency Issues Found

### 2.1 Reversed Dependencies (src → scripts)

| Component | Imports From | Class Used |
|-----------|-------------|------------|
| `src/components/post_inference_monitoring.py` | `scripts/post_inference_monitoring.py` | `PostInferenceMonitor` |
| `src/components/baseline_update.py` | `scripts/build_training_baseline.py` | `BaselineBuilder` |

**Both use runtime `sys.path.insert(0, scripts_dir)` hacks to import.**
These MUST be fixed in Phase 1.

### 2.2 Duplicate/Alternate Implementations

| File A | File B | Relationship |
|--------|--------|-------------|
| `src/run_inference.py` (677L) | `src/pipeline/inference_pipeline.py` (658L) | Alternate inference orchestrators — `inference_pipeline.py` is the current production version |
| `src/train.py` (1146L) | `scripts/train.py` (118L) | INDEPENDENT — scripts/train.py calls components, not src/train.py |
| `src/preprocess_data.py` (693L) | `scripts/preprocess.py` (104L) | INDEPENDENT — scripts/preprocess.py calls components, not src/preprocess_data.py |

### 2.3 Import Graph (src internal — who imports whom?)

```
src/pipeline/production_pipeline.py
  ├── src/entity/artifact_entity.py
  ├── src/entity/config_entity.py
  ├── src/exceptions.py
  ├── src/logger/
  ├── src/utils/artifacts_manager.py
  └── src/components/* (all 14 stages)
        └── each component → src/entity/*

src/components/wasserstein_drift.py → src/wasserstein_drift.py
src/components/calibration_uncertainty.py → src/calibration.py
src/components/curriculum_pseudo_labeling.py → src/curriculum_pseudo_labeling.py
src/components/sensor_placement.py → src/sensor_placement.py
src/components/post_inference_monitoring.py → scripts/post_inference_monitoring.py ⚠
src/components/baseline_update.py → scripts/build_training_baseline.py ⚠

src/domain_adaptation/__init__.py → src/domain_adaptation/{adabn,tent}.py
src/entity/__init__.py → src/entity/{artifact_entity,config_entity}.py
src/utils/__init__.py → src/utils/{common,main_utils}.py
src/utils/main_utils.py → src/utils/common.py
```

---

## 3. Proposed Target Layout

```
src/
├── har/                                 # MAIN PACKAGE
│   ├── __init__.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── production_pipeline.py       # 14-stage orchestrator
│   │   └── inference_pipeline.py        # alternate orchestrator
│   ├── components/                      # stage wrappers (unchanged)
│   │   └── ... (14 files)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── preprocess_data.py           # windowing, normalization
│   │   ├── sensor_data_pipeline.py      # raw Excel → fused CSV
│   │   └── data_validator.py            # schema + range checks
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py                     # training + CV
│   │   ├── curriculum_pseudo_labeling.py
│   │   └── active_learning_export.py
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── run_inference.py             # batch/RT inference
│   │   └── evaluate_predictions.py      # metrics
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── post_inference_monitoring.py # ← MOVED FROM scripts/
│   │   ├── trigger_policy.py
│   │   ├── wasserstein_drift.py
│   │   ├── ood_detection.py
│   │   ├── calibration.py
│   │   ├── robustness.py
│   │   └── prometheus_metrics.py
│   ├── domain_adaptation/               # already a sub-package
│   │   ├── __init__.py
│   │   ├── adabn.py
│   │   └── tent.py
│   ├── deployment/
│   │   ├── __init__.py
│   │   ├── deployment_manager.py
│   │   └── model_rollback.py
│   ├── entity/                          # artifact + config dataclasses
│   │   ├── __init__.py
│   │   ├── artifact_entity.py
│   │   └── config_entity.py
│   ├── core/                            # exception + logger
│   │   ├── __init__.py
│   │   ├── exception.py
│   │   └── logger.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── main_utils.py
│   │   ├── config_loader.py
│   │   ├── artifacts_manager.py
│   │   ├── production_optimizations.py
│   │   └── temporal_metrics.py
│   └── api/
│       ├── __init__.py
│       └── app.py
├── __init__.py                          # kept for backward compat
└── (backward-compat shims)              # see Phase 1 strategy
```

---

## 4. Execution Plan

### Phase 1 — Safe restructure (this session)

**Step 1a**: Fix reversed dependencies FIRST
- Move `scripts/post_inference_monitoring.py` → `src/monitoring/post_inference_monitoring.py`
  - Update `src/components/post_inference_monitoring.py` to import from `src.monitoring`
- Move `scripts/build_training_baseline.py` → `src/monitoring/build_training_baseline.py`
  - Update `src/components/baseline_update.py` to import from `src.monitoring`

**Step 1b**: Create `src/har/` package skeleton
- `git mv` all sub-packages: `components/`, `pipeline/`, `entity/`, `core/`, `logger/`, `exception/`, `domain_adaptation/`, `utils/`, `api/`
- `git mv` loose modules into domain sub-packages (see target layout above)
- Add `__init__.py` files for new packages

**Step 1c**: Create backward-compat shims in `src/`
- Each old import path (`from src.train import ...`) gets a 2-line shim:
  ```python
  # Backward compatibility – real module moved to src.har.training.train
  from src.har.training.train import *  # noqa: F401,F403
  ```
- This allows incremental migration without breaking everything at once

**Step 1d**: Update all `from src.` imports to `from src.har.`
- In: `src/har/` (internal imports)
- In: `tests/`
- In: `scripts/`
- In: root scripts

**Step 1e**: Verify
- `python -m compileall src`
- `pytest --co -q`

### Phase 2 — Script thinning

For scripts > 120 lines that contain business logic used by src/components:
- ~~`scripts/post_inference_monitoring.py`~~ (moved in Phase 1)
- ~~`scripts/build_training_baseline.py`~~ (moved in Phase 1)

Remaining large scripts are **standalone tools** (thesis figures, benchmarks, ablation, QC). They do NOT need to be thinned because:
1. They are NOT imported by `src/` (no reversed dependency)
2. They are special-purpose analysis/evaluation utilities
3. Many are thesis-only (thesis figures, paper extraction)

No further script thinning is required — the two problematic scripts (the only ones imported by src/) are already addressed in Phase 1.

### Phase 3 — Deprecation

| File | Action | Reason |
|------|--------|--------|
| `src/run_inference.py` (677L) | → `archive/code_old/20260305/run_inference.py` | Superseded by `src/pipeline/inference_pipeline.py` |
| `src/diagnostic_pipeline_check.py` (276L) | → `archive/code_old/20260305/diagnostic_pipeline_check.py` | One-off diagnostic, no longer called |
| `src/config.py` (62L) | → `archive/code_old/20260305/config.py` | Superseded by `src/entity/config_entity.py` |
| `src/logger/__init__.py` (76L) | Review — may be duplicate of `src/core/logger.py` |
| `src/exception/__init__.py` (43L) | Review — may be duplicate of `src/core/exception.py` |

---

## 5. Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Breaking import paths | Backward-compat shims in `src/` (Phase 1c) |
| Test failures | Run `pytest --co` + `compileall` after each batch |
| Docker paths | `docker/Dockerfile.*` uses `COPY src/ src/` — will pick up new structure |
| pyproject.toml `[tool.setuptools.packages.find]` | Currently `include = ["src*"]` — will match `src.har.*` automatically |
| `har-pipeline = "src.cli:main"` entry point | Currently broken (file doesn't exist) — defer to later |
| CI (GitHub Actions) | Verify `python -m compileall src` + `pytest` still pass |

---

## 6. Files this Audit Creates

- `reports/repo_audit/SRC_SCRIPTS_REFACTOR_PLAN.md` — this file

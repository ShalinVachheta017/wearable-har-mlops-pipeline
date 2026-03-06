# Project Worklog

## Purpose
Daily running log of major repo changes, progress, decisions, and next steps.
Auto-generated from git commit history and supplemented manually.

---

## 2026-03-07
### Done
- **CI black / isort fixes** — CI lint job was failing on 2 checks:
  - `black --check`: 53 files re-formatted (`python -m black .`, committed `"style: auto-format with black"`)
  - `isort --check-only src/`: 2 files in `src/monitoring/` had wrong import order — fixed manually (`"style: fix isort import ordering"`)
- **Archive duplicate audit** — read-only scan of all 506 PDFs:
  - `scripts/find_duplicate_papers.py` — SHA-256 based, never modifies files
  - `reports/repo_audit/ARCHIVE_DUPLICATES_REPORT.md` — 95 duplicate groups, 75 cross-tree, 1 name collision
  - `reports/repo_audit/ARCHIVE_DUPLICATES.csv` — machine-readable detail
  - `reports/repo_audit/ARCHIVE_DUPLICATE_ACTION_PLAN.md` — Bucket A/B/C classification + 3-phase cleanup plan
  - `.gitignore` changed `reports/` → `reports/*` + `!reports/repo_audit/` to track audit outputs
- **`run_pipeline.py` — stage manifest** — added `_print_planned_stages(args)`, prints full 14-stage queue/skip table before execution
- **README updates** — 4 sections updated: Architecture (3-pipeline overview), Pipeline Stages (stage-group table + quick usage), Project Structure (domain-structured `src/` layout), CI/CD (ASCII workflow diagrams + common fix commands)
- **Pipeline log improvements (this session)**:
  - `docs/TRIGGER_POLICY_EXPLANATION.md` — new: explains Healthy/Warning/Critical states, why class dominance ≠ retrain, run classification table for 2026-03-06 run
  - `src/evaluate_predictions.py` `analyze_distribution()` — added `distribution_dominance_warning` flag (fires when dominant class > 95 %); returns `_distribution_dominance_warning`, `_dominant_class`, `_dominant_pct` keys
  - `src/entity/artifact_entity.py` `ModelEvaluationArtifact` — new `distribution_dominance_warning: bool = False` field
  - `src/components/model_evaluation.py` — extracts and propagates dominance flag to artifact
  - `src/mlflow_tracking.py` `log_keras_model()` — removed `input_example` from `mlflow.keras.log_model` calls (fixes `input_example.json FileNotFoundError`); signature is still inferred and passed
  - `run_pipeline.py` — added `_print_compact_run_summary()` — ASCII box printed before the detailed summary (Run ID, input source, windows, inference speed, confidence, dominant class, drift, trigger, MLflow, overall)

### Files / Areas Affected
- `src/monitoring/post_inference_monitoring.py` — isort fix
- `src/monitoring/build_training_baseline.py` — isort fix
- `scripts/find_duplicate_papers.py` — NEW
- `reports/repo_audit/ARCHIVE_DUPLICATES_REPORT.md` — NEW
- `reports/repo_audit/ARCHIVE_DUPLICATES.csv` — NEW
- `reports/repo_audit/ARCHIVE_DUPLICATE_ACTION_PLAN.md` — NEW
- `.gitignore` — reports/* + !reports/repo_audit/
- `run_pipeline.py` — `_print_planned_stages()` + `_print_compact_run_summary()`
- `README.md` — 4 sections updated
- `docs/TRIGGER_POLICY_EXPLANATION.md` — NEW
- `src/evaluate_predictions.py` — dominance warning flag
- `src/entity/artifact_entity.py` — `distribution_dominance_warning` field
- `src/components/model_evaluation.py` — propagates dominance flag
- `src/mlflow_tracking.py` — removed `input_example` from `log_model` calls

### Why
- CI was blocking merges — linting must be green before any other work
- Archive had ~95 duplicate PDFs in two locations — needed an audit before semi-annual cleanup
- Stage manifest gives instant visibility into what the pipeline will actually run
- README was missing 3-pipeline overview and had stale `src/` structure
- `TRIGGER_POLICY_EXPLANATION.md` needed because the 2026-03-06 run triggered a dominance warning but correctly did NOT retrain — this decision needed to be documented for the thesis
- MLflow Keras `input_example.json` FileNotFoundError was silently swallowing the model registration step; signature-only logging is correct and sufficient
- Compact RUN SUMMARY gives at-a-glance health status without scrolling the full log

### Status
- All CI checks passing (black, isort, flake8, pytest, docker-build)
- Branch: `chore/repo-cleanup`
- Pipeline tested: 7/7 stages SUCCESS, trigger=NONE (healthy)

### Next
- Execute archive cleanup Phase 1 (Bucket A — safe removals from `archive/`)
- Run pipeline again with `--retrain` to verify dominance flag flows through the RUN SUMMARY box
- Monitor next production run — if class dominance continues, schedule a labelling session

---
# for 6tgh march morning, 



## 2026-03-06
### Done
- Refactored `src/` into domain-based subpackages: `data/`, `training/`, `inference/`, `monitoring/`, `deployment/`
- Removed reversed dependencies from `scripts/` into `src/`
- Added backward-compatibility shim modules
- Verified `python -m compileall src -q` — clean
- Verified `pytest -q` — 258/258 passed
- Restructured `docs/` into organized subdirectories: `01_PIPELINE/`, `02_TECH/`, `03_EXPERIMENTS/`, `04_THESIS_WRITING/`, `99_ARCHIVE/`
- Created pipeline stage documentation (stages 01–10)
- Created thesis writing guides, chapter drafts, research Q&A, mentor questions
- Moved archived docs to `99_ARCHIVE/` and `thesis/_snapshots/`
- Improved CD workflow: added debug endpoints step, robust multi-route smoke test (`/openapi.json` → `/health` → `/api/health` → `/`)
- Created paper catalog (`archive/_index/PAPERS_CATALOG.md`)
- Organized 76 research PDFs into `thesis/refs/papers_all/` (6 topic folders)
- Created `thesis/refs/papers_all/READING_LIST_BY_CHAPTER.md` — chapter-to-paper mapping
- Created `docs/WORKLOG.md` — this file
- **Fixed Docker build failure**: `docker/Dockerfile.inference` referenced deleted `api/` folder
  - Changed `COPY api/ /app/api/` → `COPY src/ /app/src/`
  - Changed `CMD uvicorn api.main:app` → `CMD uvicorn src.api.app:app`
  - Updated `PYTHONPATH=/app` → `PYTHONPATH=/app:/app/src`
  - Updated `HEALTHCHECK` to try `/health` then `/api/health` then `/openapi.json`
  - Root cause: refactor moved API from `api/` to `src/api/app.py` but Dockerfile was not updated

### Files / Areas Affected
- `src/data/data_validator.py` — moved from `src/`
- `src/data/preprocess_data.py` — moved from `src/`
- `src/data/sensor_data_pipeline.py` — moved from `src/`
- `src/training/train.py` — moved from `src/`
- `src/training/active_learning_export.py` — moved from `src/`
- `src/training/curriculum_pseudo_labeling.py` — moved from `src/`
- `src/inference/run_inference.py` — moved from `src/`
- `src/inference/evaluate_predictions.py` — moved from `src/`
- `src/monitoring/build_training_baseline.py` — moved from `src/`
- `src/monitoring/calibration.py` — moved from `src/`
- `src/monitoring/ood_detection.py` — moved from `src/`
- `src/monitoring/prometheus_metrics.py` — moved from `src/`
- `src/monitoring/robustness.py` — moved from `src/`
- `src/monitoring/sensor_placement.py` — moved from `src/`
- `src/monitoring/trigger_policy.py` — moved from `src/`
- `src/monitoring/wasserstein_drift.py` — moved from `src/`
- `src/deployment/deployment_manager.py` — moved from `src/`
- `src/deployment/mlflow_tracking.py` — moved from `src/`
- `src/deployment/model_rollback.py` — moved from `src/`
- `src/pipeline/inference_pipeline.py` — updated imports to new subpackage paths
- `src/components/baseline_update.py` — updated imports
- `src/components/post_inference_monitoring.py` — updated imports
- `tests/test_baseline_update.py` — updated imports
- `docker/Dockerfile.inference` — fixed COPY path, CMD entrypoint, PYTHONPATH, HEALTHCHECK
- `.github/workflows/cd.yml` — debug step + 60-iteration wait + multi-route smoke test
- `docs/01_PIPELINE/stages/` — 10 new stage documentation files (01–10)
- `docs/02_TECH/guides/` — 8 new operation guides
- `docs/03_EXPERIMENTS/` — evidence pack, threshold calibration summary
- `docs/04_THESIS_WRITING/` — chapter drafts, mentor Q&A, research analysis
- `docs/99_ARCHIVE/` — archived old doc files
- `thesis/_snapshots/` — historical work snapshots (Feb snapshots)
- `archive/_index/PAPERS_CATALOG.md` — 76-paper categorized index
- `thesis/refs/papers_all/01_mlops/` — 18 MLOps PDFs
- `thesis/refs/papers_all/02_monitoring_drift/` — 3 monitoring PDFs
- `thesis/refs/papers_all/03_har_wearables/` — 27 HAR/sensor PDFs
- `thesis/refs/papers_all/04_domain_adaptation/` — 3 domain adaptation PDFs
- `thesis/refs/papers_all/05_deployment_cicd/` — 6 deployment PDFs
- `thesis/refs/papers_all/06_mental_health_anxiety/` — 19 mental health PDFs
- `thesis/refs/papers_all/READING_LIST_BY_CHAPTER.md` — chapter-to-paper map
- `docs/WORKLOG.md` — this file (new)

### Why
- Flat `src/` had 30+ modules — hard to navigate and explain in thesis
- Reversed dependencies (scripts importing src, src importing scripts) made the codebase fragile
- `docker/Dockerfile.inference` was never updated after the API moved from `api/` to `src/api/`
- CD smoke test had insufficient wait time and no debug visibility
- Docs were scattered with no clear organization
- Papers were spread across multiple archive folders with no single library

### Status
- Refactor complete and tests passing (258/258)
- Docker build error fixed — `COPY api/` → `COPY src/`
- CD workflow improved and tag `v0.9.1` pushed
- Docs restructured into 4 clear categories
- 76 PDFs organized into thesis paper library

### Next
- Verify CD passes with `v0.9.1` tag run
- Run full pipeline locally: `python run_pipeline.py`
- Confirm `/api/health` endpoint responds in container

---

## 2026-03-05
### Done
- Updated March TODO planning docs
- Fixed CI workflow issues
- Split combined CI/CD into separate `ci.yml` and `cd.yml` workflows
- Documented CI/CD triggers and structure
- Fixed CD workflow and inference container configuration

### Files / Areas Affected
- `.github/workflows/ci.yml` — new standalone CI
- `.github/workflows/cd.yml` — new standalone CD
- `docker/Dockerfile.inference` — inference container fixes

### Why
- Combined workflow was hard to debug and had conflicting triggers
- CI and CD have different trigger conditions (push/PR vs tags)

### Status
- CI green
- CD not yet green (smoke test failing — route/startup issue)

### Next
- Debug actual container routes with enhanced smoke test
- Validate refactored `src/` structure

---

## 2026-02-25 – 2026-02-26
### Done
- MiKTeX installation for LaTeX thesis compilation
- README update

### Files / Areas Affected
- `auto-install=yes/` — MiKTeX package files
- `README.md`

### Status
- LaTeX toolchain available for thesis compilation

---

## 2026-02-22 – 2026-02-23
### Done
- Major bug fix sprint: aligned code to 11 anxiety behavior classes (was using wrong PAMAP2 class list)
- Fixed train.py architecture to match pretrained model (~499K params, not ~1.5M)
- Fixed Docker container: resolved `api.app` module shadowing, set correct PYTHONPATH
- Fixed CI/CD: switched Docker to `src/api/app.py`, poll loop replaces `sleep 10`, corrected `/health` → `/api/health`
- Fixed Stage 11 crash — TTA governance registration fallback
- Renamed `psi_warn` → `drift_zscore_warn` (threshold 2.0σ / 3.0σ) with thesis parameter citations
- Fixed Stage 7 — reads `drift_zscore_warn` after rename
- Comprehensive cross-code audit of all markdown files
- Reformatted `train.py` for black compliance
- Config updates
- Moved thesis writing docs to `Thesis_report/` (local-only, gitignored)

### Files / Areas Affected
- `src/active_learning_export.py` — fixed class list
- `tests/conftest.py` — fixture uses correct 11 classes
- `src/train.py` — architecture alignment + black formatting
- `docker/Dockerfile.inference` — PYTHONPATH fix
- `.github/workflows/` — CI/CD route fixes
- `README.md` — corrected params, endpoints, progress
- Multiple docs — cross-code audit corrections
- `config/pipeline_config.yaml` — threshold rename

### Why
- Wrong class list caused silent data integrity issues
- Model param count mismatch between docs and code
- Docker shadowing caused container startup failures
- Threshold naming was inconsistent across codebase

### Status
- 215 tests passing after fixes
- CI green
- CD still failing on smoke test

---

## 2026-02-19
### Done
- Fixed baseline + metric loss bugs
- Added missing `build_training_baseline.py`, saved normalized baseline, exposed tent/adabn_tent in CLI
- Hardened PSI test, schema guard in Stage 6, schema_version, artifact baseline copy
- Split unit/slow tests, fixed artifact copy guard, marked TF tests as slow
- Thesis closure: traceability docs, audit script, fixed pseudo-label pipeline
- Fixed TENT running-stats freeze + rollback, baseline governance, GPU detection
- Fixed baseline governance (no `models/` write when not promoting), TENT confidence-drop rollback
- Fixed `tf.function` retracing, GPU diagnostic message, MLflow `name=` fix
- Reorganized Feb 19 docs into `docs/19_Feb/`
- Reorganized docs into archive/technical/research/thesis structure

### Files / Areas Affected
- `src/build_training_baseline.py` — new
- `src/tent_adaptation.py`, `src/adabn_adaptation.py` — TENT fixes
- `tests/` — PSI test fix, slow test markers
- `config/pipeline_config.yaml` — schema_version added
- Multiple doc reorganization

### Why
- TENT freeze/rollback was unsafe — could corrupt model on bad batches
- Schema validation was missing in Stage 6
- Test suite needed separation of fast/slow tests for CI efficiency
- Pseudo-label pipeline had safety issues

### Status
- All tests passing
- Pipeline hardened
- Docs reorganized

---

## 2026-02-15 – 2026-02-16
### Done
- Added FastAPI with web UI for CSV upload, inference, and monitoring
- Consolidated progress tracking into single source of truth
- Added production-ready CI/CD pipeline (GitHub Actions)
- Fixed Docker image name for ghcr.io compliance (lowercase)
- Monitoring docs completed
- GitHub Actions settings configured

### Files / Areas Affected
- `src/api/app.py` — new FastAPI application
- `.github/workflows/` — CI/CD workflows
- `docker/Dockerfile.inference` — Docker build
- Multiple docs — progress consolidation

### Why
- Needed serving layer for inference API
- Needed automated CI/CD for thesis demonstration
- Docker image naming rules require lowercase

### Status
- FastAPI running locally with CSV upload
- CI/CD pipeline created
- 95% progress on thesis pipeline

---

## 2026-02-14
### Done
- Fixed all tests: 225/225 passing
- Integrated monitoring pipeline
- Added production optimizations

### Files / Areas Affected
- `src/` — monitoring integration
- `tests/` — test fixes

### Status
- Full test suite green

---

## 2026-02-12
### Done
- Completed 10-stage MLOps pipeline with AdaBN domain adaptation
- Removed large image and model files from git tracking (moved to .gitignore)

### Files / Areas Affected
- `src/` — full pipeline implementation
- `.gitignore` — added model/image exclusions
- `run_pipeline.py` — pipeline orchestration

### Why
- Large binary files were bloating repo
- AdaBN domain adaptation is a core thesis contribution

### Status
- Full 10-stage pipeline implemented
- Models tracked via DVC, not git

---

## 2026-01-09 – 2026-01-17
### Done
- Documentation updates
- Updated .gitignore

### Status
- Maintenance period

---

## 2025-12-21
### Done
- Documentation updates

---

## 2025-12-16
### Done
- Updated analysis, progress, and stack documentation
- Updated pipeline and source files
- Removed obsolete and log files

---

## 2025-12-11 – 2025-12-12
### Done
- Reorganized documentation — added PATH_COMPARISON_ANALYSIS, archived outdated files
- Added complete MLOps infrastructure: DVC, MLflow, Docker
- README updates
- Repo reform / restructuring

### Files / Areas Affected
- `config/` — DVC and MLflow configs
- `docker/` — Dockerfile
- `.dvc/` — DVC initialization
- `docs/` — documentation structure

### Why
- Needed MLOps tooling foundation: data versioning (DVC), experiment tracking (MLflow), containerization (Docker)

---

## 2025-12-06 – 2025-12-08
### Done
- Resolved conversion ratio/solution for sensor data
- Phase 2 complete: model inference & evaluation pipeline

### Files / Areas Affected
- `src/run_inference.py`, `src/evaluate_predictions.py`

### Status
- Inference pipeline functional

---

## 2025-11-05 – 2025-11-28
### Done
- Identified accelerometer data error between prod and main
- Fixed data distribution error in acceleration values
- Main data added to .gitignore

### Why
- Sensor data had inconsistencies in acceleration units/ranges

---

## 2025-10-23 – 2025-10-25
### Done
- Initial commit with structured files and folders
- Data preprocessing pipeline created
- README added
- Excluded documentation from Git (keep progress private)

### Files / Areas Affected
- Full repo scaffolding
- `src/preprocess_data.py` — initial preprocessing
- `.gitignore` — docs exclusion

### Status
- Project initialized

---

## Current Repo Status
- **Branch:** `chore/docs-restructure`
- **Tests:** 258/258 passing
- **CI:** Green
- **CD:** Docker build fixed (`COPY src/` + `uvicorn src.api.app:app`), tag `v0.9.1` pushed
- **Refactor:** `src/` domain subpackages complete
- **Docs:** Restructured into 4 categories
- **Paper library:** 76 PDFs organized in `thesis/refs/papers_all/` (6 topic folders)
- **Paper catalog:** `archive/_index/PAPERS_CATALOG.md`
- **WORKLOG:** `docs/WORKLOG.md` — this file

## Open Issues
1. CD not yet confirmed green — `v0.9.1` run in progress
2. Full pipeline not yet run end-to-end on real data after refactor

## Recommended Next 3 Actions
1. Confirm CD green from `v0.9.1` run — check `/api/health` responds
2. Run `python run_pipeline.py` on real data locally
3. Wire docs into thesis chapters using `READING_LIST_BY_CHAPTER.md`

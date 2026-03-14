# Project Worklog

## Purpose
Daily running log of major repo changes, progress, decisions, and next steps.
Auto-generated from git commit history and supplemented manually.

---

## 2026-03-14
### Done Today
- Stabilized thesis writing structure under `thesis/` with canonical entrypoint `thesis/main.tex` and tracked chapter files (`ch1` to `ch8`).
- Added real bibliography usage and Chapter 1 problem statement:
  - `thesis/references.bib`
  - `thesis/chapters/ch1_introduction.tex`
- Verified thesis build pipeline with full sequence:
  - `pdflatex main.tex`
  - `bibtex main`
  - `pdflatex main.tex`
  - `pdflatex main.tex`
- Cleaned `docker/Dockerfile.inference` (kept only valid Docker instructions; removed accidental command text).
- Consolidated thesis planning docs under `docs/thesis/`:
  - `docs/thesis/THESIS_WORKFLOW_MAR_JUN_2026.md`
  - `docs/thesis/THESIS_EVIDENCE.md`
  - `docs/thesis/EXPERIMENT_PLAN.md`
  - `docs/thesis/DEFENSE_PLAN.md`
- Updated README links and added thesis reproducible build command block.

### Commits (Today)
- `80e01ae` - thesis: finalize workflow docs and chapter-1 citation baseline
- `1aad2a6` - thesis: add chapter placeholders 2-8
- `fd7ada2` - docs: consolidate thesis workflow under docs/thesis
- `f69d874` - docs: update thesis links and add latex build steps

### Planning Alignment
- Followed the March to June execution strategy: structure first, then writing, then experiments.
- Current phase focus remains: documentation and thesis writing momentum during exam period.

### Next Work (Important)
- Before starting any next task, check this file first:
  - `docs/thesis/THESIS_WORKFLOW_MAR_JUN_2026.md`
- Use this as the release/checkpoint reference for March to June planning.
- Next high-impact writing task: continue `thesis/chapters/ch2_background_related_work.tex`.

## 2026-03-07
### Done
Perfect — let’s make this **practical and actionable**. I’ll give you:

1️⃣ **Exactly what you should do today (realistic tasks)**
2️⃣ The **final Markdown file** you can paste directly into your repo
3️⃣ Instructions to **rename and update your workflow file**
4️⃣ A **clean structure** so Copilot and you can maintain it easily

You can copy the Markdown below into:

```
docs/MARCH_TO_JUNE_THESIS_WORKFLOW.md
```

or

```
THESIS_WORKFLOW_MAR_JUN_2026.md
```

---

# 1️⃣ What You Should Do **Today**

Keep today **light**, because you also have exams.

### Today’s Tasks (2–3 hours max)

**1️⃣ Rename the existing workflow file**

Rename:

```
TODO_MARCH.md
```

to

```
THESIS_WORKFLOW_MAR_JUN_2026.md
```

---

**2️⃣ Fix two repo issues Copilot detected**

Small but important.

### Fix README path drift

Update links pointing to old thesis folders.

---

### Fix Dockerfile inference

Check file:

```
docker/Dockerfile.inference
```

Remove any accidental text like:

```
git commit
git status
```

or anything not part of Docker commands.

---

**3️⃣ Create thesis folder**

Inside repo:

```
thesis/
```

Structure:

```
thesis
 ├── main.tex
 ├── chapters
 ├── figures
 ├── tables
 └── references.bib
```

---

**4️⃣ Test LaTeX once**

Run:

```
pdflatex main.tex
```

or in VS Code:

```
CTRL + ALT + B
```

Make sure **one PDF compiles successfully**.

---

**5️⃣ Create Evidence Tracker**

Create:

```
THESIS_EVIDENCE.md
```

Example:

```
Experiment → Artifact → Chapter
```

This will save you huge time later.

---

# 2️⃣ Final Markdown File (Paste This)

Create file:

```
THESIS_WORKFLOW_MAR_JUN_2026.md
```

Paste this:

---

# THESIS WORKFLOW (March – June 2026)

Master Thesis: **Offline MLOps Pipeline for Human Activity Recognition**

Student: **Shalin Vachheta**

University: **University of Siegen**

Submission Deadline: **1 July 2026**

---

# 1. Thesis Objective

Design and implement an **offline-first MLOps pipeline** for Human Activity Recognition that supports:

* reproducible model training
* monitoring of production predictions
* drift detection
* trigger-based retraining
* containerized deployment
* reproducible experiments

---

# 2. System Pipeline Overview

Pipeline stages implemented in the repository:

```
Stage 0  Data ingestion
Stage 1  Data validation
Stage 2  Data preprocessing
Stage 3  Model training
Stage 4  Model inference
Stage 5  Model evaluation
Stage 6  Monitoring and drift detection
Stage 7  Trigger decision
Stage 8  Retraining pipeline
Stage 9  Model management
Stage 10 Deployment interface
```

---

# 3. Phase Plan

## Phase 1 — Exam Mode

**Now → April 15**

Focus:

* exam preparation
* thesis structure
* documentation
* diagrams
* evidence organization

* bug fixes

Engineering blocked:

* architecture redesign

---

## Phase 2 — Pipeline Finalization
**April 16 → April 30**

* run experiments
* generate artifacts

* clean environment pipeline run
* drift detection experiments
---

## Phase 3 — Thesis Writing

**May 1 → May 31**

Write main thesis chapters.

Focus:

* architecture explanation
* pipeline implementation
* monitoring system
* experiments

---

## Phase 4 — Finalization

**June 1 → June 20**

Tasks:

* editing
* figures
* citations
* formatting

---

## Phase 5 — Defense Preparation

**June 20 → June 30**

Tasks:

* presentation slides
* demo preparation
* defense rehearsal

---

# 4. Weekly Roadmap

## March 16 – March 22

* finalize thesis chapter structure
* create thesis LaTeX project
* build figure inventory
* create evidence tracking file

---

## March 23 – March 29

* draft Chapter 1
* draft system architecture overview
* map repository components to thesis chapters

---

## March 30 – April 5

* prepare pipeline architecture diagrams
* collect Wave 1 and Wave 2 evidence
* update documentation

---

## April 6 – April 15

Exam period.

Tasks:

* finalize architecture diagrams
* prepare experiment plan
* minimal pipeline sanity run if necessary

---

## April 16 – April 22

* run reproducibility pipeline
* validate monitoring pipeline
* verify trigger logic

---

## April 23 – April 30

Run experiments:

* baseline evaluation
* drift detection
* trigger behaviour
* runtime analysis

Export artifacts.

---

## May 1 – May 7

Write:

* dataset description
* preprocessing
* model architecture

---

## May 8 – May 14

Write:

* MLOps pipeline implementation
* DVC usage
* MLflow tracking

---

## May 15 – May 21

Write:

* monitoring system
* drift detection
* trigger policy

---

## May 22 – May 31

Write results chapter.

Include:

* experiment tables
* evaluation plots
* runtime charts

---

## June 1 – June 10

Editing pass.

Fix:

* grammar
* diagrams
* cross references

---

## June 10 – June 20

Finalize:

* bibliography
* appendix
* reproducibility instructions

---

## June 20 – June 30

Defense preparation.

Tasks:

* build presentation slides
* prepare demo pipeline run
* rehearse defense talk

---

# 5. Experiments Required

The thesis requires **five experiments**.

### Experiment 1

Model performance evaluation.

Metrics:

* accuracy
* precision
* recall
* F1 score

---

### Experiment 2

Drift detection validation.

Measure detection sensitivity.

---

### Experiment 3

Prediction monitoring behaviour.

Evaluate:

* confidence
* entropy
* prediction distribution

---

### Experiment 4

Trigger policy evaluation.

Demonstrate retraining trigger logic.

---

### Experiment 5

Pipeline runtime evaluation.

Measure:

* runtime vs dataset size
* resource consumption

---

# 6. Repository Validation Checklist

Pipeline:

* full pipeline executes end-to-end
* artifacts are reproducible

Monitoring:

* drift detection works
* baseline statistics valid

CI/CD:

* tests run successfully
* Docker images build successfully

Documentation:

* README updated
* thesis docs aligned with repo structure

---

# 7. Evidence Tracking

Create mapping between experiments and artifacts.

Example:

| Experiment          | Artifact              | Chapter   |
| ------------------- | --------------------- | --------- |
| Baseline evaluation | MLflow run            | Chapter 7 |
| Drift experiment    | monitoring logs       | Chapter 6 |
| Trigger evaluation  | trigger_decision.json | Chapter 6 |

---

# 3️⃣ Recommended Repo Folder for Thesis Docs

Inside repo:

```
docs/
   thesis_workflow/
```

Store:

```
THESIS_WORKFLOW_MAR_JUN_2026.md
THESIS_EVIDENCE.md
EXPERIMENT_PLAN.md
DEFENSE_PLAN.md
```

---

# 4️⃣ One Last Recommendation

Once this file is created, run Copilot prompt:

```
Audit the repository against THESIS_WORKFLOW_MAR_JUN_2026.md
and identify completed tasks, pending tasks, and risks
for the thesis completion timeline.
```

This makes Copilot **act like a project manager**.

---

If you want, I can also show you something **very powerful for your thesis**:

The **10 diagrams you should create from your repo** that will dramatically improve the quality of your thesis presentation.
  - `black --check`: 53 files re-formatted (`python -m black .`, committed `"style: auto-format with black"`)
  - `isort --check-only src/`: 2 files in `src/monitoring/` had wrong import order — fixed manually (`"style: fix isort import ordering"`)
  - `scripts/find_duplicate_papers.py` — SHA-256 based, never modifies files
  - `reports/repo_audit/ARCHIVE_DUPLICATES_REPORT.md` — 95 duplicate groups, 75 cross-tree, 1 name collision
  - `reports/repo_audit/ARCHIVE_DUPLICATES.csv` — machine-readable detail
  - `reports/repo_audit/ARCHIVE_DUPLICATE_ACTION_PLAN.md` — Bucket A/B/C classification + 3-phase cleanup plan
  - `.gitignore` changed `reports/` → `reports/*` + `!reports/repo_audit/` to track audit outputs
  - `docs/TRIGGER_POLICY_EXPLANATION.md` — new: explains Healthy/Warning/Critical states, why class dominance ≠ retrain, run classification table for 2026-03-06 run
  - `src/evaluate_predictions.py` `analyze_distribution()` — added `distribution_dominance_warning` flag (fires when dominant class > 95 %); returns `_distribution_dominance_warning`, `_dominant_class`, `_dominant_pct` keys
  - `src/entity/artifact_entity.py` `ModelEvaluationArtifact` — new `distribution_dominance_warning: bool = False` field
  - `src/components/model_evaluation.py` — extracts and propagates dominance flag to artifact
  - `src/mlflow_tracking.py` `log_keras_model()` — removed `input_example` from `mlflow.keras.log_model` calls (fixes `input_example.json FileNotFoundError`); signature is still inferred and passed
  - `run_pipeline.py` — added `_print_compact_run_summary()` — ASCII box printed before the detailed summary (Run ID, input source, windows, inference speed, confidence, dominant class, drift, trigger, MLflow, overall)

### Files / Areas Affected

### Why

### Status

### Next

# for 6tgh march morning, 



## 2026-03-06
### Done
- Restructured `docs/` into organized subdirectories: `01_PIPELINE/`, `02_TECH/`, `03_EXPERIMENTS/`, `04_THESIS_WRITING/`, `99_ARCHIVE/`
- Created pipeline stage documentation (stages 01–10)
- Created thesis writing guides, chapter drafts, research Q&A, mentor questions
- Improved CD workflow: added debug endpoints step, robust multi-route smoke test (`/openapi.json` → `/health` → `/api/health` → `/`)
- Created paper catalog (`archive/_index/PAPERS_CATALOG.md`)
- Created `thesis/refs/papers_all/READING_LIST_BY_CHAPTER.md` — chapter-to-paper mapping
- **Fixed Docker build failure**: `docker/Dockerfile.inference` referenced deleted `api/` folder
  - Changed `COPY api/ /app/api/` → `COPY src/ /app/src/`
  - Changed `CMD uvicorn api.main:app` → `CMD uvicorn src.api.app:app`
  - Updated `PYTHONPATH=/app` → `PYTHONPATH=/app:/app/src`
  - Root cause: refactor moved API from `api/` to `src/api/app.py` but Dockerfile was not updated

### Files / Areas Affected
- `src/data/data_validator.py` — moved from `src/`
- `src/data/preprocess_data.py` — moved from `src/`
- `src/data/sensor_data_pipeline.py` — moved from `src/`
- `src/training/train.py` — moved from `src/`
- `src/training/active_learning_export.py` — moved from `src/`
- `src/training/curriculum_pseudo_labeling.py` — moved from `src/`
- `src/inference/run_inference.py` — moved from `src/`
- `src/monitoring/ood_detection.py` — moved from `src/`
- `src/monitoring/robustness.py` — moved from `src/`
- `src/monitoring/sensor_placement.py` — moved from `src/`
- `src/monitoring/trigger_policy.py` — moved from `src/`
- `src/monitoring/wasserstein_drift.py` — moved from `src/`
- `src/deployment/deployment_manager.py` — moved from `src/`
- `src/deployment/mlflow_tracking.py` — moved from `src/`
- `docker/Dockerfile.inference` — fixed COPY path, CMD entrypoint, PYTHONPATH, HEALTHCHECK
- `.github/workflows/cd.yml` — debug step + 60-iteration wait + multi-route smoke test
- `docs/01_PIPELINE/stages/` — 10 new stage documentation files (01–10)
- `docs/02_TECH/guides/` — 8 new operation guides
- `docs/03_EXPERIMENTS/` — evidence pack, threshold calibration summary
- `docs/99_ARCHIVE/` — archived old doc files
- `thesis/_snapshots/` — historical work snapshots (Feb snapshots)
- `thesis/refs/papers_all/01_mlops/` — 18 MLOps PDFs
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

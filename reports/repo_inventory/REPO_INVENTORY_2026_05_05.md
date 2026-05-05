# MLOps Thesis Repository Inventory & Cleanup Audit
**Date:** May 5, 2026
**Scope:** `D:\study apply\ML Ops\MasterArbeit_MLops`
**Audit Type:** Read-only (No files were modified)

## 1. Executive Summary

### Is the repo clean enough for thesis writing?

**Partially — but several categories need attention before submission.**

The core pipeline source code (`src/`, `tests/`, `config/`, `models/raw_physical_baseline.json`, `run_pipeline.py`) is clean, well-structured, and matches the defended 7+3+1 stage architecture. The thesis LaTeX source in `thesis/` is intact. The git-tracked file set (719 files) is reasonable in size.

However, **four significant cleanup risks** exist:

1. **Binary model files are tracked in git** — `models/retrained/*.keras`, `models/registry/har_model_vauto.keras`, `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` (~114 MB total). These should be DVC-only, not git-tracked. They inflate clone size and slow CI.

2. **`stage6_pytest_work/` and `stage7_pytest_work/` are partially tracked** — hundreds of UUID-named test-artifact folders (baseline JSON, monitoring reports, trigger state files) are tracked in git. These are generated test fixtures, not evidence. They pollute `git status` and commit history.

3. **`artifacts/` directory is ~9 GB locally** — contains ~180+ timestamped pipeline run folders, pytest cache dirs (locked/permission-denied), and large CSV/NPY files. All correctly gitignored but physically large and noisy.

4. **`notebooks/` and `nb/` contain very large data files** — `nb/model_artifacts/model.joblib` is ~94 MB, `nb/ADAMSENSE.csv` is ~128 MB, `notebooks/synthetic_labeled.csv` is ~57 MB, and multiple raw CSVs in `nb/` exceed 50 MB each. These are correctly gitignored but represent local clutter.

### What are the main cleanup risks?

| Risk | Severity | Notes |
|------|----------|-------|
| `.keras` files tracked in git (models/retrained, models/registry) | HIGH | Bloat git history; should be DVC only |
| `stage6_pytest_work/` + `stage7_pytest_work/` tracked in git | HIGH | Generated test fixtures, not source code |
| `artifacts/` 9 GB local dir with pytest cache folders (some locked) | MEDIUM | Gitignored correctly but messy locally |
| Root-level clutter markdown files | LOW | Stale worklog/diagnostic files |
| `.pyc` files in `scripts/` and `tests/` | LOW | Should be gitignored completely |
| `nb/model_artifacts/model.joblib` 94 MB and raw CSVs in `nb/` | LOW | Gitignored; local cleanup safe |

### What should not be touched?

- `src/` — entire pipeline source
- `tests/` — test source files (`.py` only, not `.pyc`)
- `config/pipeline_config.yaml` and related config
- `models/raw_physical_baseline.json`, `models/drift_reference.json`, `models/training_baseline.json`, `models/normalized_baseline.json`
- `models/mmd_reference_windows.npy` (~5.5 MB — baseline reference for MMD drift detection)
- `docs/thesis/` — all thesis planning docs
- `docs/` policy and audit docs
- `evidence/final_runtime_freeze_2026_05_05/` — keep entirely
- `evidence/inference_parity_before_fix/` — keep as fix evidence
- `thesis/` — LaTeX chapters and all `.tex`, `.bib`, `.pdf`
- `run_pipeline.py`, `pyproject.toml`, `pytest.ini`, `.github/workflows/`
- `data/codex_synth/` — tracked synthetic data generation manifest and CSV
- `reports/pipeline_runs/` — batch run evidence (keep for thesis)
- `internal/reference/` — tracked reference/explanation docs

---

## 2. Top-Level Tree

```
MasterArbeit_MLops/
├── .dvc/                     DVC configuration (tracked)
├── .dvc_storage/             Local DVC cache (gitignored)
├── .github/workflows/        CI/CD YAML (ci.yml, cd.yml) — tracked
├── .mypy_cache/              Type-check cache — gitignored
├── .pytest_cache/            Pytest cache — gitignored
├── .pytest_tmp/              Pytest temp dirs (locked) — GITIGNORE candidate
├── .tmp_pytest/              More pytest temp (locked) — GITIGNORE candidate
├── .tmp_pytest_current/      More pytest temp (locked) — GITIGNORE candidate
├── .tmp_stage6_pytest_current/ Stage6 temp (locked) — GITIGNORE candidate
├── .qodo/                    Local IDE config — gitignored
├── .vscode/                  VSCode workspace settings — gitignored
├── 27 april meet/            Meeting data dump (CSVs) — gitignored
├── _archive/                 Internal archive — gitignored
├── artifacts/                Pipeline run outputs (~9 GB, ~201 top-level dirs) — gitignored
├── config/                   Pipeline config YAML, requirements, alerts — tracked
├── data/                     DVC-managed data (raw/processed/prepared pointers) — mixed
├── docker/                   Dockerfiles + FastAPI inference server — tracked
├── docs/                     Policy/audit/thesis planning markdown — mostly tracked
├── evidence/                 Runtime freeze evidence snapshots — gitignored
├── har_mlops_pipeline.egg-info/ Python package build artifact — gitignored
├── internal/                 Internal notes, reference docs — partially tracked
├── logs/                     Pipeline run logs — gitignored
├── main/                     Legacy folder (content unclear) — REVIEW
├── mlruns/                   MLflow tracking (~118K files) — gitignored
├── models/                   Model artifacts (DVC + git mixed) — partially tracked
├── nb/                       Jupyter/batch notebooks + large data files — gitignored
├── notebooks/                Experiment notebooks + large CSVs — gitignored
├── notes/                    Local text notes — gitignored
├── outputs/                  Ablation/evaluation outputs — gitignored
├── recording/                Screen recordings or logs — REVIEW
├── reports/                  Evaluation reports, batch run evidence — partially tracked
├── scripts/                  Experiment, analysis, and utility scripts — tracked
├── src/                      Pipeline source code (components/pipeline/monitoring) — tracked
├── stage6_pytest_work/       Stage 6 test artifacts (UUID dirs) — PARTIALLY TRACKED (problem)
├── stage7_pytest_work/       Stage 7 test artifacts (UUID dirs) — PARTIALLY TRACKED (problem)
├── tests/                    Pytest test suite — tracked (pyc files should be gitignored)
├── thesis/                   LaTeX thesis chapters + build files — gitignored (by rule)
├── tmp_run3/                 Temp run folder — REVIEW/CLEANUP
├── run_pipeline.py           Main pipeline entry point — tracked
├── pyproject.toml            Python project config — tracked
├── pytest.ini                Pytest configuration — tracked
├── README.md                 Project README — tracked
├── docker-compose.yml        Docker orchestration — tracked
├── .gitignore                750-line gitignore — tracked
├── .dockerignore             Docker build exclusion — tracked
└── [root-level .md files]    Mix of tracked worklog/diagnostic docs — see §7
```

---

## 3. Git Tracking State

### Summary

| Category | Count | Notes |
|----------|-------|-------|
| Tracked files (`git ls-files`) | 719 | Includes some `.keras` and `.pyc` files — see below |
| Deleted from index (`git status D`) | ~200+ | `stage6_pytest_work/` and `stage7_pytest_work/` files deleted locally but still tracked |
| Untracked, not ignored | ~100+ | Remaining `stage6_pytest_work/` and `stage7_pytest_work/` UUID artifact dirs |

### Key tracked files by category

| Category | Examples |
|----------|---------|
| Source code | `src/**/*.py`, `tests/test_*.py`, `run_pipeline.py` |
| Config | `config/pipeline_config.yaml`, `config/requirements.txt` |
| Models (JSON baselines) | `models/raw_physical_baseline.json`, `models/training_baseline.json`, `models/drift_reference.json` |
| Models (`.keras` — PROBLEM) | `models/retrained/*.keras` (7 files), `models/registry/har_model_vauto.keras` |
| DVC pointers | `data/prepared.dvc`, `data/processed.dvc`, `data/raw.dvc`, `models/pretrained.dvc` |
| Docs | `docs/**/*.md`, `docs/thesis/**/*.md` |
| CI/CD | `.github/workflows/ci.yml`, `.github/workflows/cd.yml` |
| Internal notes | `internal/notes/*.md`, `internal/reference/*.md` |
| Stage pytest work (PROBLEM) | `stage6_pytest_work/**/transformed_baseline.json` (~200 files) |
| Scripts | `scripts/**/*.py` |

### Notable git-tracking issues

1. **`.keras` model binaries in git index** — `models/retrained/*.keras`, `models/registry/har_model_vauto.keras` are tracked directly in git. This contradicts the `.gitignore` entry `models/retrained/*.keras` (which was added _after_ these were staged). They likely need `git rm --cached` treatment.

2. **`stage6_pytest_work/` and `stage7_pytest_work/` in git index** — These UUID-named JSON files were tracked at some point. The local files have since been deleted (shown as `D` in `git status`), but new UUID variants keep appearing as untracked. The whole `stage*_pytest_work/` tree should be gitignored.

3. **`.pyc` files tracked in `tests/` and `scripts/`** — `**/__pycache__/` and `**/*.pyc` appear in `.gitignore` but several pyc files are already in the index. These need `git rm --cached` to fully remove.

### Ignored categories (confirmed by .gitignore)

- `artifacts/` — all pipeline run outputs
- `outputs/` — ablation results
- `mlruns/` — MLflow tracking
- `logs/` — pipeline logs
- `evidence/` — runtime evidence folders (post-recent gitignore update)
- `*.keras`, `*.h5`, `*.npy`, `*.npz`, `*.csv`, `*.pkl`, `*.joblib` — except `data/codex_synth/synthetic_all_users_labeled_v1.csv` (tracked) and `data/samples_2005 dataset/f_data_50hz.csv` (tracked)
- `thesis/` — LaTeX source and build
- `nb/`, `notebooks/` outputs

---

## 4. Large Files Audit

### Files > 100 MB (local, not necessarily git-tracked)

| Path | Size (MB) | Tracked? | Recommendation |
|------|-----------|---------|----------------|
| `nb/ADAMSENSE.csv` | ~128.7 | Gitignored | KEEP_LOCAL_IGNORED |
| `nb/inference_outputs/production_row_predictions.csv` | ~219 | Gitignored | KEEP_LOCAL_IGNORED (or DELETE_IF_NOT_NEEDED) |

### Files > 50 MB (local)

| Path | Size (MB) | Tracked? | Recommendation |
|------|-----------|---------|----------------|
| `nb/2025-08-12-12-09-08_accelerometer.csv` | ~91 | Gitignored | KEEP_LOCAL_IGNORED |
| `nb/2025-08-12-12-09-08_gyroscope.csv` | ~93 | Gitignored | KEEP_LOCAL_IGNORED |
| `nb/2025-08-19-08-58-40_accelerometer.csv` | ~52 | Gitignored | KEEP_LOCAL_IGNORED |
| `nb/2025-08-19-08-58-40_gyroscope.csv` | ~53 | Gitignored | KEEP_LOCAL_IGNORED |
| `nb/model_artifacts/model.joblib` | ~94 | Gitignored | KEEP_LOCAL_IGNORED |
| `nb/all_users_data_labeled.csv` | ~56 | Gitignored | KEEP_LOCAL_IGNORED |
| `notebooks/synthetic_labeled.csv` | ~57 | Gitignored | KEEP_LOCAL_IGNORED |
| `data/codex_synth/synthetic_all_users_labeled_v1.csv` | ~38 | TRACKED | KEEP_TRACKED (small enough, is synthetic reference) |
| `nb/datat/2025-08-12-17-01-38_accelerometer.csv` | ~20 | Gitignored | KEEP_LOCAL_IGNORED |
| `nb/datat/2025-08-12-17-01-38_gyroscope.csv` | ~21 | Gitignored | KEEP_LOCAL_IGNORED |
| `nb/inference_outputs/production_window_predictions.csv` | ~1.4 GB | Gitignored | REVIEW — possibly DELETE_IF_NOT_NEEDED |

### Files > 10 MB (tracked in git — CRITICAL)

| Path | Size (MB) | Recommendation |
|------|-----------|----------------|
| `models/registry/har_model_vauto.keras` | ~5.82 | MOVE_TO_DVC — remove from git index |
| `models/retrained/adabn_tent_adapted_model.keras` | ~5.82 | MOVE_TO_DVC |
| `models/retrained/har_model_latest.keras` | ~5.82 | MOVE_TO_DVC |
| `models/retrained/retrained_model.keras` | ~5.82 | MOVE_TO_DVC |
| `models/retrained/har_model_20260219_123616.keras` | ~3.62 | MOVE_TO_DVC |
| `models/retrained/har_model_20260219_124914.keras` | ~3.62 | MOVE_TO_DVC |
| `models/retrained/pseudo_label_model.keras` | ~2.0 | MOVE_TO_DVC |
| `models/retrained/best_model.keras` | ~0.017 | KEEP_TRACKED (tiny) |
| `models/mmd_reference_windows.npy` | ~5.49 | KEEP_TRACKED (critical baseline reference) |

> **Note:** `models/pretrained/` has a `pretrained.dvc` pointer, which is correct. The problem is `models/retrained/` and `models/registry/` which have live `.keras` files tracked directly.

### artifacts/ directory — local only, ~9 GB

- ~180 timestamped run folders (`20260329_*/`, `20260504_*/`, `20260505_*/`) — pipeline output artifacts
- Several pytest cache dirs inside `artifacts/` (some locked: `pytest-cache-files-*`, `pytest_stage3_tmp`, `_pytest_stage6_tmp`)
- All correctly gitignored
- Physical size warrants periodic pruning of old runs

---

## 5. Cache and Generated File Audit

### Python cache

| Location | Type | Status | Recommendation |
|----------|------|--------|----------------|
| `__pycache__/` (root) | Python bytecode cache | Gitignored | GITIGNORE — safe to delete locally |
| `src/**/__pycache__/` | Python bytecode | Gitignored | GITIGNORE — safe to delete locally |
| `tests/__pycache__/` | Test bytecode | Gitignored | GITIGNORE — safe to delete locally |
| `scripts/__pycache__/` | Scripts bytecode | PARTIALLY in index (`.pyc` files tracked) | Run `git rm --cached scripts/**/*.pyc` |
| `.mypy_cache/` | Type checking cache | Gitignored | Safe to delete locally |
| `.pytest_cache/` | Pytest cache | Gitignored | Safe to delete locally |

### Pytest temporary directories

| Location | Status | Size | Recommendation |
|----------|--------|------|----------------|
| `.pytest_tmp/` | NOT gitignored (only `tmp/` is) | Unknown (locked dirs) | GITIGNORE — add `.pytest_tmp/` explicitly |
| `.tmp_pytest/` | NOT gitignored | Unknown (locked dirs) | GITIGNORE — add `.tmp_pytest/` explicitly |
| `.tmp_pytest_current/` | NOT gitignored | Unknown (locked dirs) | GITIGNORE — add `.tmp_pytest_current/` |
| `.tmp_stage6_pytest_current/` | NOT gitignored | Unknown (locked) | GITIGNORE — add explicitly |
| `artifacts/pytest_stage3_tmp/` | Gitignored (artifacts/) | Unknown (locked) | KEEP_LOCAL_IGNORED |
| `artifacts/_pytest_stage6_tmp/` | Gitignored (artifacts/) | Unknown (locked) | KEEP_LOCAL_IGNORED |

> **Note:** `.pytest_tmp/`, `.tmp_pytest/`, `.tmp_pytest_current/`, `.tmp_stage6_pytest_current/` appear at the root level and are NOT covered by the current `.gitignore`. They have locked subdirectories causing `git status` permission warnings. They must be added to `.gitignore`.

### MLflow

| Location | Status | Recommendation |
|----------|--------|----------------|
| `mlruns/` | Gitignored | KEEP_LOCAL_IGNORED — contains ~118K files, experiment run history |

### Evidence folders

| Location | Status | Recommendation |
|----------|--------|----------------|
| `evidence/final_runtime_freeze_2026_05_05/` | Gitignored (evidence/ rule) | KEEP_LOCAL_IGNORED — critical thesis evidence |
| `evidence/inference_parity_before_fix/` | TRACKED (`evidence/inference_parity_before_fix/config_py_before.py`, `pipeline_config_before.yaml`) | KEEP_TRACKED — pre-fix reference |
| `evidence/inference_parity_all_20260504_*/` | Gitignored | KEEP_LOCAL_IGNORED — parity test evidence |
| `evidence/docs_snapshot/` | Gitignored | KEEP_LOCAL_IGNORED |
| `evidence/pipeline_outputs/` | Gitignored | KEEP_LOCAL_IGNORED |
| `evidence/screenshots/` | Gitignored | KEEP_LOCAL_IGNORED |
| `evidence/verification/` | Gitignored | KEEP_LOCAL_IGNORED |

### Logs

| Location | Status | Recommendation |
|----------|--------|----------------|
| `logs/` (root) | Gitignored | Safe to delete locally after thesis |
| `reports/pipeline_runs/batch_28_full/logs/` | Gitignored (reports/*) | KEEP_LOCAL — thesis batch run evidence |

---

## 6. Notebook and Experiment Audit

### notebooks/

| File | Category | Notes |
|------|----------|-------|
| `data_normalization_demo.ipynb` (1.6 MB) | old experiment | Normalization disabled in final pipeline — historical only |
| `gravity_removal_demo.ipynb` (0.5 MB) | old experiment | Gravity removal not in final pipeline — historical only |
| `27april_model_preprocess_test_OPTIMIZED.ipynb` (0.8 MB) | useful evidence | Preprocessing parity exploration |
| `synthetic_comparison.ipynb` (0.6 MB) | useful evidence | Synthetic vs real data comparison |
| `train_synthetic_production_distribution_comparison.ipynb` | useful evidence | Distribution comparison evidence |
| `data_preprocessing_step1.ipynb` | old experiment | Early pipeline step notebook |
| `from_guide_processing.ipynb` | old experiment | Guide-based preprocessing test |
| `model_inference_diagnostics.ipynb` | useful evidence | Inference diagnostics |
| `production_preprocessing.ipynb` | useful evidence | Production preprocessing test |
| `synthetic_labeled.csv` (~57 MB) | gitignored data | KEEP_LOCAL_IGNORED |
| `_build_notebook.py` | utility script | Notebook build helper |
| `_generate_cloud_v2.py` | utility script | Data generation utility |

### nb/

| File | Category | Notes |
|------|----------|-------|
| `gpt.ipynb` | old experiment | GPT-based exploration notebook |
| `processing.ipynb` | old experiment | Early processing notebook |
| `batch_inference.py` | useful evidence | Batch inference script |
| `INFERENCE_ANALYSIS_REPORT.md` | useful evidence | Inference analysis |
| `gpt explain.md` | historical only | GPT explanation notes |
| `EHB_2025_71.pdf`, `ICTH_16.pdf` | reference papers | Gitignored PDFs |
| `fine_tuned_model_1dcnnbilstm.keras` (~5.8 MB) | gitignored model copy | Duplicate of pretrained model |
| `inference_outputs/` | gitignored | Large CSV outputs |
| `model_artifacts/model.joblib` (~94 MB) | gitignored | Old sklearn model artifact |
| `ADAMSENSE.csv` (~128 MB), multiple raw CSVs | gitignored data | Local raw data copies |

### scripts/ (tracked — important for thesis evidence)

| File | Category | Notes |
|------|----------|-------|
| `build_raw_physical_baseline.py` | thesis-core | Builds defended Stage 6 baseline |
| `build_mmd_reference_windows.py` | thesis-core | Builds MMD reference for drift |
| `build_training_baseline.py` | thesis-core | Stage 6 training baseline builder |
| `run_thesis_ablation_experiments.py` | thesis evidence | Ablation study runner |
| `run_ablation_experiment.py` | thesis evidence | Individual ablation runner |
| `generate_thesis_figures.py` | thesis evidence | Figure generation |
| `generate_chapter4_assets.py` | thesis evidence | Chapter 4 assets |
| `mlops_audit.py` | thesis evidence | Audit script |
| `evaluate_mmd_governance_policy.py` | thesis evidence | MMD governance evaluation |
| `compare_scaler_policies.py` | old experiment | Scaler comparison — historical (scaler removed) |
| `experiment_gravity_aligned_rotation*.py` | old experiment | Gravity removal experiments — historical |
| `debug_stage1_to_stage7_*.py` | historical only | Debug scripts — keep as evidence |
| `run_29_datasets_all_models_pipeline.py` | useful evidence | Cross-dataset pipeline runs |
| `run_batch_raw_and_synthetic.py` | useful evidence | Batch comparison |
| `compare_models_inference.py` | useful evidence | Model comparison |
| `finetune_garmin.py` | useful evidence | Garmin fine-tuning script |
| `*.pyc` files in scripts/ | cleanup candidate | Should be gitignored/deleted |
| `preprocess_qc.py`, `preprocess.py` | utility | QC scripts |
| `audit_artifacts.py` | utility | Artifact audit |
| `analyze_datasets.py` | utility | Dataset analysis |

---

## 7. Markdown/Docs Audit

### Thesis-core docs (keep tracked)

| File | Notes |
|------|-------|
| `docs/thesis/DEFENSE_PLAN.md` | Defense planning |
| `docs/thesis/EXPERIMENT_PLAN.md` | Experiment documentation |
| `docs/thesis/METRIC_DISCLOSURES.md` | Metric transparency |
| `docs/thesis/THESIS_EVIDENCE.md` | Evidence catalogue |
| `docs/thesis/THESIS_WORKFLOW_MAR_JUN_2026.md` | Timeline |
| `docs/thesis/THESIS_WRITING_READINESS.md` | Writing readiness checklist |
| `docs/thesis/THRESHOLD_TRIGGER_JUSTIFICATION.md` | Stage 7 policy justification |
| `docs/thesis/DATAFLOW_MAP_A15.md` | Data flow reference |
| `docs/thesis/thesis_masterplan_v2_FINAL.md` | Master plan |
| `docs/MONITORING_AND_TRIGGER_POLICY.md` | Policy doc for Stage 6-7 |
| `docs/MODEL_PROMOTION_POLICY.md` | Stage 9 registration policy |
| `docs/PIPELINE_STAGE_MAP.md` | Stage map reference |
| `docs/PIPELINE_DATA_FLOW_MAP.md` | Data flow map |
| `docs/RUNTIME_DEPENDENCY_MAP.md` | Dependency map |
| `docs/TRIGGER_POLICY_EXPLANATION.md` | Trigger policy detail |
| `docs/INFERENCE_PARITY_FIX.md` | Inference parity fix record |
| `docs/THESIS_CONSISTENCY_NOTES.md` | Thesis consistency audit notes |
| `docs/MANUAL_STAGE_1_TO_7_AUDIT_GUIDE.md` | Manual audit guide |
| `docs/METRIC_DISCLOSURES.md` | (see thesis/) |

### Audit/evidence docs (keep tracked)

| File | Notes |
|------|-------|
| `docs/DRIFT_INVESTIGATION_2026-04-29.md` | Drift analysis record |
| `docs/COMPONENT_IMPROVEMENT_REVIEW_2026-04-27.md` | Component review |
| `docs/FLEXIBLE_COLUMN_DETECTOR_2026-04-27.md` | Column detector docs |
| `docs/STAGE1_TO_3_CLOSURE_NOTES.md` | Stage closure evidence |
| `docs/pretrained_model_exclusion_report.md` | Pretrained model exclusion |
| `docs/thesis_section_4x_pretrained_analysis.md` | Ch4 analysis notes |
| `docs/4th_meet_20260504.md` | Meeting notes |

### Policy/design docs (keep tracked)

| File | Notes |
|------|-------|
| `docs/SRC_SCRIPTS_CLEANUP_PLAN.md` | Source cleanup plan |
| `docs/SRC_SCRIPTS_OVERLAP_MATRIX.md` | Overlap matrix |
| `docs/SRC_SCRIPTS_RIGOROUS_AUDIT.md` | Rigorous audit |
| `docs/STAGE1_INGESTION_REFACTOR_NOTES.md` | Stage 1 refactor notes |
| `docs/UNLABELED_DATA_MODEL_IMPROVEMENT_GUIDE.md` | Unlabeled data guide |
| `docs/REPO_CLEANUP_PLAN_2026-04-29.md` | Cleanup plan |

### Root-level markdown — mixed status

| File | Category | Status | Recommendation |
|------|----------|--------|----------------|
| `README.md` | thesis-core | Tracked | KEEP |
| `REPRODUCE.md` | thesis-core | Tracked | KEEP |
| `HOW_TO_BUILD_THIS_THESIS_PIPELINE_FROM_SCRATCH.md` | thesis-core | Tracked | KEEP |
| `SUBMISSION_READINESS_SUMMARY.md` | audit | Tracked | KEEP |
| `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md` | audit | Tracked | KEEP |
| `PIPELINE_DIAGNOSTIC_CHECKLIST.md` | audit | Tracked | KEEP |
| `PIPELINE_FASTAPI_DOCKER_EXECUTION_GUIDE.md` | policy | Tracked | KEEP |
| `WORKLOG.md` | historical | Gitignored | KEEP_LOCAL_IGNORED |
| `WORK_2026-04-21.md` | historical | Tracked | MOVE_TO_ARCHIVE (or gitignore) |
| `THESIS_JOURNEY_tillapril.md` | historical | Tracked | MOVE_TO_ARCHIVE |
| `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md` | stale | Tracked | MOVE_TO_ARCHIVE |
| `REFACTOR_ISSUES.md` | stale | Tracked | REVIEW_MANUALLY |
| `orange_audit_closure_plan_2026-04-26.md` | stale | NOT TRACKED (gitignored) | KEEP_LOCAL_IGNORED |
| `PIPELINE_DIAGNOSTIC_CHECKLIST.md` | useful | Tracked | KEEP |
| `pt.md` | unclear | NOT TRACKED | REVIEW_MANUALLY |
| `temp.txt` | temp | NOT TRACKED | DELETE_LOCAL_SAFE |
| `thesis_doc.txt` | notes | NOT TRACKED | REVIEW_MANUALLY |
| `reasoningtxt.txt` | notes | NOT TRACKED | REVIEW_MANUALLY |

### Stale/duplicate docs

| File | Issue | Recommendation |
|------|-------|----------------|
| `orange_audit_closure_plan_2026-04-26.md` | One-time audit, not core | KEEP_LOCAL_IGNORED |
| `THESIS_JOURNEY_tillapril.md` | Historical journey log | MOVE_TO_ARCHIVE |
| `WORK_2026-04-21.md` | Dated work log | MOVE_TO_ARCHIVE |
| `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md` | Stale TODO | MOVE_TO_ARCHIVE |
| `docs/REPO_CLEANUP_PLAN_2026-04-29.md` | Superseded by this doc | KEEP (historical) |
| `docs/SRC_SCRIPTS_SIMPLIFICATION_PLAN.md` + `SRC_VS_SCRIPTS_REVIEW.md` | Near-duplicate | REVIEW_MANUALLY |
| `docs/thesis/EXTERNAL_MLOPS_LINK_REVIEW_2026-04-15.md` | External link review | KEEP |

---

## 8. Runtime Thesis-Core Files

These files directly support the defended pipeline and must not be deleted, moved, or modified without careful review.

### Pipeline entry point
- `run_pipeline.py` — main orchestrator for all 11 stages

### Source code (`src/`)
- `src/pipeline/` — stage orchestration logic
- `src/components/` — stage implementations (ingestion, validation, transformation, inference, evaluation, monitoring, trigger, retraining, registration, baseline_update)
- `src/monitoring/` — drift detection, MMD implementation
- `src/entity/` — config entities and data classes
- `src/trigger_policy.py` — Stage 7 review gate logic (`auto_retrain=false`)
- `src/inference/` — inference preprocessing (raw physical units, no scaler, no normalization)
- `src/api/`, `src/core/`, `src/utils/`, `src/logger/`

### Configuration
- `config/pipeline_config.yaml` — master pipeline configuration (50 Hz, window=200, stride=100, normalization disabled)
- `config/pipeline_overrides.yaml` — override configuration
- `config/mlflow_config.yaml` — MLflow experiment tracking config
- `config/alerts/har_alerts.yml` — Alertmanager rules
- `config/requirements.txt`, `config/requirements-lock.txt`

### Models (baseline and reference files)
- `models/raw_physical_baseline.json` — **Stage 6 raw physical baseline** (critical)
- `models/drift_reference.json` — drift reference statistics
- `models/training_baseline.json` — training distribution baseline
- `models/mmd_reference_windows.npy` — MMD reference windows for drift detection
- `models/pretrained.dvc` — DVC pointer to `models/pretrained/`
- `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` — production inference model (DVC-managed)

### Tests
- `tests/test_stage1_ingestion.py` through `tests/test_stage9_registration.py`
- `tests/test_stage6_monitoring.py` — Stage 6 test
- `tests/test_stage7_trigger.py` — Stage 7 review gate test (auto_retrain=false path)
- `tests/test_trigger_policy.py` — trigger policy contract tests
- `tests/conftest.py` — shared test fixtures

### Docker and deployment
- `docker/Dockerfile.inference` — production inference container
- `docker/Dockerfile.training` — training container
- `docker/api/main.py` — FastAPI inference server
- `docker-compose.yml` — local orchestration

### CI/CD
- `.github/workflows/ci.yml` — CI pipeline
- `.github/workflows/cd.yml` — CD pipeline

### Thesis documents
- `thesis/main.tex` — master LaTeX document
- `thesis/ch1_introduction.tex` through `thesis/ch8_discussion_limitations_roadmap.tex`
- `thesis/appendix_*.tex`
- `thesis/references.bib`
- `docs/thesis/` — all planning and evidence docs

### Evidence (critical)
- `evidence/inference_parity_before_fix/` — tracked pre-fix reference
- `evidence/final_runtime_freeze_2026_05_05/` — local runtime freeze evidence (gitignored)

---

## 9. Files and Folders NOT to Claim as Current Evidence

The following exist in the repo but should not be cited as part of the defended production pipeline.

### Prometheus / Grafana / Alertmanager
- `config/alerts/har_alerts.yml` and `har_alerts_pending.yml` — alerting rules **exist** but Prometheus/Grafana monitoring is **optional/future work** (Stage 11 or roadmap). Acknowledge as roadmap in thesis; do not claim as active deployed monitoring.
- Docker services for Prometheus/Grafana if referenced in `docker-compose.yml` — verify they are optional service definitions.

### Kubernetes / Cloud deployment
- No `k8s/` or `kubernetes/` folder found in this audit. If referenced in any script or doc, mark as future work.

### Stage 11 (Sensor Calibration)
- `tests/test_stage11_calibration.py` — exists and is tested, but Stage 11 is **optional/future work** in the defended pipeline. Cite as extension, not current runtime.
- `scripts/experiment_gravity_aligned_rotation*.py` — gravity removal is **not** in the defended pipeline.

### Old scaler / Z-score experiments
- `models/retrained/scaler_config.json` — tracked in git, but normalization/scaler is **disabled** in the defended inference. This is a historical artifact from experiments.
- `scripts/compare_scaler_policies.py` — scaler comparison experiment, historical.
- `scripts/refit_scaler_train_only.py` — scaler refit, historical.
- `notebooks/data_normalization_demo.ipynb` — normalization demo, historical.

### Old 14-stage or multi-stage architecture docs
- Any doc referencing more than 11 stages is stale. The defended architecture is exactly **7 core + 3 conditional (8-10) + 1 optional (11)**.

### Old retraining / domain adaptation experiments
- `src/domain_adaptation/` — AdaBN, TTA adaptation components. These are **experimental/optional** and not in the 7-stage production runtime. Reference only as experimental extensions.
- `tests/test_adabn.py` — AdaBN test.
- `src/training/` — training pipeline components used by Stage 8-10, not Stage 1-7 runtime inference.
- `models/retrained/adabn_tent_adapted_model.keras` — AdaBN model artifact (historical experiment).
- `scripts/retrain_user_holdout*.py` — user holdout retraining experiments.

### Pseudo-labeling / active learning
- `tests/test_active_learning.py` — active learning component test (experimental).
- `src/components/active_learning/` (if exists) — not in defended pipeline.
- `models/retrained/pseudo_label_model.keras` — pseudo-label experiment artifact.

---

## 10. .gitignore and .dockerignore Audit

### Current .gitignore — strengths

The `.gitignore` is comprehensive (750+ lines). Key correct entries:
- `__pycache__/`, `*.pyc`, `*.pyo` — Python cache
- `artifacts/`, `outputs/`, `mlruns/` — generated outputs
- `logs/` — log files
- `*.keras`, `*.h5`, `*.npy`, `*.npz`, `*.csv`, `*.joblib`, `*.pkl` — data and model binaries
- `data/raw/`, `data/processed/`, `data/prepared/` — DVC-managed data
- `thesis/` — LaTeX source
- `evidence/` — evidence outputs

### .gitignore — gaps and recommended additions

```gitignore
# ---- ADD THESE ----

# Pytest root-level temp directories (currently causing permission warnings in git status)
.pytest_tmp/
.tmp_pytest/
.tmp_pytest_current/
.tmp_stage6_pytest_current/

# Stage pytest work directories (test fixtures, not source code)
stage6_pytest_work/
stage7_pytest_work/

# Python egg info (build artifact)
har_mlops_pipeline.egg-info/

# Temp run directories
tmp_run3/

# Jupyter notebook outputs (ensure all notebook output is stripped)
notebooks/*.html
notebooks/*.pdf

# Local meeting data dumps
"27 april meet"/

# Temp and notes files at root
temp.txt
temp/
reasoningtxt.txt
thesis_doc.txt
pt.md

# DVC local storage
.dvc_storage/

# Already gitignored but verify no accidental track:
# models/retrained/*.keras  <- verify git rm --cached applied
# scripts/**/*.pyc          <- verify git rm --cached applied
```

### .gitignore — potential removals / clarifications

| Current entry | Issue | Recommendation |
|--------------|-------|----------------|
| `reports/*` with `!reports/repo_audit/` | The exception uses wrong path (`repo_audit/` vs `repo_inventory/`) | Fix to `!reports/repo_inventory/` to match actual directory |
| `WORKLOG.md` (explicit ignore) | Good, already there | KEEP |
| `thesis/` (explicit ignore) | Correct — LaTeX source is local only | KEEP |
| `_archive/` | Correct | KEEP |

### Current .dockerignore — assessment

The `.dockerignore` is well-structured. Correctly excludes:
- `.git`, `.dvc`, `.dvc_storage`
- `__pycache__`, `*.pyc`, `.pytest_cache`, `.mypy_cache`
- `logs/`, `data/raw/`, `data/processed/`, `mlruns/`
- `docs/`, `tests/`, `*.ipynb`

**Recommended additions to .dockerignore:**

```dockerignore
# ---- ADD THESE ----

# Root-level temp and work dirs
stage6_pytest_work/
stage7_pytest_work/
.pytest_tmp/
.tmp_pytest/
.tmp_pytest_current/
tmp_run3/
artifacts/
outputs/
evidence/
mlruns/
nb/
notebooks/

# Large root-level markdown worklog files
WORKLOG.md
THESIS_JOURNEY_tillapril.md
WORK_2026-04-21.md
```

---

## 11. Cleanup Recommendations Table

| Path | Type | Risk Level | Recommended Action | Reason |
|------|------|------------|-------------------|--------|
| `models/retrained/*.keras` (7 files, ~114 MB) | Binary models | HIGH | MOVE_TO_DVC (`git rm --cached`) | Tracked in git violating DVC contract; bloat |
| `models/registry/har_model_vauto.keras` | Binary model | HIGH | MOVE_TO_DVC (`git rm --cached`) | Same as above |
| `stage6_pytest_work/` | Test fixtures | HIGH | GITIGNORE + `git rm --cached -r` | Generated test artifacts in git index |
| `stage7_pytest_work/` | Test fixtures | HIGH | GITIGNORE + `git rm --cached -r` | Generated test artifacts in git index |
| `.pytest_tmp/` | Pytest temp | MEDIUM | GITIGNORE | Causing `git status` permission warnings |
| `.tmp_pytest/` | Pytest temp | MEDIUM | GITIGNORE | Causing `git status` permission warnings |
| `.tmp_pytest_current/` | Pytest temp | MEDIUM | GITIGNORE | Causing `git status` permission warnings |
| `.tmp_stage6_pytest_current/` | Pytest temp | MEDIUM | GITIGNORE | Causing `git status` permission warnings |
| `scripts/__pycache__/` + `*.pyc` | Bytecode | MEDIUM | GITIGNORE + `git rm --cached` | `.pyc` files tracked in git index |
| `tests/__pycache__/` + `*.pyc` | Bytecode | MEDIUM | GITIGNORE + `git rm --cached` | Same; pyc files in index |
| `har_mlops_pipeline.egg-info/` | Build artifact | LOW | GITIGNORE | Python package build artifact |
| `tmp_run3/` | Temp | LOW | DELETE_LOCAL_SAFE (after review) | Temporary run directory |
| `temp.txt` | Temp file | LOW | DELETE_LOCAL_SAFE | Temp file at root |
| `reasoningtxt.txt` | Notes | LOW | REVIEW_MANUALLY | Unknown content |
| `thesis_doc.txt` | Notes | LOW | REVIEW_MANUALLY | May contain thesis outline notes |
| `THESIS_JOURNEY_tillapril.md` | Historical log | LOW | MOVE_TO_ARCHIVE | Journey log, not current evidence |
| `WORK_2026-04-21.md` | Historical log | LOW | MOVE_TO_ARCHIVE | Dated work log |
| `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md` | Stale TODO | LOW | MOVE_TO_ARCHIVE | Completed fix register |
| `models/retrained/scaler_config.json` | Historical artifact | LOW | KEEP (small) | Documents removed scaler experiment |
| `models/archive/2026-04-27_model_matrix_*/` | Archive | LOW | KEEP | Model matrix experiment archive |
| `reports/*` (local) | Generated reports | LOW | KEEP_LOCAL_ONLY | Gitignored; batch run evidence |
| `nb/` large CSVs and model.joblib | Local data | LOW | KEEP_LOCAL_IGNORED | Gitignored; large but legitimate |
| `notebooks/data_normalization_demo.ipynb` | Old experiment | LOW | KEEP_LOCAL_ONLY (gitignore status) | Historical but keep locally |
| `notebooks/gravity_removal_demo.ipynb` | Old experiment | LOW | KEEP_LOCAL_ONLY | Historical gravity removal demo |
| `mlruns/` (~118K files) | MLflow tracking | LOW | KEEP_LOCAL_IGNORED | Gitignored; local experiment tracking |
| `artifacts/` (~9 GB) | Pipeline outputs | LOW | KEEP_LOCAL_IGNORED (prune old runs) | Generated; keep recent runs for thesis |
| `src/domain_adaptation/` | Experimental | LOW | KEEP (DO_NOT_TOUCH) | Experimental extension; mark as such |
| `evidence/` | Evidence folders | LOW | KEEP_LOCAL_IGNORED | Correctly gitignored; keep all locally |
| `run_pipeline.py` | Core | — | DO_NOT_TOUCH | Pipeline entry point |
| `src/pipeline/` | Core | — | DO_NOT_TOUCH | Pipeline orchestration |
| `src/components/` | Core | — | DO_NOT_TOUCH | Stage implementations |
| `config/pipeline_config.yaml` | Core | — | DO_NOT_TOUCH | Master config |
| `models/raw_physical_baseline.json` | Core | — | DO_NOT_TOUCH | Stage 6 baseline |
| `models/mmd_reference_windows.npy` | Core | — | DO_NOT_TOUCH | MMD drift reference |
| `tests/test_stage*.py` | Core | — | DO_NOT_TOUCH | Stage test suite |
| `thesis/` | Thesis source | — | DO_NOT_TOUCH | LaTeX chapters |
| `evidence/inference_parity_before_fix/` | Evidence | — | DO_NOT_TOUCH | Pre-fix reference |
| `data/codex_synth/` | Reference data | — | DO_NOT_TOUCH | Synthetic data manifest |

---

## 12. Safe Cleanup Command Plan

> **IMPORTANT:** Do not execute these commands automatically. Review each section carefully before running. All commands are reversible via `git` except local file deletions.

---

### A. Safe Cache Cleanup (no git changes, local only)

```powershell
# Remove Python bytecode caches (safe — regenerated on next run)
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Include "*.pyc","*.pyo" | Remove-Item -Force

# Remove mypy cache (safe — regenerated by mypy)
Remove-Item -Recurse -Force .mypy_cache -ErrorAction SilentlyContinue

# Remove pytest cache (safe — regenerated by pytest)
Remove-Item -Recurse -Force .pytest_cache -ErrorAction SilentlyContinue

# Remove egg-info build artifact (safe — regenerated by pip install -e)
Remove-Item -Recurse -Force har_mlops_pipeline.egg-info -ErrorAction SilentlyContinue
```

---

### B. Safe Local Generated-Output Cleanup

```powershell
# Remove root-level temp text files (REVIEW CONTENTS FIRST)
# Remove-Item temp.txt
# Remove-Item reasoningtxt.txt   # review first

# Remove temporary run directory (REVIEW CONTENTS FIRST)
# Remove-Item -Recurse -Force tmp_run3

# Optional: prune old artifact run folders (KEEP recent 5-10 runs for thesis)
# Only after confirming you have the evidence you need in reports/pipeline_runs/
# Get-ChildItem artifacts -Directory | Sort-Object LastWriteTime | Select-Object -First 50 | Remove-Item -Recurse

# Clear logs (safe if you have what you need in reports/)
# Remove-Item logs\* -Force
```

---

### C. Gitignore Updates

Add to `.gitignore`:

```gitignore
# Pytest root-level temp directories
.pytest_tmp/
.tmp_pytest/
.tmp_pytest_current/
.tmp_stage6_pytest_current/

# Stage pytest work test fixtures
stage6_pytest_work/
stage7_pytest_work/

# Python egg info
har_mlops_pipeline.egg-info/

# Temp run directories at root
tmp_run3/
temp.txt
reasoningtxt.txt
thesis_doc.txt
pt.md

# Fix exception path (currently wrong)
# Change: !reports/repo_audit/
# To:     !reports/repo_inventory/
```

Remove staged files that should be gitignored:

```powershell
# Remove .pyc files from git index (they are already in .gitignore but were tracked before)
git rm --cached -r scripts/__pycache__
git rm --cached -r tests/__pycache__
git rm --cached "scripts/*.pyc" 2>$null

# Remove stage pytest work from git index
git rm --cached -r stage6_pytest_work/
git rm --cached -r stage7_pytest_work/
```

---

### D. Archive Candidates (move to _archive/ or internal/archive/)

```powershell
# Move stale root-level logs to _archive (or delete after review)
# Move-Item THESIS_JOURNEY_tillapril.md _archive\THESIS_JOURNEY_tillapril.md
# Move-Item WORK_2026-04-21.md _archive\WORK_2026-04-21.md
# Move-Item NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md _archive\
```

---

### E. Model Binary DVC Migration (HIGH PRIORITY)

```powershell
# 1. Remove model binaries from git index (they should be DVC-only)
git rm --cached models/retrained/adabn_tent_adapted_model.keras
git rm --cached models/retrained/har_model_20260219_123616.keras
git rm --cached models/retrained/har_model_20260219_124914.keras
git rm --cached models/retrained/har_model_latest.keras
git rm --cached models/retrained/pseudo_label_model.keras
git rm --cached models/retrained/retrained_model.keras
git rm --cached models/registry/har_model_vauto.keras

# 2. Ensure models/retrained/ and models/registry/ are covered by .gitignore
# (The existing entry 'models/retrained/*.keras' should handle this after git rm --cached)

# 3. Optionally track via DVC:
# dvc add models/retrained/har_model_latest.keras
# dvc push
```

---

### F. Do-Not-Delete List

The following must NEVER be deleted or moved without explicit decision:

```
run_pipeline.py
src/
tests/test_stage*.py
tests/test_trigger_policy.py
tests/test_pipeline.py
config/pipeline_config.yaml
config/pipeline_overrides.yaml
models/raw_physical_baseline.json
models/training_baseline.json
models/drift_reference.json
models/mmd_reference_windows.npy
models/pretrained.dvc
evidence/inference_parity_before_fix/
evidence/final_runtime_freeze_2026_05_05/
data/codex_synth/
data/samples_2005 dataset/f_data_50hz.csv
data/prepared.dvc
data/processed.dvc
data/raw.dvc
docs/thesis/
docs/MONITORING_AND_TRIGGER_POLICY.md
docs/MODEL_PROMOTION_POLICY.md
docs/PIPELINE_STAGE_MAP.md
docs/INFERENCE_PARITY_FIX.md
docs/THESIS_CONSISTENCY_NOTES.md
docs/MANUAL_STAGE_1_TO_7_AUDIT_GUIDE.md
thesis/main.tex
thesis/ch*.tex
thesis/references.bib
.github/workflows/
pyproject.toml
pytest.ini
docker/
docker-compose.yml
README.md
REPRODUCE.md
HOW_TO_BUILD_THIS_THESIS_PIPELINE_FROM_SCRATCH.md
scripts/build_raw_physical_baseline.py
scripts/generate_thesis_figures.py
scripts/generate_chapter4_assets.py
scripts/run_thesis_ablation_experiments.py
reports/pipeline_runs/batch_28_full/
reports/pipeline_runs/batch_28_smoke1/
internal/reference/
```

---

*Audit completed: 2026-05-05. This report is read-only — no files were modified, deleted, or moved during audit.*

# Repository Inventory & Cleanup Guide

**Generated:** March 4, 2026  
**Total Repo Size:** ~15.8 GB (excluding `.git/`)

---

## Size Summary (Top Folders)

| Folder | Size (MB) | Files | Verdict |
|--------|-----------|-------|---------|
| `data/` | 7,626 | many | **KEEP** (managed by DVC) |
| `artifacts/` | 5,955 | 1,059 | **CLEAN UP** — keep only latest runs |
| `archive/` | 1,151 | many | **KEEP** — already the archive |
| `.dvc/` | 346 | — | **KEEP** (DVC internals) |
| `.dvc_storage/` | 346 | — | **KEEP** (local DVC cache) |
| `mlruns/` | 243 | 200+ folders | **CLEAN UP** — prune old experiments |
| `.mypy_cache/` | 167 | — | **DELETE** (auto-generated) |
| `outputs/` | 47 | — | **REVIEW** — keep useful, archive rest |
| `logs/` | 46 | 268 | **CLEAN UP** — keep latest few |
| `models/` | 42 | — | **KEEP** (active models) |
| `Thesis_report/` | 38 | — | **KEEP** (thesis LaTeX + docs) |
| `src/` | 29 | — | **KEEP** (core source code) |
| `--auto-install=yes/` | 7 | — | **DELETE** (MiKTeX artifact, accidental) |
| `tests/` | 1.4 | 25+ | **KEEP** (unit/integration tests) |
| `reports/` | 1.3 | — | **KEEP** (generated evidence) |
| `notebooks/` | 0.7 | — | **KEEP** (exploration notebooks) |
| `scripts/` | 0.4 | 25 | **REVIEW** — some may be redundant |
| `docs/` | 0.4 | — | **KEEP** (documentation) |
| `config/` | 0.2 | — | **KEEP** (pipeline config) |
| `images/` | 0.2 | 1 file | **KEEP** (README image) |
| `docker/` | 0.03 | — | **KEEP** (Dockerfiles) |
| `tmp_runtime/` | 0 | 200 dirs | **DELETE** (temp pipeline scratch) |
| `__pycache__/` | 0.05 | — | **DELETE** (Python cache) |
| `.pytest_tmp/` | 0 | — | **DELETE** (empty) |
| `.pytest_cache/` | 0.02 | — | **DELETE** (auto-generated) |

---

## Detailed Inventory

---

### 1. `src/` — Core Source Code  **KEEP**

The heart of the project. Contains the 14-stage MLOps pipeline.

| File/Folder | What It Is | Importance |
|-------------|-----------|------------|
| `__init__.py` | Package init | Essential |
| `config.py` | Central config (paths, constants) | Essential |
| `train.py` | Model training logic (1D-CNN-BiLSTM) | Essential |
| `run_inference.py` | Run model predictions | Essential |
| `preprocess_data.py` | Data preprocessing (windowing, normalization) | Essential |
| `calibration.py` | Temperature scaling, MC Dropout, ECE | Essential |
| `data_validator.py` | Schema/value-range validation | Essential |
| `mlflow_tracking.py` | MLflow experiment tracking | Essential |
| `deployment_manager.py` | Model deployment logic | Essential |
| `model_rollback.py` | Model rollback capability | Essential |
| `ood_detection.py` | Out-of-distribution detection | Essential |
| `robustness.py` | Robustness testing | Essential |
| `wasserstein_drift.py` | Wasserstein drift detection | Essential |
| `sensor_data_pipeline.py` | Sensor data processing | Essential |
| `sensor_placement.py` | Sensor placement analysis | Essential |
| `trigger_policy.py` | Automated retraining trigger | Essential |
| `prometheus_metrics.py` | Prometheus metrics export | Essential |
| `evaluate_predictions.py` | Prediction evaluation | Essential |
| `active_learning_export.py` | Active learning data export | Essential |
| `curriculum_pseudo_labeling.py` | Curriculum + pseudo-label training | Essential |
| `diagnostic_pipeline_check.py` | Pipeline health diagnostics | Useful |
| `exceptions.py` | Custom exceptions | Essential |
| **`core/`** | Core utilities (logger, exception handling) | Essential |
| **`pipeline/`** | Pipeline orchestration (inference_pipeline.py, production_pipeline.py) | Essential |
| **`components/`** | 15 pipeline stage components (ingestion, validation, transformation, inference, evaluation, monitoring, retraining, registration, etc.) | Essential |
| **`entity/`** | Data classes (config_entity.py, artifact_entity.py) | Essential |
| **`api/`** | FastAPI app (app.py) for inference serving | Essential |
| **`utils/`** | Utilities (config_loader, artifacts_manager, temporal_metrics, production_optimizations) | Essential |
| **`logger/`** | Logging setup | Essential |
| **`exception/`** | Exception handling | Essential |
| **`domain_adaptation/`** | AdaBN + TENT domain adaptation | Essential |
| **`Archived(prepare traning- production- conversion)/`** | Old scripts (prepare_training_data.py, etc.) | **MOVE to `archive/`** |

**Action:** Move `src/Archived(...)` to `archive/superseded_code/`.

---

### 2. `config/` — Configuration Files  **KEEP**

| File/Folder | What It Is | Importance |
|-------------|-----------|------------|
| `pipeline_config.yaml` | Main pipeline configuration (14 stages) | Essential |
| `pipeline_overrides.yaml` | Per-environment overrides | Essential |
| `mlflow_config.yaml` | MLflow tracking config | Essential |
| `monitoring_thresholds.yaml` | Monitoring alert thresholds | Essential |
| `requirements.txt` | Python dependencies | Essential |
| `requirements-lock.txt` | Pinned 578-package lock file | Essential |
| `prometheus.yml` | Prometheus scrape config | Essential |
| `alertmanager.yml` | Alertmanager config | Essential |
| `.pylintrc` | Linting rules | Keep |
| `alerts/` | Alert rule files (har_alerts.yml, har_alerts_pending.yml) | Essential |
| `grafana/` | Grafana dashboards + datasources | Essential |

**Action:** None — all files are purposeful.

---

### 3. `tests/` — Test Suite  **KEEP**

25 test files covering all 14 pipeline stages + integration tests. All 225 tests pass.

| File | What It Tests |
|------|--------------|
| `conftest.py` | Shared fixtures |
| `test_active_learning.py` | Active learning export |
| `test_adabn.py` | AdaBN domain adaptation |
| `test_baseline_age_gauge.py` | Baseline age checks |
| `test_baseline_update.py` | Baseline update logic |
| `test_calibration.py` | Temperature scaling, ECE |
| `test_config_loader.py` | Config loading |
| `test_curriculum_pseudo_labeling.py` | Curriculum training |
| `test_data_validation.py` | Data validation |
| `test_drift_detection.py` | Drift detection |
| `test_model_registration_gate.py` | Model registration |
| `test_model_rollback.py` | Model rollback |
| `test_ood_detection.py` | Out-of-distribution detection |
| `test_pipeline_integration.py` | Full pipeline integration |
| `test_preprocessing.py` | Data preprocessing |
| `test_progress_dashboard.py` | Dashboard |
| `test_prometheus_metrics.py` | Prometheus metrics |
| `test_retraining.py` | Retraining logic |
| `test_robustness.py` | Robustness tests |
| `test_sensor_placement.py` | Sensor placement |
| `test_temporal_metrics.py` | Temporal metrics |
| `test_threshold_consistency.py` | Threshold consistency |
| `test_trigger_policy.py` | Trigger policy |
| `test_validation_gate.py` | Validation gate |
| `test_wasserstein_drift.py` | Wasserstein drift |

**Action:** None — all important.

---

### 4. `scripts/` — Helper/Utility Scripts  **REVIEW**

25 scripts for various one-off or recurring tasks.

| File | What It Does | Verdict |
|------|-------------|---------|
| `train.py` | Training entry point | **KEEP** |
| `preprocess.py` | Preprocessing entry point | **KEEP** |
| `preprocess_qc.py` | Quality-check preprocessing | **KEEP** |
| `inference_smoke.py` | Quick inference smoke test | **KEEP** |
| `per_dataset_inference.py` | Run inference on each dataset | **KEEP** |
| `post_inference_monitoring.py` | Post-inference monitoring | **KEEP** |
| `run_tests.py` | Test runner | KEEP (but `pytest` is enough) |
| `run_ab_comparison.py` | A/B model comparison | **KEEP** |
| `analyze_drift_across_datasets.py` | Cross-dataset drift analysis | **KEEP** |
| `benchmark_latency.py` | Latency benchmarking | **KEEP** |
| `benchmark_throughput.py` | Throughput benchmarking | **KEEP** |
| `threshold_sweep.py` | Threshold sweeps for calibration | **KEEP** |
| `trigger_policy_eval.py` | Evaluate trigger policy | **KEEP** |
| `windowing_ablation.py` | Windowing ablation experiment | **KEEP** |
| `build_normalized_baseline.py` | Build normalized baseline | **KEEP** |
| `build_training_baseline.py` | Build training baseline | **KEEP** |
| `regenerate_support_map.py` | Regenerate paper support map | Keep |
| `generate_thesis_figures.py` | Generate thesis figures | **KEEP** |
| `export_mlflow_runs.py` | Export MLflow runs | Keep |
| `audit_artifacts.py` | Audit artifact folders | Keep |
| `extract_papers_to_text.py` | Extract PDF papers to text | Keep |
| `fetch_foundation_papers.py` | Download foundation papers | Keep |
| `verify_prometheus_metrics.py` | Verify Prometheus metrics | Keep |
| `verify_repository.py` | Verify repo integrity | Keep |
| `update_progress_dashboard.py` | Update progress dashboard | Keep |

**Action:** None critical, but `run_tests.py` could be removed (just use `pytest`).

---

### 5. `data/` — Datasets  **KEEP** (DVC-managed)

**7.6 GB** — Largest folder. Managed by DVC.

| Subfolder/File | What It Is | Verdict |
|----------------|-----------|---------|
| `raw/` | 26 recording sessions (accelerometer + gyroscope CSVs from Garmin) | **KEEP** |
| `raw.dvc` | DVC tracking for raw data | **KEEP** |
| `processed/` | Pipeline output (sensor_fused_50Hz.csv) | **KEEP** |
| `processed.dvc` | DVC tracking for processed | **KEEP** |
| `prepared/` | Windowed/normalized data (production_X.npy) | **KEEP** |
| `prepared.dvc` | DVC tracking for prepared | **KEEP** |
| `preprocessed/` | **Empty folder** | **DELETE** |
| `active_learning/` | **Empty folder** | **DELETE** |
| `raw_backup/` | **Duplicate of `raw/`** — same 26 datasets | **DELETE** (saves ~3.8 GB) |
| `all_users_data_labeled.csv` | Labeled dataset (root level) | **KEEP** (or move into `raw/`) |
| `anxiety_dataset.csv` | External anxiety dataset | **KEEP** (or move into `raw/`) |
| `samples_2005 dataset/` | Extra sample dataset (f_data_50hz.csv) | **REVIEW** — move to `archive/` if unused |

**Action:** Delete `raw_backup/` (saves ~3.8 GB!), delete empty `preprocessed/` and `active_learning/`, move loose CSVs into `raw/`.

---

### 6. `models/` — Trained Models  **KEEP**

| Subfolder/File | What It Is | Verdict |
|----------------|-----------|---------|
| `pretrained/` | Pre-trained model (current_model.keras + .tflite) | **KEEP** |
| `pretrained.dvc` | DVC tracking | **KEEP** |
| `trained/` | All training outputs (latest, retrained, adapted models) | **KEEP** |
| `registry/` | Model registry (har_model_vauto.keras + registry JSON) | **KEEP** |
| `retrained/` | **Empty** | **DELETE** |
| `archived_experiments/` | Old experiment (cv_training_20260106/) | **KEEP** or move to `archive/` |
| `normalized_baseline.json` | Drift baseline | **KEEP** |
| `training_baseline.json` | Training baseline | **KEEP** |
| `.gitignore` | Ignore rules | **KEEP** |

**Action:** Delete empty `retrained/`. Optionally move `archived_experiments/` to `archive/`.

---

### 7. `artifacts/` — Pipeline Run Artifacts  **CLEAN UP**

**5.95 GB, 1,059 files** across ~170 timestamped run folders. Each run saves model checkpoints, predictions, configs, etc.

**Action:** Keep only the 3-5 most recent/important runs. Delete or archive the rest. This alone could free **5+ GB**.

---

### 8. `logs/` — Pipeline Logs  **CLEAN UP**

**46 MB, 268 files.** Contains timestamped `.log` files plus subfolders:
- `evaluation/`, `inference/`, `pipeline/`, `preprocessing/`, `trigger/`
- Several `a3_audit_*.txt`, `a4_audit_*.txt`, `a5_audit_*.txt` files (old audit outputs)

**Action:** Keep the latest 5-10 log files. Delete old ones. Delete all `a*_audit_*.txt` files (old, not needed).

---

### 9. `mlruns/` — MLflow Experiment Tracking  **CLEAN UP**

**243 MB, 200+ experiment folders** with random hash names.

**Action:** Keep this if you need experiment history. Otherwise, delete old runs via MLflow UI or `mlflow gc`. At minimum, make sure `.gitignore` excludes this from Git.

---

### 10. `outputs/` — Pipeline Outputs  **REVIEW**

**47 MB.** Contains:
- `batch_analysis/` — Batch processing results
- `calibration/` — Calibration outputs
- `curriculum_training/` — Curriculum training outputs
- `evaluation/` — Evaluation results
- `sensor_placement/` — Sensor placement analysis
- `wasserstein_drift/` — Drift detection outputs
- `gravity_removal_comparison.png` — Comparison plot
- Prediction files (`predictions_*.csv`, `*_probs.npy`, `*_metadata.json`)

**Action:** Keep the subfolders (useful for thesis). Delete old loose prediction files if newer versions exist in subfolders.

---

### 11. `reports/` — Evidence Reports  **KEEP**

Contains thesis-critical evidence:
- Ablation results (CSV, PNG)
- Threshold calibration reports
- Trigger policy evaluations
- Pipeline factsheet, CTO review, gaps analysis
- Paper support map, evidence pack index

**Action:** None — all useful for thesis defense.

---

### 12. `docs/` — Documentation  **KEEP**

| File/Folder | What It Is |
|-------------|-----------|
| `DEFENSE_QA.md` | Defense Q&A preparation |
| `PRODUCT_REVIEW.md` | Product review doc |
| `WHY_BOOK.md` | "Why" explanations |
| `WHY_BY_FILE.md` | Why each file exists |
| `WHY_BY_TECH.md` | Why each technology |
| `YOU_SHOULD_KNOW_BEFORE_MASTER_FILE/` | 10 files: decision register, evidence ledger, references, pipeline Y-explained, etc. |

**Action:** None — useful for understanding/defense.

---

### 13. `notebooks/` — Jupyter Notebooks  **KEEP**

| File | What It Is |
|------|-----------|
| `data_preprocessing_step1.ipynb` | Step 1 preprocessing |
| `from_guide_processing.ipynb` | Processing from guide |
| `production_preprocessing.ipynb` | Production preprocessing |
| `exploration/gravity_removal_demo.ipynb` | Gravity removal demo |
| `README.md` | Notebook docs |

**Action:** None.

---

### 14. `docker/` — Docker Configuration  **KEEP**

| File | What It Is |
|------|-----------|
| `Dockerfile.inference` | Inference container |
| `Dockerfile.training` | Training container |
| `api/main.py` | Docker API entry point |

**Action:** None.

---

### 15. `Thesis_report/` — Thesis LaTeX + Planning  **KEEP**

**38 MB.** Contains the actual thesis document and all planning.

| Subfolder | What It Is |
|-----------|-----------|
| `chapters/` | 6 LaTeX chapter files (ch1-ch6) |
| `appendices/` | 3 appendix LaTeX files |
| `frontmatter/` | Title page, abstract, etc. |
| `refs/` | 15 PDF reference papers + BibTeX |
| `docs/` | Extensive docs (19_Feb, 22Feb audit, stages, technical, thesis, research) |
| `things to do/` | Task tracking (remaining work, knowledge base, work done log) |
| `papers_text/` | Extracted text from papers |
| `thesis_main.tex` | Main LaTeX file |
| `febreport.tex` | February report |
| `22 feb codex/`, `23-5 codex/` | Codex sessions |
| `sample reports/` | Sample report templates |
| `mentor_questions*.md` | Mentor Q&A |
| `Thesis_Plan.md` | Original thesis plan |

**Action:** None — all essential for thesis.

---

### 16. `archive/` — Already Archived Material  **KEEP AS-IS**

**1.15 GB.** This is the archive. Contains:
- `ai_conversations/` — AI chat logs
- `docs_feb2026/` — Old February docs
- `misc_papers/` — Misc papers
- `old_docs/` — Old documentation
- `old_planning_docs/` — Old plans
- `papers/` — Old papers
- `personal_notes/` — Cheat sheets, notes
- `research_papers/` — Research papers
- `scripts_feb2026/` — Old scripts
- `superseded_code/` — Old code (diagnostic check, old pipeline orchestrator, old training scripts)

**Action:** None — this is already the archive.

---

### 17. `.github/` — CI/CD  **KEEP**

Contains `workflows/ci-cd.yml` — weekly model-health check + test suite.

**Action:** None.

---

### 18. Top-Level Files

| File | What It Is | Verdict |
|------|-----------|---------|
| `run_pipeline.py` | **Main entry point** — runs all 14 stages | **KEEP** |
| `pyproject.toml` | Project metadata + dependencies | **KEEP** |
| `setup.py` | Package setup | **KEEP** |
| `pytest.ini` | Pytest config | **KEEP** |
| `docker-compose.yml` | Docker Compose for services | **KEEP** |
| `README.md` | Project README (1,172 lines) | **KEEP** |
| `.gitignore` | Git ignore rules | **KEEP** |
| `.gitattributes` | Git LFS attributes | **KEEP** |
| `.dockerignore` | Docker ignore | **KEEP** |
| `.dvcignore` | DVC ignore | **KEEP** |
| `batch_process_all_datasets.py` | Batch processing script | **MOVE** to `scripts/` |
| `generate_summary_report.py` | Generate batch summary | **MOVE** to `scripts/` |
| `cleanup_repo.ps1` | Repo cleanup script | **KEEP** (useful) |
| `qna explain.md` | Q&A notes | **MOVE** to `archive/` or `docs/` |
| `solution.md` | Solution notes | **MOVE** to `archive/` or `docs/` |
| `tech.md` | Tech notes | **MOVE** to `archive/` or `docs/` |
| `the march todo.md` | March TODO | **KEEP** temporarily |

---

### 19. Folders to DELETE (auto-generated / accidental)

| Folder | Why Delete | Est. Savings |
|--------|-----------|-------------|
| `--auto-install=yes/` | MiKTeX auto-install artifact created by accident | 7 MB |
| `__pycache__/` (root) | Python bytecode cache | 0.05 MB |
| `.mypy_cache/` | MyPy type-checking cache (auto-regenerated) | **167 MB** |
| `.pytest_cache/` | Pytest cache (auto-regenerated) | 0.02 MB |
| `.pytest_tmp/` | Empty temp folder | 0 |
| `tmp_runtime/` | 200 empty temp directories from pipeline runs | 0 |

---

## Recommended Cleanup Actions (Priority Order)

### Immediate (saves ~9+ GB):

| # | Action | Savings |
|---|--------|---------|
| 1 | **Delete `data/raw_backup/`** — exact duplicate of `data/raw/` | ~3.8 GB |
| 2 | **Prune `artifacts/`** — keep only 3-5 latest runs, delete rest | ~5 GB |
| 3 | **Delete `.mypy_cache/`** | 167 MB |
| 4 | **Delete `--auto-install=yes/`** | 7 MB |
| 5 | **Delete `tmp_runtime/`** (empty dirs) | 0 |
| 6 | **Delete `__pycache__/`** (root) | 0.05 MB |
| 7 | **Delete `.pytest_cache/`, `.pytest_tmp/`** | 0 |
| 8 | **Delete `data/preprocessed/`, `data/active_learning/`** (empty) | 0 |
| 9 | **Delete `models/retrained/`** (empty) | 0 |

### Organize (no space savings, cleaner structure):

| # | Action |
|---|--------|
| 10 | Move `batch_process_all_datasets.py` → `scripts/` |
| 11 | Move `generate_summary_report.py` → `scripts/` |
| 12 | Move `qna explain.md`, `solution.md`, `tech.md` → `docs/` or `archive/` |
| 13 | Move `src/Archived(prepare traning- production- conversion)/` → `archive/superseded_code/` |
| 14 | Move `data/all_users_data_labeled.csv`, `data/anxiety_dataset.csv` → `data/raw/` |
| 15 | Move `models/archived_experiments/` → `archive/` |

### Maintenance (ongoing):

| # | Action |
|---|--------|
| 16 | Prune `mlruns/` — delete old experiment runs (saves ~200 MB) |
| 17 | Prune `logs/` — keep only latest 10 logs, delete `a*_audit_*.txt` files |
| 18 | Add `--auto-install=yes/`, `.mypy_cache/`, `__pycache__/`, `.pytest_cache/`, `tmp_runtime/` to `.gitignore` |

---

## Summary

- **Total repo:** 15.8 GB
- **Potential savings:** ~9+ GB (mostly `raw_backup` + old `artifacts`)
- **Essential code:** `src/`, `tests/`, `config/`, `scripts/`, `docker/`, `.github/`
- **Essential data:** `data/raw/`, `data/processed/`, `data/prepared/`, `models/`
- **Essential docs:** `docs/`, `Thesis_report/`, `reports/`, `README.md`
- **Safe to delete:** caches, empty folders, `raw_backup`, old artifacts, `--auto-install=yes/`

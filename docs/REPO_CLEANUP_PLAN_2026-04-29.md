# Repository Cleanup Master Plan - 2026-04-29

Status: planning document only. No files are deleted or moved by this document.

Active cleanup-planning branch: `repo-noise-plan-2026-04-29`

Source state inspected: `audit/stage1-7-manual-check` with manual Stage 1-7 audit
work in progress.

## Goal

Remove repository noise without breaking:

- the production pipeline entry point: `run_pipeline.py`
- the CI path: `.github/workflows/ci.yml`
- the Docker inference path: `docker/Dockerfile.inference`
- the FastAPI serving path: `src/api/app.py`
- the DVC data/model lineage: `.dvc`, `*.dvc`, `.dvcignore`
- the thesis evidence trail needed for defense

The cleanup should reduce working-tree size and visual clutter first. Runtime
code changes are out of scope for this wave.

## Current State Found

### Branch and dirty state

The cleanup branch was created from the current audit branch. The branch name is
flat because slash-nested branch creation failed on this machine due a `.git`
ref lock/permission issue.

Current important working-tree changes before this document:

| Path | Status before cleanup doc | Cleanup implication |
|---|---|---|
| `WORKLOG.md` | modified | Keep; add cleanup-plan entry only. |
| `src/entity/config_entity.py` | modified | Do not touch in this cleanup. |
| `notebooks/model_inference_diagnostics.ipynb` | modified | Do not touch in this cleanup. |
| `data/codex_synth/synthetic_all_users_labeled_v1.csv` | deleted | Accept only if synthetic CSV is regenerable or moved to DVC/archive. |
| `docs/DRIFT_INVESTIGATION_2026-04-29.md` | untracked | Keep; active evidence. |
| `docs/MANUAL_STAGE_1_TO_7_AUDIT_GUIDE.md` | untracked | Keep; active audit guide. |
| `models/drift_reference.json` | untracked | Keep; runtime drift reference. |
| `models/mmd_reference_windows.npy` | untracked | Keep for MMD audit/runtime experiment if MMD mode is used. |
| `models/archive/2026-04-27_model_matrix_cleanup/` | untracked | Keep or move to off-repo archive; do not leave on main long term. |
| `27 april meet/` | untracked | Extract unique notes, then archive/delete duplicate data/model files. |
| root scratch files (`temp.txt`, `pt.md`, `reasoningtxt.txt`, `thesis_doc.txt`, `mlops.docx`) | untracked | Delete or archive after verifying no unique thesis text. |

### Disk footprint by top-level folder

Measured from the working tree on 2026-04-29:

| Path | Size | Decision |
|---|---:|---|
| `artifacts/` | 53,275 MB | Archive latest evidence only; delete old generated run folders. |
| `data/` | 10,985 MB | Keep DVC-managed canonical data; remove duplicate backup/copy locations. |
| `outputs/` | 5,016 MB | Keep thesis plots/evidence; archive/delete old experiment run dumps. |
| `mlruns/` | 3,899 MB | Move local MLflow store off repo or keep only exported summaries. |
| `internal/` | 836 MB | Keep reference docs; move large paper cache off main branch if not tracked. |
| `_archive/` | 464 MB | Delete from repo working tree or move outside repo. |
| `thesis/` | 365 MB | Local thesis workspace; ignored by git, keep out of cleanup commits. |
| `.dvc/` + `.dvc_storage/` | 692 MB | Do not delete for this cleanup. |
| `.mypy_cache/` | 183 MB | Delete; regenerated. |
| `27 april meet/` | 191 MB | Archive notes; delete duplicate data/model copies. |
| `notebooks/` | 139 MB | Delete/move CSV data drops; keep only notebooks with defended value. |
| `reports/` | 118 MB | Keep canonical evidence; delete pytest/temp run logs. |
| `models/` | 112 MB | Keep runtime and registry files; archive duplicate checkpoints. |
| `src/` | 29 MB | Keep unchanged. |
| `logs/` | 26 MB | Keep latest proof logs only; delete old runtime logs. |
| `main/` | 3 MB | Likely stale/misplaced analysis folder; move/archive after review. |
| `scripts/` | 1 MB | No runtime imports from `src`; classify as thesis utilities vs scratch. |
| `tests/` | 1 MB | Keep unchanged. |

## Pipeline Protection Baseline

These observations define what cleanup must not break:

- CI installs `config/requirements.txt`, lints `src/`, runs `pytest tests/`,
  and builds `docker/Dockerfile.inference`.
- Docker inference copies only `src/` and `config/`; it volume-mounts `models/`
  at runtime.
- The production pipeline is `run_pipeline.py` -> `src.pipeline.production_pipeline`.
- Stage 6 monitoring imports `src.monitoring.post_inference_monitor`, not
  `scripts/post_inference_monitoring.py`.
- Stage 10 baseline update imports `src.monitoring.baseline_builder`, not
  `scripts/build_training_baseline.py`.
- Current scan found no active `src/` runtime import from `scripts/`.

Result: pipeline-safe cleanup should focus on generated folders, duplicate
data/model copies, scratch files, old docs, and one-shot scripts. Do not refactor
`src/` in this wave.

## Hard Do-Not-Delete List

Do not delete, move, or rename these in the cleanup branch unless a separate
runtime refactor is planned and tested:

| Path | Why protected |
|---|---|
| `.github/` | CI/CD definitions. |
| `.dvc/`, `.dvcignore`, `data/*.dvc`, `models/pretrained.dvc` | DVC lineage and data/model restore path. |
| `.gitattributes`, `.gitignore`, `.dockerignore`, `.flake8` | Repo behavior and packaging hygiene. |
| `pyproject.toml`, `setup.py`, `pytest.ini` | Install/test configuration. |
| `config/` | Runtime, test, and Docker dependency/config source. |
| `docker/`, `docker-compose.yml` | Inference and local service surface. |
| `run_pipeline.py` | Main thesis pipeline entry point. |
| `src/` | Production code. |
| `tests/` | Regression protection. |
| `README.md`, `REPRODUCE.md`, `WORKLOG.md` | Public entry point, reproduction, and canonical history. |
| `models/pretrained/` | DVC-managed defended runtime model location. |
| `models/normalized_baseline.json`, `models/training_baseline.json`, `models/drift_reference.json`, `models/mmd_reference_windows.npy` | Monitoring/baseline references. |
| `models/registry/model_registry.json` | Registration history. |
| `data/raw/`, `data/processed/`, `data/prepared/` | DVC-managed working data; clean only through DVC-aware process. |
| `data/all_users_data_labeled.csv` | Canonical labeled training/evaluation source. |
| `data/samples_2005 dataset/f_data_50hz.csv` | Tracked sample data. |

## Immediate Safe Deletes

These can be removed first because they are generated or obvious scratch. If the
machine refuses deletion due permissions, close any running shells/editors and
try again.

| Path | Action | Risk |
|---|---|---|
| `.pytest_cache/` | Delete. | None; regenerated. |
| `.pytest_tmp/` | Delete. | None; generated temp data. |
| `.tmp_pytest/` | Delete. | None; generated temp data. |
| `.tmp_pytest_current/` | Delete. | None; generated temp data. |
| `.mypy_cache/` | Delete. | None; regenerated. |
| `tmp_pytest_trigger/` | Delete. | None; generated temp data. |
| `tmp_pytest_trigger2/` | Delete. | None; generated temp data. |
| `tmp_run3/` | Delete. | None; generated temp data. |
| `__pycache__/` and nested `__pycache__/` | Delete. | None; regenerated. |
| `har_mlops_pipeline.egg-info/` | Delete. | None; regenerated by editable install/build. |
| `scripts/temp_dia.py` | Delete. | Low; scratch diagnostic file. |
| `scripts/temp_final.py` | Delete. | Low; scratch diagnostic file. |
| `scripts/temp_pre.py` | Delete. | Low; scratch diagnostic file. |
| `scripts/models_test.py` | Delete after confirming no unique result. | Low; one-off probe. |
| `temp.txt` | Delete after a quick skim. | Low; scratch root note. |
| `reasoningtxt.txt` | Delete after a quick skim. | Low; scratch root note. |
| `thesis_doc.txt` | Delete after a quick skim. | Low; scratch root note. |
| `pt.md` | Move to `internal/archive_candidates/dated_md/` or delete. | Low; root clutter. |
| `notebooks/reports/drift_log.json` | Delete or move to `reports/`. | Low; notebook-local duplicate report. |

## High-Value Archive/Delete Targets

### `artifacts/`

Decision: delete almost all old generated run folders from the working tree.

Reason: this folder is about 53.3 GB and is generated by `ArtifactsManager`.
The pipeline writes to it; the source code does not need old runs to execute.

Recommended execution:

1. Keep only the last 3-5 timestamped runs that are needed as current evidence.
2. Move any thesis-critical run summaries to `reports/pipeline_runs/`.
3. Move older run folders to an external sibling archive, not to `main`:
   `../MasterArbeit_MLops_archive_2026-04-29/artifacts/`.
4. Delete old generated run folders from the repo working tree.

Do not commit `artifacts/` contents. They are already ignored.

### `outputs/`

Decision: keep final plots and small summaries; archive/delete large experiment
run directories.

| Path | Action |
|---|---|
| `outputs/ablation/` (about 4.0 GB) | Archive off-repo after copying final CSV/PNG evidence to `reports/` or `reports/chapter4/`. |
| `outputs/archive/` (about 878 MB) | Move outside repo or delete if duplicated elsewhere. |
| `outputs/experiments/` | Archive outside repo. |
| `outputs/charts_26runs/` | Delete if charts exist in `reports/chapter4/`; otherwise move final charts to `reports/chapter4/`. |
| `outputs/calibration/`, `outputs/evaluation/`, `outputs/monitoring/` | Keep latest current run only; archive old run dumps. |
| root `outputs/*.png` thesis plots | Keep if referenced in thesis; otherwise move to `reports/chapter4/` or `thesis/figures/`. |
| `outputs/pytest-*`, `outputs/pytest-cache*` | Delete. |

### `mlruns/`

Decision: move the local MLflow experiment store outside the repo or keep only
exported summaries.

Reason: `mlruns/` is about 3.9 GB and local-only. The code can create a new
local store. Thesis evidence should be exported as small JSON/CSV/Markdown under
`reports/`.

Recommended execution:

1. Export thesis-critical run IDs and metrics to `reports/mlflow_exports/`.
2. Move `mlruns/` to `../MasterArbeit_MLops_archive_2026-04-29/mlruns/`.
3. Keep `.gitignore` rule for `mlruns/`.

### `data/`

Decision: keep canonical DVC data, remove duplicate local copies.

| Path | Action | Reason |
|---|---|---|
| `data/raw/` | Keep through DVC. | Stage 1 uses raw sensor files. |
| `data/processed/` | Keep through DVC. | Stage 1/2/3 handoff evidence and generated fused files. |
| `data/prepared/` | Keep through DVC. | Scaler/window artifacts. |
| `data/raw_backup/` (about 3.65 GB) | Move off-repo or delete after verifying `data/raw/` and DVC restore. | Duplicate backup. |
| `data/all_users_data_labeled.csv` | Keep. | Canonical labeled dataset. |
| `data/anxiety_dataset.csv` | Move to DVC/off-repo archive unless directly used. | Large standalone data file. |
| `data/synth/`, `data/synthetic_production/` | Archive or DVC; keep only summaries in git. | Generated synthetic data. |
| `data/active_learning/` | Delete if empty. | Empty/generated path. |
| `data/codex_synth/*.md`, manifest/profile JSON | Keep. | Small synthetic generation evidence. |
| `data/codex_synth/synthetic_all_users_labeled_v1.csv` | Accept current deletion only if regenerable from manifest or moved to DVC/archive. | Large generated CSV should not be normal git noise. |

Before deleting any `data/` working file, run:

```powershell
dvc status
dvc pull
git status --short data
```

### `models/`

Decision: keep runtime model/baseline files; archive duplicate checkpoints.

| Path | Action | Reason |
|---|---|---|
| `models/pretrained/` and `models/pretrained.dvc` | Keep. | Defended runtime model path. |
| `models/registry/` | Keep for now. | Registration history and possible Stage 9 evidence. |
| `models/training_baseline.json` | Keep. | Monitoring baseline source. |
| `models/normalized_baseline.json` | Keep even though ignored/untracked. | Stage 6 default drift baseline. |
| `models/drift_reference.json` | Keep. | Drift monitor reference. |
| `models/mmd_reference_windows.npy` | Keep if MMD audit path remains. | MMD reference windows. |
| `models/retrained/*.keras` | Archive old candidates after model registry and promotion policy review. | Multiple checkpoints are not needed for normal runtime. |
| `models/archive/2026-04-27_model_matrix_cleanup/` | Move outside repo or keep as archive-only evidence; do not merge to main as normal source. | Duplicate model binaries. |
| `models/actual model/`, `models/trained/` | Delete if empty. | Empty legacy folders. |

### `notebooks/`

Decision: keep explanatory notebooks, remove data files from notebook folder.

| Path | Action |
|---|---|
| `notebooks/README.md` | Keep. |
| `notebooks/data_preprocessing_step1.ipynb` | Keep if referenced in README/thesis. |
| `notebooks/from_guide_processing.ipynb` | Keep or archive after findings are captured. |
| `notebooks/production_preprocessing.ipynb` | Keep if used for explanation. |
| `notebooks/model_inference_diagnostics.ipynb` | Keep for now; currently modified. |
| `notebooks/exploration/` | Keep if curated; otherwise archive. |
| `notebooks/synthetic_comparison/` | Keep if it regenerates synthetic evidence; otherwise archive. |
| `notebooks/2025-08-12-17-01-38_accelerometer.csv` | Move to `data/raw/` or delete as duplicate. |
| `notebooks/2025-08-12-17-01-38_gyroscope.csv` | Move to `data/raw/` or delete as duplicate. |
| `notebooks/synthetic_all_users_labeled_v1.csv` | Delete/move to DVC archive; not notebook material. |
| `notebooks/synthetic_labeled.csv` | Delete/move to DVC archive; not notebook material. |
| `notebooks/27april_model_preprocess_test*.ipynb/.py` | Archive after findings are captured in `docs/` or `WORKLOG.md`. |

### `reports/`

Decision: preserve canonical thesis evidence, delete test temp folders and
one-off logs after summaries are retained.

Keep:

- `reports/repo_audit/`
- `reports/chapter4/`
- `reports/pipeline_runs/` latest/canonical evidence
- `reports/ABLATION_WINDOWING.*`
- `reports/THRESHOLD_CALIBRATION.*`
- `reports/TRIGGER_POLICY_EVAL.*`
- `reports/DECISION_REGISTER.csv`
- `reports/MODEL_IMPROVEMENT_ASSESSMENT_2026-04-27.md`
- `reports/PRODUCTION_SYNTHETIC_EVALUATION_2026-04-27.txt`
- `reports/SYNTHETIC_PRODUCTION_DATASET_REPORT_2026-04-27.md`
- `reports/VERIFICATION_SUMMARY_2026-04-27.md`
- `reports/governance_matrix_2026-04-27.*`
- `reports/model_promotion_gate_2026-04-27.*`
- `reports/P0-06_*`

Delete or archive:

- `reports/pytest-*`
- `reports/pytest_*`
- `reports/tmp/`
- `reports/tmp_run2/`
- `reports/_smoke_29_runner*.csv`
- `reports/_tmp_matrix.csv`
- `reports/_tmp_per_class.csv`
- `reports/uvicorn_*.log`
- hash-named full pytest output folders

### Root files

Decision: root should contain only public entry points, build/config files, and
the worklog.

Keep at root:

- `README.md`
- `REPRODUCE.md`
- `WORKLOG.md`
- `run_pipeline.py`
- `pyproject.toml`
- `setup.py`
- `pytest.ini`
- `.gitignore`, `.gitattributes`, `.dockerignore`, `.dvcignore`, `.flake8`
- `docker-compose.yml`

Move to `docs/` or `internal/archive_candidates/dated_md/`:

| File | Action |
|---|---|
| `HOW_TO_BUILD_THIS_THESIS_PIPELINE_FROM_SCRATCH.md` | Move to `docs/BUILD_FROM_SCRATCH.md`. |
| `PIPELINE_FASTAPI_DOCKER_EXECUTION_GUIDE.md` | Move to `docs/EXECUTION_GUIDE.md`. |
| `PIPELINE_DIAGNOSTIC_CHECKLIST.md` | Move to `docs/DIAGNOSTIC_CHECKLIST.md`. |
| `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md` | Archive; dashboard is now in `WORKLOG.md`. |
| `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md` | Archive; dashboard is now in `WORKLOG.md`. |
| `orange_audit_closure_plan_2026-04-26.md` | Archive. |
| `REFACTOR_ISSUES.md` | Archive unless still active. |
| `SUBMISSION_READINESS_SUMMARY.md` | Archive. |
| `THESIS_JOURNEY_tillapril.md` | Archive. |
| `WORK_2026-04-21.md` | Archive because `WORKLOG.md` is canonical. |
| `dataset_comparison_analysis.ipynb` | Move to `notebooks/exploration/` or archive. |
| `pipeline_1.png`, `pieline_2.png` | Move to `docs/images/` if unique; delete if duplicated. |
| root PDFs (`feature engineering.pdf`, `mlops pipeline.pdf`, `ppt help.pdf`, `Mlops_Shalin_index.pdf`, `thesis_report_index_blueprint*.pdf`, `thesis_technology_handbook.pdf`) | Move to `thesis/refs/`, `thesis/_snapshots/`, or off-repo archive. |

Delete after skim:

- `temp.txt`
- `reasoningtxt.txt`
- `thesis_doc.txt`
- `mlops.docx` if superseded by PDFs/Markdown

### `docs/`

Decision: keep active architecture/audit docs; archive superseded script audits.

Keep:

- `docs/REPO_CLEANUP_PLAN_2026-04-29.md`
- `docs/DRIFT_INVESTIGATION_2026-04-29.md`
- `docs/DRIFT_INVESTIGATION_CHAT_2026-04-29.txt`
- `docs/MANUAL_STAGE_1_TO_7_AUDIT_GUIDE.md`
- `docs/MODEL_PROMOTION_POLICY.md`
- `docs/PIPELINE_DATA_FLOW_MAP.md`
- `docs/PIPELINE_STAGE_MAP.md`
- `docs/RUNTIME_DEPENDENCY_MAP.md`
- `docs/STAGE1_INGESTION_REFACTOR_NOTES.md`
- `docs/THESIS_CONSISTENCY_NOTES.md`
- `docs/TRIGGER_POLICY_EXPLANATION.md`
- `docs/thesis/`
- `docs/images/`

Archive to `internal/archive_candidates/dated_docs/` after this plan is
approved:

- `docs/COMPONENT_IMPROVEMENT_REVIEW_2026-04-27.md`
- `docs/FLEXIBLE_COLUMN_DETECTOR_2026-04-27.md`
- `docs/SRC_SCRIPTS_CLEANUP_PLAN.md`
- `docs/SRC_SCRIPTS_OVERLAP_MATRIX.md`
- `docs/SRC_SCRIPTS_RIGOROUS_AUDIT.md`
- `docs/SRC_SCRIPTS_SIMPLIFICATION_PLAN.md`
- `docs/SRC_VS_SCRIPTS_REVIEW.md`
- `docs/pretrained_model_exclusion_report.md`
- `docs/thesis_section_4x_pretrained_analysis.md`
- `docs/UNLABELED_DATA_MODEL_IMPROVEMENT_GUIDE.md` after checking whether the
  2026-04-29 drift investigation supersedes it.

### `scripts/`

Decision: no runtime code imports scripts today, so script cleanup cannot break
the production pipeline directly. The risk is thesis reproducibility. Classify
by evidence value.

Keep until thesis/evidence freeze:

- `scripts/__init__.py`
- `scripts/mlops_audit.py`
- `scripts/refit_scaler_train_only.py`
- `scripts/build_mmd_reference_windows.py`
- `scripts/calibrate_drift_monitor.py`
- `scripts/calibrate_mmd_thresholds.py`
- `scripts/build_governance_matrix.py`
- `scripts/run_model_promotion_gate.py`
- `scripts/compare_train_vs_prod_distribution.py`
- `scripts/experiment_gravity_aligned_rotation.py`
- `scripts/experiment_gravity_aligned_rotation_v2.py`
- `scripts/generate_chapter4_assets.py`
- `scripts/generate_thesis_figures.py`
- `scripts/run_thesis_ablation_experiments.py`
- `scripts/windowing_ablation.py`
- `scripts/threshold_sweep.py`
- `scripts/trigger_policy_eval.py`

Archive after outputs are captured:

- `scripts/analyze_drift_across_datasets.py`
- `scripts/batch_inference_all_sessions.py`
- `scripts/batch_process_all_datasets.py`
- `scripts/compare_mmd_branch_results.py`
- `scripts/compare_models_inference.py`
- `scripts/compare_models_new_session.py`
- `scripts/compare_scaler_policies.py`
- `scripts/debug_stage1_to_stage7_hand_tapping_collapse.py`
- `scripts/evaluate_mmd_governance_policy.py`
- `scripts/evaluate_mmd_staged_policy.py`
- `scripts/evaluate_paired_windows.py`
- `scripts/evaluate_user_holdout.py`
- `scripts/forensic_investigation.py`
- `scripts/generate_synthetic_data.py`
- `scripts/per_dataset_inference.py`
- `scripts/rebuild_paired_windows.py`
- `scripts/retrain_user_holdout.py`
- `scripts/retrain_user_holdout_fast.py`
- `scripts/run_29_datasets_all_models_pipeline.py`
- `scripts/run_ab_comparison.py`
- `scripts/run_ablation_experiment.py`
- `scripts/run_all_datasets_all_models.py`
- `scripts/run_batch_raw_and_synthetic.py`
- `scripts/test_all_models.py`
- `scripts/test_all_models_full.py`
- `scripts/test_gravity_removal.py`
- `scripts/unify_scalars.py`

Delete:

- `scripts/temp_dia.py`
- `scripts/temp_final.py`
- `scripts/temp_pre.py`
- `scripts/models_test.py`

Keep `scripts/archive/` as historical evidence only, or move it to
`internal/archive_candidates/scripts_legacy/` if the goal is a cleaner active
`scripts/` folder.

### `main/`

Decision: archive after review.

Reason: the repo root already has the actual project. This folder looks like a
misplaced analysis workspace (`main/data_comparison/`, `main/README.md`,
`main/data_intelligence_audit.ipynb`).

Action:

1. Confirm no thesis references depend on `main/data_comparison/*`.
2. Move unique CSV/PNG/JSON evidence to `reports/data_comparison/`.
3. Move notebook to `notebooks/exploration/` or archive.
4. Delete `main/`.

### `internal/`, `thesis/`, `_archive/`, `notes/`

Decision: do not treat these as runtime. Clean for human navigation only.

| Path | Action |
|---|---|
| `internal/reference/`, `internal/workflow/`, `internal/writing/` | Keep curated reference material. |
| `internal/papers/` | Move off-repo or keep local-only; not needed by CI/runtime. |
| `internal/archive_candidates/` | Use as the staging location for old docs/scripts. |
| `notes/` | Merge unique items into `WORKLOG.md` or `internal/notes/`, then delete duplicate root notes. |
| `_archive/` | Move outside repo or delete after unique material is accounted for. |
| `thesis/` | Leave local-only; do not include in cleanup commits unless thesis packaging is requested. |

## Execution Waves

### Wave 0 - Documentation only

Current wave. Create this cleanup plan and add a worklog entry. No destructive
actions.

### Wave 1 - Safe generated noise

Delete caches, pytest temp dirs, bytecode, egg-info, empty temp dirs, root scratch
notes, and `scripts/temp_*.py`.

Verification:

```powershell
pytest tests/ -m "not slow and not integration"
python -m py_compile run_pipeline.py
```

### Wave 2 - Heavy generated run folders

Archive/delete `artifacts/`, old `outputs/`, local `mlruns/`, old `logs/`.
This should reclaim most of the working-tree size without touching source code.

Verification:

```powershell
python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger --continue-on-failure
pytest tests/ -m "not slow and not integration"
```

### Wave 3 - Documentation consolidation

Move root Markdown/PDF/image clutter into `docs/`, `thesis/refs/`,
`thesis/_snapshots/`, or `internal/archive_candidates/`.

Verification:

```powershell
git status --short
rg -n "HOW_TO_BUILD_THIS_THESIS_PIPELINE_FROM_SCRATCH|PIPELINE_DIAGNOSTIC_CHECKLIST|WORK_2026-04-21" README.md docs internal WORKLOG.md
```

### Wave 4 - Script pruning

Delete scratch scripts and move one-shot experiment scripts to archive after
their outputs are in `reports/`.

Verification:

```powershell
rg -n "from scripts|import scripts|scripts\\." src run_pipeline.py tests config docker .github
pytest tests/ -m "not slow and not integration"
```

### Wave 5 - Data/model archive

Move duplicate model/data copies off repo. Do this last because this is where
lineage mistakes are easiest.

Verification:

```powershell
dvc status
python run_pipeline.py --stages inference evaluation monitoring trigger --skip-ingestion --skip-validation
docker compose build inference
```

## Guardrails To Add After Cleanup

Add or verify `.gitignore` coverage:

```gitignore
.pytest_tmp/
.tmp_pytest*/
tmp_pytest*/
tmp_run*/
*.egg-info/
__pycache__/
.mypy_cache/
artifacts/
mlruns/
outputs/archive/
outputs/pytest*/
logs/
_repo_cleanup_quarantine/
```

Add a simple review rule before committing cleanup changes:

- If a file is in `src/`, `tests/`, `config/`, `docker/`, `.github/`, or DVC
  metadata: require explicit review and tests.
- If a file is over 5 MB: do not commit it unless it is a documented tracked
  sample, a DVC pointer, or a deliberate thesis artifact.
- If a script is moved/deleted: run the `rg "from scripts|import scripts"`
  check and record the result in the commit message.
- If data/model files are moved: run `dvc status` and document the archive
  location.

## Final Recommendation

The safest cleanup that removes the most noise is:

1. Delete generated caches/temp folders and scratch files.
2. Move `artifacts/`, most of `outputs/`, `mlruns/`, `_archive/`, and
   `data/raw_backup/` outside the repo.
3. Keep `src/`, `tests/`, `config/`, `docker/`, `.github/`, DVC metadata, and
   runtime model/baseline files unchanged.
4. Consolidate root docs into `docs/` or `internal/archive_candidates/`.
5. Prune scripts only after their outputs are captured in `reports/`.

This should remove tens of GB of working-tree noise while keeping the pipeline,
CI, Docker, API, and thesis evidence path intact.

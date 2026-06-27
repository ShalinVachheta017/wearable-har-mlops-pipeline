# Repository Cleaning Plan

This plan is a cleanup guide only. It does not delete, move, rename, or rewrite anything. The goal is to make the repository easier to defend, reproduce, and hand over without losing thesis evidence, final model artifacts, or mentor-review history.

## 1 Executive Summary

The repository is useful but currently very heavy. The main reason is not bad code; it is that the repo contains final thesis material, older thesis drafts, raw and processed data, DVC storage, model artifacts, MLflow runs, generated pipeline outputs, screenshots, caches, and large archive folders in the same working tree.

Recommended cleanup priority:

| Area | Action | Risk | Reason |
|---|---|---:|---|
| Final thesis source and PDF | DO NOT TOUCH | CRITICAL | This is the submission/defense material. |
| Active runtime model D1 | DO NOT TOUCH | CRITICAL | Current pipeline and API use this model contract. |
| Defended run `20260528_122625` | DO NOT TOUCH | CRITICAL | This is the main reproducibility evidence. |
| DVC pointer files | DO NOT TOUCH | CRITICAL | These describe tracked data/model/artifact state. |
| Data folders | KEEP BUT DOCUMENT | HIGH | Needed for reproducibility, but too large for normal Git use. |
| MLflow runs | KEEP BUT DOCUMENT | MEDIUM | Useful audit trail, but many runs are not final. |
| Old outputs and repeated run folders | ARCHIVE | MEDIUM | Useful history, but not needed in the clean root. |
| Caches, build files, temp files | DELETE LATER AFTER CONFIRMATION | LOW | Generated files can be recreated. |
| `_archive/` | NEEDS MANUAL CHECK | HIGH | Very large and already contains older moved material. |

The clean repository should keep the final pipeline, final thesis, final runtime contract, defended artifacts, reproducibility docs, tests, Docker files, and selected reports. Everything else should be archived after confirmation and backup.

## 2 Safety Rules Before Cleanup

1. Do not delete anything before the thesis defense unless it is clearly generated cache.
2. Do not rename thesis figures, appendix files, model folders, or artifact folders before defense.
3. Do not touch `thesis/main.pdf`, `thesis/main.tex`, chapter files, appendix files, or `thesis/references.bib` during cleanup.
4. Do not touch `models/runtime_contract/model_d1_final_20260528/`.
5. Do not touch `artifacts/20260528_122625/` or `artifacts/20260528_122625.dvc`.
6. Do not touch DVC files until a full backup exists.
7. Do not clean `_archive/` casually. It is large, but it may contain old evidence.
8. Do not remove notebooks until the final model source notebook/script is clearly documented.
9. Before any real cleanup, create an external backup or zip of the full repo.
10. After cleanup, rebuild the thesis PDF and run the pipeline smoke tests.

## 3 Suggested Archive Structure

Use a separate external archive location, not the active repo root, for large historical material.

Recommended structure:

```text
repo_archive_before_defense/
  thesis_old_drafts/
  thesis_raw_screenshots/
  old_pipeline_runs/
  old_mlflow_runs/
  old_notebook_artifacts/
  old_model_experiments/
  old_data_extras/
  internal_planning/
  cache_and_build_files/
```

Inside the active repository, keep `_archive/` only if it is intentionally needed. Right now `_archive/` is very large and should be reviewed after defense.

## 4 Folder-by-Folder Audit

| Path | Action | Risk | Notes |
|---|---|---:|---|
| `.git/` | DO NOT TOUCH | CRITICAL | Git history and refs. It is large but must not be manually edited. |
| `.github/` | KEEP | LOW | CI workflow and workflow README. |
| `.dvc/` | DO NOT TOUCH | CRITICAL | DVC metadata/cache. Needed if DVC-tracked data/artifacts must be restored. |
| `.dvc_storage/` | DO NOT TOUCH | CRITICAL | Local DVC storage. Back up before any cleanup. |
| `.codex/`, `.agents/`, `.claude/` | KEEP BUT DOCUMENT | MEDIUM | Local assistant/tool metadata. Not central to thesis, but may support current workflow. |
| `.vscode/` | KEEP BUT DOCUMENT | LOW | Local editor settings. Can be excluded later if not needed. |
| `.mypy_cache/` | DELETE LATER AFTER CONFIRMATION | LOW | Generated type-check cache. |
| `.pytest_tmp/`, `.pytest_tmp_audit/` | DELETE LATER AFTER CONFIRMATION | LOW | Test temp folders. One audit folder had permission issues, so clean carefully. |
| `__pycache__/`, `src/**/__pycache__/`, `tests/**/__pycache__/` | DELETE LATER AFTER CONFIRMATION | LOW | Python-generated cache. |
| `artifacts/` | KEEP BUT DOCUMENT | HIGH | Contains final defended run and many older runs. Keep final run, archive older runs later. |
| `config/` | KEEP | HIGH | Pipeline, MLflow, requirements, and alert configs. |
| `data/` | KEEP BUT DOCUMENT | HIGH | Large raw/processed/prepared data. Should be DVC-managed, not normal Git-managed. |
| `docker/` | KEEP | MEDIUM | Training and inference Dockerfiles. Important for reproducibility story. |
| `docs/` | KEEP BUT DOCUMENT | MEDIUM | Useful documentation, but some docs may be stale. |
| `evidence/` | KEEP BUT DOCUMENT | HIGH | Defense and runtime evidence. Archive only after defense. |
| `har_mlops_pipeline.egg-info/` | DELETE LATER AFTER CONFIRMATION | LOW | Generated packaging metadata. |
| `images/` | NEEDS MANUAL CHECK | MEDIUM | Check whether any thesis or docs still reference these files. |
| `internal/` | ARCHIVE | MEDIUM | Planning and private working notes. Keep until defense, then archive outside repo. |
| `logs/` | KEEP BUT DOCUMENT | MEDIUM | Keep defended pipeline result log; archive repeated logs later. |
| `mlruns/` | KEEP BUT DOCUMENT | MEDIUM | MLflow audit trail. Export/index important runs before trimming. |
| `models/` | KEEP BUT DOCUMENT | HIGH | Active D1 model must stay. Older models can be archived only after confirmation. |
| `nb/` | ARCHIVE | MEDIUM | Older notebook/artifact area. Check references before moving. |
| `notebooks/` | KEEP BUT DOCUMENT | HIGH | Final model notebook/script and generated artifacts are part of model history. |
| `outputs/` | ARCHIVE | MEDIUM | Generated outputs. Keep only if directly cited or needed for defense. |
| `recording/` | ARCHIVE | LOW | Not needed for final clean repo unless used in defense. |
| `reports/` | KEEP BUT DOCUMENT | HIGH | Thesis evidence CSV/PNG files should remain. |
| `scripts/` | KEEP BUT DOCUMENT | MEDIUM | Some scripts generate thesis figures/evidence. Some diagnostics can be archived later. |
| `src/` | KEEP | CRITICAL | Main MLOps pipeline and API code. |
| `tests/` | KEEP | HIGH | Needed to verify cleanup did not break behavior. |
| `thesis/` | DO NOT TOUCH | CRITICAL | Main report, figures, references, appendices, and final PDF. |
| `tmp/` | DELETE LATER AFTER CONFIRMATION | LOW | Temporary files, after checking no active work is stored there. |
| `_archive/` | NEEDS MANUAL CHECK | HIGH | Already very large. Review after defense and move externally if possible. |

## 5 Thesis Folder Cleanup Plan

Main thesis material:

| File/Folder | Action | Risk | Notes |
|---|---|---:|---|
| `thesis/main.tex` | DO NOT TOUCH | CRITICAL | Main LaTeX entrypoint. |
| `thesis/main.pdf` | DO NOT TOUCH | CRITICAL | Current final PDF output. |
| `thesis/chapters/` | DO NOT TOUCH | CRITICAL | Chapter source files. |
| `thesis/appendices/` | DO NOT TOUCH | CRITICAL | Appendix source files. Appendix naming is not perfectly clean, but it works. |
| `thesis/references.bib` | DO NOT TOUCH | CRITICAL | Bibliography source. |
| `thesis/figures/` | DO NOT TOUCH | HIGH | Current thesis figures. Do not rename before defense. |
| `thesis/tables/` | KEEP | HIGH | Thesis tables. |
| `thesis/build_thesis.ps1` | KEEP | MEDIUM | Build helper. |
| `thesis/cited_papers/` | KEEP BUT DOCUMENT | MEDIUM | Useful reference evidence. |
| `thesis/papers_to_read/` | ARCHIVE | MEDIUM | Very large reading folder. Keep outside clean repo after references are finalized. |
| `thesis/draw.io/` | KEEP BUT DOCUMENT | MEDIUM | Diagram sources. Keep `.drawio`; archive duplicate exports later. |
| `thesis/webui+mlops images/` | ARCHIVE | MEDIUM | Raw screenshot staging. Keep until copied figures are verified. |
| `thesis/chnage suggested by mentor/main_UO.pdf` | ARCHIVE | MEDIUM | Mentor review version. Keep as review evidence, not active final report. |
| `thesis/21 june final.pdf` | DELETE LATER AFTER CONFIRMATION | LOW | Appears to duplicate `thesis/main.pdf`; confirm visually before deleting. |
| `thesis/with smoothed,mlflow and webui ss no mentor chnages.pdf` | ARCHIVE | LOW | Older draft/export. |
| LaTeX build files: `.aux`, `.log`, `.toc`, `.out`, `.lof`, `.lot`, `.fls`, `.fdb_latexmk`, `.bbl`, `.blg` | DELETE LATER AFTER CONFIRMATION | LOW | Generated by LaTeX. Delete only after final PDF rebuild succeeds. |

Important appendix note:

- The report currently uses Appendix E for the system walkthrough material.
- Some figure names still contain `fig_appF_*`. This is only a file-name history issue.
- Do not rename those files before defense because LaTeX references may depend on them.
- There is no need to create a new Appendix F unless the thesis structure actually requires it.

## 6 Code Folder Cleanup Plan

Core code to keep:

| Path | Action | Risk | Notes |
|---|---|---:|---|
| `run_pipeline.py` | KEEP | CRITICAL | Main pipeline entrypoint. |
| `src/pipeline/production_pipeline.py` | KEEP | CRITICAL | Main pipeline orchestration. |
| `src/pipeline/pipeline_stage_registry.py` | KEEP | HIGH | Stage mapping. |
| `src/pipeline/pipeline_safety.py` | KEEP | HIGH | Runtime checks and safety behavior. |
| `src/pipeline/pipeline_mlflow_logger.py` | KEEP | HIGH | MLflow logging integration. |
| `src/pipeline/pipeline_input_resolver.py` | KEEP | HIGH | Input selection and validation support. |
| `src/pipeline/pipeline_context.py` | KEEP | HIGH | Shared pipeline state. |
| `src/pipeline/pipeline_console_reporter.py` | KEEP | MEDIUM | CLI reporting. |
| `src/pipeline/pipeline_config_factory.py` | KEEP | HIGH | Config construction. |
| `src/pipeline/pipeline_chunked_drift.py` | KEEP | MEDIUM | Drift-related support. |
| `src/pipeline/pipeline_artifact_writer.py` | KEEP | HIGH | Artifact writing. |
| `src/components/data_ingestion.py` | KEEP | CRITICAL | Stage 1. |
| `src/components/data_validation.py` | KEEP | CRITICAL | Stage 2. |
| `src/components/data_transformation.py` | KEEP | CRITICAL | Stage 3. |
| `src/components/model_inference.py` | KEEP | CRITICAL | Stage 4 and active model loading. |
| `src/components/model_evaluation.py` | KEEP | HIGH | Evaluation/reporting. |
| `src/components/post_inference_monitoring.py` | KEEP | HIGH | Monitoring stage. |
| `src/components/trigger_evaluation.py` | KEEP | HIGH | Trigger policy stage. |
| `src/components/model_retraining.py` | KEEP BUT DOCUMENT | MEDIUM | Optional stage; do not overclaim retraining in thesis. |
| `src/components/model_registration.py` | KEEP BUT DOCUMENT | MEDIUM | Optional registration stage. |
| `src/components/baseline_update.py` | KEEP BUT DOCUMENT | MEDIUM | Optional baseline update stage. |
| `src/components/calibration_uncertainty.py` | KEEP | HIGH | Calibration/uncertainty evidence. |
| `src/entity/config_entity.py` | KEEP | HIGH | Config dataclasses/entities. |
| `src/entity/artifact_entity.py` | KEEP | HIGH | Artifact dataclasses/entities. |
| `src/api/app.py` | KEEP | HIGH | API/WebUI path. |
| `src/utils/` | KEEP | HIGH | Shared utility functions. |
| `tests/` | KEEP | HIGH | Regression safety. |

Manual-check code:

| Path | Action | Risk | Notes |
|---|---|---:|---|
| `src/train.py` | NEEDS MANUAL CHECK | MEDIUM | May be old or experimental compared with current pipeline. |
| `src/sensor_data_pipeline.py` | NEEDS MANUAL CHECK | MEDIUM | Check if still referenced. |
| `src/preprocess_data.py` | NEEDS MANUAL CHECK | MEDIUM | May overlap with current transformation component. |
| `src/run_inference.py` | NEEDS MANUAL CHECK | MEDIUM | May overlap with pipeline/API inference. |
| `src/evaluate_predictions.py` | NEEDS MANUAL CHECK | MEDIUM | `src/README.md` appears stale about this file. |
| `src/model_rollback.py` | NEEDS MANUAL CHECK | MEDIUM | Keep if rollback story is needed. |
| `src/calibration.py` | NEEDS MANUAL CHECK | MEDIUM | Check against current calibration component. |
| `src/monitoring/` | NEEDS MANUAL CHECK | MEDIUM | Check overlap with `post_inference_monitoring.py`. |
| `src/README.md` | MERGE/CONSOLIDATE | LOW | It appears stale and should be updated later, not deleted. |

Script cleanup:

| Script | Action | Risk | Notes |
|---|---|---:|---|
| `scripts/generate_ch4_figures.py` | KEEP | HIGH | Thesis figure generation. |
| `scripts/generate_ch7_figures.py` | KEEP | HIGH | Thesis figure generation. |
| `scripts/generate_smoothing_figure.py` | KEEP | HIGH | Supports smoothing explanation. |
| `scripts/generate_user2_figure.py` | KEEP | MEDIUM | Thesis/analysis support. |
| `scripts/run_unlabeled_sessions.py` | KEEP BUT DOCUMENT | HIGH | Monitoring evidence. |
| `scripts/collect_unlabeled_monitoring.py` | KEEP BUT DOCUMENT | HIGH | Monitoring evidence. |
| `scripts/run_thesis_ablation_experiments.py` | KEEP BUT DOCUMENT | HIGH | Ablation evidence. |
| `scripts/threshold_sweep.py` | KEEP BUT DOCUMENT | HIGH | Trigger threshold evidence. |
| `scripts/diagnose_temporal.py` | DELETE LATER AFTER CONFIRMATION | LOW | Marked as safe-to-delete style diagnostic. Confirm first. |
| `scripts/shorten_figure_captions.py` | ARCHIVE | LOW | One-time thesis cleanup helper. |
| `scripts/fix_figure_index.py` | ARCHIVE | LOW | One-time thesis cleanup helper. |
| `scripts/verify_smoothing.py` | ARCHIVE | LOW | Diagnostic helper. |
| `scripts/compute_smoothed_transition.py` | ARCHIVE | LOW | Diagnostic helper after outputs are frozen. |

## 7 Data and Model Artifact Cleanup Plan

Data:

| Path | Action | Risk | Notes |
|---|---|---:|---|
| `data/raw/` | KEEP BUT DOCUMENT | CRITICAL | Original/raw data. DVC pointer exists. |
| `data/processed/` | KEEP BUT DOCUMENT | HIGH | Processed data. DVC pointer exists. |
| `data/prepared/` | KEEP BUT DOCUMENT | HIGH | Prepared windows/features. DVC pointer exists. |
| `data/labels/` | KEEP BUT DOCUMENT | HIGH | Label files and labeling report. |
| `data/raw.dvc` | DO NOT TOUCH | CRITICAL | DVC pointer. |
| `data/processed.dvc` | DO NOT TOUCH | CRITICAL | DVC pointer. |
| `data/prepared.dvc` | DO NOT TOUCH | CRITICAL | DVC pointer. |
| `data/synth/` | ARCHIVE | MEDIUM | Synthetic/extra data. Check references first. |
| `data/codex_synth/` | ARCHIVE | MEDIUM | Synthetic/extra data. |
| `data/synthetic_cluade/` | ARCHIVE | MEDIUM | Synthetic/extra data. |
| `data/all_users_data_labeled.csv` | NEEDS MANUAL CHECK | HIGH | May be a large important intermediate. |
| `data/anxiety_dataset.csv` | NEEDS MANUAL CHECK | MEDIUM | Check if thesis or experiments use it. |

Models:

| Path | Action | Risk | Notes |
|---|---|---:|---|
| `models/runtime_contract/model_d1_final_20260528/` | DO NOT TOUCH | CRITICAL | Active final runtime model contract. |
| `models/runtime_contract/model_d1_final_20260528.dvc` | DO NOT TOUCH | CRITICAL | DVC pointer for active model contract. |
| `models/runtime_contract/model_a_final_20260508/` | KEEP BUT DOCUMENT | MEDIUM | Historical rollback/mentor comparison evidence. |
| `models/model_registry/` | KEEP BUT DOCUMENT | MEDIUM | Model A/B/C/D metadata story. |
| `models/pretrained/` | KEEP BUT DOCUMENT | MEDIUM | Historical/forensic; DVC pointer exists. |
| `models/pretrained.dvc` | DO NOT TOUCH | CRITICAL | DVC pointer. |
| `models/retrained/` | ARCHIVE | MEDIUM | Older training output unless directly referenced. |
| `models/training_baseline.json` | KEEP | HIGH | Baseline evidence. |
| `models/raw_physical_baseline.json` | KEEP | HIGH | Baseline evidence. |
| `models/drift_reference.json` | KEEP | HIGH | Drift reference. |

Current model statement:

- The current production/API path should be treated as using the D1 `.keras` model from `models/runtime_contract/model_d1_final_20260528/`.
- SavedModel files should be described as portability/export evidence, not the main loaded API model path.
- Older mentor or notebook models should be kept only as comparison/history unless the runtime config points to them.

## 8 MLflow, DVC, Docker, and Reproducibility Plan

DVC:

| Item | Action | Risk | Notes |
|---|---|---:|---|
| `data/raw.dvc` | DO NOT TOUCH | CRITICAL | Raw data pointer. |
| `data/processed.dvc` | DO NOT TOUCH | CRITICAL | Processed data pointer. |
| `data/prepared.dvc` | DO NOT TOUCH | CRITICAL | Prepared data pointer. |
| `models/pretrained.dvc` | DO NOT TOUCH | CRITICAL | Historical model pointer. |
| `models/runtime_contract/model_d1_final_20260528.dvc` | DO NOT TOUCH | CRITICAL | Active model pointer. |
| `artifacts/20260528_122625.dvc` | DO NOT TOUCH | CRITICAL | Defended artifact pointer. |
| `dvc.yaml`, `dvc.lock` | NEEDS MANUAL CHECK | MEDIUM | These were not visible in the root scan. The project uses Python orchestration, not a DVC stage graph. |

MLflow:

| Path | Action | Risk | Notes |
|---|---|---:|---|
| `mlruns/` | KEEP BUT DOCUMENT | MEDIUM | Keep through defense. Later export key run IDs and archive old runs. |
| `mlruns/.trash/` | DELETE LATER AFTER CONFIRMATION | LOW | MLflow trash can be removed after backup. |

Docker:

| Path | Action | Risk | Notes |
|---|---|---:|---|
| `docker/Dockerfile.training` | KEEP | MEDIUM | Training/reproducibility image. |
| `docker/Dockerfile.inference` | KEEP | MEDIUM | API/inference image. |
| `docker/README.md` | KEEP | LOW | Docker usage docs. |
| `docker-compose.yml` | KEEP | MEDIUM | Local service orchestration. |
| `.dockerignore` | KEEP | MEDIUM | Prevents large/unwanted files in Docker context. |

Reproducibility docs:

| Path | Action | Risk | Notes |
|---|---|---:|---|
| `README.md` | KEEP | HIGH | Main repo explanation. |
| `REPRODUCE.md` | KEEP | HIGH | Reproduction instructions. |
| `BUILD_FROM_SCRATCH.md` | KEEP | MEDIUM | Build explanation. |
| `CODE_WALKTHROUGH.md` | KEEP | MEDIUM | Defense/interview support. |
| `PROJECT_DEEP_DIVE.md` | KEEP | MEDIUM | Architecture explanation. |
| `MENTOR_REVIEW_CHANGE_SUMMARY.md` | KEEP BUT DOCUMENT | MEDIUM | Useful mentor-facing summary. |

## 9 Duplicate and Obsolete Files

Likely duplicates or obsolete generated material:

| Item | Action | Risk | Notes |
|---|---|---:|---|
| `thesis/21 june final.pdf` | DELETE LATER AFTER CONFIRMATION | LOW | Same size/timestamp as `thesis/main.pdf` in scan. Confirm visually first. |
| `thesis/with smoothed,mlflow and webui ss no mentor chnages.pdf` | ARCHIVE | LOW | Older draft/export. |
| `thesis/webui+mlops images/` | ARCHIVE | MEDIUM | Raw screenshots likely copied into `thesis/figures/`. |
| `notebooks/model_d1_artifacts/` | ARCHIVE | MEDIUM | Older duplicate artifact folder. |
| `notebooks/model_d1_final_artifacts/` | ARCHIVE | MEDIUM | Older duplicate artifact folder. |
| `notebooks/model_d3_centered_artifacts/` | ARCHIVE | MEDIUM | Experimental artifact folder. |
| `nb/model_d1_artifacts/` | ARCHIVE | MEDIUM | Duplicate/older notebook artifact area. |
| Repeated `run_info.json`, `monitoring_report.json`, prediction `.npy`, inference summaries | ARCHIVE | MEDIUM | Normal generated outputs from many runs. Keep defended run first. |
| LaTeX build files | DELETE LATER AFTER CONFIRMATION | LOW | Rebuildable. |
| Python caches | DELETE LATER AFTER CONFIRMATION | LOW | Rebuildable. |
| `har_mlops_pipeline.egg-info/` | DELETE LATER AFTER CONFIRMATION | LOW | Rebuildable packaging metadata. |

Obsolete does not mean useless. For this project, many old files are evidence of development. Archive first, delete only when the final PDF, code, model, and defended artifacts are backed up.

## 10 Cleanup Order

Recommended order after thesis defense:

1. Create a full external backup of the whole repository.
2. Save a copy of `thesis/main.pdf`, `thesis/main.tex`, `thesis/chapters/`, `thesis/appendices/`, `thesis/figures/`, and `thesis/references.bib`.
3. Save a copy of `models/runtime_contract/model_d1_final_20260528/`.
4. Save a copy of `artifacts/20260528_122625/`.
5. Save a copy of `logs/pipeline/pipeline_result_20260528_122625.json`.
6. Save DVC metadata and DVC storage.
7. Delete generated caches only: Python caches, mypy cache, pytest temp folders, LaTeX build files.
8. Rebuild `thesis/main.pdf`.
9. Run tests.
10. Run a pipeline smoke test using the final runtime model and final config.
11. Archive old thesis PDFs and raw screenshot staging.
12. Archive old notebook artifacts.
13. Archive non-final pipeline output runs.
14. Export or document important MLflow run IDs, then archive old MLflow runs.
15. Review `_archive/` and move it outside the active repo if it is only historical.

## 11 Files That Must Not Be Deleted

Do not delete these:

```text
README.md
REPRODUCE.md
BUILD_FROM_SCRATCH.md
CODE_WALKTHROUGH.md
PROJECT_DEEP_DIVE.md
pyproject.toml
setup.py
run_pipeline.py
config/pipeline_config.yaml
config/mlflow_config.yaml
config/requirements.txt
config/requirements-runtime.txt
src/
tests/
docker/
docker-compose.yml
.github/
thesis/main.tex
thesis/main.pdf
thesis/chapters/
thesis/appendices/
thesis/figures/
thesis/tables/
thesis/references.bib
thesis/build_thesis.ps1
models/runtime_contract/model_d1_final_20260528/
models/runtime_contract/model_d1_final_20260528.dvc
artifacts/20260528_122625/
artifacts/20260528_122625.dvc
logs/pipeline/pipeline_result_20260528_122625.json
data/raw.dvc
data/processed.dvc
data/prepared.dvc
models/pretrained.dvc
.dvc/
.dvc_storage/
```

Also keep these thesis evidence reports unless the thesis no longer references them:

```text
reports/ABLATION_WINDOWING.csv
reports/ABLATION_WINDOWING.png
reports/THRESHOLD_CALIBRATION.csv
reports/THRESHOLD_CALIBRATION.png
reports/TRIGGER_POLICY_EVAL.csv
reports/TRIGGER_POLICY_EVAL.png
reports/unlabeled_sessions_monitoring.csv
reports/unlabeled_sessions_monitoring.json
reports/chapter4/
reports/abc_comparison/
```

## 12 Files Safe to Delete Later

Only delete these after backup and after confirming the final thesis PDF and pipeline still work:

```text
*.pyc
__pycache__/
.mypy_cache/
.pytest_cache/
.pytest_tmp/
.pytest_tmp_audit/
har_mlops_pipeline.egg-info/
*.aux
*.log
*.toc
*.out
*.lof
*.lot
*.fls
*.fdb_latexmk
*.blg
*.bbl
```

Likely safe after visual/manual confirmation:

```text
thesis/21 june final.pdf
thesis/with smoothed,mlflow and webui ss no mentor chnages.pdf
thesis/webui+mlops images/
notebooks/model_d1_artifacts/
notebooks/model_d1_final_artifacts/
notebooks/model_d3_centered_artifacts/
nb/model_d1_artifacts/
outputs/
recording/
tmp/
```

## 13 Final Recommended Clean Repository Structure

A cleaner repository after defense could look like this:

```text
MasterArbeit_MLops/
  README.md
  REPRODUCE.md
  BUILD_FROM_SCRATCH.md
  CODE_WALKTHROUGH.md
  PROJECT_DEEP_DIVE.md
  pyproject.toml
  setup.py
  run_pipeline.py
  config/
  docker/
  src/
  tests/
  scripts/
  reports/
  thesis/
    main.tex
    main.pdf
    chapters/
    appendices/
    figures/
    tables/
    references.bib
    build_thesis.ps1
  models/
    runtime_contract/
      model_d1_final_20260528/
      model_d1_final_20260528.dvc
    model_registry/
    pretrained.dvc
  artifacts/
    20260528_122625/
    20260528_122625.dvc
  data/
    raw.dvc
    processed.dvc
    prepared.dvc
    labels/
  logs/
    pipeline/
      pipeline_result_20260528_122625.json
  .github/
  .dvc/
```

Large historical material should live outside the active repo:

```text
repo_archive_before_defense/
  old_pipeline_runs/
  old_mlflow_runs/
  old_notebook_artifacts/
  old_thesis_drafts/
  old_screenshots/
  old_models/
  old_data_extras/
  internal_notes/
```

## 14 Final Checklist Before Any Real Cleanup

Before deleting or moving anything, confirm:

- [ ] Full repository backup exists outside the repo.
- [ ] `thesis/main.pdf` opens correctly.
- [ ] `thesis/main.tex` rebuilds successfully.
- [ ] All thesis figures render correctly.
- [ ] Appendix E/system walkthrough figures are visible.
- [ ] `models/runtime_contract/model_d1_final_20260528/` is backed up.
- [ ] `artifacts/20260528_122625/` is backed up.
- [ ] `logs/pipeline/pipeline_result_20260528_122625.json` is backed up.
- [ ] DVC pointer files are backed up.
- [ ] `.dvc/` and `.dvc_storage/` are backed up.
- [ ] Important MLflow runs are exported or documented.
- [ ] Final model notebook/script is documented.
- [ ] `README.md` and `REPRODUCE.md` still match the actual pipeline.
- [ ] Tests pass after cleanup.
- [ ] A small pipeline/API smoke test passes after cleanup.
- [ ] No thesis source file was renamed during cleanup.
- [ ] No active model path was changed during cleanup.
- [ ] No final artifact path was changed during cleanup.

Short recommendation: keep the repo as it is until defense submission is fully safe, then clean in small steps. Start with caches and generated build files, then archive old PDFs and screenshots, then old pipeline runs, then old notebook artifacts, then MLflow history. Do not touch the final thesis, final D1 model, defended run, DVC metadata, or reproducibility docs.

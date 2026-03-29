# Safe Cleanup Plan — MasterArbeit_MLops
**Date:** 2026-03-29
**Branch:** chore/repo-cleanup
**Principle:** Thesis repo — preserve reproducibility, evidence, traceability. No destructive action without explicit confirmation.

---

## Context: Already Deleted (Working Tree Only, Not Yet Committed)

These files have been deleted from disk on the current branch but the deletions are **not yet staged or committed**. They appear as `D` in `git status`. They are safe to stage and commit — but verify the list first.

| Path | Reason Safe |
|------|-------------|
| `config/alertmanager.yml` | Monitoring stack placeholder, not used in thesis pipeline |
| `config/alerts/har_alerts.yml` | Grafana alert placeholder, unused |
| `config/alerts/har_alerts_pending.yml` | Grafana alert placeholder, unused |
| `config/grafana/**` (all 5 files) | Grafana dashboard configs, monitoring stack not in final thesis scope |
| `config/prometheus.yml` | Prometheus config, monitoring stack not in scope |
| `internal/writing/thesis_execution_plan_mar_jun_2026.md` | Superseded by root-level `thesis_execution_plan_mar_jun_2026.md` |
| `scripts/_wave1_archive/**` (14 files) | Explicitly wave-1 archived — benchmarking, paper extraction, repo-gen scripts no longer needed |
| `src/_wave2_archive/**` (4 files) | Explicitly wave-2 archived — alternate core/exception path, ruled out in Wave 2 decision |
| `src/diagnostic_pipeline_check.py` | One-off diagnostic script, not part of reproducible pipeline |
| `src/ood_detection.py` | Experimental OOD module, removed from active pipeline |
| `src/robustness.py` | Experimental robustness module, removed from active pipeline |
| `src/utils/production_optimizations.py` | Removed optimization module |
| `tests/test_ood_detection.py` | Tests for removed module |
| `tests/test_progress_dashboard.py` | Tests for removed module |
| `tests/test_prometheus_metrics.py` | Tests for removed Prometheus monitoring stack |
| `tests/test_robustness.py` | Tests for removed module |

**Action:** `git add -u` then commit with message `chore: commit wave cleanup deletions`.

---

## Section 1 — Safe to Delete Now

These can be deleted without any thesis or reproducibility risk.

### 1a. Python Bytecode Cache (on disk, NOT in git)

Not tracked by git — deletion has zero git impact. Python regenerates these automatically.

```
# Run from repo root:
find . -type d -name __pycache__ -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -not -path "./.git/*" -delete 2>/dev/null
```

Affected locations (95 files across):
- `src/**/__pycache__/` (multiple: entity, pipeline, utils, api, components, domain_adaptation, logger)
- `tests/__pycache__/`
- `scripts/__pycache__/`
- `./__pycache__/` (root level)

Then add to `.gitignore` if not already present: `**/__pycache__/` and `**/*.pyc`

### 1b. Zero-Byte Log Files

These are empty log files with no content — confirmed in the repository audit.

| Path | Reason |
|------|--------|
| `logs/20260225_132212.log` | Zero bytes, no content |
| `logs/20260327_174656.log` | Zero bytes, no content |
| `logs/20260327_174815.log` | Zero bytes, no content |
| `logs/20260327_175440.log` | Zero bytes, no content |

### 1c. Empty Generated Directories

| Path | Reason |
|------|--------|
| `outputs/wasserstein_drift/` | Empty — Wasserstein drift stage not producing output |
| `outputs/ablation/runs/2025-08-13-04-18-52/ingestion/` | Empty subfolder inside a historical ablation run |
| `logs/evaluation/` | Empty — evaluation logging not writing here |
| `logs/inference/` | Empty — inference logging not writing here |
| `logs/preprocessing/` | Empty — preprocessing logging not writing here |

### 1d. Empty Artifact Run Folders

These artifact folders are empty (confirmed in audit SAFE_DELETE_CANDIDATES.md). No stage output, no evidence.

| Path | Reason |
|------|--------|
| `artifacts/20260306_141446/` | Empty run folder |
| `artifacts/20260314_125816/` | Empty run folder |
| `artifacts/20260318_225016/` | Empty run folder |
| `artifacts/20260327_113118/` | Empty run folder |
| `artifacts/20260328_170543/` | Empty run folder |
| `artifacts/20260328_171743/` | Empty run folder |
| `artifacts/20260328_172246/` | Empty run folder |
| `artifacts/20260328_172732/` | Empty run folder |
| `artifacts/20260328_181826/` | Empty run folder |

### 1e. Root-Level Duplicate Audit Files (Untracked)

These files were generated at the root during the 2026-03-29 audit session. The canonical versions are in `reports/repo_audit/`.

| Path | Canonical Location |
|------|-------------------|
| `REPOSITORY_CLEANUP_AUDIT_2026-03-29.md` (root) | Content in `reports/repo_audit/FULL_REPOSITORY_AUDIT_2026-03-29.md` |
| `REPOSITORY_FILE_INVENTORY_2026-03-29.md` (root) | Superseded by the full audit |
| `INTERNAL_SUMMARY_FOR_REVIEW.md` (root) | Working note, not thesis evidence |

**Action:** Delete all three. Add to `.gitignore`: `REPOSITORY_*.md` at root (or move content first if needed).

### 1f. LaTeX Build Artifacts (Untracked)

These are generated by `pdflatex`/`bibtex` and should not be committed.

| Path | Reason |
|------|--------|
| `thesis/chapters/ch*.aux` (8 files) | LaTeX build cache |
| `thesis/main.aux` | LaTeX build cache |
| `thesis/main.bbl` | BibTeX output |
| `thesis/main.blg` | BibTeX log |
| `thesis/main.toc` | Table of contents cache |

**Action:** Delete all. Add to `.gitignore`:
```
thesis/*.aux
thesis/*.bbl
thesis/*.blg
thesis/*.toc
thesis/chapters/*.aux
```

### 1g. internal/review_later/ (Untracked, Not in Git)

All 31 files are `archive_` prefixed, untracked (git has no record of them). These are legacy working materials that were moved here during archive triage. None are referenced by code, tests, or docs/thesis evidence.

| Path | Reason |
|------|--------|
| `internal/review_later/archive_*.py` (16 script files) | Legacy development scripts, superseded by active scripts/ |
| `internal/review_later/archive_*.md` (12 note files) | Planning notes and paper summaries, not thesis evidence |
| `internal/review_later/archive_*.txt`, `*.jpeg`, `*.png` (3 media files) | Working session materials |

**Risk:** LOW — not tracked by git, not referenced anywhere active.
**Action:** Delete entire `internal/review_later/` directory.

---

## Section 2 — Safe to Archive (Move to Local External Location)

These should **not** be deleted but should be **moved out of the main repo** to a local archive folder (e.g., `D:\study apply\ML Ops\MasterArbeit_MLops_archive\`). They are too large or too historical for daily use but may be needed for defense questions.

### 2a. Historical Artifact Run Folders (Pre-Evidence Window)

**Keep:** The following runs are in the final evidence window:
```
artifacts/20260327_183354/    # 2026-03-27 final runs
artifacts/20260327_203611/
artifacts/20260327_203619/
artifacts/20260327_215139/
artifacts/20260327_215143/
artifacts/20260328_170551/    # 2026-03-28 controlled comparison
artifacts/20260328_170554/
artifacts/20260328_170558/
artifacts/20260328_171752/
artifacts/20260328_171755/
artifacts/20260328_171758/
artifacts/20260328_172253/
artifacts/20260328_172256/
artifacts/20260328_172300/
artifacts/20260328_172739/
artifacts/20260328_172742/
artifacts/20260328_172745/
artifacts/20260328_172909/
```

**Archive (move out):** All artifact folders from 2026-03-06 through 2026-03-26 (approximately 30 folders):
```
artifacts/20260306_*/
artifacts/20260313_*/
artifacts/20260314_*/
artifacts/20260318_*/
```

**Reason:** Old development runs. Not linked from `docs/thesis/THESIS_EVIDENCE.md`. 741 MB total in artifacts — these pre-evidence runs are the bulk.

### 2b. Historical Pipeline Result Logs (Pre-Evidence Window)

**Keep (final evidence):**
```
logs/pipeline/pipeline_result_20260328_232116.json
logs/pipeline/pipeline_result_20260328_232231.json
logs/pipeline/pipeline_result_20260329_002240.json
logs/pipeline/pipeline_result_20260329_002404.json
logs/pipeline/pipeline_result_20260329_002442.json
logs/pipeline/pipeline_result_20260329_002536.json
logs/pipeline/pipeline_result_20260329_002606.json
logs/pipeline/pipeline_result_20260329_002659.json
```

**Archive (move out):** All pipeline result files from 2026-02-27 through 2026-03-27 (approximately 42 files).
**Reason:** Development history, not final evidence. These fill `logs/pipeline/` with noise.

### 2c. Ablation Run Tree

| Path | Size | Reason |
|------|------|--------|
| `outputs/ablation/runs/` | ~4 GB | Historical ablation session tree. Keep `outputs/ablation/ablation_results.csv`, `ablation_summary.csv`, `ablation_errors.json` — these are the summary evidence. The full `runs/` tree is session-by-session intermediate output. |

**Keep in place:**
```
outputs/ablation/ablation_results.csv
outputs/ablation/ablation_summary.csv
outputs/ablation/ablation_errors.json
```

**Archive:** `outputs/ablation/runs/` (entire subdirectory)

### 2d. models/retrained/ — Untracked Ablation Model Snapshots

These 6 files were generated by the ablation experiment and are NOT tracked by git (correctly):

| File | Config | Disposition |
|------|--------|-------------|
| `models/retrained/adabn_adapted_model_configA_20260329_002340.keras` | Config A (no gravity, no calibration) — ablation baseline | Archive externally |
| `models/retrained/adabn_adapted_model_configB_20260329_002515.keras` | Config B (no gravity, yes calibration) | Archive externally |
| `models/retrained/adabn_adapted_model_configC_20260329_002638.keras` | Config C (yes gravity, no calibration) | Archive externally |
| `models/retrained/adabn_adapted_model_configD_20260328_232204.keras` | Config D (yes gravity, yes calibration) — ablation winner | **Keep locally** (thesis evidence) |
| `models/retrained/har_model_20260327_213930.keras` | Historical retrain snapshot | Archive externally |
| `models/retrained/har_model_20260327_223917.keras` | Historical retrain snapshot | Archive externally |

**Do NOT commit these to git** — keras files belong under DVC or external archive.
**Action:** Archive configs A/B/C and the two historical har_model snapshots externally. Keep Config D locally until thesis is submitted.

### 2e. internal/reference/ Archive Files

The `internal/reference/` directory contains 16 files prefixed `archive_` that are superseded by their non-prefixed counterparts in the same directory.

| Archive File | Live Counterpart |
|-------------|-----------------|
| `internal/reference/archive_CICD_EXPLAINED.md` | `internal/reference/cicd_explained.md` |
| `internal/reference/archive_DOCKER_EXPLAINED.md` | `internal/reference/docker_explained.md` |
| `internal/reference/archive_DVC_EXPLAINED.md` | `internal/reference/dvc_explained.md` |
| `internal/reference/archive_EXPERIMENT_TRACKING_EXPLAINED.md` | `internal/reference/experiment_tracking_explained.md` |
| `internal/reference/archive_FASTAPI_EXPLAINED.md` | `internal/reference/fastapi_explained.md` |
| `internal/reference/archive_GRAFANA_EXPLAINED.md` | `internal/reference/grafana_explained.md` |
| `internal/reference/archive_MLFLOW_EXPLAINED.md` | `internal/reference/mlflow_explained.md` |
| `internal/reference/archive_MODEL_REGISTRY_EXPLAINED.md` | `internal/reference/model_registry_explained.md` |
| `internal/reference/archive_MONITORING_EXPLAINED.md` | `internal/reference/monitoring_explained.md` |
| `internal/reference/archive_PROMETHEUS_EXPLAINED.md` | `internal/reference/prometheus_explained.md` |
| `internal/reference/archive_WHY_BOOK.md` | `internal/reference/why_book.md` (+ WHY_BOOK_2.md) |
| `internal/reference/archive_WHY_BY_FILE.md` | `internal/reference/why_by_file.md` (+ WHY_BY_FILE_2.md) |
| `internal/reference/archive_WHY_BY_STAGE.md` | `internal/reference/WHY_BY_STAGE.md` |
| `internal/reference/archive_WHY_BY_TECH.md` | `internal/reference/why_by_tech.md` (+ WHY_BY_TECH_2.md) |
| `internal/reference/archive_WHY_INVENTORY.md` | `internal/reference/WHY_INVENTORY.md` |
| `internal/reference/archive_thesis-pipeline-why-what-how.md` | `internal/reference/thesis-pipeline-why-what-how.md` |

**Action:** These are tracked by git. Run `git rm` for each, or move to an `archive/` subfolder. Since they're internal notes, low thesis risk.

### 2f. internal/workflow/ Archive Files

Similarly, `internal/workflow/` has 8 `archive_` prefixed files that are historical drafts:

```
internal/workflow/archive_01_data_pipeline_flow.md
internal/workflow/archive_02_src_deep_dive.md
internal/workflow/archive_03_scripts_reference.md
internal/workflow/archive_04_tests_reference.md
internal/workflow/archive_05_config_deps_infra.md
internal/workflow/archive_2026_03_04_artifact_source_mapping.md
internal/workflow/archive_2026_03_04_normalization_analysis.md
internal/workflow/archive_REPO_INVENTORY.md
internal/workflow/archive_artifact_source_mapping.md
internal/workflow/archive_normalization_analysis.md
```

Live counterparts exist: `repo_inventory.md`, `EVIDENCE_LEDGER.md`, `DECISION_REGISTER.csv`, `REFERENCES.md`

**Action:** Move to `internal/archive/` subfolder and `git mv`. These are internal-only, no external references.

---

## Section 3 — Keep but Rename

### 3a. Root-Level Thesis Execution Plan (Untracked)

| Current Path | Suggested Path | Reason |
|-------------|----------------|--------|
| `thesis_execution_plan_mar_jun_2026.md` (root) | `internal/workflow/thesis_execution_plan_mar_jun_2026.md` | Root is not the right home for internal planning docs. Move to `internal/workflow/`. The old one at `internal/writing/thesis_execution_plan_mar_jun_2026.md` was already deleted from disk. |

### 3b. Untracked Audit Reports (reports/repo_audit/)

These are newly generated, untracked, and should be committed under cleaner names:

| Current Name | Suggested Name | Reason |
|-------------|----------------|--------|
| `reports/repo_audit/FULL_REPOSITORY_AUDIT_2026-03-29.md` | Keep as-is | Descriptive, date-stamped correctly |
| `reports/repo_audit/THESIS_CRITICAL_AUDIT_2026-03-29.md` | Keep as-is | Descriptive, date-stamped correctly |
| `reports/repo_audit/SAFE_DELETE_CANDIDATES.md` | `reports/repo_audit/SAFE_DELETE_CANDIDATES_2026-03-29.md` | Add date to distinguish from future versions |
| `reports/repo_audit/WAVE_1_CLEANUP_PLAN.md` | Keep as-is | Clear scope name |

### 3c. models/retrained/ — Tracked Keras Files with Opaque Names

| Current Name | Suggested Name | Reason |
|-------------|----------------|--------|
| `models/retrained/best_model.keras` | `models/retrained/best_model_20260219.keras` | Date disambiguates from newer retrains |
| `models/retrained/retrained_model.keras` | `models/retrained/retrained_model_20260219.keras` | Same reason |
| `models/retrained/pseudo_label_model.keras` | `models/retrained/pseudo_label_model_20260219.keras` | Same reason |
| `models/retrained/har_model_latest.keras` | `models/retrained/har_model_latest_20260219.keras` | "latest" is ambiguous; date makes it static |

**Note:** Renaming tracked keras files requires a git mv. More importantly, see Section 4 — these files should eventually move to DVC rather than stay in git.

---

## Section 4 — Keep but Refactor

### 4a. `config/pipeline_config.yaml` — CRITICAL (Bug B1)

**Issue:** `enable_gravity_removal: true` on line 35 with the comment directly above saying `RECOMMENDED: false`. This causes a 1.09σ systematic offset in normalized Az because the production scaler was fitted on gravity-included data (Az mean = −3.5295 m/s²).

**Fix:** Set `enable_gravity_removal: false` to match training preprocessing.

Also: `enable_calibration: true` and `enable_domain_calibration: true` — also `RECOMMENDED: false`. These were left on from Config D ablation. Reset to `false` for baseline production config.

**Risk of fix:** LOW — matches the comment in the file and the training paper. Needs one pipeline run to verify evaluation metrics recover.

### 4b. `src/components/trigger_evaluation.py` — Line 136 (Bug B2)

**Issue:** `cooldown_active=False` is hardcoded. The actual cooldown state from `decision.cooldown_active` is never propagated, meaning the trigger policy never enforces cooldown in practice.

**Fix:** Pass `cooldown_active=decision.cooldown_active` (or equivalent engine state lookup).

### 4c. `models/registry/model_registry.json`

**Issue:** Registry shows `"current_version": null`, `"deployed_at": null`, `"status": "archived"`. Any examiner inspecting this will see an empty registry, undermining the claim that model registration is part of the pipeline.

**Fix:** Update to reflect the actual registered model (har_model_vauto.keras) with correct metadata.

### 4d. `.gitignore` — Missing Entries

Add these to prevent future commits of generated artifacts:
```gitignore
# LaTeX build outputs
thesis/*.aux
thesis/*.bbl
thesis/*.blg
thesis/*.toc
thesis/chapters/*.aux

# Keras model snapshots (use DVC instead)
models/retrained/*.keras
!models/retrained/scaler_config.json
!models/retrained/label_mapping.json

# Python cache
**/__pycache__/
**/*.pyc

# Root-level temp audit files
REPOSITORY_*.md
INTERNAL_SUMMARY_*.md
```

### 4e. `models/retrained/` — Move Keras Files to DVC

**Issue:** 10 `.keras` files are tracked directly in git (verified by `git ls-files models/retrained/`). This adds ~68MB+ to git history and is an H1 finding from the critical audit. DVC already manages `models/pretrained/` and `models/trained/`.

**Fix:** `git rm --cached models/retrained/*.keras`, add DVC tracking with `dvc add models/retrained/*.keras`, commit the `.dvc` pointer files. Keep `scaler_config.json` and `label_mapping.json` in git (they're small JSON metadata).

**Risk:** MEDIUM — requires DVC setup for retrained. Do after fixing B1 and running a validation pipeline run.

---

## Section 5 — Keep Unchanged

### Active Source Code

| Path | Why Unchanged |
|------|---------------|
| `src/` (all modules except removed files) | Active production pipeline — changes need tests |
| `src/pipeline/production_pipeline.py` | 14-stage orchestrator — thesis core |
| `src/trigger_policy.py` | Multi-metric voting logic — thesis Chapter 6 |
| `src/components/` (all except trigger_evaluation.py Section 4b) | Active stage implementations |
| `src/domain_adaptation/` | AdaBN implementation — thesis Chapter 6 |
| `src/train.py` | Training script with StandardScaler fitting |
| `src/api/app.py` | FastAPI inference endpoint — thesis demo |
| `src/entity/config_entity.py` | All entity config classes |

### Tests

| Path | Why Unchanged |
|------|---------------|
| `tests/` (active tests) | Validation suite — run before any thesis demo |
| `tests/test_trigger_policy.py` | Critical governance test |
| `tests/test_threshold_consistency.py` | Validates tiered alerting design |
| `tests/test_preprocessing.py` | Pipeline correctness validation |
| `tests/test_calibration.py` | Calibration correctness |
| `tests/test_pipeline_integration.py` | End-to-end integration |

### Configuration

| Path | Why Unchanged |
|------|---------------|
| `config/pipeline_overrides.yaml` | Ablation override mechanism — thesis evidence |
| `config/mlflow_config.yaml` | MLflow tracking configuration |
| `config/requirements.txt` / `requirements-lock.txt` | Reproducibility — pin exact versions |

### Thesis and Documentation

| Path | Why Unchanged |
|------|---------------|
| `thesis/` (entire directory) | Active manuscript — never touch during write phase |
| `docs/TRIGGER_POLICY_EXPLANATION.md` | Policy evidence for examiner |
| `docs/thesis/THESIS_EVIDENCE.md` | Master evidence ledger |
| `.github/workflows/ci.yml` | CI/CD validation pipeline |
| `.github/workflows/cd.yml` | CD pipeline |

### Final Evidence Files

| Path | Why Unchanged |
|------|---------------|
| `logs/pipeline/pipeline_result_20260328_232116.json` | Final controlled comparison |
| `logs/pipeline/pipeline_result_20260328_232231.json` | Final controlled comparison |
| `logs/pipeline/pipeline_result_20260329_00*.json` (6 files) | Final ablation evidence runs |
| `reports/repo_audit/WAVE1_STAGE5_STAGE7_LABELMAP_FIXES.md` | Wave 1 fix evidence |
| `reports/repo_audit/WAVE2_BASELINE_SPACE_VERIFICATION.md` | Wave 2 baseline evidence |
| `reports/repo_audit/WAVE2_STAGE6_BASELINE_SPACE_FIX_VALIDATION.md` | Wave 2 validation evidence |
| `reports/repo_audit/PREDICTION_DOMINANCE_ROOT_CAUSE.md` | Root cause evidence |
| `models/pretrained/` (DVC tracked) | Original model — do not touch |
| `models/training_baseline.json` | Training distribution reference |
| `models/normalized_baseline.json` | Normalized baseline reference |
| `models/retrained/scaler_config.json` | Production scaler state (Az mean = −3.5295) |
| `models/retrained/label_mapping.json` | Activity label mapping |
| `internal/workflow/DECISION_REGISTER.csv` | Architecture decisions log |
| `internal/workflow/EVIDENCE_LEDGER.md` | Evidence inventory |
| `internal/workflow/DEFENSE_QA.md` | Defense prep Q&A |
| `scripts/run_ablation_experiment.py` | Ablation experiment entry point |
| `scripts/post_inference_monitoring.py` | Monitoring script |
| `scripts/run_ab_comparison.py` | A/B comparison script |

---

## Section 6 — Cleanup Order (Safest to Riskiest)

### Wave 0 — Zero Risk (No git impact, no code impact)
1. Delete `__pycache__/` directories and `.pyc` files (on disk only, not tracked)
2. Delete zero-byte log files (`logs/2026*.log`)
3. Delete empty directories (`logs/evaluation/`, `logs/inference/`, `logs/preprocessing/`, `outputs/wasserstein_drift/`)
4. Delete empty artifact run folders (9 folders listed in Section 1d)
5. Delete LaTeX build artifacts (`thesis/*.aux`, `thesis/*.bbl`, etc.)
6. Delete `internal/review_later/` directory (untracked)
7. Delete root-level duplicate audit files (`REPOSITORY_*.md`, `INTERNAL_SUMMARY_*.md`)

### Wave 1 — Low Risk (Commit Already-Staged Deletions)
8. Stage the `D`-status deletions: `git add -u` (picks up all working-tree deletions)
9. Verify the staged file list matches the "Already Deleted" table above
10. Commit: `chore: commit wave-1 cleanup — monitoring stack, dead modules, wave archives`

### Wave 2 — Low Risk (Add New Audit Files to Git)
11. Stage new audit files: `git add reports/repo_audit/FULL_REPOSITORY_AUDIT_2026-03-29.md reports/repo_audit/THESIS_CRITICAL_AUDIT_2026-03-29.md reports/repo_audit/SAFE_CLEANUP_PLAN_2026-03-29.md reports/repo_audit/WAVE_1_CLEANUP_PLAN.md`
12. Move root-level `thesis_execution_plan_mar_jun_2026.md` to `internal/workflow/`
13. Update `.gitignore` with LaTeX, cache, and keras entries (Section 4d)
14. Commit: `chore: add audit reports, update gitignore, relocate thesis plan`

### Wave 3 — Low-Medium Risk (Internal Archive Reorganization)
15. Move `internal/workflow/archive_*.md` files to `internal/archive/workflow/`
16. Move `internal/reference/archive_*.md` files to `internal/archive/reference/`
17. `git add -A internal/` and commit: `chore: consolidate internal archive files`
18. Move `internal/writing/copilot_mega_prompt.md` to `internal/archive/writing/` if not needed for active thesis writing

### Wave 4 — Medium Risk (Archive Historical Run Data)
19. **Create external archive folder first:** `D:\study apply\ML Ops\MasterArbeit_MLops_archive\`
20. Move (don't delete) pre-evidence artifact runs to archive: `artifacts/20260306_*/`, `20260313_*/`, `20260314_*/`, `20260318_*/`
21. Move pre-evidence pipeline logs to archive: `logs/pipeline/pipeline_result_2026022*.json` and `pipeline_result_20260306*.json` through `20260327*.json`
22. Move ablation run tree to archive: `outputs/ablation/runs/`
23. Move models/retrained ablation snapshots (configs A/B/C) to archive
24. Verify remaining artifacts/logs match the final evidence window
25. Run one full pipeline execution to confirm pipeline still works with reduced artifact history

### Wave 5 — Medium Risk (Config Fix — Bug B1)
26. Fix `config/pipeline_config.yaml`: set `enable_gravity_removal: false`, `enable_calibration: false`, `enable_domain_calibration: false`
27. Run full test suite: `python -m pytest tests/ -v`
28. Run one pipeline execution and verify evaluation metrics
29. Verify MLflow logs `transformation_gravity_removal = 0` after fix
30. Commit: `fix: reset preprocessing config to match training baseline (B1 fix)`

### Wave 6 — Medium Risk (Registry + Trigger Fix)
31. Fix `models/registry/model_registry.json` to reflect actual registered model
32. Fix `src/components/trigger_evaluation.py:136` cooldown propagation (Bug B2)
33. Run trigger policy tests to verify behavior unchanged
34. Commit: `fix: propagate cooldown state and update model registry metadata`

### Wave 7 — Higher Risk (DVC Migration for Models)
35. `git rm --cached models/retrained/*.keras`
36. `dvc add models/retrained/` (or individual files)
37. Commit DVC pointer files
38. Verify `dvc pull` restores models correctly
39. This removes 68MB+ from git tracking — test that pipeline still loads models correctly

---

## Quick Reference — Evidence Must-Keep Checklist

Before any wave, verify these paths still exist:
- [ ] `docs/thesis/THESIS_EVIDENCE.md`
- [ ] `docs/TRIGGER_POLICY_EXPLANATION.md`
- [ ] `models/pretrained/` (DVC pointer intact)
- [ ] `models/retrained/scaler_config.json`
- [ ] `models/retrained/label_mapping.json`
- [ ] `models/training_baseline.json`
- [ ] `models/normalized_baseline.json`
- [ ] `reports/repo_audit/WAVE1_STAGE5_STAGE7_LABELMAP_FIXES.md`
- [ ] `reports/repo_audit/WAVE2_BASELINE_SPACE_VERIFICATION.md`
- [ ] `reports/repo_audit/WAVE2_STAGE6_BASELINE_SPACE_FIX_VALIDATION.md`
- [ ] `logs/pipeline/pipeline_result_20260328_232116.json`
- [ ] `logs/pipeline/pipeline_result_20260328_232231.json`
- [ ] `logs/pipeline/pipeline_result_20260329_*.json` (6 files)
- [ ] `internal/workflow/DECISION_REGISTER.csv`
- [ ] `internal/workflow/EVIDENCE_LEDGER.md`
- [ ] `internal/workflow/DEFENSE_QA.md`
- [ ] `outputs/ablation/ablation_results.csv`
- [ ] `outputs/ablation/ablation_summary.csv`

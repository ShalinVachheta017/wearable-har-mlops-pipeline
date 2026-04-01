# Project Worklog

## Purpose
Detailed reverse-chronological worklog reconstructed from git history, dated artifacts, training outputs, and thesis evidence documents.

## Source Notes
- Built from `git log --all --reverse`, commit stats, dated reports, model/training artifacts, and thesis evidence files.
- Entries are ordered newest first so the current day stays visible at the top.
- Duplicate or parallel branch commits are consolidated by actual work date so the log describes the work, not every repeated hash.
- Commit hashes below are evidence anchors, not a complete dump of every repeated or merge-only hash.

---

## April to June 2026 Master To-Do List (Start: 2026-04-15)

Shalim note: this is the master thesis-completion to-do list and must be reviewed/updated in each future worklog update.

### Status Legend
- `OPEN`: not started
- `IN_PROGRESS`: currently active
- `DONE`: completed and validated
- `BLOCKED`: waiting on dependency/decision

### Workstreams and Tasks

| ID | Status | Task | Expected Output / Evidence | Target Window |
|---|---|---|---|---|
| A1 | OPEN | Create and use one dedicated branch for this full April-June execution wave | New branch created and all related commits isolated there | Apr 15-16 |
| A2 | OPEN | Validate newly developed synthetic data through the full pipeline end-to-end | Synthetic-vs-real pipeline run report with metrics and failure notes | Apr 15-25 |
| A3 | OPEN | Evaluate confidence behavior on synthetic and production-like runs | Confidence trend tables and threshold-hit analysis | Apr 15-30 |
| A4 | OPEN | Decide and test retraining-loop activation logic (triggered vs not triggered) | Retraining loop decision matrix and trigger-case evidence | Apr 20-May 10 |
| A5 | OPEN | Execute retraining loop materialization (artifacts/models) and verify Docker path | Reproducible retraining run logs + Docker run instructions/results | Apr 20-May 15 |
| A6 | OPEN | Clean up extra/unnecessary MLflow metrics and keep only thesis-critical tracking | MLflow metric schema cleanup note and updated tracking outputs | Apr 18-May 05 |
| A7 | OPEN | Compare all meaningful preprocessing/config combinations to identify best base config | Config sweep matrix + selected baseline config with rationale | Apr 18-May 12 |
| A8 | OPEN | Update FastAPI Web UI with confirmed analysis and pipeline status visibility | UI update showing key metrics/status and user-facing checks | Apr 25-May 20 |
| A9 | OPEN | Confirm CI/CD requirement: needed now vs optional/future phase | CI/CD decision note (required/not required) with justification | May 01-May 15 |
| A10 | OPEN | Confirm pseudo-labeling usage strategy (benefits, risks, when to use) | Pseudo-labeling decision brief with evidence | May 01-May 20 |
| A11 | OPEN | Confirm AdaBN strategy and practical value for this pipeline | AdaBN applicability note and experiment-backed recommendation | May 01-May 20 |
| A12 | OPEN | Provide citation-based justification for each and every operational threshold | Threshold-to-citation mapping document for defense questions | May 05-Jun 05 |
| A13 | OPEN | Extract and finalize output charts/figures for thesis writing | Thesis-ready figure pack with naming and chapter mapping | May 10-Jun 10 |
| A14 | OPEN | Debug and harden each major code path in repository (core pipeline first) | Bug-fix log, validation notes, and updated tests where needed | Apr 15-Jun 15 |
| A15 | OPEN | Document/verify complete dataflow understanding from 0% to 200% depth (ingest to deploy decisions) | End-to-end dataflow map/checklist with checkpoints | Apr 15-May 30 |
| A16 | OPEN | Prepare repo narrative for MLOps positioning: proof-of-concept vs production-readiness | Thesis narrative section + future-work framing | May 15-Jun 20 |
| A17 | OPEN | Build literature base to target range (75 to 85 papers) and keep chapter mapping traceable | Chapter-wise literature tracker with used/candidate lists | Apr 15-Jun 20 |
| A18 | OPEN | Deliver thesis draft target range (80 to 120 pages) including visual evidence | Structured chapter page plan + image insertion tracker | Apr 20-Jun 25 |
| A19 | OPEN | Ensure all major new experiments are explicitly framed either as validated result or future work | Results-vs-future-work decision register | May 15-Jun 25 |
| A20 | OPEN | Repo readiness pass: reproducibility, documentation, and final evidence organization | Final repo-readiness checklist and sign-off block | Jun 10-Jun 30 |

### Milestone Plan

| Milestone | Date Window | Focus |
|---|---|---|
| M1 | Apr 15-Apr 30 | Branch setup, synthetic data validation, confidence checks, config-sweep start |
| M2 | May 01-May 31 | Retraining-loop verification, pseudo-labeling/AdaBN decisions, threshold-citation grounding, UI and CI/CD decisions |
| M3 | Jun 01-Jun 30 | Thesis figure pack, final narrative, repo hardening, readiness closure |

### Reminder Rule
- On every future worklog update, update this table first (status + evidence pointer) before adding daily work details.

---

## 2026-04-01

### Session Trail (uncommitted worklog update)
- Repository reorganization and analysis-packaging actions executed in local session.
- Data-fit and dataset-comparison artifacts moved into `main/data_comparison/`.
- Main analysis workspace guide added at `main/README.md`.

### Work Completed
- Consolidated data-comparison outputs into a single thesis/report-ready workspace:
  - moved `data_fit_*` artifacts from repo root to `main/data_comparison/`
  - moved `dataset_comparison_analysis.ipynb` to `main/data_comparison/`
  - moved `_write_notebook.py` to `main/data_comparison/`
- Verified file consolidation state:
  - root no longer contains duplicate `data_fit_*`, `dataset_comparison_analysis.ipynb`, or `_write_notebook.py`
  - inventory under `main/data_comparison/` is now the canonical analysis bundle
- Added a practical usage guide for writing/reporting:
  - created `main/README.md`
  - documented all analysis files and what each file supports
  - included chapter-wise mapping for thesis usage (data, implementation, monitoring, experiments, conclusions)
  - added reproducibility command for regenerating analysis outputs
- Carried forward today’s analysis context (late 31-March + 1-April continuity):
  - deep data-fit diagnostics and harmonized metrics now represented by the packaged CSV/JSON artifacts
  - final charts for scale, quantiles, and transform ranking are grouped in one location for direct thesis insertion
  - citation-backed and defense-mapping outputs are now indexable from one folder

### Why
- Root-level analysis files were scattered, making thesis/report reuse error-prone.
- A single canonical folder and guide were needed so all evidence files could be found, cited, and reused consistently.

### Validation
- Confirmed `main/data_comparison/` contains:
  - notebooks: `data_fit_analysis.ipynb`, `dataset_comparison_analysis.ipynb`
  - script/helper files: `data_fit_analysis_helper.py`, `_write_notebook.py`
  - metrics and summaries: harmonized metrics, transform scores, calibration parameters, barriers/actions, chapter-defense mapping, citation-based comparison, and summary JSON
  - figures: `data_fit_chart_scale.png`, `data_fit_chart_quantiles.png`, `data_fit_chart_transform_scores.png`
- Confirmed `main/README.md` exists and includes:
  - full inventory table
  - report/thesis usage workflow
  - chapter mapping guidance

### Outcome
- Analysis evidence is now packaged under one stable path: `main/data_comparison/`.
- The main workspace has a clear guide (`main/README.md`) for thesis/report integration.
- Today’s work is now captured as one consolidated dated block for traceability.

---

## 2026-03-30

### Commit Trail
- `efac93a` finalize consistency fixes and `src/scripts` cleanup audit
- `6f1397d` finalize leftover repo hygiene updates
- `7480187` resolve CI lint failures (`isort` and `.gitignore` parse)
- `bef9b1f` cleanup work landed in `main`

### Work Completed
- Finalized the consistency-fix wave and the `src` vs `scripts` audit:
  - expanded `docs/RUNTIME_DEPENDENCY_MAP.md`
  - added `docs/SRC_SCRIPTS_CLEANUP_PLAN.md`
  - added `docs/SRC_SCRIPTS_OVERLAP_MATRIX.md`
  - added `docs/SRC_SCRIPTS_RIGOROUS_AUDIT.md`
  - added `docs/SRC_SCRIPTS_SIMPLIFICATION_PLAN.md`
  - refreshed `docs/TRIGGER_POLICY_EXPLANATION.md`
  - added `docs/thesis/THRESHOLD_TRIGGER_JUSTIFICATION.md`
- Tightened the active runtime path around monitoring, preprocessing/training entrypoints, and trigger governance:
  - `scripts/post_inference_monitoring.py`
  - `scripts/preprocess.py`
  - `scripts/train.py`
  - `src/components/post_inference_monitoring.py`
  - `src/trigger_policy.py`
- Expanded guardrail coverage so the threshold and trigger-policy behavior matched the thesis-facing docs:
  - `tests/test_threshold_consistency.py`
  - `tests/test_trigger_policy.py`
- Refreshed thesis-facing result material after the consistency pass:
  - `thesis/tables/before_vs_after_26datasets.csv`
  - `thesis/chapters/before_vs_after_26datasets.md`
  - `thesis/chapters/ch7_experiments_evaluation.tex`
- Fixed the CI blockers that were still preventing a clean cleanup merge:
  - import ordering fixes
  - `.gitignore` parse fix
  - touched `src/api/app.py`, `src/evaluate_predictions.py`, `src/pipeline/production_pipeline.py`, `src/run_inference.py`, `src/train.py`, and `src/utils/label_mapping.py`
- Landed the cleanup branch into `main` and consolidated the end-of-March repo state:
  - removed tracked MiKTeX auto-install noise and other heavy accidental files
  - removed old monitoring-stack leftovers and dead modules/scripts
  - kept the new reproducibility, audit, and internal-workspace structure
  - carried forward refreshed registry/retrained artifacts, March training reports, thesis docs, and the repo-audit pack

### Why
- The repo still had overlap between `src/` and `scripts`, plus CI/lint friction that weakened reproducibility.
- Today was mostly a consolidation-and-correctness day so `main` matched the late-March evidence pack and thesis narrative.

### Validation
- Local lint-equivalent checks passed:
  - `flake8`
  - `black --check`
  - `isort --check-only`
- Smoke subset passed:
  - `tests/test_pipeline_integration.py`
  - `tests/test_trigger_policy.py`
  - `tests/test_threshold_consistency.py`
- Result: `37 passed`, `0 failed`, `1` non-blocking warning

### Outcome
- March 30 was the landing and cleanup day:
  - consistency and trigger-governance evidence were finalized
  - CI lint blockers were removed
  - the cleanup branch landed in `main`
  - the repo ended March in a thesis-usable state

### Additional Same-Day Update (Later Session, pre-live-testing prep)

### Work Completed
- Continued internal documentation consolidation and canonicalization work:
  - updated navigation and migration hubs
  - refreshed internal reference links and compatibility pointers
  - aligned workflow docs with chapter-level literature mapping
- Added chapter-wise literature mapping artifacts for thesis writing flow:
  - `internal/workflow/literature/README.md`
  - `internal/workflow/literature/chapter_buckets.md`
  - `internal/workflow/literature/archive_candidates.md`
- Synced thesis-facing related-work mapping and chapter context:
  - `thesis/chapters/ch2_background_related_work.tex`
  - `thesis/chapters/ch2_2_related_work_paper_map.md`
- Added practical thesis authoring/compilation operations docs:
  - `thesis/README.md` (step-by-step LaTeX workflow)
  - `thesis/build_thesis.ps1` (one-command build helper with `-Quick`, `-Clean`, `-OpenPdf`)
- Reviewed drift/trigger sigma governance in runtime code and docs to prepare safe experimental retraining planning (without executing live dataset testing).

### Validation
- File-level diagnostics for the thesis operation guide and helper script were clean after lint fixes.
- Runtime governance checks reconfirmed:
  - retraining stages are trigger-gated unless explicitly forced in code path
  - deployment stays off unless `--auto-deploy` is set
  - shared baseline promotion stays off unless `--update-baseline` is set

### Outcome
- Live dataset retraining test was intentionally deferred.
- Agreed next step is isolated experimentation first (branch/worktree), then commit/push only after review.

### Additional Same-Day Update (Thesis chapter-process synchronization)

### Work Completed
- Audited all thesis chapter files in `thesis/chapters/` against the current runtime process and governance docs.
- Expanded chapter text to align with current repository behavior and evidence flow:
  - `thesis/chapters/ch1_introduction.tex`
  - `thesis/chapters/ch2_background_related_work.tex`
  - `thesis/chapters/ch3_offline_mlops_architecture.tex`
  - `thesis/chapters/ch4_data_model_development.tex`
  - `thesis/chapters/ch5_pipeline_implementation.tex`
  - `thesis/chapters/ch6_monitoring_drift_retraining.tex`
  - `thesis/chapters/ch7_experiments_evaluation.tex`
  - `thesis/chapters/ch8_discussion_conclusion.tex`
- Added a thesis-local chapter synchronization index:
  - `thesis/CHAPTER_PROCESS_INDEX.md`
- Updated thesis authoring guide navigation to include the new index:
  - `thesis/README.md`

### Validation
- Cross-checked chapter statements against:
  - `run_pipeline.py`
  - `REPRODUCE.md`
  - `docs/PIPELINE_STAGE_MAP.md`
  - `docs/PIPELINE_DATA_FLOW_MAP.md`
  - `docs/TRIGGER_POLICY_EXPLANATION.md`
  - `docs/THESIS_CONSISTENCY_NOTES.md`
  - `docs/thesis/THESIS_EVIDENCE.md`

### Outcome
- Thesis chapter skeletons are now process-aligned with the current executable pipeline path and governance behavior.
- A single index now exists to keep chapter updates synchronized when runtime/process docs evolve.

---

## 2026-03-29

### Commit Trail
- `12b30b9` commit pending deletions for monitoring stack/dead modules/wave archives
- `f5727c3` end-of-March checkpoint before 26-dataset experiment
- `a3d00a7` thesis consistency alignment
- `fb3c9c9` reproduce guide, pipeline map, writing readiness, metric disclosures, and thesis docs pack

### Work Completed
- Staged and committed pending cleanup deletions for obsolete monitoring-stack configs, dead modules, and wave archives.
- Added thesis consistency and governance fixes:
  - aligned thresholds
  - added collapse-guard tests
  - documented Config D framing
  - standardized AdaBN framing in thesis-facing docs
- Added thesis/reporting docs:
  - `REPRODUCE.md`
  - `docs/PIPELINE_DATA_FLOW_MAP.md`
  - `docs/PIPELINE_STAGE_MAP.md`
  - `docs/RUNTIME_DEPENDENCY_MAP.md`
  - `docs/THESIS_CONSISTENCY_NOTES.md`
  - `docs/thesis/METRIC_DISCLOSURES.md`
  - `docs/thesis/THESIS_WRITING_READINESS.md`
  - `docs/thesis/THRESHOLD_TRIGGER_JUSTIFICATION.md`
- Ran the 26-session baseline-vs-modified comparison and saved:
  - `thesis/tables/before_vs_after_26datasets.csv`
  - `thesis/chapters/before_vs_after_26datasets.md`
- Recorded the negative-result summary:
  - `25/26` successful runs in both variants
  - mean confidence unchanged at `0.8578`
  - dominant-class share reduced by about `13.83` percentage points
  - review share increased by about `63.55` percentage points
  - one session failed in both variants because accelerometer input was empty
- Generated the main March 29 audit pack under `reports/repo_audit/`, including:
  - `FULL_REPOSITORY_AUDIT_2026-03-29.md`
  - `THESIS_CRITICAL_AUDIT_2026-03-29.md`
  - `SAFE_CLEANUP_PLAN_2026-03-29.md`
  - `PREDICTION_DOMINANCE_ROOT_CAUSE.md`
- Captured final comparison/evidence runs in:
  - `artifacts/20260329_*`
  - `logs/pipeline/pipeline_result_20260329_*.json`

### Outcome
- March 29 became the main thesis-evidence checkpoint:
  - honest negative result documented
  - trigger/collapse behavior justified
  - audit trail created
  - reproducibility docs added

---

## 2026-03-28

### Commit Trail
- `a2c0478` wire Stage 5 collapse signal into trigger and force `REVIEW` on dominance over 95 percent

### Work Completed
- Connected Stage 5 collapse signals into Stage 7 trigger governance.
- Formalized the collapse path so dominant single-class output gets routed to `REVIEW` instead of silent pass-through.
- Ran the preprocessing ablation experiment across production sessions.
- Saved ablation outputs:
  - `outputs/ablation/ablation_results.csv`
  - `outputs/ablation/ablation_summary.csv`
  - `outputs/ablation/ablation_errors.json`
- Compared four preprocessing configs:
  - A: no gravity removal, no calibration
  - B: calibration only
  - C: gravity removal only
  - D: gravity removal plus calibration
- Observed from the saved summary:
  - Config D had the most diverse predictions
  - Config D reduced `hand_tapping` dominance the most vs baseline A
  - Config C worsened collapse
- Produced per-session ablation run trees under `outputs/ablation/runs/`.
- Generated the first adapted ablation-model snapshots, including `adabn_adapted_model_configD_20260328_232204.keras`.

### Outcome
- March 28 connected governance fixes with real experiment evidence instead of only code-level changes.

---

## 2026-03-27

### Commit Trail
- `5285f9f` simplify root, fix README, keep worklog/TODO, add duplicate audit
- `cf098df` stop tracking local worklog
- `1bd16d9` create internal workspace and move non-core materials
- `f794d2c` normalize archive into internal workspace
- `4a9428d` archive alternate inference/core path and finalize wave-2 decisions

### Work Completed
- Simplified the repo root and moved non-core working material into structured internal folders:
  - `internal/notes/`
  - `internal/reference/`
  - `internal/workflow/`
  - `internal/writing/`
- Added:
  - `REPRODUCE.md`
  - `TODO.md`
  - `internal/INDEX.md`
- Moved many long-form notes, WHY docs, tech explainers, and audit support files out of the main docs surface and into `internal/`.
- Normalized archive material and snapshot material for later thesis traceability.
- Removed stale/dead modules and alternate architecture leftovers from the active path.
- Added or retained the main repo audit pack under `reports/repo_audit/`.
- Added `scripts/run_ablation_experiment.py` and `scripts/data_analysis/analyze_datasets.py` to support late-March experiment work.
- Added thesis result/table inputs:
  - `thesis/chapters/before_vs_after_26datasets.md`
  - `thesis/tables/before_vs_after_26datasets.csv`
  - root `thesis_execution_plan_mar_jun_2026.md`
- Saved new retraining reports:
  - `models/retrained/training_report_20260327_213930.json`
  - `models/retrained/training_report_20260327_223917.json`

### Model Snapshot Notes
- New March retraining snapshots existed by this point:
  - `har_model_20260327_213930.keras`
  - `har_model_20260327_223917.keras`
- Training-report metrics show:
  - best snapshot accuracy about `0.9326`
  - second registration snapshot accuracy about `0.9223`

### Outcome
- The repo was cleaned into a form that separated core reproducible assets from personal/internal working material.

---

## 2026-03-14

### Commit Trail
- `5f8ec27` wave-1 runtime proof and golden-run hotfixes
- `31cb3dc` thesis workflow docs and Chapter 1 citation baseline
- `307a411` thesis chapter placeholders 2-8
- `c2e18d2`, `da58123` thesis docs consolidation and LaTeX link/build updates
- `0d9cad5` runtime fixes, repo-audit evidence pack, and regression tests

### Work Completed
- Fixed/evidenced Stage 5 and Stage 7 behavior:
  - evaluation contract parsing
  - temporal-threshold pass-through
  - single-source activity label mapping
- Added `src/utils/label_mapping.py`.
- Added regression tests:
  - `tests/test_activity_label_mapping_single_source.py`
  - `tests/test_stage5_evaluation_summary_contract.py`
  - `tests/test_stage6_baseline_space_consistency.py`
  - `tests/test_trigger_threshold_pass_through.py`
- Verified and documented Stage 6 baseline-space mismatch, then fixed/validated it through:
  - `scripts/build_training_baseline.py`
  - `scripts/post_inference_monitoring.py`
  - `reports/repo_audit/WAVE2_BASELINE_SPACE_VERIFICATION.md`
  - `reports/repo_audit/WAVE2_STAGE6_BASELINE_SPACE_FIX_VALIDATION.md`
- Added repo-audit support documents:
  - broken links
  - archive scans
  - move log
  - root cause note
  - src/scripts audit/refactor plan
- Added thesis workflow docs and LaTeX manuscript scaffold:
  - `docs/thesis/DEFENSE_PLAN.md`
  - `docs/thesis/EXPERIMENT_PLAN.md`
  - `docs/thesis/THESIS_EVIDENCE.md`
  - `docs/thesis/THESIS_WORKFLOW_MAR_JUN_2026.md`
  - `thesis/main.tex`
  - `thesis/references.bib`
  - `thesis/chapters/ch1_introduction.tex`
  - placeholder chapters `ch2` to `ch8`

### Outcome
- March 14 linked runtime correctness work directly to thesis writing readiness.
- The repo gained both stronger governance tests and the first serious manuscript structure.

---

## 2026-03-06

### Commit Trail
- `6c5ae28` final src/docs/library/worklog refactor
- `4cab0a0` robust multi-route CD smoke test
- `2e87fba` Docker fix to `COPY src/` and run `src.api.app`
- `337cefd`, `d247c7c`, `b022c3c` lint/flake8 cleanup
- `56c969a`, `6209faa`, `3984379`, `e28b3eb` Docker image/smoke-test fixes
- `ab4b989` generated-artifact cleanup
- `d21e5ad`, `f50955e`, `f1ead47` duplicate-paper audit and action plan
- `bc572a6` stage manifest and README architecture update
- `e29e17f` trigger policy docs and dominance warning wiring

### Work Completed
- Refactored `src/` into clearer domain packages:
  - `src/data/`
  - `src/inference/`
  - `src/monitoring/`
  - `src/training/`
  - `src/deployment/`
- Added/updated backward-compatible paths while moving active modules into the new package layout.
- Reorganized docs into:
  - `docs/01_PIPELINE/`
  - `docs/02_TECH/`
  - `docs/03_EXPERIMENTS/`
  - `docs/04_THESIS_WRITING/`
  - `docs/99_ARCHIVE/`
- Created the first tracked worklog file.
- Fixed Docker inference after the API moved:
  - `COPY src/` instead of `COPY api/`
  - run `uvicorn src.api.app:app`
  - adjust health checks and build context
- Added a more robust CD smoke test that tries multiple routes instead of assuming one endpoint.
- Added trigger-policy explanation docs and strengthened dominance-warning reporting in evaluation/MLflow.
- Added stage manifest updates to `run_pipeline.py` and refreshed README architecture sections.
- Added duplicate-paper detection tooling and reports under `reports/repo_audit/`.
- Performed large lint, format, and CI cleanup passes.

### Validation
- `python -m compileall src -q` clean
- `pytest -q` passed with `258/258`

### Outcome
- This was one of the biggest structural refactors in the repo.
- The repo became much easier to explain as a thesis system and much easier to maintain.

---

## 2026-03-05

### Commit Trail
- `42c740d` March planning and deep-dive docs pack
- `2705be5` CI fixes
- `caba9f0` split CI/CD workflows
- `b7af1cf` CD and inference Docker fixes

### Work Completed
- Generated a large March deep-dive documentation pack covering:
  - data pipeline flow
  - `src/` deep dive
  - scripts reference
  - tests reference
  - config/deps/infra map
  - artifact source mapping
  - normalization analysis
- Added defense, evidence, WHY, and thesis-tech explainer docs in bulk.
- Added Grafana, Prometheus, alertmanager, and dashboard config files.
- Added threshold/benchmark scripts and tests:
  - `scripts/threshold_sweep.py`
  - `scripts/trigger_policy_eval.py`
  - `scripts/run_ab_comparison.py`
  - `tests/test_threshold_consistency.py`
  - `tests/test_config_loader.py`
  - `tests/test_validation_gate.py`
  - more related support tests
- Split the old combined CI/CD workflow into separate `ci.yml` and `cd.yml`.
- Fixed CD startup behavior and Docker inference configuration.

### Outcome
- March started with a heavy documentation and infrastructure pass, plus a cleaner CI/CD separation.

---

## 2026-02-25 to 2026-02-26

### Commit Trail
- `1debabf` MiKTeX installation
- `2568191` README and model-registry refresh

### Work Completed
- Installed MiKTeX and brought LaTeX support into the working environment.
- Updated `README.md`.
- Refreshed registry/retrained-model artifacts:
  - `models/registry/har_model_vauto.keras`
  - `models/registry/model_registry.json`
  - `models/retrained/pseudo_label_model.keras`

### Outcome
- Thesis compilation tooling became locally available and model-registry artifacts were refreshed.

---

## 2026-02-22 to 2026-02-23

### Commit Trail
- `cf9c036`, `c98b45c` align code/docs to 11 anxiety behavior classes
- `5c38f65` align `train.py` architecture to pretrained model
- `7f892d8`, `e9b19cd`, `edbc399` CI/CD route and Docker path fixes
- `380e455`, `6a152e7`, `21d7bdf` config and README corrections
- `13d1c35` black formatting fix for `train.py`
- `e336770` Stage 11/TTA governance fallback
- `c4b4994`, `b92ae0a` `psi_warn` to `drift_zscore_warn` rename and Stage 7 fix
- `f55dbbe` move thesis writing docs to local-only area

### Work Completed
- Replaced the wrong PAMAP2-style class list with the correct 11 anxiety behavior classes in active code and tests.
- Updated `src/active_learning_export.py`, `tests/conftest.py`, and README/docs to match the corrected class set.
- Corrected model-architecture references from approximately `1.5M` or `850K` style numbers down to the actual deployed architecture around `499K` parameters.
- Fixed Docker/App pathing to use `src/api/app.py` correctly.
- Replaced fixed sleep-based CI waiting with a poll loop.
- Corrected health endpoint usage to `/api/health`.
- Fixed Docker shadowing issues and `PYTHONPATH` handling.
- Reformatted `train.py` to satisfy `black`.
- Fixed Stage 11 crash behavior in the TTA governance path.
- Renamed PSI-style drift warning config to z-score-based naming and wired Stage 7 to the new field.
- Moved thesis-writing materials into a local-only/gitignored path to reduce repo noise.

### Outcome
- The pipeline, docs, model description, and deployment path were finally aligned around the correct 11-class thesis problem.
- Test suite status at this point: `215` passing.

---

## 2026-02-19

### Commit Trail
- `34f80df` baseline + metric-loss fixes
- `700381a` missing baseline builder, normalized baseline, CLI exposure
- `bd8dc1e` PSI/schema hardening
- `1ae27cc` split unit/slow tests
- `3fd3c00` thesis closure docs and pseudo-label fix
- `f47a48b`, `e2bc784` TENT, rollback, baseline governance, GPU, MLflow fixes
- `b84e583`, `168c05b` documentation reorganization

### Work Completed
- Fixed baseline update and retraining behavior around metric loss.
- Added/standardized baseline tooling and saved normalized baseline artifacts.
- Added `src/domain_adaptation/tent.py` and improved TENT handling.
- Hardened Stage 6 with schema guards and baseline-copy behavior.
- Split tests into faster unit paths and slower TensorFlow-heavy paths.
- Fixed pseudo-label pipeline safety issues.
- Fixed TENT running-stat freezes and rollback behavior.
- Prevented unsafe writes into `models/` when promotion should not happen.
- Improved GPU diagnostics and MLflow run handling.
- Reorganized February docs into `docs/19_Feb/` and then broader archive/technical/research/thesis buckets.

### Outcome
- This was a major reliability/hardening checkpoint for monitoring, adaptation, retraining, and reproducibility.

---

## 2026-02-15 to 2026-02-16

### Commit Trail
- `647c893` FastAPI upload/inference/monitoring UI
- `4bfbb08` progress tracking consolidation
- `7463cc2` production-ready CI/CD
- `daad751` GitHub Actions setup complete
- `8b4dab7` lowercase image naming for GHCR
- `d263058`, `7e51e8d`, `96717a4` thesis/monitoring docs and next-step cleanup

### Work Completed
- Added the FastAPI serving layer:
  - `src/api/app.py`
  - `src/api/__init__.py`
- Added a web UI path for CSV upload, inference, and monitoring review.
- Added and configured GitHub Actions CI/CD.
- Fixed Docker image naming for GitHub Container Registry compliance.
- Consolidated progress tracking docs into a more consistent structure.
- Finished a major monitoring-docs pass and recorded next-step MLflow follow-ups.

### Outcome
- The project gained its API/demo layer and automated delivery workflow.

---

## 2026-02-14

### Commit Trail
- `e39f7d7` fix all tests, integrate monitoring, add production optimizations

### Work Completed
- Brought the test suite to a clean `225/225`.
- Expanded monitoring and advanced pipeline features:
  - `src/calibration.py`
  - `src/components/calibration_uncertainty.py`
  - `src/components/curriculum_pseudo_labeling.py`
  - `src/components/sensor_placement.py`
  - `src/components/wasserstein_drift.py`
  - `src/curriculum_pseudo_labeling.py`
  - `src/robustness.py`
  - `src/sensor_placement.py`
  - `src/wasserstein_drift.py`
- Added shared utility modules:
  - `src/utils/artifacts_manager.py`
  - `src/utils/common.py`
  - `src/utils/main_utils.py`
  - `src/utils/production_optimizations.py`
- Added packaging metadata:
  - `pyproject.toml`
  - `setup.py`
- Added operational scripts:
  - `scripts/preprocess.py`
  - `scripts/train.py`
  - `scripts/update_progress_dashboard.py`
  - `scripts/verify_repository.py`
- Added more implementation and thesis docs around ingestion, CI/CD, preprocessing comparison, and chapter drafting.
- Removed a large amount of heavy paper/archive clutter from active tracking.

### Outcome
- The pipeline became more stable, better tested, and more production-oriented.

---

## 2026-02-12

### Commit Trail
- `fc06452`, `8632082`, `3b5fc41` 10-stage pipeline and AdaBN build-out
- `094a921`, `8d8de1d`, `1918333` large-file cleanup and ignore hardening

### Work Completed
- Built the complete 10-stage MLOps pipeline around `run_pipeline.py`.
- Added the active component architecture:
  - `src/components/data_ingestion.py`
  - `src/components/data_transformation.py`
  - `src/components/data_validation.py`
  - `src/components/model_inference.py`
  - `src/components/model_evaluation.py`
  - `src/components/post_inference_monitoring.py`
  - `src/components/trigger_evaluation.py`
  - `src/components/model_retraining.py`
  - `src/components/model_registration.py`
  - `src/components/baseline_update.py`
- Added core pipeline/data structures:
  - `src/entity/artifact_entity.py`
  - `src/entity/config_entity.py`
  - `src/pipeline/production_pipeline.py`
  - `src/pipeline/inference_pipeline.py`
- Added domain-adaptation and governance pieces:
  - `src/domain_adaptation/adabn.py`
  - `src/model_rollback.py`
  - `src/ood_detection.py`
  - `src/trigger_policy.py`
  - `src/deployment_manager.py`
- Added broad test coverage across preprocessing, drift, rollback, retraining, trigger behavior, and integration.
- Added early CI/CD and monitoring stack files:
  - `.github/workflows/ci-cd.yml`
  - Prometheus/Grafana/alert configs
- Added stage-by-stage documentation and thesis/planning docs for the pipeline.
- Removed large CSV/image/model files from direct Git tracking and pushed more of that burden into ignore rules/DVC handling.

### Outcome
- This was the first full thesis-grade pipeline milestone.

---

## 2026-01-09 to 2026-01-25

### Commit Trail
- `515a0b7` docs and structure update
- `f65a8da` `.gitignore` and docs hierarchy update
- `402189f` additional repository, paper, and thesis analysis

### Work Completed
- Reorganized docs into clearer domains:
  - `docs/archive/`
  - `docs/research/`
  - `docs/technical/`
  - `docs/thesis/`
- Added navigation/meta docs:
  - `docs/README.md`
  - `docs/ORGANIZATION_MAP.md`
  - `HOW_TO_READ_THIS_REPOSITORY.md`
- Added monitoring and QC tooling:
  - `scripts/build_training_baseline.py`
  - `scripts/create_normalized_baseline.py`
  - `scripts/inference_smoke.py`
  - `scripts/post_inference_monitoring.py`
  - `scripts/preprocess_qc.py`
  - `src/diagnostic_pipeline_check.py`
- Added the first normalized baseline artifact `models/normalized_baseline.json`.
- Collected QC and monitoring outputs under `reports/preprocess_qc/` and `reports/monitoring/`.
- Added deeper thesis/paper analysis docs:
  - mentor Q and A
  - pipeline deep dive
  - repository cleanup analysis
  - thesis progress dashboard
- Added and later analyzed larger dataset and paper-tracking files during this phase.

### Why
- Needed a stronger monitoring baseline and reporting workflow.
- Needed docs that could support both debugging and thesis writing.

### Outcome
- By late January, the repo had baseline-building, QC, monitoring scripts, and much stronger documentation scaffolding.

---

## 2025-12-21

### Commit Trail
- `cba9ee4`, `5cdc938`

### Work Completed
- Added planning and reference files:
  - `LEARNINGS_FROM_REFERENCE_PROJECT.md`
  - `TODO_THIS_WEEK.md`
  - `WHAT_TO_DO_NEXT.md`
- Hardened `.gitignore`.
- Added extra design/reference images.

### Outcome
- Closed the December phase with clearer planning, stronger ignore rules, and a better idea of the next engineering steps.

---

## 2025-12-16

### Commit Trail
- `f36ff26` analysis/progress/stack update wave

### Work Completed
- Added thesis/project progress documentation:
  - `PROJECT_GUIDE.md`
  - `THESIS_PROGRESS_ANALYSIS.md`
  - `THESIS_PROGRESS_REPORT.md`
  - `Technology Stack Analysis.md`
  - updated `Thesis_Plan.md`
- Added organization and maintenance docs:
  - `docs/FILE_ORGANIZATION_SUMMARY.md`
  - `docs/FRESH_START_CLEANUP_GUIDE.md`
  - `docs/MARKDOWN_CLEANUP_GUIDE.md`
  - `docs/PIPELINE_RERUN_GUIDE.md`
  - `docs/RESEARCH_PAPER_INSIGHTS.md`
- Added preprocessed working-state data files under `data/preprocessed/`.
- Updated `config/pipeline_config.yaml`.
- Added `dvc_experiments.html` plus a large figure/image set for architecture and thesis communication.
- Imported and organized a much larger paper set plus paper summaries under `research_papers/`.
- Updated active source files:
  - `src/preprocess_data.py`
  - `src/run_inference.py`
  - `src/sensor_data_pipeline.py`

### Outcome
- The repository became both an engineering workspace and a thesis-knowledge workspace.

---

## 2025-12-11 to 2025-12-12

### Commit Trail
- `450ebf0`, `52266cf` documentation reorganization
- `037e62b`, `21aaec5` MLOps infrastructure with DVC, MLflow, and Docker
- `2d185e6`, `d49c34f` repo reform and archival cleanup

### Work Completed
- Reorganized docs and added deeper analysis docs such as:
  - `docs/PATH_COMPARISON_ANALYSIS.md`
  - `docs/RESEARCH_PAPERS_ANALYSIS.md`
- Created a large `docs/archived/` area to separate active docs from old problem-solving notes.
- Added DVC foundations:
  - `.dvc/`
  - `data/raw.dvc`
  - `data/processed.dvc`
  - `data/prepared.dvc`
  - `models/pretrained.dvc`
- Added MLOps config files:
  - `config/mlflow_config.yaml`
  - `config/pipeline_config.yaml`
- Added containerization and runtime orchestration:
  - `docker-compose.yml`
  - `docker/Dockerfile.inference`
  - `docker/Dockerfile.training`
  - `docker/api/main.py`
- Added `src/mlflow_tracking.py` and `src/data_validator.py`.
- Moved large raw data and model artifacts out of direct Git tracking toward DVC pointers.
- Added a gravity-removal demo notebook and strengthened the `.gitignore`/`.dockerignore` setup.
- Archived a large number of no-longer-primary guidance docs into `docs/archived/`.

### Why
- The project needed proper MLOps foundations:
  - data versioning
  - experiment tracking
  - containerized runtime
- The documentation had become too noisy to support continued engineering work.

### Outcome
- This was the moment the repo became a real MLOps repository rather than a collection of scripts and notebooks.

---

## 2025-12-06 to 2025-12-08

### Commit Trail
- `1c403f8`, `d8c79f9` unit-conversion solution phase
- `215f1f0`, `1c10a2f` Phase 2 inference and evaluation pipeline

### Work Completed
- Solved the unit-conversion problem between production data and training expectations.
- Added `src/preprocessing/convert_production_units.py`.
- Generated converted fused data (`data/processed/sensor_fused_50Hz_converted.csv`) and a unit-conversion log.
- Added `docs/UNIT_CONVERSION_SOLUTION.md` and a comparison notebook to verify the conversion.
- Moved paper files into a dedicated `research_papers/` workspace.
- Completed the first proper inference/evaluation phase:
  - `src/preprocess_data.py`
  - `src/run_inference.py`
  - `src/evaluate_predictions.py`
  - `src/compare_data.py`
- Added `data/prepared/production_metadata.json` and supporting prepared-data docs.
- Reorganized notebooks into clearer top-level names and added `notebooks/README.md`.
- Archived older one-off preprocessing scripts instead of leaving them mixed into the active path.

### Why
- Production data could not be trusted until the sensor-unit mismatch was resolved.
- After preprocessing stabilized, inference and evaluation needed to become first-class modules rather than notebook steps.

### Outcome
- The repository moved from "preprocess and inspect" into an actual inference/evaluation pipeline.

---

## 2025-11-28

### Commit Trail
- `3a07e4f`, `b6e249a` acceleration distribution error review

### Work Completed
- Investigated acceleration-distribution problems and refreshed the project status around that issue.
- Reworked `README.md` and added `CURRENT_STATUS.md` and `REPO_STRUCTURE.md`.
- Added paper/resource spreadsheets and image references for research tracking.
- Deleted older restructuring summaries that were no longer helping current work.

### Outcome
- The acceleration-distribution issue was promoted from a vague suspicion to an explicit tracked problem in the repo narrative.

---

## 2025-11-05

### Commit Trail
- `c17f3dd`, `806ea9e` data-path and repo-structure rewrite around accelerometer mismatch
- `4af0d20`, `2711bcb` ignore main-data artifacts

### Work Completed
- Renamed the repository out of the numbered-folder layout into a more standard structure:
  - `config/`
  - `data/`
  - `docs/`
  - `models/`
  - `notebooks/`
  - `src/`
- Added runtime/config foundations:
  - `src/config.py`
  - `src/preprocessing/prepare_production_data.py`
  - `src/preprocessing/prepare_training_data.py`
- Added prepared-data metadata and split train/val/test metadata JSONs under `data/prepared/`.
- Added fused and merged processed sensor CSVs under `data/processed/`.
- Added the raw accelerometer and gyroscope source pair used for comparison/debugging.
- Added the pretrained model artifact `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`.
- Wrote problem-analysis docs around:
  - critical model issues
  - dataset difference summary
  - data leakage concerns
  - unlabeled production usage
- Added evaluation logs and summary text for cross-user review.
- Updated `.gitignore` to stop tracking the main-data copy.

### Why
- The repo had already reached the point where production data handling and training data handling needed to be separated clearly.
- There was an active mismatch between production and main accelerometer behavior that needed direct evidence.

### Outcome
- This was the first major data-integrity debugging milestone.
- The repo became more operational and much less notebook-only.

---

## 2025-10-23 to 2025-10-25

### Commit Trail
- `2679477` initial scaffold with preprocessing pipeline
- `f60fe0d` README cleanup on the same day
- `fa6cd2b` excluded documentation from Git

### Work Completed
- Created the original repository scaffold with numbered folders:
  - `01_data/`
  - `02_src/`
  - `03_models/`
  - `04_notebooks/`
  - `07_docs/`
  - `08_config/`
- Implemented the first preprocessing pipeline in `02_src/preprocessing/sensor_data_pipeline.py`.
- Added early analysis helpers:
  - `02_src/analysis/analyze_data.py`
  - `02_src/analysis/inspect_model.py`
- Added sample fused 50 Hz sensor data and metadata.
- Added first exploratory notebooks for preprocessing and data inspection.
- Added the first `README.md`, `.gitignore`, requirements, and project/mentor planning docs.
- On October 25, hardened `.gitignore` to keep progress/private documentation out of Git.

### Outcome
- The project started as a preprocessing-first repository with a working structure, sample data, and a clear early roadmap.

---

## High-Level Progress Summary Through 2026-03-30

### Phase 1 - Bootstrapping
- Initial repo scaffold, first preprocessing pipeline, notebooks, and sample fused data.

### Phase 2 - Data Integrity and Inference
- Production/training data mismatch analysis, unit conversion fix, preprocessing, inference, and evaluation pipeline.

### Phase 3 - MLOps Foundations
- DVC, MLflow, Docker, config standardization, baseline tooling, monitoring scripts, QC, and CI/CD setup.

### Phase 4 - Full Thesis Pipeline
- 10-stage MLOps pipeline, AdaBN domain adaptation, rollback/governance, broad tests, FastAPI serving layer.

### Phase 5 - Hardening and Thesis Readiness
- 11-class correction, Docker/API/CI fixes, baseline governance, Stage 5/6/7 evidence fixes, collapse guard, ablation experiments, reproducibility docs, audit pack, and repo cleanup.

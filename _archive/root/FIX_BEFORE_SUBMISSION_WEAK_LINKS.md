# Fix Before Submission - Action Board

Date: 2026-04-21  
Simplified: 2026-04-23  
Last refresh: 2026-04-25 (Chapter 4 rewrite + April-report polish landed; tracker rolled forward)  
Purpose: one readable board for what must be fixed, verified, documented, or parked before submission.

This file is not thesis prose. It is the control board. If a task produces important evidence or an important design decision, it must later appear in the thesis/report, README, or submission summary.

## How To Use This File

Every task should end with four answers:

| Question | Meaning |
| --- | --- |
| What changed? | Code, config, data, docs, or evidence |
| Where is the proof? | Test result, report file, artifact path, screenshot, log, or command output |
| Should it go in the thesis/report? | Yes, no, or future work |
| Where should it be written? | Ch4, Ch5, Ch6, Ch7, Ch8, README, REPRODUCE, or submission summary |

Rule: if the work changes the defended story, it belongs in the report. If it is only cleanup, archive hygiene, or local convenience, it usually belongs in README/REPRODUCE or nowhere.

Hard model-policy rule:
- Use the mentor-provided pretrained model as default across pipeline/API/Docker.
- Retrain/fine-tune only when labeled data is available for evaluation.
- Promote a new model only when labeled comparison proves it outperforms the current default.
- If equal or worse, do not promote.

## Current Priority

Start with pipeline evidence, not report polishing.

| Order | Task | Status | Why it matters | Output |
| --- | --- | --- | --- | --- |
| 1 | A7 - Z-score normalization vs no normalization | IN PROGRESS | Proves the defended preprocessing choice | Config comparison evidence |
| 2 | A4 - Retraining activation decision matrix | OPEN | Proves when the system says NONE, REVIEW, or RETRAIN | Decision matrix + trigger evidence |
| 3 | A5 - Execute retraining loop + Docker path | OPEN | Proves retraining is executable, not just described | Logs, artifacts, Docker note |
| 4 | A8 - FastAPI status/UI visibility | IN PROGRESS | Helps demo and explain local serving | API/UI evidence |

Report-only work is parked until these are stable.

## Track 1 - Pipeline Evidence Now

### A7 - Z-Score Normalization vs No Normalization

Status: IN PROGRESS  
Priority: P0  
Report impact: yes, Ch4 and Ch7

Goal: prove why the defended pipeline keeps `enable_normalization: true` and `normalization_variant: "zscore"`.

Do:
- Run or consolidate a comparison between z-score normalization and no normalization.
- Use the same model and same input session(s).
- Save config, input path, model path, confidence, dominant-class share, review percentage, trigger decision, and failure behavior.

Write later:
- Ch4: training/serving parity and preprocessing design.
- Ch7: experiment result showing why no-normalization is not the defended path.

### A4 - Retraining Activation Decision Matrix

Status: OPEN  
Priority: P0  
Report impact: yes, Ch6

Goal: make retraining governance explicit.

Matrix cases to prove:
- healthy input -> `NONE`
- warning input -> `REVIEW` or no automatic retrain
- valid retrain trigger -> retraining allowed
- dominant-class collapse -> `REVIEW`, not blind retrain
- cooldown active -> retrain blocked
- labels missing -> retrain blocked or marked ineligible
- bad candidate model -> registration/deployment blocked

Output:
- one small decision table
- evidence files or trigger reports for each important path

### A5 - Execute Retraining Loop And Docker Path

Status: OPEN  
Priority: P0  
Report impact: yes, Ch5 and Ch6

Goal: prove retraining can run reproducibly.

Do:
- Run the retraining path with controlled input.
- Capture logs, output model path, MLflow run if active, metrics, and registration decision.
- Verify whether the same path works through `docker/Dockerfile.training` or `docker-compose.yml` training profile.

Output:
- retraining evidence report under `reports/`
- exact commands
- final artifact paths
- Docker reproducibility note

### A8 - FastAPI Status/UI Visibility

Status: IN PROGRESS  
Priority: P1 after A7/A4/A5  
Report impact: yes, Ch5; maybe README

Already proved:
- `/docs`, `/api/health`, `/api/model/info`, and `/api/upload` returned HTTP 200 on 2026-04-23.
- Evidence: `reports/api_operational_smoke_2026-04-23.md`.
- API supports fused CSV and raw accelerometer + gyroscope pair upload.

Remaining:
- Browser screenshots only if required.
- Docker-level browser/API proof only if required.
- UI should not block A7/A4/A5.

## Track 2 - Docker, Environment, And Reproducibility

| Task | Status | Report impact | Notes |
| --- | --- | --- | --- |
| Docker image size | OPEN | Maybe Ch5/README | Current inference image is about 4.5GB; biggest layer is pip dependencies |
| Lightweight inference requirements | OPTIONAL | README/REPRODUCE if done | Do only if Docker size matters for submission |
| Explain two Dockerfiles | OPEN | Ch5/README | `Dockerfile.inference` serves FastAPI; `Dockerfile.training` supports training/retraining |
| Explain Docker Compose | OPEN | Ch5/README | Compose starts MLflow, inference API, and optional training profile |
| Submission environment | OPEN | REPRODUCE/README | Recommend documenting `thesis-mlops` conda env with Python 3.11; do not submit `.conda/` |
| `pyproject.toml` vs `setup.py` | OPEN | README/REPRODUCE | `pyproject.toml` is canonical; `setup.py` is compatibility shim |

Recommended environment answer:
- Submit code, requirements/config, DVC pointers, and reproducibility commands.
- Do not submit the full virtual environment or `.conda/` folder.
- If exact dependency capture is needed, export an `environment.yml` from the working `thesis-mlops` environment later.

## Track 3 - Data Explanation For Report

| Topic | Status | Report location | What to explain |
| --- | --- | --- | --- |
| Fused data | OPEN | Ch4/Ch5 | Raw accelerometer + gyroscope streams are aligned/resampled/merged into one table for windowing |
| Synthetic data | OPEN | Ch4/Ch7 | Created for stress testing monitoring behavior, not for real accuracy claims |
| Own data A21-A24 | OPEN | Ch4/Ch7 only if complete | Include only if capture, QC, evaluation, and comparison are finished |

Fused data explanation should cover:
- where fused files live
- how raw sensor pairs become fused CSV
- how unit conversion, normalization, and windowing happen after fusion
- how this connects to `/api/upload`

Synthetic data explanation should cover:
- why it was created
- how it was generated
- how it helped test monitoring/trigger behavior
- what claims it does not support

## Track 4 - DVC, MLflow, Git, And Ignore Files

| Task | Status | Report impact | Notes |
| --- | --- | --- | --- |
| DVC restore story | OPEN | Ch5/REPRODUCE | Explain Git tracks code and `.dvc` pointers; DVC restores large data/model artifacts |
| DVC commands | OPEN | REPRODUCE | Document `dvc status`, `dvc pull`, `dvc checkout` |
| MLflow story | OPEN | Ch5/Ch6 | Explain runs, metrics, artifacts, retraining evidence |
| A6 MLflow metric cleanup | LOW | Maybe Ch5 | Do after A4/A5 evidence is stable |
| Ignore files audit | OPEN | README/REPRODUCE | Check `.gitignore`, `.dockerignore`, `.dvcignore`, `models/.gitignore` |

Do not delete `mlruns/` until final evidence is frozen.

## Track 5 - Folder Cleanup And Certification

Do not delete first. Certify first.

Classification labels:
- canonical source
- final evidence
- generated reproducible output
- historical note
- cache/temp
- unsafe to delete

Folders to certify:

| Folder | Current handling |
| --- | --- |
| `src/` | canonical implementation; do not archive |
| `scripts/` | keep experiment runners and generators; archive only after reference check |
| `tests/` | map tests to claims before removing anything |
| `models/` | simplify only after model paths are certified |
| `notebooks/` | keep if they reproduce final evidence; otherwise archive as exploration |
| `docs/` | keep useful maps/explanations; archive stale drafts |
| `internal/` | keep as internal reference; not submission-facing unless curated |
| `outputs/` | keep thesis figures/data; archive generated clutter |
| `reports/` | keep final evidence reports; archive pytest/temp runs |
| `logs/` | keep only logs that support evidence |
| `mlruns/` | keep until retraining/MLflow evidence is frozen |
| `main/` | inspect before deciding; likely historical/support material |

Obvious cleanup candidates after evidence transfer:
- `.tmp_pytest/`
- `outputs/pytest-*`
- `reports/pytest-*`
- `reports/tmp*`
- `tmp_run3/`
- root scratch files like `temp.txt` and `thesis_doc.txt`

Do not delete these yet if they contain evidence not copied into `reports/`, `WORKLOG.md`, or thesis files.

## Track 6 - Models Folder Simplification

Defended/default model:
- `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`

Important support artifacts:
- `models/normalized_baseline.json`
- `models/training_baseline.json`
- scaler config used by API/pipeline, if present

Candidate model policy:
- Retrained models are candidate artifacts, not automatic defaults.
- A candidate can become default only after labeled evaluation beats the current default model.

Before renaming or deleting any model:
- search code, Docker Compose, README, thesis, and tests for the path
- classify it as current, pretrained source, retrained current, registry artifact, historical comparison, negative result, or archive candidate
- record the decision

## Track 7 - Report Work Parked For Later

These are important, but not first.

| Task | Status | When to do |
| --- | --- | --- |
| A12 | parked | after pipeline evidence is stable |
| A13 | parked | after final figures/evidence are stable |
| A17 | parked | after technical story is stable |
| A18 | parked | after evidence and figures are stable |
| A32 | done/verify later | final consistency pass |
| A33 | parked | after A7/A4/A5 if table evidence is ready |
| A34 | parked | after data table facts are stable |

Lower priority:
- A6: MLflow metric cleanup
- A16: MLOps positioning narrative
- A19: results vs future-work separation
- A20: README and final repo readiness pass

## Already Done Or Mostly Done

| Item | Status |
| --- | --- |
| A27/A28 threshold alignment | DONE |
| Stage 6 z-score runtime drift story | DONE |
| MMD scoped as offline/experimental evidence | DONE |
| `/api/upload` endpoint wording | DONE |
| API localhost/TestClient smoke | DONE, evidence in `reports/api_operational_smoke_2026-04-23.md` |
| Default model path clarified | DONE |
| CI/CD wording bounded to CI + release-image smoke | DONE |
| Thesis build (full original report) | DONE in latest readiness pass |
| April-report Chapter 4 rewrite (11 sections, 10 figures, 4 generated tables, 5 in-chapter tables) | DONE 2026-04-25; backup `.bak` kept; active 2026-04-26 wording edits are scoped to the April report |
| April-report polish pass (title fix, mental-health-adjacent framing, SI units, row-count footnote, softened final-model split, compact stats table in Ch.4 with full table moved to Appendix D, preprocessing-baseline table tightened) | DONE 2026-04-25 |
| April-report build clean | DONE 2026-04-25 — `thesis/april_report/main.pdf` 52 pages, no undefined refs/citations, no LaTeX errors |
| Pipeline-hardening code paths (canonical scaler utility, train-only refit script, user-holdout training/eval scripts, chunked drift monitor, gravity-removal ablation) | LANDED in working tree 2026-04-25; **verification still required** (pytest, API smoke, Docker smoke, thesis build) |
| Model-governance docs (`docs/MODEL_PROMOTION_POLICY.md`, `docs/pretrained_model_exclusion_report.md`, `docs/thesis_section_4x_pretrained_analysis.md`, `docs/THESIS_CONSISTENCY_NOTES.md`) | DRAFTED 2026-04-25; Option A comparison-boundary wording updated 2026-04-26 |

### Newly raised (2026-04-25)

| Item | Status | Why it matters | Where to do it |
| --- | --- | --- | --- |
| Stale CV wording (`stratified`, `StratifiedKFold`, `LOSO`) outside safe-edit scope | OPEN, flagged | Original code/docs still describe the old window-level stratified CV; current canonical training is `GroupKFold` with user holdout | `src/train.py:12` docstring, `scripts/generate_chapter4_assets.py`, `notes/`, `internal/`, `thesis/writing/defense_qa.md`, `thesis/reference/tech_overview.md`, `thesis/reference/why_inventory.md`, `THESIS_WRITING_AUDIT.md`, `HOW_TO_BUILD_THIS_THESIS_PIPELINE_FROM_SCRATCH.md` |
| Verify the 2026-04-25 hardening code paths | OPEN | Code landed but not exercised this session | Run focused pytest, API smoke, drift-monitor smoke; record evidence under `reports/` |
| Self-recorded final validation dataset | PENDING | April-report Ch.4 §4.2.5 has a `% TODO` placeholder; no invented numbers | Collect data → rerun `scripts/generate_chapter4_assets.py` → refresh tables/figures and §4.2.5 / §4.3 |
| Reconcile original-report Ch.4 with rewritten April-report Ch.4 | PARKED | Two parallel chapter sources risk drift | Current pass is April-report-only; decide later whether the April version supersedes the original structurally |

### Newly raised from read-only audit - 2026-04-25

| ID | Weak link | Severity | Status | Required closure |
|---|---|---:|---|---|
| P0-AUDIT-1 | Runtime model identity contradiction: pretrained default vs retrained/excluded documentation | Critical | **CLOSED 2026-04-26** — Option A locked. Defended runtime model is `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` (supervisor-provided 1D-CNN-BiLSTM). Canonical sentence and citation anchors recorded in `docs/THESIS_CONSISTENCY_NOTES.md` section 5; `EVIDENCE_LEDGER.md` EV-009 marked **DEFENDED RUNTIME MODEL**; `defense_qa.md` section 0 added with three Q&As; registry confirms `current_version: null`. Follow-up wording is scoped to the April report plus model-governance docs; main thesis-report edits from this pass were reverted. | No remaining April-report model-identity action unless new April sections are added |
| P0-AUDIT-2 | Current branch not fully verified after hardening | High | Open | Run full pytest, pipeline stages 1-7, API smoke, and Docker smoke with defended model loaded |
| P0-AUDIT-3 | Prometheus/Grafana/alerting are not part of the defended current implementation | High | **CLOSED 2026-04-26** — EVIDENCE_LEDGER entries annotated as historical/future-work; defense_qa.md Docker section scoped and corrected | No further action required unless a new doc is found to make active claims |
| P0-AUDIT-4 | Docker health check can pass without proving model-loaded inference | High | Open | Capture Docker run evidence with actual defended model loaded and inference request |
| P0-AUDIT-5 | Retraining governance matrix not fully proven | High | Open | Evidence healthy/warning/collapse/cooldown/no-labels/worse-model cases |
| P0-AUDIT-6 | API monitoring weaker than pipeline monitoring | High | Open | Either align API monitoring with pipeline monitoring or document API monitoring as lightweight/demo path |

### Added from `pt.md` internal review - 2026-04-26

`pt.md` is internal design guidance only. Do **not** cite it in the thesis. Use it to improve pipeline evidence, checks, and report structure.

Detailed reusable note: `docs/UNLABELED_DATA_MODEL_IMPROVEMENT_GUIDE.md`.

| ID | Improvement | Priority | Status | Required closure |
|---|---|---:|---|---|
| PT-1 | Window-level evidence schema | High | Open | Verify or add per-window output with `window_id`, file/session id, start/end time, model version, scaler version, sampling rate, sensor stats, predicted class, top probabilities, confidence, entropy, top-2 margin, drift/OOD score, and processing status |
| PT-2 | Accelerometer/gyroscope synchronization QA artifact | High | Open | Save a synchronization report with match rate, mean/max timestamp delta, dropped rows, missing synchronized rows, and effective sampling rate; use as Ch4/Ch5 evidence if clean |
| PT-3 | Gyro-axis drift quarantine and ablation evidence | High | Open | For severe gyro-axis shift, do not retrain immediately; check units, axis mapping, calibration, clipping, timestamp alignment, and wearing position; run all-channels vs accel-only vs gyro-only vs no-gyro-x/clipped-gyro-x comparison if needed |
| PT-4 | Strict pseudo-label and active-learning boundary | High | Open | Keep pseudo-labeling candidate-only: require high confidence, low entropy, low OOD, temporal stability, and class-balance control; prefer active-learning export for suspicious/uncertain windows; no promotion without labeled confirmation |
| PT-5 | Monitoring report completeness | Medium | Open | Ensure defended monitoring evidence covers data quality, sampling-rate/unit checks, synchronization, raw-axis drift, magnitude drift, window-feature or embedding drift if available, prediction distribution, confidence, temporal consistency, OOD rate, and recommended action |

## Report Capture Rule

When a task is completed, decide where it belongs:

| Work type | Put in report? | Suggested place |
| --- | --- | --- |
| preprocessing comparison | yes | Ch4 and Ch7 |
| retraining decision matrix | yes | Ch6 |
| retraining execution evidence | yes | Ch5 and Ch6 |
| Docker architecture | yes, concise | Ch5 or README |
| API behavior | yes | Ch5 and README |
| DVC/MLflow reproducibility | yes | Ch5 and REPRODUCE |
| folder cleanup | usually no | README/REPRODUCE only if it affects submission |
| historical scratch notes | no | archive/internal only |
| negative result | yes if scientifically useful | Ch7/Ch8 |
| limitation/future work | yes | Ch8 |

## Next Action

Two tracks running in parallel after the 2026-04-25 update:

**Pipeline evidence track (still primary):** start with A7.

- find or run the z-score vs no-normalization comparison
- save the evidence under `reports/`
- record the result in `WORKLOG.md`
- mark whether the result should go into Ch.4, Ch.7, or both
- while doing A7/A4/A5, fold in the `pt.md` follow-ups above: window-level logging, sync QA, gyro-drift quarantine/ablation, strict pseudo-label governance, and monitoring-report completeness

**April-report consolidation track (new):**

- decide whether the rewritten April-report Ch.4 should be the canonical thesis chapter or stay as a parallel "April draft" reference until A7/A4/A5 evidence lands
- if it becomes canonical, line up the same polish pass (title, mental-health-adjacent framing, formatting, table tightening) for the original-report Chs. 1, 2, 5, 6, 7, 8 in a separate session
- backfill the self-recorded validation dataset placeholder (§4.2.5) once the data exist; do not invent numbers

**Read-only audit track (next 1–2 days, run in Codex/Copilot, NOT in this Claude session):**

- Session title for worklog: **2026-04-25/26 — Read-Only Pipeline Robustness and Evidence Verification Audit**.
- Prompt file: `sandbox:/mnt/data/temporary_pipeline_audit_prompt_2026-04-25.md` (temporary, external).
- **Hard rule: do not edit anything. Only audit, classify, and report evidence.**
- Output expected: an audit report under `reports/` plus a short summary in `WORKLOG.md`. Any required code/doc changes are then queued back into this board, not applied during the audit.

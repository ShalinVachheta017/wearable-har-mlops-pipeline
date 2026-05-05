<!-- markdownlint-disable MD022 MD024 MD028 MD032 MD034 MD036 MD060 -->

# Project Worklog

## Purpose
Detailed reverse-chronological worklog reconstructed from git history, dated artifacts, training outputs, and thesis evidence documents.

## Source Notes
- Built from `git log --all --reverse`, commit stats, dated reports, model/training artifacts, and thesis evidence files.
- Entries are ordered newest first so the current day stays visible at the top.
- Duplicate or parallel branch commits are consolidated by actual work date so the log describes the work, not every repeated hash.
- Commit hashes below are evidence anchors, not a complete dump of every repeated or merge-only hash.
- Model policy note (current): default runtime model is `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`; promotion of retrained candidates is label-gated and requires demonstrated improvement. Older entries may describe earlier default-model experiments.

## Reading Format (Quick + Detailed)

From 2026-04-16 onward, each day should start with a compact scan block before detailed evidence:

1. Today in 5 lines
2. Done today (short)
3. Leftover and risk
4. Writing impact
5. Next session start point

Detailed bug narratives, full file lists, and deep forensics stay below the quick block as evidence.

## 2026-05-06 - Self-Recorded Garmin External Evaluation And Thesis Defense Package

### Today in 5 lines

- Self-recorded Garmin session `2026-05-05-15-11-15` is now fully documented as external evaluation evidence, not retraining data.
- Parser timestamps, manual labels, transition exclusion, and m/s2 accelerometer unit correction are validated.
- Frozen model performance is weak on the external User 7 session: accuracy `0.0860`, balanced accuracy `0.0868`, macro F1 `0.0281`, weighted F1 `0.0278` over `977` included windows.
- Distribution comparison shows self-recorded windows are closest to original training among compared datasets (`mean KS=0.2146`, `mean PSI=0.3502`, `MMD=0.0328`) but still shifted in movement variability/range features.
- Thesis-ready reporting package is complete; decision remains: use as self-recorded external evaluation + domain-shift evidence, do not retrain yet.

### Done Today

- Created and validated the thesis-facing self-recorded evaluation report:
  - `reports/self_recorded_eval_2026_05_05/EVALUATION_REPORT.md`
  - `reports/self_recorded_eval_2026_05_05/prediction_timeline_summary.csv`
  - `reports/self_recorded_eval_2026_05_05/THESIS_PARAGRAPH_SELF_RECORDED_EVAL.md`
  - `reports/self_recorded_eval_2026_05_05/CLAIM_EVIDENCE_TABLE.md`
- Preserved existing evaluation artifacts:
  - `evaluation_metrics.json`
  - `classification_report.csv`
  - `confusion_matrix.csv`
  - `DISTRIBUTION_COMPARISON_REPORT.md`
  - `distribution_pair_summary.csv`
  - `psi_ks_summary.csv`
  - `mmd_summary.csv`
  - `plots/prediction_timeline.png`
- Added a thesis-facing prediction timeline summary with 11 activity segments:
  - dominant prediction per segment,
  - segment recall,
  - mean confidence,
  - top-2 predicted activities.
- Updated the thesis defense dashboard/evidence docs so the newest external-evaluation result is visible from the main readiness and evidence trackers.
- Archived stale root planning documents into `_archive/root/` in commit `77ffa03`:
  - `SUBMISSION_READINESS_SUMMARY.md`
  - `WORK_2026-04-21.md`
  - `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md`
  - `orange_audit_closure_plan_2026-04-26.md`
  - `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md`
- Kept `THESIS_JOURNEY_tillapril.md` and `pt.md` in the root for tomorrow's cleanup review.

### Cleanup And Evidence Handoff

Starting tomorrow, cleanup should proceed folder-by-folder and should not be only deletion. Every folder/file decision should answer: keep as active evidence, update because it is stale, archive as historical, or remove only after a second check.

Report-writing rule for tomorrow's historical analysis: if past work reveals something that improves the written report, add or revise it in the main thesis report only. The main report targets are `thesis/main.tex` and `thesis/chapters/*.tex`. Do not put new thesis conclusions into `thesis/april_report/` unless explicitly requested; that folder is historical April-report material.

Current branch state checked on 2026-05-06:

| Item | State |
|---|---|
| Current active branch | `feature/inference-parity-gpt-no-scaler` |
| Most advanced branch to preserve | `feature/inference-parity-gpt-no-scaler` |
| Local branches | 11 |
| Remote branch refs | 5 |
| Important side branch to inspect before deletion | `audit/stage1-7-manual-check` because it is ahead of its remote |
| Immediate branch goal | Keep `main` plus one or two active thesis branches; delete/archive redundant old branches after evidence is checked |

Tomorrow's cleanup/evidence checklist:

| Area | What to check | Why it matters |
|---|---|---|
| Folder cleanup | Root, `docs/`, `reports/`, `internal/`, `notes/`, `thesis/`, `outputs/`, `data/`, `models/`, `scripts/`, `notebooks/` | Reduce final repo noise without deleting evidence |
| Stage evidence | Stages 1-7 runtime artifacts; Stages 8-10 conditional retraining artifacts; Stage 11 optional calibration scope | Prove each defended stage has artifact-backed evidence |
| Technology evidence | DVC, MLflow, Docker, FastAPI, GitHub Actions, pytest, logging/artifacts, config management | Support the MLOps claim, not only the ML claim |
| Robustness | unit/timestamp checks, schema checks, missing data handling, confidence/collapse monitoring, trigger guardrails | Show the system fails safely and review-gates risky updates |
| Deployment | Docker Compose, FastAPI health/upload, local service smoke, image-size/runtime notes | Bound deployment claims to local/offline-first evidence |
| Scalability | batch processing limits, memory/runtime notes, single-machine scope, future cloud/Kubernetes boundary | Avoid over-claiming production scalability |
| Reproducibility | `README.md`, `REPRODUCE.md`, configs, fixed paths, model/data provenance, seed/config notes | Examiner must be able to rerun or trace results |
| Governance | model promotion policy, review gate, label/QA requirements, no automatic retraining from unlabeled drift | This is the thesis-specific MLOps contribution |
| Data and labels | training data, mentor production data, self-recorded User 7 labels, unit conversion, transition exclusion | Keep evaluation claims defensible |
| CI/CD and tests | test counts, focused tests, workflow scope, release-image smoke if available | Separate real CI evidence from future CD claims |
| Security/privacy | local/offline-first positioning, no cloud deployment claim, no unnecessary personal data in final package | Important for wearable and mental-health framing |
| Writing | Main report only: Chapter 5/6/7 integration, Chapter 8 limitations, defense slide anchors, claim-evidence table | Most important next deliverable is thesis text, not more code |

Possible missed items to remember: figure/table cross-references, bibliography consistency, final package `.gitignore` hygiene, branch consolidation plan, screenshots or command-output evidence for demos, and a final "do not retrain yet" wording sweep.

### Key Evidence

| Evidence item | Value |
|---|---:|
| Fused rows | 104,057 |
| Pipeline windows | 1,039 |
| Included evaluation windows | 977 |
| Excluded windows | 62 |
| Training-style labeled rows | 99,017 |
| Evaluated accuracy | 0.0860 |
| Balanced accuracy | 0.0868 |
| Macro F1 | 0.0281 |
| Weighted F1 | 0.0278 |
| Training vs self mean KS | 0.2146 |
| Training vs self mean PSI | 0.3502 |
| Training vs self MMD | 0.0328 |

### Interpretation

The self-recorded session is not broken: timestamps, labels, official activity names, window alignment, and m/s2 units are now validated. The frozen model still performs poorly, mostly collapsing into `ear_rubbing` and `hand_tapping`. This supports a thesis-safe domain-shift/generalization conclusion rather than a pipeline-failure conclusion.

The self-recorded session was closest to the original labeled training distribution among the compared production-style datasets, but performance remained weak, especially for activities whose motion variability differed from the training set. This supports treating new user data as external evaluation and gating retraining behind additional labeled sessions and QA rather than triggering automatic retraining from a single recording.

### Leftover and Risk

| Risk | Severity | Current stance |
|---|---|---|
| Single labeled self-recorded session | HIGH | Not enough for retraining; use only as external evaluation evidence |
| Dominant-wrist/session-specific motion style | MEDIUM | Discuss as plausible generalization limitation, not as proven universal cause |
| Mentor production sessions are unlabeled continuous recordings | MEDIUM | Use distribution comparison cautiously; do not over-claim activity-level conclusions |
| Dashboard/manuscript wording drift | MEDIUM | Keep worklog, defense dashboard, evidence table, and Chapter 5/6 wording synchronized |

### Writing Impact

- Chapter 5/6 can cite the self-recorded Garmin evaluation as a full parser-label-unit-prediction-governance case study.
- Chapter 7 should report the external evaluation metrics and confusion/timeline collapse pattern as an external-user generalization finding.
- Chapter 8 should frame retraining as conditional future work requiring more labeled sessions, repeated days, a held-out self-recorded split, and QA.
- Defense answer: "The system did not auto-retrain because one labeled recording is insufficient; Stage 7 correctly supports review-gated governance."

### Next Session Start Point

1. Insert the thesis paragraph from `THESIS_PARAGRAPH_SELF_RECORDED_EVAL.md` into the Chapter 5/6 or Chapter 7 draft location.
2. Add the claim-evidence table to the appendix or defense backup slides.
3. Use `prediction_timeline.png`, `confusion_matrix.png`, and `distribution_pair_summary.csv` as the three visual/numeric anchors for the self-recorded evaluation slide.
4. Do not retrain until at least multiple labeled self-recorded sessions and a held-out split exist.

---

## 2026-05-05 - Final Runtime Contract and Governance Freeze

### Today in 5 lines

- Final defended production inference contract is raw physical IMU units: accelerometer milli-g converted to m/s^2, gyroscope retained in deg/s.
- Sampling is fixed at 50 Hz, windows are 200 samples, stride is 100 samples, model input is `(N, 200, 6)`, and output is 11 classes.
- Normalization, external StandardScaler use, gravity removal, and calibration are disabled for final production inference.
- Stage 6 uses the raw physical monitoring baseline and avoids fake CRITICAL drift when a raw baseline is missing or a baseline feature-space mismatch is detected.
- Stage 7 is review-gate governance: unlabeled drift, collapse, and low confidence require review/QA/labels before any model mutation.

### Governance Hardening Summary

This freeze supersedes the 2026-05-04 normalization-enable plan. The final runtime contract keeps production inference in raw physical units and treats `scaler_train_only.json` as training/A-B/legacy diagnostic evidence, not as a production inference dependency. Stage 6 now separates raw physical drift monitoring from normalized legacy baselines and fails safely with review-oriented outcomes instead of creating fake drift alarms from feature-space mismatch. Stage 7 keeps `auto_retrain=false` for unlabeled production data, separates controlled single-activity dominance from uncontrolled production collapse, and routes collapse, drift, and low confidence to review, QA, and label requirements rather than immediate retraining. MLflow finalization during inference no longer registers new model versions; model registration remains a conditional Stage 9 action after review, labels, QA, and promotion evidence.

### Verification State

Post-governance-hardening final evidence (2026-05-05):

- **pytest**: `369/369` passed (includes 3 governance-updated tests: `test_degraded_metrics_trigger`, `test_consecutive_warnings_escalate`, `test_cooldown_wins_over_consecutive_warning_escalation` — all updated to assert `auto_retrain=False` / `REVIEW` action instead of former `TRIGGER_RETRAIN`).
- **git diff --check**: clean (CRLF advisory only, no content issues).
- **MLflow model registration**: zero new versions created in any of today's inference runs (confirmed: no "register" / "Created version" lines in run logs).
- **Session `2025-08-19-08-58-40`** (ear rubbing): `ear_rubbing` 53.5%, mean confidence 74.4%, drift HEALTHY (max z-score 0.676 vs raw physical baseline), `should_retrain=false`, `auto_retrain=false`.
- **Session `2025-03-23-15-23-10`** (controlled hand tapping): `hand_tapping` 100.0%, `dominance_context=CONTROLLED_OR_LOW_MOTION_DOMINANCE`, `collapse_level_tag=EXPECTED_SINGLE_ACTIVITY_DOMINANCE`, `alert_level=WARNING`, `should_retrain=false`, `auto_retrain=false`.
- Re-run the final freeze checklist after the documentation/API wording cleanup and before final PDF submission.

### Writing Impact

- Chapter 4 should describe production inference as raw physical units after unit conversion, with no external scaler in final production inference.
- Chapter 6 should describe Stage 6 drift as raw physical baseline comparison with feature-space mismatch guards.
- Chapter 6/7 should describe Stage 7 as review-gate governance, not automatic retraining from unlabeled production drift.
- Stage 8-10 should be framed as conditional mutation stages only after review, labels, QA, and promotion criteria.
- Stage 11 calibration/UQ should remain optional/future work unless a result is directly evidenced.

---

## 2026-05-04 - Root Cause Confirmed: Normalization Mismatch + Live Data Recording Day

### Today in 5 lines

- Full root-cause confirmed: **8 verified factors** drive 100% hand_tapping collapse; primary cause is `enable_normalization: false` in `config/pipeline_config.yaml`.
- Drift alarm (9.797σ) is measurement error — enabling normalization drops max drift to 1.262σ (HEALTHY) with no code changes.
- `models/pretrained/current_model.keras` is a 10-byte text stub ("1.0.0 data"), not a real model; production runs on `fine_tuned_model_1dcnnbilstm.keras` via explicit config path only.
- Two prometheus-skip tests removed from `tests/test_stage6_monitoring.py`; `tests/test_baseline_age_gauge.py` deleted (duplicates already in stage6 test).
- Tomorrow: enable normalization, fix mtime sort loop in ingestion, record fresh data with Garmin watch (all 11 classes), re-run pipeline to verify predictions diversify.

### Done Today

- Deleted `tests/test_baseline_age_gauge.py` (125 lines, full prometheus gauge test file — duplicated in test_stage6_monitoring.py).
- Removed 2 prometheus-skip test methods from `tests/test_stage6_monitoring.py`: `test_prom_gauge_is_defined_when_prometheus_available` and `test_run_monitoring_sets_gauge_minus_one_when_missing`. Removed now-unused `from unittest.mock import MagicMock, patch` import.
- Ran pipeline on July 17 2025 dataset (stages 1–3 only, TF not available in shell env): 8799 rows ingested, 86 windows created — confirmed different window distribution from March 23 (1814 windows, device flat on desk).
- Forensically verified each of the 8 collapse factors using archived `artifacts/20260503_184608/` (production_X.npy, probabilities npy, inference_report.json, scaler JSON, baseline JSON, calibration JSON).
- Drift simulation verified: `mean_diff = |Az_mean - 0| / 1.0 = |-9.8227| = 9.797σ` exactly matches log. Normalization ON → max drift 1.262σ (below 1.8 threshold).
- Created `docs/4th_meet_20260504.md` — comprehensive meeting prep doc: 8-factor root cause, full codebase audit tables, priority action items, useful commands.

### Leftover and Risk

| Risk | Severity | Status |
|---|---|---|
| `enable_normalization: false` in config | CRITICAL | NOT fixed — fix tomorrow first |
| `models/pretrained/current_model.keras` is 10-byte stub | HIGH | NOT fixed — anything loading `current_model.keras` will crash |
| `data_ingestion.py:125` sorts by `st_mtime` not filename date | HIGH | NOT fixed — causes March 23 dataset to keep being picked (mtime updated on May 3) |
| Temperature calibration hardcoded T=1.5 (`fitted: false`) | MEDIUM | NOT fixed — cannot correct overconfidence |
| Stage 2 gyroscope clipping: WARNING not ERROR when > 500 deg/s | MEDIUM | NOT fixed — July 17 data has Gx max=936 deg/s, passes validation |
| No `dvc.yaml` pipeline definition | MEDIUM | NOT fixed — DVC versioning exists but no formal pipeline reproducibility |
| Two Docker API implementations: `src/api/app.py` vs `docker/api/main.py` | LOW | NOT fixed — needs clarification which is authoritative |
| March 23 dataset was device-on-desk, not wrist-worn | INFO | Known artifact; new data recording scheduled for today |

### Writing Impact

- Section 4 (Methodology / Preprocessing): add sentence clarifying production pipeline must apply the same z-score normalization used during training — scaler `scaler_train_only.json` (fit_users=[1,2,3,4]) must be applied at inference time.
- Section 5 (Monitoring): drift metric formula is `|prod_mean - baseline_mean| / baseline_std`; when baseline is in normalized space and production is raw, drift is guaranteed to alarm regardless of real distribution shift.
- Section 6 (Results): note that 100% hand_tapping result in May 3 run is a pipeline configuration artifact, not a model generalization failure.
- Appendix (Reproducibility): `dvc.yaml` missing — DVC tracks artifact files but pipeline stages are not formally defined; add this before defense.

### Next Session Start Point

1. **First action**: `config/pipeline_config.yaml` line 45 — change `enable_normalization: false` → `true`
2. **Second action**: Fix `src/components/data_ingestion.py:125` — sort pairs by filename-encoded timestamp, not `st_mtime`
3. **Third action**: Replace `models/pretrained/current_model.keras` (10-byte stub) with a real copy or proper pointer to `fine_tuned_model_1dcnnbilstm.keras`
4. **Live data recording**: Record all 11 activity classes with Garmin watch, ≥3 min each, device properly worn on wrist; save to `data/raw/`
5. **Pipeline verification**: Re-run full pipeline on new recording; confirm predictions are no longer 100% hand_tapping; confirm drift drops to < 1.8σ
6. **Optional**: Fit temperature calibration — requires a labeled validation set; document as future work if deferred

### Evidence and Key Numbers

- March 23 artifact Az: mean=−9.8227 m/s², std=0.1763 m/s² (device lying flat, full gravity on Z, 60.5 min recording)
- Drift formula result: `|−9.8227 − 0| / 1.0 = 9.797σ` (matches log exactly)
- Normalization simulation: max drift drops from 9.797σ → 1.262σ with one config change
- hand_tapping mean prob: 0.998035; entropy < 0.01 for 1801/1814 windows
- Logit advantage mean=6.94, max=9.51 — model is maximally certain (near-zero temperature would not help)
- July 17 dataset: 8799 samples, 86 windows (50% overlap), no flat-device signature — different session profile
- Real model: `fine_tuned_model_1dcnnbilstm.keras` (5.9 MB); broken stub: `current_model.keras` (10 bytes, text "1.0.0 data")

---

## 2026-05-03 - Today Checklist: Stage 6/7 And Repo-Weak-Link Closure

### Today in 5 lines

- Stage 1-5 are the current clean baseline; do not reopen them except for verification.
- Stage 6 and Stage 7 are today's main implementation/audit targets.
- The fresh repo-wide audit confirms the project is real MLOps, but not defense-clean until thesis/code/config wording is consistent.
- Correction to older notes: Stage 4 `inference_report.json` does **not** contain `G_mag_median`, per-axis means, or `gravity_dominant_axis`; Stage 6 must compute these from `DataTransformationArtifact.production_X_path`.
- Today's finish line: monitoring detects low-motion/orientation collapse, trigger blocks unsafe unlabeled retraining, and the highest-risk thesis/code contradictions are recorded for cleanup.

### Current Working-Tree Note

Current `git status --short` before today's work shows:

- `M WORKLOG.md`
- `D data/codex_synth/synthetic_all_users_labeled_v1.csv`
- `M notebooks/model_inference_diagnostics.ipynb`
- many untracked historical docs/scripts/notebooks/models and temp/report files

Do not revert these blindly. Treat them as existing user/work artifacts unless a later cleanup pass explicitly decides what to keep, archive, or delete.

### Fresh Repo-Wide Audit Summary To Carry Forward

Updated defense-readiness scores from the 2026-05-03 full repo audit:

| Dimension | Score | Main reason |
|---|---:|---|
| Code quality | 74/100 | Real staged code, but several large files and stale helpers remain |
| MLOps completeness | 84/100 | Pipeline, artifacts, MLflow, DVC, Docker, CI, monitoring, trigger, registry all exist |
| Thesis-code consistency | 62/100 | Current runtime/default model/scaler wording is inconsistent across code, docs, and thesis |
| Robustness | 72/100 | Stages 1-5 strong; Stage 6/7 collapse-safety gaps remain |
| Reproducibility | 76/100 | Good entrypoints and evidence, but dirty tree and scattered artifacts reduce clarity |
| Defense readiness | 70/100 | Strong thesis project; still needs consistency and safety closure |

Overall current score: **74/100**.

### Priority P1 - Stage 6 Monitoring Work For Today

Files to inspect first:

- `src/components/post_inference_monitoring.py`
- `src/monitoring/post_inference_monitor.py`
- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`
- `src/pipeline/production_pipeline.py`
- `config/pipeline_config.yaml`

Tasks:

1. Verify Stage 6 input contract:
   - receives Stage 4 prediction CSV,
   - receives Stage 3 transformation artifact / `production_X.npy`,
   - receives or creates baseline reference,
   - writes monitoring report and monitoring artifact.
2. Add or verify real entropy and top-2 margin usage:
   - Stage 4 CSV already has per-window `entropy` and `top2_margin`;
   - Stage 6 should use those real columns instead of only approximating entropy from max confidence.
3. Add low-motion / orientation evidence from `production_X.npy`:
   - load `X` with shape `(n_windows, 200, 6)`;
   - gyro columns are indices `3:6` = `Gx, Gy, Gz`;
   - compute sample-level `G_mag = sqrt(Gx^2 + Gy^2 + Gz^2)`;
   - report `g_mag_median`, `g_mag_mean`, and useful percentiles;
   - accelerometer columns are indices `0:3` = `Ax, Ay, Az`;
   - report per-axis acceleration mean/std and `gravity_dominant_axis`.
4. Add monitoring flags:
   - `low_gyro_motion = g_mag_median < 1.1`;
   - `low_motion_collapse_risk = low_gyro_motion and dominant_pct >= 70`;
   - keep `1.1 deg/s` framed as an empirical threshold from the 28-session audit, not a universal literature constant.
5. Fix or verify temporal duration math:
   - model window span is `200 / 50 = 4s`;
   - with 50% overlap, prediction stride is `2s`;
   - any dwell/duration estimate should not use a hardcoded `8.0s` window duration.
6. Verification target:
   - collapsed session should show low `G_mag` and collapse risk;
   - normal sessions should show higher `G_mag`;
   - monitoring report should make the failure easy to defend.

### Priority P1 - Stage 7 Trigger Work For Today

Files to inspect first:

- `src/components/trigger_evaluation.py`
- `src/trigger_policy.py`
- `src/pipeline/production_pipeline.py`
- `src/entity/config_entity.py`
- `src/entity/artifact_entity.py`

Tasks:

1. Verify the existing indirect collapse guard:
   - Stage 5/6 dominance warning and `dominant_pct >= 95` should already route to REVIEW / no retrain.
2. Add or verify direct Stage 4 collapse signal flow:
   - Stage 4 artifact has `collapse_level`;
   - pipeline should pass `collapse_level` into the collapse signal payload;
   - Stage 7 should not depend only on Stage 5/6 being run.
3. Add hard safety rule:
   - if `collapse_level == "CRITICAL_COLLAPSE"` or `low_motion_collapse_risk == true`,
   - and adaptation method is unlabeled/unsupervised (`pseudo_label`, `adabn`, `tent`, `adabn_tent`),
   - block retraining and return REVIEW / critical warning.
4. Check `force_retraining` behavior:
   - force should not override critical collapse for pseudo-label or unlabeled adaptation;
   - supervised retraining with real labels can remain allowed if clearly documented.
5. Verification target:
   - collapsed session produces `should_retrain=false`;
   - action/reason explains **why** the model is unhealthy;
   - no path can pseudo-label 100% `hand_tapping` and retrain on it silently.

### Priority P1 - Repo Weak Links From Fresh Audit

These are not all today's code changes, but they must stay visible:

1. Thesis/report wording must match current Stage 3 default:
   - current runtime default is raw physical input (`m/s^2`, `deg/s`), no external scaler;
   - z-score scaler is optional A/B, not the defended default unless config is changed intentionally.
2. Model lineage must be explained cleanly:
   - default runtime model is the mentor/pretrained checkpoint;
   - accuracy claims from the paper must not be stated as achieved by the current local runtime unless proven.
3. API preprocessing parity is a high-risk follow-up:
   - `src/api/app.py` may still apply scaler-like preprocessing while batch Stage 3 default does not;
   - either align API with Stage 3 or document API as demo/legacy path.
4. `src/config.py` still has risky duplicate/legacy constants:
   - especially production sensor-column naming and model/scaler defaults;
   - do not fix during Stage 6/7 unless directly needed, but keep on cleanup list.
5. `src/utils/label_mapping.py` should eventually become single-source canonical mapping:
   - avoid legacy `data/prepared/config.json` silently overriding the canonical class order.
6. Documentation cleanup is required before submission:
   - mark stale docs as historical,
   - create/current-evidence index,
   - keep one clear story for model, scaler, API, and monitoring.

### Priority P2 - Verification Commands For Today

Use these after edits, adjusting paths only if needed:

- `python -m py_compile src/components/post_inference_monitoring.py src/monitoring/post_inference_monitor.py src/components/trigger_evaluation.py src/trigger_policy.py src/pipeline/production_pipeline.py`
- `python -m pytest tests/test_post_inference_monitor.py tests/test_trigger_policy.py tests/test_stage6_baseline_space_consistency.py -q --tb=short`
- `python run_pipeline.py --stages inference evaluation monitoring trigger`
- If feasible after that: run one collapsed session and one non-collapsed session through stages 3-7 and compare monitoring/trigger reports.

### Done Criteria For 2026-05-03

- Stage 6 report contains confidence, dominance, real entropy/top2 margin, G-mag, per-axis orientation, and low-motion collapse risk.
- Stage 7 blocks critical collapse and low-motion collapse from unsafe unlabeled retraining.
- Trigger report explains REVIEW with an explicit reason.
- The worklog records any remaining thesis/report/config contradictions.
- No unrelated root cleanup is mixed into the Stage 6/7 implementation commit.

### Stage 6 Implementation Addendum

Implemented today:

- Refactored `src/components/post_inference_monitoring.py` into a readable Stage 6 wrapper with small helper methods and thesis-style four-line docstrings.
- Kept the two-file Stage 6 design:
  - `src/components/post_inference_monitoring.py` owns pipeline config/artifact/path resolution.
  - `src/monitoring/post_inference_monitor.py` owns the monitoring math.
- Added typed config defaults in `PostInferenceMonitoringConfig`:
  - `window_duration_seconds = 4.0`
  - `prediction_stride_seconds = 2.0`
  - `low_gyro_motion_threshold = 1.1`
  - `low_motion_dominance_threshold = 70.0`
- Fixed Layer 2 dwell-time math:
  - old logic effectively used a hardcoded 8 seconds per window,
  - new logic uses `4 + (sequence_length - 1) * 2` seconds for 200-sample windows at 50 Hz with 50% overlap.
- Changed Layer 1 uncertainty evidence:
  - Stage 6 now uses real Stage 4 `entropy` and `top2_margin` columns when present,
  - fallback entropy approximation remains only for older prediction CSVs.
- Added motion-context monitoring from `production_X.npy`:
  - computes sample-level `G_mag = sqrt(Gx^2 + Gy^2 + Gz^2)`,
  - reports `g_mag_median`, mean/std/p05/p95,
  - reports `a_mag` summary,
  - reports per-axis acceleration and gyroscope mean/std,
  - reports `gravity_dominant_axis`,
  - flags `low_gyro_motion`,
  - flags `low_motion_collapse_risk`.
- Added a safe fallback so Stage 6 can still read `data/prepared/production_X.npy` when stages 1-3 are skipped and only `inference evaluation monitoring trigger` are run.

Verification:

- Syntax check passed:
  `python -m py_compile src/components/post_inference_monitoring.py src/monitoring/post_inference_monitor.py src/entity/config_entity.py`
- Focused tests passed:
  `16 passed` for `tests/test_post_inference_monitor.py` and `tests/test_stage6_baseline_space_consistency.py`.
- Pipeline verification passed:
  `python run_pipeline.py --stages inference evaluation monitoring trigger`
  with run ID `20260503_114540`.
- The new `outputs/monitoring/monitoring_report.json` contains:
  - `entropy_source = stage4_prediction_csv`
  - `top2_margin_mean = 0.9962`
  - `mean_dwell_time_seconds = 3630.0`
  - `window_duration_seconds = 4.0`
  - `prediction_stride_seconds = 2.0`
  - `g_mag_median = 0.545`
  - `gravity_dominant_axis = Az`
  - `low_gyro_motion = true`
  - `low_motion_collapse_risk = true`
  - `overall_status = CRITICAL`

Important remaining environment note:

- Some pytest temp directories remain Windows-ACL locked and could not be removed even with elevated deletion. This is a local filesystem cleanup issue, not a Stage 6/7 logic failure.

### Stage 7 Implementation Addendum

Implemented today:

- Refactored `src/components/trigger_evaluation.py` into a readable Stage 7 wrapper with thesis-style four-line docstrings.
- Preserved the two-file Stage 7 design:
  - `src/components/trigger_evaluation.py` builds the trigger-policy payload from Stage 6 artifacts.
  - `src/trigger_policy.py` owns the trigger decision logic.
- Added direct collapse-safety signals to the trigger payload:
  - `collapse_level`
  - `top2_margin_mean`
  - `low_gyro_motion`
  - `low_motion_collapse_risk`
  - `g_mag_median`
  - `gravity_dominant_axis`
- Updated `src/pipeline/production_pipeline.py` so Stage 4 and Stage 6 collapse evidence is merged into the same `collapse_signals` payload before Stage 7 runs.
- Updated `src/trigger_policy.py` so the collapse guard now returns REVIEW / no retrain for:
  - Stage 5/6 dominance warning,
  - `dominant_pct >= 95`,
  - `dominant_pct >= 90` plus zero transitions plus high confidence,
  - Stage 4 `collapse_level == "CRITICAL_COLLAPSE"`,
  - Stage 6 `low_motion_collapse_risk == true`.
- Added a Stage 8 safety block in `src/pipeline/production_pipeline.py`:
  - critical collapse or low-motion collapse risk blocks unlabeled adaptation methods (`pseudo_label`, `adabn`, `tent`, `adabn_tent`),
  - this block takes precedence even when `force_retraining=True`,
  - supervised retraining with real labels is not blocked by this unlabeled-safety guard.
- Moved the trigger-policy test state fixture away from Windows `tmp_path` into workspace-local `stage7_pytest_work/` because pytest temp cleanup repeatedly hit Windows ACL errors.

Verification:

- Syntax check passed:
  `python -m py_compile src/components/trigger_evaluation.py src/trigger_policy.py src/pipeline/production_pipeline.py tests/test_trigger_policy.py tests/test_trigger_threshold_pass_through.py tests/test_stage7_retraining_collapse_guard.py tests/conftest.py`
- Focused Stage 7 tests passed:
  `29 passed` for `tests/test_trigger_policy.py`, `tests/test_trigger_threshold_pass_through.py`, and `tests/test_stage7_retraining_collapse_guard.py`.
- Combined Stage 6/7 tests passed:
  `45 passed` for `tests/test_post_inference_monitor.py`, `tests/test_stage6_baseline_space_consistency.py`, `tests/test_trigger_policy.py`, `tests/test_trigger_threshold_pass_through.py`, and `tests/test_stage7_retraining_collapse_guard.py`.
- Pipeline verification passed:
  `python run_pipeline.py --stages inference evaluation monitoring trigger`
  with run ID `20260503_124417`.
- The generated `artifacts/20260503_124417/trigger/trigger_decision.json` contains:
  - `should_retrain = false`
  - `action = review`
  - `alert_level = CRITICAL`
  - `collapse_level = CRITICAL_COLLAPSE`
  - `low_gyro_motion = true`
  - `low_motion_collapse_risk = true`
  - `g_mag_median = 0.545`
  - `gravity_dominant_axis = Az`

Defense meaning:

- The pipeline now catches the exact failure mode observed during the audit:
  a near-static, orientation-dominated session that collapses into `hand_tapping`.
- The system does not silently turn 100% `hand_tapping` predictions into pseudo-label training data.
- Stage 6 explains the failure condition; Stage 7 turns it into a safe REVIEW decision.

### Pipeline Entrypoint / Orchestrator Refactor Addendum

Implemented today:

- Simplified `run_pipeline.py` from 848 lines to 236 lines.
- Simplified `src/pipeline/production_pipeline.py` from 1177 lines to 818 lines.
- Moved CLI support responsibilities into explicit pipeline helper modules:
  - `src/pipeline/pipeline_config_factory.py`
  - `src/pipeline/pipeline_console_reporter.py`
- Moved production orchestrator support logic out of `src/pipeline/production_pipeline.py`:
  - `src/pipeline/pipeline_input_resolver.py` handles resume/fallback artifacts and label detection.
  - `src/pipeline/pipeline_safety.py` handles collapse-signal extraction/merge logic and unlabeled retraining safety.
  - `src/pipeline/pipeline_mlflow_logger.py` handles non-fatal MLflow lifecycle, metrics, artifacts, and registry logging.
- Kept existing `ProductionPipeline` method names as thin wrappers where tests or external scripts patch them.
- Preserved behavior:
  - same CLI flags,
  - same config precedence,
  - same Stage 1-7 stage order,
  - same skip/resume behavior,
  - same Stage 6/7 collapse guard,
  - same pipeline output artifacts.

Verification:

- Syntax check passed:
  `python -m py_compile run_pipeline.py src/pipeline/production_pipeline.py src/pipeline/pipeline_config_factory.py src/pipeline/pipeline_console_reporter.py src/pipeline/pipeline_input_resolver.py src/pipeline/pipeline_safety.py src/pipeline/pipeline_mlflow_logger.py`
- Focused regression tests passed:
  `43 passed, 1 deselected` for pipeline integration, fix-regression, Stage 7 retraining guard, trigger policy, and trigger threshold pass-through tests.
- The one deselected test was `test_result_serialization`, which only triggered the known Windows `tmp_path` ACL cleanup failure in this workspace.
- Runtime pipeline verification passed:
  `python run_pipeline.py --stages inference evaluation monitoring trigger`
  with run ID `20260503_130924`.
- The verified run still produced:
  - `overall_status = SUCCESS`
  - `trigger = review`
  - `alert_level = CRITICAL`
  - `should_retrain = false`
  - `low_motion_collapse_risk = true`

Readability outcome:

- `run_pipeline.py` is now a true entrypoint.
- `production_pipeline.py` is closer to a stage orchestrator; remaining complexity is mostly stage artifact-summary writing and backward-compatible MLflow wrappers.
- The next safe cleanup, if needed, is to move repeated stage artifact-summary writing into a `PipelineArtifactWriter`.

### Pipeline Orchestrator Simplification Addendum 2

Implemented after the first orchestrator split:

- Reduced `src/pipeline/production_pipeline.py` further from 818 lines to 606 lines.
- Added a typed runtime context:
  - `src/pipeline/pipeline_context.py`
  - replaces loose `ctx["..."]` access in the orchestrator with readable fields like `ctx.inference_art`.
- Added stage-selection registry:
  - `src/pipeline/pipeline_stage_registry.py`
  - owns `ALL_STAGES`, retraining stages, advanced stages, and stage selection rules.
- Added artifact writer:
  - `src/pipeline/pipeline_artifact_writer.py`
  - owns repeated save/copy/summary JSON logic for ingestion, validation, transformation, inference, evaluation, monitoring, trigger, calibration, and final pipeline result.
- Added chunked drift helper:
  - `src/pipeline/pipeline_chunked_drift.py`
  - keeps optional 500-window drift-monitor details out of the main pipeline orchestrator.
- Preserved backward compatibility:
  - `ALL_STAGES`, `RETRAIN_STAGES`, and `ADVANCED_STAGES` remain importable from `src.pipeline.production_pipeline`;
  - existing wrapper methods for MLflow, fallback artifacts, label detection, and collapse safety remain in place for tests and older scripts.

Verification:

- Syntax check passed:
  `python -m py_compile run_pipeline.py src/pipeline/production_pipeline.py src/pipeline/pipeline_config_factory.py src/pipeline/pipeline_console_reporter.py src/pipeline/pipeline_input_resolver.py src/pipeline/pipeline_mlflow_logger.py src/pipeline/pipeline_safety.py src/pipeline/pipeline_stage_registry.py src/pipeline/pipeline_context.py src/pipeline/pipeline_artifact_writer.py src/pipeline/pipeline_chunked_drift.py`
- Focused tests passed:
  `71 passed, 4 deselected` for pipeline integration, fix-regression, Stage 7, trigger policy, and threshold pass-through tests.
- Stage 6 math/utility tests passed:
  `22 passed, 15 deselected`.
- Full Stage 1-7 runtime verification passed with explicit known sensor pair:
  `python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger --accel-file data/raw/2025-03-23-15-23-10-accelerometer_data.xlsx --gyro-file data/raw/2025-03-23-15-23-10-gyroscope_data.xlsx`
  with run ID `20260503_161728`.
- Verified runtime result:
  - `overall_status = SUCCESS`
  - `completed = 7/7 stages`
  - `dominant_class = hand_tapping`
  - `dominant_pct = 100.0`
  - `g_mag_median = 0.545`
  - `low_motion_collapse_risk = true`
  - `trigger action = review`
  - `should_retrain = false`

Environment notes:

- `python run_pipeline.py --stages inference evaluation monitoring trigger` failed before Stage 4 because `data/prepared/production_X.npy` was not present on this branch at the start of verification. Running Stage 1-3 first correctly recreated it.
- Full default Stage 1 auto-discovery failed because the newest raw `2025-08-13` CSV pair contains an accelerometer file read as `0 rows x 1 columns`; explicit known-pair execution is the valid verification path until raw-file cleanup is done.
- Some pytest cases still hit Windows temp-directory ACL errors under `%TEMP%`; this is the known local Windows cleanup issue, not a failed pipeline assertion.

### Stage 7 Threshold Defense Notes For Report/PPT

Use this framing in the thesis and slides:

- Softmax confidence thresholds are monitoring signals, not correctness proof.
  - Citation: Guo et al., 2017, *On Calibration of Modern Neural Networks*, ICML. Modern neural networks can be poorly calibrated; temperature scaling is a practical calibration method. Source: https://proceedings.mlr.press/v70/guo17a.html
  - Citation: Hendrycks and Gimpel, 2017, *A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks*. Maximum softmax probability is a useful cheap signal for error/OOD detection, but not a guarantee. Source: https://arxiv.org/abs/1610.02136
- Drift z-score thresholds are statistical process-control style safeguards.
  - `2.0 sigma` is an early warning level because about 95% of normally distributed stable data lies within +/-2 standard deviations.
  - `3.0 sigma` is a critical level because about 99.7% lies within +/-3 standard deviations.
  - Source for empirical/three-sigma rule and control chart framing: JMP control chart probability limits, https://www.jmp.com/en/statistics-knowledge-portal/quality-and-reliability-methods/control-charts/probability-limits-on-control-charts
  - Citation for sequential change monitoring: Page, 1954, *Continuous Inspection Schemes*, Biometrika, https://doi.org/10.1093/biomet/41.1-2.100
  - Citation for concept drift framing: Gama et al., 2014, *A Survey on Concept Drift Adaptation*, ACM Computing Surveys, https://doi.org/10.1145/2523813
- Gyroscope magnitude is defensible as an orientation-invariant motion-intensity signal.
  - Citation/evidence pattern: UCI HAR uses 3-axis accelerometer/gyroscope signals at 50 Hz and derived magnitude features such as `tBodyGyroMag` and `fBodyGyroMag`; magnitude is a standard HAR feature family for combining 3D axes into one motion-intensity measure. UCI dataset source: https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones
  - Feature detail reference: UCI HAR `features_info.txt` describes Euclidean-norm magnitude features for accelerometer and gyroscope signals; mirror/source file: https://huggingface.co/datasets/udayl/UCI_HAR/blob/main/features_info.txt
- Collapse thresholds are empirical safety guards from this repository audit, not universal literature constants.
  - `dominant_pct >= 95%`: critical one-class collapse because nearly all windows map to one class; this is an operational guard to block unsafe pseudo-labeling.
  - `dominant_pct >= 90%` plus `transition_rate == 0` plus high confidence: static high-confidence collapse proxy.
  - `G_mag_median < 1.1 deg/s`: empirical separator from the 28-session audit; all low-motion collapsed/warning sessions were below 1.1, while the nearest non-collapsed session was above 3.6.
  - `low_motion_dominance_threshold = 70%`: early warning for partial collapse, based on the observed 78.5% warning session.
- Cooldown is a governance rule, not a model-science claim.
  - `cooldown_hours = 24` prevents repeated automatic retraining loops from the same unhealthy signal.
  - Defensible wording: "The value is an operational safety interval chosen to avoid repeated retraining on a single unresolved production anomaly; it can be tuned per deployment policy."

## 2026-05-02 — Full Repo Audit + 2-Day Sprint Plan

### Audit Summary (Read-Only)

Full repository audit performed by Claude Code acting as senior ML/MLOps reviewer.
No files were changed during the audit. Findings recorded below.

**Verdict:** This is a real, defensible MLOps thesis. The pipeline infrastructure,
monitoring, governance, domain adaptation, and investigation work are all at thesis
level. The three things that determine how well the defense goes are:
(1) how clearly the pretrained model accuracy situation is framed,
(2) whether retraining can be shown to have actually run,
(3) whether the normalization story is consistent end to end.

**Overall score: 70/100**

Subscores:

| Dimension | Score | Main reason |
|---|---|---|
| Code quality | 74/100 | Strong modular design; some files too large (train.py 1494 lines, trigger_policy.py 989 lines) |
| MLOps completeness | 76/100 | All 11 stages real; retraining unproven end-to-end |
| Thesis-code consistency | 62/100 | Normalization contradiction; two chapter versions; accuracy framing |
| Robustness | 68/100 | Stage 6 G_mag missing; Stage 7 no direct collapse block |
| Reproducibility | 78/100 | REPRODUCE.md + DVC + MLflow solid; remote DVC uncertain |
| Defense readiness | 65/100 | Infrastructure strong; model accuracy framing not settled |

### Critical Findings From Audit

**C1 — Normalization toggle contradiction (High)**
`config/pipeline_config.yaml` sets `enable_normalization: false`.
Older readiness notes treated z-score normalization as the defended preprocessing
baseline. The 2026-05-05 freeze resolves this in favor of raw physical production
inference with no external scaler.

**C2 — Retraining never proven end-to-end (High)**
Stages 8, 9, 10 are all implemented but `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md`
item A5 is still OPEN. No artifact directory shows stages 8-10 running together.

**C3 — Stage 7 has no direct CRITICAL_COLLAPSE hard block (Medium)**
Stage 4 produces `collapse_level = "CRITICAL_COLLAPSE"`. Stage 7 blocks retraining
indirectly via the 95% dominance threshold path — not via a direct check on
`collapse_level`. The planned direct block is not yet implemented.

**C4 — Stage 6 missing G_mag signal (Medium)**
`post_inference_monitoring.py` delegates to `post_inference_monitor.py` but the
low-motion collapse risk (`G_mag_median < 1.1`) is not computed or surfaced in the
monitoring report. The signal exists only in Stage 4 `inference_report.json`.

**C5 — Root directory is messy (High — examiner impression)**
`stage4_pytest_tmp/`, `stage5_pytest_tmp_*/` (x8), `tmp_run3/`, `tmp_pytest_trigger/`,
`tmp_pytest_trigger2/`, `test_tmp_stage3/`, `.conda/`, `temp.txt`,
`thesis_doc.txt`, `reasoningtxt.txt`, `pt.md`, and planning MDs are all
visible at root. An examiner reading `ls` will ask what is broken.

**C6 — Two parallel thesis chapter versions (High)**
`thesis/main.tex` (original, 92 pages built) and the April-report rewrite of Ch.4
coexist. No decision recorded on which is canonical for submission.

**C7 — `§4.2.5` TODO placeholder in LaTeX (High)**
A `% TODO` placeholder for the self-recorded validation dataset exists in the
April-report chapter. An examiner reading the source or a compiled blank section
is not acceptable.

**C8 — Model accuracy framing (Critical)**
`src/config.py::PRETRAINED_MODEL_STATUS` documents the model as
`EXCLUDED_UNDOCUMENTED_PROVENANCE` with max 18.5% accuracy on this dataset vs the
reported 87%. The defended answer for "what accuracy does your system achieve?"
must be prepared and consistent with the thesis prose.

### What Is Already Strong (Do Not Touch)

- Config / Artifact / Component pattern across all 11 stages
- Collapse investigation: 28-session analysis, G_mag < 1.1 separator, gravity axis mechanism
- Trigger policy engine: voting, cooldown, governance docs
- MLflow evidence: 3699 runs
- Stage 1 auto-detection of milliG vs m/s², alias normalization, label detection
- REPRODUCE.md: single command producing all 7 stages of evidence
- DVC tracking: MD5-verified assets
- Baseline staleness guard + self-comparison exclusion guard
- Model promotion governance docs and exclusion record

---

### 2-Day Sprint Plan

The goal for the next two days is to close the highest-severity open items so the
thesis can be defended without a surprise question going unanswered.

---

#### Day 1 (2026-05-03) — Fix fundamentals + Stage 6/7 signals + framing

**Task D1-1 — Resolve the normalization contradiction**
- Decide: `enable_normalization: false` (paper-aligned, no external scaler) OR
  `true` (z-score defended, scaler applied).
- Update `config/pipeline_config.yaml`.
- Update `SUBMISSION_READINESS_SUMMARY.md` to match.
- Run `python run_pipeline.py --stages ingestion validation transformation` to confirm
  no crash and check Stage 3 transformation report shows or hides normalization.
- Done when: both config and summary say the same thing and a pipeline run confirms it.

**Task D1-2 — Clean the root directory**
- Move to `internal/` or delete: `temp.txt`, `thesis_doc.txt`, `reasoningtxt.txt`,
  `pt.md`, `WORK_2026-04-21.md`, `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md`,
  `orange_audit_closure_plan_2026-04-26.md`, `REFACTOR_ISSUES.md`,
  `THESIS_JOURNEY_tillapril.md`.
- Remove or move the pytest cache dirs scattered at root:
  `stage4_pytest_tmp/`, `stage4_pytest_tmp_simple_531/`, `stage4_pytest_cache_simple_531/`,
  `stage5_pytest_tmp_*/` (all 5 variants), `stage5_pytest_cache_*/` (all 4 variants),
  `tmp_run3/`, `tmp_pytest_trigger/`, `tmp_pytest_trigger2/`, `test_tmp_stage3/`,
  `pytest-cache-files-dk416ohy/`, `pytest-cache-files-yanki_9t/`.
- Add `.conda/` to `.gitignore` if not already there.
- Done when: `ls` at root shows only code, config, docs, and canonical MDs.

**Task D1-3 — Decide canonical thesis version**
- Choose: April-report Ch.4 rewrite OR original `thesis/main.tex` as the submission chapter.
- Record the decision in this WORKLOG entry.
- If April-report wins: note which chapters of the original thesis are still the source.
- Done when: one sentence in this worklog says which file is the submission version.

**Task D1-4 — Fix or remove `§4.2.5` TODO placeholder**
- Open the April-report LaTeX source, find the `% TODO` in §4.2.5.
- Either insert a one-paragraph placeholder note ("Data collection is planned; results
  will be added before final submission") or remove the subsection and renumber.
- Rebuild the PDF to confirm no undefined-reference errors.
- Done when: `thesis/april_report/main.pdf` builds with no TODO visible.

**Task D1-5 — Add G_mag signal to Stage 6**
- In `src/components/post_inference_monitoring.py`, after the `monitor.run()` call,
  load `production_X.npy` (channels 3–5 are Gx, Gy, Gz), compute G_mag per window
  = `sqrt(Gx² + Gy² + Gz²)`, take the median across all windows.
- Add to the monitoring report dict returned from the component:
  `g_mag_median` (float), `low_gyro_motion` (bool, True when median < 1.1 deg/s),
  `low_motion_collapse_risk` (bool, True when `low_gyro_motion` AND `dominant_pct >= 70`).
- Run `python run_pipeline.py --stages inference evaluation monitoring` on the
  collapsed session (2025_03_23_15_23_10).
- Confirm `outputs/monitoring/monitoring_report.json` contains:
  `"g_mag_median": <value near 0.5>`, `"low_gyro_motion": true`,
  `"low_motion_collapse_risk": true`.
- Done when: monitoring report has all three G_mag fields and shows True for the
  collapsed session.

**Task D1-6 — Add direct CRITICAL_COLLAPSE hard block to Stage 7**
- In `src/components/trigger_evaluation.py`, before calling `engine.evaluate()`,
  read `collapse_level` from the pipeline context (passed via `collapse_signals` in
  the trigger report dict).
- If `collapse_level == "CRITICAL_COLLAPSE"` and the configured adaptation method
  is one of `pseudo_label`, `adabn`, `tent`, `adabn_tent`:
  short-circuit to `TriggerEvaluationArtifact(should_retrain=False, action="REVIEW",
  alert_level="CRITICAL", reasons=["CRITICAL_COLLAPSE: unsupervised retraining blocked"])`.
- Run the full pipeline stages 1-7 on the collapsed session and confirm
  `artifacts/<run_id>/trigger/trigger_decision.json` shows
  `"action": "REVIEW"` and `"should_retrain": false`.
- Done when: trigger artifact for the collapsed session shows REVIEW without relying
  only on the indirect 95% dominance path.

**Task D1-7 — Write collapse framing for thesis and defense**
- The collapse is a thesis strength, not a weakness. It needs to be explicitly framed
  as such in one place. Open `docs/thesis/DEFENSE_PLAN.md` under "Hard Questions."
- Add the following framing (or rewrite in your own voice):

  > "Why does the model predict 100% hand_tapping on some sessions?"
  >
  > The model was trained on actively-gestured wrist data. When the wrist is near-static
  > (G_mag median < 1.1 deg/s — empirically derived from 28 production sessions), the
  > gyroscope goes silent and softmax probability mass concentrates on whichever activity
  > resembles the current gravity orientation: flat wrist (Az ≈ −9.8) → hand_tapping;
  > arm-against-chest (Ax ≈ −9.8) → forehead_rubbing. This is a mechanically explainable
  > domain shift. The pipeline detects it at Stage 4 (CRITICAL_COLLAPSE flag), surfaces
  > it at Stage 6 (low_gyro_motion signal), and blocks unsupervised retraining at Stage 7
  > (REVIEW action). The 28-session analysis and the G_mag < 1.1 threshold are original
  > empirical findings produced during this project — not something inherited from the
  > pretrained model paper.

- Done when: the framing paragraph is in `docs/thesis/DEFENSE_PLAN.md` and you have
  read it out loud once to yourself.

**Task D1-8 — Write accuracy and progress framing for thesis and defense**
- The 18.5% accuracy and overall project progress need an honest, confident answer.
  Open `docs/thesis/DEFENSE_PLAN.md`, same "Hard Questions" section.
- Add the following framing (or rewrite in your own voice):

  > "What accuracy does your system achieve?"
  >
  > The pretrained checkpoint was provided externally (Oleh & Obermaisser, ICTH 2025).
  > Forensic investigation (BN running variance 363.7, Az orientation mismatch, 20+
  > preprocessing configurations tested) revealed that the checkpoint was trained on
  > a different dataset with different preprocessing than our sessions. Maximum accuracy
  > on our data was 18.5%, vs the reported 87%. This is not a pipeline failure — it is
  > evidence of a training/serving distribution mismatch, which is exactly the scenario
  > the monitoring and trigger infrastructure is designed to detect. The system correctly
  > flagged this mismatch as CRITICAL_COLLAPSE and blocked unsupervised retraining.
  > The MLOps contribution of this thesis is not accuracy — it is the infrastructure
  > that detects when a model should not be trusted and governs what happens next.

  > "Is the project actually done / does it work?"
  >
  > Yes. All 11 pipeline stages are implemented with real code (not stubs). 3699 MLflow
  > runs prove iteration history. 428+ artifact runs show the pipeline executing on real
  > data. The 28-session collapse investigation is original empirical research. The
  > monitoring, trigger, domain adaptation, model registry, and calibration components
  > all run end-to-end. The remaining open items (retraining proof, Stage 6 G_mag,
  > Stage 7 direct block) are evidence gaps, not implementation gaps — the code exists,
  > the runs need to be captured and referenced.

- Done when: both paragraphs are in `docs/thesis/DEFENSE_PLAN.md` and you are
  comfortable saying them without reading from notes.

---

#### Day 2 (2026-05-04) — Retraining proof + final defense prep

**Task D2-1 — Run retraining end-to-end (A5)**
- Use a small controlled labeled dataset (`all_users_data_labeled.csv` or synthetic).
- Run: `python run_pipeline.py --retrain --adapt none` (standard retraining, simplest path).
  If that fails, try `--adapt adabn` for the unsupervised path.
- Capture the artifact directory path and confirm it contains:
  `retraining/retrained_model.keras` (or `.h5`), `registration/registry.json`,
  `baseline_update/normalized_baseline.json`.
- Record the exact run ID and artifact path in this worklog under a new entry.
- Done when: one artifact directory contains all three retraining-cycle outputs.

**Task D2-2 — Final defense answer review**
- Read through all framing paragraphs written in D1-7 and D1-8 out loud.
- Check that the thesis/report prose (particularly Ch.4, Ch.6, Ch.8) is consistent
  with what you would say in the defense for each hard question.
- If any chapter still uses old wording (e.g., "87% accuracy", uncaveated Prometheus
  claims, "the model achieves X"), note it here so a targeted edit can be scoped.
- Done when: you can answer the four hardest examiner questions without notes.

---

### Evidence Targets After 2-Day Sprint

After completing the above, you should be able to show:

| Examiner question | Where the evidence is |
|---|---|
| "Show me the normalization config" | `config/pipeline_config.yaml` and `SUBMISSION_READINESS_SUMMARY.md` agree |
| "Run the pipeline live" | `python run_pipeline.py` → stages 1-7 → artifact dir with JSON reports |
| "What does monitoring report?" | `monitoring_report.json` with G_mag, low_gyro_motion, 3-layer summary |
| "What does the trigger decide for collapse?" | `trigger_decision.json` → `action: REVIEW`, `should_retrain: false` |
| "Did retraining ever run?" | Artifact dir with retrained model + registration + baseline update |
| "What accuracy does the model achieve?" | Prepared 2-sentence answer + exclusion record in `src/config.py` |

---

### Things NOT To Touch This Sprint

- `src/components/model_inference.py` (Stage 4) — just verified, do not reopen
- `src/components/model_evaluation.py` (Stage 5) — just refactored and verified
- `mlruns/` — do not delete or reorganize
- `src/train.py` — do not split or restructure
- `src/trigger_policy.py` — do not restructure; only add the one collapse guard

---

## 2026-05-02 - Train vs Production Per-Feature Distribution Diagnostic

### Today in 5 lines

- Extended `notebooks/train_synthetic_production_distribution_comparison.ipynb` so it no longer relies only on `A_mag`/`G_mag` for the train-vs-production comparison.
- Added per-class similarity, per-axis sample-level PSI heatmap, and 4 s window-level per-axis PSI heatmap; reframed the section as descriptive only after the earlier "why hand_tapping wins" framing was disproved by the actual rankings.
- Added a side-by-side feature table (training column on the left, production column on the right) with mean, std, delta, and prod/train std ratio for every raw channel and every windowed per-axis feature.
- Added paired bar charts (chart_21 raw 6 channels, chart_22 windowed per-axis features) so the same comparison can be read at a glance.
- Result: Stage 1-3 data is structurally valid (gravity OK, units OK), but production is distribution-shifted from train on per-axis orientation and gyroscope behavior. The notebook does not explain hand-tapping collapse on its own; Stage 4 model behavior (logits on production windows) is the next step.

### Done Today

- New diagnostics in `notebooks/train_synthetic_production_distribution_comparison.ipynb`:
  - Train per-class summary table (`reports/data_distribution_comparison/train_per_class_stats.csv`).
  - Per-class similarity ranking on (A_mag, G_mag) with bar chart_13 and `production_to_train_class_ranking.csv`.
  - Per-session nearest-class assignment in (A_mag mean, A_mag std, G_mag mean, G_mag std) with chart_14 and `production_session_nearest_class.csv`.
  - Window-level "quiet wrist" fraction across 2 s windows with chart_15 and `quiet_wrist_fraction.csv`.
  - Box plots chart_16 (`A_mag`) and chart_17 (`G_mag`) per dataset.
  - Time-series strip chart_18 with 10 s of `Ax`/`Gx` for `sitting`, `hand_tapping`, `smoking`, `hand_scratching`, first production, first synthetic_production.
  - Sample-level per-axis PSI heatmap chart_19 with `per_axis_class_vs_production_shift.csv` and `per_axis_class_ranking.csv`.
  - Window-level per-axis PSI heatmap chart_20 (window length set to 200 = 4 s @ 50 Hz to match Stage 3/4 input) with `windowed_per_axis_features_vs_production.csv` and `windowed_per_axis_class_ranking.csv`.
  - Side-by-side feature table `feature_side_by_side_train_vs_production.csv` (sample + windowed scopes) and paired bar charts chart_21 / chart_22.
  - Final scorecard `scorecard.csv` plus printed headline (closest train class in (A_mag, G_mag) space, production quiet-wrist fraction, gravity-OK flag for all five datasets).

### Evidence And Risk

- All five datasets pass the gravity sanity check (`A_mag` median in 8.5 - 11.0 m/s^2 range): scorecard cell.
- Train `A_mag` median ~9.77, production `A_mag` median ~9.82 - production is not scaled wrong.
- Train `G_mag` median ~11.75 vs production ~3.96 - production has many quieter wrist windows.
- Per-axis heatmaps show `Ax`/`Ay`/`Az` mean shift between train and production, consistent with an orientation difference rather than an energy mismatch.
- Three independent rankings (magnitude shift, sample per-axis PSI, window per-axis PSI) disagree on the closest class. Top matches by metric: magnitude -> `hand_scratching` / `hair_pulling` / `smoking`; sample per-axis -> `knuckles_cracking` / `hand_scratching`; 4 s window per-axis -> `hand_scratching` / `smoking` / `hair_pulling`. `hand_tapping` is not the top match in any of them.
- Risk: per-axis comparisons are not orientation-invariant; some of the "shift" is wrist mounting, not behavior. Gravity-aligned features (`scripts/experiment_gravity_aligned_rotation_v2.py`) are the right next iteration if this notebook is cited in the thesis.
- Risk: train-side window features are computed from the per-class subsample, while production-side windows come from full files. Asymmetry is small but worth a footnote if numbers are quoted.

### Writing Impact

- Thesis can now cite three converging pieces of evidence: (1) preprocessing is structurally valid, (2) production is distribution-shifted on per-axis and gyroscope behavior, (3) no single sensor-statistic ranking predicts model behavior, motivating Stage 4 logit inspection.
- The "why hand_tapping" question is explicitly *not* answered by Stage 1-3 distribution evidence, which is itself a result worth a paragraph.

### Next Session Start Point

- Stage 4: run the trained checkpoint on production windows, dump per-window softmax/logits, build a confusion-style heatmap of predicted-class fractions per session.
- Stage 5: combine Stage 4 model behavior with this notebook's per-feature shifts to write the drift narrative.

### Stage 4 Inference Contract Audit Addendum

Stage 4 evidence generated today:

- `reports/stage4_inference_audit/stage4_inference_contract_report.md`
- `reports/stage4_inference_audit/stage4_inference_contract_report.json`
- `reports/stage4_inference_audit/stage4_top20_probabilities.csv`

Confirmed:

- Default model path resolves to `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`.
- Model MD5 is `4f403fe417e2086e6088caf7c8699869`.
- The 27 April mentor-folder copy has the same MD5, so the runtime model is the mentor copy.
- `production_X.npy` shape is `(1814, 200, 6)`, finite, float32, and channel order is
  `Ax, Ay, Az, Gx, Gy, Gz`.
- Model input shape is `(None, 200, 6)` and output shape is `(None, 11)`.
- Fresh probabilities have shape `(1814, 11)` and every row sums to `1`.
- Prediction uses `argmax(axis=1)` and confidence is max softmax probability per window.
- Runtime class mapping is canonical; index `4` maps to `hand_tapping` exactly once.
- Latest saved prediction CSV and probability NPY match fresh model output.

Finding:

- Stage 4 contract is mostly correct, but the model still predicts `hand_tapping` for
  100% of windows with mean confidence `0.9980`.
- Class-label mapping is not the cause.
- Wrong model path is not the cause.
- Input/output tensor shape is not the cause.
- One Stage 4 artifact bug remains: `ModelInferenceArtifact.predictions_npy_path` points to
  `production_predictions_fresh.npy`, but the exporter never writes that file.

Refactor direction for Stage 4:

- Move the runtime inference logic into `src/components/model_inference.py` or a small
  `src/inference/` package used by that component.
- Keep `src/run_inference.py` only as a thin CLI wrapper, or remove it later if `run_pipeline.py`
  is the only defended entrypoint.
- Default to offline batch inference. Real-time inference should be future scope, not mixed into
  the defended runtime path.
- Add the same four-line method docstrings used in Stages 1-3.
- Add a Stage 4 evidence report directly from the component: model path/hash, model/input/output
  shapes, class mapping, probability checks, prediction distribution, confidence, entropy,
  top-2 margin, and top-3 probabilities.
- Confidence reporting should say "model confidence", not "correctness probability", unless labeled
  validation calibration evidence is available.

### Stage 4 Implementation And Verification Addendum

Implemented after the audit:

- Moved core inference ownership into `src/components/model_inference.py`.
- Reduced `src/run_inference.py` to a thin offline CLI wrapper.
- Removed the unused `mode` field from `ModelInferenceConfig`; Stage 4 is defended as offline
  batch inference.
- Added hard checks for model path, model input/output shape, `production_X.npy` shape, finite input
  values, probability matrix shape, probability row sums, and class mapping consistency.
- Fixed the artifact bug: Stage 4 now writes `production_predictions_fresh.npy` instead of returning
  a path to a file that does not exist.
- Added `inference_report.json` with model MD5, input/model/output contract, class mapping,
  prediction distribution, confidence stats, entropy stats, top-2 margin stats, collapse flags, and
  top-3 probabilities for the first 20 windows.
- Added `metadata_json_path`, `inference_report_path`, `model_md5`, entropy/top-2 stats, dominant
  class, dominant percentage, and collapse level to `ModelInferenceArtifact`.
- Updated `ProductionPipeline._run_inference()` so Stage 4 summary artifacts include the new report
  and collapse evidence.
- Updated deployment packaging and the label-mapping test import after moving logic out of
  `src/run_inference.py`.

Verification performed:

- Syntax check passed for Stage 4 connected files with `python -m py_compile`.
- `python run_pipeline.py --stages inference` passed with run ID `20260502_152120`.
- Stage 4 wrote CSV, prediction NPY, probability NPY, metadata JSON, and `inference_report.json`.
- The new `production_predictions_fresh.npy` exactly matched the CSV `predicted_class` column.
- Probability rows summed to 1 within tolerance.
- Model MD5 stayed `4f403fe417e2086e6088caf7c8699869`.
- Thin CLI wrapper passed with output directory `artifacts/stage4_cli_verify`.
- Later simplification kept Stage 4 as one runtime owner in `src/components/model_inference.py`,
  with `src/run_inference.py` remaining only as a thin CLI wrapper.
- Multi-session check passed on 8 production fused CSVs and saved:
  - `artifacts/stage4_multi_dataset_verify/stage4_multi_dataset_summary.json`
  - `artifacts/stage4_multi_dataset_verify/stage4_multi_dataset_summary.csv`
  - `artifacts/stage4_multi_dataset_verify/stage4_multi_dataset_failures.json`

Important result:

- Current default `production_X.npy` still collapses to `hand_tapping` for 100% of windows with mean
  confidence about `0.998`.
- Across 8 additional production sessions, Stage 4 did not always collapse to `hand_tapping`; one
  session collapsed critically to `forehead_rubbing` at about `98.2%`, while the others had dominant
  class percentages around `46%` to `62%`.
- Therefore Stage 4 is now exposing collapse correctly. The remaining model-quality question is
  model/domain/provenance/orientation behavior, not a hidden Stage 4 artifact or mapping bug.

### Stage 5 Evaluation Refactor Addendum

Implemented after the Stage 5 audit:

- Moved Stage 5 runtime logic into `src/components/model_evaluation.py`.
- Removed `src/evaluate_predictions.py`; Stage 5 now has one runtime owner:
  `src/components/model_evaluation.py`.
- Added thesis-style method docstrings to the Stage 5 component methods.
- Added strict prediction CSV contract validation for Stage 4 columns, probability columns, finite
  values, class-id range, class-name mapping, confidence range, and probability row sums.
- Changed label/prediction length mismatch from silent truncation to a hard `ValueError`.
- Preserved and wrote `dominant_class`, `dominant_pct`, and
  `distribution_dominance_warning` into the Stage 5 artifact summary JSON.
- Fixed temporal duration reporting for 50% overlap: `4 + (length - 1) * 2` seconds.

Verification performed:

- Syntax check passed for `src/components/model_evaluation.py`,
  `src/pipeline/production_pipeline.py`, and the Stage 5 tests.
- Focused tests passed with a fresh local pytest temp directory:
  `tests/test_stage5_evaluation_summary_contract.py` and
  `tests/test_activity_label_mapping_single_source.py` (`6 passed`).
- `python run_pipeline.py --stages inference evaluation` passed with run ID `20260502_222133`.
- Stage 5 now reports the default session as unlabeled, `hand_tapping` dominant at `100.0%`,
  `distribution_dominance_warning=true`, mean confidence about `0.998`, and no classification
  metrics.

## 2026-04-30 - Stage 3 Transformation Refactor And A/B Evidence

### Today in 5 lines

- Stage 1 and Stage 2 refactors were committed before starting Stage 3.
- Stage 3 was refactored into a readable component with explicit unit conversion, optional A/B preprocessing, optional saved-scaler normalization, and a JSON transformation report.
- Default runtime input space is now raw physical units: accelerometer `m/s^2`, gyroscope `deg/s`.
- Saved z-score normalization remains available only for A/B diagnosis through YAML or `--enable-normalization`.
- Pre-refactor A/B evidence showed both raw and z-score variants collapsing to `hand_tapping`, which points beyond a simple scaler-only bug.

### Done Today

- Added `data/prepared/transformation_report.json` generation with:
  `model_input_space`, `feature_space`, channel order, accelerometer/gyro output units,
  unit conversion details, normalization details, windowing shape, labels/stale-label status,
  before/after channel stats, and final tensor quality checks.
- Changed Stage 3 default normalization to `false` in config defaults and YAML.
- Added stale `production_y.npy` protection: unlabeled Stage 3 runs now ignore old labels instead of attaching them to new `production_X.npy`.
- Added optional raw-vs-zscore diagnostic script: `scripts/debug_stage3_input_space_ab.py`.
- Added CLI support for `--enable-normalization` while preserving `--no-normalization`.

### Evidence And Risk

- Pre-refactor report: `artifacts/stage3_ab_diagnostics/pre_refactor_stage3_ab_report.json`.
- Pre-refactor result: both `raw_physical_units_ms2_dps` and `zscore_scaled_current_scaler`
  predicted `hand_tapping` for 100% of 1814 windows.
- Post-refactor report: `artifacts/stage3_ab_diagnostics/stage3_input_space_ab_report.json`.
- Post-refactor result: both raw and z-score variants still predicted `hand_tapping` for 100% of
  1814 windows; raw mean confidence `0.9980`, z-score mean confidence `0.8347`.
- Stage 1 -> Stage 2 -> Stage 3 verification run passed with run ID `20260430_175531`.
- Main residual risk: after Stage 3 audit clarity, a persistent one-class collapse likely means
  model/domain/provenance mismatch rather than only Stage 3 scaler behavior.

### Next Session Start Point

- Continue manual audit into Stage 4 inference.
- Use `data/prepared/transformation_report.json` as the Stage 3 evidence file before touching model retraining.

### Stage 1-3 Closure Addendum For Next Session

Read first tomorrow:

- `docs/STAGE1_TO_3_CLOSURE_NOTES.md` is the current Stage 1-3 closure note.
- `data/prepared/transformation_report.json` is the current Stage 3 evidence artifact.
- `artifacts/stage3_ab_diagnostics/heavy_20260430_180959/heavy_stage3_input_space_ab_report.json`
  is the heavy raw-vs-zscore comparison.
- `artifacts/stage1_paper_parity/stage1_paper_parity_2025_03_23_report.json`
  is the strict paper mean-bin vs current Stage 1 comparison.

Important conclusion:

- Stages 1-3 are clean enough to move to Stage 4.
- Stage 1 uses 20 ms mean aggregation plus limited small-gap interpolation; strict mean-bin-only
  still collapses, so interpolation is not the hand-tapping root cause.
- Stage 3 default now follows the paper/mentor runtime path: accelerometer in `m/s^2`,
  gyroscope in `deg/s`, no gravity removal, no calibration, no external scaler by default.
- Z-score remains only an A/B option. It does not fix the collapse and often increases
  dominant-class behavior.
- Stale `production_y.npy` poisoning is fixed/guarded in Stage 3.

What the 27 April markdown scan adds:

- `27 april meet/MEETING_REVIEW_2026-04-27.md` confirms the mentor folder is the canonical
  reference bundle: `processing.ipynb`, `fit_parser.py`, `all_users_data_labeled.csv`,
  `ADAMSENSE.csv`, and a copy of the same defended model.
- `27 april meet/FIX_SUMMARY_BAD_RESULTS_2026-04-27.md` documented a column-name/scaler
  mismatch. That bug was worth fixing, but its "predictions should be reasonable now" expectation
  is superseded by the 2026-04-30 A/B evidence: column handling is not the remaining root cause.
- `27 april meet/REFACTOR_PLAN_2026-04-27.md` still has useful next-step ideas:
  model MD5 invariant test, shared sensor-column utility, scaler-loader cleanup, transformation
  manifest/report, and window-boundary hygiene.
- `27 april meet/CLEANUP_PLAN_2026-04-27.md` says not to touch `models/pretrained/`,
  not to alter `data/prepared/scaler_train_only.json`, and not to delete mentor evidence before
  replacement evidence is written down.
- `docs/pretrained_model_exclusion_report.md` already documents the strongest current suspicion:
  the runtime checkpoint has an undocumented provenance / BatchNorm fingerprint mismatch and
  repeatedly fails local labeled evidence.

Current problem to carry into Stage 4:

- The same model still predicts `hand_tapping` heavily after Stage 1-3 are aligned and audited.
- Heavy A/B did not show a class-index permutation fix.
- The next weak link is Stage 4 inference/model contract: model path, MD5, input shape, output shape,
  class mapping, probability handling, argmax axis, prediction CSV/NPY/probability consistency,
  and BatchNorm running stats versus current `production_X.npy` stats.

Research / mentor questions to keep for tomorrow:

1. Was `fine_tuned_model_1dcnnbilstm.keras` trained on raw physical units with only internal
   BatchNorm, or on externally z-scored input?
2. Was gyroscope input in `deg/s` or `rad/s` during model training?
3. Was the watch worn on the same wrist and orientation as our production recordings?
4. What were the model-training input channel means/stds, especially `Az`?
5. Is the provided `.keras` file the exact checkpoint behind the reported 87% result?
6. In the 5-fold CV setup, was any scaler refit inside each fold, or was no external scaler used?
7. Was downsampling strict 20 ms mean-bin only, or did the mentor notebook also tolerate/interpolate
   small missing bins?
8. Do the checkpoint BatchNorm moving means/variances match any documented training feature
   distribution?
9. If sensor orientation is the issue, should we test orientation-invariant features or a controlled
   wrist-orientation recollection before retraining?
10. If Stage 4 is clean, should the defended story treat the pretrained model as an operational
    baseline only and move improved accuracy to candidate retraining evidence?

## Consolidated Remaining To-Do Dashboard (2026-04-26)

This is the single human-readable remaining-work list consolidated from:

- `WORKLOG.md`
- `WORK_2026-04-21.md`
- `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md`
- `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md`
- `PIPELINE_DIAGNOSTIC_CHECKLIST.md`
- `orange_audit_closure_plan_2026-04-26.md`
- `docs/COMPONENT_IMPROVEMENT_REVIEW_2026-04-27.md`

Older tracker files remain as evidence and detail. For planning, use this dashboard first. Items below are deduplicated; many old checkboxes map into one row here.

### Remaining Count

| Part | Focus | Remaining items |
|---|---|---:|
| Part 1 | Submission blockers and evidence closure | 12 |
| Part 2 | Pipeline robustness and implementation hardening | 11 |
| Part 3 | Writing, thesis/report, and repo packaging | 13 |
| **Total** |  | **36** |

### Part 1 - Submission Blockers and Evidence Closure (12)

| ID | Task | Main source(s) | Closure evidence |
|---|---|---|---|
| P0-01 | Run full current-branch pytest in the intended thesis environment | P0-AUDIT-2, next-week net-open item 1 | Test log under `reports/` with pass/skip/fail count |
| P0-02 | Run pipeline stages 1-7 on a known session and save artifacts | P0-AUDIT-2, A7, next-week net-open item 2 | Run folder + `run_info.json` + stage artifacts |
| P0-03 | Run local API smoke with the defended pretrained model loaded | P0-AUDIT-2, A8 | `/api/health`, `/api/model/info`, upload response, model path confirmed |
| P0-04 | Run Docker smoke with actual model-loaded inference, not only health | P0-AUDIT-4, A5 | Docker health/model-info JSON + real inference response + container logs |
| P0-05 | Verify canonical scaler source of truth end-to-end | next-week P0.1/P0.2, diagnostic Blocks A/J | Refit or inspect scaler, diff expected files, prove one runtime loader |
| P0-06 | Execute user-grouped evaluation and regenerate the model comparison matrix | next-week P0.3, diagnostic Block G | User-holdout report + old random-split rows marked non-generalization |
| P0-07 | Close pretrained comparison fairness | next-week P0.4, diagnostic Block I | With-scaler vs without-scaler ablation or final documented comparison boundary |
| P0-08 | Produce retraining-governance decision matrix | A4, P0-AUDIT-5, orange plan P0.5 | Healthy/warning/collapse/cooldown/no-labels/worse-candidate artifacts |
| P0-09 | Execute retraining loop and registration/proof path | A5, FIX Track 1 | Logs, candidate artifact, MLflow/run evidence, registration decision |
| P0-10 | Decide API monitoring parity: align API with Stage 6 or document lightweight API path | P0-AUDIT-6, PT-5 | API monitoring decision note + evidence or bounded-scope wording |
| P0-11 | Finish z-score/no-normalization and gravity/orientation baseline evidence | A7, P1.1, diagnostic Block F | Config comparison table and collapse-tendency evidence |
| P0-12 | Rebuild April report after current April-only edits | April-report consolidation track | Clean `thesis/april_report/main.pdf` build log |

### Part 2 - Pipeline Robustness and Implementation Hardening (11)

| ID | Task | Main source(s) | Closure evidence |
|---|---|---|---|
| P1-01 | Add or verify window-level evidence schema | PT-1 | Per-window output includes ids, session, model/scaler version, probabilities, confidence, entropy, drift/OOD fields |
| P1-02 | Add accelerometer/gyroscope synchronization QA artifact | PT-2 | Sync report with match rate, timestamp delta, dropped rows, missing rows, effective sampling rate |
| P1-03 | Verify window-boundary hygiene | P1.2, diagnostic Block D | Test/report proving no participant-crossing windows by construction |
| P1-04 | Run gyro-axis drift quarantine/ablation | PT-3, diagnostic Blocks F/H | All-channels vs accel-only vs gyro-only vs no/clipped gyro-x comparison |
| P1-05 | Ensure final monitoring report completeness | PT-5 | Report covers data quality, sampling/unit checks, sync, drift, confidence, temporal consistency, OOD/proxy risk, recommended action |
| P1-06 | Finish FastAPI status/UI visibility if needed for demo | A8, FIX Track 1 | Screenshot or command evidence; not blocking if API logs are enough |
| P1-07 | Create lightweight inference Docker requirements or explain current 4.5GB image | FIX Track 2, WORK_2026-04-21 K4 | Image-size note or smaller rebuilt image evidence |
| P1-08 | Clean model comparison matrix artifacts | P1.3, diagnostic Block E | Missing `pretrained/current_model` row resolved; duplicate aliases and 306K-parameter outlier labeled |
| P1-09 | Clean MLflow metric schema and keep thesis-critical tracking only | A6, FIX Track 4 | Metric cleanup note or explicit decision to leave runs unchanged |
| P1-10 | Harden default model-path failure behavior | WORK_2026-04-21 J | Helper/fallback tests or explicit decision that current strict path is enough |
| P1-11 | Review component improvement plan before component-level implementation | `docs/COMPONENT_IMPROVEMENT_REVIEW_2026-04-27.md` | Accepted ideas converted into concrete P0/P1 tasks; rejected ideas marked future-work or no-action |

### Part 3 - Writing, Thesis/Report, and Repo Packaging (13)

| ID | Task | Main source(s) | Closure evidence |
|---|---|---|---|
| W-01 | Decide whether April report becomes canonical or remains parallel draft | April-report consolidation track | Worklog decision + one defended source path |
| W-02 | Write fused-data explanation for Ch4/Ch5 | FIX Track 3 | Paragraph/table explaining raw pair to fused CSV to windows |
| W-03 | Write synthetic-data explanation for Ch4/Ch7 | FIX Track 3 | Scope paragraph: stress testing only, not real accuracy proof |
| W-04 | Record own manual sensor dataset if still required | A21, self-recorded dataset pending | Capture log with sessions, timestamps, conditions, device notes |
| W-05 | Run QC for own manual dataset | A22 | Missingness/unit/sampling/alignment report |
| W-06 | Evaluate pipeline behavior on own manual dataset | A23 | Metrics/proxy outputs, confidence, monitoring, trigger bundle |
| W-07 | Compare original vs synthetic vs own data | A24 | Three-way comparison table, charts, interpretation note |
| W-08 | Write DVC restore story and commands | A25, FIX Track 4 | README/REPRODUCE section with `dvc status`, `dvc pull`, `dvc checkout` |
| W-09 | Write MLflow evidence story | FIX Track 4, A6 | Ch5/Ch6 paragraph explaining runs, metrics, artifacts, retraining evidence |
| W-10 | Finish repo readiness and ignore/folder/model certification | A20, FIX Tracks 4-6 | Final readiness checklist; no deletion without evidence transfer |
| W-11 | Finish citation/threshold/literature cleanup | A12, A17 | Threshold citation map refreshed; needed bib entries cited or parked |
| W-12 | Finish final figures and thesis tables | A13, A33, A34 | Figure pack cleaned; 26-session table and participant/class table inserted if still needed |
| W-13 | Finish MLOps positioning, results-vs-future-work framing, and final thesis build plan | A16, A18, A19, A20 | Ch8/summary wording plus final build/readiness sign-off |

### Immediate Execution Order

1. `P0-01` full pytest.
2. `P0-02` pipeline stages 1-7 smoke.
3. `P0-05` canonical scaler verification.
4. `P0-03` local API model-loaded smoke.
5. `P0-04` Docker model-loaded inference proof.
6. `P0-08` retraining-governance matrix.
7. `P0-12` rebuild April report.

Do not start broad repo cleanup before the P0 evidence closure items are done.

---

## April to June 2026 Master To-Do List (Start: 2026-04-15)
 note: this is the master thesis-completion to-do list and must be reviewed/updated in each future worklog update.

### Status Legend
- `OPEN`: not started
- `IN_PROGRESS`: currently active
- `DONE`: completed and validated
- `BLOCKED`: waiting on dependency/decision
- `REMOVED`: descoped — decision recorded in the table, entry kept for traceability
- `ACTIVE`: governance rule or recurring process that stays in force indefinitely

### Branching Rule (for this master wave)

- Do not run this wave on `main`.
- Create one umbrella branch for high-level coordination: `epic/apr-jun-2026-thesis-wave`.
- Execute work in grouped epic branches (below), then use short-lived task branches under each epic branch.
- Merge to `main` only after each group has evidence outputs and checklist closure.

### Master Task Backlog (A1 to A36)

| ID | Status | Task | Expected Output / Evidence | Target Window |
|---|---|---|---|---|
| A1 | DONE | Create and use one dedicated branch strategy for this April-June wave | Umbrella + epic/task branch structure created and used | Apr 15-16 |
| A2 | DONE | Validate synthetic data through full pipeline end-to-end | Synthetic run report with stage-wise metrics and failures | Apr 15-25 |
| A3 | DONE | Evaluate confidence behavior on synthetic and production-like runs | Confidence trend tables and threshold-hit analysis | Apr 15-30 |
| A4 | OPEN | Decide and test retraining-loop activation logic (triggered vs not triggered) | Retraining decision matrix still open; 2026-04-24 diagnostics provide risk basis for the matrix | Apr 20-May 10 |
| A5 | IN_PROGRESS | Execute retraining loop materialization and verify Docker path | User-holdout retraining/evaluation scripts and grouped training changes started; Docker reproducibility note still open | Apr 20-May 15 |
| A6 | OPEN | Clean extra MLflow metrics and keep thesis-critical tracking only | Metric schema cleanup note and updated runs | Apr 18-May 05 |
| A7 | IN_PROGRESS | Compare preprocessing/config combinations to select baseline config | Pipeline diagnostic, train-only scaler refit path, and gravity/z-score ablation script started; final baseline rationale still open | Apr 18-May 12 |
| A8 | IN_PROGRESS | Update FastAPI Web UI with pipeline-status visibility | Partial 2026-04-22: API/UI now supports one fused CSV or a raw accelerometer+gyroscope CSV pair; retraining remains label-gated. Pipeline-status visibility still open. | Apr 25-May 20 |
| A9 | REMOVED | ~~Confirm CI/CD requirement~~ — Decision: CD is out of scope for this thesis. CI (linting/tests) stays; no automated deployment pipeline needed. | Closed 2026-04-16 | — |
| A10 | REMOVED | ~~Confirm pseudo-labeling usage strategy~~ — Decision: Stage 13 (Curriculum Pseudo-Labeling) not implemented in this thesis wave; moved to future work. | Closed 2026-04-16 | — |
| A11 | REMOVED | ~~Confirm AdaBN strategy~~ — Decision: Stage 12/14 advanced optional stages (Wasserstein, Sensor Placement, AdaBN) deferred; not part of core pipeline thesis contribution. | Closed 2026-04-16 | — |
| A12 | IN_PROGRESS | Provide citation-based justification for each operational threshold | Draft mapping exists in `thesis/reference/THRESHOLD_CITATIONS.md` and `docs/thesis/THRESHOLD_TRIGGER_JUSTIFICATION.md`; refresh after threshold changes | May 05-Jun 05 |
| A13 | IN_PROGRESS | Finalize output charts/figures for thesis writing | Figure pack + chapter mapping exist under `thesis/figures/`; final thesis-body insertion and cleanup still open | May 10-Jun 10 |
| A14 | IN_PROGRESS | Debug and harden major code paths (core pipeline first) | Bug-fix log, validations, and updated tests — Batch A-E refactor complete 2026-04-17 | Apr 15-Jun 15 |
| A15 | DONE | Verify complete dataflow understanding (ingest to deploy decisions) | `docs/thesis/DATAFLOW_MAP_A15.md` — complete S1-S11 input/output map, CLI reference, thesis chapter mapping | Apr 15-May 30 |
| A16 | OPEN | Prepare repo narrative for MLOps positioning (PoC vs production-ready) | Thesis narrative section + future-work framing | May 15-Jun 20 |
| A17 | IN_PROGRESS | Build literature base to 75 to 85 papers with chapter traceability | `references.bib` reached 75 entries 2026-04-22 (low-end target met); 11 newly added entries still need \cite{} placement in .tex chapters to appear in compiled bibliography; upper-band (85) and chapter-traceability map still open | Apr 15-Jun 20 |
| A18 | IN_PROGRESS | Deliver thesis draft target (80 to 120 pages) with visual evidence | Current build is already in-band at 89 pages (`thesis/main.log`); page-plan and final image-tracker cleanup still open | Apr 20-Jun 25 |
| A19 | OPEN | Frame major new experiments as validated result or future work | Results-vs-future-work register | May 15-Jun 25 |
| A20 | OPEN | Repo readiness pass (reproducibility + docs + evidence organization) | Final readiness checklist and sign-off block | Jun 10-Jun 30 |
| A21 | OPEN | Record own manual sensor dataset using defined capture protocol | Manual capture log (sessions, timestamps, conditions, device notes) | Apr 18-May 05 |
| A22 | OPEN | Run validation and preprocessing QC for manually recorded data | Data quality report (missingness, units, sampling, alignment) | Apr 20-May 10 |
| A23 | OPEN | Evaluate pipeline behavior on manually recorded data | Metrics, confidence/trigger output bundle for own data | Apr 25-May 15 |
| A24 | OPEN | Compare three data sources: given original data vs synthetic data vs own recorded data | Three-way comparison table, charts, and thesis-ready interpretation note | May 01-May 25 |
| A25 | OPEN | Strengthen DVC usage for reproducibility (data/model version lineage + restore protocol) | DVC rigor note (what is tracked, why, and how to restore) + updated reproducibility checklist | May 01-Jun 10 |
| A26 | DONE | Generate 26-session production comparison charts (baseline vs unit-fix+abstain, 6 charts) | `outputs/charts_26runs/` — 6 PNG charts; run via `conda run -n thesis-mlops python outputs/charts_26runs/plot_26runs.py` | Apr 20 |
| A27 | DONE | Add class-collapse detection thresholds to monitoring config — `dominant_class_warn_threshold` (0.85) and `dominant_class_critical_threshold` (0.95) | Completed 2026-04-21: Stage 6 now emits dominant class, dominant percentage, warning, and critical collapse flags; Stage 7 uses the config-owned 95% critical threshold; covered by `tests/test_post_inference_monitor.py` and trigger-policy tests | Apr 20-May 05 |
| A28 | DONE | Tighten existing monitoring thresholds for unlabeled production data — confidence warn 0.60→0.70, uncertain_pct 30→20%, drift z-score 2.0→1.8, transition_rate 50→35% | Completed 2026-04-21: updated Stage 6 defaults in `src/entity/config_entity.py`; Stage 7 remains at its citation-backed 0.65 confidence and 2.0/3.0 drift trigger thresholds | Apr 20-May 05 |
| A29 | DONE | Archive legacy scripts that were superseded by src/ — train.py, preprocess.py, post_inference_monitoring.py, build_training_baseline.py, build_normalized_baseline.py, inference_smoke.py, audit_artifacts.py, preprocess_qc.py, run_tests.py | Moved to `scripts/archive/` 2026-04-20; no runtime breakage confirmed (no src/ imports from scripts/) | Apr 20 |
| A30 | DONE | Fix Dockerfile.training: remove duplicate pip install (packages already in requirements.txt) and drop build-essential/git to reduce image size | `docker/Dockerfile.training` — removed apt-get block + collapsed to single pip install; estimated ~150-200 MB smaller | Apr 20 |
| A31 | DONE | Thesis Ch7: systematic 25-session pseudo-labeled vs raw retrained model comparison — script `outputs/charts_26runs/compare_models_26sessions.py`, results CSV, 5 charts generated. New subsection `\ref{sec:pseudolabel_vs_raw}` added to ch7. `model_compare_E_dashboard.png` copied to `thesis/figures/thesis_body/`. Key finding: fine-tuned dominant hand_tapping 24/25 sessions; raw predicts all 11 classes in 22/25. | Completed 2026-04-20 | Apr 20 |
| A32 | DONE | Thesis Ch6: add subsection on why training-distribution thresholds are systematically optimistic for unlabeled production data — synthetic training vs real production confidence variance gap | New section `\section{Threshold Calibration Gap}` added to `ch6_monitoring_drift_retraining.tex` 2026-04-20 | Apr 20 |
| A33 | OPEN | Thesis Ch7: add per-session table for the 26-run experiment (session ID, n_windows, mean_conf, review_pct, trigger action, before/after) | LaTeX table in `ch7_experiments_evaluation.tex` | Apr 20-May 10 |
| A34 | OPEN | Thesis Ch4: add participant data table — 6 participants, session counts, total windows, class distribution balance | LaTeX table in `ch4_data_model_development.tex` | Apr 25-May 10 |
| A35 | DONE | Thesis Ch8 future work: add class-collapse detection gap and training-vs-production threshold calibration gap as explicit future-work items | Completed 2026-04-22: (1) new limitations bullet explicitly states Stage 6 thresholds are engineering operating points, not statistically calibrated deployment limits; (2) future-work item 4 now cross-references `\ref{sec:threshold_calibration_gap}` with the same constraint. Build confirmed clean at 92 pages. | Apr 25-May 10 |
| A36 | DONE | Thesis Ch8 future work: add cloud multi-user deployment as a dedicated future-work item — Cloud Run / Azure Container Apps, FastAPI container, multi-tenant inference, privacy, Level 2 MLOps path | Added to `ch8_discussion_conclusion.tex` 2026-04-20 | Apr 20 |

### Grouped Execution Blocks (4 to 5 tasks together)

| Group | Epic Branch Name | Task IDs (Run Together) | Suggested Task Branch Names | Target Window |
|---|---|---|---|---|
| G1 - Foundation and Baseline Evidence | `epic/apr-foundation-baseline` | A1, A2, A3, A7, A15 | `task/a1-branch-setup`, `task/a2-synth-e2e`, `task/a3-confidence-review`, `task/a7-config-sweep`, `task/a15-dataflow-map` | Apr 15-Apr 30 |
| G2 - Manual Data Capture and Comparative Validation | `epic/apr-manual-data-compare` | A21, A22, A23, A24, A4 | `task/a21-manual-capture-protocol`, `task/a22-manual-data-qc`, `task/a23-manual-data-eval`, `task/a24-3way-dataset-compare`, `task/a4-trigger-decision-matrix` | Apr 18-May 25 |
| G3 - Retraining and Threshold Governance | `epic/may-retraining-governance` | A5, A6, A12, A25 | `task/a5-retraining-docker-verify`, `task/a6-mlflow-metric-prune`, `task/a12-threshold-citation-map`, `task/a25-dvc-rigor` | May 01-Jun 10 |
| G4 - Product Visibility and Thesis Packaging | `epic/may-product-thesis-pack` | A8, A13, A16, A17 | `task/a8-fastapi-status-ui`, `task/a13-figure-pack-final`, `task/a16-mlops-positioning`, `task/a17-literature-75-85` | May 01-Jun 20 |
| G5 - Final Hardening and Submission Readiness | `epic/june-hardening-submission` | A14, A18, A19, A20 | `task/a14-core-path-hardening`, `task/a18-thesis-80-120-pages`, `task/a19-results-vs-future-work`, `task/a20-repo-readiness-signoff` | Jun 01-Jun 30 |

### Milestone Plan (Grouped)

| Milestone | Date Window | Groups |
|---|---|---|
| M1 | Apr 15-Apr 30 | G1 start + G2 start |
| M2 | May 01-May 31 | G2 close + G3 + G4 core |
| M3 | Jun 01-Jun 30 | G4 close + G5 close |

### Reminder Rule
- On every future worklog update, update this master section first:
  - task status changes (A1 to A36),
  - branch used for the task,
  - evidence pointer (artifact/log/doc path),
  - and only then append daily work entries.

## APRIL TO JUNE REVIEW-FIRST GOVERNANCE (MANDATORY)

This block is a hard rule for all April to June edits: do not remove core pipeline logic first; review and validate first, then change.

### First Law - Review Before Change
- Review all April changes before any structural edit, deletion, or merge.
- Core pipeline stages are currently the highest-priority thesis path and must be treated as protected until review sign-off.
- For any candidate file removal or merge, record impact on runtime orchestration and stage outputs first.

### Second Law - Clean Ownership (src vs scripts)
- `src/` is the canonical implementation layer for production pipeline logic.
- `scripts/` should remain wrappers, diagnostics, experiment runners, or utilities.
- Remove repetition by keeping one canonical implementation in `src/` and converting duplicated script logic into thin wrappers or references.

### Third Law - Consolidate Safely by Stage Bands
- Band A (stages 1 to 7): inference-monitoring core loop.
- Band B (stages 8 to 11): governed retraining and confidence-governance loop.
- If files are combined, combine only within the same band and only after dependency mapping and smoke-test validation.

### Workstream Added to April-June Aim

| Item | Status | Review requirement | Target outcome |
|---|---|---|---|
| April changes full review (pre-cleanup) | IN_PROGRESS | Mandatory before refactor | Approved review log of what to keep/merge/archive |
| src vs scripts ownership cleanup | OPEN | Required before file moves | Clear boundary: canonical code in `src/`, wrappers in `scripts/` |
| Repetition and duplicate logic removal | OPEN | Must include file-impact map | Reduced duplicate code paths and lower maintenance risk |
| Stage-band consolidation plan (1 to 7, 8 to 11) | OPEN | Must pass review gate first | Safe merge plan without breaking runtime flow |
| Review-before-change gate in all future edits | ACTIVE | Always on | No direct deletion without documented review evidence |

---

## 2026-04-30

### Stage 1 final cleanup and Stage 2 handoff preparation

#### Today in 5 lines

1. Performed a second cleanup pass on `src/components/data_ingestion.py` after the open-file review showed the file was still too long.
2. Restored the requested thesis-style method docstrings with `Method Name`, `Description`, `Output`, and `On Failure` fields.
3. Kept Stage 1 behavior unchanged: selected input writes `data/processed/fused_<dataset_name>_50Hz.csv`, and Stage 2 receives the path through `DataIngestionArtifact.fused_csv_path`.
4. Re-ran the explicit raw-pair Stage 1 command and confirmed the same fused output shape and 50 Hz timing evidence.
5. Updated Stage 1 notes and the manual Stage 1-7 audit guide so the next work item is Stage 2 Data Validation.

#### Evidence captured

- Current `src/components/data_ingestion.py` length: `573` lines, including the restored docstring blocks.
- `py_compile` passed for `src/components/data_ingestion.py`.
- Explicit command passed:
  `python run_pipeline.py --stages ingestion --accel-file data/raw/2025-03-23-15-23-10-accelerometer_data.xlsx --gyro-file data/raw/2025-03-23-15-23-10-gyroscope_data.xlsx`
- Pipeline result: `SUCCESS (1/1 stages)`.
- Output file: `data/processed/fused_2025_03_23_15_23_10_50Hz.csv`.
- Output shape: `(181509, 9)`.
- Output columns: `true_time, Ax, Ay, Az, Gx, Gy, Gz, timestamp_ms, timestamp_iso`.
- Timestamp-gap check: median `0.020000` seconds, mean `0.020021`, max `0.140000`.

#### Next session start point

Start Stage 3 Data Transformation audit. Stage 2 now confirms the Stage 1 fused file, detects `true_time`, reports 50 Hz timing, and detects raw Garmin acceleration as `milliG`.

### Stage 2 Data Validation refactor

#### Work completed

1. Collapsed Stage 2 validation into one runtime file: `src/components/data_validation.py`.
2. Removed the separate `src/data_validator.py` implementation so Stage 2 has one source of truth.
3. Added thesis-style method docstrings with `Method Name`, `Description`, `Output`, and `On Failure`.
4. Fixed the timestamp weak link: Stage 2 now detects `true_time`, `timestamp`, `timestamp_iso`, or `timestamp_ms` instead of only relying on `timestamp`.
5. Added unit-aware acceleration validation: raw Garmin-like `milliG` data is detected and checked against the m/s2 threshold converted to milliG, avoiding false acceleration warnings before Stage 3 conversion.
6. Wired `config/pipeline_config.yaml` validation thresholds into `DataValidationConfig` at runtime.
7. Updated the validation artifact report to include detailed `stats`, not only errors and warnings.
8. Added `threshold_reference_notes` into the Stage 2 validation report so each threshold records citation strength, evidence type, source URLs, and defensible thesis wording.

#### Evidence captured

- `py_compile` passed for `src/components/data_validation.py`, `src/entity/config_entity.py`, `src/pipeline/production_pipeline.py`, and `run_pipeline.py`.
- Stage 1 + Stage 2 command passed:
  `python run_pipeline.py --stages ingestion validation --accel-file data/raw/2025-03-23-15-23-10-accelerometer_data.xlsx --gyro-file data/raw/2025-03-23-15-23-10-gyroscope_data.xlsx`
- Pipeline result: `SUCCESS (2/2 stages)`.
- Latest run ID after adding threshold citations: `20260430_150837`.
- Validation report: `artifacts/20260430_150837/validation/validation_report.json`.
- Key validation stats:
  - `timestamp_column`: `true_time`
  - `actual_frequency_hz`: `50.0`
  - `duplicate_timestamp_count`: `0`
  - `acceleration_unit_detected`: `milliG`
  - `max_acceleration_milliG_equivalent`: `5098.58`
- Current warnings:
  - `75` timestamp gaps larger than `0.050s`
  - `Gx` max `800.86 deg/s` exceeds `500.00 deg/s`
  - `Gy` max `584.83 deg/s` exceeds `500.00 deg/s`
- Focused tests passed: `23 passed` from `tests/test_validation_gate.py`, `tests/test_fix_regression.py`, and `tests/test_data_validation.py`.

#### Threshold evidence note

- The mentor/paper-backed preprocessing contract in `config/pipeline_config.yaml` supports `milliG -> m/s2`, no gravity removal, StandardScaler, and 50 Hz/windowing parity.
- The Stage 2 thresholds (`0.05` missing ratio, `50 m/s2`, `500 deg/s`, `10%` frequency tolerance) are local project/sensor-spec/empirical decisions, not direct paper quotes. They remain configurable and are now written into the validation report for audit traceability.

---

## 2026-04-29

### Drift investigation: orientation drift vs behavioral drift, plus pipeline audit

#### Today in 5 lines

1. Quantified the train-vs-production distribution gap at the pre-NumPy boundary (no z-score), confirming two distinct drift mechanisms: **orientation drift** on the accelerometer (mean shift up to 2.67 m/s²) and **behavioral drift** on the gyroscope (variance ratio 1.69×–2.24×).
2. Rejected the magnitude-only feature collapse proposed externally; ran three rotation experiments (v1 per-session to train mean; v2a per-session to canonical [0,0,−9.81]; v2b per-window to canonical) to test whether orientation drift can be removed without losing directional information.
3. Per-window canonical rotation (v2b) collapsed accelerometer variance 3-5× while leaving gyro variance untouched — proving gyro drift is real motion, not orientation, and cannot be transformed away.
4. Audited the rest of the monitoring pipeline. Found 11 issues organised by stage, including a 4× dwell-time inflation bug (`WINDOW_DURATION_SECS = 8.0` vs actual step = 2 s), an approximate (binary) entropy formula that disagrees with `drift_monitor.py`'s true Shannon entropy, and a flip-rate threshold conflict (0.25 vs 0.35) across `TriggerThresholds` and `TriggerEvaluationConfig`.
5. Compiled a research-backed threshold reference table (Hendrycks & Gimpel 2017, Page 1954 CUSUM, Gama 2014 DDM, Gretton 2012, Banos 2014, Mannini & Sabatini 2010) covering confidence, temporal, drift, and voting/cooldown groups; attached priority fix order.

#### Evidence captured

- `scripts/compare_train_vs_prod_distribution.py` — pre-zscore mean/std table, train (users 1-4, 253 711 rows) vs 26 timestamped production sessions (10 532 297 rows).
- `scripts/experiment_gravity_aligned_rotation.py` — v1 rotation experiment (per-session, mean-accel target). Result: 6 → 3 drift alerts; Az std 2.20 → 1.19; Gy/Gz std got worse (1.69 → 2.11, 2.24 → 2.54), proving rotation cannot remove gyro behavioral drift.
- `scripts/experiment_gravity_aligned_rotation_v2.py` — v2a (per-session canonical) and v2b (per-window canonical). Result: v2b collapses Ax/Ay/Az std to 1.39/1.60/1.37 (raw 4.79/4.08/6.78) while gyro Gy/Gz std stays at 28.46/38.77.
- `docs/DRIFT_INVESTIGATION_2026-04-29.md` — full writeup with TL;DR, step-by-step journey, rejected magnitude-only prescription, three-phase remediation plan, and a stage-organized pipeline audit (Stages 3, 5, 6, 7, 10) covering 11 issues with research-backed threshold recommendations.
- `docs/DRIFT_INVESTIGATION_CHAT_2026-04-29.txt` — condensed transcript of the investigation as evidence trail.

#### Pipeline issues catalogued (by stage)

- **Stage 3** — Scaler architecturally cannot rotate a 3D coordinate system (1 issue).
- **Stage 5** — Calibration temperature defaults to 1.0 (off); `mean_confidence` is inflated (1 issue).
- **Stage 6** — Dwell time inflated 4× (HIGH); approximate vs true Shannon entropy mismatch with `drift_monitor.py` (HIGH); drifted-channel counter uses 1.0σ but alert fires at 1.8σ (MEDIUM); MMD bootstrap iterations = 40 vs literature recommendation 1000+ (MEDIUM); two coexisting drift monitors with different metrics, PSI calibrated but never called at runtime (MEDIUM); hardcoded `K = 11` in entropy formula needs verification against actual class count (MEDIUM); `is_training_session` flag — verify wiring (LOW). 7 issues total.
- **Stage 7** — Threshold duplication with conflicting defaults across `PostInferenceMonitoringConfig`, `TriggerEvaluationConfig`, `TriggerThresholds`: `flip_rate_warn` is 0.25 vs 0.35, `drift_zscore_warn` is 1.8 vs 2.0, `confidence_warn` is 0.70 vs 0.65 (HIGH); entropy thresholds 1.8/2.2 don't scale with K and are infeasible for K=4 (MEDIUM); `batch_accumulation_min = 100` defined but unused (LOW). 3 issues total.
- **Stage 10** — Baseline staleness alert (90 days) raises a log warning but does not action-gate Layer 3 (LOW).

#### Recommended thesis-defensible thresholds

- Confidence: warn 0.70, critical 0.50; entropy `0.5·log K` warn / `0.7·log K` critical; uncertain ratio 0.15/0.30.
- Temporal (2 s steps): flip-rate warn 0.20, critical 0.35; mean dwell warn < 6 s; short-dwell ratio warn > 0.40.
- Drift: z-score warn 2.0σ, critical 3.0σ; min drifted channels 2 warn / 4 critical; PSI 0.20; MMD bootstrap iterations 1000+.
- Voting: 2-of-3 retained; 3 consecutive warnings; cooldown 24-72 h.

#### Leftover and risk

- None of the audit findings have been applied to the runtime pipeline. All scripts and docs are read-only diagnostics.
- Stage 6.1 (dwell × 4 inflation) means every monitoring report ever generated has reported dwell time 4× too high — historical figures need re-interpretation.
- Stage 6.2 (entropy mismatch) means `entropy_p95` in `drift_reference.json` is not directly comparable to `mean_entropy` in monitoring reports.
- The gravity-alignment Phase 1 fix requires refitting `scaler_train_only.json` and `models/drift_reference.json` — coordinated change across preprocessing + monitoring.
- Behavioral gyro drift (1.7σ–2.2σ) cannot be transformed away. Real options: collect labeled production-style data, augment training, or accept the alert. Threshold relaxation rejected as it defeats the purpose of monitoring.

#### Writing impact

- Provides a clean drift-mechanism narrative for the thesis monitoring chapter: orientation drift (fixable) vs behavioral drift (real residual signal).
- Stage-organized audit serves as the basis for the "monitoring threshold calibration" subsection with cited research backing each value.
- Strengthens the defense argument: monitoring system distinguishes false-alarm sources (orientation) from genuine model risk (behavioral cohort gap).

#### Next session start point

- Apply Stage 6.1 (dwell multiplier) and Stage 6.2 (true Shannon entropy) as the two cheapest correctness fixes — single-line changes in `src/monitoring/post_inference_monitor.py`.
- Decide flip-rate single source of truth (Stage 7.1) and propagate.
- Decide whether to apply gravity-alignment Phase 1 now or leave as documented future work.

### Repo cleanup master plan prepared

#### Today in 5 lines

1. Created cleanup-planning branch `repo-noise-plan-2026-04-29` from the current manual audit state.
2. Inspected the top-level repo footprint and confirmed the biggest safe cleanup targets are generated/non-runtime folders: `artifacts/` (~53.3 GB), `outputs/` (~5.0 GB), `mlruns/` (~3.9 GB), and `data/raw_backup/` (~3.65 GB).
3. Verified the protected runtime surface: `run_pipeline.py`, `src/`, `config/`, `docker/`, `.github/`, `tests/`, DVC pointers, and runtime model/baseline files.
4. Confirmed current runtime code imports Stage 6/10 support from `src.monitoring`, not from `scripts/`, so script cleanup can be planned separately from pipeline runtime safety.
5. Replaced the draft cleanup note with `docs/REPO_CLEANUP_PLAN_2026-04-29.md`, including keep/delete/archive decisions, execution waves, and verification gates.

#### Evidence captured

- `docs/REPO_CLEANUP_PLAN_2026-04-29.md` - current master cleanup plan for safe repo-noise removal.
- Branch: `repo-noise-plan-2026-04-29`.

#### Next cleanup start point

- Start with Wave 1 only: generated caches/temp folders, scratch root files, and scratch `scripts/temp_*.py` files.
- Do not touch `src/`, `tests/`, `config/`, `docker/`, `.github/`, DVC metadata, or runtime model/baseline files during the first cleanup wave.

---

## 2026-04-28

### Evening continuation - Stage 1 ingestion simplification and evidence run

#### Today in 5 lines

1. Refactored Stage 1 ingestion so each selected dataset writes its own fused file: `data/processed/fused_<dataset_name>_50Hz.csv`.
2. Removed the hard-to-debug Stage 1 reuse path: manifest caching, already-processed skips, Decoded folder fallback, canonical `sensor_fused_50Hz.csv` syncing/copying, and `reused_existing`.
3. Kept the Stage 2 handoff contract through `DataIngestionArtifact.fused_csv_path`; changed the artifact default `source_type` to `"unknown"` and removed the stale `reused_existing` flag.
4. Updated pipeline-facing text and fallback resolution so `run_pipeline.py` / `src/pipeline/production_pipeline.py` prefer dataset-specific fused files instead of the old canonical filename.
5. Added `docs/STAGE1_INGESTION_REFACTOR_NOTES.md` with the manual Stage 1 command, expected output file, fused-file inspection command, and 50 Hz timestamp-gap check.

#### Evidence captured

- `py_compile` passed for `src/components/data_ingestion.py`, `src/entity/artifact_entity.py`, `src/pipeline/production_pipeline.py`, and `run_pipeline.py`.
- Explicit raw-pair ingestion command passed:
  `python run_pipeline.py --stages ingestion --accel-file data/raw/2025-03-23-15-23-10-accelerometer_data.xlsx --gyro-file data/raw/2025-03-23-15-23-10-gyroscope_data.xlsx`
- Output written:
  `data/processed/fused_2025_03_23_15_23_10_50Hz.csv`
- Fused CSV check:
  shape `(181509, 9)` with columns `['true_time', 'Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz', 'timestamp_ms', 'timestamp_iso']`.
- 50 Hz check:
  median timestamp gap `0.020000` seconds; mean `0.020021`; max gap `0.140000`.
- The old `data/processed/sensor_fused_50Hz.csv` still exists from a previous run, but the refactored Stage 1 run did not update or recreate it.

#### Leftover and risk

- Stage 1 is much more traceable, but `src/components/data_ingestion.py` is still above the requested 200-350 line target because the required helper list and docstring style are verbose. A second cleanup pass can shorten it further without changing behavior.
- Only `--stages ingestion` was smoke-tested in this pass. A Stage 1 to Stage 2 handoff run should still be captured before claiming full stage-band validation.
- Do not clean old processed/generated files yet. Keep them as evidence until the dataset-specific output path has been checked through stages 1-7.

### Full-day roll-up — notebook alignment to production pipeline + root-cause diagnosis of "13% on training data"

#### Today in 5 lines

1. Aligned `notebooks/27april_model_preprocess_test_OPTIMIZED.ipynb` (and the byte-identical non-OPTIMIZED copy) with the production pipeline contract: 1 ms `merge_asof` tolerance, 50 Hz resample, canonical alias resolver, Butterworth high-pass gravity removal (0.3 Hz, order 3, `filtfilt`), domain calibration, scaling via `src/utils/scaler.py:load_canonical_scaler`, and drift gating via `src/monitoring/drift_monitor.py:DriftMonitor` with auto-calibration of `models/drift_reference.json` from `all_users_data_labeled.csv` users 1-4.
2. Added five debug affordances to the OPTIMIZED notebook: `APPLY_CANONICAL_SCALER` master toggle, `REFERENCE_NPY_PATH/LABELS` (renamed away from "production" so users can repoint), a sampling-rate sanity check in Step 1, an `if/else` gate in Step 4 around the canonical scaler, an inline `report_input_space()` printed before each `model.predict`, and a new `Step 5b — Reference-array sanity check` cell that runs the loaded model on `production_X.npy` with no preprocessing and reports per-channel stats + accuracy.
3. Ran a full direct-Python diagnosis (no notebook) on `data/prepared/production_X.npy` (shape `(673, 200, 6)`) against `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` and proved: (a) `production_y.npy` shape `(3852,)` is **not** the labels for `production_X.npy` — they cannot be paired; (b) running X as-is gives 16.94% accuracy and 0.7740 mean confidence; (c) running with the canonical scaler reapplied gives 8.62% with 0.9926 confidence (collapses to one class); (d) reconstructing labels from `all_users_data_labeled.csv` per-user (user 2 first 67,400 rows) yields 16.94% — the **mentor's pretrained model is collapsing to classes 1 and 4 regardless of preprocessing**.
4. Verified `27 april meet/fine_tuned_model_1dcnnbilstm.keras` is byte-identical to the pretrained one (same accuracy, same confidence, same prediction distribution) and that `models/retrained/har_model_20260327_213930.keras` referenced by `scripts/calibrate_drift_monitor.py` does **not exist on disk** — only the mentor's pretrained checkpoint is available.
5. Cell-2 helper file rewrites for the OPTIMIZED notebook went through three iterations of this conversation and are documented as a self-contained cell-source script pattern; both `27april_model_preprocess_test.ipynb` and `27april_model_preprocess_test_OPTIMIZED.ipynb` now share the same updated cell layout (31 cells, with the new Step 5b inserted at index 15).

#### Done today

- **Notebook alignment (P0-09 / P1-04 evidence)**: rewrote cells 2 (config), 3 (imports), 6 (ingestion), 8 (column detection), 10 (preprocessing), 26 (drift) to match the production pipeline. Imports now route through `from src.utils.scaler import load_canonical_scaler, assert_scaler_integrity, CANONICAL_SCALER_PATH` and `from src.components.data_ingestion import SENSOR_COLUMN_ALIASES, _build_alias_rename_map` and `from src.monitoring.drift_monitor import DriftMonitor, CHANNELS`.
- **Notebook debug affordances**: added `APPLY_CANONICAL_SCALER` (default `True`), `REFERENCE_NPY_PATH`, `REFERENCE_NPY_LABELS`, `MERGE_TOLERANCE_MS`, `TARGET_HZ`, `DOMAIN_CALIBRATION` to cell 2; sampling-rate sanity check at Step 1 that infers Hz from `timestamp` and warns if `WINDOW_SIZE=200` no longer covers `200/TARGET_HZ` seconds; `report_input_space()` helper that classifies arrays as `SCALED`/`RAW`/`AMBIGUOUS` based on per-channel mean/std heuristics; `Step 5b` reference-array sanity-check cell that runs the loaded model on a pre-windowed `.npy` with no preprocessing and prints accuracy + heuristic verdict.
- **Direct-Python diagnostics**: ran three- and six-variant model evaluation experiments through `/c/Users/shali/anaconda3/envs/thesis-mlops/python.exe`. Key numbers (n=673 windows of `production_X.npy`):
  - X as-is + pretrained model → acc=0.1694, mean_conf=0.7740
  - X scaled (`(x-mean)/scale` with `scaler_train_only.json`) + pretrained → acc=0.0862, mean_conf=0.9926 (collapse)
  - X "un-scaled" (`x*scale+mean`) + pretrained → acc=0.1456, mean_conf=0.7635
  - Predicted class distribution: class 4 (`hand_tapping`) 51.1%, class 1 (`forehead_rubbing`) 23.6%, classes 2/5/6/8/10 ≤1% combined → **model is collapsing**
  - `production_X.npy` per-channel mean ≈ `[0.45, 0.27, 0.30, -0.00, -0.01, 0.01]`, std ≈ `[0.78, 0.77, 1.25, 0.81, 1.00, 0.99]` → already in some scaled space, not the canonical-scaler space
  - `scaler_train_only.json` mean = `[2.34, 0.59, -3.59, 0.67, 0.25, 0.06]`, scale = `[6.89, 4.66, 3.08, 54.79, 15.50, 14.53]` (gyro scales confirm fit on raw deg/s)
- **Label-pair reconstruction**: from `all_users_data_labeled.csv` (385,326 rows; users 1-6 each 60-68k rows), built majority-vote labels per user at WINDOW=200/STEP=100. For user 2 first 67,400 rows: 673 reconstructed labels matching the metadata window count, accuracy still 16.94%. For user 6 first 67,400 rows: 16.49%. Across the CSV first 67,400 rows: 15.60%. **No paired-label candidate recovers expected accuracy → bug is in the model checkpoint, not in pairing.**
- **Permutation / class-shuffle test**: built a confusion matrix and ran the Hungarian algorithm to find the optimal `model_pred → true_label` permutation. Best mapping `{1:0, 3:1, 0:2, 6:3, 4:4, 9:5, 8:6, 7:7, 10:8, 5:9, 2:10}` was discovered, but accuracy still did not exceed ~17% even after permutation, ruling out simple class-index shuffle as the root cause.
- **Misalignment confirmed**: `production_y.npy` has 3,852 entries (sorted, e.g. first 30 are all 0, last 30 are all 10 — class-grouped sample sequence) vs `production_X.npy`'s 673 windows. Every accuracy number anyone has computed against `production_y.npy` since this file was created has been against the **wrong** label array.

#### Leftover and risk

- **`production_y.npy` is broken/misaligned** and is the proximate cause of every "X% on training data" report we've made. Action: rename to `production_y_BROKEN.npy` or delete; or rebuild a paired `(X, y)` from `all_users_data_labeled.csv` with the same window logic that produced `production_X.npy`.
- **The mentor's `fine_tuned_model_1dcnnbilstm.keras` collapses to two classes** (`hand_tapping`, `forehead_rubbing`) on `production_X.npy` regardless of preprocessing. This is the actual blocker for any meaningful evaluation. Possible causes (in priority order): (a) the checkpoint was pretrained on a different HAR dataset and never properly fine-tuned on this 11-class wrist data; (b) it was fine-tuned with a different class-index ordering than `src/utils/label_mapping.py`; (c) it is a half-trained/early-checkpoint that was handed over thinking it was final.
- **`models/retrained/har_model_20260327_213930.keras` is missing** but is referenced by `scripts/calibrate_drift_monitor.py:19`. Either restore it from MLflow (artifact `mlruns/745412409067384126/models/m-*/artifacts/data/model.keras` size 6,095,582 — multiple candidates) or update the script to point at the correct registered version.
- **`scripts/calibrate_drift_monitor.py` cannot run** until the retrained model is restored or repointed. Until then, the notebook's drift cell will auto-calibrate `models/drift_reference.json` on first run from `all_users_data_labeled.csv` users 1-4.
- **Notebook still uses Windows absolute paths** for `DATA_PATH`, `PRETRAINED_MODEL_PATH`, `CANONICAL_SCALER_PATH`, `DRIFT_REFERENCE_PATH`, `DRIFT_REFERENCE_DATA`, `PIPELINE_CONFIG_PATH`, `REFERENCE_NPY_PATH`, `REFERENCE_NPY_LABELS`. Acceptable for the user's local thesis development environment but should be `Path(__file__).resolve().parents[1]`-style or env-var driven before commit.
- The two helper scripts I wrote and immediately deleted (`scripts/_fix_27april_notebook.py`, `scripts/_align_optimized_notebook.py`, `scripts/_add_debug_toggles.py`) are documented in chat history but not in the repo. If the notebook needs to be re-aligned from scratch, the patterns are: (i) load notebook JSON, (ii) iterate cells, (iii) match by header text marker, (iv) replace cell `source` with `text.splitlines(keepends=True)`, (v) `nb.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")`.

#### Writing impact

- **Ch4 (preprocessing)**: the alignment work in this notebook is the second concrete artifact (after `src/preprocess_data.py:GravityRemover`) demonstrating that the project's notebook surface and the production pipeline share a single preprocessing contract. Cite the OPTIMIZED notebook as a worked example of the contract being honored end-to-end.
- **Ch6 (monitoring/retraining) — IMPORTANT**: today's diagnostic invalidates any past evaluation row that used `production_y.npy` as the label source. Ch6 must add a sentence stating that `production_y.npy` was identified on 2026-04-28 as misaligned with `production_X.npy` and that the reported "training-data accuracy" numbers prior to this date were against the wrong label array. The narrative survives — the *mechanism* (label-gated promotion, governance matrix, drift gates) is unchanged — but specific numbers in any "we got X% on training" claim need re-derivation against a freshly reconstructed paired `(X, y)`.
- **Ch7 (experiments)**: model-comparison rows that used `production_y.npy` need an asterisk and a re-run. Once a paired `(X, y)` is rebuilt, the same matrix can be regenerated with valid numbers.
- **Ch8 (future work)**: the mentor-handed model's collapse to two classes elevates "fine-tune the mentor's model on `all_users_data_labeled.csv` users 1-4 with the canonical 11-class mapping" from candidate to **required** before any defended evaluation can be reported. This is now Phase B of `MEETING_REVIEW_2026-04-27.md`'s candidate retrain, but the framing changes from "candidate generation" to "fix-the-defended-model".

#### Next session start point

1. **Decide and execute on `production_y.npy`**: either delete it as broken or replace it with a freshly reconstructed paired-label array. Smallest concrete action: write `scripts/rebuild_production_xy.py` that reads `all_users_data_labeled.csv`, applies the same scaling that produced `production_X.npy` (whatever scaler that was — needs identification), windows at 200/100 with majority-vote labels per user, and writes `data/prepared/production_X_v2.npy` + `production_y_v2.npy` with `production_metadata_v2.json`. Then verify model accuracy on the new pair.
2. **Talk to the mentor** with one specific question: *"Was `fine_tuned_model_1dcnnbilstm.keras` fine-tuned on `all_users_data_labeled.csv` with the 11-class mapping in `src/utils/label_mapping.py`? On users 1-4 only or all 6? And was the input pre-scaled by `scaler_train_only.json`, `scaler_canonical.json`, or raw?"* If yes to all and the model still collapses to two classes on user 2, the checkpoint is corrupt; otherwise we have the right preprocessing target.
3. **Run the OPTIMIZED notebook end-to-end with `APPLY_CANONICAL_SCALER=False`** on `production_X.npy` to confirm the Step 5b sanity-check accuracy matches the direct-Python diagnosis (~16.94%). This validates that the notebook is reproducing the same numbers.
4. **Restore `models/retrained/har_model_20260327_213930.keras`** from MLflow or repoint `scripts/calibrate_drift_monitor.py:19` to a model that exists. Then run `scripts/calibrate_drift_monitor.py` to produce a committed `models/drift_reference.json` and remove the auto-calibrate fallback path from the notebook drift cell.
5. **Fine-tune the mentor's model** on users 1-4 with the canonical 11-class mapping (use `src/components/model_training.py` or the existing training entry point). Validate on user 5; test on user 6; promote via `scripts/run_model_promotion_gate.py` only if `macro_f1_delta >= 0.01`. Even one epoch of fine-tuning should break the class-1/class-4 collapse if the architecture is sound.

---

## 2026-04-27

### Full-day roll-up — review, mentor folder, root-cause fix, governance scripts

#### Today in 5 lines

1. Captured the component-by-component ML/MLOps improvement review (`docs/COMPONENT_IMPROVEMENT_REVIEW_2026-04-27.md`); fed it as P1-11 into the dashboard.
2. Reviewed the mentor folder `27 april meet/` (ADAMSENSE.csv, all_users_data_labeled.csv, processing.ipynb, fit_parser.py, fine_tuned_model_1dcnnbilstm.keras): wrote `MEETING_REVIEW_2026-04-27.md` confirming the defended runtime model is byte-identical to mentor's, and gravity handling is already mentor-aligned (milliG→m/s² only, gravity removal OFF by default).
3. Diagnosed and fixed the "bad production predictions" root cause — column-name mismatch (`Ax_w` vs `Ax`) was preventing the train-only scaler from normalizing production data; added flexible regex column detection in `src/preprocess_data.py` (`_detect_sensor_columns`, modified `detect_data_format`); documented in `docs/FLEXIBLE_COLUMN_DETECTOR_2026-04-27.md` and `27 april meet/FIX_SUMMARY_BAD_RESULTS_2026-04-27.md`.
4. Authored four new evidence/governance scripts: `scripts/build_governance_matrix.py` (P0-08 retraining-governance matrix), `scripts/compare_scaler_policies.py` (train-only vs all-users-experimental scaler comparison + `data/prepared/scaler_all_users_experimental.json`), `scripts/run_model_promotion_gate.py` (label-gated promotion eligibility from the comparison report), `docs/MODEL_PROMOTION_POLICY.md` (formal candidate-only promotion policy).
5. Drafted `27 april meet/NEW_MODEL_DESIGN_PLAN_2026-04-27.md` — a candidate v3 architecture plan (BiLSTM + temporal attention + GlobalAvgPool, label smoothing, AdamW + cosine restarts, temperature scaling, optional SimCLR pretrain) explicitly gated as candidate-only with no preprocessing changes; ran 24+ pipeline executions today (artifacts under `artifacts/20260427_*/`, MLflow runs under experiment `745412409067384126`).

#### Done today

- **Mentor folder audit**: confirmed `27 april meet/fine_tuned_model_1dcnnbilstm.keras` MD5 `4f403fe417e2086e6088caf7c8699869` matches `models/pretrained/` and `models/actual model/`. Mentor preprocessing (`processing.ipynb`) → expand list-cols → concat → `*0.00981` accel → asof-merge tol=1ms → resample 20ms → activity labels. Locked decision: do **not** rebuild a new defended model; run **one** mentor-aligned candidate retrain only.
- **Root-cause fix (column detector)**: replaced hardcoded sensor-column lookup with regex detection accepting `Ax`, `Ax_w`, `accel_x`, mixed case, etc. Renames in-place to canonical `[Ax,Ay,Az,Gx,Gy,Gz]` so the train-only scaler can apply correctly to production `Ax/Ay/...` files. Backwards-compatible with already-canonical input.
- **Governance evidence scaffolding**: `build_governance_matrix.py` produces `reports/governance_matrix_2026-04-27.{json,md}` with six scenarios (healthy, warning_review, critical_trigger_offline_candidate, collapse_review_no_auto_retrain, worse_candidate_no_promotion, better_candidate_promotion_eligible). `compare_scaler_policies.py` produces channel-wise mean/scale deltas + macro-F1 per split per (defended, candidate) × (train-only, all-users) and persists an experimental scaler at `data/prepared/scaler_all_users_experimental.json`. `run_model_promotion_gate.py` consumes the comparison and decides eligibility against a configurable macro-F1 delta (default 0.01).
- **Notebook work**: heavily updated `notebooks/model_inference_diagnostics.ipynb` (4 models × 4 datasets × shared preprocessing) and added a new `notebooks/27april_model_preprocess_test.ipynb` for column-detector and scaler-mismatch verification.
- **Pipeline executions**: 24+ artifact folders generated today (`artifacts/20260427_143107` … `20260427_191014`) plus matching MLflow runs and pipeline-result JSONs under `logs/pipeline/`. These are pre-fix and post-fix smoke runs validating the column-detector behavior end-to-end on real production sessions.
- **Untracked scratch noise** accumulated under repo root and `scripts/` (`temp_dia.py`, `temp_final.py`, `temp_pre.py`, `models_test.py`, `unify_scalars.py`, `temp.txt`, `pt.md`, `reasoningtxt.txt`, `thesis_doc.txt`, `mlops.docx`, plus mirrored CSVs in `notebooks/`). See cleanup plan.

#### Leftover and risk

- Today produced four new scripts but **none were committed yet**; cleanup plan must decide which scripts are evidence (keep), which are scratch (delete), and which need a unit test before committing.
- `scripts/unify_scalars.py` references stale paths (`config.json`, `models/retrained/scaler_config.json`) and assumes the old non-canonical scaler — superseded by `data/prepared/scaler_train_only.json`. Decision pending: delete or rewrite header to clarify it is an obsolete one-shot.
- `models/archive/2026-04-27_model_matrix_cleanup/` and `models/mmd_reference_windows.npy` are untracked artifacts that need DVC tracking or `.gitignore` decision.
- `.pytest_tmp/`, `.tmp_pytest/`, `.tmp_pytest_current/`, `tmp_pytest_trigger/`, `tmp_pytest_trigger2/`, `tmp_run3/` are pytest scratch directories with permission-denied subfolders polluting the workspace; need `.gitignore` entry and a one-shot purge.
- Notebook duplicate CSVs (`notebooks/synthetic_all_users_labeled_v1.csv`, `notebooks/synthetic_labeled.csv`, `notebooks/2025-08-12-17-01-38_*.csv`) duplicate data in `data/synthetic_production/` and the mentor folder; need to be moved or deleted.
- Multi-line free-text scratch (`pt.md`, `reasoningtxt.txt`, `temp.txt`, `thesis_doc.txt`, `mlops.docx`) at repo root — none of these belong on the main branch.
- The `27 april meet/` folder is untracked and contains a 134.9 MB raw CSV plus a 58.7 MB labeled CSV and the mentor's `.keras` (already mirrored in `models/pretrained/`); decide DVC vs `.gitignore` vs move-into-`internal/reference/`.

#### Writing impact

- Ch4 (preprocessing): cite mentor's `processing.ipynb` as canonical reference; add the gravity-OFF parity sentence (`MEETING_REVIEW_2026-04-27.md` §4.3) into `docs/thesis_section_4x_pretrained_analysis.md` and `thesis/april_report/chapters/ch4_data_processing_model_development.tex` §4.5.
- Ch6 (monitoring/retraining): describe the new governance matrix script and its six scenarios as concrete artifact behind A4/P0-08.
- Ch7 (experiments): scaler-policy comparison (train-only vs all-users) becomes a labeled-evaluation row with reproducible command.
- Ch8 (future work): note v3 architecture and SimCLR pretrain remain candidate-only/future work, and that the column-detector is the production-robustness improvement that landed today.

#### Next session start point

1. Apply the cleanup plan (`27 april meet/CLEANUP_PLAN_2026-04-27.md`) — purge tmp dirs, decide on scratch files, gate the four new scripts with a smoke test.
2. Run the bounded mentor-aligned candidate retrain (Phase B of `MEETING_REVIEW_2026-04-27.md`) → `scripts/retrain_user_holdout.py` → `scripts/evaluate_user_holdout.py` → `scripts/compare_scaler_policies.py` → `scripts/run_model_promotion_gate.py`.
3. Lock the gravity/preprocessing-parity sentence in the April-report Ch4.
4. Address Top-3 high-priority refactors from `27 april meet/REFACTOR_PLAN_2026-04-27.md` (single-source-of-truth scaler loader, sensor-column rename utility, pytest scratch dir hygiene).

---

## 2026-04-26

### Evening session — P0.1 model identity closure and defended-scope cleanup

#### Today in 5 lines

1. P0-AUDIT-1 was closed with **Option A**: the defended runtime model is `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`.
2. The retraining story was locked as governance/candidate generation, not automatic promotion; `models/registry/model_registry.json` shows `current_version: null`.
3. `docs/THESIS_CONSISTENCY_NOTES.md` section 5 now carries the canonical model sentence, citation anchors, and stage-scope clarification.
4. `internal/workflow/EVIDENCE_LEDGER.md` EV-009 marks the pretrained model as **DEFENDED RUNTIME MODEL**; EV-415, EV-416, and EV-417 mark stages 12-14 as future-work scaffolding.
5. `internal/writing/defense_qa.md`, `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md`, and `orange_audit_closure_plan_2026-04-26.md` were updated so defense prep, trackers, and the audit plan tell the same Option A story.

#### Done today

- Read the actual code and artifacts rather than relying on markdown claims: `run_pipeline.py` and `src/pipeline/production_pipeline.py` define an 11-stage defended pipeline; `models/retrained/` contains candidate artifacts; `models/registry/model_registry.json` confirms no promoted retrained current version.
- Added the defended-model Q&A block to `internal/writing/defense_qa.md`: model identity, why retraining does not replace the defended model, and why stages 12-14 are future work.
- Corrected older `defense_qa.md` contradictions that still described a 14-stage defended pipeline and treated Prometheus/Grafana/Alertmanager as active evidence.
- Closed `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md` P0-AUDIT-1 and kept the remaining README/Ch4/Ch7 wording sweep under P0.6.
- Updated `orange_audit_closure_plan_2026-04-26.md` so P0.1 is recorded as closed and the execution order no longer asks to choose between Option A and Option B.

#### Leftover and risk

- P0.6 remains open: README, original Ch4, April Ch4, Ch7, and exclusion docs still need a final defended-scope wording sweep against the canonical sentence.
- P0.2/P0.4/P0.5 remain open: fresh full verification, Docker model-loaded inference proof, and the retraining-governance matrix still need captured artifacts.
- Professor expectation remains the only real residual risk: if the supervisor expects a promoted retrained model, the thesis should use a hybrid explanation, but the repo state currently supports Option A.

#### Writing impact

- Ch4/Ch5 should state that the supervisor-provided 1D-CNN-BiLSTM is the defended runtime model.
- Ch6 should present retrained artifacts as candidate evidence and governance behavior, not as the deployed defended model.
- Ch7/Ch8 should explain that stages 12-14 are future work; candidate-mode pseudo-labeling remains part of Stage 8, but curriculum pseudo-labeling as "Stage 13" is not defended.

#### Late continuation - P0.6 defended-scope wording sweep

- Flattened the April-report Chapter 4 hierarchy by converting many one-paragraph `\subsection{}` blocks into lower-weight paragraph headings.
- Aligned April-report Ch4 and added April-report Ch7/Ch8 draft boundaries with Option A: pretrained model is the defended runtime; retrained artifacts are candidates/reference evidence.
- Reframed `docs/pretrained_model_exclusion_report.md` and `docs/thesis_section_4x_pretrained_analysis.md` from "pretrained excluded" to "pretrained runtime model with a local quantitative-comparison boundary."
- Updated `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md` and `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md` so the April-report/exclusion-doc sweep is no longer listed as open.

Correction: main thesis-report edits made during the first sweep were reverted in the same session. This wording pass is April-report-only unless a later decision explicitly promotes the April report into the main thesis source.

#### Next session start point

Start evidence verification, not new model-identity writing: run fresh current-branch tests, prove Docker/API model-loaded inference with the defended pretrained model, and build the retraining-governance decision matrix.

---

## 2026-04-25

### Evening session — Chapter 4 rewrite, April-report polish, and four-tracker reconciliation

#### Today in 5 lines

1. April-report Chapter 4 was rewritten as an 11-section thesis-quality chapter at `thesis/april_report/chapters/ch4_data_processing_model_development.tex`; the original `thesis/chapters/ch4_data_model_development.tex` was **not** modified.
2. Cleanup pass landed: title shortened, mental-health-adjacent framing added in §4.1 and §4.2.2 with the safe "not clinical diagnosis" sentence, "explicit explicit" duplicate fixed, replay row-count footnote added, final-model split wording softened to a configured-split + footnote, full channel-statistics table moved to Appendix D and replaced in Ch.4 by a compact mean±std summary, preprocessing-baseline table tightened.
3. April-report `main.tex` graphicspath extended with `../figures/` so generated `ch4_*.pdf` figures resolve; April-report `main.pdf` rebuilt clean (52 pages, ~638 KB, no undefined refs/citations, no LaTeX errors, no rerun warnings, no duplicate labels).
4. Four trackers reconciled in one update: `WORK_2026-04-21.md` (closing addendum L1--L8), `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md` (Already-Done refresh + Newly-raised rows), `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md` (P0/P1/P2 status refresh and net-open work).
5. Stale CV wording (`stratified`, `StratifiedKFold`, `LOSO`) confirmed removed from `thesis/chapters/` and the April report; remaining hits in `src/train.py:12` docstring, `scripts/generate_chapter4_assets.py`, `notes/`, `internal/`, `thesis/writing/defense_qa.md`, `thesis/reference/tech_overview.md`, `thesis/reference/why_inventory.md`, `THESIS_WRITING_AUDIT.md`, `HOW_TO_BUILD_THIS_THESIS_PIPELINE_FROM_SCRATCH.md` — out of safe-edit scope, parked.

#### Done today

- **April-report Ch.4 rewrite (11 sections)** with all required content: chapter purpose, dataset and data sources (incl. ADAM-sense literature anchor), exploratory statistical comparison across data sources (with claim-boundary statement), data characteristics and challenges, preprocessing methodology framed as a train--serve consistency contract, windowing and input representation (4 s context + 2 s cadence), 1D-CNN+BiLSTM model architecture and rationale, training setup and baseline assumptions (grouped user-fold CV with user IDs as groups, train-only scaler fitting, defense-safe paragraph), baseline scope and adaptation boundary, reproducibility and consistency considerations, chapter summary.
- **Pre-edit backup** kept at `.../ch4_data_processing_model_development.tex.bak` so the prior April-report state is recoverable.
- **Generated artifacts referenced**: 10 figures (`ch4_dataset_source_overview.pdf`, `ch4_channel_mean_comparison.pdf`, `ch4_channel_std_comparison.pdf`, `ch4_channel_boxplots.pdf`, `ch4_raw_signal_examples.pdf`, `ch4_preprocessing_flow.pdf`, `ch4_windowing_diagram.pdf`, `ch4_input_tensor_shape.pdf`, `ch4_model_architecture.pdf`, `ch4_training_workflow.pdf`) and 4 generated tables (`ch4_channel_statistics.tex`, `ch4_dataset_shift_comparison.tex`, `ch4_class_distribution.tex`, `ch4_windowing_summary.tex`); 5 in-chapter tables added (data-source roles, preprocessing baseline, layer config, design rationale, training config, split basis, scope boundary, reproducibility anchors, compact channel summary).
- **Safety verified**: original-report file untouched; `git status` shows the April-report tree is gitignored.
- **Citation check**: all 27 `\cite{}` keys verified in `thesis/references.bib`; `reports/chapter4/ch4_missing_citations.md` confirmed empty.
- **Title fix** in `thesis/april_report/main.tex` to remove the repeated "Wearable" wording → `An Offline-First MLOps Pipeline with Governance for Wearable IMU-Based Human Activity Recognition`.

#### Build verification

- `pdflatex -interaction=nonstopmode -halt-on-error main.tex` → `bibtex main` → `pdflatex × 2` (latexmk-equivalent), all clean.
- Output: `thesis/april_report/main.pdf` — **52 pages, ~638 KB**.
- Worst residual overfull = 24.2 pt inside the moved appendix table; section-heading line "Exploratory Statistical Comparison Across Data Sources" overfills by 40.5 pt as a heading-only line; remaining ≤5.3 pt. Worst case before cleanup was 93.7 pt.

#### Tracker writes

- `WORK_2026-04-21.md` — appended Section L "Closing Addendum — Five-Day Roll-Up" covering A27/A28 closure (L1), FastAPI two-file upload + Docker size (L2), thesis citation pass (L3), submission readiness verification (L4), pipeline diagnostic register (L5), 2026-04-24 pipeline-hardening + governance docs (L6), Ch.4 rewrite + April-report polish (L7), and tracker state summary (L8).
- `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md` — Already-Done table now lists the April-report Ch.4 rewrite, polish pass, and clean build; Newly-Raised section adds stale CV wording, hardening-code verification, self-recorded validation dataset placeholder, and the original-vs-April Ch.4 reconciliation. Next-Action block split into Pipeline-evidence and April-report-consolidation tracks.
- `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md` — added 2026-04-25 progress refresh: P0.1 / P0.2 / P0.3 marked landed-but-unverified; P0.4 still open (pretrained fairness ablation not run); P1.1 / P1.2 partially scaffolded; P2.1 partially addressed (April-report Ch.4 wording already tightened); P2.2 captured in `docs/`. Net-open work block lists the six concrete checks for the next focused session.

#### Leftover and risk

- The new pipeline-hardening code paths (canonical scaler utility, refit script, user-holdout training/eval scripts, drift monitor, gravity-removal ablation) **were not exercised in this session**. Verification (`pytest`, API smoke, drift-monitor smoke, thesis full build, Docker smoke) is the prerequisite for treating L6 as closed.
- Original `thesis/chapters/ch4_data_model_development.tex` and the April-report Ch.4 are now two parallel chapter sources. If the April version is to become canonical, a separate session must propagate the polish (title, mental-health-adjacent framing, formatting) into the original report and the other chapters.
- Self-recorded final validation dataset still pending; the `% TODO` placeholder in §4.2.5 must remain until data exist.

#### Writing impact

- Ch.4 (April version): closed for the moment; defensible as a thesis-quality chapter with descriptive-only framing for replay and synthetic data.
- Ch.5 / Ch.6: still need wording on the canonical scaler and retraining-governance once L6 verification lands.
- Ch.7 / Ch.8: still need the in-sample-vs-user-holdout separation and the pretrained-exclusion paragraph once P0.4 closes.

#### Next session start point

1. Run `pytest tests/ -q --tb=short` against the dirty workspace; record pass/skip/fail count under `reports/`.
2. Smoke `python run_pipeline.py --help` and stages 1--7 against `feature/api-two-file-upload`; capture artifacts.
3. Refit canonical scaler with `scripts/refit_scaler_train_only.py`; diff the new `data/prepared/scaler_train_only.json` against `models/retrained/scaler_config.json`; confirm only the canonical one is loaded at runtime.
4. Run `scripts/evaluate_user_holdout.py` and regenerate the model comparison matrix; relabel old random-split rows as non-generalization.
5. Decide P0.4: pretrained-compatible scaler or final exclusion; update `thesis/chapters/ch7_*` accordingly once chosen.
6. Close A7 (z-score vs no-normalization comparison) and start A4 (retraining decision matrix).

#### Planned next session — title

**2026-04-25/26 — Read-Only Pipeline Robustness and Evidence Verification Audit.**

Run in Codex/Copilot, not in this Claude session. External prompt file: `sandbox:/mnt/data/temporary_pipeline_audit_prompt_2026-04-25.md`. Hard rule for that session: **do not edit anything; only audit, classify, and report evidence**. Output expected = an audit report under `reports/` plus a short summary appended to this worklog. Any required code/doc changes are queued back into `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md` and not applied during the audit.

### Late evening - read-only audit closure and ORANGE plan

#### Today in 5 lines

1. Completed the planned read-only robustness/evidence audit on branch `feature/api-two-file-upload`.
2. Audit verdict: **ORANGE** - structurally strong pipeline, but not yet 100% evidence-verified.
3. Main P0 risk: model identity contradiction between pretrained default, pretrained-exclusion docs, retrained-model thesis wording, and April-report wording.
4. Safe verification commands run: `python run_pipeline.py --help`, `pytest --collect-only -q -p no:cacheprovider`, `docker compose config`, targeted source/doc inspection, and git status checks.
5. Created `orange_audit_closure_plan_2026-04-26.md` as the next-session closure plan; no code fixes were applied during the audit.

#### Audit evidence captured

- `python run_pipeline.py --help` succeeded and showed the current CLI for stages 1-11, preprocessing toggles, retraining flags, and advanced calibration options.
- `pytest --collect-only -q -p no:cacheprovider` collected **183 tests**. Full pytest was **not** run in this audit pass.
- `docker compose config` rendered the MLflow + inference services and confirmed model/config/log bind mounts for local compose execution.
- Latest inspected full artifact run `artifacts/20260423_233137` contains ingestion, validation, transformation, inference, evaluation, monitoring, trigger, and `run_info.json`.
- Canonical scaler file `data/prepared/scaler_train_only.json` records `fit_users: [1, 2, 3, 4]`, `val_users: [5]`, `test_users: [6]`, z-score normalization, and six sensor columns.

#### ORANGE reasons

- Runtime default model currently points to `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`, while several docs and thesis sections describe either a retrained default or an excluded pretrained artifact.
- Current branch has landed hardening paths, but the fix register still marks important parts as verification pending.
- Prometheus/Grafana/alerting were removed from the defended current evidence scope. They may remain as historical, optional, or future-work material only; active monitoring evidence comes from pipeline artifacts, trigger reports, logs, MLflow/DVC evidence, and saved run outputs.
- Docker health can pass without proving model-loaded inference because the image does not copy the model and compose relies on a mounted `models/` directory.
- API monitoring is lighter than pipeline Stage 6 monitoring and does not emit the full dominance/collapse signal set.
- Retraining governance is gated by default, but the complete healthy/warning/collapse/cooldown/no-labels/worse-model matrix still needs evidence.

#### Monitoring infrastructure scope decision

Prometheus, Grafana, and alert-rule files will **not** be treated as active evidence for the defended current implementation. The defended monitoring evidence will come from pipeline monitoring artifacts, trigger reports, logs, saved run outputs, MLflow/DVC evidence, and thesis-documented governance behavior.

#### Immediate P0 closure order

1. Decide the defended runtime model: exact `.keras` file, exact scaler file, and where it is stated.
2. Align README, original Ch4, April Ch4, Ch7, model-exclusion docs, and worklogs to that model decision.
3. Run fresh current-branch full pytest in the intended thesis environment.
4. Run pipeline stages 1-7 on a known session and save current artifacts.
5. Run API smoke with the defended model actually loaded.
6. Run Docker smoke with an actual inference request, not only a health check.
7. Remove Prometheus/Grafana/alerting from active thesis evidence claims or clearly mark them as historical/future-work.
8. Produce the retraining-governance decision matrix.

#### Files produced

- `orange_audit_closure_plan_2026-04-26.md` - paste-ready ORANGE closure plan with worklog/register blocks and P0 verification order.

#### Commit note

- This entry records the audit outcome and closure plan only. It does not mark the pipeline GREEN or close any verification-pending item.

---

### Current session status and 2026-04-24/25 pipeline hardening snapshot

#### Today in 5 lines
1. Current branch checked: `feature/api-two-file-upload`.
2. Current task: update this worklog so the dirty workspace shows what is done, what is active, and what still needs proof.
3. Done since the last top entry: pipeline diagnostics identified scaler leakage, pretrained/scaler mismatch, gravity/orientation bias, production shift, and user-split leakage risk.
4. Code hardening started: canonical train-only scaler loading, guarded scaler integrity checks, user-isolated windowing/user-holdout training, gravity-removal ablation, and chunked drift-monitor integration.
5. Still open: validation for the new code paths, A7 final config rationale, A4 retraining decision matrix, A5 Docker retraining proof, and final cleanup of the default-model vs pretrained-exclusion story.

#### Done / captured
- Simplified the submission weak-links register into a priority action board in `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md`.
- Added a next-work register in `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md` for scaler source of truth, train-only scaler fitting, user-grouped evaluation, pretrained fairness, gravity/orientation robustness, and window-boundary hygiene.
- Recorded the diagnostic root causes in `PIPELINE_DIAGNOSTIC_CHECKLIST.md`: all-users scaler leakage, non-grouped/random split reporting, pretrained model missing its matching scaler, production distribution shift, and orientation/gravity shortcut risk.
- Added model-governance documentation in `docs/MODEL_PROMOTION_POLICY.md`, `docs/pretrained_model_exclusion_report.md`, `docs/thesis_section_4x_pretrained_analysis.md`, and `docs/THESIS_CONSISTENCY_NOTES.md`.
- Added canonical scaler utilities in `src/utils/scaler.py` and a refit script in `scripts/refit_scaler_train_only.py` for `data/prepared/scaler_train_only.json`.
- Rewired runtime paths toward the canonical train-only scaler in `src/config.py`, `src/api/app.py`, `src/preprocess_data.py`, and `src/monitoring/baseline_builder.py`.
- Started user-holdout training/evaluation hardening in `src/train.py`, `scripts/evaluate_user_holdout.py`, `scripts/retrain_user_holdout.py`, and `scripts/retrain_user_holdout_fast.py`.
- Added drift-monitor work in `src/monitoring/drift_monitor.py`, `scripts/calibrate_drift_monitor.py`, and the chunked drift hook in `src/pipeline/production_pipeline.py`.
- Added gravity-removal ablation support in `src/components/data_transformation.py` and `scripts/test_gravity_removal.py`.
- Captured honest evaluation evidence in `reports/honest_evaluation.json`.

#### What I am doing now
- Updating `WORKLOG.md` to match the current workspace before more edits are made.
- Marking A5 as `IN_PROGRESS` because user-holdout retraining/evaluation code exists, while Docker reproducibility proof remains open.
- Keeping A7 as `IN_PROGRESS` because the diagnostic and ablation scaffolding exists, but the final defended baseline rationale is not closed.

#### Leftover and risk
- The current workspace is dirty and includes code, docs, scripts, model artifacts, and generated evidence; it needs a verification pass before commit.
- `models/retrained/best_model.keras` changed and must be checked before it is treated as a valid artifact.
- The model story needs one final wording pass: the pretrained model is now the configured default in several files, while `docs/pretrained_model_exclusion_report.md` excludes it from quantitative comparison. This can be defensible only if the distinction is explicit.
- New hardening code has not been verified in this session with pytest, API smoke, thesis build, or Docker smoke.

#### Writing impact
- Ch4/Ch7 need the pretrained-artifact diagnostic and the train-only/user-holdout evaluation caveat.
- Ch5/Ch6 need the canonical scaler and retraining-governance wording.
- Ch6 should treat drift/chunked monitor evidence as a governance signal, not automatic model promotion.

#### Next session start point
1. Run focused checks for scaler integrity, user-holdout evaluation, API upload, and drift monitor integration.
2. Decide the exact default-model wording: runtime default, excluded quantitative comparison, and candidate-promotion policy must not contradict each other.
3. Finish A7 by running or summarizing z-score vs no-normalization and gravity-removal evidence.
4. Build the A4 retraining decision matrix and then verify A5 through the Docker/retraining path.

---

## 2026-04-23

### Submission readiness verification closure
1. Verified A27/A28 remain recorded as DONE and that the Stage 6 runtime story is z-score drift with MMD retained as offline branch evidence.
2. Fixed the remaining appendix wording contradiction in `thesis/chapters/appendix_a_math.tex`: Stage 6 is now described as using the lightweight z-score drift signal, not MMD as the runtime retraining trigger.
3. Ran FastAPI operational smoke in the `thesis-mlops` conda environment. Localhost Uvicorn on `127.0.0.1:8017` returned HTTP `200` for `/docs`, `/api/health`, `/api/model/info`, and fused `POST /api/upload`; health reported `model_loaded=True` and `baseline_loaded=True`; upload produced `windows_created=1209` and `monitoring_overall=WARNING`.
4. Ran TestClient upload smoke for both supported upload modes. Fused CSV and raw accelerometer+gyroscope pair both returned HTTP `200`; the raw pair reported `upload_mode=accel_gyro_pair`.
5. Rechecked workflow scope. `.github/workflows/ci.yml` is the CI evidence for lint, unit tests, and inference-image build check. `.github/workflows/cd.yml` is optional tag/manual release-image build/push plus `/api/health` smoke validation, not production continuous deployment.
6. Quick thesis rebuild after the appendix wording fix completed successfully via `powershell -NoProfile -ExecutionPolicy Bypass -File thesis\build_thesis.ps1 -Quick`. `latexmk` hit a MiKTeX access-denied warning and the script fell back to `pdflatex`; `main.pdf` was produced at 92 pages and `main.log` showed no fatal LaTeX, undefined-citation, or undefined-reference warnings.
7. Evidence saved in `reports/api_operational_smoke_2026-04-23.md`. Remaining non-blocking packaging work: browser screenshots and Docker image smoke can still be captured if required by the final submission package.

---

## 2026-04-22

### FastAPI two-file upload and Docker size evidence
1. Created/continued `feature/api-two-file-upload` for the API upload-mode fix, separate from the stable submission branch.
2. Fixed the browser upload failure caused by submitting an accelerometer-only CSV to an endpoint that previously required one fused accel+gyro CSV.
3. `POST /api/upload` now accepts either a single fused CSV (`file`) or a raw pair (`accelerometer_file` + `gyroscope_file`), then reuses the existing ingestion merge/resample logic.
4. The API path now applies Garmin milliG-to-m/s2 conversion when needed and the retained model's z-score scaler from `models/retrained/scaler_config.json`.
5. Retraining remains governance-gated: labeled uploads are detected and marked as eligible metadata, but `/api/upload` still performs inference + monitoring only and does not mutate/register models.

**Evidence:** raw pair smoke with `data/raw/2025-07-16-21-46-56_accelerometer.csv` + `data/raw/2025-07-16-21-46-56_gyroscope.csv` returned `200`, `upload_mode=accel_gyro_pair`, `total_rows=121050`, `windows_created=1209`, `normalization_applied=True`, `monitoring_overall=WARNING`.

**Compatibility evidence:** fused CSV smoke with `data/processed/fused_2025_07_16_21_46_56_50Hz.csv` returned `200`, `upload_mode=fused_csv`, `total_rows=121050`, `windows_created=1209`, `normalization_applied=True`, `monitoring_overall=WARNING`.

**Tests:** new `tests/test_api_upload_modes.py` passed (`3 passed`); full regression outside the sandbox passed with `181 passed, 2 skipped, 1 warning`.

**Docker size finding:** `har-inference:phase2` is `4.5GB`; the largest layer is the pip dependency install at `3.3GB`, while `COPY src/` is only `31.9MB`. The size problem is dependency-layer dominated, not source-code dominated. Next Docker task: create a lightweight inference requirements file and remove training/dev dependencies from the inference image.

**Important runtime note:** the running Docker Desktop container must be rebuilt/restarted before the browser UI shows the new two-file upload controls; the TestClient evidence validates the code path in the working tree, not the old running image.

**Next session start point:** rebuild the inference container from `feature/api-two-file-upload`, verify `/docs`, `/api/health`, `/api/model/info`, and `/api/upload` in the browser, then start the lightweight inference-image cleanup.

---

### Thesis citation pass and bib expansion (2026-04-22)

#### Today in 5 lines
1. Four previously orphaned bib entries (`hammerla2016deep`, `shewhart1931economic`, `montgomery2009sqc`, `hendrycks2017baseline`) cited in contextually appropriate locations in `ch6_monitoring_drift_retraining.tex`.
2. `references.bib` expanded from 59 to 75 entries (+16 across two sessions), hitting the A17 low-end target.
3. Ch8 A35 tightened: new limitations bullet explicitly scopes Stage 6 thresholds as engineering operating points, and future-work item 4 now cross-references `sec:threshold_calibration_gap`.
4. Canonical label `knuckles_cracking` (plural) restored in `tests/test_post_inference_monitor.py` — aligned with `label_mapping.py` and `conftest.py`.
5. Full bibtex + two-pass pdflatex confirmed: 92 pages, zero undefined citation warnings.

#### Done today
- **A35 DONE**: Ch8 limitations bullet + future-work cross-reference to threshold calibration gap section
- **A17 milestone**: `references.bib` at 75 entries; 11 newly added entries still need `\cite{}` placement in `.tex` to appear in compiled bibliography
- **Label fix**: `knuckle_cracking` → `knuckles_cracking` in `tests/test_post_inference_monitor.py`
- **4 orphaned entries cited**: placed in ch6 in HAR accuracy discussion, threshold section, and calibration-limits context

#### Newly added bib entries (batch detail)

| Key | Paper | Why added |
|---|---|---|
| `alomar2024cnnrnn` | Alomar et al. 2024 — CNNs/RNNs/Transformers HAR survey | HAR model survey for ch2 |
| `khatun2022deepcnnlstm` | Khatun et al. 2022 — Deep CNN-LSTM self-attention HAR | Wrist sensor model for ch2 |
| `jain2024anxiety` | Jain & Kumar 2024 — ML anxiety detection via physiological signals | Anxiety detection for ch2 |
| `jacobson2021anxiety` | Jacobson et al. 2021 — Deep learning + wearable passive sensing for anxiety | Longitudinal wearable study ch2 |
| `duan2023multitask` | Duan et al. 2023 — Multi-task HAR and segmentation | Multi-task sensing ch2 |
| `saha2024accel` | Saha et al. 2024 — Decoding human activities from accel/gyro | Wearable signal decoding ch2 |
| `tsai2022panic` | Tsai et al. 2022 — Panic attack prediction via wearables | Mental health wearables ch2 |
| `cuperman2022football` | Cuperman et al. 2022 — End-to-end DL pipeline for football HAR | Domain-specific HAR pipeline ch5 |
| `diazramos2023wearable` | Diaz-Ramos et al. 2023 — Wearable + speech for mental disorder detection | Mental health wearable ch2 |
| `xu2025llmimu` | Xu et al. 2025 — LLM capabilities for IMU-based HAR | Future work / LLM+HAR ch8 |
| `ng2019sensor` | Ng et al. 2019 — Clinician perspectives on patient-generated sensor data | Deployment + governance ch6 |
| `sadhu2023careportal` | Sadhu et al. 2023 — CarePortal clinician wearable dashboard | Clinical wearable deployment ch8 |
| `zhang2025sensorlm` | Zhang et al. 2025 — SensorLM foundation model for wearables | Foundation model future work ch8 |
| `lecun2015deep` | LeCun/Bengio/Hinton 2015 — Deep Learning (Nature) | Deep learning foundation ch2 |
| `paszke2019pytorch` | Paszke et al. 2019 — PyTorch NeurIPS | Implementation framework ch4/ch5 |
| `reiss2012pamap` | Reiss & Stricker 2012 — PAMAP2 benchmark dataset | HAR benchmarks context ch2 |

#### Leftover and risk
- **28 bib entries are uncited orphans** — in `references.bib` but not `\cited{}` anywhere; they do NOT appear in the compiled PDF bibliography. Full list and placement targets below.
- A33 (per-session table ch7) and A34 (participant table ch4) remain open — need raw data.

#### Writing impact
- Ch6 now has explicit threshold-source citations at the engineering-vs-statistical-limits distinction.
- Ch8 limitations and future work sections both explicitly name the threshold calibration gap with cross-references, so examiner questions on "how did you choose these thresholds?" are handled.

#### Compiled bibliography status (verified 2026-04-22)
- **PDF bibliography**: 47 entries (all correctly compiled from `\cite{}` calls in `.tex` files)
- **Bib file total**: 75 entries
- **Uncited orphans** (28 entries — need `\cite{}` placement to appear in PDF):

| Key | Paper | Target chapter |
|---|---|---|
| `alomar2024cnnrnn` | CNNs/RNNs/Transformers HAR survey | ch2 related work |
| `cdfoundation2020mlops` | CD Foundation MLOps definition | ch2 MLOps background |
| `corbin2023deployr` | DeployR production deployment | ch5 or ch8 |
| `cuperman2022football` | End-to-end DL pipeline for sport HAR | ch2 or ch5 |
| `diazramos2023wearable` | Wearable+speech for mental disorder detection | ch2 |
| `duan2023multitask` | Multi-task HAR and segmentation | ch2 |
| `gama2014survey` | Concept drift adaptation survey | ch6 drift section |
| `jacobson2021anxiety` | Deep learning + wearable passive sensing for anxiety | ch2 |
| `jain2024anxiety` | ML anxiety detection via physiological signals | ch2 |
| `khatun2022deepcnnlstm` | Deep CNN-LSTM self-attention HAR | ch2 or ch4 |
| `kingma2014adam` | Adam optimizer | ch4 model/training |
| `kuprieiev2023dvc` | DVC documentation | ch5 pipeline |
| `lecun2015deep` | LeCun/Bengio/Hinton Deep Learning (Nature) | ch2 deep learning background |
| `mark2021batch` | Batch monitoring | ch6 monitoring |
| `ng2019sensor` | Clinician perspectives on patient sensor data | ch8 future work |
| `oleh2024harreview` | HAR review 2024 | ch2 |
| `page1954cusum` | CUSUM control chart | ch6 drift section |
| `paszke2019pytorch` | PyTorch | ch4 implementation |
| `reiss2012pamap` | PAMAP2 benchmark dataset | ch2 datasets |
| `sadhu2023careportal` | CarePortal clinician wearable dashboard | ch8 future work |
| `saha2024accel` | Decoding human activities from accel/gyro | ch2 |
| `shankar2022operationalizing` | Operationalizing ML | ch2 or ch5 |
| `sugiyama2012nonstationary` | Non-stationary environments (book) | ch6 drift section |
| `tsai2022panic` | Panic attack prediction via wearables | ch2 |
| `webb2016characterizing` | Characterizing concept drift | ch6 drift section |
| `xu2025llmimu` | LLMs for IMU-based HAR | ch8 future work |
| `zenisek2019drift` | Drift detection in industrial settings | ch6 drift section |
| `zhang2025sensorlm` | SensorLM foundation model for wearables | ch8 future work |

**Quick-win placement (ch6 drift section, one sentence each):** `gama2014survey`, `webb2016characterizing`, `zenisek2019drift`, `page1954cusum`, `sugiyama2012nonstationary`, `mark2021batch` — all belong near the threshold calibration gap discussion already in ch6. Placing these 6 would bring compiled bibliography to 53.

**ch8 future work placements:** `ng2019sensor`, `sadhu2023careportal`, `xu2025llmimu`, `zhang2025sensorlm` — fit naturally into the cloud/multi-user and foundation-model future-work paragraphs already written.

#### Next session start point
Citation placement pass: (1) ch6 drift section — place 6 quick-win entries; (2) ch8 future work — place 4 entries; (3) ch2 — HAR survey/model/dataset entries; (4) ch4 — PyTorch, Adam, PAMAP2. Then rebuild and verify compiled count ≥ 60. Then address A33/A34 data tables.

---
## 2026-04-21

### A27/A28 threshold alignment
1. Stage 6 monitoring thresholds now match the thesis calibration story: confidence warn `0.70`, uncertain windows `20%`, transition rate `35%`, and drift z-score `1.8`.
2. Dominant-class collapse is now emitted directly by Stage 6 with `85%` warning and `95%` critical thresholds.
3. Stage 7 keeps its citation-backed trigger thresholds (`0.65` confidence warn, `2.0/3.0` drift z-score) so monitoring warns before retraining escalation.
4. The old `psi` drift payload name now has a `drift_zscore` replacement with `psi` retained as a compatibility alias.
5. `thesis/reference/THRESHOLD_CITATIONS.md` and `thesis/references.bib` were refreshed so code, thesis wording, and bibliography keys align.

**Verification:** full regression passed after the Stage 6/7 wiring fix: `178 passed, 2 skipped, 1 warning` via `C:\Users\shali\anaconda3\envs\thesis-mlops\python.exe -m pytest tests/ -q --tb=short`.

**CLI smoke:** `run_pipeline.py --help` succeeded and was saved to `reports/post_a27_a28_cli.txt`.

**Important integration note:** Stage 7 now consumes the new Stage 6 dominance fields directly when no older Stage 5 `collapse_signals` payload is present. This prevents a Stage 6 `dominance_warning=True` report from being lost before trigger evaluation.

**Residual housekeeping:** temporary pytest folders created during sandboxed verification still have Windows access-denied permissions (`tmp_run3`, `reports/tmp`, `reports/pytest-tmp`). They are generated artifacts only; they are not part of the code changes.

### Submission consistency pass
1. Created/continued the final consistency branch `submission/final-consistency-pass` from `epic/apr-foundation-baseline`.
2. Historical note for that pass: the defended model path at that time was `models/retrained/har_model_20260327_223917.keras`.
3. Current policy supersedes that historical default: `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` is the repository default, and retrained models are candidate artifacts promoted only after labeled comparison shows improvement.
4. Aligned API and workflow wording: FastAPI upload path is `POST /api/upload`; workflow evidence is CI plus optional release-image smoke, not production CD.
5. Confirmed final runtime drift story: Stage 6 default is `zscore_mean_shift`; MMD remains calibrated experimental/offline audit evidence.

**Verification:** final regression after the consistency pass passed with `178 passed, 2 skipped, 1 warning`; `python run_pipeline.py --help` succeeded after ASCII-safe CLI help cleanup; thesis build completed and produced `thesis/main.pdf` at 92 pages.

---
## 2026-04-20

### Today in 5 lines
1. Full codebase audit session: explored all 51 src modules, 23 scripts, 25 test files, 2 Dockerfiles, and CI/CD workflows.
2. 26-session production experiment data located in `outputs/experiments/unit_fix_abstain_26runs_20260329_205008/`; 6 comparison charts generated and saved to `outputs/charts_26runs/`.
3. Threshold gap identified: the monitoring stack has no class-collapse guard — a model that's confidently wrong (all hand_tapping, 0% review) passes all current warning thresholds undetected.
4. Scripts audit completed: 9 legacy scripts confirmed superseded by `src/`; no `src/` file imports from `scripts/`.
5. New tasks A26–A35 added to master backlog covering charts, threshold hardening, Docker cleanup, legacy script archival, and thesis insertions.

**Done today:** codebase audit, 26-run chart generation (A26 DONE), and backlog population for all identified gaps.
**Leftover/risk:** Thresholds (A27, A28) are still loose — class collapse currently goes undetected on unlabeled production sessions. This is a thesis-writing risk if reviewers notice.
**Writing impact:** A31, A32, A33, A35 are new thesis tasks that can be executed quickly since the charts and analysis are already done; Ch7 gets a new figure, Ch6 gets a new subsection.
**Next session start point:** execute A31 (insert chart6_dashboard.png into Ch7) + A27 (add dominant_class threshold to config_entity.py) — both are concrete, fast, and highest-return for today.

---

### Later update (2026-04-20, repo-state sync)

### Later in 5 lines
1. The master backlog was resynchronized against live repository evidence rather than against the earlier top-line note alone.
2. Repo-wide checks confirmed additional progress already present on disk: threshold-justification drafts, thesis figure-pack mapping docs, a 76-paper literature longlist, and a current thesis build at 89 pages.
3. Ch8 now clearly contains the class-collapse future-work item, but the explicit training-versus-production threshold-calibration-gap wording is still only partially reflected, so A35 remains in progress rather than done.
4. Ch7 still does not contain the literal per-session table promised by A33, and Ch4 still does not contain the participant table promised by A34.
5. The highest-return next action remains A27/A28 because the monitoring defaults in code still lag behind the collapse-risk story now defended in the thesis text.

**Done later today:** updated the master backlog so A12, A13, A17, and A18 are no longer misrepresented as untouched, kept A7 active, and marked A35 as partially completed rather than closed.
**Leftover/risk:** the strongest remaining repo-level gap is still threshold alignment: Stage 7 has collapse-guard behavior, but Stage 6/config defaults still reflect older loose thresholds.
**Writing impact:** the worklog now better reflects actual repo maturity — figure-pack work, literature tracking, and page-count progress are visible as active rather than hidden.
**Next session start point:** implement A27/A28 in `src/entity/config_entity.py` and `src/monitoring/post_inference_monitor.py`, then refresh the threshold-citation docs to match the new defaults.

---

### Final update (2026-04-20, work-note review)

### Final in 5 lines
1. Reviewed `WORK_2026-04-21.md` as the main repo/thesis audit note prepared for the next session.
2. The core audit content is strong: the A27/A28 threshold gap, AdaBN/TENT framing, OOD future-work boundary, and pre-refactor safety risks are all clearly argued and evidence-based.
3. The file itself is not yet a clean final document: it contains duplicate audit sections, raw `Bash / IN / OUT` transcript blocks, and pasted prompt/task text mixed into the report.
4. This means the work file currently functions well as an internal scratchpad, but not yet as a polished repo-facing audit record.
5. The highest-value cleanup later is document hygiene, not new analysis: keep the first coherent audit block plus the addendum, remove the transcript dump, and leave only the reviewer-useful sections.

**Done later today:** confirmed that the audit logic is worth keeping, but also documented that `WORK_2026-04-21.md` needs trimming before it should be treated as a finished review artifact.
**Leftover/risk:** if the file is left as-is, the repo will contain a large mixed transcript that is harder to trust, search, and reuse than a clean audit note.
**Writing impact:** tomorrow's work can start from the current audit findings without redoing the analysis, but the note should be cleaned before it is used as formal project documentation.
**Next session start point:** either implement A27/A28 directly from the existing plan, or spend a short pass cleaning `WORK_2026-04-21.md` into a proper final audit file before further thesis-facing reuse.

---
## 2026-04-19

### Today in 5 lines
1. Thesis benchmark review was converted into an execution checklist that can drive the remaining writing wave.
2. Priority order was fixed by grading return: Chapter 2 first, then Chapter 7, then Chapter 4 evidence framing, bibliography growth, metadata cleanup, and only then Chapter 5/6 polish.
3. A new checklist document was added at `thesis/THESIS_EXECUTION_CHECKLIST_2026-04-19.md`.
4. The checklist explicitly treats the MLOps lifecycle paper as a core citation pillar and the LLMOps paper as peripheral only.
5. The next writing sessions now have concrete stop conditions instead of general intentions.

**Done today:** converted review into a chapter-by-chapter execution checklist with Chapter 2 and Chapter 7 as the first active work blocks.
**Leftover/risk:** No chapter text was expanded yet. Main academic risk remains unchanged until Chapter 2 and Chapter 7 are actually rewritten.
**Writing impact:** thesis work is now sequenced by grade impact rather than by convenience. This should prevent time loss on low-return polish.
**Next session start point:** open `thesis/THESIS_EXECUTION_CHECKLIST_2026-04-19.md` and execute the Chapter 2 rewrite block first.

---

### Later update (2026-04-19, writing execution completed)

### Later in 5 lines
1. The thesis writing audit and post-fix wave were executed end-to-end across core chapters and bibliography.
2. `THESIS_WRITING_AUDIT.md` and `THESIS_WRITING_POST_FIX_REPORT.md` were produced as evidence logs for what was changed and why.
3. Chapter files `ch1`, `ch3`, `ch4`, `ch5`, `ch6`, `ch7`, and `ch8` plus `references.bib` were expanded and aligned.
4. Current bibliography now contains 47 BibTeX entries and the latest LaTeX build log reports `main.pdf` at 107 pages.
5. Thesis handbook/dashboard tracking is synchronized with this writing wave so status does not lag behind the manuscript.

**Done later today:** completed a major writing-and-citation expansion pass, including methods framing, evaluation strengthening, discussion/conclusion growth, and bibliography broadening.
**Leftover/risk:** Chapter 2 synthesis depth and final evidence-polish still require focused quality review before submission freeze.
**Writing impact:** manuscript maturity moved from planning-heavy to draft-complete structure with stronger citation grounding and explicit limitations.
**Next session start point:** execute a Chapter 2 critical-synthesis pass, then run final consistency and citation hygiene checks before submission packaging.

---

### Final update (2026-04-19, dashboard and defense metadata sync)

### Final in 5 lines
1. Thesis title-page examiner metadata was finalized from the seq2seq report reference and updated in `thesis/main.tex`.
2. `main.pdf` open issue was validated as a filename/output-location mismatch and resolved via clean rebuild.
3. Thesis handbook defense dashboard was synchronized again for today, and version banner advanced to `v6 - 19 April 2026`.
4. Dashboard metric generation logic was corrected to parse MiKTeX logs that emit quoted full PDF paths.
5. Defense dashboard status is now explicitly marked `OK` for this date.

**Done final today:** finalized defense-facing metadata and synchronized dashboard/worklog status for end-of-day closure.
**Leftover/risk:** only normal final-proofreading and institution-side plagiarism submission remain outside repo automation.
**Writing impact:** defense narrative assets and manuscript metadata are now aligned, reducing mismatch risk during submission and oral prep.
**Next session start point:** open `thesis/main.pdf`, run one final visual title-page check, then continue with defense slide mapping.

---

## 2026-04-18

### Today in 5 lines
1. External review (12 findings: 2 High, 5 Medium, 5 Low) cross-checked against live code — all 12 confirmed.
2. All 12 fixes applied across `production_pipeline.py`, `run_pipeline.py`, `artifact_entity.py`, `data_ingestion.py`, `WORKLOG.md`, and new `src/utils/label_detection.py`.
3. Targeted regression tests written (`tests/test_fix_regression.py`, 6 new tests for FIX-1 and FIX-2).
4. Full test suite run: **167 passed, 2 skipped, 0 failed** — no regressions.
5. Bug log updated in both `internal/notes/bug_april.md` and `thesis/notes/bug_april.md`.

**Done today:** full pipeline hardening pass — all reviewed findings fixed and verified.
**Leftover/risk:** None from this session. Test gap noted: `test_validation_gate.py` asserts exception raises but not cleanup — new tests in `test_fix_regression.py` cover this now.
**Writing impact:** A14 (debug and harden major code paths) progressed. Audit trail in bug_april.md is thesis-ready evidence for observability and resilience claims.
**Next session start point:** A7 config sweep continuation; investigate the 1 failed batch row from 2026-04-17.

---

### Fixes Applied (2026-04-18)

#### FIX-1 — Validation hard-stop drops cleanup (HIGH) ✓
- **File:** `src/pipeline/production_pipeline.py`
- **Change:** Stage loop wrapped in `try/finally`. `finalize()`, `_save_result()`, `_end_mlflow()` now always run even when `DataValidationError` is raised.
- **Verified:** `test_fix_regression.py::TestFix1ValidationCleanup` (3 tests, all pass).

#### FIX-2 — Stage 8 BREAK aborts calibration (HIGH) ✓
- **File:** `src/pipeline/production_pipeline.py`
- **Change:** Both `return "BREAK"` in `_run_retraining` changed to `return "SKIP"`. Loop continues to Stage 11. Main loop now also records `result.stages_skipped` for any stage returning SKIP.
- **Verified:** `test_fix_regression.py::TestFix2RetrainGateSkipNotBreak` (3 tests, all pass).

#### FIX-3 — `--config` misleading scope (MEDIUM) ✓
- **File:** `run_pipeline.py`
- **Change:** `--config` help text updated to state it only applies to preprocessing settings; monitoring/trigger use `pipeline_overrides.yaml` or `$HAR_PIPELINE_OVERRIDES`.

#### FIX-4 — Hardcoded drift cutoffs in summary (MEDIUM) ✓
- **File:** `run_pipeline.py`
- **Change:** `_print_compact_run_summary` and `_print_pipeline_summary` now read drift status from the monitoring artifact (`HEALTHY`/`WARNING`/`CRITICAL`) instead of hardcoded 0.75/1.50 z-score thresholds.

#### FIX-5 — MLflow always claims "run logged" (MEDIUM) ✓
- **Files:** `src/entity/artifact_entity.py`, `src/pipeline/production_pipeline.py`, `run_pipeline.py`
- **Change:** `mlflow_tracked: bool = False` added to `PipelineResult`. Set to `True` after successful `_init_mlflow`. Compact summary reflects actual state.

#### FIX-6 — Fallback artifact loses `production_y_path` (MEDIUM) ✓
- **File:** `src/pipeline/production_pipeline.py`
- **Change:** `_make_fallback_transformation_artifact` now checks for `production_y.npy` in `data/prepared/` and sets `production_y_path` if it exists.

#### FIX-7 — Stage 11 outputs not persisted (MEDIUM) ✓
- **File:** `src/pipeline/production_pipeline.py`
- **Change:** `_run_calibration` now saves `temperature.json`, `calibration_report.json`, `calibrated_probabilities.npy` via `ArtifactsManager.save_file()`. Status in `log_stage_completion` now reflects `art.overall_status` instead of hardcoded `"SUCCESS"`.

#### FIX-8 — TF version string compare (LOW) ✓
- **File:** `run_pipeline.py`
- **Change:** `tf_ver >= "2.11"` replaced with integer `(major, minor)` tuple comparison — correctly handles versions like 2.9, 2.10.

#### FIX-9 — Duplicate label constants (LOW) ✓
- **Files:** `src/components/data_ingestion.py`, `src/pipeline/production_pipeline.py`, new `src/utils/label_detection.py`
- **Change:** `LABEL_COLUMN_CANDIDATES` and `NON_GROUND_TRUTH_COLUMNS` moved to single source in `src/utils/label_detection.py`; both files import from there.

#### FIX-10 — Startup UX before parse_args (LOW) ✓
- **File:** `run_pipeline.py`
- **Change:** `parse_args()` moved to top of `main()` before banner print and `_detect_gpu()`. `--help` and bad CLI invocations no longer pay TF startup cost.

#### FIX-11 — Worklog legend missing REMOVED/ACTIVE (LOW) ✓
- **File:** `WORKLOG.md`
- **Change:** `REMOVED` and `ACTIVE` added to Status Legend with definitions.

#### FIX-12 — Worklog 2026-04-17 format violation (LOW) ✓
- **File:** `WORKLOG.md`
- **Change:** Compact scan block prepended to 2026-04-17 section per the format rule established 2026-04-16.

---

### Test Run Results (2026-04-18)

```text
pytest tests/ -v
167 passed, 2 skipped, 0 failed  (18.48s)
2 skips: prometheus_client not installed (pre-existing, unrelated)
1 warning: sklearn feature names (pre-existing, unrelated)
```

New tests added: `tests/test_fix_regression.py` - 6 targeted regression tests for FIX-1 and FIX-2.

---

### Additional Thesis Writing And Figure-Pack Work (2026-04-18, later)

### Later in 5 lines
1. Built `THESIS_JOURNEY_tillapril.md` as a full evidence-led thesis journey memo covering scope, architecture, experiments, readiness, and bottom-line assessment.
2. Rewrote `thesis/chapters/ch1_introduction.tex` into thesis-ready prose with motivation, problem statement, objectives, questions, contributions, scope boundary, and chapter structure.
3. Created a reproducible thesis-support figure pack under `thesis/figures/thesis_journey/` with 14 SVG figures plus generator and support docs.
4. Inserted the generated figures back into `THESIS_JOURNEY_tillapril.md` at the matching sections with short captions.
5. Added figure-pack metadata docs: `FIGURE_INDEX.md`, `CAPTIONS_AND_INSERTION_GUIDE.md`, and `README.md`.

**Done later today:** thesis documentation and packaging wave for supervision, defense prep, and manuscript conversion.
**Visible work count:** 4 major workstreams, and at least 20 thesis-facing artifacts added or substantially updated in the current workspace:
- 1 evidence memo: `THESIS_JOURNEY_tillapril.md`
- 1 chapter rewrite: `thesis/chapters/ch1_introduction.tex`
- 18 figure-pack files in `thesis/figures/thesis_journey/`:
  - 14 SVG figures
  - 1 reproducible generator script
  - 3 support docs (`README.md`, `FIGURE_INDEX.md`, `CAPTIONS_AND_INSERTION_GUIDE.md`)

**Writing impact:** the repo now has a thesis-support dossier, a stronger Chapter 1, and a reusable figure pack for both the support memo and later thesis-body extraction.
**Verification note:** the figure generator rendered successfully using `C:\Program Files\Python311\python.exe` because the default `python` in the shell did not have `matplotlib` installed.
**Leftover/risk:** figures are linked into the Markdown memo, but thesis-PDF insertion and any width tuning for final manuscript layout are still open.
**Next session start point:** convert the strongest evidence sections into thesis chapters in order: Section 2, Section 5, Section 7, then Section 14.

---

## 2026-04-17

### Today in 5 lines
1. Full batch rerun for CR26 raw sessions + 2 synthetic datasets completed.
2. Consolidated output in `reports/pipeline_runs/batch_28_full/` — 27 success / 1 failure (28 total).
3. Synthetic training metrics appended to consolidated table and plotted.
4. Summary regenerated with training metrics and new synthetic training chart.
5. Late-night: evidence finalized, no open blockers for next session.

**Done today:** batch rerun, consolidated output, synthetic metrics table + chart.
**Leftover/risk:** 1 failure in batch run not yet root-caused.
**Writing impact:** A2/A3 evidence strengthened; batch evidence now in one location.
**Next session start point:** Investigate the 1 failed batch row; continue A7 config sweep.

---

### Late-night addendum (batch rerun + consolidated evidence)

#### End-of-day snapshot (for tomorrow)

1. Ran full batch rerun for CR26 raw sessions + 2 synthetic datasets using `scripts/run_batch_raw_and_synthetic.py`.
2. Consolidated output was finalized in one location: `reports/pipeline_runs/batch_28_full/`.
3. Final batch status after rerun: **27 success / 1 failure** (total rows = 28).
4. Synthetic training metrics were appended to the same consolidated table and plotted.
5. Summary was regenerated to include training metrics and the new synthetic training chart.

#### Re-check performed tonight (verification pass)

| Check | Verified value |
|---|---|
| Consolidated rows | 28 |
| Successful runs | 27 |
| Failed runs | 1 |
| Failed dataset | `2025-08-13-04-18-52` |
| Synthetic eval accuracy (codex) | 0.704050 |
| Synthetic eval accuracy (other) | 0.696521 |
| Synthetic train final accuracy (codex) | 0.896373 |
| Synthetic train final accuracy (other) | 0.901554 |

#### Important artifacts (open these first tomorrow)

- `reports/pipeline_runs/batch_28_full/SUMMARY.md`
- `reports/pipeline_runs/batch_28_full/all_runs_metrics.csv`
- `reports/pipeline_runs/batch_28_full/all_runs_metrics.json`
- `reports/pipeline_runs/batch_28_full/charts/mean_confidence_by_dataset.png`
- `reports/pipeline_runs/batch_28_full/charts/drift_vs_uncertain_scatter.png`
- `reports/pipeline_runs/batch_28_full/charts/dominant_pct_by_dataset.png`
- `reports/pipeline_runs/batch_28_full/charts/synthetic_eval_accuracy.png`
- `reports/pipeline_runs/batch_28_full/charts/synthetic_training_accuracy.png`

#### Failure note (captured for thesis evidence)

- Session `2025-08-13-04-18-52` failed ingestion.
- Root cause confirmed: accelerometer source is binary-corrupted (all null bytes), so no recoverable rows.
- Decision for current batch evidence: keep as one failed run in the consolidated report (do not force-repair inside this run).

#### Tomorrow quick-start checklist

1. Read `reports/pipeline_runs/batch_28_full/SUMMARY.md` completely first (2-3 minutes).
2. Review synthetic section in `all_runs_metrics.csv` and confirm eval vs train gap interpretation.
3. Decide whether failed-session handling is thesis text only (recommended) or needs separate recovery attempt.
4. If continuing analysis, derive threshold update candidates from confidence/uncertainty/drift columns.

### Today in 5 lines

1. Completed all 5 refactoring batches (A → E) + `src/monitoring/` migration + BUG-3 re-fix + Excel ingestion support.
2. Stages 12-14 deleted from runtime; `PostInferenceMonitor` + `BaselineBuilder` moved from `scripts/` into `src/monitoring/`.
3. BUG-3 regressed during Batch A (DEFAULT_MODEL_PATH set to wrong model) — re-fixed to `har_model_20260327_223917.keras`, validated 70.4% accuracy.
4. A15 DONE — full dataflow map created at `docs/thesis/DATAFLOW_MAP_A15.md`.
5. Dashboard updated with stage-wise file paths, run commands, and 11-stage architecture.

### Done today

| Item | Detail |
|---|---|
| Batch A — Safety | Status vocabulary unified (HEALTHY/WARNING/CRITICAL), DEFAULT_MODEL_PATH single source of truth, unified run_id |
| Batch B — Correctness | ctx dict for cross-stage artifact passing, label detection wired correctly |
| Batch C — Maintainability | `run()` decomposed into `_run_ingestion` … `_run_calibration` helpers; BREAK/SKIP sentinel pattern |
| Batch D — Hygiene | `get_timestamp()` centralized, PROJECT_ROOT canonicalized, JSON serializer extracted, deprecated wrappers hard-fail |
| Batch E — Scope cleanup | S12-S14 deleted: 6 runtime modules + 3 test files + config/artifact classes + CLI flags removed |
| `src/monitoring/` package | `PostInferenceMonitor` + `BaselineBuilder` moved from `scripts/` → `src/monitoring/`; scripts converted to thin wrappers; `deployment_manager.py` stale refs fixed |
| BUG-3 re-fix | `DEFAULT_MODEL_PATH` corrected back to `har_model_20260327_223917.keras`; validated 70.4% acc / 71.1% F1 on Codex synthetic |
| Ingestion Excel support | `_ingest_csv` now auto-detects `.xlsx`/`.xls` and calls `pd.read_excel()` — single Excel file accepted via `--input-csv` |
| Python File Importance Audit | `reports/repo_audit/PYTHON_FILE_IMPORTANCE_AND_CLEANUP_2026-04-17.md` reviewed; S6/S10 scripts→src migration confirmed as top priority (now done) |
| A15 DONE | `docs/thesis/DATAFLOW_MAP_A15.md` — S1-S11 input/output map, branching logic, file location table, CLI reference, thesis chapter mapping |
| handbook-dashboard | Stage file paths added, 11-stage architecture, run commands card added |

### Leftover and risk

- Resolved later in Stage 5 refactor: label/prediction length mismatch is now a hard error in
  `src/components/model_evaluation.py`; the old evaluation script was removed.
- A7 (config sweep matrix) still IN_PROGRESS — 4 preprocessing configs not yet systematically compared
- `scripts/` archive candidates (16 files) not yet moved — safe to leave, none are runtime-imported

### Writing impact

- Ch4.2 + Ch5.2: `DATAFLOW_MAP_A15.md` is the direct evidence — every file path and branching decision is documented
- Ch5.2.1: component + src two-file pattern explained; src/monitoring canonical location confirmed
- Ch5.3.2: BUG-3 re-fix with evidence — wrong model caused class collapse (hand_tapping 71.6%), correct model gives healthy distribution (8.7%)
- Ch9.2: S12-S14 as future work is now concrete — deleted with rationale, not just deferred

### Next session start point

A4 — retraining decision matrix (run pipeline with RETRAIN trigger firing vs not firing, document decision matrix for Ch6.3).
Evidence pointer: `docs/thesis/DATAFLOW_MAP_A15.md` for dataflow, `REFACTOR_ISSUES.md` for refactor audit trail.

---

### Refactoring evidence (full detail)

**Files deleted (Batch E — S12-S14 scope removal):**

| File | Reason |
|---|---|
| `src/wasserstein_drift.py` | Stage 12 not in scope |
| `src/components/wasserstein_drift.py` | Stage 12 not in scope |
| `src/components/curriculum_pseudo_labeling.py` | Stage 13 not in scope |
| `src/components/sensor_placement.py` | Stage 14 not in scope |
| `src/sensor_placement.py` | Stage 14 not in scope |
| `src/curriculum_pseudo_labeling.py` | Stage 13 not in scope |
| `tests/test_wasserstein_drift.py` | Test for deleted module |
| `tests/test_sensor_placement.py` | Test for deleted module |
| `tests/test_curriculum_pseudo_labeling.py` | Test for deleted module |

**Files modified (all batches combined):**

| File | Change |
|---|---|
| `src/pipeline/production_pipeline.py` | Complete rewrite: 11-stage dispatch dict, `_run_<stage>()` helpers, ctx dict, BREAK/SKIP sentinels |
| `src/entity/config_entity.py` | Removed WassersteinDriftConfig, CurriculumPseudoLabelingConfig, SensorPlacementConfig |
| `src/entity/artifact_entity.py` | Removed S12-S14 artifact classes and PipelineResult fields |
| `src/trigger_policy.py` | Removed wasserstein_warn/critical dead fields; fixed docstring |
| `run_pipeline.py` | Removed S12-S14 CLI flags/imports; fixed F541 empty f-strings; fixed PASS/WARN/ALERT → HEALTHY/WARNING/CRITICAL |
| `tests/test_pipeline_integration.py` | Updated ALL_STAGES assertions: len=11, last="calibration" |
| `scripts/mlops_audit.py` | Removed dead reference to `src/wasserstein_drift.py` |
| `scripts/preprocess.py` | Hard-fail sys.exit(1) with migration message |
| `scripts/train.py` | Hard-fail sys.exit(1) with migration message |
| `src/utils/common.py` | Added `get_timestamp()` helper |
| `REFACTOR_ISSUES.md` | All 21 issues marked Done; pipeline impact section added |

---
## 2026-04-16

### What happened today (plain summary)

A full day of pipeline debugging, synthetic data validation, dashboard work, and repo cleanup. By end of day the pipeline was correctly wired and producing meaningful numbers for the first time. Branch was merged and GitHub cleaned up.

---

### Tasks completed (A2 DONE, A3 DONE)

| Task | Result |
|---|---|
| A2 — Validate synthetic data end-to-end | Done. 3 datasets ran through the full 7-stage pipeline. Final validated numbers locked. |
| A3 — Evaluate confidence behavior | Done. Confidence and drift signals correctly track accuracy degradation across datasets. |
| A14 — Harden pipeline code | In progress. 4 bugs fixed today. |

---

### Pipeline bugs fixed

Four issues were found and fixed in the pipeline code. All are in `src/`:

**BUG-1 — Stage 1 cache not reported correctly.**
When the pipeline reused an already-processed file, it did not log this. Fixed so run logs now show clearly when a cached file was reused vs freshly processed.

**BUG-2 — Stage 5 ignored labels even when they existed (thesis-critical).**
The pipeline had all the pieces in place to compute accuracy, F1, and confusion matrix when labeled data was given — but three small wiring mistakes meant it always ran in unlabeled mode and returned `None` for all metrics. Fixed by connecting the label file path from Stage 3 through to Stage 5 properly. This was the main blocker for Chapter 7 evidence.

**BUG-3 — Wrong model was loaded (critical).**
The pipeline was defaulting to `fine_tuned_model_1dcnnbilstm.keras`, a May 2025 model that was fine-tuned on heavily hand-tapping dominated unlabeled data. This model predicted `hand_tapping` 68–72% of the time for any input. The symptom was pipeline accuracy of 14.5% on the training data itself — which should have been ≥90%. Fixed by changing the default to `har_model_20260327_223917.keras` (92.2% test accuracy, trained March 2026 on balanced labeled data). All numbers produced before this fix are invalid and were discarded.

**DESIGN-1 — Fragile error-handling pattern in pipeline loop.**
The pipeline used a confusing `goto_cleanup` flag to stop stage execution on error. This could silently fail to actually stop. Replaced with a clean `break` statement. No change in behavior, but the code is now reliable and obvious.

**BUG-3 also existed in the Docker API layer** (`src/api/app.py`) — the FastAPI inference server had the same wrong model hardcoded and did not read the `MODEL_PATH` environment variable. Fixed in the same session after a Docker config review.

---

### Key thesis finding — hand-tapping dominance and label shift

The wrong model (BUG-3) is not just a code bug — it is a real-world example of exactly what the thesis argues against.

The model was fine-tuned on production Garmin data without any class-balance check. Wrist sensor data from real daily use is dominated by hand-tapping motion (typing, phone use, surface tapping). The model silently adapted to this distribution. Even more dangerous: the monitoring layer reported confidence of 85% the whole time — high confidence in wrong predictions. Drift signals alone did not catch it either.

This validates the thesis argument for multi-signal monitoring (confidence + drift + class distribution together) and governed retraining with class-balance enforcement. BUG-3 is now documented as the concrete evidence for Chapters 6 and 7.

---

### Synthetic data comparison — final validated numbers

Three datasets were run through the full pipeline with the correct model:

| Dataset | Accuracy | F1 | Confidence | Uncertain | Drift |
|---|---:|---:|---:|---:|---:|
| Actual labeled (real Garmin) | 98.9% | 98.9% | 98.6% | 0.2% | 0.000 |
| Synth Codex (AI-generated, correct distribution) | 70.4% | 71.1% | 86.8% | 6.5% | 0.001 |
| Synth Cloud v2 (AI-generated, fixed distribution) | 69.7% | 70.5% | 83.1% | 5.9% | 0.028 |

Run IDs: `20260416_143710` / `20260416_144428` / `20260416_151805`

The two synthetic datasets both land near 70% — a consistent ~29 percentage point gap from the real labeled data. This is the clean domain shift evidence for Chapter 7. The confidence and drift signals correctly track the degradation as distribution moves further from training.

**Synth Cloud v2 note:** The original "Synth Other" file had a 4× gyroscope amplitude error (Gx std was 11.9 instead of the correct 49.9). This caused the original 34.6% result which was an artifact of wrong data, not real distribution shift. Regenerated using the same statistical method as Synth Codex with a different seed and a small ±10% per-channel variation. New data matches training distribution correctly.

---

### Notebook created

`notebooks/synthetic_comparison/synthetic_comparison.ipynb` — a clean 24-cell notebook that walks through:

1. Load all three datasets
2. Check physical units (accelerometer m/s², gyroscope deg/s)
3. Apply z-score normalization using the training scaler
4. Show sensor statistics (mean, std, distribution per channel)
5. Show pipeline performance metrics (accuracy, F1, confidence, drift)
6. Charts: per-class heatmap, accuracy vs drift scatter

All charts are inline. No external image files. Two companion scripts kept in the same folder: one to rebuild the notebook, one to regenerate the Synth Cloud CSV.

---

### Dashboard updates

The handbook dashboard (`thesis/handbook-dashboard/`) received several additions:

**Pipeline flow diagram added.** An animated diagram now shows data flowing through all 10 pipeline stages. A pulse dot moves stage by stage, then shows whether the trigger outcome is NONE, REVIEW, or RETRAIN. If RETRAIN fires, the conditional stages (S8–S10) light up. Key features:

- Toggle between Labeled and Unlabeled mode to demonstrate that RETRAIN requires labels
- Input shows two separate files (Accel CSV + Gyro CSV → merge) matching the actual Garmin format
- Click any stage to see its inputs, outputs, and artifact file
- Clicking the Monitoring stage (S6) opens the 3-layer drift threshold table with exact values from the code

**Deployments tab removed.** Was not useful for thesis work and added unnecessary complexity.

**Dashboard rebuilt** (`npm run build`) — clean 274 KB output.

---

### Repository audit and cleanup

A full repo audit was done. Main findings:

- Config values and thresholds are consistent across all files and match their paper citations
- 24 test modules covering all major pipeline stages
- `.gitignore` is comprehensive
- `src/train.py` is the canonical training file; `scripts/train.py` is a deprecated wrapper (both now have comments saying this)

Cleanup done:

- Stale root-level files moved to `_archive/` (local only, not tracked)
- `.gitignore` updated with pattern for daily link-dump files
- Dashboard artifact name for S9 corrected to match actual file on disk

---

### Branch work and GitHub cleanup

- All work committed to `task/synthetic-data-tasting`
- Merged into `epic/apr-foundation-baseline` (new epic branch created)
- `epic/apr-foundation-baseline` pushed to GitHub
- Deleted branches: `task/synthetic-data-tasting`, `chore/docs-restructure`, `backup-before-cleanup`, `clean-no-large-files`, `chore/repo-cleanup`
- GitHub now has exactly 2 branches: `main` and `epic/apr-foundation-baseline`

---

### Open items carried forward

- Resolved later in Stage 5 refactor: label/prediction length mismatch now hard-fails in
  `src/components/model_evaluation.py`; the old evaluation script was removed.
- Model smoke test not yet implemented (pre-run check: if any single class gets >50% of predictions, abort)
- A7 (config sweep) and A15 (dataflow map) still in progress

---

### Writing status

Ch4 System Design and Ch5 Implementation are writing-ready. Starting Ch4 next session.

---

### Late-session update (continuation)

Additional cleanup and thesis-prep work done in the same day, second session.

**Scope decisions locked — tasks removed from master backlog:**

- A9 (CI/CD): decided that CD is not needed for this thesis. CI (tests/linting) stays, but no automated deployment pipeline. A9 removed from backlog.
- A10 (pseudo-labeling): Stage 13 (Curriculum Pseudo-Labeling) deferred to future work. A10 removed.
- A11 (AdaBN strategy): Advanced optional stages 12–14 (Wasserstein Drift, Pseudo-Labeling, Sensor Placement) all deferred. A11 removed.
- Groups G3 and G4 updated to remove these tasks.

**Docker cleanup:**

- Removed the `preprocessing` service from `docker-compose.yml` — it was a duplicate of the `training` service with a different command. Two services remain: `mlflow` (always-on) and `inference` (always-on) and `training` (on-demand via `--profile training`).

**API metrics pruned:**

- Removed `har_entropy_mean` and `har_baseline_age_days` Prometheus gauges from `src/api/app.py`. These were not thesis-critical. Remaining Prometheus metrics: `har_api_requests_total`, `har_confidence_mean`, `har_flip_rate`, `har_drift_detected`, `har_inference_latency_ms`.

**FastAPI dashboard UI updated (A8 partial):**

- Added a 10-stage pipeline status panel at the top of the dashboard at `src/api/app.py`. S1–S3 shown as grey (require full pipeline CLI). S4–S7 light up green/yellow after inference runs. S8–S10 activate if monitoring signals a drift warning.

**Threshold citations mapped (A12 started):**

- Created `thesis/reference/THRESHOLD_CITATIONS.md` — maps each drift detection threshold to a specific paper citation with ready-to-use thesis sentences:
  - L1 Confidence (0.65/0.50): Guo et al. 2017 ICML + Hendrycks & Gimpel 2017 ICLR
  - L2 Flip rate (35%/50%): Ordóñez & Roggen 2016 Sensors + Hammerla et al. 2016 IJCAI
  - L3 Z-score (2.0σ/3.0σ): Shewhart 1931 SPC + Montgomery 2009 + Gama et al. 2014 ACM CSUR

**Writing resources moved into thesis/ folder:**

- `thesis/notes/` ← `internal/notes/` (TODO, bug log, QnA, solution notes)
- `thesis/reference/` ← `internal/reference/` (tech explanations, why-docs, cheat sheets)
- `thesis/writing/` ← `internal/writing/` (defense QA, writing prompts)

---

## 2026-04-15

### Thesis execution focus update (COPY FROM LLM)

- Final thesis planning is now frozen; no further structure revisions unless supervisor requests changes.
- Current execution priority is writing, not repo redesign.
- Writing order confirmed: Ch4 System Design -> Ch5 Implementation -> Ch7 Experiments -> Ch6 Monitoring.
- Synthetic data will be used as a controlled end-to-end pipeline validation step, not as proof of real-world generalization.
- Newly recorded personal data will be collected next week or next-to-next week as deployment-like evidence.
- Planned evidence story: original labeled data vs synthetic data vs own recorded data.
- Cleanup work allowed only as low-priority background work when blocked or mentally fatigued.
- Main thesis claim remains: production-oriented offline-first MLOps pipeline for wearable HAR under domain shift with monitoring and governed retraining.

## 2026-04-07

### Additional Same-Day Update (workflow review and stage governance)

### Scope Note
- Scientific justification is based on research papers and official technical sources.
- Repository inspection is used only for file-impact mapping and runtime wiring checks.
- Runtime mapping reference in repo: `run_pipeline.py` -> `src/pipeline/production_pipeline.py`, with stage wrappers in `src/components/`; stages 1 to 7 as base path, 8 to 10 as retraining branch, and 11 to 14 as advanced modules.

### MLOps Pipeline Stage Review Checklist (14 stages)

| Stage | Decision | Scientific reason (short) | Manual files to inspect |
|---|---|---|---|
| 1 - Data Ingestion | KEEP (REQUIRED) | Stable ingestion is a non-optional production-ML foundation; dependency instability is a known technical-debt source. | `run_pipeline.py`; `src/pipeline/production_pipeline.py`; `src/components/data_ingestion.py` |
| 2 - Data Validation | KEEP (REQUIRED) | Schema/range/missing-value checks are first-class production safeguards (TFX/TFDV practice). | `src/components/data_validation.py`; `src/data_validator.py`; `src/pipeline/production_pipeline.py` |
| 3 - Data Transformation | KEEP (REQUIRED) | Wearable HAR depends on preprocessing and sliding-window segmentation before inference. | `src/components/data_transformation.py`; `src/preprocess_data.py`; `src/pipeline/production_pipeline.py` |
| 4 - Model Inference | KEEP (REQUIRED) | Inference is the operational prediction step; without it there is no deployed ML system behavior. | `src/components/model_inference.py`; `src/run_inference.py`; `src/pipeline/production_pipeline.py` |
| 5 - Model Evaluation | KEEP (REQUIRED, lean) | Output behavior summaries (confidence, entropy, class balance) are needed for reliability checks, even in weak-label settings. | `src/components/model_evaluation.py`; `src/pipeline/production_pipeline.py` |
| 6 - Post-Inference Monitoring | KEEP (REQUIRED) | Monitoring is essential in non-stationary environments with drift risk and delayed/no production labels. | `src/components/post_inference_monitoring.py`; `scripts/post_inference_monitoring.py`; `src/pipeline/production_pipeline.py` |
| 7 - Trigger Evaluation | KEEP (REQUIRED) | Drift evidence must be converted into governed action decisions (`no action`, `alert`, `review`, `retrain`). | `src/components/trigger_evaluation.py`; `src/trigger_policy.py`; `src/pipeline/production_pipeline.py` |
| 8 - Model Retraining | KEEP (REQUIRED, branch-only) | Adaptation under drift is required, but should be evidence-triggered rather than blindly periodic. | `src/components/model_retraining.py`; `src/pipeline/production_pipeline.py`; `src/domain_adaptation/*` |
| 9 - Model Registration | KEEP (REQUIRED, branch-only) | Promotion/versioning/rollback are needed for traceability and safe governance after retraining. | `src/components/model_registration.py`; `src/deployment_manager.py`; `src/model_rollback.py`; `src/pipeline/production_pipeline.py` |
| 10 - Baseline Update | KEEP (REQUIRED, branch-only) | Monitoring baselines must stay aligned with accepted model updates to avoid false/inconsistent drift alarms. | `src/components/baseline_update.py`; `scripts/build_training_baseline.py`; `src/pipeline/production_pipeline.py` |
| 11 - Calibration and Uncertainty | KEEP (MERGE into 5/6) | Confidence-based policies are weaker with uncalibrated probabilities; calibration is useful but cleaner inside evaluation/monitoring. | `src/components/calibration_uncertainty.py`; `src/calibration.py` |
| 12 - Wasserstein Drift | OPTIONAL (research) | Useful metric, but metric choice is implementation-specific; not mandatory as a standalone core stage. | `src/components/wasserstein_drift.py`; `src/wasserstein_drift.py`; `src/pipeline/production_pipeline.py` |
| 13 - Curriculum Pseudo-Labeling | OPTIONAL (research) | Valuable for adaptation experiments but assumption-sensitive and risk-prone under low pseudo-label quality. | `src/components/curriculum_pseudo_labeling.py`; `src/curriculum_pseudo_labeling.py`; `src/pipeline/production_pipeline.py` |
| 14 - Sensor Placement Robustness | OPTIONAL (research) | Scientifically important for wearable HAR robustness, but not required in the central operational MLOps loop. | `src/components/sensor_placement.py`; `src/sensor_placement.py`; `src/pipeline/production_pipeline.py` |

### Final Workflow Decision
- Required thesis core: stages 1 to 10.
- Keep but merge (not standalone major stage): stage 11 into stages 5 and 6.
- Keep as optional research/advanced modules: stages 12, 13, and 14.

### Paste-Ready Summary Note
> Final decision for thesis workflow governance: stages 1 to 10 are required as the minimum defensible MLOps pipeline (7-stage inference-monitoring loop plus 3-stage governed retraining loop). Stage 11 should be retained only as an integrated calibration/uncertainty enhancement inside evaluation or monitoring. Stages 12 to 14 should remain optional research modules rather than core runtime requirements. File-impact checks must prioritize `run_pipeline.py`, `src/pipeline/production_pipeline.py`, stage wrappers under `src/components/`, and supporting modules under `src/` and `scripts/` before any deletion/refactor action.

### Scientific References Used For Justification
1. Hidden Technical Debt in Machine Learning Systems - https://papers.neurips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf
2. The ExampleValidator TFX Pipeline Component - https://www.tensorflow.org/tfx/guide/exampleval
3. A Survey on Wearable Human Activity Recognition - https://publikationen.bibliothek.kit.edu/1000169626/152527236
4. TFX: A TensorFlow-Based Production-Scale Machine Learning Platform - https://dl.acm.org/doi/10.1145/3097983.3098021
5. On The Reliability Of Machine Learning Applications In Manufacturing Environments - https://arxiv.org/abs/2112.06986
6. A Survey on Concept Drift Adaptation - https://mpechen.win.tue.nl/publications/pubs/Gama_ACMCS_AdaptationCD_accepted.pdf
7. Time to Retrain? Detecting Concept Drifts in Machine Learning Systems - https://arxiv.org/abs/2410.09190
8. On Calibration of Modern Neural Networks - https://proceedings.mlr.press/v70/guo17a/guo17a.pdf
9. Pseudo Labels for Unsupervised Domain Adaptation: A Review - https://www.researchgate.net/publication/372896834_Pseudo_Labels_for_Unsupervised_Domain_Adaptation_A_Review
10. Sensor Placement Variations in Wearable Activity Recognition - https://kaikunze.de/papers/pdf/kunze2014sensor.pdf

## 2026-04-08

### Audit Script Build and Enhancement (repo-level MLOps audit)

### Scope
- Added and stabilized a dedicated repository audit script to generate structured MLOps health reports.
- Extended reports to show not only findings, but also exactly what each category checked.
- Added cleanup-oriented analysis for documentation/script sprawl to support thesis-repo maintainability.

### Work Completed
- Created and completed `mlops_audit.py` as an executable end-to-end auditor.
- Implemented all missing methods and added a working CLI entrypoint.
- Added category-level check catalog and report rendering:
  - each category now includes a `Checks performed` subsection in Markdown,
  - JSON now includes `checks_per_category` for downstream tooling.
- Improved dead-code/duplication scan scope:
  - scans both `src/**/*.py` and `scripts/**/*.py`,
  - uses import graph + CLI entrypoint detection + textual reference checks,
  - includes file-level and function-level duplication heuristics.
- Added repository sprawl analytics and cleanup guide output:
  - markdown/script volume metrics,
  - duplicate markdown-stem examples,
  - cleanup candidate list and recommended consolidation actions.

### Validation
- Executed `python mlops_audit.py` multiple times after each enhancement wave.
- Executed `python -m py_compile mlops_audit.py` and confirmed exit code `0`.

### Evidence
- Script: `mlops_audit.py`
- Latest markdown report: `reports/repo_audit/audit_2026-04-08T1441.md`
- Latest JSON report: `reports/repo_audit/audit_2026-04-08T1441.json`

### Outcome
- Audit reports are now explainable per category (transparent check list even when findings are empty).
- Dead-code/duplication scanning is more thorough for both `src` and `scripts`.
- Documentation cleanup pressure is explicit and actionable via the new cleanup guide section.

### Task Linkage
- Primary: A14 (debug/harden major code paths), A20 (repo-readiness pass).
- Secondary support: A15 (dataflow and traceability clarity through structured audit outputs).

## 2026-04-03

### Session Trail (synthetic-data kickoff)
- Created working branch `task/synthetic-data-tasting` from `main` for synthetic-data execution.
- Started grouped execution from G1 and excluded branch setup/naming from remaining task list.

### Group Task Focus (Remaining from G1, excluding A1)

| Task ID | Status | Task | Expected Output / Evidence |
|---|---|---|---|
| A2 | IN_PROGRESS | Validate synthetic data through full pipeline end-to-end | Synthetic pipeline run report with stage metrics and failure notes |
| A3 | IN_PROGRESS | Evaluate confidence behavior on synthetic and production-like runs | Confidence trend tables and threshold-hit analysis |
| A7 | IN_PROGRESS | Compare preprocessing/config combinations to select baseline config | Config sweep matrix + selected baseline with rationale |
| A15 | IN_PROGRESS | Verify complete dataflow understanding (ingest to deploy decisions) | End-to-end dataflow map/checklist with checkpoints |

### Immediate Next Actions
- Execute first synthetic end-to-end run and log artifact paths.
- Capture confidence and monitoring outputs for synthetic sessions.
- Prepare config-sweep plan for A7 after first stable synthetic baseline run.

### Additional Same-Day Update (label-aware synthetic run governance)

### Work Completed
- Added labeled-vs-unlabeled detection during Stage 1 ingestion (CSV header check for label columns such as `activity`, `label`, `target`).
- Extended ingestion artifact metadata to persist detected label status and label-column name.
- Added startup log line in pipeline orchestration to explicitly report dataset label status:
  - `LABELED` when labels file exists or label column is detected
  - `UNLABELED` when neither is present
- Added retraining safety gate in Stage 8:
  - unlabeled runs now skip supervised retraining by default
  - unlabeled retraining is allowed only with explicit adaptation methods (`adabn`, `tent`, `adabn_tent`, `pseudo_label`) or with provided labels.
- Added explicit Stage 5 evaluation-mode logs (`LABELED` vs `UNLABELED`) based on real labels-file availability.
- Wired `--labels` into Stage 5 evaluation config (not only Stage 8 retraining config), so run context is consistent.

### Task Linkage
- Primary: A2 (synthetic validation), A3 (confidence/drift interpretation), A15 (dataflow clarity)
- Secondary: A14 (code-path hardening, partial)

### Validation
- Ran syntax validation on modified files:
  - `python -m compileall run_pipeline.py src/components/data_ingestion.py src/components/model_evaluation.py src/entity/artifact_entity.py src/pipeline/production_pipeline.py`
- Ran runtime smoke test for stages 4 to 7:
  - `python run_pipeline.py --stages inference evaluation monitoring trigger --skip-ingestion --skip-validation`
  - confirmed log lines for:
    - `Dataset label status: UNLABELED ...`
    - `Inference confidence threshold: 0.50`
    - `Evaluation mode: UNLABELED ...`
- Ran runtime smoke test including Stage 8 gate:
  - `python run_pipeline.py --stages inference evaluation monitoring trigger retraining --skip-ingestion --skip-validation`
  - confirmed skip guard log line:
    - `Stage 8 SKIPPED — dataset is UNLABELED and supervised retraining is blocked by default ...`

### Outcome
- Synthetic and production runs are now easier to distinguish operationally in logs.
- Unlabeled production-like runs no longer enter supervised retraining by accident.

### Additional Same-Day Update (dual synthetic dataset run, codex vs other)

### Dataset Naming and Source Mapping
- Codex synthetic dataset source:
  - `data/codex_synth/synthetic_all_users_labeled_v1.csv`
  - run input alias: `data/synthetic_runs/synthetic_codex_input.csv`
- Other synthetic dataset source:
  - `data/synthetic/synthetic_labeled.csv`
  - run input alias: `data/synthetic_runs/synthetic_other_input.csv`

### Execution Scope Today
- Ran controlled stages 1 to 7 for both synthetic datasets:
  - ingestion, validation, transformation, inference, evaluation, monitoring, trigger
- Controlled stages 1 to 10 execution is deferred to next planned task block (not executed today).

### Saved Run Logs (terminal capture)
- Codex synthetic run log:
  - `logs/synthetic_runs/synthetic_codex_stage1to7_20260403_163854.log`
- Other synthetic run log:
  - `logs/synthetic_runs/synthetic_other_stage1to7_20260403_163958.log`

### Key Results Snapshot (from RUN SUMMARY + stage outputs)
- Codex synthetic (`synthetic_codex_input.csv`):
  - status: SUCCESS (7/7)
  - windows: 3,852
  - mean confidence: 83.3%
  - uncertain: 379 (9.8%)
  - dominant class: hand_tapping (71.6%)
  - drift max: 0.001 (PASS)
  - trigger decision: NONE
- Other synthetic (`synthetic_other_input.csv`):
  - status: SUCCESS (7/7)
  - windows: 3,852
  - mean confidence: 80.0%
  - uncertain: 491 (12.7%)
  - dominant class: hand_tapping (57.9%)
  - drift max: 0.009 (PASS)
  - trigger decision: NONE

### Quick Analysis for Today (A3, A7, A15)
- Confidence behavior (A3): both synthetic datasets are stable enough for stage-7 PASS; Codex synthetic currently yields higher mean confidence than the other synthetic set.
- Preprocessing/normalization check (A7): current pipeline path remains unit-conversion ON, gravity-removal OFF, calibration OFF, normalization ON (zscore). Both synthetic runs completed successfully with this profile.
- Normalization evidence note: transformation logs showed normalized output with controlled ranges and successful downstream inference/monitoring. This is a supporting signal that normalization is helping keep feature-space behavior compatible with the pretrained model path.
- Dataflow verification (A15): stage sequence 1 to 7 executed end-to-end on both synthetic datasets, and stage-7 decisions were traceable from stage-6 monitoring outputs.

### Additional Engineering Update
- Added one extra line in final compact run summary block:
  - `Label status` now appears in RUN SUMMARY (LABELED/UNLABELED with source when available).

### Next Planned Actions
- Run controlled stages 1 to 10 for synthetic testing in the next session with explicit retraining strategy selection.
- Expand A7 evidence from baseline profile to comparative normalization proof (zscore vs disabled/alternate settings where feasible) and document final rationale.

### Additional Same-Day Update (log cleanup + rerun verification wave)

### What Was Messy and What Was Fixed
- Root issue 1 (run-summary input source confusion): run summary showed `sensor_fused_50Hz.csv` because ingestion canonicalizes all inputs into that file before Stage 3.
- Fix: run summary now shows original source alias and canonical output together (e.g., `synthetic_codex_input.csv -> sensor_fused_50Hz.csv`).
- Root issue 2 (label status mismatch on unlabeled reruns): pre-ingestion fallback label detection could remain sticky even after Stage 1 ingested unlabeled data.
- Fix: Stage 1 ingestion label detection is now authoritative and always overwrites run label status metadata.

### Log Hygiene Note
- Terminal-capture logs under `logs/synthetic_runs/*.log` can look noisy due shell encoding/stream capture behavior.
- Canonical readable evidence for analysis is now anchored to:
  - `logs/<run_id>.log` (pipeline logger output)
  - `logs/pipeline/pipeline_result_<run_id>.json` (structured metrics)
  - `logs/synthetic_runs/run_comparison_20260403.md` (clean comparison summary)

### Reruns Executed For Verification
- Synthetic codex (stages 1 to 7): run id `20260403_165755`
- Synthetic other (stages 1 to 7): run id `20260403_165824`
- all_users labeled alias (stages 1 to 7): run id `20260403_165859`
- Real unlabeled raw pair (stages 1 to 7): run id `20260403_170648`

### Comparison Result (confidence-focused)
- See clean report: `logs/synthetic_runs/run_comparison_20260403.md`
- Snapshot:
  - synthetic_codex: mean confidence `0.8330`, uncertain `9.84%`, dominant hand_tapping `71.57%`
  - synthetic_other: mean confidence `0.7999`, uncertain `12.75%`, dominant hand_tapping `57.94%`
  - all_users_labeled alias: mean confidence `0.8505`, uncertain `7.48%`, dominant hand_tapping `68.90%`
  - real_unlabeled: mean confidence `0.8714`, uncertain `6.06%`, dominant hand_tapping `85.58%`, drift max `1.0434`

### Interpretation (today)
- The hand_tapping dominance is not caused by accidental unlabeled substitution of synthetic files; it appears consistently across labeled synthetic and labeled all-users reruns, suggesting model behavior/prior bias rather than a file-routing bug.
- Normalization remained stable and consistent across runs (`zscore`, gravity removal OFF, calibration OFF), and all runs completed successfully through Stage 7.
- Label-status reporting in both pipeline logs and run summary is now explicit and consistent after the Stage-1-authoritative fix.

### Additional Same-Day Update (fused naming + actual labeled dataset check)

### What Changed in Pipeline Behavior
- Stage 1 fused output naming is now source-aware:
  - pattern: `fused_<dataset_name>_50Hz.csv`
  - examples:
    - `fused_all_users_data_labeled_actual_input_50Hz.csv`
    - `fused_synthetic_codex_input_50Hz.csv`
- Backward compatibility preserved:
  - canonical alias `sensor_fused_50Hz.csv` is still synchronized automatically so existing skip/fallback paths continue to work.

### Actual Labeled Dataset Execution Result
- Direct run using raw training file:
  - `--input-csv data/all_users_data_labeled.csv --labels data/all_users_data_labeled.csv`
  - run id: `20260403_173725`
  - result: failed at Stage 2 validation because source schema is training-format (`Ax_w..Gz_w`) while production path requires (`Ax..Gz`).
- To evaluate the actual labeled data in production stages 1 to 7, created a pipeline-compatible projection with column-name mapping only:
  - `data/synthetic_runs/all_users_data_labeled_actual_input.csv`
  - no row/value changes, only `*_w` sensor columns renamed to production sensor names.

### Fresh Comparison Runs (post naming update)
- actual labeled projected run id: `20260403_173813`
- synthetic codex run id: `20260403_173852`
- clean report:
  - `logs/synthetic_runs/actual_vs_synthetic_20260403.md`

### Snapshot
- actual_all_users_labeled_projected:
  - mean confidence `0.8505`
  - uncertain `7.48%`
  - dominant hand_tapping `68.90%`
  - drift max `0.000`
  - trigger `none`
- synthetic_codex:
  - mean confidence `0.8330`
  - uncertain `9.84%`
  - dominant hand_tapping `71.57%`
  - drift max `0.001`
  - trigger `none`

### Interpretation (this update)
- The actual labeled dataset (projected to production schema) shows slightly better confidence and lower uncertainty than synthetic codex under the same Stage 1 to 7 path.
- Both runs still show hand_tapping dominance and both remain trigger-action `none`, reinforcing that current system behavior is stable but biased toward one dominant class.

### Additional Same-Day Update (automatic schema acceptance for labeled/synthetic/production)

### Feature Added
- Stage 1 now auto-normalizes common sensor-column variants in direct CSV ingestion so mixed schemas are accepted without manual projection.
- Example auto-mappings:
  - `Ax_w -> Ax`, `Ay_w -> Ay`, `Az_w -> Az`
  - `Gx_w -> Gx`, `Gy_w -> Gy`, `Gz_w -> Gz`
  - case/underscore/hyphen variants and common accel/gyro aliases are also accepted.

### Verification Runs
- Labeled training-format CSV direct (no manual projection):
  - command input: `data/all_users_data_labeled.csv`
  - run id: `20260403_180724`
  - result: SUCCESS through Stage 7; schema normalization applied and validation passed.
- Synthetic labeled CSV:
  - command input: `data/synthetic_runs/synthetic_codex_input.csv`
  - run id: `20260403_180810`
  - result: SUCCESS (stages ingestion + validation).
- Production raw pair (unlabeled):
  - command input: `data/raw/2025-07-16-21-03-13_accelerometer.csv` + gyroscope pair
  - run id: `20260403_180832`
  - result: SUCCESS (stages ingestion + validation).

### Outcome
- Pipeline now accepts all requested dataset categories in one path:
  - production raw sensor pair,
  - synthetic CSV,
  - labeled training-style CSV with `*_w` sensor columns.
- No manual preprocessing projection step is required for `all_users_data_labeled.csv` anymore.

### End-of-Day Review (senior MLOps audit)

Full review recorded in `bug_april.md`. Summary:

#### Bugs confirmed

- BUG-1 (low): `reused_existing` field referenced in RUN SUMMARY (`run_pipeline.py:630`) but never set in `DataIngestionArtifact` — `(reused)` label silently never appears.
- BUG-2 (high, thesis-critical): Label awareness broken between Stage 1 and Stage 5. Stage 1 auto-detects label columns and marks run as LABELED. Stage 5 evaluation ignores this and only goes LABELED when `--labels` is passed explicitly. All synthetic labeled runs today ran Stage 5 in UNLABELED mode — no classification metrics computed against ground truth. Evidence for A2/A3 is incomplete.
- BUG-3 (low): `LABEL_COLUMN_CANDIDATES` and `NON_GROUND_TRUTH_COLUMNS` duplicated in both `data_ingestion.py` and `production_pipeline.py` — divergence risk.

#### Research gaps confirmed

- GAP-1 (thesis-critical): `hand_tapping` dominance (57–85%) across all datasets not investigated. Needs training data class distribution check and majority-class baseline comparison before Ch.7/Ch.8 can make valid claims.
- GAP-2: `drift_max = 1.0434` on real production data is the most interesting result today and is under-documented. Real data drift is ~100x higher than synthetic (0.001–0.009). Needs thesis-level interpretation.

#### Next session priorities

1. Fix BUG-2 — wire ingested label column into Stage 5 evaluation so labeled CSVs get classification metrics automatically.
2. Investigate GAP-1 — check training data class balance, run majority-class baseline comparison.
3. Document GAP-2 drift finding properly for Ch.6/Ch.7.

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
  - touched `src/api/app.py`, the old Stage 5 evaluation script, `src/pipeline/production_pipeline.py`, `src/run_inference.py`, `src/train.py`, and `src/utils/label_mapping.py`
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
  - old Stage 5 evaluation script (later removed after logic moved into `src/components/model_evaluation.py`)
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

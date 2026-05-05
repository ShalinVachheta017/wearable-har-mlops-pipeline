  # Next-Week Pipeline Fix Register (2026-04-23)

This file records what we found today and what must be fixed next week.

- Scope date: 2026-04-23
- Decision: do not implement fixes this week; execute next week.
- Primary evidence: [PIPELINE_DIAGNOSTIC_CHECKLIST.md](PIPELINE_DIAGNOSTIC_CHECKLIST.md)
- Supporting evidence: [reports/model_comparison_full_matrix.csv](reports/model_comparison_full_matrix.csv)

## Why this register exists

The current behavior is not logically consistent for production trust:

- Mentor/pretrained model is collapsing on labeled/synthetic/production runs.
- Retrained models look very strong on training-style evaluation, but leakage and split design make those numbers non-generalization scores.
- Preprocessing/scaler governance has multiple inconsistencies.

So this document is the working execution list for next week.

## Confirmed findings from today

1. Pretrained scaler mismatch is highly likely:
   - Pretrained has no dedicated scaler file.
   - Current pipeline/notebook apply retrained-era scaler statistics.
   - Signature: high-confidence wrong predictions with dominant class collapse.

2. Leakage risk is confirmed:
   - Scaler was fit on all users (not strict train-only users).
   - Random window-level split is used instead of user-group holdout split.

3. Gravity/orientation shortcut risk is confirmed:
   - Large class-linked spread in mean `Az`.
   - Production wrist orientation cluster differs from training cluster.

4. Production domain shift is real:
   - Post-zscore production means/stds are not close to `(0,1)` channel-wise.

5. Scaler governance is inconsistent:
   - `data/prepared/config.json` and `models/retrained/scaler_config.json` are not identical.
   - Notebook/API paths are not guaranteed to use a single source of truth.

6. Additional matrix findings from today:
   - `pretrained/fine_tuned_1dcnnbilstm` row: very low labeled accuracy.
   - `retrained/har_20260327_213930` row: highest normalized score in matrix.
   - `pretrained/current_model` row: file missing error.
   - Multiple rows share effectively identical metrics (possible alias/duplicate artifact references).

## Next-week execution plan (do this next week)

### P0 (must fix first)

- [ ] P0.1 Scaler source-of-truth unification
  - Choose one canonical scaler artifact for runtime.
  - Make notebook + API + pipeline all load the same file.
  - Add guard test/checksum assertion.

- [ ] P0.2 Train-only scaler fitting policy
  - Refit scaler using train users only.
  - Regenerate prepared config with explicit provenance fields (`fit_dataset`, `fit_users`, timestamp).

- [ ] P0.3 User-grouped evaluation protocol
  - Replace random window split for reporting with user-group holdout/CV (`GroupKFold` or equivalent).
  - Re-run model comparison under user-holdout protocol.
  - Re-label all old random-split metrics as non-generalization.

- [ ] P0.4 Pretrained comparison fairness
  - Either recover pretrained-compatible scaler or remove pretrained from unfair normalized comparison.
  - Run explicit ablation (`with scaler` vs `without scaler`) for pretrained path.

### P1 (high value)

- [ ] P1.1 Gravity/orientation robustness experiment
  - Add gravity-removal/preprocessing branch and run ablation.
  - Compare class-collapse tendency before/after.

- [ ] P1.2 Windowing boundary hygiene
  - Ensure window creation resets per user/session/activity boundary.
  - Remove cross-user and mixed-boundary windows by construction.

- [ ] P1.3 Artifact cleanup in model matrix
  - Resolve `pretrained/current_model` missing file reference.
  - Mark/merge duplicate alias models in reports.

### P2 (documentation and submission clarity)

- [ ] P2.1 Update report/thesis language
  - Separate in-sample numbers vs user-holdout generalization numbers.
  - Add explicit caveat about old matrix limitations.

- [ ] P2.2 Add reproducibility note
  - Document exact scaler lineage and evaluation protocol in one place.

## Deferred status

Everything in this register was deferred on 2026-04-23. Status refreshed 2026-04-25 (see "Progress refresh" below). Verification work and report wording remain pending.

## Progress refresh — 2026-04-25

Code paths landed in the working tree this week. None of these are verified end-to-end yet (no pytest, API smoke, Docker smoke, or thesis build was run after them in the current session). Treat as scaffolding to be checked, not as closed items.

### P0 status

- [x] **P0.1 Scaler source-of-truth unification** — canonical loader `src/utils/scaler.py` added; runtime call sites rewired in `src/config.py`, `src/api/app.py`, `src/preprocess_data.py`, `src/monitoring/baseline_builder.py`. **Verification pending** (integrity assertion test, single-loader confirmation across notebook/API/pipeline).
- [x] **P0.2 Train-only scaler fitting policy** — refit script `scripts/refit_scaler_train_only.py` produces `data/prepared/scaler_train_only.json`. Provenance fields (`fit_dataset`, `fit_users`, timestamp) included by construction. **Verification pending** (regenerate, diff against `models/retrained/scaler_config.json`, confirm no path still loads the old all-users scaler).
- [~] **P0.3 User-grouped evaluation protocol** — `src/train.py` switched to `GroupKFold` with user IDs as groups; user-holdout scripts added (`scripts/evaluate_user_holdout.py`, `scripts/retrain_user_holdout.py`, `scripts/retrain_user_holdout_fast.py`). **Verification pending** (run user-holdout evaluation, regenerate model comparison matrix under user-holdout, re-label old random-split metrics in reports as non-generalization).
- [~] **P0.4 Pretrained comparison fairness** — `docs/pretrained_model_exclusion_report.md` now documents the comparison-boundary stance: the pretrained artifact is the defended runtime model, but it is excluded from reproduced local quantitative comparison without the original scaler/corpus. `docs/MODEL_PROMOTION_POLICY.md` records the promotion rules. Ablation (with-scaler vs without-scaler for the pretrained path) **not yet executed**.

### P1 status

- [~] **P1.1 Gravity/orientation robustness experiment** — ablation hooks added in `src/components/data_transformation.py` and `scripts/test_gravity_removal.py`. **Run + collapse-tendency comparison still open.**
- [~] **P1.2 Windowing boundary hygiene** — user-isolated windowing referenced in `src/train.py`; per-session/activity boundary handling needs an explicit verification test ("zero participant-crossing windows by construction"). The April-report Ch.4 evidence already cites the user-isolated count of 3,845 windows with 0 participant-crossing windows; verify the runtime path produces the same numbers.
- [ ] **P1.3 Artifact cleanup in model matrix** — `pretrained/current_model` missing-file reference and duplicate alias rows still present.

### P2 status

- [~] **P2.1 Update report/thesis language** — April-report Ch.4 (rewritten 2026-04-25) separates in-sample vs grouped/user-holdout language and labels production replay and synthetic data as descriptive-only. The 2026-04-26 wording pass is April-report-only; the remaining decision is whether the April version structurally supersedes the original report.
- [x] **P2.2 Reproducibility note** — captured across `docs/MODEL_PROMOTION_POLICY.md`, `docs/THESIS_CONSISTENCY_NOTES.md`, and the April-report Ch.4 §4.10 "Reproducibility and Consistency Considerations".

## Planned audit session (Codex/Copilot, not Claude)

- Title: **2026-04-25/26 — Read-Only Pipeline Robustness and Evidence Verification Audit.**
- Prompt: `sandbox:/mnt/data/temporary_pipeline_audit_prompt_2026-04-25.md` (temporary, external).
- **Hard rule: do not edit anything. Only audit, classify, and report evidence.**
- Output: audit report under `reports/` plus a short summary in `WORKLOG.md`. Any required code/doc changes are added to `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md`, never applied inside the audit session.

## Audit refresh - 2026-04-25

A read-only Codex audit returned **ORANGE** status. The pipeline is structurally strong but not yet 100% evidence-verified.

Scope decision: Prometheus, Grafana, and alert-rule files are **not part of the defended current thesis implementation**. They may remain as historical/optional/future-work material, but they should not be used as active evidence for monitoring or deployment readiness.

Net-open items for next verification session:

1. Defended runtime model identity: **closed 2026-04-26** with Option A (`models/pretrained/fine_tuned_model_1dcnnbilstm.keras`).
2. Align April-report Ch4, April-report Ch7/Ch8 draft boundaries, and exclusion/governance docs to the Option A canonical sentence: **closed 2026-04-26** for April-report scope; main thesis-report files are intentionally not part of this pass.
3. Run fresh current-branch full test evidence.
4. Verify Docker/API with actual model-loaded inference.
5. Prometheus/Grafana/alerting scope: **closed 2026-04-26** for the tracker/evidence files; catch any remaining active claims during the P0.6 doc sweep.
6. Produce retraining-governance decision matrix.
7. Verify API monitoring parity or document it as a lightweight API path.
8. Keep landed-but-unverified items open until evidence is captured.

## `pt.md` internal review additions - 2026-04-26

`pt.md` is not a thesis citation source. Use it only as internal implementation/checklist guidance for the next focused pipeline-evidence session.

Detailed reusable note: [docs/UNLABELED_DATA_MODEL_IMPROVEMENT_GUIDE.md](docs/UNLABELED_DATA_MODEL_IMPROVEMENT_GUIDE.md).

### Add to P0/P1 execution scope

- [ ] **PT-1 Window-level evidence schema** — verify or add per-window output fields: `window_id`, file/session id, start/end time, model version, scaler version, effective sampling rate, sensor stats, predicted class, top probabilities, confidence, entropy, top-2 margin, drift/OOD score, and processing status.
- [ ] **PT-2 Sensor synchronization QA artifact** — save match rate, mean/max timestamp delta, dropped rows, missing synchronized rows, and effective sampling rate for accel/gyro fusion. This strengthens Ch4/Ch5 evidence.
- [ ] **PT-3 Gyro-axis drift quarantine + ablation** — severe axis shift should trigger investigation before retraining: units, axis mapping, calibration, clipping, timestamp alignment, wearing position. If still suspicious, compare all channels, accel-only, gyro-only, no-gyro-x, and clipped/normalized-gyro-x.
- [ ] **PT-4 Strict pseudo-label governance** — pseudo-labeling remains candidate-only. Accept pseudo-labels only under high confidence, low entropy, low OOD, temporal stability, and class-balance control. Prefer active-learning export for suspicious/uncertain windows. No model promotion without labeled confirmation.
- [ ] **PT-5 Monitoring report completeness** — final monitoring evidence should cover data quality, sampling/unit checks, synchronization, raw-axis drift, magnitude drift, feature/embedding drift if available, prediction distribution, confidence, temporal consistency, OOD rate, and recommended action.

### How to connect this to existing next-week tasks

- PT-1 and PT-5 support P0-AUDIT-5 and P0-AUDIT-6.
- PT-2 supports P1.2 windowing/boundary hygiene and Ch4 preprocessing evidence.
- PT-3 supports P1.1 gravity/orientation robustness and the z-score/no-normalization evidence track.
- PT-4 supports A4/A5 retraining governance and the Option A model-promotion story.

## Net-open work for the next focused session

1. Run `pytest tests/` against the hardened branch and capture the result count.
2. Run `python run_pipeline.py --help` and a stages-1-7 smoke on `feature/api-two-file-upload`; save artifacts under `reports/`.
3. Run `scripts/refit_scaler_train_only.py` and diff the produced `data/prepared/scaler_train_only.json` against `models/retrained/scaler_config.json`; confirm only one is loaded at runtime.
4. Execute `scripts/evaluate_user_holdout.py` and regenerate the model comparison matrix under user-holdout; mark old random-split rows as non-generalization in `reports/model_comparison_full_matrix.csv`.
5. Run the gravity-removal ablation through `scripts/test_gravity_removal.py`; record collapse-tendency comparison.
6. Decide P0.4: either recover a pretrained-compatible scaler or finalize the exclusion of pretrained from the normalized comparison and update the thesis matrix accordingly.
7. Review PT-1 to PT-5 above and decide which ones are quick evidence improvements versus later/future-work items.

## Links

- [PIPELINE_DIAGNOSTIC_CHECKLIST.md](PIPELINE_DIAGNOSTIC_CHECKLIST.md)
- [reports/model_comparison_full_matrix.csv](reports/model_comparison_full_matrix.csv)
- [src/train.py](src/train.py)
- [src/components/model_retraining.py](src/components/model_retraining.py)
- [src/utils/scaler.py](src/utils/scaler.py)
- [scripts/refit_scaler_train_only.py](scripts/refit_scaler_train_only.py)
- [scripts/evaluate_user_holdout.py](scripts/evaluate_user_holdout.py)
- [scripts/retrain_user_holdout.py](scripts/retrain_user_holdout.py)
- [scripts/test_gravity_removal.py](scripts/test_gravity_removal.py)
- [data/prepared/config.json](data/prepared/config.json)
- [models/retrained/scaler_config.json](models/retrained/scaler_config.json)
- [docs/MODEL_PROMOTION_POLICY.md](docs/MODEL_PROMOTION_POLICY.md)
- [docs/pretrained_model_exclusion_report.md](docs/pretrained_model_exclusion_report.md)
- [docs/THESIS_CONSISTENCY_NOTES.md](docs/THESIS_CONSISTENCY_NOTES.md)
- [docs/UNLABELED_DATA_MODEL_IMPROVEMENT_GUIDE.md](docs/UNLABELED_DATA_MODEL_IMPROVEMENT_GUIDE.md)
- [thesis/april_report/chapters/ch4_data_processing_model_development.tex](thesis/april_report/chapters/ch4_data_processing_model_development.tex)

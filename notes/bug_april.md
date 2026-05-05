# Bug & Review Log — April 2026

---

## 2026-04-03 — Senior MLOps Review (task/synthetic-data-tasting)

### What Worked

- Schema auto-normalization (`Ax_w → Ax`) correct — `_normalize_column_key` strips underscores → `axw` matches alias set
- Stage-1-authoritative label overwrite correctly fixes the sticky-label race condition
- Stage 8 unlabeled guard (`goto_cleanup`) works correctly
- Fused naming `fused_<dataset>_50Hz.csv` + canonical sync is clean backward-compat design
- `DataIngestionArtifact` `has_labels`/`label_column` fields propagate correctly through `PipelineResult`

---

### Bugs

#### BUG-1 — `reused_existing` referenced but never set (silent feature hole)

- **File:** `run_pipeline.py:630`
- **Description:** `getattr(result.ingestion, "reused_existing", False)` is called in the RUN SUMMARY block, but `DataIngestionArtifact` (artifact_entity.py:21-33) has no such field. The `getattr` fallback prevents a crash but the `(reused)` label in the RUN SUMMARY box will never appear, even when it should.
- **Severity:** Low — silent, no crash, wrong display only
- **Fix:** Add `reused_existing: bool = False` to `DataIngestionArtifact` and set it to `True` in the cached/existing paths inside `data_ingestion.py`

---

#### BUG-2 — Label awareness broken between Stage 1 and Stage 5 (thesis-critical)

- **Files:** `src/components/data_ingestion.py`, `src/components/model_evaluation.py:45-52`
- **Description:** Stage 1 auto-detects label columns in the CSV and marks the run as `LABELED` in `PipelineResult`. Stage 5 evaluation **ignores this** — it only enters LABELED mode if `--labels` is passed as a CLI argument. All synthetic runs today showed `dataset_has_labels=True` in the result, but Stage 5 ran in UNLABELED mode — no classification metrics were computed against ground truth labels even though they were in the CSV.
- **Severity:** High — synthetic labeled data is not actually being evaluated with labels. Evidence for A2/A3 is incomplete.
- **Fix:** Wire `ingestion_art.label_column` (or `result.dataset_has_labels`) into `ModelEvaluationConfig.labels_path` when no explicit `--labels` is provided but the ingested CSV contains a label column.

---

#### BUG-3 — Duplicate constants, no single source of truth

- **Files:** `src/components/data_ingestion.py:78-98` and `src/pipeline/production_pipeline.py:81-101`
- **Description:** `LABEL_COLUMN_CANDIDATES` and `NON_GROUND_TRUTH_COLUMNS` are copy-pasted in both files. If one is updated the other silently diverges.
- **Severity:** Low — tech debt, future divergence risk
- **Fix:** Move both to a shared module (e.g., `src/utils/label_detection.py`) and import from both locations.

---

### Research / Analysis Gaps

#### GAP-1 — `hand_tapping` dominance not investigated (thesis-critical)

| dataset | dominant_pct |
|---|---:|
| real_unlabeled | 85.6% |
| synthetic_codex | 71.6% |
| actual_labeled_projected | 68.9% |
| synthetic_other | 57.9% |

Dismissed in worklog as "model behavior/prior bias". Not a valid thesis argument.

**Required actions:**
1. Check class distribution in training data — if `hand_tapping` ~70% of training samples, model learned class-prior shortcut
2. Compare against majority-class baseline — if a trivial predictor matches model accuracy, the model is broken
3. Document explicitly in Ch.7 and Ch.8 — do not hide this finding

---

#### GAP-2 — `drift_max = 1.0434` on real production data under-documented

- Real unlabeled run (`20260403_170648`): `drift_max = 1.0434`, `trigger = none`
- Threshold is `drift_zscore_warn: 2.0` so trigger is technically correct
- But 1.04 is halfway to the warning threshold on the **first real-data run**
- Synthetic data drift: 0.001 / 0.009 — real data is 100x higher
- **This is the most interesting result from today and needs thesis-level interpretation, not just a PASS note**

---

### Design Issues

#### DESIGN-1 — `goto_cleanup = True` pattern is fragile

- **File:** `src/pipeline/production_pipeline.py` ~line 654-660
- Sets `retraining_art = registration_art = baseline_art = None` then `goto_cleanup = True; continue`
- Works now, but if any stage is added after retraining in the future it silently won't run
- A plain `break` would be more honest and safer

#### DESIGN-2 — Identical window count (3,852) for both synthetic datasets

- Both synthetic datasets produce exactly 3,852 windows
- Likely same row count in generated CSVs — verify synthetic generators produce same recording duration
- If yes, comparison is a single-point test, not a sweep — weak evidence for A7

#### DESIGN-3 — `all_users_data_labeled_actual_input.csv` projection now obsolete

- Created manually before schema normalization was added
- Schema normalization (`Ax_w → Ax`) now handles this automatically
- `actual_vs_synthetic_20260403.md` still references the projected file
- Future runs will use the original CSV; past report used projection — traceability gap

---

---

## 2026-04-18 — Pipeline Hardening (external review findings)

### Fixes Applied

#### FIX-1 — Validation hard-stop drops cleanup and audit persistence (HIGH) ✓ FIXED
- Stage loop wrapped in `try/finally` in `production_pipeline.py`. Cleanup always runs on `DataValidationError`.

#### FIX-2 — Stage 8 BREAK aborts calibration and later stages (HIGH) ✓ FIXED
- Both `return "BREAK"` in `_run_retraining` changed to `return "SKIP"`. Loop continues to Stage 11.
- Main loop now records skipped stages in `result.stages_skipped`.

#### FIX-3 — `--config` misleading scope (MEDIUM) ✓ FIXED
- Help text updated to state clearly it only applies to preprocessing settings.

#### FIX-4 — Hardcoded drift cutoffs in summary (MEDIUM) ✓ FIXED
- Summary now reads `status` from monitoring artifact (HEALTHY/WARNING/CRITICAL) instead of hardcoded 0.75/1.50 thresholds.

#### FIX-5 — MLflow always claims "run logged" (MEDIUM) ✓ FIXED
- `mlflow_tracked: bool` field added to `PipelineResult`. Compact summary reflects actual MLflow state.

#### FIX-6 — Fallback artifact loses `production_y_path` (MEDIUM) ✓ FIXED
- `_make_fallback_transformation_artifact` now checks for `production_y.npy` and sets `production_y_path` if found.

#### FIX-7 — Stage 11 outputs not persisted (MEDIUM) ✓ FIXED
- `_run_calibration` now saves `temperature.json`, `calibration_report.json`, `calibrated_probabilities.npy` via ArtifactsManager.

#### FIX-8 — TF version string comparison (LOW) ✓ FIXED
- Version parsed to `(major, minor)` int tuple before comparison.

#### FIX-9 — Duplicate label constants (LOW) ✓ FIXED
- `LABEL_COLUMN_CANDIDATES` / `NON_GROUND_TRUTH_COLUMNS` moved to `src/utils/label_detection.py`; both files import from there.

#### FIX-10 — Startup UX before parse_args (LOW) ✓ FIXED
- `parse_args()` moved to top of `main()` before banner and GPU detection.

#### FIX-11 — Worklog legend missing REMOVED/ACTIVE (LOW) ✓ FIXED
- REMOVED and ACTIVE added to status legend in WORKLOG.md.

#### FIX-12 — Worklog 2026-04-17 format violation (LOW) ✓ FIXED
- Compact scan block prepended to 2026-04-17 section before the late-night addendum.

---

### Summary Table

| Area | Status |
|---|---|
| Stage 1 ingestion mechanics | Correct |
| Stage 1 authoritative label fix | Correct |
| Stage 8 unlabeled gate | Correct |
| Schema normalization (`Ax_w → Ax`) | Correct |
| RUN SUMMARY `reused_existing` | BUG-1 — silent, never fires |
| Label awareness Stage 1 → Stage 5 | BUG-2 — thesis-critical, labels ignored in evaluation |
| Duplicate constants | BUG-3 — tech debt |
| `hand_tapping` dominance analysis | GAP-1 — thesis-critical, not investigated |
| Drift 1.04 on real data | GAP-2 — most interesting result, under-documented |
| `goto_cleanup` pattern | DESIGN-1 — fragile, should be `break` |
| Window count sweep coverage | DESIGN-2 — single-point, not a sweep |
| Projection file obsolescence | DESIGN-3 — traceability gap |

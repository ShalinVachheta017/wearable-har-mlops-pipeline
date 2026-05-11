# Master Thesis Finish Board — May–June 2026

*Last updated: 2026-05-11. Replaces older mixed historical/planning versions.*

---

## 1. Current Freeze State

```text
Model A  = defended clean proof-of-concept runtime candidate (FROZEN — do not retrain or change contract)
Model B  = legacy/mentor diagnostic reference only (not a defended runtime)
Model C  = previous baseline / checkpoint-contract mismatch evidence (retained as proof, not used)

auto_retrain = false (governance policy, not a bug)
Scaler       = Garmin train-only StandardScaler, persisted and SHA-256 verified
Pipeline     = Stage 1–7 governed pipeline path verified through committed evidence runs and ABC runtime evidence; Stage 1+2 validation gates operate as designed (hard-stop on bad data)

No model improvement until docs/evidence/thesis sync are complete.
Model A improvement is P2 / future work.
```

---

## 2. Completed Since May 8

```text
✓ Test suite fixed: 240/240 green (from 370 / 2 failing)
✓ Test suite cleaned: 370 → 240 tests, 34 → 23 files. Pyramid 200/23/17.
✓ .dockerignore hardened
✓ cd.yml deleted; workflows README rewritten as CI-only
✓ Dockerfile.inference: tensorflow-cpu pin + requirements split → 4.52 GB → 2.63 GB (-42 %)
✓ Stage 1–7 dry run on Model A (5/7 stages; Stage 1+2 correctly gated)
✓ Model A batch/API parity verified: 100 % agreement, 1.9e-6 max abs diff on User 7
✓ LEGACY_PRETRAINED_MODEL gated in src/config.py via EXCLUDED_UNDOCUMENTED_PROVENANCE
✓ KS / PSI / MMD / z-score drift audit complete
✓ reports/THESIS_QA_REFERENCE_2026_05_08.md created
✓ reports/FINAL_RUNTIME_RUN_SUMMARY_2026-05-09.md created
✓ ABC model-contract comparison runner: hardened, re-run, evidence committed
✓ ABC evaluation: all_users diagnostic + User 7 labeled + Garmin unlabeled — all three datasets
✓ ABC model registry: model_a / model_b / model_c contract JSONs created and committed
✓ Model A scaler JSON/joblib parity verified: 0.0 absolute diff
✓ docs/MODEL_ABC_MENTOR_BRIEF_2026-05.md — written (commit if not yet done)
✓ docs/MODEL_DECISION_2026-05.md — exists (verify still matches current state)
✓ docs/MASTER_THESIS_FINISH_TODO_MAY_JUNE_2026.md — this rewrite
```

---

## 3. P0 — Must Finish Before Defense

These are blocking. Without them, defense confidence is weak.

---

### P0-01 — Commit Mentor Brief

```text
git add docs/MODEL_ABC_MENTOR_BRIEF_2026-05.md
git commit -m "docs: add ABC mentor brief"
```

Status: pending commit check — if not yet committed, do immediately.

---

### P0-02 — Verify Final Model Decision Doc

File: `docs/MODEL_DECISION_2026-05.md`

Must state clearly:

```text
Model A = clean proof-of-concept runtime candidate
Model B = diagnostic reference only
Model C = checkpoint-contract mismatch baseline
Scaler  = Garmin train-only StandardScaler, persisted, SHA-256 verified
auto_retrain = false
```

Check that the wording matches current `src/config.py` and the mentor brief.
Replace any "production-grade" / "deployable" language.

Time: 1 hour.

---

### P0-03 — Evidence Pack Index (60–70 % done)

Two artifact runs already exist:

```text
artifacts/20260508_235323/              — unlabeled Garmin, 1304 windows, confidence 0.393, REVIEW
artifacts/20260508_235356/              — User 7 labeled, 989 windows, accuracy 0.376, REVIEW
reports/abc_comparison/                 — full ABC comparison evidence (6 files + model_a/b/c subdirs)
docs/MODEL_ABC_MENTOR_BRIEF_2026-05.md — mentor-facing decision summary
docs/MODEL_DECISION_2026-05.md         — final runtime contract decision
```

Remaining work: curate into one index and map to thesis claims.

Create:

```text
docs/EVIDENCE_KIT_INDEX_2026-05.md
```

Structure:

```text
| Evidence file | What it shows | Thesis chapter | Defense slide |
```

Include: ABC results CSV, monitoring JSON, trigger JSON, User 7 eval, Garmin unlabeled run.

Time: 3–4 hours.

---

### P0-04 — Create Claim-to-Evidence Register

Create:

```text
docs/FINAL_THESIS_CLAIMS_2026-06.md
```

Structure:

| Claim | Evidence file | Thesis chapter | Defense slide |
| --- | --- | --- | --- |
| Stage 1–7 pipeline runs end-to-end | artifact run logs | Ch5 | Slide 5 |
| Runtime contract is fixed and verified | model_a_clean_contract.json, MODEL_DECISION_2026-05.md | Ch5/Ch7 | Slide 6 |
| Monitoring detects drift and uncertainty | monitoring_report.json, abc_results.json | Ch6 | Slide 10 |
| Trigger blocks unsafe retraining | trigger_decision.json | Ch6/Ch8 | Slide 11 |
| Domain shift shown by external evaluation | User 7 labeled run, MODEL_ABC_MENTOR_BRIEF | Ch7 | Slide 12 |
| Contract mismatch proof | Model C result in abc_results.csv | Ch5 | Slide 7 |
| No automatic retraining was triggered | comparison_summary.json auto_retrain=false | Ch6/Ch8 | Slide 13 |

Time: 2–3 hours.

---

### P0-05 — Sync Thesis Chapters with May Findings

Chapters to update:

```text
ch4_data_model_development.tex
ch5_pipeline_implementation.tex
ch6_monitoring_drift_retraining.tex
ch7_experiments_evaluation.tex
ch8_discussion_conclusion.tex
```

Key points to add or update:

```text
1. Final runtime is Model A — clean proof-of-concept runtime candidate, not production-grade
2. Scaler policy: train-only, persisted, SHA-256 verified
3. auto_retrain=false governance policy
4. Drift formula correction and z-score false alarm story
5. Self-recorded Garmin evaluation (User 7, single participant)
6. Low accuracy = domain shift evidence, not pipeline failure
7. ABC model-contract comparison — Model C proves contract matters more than checkpoint
8. Why no automatic retraining was triggered
9. Stage 8–11 as optional/gated extensions, not required for thesis defense
```

Do not write new claims. Only align text with current code, evidence, and ABC results.

Time: 14–20 hours.

---

### P0-06 — Rebuild Thesis PDF

Fix LaTeX path first if needed (`pdflatex` not on PATH), then rebuild:

```text
thesis/build_thesis.ps1
```

Check:

```text
no undefined references
no blank sections
figures and tables visible
ToC / LoF / LoT updated
main.pdf date is current
```

Time: 3–5 hours.

---

### P0-07 — Update Defense Q&A

File: `internal/writing/defense_qa.md`

Update for:

```text
Runtime contract (Model A, clean PoC)
Scaler policy (train-only, persisted)
ABC comparison and why Model A was chosen
Monitoring and trigger behavior
auto_retrain=false governance
Self-recorded Garmin evaluation (what it proves and what it does not)
Domain shift / low accuracy explanation
Limitations
```

Time: 3–4 hours.

---

### P0-08 — Build Defense Slides

Target: 15–20 slides.

| Slide | Topic |
| ---: | --- |
| 1 | Title |
| 2 | Problem statement and research questions |
| 3 | Why MLOps for wearable HAR |
| 4 | Full pipeline overview (Stage 1–11) |
| 5 | Stage 1–7 operational path |
| 6 | Stage 8–11 gated extensions |
| 7 | Dataset and 11 classes |
| 8 | Final runtime/model contract |
| 9 | Model architecture |
| 10 | ABC comparison — one slide |
| 11 | Main evaluation results |
| 12 | Monitoring and drift behavior |
| 13 | Trigger governance — REVIEW, no auto-retrain |
| 14 | External Garmin evaluation |
| 15 | What low accuracy means (domain shift, honest pipeline) |
| 16 | Limitations |
| 17 | Future work |
| 18 | Contribution summary |
| 19–20 | Backup Q&A slides |

Time: 10–14 hours.

---

### P0-09 — Create Demo Runbook

Create: `thesis/defense_demo_runbook.md`

Include:

```text
exact commands (python run_pipeline.py, docker compose, curl)
expected output at each stage
where evidence is saved
what to say if demo is slow or fails
what not to claim
```

Time: 4–6 hours.

---

### P0-10 — Repo Cleanup Wave

Do **not** start before P0-03 (evidence index) is complete.

Archive candidates (move to `_archive/`, do not delete):

```text
Root noise: analyze_alluser_transitions.py, analyze_predictions.py, analyze_user7_timestamps.py
Root noise: COMPARATIVE_ANALYSIS_2026-05-08.md, temp.txt, reasoningtxt.txt, pt.md
Root noise: stage1_7_run_20260508_213835.log, tmp_run3/
Root noise: dataset_comparison_analysis.ipynb
docs/: old April planning docs (DRIFT_INVESTIGATION, COMPONENT_IMPROVEMENT_REVIEW, etc.)
reports/: _smoke_29_*.csv, _tmp_*.csv, P0-06_* older sprint reports
6th may/ folder — archive after ABC evidence is committed
old notebooks: nb/processing.ipynb, nb/gpt.ipynb
```

Do not delete `docs/MODEL_ABC_COMPARISON_2026-05.md` yet — check if any thesis chapter cites it first.

Time: 6–10 hours.

---

## 4. P1 — Important Quality Tasks

Not all defense-blocking, but they significantly improve quality.

### P1-01 — DVC Audit and Clarification

Write clearly what DVC is used for in this thesis. Minimum acceptable:

```text
DVC is used for artifact and data versioning.
Pipeline orchestration is handled by run_pipeline.py.
dvc repro is not configured for the full pipeline in this thesis version.
```

Or add a minimal `dvc.yaml` for stages 1–7.

Time: 2–4 hours.

### P1-02 — Threshold and Trigger Justification

Document the monitoring thresholds in one place (they are already in `config/pipeline_overrides.yaml`).

Write a short thesis paragraph explaining:

```text
Why confidence_warn=0.70
Why uncertain_pct=20%
Why dominant_class_warn=85%
Why these thresholds are not calibrated, they are conservative defaults
```

Note: threshold parity with full pipeline still needs manual review.

Time: 2–3 hours.

### P1-03 — Single Canonical Class Mapping Source

Ensure `src/utils/label_mapping.py` is the only source of truth.
Remove or deprecate silent overrides from `data/prepared/config.json`.

Time: 2–3 hours.

### P1-04 — Chapter 4 Data Tables

Add tables for: participants, sessions, class distribution, train/val/test split, self-recorded Garmin session.
Add limitation sentence: "This evaluation supports baseline operational analysis but is not population-level generalization evidence."

Time: 3–5 hours.

### P1-05 — Bibliography Cleanup

Target: 55–65 strong references. Remove padding entries. Prioritize MLOps, HAR, wearable sensors, domain shift, monitoring, calibration.

Time: 5–8 hours.

### P1-06 — Chapter 2 Related-Work Synthesis Table

| Area | What literature says | Gap | Thesis response |
| --- | --- | --- | --- |
| Wearable HAR | Models work under controlled data | Domain shift remains | External Garmin evaluation |
| MLOps | Lifecycle needs monitoring/versioning | Few offline thesis pipelines | 11-stage offline-first pipeline |
| Drift monitoring | Production data changes | Labels often unavailable | Warning + review-gated trigger |
| Retraining | Can improve model | Unsafe without labels | auto_retrain=false |

Time: 4–6 hours.

### P1-07 — Stage 11 Calibration Wording

Recommended framing: calibration is implemented as an optional uncertainty extension but final fitted calibration is left as future work because available labeled external data are insufficient for reliable post-hoc calibration.

Time: 1–2 hours.

### P1-08 — Gyroscope Validation Policy

Document: high angular velocity values (900–1000 deg/s) are treated as warning-level anomalies, not automatic errors, because fast wrist motion can produce high readings. Log for review.

Time: 1–2 hours.

### P1-09 — CI Smoke Workflow

Drop the `-m "not slow and not integration"` filter from CI unit-tests job so all 240 tests run.
Deferred until test cleanup is settled.

Time: 2–3 hours.

### P1-10 — Ingestion Ordering Hygiene

Verify that dataset/session selection is based on filename or session timestamp, not file modified time.
File modified time can change accidentally and cause the wrong session to be loaded.
If not fixed before defense, document the current behavior and avoid automatic latest-file selection in the demo runbook.

Time: 1–2 hours.

---

## 5. P2 — Optional / Future Work

Do not start these until P0 and main P1 tasks are safe.

- Model A improvement: calibration, higher-capacity variant, weak-class retune
- Stage 8–10 retraining demo with labeled data
- Stage 11 calibration/UQ finalization
- Optional model comparison sweep (CNN-GAP, CNN-GRU)
- Notebook hygiene: mark canonical, archive old

---

## 6. Archive / No Longer Defended

```text
docs/MODEL_ABC_COMPARISON_2026-05.md  — superseded by mentor brief + abc_comparison reports
                                        keep until no thesis chapter cites it, then archive
old "production-grade" / "deployable" wording anywhere in docs
May 9/10 calendar items — completed or superseded
"Use Model B if production-safe" framing — resolved: Model B is diagnostic reference only
```

---

## 7. Do Not Touch

```text
reports/abc_comparison/            — all evidence files, committed
models/model_registry/             — 3 contract JSONs
models/production_contract/model_a_final_20260508/  — frozen model package
src/config.py                      — Model A runtime config
tests/                             — 240 passing tests
```

No retraining. No contract changes until defense is over.

**Protected unless audited** (P1-02 may inspect but not change values without documenting the audit):

```text
config/pipeline_config.yaml        — runtime config
config/pipeline_overrides.yaml     — monitoring thresholds (threshold parity still needs manual review)
```

---

## 8. Final May–June Calendar

### May 11–12 (this week)

```text
✓ Commit mentor brief
✓ Verify MODEL_DECISION_2026-05.md wording
Start EVIDENCE_KIT_INDEX_2026-05.md
Start FINAL_THESIS_CLAIMS_2026-06.md
```

### May 13–17

```text
Finish evidence kit index and claim register
Begin Ch5 and Ch7 thesis updates (parity paragraph and domain-shift paragraph already drafted)
Begin Ch4 data tables
```

### May 18–24

```text
Finish Ch4/5/6 updates
Start Ch7/8 updates
First PDF build attempt
Bibliography cleanup
Begin slide deck
```

### May 25–31

```text
Finish Ch7/8 and full PDF build
Slides final draft
Demo runbook
Repo cleanup wave
Mock defense 1
```

### June

```text
Final PDF polish
Slides polish
Demo rehearsal
Supervisor feedback fixes
Submission formatting
```

Do not change the model story or evidence in June unless supervisor explicitly requires it.

---

## 9. Final Defense Story

> The thesis does not claim a perfect or universally generalizable HAR model. It contributes an offline-first MLOps pipeline for wearable IMU-based human activity recognition, where ingestion, validation, transformation, inference, monitoring, and trigger evaluation are reproducible and governed. The self-recorded Garmin evaluation exposed domain shift, and the pipeline correctly avoided unsafe automatic retraining from weak or unlabeled evidence.

---

## 10. Definition of Done

```text
pytest is green (currently 240/240)
fresh thesis PDF builds from source
one final model contract is stated everywhere
Model A is identified as defended proof-of-concept runtime candidate in code, thesis, slides, and demo
evidence kit index maps each artifact to a thesis claim
self-recorded Garmin evaluation is honestly explained as a single-participant external test
slides answer the main examiner questions
demo runbook works from clean shell
stale docs are archived or marked historical
README, thesis, slides, and defense Q&A tell the same story
```

> By end of May, the thesis should be technically frozen. June is writing polish, supervisor feedback, slides, and rehearsal only.

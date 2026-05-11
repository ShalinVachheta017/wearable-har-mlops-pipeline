# Evidence Kit Index — May 2026

*Created: 2026-05-11. Maps all committed evidence files to thesis claims and defense slides.*
*Do not move or delete any file listed in Section 9 before the defense.*

---

## 1. Purpose

This document is the single reference for what evidence exists, what each file proves, and which thesis chapter and defense slide it supports. It makes repo cleanup safe by identifying which files are protected evidence and which are noise.

---

## 2. Current Defended Runtime Story

```text
Model A  = defended clean proof-of-concept runtime candidate (FROZEN)
Model B  = legacy/mentor diagnostic reference only
Model C  = checkpoint-contract mismatch evidence (proves preprocessing contract matters)
Pipeline = Stage 1–7, REVIEW-gated trigger, auto_retrain=false
```

The pipeline is not broken. Monitoring correctly routes low-confidence and uncertain sessions to REVIEW without triggering automatic retraining. Low accuracy on User 7 is domain shift, not pipeline failure.

---

## 3. Evidence Map

| Evidence file/folder | What it proves | Thesis chapter | Defense slide | Status |
| --- | --- | --- | --- | --- |
| `reports/abc_comparison/abc_results.csv` | 9-row accuracy/F1/confidence/trigger summary for all 3 models × 3 datasets | Ch7 | 10 | committed |
| `reports/abc_comparison/abc_results.json` | Full metrics: per-class precision/recall/F1, confusion matrices, runtime environment | Ch7 | 10 | committed |
| `reports/abc_comparison/comparison_summary.json` | Decision summary; scaler JSON/joblib parity = 0.0 | Ch5/Ch7 | 6, 10 | committed |
| `reports/abc_comparison/contract_runtime_verification.json` | SHA-256 artefact verification, fresh model load, runner commit | Ch5 | 6 | committed |
| `reports/abc_comparison/dataset_validation_summary.json` | Dataset row/window counts, unit detection, timestamp validation | Ch4/Ch5 | 7 | committed |
| `reports/abc_comparison/ABC_MODEL_COMPARISON_REPORT_2026-05-11.md` | Full narrative comparison report | Ch7 | — | committed |
| `reports/abc_comparison/model_a/` | Per-dataset summaries for Model A (all_users, user7, garmin) | Ch7 | 10 | committed |
| `reports/abc_comparison/model_b/` | Per-dataset summaries for Model B (forensic reference) | Ch7 | 10 | committed |
| `reports/abc_comparison/model_c/` | Per-dataset summaries for Model C (mismatch evidence) | Ch7 | 10 | committed |
| `docs/MODEL_ABC_MENTOR_BRIEF_2026-05.md` | Mentor-readable decision brief; ABC tables and decision blocks | Ch7 | 10 | committed |
| `artifacts/20260508_235323/run_info.json` | Stage 1–7 all SUCCESS on Garmin unlabeled (130,500 rows, 1,304 windows, 50 Hz, unit conversion applied) | Ch5 | 5 | committed |
| `artifacts/20260508_235323/monitoring/monitoring_report.json` | Monitoring output: confidence CRITICAL, drift HEALTHY, temporal HEALTHY | Ch6 | 12 | committed |
| `artifacts/20260508_235323/trigger/trigger_decision.json` | Trigger: should\_retrain=false, action=review, alert\_level=CRITICAL, 4 reasons | Ch6/Ch8 | 13 | committed |
| `artifacts/20260508_235323/evaluation/evaluation_summary.json` | Unlabeled run evaluation: mean\_confidence=0.393, 1,304 predictions | Ch7 | 14 | committed |
| `artifacts/20260508_235356/run_info.json` | Stage 1–7 all SUCCESS on User 7 labeled (99,017 rows, 989 windows, 50 Hz, no unit conversion) | Ch5 | 5 | committed |
| `artifacts/20260508_235356/monitoring/monitoring_report.json` | Monitoring output: confidence CRITICAL, drift HEALTHY, temporal HEALTHY | Ch6 | 12 | committed |
| `artifacts/20260508_235356/trigger/trigger_decision.json` | Trigger: should\_retrain=false, action=review, alert\_level=CRITICAL, 4 reasons | Ch6/Ch8 | 13 | committed |
| `artifacts/20260508_235356/evaluation/evaluation_summary.json` | User 7 evaluation: mean\_confidence=0.359, accuracy ~37.6%, 989 windows with labels | Ch7 | 14 | committed |
| `models/production_contract/model_a_final_20260508/model_contract.json` | Window contract: 200 samples / 4 s / 50% overlap, row\_wise=true, legacy\_reshape=false | Ch5 | 8 | frozen |
| `models/production_contract/model_a_final_20260508/garmin_train_scaler.json` | Persisted scaler constants (mean, scale) for [Ax, Ay, Az, Gx, Gy, Gz]; fit 2026-05-08 | Ch5 | 8 | frozen |
| `models/production_contract/model_a_final_20260508/garmin_train_scaler.joblib` | Joblib copy of above; JSON/joblib parity = 0.0 absolute diff | Ch5 | 8 | frozen |
| `models/production_contract/model_a_final_20260508/label_order.json` | Fixed 11-class label order (SHA-256 verified) | Ch5 | 8 | frozen |
| `models/production_contract/model_a_final_20260508/metrics_summary.json` | Model A selection metrics: Garmin val macro F1=0.3101, User 7 F1=0.3397, 5,023 train windows | Ch4/Ch7 | 9 | frozen |
| `models/production_contract/model_a_final_20260508/garmin_train_scaled_baseline.json` | Monitoring baseline for drift detection (SHA-256 verified) | Ch6 | 12 | frozen |
| `models/model_registry/model_a_clean_contract.json` | Full Model A contract specification: preprocessing order, risk flags, evaluation protocol | Ch5 | 8 | committed |
| `models/model_registry/model_b_legacy_contract.json` | Model B risk flags: fresh\_scaler\_fit\_risk=true, double\_scaling\_risk=possible | Ch5/Ch7 | 10 | committed |
| `models/model_registry/model_c_previous_pipeline_contract.json` | Model C contract: checkpoint-contract mismatch risk documented | Ch5/Ch7 | 10 | committed |
| `docs/MODEL_DECISION_2026-05.md` | Final model decision with rationale, ABC confirmation, and contract statement | Ch5/Ch7 | 6 | committed |
| `reports/FINAL_RUNTIME_RUN_SUMMARY_2026-05-09.md` | Narrative summary of Garmin unlabeled and User 7 runs | Ch7 | 14 | committed |
| `reports/THESIS_QA_REFERENCE_2026_05_08.md` | Threshold table, drift method map, state-machine logic for Q&A prep | Ch6 | backup | committed |
| `src/config.py` | DEFAULT\_MODEL\_PATH = FINAL\_MODEL\_A\_PATH; LEGACY model gated via EXCLUDED\_UNDOCUMENTED\_PROVENANCE | Ch5 | 8 | do not touch |

---

## 4. ABC Comparison Evidence — Key Numbers

From `reports/abc_comparison/abc_results.csv` and `abc_results.json`:

| Model | all\_users accuracy | User 7 accuracy | Garmin classes used | Trigger |
| --- | ---: | ---: | ---: | --- |
| **A — Clean PoC** | 42.4% | 37.6% | 10 / 11 | REVIEW |
| **B — Diagnostic ref** | 90.8% | 43.8% | 11 / 11 | REVIEW (all\_users: NO\_ACTION) |
| **C — Mismatch proof** | 10.6% | 7.6% | 6 / 11 | REVIEW |

Key fact for thesis: Model B's 47 pp internal-to-external gap (90.8% → 43.8%) is consistent with its non-persisted, full-evaluation-dataframe scaler not transferring outside its native diagnostic context.

---

## 5. Stage 1–7 Runtime Evidence — Key Numbers

From `artifacts/20260508_235323/` and `artifacts/20260508_235356/run_info.json`:

| Run | Data | Windows | mean\_confidence | monitoring\_status | trigger\_action | should\_retrain |
| --- | --- | --- | ---: | --- | --- | --- |
| 20260508\_235323 | Garmin unlabeled | 1,304 | 0.393 | CRITICAL | review | false |
| 20260508\_235356 | User 7 labeled | 989 | 0.359 | CRITICAL | review | false |

**Important:** `alert_level=CRITICAL` is the monitoring severity (confidence below threshold), not the retraining decision. The trigger policy correctly blocks retraining even at CRITICAL. `action=review` and `should_retrain=false` are the governance outcome. This distinction must be clear in the thesis.

Both runs: drift\_status=HEALTHY, temporal\_status=HEALTHY. Monitoring routed correctly.

---

## 6. Model Contract Evidence — Frozen Package

Package: `models/production_contract/model_a_final_20260508/`

```text
fine_tuned_clean_model.keras    — frozen model, SHA-256 verified
garmin_train_scaler.json        — scaler mean/scale constants, created 2026-05-08
garmin_train_scaler.joblib      — joblib copy, parity = 0.0 absolute diff with JSON
label_order.json                — 11-class fixed order, SHA-256 verified
model_contract.json             — window=200/50%/50Hz, row_wise=true, legacy_reshape=false
metrics_summary.json            — Garmin val macro F1=0.3101, User 7 F1=0.3397
garmin_train_scaled_baseline.json — monitoring baseline, SHA-256 verified
training_report.md              — training narrative
abc_model_comparison.csv        — older sprint comparison (superseded by reports/abc_comparison/)
```

---

## 7. Monitoring and Trigger Evidence

Both artifact runs show the same governance pattern:

```text
monitoring_status  = CRITICAL    (confidence below warn threshold)
drift_status       = HEALTHY     (feature distribution within baseline)
temporal_status    = HEALTHY     (transition rate normal)
trigger_action     = review      (REVIEW, not retrain)
should_retrain     = false       (governance policy holds)
auto_retrain       = false       (config policy)
n_reasons          = 4           (four monitoring signals contributed)
```

This is the thesis MLOps governance story: the pipeline detects uncertainty, classifies its severity, and routes it to human review without triggering automatic retraining.

Files:
- `artifacts/20260508_235323/monitoring/monitoring_report.json`
- `artifacts/20260508_235323/trigger/trigger_decision.json`
- `artifacts/20260508_235356/monitoring/monitoring_report.json`
- `artifacts/20260508_235356/trigger/trigger_decision.json`

---

## 8. Dataset Validation Evidence

From `reports/abc_comparison/dataset_validation_summary.json`:

```text
User 7 external labeled:  99,017 rows, 989 windows, timestamps monotonic, no duplicates, unit=m/s²
Garmin unlabeled:         130,500 rows, 1,304 windows, unit=milliG (converted), timestamps valid
all_users diagnostic:     385,326 rows, 3,852 windows, unit=m/s²
Mixed-label windows:      2.02% (User 7), 3.35% (all_users) — negligible, not cause of low accuracy
```

---

## 9. Files Not to Move During Cleanup

These files are primary evidence. Do not move, rename, or delete them before the defense.

```text
reports/abc_comparison/             — all files and subdirs
models/production_contract/model_a_final_20260508/  — entire package
models/model_registry/              — all three contract JSONs
artifacts/20260508_235323/          — all stage output subdirs and run_info.json
artifacts/20260508_235356/          — all stage output subdirs and run_info.json
docs/MODEL_ABC_MENTOR_BRIEF_2026-05.md
docs/MODEL_DECISION_2026-05.md
docs/EVIDENCE_KIT_INDEX_2026-05.md  (this file)
reports/FINAL_RUNTIME_RUN_SUMMARY_2026-05-09.md
reports/THESIS_QA_REFERENCE_2026_05_08.md
src/config.py
```

---

## 10. Gaps Still Open

```text
GAP-01: No canonical evidence/defense_run_2026_06/ folder yet.
        The two artifact runs above are the evidence; they need a README map to be
        navigable during defense. (P0-03 partial — index exists, README still needed)

GAP-02: Claim-to-evidence register not yet created.
        docs/FINAL_THESIS_CLAIMS_2026-06.md maps claims → files → chapters → slides.
        Required before thesis chapter updates. (P0-04)

GAP-03: Thesis chapters not yet updated with May findings.
        MODEL_ABC_MENTOR_BRIEF and MODEL_DECISION changes must be reflected in
        ch4/ch5/ch6/ch7/ch8. (P0-05)

GAP-04: Thesis PDF not yet rebuilt.
        Last build: 2026-04-27. Needs Ch4–Ch8 updates first. (P0-06)

GAP-05: monitoring_status=CRITICAL vs trigger_action=review distinction
        must be clearly explained in Ch6 and defense Q&A to avoid examiner confusion.

GAP-06: Stage 1 and Stage 2 individual evidence files (ingestion log, validation report)
        exist inside artifact subdirs but have not been mapped or curated individually.
        Lower priority — run_info.json covers the stage outcome summary.
```

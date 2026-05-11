# Final Thesis Claims — June 2026

*Created: 2026-05-11. Source map: `docs/EVIDENCE_KIT_INDEX_2026-05.md`.*
*Use this register when writing thesis chapters and building defense slides.*
*Each claim must trace to at least one committed evidence file.*

---

## Claim Register

| ID | Thesis claim | Evidence file(s) | Chapter | Slide | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| C-01 | Stage 1–7 pipeline runs end-to-end on a real unlabeled Garmin session | `artifacts/20260508_235323/run_info.json` | Ch5 | 5 | verified | All 7 stages SUCCESS; 130,500 rows, 1,304 windows, 50 Hz |
| C-02 | Stage 1–7 pipeline runs end-to-end on a real labeled User 7 session | `artifacts/20260508_235356/run_info.json` | Ch5 | 5 | verified | All 7 stages SUCCESS; 99,017 rows, 989 windows, 50 Hz |
| C-03 | Model A is the defended clean proof-of-concept runtime candidate | `docs/MODEL_DECISION_2026-05.md`, `docs/MODEL_ABC_MENTOR_BRIEF_2026-05.md` | Ch5/Ch7 | 6 | verified | Not production-grade; selected for clean reproducible contract |
| C-04 | Model A input contract is fixed: row-wise, 6 channels, 200 samples, 50% overlap, 50 Hz | `models/production_contract/model_a_final_20260508/model_contract.json` | Ch5 | 8 | verified | `row_wise_windows=true`, `legacy_mentor_reshape=false` |
| C-05 | Model A scaler is train-only, persisted, and SHA-256 verified | `models/production_contract/model_a_final_20260508/garmin_train_scaler.json`, `garmin_train_scaler.joblib` | Ch5 | 8 | verified | JSON/joblib parity = 0.0 absolute diff |
| C-06 | Model A and Model B/C share the same ADAMSense-pretrained CNN-BiLSTM base | `models/pretrained/model_info.json`, `6th may/anxiety1 - CNNBiLSTM.ipynb` | Ch4 | 9 | verified | B/C = 499,131 params; A = 87,083 params (5.7× smaller) |
| C-07 | API and batch prediction paths produce identical results on User 7 | `reports/FINAL_RUNTIME_RUN_SUMMARY_2026-05-09.md` | Ch5 | 8 | verified | 100% agreement, 1.9e-6 max abs diff, 989 windows |
| C-08 | Monitoring detects low confidence and high uncertainty on User 7 and Garmin runs | `artifacts/20260508_235323/monitoring/monitoring_report.json`, `artifacts/20260508_235356/monitoring/monitoring_report.json` | Ch6 | 12 | verified | confidence\_status=CRITICAL on both runs |
| C-09 | Drift remains HEALTHY in both final evidence runs | `artifacts/20260508_235323/monitoring/monitoring_report.json`, `artifacts/20260508_235356/monitoring/monitoring_report.json` | Ch6 | 12 | verified | drift\_status=HEALTHY, temporal\_status=HEALTHY |
| C-10 | Trigger routes to REVIEW and does not trigger automatic retraining | `artifacts/20260508_235323/trigger/trigger_decision.json`, `artifacts/20260508_235356/trigger/trigger_decision.json` | Ch6/Ch8 | 13 | verified | `should_retrain=false`, `action=review` on both runs |
| C-11 | CRITICAL monitoring severity does not mean automatic retraining — it means the severity is high and governance routes it to REVIEW | `artifacts/20260508_235323/trigger/trigger_decision.json` | Ch6 | 13 | verified | `alert_level=CRITICAL`, `should_retrain=false` — two separate fields |
| C-12 | auto\_retrain=false is a deliberate governance policy, not a limitation or missing feature | `src/config.py`, `reports/abc_comparison/comparison_summary.json` | Ch6/Ch8 | 13 | verified | Comparison\_summary confirms `auto_retrain_flag=false` for all models |
| C-13 | User 7 external evaluation shows weak cross-user generalisation (domain shift) | `artifacts/20260508_235356/evaluation/evaluation_summary.json`, `reports/abc_comparison/abc_results.json` | Ch7 | 14 | verified | accuracy=37.6%, macro F1=34.1%, mean\_confidence=0.359 |
| C-14 | Mixed-label window noise on User 7 is negligible (2.02%) and is not the cause of low accuracy | `reports/abc_comparison/dataset_validation_summary.json` | Ch7 | 15 | verified | 2.02% User 7; 3.35% all\_users |
| C-15 | Garmin unlabeled run demonstrates runtime-style monitoring and trigger behavior without ground-truth labels | `artifacts/20260508_235323/run_info.json`, `reports/abc_comparison/abc_results.json` | Ch7 | 14 | verified | 1,304 windows, mean\_confidence=0.393, trigger=REVIEW |
| C-16 | all\_users diagnostic is not primary evidence because it comes from the same data family used for training | `reports/abc_comparison/dataset_validation_summary.json` | Ch7 | 10 | verified | 385,326 rows from training population |
| C-17 | Model B's native setup does not transfer cleanly: 90.8% internal → 43.8% external (47 pp gap) | `reports/abc_comparison/abc_results.csv`, `abc_results.json` | Ch7 | 10 | verified | Non-persisted full-eval scaler and legacy native setup limit transferability |
| C-18 | Model C proves that a checkpoint alone is not enough — wrong preprocessing produces 7.6% accuracy on User 7 with 0.748 mean confidence | `reports/abc_comparison/abc_results.csv` | Ch5/Ch7 | 10 | verified | Same weights as Model B, no scaler, 4 of 11 classes used |
| C-19 | LEGACY\_PRETRAINED\_MODEL is structurally gated in runtime code and cannot be loaded by default | `src/config.py` | Ch5 | 8 | verified | `PRETRAINED_MODEL_STATUS["status"] = "EXCLUDED_UNDOCUMENTED_PROVENANCE"` |
| C-20 | The pipeline does not claim population-level generalisation, clinical diagnosis, or production-grade deployment | `docs/MODEL_ABC_MENTOR_BRIEF_2026-05.md` (Section 6 / Limitations), `models/model_registry/model_a_clean_contract.json` | Ch8 | 16 | to write | Must appear explicitly in Ch8 limitations and defense slide 16 |

---

## Claims Not to Make

These are overclaims that the evidence does not support. Do not write them.

```text
✗ "The pipeline achieves production-grade accuracy on wearable HAR data."
  (evidence shows 37.6% on User 7 — domain shift, not accuracy failure of the pipeline)

✗ "The pipeline generalizes across users."
  (only one external participant; training users are Garmin all_users 1–5, test is User 7 only)

✗ "Model B is broken or wrong."
  (Model B is a valid forensic reference; it scores 43.8% on User 7, which is comparable to Model A)

✗ "Automatic retraining is available as a live feature."
  (auto_retrain=false; retraining requires human review and labeled data)

✗ "Drift detection uses population-level statistical baselines."
  (baseline is Garmin training-set scaled statistics, not a multi-deployment baseline)

✗ "Calibration is finalized."
  (calibration is an optional extension; not fitted in the defended version)

✗ "The 47 pp generalization gap of Model B is caused by data leakage."
  (use: "non-persisted, full-evaluation scaler does not transfer outside native diagnostic context")
```

---

## Evidence Gaps Still Open

These claims are intended but not yet fully supported by committed evidence.

| Gap ID | Claim intended | What is missing | Priority |
| --- | --- | --- | --- |
| GAP-01 | "The evidence pack is navigable during defense" | `evidence/defense_run_2026_06/` README map not created | P0-03 partial |
| GAP-02 | "All thesis chapter claims trace to evidence" | `FINAL_THESIS_CLAIMS_2026-06.md` just created; chapters not yet updated | P0-05 |
| GAP-03 | "CRITICAL monitoring severity is explained clearly in the thesis" | GAP-05 from evidence index: Ch6 paragraph not written | P0-05 |
| GAP-04 | "Stage 8–11 are gated extensions, not runtime features" | Ch8 text not yet aligned | P0-05 |
| GAP-05 | "Calibration is scoped out as future work" | P1-07 wording not yet in thesis | P1-07 |

---

## Next Writing Targets

Use these claim IDs when updating each chapter:

### Chapter 4 — Data and Model Development

Write: C-06, C-16, and data table for User 7 session

### Chapter 5 — Pipeline Implementation

Write: C-01, C-02, C-03, C-04, C-05, C-07, C-18, C-19

### Chapter 6 — Monitoring, Drift, Retraining Governance

Write: C-08, C-09, C-10, C-11, C-12

### Chapter 7 — Experiments and Evaluation

Write: C-13, C-14, C-15, C-16, C-17, C-18

### Chapter 8 — Discussion and Limitations

Write: C-20, GAP-03 (CRITICAL vs REVIEW distinction), GAP-04 (Stage 8–11 as gated extensions)

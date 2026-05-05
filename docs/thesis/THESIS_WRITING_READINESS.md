# Thesis Defense Readiness Dashboard

Date checked: 2026-05-06

## Current Verdict

Status: defense-evidence ready for the self-recorded Garmin case study; manuscript integration still pending.

The repository now has a complete, thesis-safe evidence package for the self-recorded Garmin session:

- parser timestamp issue fixed,
- labels and transitions validated,
- accelerometer units corrected to m/s2,
- frozen model evaluated on included windows,
- distribution shift compared against training and mentor production data,
- review-gate retraining decision documented.

The correct conclusion is:

```text
Use the session as self-recorded external evaluation and domain-shift evidence.
Do not retrain from this single session.
```

## Defense Dashboard

| Area | Status | Evidence | Defense line |
|---|---|---|---|
| Runtime contract | PASS | `docs/THESIS_CONSISTENCY_NOTES.md`; `WORKLOG.md` 2026-05-05 | Final inference uses raw physical IMU units, 50 Hz, 200x6 windows, no scaler, no gravity removal, no calibration. |
| Parser and timestamp QA | PASS | `recording/labels/2026-05-05-15-11-15/LABELING_REPORT.md` | Corrected FIT parser restored the expected recording duration and window count. |
| Manual labels | PASS | `label_timeline.csv`; `2026-05-05-15-11-15_labeled_50Hz_user7_ms2.csv` | The session was manually labeled into official activity classes with transitions excluded. |
| Unit correction | PASS | `LABELING_REPORT.md`; `schema_unit_checks.json` | Accelerometer values were converted from milli-g to m/s2; gyroscope values stayed in deg/s. |
| External evaluation | PASS | `reports/self_recorded_eval_2026_05_05/EVALUATION_REPORT.md` | The frozen model performs poorly on this external user session, revealing limited generalization. |
| Distribution shift | PASS | `DISTRIBUTION_COMPARISON_REPORT.md`; `distribution_pair_summary.csv` | Self-recorded data is closest to training among compared datasets but still shifted in motion variability/range features. |
| Governance/retraining | PASS | `CLAIM_EVIDENCE_TABLE.md`; `RUN_SUMMARY.json` | Poor external performance triggers review and QA, not automatic retraining from one recording. |
| Thesis paragraph | READY | `THESIS_PARAGRAPH_SELF_RECORDED_EVAL.md` | Chapter 5/6/7 text is ready to integrate. |
| Claim-evidence table | READY | `CLAIM_EVIDENCE_TABLE.md` | Defense backup table links claims to artifacts. |

## Key Numbers To Defend

| Metric | Value |
|---|---:|
| Fused rows | 104,057 |
| Pipeline windows | 1,039 |
| Included evaluation windows | 977 |
| Excluded windows | 62 |
| Labeled 50 Hz rows | 99,017 |
| Accuracy | 0.0860 |
| Balanced accuracy | 0.0868 |
| Macro F1 | 0.0281 |
| Weighted F1 | 0.0278 |
| Training vs self mean KS | 0.2146 |
| Training vs self mean PSI | 0.3502 |
| Training vs self MMD | 0.0328 |

## Main Thesis Claim

The self-recorded session was closest to the original labeled training distribution among the compared production-style datasets, but performance remained weak, especially for activities whose motion variability differed from the training set. This supports treating new user data as external evaluation and gating retraining behind additional labeled sessions and QA rather than triggering automatic retraining from a single recording.

## What Is Already Sufficient

1. The defended runtime contract is now consistent across the worklog and report artifacts.
2. The self-recorded Garmin session has complete parser, labeling, unit, evaluation, distribution, and governance evidence.
3. The evaluation report contains the required metrics, confusion matrix links, prediction timeline, distribution context, and retraining verdict.
4. The claim-evidence table gives a compact oral-defense backup.
5. The result is framed as a bounded single-user external evaluation, not as proof of generalization for all users.

## Remaining Writing Work

1. Insert the self-recorded evaluation paragraph into the manuscript.
2. Add one figure/table block for:
   - confusion matrix,
   - prediction timeline,
   - distribution pair summary.
3. Make Chapter 7 wording explicit that this is external evaluation, not training data.
4. Make Chapter 8 wording explicit that retraining requires additional labeled sessions and a held-out self-recorded split.
5. Keep older notes about automatic retraining, normalization, or scaler-based production inference out of the final defended story unless they are described as superseded historical experiments.

## Immediate Next Writing Sequence

1. Open `reports/self_recorded_eval_2026_05_05/THESIS_PARAGRAPH_SELF_RECORDED_EVAL.md`.
2. Place the paragraph in the external evaluation/domain-shift results section.
3. Add `CLAIM_EVIDENCE_TABLE.md` as appendix or defense backup material.
4. Use `prediction_timeline_summary.csv` for the timeline table.
5. Cite `EVALUATION_REPORT.md` and `DISTRIBUTION_COMPARISON_REPORT.md` as the local evidence anchors.

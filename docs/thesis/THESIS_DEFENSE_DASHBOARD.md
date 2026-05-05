# Thesis Defense Dashboard

Date: 2026-05-06

## One-Line Defense Status

The self-recorded Garmin evaluation is ready to defend as external evaluation and domain-shift evidence; it does not justify retraining yet.

## Latest Evidence Package

| Package item | Path | Status |
|---|---|---|
| Thesis-ready evaluation report | `reports/self_recorded_eval_2026_05_05/EVALUATION_REPORT.md` | READY |
| Distribution comparison report | `reports/self_recorded_eval_2026_05_05/DISTRIBUTION_COMPARISON_REPORT.md` | READY |
| Prediction timeline summary | `reports/self_recorded_eval_2026_05_05/prediction_timeline_summary.csv` | READY |
| Thesis paragraph | `reports/self_recorded_eval_2026_05_05/THESIS_PARAGRAPH_SELF_RECORDED_EVAL.md` | READY |
| Claim-evidence table | `reports/self_recorded_eval_2026_05_05/CLAIM_EVIDENCE_TABLE.md` | READY |
| Labeling report | `recording/labels/2026-05-05-15-11-15/LABELING_REPORT.md` | READY |
| Corrected labeled CSV | `recording/labels/2026-05-05-15-11-15/2026-05-05-15-11-15_labeled_50Hz_user7_ms2.csv` | READY |

## Defense Questions And Short Answers

| Question | Answer |
|---|---|
| Did the parser problem remain? | No. Sample-level timestamp reconstruction restored the expected duration and `1,039` windows. |
| Was the label set valid? | Yes. Only official classes are used; `knuckle_cracking` was mapped to `knuckles_cracking`, and the mistaken `nail_rubbing` segment was corrected to `nape_rubbing`. |
| Were units correct? | Yes. The final evaluation file uses accelerometer m/s2 and gyroscope deg/s. |
| Did the model generalize to the self-recorded user? | Poorly. Balanced accuracy is `0.0868` and macro F1 is `0.0281` on `977` included windows. |
| Is this a pipeline failure? | No. Parser, labeling, unit, window-alignment, and frozen-contract checks pass. The result is a model generalization/domain-shift finding. |
| Is self-recorded data random or broken? | No. It is closest to training among compared datasets by mean KS, PSI, and MMD, but still shifted in motion dynamics. |
| Should Stage 8 retraining run now? | No. One labeled session is insufficient. Stage 7 review-gate governance is justified. |
| What is the next scientific step? | Collect multiple labeled self-recorded sessions over multiple days, keep a held-out split, and repeat unit/timestamp QA before retraining. |

## Slide Anchors

1. Parser and labeling QA:
   - `LABELING_REPORT.md`
   - row/window count table
2. Frozen evaluation:
   - `confusion_matrix.csv`
   - `plots/confusion_matrix.png`
   - `prediction_timeline_summary.csv`
3. Domain-shift analysis:
   - `distribution_pair_summary.csv`
   - `psi_ks_summary.csv`
   - `plots/pca_window_features.png`
4. Governance:
   - `CLAIM_EVIDENCE_TABLE.md`
   - final verdict in `EVALUATION_REPORT.md`

## Safe Thesis Wording

Use:

```text
self-recorded external evaluation
domain-shift analysis
review-gated retraining
conditional retraining would require more labeled data and QA
```

Avoid:

```text
the model is production-ready for all users
the single session proves retraining is needed
automatic retraining should run on this session
the self-recorded result proves all future users will fail
```

## Final Verdict

Parser fixed: yes.
Labeling fixed: yes.
Units fixed: yes.
Distribution comparison: useful and defensible.
Retraining now: no.
Next: integrate the thesis paragraph and claim-evidence table into Chapter 5/6/7 and defense slides.

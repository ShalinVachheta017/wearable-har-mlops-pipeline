# DEFENSE PLAN

## Timeline

- June 20 to June 25: slide draft + first demo rehearsal
- June 26 to June 28: mock defense and timing pass
- June 29 to June 30: final polish and backup demo recording

## Required Assets

- 12 to 15 slide deck
- One end-to-end pipeline demo script
- Evidence appendix with run IDs and key artifacts
- Self-recorded Garmin external-evaluation slide:
  - `reports/self_recorded_eval_2026_05_05/EVALUATION_REPORT.md`
  - `reports/self_recorded_eval_2026_05_05/plots/confusion_matrix.png`
  - `reports/self_recorded_eval_2026_05_05/plots/prediction_timeline.png`
  - `reports/self_recorded_eval_2026_05_05/distribution_pair_summary.csv`
- Claim-evidence backup:
  - `reports/self_recorded_eval_2026_05_05/CLAIM_EVIDENCE_TABLE.md`
  - `docs/thesis/THESIS_DEFENSE_DASHBOARD.md`

## Core Narrative

1. Problem and constraints (offline-first HAR MLOps)
2. Architecture and implementation choices
3. Monitoring and retraining integrity improvements
4. Experimental evidence and limitations
5. Conclusion and future work

## Current Self-Recorded Evaluation Narrative

Use this as a Chapter 5/6/7 defense example:

1. The Garmin FIT parser timestamp issue was fixed, restoring `104,057` fused rows and `1,039` windows.
2. The self-recorded session was manually labeled into official classes, with transitions excluded and `99,017` final labeled rows for `User = 7`.
3. Accelerometer values were corrected to m/s2; gyroscope values stayed in deg/s.
4. The frozen model performed poorly on `977` included external windows: accuracy `0.0860`, balanced accuracy `0.0868`, macro F1 `0.0281`, weighted F1 `0.0278`.
5. Distribution comparison shows self-recorded data is closest to training among the compared datasets, but still shifted in motion variability/range features.
6. This supports external evaluation and review-gated retraining, not immediate retraining from a single recording.

## Q&A Preparation Themes

- Why offline-first design?
- How drift is measured and validated
- How trigger policy avoids false retraining
- Reproducibility guarantees and remaining risks
- Why one self-recorded external session does not justify retraining
- Why weak external performance is a model generalization/domain-shift finding, not a parser or pipeline failure

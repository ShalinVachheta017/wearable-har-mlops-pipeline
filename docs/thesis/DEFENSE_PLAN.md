# DEFENSE PLAN

## Timeline

- June 20 to June 25: slide draft + first demo rehearsal
- June 26 to June 28: mock defense and timing pass
- June 29 to June 30: final polish and backup demo recording

## Required Assets

- 12 to 15 slide deck
- One end-to-end pipeline demo script
- Evidence appendix with run IDs and key artifacts
- User-7 blind external-evaluation slide (D1 contract):
  - `models/runtime_contract/model_d1_final_20260528/user7_blind_probe_summary.json`
  - `models/runtime_contract/model_d1_final_20260528/user7_unlabeled_probe_summary.json`
  - `thesis/figures/Figure_7_4_user7_confusion.png`
- Claim-evidence backup:
  - `docs/thesis/THESIS_DEFENSE_DASHBOARD.md`
  - `reports/TRIGGER_POLICY_EVAL.csv`, `reports/ABLATION_WINDOWING.csv`

## Core Narrative

1. Problem and constraints (offline-first HAR MLOps)
2. Architecture and implementation choices
3. Monitoring and retraining integrity improvements
4. Experimental evidence and limitations
5. Conclusion and future work

## Current User-7 Evaluation Narrative (D1 contract)

Use this as a Chapter 5/6/7 defense example:

1. The D1 runtime contract (`model_d1_final_20260528`) freezes the model, the
   train-only StandardScaler (users 1–6), the drift baseline, the label order,
   and the units (accel m/s², gyro deg/s).
2. User 7 was held out of training entirely and evaluated blind. The labeled
   session yields `989` windows under the contract's 200/100 windowing.
3. Blind performance: accuracy `36.96%`, macro F1 `0.350`, mean confidence
   `0.858`, bootstrap CI95 `[0.339, 0.398]` — a high-confidence-but-wrong
   failure mode, not a low-confidence abstention.
4. Within-distribution vs unseen-user contrast: 5-fold CV `93.61%` (optimistic)
   vs LOUO mean `44.42%` (the deployment-relevant unseen-user number).
5. Schedule-aligned (proxy) accuracy `36.70%` ≈ labeled `36.96%`, validating the
   unlabeled monitoring proxy.
6. This supports external evaluation and review-gated retraining, not immediate
   retraining from a single recording.

## Q&A Preparation Themes

- Why offline-first design?
- How drift is measured and validated
- How trigger policy avoids false retraining
- Reproducibility guarantees and remaining risks
- Why one self-recorded external session does not justify retraining
- Why weak external performance is a model generalization/domain-shift finding, not a parser or pipeline failure

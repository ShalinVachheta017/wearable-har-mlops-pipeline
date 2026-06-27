# Thesis Defense Dashboard

Date: 2026-06-27 (rewritten for the Model D1 runtime contract)

## One-Line Defense Status

The thesis is built on the **Model D1 runtime contract** (`model_d1_final_20260528`):
a train-only StandardScaler (users 1–6) 1D-CNN+BiLSTM, evaluated blind on User 7.
The User-7 result is presented as bounded external evaluation and domain-shift
evidence — it does not justify automatic retraining.

## Canonical Numbers To Defend

All values verified against the D1 contract artifacts and build-notebook result
files (do not re-quote pre-D1 numbers).

| Metric | Value | Source |
|---|---:|---|
| 5-fold CV accuracy (within-distribution) | 93.61% | `garmin_5fold_window_cv_results.json` |
| 5-fold CV macro F1 | 0.937 | same |
| LOUO mean accuracy (unseen user) | 44.42% | `garmin_louo_users_1_6_results.json` |
| LOUO mean macro F1 | 0.419 | same |
| Within-distribution validation accuracy | 94.41% | `model_contract.json` |
| User-7 blind accuracy | 36.96% | `user7_blind_probe_summary.json` |
| User-7 macro F1 | 0.350 | same |
| User-7 mean confidence | 0.858 | same |
| User-7 bootstrap CI95 | [0.339, 0.398] | same |
| User-7 unlabeled windows | 989 | `user7_unlabeled_probe_summary.json` |
| Schedule-aligned accuracy (proxy) | 36.70% | same |
| Total parameters | 967,499 | `model_param_count.json` |

## Runtime Contract (D1) — the deployment unit

| Property | Value |
|---|---|
| Contract folder | `models/runtime_contract/model_d1_final_20260528/` |
| Model | 1D-CNN + BiLSTM, ADAMSense pretrain (g→m/s²), Garmin users 1–6 final freeze |
| Input shape | 200 × 6 (window 200, stride 100, 50 Hz) |
| Units | accelerometer m/s², gyroscope deg/s |
| Scaler | **train-only StandardScaler fit on users 1–6** (`garmin_train_scaler.json`) |
| Drift baseline | `garmin_train_scaled_baseline.json` (scaled feature space) |
| User 7 | excluded from training; blind evaluation only |

## Latest Evidence Package

| Package item | Path | Status |
|---|---|---|
| D1 runtime contract | `models/runtime_contract/model_d1_final_20260528/` | READY |
| Build notebook (5-fold + LOUO) | `notebooks/model_HAR_27may_artifacts/` | READY |
| User-7 blind probe | `models/runtime_contract/model_d1_final_20260528/user7_blind_probe_summary.json` | READY |
| User-7 unlabeled / schedule-aligned probe | `models/runtime_contract/model_d1_final_20260528/user7_unlabeled_probe_summary.json` | READY |
| Labeled User-7 session | `data/labels/2026-05-05-15-11-15/` | READY |
| 25-session monitoring | `reports/unlabeled_sessions_monitoring.csv` | READY |
| Trigger-policy evaluation | `reports/TRIGGER_POLICY_EVAL.csv` | READY |
| Windowing/contract ablation | `reports/ABLATION_WINDOWING.csv` | READY |

## Defense Questions And Short Answers

| Question | Answer |
|---|---|
| What is the deployed model? | The D1 runtime contract, not a loose `.keras`. The contract pins model, scaler, baseline, label order, and units. |
| Within-distribution vs unseen user? | 5-fold CV 93.61% is within-distribution (optimistic). LOUO 44.42% is the deployment-relevant unseen-user number. |
| Did the model generalize to User 7? | Partially. Blind accuracy 36.96% (F1 0.350) at high confidence 0.858 — a high-confidence-but-wrong failure mode that the monitoring layer is designed to surface. |
| Is this a pipeline failure? | No. Contract, units, label order, and windowing all pass. It is a model generalization / domain-shift finding. |
| Should Stage 8 retraining run? | No. The governance gate requires labeled data + QA review; one session does not justify automatic retraining. |
| What is schedule-aligned accuracy? | The fraction of windows whose prediction matches the activity scheduled for that time interval (proxy ground truth from the recording protocol). 36.70% ≈ 36.96% labeled, validating the unlabeled monitoring proxy. |

## Safe Thesis Wording

Use:

```text
D1 runtime contract
train-only StandardScaler (users 1-6)
blind external evaluation on User 7
within-distribution 5-fold vs unseen-user LOUO
high-confidence-but-wrong failure mode
review-gated retraining
schedule-aligned proxy validation
```

Avoid:

```text
the model is production-ready for all users
raw physical units / no scaler   (this is the superseded Model-A contract, NOT D1)
the single session proves retraining is needed
automatic retraining should run on this session
```

## Final Verdict

D1 contract is the source of truth: yes.
5-fold 93.61% / LOUO 44.42% / User-7 36.96%: verified against artifacts.
Retraining now: no — review-gated by design.
Pre-D1 "no-scaler / 0.086 User-7" numbers: superseded; do not use.

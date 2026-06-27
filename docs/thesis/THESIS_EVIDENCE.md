# THESIS EVIDENCE

Track every thesis claim with a reproducible artifact (D1 runtime contract).

## Mapping Table

| Experiment | Artifact | Chapter | Notes |
|---|---|---|---|
| 5-fold within-distribution CV | `notebooks/model_HAR_27may_artifacts/garmin_5fold_window_cv_results.json` | Chapter 7 | mean 93.61%, F1 0.937 (optimistic; global scaler) |
| LOUO unseen-user generalization | `notebooks/model_HAR_27may_artifacts/garmin_louo_users_1_6_results.json` | Chapter 7 | mean 44.42%, F1 0.419 |
| User-7 blind evaluation | `models/runtime_contract/model_d1_final_20260528/user7_blind_probe_summary.json` | Chapter 7 | 36.96% / F1 0.350 / conf 0.858, CI [0.339, 0.398] |
| User-7 schedule-aligned proxy | `models/runtime_contract/model_d1_final_20260528/user7_unlabeled_probe_summary.json` | Chapter 7 | 989 windows; 36.70% proxy ≈ 36.96% labeled |
| Contract-sensitivity ablation | `reports/ABLATION_WINDOWING.csv` | Chapter 7 | RQ2: window/overlap → accuracy, F1, flip-rate |
| Trigger-policy evaluation | `reports/TRIGGER_POLICY_EVAL.csv` | Chapter 7 | RQ3: 2-of-3 voting precision 0.988 / FAR 0.007 vs single-signal 0.841 / 0.139 |
| 25-session monitoring decomposition | `reports/unlabeled_sessions_monitoring.csv` | Chapter 6/7 | 23 review / 1 monitor / 1 none; queue_retrain never fired |
| Threshold calibration | `reports/THRESHOLD_CALIBRATION.csv` | Chapter 6 | threshold provenance |
| Runtime contract definition | `models/runtime_contract/model_d1_final_20260528/model_contract.json` | Chapter 3/5 | model, scaler, baseline, label order, units |

## Defense Evidence Summary

| Claim | Primary artifact | Status |
|---|---|---|
| Deployment unit is the runtime contract | `model_contract.json` + `artifact_md5.json` | PASS |
| Train-only StandardScaler (users 1–6) | `garmin_train_scaler.json` | PASS |
| Label order parity (4-way) | `label_order.json` ↔ `src/config.py` ↔ `src/utils/label_mapping.py` ↔ `data/prepared/config.json` | PASS |
| Within-distribution learnability | `garmin_5fold_window_cv_results.json` | PASS |
| Unseen-user generalization limit | `garmin_louo_users_1_6_results.json` | PASS |
| High-confidence-but-wrong User-7 failure | `user7_blind_probe_summary.json` | PASS |
| Schedule-aligned proxy validates monitoring | `user7_unlabeled_probe_summary.json` | PASS |
| Governed trigger beats naive single-signal | `reports/TRIGGER_POLICY_EVAL.csv` | PASS |
| No auto-mutation on real data | `reports/unlabeled_sessions_monitoring.csv` (should_retrain=False ×25) | PASS |

> Superseded: the pre-D1 `self_recorded_eval_2026_05_05/*` evidence tree and the
> Wave 1/2/3 audit reports described an earlier Model-A (raw-units/no-scaler)
> contract with a 0.086 User-7 result. They are historical and must not be
> quoted for the D1 story.

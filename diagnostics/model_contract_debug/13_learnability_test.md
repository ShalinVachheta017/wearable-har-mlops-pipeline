# 13 Baseline Learnability Test

These models are diagnostic-only and are not saved or used for production inference.

| test | n_train | n_eval | accuracy | macro F1 |
| --- | --- | --- | --- | --- |
| RandomForest summary features user_group_val_user5 | 2265 | 585 | 0.4461538461538462 | 0.35972799676561246 |
| RandomForest summary features user_group_test_user6 | 2265 | 599 | 0.5759599332220368 | 0.5830945924071022 |
| RandomForest train users1-4 -> User7 summary features | 2265 | 768 | 0.3489583333333333 | 0.31257562401058636 |
| RandomForest flattened tiny overfit same 300 windows | 300 | 300 | 1.0 | 1.0 |
| LogisticRegression flattened tiny overfit same 300 windows | 300 | 300 | 1.0 | 1.0 |

Interpretation: successful tiny overfit means the regenerated labels/features are internally learnable; failure of the deployed checkpoint is therefore more likely a checkpoint/provenance or hidden training-contract issue than a total label/window corruption.

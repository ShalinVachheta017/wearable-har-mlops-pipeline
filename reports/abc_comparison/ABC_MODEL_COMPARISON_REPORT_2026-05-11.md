# ABC Model Comparison Report - 2026-05-11

Status: evaluation mode completed. Registry contracts were not rewritten, model
artifacts were not overwritten, thresholds were not changed, and no retraining was run.

## Decision Rule

- clean production contract compatibility
- avoid class collapse
- use most/all classes
- honest train-only preprocessing
- User 7 external metrics
- safe monitoring/trigger behavior
- explainable provenance and preprocessing

## User 7 Labeled External Evaluation

| Model | Contract mode | Accuracy | Macro F1 | Classes used | Dominant class % | Mean confidence | Trigger | Decision hint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| model_a | clean_pipeline | 0.3761 | 0.3410 | 11 | 16.4813 | 0.3594 | REVIEW | clean_runtime_candidate_pending_human_review |
| model_b | native_legacy_diagnostic | 0.4378 | 0.4186 | 11 | 19.5147 | 0.7746 | REVIEW | forensic_reference_only_native_mode_not_production_safe |
| model_c | previous_pipeline_clean_rowwise_no_scaler | 0.0758 | 0.0248 | 4 | 47.1183 | 0.7484 | REVIEW | historical_baseline_pending_human_review |

## Garmin Production-Style Unlabeled Run

| Model | Contract mode | Windows | Classes used | Dominant class % | Mean confidence | Monitoring | Trigger | Auto retrain |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| model_a | clean_pipeline | 1304 | 10 | 51.8405 | 0.3929 | WARNING | REVIEW | False |
| model_b | native_legacy_diagnostic | 1303 | 11 | 29.7774 | 0.7167 | WARNING | REVIEW | False |
| model_c | previous_pipeline_clean_rowwise_no_scaler | 1304 | 6 | 46.0123 | 0.7302 | WARNING | REVIEW | False |

## Model B Clean Pipeline Compatibility

Model B was **not evaluated under the clean_pipeline contract** because:

- No persisted legacy scaler exists (it requires a full-evaluation fitted StandardScaler).
- Legacy channel-major tensor layout is incompatible with the clean production pipeline contract.

Model B native diagnostic score is therefore forensic reference only and not production-safe.

## Provisional Status

- Model A: clean runtime candidate pending human review.
- Model B: forensic native legacy reference only; not production-safe.
- Model C: historical baseline with checkpoint-contract mismatch risk.

## Output Files

- `reports/abc_comparison/abc_results.csv`
- `reports/abc_comparison/abc_results.json`
- `reports/abc_comparison/comparison_summary.json`
- `reports/abc_comparison/contract_runtime_verification.json`

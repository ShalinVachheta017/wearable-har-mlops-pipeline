# A/B/C Final Model Comparison - May 2026

Date: 2026-05-08

## Models

```text
A = Clean-contract Model A
B = Mentor/vendor legacy model
C = Previous current pipeline/default model
```

## Result Table

| Model | Contract | Main Metric | User 7 Macro F1 | Decision |
|---|---|---:|---:|---|
| A | Row-wise (200,6), Garmin train-only scaler, no legacy reshape | Garmin macro F1 0.3101 | 0.3397 | Selected |
| B | Legacy full-data scaler, random overlapping split, legacy tensor reshape | Legacy all_users macro F1 0.9089 | 0.4186 | Forensic evidence only |
| C | Previous raw/no-scaler pipeline with vendor/default model mismatch | Clean-contract macro F1 0.0358 | 0.0248 | Rejected |

## Decision

Model A is selected for the final package because it is the only candidate with a documented, deployable production contract:

```text
normal row-wise IMU windows
fixed 6-channel feature order
Garmin train-only scaler
fixed 11-class label order
no legacy tensor reshape
no validation/User7 scaler leakage
```

Model B is not selected even though its legacy metrics are higher, because those metrics depend on a different notebook contract:

```text
full-data scaler
random overlapping window split
legacy tensor layout
fresh scaler during file inference
accuracy-first validation
```

Model C is not selected because it shows severe contract mismatch under clean row-wise evaluation.

## Thesis Wording

Use this wording:

> The final model was not selected from random-window or legacy-contract accuracy. Model selection used a clean row-wise production contract, Garmin validation macro F1, and a single external User 7 evaluation after the candidate was frozen.

## Artifact

The machine-readable comparison table is:

```text
models/production_contract/model_a_final_20260508/abc_model_comparison.csv
```

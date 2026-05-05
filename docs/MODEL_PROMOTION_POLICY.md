# Model Promotion Policy

## Purpose

Prevent accidental model swaps and keep the pipeline behavior consistent with the thesis/repo governance story.

## Default Model Rule

- The default runtime model is the mentor-provided pretrained baseline:
  - `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`
- This applies to pipeline defaults, API defaults, and Docker defaults.

## Monitoring And Drift Rule

- Drift, confidence degradation, temporal instability, or trigger alerts are signals for investigation.
- These signals alone do not authorize model promotion.

## Retraining Rule

- Retraining/fine-tuning is allowed only when labeled data is available for evaluation.
- Unlabeled data can be used for monitoring or exploratory analysis, but not for automatic promotion decisions.

## Promotion Gate

A candidate model can become the new default only if all of the following are true:

1. Labeled evaluation data is available and traceable.
2. Candidate-vs-current comparison is run with reproducible commands/artifacts.
3. Candidate meets defined acceptance criteria and outperforms the current default.
4. Governance checks (trigger/policy/quality gates) are satisfied.

If the candidate is equal or worse, keep the current default model.

## Required Evidence Before Promotion

- Candidate model path and source run id.
- Current default model path.
- Labeled comparison metrics and threshold/acceptance decision.
- Command history or report file under `reports/`.
- Updated documentation (`README.md`, `WORKLOG.md`, and relevant thesis/report sections if in scope).

## Operational Reminder

- API upload/inference endpoints do not auto-promote models.
- Promotion is an explicit, governed decision.

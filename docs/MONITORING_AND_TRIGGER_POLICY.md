# Monitoring and Trigger Policy

Purpose: summarize the final Stage 6/7 governance behavior for thesis writing and defense.

## Stage 6 Monitoring

Stage 6 is warning-oriented and non-mutating. It evaluates confidence, uncertainty proxies, temporal behavior, drift, and collapse risk.

Final monitoring defaults:

- Mean confidence warning: below `0.70`
- Uncertain windows warning: above `20%`
- Transition-rate warning: above `35%`
- Drift z-score warning: above `1.8`
- Dominant-class warning/critical: `85%` / `95%`

The final runtime drift baseline is `models/raw_physical_baseline.json`. If the raw baseline is missing or the baseline feature space does not match the production windows, Stage 6 reports the condition for review instead of fabricating a critical drift result from incompatible feature spaces.

## Stage 7 Trigger Governance

Stage 7 converts Stage 6 signals and collapse evidence into governance actions. It does not automatically retrain from unlabeled production drift.

Final governance rule:

- Healthy signals: no action.
- One warning: monitor.
- Multiple warnings: review/label queue.
- Critical signal: review required.
- Dominant-class collapse or low-motion collapse risk: review required and `should_retrain=false`.

Retraining, registration, and baseline update are conditional stages. They require review, QA, labels, and promotion evidence before they can be claimed as model mutation. MLflow inference finalization does not register new model versions; model registration belongs to conditional Stage 9.

## Scope Boundary

Controlled single-activity dominance is not the same as uncontrolled production collapse. Controlled dominance can be valid evidence when the input session intentionally contains one activity. Uncontrolled high-confidence single-class production behavior is treated as collapse risk and routed to review.

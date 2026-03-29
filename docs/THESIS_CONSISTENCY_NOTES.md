# Thesis Consistency Notes

Purpose: lock a single, reproducible interpretation for thresholding, ablation config labels, and adaptation framing.

## 1) Threshold Design (Monitoring vs Trigger)

Final design is tiered and explicit:

- Stage 6 monitoring warning threshold (mean confidence): `0.60`
- Stage 7 trigger warning threshold (mean confidence): `0.65`
- Stage 7 trigger critical threshold (mean confidence): `0.50`

Implementation alignment:

- `PostInferenceMonitoringConfig.confidence_warn_threshold = 0.60`
- `TriggerEvaluationConfig.confidence_warn = 0.65`
- `TriggerEvaluationConfig.confidence_critical = 0.50`
- `TriggerThresholds` defaults are aligned to `0.65 / 0.50`

Why: monitoring is an early warning layer; retraining trigger is a stricter governance gate.

## 2) Collapse Guard Rule

Stage 7 includes a collapse guard that returns `REVIEW` (and blocks auto-retrain) when collapse-like proxies are detected, including:

- `dominant_pct >= 95`, or
- other configured collapse guard conditions in `src/trigger_policy.py`

This behavior is intentionally conservative for unlabeled production data.

## 3) Ablation Config A/B/C/D Definitions

Canonical source: `scripts/run_ablation_experiment.py`.

- Config A: `gravity_removal=False`, `calibration=False`
- Config B: `gravity_removal=False`, `calibration=True`
- Config C: `gravity_removal=True`, `calibration=False`
- Config D: `gravity_removal=True`, `calibration=True`

Important reproducibility note:

Any statement that says "Config D = calibration only (no gravity removal)" is incorrect for the current repository state. That definition corresponds to Config B.

## 4) AdaBN Framing

Adaptation is optional and not the default pipeline mode.

- CLI default remains `--adapt none`
- `ModelRetrainingConfig.adaptation_method` default is `none`
- AdaBN/TENT/pseudo-label options are available as explicit research modes

This keeps the baseline production story and the adaptation experiments clearly separated.

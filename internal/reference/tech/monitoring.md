# Monitoring

## What it is

Monitoring observes model behavior and runtime health after inference using defined metrics and thresholds.

## Why it is used in this thesis

Monitoring is central to thesis claims about drift awareness, uncertainty detection, and safe trigger-based retraining governance.

## Repository locations

- `src/components/post_inference_monitoring.py`
- `scripts/post_inference_monitoring.py`
- `src/trigger_policy.py`
- `config/alerts/har_alerts.yml`
- `docs/TRIGGER_POLICY_EXPLANATION.md`

## Role in this project

- Core:
  - Stage 6 (monitoring) and Stage 7 (trigger) are in the default main path.
- Optional:
  - Prometheus/alerting deployment is optional in local offline runs.
- Future work:
  - Expand alert routing and long-window trend analytics.

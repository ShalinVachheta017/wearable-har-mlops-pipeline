# Trigger Policy Explanation

Document: docs/TRIGGER_POLICY_EXPLANATION.md
Pipeline stage: 7 - Trigger Evaluation
Core modules: src/components/trigger_evaluation.py, src/trigger_policy.py

## Purpose

The trigger policy converts Stage 6 monitoring outputs (plus Stage 5 collapse signals) into one action:

- none
- monitor
- review
- queue_retrain (review/label queue, not immediate mutation)
- trigger (candidate generation only after governance gates)

The result is written into TriggerEvaluationArtifact and persisted in artifacts/*/trigger/trigger_decision.json.

## Runtime Decision Flow

1. Stage 6 produces layer metrics:
- Layer 1 confidence/uncertainty
- Layer 2 temporal transitions
- Layer 3 drift

2. Stage 7 maps these metrics into TriggerPolicyEngine inputs.

3. Collapse guard is checked first.
- If collapse conditions match, action is review with should_retrain=false.

4. If no collapse review, confidence/temporal/drift signals are scored.

5. Signals are aggregated by voting (NO_AUTO_RETRAIN policy):
- Any CRITICAL signal -> REVIEW_REQUIRED (action=review, should_trigger=false, auto_retrain=false)
- 2+ WARNING signals -> REVIEW_LABEL_QUEUE (action=queue_retrain, should_trigger=false, label_required=true)
- 1 WARNING signal -> monitor (should_trigger=false)
- Otherwise -> HEALTHY (none)

Unlabeled production data must NOT trigger automatic retraining regardless of signal severity.
A label/QA gate is required before any retraining candidate is generated.

6. Consecutive-warning escalation promotes to REVIEW_REQUIRED (not automatic trigger).
   should_trigger remains false; label_required and qa_required are set true.

7. Cooldown is applied as the final gate.
- If cooldown is active, final action is queue_retrain and should_trigger=false.
- This final gate has precedence over same-cycle escalation.

## Threshold Sources

Stage 6 monitoring thresholds are defined in `PostInferenceMonitoringConfig` and passed at runtime into `src/monitoring/post_inference_monitor.py` by `src/components/post_inference_monitoring.py`.

Default Stage 6 thresholds:
- confidence_warn_threshold: 0.70
- uncertain_window_threshold: 0.50
- uncertain_pct_threshold: 20.0
- transition_rate_threshold: 35.0
- drift_zscore_threshold: 1.8
- dominant_class_warn_threshold: 85.0
- dominant_class_critical_threshold: 95.0

Stage 7 trigger thresholds are defined in TriggerEvaluationConfig and passed to TriggerPolicyEngine via TriggerThresholds in src/components/trigger_evaluation.py.

Default Stage 7 thresholds:
- confidence_warn: 0.65
- confidence_critical: 0.50
- temporal_flip_warn: 0.35
- temporal_flip_critical: 0.50
- drift_zscore_warn: 2.0
- drift_zscore_critical: 3.0
- cooldown_hours: 24

Notes:
- Stage 6 and Stage 7 are intentionally tiered (monitoring warning is earlier; trigger is stricter governance).
- Runtime values can be overridden with config/pipeline_overrides.yaml or HAR_PIPELINE_OVERRIDES.
- Stage 6 drift uses the raw physical monitoring baseline for the final production contract and skips or routes review when a baseline is missing or feature-space mismatched.

Prometheus/Grafana alerting is not part of the defended current implementation. The defended monitoring evidence comes from offline-first pipeline artifacts, trigger reports, logs, MLflow/DVC evidence, and saved run outputs.

## Collapse Guard Semantics

Collapse guard is intentionally conservative for unlabeled production data.

review is returned when any collapse condition holds, including:
- dominance_warning=true from upstream signals, or
- dominant_pct >= 95, or
- dominant_pct >= 90 with transition_rate == 0 and high confidence, or
- Stage 4 `collapse_level == "CRITICAL_COLLAPSE"`, or
- Stage 6 `low_motion_collapse_risk == true`.

When collapse guard matches:
- should_retrain=false
- action=review
- recommendation is manual review, not automatic retraining.

## Cooldown Semantics

Cooldown exists to prevent rapid retraining loops.

Behavior:
- If a decision would create a candidate and a recent retrain is still within cooldown_hours,
  the final decision is rewritten to queue_retrain/review queue with cooldown_active=true.
- The final decision is persisted together with cooldown status.

After the P0 fix, cooldown is enforced after escalation logic so it cannot be overridden later in the same evaluation cycle.

## Practical Interpretation

1. High confidence alone does not force trigger.
2. Drift or temporal instability can trigger action even when confidence is relatively high.
3. Dominance/collapse patterns route to review rather than automatic retraining.
4. Cooldown prevents repeated immediate retrains from back-to-back runs.

## Key Files

- src/components/post_inference_monitoring.py
- src/components/trigger_evaluation.py
- src/trigger_policy.py
- src/entity/config_entity.py
- docs/thesis/THRESHOLD_TRIGGER_JUSTIFICATION.md
- docs/THESIS_CONSISTENCY_NOTES.md
- docs/PIPELINE_DATA_FLOW_MAP.md

# Trigger Policy Explanation

**Document:** `docs/TRIGGER_POLICY_EXPLANATION.md`  
**Pipeline stage:** 7 — Trigger Evaluation  
**Component:** `src/trigger_policy.py` → `TriggerPolicy`

---

## What the trigger policy decides

After each inference run the trigger policy reads the monitoring signals from
stages 5 (Evaluation) and 6 (Post-Inference Monitoring) and makes a single
binary decision: **retrain the model now, or leave it alone**.

```
Stage 5 → distribution + confidence metrics ──┐
Stage 6 → confidence / temporal / drift layers ├──> TriggerPolicy → TriggerAction
                                               ┘
```

The decision is written to the pipeline result as `TriggerEvaluationArtifact`:

| Field            | Type              | Example                          |
|------------------|-------------------|----------------------------------|
| `action`         | `TriggerAction`   | `NONE`                           |
| `alert_level`    | `AlertLevel`      | `INFO`                           |
| `should_retrain` | `bool`            | `False`                          |
| `reasons`        | `List[str]`       | `["All metrics within normal ranges"]` |

---

## States

### HEALTHY — trigger = NONE

All three monitoring layers pass their thresholds:

| Layer | Signal | Healthy threshold |
|-------|--------|-------------------|
| Layer 1 – Confidence | Uncertain predictions | < 5 % |
| Layer 2 – Temporal   | Activity transition rate | < 10 % |
| Layer 3 – Drift      | Max channel drift (z-score) | < 1.50 |

```
DECISION: NONE
Alert Level: INFO
Should Trigger: False
Reason: All metrics within normal ranges
```

No automatic action is taken. The pipeline ends after stage 7 and archives
its artifacts.

---

### WARNING — trigger = MONITOR

One or more signals are elevated but have not crossed the critical threshold:

- Moderate drift: 0.75 ≤ max_drift < 1.50
- Elevated uncertainty: 5 % ≤ uncertain_pct < 15 %
- High transition rate signalling potential out-of-distribution inputs

```
DECISION: MONITOR
Alert Level: WARNING
Should Trigger: False
Reason: Drift approaching threshold (max=0.87) — monitoring recommended
```

Model is **not** retrained automatically. The run is flagged in MLflow and a
warning appears in the pipeline summary. The recommended response is to
schedule a labelling review in the next sprint.

---

### CRITICAL — trigger = TRIGGER_RETRAIN

A hard threshold is crossed:

- Drift: max_drift ≥ 1.50 on any sensor channel
- Confidence collapse: mean_confidence < 0.60 for the batch
- Uncertainty flood: > 15 % uncertain predictions

```
DECISION: TRIGGER_RETRAIN
Alert Level: CRITICAL
Should Retrain: True
Reason: Sensor drift exceeds threshold (max=1.73 on acc_z)
```

Automatic retraining is then initiated if `--retrain` is present in the run
command. Without `--retrain` the decision is recorded but no action is taken —
the pipeline does not self-modify without the explicit flag.

---

## Why high class dominance alone does NOT trigger retraining

The 2026-03-06 production run showed `hand_tapping = 99.9 %` of predictions.
Evaluation stage 5 emits a `⚠️ distribution dominance` warning, but the
trigger policy correctly sets `NONE`:

1. **All three monitoring layers passed.**  
   Confidence was high (93.4 % mean, 99.7 % HIGH-tier). Temporal patterns
   were stable (2 transitions / 1814 windows = 0.1 %). Drift was within
   bounds (max = 0.569, threshold = 1.50).

2. **Class dominance is a data property, not a model failure.**  
   If a participant genuinely performed `hand_tapping` for the entire
   recording session the correct behaviour is to predict `hand_tapping`.
   A model that correctly identifies a single-activity session is *working*,
   not degrading.

3. **Retraining on a single-class batch would cause catastrophic forgetting.**  
   Fine-tuning on a batch containing only `hand_tapping` would reduce
   performance on the other 10 activity classes. The trigger policy
   intentionally prevents this.

4. **The appropriate response to class dominance is a *labelling* action,**  
   not an automated retrain: collect a more representative batch, verify the
   label, and include it in the next supervised retraining cycle.

### The 95 % dominance flag

Starting from this commit, the evaluation stage additionally sets a structured
flag `distribution_dominance_warning = True` whenever any single class exceeds
95 % of predictions. This flag flows through the `ModelEvaluationArtifact`
into the pipeline summary and MLflow metrics, where it is logged as
`metric: distribution_dominance_warning = 1.0`.

The flag does **not** affect the trigger decision; it is informational only.

---

## Run classification — 2026-03-06 15:06

| Signal | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Mean confidence | 93.4 % | > 80 % | ✅ PASS |
| HIGH-tier predictions | 99.7 % | > 90 % | ✅ PASS |
| Uncertain predictions | 0 / 1814 | < 5 % | ✅ PASS |
| Activity transitions | 0.1 % | < 10 % | ✅ PASS |
| Max sensor drift | 0.569 | < 1.50 | ✅ PASS |
| Class dominance | 99.9 % (`hand_tapping`) | — | ⚠️ WARNING (informational) |
| **Trigger decision** | **NONE** | — | ✅ **HEALTHY** |

Overall classification: **Healthy overall, monitoring note on class dominance.**

---

## Key source files

| File | Role |
|------|------|
| `src/trigger_policy.py` | `TriggerPolicy` — reads signals, returns `TriggerAction` |
| `src/components/trigger_evaluation.py` | Pipeline component wrapper for stage 7 |
| `src/evaluate_predictions.py` | `analyze_distribution()` — emits dominance warning |
| `src/components/post_inference_monitoring.py` | 3-layer monitoring runner |
| `src/entity/artifact_entity.py` | `TriggerEvaluationArtifact`, `ModelEvaluationArtifact` |
| `config/pipeline_config.yaml` | Drift / confidence threshold values |

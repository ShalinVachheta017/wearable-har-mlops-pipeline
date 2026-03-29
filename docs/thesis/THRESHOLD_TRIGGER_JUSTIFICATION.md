# Threshold and Trigger Justification (Repository-Grounded)

Generated: 2026-03-29

## Scope and method

This report is intentionally constrained to repository evidence only:

- Runtime implementation in source code.
- Config defaults and override wiring.
- Unit/integration tests in this repository.
- Stored experiment/evaluation outputs in `reports/`, `thesis/`, and `artifacts/`.

No external claims are introduced here. Where support is weak, it is labeled explicitly as heuristic or unresolved.

Evidence classes used in this report:

- Paper-anchored: rationale is explicitly tied to paper references inside repo files/comments.
- Stats-backed: behavior is supported by repo-local measured outputs.
- Heuristic safeguard: engineering rule with weak/no direct calibration in repo.
- Unresolved: contradiction, stale doc, or missing calibration evidence.

## 1) Threshold inventory: definition vs actual use

| Rule family | Defined value(s) and source | Actual runtime behavior | Consistency | Evidence class |
| --- | --- | --- | --- | --- |
| Stage 6 Layer 1 mean-confidence warning | `confidence_warn_threshold = 0.60` in `src/entity/config_entity.py:181` | Pipeline Stage 6 computes mean confidence (`scripts/post_inference_monitoring.py:178`) but status decision is driven by uncertain percentage check (`scripts/post_inference_monitoring.py:212`), and wrapper does not pass threshold fields (`src/components/post_inference_monitoring.py:71`). API path does apply mean confidence threshold (`src/api/app.py:242`). | Inconsistent (pipeline vs API vs config intent). | Unresolved |
| Stage 6 uncertain-window cutoff | `uncertain_window_threshold = 0.50` in `src/entity/config_entity.py:183` | Script default confidence cutoff is 0.5 (`scripts/post_inference_monitoring.py:49`), but if `is_uncertain` column exists, script uses that flag directly (`scripts/post_inference_monitoring.py:189-190`) rather than recomputing from confidence threshold (`scripts/post_inference_monitoring.py:193`). Inference flag uses 0.50 (`src/run_inference.py:95`, `src/run_inference.py:511`). | Partially consistent, but behavior depends on upstream `is_uncertain` semantics. | Heuristic safeguard |
| Stage 6 uncertain-percentage warning | `uncertain_pct_threshold = 30.0` in `src/entity/config_entity.py:182` | Script default threshold is 10.0 (`scripts/post_inference_monitoring.py:50`) and wrapper does not pass config threshold (`src/components/post_inference_monitoring.py:71`). API uses config threshold (`src/api/app.py:243`). | Inconsistent and high impact. | Unresolved |
| Stage 6 temporal transition warning | `transition_rate_threshold = 50.0` in `src/entity/config_entity.py:185` | Script warns if `transition_rate > 50` (`scripts/post_inference_monitoring.py:287`). API uses config threshold (`src/api/app.py:250`). | Consistent at current defaults, fragile because Stage 6 wrapper does not pass threshold fields (`src/components/post_inference_monitoring.py:71`). | Heuristic safeguard |
| Stage 6 drift warning | `drift_zscore_threshold = 2.0` in `src/entity/config_entity.py:187` | Script default drift threshold is 2.0 (`scripts/post_inference_monitoring.py:51`, `scripts/post_inference_monitoring.py:367`). API uses config threshold (`src/api/app.py:265`). | Consistent at current defaults. | Paper-anchored + stats-backed |
| Stage 7 confidence warn/critical | `0.65 / 0.50` in `src/entity/config_entity.py:211-212` | Trigger engine defaults match (`src/trigger_policy.py:103-104`), and wrapper passes config into engine (`src/components/trigger_evaluation.py:45-46`). | Consistent. | Stats-backed |
| Stage 7 temporal flip warn/critical | `0.35 / 0.50` in `src/entity/config_entity.py:217-218` | Trigger engine defaults are `0.25 / 0.40` (`src/trigger_policy.py:111-112`), but wrapper passes config values (`src/components/trigger_evaluation.py:49-50`) for pipeline runtime. Prometheus alert uses 0.25 (`config/alerts/har_alerts.yml:59`). | Partially consistent (runtime path is consistent; observability threshold is a lower-tier warning but not clearly documented as tiered). | Heuristic safeguard |
| Stage 7 drift warn/critical | `2.0 / 3.0` in `src/entity/config_entity.py:215-216` | Wrapper passes values (`src/components/trigger_evaluation.py:47-48`). Engine uses aggregate drift thresholds (`src/trigger_policy.py:530`, `src/trigger_policy.py:535`). Wrapper sends empty `per_channel_metrics` (`src/components/trigger_evaluation.py:95`), so channel-wise drift count logic is effectively inactive. | Partially consistent (aggregate path works; per-channel path inactive in pipeline). | Paper-anchored + stats-backed |
| Collapse guard (review gate) | Stage 5 dominance warning threshold: `dominant_pct > 95` (`src/evaluate_predictions.py:223`). Stage 7 guard conditions include: warning flag, `dominant_pct >= 95`, or `dominant_pct >= 90` with zero transition + high confidence (`src/trigger_policy.py:360-368`). | Guard returns `REVIEW` with `should_trigger=False` (`src/trigger_policy.py:391-393`). Flow is validated by tests (`tests/test_trigger_policy.py:119`, `tests/test_trigger_policy.py:133-134`) and artifact examples (`artifacts/20260329_205039/trigger/trigger_decision.json:2-4`). | Consistent in code and observed outputs. | Stats-backed + heuristic safeguard |
| Retrain decision voting | `min_signals_for_retrain = 2` (`src/trigger_policy.py:131`) and CRITICAL-any-signal rule (`src/trigger_policy.py:584`, `src/trigger_policy.py:601`) | Stage 8 is gated on `should_retrain` (`src/pipeline/production_pipeline.py:555`). Trigger policy evaluation file shows strong precision/FAR tradeoff for `two_of_three` (`reports/TRIGGER_POLICY_EVAL.csv:3`). | Consistent and empirically supported. | Stats-backed |
| Cooldown gate | `cooldown_hours = 24` (`src/entity/config_entity.py:219`), cooldown config default 24 (`src/trigger_policy.py:139`) | Cooldown suppression is applied (`src/trigger_policy.py:671`), but then consecutive-warning escalation can re-enable trigger after cooldown call (`src/trigger_policy.py:287`, `src/trigger_policy.py:290`, `src/trigger_policy.py:690-693`). Artifacts show contradictory state: `cooldown_active=true` with `should_retrain=true` in some runs (`artifacts/20260329_210502/trigger/trigger_decision.json:2-3`, `artifacts/20260329_210502/trigger/trigger_decision.json:13`; same pattern in `artifacts/20260329_210952/trigger/trigger_decision.json:2-3`, `artifacts/20260329_210952/trigger/trigger_decision.json:13`). | Inconsistent (logic ordering bug risk). | Unresolved |

## 2) Requested safety checks

### A) Collapse -> REVIEW (not auto-retrain)

Verdict: Supported.

- Code-level guard forces `REVIEW` and `should_trigger=False` (`src/trigger_policy.py:391-393`).
- Tests assert this behavior (`tests/test_trigger_policy.py:119`, `tests/test_trigger_policy.py:133-134`).
- Artifact evidence includes explicit collapse decision with no retrain (`artifacts/20260329_205039/trigger/trigger_decision.json:2-4`).
- Repository sweep over 55 trigger artifacts found 10 runs with `dominant_pct >= 95`; all 10 were `review`, none had `should_retrain=true`.

### B) High confidence alone is insufficient

Verdict: Supported.

- Decision logic is multi-signal, not confidence-only (`src/trigger_policy.py:584`, `src/trigger_policy.py:601`).
- High-confidence runs can still queue/trigger on drift/other signals. Example: mean confidence ~0.88 with drift ~3.29 produced `queue_retrain`/`trigger` (`artifacts/20260329_210734/monitoring/monitoring_report.json` and `artifacts/20260329_210734/trigger/trigger_decision.json:3-4`; `artifacts/20260329_210952/trigger/trigger_decision.json:2-4`).

### C) Drift can matter even with high confidence

Verdict: Supported.

- Aggregate drift can produce CRITICAL independent of confidence (`src/trigger_policy.py:530`, `src/trigger_policy.py:535`).
- Observed in artifacts where high confidence co-exists with CRITICAL drift (`artifacts/20260329_210734/monitoring/monitoring_report.json`, `artifacts/20260329_210734/trigger/trigger_decision.json:4`).

### D) Retraining requires stronger evidence than review

Verdict: Mostly supported, with one caveat.

- REVIEW path is explicitly non-triggering (`src/trigger_policy.py:391-393`).
- Retraining path needs CRITICAL or multi-signal escalation (`src/trigger_policy.py:584`, `src/trigger_policy.py:601`).
- Pipeline enforces gate before Stage 8 (`src/pipeline/production_pipeline.py:555`).
- Caveat: cooldown can be overridden by consecutive-warning escalation in some cases (`src/trigger_policy.py:690-693`), weakening intended governance.

### E) Thresholds vs observed behavior

Verdict: Mixed.

Supported by data:

- Trigger policy benchmark favors `two_of_three` over `single_signal` for false alarms and precision (`reports/TRIGGER_POLICY_EVAL.csv:2-3`).
- Negative-result ablation documents unchanged mean confidence and increased review routing (`thesis/chapters/before_vs_after_26datasets.md:12-15`, `thesis/chapters/before_vs_after_26datasets.md:22`).

Not well supported / contradictory:

- Some configured Stage 6 thresholds are not the actual pipeline runtime thresholds because wrapper does not pass them (`src/components/post_inference_monitoring.py:71`).
- Threshold calibration table gives weak support for selected values in several dimensions (for example, `confidence_warn_threshold=0.65` has very high clean false alarm in that table: `reports/THRESHOLD_CALIBRATION.csv:18`).

## 3) Consistency audit (code, config, tests, docs)

### High-priority inconsistencies (submission risk)

1. Stage 6 config/runtime mismatch for confidence and uncertain-percentage gating.
   - Defined in config: 0.60 and 30% (`src/entity/config_entity.py:181-182`).
   - Pipeline runtime effectively uses script defaults and uncertain-flag semantics (`scripts/post_inference_monitoring.py:50`, `scripts/post_inference_monitoring.py:189-193`, `scripts/post_inference_monitoring.py:212`), because wrapper does not pass threshold parameters (`src/components/post_inference_monitoring.py:71`).
   - API runtime uses config thresholds (`src/api/app.py:242-243`).

2. Cooldown inconsistency in trigger engine update order.
   - Cooldown can mark decision queued (`src/trigger_policy.py:671`), then consecutive-warning update can re-promote to trigger (`src/trigger_policy.py:690-693`) after cooldown has already been applied (`src/trigger_policy.py:287`, `src/trigger_policy.py:290`).
   - Observed in artifacts with both `cooldown_active=true` and `should_retrain=true` (`artifacts/20260329_210502/trigger/trigger_decision.json:2`, `artifacts/20260329_210502/trigger/trigger_decision.json:13`).

### Medium-priority inconsistencies

1. `docs/TRIGGER_POLICY_EXPLANATION.md` contains stale threshold values (for example drift `1.50`, uncertain `<5%`, transitions `<10%`) that do not reflect current engine defaults/config (`docs/TRIGGER_POLICY_EXPLANATION.md:40-42`, `docs/TRIGGER_POLICY_EXPLANATION.md:81-83`).

2. Drift per-channel signal path in trigger engine is underused in pipeline because wrapper sends empty `per_channel_metrics` (`src/components/trigger_evaluation.py:95`) while engine expects per-channel z-scores under `psi` keys (`src/trigger_policy.py:511`).

### Test coverage observations

- Good: collapse guard behavior is tested (`tests/test_trigger_policy.py:119`, `tests/test_trigger_policy.py:133-134`).
- Good: trigger temporal thresholds pass-through is tested (`tests/test_trigger_threshold_pass_through.py:27-28`, `tests/test_trigger_threshold_pass_through.py:41-42`).
- Gap: no Stage 6 test verifies that `PostInferenceMonitoringConfig` threshold fields are actually wired into `PostInferenceMonitor` constructor in pipeline path.

## 4) Evidence-based justification by category

### Paper-anchored (repo-local paper linkage exists)

1. Drift z-score framing at 2-sigma warning and 3-sigma critical is documented in code comments with explicit references (`src/trigger_policy.py:94-95`, `src/trigger_policy.py:119`; also `scripts/post_inference_monitoring.py:58-59`).

### Stats-backed

1. Multi-signal trigger policy quality tradeoff is evidenced by benchmark CSV:
   - `single_signal`: precision 0.8406, FAR 0.1389 (`reports/TRIGGER_POLICY_EVAL.csv:2`).
   - `two_of_three`: precision 0.9878, FAR 0.0069 (`reports/TRIGGER_POLICY_EVAL.csv:3`).
2. Collapse guard behavior appears in actual run artifacts and tests (see Section 2A).
3. Negative-result ablation is explicitly documented (confidence unchanged, review routing increased) (`thesis/chapters/before_vs_after_26datasets.md:12-15`, `thesis/chapters/before_vs_after_26datasets.md:22`).

### Heuristic safeguards (keep, but label honestly)

1. Collapse guard secondary condition (`dominant_pct >= 90` + zero transition + high confidence) appears as an engineering rule in code (`src/trigger_policy.py:362-368`) without dedicated calibration artifact.
2. Entropy and uncertain-ratio trigger thresholds in `TriggerThresholds` (`src/trigger_policy.py:105-108`) lack direct per-threshold calibration summary in current docs.

### Unresolved or weakly supported

1. Stage 6 confidence/uncertainty threshold mismatch across pipeline and API paths (Section 3).
2. Cooldown-overridden-by-consecutive-warning behavior (Section 3).
3. `reports/PAPER_SUPPORT_MAP.json` points Stage 6/7 calibration evidence to `reports/THRESHOLD_CALIBRATION_SUMMARY.md` (`reports/PAPER_SUPPORT_MAP.json:67`, `reports/PAPER_SUPPORT_MAP.json:74`, `reports/PAPER_SUPPORT_MAP.json:86`), but that summary file is not present in repository.

## 5) Submission-ready summary

### What is defensible now

1. The governance intent is clear and mostly implemented: multi-signal triggering, collapse-to-review gate, and retrain gating in pipeline.
2. Trigger policy design choice (two-of-three) is empirically supported by repo-local benchmark data.
3. Negative-result reporting is present and honest.

### What must be labeled as limitation (unless fixed)

1. Stage 6 thresholds are not fully wired as configured in pipeline runtime.
2. Cooldown behavior has edge-case inconsistency.
3. Some threshold values are operational heuristics rather than fully calibrated optima.

### Priority actions before thesis submission

1. P0: Align Stage 6 runtime wiring so configured monitoring thresholds are actually passed to `PostInferenceMonitor` in pipeline path.
2. P0: Fix trigger cooldown/update ordering so cooldown cannot be silently bypassed by consecutive-warning escalation in the same decision cycle.
3. P1: Update `docs/TRIGGER_POLICY_EXPLANATION.md` to current thresholds and decision semantics.
4. P1: Add a compact threshold calibration summary doc linked from `PAPER_SUPPORT_MAP.json`.
5. P1: Add regression tests for Stage 6 threshold pass-through and cooldown-plus-consecutive-warning interaction.

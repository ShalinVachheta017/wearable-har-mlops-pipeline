# Wave 1 Fixes: Stage 5, Stage 7, Label Mapping

## Scope
This Wave 1 patch intentionally addresses only three engineering integrity issues:
- Stage 5 evaluation contract parsing
- Stage 7 temporal threshold pass-through
- Single-source label mapping across runtime entrypoints

Not included in this wave:
- Drift baseline normalization changes
- Semantic trigger lane changes
- Retraining policy redesign

## What Was Wrong

### 1) Stage 5 evaluation contract mismatch
`EvaluationPipeline.run()` returns wrapper shape:
- `{"success": bool, "results": {...}}`

But Stage 5 wrapper (`ModelEvaluation`) was reading top-level keys like `distribution` and `confidence`, which could produce empty stage summaries/artifacts.

### 2) Stage 7 temporal thresholds not passed through
`TriggerEvaluationConfig` exposed `temporal_flip_warn` and `temporal_flip_critical`, but Stage 7 runtime threshold construction did not pass them into `TriggerThresholds`.

### 3) Duplicated label mappings
Activity class mappings were duplicated in:
- inference
- evaluation
- API

This increases drift risk if one copy changes and others do not.

## What Was Fixed

### 1) Stage 5 contract parsing fixed
In `src/components/model_evaluation.py`:
- Stage now checks `result.get("success")`
- Unwraps with `payload = result.get("results", {})`
- Reads:
  - `distribution` summary
  - `confidence` summary
  - dominance warning flag
  - report paths from `output_files`
- Adds warning logs when expected payload sections are empty

### 2) Stage 7 temporal threshold pass-through fixed
In `src/components/trigger_evaluation.py`:
- `temporal_flip_warn` now passed to `TriggerThresholds.flip_rate_warn`
- `temporal_flip_critical` now passed to `TriggerThresholds.flip_rate_critical`

### 3) Single-source label mapping introduced
Added `src/utils/label_mapping.py`:
- Canonical mapping loader with priority:
  1. `data/prepared/config.json` mapping (if present and valid)
  2. canonical static fallback in one place
- Validation checks:
  - non-empty mapping
  - contiguous labels (`0..n-1`)
  - reverse mapping consistency

Wired runtime entrypoints to shared loader:
- `src/run_inference.py`
- `src/evaluate_predictions.py`
- `src/api/app.py`

## Regression Tests Added
- `tests/test_stage5_evaluation_summary_contract.py`
  - Verifies wrapper `{"success": True, "results": ...}` is correctly parsed.
  - Verifies non-empty distribution summary and confidence mean propagation.
  - Verifies dominance warning and report path propagation.

- `tests/test_trigger_threshold_pass_through.py`
  - Verifies non-default temporal threshold values are passed into runtime `TriggerThresholds`.

- `tests/test_activity_label_mapping_single_source.py`
  - Verifies inference/evaluation/API use the same mapping.
  - Verifies inconsistent metadata mapping raises fail-fast `ValueError`.

## Remaining Caveats
- Drift baseline scale alignment is unchanged in this wave.
- Semantic dominance is still informational and not part of trigger voting.
- Retraining policy behavior is unchanged.

## Next (Wave 2) Recommendations
1. Fix drift baseline normalization contract so Stage 6 compares compatible feature spaces.
2. Add optional semantic-warning lane in trigger evaluation (monitor-level only by default).
3. Add targeted integration test from evaluation -> monitoring -> trigger evidence propagation.

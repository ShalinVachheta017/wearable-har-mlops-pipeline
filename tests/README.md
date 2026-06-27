# Tests — HAR MLOps Pipeline

**Verified status (2026-06-27): 88 tests across 11 test files — all passing
(`88 passed in ~4s`, pytest 9.0.2, conda env `thesis-mlops`).**

## Running the suite

```
pytest tests/
```

Single file, verbose:

```
pytest tests/test_stage6_monitoring.py -v
```

The `-v` flag prints each test name and its pass/fail result. Pytest discovers
any file named `test_*.py` and any function named `test_*` automatically — no
registration needed.

> Note: pytest runs in the project environment (conda `thesis-mlops`), not the
> base interpreter.

---

## Test inventory (per file)

| Test file | Tests | What it covers |
|---|---|---|
| `test_stage6_monitoring.py` | 16 | Stage 6 post-inference monitoring: confidence/uncertainty thresholds, dominance/collapse risk, drift (z-score, PSI), flip-rate, baseline age, entropy proxy |
| `test_stage7_trigger.py` | 14 | Stage 7 trigger policy: multi-signal voting, collapse→review guard, cooldown, consecutive-warning escalation, deploy/regression decisions |
| `test_pipeline.py` | 12 | End-to-end pipeline behavior |
| `test_api_upload_modes.py` | 10 | FastAPI upload paths / serving modes |
| `test_stage2_validation.py` | 8 | Stage 2 data validation (ranges, NaN/constant columns, window dims) |
| `test_stage3_transformation.py` | 7 | Stage 3 preprocessing: unit conversion, gravity removal, scaling, downsampling |
| `test_stage9_registration.py` | 6 | Stage 9 model registration gate + baseline update |
| `test_runtime_contract_consistency.py` | 5 | D1 runtime-contract assertions (scaler / label order / shape / baseline binding) |
| `test_stage5_evaluation_summary_contract.py` | 4 | Stage 5 evaluation summary contract (dominance fields, length/column checks, overlap math) |
| `test_stage8_retraining.py` | 3 | Stage 8 retraining config + fine-tune fields |
| `test_stage5_evaluation.py` | 3 | Stage 5 label-mapping consistency across entrypoints; fail-fast on inconsistent metadata |
| **Total** | **88** | across 11 files |

> Stage 11 (calibration) is an optional, non-defended stage; its test
> (`test_stage11_calibration.py`) is kept in `_archive/` and excluded from the
> defended suite.

Largest suites are the MLOps governance stages — Stage 6 monitoring (16) and
Stage 7 trigger (14) — reflecting the thesis focus on the governed lifecycle
around the model.

---

## conftest.py

Not a test file — a shared configuration pytest loads automatically before any
test runs. It provides reusable fixtures (e.g. `sample_sensor_data`,
`sample_predictions`, `sample_baseline_stats`, `degraded_monitoring_report`)
that generate synthetic data on the fly, so individual test files don't repeat
data-creation code. It imports no real pipeline code — only synthetic data.

---

## Notes

- `test_runtime_contract_consistency.py` is the defense-critical suite: it
  asserts the deployed D1 contract (scaler, label order, input shape, baseline
  binding) stays internally consistent.
- All tests use synthetic fixtures or small inline data; no test depends on the
  raw recordings, the archived experiment notebooks, or `scripts/` tooling.

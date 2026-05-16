# Release Notes

## Master Release Candidate - 2026-05-16

Source branch note: the working tree was inspected from `audit/stage1-7-manual-check`, not from a clean checked-out `master`, because the repository currently contains many pre-existing modified/deleted files. This release note records the intended master release baseline after the current documentation/runtime-contract sync is merged.

### Runtime Baseline

- Defended runtime model: `models/runtime_contract/model_a_final_20260508/fine_tuned_clean_model.keras`
- Runtime contract: unit conversion when needed, Garmin train-only StandardScaler, row-wise `(200, 6)` windows, fixed 11-class label order.
- Core defended path: Stage 1-7 only.
- Gated mutation path: Stage 8-10 require labels, QA/review, and promotion evidence.
- Optional extension: Stage 11 calibration/uncertainty remains research/future-work unless explicitly run and reported.
- Removed from active runtime: AdaBN, TENT, and pseudo-label adaptation hooks.

### Fresh Verification Runs

| Run | Input | Status | Windows | Mean confidence | Top class | Uncertain | Drift | Trigger | Accuracy |
| --- | --- | --- | ---: | ---: | --- | ---: | --- | --- | ---: |
| `20260516_013345` | User 7 labeled CSV | `SUCCESS (7/7)` | 989 | 35.9% | `nape_rubbing` 16.5% | 80.5% | 0.164 HEALTHY | REVIEW | 37.6% |
| `20260516_013406` | User 7 unlabeled CSV | `SUCCESS (7/7)` | 989 | 35.9% | `nape_rubbing` 16.5% | 80.5% | 0.164 HEALTHY | REVIEW | n/a |

### Release Interpretation

- The previous labeled User 7 Stage 5 crash is no longer present in the current code path.
- Labeled and unlabeled User 7 inference outputs are deterministic and match, as expected.
- The high uncertainty rate is a model-confidence/generalization signal, not a stale-label or drift failure.
- The unlabeled run correctly keeps `production_y_path=null` and does not reuse stale labeled artifacts.
- `CRITICAL` monitoring severity still routes to `REVIEW`; it does not imply automatic retraining.

### Deferred Work

- May 17 or May 18, 2026: run a controlled Stage 11 calibration experiment with a labeled User 7 calibration/test split.
- Use User 7 augmentation only as calibration/sensitivity support unless a separate real held-out set is preserved.
- Do not lower the uncertainty threshold from `0.50` unless a calibration/coverage study justifies it.


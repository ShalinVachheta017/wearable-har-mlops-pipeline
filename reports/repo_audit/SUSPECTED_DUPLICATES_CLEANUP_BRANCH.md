# Suspected Duplicate Code Paths (Not Deleted)

Date: 2026-03-27
Branch: chore/repo-cleanup

Purpose: list duplicate-looking code paths that were reviewed but intentionally not deleted during root cleanup.

## Findings

| Suspected duplicate file | Source-of-truth candidate | Where imported/used | Safe to remove now? |
|---|---|---|---|
| `src/components/curriculum_pseudo_labeling.py` | `src/curriculum_pseudo_labeling.py` | `src/pipeline/production_pipeline.py:604` imports component wrapper; wrapper imports core module | **No** (wrapper still used by stage orchestration) |
| `src/components/wasserstein_drift.py` | `src/wasserstein_drift.py` | `src/pipeline/production_pipeline.py:581` imports component wrapper; wrapper imports core module | **No** (wrapper used by pipeline) |
| `src/components/sensor_placement.py` | `src/sensor_placement.py` | `src/pipeline/production_pipeline.py:625` imports component wrapper; wrapper imports core module | **No** (wrapper used by pipeline) |
| `src/components/post_inference_monitoring.py` and `scripts/post_inference_monitoring.py` | likely split: `src/components/post_inference_monitoring.py` as pipeline adapter, `scripts/post_inference_monitoring.py` as monitoring implementation | `src/pipeline/production_pipeline.py:445` imports component wrapper; historical docs reference script path | **No** (needs targeted architectural review first) |

## Cleanup Decision

- No duplicate code path was deleted in this pass.
- Root cleanup focused on file placement and documentation clarity only.
- Any duplicate removal should be done in a separate, test-backed change.

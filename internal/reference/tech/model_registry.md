# Model Registry and Rollback

## What it is

A model registry stores model versions and deployment state, and supports rollback to previously known versions.

## Why it is used in this thesis

It provides governance for post-retraining model promotion and supports safe recovery if a new model underperforms.

## Repository locations

- `src/components/model_registration.py`
- `src/model_rollback.py`
- `models/registry/model_registry.json`
- `models/registry/har_model_vauto.keras`

## Role in this project

- Core:
  - Used in stage 9 when retraining branch is enabled and gate conditions are met.
- Optional:
  - Not required for pure stages 1-7 monitoring runs.
- Future work:
  - Stronger policy checks and richer deployment metadata in registry history.

# MLflow

## What it is

MLflow tracks experiments, metrics, parameters, artifacts, and model versions for machine learning workflows.

## Why it is used in this thesis

MLflow provides an auditable evidence trail for experiments and pipeline runs, which supports thesis reproducibility and defense claims.

## Repository locations

- `src/mlflow_tracking.py`
- `config/mlflow_config.yaml`
- `mlruns/`
- `docker-compose.yml` (MLflow service)

## Role in this project

- Core:
  - Experiment/evidence tracking for training and pipeline outcomes.
- Optional:
  - Some local debugging runs can still execute without remote tracking server setup.
- Future work:
  - Enforce stricter artifact governance and retention policies for long-term archival.

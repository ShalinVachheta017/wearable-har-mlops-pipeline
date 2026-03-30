<!-- markdownlint-disable MD060 -->

# Experiment Tracking (End-to-End Lineage)

This document explains experiment tracking as a cross-cutting thesis capability.

---

## 1. What Experiment Tracking Means (General Concept)

Experiment tracking is the practice of recording:

- model/training configuration,
- data version,
- code version,
- metrics and artifacts,
- deployment/registry outcomes.

The goal is reproducibility and defensible comparison.

---

## 2. General Pseudocode (Lineage Pattern)

```text
SELECT code_version
SELECT data_version

START tracked_run
    log parameters
    train/evaluate model
    log metrics
    log artifacts (model, plots, reports)
END tracked_run

STORE run outputs with run_id/timestamp
ENABLE query: best_run, compare_runs, reproduce_run
```

### Explanation

- Reproducibility requires synchronized tracking across code, data, and artifacts.
- A single tracking system is often insufficient; layered tracking is common in MLOps.
- Run IDs and timestamps must be stable references for auditability.

---

## 3. Thesis-Centric Pseudocode (Current Repository)

```text
CODE LINEAGE:
    Git commit/branch history

DATA/MODEL LINEAGE:
    DVC pointers (.dvc files) + configured remote

EXPERIMENT LOGGING:
    MLflowTracker in src/mlflow_tracking.py
    tracking_uri + experiment_name from config/mlflow_config.yaml

PIPELINE ARTIFACT LINEAGE:
    ArtifactsManager creates artifacts/<timestamp>/stage_dirs
    run metadata written to run_info.json

PIPELINE ENTRY:
    run_pipeline.py executes stages and persists outputs
```

### Thesis-Centric Explanation

- This repo implements layered lineage, not a single monolithic tracker.
- MLflow tracks experiment metadata and model/evaluation artifacts.
- DVC tracks large data/model inputs.
- Artifacts manager records stage-wise pipeline outputs by timestamp.

---

## 4. Repository Locations

- `src/mlflow_tracking.py`
- `config/mlflow_config.yaml`
- `.dvc/config`
- `data/raw.dvc`
- `data/processed.dvc`
- `data/prepared.dvc`
- `models/pretrained.dvc`
- `src/utils/artifacts_manager.py`
- `run_pipeline.py`
- `artifacts/`

---

## 5. What We Use Here

- MLflow run lifecycle + metrics/params/artifact logging.
- DVC pointer-based data/model versioning.
- Timestamped pipeline artifact directories.
- Stage summaries persisted as JSON reports.

---

## 6. What Is Not Fully Used Yet

- Strict automated linkage of every run to an immutable release tag by policy.
- Centralized enterprise artifact governance workflows.
- Fully automated end-to-end promotion from best run to production deployment.

These are growth directions, not blockers for current thesis reproducibility claims.

---

## 7. Lineage Graph

```mermaid
graph TD
    Git[Code Version (Git)] --> Run[Pipeline Run]
    DVC[Data/Model Version (DVC)] --> Run
    Run --> MLflow[Experiment Metadata + Artifacts]
    Run --> Artifacts[artifacts/<timestamp>/...]
    Run --> Registry[Model Registration / Rollback]
```

---

## 8. Role in This Thesis

- **Core role:** supports reproducibility and evidence-backed evaluation.
- **Optional role:** advanced governance workflows can be layered later.
- **Defense role:** provides traceable answers for "which code/data/model produced this result?".

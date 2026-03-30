<!-- markdownlint-disable MD060 -->

# Reproducibility

This standalone deep dive explains reproducibility as a first-class thesis requirement.
It connects reproducibility theory to concrete controls implemented in this repository.

---

## 1. What Reproducibility Means (General Concept)

Reproducibility means that the same inputs, code, and configuration produce equivalent results across runs.

For MLOps systems this usually requires:

- versioned data and model artifacts,
- versioned code and configuration,
- controlled execution environment,
- run metadata and result traceability.

---

## 2. General Pseudocode (Reproducibility Contract)

```text
PIN code version
PIN data/model artifact versions
PIN runtime environment and dependencies
PIN configuration values

EXECUTE pipeline
LOG parameters, metrics, and artifacts
STORE run outputs with immutable identifiers

TO reproduce:
  restore code + artifacts + environment + config
  rerun workflow
  compare outputs within accepted tolerance
```

### Explanation

- Reproducibility is a system contract, not a single tool feature.
- Provenance must include code, data, model, and environment together.
- Logging and artifact storage are needed to verify reruns.

---

## 3. Reproducibility Stack in This Thesis

This repository composes reproducibility across multiple layers:

- **Git** for code state.
- **DVC** for dataset/model artifact pointers and storage sync.
- **MLflow** for run metadata, metrics, and experiment artifacts.
- **Docker** for repeatable runtime environments.
- **Pipeline artifacts** for stage-by-stage outputs.
- **Model registry** for deployed model version traceability.

---

## 4. Data and Model Artifact Reproducibility (DVC)

DVC pointer files tracked in Git:

- `data/raw.dvc`
- `data/processed.dvc`
- `data/prepared.dvc`
- `models/pretrained.dvc`

These pointers store hash and size metadata, allowing artifact restoration for a commit-aligned state.

---

## 5. Experiment Reproducibility (MLflow)

`src/mlflow_tracking.py` and `config/mlflow_config.yaml` provide:

- run lifecycle management,
- parameter logging,
- epoch/final metric logging,
- artifact logging (reports, plots, model files),
- best-run and run-comparison querying.

This enables thesis claims to be tied to explicit run evidence.

---

## 6. Environment Reproducibility (Docker)

- `docker/Dockerfile.inference` defines serving runtime.
- `docker/Dockerfile.training` defines training/preprocessing runtime.
- `docker-compose.yml` provides consistent local multi-service orchestration.

Containerized environments reduce machine-specific drift.

---

## 7. Pipeline and Configuration Reproducibility

Execution controls include:

- stage-based orchestration through `run_pipeline.py`,
- centralized config in `config/pipeline_config.yaml` and `config/pipeline_overrides.yaml`,
- timestamped outputs under `artifacts/` and `outputs/`.

These controls preserve execution context and intermediate evidence.

---

## 8. Deployment Reproducibility and Version Traceability

- CD workflow publishes version-tagged inference images.
- `src/model_rollback.py` and `models/registry/model_registry.json` preserve deployed model lineage.

This allows reproducible deployment-state reconstruction, not only training-state reconstruction.

---

## 9. Thesis-Centric Pseudocode (Exact Repository Flow)

```text
SELECT target commit
RESTORE DVC artifacts for commit pointers
LOAD pipeline configuration files
RUN pipeline stages via run_pipeline.py

FOR training/evaluation runs:
  log params/metrics/artifacts in MLflow

FOR deployment state:
  use registry history and current model pointer

COMPARE rerun outputs against prior artifacts/reports
```

### Thesis-Centric Explanation

- Reproducibility here is multi-layer and evidence-backed.
- The design supports both scientific repeatability and operational traceability.

---

## 10. Reproducibility Evidence Checklist

Minimum evidence for a reproducible claim:

1. Commit id for code state.
2. DVC pointer state for data/model artifacts.
3. Config snapshot used for run.
4. MLflow run id with metrics and artifacts.
5. Generated stage outputs and reports.
6. Model registry/deployment state if production claim is included.

---

## 11. What We Use Here

- DVC pointer-based artifact versioning.
- MLflow experiment tracking and artifact retention.
- Dockerized runtime definitions.
- Stage outputs and report persistence.
- Local registry history for deployed model tracking.

---

## 12. Reproducibility Capabilities Not Fully Used Yet

- Fully deterministic seed policy enforced across every execution path.
- Immutable lockfile and container digest pinning for every release artifact.
- Automated reproducibility regression tests in CI.
- External long-term artifact registry with governance policies.

---

## 13. Role in This Thesis

- **Core role:** underpins scientific credibility of experimental and operational results.
- **Evidence role:** supports defense with traceable and rerunnable artifacts.
- **Future role:** basis for stricter enterprise-grade reproducibility governance.

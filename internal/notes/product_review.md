# Product Owner / CTO Review — HAR MLOps Pipeline

**Audit date:** February 24, 2026  
**Reviewer role:** Senior MLOps Product Owner + CTO  
**Repository:** `ShalinVachheta017/MasterArbeit_MLops` (branch: `main`)  
**Pipeline version:** 2.1.0 (`pyproject.toml`)

---

## Legend

| Symbol | Meaning |
|:------:|---------|
| ✅ | Implemented **and** running / integrated end-to-end |
| 🟡 | Code / config exists but **not wired** into the running stack |
| 🔴 | Not implemented |
| 📌 | Measured result — cite date, hardware, dataset split |
| 🎯 | Target — not yet measured |
| ⚠️ Assumption | Claim is inferred, not proven by repo evidence |

---

## Assumptions & Scope Limits

> **Read this section before treating any claim below as an enterprise production guarantee.**

1. **Single-machine scope.** The entire stack runs on a single host via Docker Compose. No Kubernetes, no load balancing, no horizontal scaling has been tested or is implied.
2. **Local DVC remote.** Data versioning uses a local filesystem remote (`../.dvc_storage`). Cloud-backed reproducibility (S3/GCS/Azure) is not configured.
3. **Lab data only (production simulated).** Training and evaluation use 26 controlled lab recording sessions. “Production” runs are currently simulated via file-based batch ingestion; end-to-end live device→cloud streaming is not implemented.
4. **Retraining is manual.** The CI weekly drift check *detects* drift but does **not** automatically trigger retraining. The `--retrain` flag must be run manually. An automated CI loop is designed but not wired (see Roadmap item 4).
5. **Security not implemented.** No encryption at rest, no access controls, no GDPR-compliant audit trail. This is explicitly a thesis prototype. Any real-world deployment would require a full security review before handling wearable health data.
6. **Legacy planning metrics are not traceable.** The `val_acc 0.969 / F1 0.814` figures appear in an older planning note but are **not present in any MLflow run** (verified by searching `mlruns/`). Use the MLflow‑traceable 5‑fold CV results instead (mean val_accuracy ≈ **0.938**, f1_macro ≈ **0.939** on a window-level split; see §1).
7. **Latency figures are targets.** No benchmarked p95 latency measurement exists in the repo. The `≤ 250 ms` figure is a design target, not a measured SLO.

---

## Non-Functional Requirements (NFRs)

| NFR | Target | Status |
|-----|--------|:------:|
| **Latency** | p95 ≤ 250 ms per inference window (CPU, batch=1) | 🎯 Target |
| **Availability** | ≥ 99.5 % (weekly health-check gate) | 🎯 Target |
| **Reproducibility** | Any commit reproducible via `pip install + dvc pull + pytest` (requires access to local DVC remote `../.dvc_storage`) | 🟡 Process documented; DVC remote local-only |
| **Auditability** | Every training run logged in MLflow with params + metrics + artifacts | ✅ |
| **Data freshness** | Baseline staleness alert after 30 days | 🟡 Code exists, no live alert |
| **Label-free operability** | Detect drift + quality degradation without ground truth (proxy monitoring coverage ≥ 95%; false-trigger rate ≤ 1/week) | 🎯 Target |
| **Rollback time** | ≤ 5 minutes from critical alert to serving previous stable model | 🎯 Target |
| **Privacy / Security** | Encryption at rest; access controls; GDPR compliance | 🔴 Not implemented (thesis scope) |

---

## System Boundary Diagram

> **Purpose:** One-page visual showing what is inside the system, what flows in/out, who the users are, and what is explicitly out of scope. This is a standard CTO artifact for thesis appendices and architecture reviews.

```mermaid
flowchart TD
    subgraph INPUTS [" 📥 Inputs "]
        I1[Garmin IMU — raw Excel/CSV\n3-axis Accel + Gyro @ 50 Hz]
        I2[Researcher-uploaded CSV\nvia FastAPI web UI]
        I3[Reference baseline\nmodels/normalized_baseline.json]
    end

    subgraph PIPELINE [" ⚙️ Pipeline — 14 Stages (run_pipeline.py) "]
        S1[Stage 1: Data Ingestion\nsrc/components/data_ingestion.py]
        S2[Stage 2: Data Transformation\nwindowing · scaling · .npy]
        S3[Stage 3: Data Validation\nschema · range · missing]
        S4[Stage 4: Model Training\n1D-CNN-BiLSTM · 5-fold CV · MLflow]
        S5[Stage 5: Model Evaluation\nF1 · val_acc · per-class recall]
        S6[Stage 6: Model Registration\nlocal JSON registry · SHA256]
        S7[Stage 7: Inference\nFastAPI :8000 · /api/predict]
        S8[Stage 8: Post-Inference Monitoring\n3-layer: confidence · temporal · drift]
        S9[Stage 9: Trigger Policy\n2-of-3 vote · cooldown · tiered alert]
        S10[Stage 10: Model Retraining\nAdaBN · TENT · pseudo-label]
        S11[Stage 11 ●: Calibration\ntemperature scaling · ECE]
        S12[Stage 12 ●: Wasserstein Drift\nchange-point detection]
        S13[Stage 13 ●: Curriculum Pseudo-Labeling\nhigh-confidence-first · EWC]
        S14[Stage 14 ●: Sensor-Placement Analysis\nwrist placement robustness]
    end

    subgraph OUTPUTS [" 📤 Outputs "]
        O1[Predictions JSON\n11-class activity labels + confidence]
        O2[MLflow Experiments\nmlruns/ — params · metrics · artifacts]
        O3[Docker Image\nghcr.io inference container]
        O4[Monitoring Reports\noutputs/monitoring/ JSON]
        O5[Model Artifacts\nmodels/registry/ .keras + manifest]
        O6[DVC-tracked Data\n../.dvc_storage snapshots]
    end

    subgraph USERS [" 👤 Users "]
        U1[Clinical Researcher\nPOSTs CSV → reads predictions]
        U2[ML Engineer\nruns pipeline · reads MLflow]
        U3[MLOps / DevOps Engineer\nCI/CD · Docker · monitoring]
    end

    subgraph OUT_OF_SCOPE [" 🚫 Out of Scope (Thesis Prototype) "]
        X1[Privacy / GDPR compliance]
        X2[Kubernetes / horizontal scaling]
        X3[Real-time BLE streaming ingestion]
        X4[Multi-tenant / access controls]
        X5[Cloud DVC remote]
        X6[Automated retraining CI loop]
    end

    I1 --> S1
    I2 --> S7
    I3 --> S8
    S1 --> S2 --> S3 --> S4 --> S5 --> S6
    S6 --> S7 --> S8 --> S9
    S9 -->|CRITICAL trigger| S10
    S10 --> S6
    S4 -.->|\"--advanced flag\"| S11 & S12 & S13 & S14
    S7 --> O1
    S4 --> O2
    S6 --> O3
    S8 --> O4
    S6 --> O5
    S1 --> O6
    O1 --> U1
    O2 --> U2
    O3 --> U3
    O4 --> U3
```

> ● Stages 11–14 are activated only with `python run_pipeline.py --advanced`. Default CI runs stages 1–10 only.

---

## 1) Executive Summary

**What the product is.** This repository implements a production-grade MLOps pipeline for **anxiety-related behavior recognition** from wrist-worn IMU sensors (3-axis accelerometer + gyroscope). It classifies 11 activities (e.g., nail biting, hair pulling, sitting, smoking) from 4-second sliding windows (200 samples @ 50 Hz, 50 % overlap) using a 1D-CNN-BiLSTM model (⚠️ Assumption: ~499 K parameters — computed from architecture; `model.count_params()` now logged as `model_total_params` in MLflow fold-1 run at [src/train.py](src/train.py#L428), verifiable after next training run). The pipeline spans 14 orchestrated stages — from raw Garmin Excel ingestion through inference, 3-layer monitoring, automated retraining triggers, domain adaptation (AdaBN / TENT / pseudo-labeling), model registration with rollback, and advanced analytics (calibration, Wasserstein drift, 🟡 curriculum pseudo-labeling, 🟡 sensor-placement augmentation — both wired via `--advanced` flag but not activated in default CI runs; see [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py)).

**Key differentiation: scalable MLOps for *unlabeled* production data.** Unlike a classic “train once, deploy once” thesis, this pipeline is explicitly designed for the real production constraint that **incoming wearable data is typically unlabeled**. It therefore treats *monitoring signals as proxy supervision* (confidence/entropy/flip‑rate + drift + OOD), and uses those signals to:
- decide **when** to retrain (trigger policy),
- decide **how** to adapt (AdaBN / TENT / pseudo‑labeling), and
- decide **whether** to promote or rollback a candidate model (registration gate + safe rollback).

**Scalability posture (within thesis scope).** The current implementation runs on a single host, but it is structured as modular stages + stateless inference service, which is the typical foundation for scaling later (separate compute for ingestion, inference, monitoring, and retraining; external state store for triggers; containerized deployment).

**Who it serves.** Clinical researchers studying anxiety-related behaviors, wearable-device product teams, and ultimately end-users wearing Garmin devices whose data is classified in near-real-time via a FastAPI service.

**What success means.** A closed-loop system that (a) detects behavioral patterns reliably (🎯 targets: macro F1 ≥ 0.80, val_accuracy ≥ 0.96; 📌 current MLflow baseline: window‑level 5‑fold CV mean val_accuracy ≈ **0.938**, f1_macro ≈ **0.939** on CPU; ⚠️ subject‑wise generalization not yet measured), (b) detects and adapts to data drift autonomously, and (c) is reproducible, versioned, and deployable by a single command.

> **📌 MLflow-traceable training metrics (verified Feb 24, 2026):**
>
> | MLflow Experiment | ID | Run ID (sample) | val_accuracy | f1_macro |
> |-------------------|----|-----------------|:------------:|:--------:|
> | `har-retraining` | `909768134748430965` | `ea61a55b` (cv_fold_1) | 0.9351 | 0.9355 |
> | `har-retraining` | `909768134748430965` | `87ed2c16` (cv_fold_2) | 0.9468 | 0.9474 |
> | `har-retraining` | `909768134748430965` | `eef69197` (cv_fold_3) | 0.9455 | 0.9462 |
> | `har-retraining` | `909768134748430965` | `840d8c36` (cv_fold_4) | 0.9286 | 0.9295 |
> | `har-retraining` | `909768134748430965` | `8da36319` (cv_fold_5) | 0.9364 | 0.9370 |
>
> **Mean (5-fold CV):** val_accuracy ≈ **0.938**, f1_macro ≈ **0.939**.
> **Metric paths:** `mlruns/909768134748430965/<run_id>/metrics/val_accuracy` and `.../f1_macro`
> **Hardware:** CPU-only, single machine. **Split:** `StratifiedKFold(n_splits=5)` on shuffled windows — NOT subject-wise.
>
> ⚠️ **Note on 0.969 / 0.814 figures:** These values from `Thesis_report/things to do/CHATGPT_2_PIPELINE_WORK_DONE.md` §A3 are **not traceable to any MLflow run**. The planning doc predates proper MLflow logging. The authoritative figures above (from actual logged runs) should be used in the thesis.

> ⚠️ **Split strategy note:** Current training uses `StratifiedKFold` on shuffled windows ([src/train.py](src/train.py#L397)), not subject-wise or group k-fold. This can inflate accuracy figures because windows from the same user appear in both train and validation folds. A subject-wise evaluation is required for credible generalization claims in wearable HAR (see Risk R11).

### Top 3 Strengths

| # | Strength | Evidence |
|---|----------|----------|
| S1 | ✅ **Full lifecycle coverage (14 stages)** — one of the most complete thesis-grade pipelines reviewed. | [run_pipeline.py](run_pipeline.py#L1-L44) defines stages 1-14; [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py#L58-L71) lists `ALL_STAGES`. |
| S2 | 🟡 **3-layer monitoring + automated trigger policy** — monitoring logic and trigger policy engine implemented; Prometheus/Grafana not live (see R3). | [src/trigger_policy.py](src/trigger_policy.py#L1-L35) documents the multi-metric voting; [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py#L1-L10). |
| S3 | ✅ **225/225 tests passing, CI/CD with weekly model-health check** — hard-fail unit tests, lint, smoke test against Docker image, scheduled drift check. | [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) (350 lines); [pytest.ini](pytest.ini). |

### Top 3 Risks

| # | Risk | Evidence |
|---|------|----------|
| R1 | **No gated deployment approval** — `auto_deploy` defaults to `False` but there is no human-in-the-loop approval gate enforced in CI; anyone with push access can override. The `is_better` check for TTA/AdaBN runs falls back to `True` (no labeled holdout to compare). **Recommended fix:** require confidence stability + holdout proxy metric gate before promotion to `current_model.keras`. | [src/components/model_registration.py](src/components/model_registration.py#L85-L100) — `is_better = True` fallback for TTA runs; no PR-review requirement in CI for deploy. |
| R2 | **Evaluation + documentation inconsistency (thesis risk)** — README/Chapter status implies “no results yet,” but MLflow contains 5‑fold **window‑level** CV runs (mean val_accuracy ≈ **0.938**, f1_macro ≈ **0.939**). Risk: the report can be challenged unless results are consolidated, exported, and **re-evaluated subject‑wise** (GroupKFold/LOSO) with ablations (baseline vs AdaBN vs TENT). | [README.md](README.md#L23-L26) status text; MLflow paths listed in §1 (`mlruns/909768134748430965/<run_id>/metrics/*`). |
| R3 | **Prometheus/Grafana not wired to running application** — alert rules and dashboards exist as config files but are not integrated into the Docker Compose stack or CI. | [README.md](README.md#L92): "Prometheus/Grafana: Config ready, not wired to app"; `docker-compose.yml` has no Prometheus/Grafana service. |

---

## 2) Business Needs → OKRs → KPIs

### Proposed OKRs

| # | Objective | Key Results (KR) | Measured Where |
|---|-----------|-------------------|----------------|
| OKR-1 | **Deliver reliable anxiety-behavior classification to researchers** | KR1a: Macro F1 ≥ 0.80 on held-out fold. KR1b: Per-class recall ≥ 0.60 for all 11 classes. | MLflow experiment `har-retraining` (ID: `909768134748430965`) ([config/mlflow_config.yaml](config/mlflow_config.yaml#L17)); key metrics: `val_accuracy`, `f1_macro` (see §1 metric paths). Per-class recall should be stored as an artifact (classification report / confusion matrix) from [src/train.py](src/train.py). |
| OKR-2 | **Ensure production uptime and latency** | KR2a: 🎯 API p95 latency ≤ 250 ms per window (CPU, batch=1) — target, not yet benchmarked. KR2b: 🎯 Health-check availability ≥ 99.5 % (weekly) — target, measured by CI schedule. | Prometheus histogram `har_inference_latency_seconds` ([src/prometheus_metrics.py](src/prometheus_metrics.py#L126-L131)) — metric defined but not scraped live; `/api/health` endpoint ([src/api/app.py](src/api/app.py#L68)). |
| OKR-3 | **Operate safely on *unlabeled* production data with bounded risk** | KR3a: 🎯 Drift / degradation detected within 100 inference batches (proxy signals). KR3b: 🎯 Trigger→candidate model registered within 24 h (manual today; automated later). KR3c: 🎯 Rollback to last stable model within 5 min on CRITICAL. KR3d: 🎯 ≤ 1 false retrain trigger/week (to avoid churn). | Proxy monitoring reports ([src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py)) + trigger state `logs/trigger/trigger_state.json` ([src/trigger_policy.py](src/trigger_policy.py#L136)) + model registry and rollback logic ([src/model_registry.py](src/model_registry.py); [src/model_rollback.py](src/model_rollback.py)). |
| OKR-4 | **Maintain full reproducibility** | KR4a: Any commit reproducible from `pip install + dvc pull + pytest`. KR4b: 0 test failures on CI for every push to `main`. | DVC tracked data ([.dvc/config](.dvc/config)); CI test job ([.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml#L77-L105)). |
| OKR-5 | **Complete thesis deliverables on time** | KR5a: All experiments logged by March 2026. KR5b: Thesis draft complete by April 2026. | **Assumption** — no automated tracking of writing progress in repo. README mentions "~70 % of chapters remain". |

---

## 3) Lifecycle Coverage Map (MLOps End-to-End)

**Status key:** ✅ Running end-to-end · 🟡 Code/config exists, not integrated · 🔴 Not implemented

| Stage | Status | Repo Evidence | Gaps / Risks | Next Action |
|-------|:------:|---------------|--------------|-------------|
| **Business Needs** | 🟡 | [README.md](README.md#L80-L89) describes the classification problem. OKRs not formally documented. | No formal OKR/SLO document in repo. | Add `docs/OKRS_AND_SLOS.md` defining measurable targets. |
| **Data Collection** | ✅ | [src/components/data_ingestion.py](src/components/data_ingestion.py) — handles Garmin Excel/CSV, sensor fusion at 50 Hz, manifest tracking. | Data sourced from 26 controlled lab sessions; no continuous or streaming production data pipeline. | Plan real-time data ingestion from Garmin Connect API or BLE gateway for production use. |
| **Data Preparation** | ✅ | [src/components/data_transformation.py](src/components/data_transformation.py) — unit conversion, gravity removal toggle, windowing to `.npy`. [config/pipeline_config.yaml](config/pipeline_config.yaml) controls preprocessing. | Preprocessing matches training pipeline (documented); no automated data quality dashboard. | Wire data validation stats to MLflow/Grafana dashboard. |
| **Admin / Setup** | ✅ | [pyproject.toml](pyproject.toml) (v2.1.0), [config/requirements-lock.txt](config/requirements-lock.txt) (578 pinned packages), [setup.py](setup.py). Conda/pip install documented. | No `.env.example` or secrets management guidance. | Add `.env.example` and document secret handling for MLflow remote. |
| **Model Development** | ✅ | [src/train.py](src/train.py) — 5-fold `StratifiedKFold` on windows ([src/train.py](src/train.py#L397)), 1D-CNN-BiLSTM v1/v2 (⚠️ Assumption: ~499 K params computed from architecture; will be confirmed via MLflow param `model_total_params` logged from `model.count_params()`), MLflow tracking, domain adaptation hooks. | **⚠️ Window-level stratified split, not subject-wise** — results may be optimistic (see Risk R11). Only one architecture tested; no hyperparameter sweep logged. | Run subject-wise GroupKFold evaluation; run systematic HPO and log to MLflow. |
| **Version Control** | ✅ | Git + DVC ([.dvc/config](.dvc/config) → local storage), MLflow experiment tracking ([src/mlflow_tracking.py](src/mlflow_tracking.py)), model registry ([models/registry/model_registry.json](models/registry/model_registry.json)). | DVC remote is local (`../.dvc_storage`); not cloud-backed. | Configure a cloud DVC remote (S3/GCS/Azure Blob) for team collaboration. |
| **CI** | ✅ | [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) — lint (flake8, black, isort), unit tests with coverage, slow TF tests (non-blocking), Docker build + push to `ghcr.io`. | No `mypy` type-checking step in CI; slow tests are non-blocking. | Add `mypy src/` as a CI lint step; consider making slow tests blocking. |
| **Deployment** | 🟡 | Docker Compose ([docker-compose.yml](docker-compose.yml)) with MLflow + inference services. Dockerfile ([docker/Dockerfile.inference](docker/Dockerfile.inference)) with health check. Image pushed to `ghcr.io`. Blue-green/canary logic in [src/deployment_manager.py](src/deployment_manager.py). | **Blue-green/canary code exists but is not wired to CI.** No Kubernetes/Helm manifests. No staging → production gate enforced. | Wire `deployment_manager.py` into CI for staging deployments; add GitHub Environments approval gate. |
| **Monitoring** | 🟡 | 3-layer monitoring logic ✅ running ([src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py)); Prometheus metrics **defined** but not scraped ([src/prometheus_metrics.py](src/prometheus_metrics.py)); Grafana dashboard JSON exists ([config/grafana/har_dashboard.json](config/grafana/har_dashboard.json)) but **not deployed**; alert rules exist ([config/alerts/har_alerts.yml](config/alerts/har_alerts.yml)) but **no Alertmanager**. | Live Prometheus scraping, Grafana, Alertmanager all missing from Docker Compose stack. | Add `prometheus` + `grafana` services to `docker-compose.yml`; wire `/metrics` endpoint; configure Alertmanager. |
| **Retraining / Adaptation** | 🟡 | 4 adaptation methods implemented: AdaBN, TENT, AdaBN+TENT, pseudo-label ([src/components/model_retraining.py](src/components/model_retraining.py)). Trigger policy engine ✅ implemented ([src/trigger_policy.py](src/trigger_policy.py)). **Retraining is manually invoked via `--retrain` flag.** CI weekly job runs drift check only. | DANN/MMD referenced but raise `NotImplementedError`. No automated CI loop that reads trigger state and fires retraining. | Add `.github/workflows/auto-retrain.yml` that reads `trigger_state.json` and runs `--retrain` on CRITICAL. |
| **Rollback** | 🟡 | [src/model_rollback.py](src/model_rollback.py) — local ModelRegistry with SHA256 hashing, version history, deploy/rollback commands. Tested ([tests/test_model_rollback.py](tests/test_model_rollback.py)). | Registry is file-based JSON (`models/registry/model_registry.json`); `current_version` is `null` — no model has been formally deployed. No MLflow Model Registry integration. | Promote model to `current_version` in registry; integrate with MLflow Model Registry staging gates. |

---

## 4) Maturity Assessment

### A) Google MLOps Levels (Sculley et al. 2015; Google Cloud Best Practices)

| Level | Description | Assessed? | Evidence |
|-------|-------------|:---------:|----------|
| **Level 0 — Manual** | Manual training, manual deployment, no CI. | Surpassed | CI exists, training is scriptable. |
| **Level 1 — ML Pipeline Automation** | End-to-end pipeline orchestrated; data and model tracked; CI/CD in place; automated testing. | **✅ Current** | 14-stage orchestrated pipeline ([run_pipeline.py](run_pipeline.py)); DVC data versioning; MLflow experiment tracking; CI with lint + test + build + smoke test + weekly model check ([.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml)). |
| **Level 2 — CI/CD + Automated Training** | Fully automated retraining triggered by data/drift signals; automated model validation and deployment without human intervention. | **Partially** | Trigger policy and retrain code exist but are not yet wired to an automated CI loop. No automated deployment gate. |

**Current maturity: Level 1 (solid), approaching Level 2.**  
**To reach Level 2:** (1) Wire trigger-policy output to a scheduled CI job that auto-retrains; (2) integrate MLflow Model Registry staging gates; (3) add Prometheus/Grafana live monitoring.

### B) Microsoft MLOps Maturity Model

| Level | Description | Assessed? | Evidence |
|-------|-------------|:---------:|----------|
| 0 — No MLOps | No automation. | Surpassed | — |
| 1 — DevOps but no MLOps | CI/CD for code but no ML specifics. | Surpassed | — |
| 2 — Automated Training | Training automated, experiment tracking, reproducibility. | **✅ Current** | Automated training via `src/train.py` with MLflow; DVC reproducibility; 5-fold CV. |
| 3 — Automated Model Deployment | Model deployment automated, canary/blue-green, registry stages. | **Partial** | Docker image built and pushed in CI. Rollback manager and deployment manager exist. But no staging → production gate in CI. |
| 4 — Full Automated Retraining + Ops | Drift detection triggers retraining; monitoring drives deployment decisions. | **Partially designed** | All code building blocks are present: drift detection, trigger policy, retraining, registration, baseline update. But the closed-loop automation is not yet wired end-to-end in CI. |

**Current maturity: Microsoft Level 2, with Level 3-4 components designed but not fully operational.**  
**To reach Level 3:** (1) Add a deployment-approval step in CI (GitHub Environments with required reviewers); (2) wire Docker build → staging → smoke test → production promotion.  
**To reach Level 4:** (1) Scheduled drift check already exists (Monday 06:00 UTC CI cron); (2) connect trigger decision to automated retrain-and-deploy job.

### C) Amazon MLOps Maturity (Initial → Repeatable → Reliable → Scalable)

| Level | Assessed? | Evidence |
|-------|:---------:|----------|
| Initial | Surpassed | — |
| **Repeatable** | **✅ Current** | Pinned dependencies (578 packages), DVC-tracked data, reproducible 3-command quickstart. |
| Reliable | Partial | 225 tests pass; weekly CI health check; monitoring exists but Prometheus/Grafana not live. |
| Scalable | Not yet | Single-machine Docker Compose; no K8s, no auto-scaling, no multi-tenant support. |

**CTO-style conclusion:** *Current maturity = Google Level 1 / Microsoft Level 2 / Amazon "Repeatable" because the pipeline is fully orchestrated, versioned, tested, and has CI/CD with Docker image publishing. Reaching next maturity (Google Level 2 / Microsoft Level 3-4 / Amazon "Reliable → Scalable") requires: (A) wiring the trigger-policy retraining loop into CI, (B) adding a deployment-approval gate, (C) integrating live Prometheus/Grafana monitoring, and (D) optionally moving to Kubernetes for horizontal scaling.*

---

## 5) Operating Model (Roles + RACI)

### Defined Roles

| Role | Abbreviation | Typical Responsibility |
|------|:---:|------------------------|
| Product Owner / Business Analyst | PO | Defines KPIs, acceptance criteria, prioritizes backlog |
| Data Engineer | DE | Data pipelines, DVC, data quality |
| ML Engineer | MLE | Model development, training, evaluation |
| MLOps / DevOps Engineer | OPS | CI/CD, Docker, deployment, monitoring infra |
| QA / Test Lead | QA | Test design, integration tests, smoke tests |
| Security / Compliance | SEC | Access controls, audit, governance |

### RACI Matrix

| Activity | PO | DE | MLE | OPS | QA | SEC |
|----------|:--:|:--:|:---:|:---:|:--:|:---:|
| **Data quality** (validation thresholds) | A | R | C | I | C | I |
| **Model training** (hyperparams, CV) | C | I | R | I | I | I |
| **Deployment approval** | A | I | C | R | C | C |
| **Monitoring alerts** (threshold tuning) | I | I | C | R | I | I |
| **Rollback decision** | A | I | C | R | I | C |
| **Retraining trigger thresholds** | C | I | R | C | I | I |

> R = Responsible, A = Accountable, C = Consulted, I = Informed

**Repo evidence for implied responsibilities:**
- [config/pipeline_config.yaml](config/pipeline_config.yaml) — preprocessing toggles imply MLE ownership.
- [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) — CI maintenance implies OPS ownership.
- [src/trigger_policy.py](src/trigger_policy.py#L87-L120) — threshold dataclass with 17 configurable parameters implies MLE + OPS co-ownership.
- **Gap:** No `CODEOWNERS` file, no documented on-call rotation, no escalation policy.

---

## 6) Release Governance & Quality Gates

### Current Quality Gates

| Gate | Mechanism | Pass Criteria | Evidence |
|------|-----------|---------------|----------|
| **Code quality** | flake8, black, isort in CI | Zero critical lint errors; formatting consistent. | [ci-cd.yml](.github/workflows/ci-cd.yml#L48-L66) |
| **Unit tests** | pytest (fast, no TF) | All non-slow tests pass, coverage uploaded. | [ci-cd.yml](.github/workflows/ci-cd.yml#L77-L105) |
| **Slow / TF tests** | pytest (slow marker) | Non-blocking (`continue-on-error: true`). | [ci-cd.yml](.github/workflows/ci-cd.yml#L112-L141) |
| **Docker build** | Build + push to `ghcr.io` | Image builds successfully. | [ci-cd.yml](.github/workflows/ci-cd.yml#L147-L199) |
| **Smoke test** | Container health check + `/api/health` + `scripts/inference_smoke.py` | API responds, predictions returned. | [ci-cd.yml](.github/workflows/ci-cd.yml#L205-L260) |
| **Scheduled model validation** | Weekly Monday 06:00 UTC cron | Tests pass + drift check completes. | [ci-cd.yml](.github/workflows/ci-cd.yml#L271-L318) |

### What Is Missing (Gated Approval)

| Gap | Impact | Proposed Implementation |
|-----|--------|------------------------|
| **No PR approval required for `main`** | Anyone with push access can deploy. | Add GitHub branch protection: require 1 reviewer + passing CI before merge to `main`. |
| **No staging environment** | Docker image goes directly to "latest". | Use GitHub Environments (`staging`, `production`) with required reviewers before the `docker push` step. |
| **Slow tests are non-blocking** | Model-loading bugs could slip through. | Change `continue-on-error` to `false` on slow tests or add a separate "must-pass" model-loading test. |
| **No model metric gate** | A retrained model with lower accuracy can be registered. | In `model_registration.py`, enforce `is_better` check strictly; fail registration if accuracy degrades beyond threshold. |

---

## 7) Observability & Monitoring Review

### What Is Monitored

| Signal | Mechanism | Storage | Evidence |
|--------|-----------|---------|----------|
| **Prediction confidence** | Layer 1: mean confidence, entropy, uncertain ratio. | JSON reports in `outputs/monitoring/`. | [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py) |
| **Temporal patterns** | Layer 2: flip rate, dwell time, transition frequency. | Same JSON reports. | Same component. |
| **Data drift** | Layer 3: per-channel z-score of mean shift vs. normalized baseline. | Same JSON reports. | Same component; baseline from [models/normalized_baseline.json](models/normalized_baseline.json). |
| **Wasserstein drift** | Per-channel Wasserstein distance + change-point detection. | Outputs from Stage 12. | [src/wasserstein_drift.py](src/wasserstein_drift.py) |
| **OOD detection** | Energy-based OOD scoring. | Logged per-batch. | [src/ood_detection.py](src/ood_detection.py) |
| **Calibration quality** | Temperature scaling, ECE, Brier score, reliability diagrams. | Stage 11 outputs. | [src/calibration.py](src/calibration.py) |
| **Infrastructure** | Prometheus metric definitions (latency, throughput, batch time). | **Defined but not scraped** — no live Prometheus server. | [src/prometheus_metrics.py](src/prometheus_metrics.py); [config/prometheus.yml](config/prometheus.yml) |

### Operating Without Labels (Production Reality)

In production, ground truth labels are absent or delayed. The pipeline therefore uses a **proxy-supervision strategy**:

- **Proxy metrics** (confidence, entropy, flip-rate, drift distance, OOD energy) serve as *early warning signals*.
- A **trigger policy** aggregates signals (2-of-3 voting) to reduce false alarms before escalating to CRITICAL.
- Retraining uses **adaptation methods** (AdaBN/TENT) and, optionally, **pseudo-labeling**. Promotion must be gated by a safety check (holdout where labels exist, or at minimum: proxy improvement + stability + rollback readiness).

**Recommended (lightweight) human-in-the-loop:** export a small daily/weekly batch of **high-uncertainty** windows for labeling to validate proxy→performance correlation and to prevent pseudo-label feedback loops. This can be implemented as a new pipeline step that writes `outputs/labeling_queue/*.csv` containing window metadata (timestamp, user/session, predicted class, confidence, drift score).

### Alert Rules (Defined but Not Active)

| Alert | Condition | Severity | Evidence |
|-------|-----------|----------|----------|
| HARLowConfidence | `har_confidence_mean < 0.75` for 5 min | Warning | [config/alerts/har_alerts.yml](config/alerts/har_alerts.yml#L12-L22) |
| HARHighEntropy | `har_entropy_mean > 1.5` for 5 min | Warning | Same file |
| HARHighFlipRate | `har_flip_rate > 0.15` for 10 min | Warning | Same file |
| HARDataDriftDetected | `har_drift_detected == 1` for 5 min | Critical | Same file |

### Alert Runbooks (What Happens When an Alert Fires)

| Alert | Auto Action | Human Action | Logged Where | RACI Owner |
|-------|-------------|--------------|-------------|------------|
| **HARLowConfidence** (confidence < 0.75 for 5 min) | Stage 7 trigger policy evaluates; if 2-of-3 signals confirm → sets trigger state to WARNING/CRITICAL in `logs/trigger/trigger_state.json`. | Operator reviews monitoring report in `outputs/monitoring/`; decides manual `--retrain` invocation. Until auto-retrain CI job is wired, **this requires a human.** | `logs/trigger/trigger_state.json` + MLflow run tag. | MLE + OPS |
| **HARHighEntropy** (entropy > 1.5 for 5 min) | Same trigger policy path as above. | Same as above. | Same. | MLE + OPS |
| **HARHighFlipRate** (flip rate > 15 % for 10 min) | Same trigger policy path. | Investigate session-level data quality; may indicate sensor placement issue rather than drift. | Same. | DE + MLE |
| **HARDataDriftDetected** (drift flag = 1 for 5 min) | Trigger policy escalates to CRITICAL if ≥ 4 channels drift. Retraining stage can be invoked manually. | Run `python run_pipeline.py --retrain --adapt adabn_tent`; review registration output before deploying. | `logs/trigger/`; MLflow retraining run. | MLE (R) + OPS (A) |

> ⚠️ **Current limitation:** Alertmanager and Prometheus scraping are not live, so the alert rules in `config/alerts/har_alerts.yml` are **not active**. The trigger policy JSON-based path is fully operational for local runs, but there is no automated notification channel.

### Missing Monitors (Must-Have for Production)

| Monitor | Why | Priority |
|---------|-----|:--------:|
| **Live Prometheus scraping** | Defined metrics are useless without a running scrape target. | P0 |
| **Grafana dashboard wired** | Dashboard JSON exists but no service to render it. | P0 |
| **Alertmanager integration** | Alerts defined but no notification channel (Slack/email/PagerDuty). | P1 |
| **Resource utilization** | No cAdvisor/Node Exporter running despite config. | P2 |
| **Data freshness monitoring** | No alert if no new data arrives for > N hours. | P1 |
| **Model-version tracking in dashboards** | Which model version is currently serving? (Registry `current_version` is null.) | P1 |

---

## 8) Risk Register (CTO-Style)

| # | Risk | Impact | Likelihood | Detection Signal | Mitigation | Owner | Evidence |
|---|------|:------:|:----------:|-----------------|------------|:-----:|----------|
| R1 | **Data drift / concept drift** | High — silent accuracy degradation | Medium | 3-layer monitoring, z-score alerts, Wasserstein CPD | Automated trigger policy (2-of-3 voting → retraining) | MLE + OPS | [src/trigger_policy.py](src/trigger_policy.py); [src/wasserstein_drift.py](src/wasserstein_drift.py) |
| R2 | **Reproducibility gap** | High — cannot recreate results | Low | CI test failures, DVC hash mismatch | DVC-tracked data, 578-package lockfile, MLflow parameter logging | DE + MLE | [config/requirements-lock.txt](config/requirements-lock.txt); [.dvc/config](.dvc/config) |
| R3 | **Data quality degradation** | High — garbage-in-garbage-out | Medium | Validation stage (schema + range checks) | [src/data_validator.py](src/data_validator.py) runs per-ingestion; config thresholds in [pipeline_config.yaml](config/pipeline_config.yaml#L45-L52) | DE | [src/components/data_ingestion.py](src/components/data_ingestion.py) |
| R4 | **Security / privacy** | High — sensor data contains behavioral patterns (health data) | Low (thesis scope) | No current detection | **Gap:** No access controls, no encryption at rest, no audit log for data access. | SEC | **Assumption** — no security module found in repo. |
| R5 | **Silent model degradation** | High — model serves bad predictions unnoticed | Medium | Confidence drop, entropy rise, flip rate | 3-layer monitoring exists but Prometheus not live. | OPS | [src/prometheus_metrics.py](src/prometheus_metrics.py) (defined only) |
| R6 | **Dependency / environment breakage** | Medium — TF version mismatch, OS-specific bugs | Low | CI runs on ubuntu-latest; pinned deps | Requirements lockfile; Docker containerization. | OPS | [docker/Dockerfile.inference](docker/Dockerfile.inference); CI matrix could test multiple OS. |
| R7 | **Rollback failure** | High — cannot revert to known-good model | Low | Rollback test exists | File-based model registry with hash verification; rollback command. | OPS | [src/model_rollback.py](src/model_rollback.py); [tests/test_model_rollback.py](tests/test_model_rollback.py) |
| R8 | **Retraining instability** | Medium — adapted model worse than incumbent | Medium | Confidence comparison pre/post | Proxy validation in registration; `is_better` check. But fallback to `True` for TTA. | MLE | [src/components/model_registration.py](src/components/model_registration.py#L75-L100) |
| R9 | **DVC remote unavailable** | Medium — data cannot be pulled for training | Medium | `dvc pull` failure in CI | CI gracefully falls back: "DVC remote not configured — using model already present in repo." | DE + OPS | [ci-cd.yml](.github/workflows/ci-cd.yml#L283-L286) |
| R10 | **Thesis evaluation incomplete** — MLflow window‑level CV results exist, but Chapter 5 tables/plots + subject‑wise evaluation + adaptation ablation (baseline vs AdaBN vs TENT) are not yet completed. | Critical — thesis claims not defensible yet | High | README/Chapter status; absence of GroupKFold/LOSO run outputs | Run systematic experiments and export MLflow results into Chapter 5; add GroupKFold/LOSO evaluation and ablation tables. | MLE + PO | [README.md](README.md#L23-L26); MLflow paths listed in §1. |
| R11 | **Data leakage / split integrity** — current training uses `StratifiedKFold` on shuffled sliding windows, not subject-wise split. Windows from the same user can appear in both train and validation folds, inflating reported accuracy. | High — reported metrics non-generalizable to new users | High (by design) | Non-zero **train/val user overlap** per fold; or a **large metric drop** when switching to GroupKFold/LOSO vs window-level CV | Switch to `GroupKFold` keyed on user ID, or leave-one-subject-out CV. Compare metrics before/after to quantify leakage. | MLE | [src/train.py](src/train.py#L397) — `StratifiedKFold(n_splits=5)` with no `groups` argument; `df['User']` is logged ([src/train.py](src/train.py#L165)) but not used in split. |
| R12 | **Class imbalance / rare-class failure** — 11 activity classes including rare behaviors (nail biting, knuckles cracking) vs ambient activities (sitting, standing). Macro F1 may mask poor per-class recall on rare classes. | Medium — system silently fails on clinically important rare behaviors | Medium | Per-class recall in classification report; confusion matrix | Use stratified sampling, class-weighted loss, or oversampling (SMOTE on windows). Log per-class F1 to MLflow and set minimum threshold per class. | MLE | [src/train.py](src/train.py#L46-L50) — `StratifiedKFold` preserves class ratios but does not address base-rate imbalance; per-class metrics are logged ([config/mlflow_config.yaml](config/mlflow_config.yaml#L32)). |
| R13 | **Proxy-metric misfire in unlabeled production** — confidence/entropy/drift signals can trigger retraining even when true task performance is stable (or fail to trigger when performance drops). | High — wasted retrains or silent degradation | Medium | Divergence between proxy alarms and periodic labeled audit performance; high alert volume with stable outcome metrics | Use multi-signal voting (already), add a “cooldown” window, require stability checks, and periodically validate proxies on a labeled audit set / human-reviewed queue. | PO + MLE | Trigger voting logic ([src/trigger_policy.py](src/trigger_policy.py)); monitoring proxies ([src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py)). |
| R14 | **Pseudo-label feedback loop / confirmation bias** — retraining on self-generated labels can reinforce model mistakes and reduce diversity. | Medium — gradual collapse on rare behaviors | Medium | Increasing confidence with worsening rare-class recall on labeled audits; reduced entropy but worse generalization | Use conservative pseudo-label thresholds, class-balanced sampling, uncertainty-based human labeling queue, and require subject-wise evaluation before promotion. | MLE | Adaptation hooks in pipeline ([src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py)); pseudo-label wiring via `--advanced` flag. |

---

## 9) Roadmap (Next 4–6 Weeks)

| # | Epic / Story | Acceptance Criteria | Priority | Implement Where |
|---|-------------|---------------------|:--------:|-----------------|
| 1 | **Run systematic experiments and log to MLflow** | ≥ 3 experiment runs (baseline, AdaBN, TENT) with full metrics logged; Chapter 5 data tables populated. | P0 — Thesis Critical | [src/train.py](src/train.py); MLflow experiment `har-retraining` (ID: `909768134748430965`) — existing per-fold runs show val_accuracy 0.929–0.953; target: add subject-wise GroupKFold runs + adaptation comparison; thesis report Chapter 5. |
| 2 | **Wire Prometheus + Grafana into Docker Compose** | `docker-compose up` starts Prometheus + Grafana alongside inference; `/metrics` endpoint scraped; Grafana dashboard loads. | P0 — Production | [docker-compose.yml](docker-compose.yml) — add `prometheus` and `grafana` services referencing existing [config/prometheus.yml](config/prometheus.yml) and [config/grafana/har_dashboard.json](config/grafana/har_dashboard.json). |
| 3 | **Add deployment-approval gate in CI** | GitHub branch protection on `main` requires 1 reviewer; Docker push only after approval; use GitHub Environments. | P1 — Governance | [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml); GitHub repo Settings → Branch protection rules. |
| 4 | **Automate retraining loop in CI** | New scheduled CI job: if trigger state is CRITICAL, run `run_pipeline.py --retrain --adapt adabn_tent`, register model, open PR for review. | P1 — Maturity | New workflow file `.github/workflows/auto-retrain.yml`; reads `logs/trigger/trigger_state.json`. ⚠️ **State persistence prerequisite:** `logs/trigger/trigger_state.json` is a local file — CI runners have no access to it. The trigger state must be persisted to an external store (S3 bucket, DVC remote, GitHub Actions artifact, or a DB) and pulled by the CI job before it can evaluate the CRITICAL condition. Without this, the auto-retrain workflow cannot function. (Note: GitHub Actions Artifacts have retention limits; for long-term reproducible evidence prefer S3/DB.) |
| 5 | **Migrate DVC remote to cloud storage** | `dvc push/pull` works against S3 or Azure Blob; CI can pull data without local `.dvc_storage`. | P1 — Collaboration | [.dvc/config](.dvc/config) — change remote URL; add credentials to GitHub Secrets. |
| 6 | **Add `CODEOWNERS` and escalation policy** | `CODEOWNERS` file maps `src/`, `config/`, `.github/` to named reviewers; `docs/ON_CALL.md` defines escalation. | P2 — Governance | New files: `.github/CODEOWNERS`, `docs/ON_CALL.md`. |
| 7 | **Enforce `mypy` type checking in CI** | `mypy src/` passes (or ≤ N errors); added as CI step before tests. | P2 — Quality | [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) lint job. |
| 8 | **Add Alertmanager notification channel** | Slack/email notifications fire when critical alerts trigger; test with a simulated drift scenario. | P2 — Observability | [config/prometheus.yml](config/prometheus.yml#L17-L20) — uncomment alertmanager target; add Alertmanager service in Docker Compose. |
| 9 | **Document security & data governance** | `docs/SECURITY_AND_GOVERNANCE.md` covers: data classification (health data), access controls, encryption at rest, GDPR considerations for behavioral sensor data. | P2 — Compliance | New file `docs/SECURITY_AND_GOVERNANCE.md`. |
| 10 | **Add subject-wise evaluation (GroupKFold)** | Re-run training with `GroupKFold(groups=user_id)`; compare macro F1 and per-class recall vs current window-level split; document results in Chapter 5. | P0 — Credibility | [src/train.py](src/train.py#L397) — replace `StratifiedKFold` with `GroupKFold(n_splits=5)` using user column as group key. |
| 11 | **Add labeling queue for unlabeled production (human-in-the-loop audit)** | New step exports top‑K uncertain/drifty windows to `outputs/labeling_queue/` (CSV) with metadata; a small labeled audit set is created monthly; proxy alarms are validated against audit performance; results logged to MLflow as `audit_f1_macro`. | P1 — Unlabeled Ops | **NEW:** `src/labeling_queue.py` + wire into pipeline after monitoring (e.g., Stage 12/13). Uses signals from [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py). |

### Thesis Delivery (Separate Track)

> The following items are thesis-specific deliverables. They are tracked here for completeness but are outside the scope of a product/platform roadmap.

| # | Deliverable | Acceptance Criteria | Priority |
|---|------------|---------------------|:--------:|
| T1 | **Write thesis Chapters 3–6** | Chapters 3 (methodology), 4 (implementation), 5 (experiments + grouped evaluation), 6 (discussion + limitations) drafted and peer-reviewed. | P0 — Thesis Critical |
| T2 | **Systematic experiment campaign** | ≥ 3 MLflow runs (baseline, AdaBN, TENT) with both window-level and subject-wise metrics; Chapter 5 tables populated. | P0 — Thesis Critical |
| T3 | **Thesis defense preparation** | Examiner quickstart (3-command reproduce) verified on clean machine; all claims in thesis linked to repo evidence. | P0 — Thesis Critical |

---

## 10) Appendix

### A) Repo Map

| Path | Purpose |
|------|---------|
| [run_pipeline.py](run_pipeline.py) | Single entry point for 14-stage pipeline (CLI). |
| [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py) | Orchestrator — delegates to component classes. |
| [src/components/](src/components/) | Component classes for each pipeline stage (data_ingestion, transformation, inference, monitoring, retraining, registration, baseline_update, etc.). |
| [src/train.py](src/train.py) | Model training (5-fold stratified CV, 1D-CNN-BiLSTM, MLflow). |
| [src/trigger_policy.py](src/trigger_policy.py) | Automated retraining trigger engine (2-of-3 voting, cooldowns). |
| [src/model_rollback.py](src/model_rollback.py) | Model registry and rollback manager. |
| [src/deployment_manager.py](src/deployment_manager.py) | Container build/push, blue-green/canary deployment logic. |
| [src/api/app.py](src/api/app.py) | FastAPI inference service with web UI + CSV upload. |
| [src/mlflow_tracking.py](src/mlflow_tracking.py) | MLflow experiment tracking wrapper. |
| [src/prometheus_metrics.py](src/prometheus_metrics.py) | Prometheus metric definitions and HTTP exporter. |
| [src/calibration.py](src/calibration.py) | Temperature scaling, MC Dropout, ECE, reliability diagrams. |
| [src/wasserstein_drift.py](src/wasserstein_drift.py) | Wasserstein-based drift detection + change-point detection. |
| [src/ood_detection.py](src/ood_detection.py) | Energy-based out-of-distribution detection. |
| [src/data_validator.py](src/data_validator.py) | Production-grade data validation (schema, range, missing values). |
| [src/domain_adaptation/](src/domain_adaptation/) | AdaBN (`adabn.py`) and TENT (`tent.py`) implementations. |
| [src/config.py](src/config.py) | Path configuration and constants. |
| [src/entity/](src/entity/) | Config and artifact dataclass definitions. |
| [config/pipeline_config.yaml](config/pipeline_config.yaml) | Runtime configuration (preprocessing toggles, validation thresholds). |
| [config/mlflow_config.yaml](config/mlflow_config.yaml) | MLflow experiment and registry settings. |
| [config/prometheus.yml](config/prometheus.yml) | Prometheus scrape configuration. |
| [config/alerts/har_alerts.yml](config/alerts/har_alerts.yml) | Prometheus alert rules. |
| [config/grafana/har_dashboard.json](config/grafana/har_dashboard.json) | Grafana dashboard definition. |
| [config/requirements.txt](config/requirements.txt) | Runtime dependencies. |
| [config/requirements-lock.txt](config/requirements-lock.txt) | Pinned lockfile (578 packages). |
| [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) | GitHub Actions CI/CD (lint → test → build → smoke → validate). |
| [docker/Dockerfile.inference](docker/Dockerfile.inference) | Inference container image. |
| [docker/Dockerfile.training](docker/Dockerfile.training) | Training container image. |
| [docker-compose.yml](docker-compose.yml) | Multi-service orchestration (MLflow, inference, training, preprocessing). |
| [tests/](tests/) | 19 test files, 225 tests (unit + integration + slow). |
| [scripts/](scripts/) | Supporting scripts (smoke test, drift analysis, baseline build, figure generation). |
| [models/registry/](models/registry/) | Local model registry (JSON manifest + `.keras` artifacts). |
| [data/](data/) | Raw, processed, prepared sensor data (DVC-tracked). |
| [mlruns/](mlruns/) | MLflow experiment storage. |
| [notebooks/](notebooks/) | Jupyter notebooks for exploration and preprocessing. |
| [Thesis_report/](Thesis_report/) | LaTeX/Word thesis report files. |

> **⚠️ Evidence link note for thesis PDF:** All `file.py#Lx` references in this document use current line numbers. Line numbers will shift as the codebase evolves. Before including evidence links in the submitted thesis PDF, replace them with **commit-pinned GitHub permalinks** (e.g., `https://github.com/ShalinVachheta017/MasterArbeit_MLops/blob/<commit-sha>/src/train.py#L397`). Use `git log --oneline -1` to get the pinning commit SHA.

### B) Citations / References Used in This Review

> **Thesis note:** Add full BibTeX entries to `Thesis_report/refs/parameter_citations.bib`. DOI/arXiv links provided below.

| Reference | Venue / DOI | Context |
|-----------|------------|---------|
| Sculley et al. (2015), "Hidden Technical Debt in Machine Learning Systems" | NeurIPS 2015 · [papers.nips.cc/paper/5656](https://papers.nips.cc/paper/5656) | Technical debt framing, rollback philosophy. |
| Shankar Krishnan et al. / Google Cloud, "MLOps: Continuous delivery and automation pipelines in machine learning" (2020) | Google Cloud whitepaper · [cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning](https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning) | Maturity levels 0–2 (Section 4A). |
| Microsoft, "Machine Learning Operations (MLOps) Maturity Model" (2023) | Microsoft Learn · [learn.microsoft.com/azure/architecture/ai-ml/guide/mlops-maturity-model](https://learn.microsoft.com/azure/architecture/ai-ml/guide/mlops-maturity-model) | Maturity levels 0–4 (Section 4B). |
| Guo et al. (2017), "On Calibration of Modern Neural Networks" | ICML 2017 · [arXiv:1706.04599](https://arxiv.org/abs/1706.04599) | Temperature scaling (cited in [src/calibration.py](src/calibration.py)). |
| Gal & Ghahramani (2016), "Dropout as a Bayesian Approximation" | ICML 2016 · [arXiv:1506.02142](https://arxiv.org/abs/1506.02142) | MC Dropout uncertainty quantification (cited in [src/calibration.py](src/calibration.py)). |
| Gama et al. (2014), "A Survey on Concept Drift Adaptation" | ACM Computing Surveys 46(4) · [DOI:10.1145/2523813](https://doi.org/10.1145/2523813) | DDM drift detection thresholds (cited in [src/trigger_policy.py](src/trigger_policy.py#L106-L110)). |
| Page, E. S. (1954), "Continuous Inspection Schemes" | Biometrika 41(1-2):100–115 · [DOI:10.2307/2333009](https://doi.org/10.2307/2333009) | CUSUM change-point detection (cited in [src/trigger_policy.py](src/trigger_policy.py#L106-L110)). |
| Liu et al. (2020), "Energy-based Out-of-distribution Detection" | NeurIPS 2020 · [arXiv:2010.03759](https://arxiv.org/abs/2010.03759) | OOD energy scoring (cited in [src/ood_detection.py](src/ood_detection.py)). |
| Yau & Kolaczyk (2023), WATCH | ⚠️ Verify DOI/venue in `Thesis_report/refs/parameter_citations.bib` | Wasserstein change-point detection (cited in [src/wasserstein_drift.py](src/wasserstein_drift.py#L17-L21)). |
| Oleh & Obermaisser (2025), ICTH_16 | ⚠️ Verify DOI/venue in `Thesis_report/refs/parameter_citations.bib` | Training pipeline methodology (cited in [config/pipeline_config.yaml](config/pipeline_config.yaml#L8-L10), [src/train.py](src/train.py#L143)). |
| Baylor et al. (2017), "TFX: A TensorFlow-Based Production-Scale ML Platform" | KDD 2017 · [DOI:10.1145/3097983.3098021](https://doi.org/10.1145/3097983.3098021) | Deployment governance philosophy (cited in [src/components/model_registration.py](src/components/model_registration.py#L90-L97)). |

---

*End of review. This document is structured for direct inclusion in a Master's thesis report (e.g., as an appendix or as the basis for Chapter 4 – System Evaluation).*

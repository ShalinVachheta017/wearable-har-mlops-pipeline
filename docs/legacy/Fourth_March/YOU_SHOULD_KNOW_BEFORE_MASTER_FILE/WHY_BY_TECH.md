# WHY BY TECHNOLOGY — Technology-Level WHY Analysis

> Each technology choice gets a WHY CARD.
> Rule: REF IDs only — full citations in REFERENCES.md.

---

## WHY CARD: MLOps (Paradigm)

| Field | Value |
|---|---|
| **Technology** | MLOps — structured ML lifecycle management |
| **Scope** | Whole repository |
| **WHY Bucket** | Reliability + Governance + Reproducibility |

**Business Lens**
- *Cost:* Reduces "hidden tech debt" (REF_HIDDEN_TECH_DEBT) — ML systems without MLOps accrue 10× maintenance cost.
- *Risk:* Without pipeline automation, human error in each stage compounds.
- *Compliance:* Audit trail (who trained what, when, with which data) is mandatory for regulated domains.
- *Speed:* Automated pipeline reduces deploy time from days to minutes.

**Thesis Lens**
- *Scope:* MLOps IS the thesis topic — the contribution is not the model, it's the infrastructure.
- *Contribution:* Demonstrates Google MLOps Level 2 (REF_GOOGLE_MLOPS_CDCT): automated pipeline, CT, CD.
- *Reproducibility:* Any experiment can be re-run from config + data version.
- *Evaluation:* ML Test Score rubric (REF_ML_TEST_SCORE) used to evaluate pipeline maturity.

**Key Decisions**

| Decision | Evidence | REF |
|---|---|---|
| 14-stage pipeline (not monolithic script) | Modular stages enable independent testing/updates | REF_CD4ML |
| 3-phase grouping (Default/Retrain/Advanced) | Not every run needs all stages; saves compute | PROJECT_DECISION |
| Config-driven (dataclass per stage) | Single source of truth in `config_entity.py` | REF_GOOGLE_MLOPS_CDCT |
| Artifact versioning per run | Timestamp-based artifact dirs + MLflow artifacts | REF_MLFLOW_ARTIFACTS |

**Alternatives Considered**
1. ~~Jupyter notebooks~~ — Not reproducible, not testable, not deployable.
2. ~~Single training script~~ — Cannot update monitoring without touching training code.
3. ~~Kubeflow/Vertex AI~~ — Cloud-locked; thesis requires local reproducibility.

**Domain Add-ons**
- 💳 *Fraud:* MLOps + real-time scoring via streaming (Kafka → FastAPI).
- 🏭 *Industrial:* MLOps + OPC-UA data collection + edge deployment.
- 🌾 *Agriculture:* MLOps + satellite image pipeline + seasonal retraining.

---

## WHY CARD: DVC (Data Version Control)

| Field | Value |
|---|---|
| **Technology** | DVC 3.50+ |
| **Primary Files** | `.dvc/config`, `data/*.dvc` |
| **WHY Bucket** | Reproducibility |

**Business Lens**
- *Reproducibility:* Can recreate any model by checking out the data version that trained it.
- *Cost:* Deduplication — DVC stores diffs, not full copies.
- *Risk:* Without data versioning, "which data trained this model?" is unanswerable.

**Thesis Lens**
- *Contribution:* Implements data versioning pattern from CD4ML (REF_CD4ML).
- *Reproducibility:* `dvc pull` restores exact training data for any commit.
- *Scope:* DVC is a cross-cutting concern, NOT a pipeline stage.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| DVC (not Git LFS) | DVC has pipeline support + ML-aware caching | REF_DVC_PIPELINES |
| Local remote | `.dvc/config` → `../../dvc_remote` | REF_DVC_VERSIONING |
| Track raw + processed | Both `data/raw/*.dvc` and `data/processed/*.dvc` | PROJECT_DECISION |

**Alternatives Considered**
1. ~~Git LFS~~ — No pipeline DAG, no caching, no `dvc repro`.
2. ~~S3 bucket (manual)~~ — No versioning, no linkage to Git commits.
3. ~~Pachyderm~~ — Over-engineered for single-developer project.

**Verification**
```bash
dvc status         # Should show "Data and pipelines are up to date"
dvc doctor         # Verify DVC configuration
```

---

## WHY CARD: MLflow

| Field | Value |
|---|---|
| **Technology** | MLflow 2.11+ |
| **Primary Files** | `src/mlflow_tracking.py` (643 L), `mlruns/` |
| **WHY Bucket** | Reproducibility + Governance |

**Business Lens**
- *Governance:* Every training run logged: hyperparameters, metrics, artifacts, model version.
- *Reproducibility:* `mlflow.search_runs()` finds any historical experiment.
- *Risk:* Model Registry enables rollback to any previous version.
- *Cost:* Open-source; no vendor lock-in.

**Thesis Lens**
- *Contribution:* Full experiment tracking with custom metrics (confidence, drift, ECE).
- *Reproducibility:* Any reported number traces to a specific MLflow run ID.
- *Scope:* MLflow is a cross-cutting concern, NOT a pipeline stage.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| MLflow (not W&B) | Open-source, self-hosted, no data leaves machine | REF_MLFLOW_TRACKING |
| Local tracking server | `mlruns/` directory; no external server needed | PROJECT_DECISION |
| Model Registry | Version, stage (Staging/Production), rollback | REF_MLFLOW_REGISTRY |
| Log artifacts per stage | Each component logs outputs as MLflow artifacts | REF_MLFLOW_ARTIFACTS |

**Alternatives Considered**
1. ~~Weights & Biases~~ — Cloud-only; data privacy concern.
2. ~~TensorBoard~~ — No model registry, no artifact tracking.
3. ~~Neptune.ai~~ — Commercial; license cost.
4. ~~CSV logs~~ — Not queryable, no UI, no versioning.

**Verification**
```bash
mlflow ui --port 5000             # Open UI
mlflow models list                # List registered models
python -c "import mlflow; print(mlflow.__version__)"  # Verify version
```

---

## WHY CARD: Docker

| Field | Value |
|---|---|
| **Technology** | Docker (python:3.11-slim base) |
| **Primary Files** | `docker/Dockerfile.inference` (65 L), `docker/Dockerfile.training` (52 L), `docker-compose.yml` (223 L) |
| **WHY Bucket** | Reproducibility + Reliability |

**Business Lens**
- *Reproducibility:* "Works on my machine" eliminated; same container everywhere.
- *Reliability:* Isolation prevents dependency conflicts.
- *Scalability:* Docker Compose orchestrates 7 services with one command.

**Thesis Lens**
- *Contribution:* Containerized inference and training with monitoring stack.
- *Reproducibility:* Dockerfile pins all dependencies; build is deterministic.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| python:3.11-slim base | Minimal image; matches conda env | REF_DOCKER_BEST_PRACTICES |
| Separate inference/training Dockerfiles | Different dependencies; smaller inference image | PROJECT_DECISION |
| Single-stage builds | ⚠️ GAP-DOCKER-01: should be multi-stage | REF_DOCKER_MULTI_STAGE |
| 7 docker-compose services | inference, training, mlflow, prometheus, alertmanager, grafana, node-exporter | PROJECT_DECISION |

**Docker Compose Services**

| Service | Image / Build | Port | Purpose |
|---|---|---|---|
| har-inference | `docker/Dockerfile.inference` | 8000 | FastAPI inference API |
| har-training | `docker/Dockerfile.training` | — | Training pipeline |
| mlflow | `ghcr.io/mlflow/mlflow:v2.11.0` | 5000 | Experiment tracking |
| prometheus | `prom/prometheus:v2.50.1` | 9090 | Metrics collection |
| alertmanager | `prom/alertmanager:v0.27.0` | 9093 | Alert routing |
| grafana | `grafana/grafana:10.3.1` | 3000 | Dashboards |
| node-exporter | `prom/node-exporter:v1.7.0` | 9100 | System metrics |

**Alternatives Considered**
1. ~~Kubernetes~~ — Over-engineered for single-machine thesis project.
2. ~~Podman~~ — Less ecosystem support; Docker is industry standard.
3. ~~No containers~~ — Dependency hell across Windows/Linux/Mac.

**Verification**
```bash
docker compose config --quiet    # Validate compose file
docker compose build --dry-run   # Verify Dockerfiles parse
```

---

## WHY CARD: CI/CD (GitHub Actions)

| Field | Value |
|---|---|
| **Technology** | GitHub Actions |
| **Primary File** | `.github/workflows/ci-cd.yml` (350 L) |
| **WHY Bucket** | Maintainability + Reliability |

**Business Lens**
- *Reliability:* Every push tested automatically; regressions caught before merge.
- *Speed:* Automated deploy removes manual steps.
- *Cost:* GitHub Actions free for public repos.

**Thesis Lens**
- *Contribution:* Demonstrates CI/CD as part of MLOps Level 2.
- *Scope:* Tests, linting, Docker build verification, threshold consistency checks.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| GitHub Actions (not Jenkins) | Native to GitHub; no self-hosted server needed | REF_GITHUB_ACTIONS |
| 6 CI jobs | lint, unit-test, integration-test, docker-build, threshold-check, deploy | PROJECT_DECISION |
| Path filters | Only trigger on `src/**`, `tests/**`, `config/**` changes | PROJECT_DECISION |
| Cron schedule | Weekly lint + test run on `main` | PROJECT_DECISION |
| Python 3.11 matrix | Single version; matches production | PROJECT_DECISION |

**Alternatives Considered**
1. ~~Jenkins~~ — Self-hosted; maintenance overhead.
2. ~~GitLab CI~~ — Repo is on GitHub.
3. ~~No CI~~ — Manual testing is unreliable.

**Verification**
```bash
gh workflow list                   # List workflows
gh run list --limit 5              # Check recent runs
```

---

## WHY CARD: FastAPI

| Field | Value |
|---|---|
| **Technology** | FastAPI |
| **Primary File** | `src/api/app.py` (892 L) |
| **WHY Bucket** | Scalability/Cost + Reliability |

**Business Lens**
- *Speed:* Async endpoint (ASGI) handles concurrent requests.
- *Cost:* Lightweight; single-process serves HAR inference.
- *Reliability:* Built-in request validation (Pydantic).
- *Observability:* Native Prometheus metrics endpoint at `/metrics`.

**Thesis Lens**
- *Contribution:* REST API for model serving with built-in monitoring.
- *Scope:* Demonstrates serving pattern from Google MLOps.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| FastAPI (not Flask) | Async, type hints, auto-docs, Pydantic validation | REF_FASTAPI |
| Port 8000 | Standard FastAPI port | PROJECT_DECISION |
| Prometheus integration | `prometheus_client` counters/histograms on every request | REF_PROM_HISTOGRAMS |
| Health + readiness endpoints | `/health`, `/ready` | REF_DOCKER_BEST_PRACTICES |
| No authentication | ⚠️ GAP-AUTH-01: should add JWT/API key | PROJECT_DECISION |

**Alternatives Considered**
1. ~~Flask~~ — Synchronous; no native async.
2. ~~gRPC~~ — Binary protocol; harder to debug.
3. ~~TF Serving~~ — Heavyweight; no custom preprocessing.
4. ~~Triton~~ — GPU-focused; overkill for CPU HAR.

**Verification**
```bash
curl http://localhost:8000/health   # Health check
curl http://localhost:8000/docs     # OpenAPI docs
```

---

## WHY CARD: Prometheus + Alertmanager

| Field | Value |
|---|---|
| **Technology** | Prometheus 2.50.1 + Alertmanager 0.27.0 |
| **Primary Files** | `config/prometheus.yml`, `config/alerts/har_alerts.yml` (8 rules), `config/alertmanager.yml` (111 L) |
| **WHY Bucket** | Observability |

**Business Lens**
- *Observability:* Real-time metrics: request latency, prediction confidence, drift scores.
- *Reliability:* Alert rules fire before human-noticeable degradation.
- *Cost:* Open-source; battle-tested at scale.

**Thesis Lens**
- *Contribution:* Custom ML-specific alerts (not just infrastructure).
- *Evaluation:* 8 alert rules across 4 groups (model, data, system, pipeline).

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Prometheus (not Datadog) | Open-source, self-hosted, pull model | REF_PROM_HISTOGRAMS |
| 6 scrape jobs | inference (10s), training (30s), mlflow, node, prometheus, alertmanager | PROJECT_DECISION |
| 10s scrape for inference | Real-time monitoring of serving latency | REF_PROM_ALERTING |
| 8 alert rules | Confidence, drift, latency, error rate, memory, retraining, readiness, CPU | PROJECT_DECISION |
| Inhibit rules | Critical alerts suppress warning-level for same metric | REF_PROM_ALERTING |

**Alert Rules Summary**

| Rule | Group | Condition | Severity |
|---|---|---|---|
| HighLowConfidence | model | mean confidence < 0.6 for 5m | warning |
| ModelDriftDetected | data | drift z-score > 2.0 | warning |
| HighPredictionLatency | model | p95 > 500ms for 5m | warning |
| HighErrorRate | system | error rate > 5% for 5m | critical |
| HighMemoryUsage | system | memory > 85% for 10m | warning |
| RetrainingTriggered | pipeline | retrain counter increased | info |
| ModelNotReady | model | readiness = 0 for 5m | critical |
| HighCPUUsage | system | CPU > 80% for 15m | warning |

**Alternatives Considered**
1. ~~Datadog/New Relic~~ — Cloud SaaS; cost + data privacy.
2. ~~Custom logging~~ — Not queryable; no alerting.
3. ~~ELK Stack~~ — Log-focused; Prometheus is metrics-native.

**Verification**
```bash
pytest tests/test_prometheus_metrics.py -v
curl http://localhost:9090/api/v1/rules   # Check loaded rules
```

---

## WHY CARD: Grafana

| Field | Value |
|---|---|
| **Technology** | Grafana 10.3.1 |
| **Primary Files** | `config/grafana/` |
| **WHY Bucket** | Observability |

**Business Lens**
- *Observability:* Visual dashboards for non-technical stakeholders.
- *Cost:* Open-source; provisioned via config (no manual setup).

**Thesis Lens**
- *Contribution:* Complete observability stack (metrics collection → alerting → visualization).

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Grafana (not custom UI) | Industry standard; provisioning support | REF_GRAFANA_PROVISIONING |
| Auto-provisioned datasource | Prometheus datasource configured via YAML | REF_GRAFANA_PROVISIONING |
| Port 3000 | Standard Grafana port | PROJECT_DECISION |

---

## WHY CARD: TensorFlow / Keras

| Field | Value |
|---|---|
| **Technology** | TensorFlow 2.14+ / Keras |
| **Primary File** | `src/train.py` (1345 L) |
| **WHY Bucket** | Reliability (model) |

**Business Lens**
- *Reliability:* Mature framework; production-tested at scale.
- *Cost:* Free; GPU and CPU support.
- *Speed:* TF SavedModel → no conversion for serving.

**Thesis Lens**
- *Contribution:* 1D-CNN-BiLSTM architecture for HAR (REF_CNN_BILSTM_HAR).
- *Evaluation:* Two model variants with different parameter counts.

**Model Architecture**

| Variant | Parameters | Input Shape | Output Shape |
|---|---|---|---|
| v1 (1D-CNN-BiLSTM) | ~499K | (None, 200, 6) | (None, 11) |
| v2 (lighter) | ~306K | (None, 200, 6) | (None, 11) |

**Training Config** (`train.py:90`)

| Param | Value | Evidence |
|---|---|---|
| Epochs | 100 | With early stopping | 
| Learning rate | 0.001 | Adam optimizer |
| Batch size | 64 | Fits in GPU memory |
| K-fold CV | 5 | Standard for HAR |
| Optimizer | Adam | Adaptive learning rate |

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| TF/Keras (not PyTorch) | SavedModel format for serving; BatchNorm for AdaBN compatibility | REF_TF_KERAS, REF_ADABN |
| 1D-CNN-BiLSTM | Spatial (CNN) + temporal (BiLSTM) feature extraction | REF_CNN_BILSTM_HAR |
| 11 classes | 11 activity types (HAR domain requirement) | PROJECT_DECISION |
| Dropout + BatchNorm | Regularization; BN enables AdaBN domain adaptation | REF_ADABN |

**Alternatives Considered**
1. ~~PyTorch~~ — Requires ONNX conversion for serving; TF has native SavedModel.
2. ~~Transformer~~ — More parameters; not proven better for 6-channel IMU HAR.
3. ~~Random Forest~~ — Cannot process raw time-series windows.
4. ~~LSTM only~~ — Misses local spatial patterns in acceleration. 

---

## WHY CARD: pytest (Testing Framework)

| Field | Value |
|---|---|
| **Technology** | pytest 8.0+ |
| **Primary Files** | `tests/` (25 files), `pytest.ini`, `pyproject.toml` |
| **WHY Bucket** | Maintainability + Reliability |

**Business Lens**
- *Reliability:* 25 test files catch regressions before production.
- *Speed:* Marker system (`-k "not slow"`) enables fast CI runs.
- *Maintainability:* Tests document expected behavior.

**Thesis Lens**
- *Contribution:* ML-specific testing: threshold consistency, drift detection, calibration.
- *Evaluation:* Test coverage by stage (see WHY_INVENTORY.md Section E).

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| pytest (not unittest) | Fixtures, parametrize, markers, plugins | REF_PYTEST |
| 6 markers | unit, integration, slow, robustness, calibration, sensor | PROJECT_DECISION |
| Threshold consistency test | `test_threshold_consistency.py` verifies all thresholds across configs | PROJECT_DECISION |
| Prometheus metrics test | `test_prometheus_metrics.py` verifies metric registration | PROJECT_DECISION |

**Alternatives Considered**
1. ~~unittest~~ — Verbose; no fixtures/parametrize.
2. ~~nose2~~ — Deprecated ecosystem.
3. ~~No tests~~ — Violates ML Test Score Level 0 (REF_ML_TEST_SCORE).

**Verification**
```bash
pytest tests/ -v --tb=short                  # All tests
pytest tests/ -k "not slow" -v               # Fast tests only
pytest tests/test_threshold_consistency.py -v # Threshold audit
```

---

## WHY CARD: Python 3.11

| Field | Value |
|---|---|
| **Technology** | Python 3.11 (conda env `thesis-mlops`) |
| **Primary Files** | `pyproject.toml`, `docker/Dockerfile.*` |
| **WHY Bucket** | Reproducibility |

**Business Lens**
- *Reproducibility:* Pinned version across dev, Docker, CI.
- *Speed:* 3.11 is 10–60% faster than 3.10 for CPU workloads.

**Thesis Lens**
- *Reproducibility:* Same Python version everywhere ensures consistent behavior.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Python 3.11 (not 3.12) | TF 2.14 requires 3.11; 3.12 not supported | REF_TF_KERAS |
| conda (not venv) | Better GPU driver management for TF | REF_CONDA |
| pyproject.toml | Modern Python packaging; 13 core deps + optional groups | PROJECT_DECISION |

---

## Technology Stack Summary

| Layer | Technology | WHY Bucket | Evidence Type |
|---|---|---|---|
| **Model** | TF/Keras 2.14+ | Reliability | PAPER (REF_CNN_BILSTM_HAR) |
| **Data** | DVC 3.50+ | Reproducibility | OFFICIAL_DOC (REF_DVC_PIPELINES) |
| **Experiment** | MLflow 2.11+ | Reproducibility + Governance | OFFICIAL_DOC (REF_MLFLOW_TRACKING) |
| **Serving** | FastAPI | Scalability | OFFICIAL_DOC (REF_FASTAPI) |
| **Container** | Docker | Reproducibility | OFFICIAL_DOC (REF_DOCKER_BEST_PRACTICES) |
| **CI/CD** | GitHub Actions | Maintainability | OFFICIAL_DOC (REF_GITHUB_ACTIONS) |
| **Monitoring** | Prometheus + Alertmanager | Observability | OFFICIAL_DOC (REF_PROM_HISTOGRAMS) |
| **Visualization** | Grafana 10.3.1 | Observability | OFFICIAL_DOC (REF_GRAFANA_PROVISIONING) |
| **Testing** | pytest 8.0+ | Maintainability | OFFICIAL_DOC (REF_PYTEST) |
| **Language** | Python 3.11 | Reproducibility | PROJECT_DECISION |
| **Domain Adapt.** | AdaBN, TENT, EWC | Reliability | PAPER (REF_ADABN, REF_TENT, REF_EWC) |
| **Calibration** | Temp scaling, MC Dropout | Safety | PAPER (REF_TEMP_SCALING, REF_MC_DROPOUT) |

# Technology WHY Map — HAR MLOps Pipeline
**Generated: 2026-03-03 | Repo: MasterArbeit_MLops (main)**

---

## Table of Contents
1. [MLOps (Pipeline Orchestration)](#1-mlops-pipeline-orchestration)
2. [DVC (Data & Model Versioning)](#2-dvc-data--model-versioning)
3. [MLflow (Experiment Tracking & Registry)](#3-mlflow-experiment-tracking--registry)
4. [CI/CD (GitHub Actions)](#4-cicd-github-actions)
5. [Docker / Docker Compose](#5-docker--docker-compose)
6. [Prometheus / Alertmanager](#6-prometheus--alertmanager)
7. [Grafana (Dashboards)](#7-grafana-dashboards)
8. [Testing (pytest)](#8-testing-pytest)
9. [FastAPI (Inference API)](#9-fastapi-inference-api)
10. [TensorFlow / Keras](#10-tensorflow--keras)
11. [Domain Adaptation (AdaBN / TENT)](#11-domain-adaptation-adabn--tent)
12. [Calibration & Uncertainty (Temperature Scaling / MC Dropout)](#12-calibration--uncertainty)

---

## 1. MLOps (Pipeline Orchestration)

### What it does in THIS repo
- 14-stage production pipeline orchestrated by `ProductionPipeline` class (src/pipeline/production_pipeline.py:80–967).
- Single CLI entry point: `run_pipeline.py:1–545`.
- Stages: ingestion → validation → transformation → inference → evaluation → monitoring → trigger → retraining → registration → baseline_update → calibration → wasserstein_drift → curriculum_pseudo_labeling → sensor_placement.
- Stage list defined at src/pipeline/production_pipeline.py:54–68 (`ALL_STAGES`, `RETRAIN_STAGES`, `ADVANCED_STAGES`).

### Why chosen
- **Problem solved**: Unlabeled production data streams from Garmin wearables require automated drift detection, retraining triggering, and model governance — manual monitoring is infeasible.
- **Alternative rejected**: Ad-hoc scripts — no artifact handoff, no stage ordering guarantees, no governance gates.
- **Alternative rejected**: Kubeflow/Airflow — too heavyweight for a single-node PoC thesis; no Kubernetes cluster available.
- **WHY bucket**: Reliability | Reproducibility | Governance

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| Pipeline orchestration pattern | OFFICIAL_DOC | [REF_GOOGLE_MLOPS] |
| 14-stage decomposition | PROJECT_DECISION | src/pipeline/production_pipeline.py:54–68 |
| MLOps maturity model alignment | PAPER | [REF_MLOPS_SURVEY] |

### How to verify
```bash
python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger
python -m pytest tests/test_pipeline_integration.py -v
```

---

## 2. DVC (Data & Model Versioning)

### What it does in THIS repo
- Tracks large binary files (sensor data, model weights) outside Git.
- Config at .dvc/config: local remote at `../.dvc_storage`.
- .dvcignore at project root.
- CI/CD pulls DVC-tracked model artifacts: `.github/workflows/ci-cd.yml:301` (`dvc pull models/pretrained/ --no-run-cache`).

### Why chosen
- **Problem solved**: Git cannot efficiently store multi-GB sensor datasets and .keras model files. Git LFS requires per-file tracking and has no pipeline-stage integration.
- **vs Git LFS**: DVC provides (a) content-addressable storage with dedup, (b) pipeline stage DAGs (dvc.yaml), (c) remote storage abstraction (local/S3/GCS), (d) `dvc pull` / `dvc push` for team sync. Git LFS only versions blobs.
- **vs No versioning**: Without DVC, model artifacts are unversioned — no rollback, no reproducibility audit trail.
- **WHY bucket**: Reproducibility | Governance

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| DVC vs Git LFS tradeoff | OFFICIAL_DOC | [REF_DVC_USE_CASES] |
| Local remote config | PROJECT_DECISION | .dvc/config |
| CI/CD DVC pull | OFFICIAL_DOC | .github/workflows/ci-cd.yml:301 |

### How to verify
```bash
dvc status
dvc pull models/pretrained/ --no-run-cache
```

### P0 Gaps
- **GAP-DVC-01**: No `dvc.yaml` pipeline definition file found in repo root. DVC is used only for storage, not for pipeline DAG tracking. Consider adding `dvc.yaml` with stage definitions to enable `dvc repro`.
- **GAP-DVC-02**: No `.dvc` tracking files found for specific data files. Verify that sensor data and model files are actually tracked by DVC (`dvc ls`).

---

## 3. MLflow (Experiment Tracking & Registry)

### What it does in THIS repo
- **Tracking**: `src/mlflow_tracking.py:45–530` — `MLflowTracker` class wraps MLflow API. Logs params, metrics, artifacts, Keras models, confusion matrices, classification reports.
- **Config**: `config/mlflow_config.yaml` — experiment name `anxiety-activity-recognition`, model name `har-1dcnn-bilstm`.
- **Registry**: Model registration at src/pipeline/production_pipeline.py:920 (`_register_model_to_mlflow()`).
- **Docker service**: docker-compose.yml:20–50 — MLflow server on port 5000, SQLite backend, artifact root `/mlflow/mlruns`.
- **Tags**: project/author/model_type/task tags on every run (config/mlflow_config.yaml:28–33).

### Why chosen
- **Problem solved**: Need to compare retraining runs (AdaBN vs TENT vs pseudo-label), track which model version is deployed, and audit training parameters.
- **vs Weights & Biases**: MLflow is open-source, self-hosted, no SaaS dependency — important for thesis reproducibility.
- **vs TensorBoard**: TensorBoard lacks model registry, parameter logging, and artifact management.
- **WHY bucket**: Reproducibility | Observability | Governance

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| MLflow tracking API | OFFICIAL_DOC | [REF_MLFLOW_TRACKING] |
| MLflow model registry | OFFICIAL_DOC | [REF_MLFLOW_REGISTRY] |
| Keras integration | OFFICIAL_DOC | [REF_MLFLOW_KERAS] |
| Self-hosted for reproducibility | PROJECT_DECISION | docker-compose.yml:20–50 |

### How to verify
```bash
docker compose up mlflow -d
python -c "import mlflow; mlflow.set_tracking_uri('http://localhost:5000'); print(mlflow.search_experiments())"
```

---

## 4. CI/CD (GitHub Actions)

### What it does in THIS repo
- Workflow: `.github/workflows/ci-cd.yml` (350 lines).
- **6 jobs**: lint → test → test-slow → build → integration-test → model-validation (+notify on failure).
- **Lint job** (line 42): flake8 + black + isort.
- **Test job** (line 74): pytest with `not slow and not integration and not gpu` markers, coverage report, codecov upload.
- **Test-slow job** (line 113): TensorFlow-dependent tests, `continue-on-error: true` (non-blocking).
- **Build job** (line 145): Docker build + push to GHCR with `docker/build-push-action@v5`, GHA cache (`cache-from: type=gha`).
- **Integration test** (line 224): Pull built image, run container, smoke-test `/api/health`, run `scripts/inference_smoke.py`.
- **Model validation** (line 280): Scheduled weekly (`cron: '0 6 * * 1'`), DVC pull, pytest, drift check.
- **Triggers**: push to main/develop, PR to main, manual dispatch, weekly schedule.
- **Path filters** (line 22): Only triggers on src/, tests/, docker/, config/, requirements.txt, workflows/ changes.

### Why chosen
- **Problem solved**: Manual testing and deployment is error-prone. CI gates prevent broken code from reaching main. Automated smoke tests catch inference regressions.
- **Pipeline shape**: lint → test → build → integration-test is standard CI/CD. Slow TF tests are non-blocking to avoid flaky CI.
- **Gating**: Build job requires test pass (`needs: test`). Integration test requires build pass and only runs on main.
- **Weekly model validation**: Catches silent model degradation between code changes.
- **WHY bucket**: Reliability | Maintainability

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| GitHub Actions workflows | OFFICIAL_DOC | [REF_GHA_WORKFLOWS] |
| GHA build cache | OFFICIAL_DOC | [REF_GHA_CACHE] |
| Docker build-push-action | OFFICIAL_DOC | [REF_DOCKER_BUILD_PUSH] |
| Codecov integration | OFFICIAL_DOC | [REF_CODECOV] |

### How to verify
```bash
# Locally simulate lint job
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
black --check --diff src/
isort --check-only --diff src/
# Locally run unit tests
pytest tests/ -m "not slow and not integration and not gpu" -v --cov=src
```

---

## 5. Docker / Docker Compose

### What it does in THIS repo
- **Dockerfile.inference** (docker/Dockerfile.inference:1–65): Python 3.11-slim base, minimal system deps (curl only), inference-focused pip install, FastAPI entry point, HEALTHCHECK on /api/health.
- **Dockerfile.training** (docker/Dockerfile.training:1–52): Python 3.11-slim base, build-essential + git + curl, full ML stack (TF, MLflow, DVC, scikit-learn).
- **docker-compose.yml** (223 lines, 7 services):
  - `mlflow` — tracking server on port 5000
  - `inference` — FastAPI on port 8000, depends_on mlflow
  - `training` — on-demand (profile: training)
  - `preprocessing` — on-demand (profile: preprocessing)
  - `prometheus` — port 9090, 15d retention, loads alert rules
  - `alertmanager` — port 9093, routes to log/null/email
  - `grafana` — port 3000, provisioned datasource + dashboard
- **Profiles**: `training` and `preprocessing` services use Docker Compose profiles — not started by default (`docker compose up` starts only inference+mlflow+monitoring).
- **Networks**: Single bridge network `har-mlops-network` connects all services.
- **Volumes**: Named volumes for mlflow-data, prometheus_data, grafana_data, alertmanager_data.
- **Health checks**: All long-running services have HEALTHCHECK (mlflow, inference, alertmanager).

### Why chosen
- **Separate images**: Training image is ~3GB (TF + scikit-learn + DVC). Inference image is ~1.5GB (TF + FastAPI only). Separate images avoid shipping training-only dependencies to production.
- **No multi-stage build**: Both Dockerfiles use single-stage FROM python:3.11-slim. Multi-stage would reduce image size by separating build/runtime layers. This is a P0 gap.
- **Profiles**: Training/preprocessing are on-demand — avoids wasting resources on always-running containers.
- **WHY bucket**: Reproducibility | Scalability/Cost

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| Docker best practices | OFFICIAL_DOC | [REF_DOCKER_BEST] |
| Docker Compose profiles | OFFICIAL_DOC | [REF_DOCKER_COMPOSE] |
| HEALTHCHECK directive | OFFICIAL_DOC | [REF_DOCKER_HEALTHCHK] |
| Layer caching (COPY requirements first) | OFFICIAL_DOC | [REF_DOCKER_BEST] |

### How to verify
```bash
docker compose up -d mlflow inference prometheus grafana alertmanager
docker compose ps
curl -f http://localhost:8000/api/health
curl -f http://localhost:5000/health
```

### P0 Gaps
- **GAP-DOCKER-01**: No multi-stage builds. Inference image could be ~40% smaller with a build stage for pip install and a slim runtime stage. Evidence: [REF_DOCKER_MULTI].
- **GAP-DOCKER-02**: Dockerfile.inference hardcodes `pip install` list instead of using a separate `requirements-inference.txt`. This duplicates dependency management.

---

## 6. Prometheus / Alertmanager

### What it does in THIS repo
- **Prometheus config**: config/prometheus.yml:1–72 — scrapes `inference:8000/metrics` every 10s, `training:8001/metrics` every 30s.
- **Metrics exported** (src/api/app.py:40–76):
  - `har_api_requests_total` (Counter)
  - `har_confidence_mean` (Gauge)
  - `har_entropy_mean` (Gauge)
  - `har_flip_rate` (Gauge)
  - `har_drift_detected` (Gauge: 0.0=PASS, 1.0=WARNING)
  - `har_baseline_age_days` (Gauge: -1=missing)
  - `har_inference_latency_ms` (Histogram)
- **Alert rules**: config/alerts/har_alerts.yml — 7 rules across 4 groups:
  - `HARLowConfidence`: har_confidence_mean < 0.65 for 5m
  - `HARHighEntropy`: har_entropy_mean > 1.8 for 5m
  - `HARHighFlipRate`: har_flip_rate > 0.25 for 10m
  - `HARDriftDetected`: har_drift_detected == 1 for 5m
  - `HARHighLatency`: p95 latency > 500ms for 5m
  - `HARNoPredictions`: rate(requests) == 0 for 10m
  - `HARStaleDriftBaseline`: baseline_age > 90 days
  - `HARMissingDriftBaseline`: baseline_age == -1 for 5m
- **Alertmanager**: config/alertmanager.yml — routes by severity (critical → 1h repeat, warning → 4h, info → 24h). Inhibition rules suppress symptoms when root cause fires (e.g., NoPredictions suppresses warnings).
- **Metrics exporter module**: src/prometheus_metrics.py:1–584 — `MetricsExporter` singleton, Prometheus text format export, HTTP handler.

### Why chosen
- **Problem solved**: Production ML models degrade silently. Without observability, confidence drift, temporal instability, and data distribution shift go undetected.
- **Why histograms**: Latency distribution (not just mean) reveals tail-latency issues. Prometheus histogram_quantile computes p95/p99 server-side. [REF_PROM_HISTOGRAMS]
- **Why alerting tiers**: Tiered thresholds (monitoring warns at 0.60, trigger fires at 0.65) prevent alert fatigue while escalating real issues.
- **vs Custom monitoring**: Prometheus is the open-source standard for metrics collection. Custom solutions lack ecosystem (Grafana, Alertmanager, PromQL).
- **WHY bucket**: Observability | Reliability

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| Prometheus architecture | OFFICIAL_DOC | [REF_PROM_OVERVIEW] |
| Histogram best practices | OFFICIAL_DOC | [REF_PROM_HISTOGRAMS] |
| Alert rule format | OFFICIAL_DOC | [REF_PROM_ALERTRULES] |
| Alertmanager routing | OFFICIAL_DOC | [REF_PROM_ALERTMGR] |
| Threshold alignment | EMPIRICAL_CALIBRATION | config/monitoring_thresholds.yaml, reports/THRESHOLD_CALIBRATION.csv |

### How to verify
```bash
docker compose up -d inference prometheus alertmanager
curl http://localhost:8000/metrics | grep har_
curl http://localhost:9090/api/v1/rules | python -m json.tool
python scripts/verify_prometheus_metrics.py --offline
```

---

## 7. Grafana (Dashboards)

### What it does in THIS repo
- **Provisioned datasource**: config/grafana/datasources/datasource-prometheus.yaml — auto-configures Prometheus as default datasource.
- **Provisioned dashboard provider**: config/grafana/dashboards/dashboard-provider.yaml — auto-loads dashboards from /etc/grafana/provisioning/dashboards.
- **Dashboard JSON**: config/grafana/dashboards/har_dashboard.json + config/grafana/har_dashboard.json.
- **Docker service**: docker-compose.yml:185–198 — Grafana 10.3.1, port 3000, admin/admin default.

### Why chosen
- **Problem solved**: Prometheus stores metrics but has minimal visualization. Grafana provides time-series panels, alerting overlays, and shareable dashboards for thesis demonstration.
- **Provisioning vs manual**: File-based provisioning (YAML + JSON) makes dashboards reproducible and version-controlled — no manual UI setup.
- **WHY bucket**: Observability | Maintainability

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| Grafana provisioning | OFFICIAL_DOC | [REF_GRAFANA_PROV] |
| Dashboard JSON format | OFFICIAL_DOC | [REF_GRAFANA_DASH] |

### How to verify
```bash
docker compose up -d grafana
# Open http://localhost:3000 (admin/admin)
# Verify "HAR MLOps" folder contains provisioned dashboard
```

---

## 8. Testing (pytest)

### What it does in THIS repo
- **20 test files** in tests/ covering stages 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, plus threshold consistency, observability, and integration.
- **Markers** (pytest.ini): `slow` (TF-dependent), `integration`, `gpu`.
- **CI split**: Fast tests run in `test` job (markers: `not slow and not integration and not gpu`). Slow tests in `test-slow` job with `continue-on-error: true`.
- **Coverage**: pytest-cov + codecov upload in CI (.github/workflows/ci-cd.yml:96–104).
- **Key test files**:
  - tests/test_threshold_consistency.py — verifies threshold alignment across config_entity.py, trigger_policy.py, and monitoring config.
  - tests/test_trigger_policy.py — 14+ tests including state persistence, consecutive warning escalation, degraded metrics.
  - tests/test_model_registration_gate.py — 7 tests for registration gate logic.
  - tests/test_pipeline_integration.py — multi-stage integration tests.
  - tests/test_wasserstein_drift.py — 9 tests for drift detection.
  - tests/test_preprocessing.py — windowing, normalization, unit conversion tests.

### Why chosen
- **Unit/integration split**: Unit tests run in <30s without TF. Integration tests require TF model loading (~60s). Splitting prevents CI timeout and flaky failures.
- **Threshold consistency tests**: Operational thresholds are duplicated across config_entity.py, trigger_policy.py, and Prometheus rules. Automated tests catch sync drift.
- **WHY bucket**: Reliability | Maintainability

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| pytest framework | OFFICIAL_DOC | [REF_PYTEST] |
| Marker-based test selection | OFFICIAL_DOC | [REF_PYTEST_MARKERS] |

### How to verify
```bash
pytest tests/ -m "not slow and not integration and not gpu" -v --tb=short
pytest tests/test_threshold_consistency.py -v
pytest tests/test_trigger_policy.py -v
```

### P0 Gaps
- **GAP-TEST-01**: No dedicated test files for Stage 1 (data_ingestion), Stage 4 (model_inference), Stage 5 (model_evaluation), Stage 6 (post_inference_monitoring component-level).
- **GAP-TEST-02**: No end-to-end smoke test that runs `run_pipeline.py` with synthetic data and verifies all 7 default stages complete.

---

## 9. FastAPI (Inference API)

### What it does in THIS repo
- **Module**: src/api/app.py (892 lines).
- **Endpoints**: `GET /api/health`, `GET /api/model/info`, `GET /metrics` (Prometheus), `POST /api/upload` (CSV inference), `GET /` (embedded HTML dashboard).
- **Inline monitoring**: `_run_monitoring()` at app.py:220 — 3-layer monitoring on every upload.
- **Prometheus metrics**: 7 metrics exported at /metrics (app.py:40–76).
- **Docker deployment**: Dockerfile.inference CMD → `uvicorn src.api.app:app --host 0.0.0.0 --port 8000`.

### Why chosen
- **Problem solved**: Need HTTP interface for production-like data upload + real-time inference + monitoring in a single request.
- **vs Flask**: FastAPI provides automatic OpenAPI docs, Pydantic validation, async support, and native type hints.
- **WHY bucket**: Reliability | Scalability/Cost

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| FastAPI framework | OFFICIAL_DOC | [REF_FASTAPI] |
| Uvicorn ASGI server | OFFICIAL_DOC | [REF_UVICORN] |

### How to verify
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/api/health
curl http://localhost:8000/api/model/info
```

---

## 10. TensorFlow / Keras

### What it does in THIS repo
- **Model architecture**: 1D-CNN-BiLSTM defined in src/train.py:235–350 (`HARModelBuilder.create_1dcnn_bilstm()`).
- **Input shape**: (None, 200, 6) — 200 timesteps × 6 sensor channels.
- **Output shape**: (None, 11) — 11 activity classes with softmax.
- **Training**: 5-fold stratified cross-validation (src/train.py:355–700, `HARTrainer.run_cross_validation()`).
- **Inference**: Batch prediction via `model.predict()` in src/run_inference.py:290 (`InferenceEngine.predict_batch()`).

### Why chosen
- **Problem solved**: HAR from wrist-worn IMU requires temporal feature extraction (CNN) + sequential modeling (BiLSTM). Architecture validated in thesis reference paper [REF_PAPER_CNN_BILSTM].
- **vs PyTorch**: TF/Keras chosen for consistency with thesis supervisor's existing codebase and deployment tooling.
- **WHY bucket**: Reliability

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| 1D-CNN-BiLSTM architecture | PAPER | [REF_PAPER_CNN_BILSTM] |
| TF/Keras API | OFFICIAL_DOC | [REF_TF_KERAS] |

### How to verify
```bash
python -c "from src.train import HARModelBuilder, TrainingConfig; m = HARModelBuilder(TrainingConfig()).create_1dcnn_bilstm(); m.summary()"
```

---

## 11. Domain Adaptation (AdaBN / TENT)

### What it does in THIS repo
- **AdaBN**: src/domain_adaptation/adabn.py:55 (`adapt_bn_statistics()`) — replaces BN running mean/var with target domain statistics. No gradient updates.
- **TENT**: src/domain_adaptation/tent.py:50 (`tent_adapt()`) — fine-tunes BN gamma/beta via entropy minimization. OOD guard at entropy > 0.85, rollback on entropy increase or confidence drop.
- **Two-stage**: src/components/model_retraining.py:230 (`_run_adabn_then_tent()`) — AdaBN first (fast, zero-gradient), then TENT (fine-tune affine params).
- **Pseudo-labeling**: src/train.py:720 (`DomainAdaptationTrainer._retrain_pseudo_labeling()`) — confidence-filtered pseudo-labels at threshold 0.70.

### Why chosen
- **Problem solved**: Production wearable data has distribution shift vs. training data (different users, sensor placement, activity patterns). Labels are unavailable in production.
- **vs Fine-tuning**: Full fine-tuning requires labels; AdaBN/TENT are unsupervised (label-free).
- **vs DANN/MMD**: Explicitly not implemented (`NotImplementedError` at model_retraining.py:68–74) — too complex for thesis scope.
- **WHY bucket**: Reliability | Scalability/Cost

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| AdaBN method | PAPER | [REF_ADABN_PAPER] |
| TENT method | PAPER | [REF_TENT_PAPER] |
| OOD guard threshold (0.85) | EMPIRICAL_CALIBRATION | src/domain_adaptation/tent.py:~50 — requires calibration artifact |
| Confidence threshold (0.70) | EMPIRICAL_CALIBRATION | src/train.py:~720 — requires calibration artifact |

### How to verify
```bash
pytest tests/test_adabn.py -v
pytest tests/test_retraining.py -v
python run_pipeline.py --retrain --adapt adabn_tent --skip-ingestion --skip-validation
```

### P0 Gaps
- **GAP-ADAPT-01**: TENT OOD threshold 0.85 and confidence threshold 0.70 lack empirical calibration artifacts (CSV/plot showing how these values were selected). Add sweep script.

---

## 12. Calibration & Uncertainty

### What it does in THIS repo
- **Temperature scaling**: src/calibration.py:70 (`TemperatureScaler`) — post-hoc calibration via NLL minimization. Initial T=1.5, fitted via scipy.optimize.
- **MC Dropout**: src/calibration.py:170 (`MCDropoutEstimator`) — 30 forward passes with dropout enabled. Outputs: predictive entropy, mutual information, expected entropy.
- **ECE evaluation**: src/calibration.py:260 (`CalibrationEvaluator.expected_calibration_error()`) — 15 bins, reliability diagram.
- **Unlabeled analysis**: src/calibration.py:380 (`UnlabeledCalibrationAnalyzer.analyze()`) — proxy calibration without labels. Warns on overconfidence > 0.80, underconfidence < 0.50.

### Why chosen
- **Problem solved**: Neural networks (especially with softmax) produce overconfident predictions. Temperature scaling corrects this without retraining. MC Dropout quantifies epistemic uncertainty for OOD detection.
- **WHY bucket**: Reliability | Observability

### Evidence
| Claim | Evidence type | Artifact |
|---|---|---|
| Temperature scaling | PAPER | [REF_TEMP_SCALING] |
| MC Dropout | PAPER | [REF_MC_DROPOUT] |
| ECE metric | PAPER | [REF_TEMP_SCALING] |
| Initial T=1.5 | EMPIRICAL_CALIBRATION | Fitted via scipy — output at outputs/calibration/temperature.json |

### How to verify
```bash
python run_pipeline.py --stages calibration --skip-ingestion --skip-validation
pytest tests/test_calibration.py -v
```

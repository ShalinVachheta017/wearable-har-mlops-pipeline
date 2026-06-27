# DEFENSE Q&A — Anticipated Examiner Questions

> **Purpose**: Pre-loaded answers for every "why" question an examiner might ask during your Master's thesis defense.
> Each answer cites the exact repo location and evidence type.
> Generated from a complete scan of the MasterArbeit_MLops repository.

---

## Table of Contents

1. [Pipeline Architecture](#1-pipeline-architecture)
2. [Data & Preprocessing](#2-data--preprocessing)
3. [Windowing & Features](#3-windowing--features)
4. [Model Architecture](#4-model-architecture)
5. [Training & Cross-Validation](#5-training--cross-validation)
6. [DVC — Data Versioning](#6-dvc--data-versioning)
7. [MLflow — Experiment Tracking](#7-mlflow--experiment-tracking)
8. [Docker — Containerization](#8-docker--containerization)
9. [CI/CD — GitHub Actions](#9-cicd--github-actions)
10. [Monitoring - Offline Artifacts](#10-monitoring---offline-artifacts-prometheusgrafana-optional)
11. [Alerting - Review Gate](#11-alerting---review-gate-not-alertmanager)
12. [Trigger Policy & Retraining](#12-trigger-policy--retraining)
13. [Domain Adaptation](#13-domain-adaptation)
14. [Calibration & Uncertainty](#14-calibration--uncertainty)
15. [Model Governance — Registration & Baseline](#15-model-governance--registration--baseline)
16. [Testing Strategy](#16-testing-strategy)
17. [Threshold Governance](#17-threshold-governance)
18. [Training–Inference Parity](#18-traininginference-parity)
19. [Security & Rollback](#19-security--rollback)

---

## 1. Pipeline Architecture

### Q: "Why 10 stages instead of a single training script?"

**A:** The pipeline decomposes the ML lifecycle into 10 stages: 7 core operational stages (always run) plus 3 conditional mutation stages (run only when governance conditions are met). The 7 core stages are ingestion, preprocessing, windowing, training, evaluation, monitoring (Stage 6), and trigger evaluation (Stage 7). The 3 conditional stages are retraining, model registration, and baseline update — these execute only when the trigger policy fires and the collapse guard clears.

**Evidence:**

- `src/pipeline/production_pipeline.py` — stage registration and orchestration
- Each stage can be run independently: `python run_pipeline.py --stages monitoring,trigger`
- Stages 1–7 are the defended operational assessment path; stages 8–10 are the conditional mutation path

**Why this matters:** Separating assessment (always runs) from mutation (governance-gated) is the core architectural claim: the system can detect risk without automatically acting on it. A monolithic script conflates these two responsibilities.

**Counter-argument ready:** "Why not a DAG (Airflow, Prefect)?" → Linear sequential execution was chosen for MLflow integration and trigger-policy coupling. A DAG engine would enable parallel stages but adds orchestrator complexity outside the defended scope.

---

### Q: "Why does the pipeline have a `continue_on_failure` flag?"

**A:** `ProductionPipeline.__init__()` at `src/pipeline/production_pipeline.py:84` accepts `continue_on_failure`. When True, a failing stage is logged but the pipeline advances to the next stage.

**Evidence:**
- `production_pipeline.py:140-160` — try/except per stage with `self.failed_stages.append(stage_name)`
- This enables best-effort runs during development and CI

**Why this matters:** In production, you want fail-fast (default: `continue_on_failure=False`). In CI integration tests, you may want to see which stages pass even if an early stage has issues with test data.

---

### Q: "How does stage orchestration work? Is there a DAG?"

**A:** The pipeline uses a linear stage list, not a DAG. Stages execute sequentially in the order defined by `ALL_STAGES` at `production_pipeline.py:54-68`. The user selects which stages to run via `--stages` CLI arg (`run_pipeline.py:156-180`), and `ProductionPipeline.run()` iterates through only the requested stages in order.

**Evidence:**
- `production_pipeline.py:117-180` — `run()` method iterates `self.stages`
- No inter-stage dependency graph — each stage reads from disk artifacts written by previous stages

**Trade-off acknowledged:** A DAG (e.g., Airflow, Prefect) would enable parallel stage execution and explicit dependency tracking. The linear approach was chosen because the thesis focuses on MLOps practices, not workflow engine evaluation. A `P0 gap` exists for DAG migration.

---

## 2. Data & Preprocessing

### Q: "Why convert milliG to m/s² and not leave raw values?"

**A:** The model expects m/s² inputs because the training data from the WISDM dataset uses that unit. If inference data arrives in milliG (which some Garmin watches emit), predictions are nonsensical.

**Evidence:**
- `config/pipeline_config.yaml:27-31` — `unit_conversion: enabled: true, source_unit: milliG, target_unit: m_per_s2`
- `src/preprocess_data.py:60` — `UnitDetector` class with heuristic-based detection (values > 100 likely milliG)
- `[REF_SENSOR_SPEC]` — Garmin sensor documentation

**Why this matters:** A model trained on m/s² data receiving milliG data sees values ~100× larger, making all predictions garbage. Auto-detection prevents silent scale mismatch.

---

### Q: "Why is gravity removal disabled?"

**A:** `config/pipeline_config.yaml:37-44` sets `gravity_removal: enabled: false` with an inline comment: the CNN-BiLSTM model from `[REF_PAPER_CNN_BILSTM]` was trained with gravity included. Removing it would introduce a domain shift vs. the original training regime.

**Evidence:**
- `config/pipeline_config.yaml:37-44` — explicit rationale in config comments
- `src/entity/config_entity.py:110` — `gravity_removal` field in `PreprocessingConfig` dataclass

**Risks:** If someone enables gravity removal without retraining, the model sees different input distributions. The config comment serves as a guard rail.

---

### Q: "Why no external scaler in final production inference?"

**A:** For the defended final production path, neither z-score nor min-max normalization is applied. The runtime contract preserves raw physical IMU units after accelerometer conversion to m/s^2 and gyroscope retention in deg/s. The train-only z-score scaler remains useful for model-development checks and explicitly labeled A/B diagnostics, but it is not a production inference dependency.

**Evidence:**
- `config/pipeline_config.yaml` - `enable_normalization: False`, `normalization_variant: "none"`
- `src/components/data_transformation.py` - production metadata records raw physical input space
- `src/api/app.py` - API upload path does not load or apply the scaler

---

## 3. Windowing & Features

### Q: "Why window size = 200 (4 seconds at 50Hz)?"

**A:** This is both a **literature-driven** and **empirically validated** choice. The reference CNN-BiLSTM paper uses window_size=200. We ran an ablation study to verify.

**Evidence:**
- `src/config.py:67` — `WINDOW_SIZE = 200`
- `config/pipeline_config.yaml:74` — `window_size: 200`
- `reports/ABLATION_WINDOWING.csv` — 6 configurations tested (ws=50,100,128,200,256,512). Window=200 yields F1=0.685 and flip_rate_median=0.239
- `reports/WINDOWING_JUSTIFICATION.md` — full rationale document

**Trade-off:** ws=256 actually achieves higher F1 (0.731) — but ws=200 was chosen for paper-compatibility and sufficient temporal context. This trade-off is documented.

**Counter-argument ready:** "If ws=256 gives better F1, why not use it?" → Because reproducibility against the reference paper matters more for a thesis. The 4.6pp F1 gap is acknowledged, and the ablation proves awareness.

---

### Q: "Why 50% overlap and not 75% or 25%?"

**A:** 50% overlap balances decision density (predictions per second) vs. computational cost.

**Evidence:**
- `src/config.py:68` — `OVERLAP = 0.5`
- `reports/ABLATION_WINDOWING.csv` — flip_rate_median=0.239 at 50% overlap; higher overlap increases compute without flip-rate benefit at ws=200

**Risks:** 25% overlap loses temporal resolution; 75% nearly doubles compute for marginal stability gain.

---

## 4. Model Architecture

### Q: "Why 1D-CNN + BiLSTM and not a Transformer or pure CNN?"

**A:** The CNN-BiLSTM architecture is established for time-series HAR. CNNs extract local spatial features from sensor channels; BiLSTM captures temporal dependencies in both directions.

**Evidence:**
- `src/train.py:235-350` — `HARModelBuilder.build_model()` defines the architecture: Conv1D layers → BiLSTM → Dense
- Input shape: `(None, 200, 6)` — 200 timesteps, 6 sensor channels (Ax, Ay, Az, Gx, Gy, Gz)
- Output shape: `(None, 11)` — 11 activity classes (softmax)
- `[REF_PAPER_CNN_BILSTM]` — Reference paper establishing this architecture for WISDM data

**Counter-argument ready:** "Transformers achieve SOTA on some HAR benchmarks" → True, but Transformers require more data and compute. This thesis focuses on MLOps infrastructure, not pushing SOTA accuracy. The CNN-BiLSTM is a well-understood, reproducible baseline that lets the MLOps framework be the contribution.

---

### Q: "How many parameters does the model have?"

**A:** The model definition is in `src/train.py:235-350`. The exact parameter count depends on the Conv1D filters and LSTM units configured in `src/entity/config_entity.py` (TrainingConfig dataclass). Typical configuration: 2 Conv1D layers (64, 128 filters) + BiLSTM (128 units) + Dense(11). Approximate parameter count: ~500K-1M, lightweight enough for edge-adjacent deployment.

---

## 5. Training & Cross-Validation

### Q: "Why 5-fold cross-validation?"

**A:** `src/train.py` — `HARTrainer` class implements stratified 5-fold CV. 5-fold is the standard for moderate-sized datasets — it balances bias-variance tradeoff in performance estimation.

**Evidence:**
- `src/train.py:400-600` — 5-fold CV with stratification
- Each fold is logged to MLflow as a child run
- Final metrics are mean ± std across folds

**Counter-argument ready:** "Why not leave-one-subject-out?" → Valid critique. LOSO is more realistic for HAR (test on unseen users). This is a known gap documented in `reports/EVIDENCE_PACK_INDEX.md`. The thesis scope prioritized MLOps infrastructure over perfect evaluation methodology.

---

### Q: "How do you prevent data leakage between train and test?"

**A:** Three layers of protection:

1. **Temporal split**: `src/data_splitting.py` splits data ensuring no temporal overlap between train/val/test
2. **Windowing after split**: Windows are created from already-split data, preventing a single raw sample from appearing in both train and test windows
3. **Scaler provenance separated from production inference**: train/A-B scaler artifacts are provenance-checked, while final production inference applies no external scaler

**Evidence:**
- `src/data_splitting.py` — split logic with subject-awareness
- `config/pipeline_config.yaml:50-55` — split ratios documented
- `tests/test_preprocessing.py` — tests verify no index overlap

---

## 6. DVC — Data Versioning

### Q: "Why DVC instead of Git LFS?"

**A:** DVC provides **pipeline-aware** data versioning, not just large-file storage.

| Feature | DVC | Git LFS |
|---------|-----|---------|
| Pipeline DAG tracking | Yes (dvc.yaml) | No |
| Remote storage backends | S3, GCS, Azure, local | Git server only |
| Metric/parameter tracking | Yes (dvc metrics, dvc params) | No |
| Reproducibility | `dvc repro` re-runs changed stages | No pipeline concept |
| Lock file | dvc.lock captures exact hashes | No equivalent |

**Evidence:**
- `.dvc/config` — configured with local remote at `../../.dvc_storage`
- `data/*.dvc` — DVC tracking files for datasets
- `models/*.dvc` — DVC tracking files for model artifacts
- `[REF_DVC_DOCS]` — Official DVC documentation

**Counter-argument ready:** "Your DVC remote is local, not S3. Is that production-grade?" → No. The local remote is a thesis-scope simplification. Migrating to S3 requires only changing `.dvc/config remote` URL. The DVC *workflow* (track, push, pull, repro) is identical regardless of backend.

---

### Q: "Where is the DVC pipeline definition?"

**A:** There is no `dvc.yaml` pipeline file in this repository. DVC is used purely for data/model artifact versioning (`.dvc` tracking files), not for pipeline orchestration. The pipeline is orchestrated by `src/pipeline/production_pipeline.py` with Python-level stage management.

**Trade-off:** Using `dvc.yaml` would enable `dvc repro` for automatic cache-aware re-execution. The custom Python pipeline was chosen for finer-grained control over MLflow integration, fallback artifacts, and the trigger policy — features hard to express in DVC YAML.

---

## 7. MLflow — Experiment Tracking

### Q: "Why MLflow and not Weights & Biases (W&B)?"

**A:** MLflow is **open-source, self-hosted**, and provides a model registry with stage transitions.

| Feature | MLflow | W&B |
|---------|--------|-----|
| Self-hosted | Yes (docker-compose) | Cloud-only (free tier) |
| Model Registry | Built-in with Staging→Production | Limited |
| Open-source | Apache 2.0 | Proprietary |
| Docker integration | First-class | Plugin |

**Evidence:**
- `docker-compose.yml:5-28` — MLflow server service with SQLite backend and `/mlruns` artifact store
- `config/mlflow_config.yaml` — tracking URI, experiment naming
- `src/pipeline/production_pipeline.py:97-115` — MLflow lifecycle: `start_run()`, `log_param()`, `log_metric()`, `log_artifact()`
- `src/components/model_registration.py` — Model registry integration with quality gate

**Counter-argument ready:** "W&B has better visualization" → True, but introduces external dependency and data residency concerns. MLflow runs entirely in the Docker Compose stack — examiner can `docker compose up` and see everything locally.

---

### Q: "How does the model registry quality gate work?"

**A:** `src/components/model_registration.py` implements a registration gate that checks:

1. **Current model accuracy** must exceed **baseline accuracy - degradation_tolerance** (default 0.005 = 0.5%)
2. If `block_if_no_metrics = True`, models without evaluation metrics are rejected
3. If `block_if_no_metrics = False` (default), TTA/domain-adapted models can register without labeled metrics

**Evidence:**
- `src/entity/config_entity.py:253` — `degradation_tolerance = 0.005`
- `src/entity/config_entity.py:256` — `block_if_no_metrics = False`
- `tests/test_model_registration_gate.py` — 8 test cases covering pass/fail/no-metrics scenarios

**Why 0.5% tolerance?** Tighter values (0.1%) caused false rejects due to training noise across folds. 0.5% absorbs noise while still catching real degradation.

---

## 8. Docker — Containerization

### Q: "Why two separate Dockerfiles instead of one?"

**A:** Attack surface reduction and image size optimization.

| Image | Base | Key packages | Size |
|-------|------|--------------|------|
| Dockerfile.inference | python:3.11-slim | FastAPI, uvicorn, TF-lite | ~1.5GB |
| Dockerfile.training | python:3.11-slim | TensorFlow, scikit-learn, MLflow, DVC | ~3GB |

**Evidence:**
- `docker/Dockerfile.inference:1-65` — Inference image with `HEALTHCHECK` at line 62
- `docker/Dockerfile.training:1-52` — Training image with full ML stack
- `docker-compose.yml:54-72` — `inference` service uses `Dockerfile.inference`
- `[REF_DOCKER_BEST]` — Docker best practices recommend minimal production images

**Counter-argument ready:** "Why not use multi-stage builds?" → The images already use `python:3.11-slim` (not full python:3.11). A multi-stage build could further reduce size by ~200MB by separating build-time deps. This is a known improvement opportunity.

---

### Q: "How do the optional Docker services interact?"

**A:** `docker-compose.yml` contains an optional local service stack. It is useful for packaging and demonstrations, but Prometheus/Grafana/Alertmanager are not defended as current thesis monitoring evidence.

1. **mlflow** (port 5000) — Experiment tracking server, SQLite backend
2. **inference** (port 8000) — FastAPI prediction API, Prometheus `/metrics` endpoint
3. **training** — Ephemeral container for training runs
4. **preprocessing** — Ephemeral container for data preprocessing
5. **prometheus** (port 9090) - optional historical/future observability
6. **alertmanager** (port 9093) - optional historical/future alert routing
7. **grafana** (port 3000) - optional historical/future dashboarding

**Evidence:**
- `docker-compose.yml:1-223` — Full service definitions
- `config/prometheus.yml:37` — scrape target `inference:8000`
- `config/grafana/datasources/prometheus.yml` — Prometheus datasource at `http://prometheus:9090`

**Current evidence flow:** pipeline artifacts and logs -> Stage 6 monitoring report -> Stage 7 trigger decision -> review/label/QA gate. Do not claim Prometheus alerts trigger retraining in the defended runtime.

---

## 9. CI/CD — GitHub Actions

### Q: "Why is CI/CD split into two workflows?"

**A:** The repository now separates quality checks and release delivery:

- **CI** in `.github/workflows/ci.yml` validates code on push/PR.
- **CD** in `.github/workflows/cd.yml` runs on release tags or manual dispatch.

This split improves clarity and reduces accidental release coupling.

CI job chain:

```
lint -> unit-tests -> docker-build-check
```

CD job chain:

```
build-and-push -> smoke-test
```

**Evidence:**
- `.github/workflows/ci.yml` — push/PR quality gates and build viability checks.
- `.github/workflows/cd.yml` — tagged release build/push plus health smoke-test.
- `.github/workflows/README.md` — workflow topology and maintenance guide.

**Counter-argument ready:** "Why not keep one single combined workflow?" -> Separation reduces cognitive load, keeps release logic independent, and supports cleaner thesis explanation of CI vs CD responsibilities.

---

### Q: "What triggers CI and CD now?"

**A:**

1. **CI triggers** (`.github/workflows/ci.yml`): push to `main` and `develop`, and pull requests to `main`.
2. **CD triggers** (`.github/workflows/cd.yml`): tag pushes matching `v*.*.*`, and manual `workflow_dispatch`.

This means normal development runs CI, while releases run CD.

---

## 10. Monitoring - Offline Artifacts, Prometheus/Grafana Optional

### Q: "Why not rely on Prometheus + Grafana as thesis evidence?"

**A:** The defended thesis implementation is offline-first and evidence is generated by pipeline artifacts, not by a live observability stack. Prometheus and Grafana remain useful optional infrastructure/future work, but they are not required to reproduce the Stage 6/7 governance claim.

**Evidence:**
- `src/components/post_inference_monitoring.py`
- `src/monitoring/post_inference_monitor.py`
- `artifacts/<run_id>/monitoring/monitoring_report.json`
- `artifacts/<run_id>/trigger/trigger_decision.json`

**Counter-argument ready:** "Why not Prometheus?" -> It is appropriate future infrastructure, but a thesis freeze needs reproducible file artifacts that can be inspected without a running service stack.

---

### Q: "How is the monitoring 3-layer model implemented?"

**A:** The defended Stage 6 runtime is implemented by `src/components/post_inference_monitoring.py` and `src/monitoring/post_inference_monitor.py`. The API contains a lightweight local monitoring view, but thesis evidence should come from the offline pipeline artifacts.

| Layer | What | Metric | Threshold |
|-------|------|--------|-----------|
| Confidence/uncertainty | Softmax confidence, entropy, top-two margin | Stage 4/6 artifacts | < 0.70 mean confidence or > 20% uncertain windows = Stage 6 warning |
| Temporal behavior | Transition rate, dwell behavior | Stage 6 monitoring report | > 35% transition rate = Stage 6 warning |
| Drift/collapse | Raw physical baseline drift, dominant class, low-motion collapse risk | Stage 6 monitoring report | drift z-score > 1.8 or dominance > 85% = Stage 6 warning |

These are computed over session-level batches in the offline-first pipeline. The API request path is a local demo/service view and must not be used as evidence for automatic model mutation.

**Evidence:**
- `src/components/post_inference_monitoring.py`
- `src/monitoring/post_inference_monitor.py`
- `outputs/monitoring/monitoring_report.json`

---

## 11. Alerting - Review Gate, Not Alertmanager

### Q: "How do alerts work in this system?"

**A:** In the defended runtime, Stage 6/7 warnings are artifact-backed governance signals. They route to monitor, review, or review/label queue states. They do not automatically trigger retraining from unlabeled production data.

| Signal | Condition | Governance outcome |
|-------|-----------|--------------------|
| Low confidence | mean confidence below 0.70 in Stage 6 | monitor/review depending on combined signals |
| High uncertainty | uncertain windows above 20% | monitor/review depending on combined signals |
| Drift | raw physical baseline drift above 1.8 | review signal, not mutation proof |
| Collapse | dominant class above warning/critical band or low-motion collapse risk | review and `should_retrain=false` |

**Governance inhibition:**
- collapse risk blocks unlabeled pseudo-label/adaptation retraining
- missing or mismatched baseline blocks fake critical drift interpretation
- cooldown/review state prevents rapid mutation loops

**Evidence:**
- `src/trigger_policy.py`
- `src/components/trigger_evaluation.py`
- `docs/MONITORING_AND_TRIGGER_POLICY.md`

---

## 12. Trigger Policy & Retraining

### Q: "Why 2-of-3 voting instead of single-signal triggering?"

**A:** Single-signal triggering produces a **13.9% false alarm rate (FAR)**. 2-of-3 voting reduces FAR to **0.7%**.

The three signals are:
1. **Accuracy degradation** — model accuracy drops below threshold
2. **Confidence degradation** — prediction confidence drops below threshold
3. **Drift detection** — feature distribution shift detected

**Evidence:**
- `src/trigger_policy.py:470` — `_apply_voting_logic()` counts signals ≥ `min_signals_for_retrain` (default: 2)
- `src/trigger_policy.py:92-130` — `TriggerThresholds` dataclass defining all thresholds
- `reports/TRIGGER_POLICY_EVAL.csv` — 500 simulated sessions: 1-of-3 precision=0.816 FAR=0.139; 2-of-3 precision=0.988 FAR=0.007
- `reports/TRIGGER_POLICY_EVAL.md` — Full simulation methodology

**Counter-argument ready:** "2-of-3 could miss a scenario where only one signal fires early" → True. The cooldown mechanism (24h) ensures we don't over-retrain, but a legitimate single-signal scenario (e.g., sudden accuracy crash) would need to wait for a second signal. The 0.988 precision justifies this trade-off.

---

### Q: "Why 24-hour cooldown?"

**A:** At `src/trigger_policy.py:135`, after a retrain trigger fires, the system enters a 24-hour cooldown during which no new triggers are accepted.

**Evidence:**
- `src/entity/config_entity.py:210` — `cooldown_hours = 24`
- `reports/TRIGGER_POLICY_EVAL.md` — Simulation shows 6h cooldown is optimal, but 24h was chosen for safety (zero FAR in simulation). This is a conservative choice prioritizing stability over responsiveness.
- `src/trigger_policy.py:500-530` — Cooldown check in `should_trigger()`

**Risks:** 24h may delay response to a second drift event that occurs shortly after the first. Documented as an acceptable risk for thesis scope.

---

## 13. Domain Adaptation

### Q: "What domain adaptation methods are implemented and why?"

**A:** Three methods, each addressing a different adaptation scenario:

| Method | File | Use Case | Supervision |
|--------|------|----------|-------------|
| AdaBN | `src/domain_adaptation/adabn.py:55` | Batch normalization statistics update | Unsupervised |
| TENT | `src/domain_adaptation/tent.py:50` | Test-time entropy minimization | Unsupervised |
| Pseudo-labeling | `src/train.py:~720` | Self-training with confident predictions | Semi-supervised |

**Evidence:**
- `src/domain_adaptation/adabn.py:55` — `adapt_bn_statistics()` — replaces BN running mean/var with target domain statistics. From Li et al. 2018 `[REF_ADABN_PAPER]`
- `src/domain_adaptation/tent.py:50` — `tent_adapt()` — minimizes prediction entropy on target data. From Wang et al. 2021 `[REF_TENT_PAPER]`
- OOD guard at `tent.py:~85` — entropy > 0.85 threshold prevents adaptation on out-of-distribution data
- `src/train.py:~700-800` — `DomainAdaptationTrainer` manages all three methods

**Counter-argument ready:** "Why not use more advanced methods like DANN or CORAL?" → These require access to source domain data during adaptation. AdaBN/TENT operate on target data only, which matches the deployment scenario where source data may not be available.

---

### Q: "What is the TENT OOD entropy guard?"

**A:** At `src/domain_adaptation/tent.py:~85`, before applying TENT adaptation, the system checks the mean entropy of predictions. If entropy exceeds 0.85, the batch is considered out-of-distribution and adaptation is skipped.

**Why:** TENT minimizes entropy — if the model is already highly uncertain (OOD data), minimizing entropy forces the model toward arbitrary confident predictions, corrupting the batch normalization parameters.

**P0 gap:** The 0.85 threshold (`GAP-ADAPT-01`) has no calibration artifact. It needs an empirical sweep on known OOD data to validate.

---

## 14. Calibration & Uncertainty

### Q: "What is temperature scaling and why do you use it?"

**A:** Temperature scaling applies a single learned parameter $T$ to the logits before softmax: $\hat{p}_i = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$. This calibrates the model's confidence to match empirical accuracy.

**Evidence:**
- `src/calibration.py:70` — `TemperatureScaler` class, initial $T=1.5$, optimized via scipy L-BFGS-B on validation NLL
- `src/entity/config_entity.py:286` — Default temperature configuration
- `outputs/calibration/temperature.json` — Fitted temperature value
- `[REF_TEMP_SCALING]` — Guo et al. 2017

**Why:** Neural networks are typically overconfident (softmax max > actual accuracy). A monitoring system that uses raw softmax probabilities for confidence thresholds will have miscalibrated alerts.

---

### Q: "What is MC Dropout and why 30 passes?"

**A:** Monte Carlo Dropout keeps dropout active at inference time and runs $N$ forward passes. The prediction is the mean, and uncertainty is the variance across passes.

**Evidence:**
- `src/calibration.py:170` — `MCDropoutEstimator` class with `n_passes=30`
- `src/entity/config_entity.py:289` — Default pass count
- `[REF_MC_DROPOUT]` — Gal & Ghahramani 2016

**Why 30:** The original paper suggests 10-100 passes. 30 is a common practical choice — enough to estimate variance reliably, not so many that inference becomes impractical. At 200-sample windows with 6 channels, 30 passes add ~300ms latency.

---

### Q: "How is calibration quality measured?"

**A:** Expected Calibration Error (ECE) with 15 bins:

$$ECE = \sum_{b=1}^{B} \frac{|B_b|}{N} |acc(B_b) - conf(B_b)|$$

**Evidence:**
- `src/calibration.py:260` — `CalibrationEvaluator` class computes ECE and generates reliability diagrams
- `src/entity/config_entity.py:295` — `ece_n_bins = 15`
- `outputs/calibration/reliability_diagram.png` — Visual calibration assessment
- `[REF_TEMP_SCALING]` — ECE definition from Guo et al. 2017

---

## 15. Model Governance — Registration & Baseline

### Q: "What prevents a bad model from being deployed?"

**A:** Three gates:

1. **Registration gate** (`src/components/model_registration.py:74`) — New model accuracy must be ≥ baseline - `degradation_tolerance` (0.005)
2. **`block_if_no_metrics` flag** (`src/entity/config_entity.py:256`) — When True, models without evaluation metrics are blocked
3. **`promote_to_shared = False`** (`src/entity/config_entity.py:277`) — Baseline update requires explicit `--update-baseline` flag; no auto-promotion

**Evidence:**
- `tests/test_model_registration_gate.py` — 8 test cases covering gate behavior
- `src/components/baseline_update.py:103` — Baseline versioning with archive-on-promote

**Counter-argument ready:** "What about A/B testing or canary deployments?" → Not implemented. The registration gate is a pre-deployment quality check, not a runtime traffic-splitting mechanism. A/B testing is out of thesis scope but would be the natural next step.

---

### Q: "How does baseline management work?"

**A:** `src/components/baseline_update.py` manages the production baseline:

1. Current baseline metrics are loaded from `outputs/baseline/metrics.json`
2. New model metrics are compared against baseline
3. If better (within tolerance), the old baseline is archived with timestamp
4. New baseline is written

**Evidence:**
- `src/components/baseline_update.py:50-120` — Full baseline update logic
- `src/entity/config_entity.py:166` — `max_baseline_age_days = 90`
- `config/monitoring_thresholds.yaml:93` — Staleness threshold alignment

---

## 16. Testing Strategy

### Q: "What is the test coverage and how are tests organized?"

**A:** 20 test files in `tests/` with pytest markers for test categorization:

| Marker | Purpose | Example |
|--------|---------|---------|
| `@pytest.mark.slow` | Tests taking > 10s (model training, full pipeline) | `test_training.py` |
| `@pytest.mark.integration` | End-to-end tests requiring Docker/MLflow | `test_integration.py` |
| `@pytest.mark.gpu` | Tests requiring GPU | Tests with CUDA operations |

**Evidence:**
- `pytest.ini` — Marker definitions and test configuration
- `tests/test_threshold_consistency.py` — Cross-file threshold consistency checks
- `tests/test_preprocessing.py` — Unit tests for data pipeline
- `tests/test_model_registration_gate.py` — Gate behavior tests
- CI runs: `pytest -m "not slow"` for fast tests, `pytest -m slow` separately

**Coverage of pipeline stages:** Tests cover the seven core runtime stages and the conditional governance path. Older stage-12-to-14 wording is historical and must not be used as the current defended stage map.

---

### Q: "What does test_threshold_consistency test?"

**A:** `tests/test_threshold_consistency.py` verifies that Stage 6 monitoring thresholds, Stage 7 trigger thresholds, and API/pipeline threshold loading remain aligned where they share a contract.

**Why this matters:** If the pipeline and API disagree about confidence, uncertainty, transition, or drift thresholds, a thesis run can produce contradictory monitoring and governance evidence.

**Evidence:**
- `tests/test_threshold_consistency.py`
- `src/entity/config_entity.py`
- `src/trigger_policy.py`

---

## 17. Threshold Governance

### Q: "How were all the thresholds chosen? Are they arbitrary?"

**A:** Thresholds fall into three categories:

| Category | How chosen | Example |
|----------|-----------|---------|
| Paper-backed | From cited literature | ECE bins=15 (Guo et al. 2017), MC passes=30 (Gal & Ghahramani 2016) |
| Engineering operating points | Calibrated against training distribution + 26-session production replays | Stage 6: confidence warn 0.70, uncertain 20%, drift z-score 1.8, dominant-class warn 85% |
| Governance trigger thresholds | Citation-backed; Stage 7 intentionally looser than Stage 6 so monitoring warns before escalation | Stage 7: confidence warn 0.65, drift z-score 2.0/3.0 |
| Project decisions | Author choice with documented rationale | degradation_tolerance=0.005, block_if_no_metrics=false |

**Evidence artifacts:**
- `reports/THRESHOLD_CALIBRATION.csv` — 54-row sweep: varied confidence_warn (0.40-0.80), drift_zscore (1.5-3.0), degradation_tol (0.001-0.050)
- `reports/TRIGGER_POLICY_EVAL.csv` — 500-session simulation results
- `reports/ABLATION_WINDOWING.csv` — 6 window configurations

**Important calibration-gap caveat:** Stage 6 thresholds are engineering operating points calibrated against this repository's training distribution and 26-session production-style replays. A multi-participant held-out longitudinal evaluation is required before they can be treated as statistically robust deployment limits. This is explicitly stated in Ch8 limitations and cross-referenced from the threshold calibration gap section (Ch6 §6.x).

**P0 gaps** (thresholds without calibration evidence):

- `GAP-ADAPT-01`: TENT OOD entropy threshold (0.85) — no calibration sweep
- `GAP-EWC-01`: EWC lambda (1000) — no lambda ablation study
- `GAP-PSEUDO-01`: Pseudo-label confidence (0.70) — no error-rate validation

---

### Q: "How does the system detect dominant-class collapse, and why is that important?"

**A:** Stage 6 (`PostInferenceMonitor`) computes the dominant-class percentage across all windows in a session and emits two tiered flags: `dominance_warning=True` at ≥85% and `dominance_critical=True` at ≥95%, both surfaced in `layer1_confidence` alongside overall status.

**Why it matters:** A model that confidently predicts a single class 100% of the time passes all confidence thresholds (high mean confidence, low uncertainty) but is behaviorally collapsed. Without a separate dominance check, this failure mode is invisible to the standard monitoring stack.

**Evidence:**

- `src/entity/config_entity.py` — `PostInferenceMonitoringConfig.dominant_class_warn_threshold=85.0`, `dominant_class_critical_threshold=95.0`
- `src/monitoring/post_inference_monitor.py` — dominance computation and flag emission in `_compute_layer1()`
- `tests/test_post_inference_monitor.py` — four test cases: healthy at 70%, warn at 86%, critical at 96%, config override
- Ch7 experiment: controlled same-input comparison showed the old fine-tuned model produced hand_tapping dominance in 24/25 sessions; the retrained model spanned all 11 classes in 22/25 — this was the motivating evidence for A27

**Counter-argument ready:** "Isn't 85% arbitrary?" → It is an engineering operating point, not a statistically calibrated limit. The thesis explicitly states this in Ch8 limitations and argues that a multi-participant longitudinal reference is required before it becomes a deployment boundary.

---

## 18. Training–Inference Parity

### Q: "How do you ensure the training pipeline and inference API preprocess data identically?"

**A (updated 2026-06-11 for the deployed D1 contract):** Three mechanisms:

1. **Shared constants**: The batch pipeline and API use the same 50 Hz, 200-sample window, 100-sample stride, and six-channel order.
2. **Explicit production input contract**: Both final production paths convert units to m/s² and apply the **saved Garmin users-1–6 train-only StandardScaler** from the D1 contract folder (no refit at inference). *(The earlier Model-A answer — "raw units, no external scaler" — is superseded since 2026-05-28.)*
3. **Docker base**: Both Dockerfiles use `python:3.11-slim` with matching Python/TF versions

**Evidence:**
- `models/runtime_contract/model_d1_final_20260528/model_contract.json` — input space, scaler fit users, label order
- `src/api/app.py` - loads the persisted D1 scaler JSON; scales before windowing; never fits
- `docker/Dockerfile.training:1` and `docker/Dockerfile.inference:1` — Same base image

**Remaining risk:** A future edit could accidentally re-enable a scaler, gravity removal, or calibration in one runtime path. The mitigation is the explicit config contract plus tests that assert raw physical API/pipeline behavior.

---

## 19. Security & Rollback

### Q: "What happens if a retrained model is worse than the current one?"

**A:** The registration gate at `src/components/model_registration.py:74` blocks registration if the new model's accuracy is more than 0.5% below the baseline. If registration is blocked, the current production model remains active.

**Rollback path:**
1. MLflow model registry preserves all model versions
2. DVC tracks model artifacts with hashes
3. Baseline archive (on promote) preserves previous baselines
4. `docker compose` can pin a specific model version via environment variable

**Evidence:**
- `src/components/model_registration.py:74` — Gate logic
- `src/components/baseline_update.py:103` — Archive-on-promote
- `models/*.dvc` — DVC-tracked model artifacts
- `mlruns/` — Full MLflow experiment history

---

### Q: "Is there any authentication or access control?"

**A:** No. The local FastAPI inference API (`src/api/app.py`) has no authentication. Optional local services should not be exposed as production infrastructure.

**Justification:** This is a thesis prototype, not a production deployment. Authentication would add complexity without advancing the MLOps research contribution.

**If asked "what would you add for production?":**
- API key or OAuth2 for FastAPI (`fastapi.security`)
- authentication for any optional observability service
- Docker network isolation (internal networks)
- HTTPS via reverse proxy (nginx/traefik)

---

## Quick Reference: Top 10 "Gotcha" Questions

| # | Question | One-line answer | Evidence |
|---|----------|----------------|----------|
| 1 | Why not Transformer? | Thesis contribution is MLOps, not SOTA accuracy | `src/train.py:235` |
| 2 | Why local DVC remote? | Thesis scope; S3 migration = config change only | `.dvc/config` |
| 3 | Why no dvc.yaml? | Custom Python pipeline needed for MLflow + trigger integration | `production_pipeline.py:54` |
| 4 | Why ws=200 if ws=256 is better? | Paper reproducibility; ablation documents trade-off | `reports/ABLATION_WINDOWING.csv` |
| 5 | Why 24h cooldown, not 6h? | 24h = zero FAR in 500-session simulation | `reports/TRIGGER_POLICY_EVAL.md` |
| 6 | Why no A/B testing? | Out of scope; registration gate is pre-deploy quality check | `src/components/model_registration.py:74` |
| 7 | Why no LOSO CV? | Known gap; 5-fold chosen for MLOps focus | `src/train.py:400` |
| 8 | Why TENT OOD = 0.85? | P0 gap — needs calibration sweep | `src/domain_adaptation/tent.py:~85` |
| 9 | Why no auth? | Thesis prototype; production auth list provided | `src/api/app.py` |
| 10 | Why inline monitoring not sidecar? | Simpler deployment; single container = no inter-service latency | `src/api/app.py:200` |

---

*Generated by scanning the complete MasterArbeit_MLops repository.*
*All file:line references point to actual source code.*
*P0 gaps are explicitly documented — not hidden.*

# WHY BY FILE — Per-File WHY Analysis

> Every critical file answers: WHY does it exist? What happens if you delete it?
> Grouped by directory.

---

## `src/pipeline/`

### `production_pipeline.py` (967 L)

| Field | Value |
|---|---|
| **WHY** | Orchestrates all 14 stages; defines stage ordering, artifact passing, and MLflow lifecycle |
| **WHY Bucket** | Reliability + Governance |
| **Delete Impact** | Pipeline cannot run. Period. |
| **Key Constants** | `ALL_STAGES` (L57–71), `RETRAIN_STAGES` (L73), `ADVANCED_STAGES` (L78) |
| **Depends On** | All 14 component files, `config_entity.py`, `mlflow_tracking.py` |
| **Evidence** | PROJECT_DECISION — modular orchestrator pattern (REF_GOOGLE_MLOPS_CDCT) |

---

## `src/entity/`

### `config_entity.py` (409 L)

| Field | Value |
|---|---|
| **WHY** | Single source of truth for ALL thresholds and config defaults across 14 stages |
| **WHY Bucket** | Reproducibility + Maintainability |
| **Delete Impact** | Every component import fails; entire pipeline breaks |
| **Key Sections** | `PipelineConfig` (L37), then one `@dataclass` per stage (14 total) |
| **Evidence** | PROJECT_DECISION — config-driven architecture avoids hardcoded magic numbers |
| **Verification** | `pytest tests/test_threshold_consistency.py -v` |

---

## `src/`

### `config.py` (82 L)

| Field | Value |
|---|---|
| **WHY** | Global path constants + model constants (WINDOW_SIZE=200, OVERLAP=0.5, NUM_SENSORS=6, NUM_CLASSES=11) |
| **WHY Bucket** | Reproducibility |
| **Delete Impact** | All path resolution fails; window/sensor constants undefined |
| **Key Values** | `WINDOW_SIZE=200`, `OVERLAP=0.5`, `NUM_SENSORS=6`, `NUM_CLASSES=11`, `ACTIVITY_LABELS` (11 items) |
| **Evidence** | PROJECT_DECISION |

### `train.py` (1345 L)

| Field | Value |
|---|---|
| **WHY** | Contains `HARModelBuilder` (architecture), `HARTrainer` (training loop), `DomainAdaptationTrainer` |
| **WHY Bucket** | Reliability (model) |
| **Delete Impact** | Cannot train or retrain models |
| **Key Classes** | `TrainingConfig` (L90: epochs=100, lr=0.001, batch=64, n_folds=5), `HARModelBuilder` (2 variants) |
| **Evidence** | PAPER (REF_CNN_BILSTM_HAR) |

### `mlflow_tracking.py` (643 L)

| Field | Value |
|---|---|
| **WHY** | Wraps MLflow API for experiment tracking, model registration, artifact logging |
| **WHY Bucket** | Reproducibility + Governance |
| **Delete Impact** | No experiment tracking; no model registry; no rollback capability |
| **Evidence** | OFFICIAL_DOC (REF_MLFLOW_TRACKING) |

### `sensor_data_pipeline.py` (1192 L)

| Field | Value |
|---|---|
| **WHY** | Core data engine for Stage 1: Excel parsing, sensor fusion, resampling to 50 Hz |
| **WHY Bucket** | Reliability |
| **Delete Impact** | Cannot ingest raw sensor data |
| **Evidence** | PROJECT_DECISION |

### `preprocess_data.py` (855 L)

| Field | Value |
|---|---|
| **WHY** | Stage 3 engine: windowing, normalization, unit conversion |
| **WHY Bucket** | Reliability + Reproducibility |
| **Delete Impact** | Cannot create windowed .npy arrays from CSV |
| **Key Logic** | Windowing (ws=200, ov=0.5), z-score normalization, gravity removal toggle |
| **Evidence** | EMPIRICAL_CALIBRATION (REF_ABLATION_CSV) |

### `run_inference.py` (863 L)

| Field | Value |
|---|---|
| **WHY** | Stage 4 engine: batch/realtime inference, confidence extraction |
| **WHY Bucket** | Reliability |
| **Delete Impact** | Cannot generate predictions |
| **Evidence** | PROJECT_DECISION |

### `evaluate_predictions.py` (752 L)

| Field | Value |
|---|---|
| **WHY** | Stage 5 engine: confidence distribution, ECE, class balance analysis |
| **WHY Bucket** | Governance |
| **Delete Impact** | No prediction quality metrics; monitoring (Stage 6) has nothing to consume |
| **Evidence** | PAPER (REF_ECE) |

### `trigger_policy.py` (830 L)

| Field | Value |
|---|---|
| **WHY** | Stage 7 engine: 2-of-3 voting, cooldown logic, state persistence |
| **WHY Bucket** | Governance + Scalability/Cost |
| **Delete Impact** | No automated retraining decision; manual-only retrain |
| **Key Logic** | 2-of-3 voting (confidence + drift + temporal), cooldown timer, state file |
| **Evidence** | EMPIRICAL_CALIBRATION (REF_TRIGGER_EVAL) |

### `data_validator.py` (265 L)

| Field | Value |
|---|---|
| **WHY** | Stage 2 engine: schema validation, range checks, frequency verification |
| **WHY Bucket** | Reliability + Safety |
| **Delete Impact** | Invalid data passes silently to transformation |
| **Evidence** | REF_ML_TEST_SCORE (Level 1 data validation) |

### `calibration.py` (547 L)

| Field | Value |
|---|---|
| **WHY** | Stage 11 engine: temperature scaling, MC Dropout, ECE computation, reliability diagrams |
| **WHY Bucket** | Reliability + Safety |
| **Delete Impact** | No calibration; overconfident predictions mislead monitoring |
| **Key Logic** | Temperature optimization (NLL loss), MC forward passes (30), reliability diagram |
| **Evidence** | PAPER (REF_TEMP_SCALING, REF_MC_DROPOUT) |

### `model_rollback.py` (531 L)

| Field | Value |
|---|---|
| **WHY** | Stage 9 engine: version comparison, rollback to previous model, deployment management |
| **WHY Bucket** | Governance + Safety |
| **Delete Impact** | Cannot rollback bad models; stuck with degraded version |
| **Evidence** | OFFICIAL_DOC (REF_MLFLOW_REGISTRY) |

### `deployment_manager.py` (730 L)

| Field | Value |
|---|---|
| **WHY** | Manages model deployment lifecycle: promote, demote, A/B testing stubs |
| **WHY Bucket** | Governance |
| **Delete Impact** | No automated deployment; manual model file replacement |
| **Evidence** | REF_GOOGLE_MLOPS_CDCT |

### `active_learning_export.py` (672 L)

| Field | Value |
|---|---|
| **WHY** | Human-in-the-loop: exports most uncertain/diverse samples for annotation |
| **WHY Bucket** | Scalability/Cost |
| **Delete Impact** | No guided annotation; random labeling is 3–5× less efficient |
| **Key Logic** | Uncertainty sampling, diversity sampling (k-medoids), export to annotation format |
| **Evidence** | PAPER (active learning literature) |

### `robustness.py` (435 L)

| Field | Value |
|---|---|
| **WHY** | Tests model robustness: noise injection, missing channels, jitter, saturation |
| **WHY Bucket** | Reliability + Safety |
| **Delete Impact** | No perturbation testing; unknown failure modes |
| **Key Tests** | Gaussian noise, channel dropout, temporal jitter, sensor saturation |
| **Evidence** | REF_ML_TEST_SCORE (perturbation testing) |

### `ood_detection.py` (454 L)

| Field | Value |
|---|---|
| **WHY** | Out-of-distribution detection: energy-score method + ensemble detector |
| **WHY Bucket** | Safety/Compliance |
| **Delete Impact** | OOD inputs misclassified without warning |
| **Key Logic** | Energy score = -T·log(Σ exp(logit/T)); ensemble of energy + entropy + max-softmax |
| **Evidence** | PAPER (REF_ENERGY_OOD) |

### `model_retraining.py` (437 L)

| Field | Value |
|---|---|
| **WHY** | Stage 8 component: coordinates AdaBN/TENT/pseudo-label adaptation |
| **WHY Bucket** | Reliability |
| **Delete Impact** | Cannot retrain; model never adapts to new domains |
| **Evidence** | PAPER (REF_ADABN, REF_TENT) |

### `wasserstein_drift.py` (410 L)

| Field | Value |
|---|---|
| **WHY** | Stage 12: Wasserstein-distance drift detection with change-point detection |
| **WHY Bucket** | Observability |
| **Delete Impact** | No distributional drift detection; z-score (Stage 6) is sole drift monitor |
| **Evidence** | PAPER (REF_WASSERSTEIN) |

### `curriculum_pseudo_labeling.py` (452 L)

| Field | Value |
|---|---|
| **WHY** | Stage 13: curriculum-schedule pseudo-labeling with EWC + teacher-student |
| **WHY Bucket** | Reliability + Scalability |
| **Delete Impact** | No semi-supervised adaptation; fully labeled data required |
| **Evidence** | PAPER (REF_CURRICULUM, REF_PSEUDO_LABEL, REF_EWC) |

### `sensor_placement.py` (332 L)

| Field | Value |
|---|---|
| **WHY** | Stage 14: hand detection + axis mirroring for wrist placement robustness |
| **WHY Bucket** | Reliability + Safety |
| **Delete Impact** | ~3% accuracy loss when sensor worn on non-training wrist |
| **Evidence** | PAPER (REF_SENSOR_INFO_GAIN), EMPIRICAL_CALIBRATION |

---

## `src/domain_adaptation/`

### `adabn.py` (157 L)

| Field | Value |
|---|---|
| **WHY** | Adaptive Batch Normalization: updates BN running stats on target domain |
| **WHY Bucket** | Reliability |
| **Delete Impact** | No zero-label domain adaptation |
| **Evidence** | PAPER (REF_ADABN) |

### `tent.py` (259 L)

| Field | Value |
|---|---|
| **WHY** | Test-Time Entropy minimization: adapts BN affine params at inference |
| **WHY Bucket** | Reliability |
| **Delete Impact** | No test-time adaptation for distribution shifts |
| **Key Logic** | Entropy threshold = 0.85 → skip OOD samples (⚠️ GAP-TENT-01) |
| **Evidence** | PAPER (REF_TENT) |

---

## `src/utils/`

### `temporal_metrics.py` (100 L)

| Field | Value |
|---|---|
| **WHY** | Computes transition rate (Layer 2 of monitoring) |
| **WHY Bucket** | Observability |
| **Delete Impact** | Stage 6 monitoring loses temporal analysis layer |
| **Evidence** | PROJECT_DECISION |

---

## `src/api/`

### `app.py` (892 L)

| Field | Value |
|---|---|
| **WHY** | FastAPI serving: `/predict`, `/health`, `/ready`, `/metrics` endpoints |
| **WHY Bucket** | Scalability/Cost + Observability |
| **Delete Impact** | No REST API; batch-only inference |
| **Key Endpoints** | `POST /predict`, `GET /health`, `GET /ready`, `GET /metrics` |
| **Evidence** | OFFICIAL_DOC (REF_FASTAPI), PROJECT_DECISION |

---

## `src/components/` (14 files, one per stage)

Each component file follows the same pattern:
1. Receives its `*Config` dataclass
2. Calls the corresponding engine file
3. Logs outputs as MLflow artifacts
4. Returns artifacts for next stage

| File | Stage | Lines | Engine |
|---|---|---|---|
| `data_ingestion.py` | 1 | 623 | `sensor_data_pipeline.py` |
| `data_validation.py` | 2 | 63 | `data_validator.py` |
| `data_transformation.py` | 3 | 133 | `preprocess_data.py` |
| `model_inference.py` | 4 | 128 | `run_inference.py` |
| `model_evaluation.py` | 5 | 67 | `evaluate_predictions.py` |
| `post_inference_monitoring.py` | 6 | 127 | `temporal_metrics.py` |
| `trigger_evaluation.py` | 7 | 114 | `trigger_policy.py` |
| `model_retraining.py` | 8 | 437 | `adabn.py`, `tent.py` |
| `model_registration.py` | 9 | 132 | `model_rollback.py` |
| `baseline_update.py` | 10 | 139 | `build_normalized_baseline.py` |
| `calibration_uncertainty.py` | 11 | 138 | `calibration.py` |
| `wasserstein_drift.py` | 12 | — | `wasserstein_drift.py` |
| `curriculum_pseudo_labeling.py` | 13 | — | `curriculum_pseudo_labeling.py` |
| `sensor_placement.py` | 14 | — | `sensor_placement.py` |

**WHY this pattern?** Component/engine separation follows the "thin controller / fat service" principle. Components are testable orchestrators; engines contain domain logic.

---

## `config/`

### `pipeline_config.yaml` (83 L)

| Field | Value |
|---|---|
| **WHY** | Runtime toggle file: preprocessing flags with inline rationale comments |
| **WHY Bucket** | Reproducibility + Maintainability |
| **Delete Impact** | Pipeline uses defaults from `config_entity.py` (not catastrophic, but loses toggles) |
| **Evidence** | PROJECT_DECISION |

### `monitoring_thresholds.yaml`

| Field | Value |
|---|---|
| **WHY** | Audit cross-reference for thresholds — NOT runtime truth (that's `config_entity.py`) |
| **WHY Bucket** | Governance |
| **Delete Impact** | Audit reference lost; runtime unaffected |
| **Evidence** | PROJECT_DECISION |

### `prometheus.yml`

| Field | Value |
|---|---|
| **WHY** | Prometheus scrape configuration: 6 jobs, intervals, targets |
| **WHY Bucket** | Observability |
| **Delete Impact** | No metrics collection; Prometheus has no targets |
| **Evidence** | OFFICIAL_DOC (REF_PROM_HISTOGRAMS) |

### `alertmanager.yml` (111 L)

| Field | Value |
|---|---|
| **WHY** | Alert routing, inhibit rules (critical suppresses warning for same metric) |
| **WHY Bucket** | Observability |
| **Delete Impact** | Alerts fire but not routed; no notification |
| **Evidence** | OFFICIAL_DOC (REF_PROM_ALERTING) |

### `alerts/har_alerts.yml`

| Field | Value |
|---|---|
| **WHY** | 8 custom alert rules across 4 groups (model, data, system, pipeline) |
| **WHY Bucket** | Observability |
| **Delete Impact** | No automated alerting; manual dashboard watching required |
| **Evidence** | PROJECT_DECISION |

---

## Root Files

### `run_pipeline.py` (545 L)

| Field | Value |
|---|---|
| **WHY** | CLI entry point: `python run_pipeline.py [--stages ...] [--retrain] [--advanced]` |
| **WHY Bucket** | Maintainability |
| **Delete Impact** | No CLI; must import and call `ProductionPipeline` manually |
| **Evidence** | PROJECT_DECISION |

### `pyproject.toml`

| Field | Value |
|---|---|
| **WHY** | Project metadata: version (2.1.0), 13 core deps, 3 optional dep groups (dev, monitoring, gpu) |
| **WHY Bucket** | Reproducibility |
| **Delete Impact** | `pip install -e .` fails; dep resolution broken |
| **Evidence** | PROJECT_DECISION |

### `docker-compose.yml` (223 L)

| Field | Value |
|---|---|
| **WHY** | Orchestrates 7 services (inference, training, mlflow, prometheus, alertmanager, grafana, node-exporter) |
| **WHY Bucket** | Reproducibility + Reliability |
| **Delete Impact** | Must start each service manually |
| **Evidence** | REF_DOCKER_BEST_PRACTICES |

### `pytest.ini`

| Field | Value |
|---|---|
| **WHY** | pytest configuration: markers, default args, test paths |
| **WHY Bucket** | Maintainability |
| **Delete Impact** | Markers not recognized; `pytest -k "not slow"` still works but `--strict-markers` fails |
| **Evidence** | REF_PYTEST |

---

## Reports

### `reports/ABLATION_WINDOWING.csv`

| Field | Value |
|---|---|
| **WHY** | Empirical evidence: 6 windowing configs tested (ws×overlap); ws=200/ov=50% is best |
| **WHY Bucket** | Reproducibility |
| **Delete Impact** | Cannot defend window_size=200 choice |
| **Evidence** | EMPIRICAL_CALIBRATION |

### `reports/THRESHOLD_CALIBRATION.csv`

| Field | Value |
|---|---|
| **WHY** | Empirical evidence: 52 threshold combos across 5 metrics |
| **WHY Bucket** | Reliability |
| **Delete Impact** | Cannot defend monitoring thresholds |
| **Evidence** | EMPIRICAL_CALIBRATION |

### `reports/TRIGGER_POLICY_EVAL.md`

| Field | Value |
|---|---|
| **WHY** | Empirical evidence: 500 simulated sessions, 5 trigger policy variants |
| **WHY Bucket** | Governance |
| **Delete Impact** | Cannot defend 2-of-3 policy + 6h cooldown |
| **Evidence** | EMPIRICAL_CALIBRATION |

### `reports/EVIDENCE_PACK_INDEX.md`

| Field | Value |
|---|---|
| **WHY** | Master index: 23 claims mapped to evidence (9 paper, 9 empirical, 1 sensor, 4 project) |
| **WHY Bucket** | Governance |
| **Delete Impact** | Lose traceability of all evidence |
| **Evidence** | ALL |

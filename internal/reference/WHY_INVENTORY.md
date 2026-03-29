# WHY INVENTORY — HAR MLOps Pipeline

> Master index of everything that needs a WHY justification.
> Status: ✅ = WHY CARD written | ⚠️ = partial | ❌ = missing evidence

---

## A. Pipeline Stages (14, as defined in `src/pipeline/production_pipeline.py:57–71`)

| # | Stage Name | Component File | Engine File | Config Dataclass | Status |
|---|---|---|---|---|---|
| 1 | `ingestion` | `src/components/data_ingestion.py` (623 L) | `src/sensor_data_pipeline.py` (1192 L) | `DataIngestionConfig` (L80) | ✅ |
| 2 | `validation` | `src/components/data_validation.py` (63 L) | `src/data_validator.py` (265 L) | `DataValidationConfig` (L97) | ✅ |
| 3 | `transformation` | `src/components/data_transformation.py` (133 L) | `src/preprocess_data.py` (855 L) | `DataTransformationConfig` (L113) | ✅ |
| 4 | `inference` | `src/components/model_inference.py` (128 L) | `src/run_inference.py` (863 L) | `ModelInferenceConfig` (L137) | ✅ |
| 5 | `evaluation` | `src/components/model_evaluation.py` (67 L) | `src/evaluate_predictions.py` (752 L) | `ModelEvaluationConfig` (L154) | ✅ |
| 6 | `monitoring` | `src/components/post_inference_monitoring.py` (127 L) | `src/utils/temporal_metrics.py` (100 L) | `PostInferenceMonitoringConfig` (L169) | ✅ |
| 7 | `trigger` | `src/components/trigger_evaluation.py` (114 L) | `src/trigger_policy.py` (830 L) | `TriggerEvaluationConfig` (L207) | ✅ |
| 8 | `retraining` | `src/components/model_retraining.py` (437 L) | `src/domain_adaptation/adabn.py` (157 L), `tent.py` (259 L) | `ModelRetrainingConfig` (L228) | ✅ |
| 9 | `registration` | `src/components/model_registration.py` (132 L) | `src/model_rollback.py` (531 L) | `ModelRegistrationConfig` (L261) | ✅ |
| 10 | `baseline_update` | `src/components/baseline_update.py` (139 L) | `scripts/build_normalized_baseline.py` | `BaselineUpdateConfig` (L285) | ✅ |
| 11 | `calibration` | `src/components/calibration_uncertainty.py` (138 L) | `src/calibration.py` (547 L) | `CalibrationUncertaintyConfig` (L306) | ✅ |
| 12 | `wasserstein_drift` | `src/components/wasserstein_drift.py` | `src/wasserstein_drift.py` (410 L) | `WassersteinDriftConfig` (L338) | ✅ |
| 13 | `curriculum_pseudo_labeling` | `src/components/curriculum_pseudo_labeling.py` | `src/curriculum_pseudo_labeling.py` (452 L) | `CurriculumPseudoLabelingConfig` (L364) | ✅ |
| 14 | `sensor_placement` | `src/components/sensor_placement.py` | `src/sensor_placement.py` (332 L) | `SensorPlacementConfig` (L398) | ✅ |

**Stage groups** (`production_pipeline.py:73–78`):
- **Default (1–7):** `python run_pipeline.py`
- **Retrain (8–10):** `python run_pipeline.py --retrain`
- **Advanced (11–14):** `python run_pipeline.py --advanced`

---

## B. Technologies

| Technology | Primary File(s) | WHY Bucket | Status |
|---|---|---|---|
| **MLOps (paradigm)** | whole repo | Reliability + Governance | ✅ |
| **DVC** | `.dvc/config`, `data/*.dvc` | Reproducibility | ✅ |
| **MLflow** | `src/mlflow_tracking.py` (643 L), `config/mlflow_config.yaml` | Reproducibility + Governance | ✅ |
| **Docker** | `docker/Dockerfile.inference` (65 L), `docker/Dockerfile.training` (52 L), `docker-compose.yml` (223 L) | Reproducibility + Reliability | ✅ |
| **CI/CD (GitHub Actions)** | `.github/workflows/ci-cd.yml` (350 L) | Maintainability + Reliability | ✅ |
| **FastAPI** | `src/api/app.py` (892 L) | Scalability/Cost | ✅ |
| **Prometheus** | `config/prometheus.yml`, `config/alerts/har_alerts.yml` | Observability | ✅ |
| **Alertmanager** | `config/alertmanager.yml` (111 L) | Observability | ✅ |
| **Grafana** | `config/grafana/` | Observability | ✅ |
| **TensorFlow/Keras** | `src/train.py` (1345 L) | Reliability (model) | ✅ |
| **pytest** | `tests/` (25 files), `pytest.ini`, `pyproject.toml` | Maintainability | ✅ |
| **Python 3.11** | `pyproject.toml`, Dockerfiles | Reproducibility | ✅ |

---

## C. Critical Files (non-stage, non-technology)

| File | Purpose | WHY Needed | Status |
|---|---|---|---|
| `run_pipeline.py` (545 L) | CLI entry point | Single command to run any/all 14 stages | ✅ |
| `src/pipeline/production_pipeline.py` (967 L) | Orchestrator | Stage ordering, artifact passing, MLflow lifecycle | ✅ |
| `src/entity/config_entity.py` (409 L) | Config dataclasses | Single source of truth for all thresholds | ✅ |
| `src/config.py` (82 L) | Global constants | WINDOW_SIZE, OVERLAP, NUM_SENSORS, paths | ✅ |
| `config/pipeline_config.yaml` (83 L) | Pipeline toggles | Preprocessing flags with inline rationale | ✅ |
| `config/monitoring_thresholds.yaml` | Threshold audit reference | NOT runtime truth — audit cross-check | ✅ |
| `src/train.py` (1345 L) | Training script | HARModelBuilder, HARTrainer, DomainAdaptationTrainer | ✅ |
| `src/active_learning_export.py` (672 L) | Human-in-the-loop | Uncertainty/diversity sampling for annotation | ✅ |
| `src/robustness.py` (435 L) | Perturbation testing | Noise/missing/jitter/saturation evaluation | ✅ |
| `src/ood_detection.py` (454 L) | Out-of-distribution | Energy-score OOD + ensemble detector | ✅ |

---

## D. Empirical Evidence Artifacts

| Artifact | Path | What Was Tested | Evidence Type |
|---|---|---|---|
| Windowing ablation | `reports/ABLATION_WINDOWING.csv` | 6 configs (ws=128/200/256 × overlap=0.25/0.50) | EMPIRICAL_CALIBRATION |
| Threshold calibration | `reports/THRESHOLD_CALIBRATION.csv` | 52 threshold combos across 5 metrics | EMPIRICAL_CALIBRATION |
| Trigger policy eval | `reports/TRIGGER_POLICY_EVAL.csv` + `.md` | 500 simulated sessions, 5 policy variants | EMPIRICAL_CALIBRATION |
| Evidence pack index | `reports/EVIDENCE_PACK_INDEX.md` | 23 claims, 9 paper + 9 empirical + 1 sensor + 4 project | ALL |
| Pipeline factsheet | `reports/PIPELINE_FACTSHEET.md` (359 L) | All 14 stages documented | PROJECT_DECISION |
| Windowing justification | `reports/WINDOWING_JUSTIFICATION.md` | Window size rationale | PAPER + EMPIRICAL |

---

## E. Test Coverage Map

| Stage | Test File(s) | Marker |
|---|---|---|
| 2 (validation) | `test_data_validation.py`, `test_validation_gate.py` | unit |
| 3 (transformation) | `test_preprocessing.py`, `test_robustness.py` | unit, robustness |
| 6 (monitoring) | `test_drift_detection.py`, `test_temporal_metrics.py`, `test_baseline_age_gauge.py` | unit |
| 7 (trigger) | `test_trigger_policy.py` | unit |
| 8 (retraining) | `test_retraining.py`, `test_adabn.py` | slow |
| 9 (registration) | `test_model_registration_gate.py`, `test_model_rollback.py` | unit |
| 10 (baseline) | `test_baseline_update.py` | unit |
| 11 (calibration) | `test_calibration.py` | calibration |
| 12 (wasserstein) | `test_wasserstein_drift.py` | unit |
| 13 (curriculum PL) | `test_curriculum_pseudo_labeling.py` | slow |
| 14 (sensor placement) | `test_sensor_placement.py` | unit |
| Cross-cutting | `test_threshold_consistency.py`, `test_prometheus_metrics.py`, `test_pipeline_integration.py` | unit, integration |
| **MISSING tests** | **Stage 1 (ingestion), Stage 4 (inference), Stage 5 (evaluation)** | **P0 gap** |

---

## F. Known Evidence Gaps (P0)

| Gap ID | What | Why It Matters | Remediation |
|---|---|---|---|
| GAP-TENT-01 | TENT OOD entropy threshold = 0.85 — no calibration artifact | Could skip adaptation on valid data or adapt on OOD | Run entropy sweep on known OOD/ID split |
| GAP-EWC-01 | EWC λ=1000 — no ablation | Could over/under-regularise | Lambda sweep: {100, 500, 1000, 5000, 10000} |
| GAP-PSEUDO-01 | Pseudo-label error rate at τ=0.70 — no labeled validation | Could inject noisy labels | Label subset + measure error rate vs τ |
| GAP-ADABN-01 | AdaBN n_batches=10 — paper default, no ablation | Could over/under-smooth BN stats | n_batches sweep: {5, 10, 20, 50} |
| GAP-LOSO-01 | No Leave-One-Subject-Out CV documented | Cross-subject generalisation unproven | Run LOSO on labeled data, report per-subject F1 |
| GAP-TEST-01 | No tests for Stage 1, 4, 5 | Component regressions undetected | Add pytest fixtures for ingestion, inference, evaluation |
| GAP-DOCKER-01 | Single-stage Dockerfiles | Larger image, not industry best practice | Convert to multi-stage builds |
| GAP-AUTH-01 | No API authentication | Security for production deployment | Add JWT/API-key middleware |
| GAP-AB-01 | No A/B testing infrastructure | Cannot compare models on live traffic | Implement traffic-split proxy |

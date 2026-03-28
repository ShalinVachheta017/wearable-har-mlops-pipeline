# EVIDENCE LEDGER — Artifact Status Tracker

> Tracks every evidence artifact: what exists, what's missing, what needs updating.
> Status: ✅ EXISTS | ⚠️ NEEDS_UPDATE | ❌ MISSING

---

## Empirical Calibration Artifacts

| ID | Artifact | Path | Status | Notes |
|---|---|---|---|---|
| EV-001 | Windowing ablation data | `reports/ABLATION_WINDOWING.csv` | ✅ EXISTS | 6 configs; best = ws=200/ov=50% |
| EV-002 | Threshold calibration data | `reports/THRESHOLD_CALIBRATION.csv` | ✅ EXISTS | 52 threshold combos, 5 metrics |
| EV-003 | Trigger policy evaluation | `reports/TRIGGER_POLICY_EVAL.md` | ✅ EXISTS | 500 simulated sessions, 5 variants; best = 2-of-3 + 6h |
| EV-004 | Trigger policy eval CSV | `reports/TRIGGER_POLICY_EVAL.csv` | ✅ EXISTS | Raw data for REF_TRIGGER_EVAL |
| EV-005 | Evidence pack index | `reports/EVIDENCE_PACK_INDEX.md` | ✅ EXISTS | 23 claims; 0 unsupported |
| EV-006 | Windowing justification | `reports/WINDOWING_JUSTIFICATION.md` | ✅ EXISTS | Narrative + paper citations |
| EV-007 | Pipeline factsheet | `reports/PIPELINE_FACTSHEET.md` | ✅ EXISTS | 359 lines; all 14 stages |
| EV-008 | Scaler config (training) | `data/prepared/config.json` | ✅ EXISTS | z-score scaler parameters |
| EV-009 | Pretrained model | `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` | ✅ EXISTS | 1D-CNN-BiLSTM v1 |
| EV-010 | Model info | `models/pretrained/model_info.json` | ✅ EXISTS | Architecture metadata |

---

## Paper-Backed Method Justifications

| ID | Method | Paper | REF ID | Status | Gap? |
|---|---|---|---|---|---|
| EV-101 | 1D-CNN-BiLSTM for HAR | Ordóñez & Roggen (2016) | REF_CNN_BILSTM_HAR | ✅ EXISTS | — |
| EV-102 | AdaBN domain adaptation | Li et al. (2018) | REF_ADABN | ✅ EXISTS | ⚠️ GAP-ADABN-01: n_batches=10 not ablated |
| EV-103 | TENT test-time adaptation | Wang et al. (2021) | REF_TENT | ✅ EXISTS | ⚠️ GAP-TENT-01: entropy threshold=0.85 not calibrated |
| EV-104 | EWC continual learning | Kirkpatrick et al. (2017) | REF_EWC | ✅ EXISTS | ⚠️ GAP-EWC-01: λ=1000 not ablated |
| EV-105 | Temperature scaling | Guo et al. (2017) | REF_TEMP_SCALING | ✅ EXISTS | — |
| EV-106 | MC Dropout uncertainty | Gal & Ghahramani (2016) | REF_MC_DROPOUT | ✅ EXISTS | — |
| EV-107 | ECE calibration metric | Naeini et al. (2015) | REF_ECE | ✅ EXISTS | — |
| EV-108 | Energy OOD detection | Liu et al. (2020) | REF_ENERGY_OOD | ✅ EXISTS | — |
| EV-109 | Wasserstein drift | Ramdas et al. (2017) | REF_WASSERSTEIN | ✅ EXISTS | — |
| EV-110 | Curriculum learning | Bengio et al. (2009) | REF_CURRICULUM | ✅ EXISTS | — |
| EV-111 | Pseudo-labels | Lee (2013) | REF_PSEUDO_LABEL | ✅ EXISTS | ⚠️ GAP-PSEUDO-01: error rate at τ=0.80 not measured |
| EV-112 | Sensor placement/info gain | Bulling et al. (2014) | REF_SENSOR_INFO_GAIN | ✅ EXISTS | — |
| EV-113 | Windowing ablation paper | Banos et al. (2014) | REF_ABLATION_WINDOW | ✅ EXISTS | — |
| EV-114 | SelfHAR semi-supervised | Tang et al. (2021) | REF_SELFHAR | ✅ EXISTS | — |

---

## Official Documentation References

| ID | Tool/Framework | REF ID | Status | Notes |
|---|---|---|---|---|
| EV-201 | DVC Pipelines | REF_DVC_PIPELINES | ✅ EXISTS | Used for data versioning |
| EV-202 | MLflow Tracking | REF_MLFLOW_TRACKING | ✅ EXISTS | Experiment tracking |
| EV-203 | MLflow Model Registry | REF_MLFLOW_REGISTRY | ✅ EXISTS | Model versioning |
| EV-204 | Docker Best Practices | REF_DOCKER_BEST_PRACTICES | ✅ EXISTS | Container standards |
| EV-205 | Prometheus Histograms | REF_PROM_HISTOGRAMS | ✅ EXISTS | Metrics patterns |
| EV-206 | FastAPI | REF_FASTAPI | ✅ EXISTS | API framework |
| EV-207 | GitHub Actions | REF_GITHUB_ACTIONS | ✅ EXISTS | CI/CD platform |
| EV-208 | Grafana Provisioning | REF_GRAFANA_PROVISIONING | ✅ EXISTS | Dashboard config |

---

## MLOps Framework References

| ID | Framework | REF ID | Status | Notes |
|---|---|---|---|---|
| EV-301 | ML Test Score | REF_ML_TEST_SCORE | ✅ EXISTS | Pipeline maturity rubric |
| EV-302 | Google MLOps CD/CT | REF_GOOGLE_MLOPS_CDCT | ✅ EXISTS | Level 2 target |
| EV-303 | CD4ML | REF_CD4ML | ✅ EXISTS | Continuous delivery pattern |
| EV-304 | Hidden Tech Debt | REF_HIDDEN_TECH_DEBT | ✅ EXISTS | Motivation for MLOps |

---

## Test Evidence

| ID | Test File | Stage Coverage | Status | Gap? |
|---|---|---|---|---|
| EV-401 | `tests/test_data_validation.py` | Stage 2 | ✅ EXISTS | — |
| EV-402 | `tests/test_validation_gate.py` | Stage 2 | ✅ EXISTS | — |
| EV-403 | `tests/test_preprocessing.py` | Stage 3 | ✅ EXISTS | — |
| EV-404 | `tests/test_robustness.py` | Stage 3 (robustness) | ✅ EXISTS | — |
| EV-405 | `tests/test_drift_detection.py` | Stage 6 | ✅ EXISTS | — |
| EV-406 | `tests/test_temporal_metrics.py` | Stage 6 | ✅ EXISTS | — |
| EV-407 | `tests/test_baseline_age_gauge.py` | Stage 6 | ✅ EXISTS | — |
| EV-408 | `tests/test_trigger_policy.py` | Stage 7 | ✅ EXISTS | — |
| EV-409 | `tests/test_retraining.py` | Stage 8 | ✅ EXISTS | — |
| EV-410 | `tests/test_adabn.py` | Stage 8 (AdaBN) | ✅ EXISTS | — |
| EV-411 | `tests/test_model_registration_gate.py` | Stage 9 | ✅ EXISTS | — |
| EV-412 | `tests/test_model_rollback.py` | Stage 9 | ✅ EXISTS | — |
| EV-413 | `tests/test_baseline_update.py` | Stage 10 | ✅ EXISTS | — |
| EV-414 | `tests/test_calibration.py` | Stage 11 | ✅ EXISTS | — |
| EV-415 | `tests/test_wasserstein_drift.py` | Stage 12 | ✅ EXISTS | — |
| EV-416 | `tests/test_curriculum_pseudo_labeling.py` | Stage 13 | ✅ EXISTS | — |
| EV-417 | `tests/test_sensor_placement.py` | Stage 14 | ✅ EXISTS | — |
| EV-418 | `tests/test_threshold_consistency.py` | Cross-cutting | ✅ EXISTS | — |
| EV-419 | `tests/test_prometheus_metrics.py` | Cross-cutting | ✅ EXISTS | — |
| EV-420 | `tests/test_pipeline_integration.py` | Integration | ✅ EXISTS | — |
| EV-421 | Stage 1 tests | Stage 1 (ingestion) | ❌ MISSING | GAP-TEST-01 |
| EV-422 | Stage 4 tests | Stage 4 (inference) | ❌ MISSING | GAP-TEST-01 |
| EV-423 | Stage 5 tests | Stage 5 (evaluation) | ❌ MISSING | GAP-TEST-01 |

---

## Infrastructure Evidence

| ID | Artifact | Path | Status | Notes |
|---|---|---|---|---|
| EV-501 | Docker inference image | `docker/Dockerfile.inference` (65 L) | ⚠️ NEEDS_UPDATE | GAP-DOCKER-01: single-stage, should be multi-stage |
| EV-502 | Docker training image | `docker/Dockerfile.training` (52 L) | ⚠️ NEEDS_UPDATE | GAP-DOCKER-01: single-stage |
| EV-503 | Docker Compose | `docker-compose.yml` (223 L) | ✅ EXISTS | 7 services |
| EV-504 | CI/CD workflow | `.github/workflows/ci-cd.yml` (350 L) | ✅ EXISTS | 6 jobs |
| EV-505 | Prometheus config | `config/prometheus.yml` | ✅ EXISTS | 6 scrape jobs |
| EV-506 | Alert rules | `config/alerts/har_alerts.yml` | ✅ EXISTS | 8 rules, 4 groups |
| EV-507 | Alertmanager config | `config/alertmanager.yml` (111 L) | ✅ EXISTS | Inhibit rules |
| EV-508 | Pipeline config | `config/pipeline_config.yaml` (83 L) | ✅ EXISTS | Runtime toggles |
| EV-509 | DVC config | `.dvc/config` | ✅ EXISTS | Local remote configured |

---

## Known Gaps Summary

| Gap ID | Category | Description | Priority | Remediation |
|---|---|---|---|---|
| GAP-TEST-01 | Testing | Missing tests for Stages 1, 4, 5 | P0 | Add pytest fixtures for ingestion, inference, evaluation |
| GAP-ADABN-01 | Ablation | AdaBN n_batches=10 — paper default, no ablation | P1 | Sweep: {5, 10, 20, 50} |
| GAP-TENT-01 | Calibration | TENT entropy threshold=0.85 — no calibration artifact | P1 | Entropy sweep on known OOD/ID split |
| GAP-EWC-01 | Ablation | EWC λ=1000 — paper default, no ablation | P1 | Sweep: {100, 500, 1000, 5000, 10000} |
| GAP-PSEUDO-01 | Validation | Pseudo-label error rate at τ=0.80 — not measured | P1 | Label subset + measure error rate vs τ |
| GAP-DOCKER-01 | Infrastructure | Single-stage Dockerfiles | P2 | Convert to multi-stage builds |
| GAP-AUTH-01 | Security | No API authentication | P2 | Add JWT/API-key middleware |
| GAP-LOSO-01 | Evaluation | No Leave-One-Subject-Out CV | P2 | Run LOSO, report per-subject F1 |
| GAP-AB-01 | Infrastructure | No A/B testing infrastructure | P3 | Implement traffic-split proxy |

---

## Evidence Completeness Score

| Category | Total | Exists | Missing | Needs Update | Score |
|---|---|---|---|---|---|
| Empirical Calibration | 10 | 10 | 0 | 0 | 100% |
| Paper References | 14 | 14 | 0 | 0 (4 with gaps) | 100% (71% w/o gaps) |
| Official Docs | 8 | 8 | 0 | 0 | 100% |
| MLOps Frameworks | 4 | 4 | 0 | 0 | 100% |
| Tests | 23 | 20 | 3 | 0 | 87% |
| Infrastructure | 9 | 7 | 0 | 2 | 78% |
| **TOTAL** | **68** | **63** | **3** | **2** | **93%** |

> **Action items for 100%:** Fix GAP-TEST-01 (3 missing test files), GAP-DOCKER-01 (2 Dockerfiles).
> **Action items for full confidence:** Run ablations for GAP-ADABN-01, GAP-EWC-01, GAP-TENT-01, GAP-PSEUDO-01.

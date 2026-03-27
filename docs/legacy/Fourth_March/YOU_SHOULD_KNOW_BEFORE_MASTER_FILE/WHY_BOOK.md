# WHY BOOK — Master Defense Reference

> The master "WHY" document combining all perspectives.
> Use this as your primary defense preparation reference.
> Rule: papers justify METHODS; your data justifies NUMBERS.

---

## How to Use This Book

1. **Before defense:** Read Section 1 (Thesis-Level WHYs) end-to-end.
2. **For a specific question:** Search by keyword → jump to the WHY CARD.
3. **For a specific stage:** See `WHY_BY_STAGE.md`.
4. **For a specific technology:** See `WHY_BY_TECH.md`.
5. **For a specific file:** See `WHY_BY_FILE.md`.
6. **For evidence:** See `EVIDENCE_LEDGER.md`.
7. **For Q&A practice:** See `DEFENSE_QA.md`.

---

## 1. Thesis-Level WHY CARDs

### WHY CARD: Why MLOps for HAR?

| Field | Value |
|---|---|
| **Decision** | Apply MLOps methodology to a HAR (Human Activity Recognition) pipeline |
| **WHY Bucket** | Reliability + Governance + Reproducibility |
| **Evidence** | REF_GOOGLE_MLOPS_CDCT, REF_ML_TEST_SCORE, REF_HIDDEN_TECH_DEBT, REF_CD4ML |

**Business Lens**
- HAR models degrade in production due to sensor drift, user variability, and environmental changes.
- Without MLOps, each degradation requires manual investigation → days of downtime.
- MLOps automates detection → triggering → adaptation → deployment: minutes, not days.
- Hidden tech debt (REF_HIDDEN_TECH_DEBT): ML systems without MLOps accrue 10× maintenance cost.

**Thesis Lens**
- The contribution is NOT the model — it's the infrastructure that keeps the model reliable.
- Demonstrates Google MLOps Level 2: automated pipeline with CT (continuous training) and CD (continuous deployment).
- ML Test Score (REF_ML_TEST_SCORE) provides measurable maturity rubric.
- Reproducibility: any experiment re-runnable from `{git_commit + dvc_version + config}`.

**Alternatives Considered**
1. ~~Pure research (train once, publish)~~ — Ignores production reality; model decays.
2. ~~MLOps on image classification~~ — Well-studied; HAR has unique challenges (sensor placement, temporal patterns, labelless monitoring).
3. ~~MLOps on NLP~~ — Labels cheap (crowdsourcing); HAR labels are expensive (wearable sessions).

---

### WHY CARD: Why 14 Stages?

| Field | Value |
|---|---|
| **Decision** | 14-stage modular pipeline (not monolithic) |
| **WHY Bucket** | Maintainability + Reliability |
| **Evidence** | REF_CD4ML, REF_GOOGLE_MLOPS_CDCT |

**Business Lens**
- Modular: update monitoring without touching training code.
- Testable: each stage has independent tests.
- Debuggable: failures localized to a specific stage.
- Configurable: run `--stages ingestion,validation` for quick checks.

**Thesis Lens**
- Each stage maps to a specific MLOps capability (data validation, monitoring, trigger, etc.).
- 3-phase grouping (Default 1–7, Retrain 8–10, Advanced 11–14) demonstrates incremental MLOps adoption.
- Component/engine separation enables unit testing of domain logic independent of orchestration.

**The 14 Stages**

| Phase | # | Stage | Primary Concern |
|---|---|---|---|
| Default | 1 | Ingestion | Data acquisition |
| Default | 2 | Validation | Data quality |
| Default | 3 | Transformation | Feature engineering |
| Default | 4 | Inference | Value delivery |
| Default | 5 | Evaluation | Quality measurement |
| Default | 6 | Monitoring | Observability |
| Default | 7 | Trigger | Decision intelligence |
| Retrain | 8 | Retraining | Model adaptation |
| Retrain | 9 | Registration | Model governance |
| Retrain | 10 | Baseline Update | Feedback loop |
| Advanced | 11 | Calibration | Uncertainty quantification |
| Advanced | 12 | Wasserstein Drift | Distribution analysis |
| Advanced | 13 | Curriculum PL | Semi-supervised learning |
| Advanced | 14 | Sensor Placement | Deployment robustness |

---

### WHY CARD: Why This Model Architecture?

| Field | Value |
|---|---|
| **Decision** | 1D-CNN-BiLSTM (not Transformer, not RF, not LSTM-only) |
| **WHY Bucket** | Reliability |
| **Evidence** | REF_CNN_BILSTM_HAR |
| **Where** | `src/train.py:90–200` |

**Business Lens**
- 1D-CNN captures local spatial patterns in accelerometer/gyroscope channels.
- BiLSTM captures temporal dependencies across the 4-second window.
- ~499K parameters → runs on CPU; no GPU required for inference.
- BatchNorm layers enable AdaBN domain adaptation (zero-label).

**Thesis Lens**
- CNN-BiLSTM is the state-of-the-art baseline for IMU-based HAR (REF_CNN_BILSTM_HAR).
- The contribution is NOT the architecture — it's the MLOps infrastructure around it.
- Architecture supports domain adaptation (AdaBN/TENT) without modification.

**Alternatives Considered**
1. ~~Transformer~~ — More parameters, not proven better for 6-channel IMU.
2. ~~LSTM only~~ — Misses local spatial patterns.
3. ~~Random Forest~~ — Cannot process raw time-series windows.
4. ~~1D-CNN only~~ — Misses temporal dependencies.

---

### WHY CARD: Why Labelless Monitoring?

| Field | Value |
|---|---|
| **Decision** | 3-layer monitoring without ground-truth labels |
| **WHY Bucket** | Observability + Reliability |
| **Evidence** | EMPIRICAL_CALIBRATION (REF_THRESHOLD_CSV) |
| **Where** | `src/components/post_inference_monitoring.py`, `config_entity.py:169–197` |

**Business Lens**
- Production HAR data has NO labels — users don't annotate their activities.
- Must detect degradation from prediction distributions alone.
- 3 independent signals reduce false alarms vs single-metric monitoring.

**Thesis Lens**
- Core contribution: novel 3-layer monitoring for labelless HAR deployment.
- Layer 1 (confidence): mean confidence, uncertain %, per-window cutoff.
- Layer 2 (temporal): transition rate catches oscillating predictions.
- Layer 3 (drift): z-score distribution shift per sensor channel.
- All 52 threshold combinations empirically tested (REF_THRESHOLD_CSV).

**Alternatives Considered**
1. ~~Wait for user complaints~~ — Reactive; degradation detected too late.
2. ~~Single confidence threshold~~ — Misses drift that doesn't affect confidence.
3. ~~Labeled monitoring~~ — Requires annotation pipeline; impractical at scale.
4. ~~Evidently AI~~ — Heavy dependency; 127-line custom solution is lighter.

---

### WHY CARD: Why Domain Adaptation (Not Just Retrain)?

| Field | Value |
|---|---|
| **Decision** | AdaBN + TENT + Pseudo-Labeling (not full supervised retrain) |
| **WHY Bucket** | Reliability + Scalability/Cost |
| **Evidence** | REF_ADABN, REF_TENT, REF_CURRICULUM, REF_EWC |

**Business Lens**
- Labels cost ~$10/hour for wearable session annotation.
- AdaBN: zero labels, updates BN stats in minutes.
- TENT: zero labels, minimizes entropy at test time.
- Pseudo-labeling: uses model's own predictions as labels (with curriculum schedule).
- Full retrain: requires labeled data + GPU hours.

**Thesis Lens**
- Demonstrates progressive adaptation: AdaBN (zero-label) → TENT (zero-label, deeper) → Pseudo-labeling (self-supervised) → Full retrain (labeled).
- EWC prevents catastrophic forgetting during adaptation.
- Teacher-student EMA (SelfHAR-inspired) stabilizes pseudo-labels.

---

## 2. Architecture-Level WHY CARDs

### WHY CARD: Why Config Dataclasses?

| Field | Value |
|---|---|
| **Decision** | One `@dataclass` per stage in `config_entity.py` (409 L) |
| **WHY Bucket** | Reproducibility + Maintainability |
| **Where** | `src/entity/config_entity.py` |

**Business Lens**
- Single source of truth: change a threshold in ONE place.
- Type-safe: Python dataclass validates types at instantiation.
- Documented: inline comments explain each default.
- Testable: `test_threshold_consistency.py` verifies cross-file alignment.

**Thesis Lens**
- Reproducibility: config + code + data = reproducible experiment.
- Config-driven architecture is a core MLOps pattern (REF_GOOGLE_MLOPS_CDCT).

---

### WHY CARD: Why Component/Engine Separation?

| Field | Value |
|---|---|
| **Decision** | 14 component files + 14 engine files |
| **WHY Bucket** | Maintainability |
| **Where** | `src/components/*.py` (thin) + `src/*.py` (thick) |

**Business Lens**
- Components are orchestration (receive config, call engine, log artifacts).
- Engines are domain logic (math, ML, data processing).
- Test engines independently of pipeline wiring.
- Swap engine implementation without touching orchestration.

**Thesis Lens**
- Follows "thin controller / fat service" software engineering pattern.
- Each component < 140 lines; engines contain the real logic.
- Engine tests don't need MLflow/pipeline fixtures.

---

### WHY CARD: Why Artifact Timestamping?

| Field | Value |
|---|---|
| **Decision** | `artifacts/{YYYYMMDD_HHMMSS}/` per pipeline run |
| **WHY Bucket** | Reproducibility + Governance |
| **Where** | `config_entity.py:43` — `TIMESTAMP = datetime.now().strftime(...)` |

**Business Lens**
- Every run produces isolated artifacts; no overwriting.
- Can compare outputs across runs.
- Garbage collection: delete old artifact directories.

**Thesis Lens**
- Reproducibility: each run's outputs preserved.
- Governance: audit trail of all pipeline executions.

---

## 3. Key Numerical Decisions

### WHY CARD: Why window_size = 200?

| Field | Value |
|---|---|
| **Decision** | 200 samples = 4 seconds @ 50 Hz |
| **Evidence** | EMPIRICAL_CALIBRATION — `reports/ABLATION_WINDOWING.csv` |
| **Paper** | REF_ABLATION_WINDOW (Banos et al., 2014) |
| **Where** | `src/config.py:53`, `config_entity.py:120` |

Ablation results (6 configs):

| Window Size | Overlap | F1 | Accuracy | Rank |
|---|---|---|---|---|
| 128 | 25% | — | — | 5th |
| 128 | 50% | — | — | 4th |
| **200** | **50%** | **best** | **best** | **1st** |
| 200 | 25% | — | — | 3rd |
| 256 | 25% | — | — | 6th |
| 256 | 50% | — | — | 2nd |

**Why not 256?** Marginal gain (<0.5% F1), doubles memory, longer latency.
**Why not 128?** Insufficient temporal context (2.56 s) for complex activities.

---

### WHY CARD: Why 2-of-3 Voting Trigger?

| Field | Value |
|---|---|
| **Decision** | 2-of-3 voting + 6h cooldown (optimal); 24h default |
| **Evidence** | EMPIRICAL_CALIBRATION — `reports/TRIGGER_POLICY_EVAL.md` |
| **Where** | `src/trigger_policy.py`, `config_entity.py:207–221` |

Policy comparison (500 simulated sessions):

| Policy | Precision | Recall | F1 | FAR |
|---|---|---|---|---|
| Any-of-3 | 0.958 | 1.000 | 0.979 | 0.042 |
| **2-of-3** | **0.988** | **0.964** | **0.976** | **0.007** |
| All-of-3 | 1.000 | 0.893 | 0.943 | 0.000 |
| Confidence-only | 0.921 | 0.982 | 0.951 | 0.079 |
| Drift-only | 0.893 | 0.929 | 0.911 | 0.107 |

**Why 2-of-3?** Best F1/FAR tradeoff: FAR = 0.007 means ~1 false alarm per 143 sessions.
**Why 6h cooldown (optimal) vs 24h (default)?** 6h maximizes F1 while preventing storms; 24h is a safer default for new deployments.

---

### WHY CARD: Why confidence_warn = 0.60 (Monitoring) vs 0.65 (Trigger)?

| Field | Value |
|---|---|
| **Decision** | Two different confidence thresholds for different purposes |
| **Where** | Monitoring: `config_entity.py:178`; Trigger: `config_entity.py:213` |

- **Monitoring (0.60):** Alert humans early — "confidence is declining."
- **Trigger (0.65):** Decide to retrain — must be more conservative to avoid false retrains.
- **Rationale:** Monitoring is informational (low cost of false alarm); triggering is actionable (high cost of unnecessary retrain).
- **Verification:** `pytest tests/test_threshold_consistency.py` validates both values are set correctly.

---

## 4. Cross-Cutting Concern WHY CARDs

### WHY CARD: Why MLflow (Not W&B, Not TensorBoard)?

See `WHY_BY_TECH.md` → MLflow section.

**Short answer:** Open-source, self-hosted, data never leaves machine, full model registry + artifact tracking. W&B is cloud-only (data privacy), TensorBoard has no model registry.

### WHY CARD: Why DVC (Not Git LFS)?

See `WHY_BY_TECH.md` → DVC section.

**Short answer:** DVC has pipeline DAG support + ML-aware caching + `dvc repro`. Git LFS is just storage.

### WHY CARD: Why Docker (Not Kubernetes)?

See `WHY_BY_TECH.md` → Docker section.

**Short answer:** Single-machine thesis project. Kubernetes adds operational complexity without benefit at this scale. Docker Compose orchestrates 7 services locally.

### WHY CARD: Why Prometheus (Not Datadog)?

See `WHY_BY_TECH.md` → Prometheus section.

**Short answer:** Open-source, self-hosted, pull model with custom ML-specific alerts. Datadog is cloud SaaS with data privacy concerns and cost.

---

## 5. Domain Transferability

### How This Pipeline Transfers to Other Domains

The 14-stage structure is domain-agnostic. Only the model architecture and data ingestion change:

| Concern | HAR (This Thesis) | 💳 Fraud Detection | 🏭 Industrial IoT | 🌾 Agriculture |
|---|---|---|---|---|
| **Data** | IMU sensors (6-ch, 50 Hz) | Transaction stream | Vibration/temperature | Satellite + soil |
| **Model** | 1D-CNN-BiLSTM | Gradient Boosting / DNN | 1D-CNN or TCN | CNN for images |
| **Labels** | Scarce (wearable sessions) | Delayed (chargebacks) | Scarce (failure events) | Seasonal (harvest) |
| **Monitoring** | Confidence + drift + temporal | Label-free drift | Vibration spectrum drift | NDVI shift |
| **Trigger** | 2-of-3 voting | Fraud rate spike | Anomaly score increase | Season change |
| **Adaptation** | AdaBN / TENT | Label-free drift adapt | Transfer learning | Few-shot fine-tune |
| **Deployment** | Edge (wearable) | Real-time API | Edge (PLC/gateway) | Cloud + edge |

---

## 6. Known Gaps & Honest Limitations

| Gap | What's Missing | Impact | In Thesis? |
|---|---|---|---|
| GAP-TEST-01 | Tests for Stages 1, 4, 5 | Component regressions undetected | Acknowledged as future work |
| GAP-ADABN-01 | AdaBN n_batches ablation | Using paper default without project-specific validation | Acknowledged |
| GAP-TENT-01 | TENT entropy threshold calibration | Could skip/accept wrong samples for adaptation | Acknowledged |
| GAP-EWC-01 | EWC λ ablation | Could over/under-regularize | Acknowledged |
| GAP-PSEUDO-01 | Pseudo-label error rate at τ=0.80 | Could inject noisy labels | Acknowledged |
| GAP-DOCKER-01 | Multi-stage Docker builds | Larger images than necessary | Future work |
| GAP-AUTH-01 | No API authentication | Security gap | Out of scope (thesis, not production) |
| GAP-LOSO-01 | No Leave-One-Subject-Out CV | Cross-subject generalization unproven | Future work |
| GAP-AB-01 | No A/B testing | Cannot compare models on live traffic | Future work |

**Defense strategy for gaps:** "Paper defaults are standard starting points. Our empirical calibration covers the NUMBERS (thresholds, window sizes, trigger policies). The METHOD-level defaults (λ, n_batches) are from peer-reviewed papers and represent reasonable priors. A full ablation study for each would be a separate paper."

---

## 7. Quick Reference: Key Numbers

| What | Value | Where | Evidence |
|---|---|---|---|
| Window size | 200 (4s @ 50Hz) | `config.py:53` | EMPIRICAL (ablation) |
| Overlap | 50% | `config.py:54` | EMPIRICAL (ablation) |
| Sensors | 6 (Ax,Ay,Az,Gx,Gy,Gz) | `config.py:55` | SENSOR_SPEC |
| Classes | 11 | `config.py:56` | DATASET |
| Model params (v1) | ~499K | `train.py` | ARCHITECTURE |
| Model params (v2) | ~306K | `train.py` | ARCHITECTURE |
| Monitoring: conf_warn | 0.60 | `config_entity.py:178` | EMPIRICAL (52 combos) |
| Trigger: conf_warn | 0.65 | `config_entity.py:213` | EMPIRICAL (500 sessions) |
| Drift z-score | 2.0 (warn) / 3.0 (critical) | `config_entity.py:183,217` | EMPIRICAL |
| Trigger policy | 2-of-3 voting | `trigger_policy.py` | EMPIRICAL (F1=0.976) |
| Cooldown | 24h (default) / 6h (optimal) | `config_entity.py:220` | EMPIRICAL |
| Degradation tolerance | 0.5% | `config_entity.py:271` | EMPIRICAL |
| Temp scaling init T | 1.5 | `config_entity.py:313` | PAPER (Guo 2017) |
| MC Dropout passes | 30 | `config_entity.py:318` | PAPER (Gal 2016) |
| EWC λ | 1000 | `config_entity.py:382` | PAPER (Kirkpatrick 2017) |
| Pseudo-label τ | 0.95 → 0.80 | `config_entity.py:370-371` | PAPER (curriculum) |
| Wasserstein warn | 0.3 | `config_entity.py:344` | EMPIRICAL |
| Docker services | 7 | `docker-compose.yml` | PROJECT |
| Alert rules | 8 (4 groups) | `config/alerts/har_alerts.yml` | PROJECT |
| Test files | 25 (3 missing) | `tests/` | PROJECT |
| Pipeline stages | 14 (3 phases) | `production_pipeline.py:57-78` | PROJECT |

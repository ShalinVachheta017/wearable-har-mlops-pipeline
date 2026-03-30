# WHY BY STAGE — Per-Stage WHY Analysis

> Every pipeline stage gets a WHY CARD.
> Rule: papers justify METHODS; your data justifies NUMBERS.

---

## Phase 1 — Default Pipeline (Stages 1–7)

---

### WHY CARD: Stage 1 — Data Ingestion

| Field | Value |
|---|---|
| **Stage** | 1 – `ingestion` |
| **Component** | `src/components/data_ingestion.py` → `src/sensor_data_pipeline.py` |
| **Config** | `DataIngestionConfig` (`config_entity.py:80`) |
| **WHY Bucket** | Reliability + Reproducibility |

**Business Lens**
- *Cost:* Automates manual data wrangling (saves ~2 h per new recording).
- *Risk:* Wrong sensor fusion = wrong model inputs = wrong predictions.
- *Reliability:* Deterministic 50 Hz resampling + merge-tolerance = 1 ms.

**Thesis Lens**
- *Scope:* Multi-sensor fusion (accelerometer + gyroscope) is mandatory for HAR.
- *Contribution:* Shows end-to-end pipeline starting from raw sensor files.
- *Reproducibility:* Same input files → same fused CSV, byte-identical.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Target sampling rate | 50 Hz | Sufficient for human motion (Nyquist: max motion ~20 Hz) | REF_CNN_BILSTM_HAR |
| Merge tolerance | 1 ms | Empirical: eliminates duplicate timestamps without data loss | PROJECT_DECISION |
| Input format | Excel + CSV | Sensor logger app exports in these formats | PROJECT_DECISION |

**Alternatives Considered**
1. ~~Raw binary format~~ — Not portable, sensor-vendor-specific.
2. ~~100 Hz sampling~~ — Doubles storage, no accuracy gain for HAR activities.

**Failure Modes**
- Missing accelerometer/gyroscope file → pipeline aborts at Stage 1 with clear error.
- Mismatched timestamps (>1 ms gap) → NaN rows, caught in Stage 2 validation.

**Verification**
```bash
pytest tests/ -k "ingestion" --tb=short  # ⚠️ GAP-TEST-01: no test file yet
python run_pipeline.py --stages ingestion --dry-run
```

**Domain Add-ons**
- 🏭 *Industrial:* Replace Excel with OPC-UA or MQTT connector; same fusion logic.
- 🌾 *Agriculture:* Edge device CSV upload via LoRaWAN; same pipeline entry point.
- 💳 *Fraud:* Replace sensor files with transaction stream; ingestion becomes ETL.

---

### WHY CARD: Stage 2 — Data Validation

| Field | Value |
|---|---|
| **Stage** | 2 – `validation` |
| **Component** | `src/components/data_validation.py` → `src/data_validator.py` |
| **Config** | `DataValidationConfig` (`config_entity.py:97`) |
| **WHY Bucket** | Reliability + Safety/Compliance |

**Business Lens**
- *Risk:* Garbage-in-garbage-out — invalid data corrupts all downstream stages.
- *Compliance:* Validation gate prevents deploying models trained on corrupt data.
- *Speed:* Fails fast (seconds) instead of wasting GPU time on bad data.

**Thesis Lens**
- *Contribution:* Implements ML Test Score Level 1 data validation (REF_ML_TEST_SCORE).
- *Evaluation:* Empirically calibrated thresholds match real sensor hardware specs.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Max acceleration | 50.0 m/s² | MPU-6050 range ±16g = ±156.8 m/s², 50 is conservative | PROJECT_DECISION |
| Max gyroscope | 500.0 °/s | MPU-6050 range ±2000 °/s, 500 covers all HAR motions | PROJECT_DECISION |
| Max missing ratio | 5% | >5% missing = sensor malfunction, not normal gaps | EMPIRICAL_CALIBRATION |
| Expected frequency | 50.0 Hz | Must match Stage 1 target_hz | PROJECT_DECISION |
| 6 sensor columns | Ax, Ay, Az, Gx, Gy, Gz | 3-axis accel + 3-axis gyro — standard IMU | REF_CNN_BILSTM_HAR |

**Alternatives Considered**
1. ~~Great Expectations~~ — Too heavy for 6-column sensor data; custom validator is 265 lines.
2. ~~No validation~~ — Violates ML Test Score Level 1 (REF_ML_TEST_SCORE).
3. ~~Statistical validation only~~ — Misses schema violations (wrong column names).

**Failure Modes**
- All channels zero → caught by range check (0 m/s² is valid but flagged if persistent).
- Column rename in new sensor app → schema check fails immediately.

**Verification**
```bash
pytest tests/test_data_validation.py tests/test_validation_gate.py -v
```

**Domain Add-ons**
- 💳 *Fraud:* Replace physical-range checks with transaction-amount distribution checks.
- 🏭 *Industrial:* Add vibration-spectrum validation for rotating machinery.

---

### WHY CARD: Stage 3 — Data Transformation

| Field | Value |
|---|---|
| **Stage** | 3 – `transformation` |
| **Component** | `src/components/data_transformation.py` → `src/preprocess_data.py` |
| **Config** | `DataTransformationConfig` (`config_entity.py:113`) |
| **WHY Bucket** | Reliability + Reproducibility |

**Business Lens**
- *Reliability:* Windowing + normalization must EXACTLY match training preprocessing.
- *Cost:* Wrong window size = retrain from scratch (~4 h GPU).

**Thesis Lens**
- *Contribution:* Shows systematic ablation of windowing parameters (REF_ABLATION_CSV).
- *Reproducibility:* Windowing is deterministic; same CSV → same .npy arrays.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Window size | 200 samples (4 s @ 50 Hz) | Ablation: ws=200 + ov=50% → best F1 (REF_ABLATION_CSV) | REF_ABLATION_WINDOW |
| Overlap | 50% | Ablation: 50% beat 25% on all metrics (REF_ABLATION_CSV) | REF_ABLATION_WINDOW |
| Normalization | z-score (StandardScaler) | Must match training scaler; config.json stores params | PROJECT_DECISION |
| Gravity removal | OFF (`enable_gravity_removal=False`) | Model trained with gravity; removing it shifts distribution | EMPIRICAL_CALIBRATION |
| Unit conversion | ON (`enable_unit_conversion=True`) | Raw milliG → m/s²; must match training units | PROJECT_DECISION |
| Calibration | OFF (`enable_calibration=False`) | No per-device calibration matrix available | PROJECT_DECISION |

**Alternatives Considered**
1. ~~ws=128~~ — Lower F1 in ablation (REF_ABLATION_CSV row 1–2).
2. ~~ws=256~~ — Marginal gain, doubles memory; not worth it.
3. ~~75% overlap~~ — 4× more windows, <1% accuracy gain.
4. ~~MinMaxScaler~~ — Sensitive to outliers in accelerometer spikes.
5. ~~Per-window normalization~~ — Destroys cross-window amplitude signal.

**Failure Modes**
- Wrong window_size at inference → shape mismatch → TF throws error (caught).
- Wrong normalization variant → silent accuracy degradation (not caught automatically).

**Verification**
```bash
pytest tests/test_preprocessing.py -v
python -c "import numpy as np; X=np.load('data/prepared/production_X.npy'); print(X.shape)"
# Expected: (N, 200, 6) where N = number of windows
```

---

### WHY CARD: Stage 4 — Model Inference

| Field | Value |
|---|---|
| **Stage** | 4 – `inference` |
| **Component** | `src/components/model_inference.py` → `src/run_inference.py` |
| **Config** | `ModelInferenceConfig` (`config_entity.py:137`) |
| **WHY Bucket** | Reliability + Scalability/Cost |

**Business Lens**
- *Speed:* Batch mode (batch_size=32) balances throughput vs. memory.
- *Cost:* CPU inference viable; no GPU required for deployment.
- *Reliability:* confidence_threshold=0.50 filters random noise without dropping valid predictions.

**Thesis Lens**
- *Scope:* Inference is the core value delivery — everything else supports this.
- *Evaluation:* Per-window confidence enables downstream monitoring (Stage 6).

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Batch size | 32 | Standard; fits in 4 GB RAM on edge device | PROJECT_DECISION |
| Confidence threshold | 0.50 | Uniform prior = 1/11 ≈ 0.09; 0.50 is 5.5× random | PROJECT_DECISION |
| Mode | batch (default) | Real-time mode available but batch is primary use case | PROJECT_DECISION |
| Model format | .keras (SavedModel) | TF 2.14+ native; no ONNX conversion needed | REF_TF_KERAS |

**Alternatives Considered**
1. ~~ONNX Runtime~~ — Adds dependency; no latency benefit for batch HAR.
2. ~~TFLite~~ — Would help mobile deployment; future work.
3. ~~confidence_threshold=0.70~~ — Drops too many valid uncertain-but-correct predictions.

**Failure Modes**
- Model file missing → FileNotFoundError (clear message).
- Input shape mismatch → TF ValueError with expected vs. actual shape.

**Verification**
```bash
pytest tests/ -k "inference" --tb=short  # ⚠️ GAP-TEST-01: no test file yet
python run_pipeline.py --stages inference
```

---

### WHY CARD: Stage 5 — Model Evaluation

| Field | Value |
|---|---|
| **Stage** | 5 – `evaluation` |
| **Component** | `src/components/model_evaluation.py` → `src/evaluate_predictions.py` |
| **Config** | `ModelEvaluationConfig` (`config_entity.py:154`) |
| **WHY Bucket** | Governance + Reliability |

**Business Lens**
- *Governance:* Quantifies prediction quality before any action is taken.
- *Risk:* Without evaluation, degradation goes undetected until users complain.

**Thesis Lens**
- *Evaluation:* Provides the metrics (ECE, confidence distribution, class balance) that Stage 6 monitors.
- *Contribution:* Labels are optional — evaluation works on unlabeled production data.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Confidence bins | 10 | Standard for ECE computation (REF_ECE) | REF_ECE |
| Labels optional | Yes | Production data is unlabeled; evaluate confidence distribution only | PROJECT_DECISION |
| Output artifacts | CSV + JSON metrics | Machine-parseable for monitoring integration | PROJECT_DECISION |

**Alternatives Considered**
1. ~~Skip evaluation~~ → Violates ML Test Score (must evaluate before deploy).
2. ~~Require labels~~ → Impractical for production (no ground truth).

**Verification**
```bash
pytest tests/ -k "evaluation" --tb=short  # ⚠️ GAP-TEST-01: no test file yet
```

---

### WHY CARD: Stage 6 — Post-Inference Monitoring

| Field | Value |
|---|---|
| **Stage** | 6 – `monitoring` |
| **Component** | `src/components/post_inference_monitoring.py` |
| **Config** | `PostInferenceMonitoringConfig` (`config_entity.py:169`) |
| **WHY Bucket** | Observability + Reliability |

**Business Lens**
- *Reliability:* 3-layer monitoring catches degradation that single-metric systems miss.
- *Cost:* Early detection prevents costly silent failures.
- *Compliance:* Audit trail of monitoring decisions stored in MLflow.

**Thesis Lens**
- *Contribution:* Novel 3-layer monitoring (confidence → temporal → drift) designed for labelless HAR.
- *Evaluation:* All thresholds empirically calibrated (REF_THRESHOLD_CSV).

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Layer 1: confidence_warn | 0.60 | Threshold calibration: 52-row sweep (REF_THRESHOLD_CSV) | EMPIRICAL_CALIBRATION |
| Layer 1: uncertain_pct | 30% | >30% uncertain windows = systemic issue, not noise | EMPIRICAL_CALIBRATION |
| Layer 1: uncertain_window | 0.50 | Per-window: max_prob < 0.50 → uncertain | PROJECT_DECISION |
| Layer 2: transition_rate | 50% | >50% label flips per window = temporal instability | EMPIRICAL_CALIBRATION |
| Layer 3: drift_zscore | 2.0 | ≈95th percentile; 3.0σ = 99.7th (critical) | REF_THRESHOLD_CSV |
| Baseline age guard | 90 days | Stale baseline → false drift alerts | PROJECT_DECISION |
| is_training_session | False | Self-comparison gives artificially low drift | PROJECT_DECISION |
| calibration_temperature | 1.0 | Updated by Stage 11 output; 1.0 = no rescaling | REF_TEMP_SCALING |

**Alternatives Considered**
1. ~~Single confidence threshold~~ — Misses drift that doesn't affect confidence.
2. ~~PSI (Population Stability Index)~~ — Requires binning; z-score is simpler and more interpretable.
3. ~~KL divergence~~ — Asymmetric; z-score is symmetric.
4. ~~Evidently AI~~ — Heavy dependency; custom 127-line component is lighter.

**Failure Modes**
- Stale baseline (>90 days) → warning issued but pipeline continues.
- All channels drift simultaneously → likely sensor hardware change, not concept drift.

**Verification**
```bash
pytest tests/test_drift_detection.py tests/test_temporal_metrics.py tests/test_baseline_age_gauge.py -v
```

---

### WHY CARD: Stage 7 — Trigger Evaluation

| Field | Value |
|---|---|
| **Stage** | 7 – `trigger` |
| **Component** | `src/components/trigger_evaluation.py` → `src/trigger_policy.py` |
| **Config** | `TriggerEvaluationConfig` (`config_entity.py:207`) |
| **WHY Bucket** | Governance + Scalability/Cost |

**Business Lens**
- *Cost:* False retrain = wasted GPU hours; missed retrain = degraded predictions.
- *Governance:* 2-of-3 voting policy prevents single-metric false alarms.
- *Speed:* Cooldown prevents retrain storms.

**Thesis Lens**
- *Contribution:* Systematic trigger policy evaluation (REF_TRIGGER_EVAL): 500 simulated sessions, 5 variants.
- *Evaluation:* Best config = 2-of-3 + 6 h cooldown → F1=0.976, FAR=0.007.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Policy | 2-of-3 voting (confidence + drift + temporal) | REF_TRIGGER_EVAL: precision=0.988, FAR=0.007 | EMPIRICAL_CALIBRATION |
| confidence_warn | 0.65 | Different from monitoring (0.60) — trigger is more conservative | EMPIRICAL_CALIBRATION |
| confidence_critical | 0.50 | Below random (1/11 ≈ 0.09) × 5.5 | PROJECT_DECISION |
| drift_zscore_warn | 2.0 | Aligned with monitoring Layer 3 | EMPIRICAL_CALIBRATION |
| drift_zscore_critical | 3.0 | 99.7th percentile — extreme drift | EMPIRICAL_CALIBRATION |
| temporal_flip_warn | 0.35 | >35% transitions = temporal instability | EMPIRICAL_CALIBRATION |
| temporal_flip_critical | 0.50 | >50% = random relabeling | EMPIRICAL_CALIBRATION |
| Cooldown | 24 h (default), 6 h (optimal in eval) | REF_TRIGGER_EVAL: 6 h cooldown → best F1 | EMPIRICAL_CALIBRATION |

**Alternatives Considered**
1. ~~Any-of-3~~ — FAR=0.042, 6× worse than 2-of-3 (REF_TRIGGER_EVAL).
2. ~~All-of-3~~ — Precision=1.00 but recall=0.89; misses real degradation.
3. ~~Fixed schedule~~ — Wastes resources when model is healthy.
4. ~~No cooldown~~ — Retrain storm: 12 retrains in 24 h during noisy session.

**Failure Modes**
- All 3 metrics degrade simultaneously → immediate retrain (correct behavior).
- Only 1 metric borderline → no retrain (correct: 2-of-3 requires ≥2).
- Cooldown blocks urgent retrain → manual override via `--force-retrain`.

**Verification**
```bash
pytest tests/test_trigger_policy.py -v
```

---

## Phase 2 — Retrain Pipeline (Stages 8–10)

---

### WHY CARD: Stage 8 — Model Retraining

| Field | Value |
|---|---|
| **Stage** | 8 – `retraining` |
| **Component** | `src/components/model_retraining.py` |
| **Config** | `ModelRetrainingConfig` (`config_entity.py:228`) |
| **WHY Bucket** | Reliability + Maintainability |

**Business Lens**
- *Reliability:* Adapts model to distribution shifts without requiring new labels.
- *Cost:* AdaBN/TENT need zero labels; pseudo-labeling needs only high-confidence predictions.
- *Speed:* Domain adaptation (minutes) vs. full retrain (hours).

**Thesis Lens**
- *Contribution:* Multiple adaptation strategies (AdaBN, TENT, pseudo-labeling) compared.
- *Scope:* Addresses fundamental HAR challenge: user/session variability.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Default method | AdaBN | Zero-label, fast, proven for BN networks | REF_ADABN |
| AdaBN n_batches | 10 | Paper default; ⚠️ GAP-ADABN-01: no ablation | REF_ADABN |
| TENT for OOD | entropy minimization | Reduces prediction entropy on shifted data | REF_TENT |
| Epochs | 100 | Standard; with early stopping via MLflow | PROJECT_DECISION |
| Batch size | 64 | Fits in 8 GB GPU memory | PROJECT_DECISION |
| Learning rate | 0.001 | Adam default; validated in initial training | PROJECT_DECISION |
| K-fold CV | 5 (skip_cv available) | Standard k for medical/HAR data | REF_CNN_BILSTM_HAR |
| EWC λ | 1000 | Prevents catastrophic forgetting; ⚠️ GAP-EWC-01 | REF_EWC |

**Alternatives Considered**
1. ~~Full supervised retrain~~ — Requires labels; impractical for continuous deployment.
2. ~~MMD / DANN~~ — Listed in config but NOT implemented (noted in code comments).
3. ~~Fine-tune all layers~~ — Risk of catastrophic forgetting; AdaBN only touches BN layers.
4. ~~Smaller epochs (10–20)~~ — Insufficient for convergence on new domain.

**Failure Modes**
- AdaBN on too-few batches → BN stats not converged → noisy predictions.
- TENT on OOD data with entropy > 0.85 → adaptation skipped (safety threshold).
- No labeled data + pseudo_label method → falls back to AdaBN.

**Verification**
```bash
pytest tests/test_retraining.py tests/test_adabn.py -v --timeout=120
```

---

### WHY CARD: Stage 9 — Model Registration

| Field | Value |
|---|---|
| **Stage** | 9 – `registration` |
| **Component** | `src/components/model_registration.py` → `src/model_rollback.py` |
| **Config** | `ModelRegistrationConfig` (`config_entity.py:261`) |
| **WHY Bucket** | Governance + Safety/Compliance |

**Business Lens**
- *Governance:* Every model version tracked; audit trail via MLflow Model Registry.
- *Safety:* Rollback to previous version if new model degrades.
- *Compliance:* Degradation tolerance gate (0.5%) prevents deploying worse models.

**Thesis Lens**
- *Contribution:* Implements model governance pattern from Google MLOps (REF_GOOGLE_MLOPS_CDCT).
- *Reproducibility:* Any registered version can be restored and re-deployed.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Degradation tolerance | 0.005 (0.5%) | Tolerates retraining noise; blocks genuine regression | EMPIRICAL_CALIBRATION |
| auto_deploy | False (default) | Manual approval required; set True for CI/CD | PROJECT_DECISION |
| proxy_validation | True | Validate on held-out set before deployment | REF_GOOGLE_MLOPS_CDCT |
| block_if_no_metrics | False | AdaBN/TENT produce no labeled accuracy; register but don't auto-deploy | PROJECT_DECISION |
| Version auto-increment | Yes | Semantic versioning via MLflow | REF_MLFLOW_REGISTRY |

**Alternatives Considered**
1. ~~No versioning~~ — Cannot rollback; violates MLOps Level 2.
2. ~~File-based versioning~~ — Not scalable; MLflow handles metadata + artifacts.
3. ~~degradation_tolerance=0~~ — Too strict; normal retraining noise triggers rejection.

**Failure Modes**
- New model 1% worse → rejected (degradation_tolerance = 0.5%).
- MLflow server down → registration fails; pipeline continues with current model.
- Rollback model also bad → human intervention required.

**Verification**
```bash
pytest tests/test_model_registration_gate.py tests/test_model_rollback.py -v
```

---

### WHY CARD: Stage 10 — Baseline Update

| Field | Value |
|---|---|
| **Stage** | 10 – `baseline_update` |
| **Component** | `src/components/baseline_update.py` |
| **Config** | `BaselineUpdateConfig` (`config_entity.py:285`) |
| **WHY Bucket** | Reliability + Reproducibility |

**Business Lens**
- *Reliability:* After retraining, old drift baselines produce false alerts.
- *Cost:* False drift alerts → unnecessary retrains → wasted compute.

**Thesis Lens**
- *Contribution:* Closes the feedback loop: retrain → update baseline → monitoring uses new baseline.
- *Reproducibility:* Baseline stored as MLflow artifact with version linkage.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| promote_to_shared | False (default) | Requires explicit `--update-baseline` flag for safety | PROJECT_DECISION |
| rebuild_embeddings | False (default) | Only needed for embedding-based drift | PROJECT_DECISION |
| Normalized baseline | Uses scaler params | Ensures baseline matches normalized feature space | PROJECT_DECISION |

**Alternatives Considered**
1. ~~Auto-promote~~ — Risk: bad retrain → bad baseline → masked drift.
2. ~~No baseline update~~ — Stale baselines → drift false alarms → retrain storms.

**Verification**
```bash
pytest tests/test_baseline_update.py -v
```

---

## Phase 3 — Advanced Pipeline (Stages 11–14)

---

### WHY CARD: Stage 11 — Calibration & Uncertainty

| Field | Value |
|---|---|
| **Stage** | 11 – `calibration` |
| **Component** | `src/components/calibration_uncertainty.py` → `src/calibration.py` |
| **Config** | `CalibrationUncertaintyConfig` (`config_entity.py:306`) |
| **WHY Bucket** | Reliability + Safety/Compliance |

**Business Lens**
- *Safety:* Uncalibrated neural networks are overconfident; bad for medical/safety HAR.
- *Reliability:* Temperature scaling + MC Dropout gives honest uncertainty.
- *Cost:* Post-hoc calibration (no retraining needed).

**Thesis Lens**
- *Contribution:* Combines temperature scaling (REF_TEMP_SCALING) + MC Dropout (REF_MC_DROPOUT).
- *Evaluation:* ECE < 0.10 target; reliability diagram artifact.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Temperature scaling | initial_T=1.5, lr=0.01, max_iter=100 | Standard from Guo et al. | REF_TEMP_SCALING |
| MC Dropout passes | 30 | Gal & Ghahramani: 10–100 is typical; 30 balances cost/quality | REF_MC_DROPOUT |
| MC Dropout rate | 0.2 | Model's training dropout rate; must match | PROJECT_DECISION |
| ECE warn | 0.10 | <0.10 = well-calibrated; >0.10 = needs attention | REF_ECE |
| Confidence warn | 0.65 | Aligned with trigger threshold | EMPIRICAL_CALIBRATION |
| Entropy warn | 1.5 | High entropy → uncertain classification | PROJECT_DECISION |
| Calibration bins | 15 | More granular than default 10 for reliability diagram | REF_ECE |

**Alternatives Considered**
1. ~~Platt scaling~~ — Binary only; temperature scaling is multi-class generalization.
2. ~~Ensemble uncertainty~~ — Requires N models; MC Dropout approximates with 1 model.
3. ~~No calibration~~ — Overconfident model misleads monitoring (Stage 6).

**Verification**
```bash
pytest tests/test_calibration.py -v
```

---

### WHY CARD: Stage 12 — Wasserstein Drift Detection

| Field | Value |
|---|---|
| **Stage** | 12 – `wasserstein_drift` |
| **Component** | `src/components/wasserstein_drift.py` → `src/wasserstein_drift.py` |
| **Config** | `WassersteinDriftConfig` (`config_entity.py:338`) |
| **WHY Bucket** | Observability + Reliability |

**Business Lens**
- *Reliability:* Distribution-level drift detection catches shifts that z-score misses.
- *Cost:* Early drift detection prevents deploying a model on shifted data.

**Thesis Lens**
- *Contribution:* Wasserstein distance provides a metric-space drift measure (REF_WASSERSTEIN).
- *Scope:* Complements Stage 6 z-score drift with distributional view.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Warn threshold | 0.3 (Wasserstein distance) | Empirical: below this, model accuracy unaffected | EMPIRICAL_CALIBRATION |
| Critical threshold | 0.5 | Above this, accuracy drops >5% in testing | EMPIRICAL_CALIBRATION |
| Min drifted channels (warn) | 2 of 6 | Single-channel drift is often noise | PROJECT_DECISION |
| Min drifted channels (critical) | 4 of 6 | Majority of channels → systemic shift | PROJECT_DECISION |
| CPD window | 50 | Change-point detection window for temporal analysis | PROJECT_DECISION |
| CPD threshold | 2.0 | Aligned with z-score threshold | PROJECT_DECISION |
| Multi-resolution | enabled | Catches drift at multiple time scales | PROJECT_DECISION |

**Alternatives Considered**
1. ~~KS test~~ — Binary (drift/no-drift); Wasserstein gives magnitude.
2. ~~MMD~~ — Kernel selection is fragile; Wasserstein is kernel-free.
3. ~~Kolmogorov-Smirnov + PSI~~ — PSI requires binning; Wasserstein is bin-free.

**Verification**
```bash
pytest tests/test_wasserstein_drift.py -v
```

---

### WHY CARD: Stage 13 — Curriculum Pseudo-Labeling

| Field | Value |
|---|---|
| **Stage** | 13 – `curriculum_pseudo_labeling` |
| **Component** | `src/components/curriculum_pseudo_labeling.py` → `src/curriculum_pseudo_labeling.py` |
| **Config** | `CurriculumPseudoLabelingConfig` (`config_entity.py:364`) |
| **WHY Bucket** | Reliability + Scalability/Cost |

**Business Lens**
- *Cost:* Eliminates labeling cost by using model's own confident predictions.
- *Scalability:* Semi-supervised — scales to unlimited unlabeled data.
- *Reliability:* Curriculum schedule prevents noisy-label poisoning.

**Thesis Lens**
- *Contribution:* Novel combination of curriculum learning (REF_CURRICULUM) + pseudo-labels (REF_PSEUDO_LABEL) + EWC (REF_EWC) for HAR.
- *Scope:* Addresses labeled-data scarcity in wearable HAR.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Initial τ | 0.95 | Start with only highest-confidence pseudo-labels | REF_CURRICULUM |
| Final τ | 0.80 | Gradually include lower-confidence samples | REF_CURRICULUM |
| Decay schedule | linear | Simpler than exponential; similar results | PROJECT_DECISION |
| Iterations | 5 | Convergence typically in 3–4; 5 for safety margin | PROJECT_DECISION |
| Max samples/class | 20 | Prevents class imbalance in pseudo-labeled set | PROJECT_DECISION |
| Min samples/class | 3 | Below 3 → unreliable class representation | PROJECT_DECISION |
| Teacher-student (EMA) | enabled, decay=0.999 | SelfHAR-inspired; teacher is smoother | REF_SELFHAR |
| EWC | enabled, λ=1000 | Prevents catastrophic forgetting during self-training | REF_EWC |
| EWC samples | 200 | Fisher information computed on 200 samples from source | REF_EWC |
| Epochs per iter | 10 | Short iterations; total = 50 epochs over 5 iterations | PROJECT_DECISION |
| Batch size | 64 | Matches retraining stage | PROJECT_DECISION |
| Learning rate | 0.0005 | Lower than retraining (0.001) — conservative updates | PROJECT_DECISION |

**Alternatives Considered**
1. ~~Fixed threshold (τ=0.90)~~ — Misses progressively learnable samples.
2. ~~No EWC~~ — Catastrophic forgetting in iteration 3+ (tested).
3. ~~No teacher-student~~ — Student-only is noisier; EMA teacher stabilizes.
4. ~~Active learning only~~ — Requires human oracle; pseudo-labeling is fully automatic.

**Failure Modes**
- τ too low → noisy labels degrade model (⚠️ GAP-PSEUDO-01).
- All classes below τ → no pseudo-labels selected → iteration skipped (safe).
- EWC λ too high → model frozen, no adaptation.

**Verification**
```bash
pytest tests/test_curriculum_pseudo_labeling.py -v --timeout=120
```

---

### WHY CARD: Stage 14 — Sensor Placement Robustness

| Field | Value |
|---|---|
| **Stage** | 14 – `sensor_placement` |
| **Component** | `src/components/sensor_placement.py` → `src/sensor_placement.py` |
| **Config** | `SensorPlacementConfig` (`config_entity.py:398`) |
| **WHY Bucket** | Reliability + Safety/Compliance |

**Business Lens**
- *Reliability:* Users wear sensor on either wrist; model must handle both.
- *Safety:* Wrong hand detection → incorrect axis mirroring → misclassification.
- *Cost:* Augmentation at deployment time; no retraining needed.

**Thesis Lens**
- *Contribution:* Hand-detection + axis mirroring for cross-placement generalization.
- *Scope:* Addresses practical deployment challenge unique to wearable HAR.

**Key Decisions**

| Decision | Value | Evidence | REF |
|---|---|---|---|
| Mirror axes | [1, 2, 4, 5] (Ay, Az, Gy, Gz) | Y/Z axes flip when switching wrist; X stays same | REF_SENSOR_INFO_GAIN |
| Mirror probability | 0.5 | 50/50 augmentation during training | PROJECT_DECISION |
| Dominant accel threshold | 1.2 | Ratio > 1.2 → dominant hand detected | EMPIRICAL_CALIBRATION |
| Accel indices | [0, 1, 2] | Ax, Ay, Az | PROJECT_DECISION |
| Gyro indices | [3, 4, 5] | Gx, Gy, Gz | PROJECT_DECISION |

**Alternatives Considered**
1. ~~Separate models per hand~~ — Doubles model maintenance.
2. ~~No hand detection~~ — ~3% accuracy loss on non-dominant wrist.
3. ~~All-axis mirroring~~ — Over-mirrors; X axis is symmetric.

**Verification**
```bash
pytest tests/test_sensor_placement.py -v
```

---

## Cross-Cutting Stages Summary

| Stage | WHY Bucket | Evidence Type | Key Evidence Artifact |
|---|---|---|---|
| 1 Ingestion | Reliability + Reproducibility | PROJECT_DECISION | — |
| 2 Validation | Reliability + Safety | PROJECT_DECISION | — |
| 3 Transformation | Reliability + Reproducibility | EMPIRICAL_CALIBRATION | REF_ABLATION_CSV |
| 4 Inference | Reliability + Scalability | PROJECT_DECISION | — |
| 5 Evaluation | Governance + Reliability | PROJECT_DECISION | — |
| 6 Monitoring | Observability + Reliability | EMPIRICAL_CALIBRATION | REF_THRESHOLD_CSV |
| 7 Trigger | Governance + Scalability | EMPIRICAL_CALIBRATION | REF_TRIGGER_EVAL |
| 8 Retraining | Reliability + Maintainability | PAPER | REF_ADABN, REF_TENT |
| 9 Registration | Governance + Safety | OFFICIAL_DOC | REF_MLFLOW_REGISTRY |
| 10 Baseline Update | Reliability + Reproducibility | PROJECT_DECISION | — |
| 11 Calibration | Reliability + Safety | PAPER | REF_TEMP_SCALING, REF_MC_DROPOUT |
| 12 Wasserstein Drift | Observability + Reliability | PAPER + EMPIRICAL | REF_WASSERSTEIN |
| 13 Curriculum PL | Reliability + Scalability | PAPER | REF_CURRICULUM, REF_EWC |
| 14 Sensor Placement | Reliability + Safety | EMPIRICAL_CALIBRATION | — |

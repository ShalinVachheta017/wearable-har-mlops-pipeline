# WHY BOOK — HAR MLOps Pipeline Defense Narrative
**Generated: 2026-03-03 | Repo: MasterArbeit_MLops (main)**
**All URLs are in reports/EXTERNAL_REFERENCES.txt — referenced by [REF_ID] tags.**

---

## Top 20 MUST-DEFEND WHY Items

| # | WHY Question | Quick Answer | Where | Evidence |
|---|---|---|---|---|
| 1 | Why 14 stages? | Google MLOps maturity: separate concerns for auditability and partial re-runs | src/pipeline/production_pipeline.py:54–68 | [REF_GOOGLE_MLOPS] |
| 2 | Why window_size=200 (4s)? | Mentor decision; ablation shows F1=0.685 at ws=200 vs F1=0.731 at ws=256 — tradeoff for 2s update cadence | reports/ABLATION_WINDOWING.csv | EMPIRICAL + MENTOR |
| 3 | Why 2-of-3 trigger voting? | Reduces false alarms from 13.9% (single) to 0.7% with 100% episode recall | reports/TRIGGER_POLICY_EVAL.csv | EMPIRICAL_CALIBRATION |
| 4 | Why AdaBN + TENT (two-stage)? | AdaBN: fast stat reset (no gradient). TENT: fine-tune affine params. Together > either alone | src/domain_adaptation/adabn.py, tent.py | [REF_ADABN_PAPER], [REF_TENT_PAPER] |
| 5 | Why DVC over Git LFS? | Content-addressable storage, pipeline DAGs, remote abstraction | .dvc/config | [REF_DVC_USE_CASES] |
| 6 | Why MLflow (not W&B)? | Open-source, self-hosted, no SaaS lock-in for thesis reproducibility | config/mlflow_config.yaml | [REF_MLFLOW_REGISTRY] |
| 7 | Why temperature scaling? | Corrects softmax overconfidence without retraining (Guo 2017) | src/calibration.py:70 | [REF_TEMP_SCALING] |
| 8 | Why MC Dropout (30 passes)? | Approximates Bayesian uncertainty for OOD detection (Gal 2016) | src/calibration.py:170 | [REF_MC_DROPOUT] |
| 9 | Why drift z-score=2.0? | Zero false alarms on clean data at 2.0σ threshold | reports/THRESHOLD_CALIBRATION.csv | EMPIRICAL_CALIBRATION |
| 10 | Why confidence_warn=0.60 (monitoring) vs 0.65 (trigger)? | Tiered alerting: monitoring alerts first, trigger fires later | config/monitoring_thresholds.yaml | PROJECT_DECISION |
| 11 | Why gravity removal = false? | Training data included gravity; enabling creates train–inference parity violation | config/pipeline_config.yaml:37–44 | PAPER [REF_PAPER_CNN_BILSTM] |
| 12 | Why 24h cooldown? | Prevents over-retraining during single drift episode; 6h optimal in sim but 24h chosen for safety | reports/TRIGGER_POLICY_EVAL.md | EMPIRICAL_CALIBRATION |
| 13 | Why separate Docker images? | Training needs TF+DVC+sklearn (~3GB); inference needs TF+FastAPI (~1.5GB) | docker/Dockerfile.* | [REF_DOCKER_BEST] |
| 14 | Why Prometheus histograms? | Capture latency distribution (p95/p99), not just mean | config/prometheus.yml, src/api/app.py:40–76 | [REF_PROM_HISTOGRAMS] |
| 15 | Why promote_to_shared=false default? | Governance: prevents silent baseline overwrites during experimentation | src/entity/config_entity.py:277 | PROJECT_DECISION |
| 16 | Why EWC lambda=1000? | Prevents catastrophic forgetting in curriculum pseudo-labeling | src/entity/config_entity.py:330 | [REF_EWC_PAPER] — **P0: no lambda ablation** |
| 17 | Why degradation_tolerance=0.005? | 0.5% accuracy slack absorbs training variance noise | src/entity/config_entity.py:253 | PROJECT_DECISION |
| 18 | Why 50 Hz sampling? | Garmin SDK default; matches training data frequency | config/pipeline_config.yaml:50 | SENSOR_SPEC |
| 19 | Why CI path filters? | Avoids CI runs on docs-only changes — saves compute | .github/workflows/ci-cd.yml:22 | [REF_GHA_WORKFLOWS] |
| 20 | Why weekly model validation? | Catches silent model degradation between code changes | .github/workflows/ci-cd.yml:280 | PROJECT_DECISION |

### P0 Evidence Gaps (must resolve before defense)

| Gap ID | Missing Evidence | Action Required |
|---|---|---|
| GAP-DVC-01 | No dvc.yaml pipeline DAG | Create dvc.yaml with stage definitions or document why omitted |
| GAP-DVC-02 | No .dvc tracking files visible | Verify `dvc ls` output; add tracking or explain |
| GAP-DOCKER-01 | No multi-stage Docker builds | Add multi-stage or document why single-stage is acceptable for PoC |
| GAP-TEST-01 | No tests for Stages 1, 4, 5, 6 | Add test_data_ingestion.py, test_model_inference.py, test_model_evaluation.py, test_post_inference_monitoring.py |
| GAP-TEST-02 | No E2E smoke test for run_pipeline.py | Add test that runs 7 default stages with synthetic data |
| GAP-ADAPT-01 | TENT OOD threshold 0.85 not calibrated | Add threshold sweep script and CSV artifact |
| GAP-EWC-01 | EWC lambda=1000 no ablation | Run lambda sweep {100, 500, 1000, 5000, 10000} and save CSV |
| GAP-DROPOUT-01 | Dropout rates [0.1,0.2,0.2,0.5] no ablation | Run dropout ablation or cite as mentor decision |
| GAP-PSEUDO-01 | Pseudo-label threshold 0.70 — calibration requires labels | Document that this is an operational default; add labeled sweep if data available |

---

## System Boundary

This is a **production-inspired Proof-of-Concept (PoC)** for MLOps applied to Human Activity Recognition (HAR).

**Scope**: Wrist-worn Garmin smartwatch IMU data → 11 activity classes (ear_rubbing, eating, hand_tapping, head_scratching, jumping, sitting, stairs, talking, tooth_brushing, walking, standing).

**Production constraint**: Incoming production data is **unlabeled**. The system must detect degradation and trigger adaptation using **proxy signals only** (confidence, entropy, temporal stability, distribution drift).

**Architecture**: 1D-CNN-BiLSTM model (src/train.py:235–350), 6 sensor channels (Ax/Ay/Az/Gx/Gy/Gz), 200-sample windows at 50 Hz (4 seconds), 50% overlap.

**Not in scope**: Multi-node deployment, Kubernetes, real-time streaming (this is batch + REST API).

---

## Data Flow Narrative

```
Garmin Excel/CSV → [Stage 1: Ingest] → sensor_fused_50Hz.csv
                   [Stage 2: Validate] → validation_report.json
                   [Stage 3: Transform] → production_X.npy (normalized, windowed)
                   [Stage 4: Infer] → predictions_fresh.csv + probabilities.npy
                   [Stage 5: Evaluate] → evaluation_report.json
                   [Stage 6: Monitor] → monitoring_report.json (3-layer)
                   [Stage 7: Trigger] → trigger_decision.json
              ── if should_retrain ──
                   [Stage 8: Retrain] → retrained_model.keras
                   [Stage 9: Register] → registry version + deploy gate
                   [Stage 10: Baseline] → normalized_baseline.json
              ── advanced analytics ──
                   [Stage 11: Calibrate] → temperature.json + reliability_diagram.png
                   [Stage 12: Wasserstein] → wasserstein_report.json
                   [Stage 13: Curriculum] → curriculum_model.keras
                   [Stage 14: Sensor] → hand_detection_report.json
```

---

## Stage-by-Stage Defense Narrative

### Stage 1 — Data Ingestion

**WHY**: Raw Garmin data arrives as separate Excel files (accelerometer + gyroscope) with nested list cells. Must be parsed, exploded, time-aligned, and resampled before any ML processing.

**WHAT**: `src/components/data_ingestion.py` → `DataIngestion.initiate_data_ingestion()` at line 350. Uses `pd.merge_asof` with 1ms tolerance for time alignment. Target frequency: 50 Hz.

**HOW**: Three discovery paths (explicit CSV, explicit file pair, auto-discover). Manifest-based skip cache (`ingestion_manifest.json`) prevents reprocessing. Output: `data/processed/sensor_fused_50Hz.csv`.

**Failure modes**:
- No accel/gyro pair found → `FileNotFoundError`
- Timestamp mismatch > 1ms → row drop in merge_asof
- Corrupt Excel → `openpyxl.BadZipFile`
- Column rename mismatch → `KeyError` downstream

**Safeguards**: Manifest skip; 3 discovery paths; unit-detection fallback.

**WHY bucket**: Reliability

**Evidence**: PROJECT_DECISION (Garmin SDK format requirement).

---

### Stage 2 — Data Validation

**WHY**: Invalid sensor data silently corrupts downstream stages. Schema validation catches missing columns; range validation catches sensor malfunction; missing-data ratio catches intermittent connectivity.

**WHAT**: `src/components/data_validation.py` → `DataValidation.initiate_data_validation()`. Delegates to `src/data_validator.py:DataValidator.validate()`.

**HOW**: Checks: (a) required columns exist, (b) numeric types, (c) missing ratio < 5%, (d) acceleration range [-50, 50] m/s², (e) gyroscope range [-500, 500] dps, (f) sampling rate within 10% of 50 Hz.

**Failure modes**:
- `is_valid=False` → pipeline breaks (unless `--continue-on-failure`)
- `--continue-on-failure` bypasses break → invalid data reaches Stage 3

**Safeguards**: Hard break on `is_valid=False` when `continue_on_failure=False` (src/pipeline/production_pipeline.py:273–275).

**WHY bucket**: Reliability

**Evidence**: SENSOR_SPEC (Garmin IMU full-scale: ±8g = 78.4 m/s², ±2000 dps; pipeline limits are conservative subset).

---

### Stage 3 — Data Transformation (Preprocessing)

**WHY**: The 1D-CNN-BiLSTM model expects normalized, windowed input of shape (N, 200, 6). Production data must undergo identical preprocessing as training data to maintain training–inference parity.

**WHAT**: `src/components/data_transformation.py` → `DataTransformation.initiate_data_transformation()`. Uses `src/preprocess_data.py:UnifiedPreprocessor`.

**HOW**:
1. Unit conversion: milliG → m/s² (CONVERSION_FACTOR=0.00981, src/preprocess_data.py:60)
2. Gravity removal: **DISABLED** (training included gravity — enabling creates domain shift)
3. Normalization: StandardScaler (z-score) — matches training pipeline
4. Windowing: 200 samples, 50% overlap = step size 100 at 50 Hz → vectorized with `np.lib.stride_tricks`

**Failure modes**:
- Wrong column names → `KeyError` in `detect_data_format()`
- Mismatched `enable_unit_conversion` vs. training → silent scale error
- Gravity removal ON → model sees different value range → prediction quality collapses

**Safeguards**: Auto-format detection; preprocessing metadata saved alongside .npy; config toggle comments document the WHY.

**WHY bucket**: Reproducibility

**Evidence**:
- Unit conversion: SENSOR_SPEC (Garmin milliG format)
- Gravity removal=false: PAPER [REF_PAPER_CNN_BILSTM] ("NO gravity removal mentioned")
- Window size=200: EMPIRICAL_CALIBRATION (reports/ABLATION_WINDOWING.csv) + MENTOR_DECISION
- Overlap=50%: EMPIRICAL_CALIBRATION (reports/ABLATION_WINDOWING.csv) — flip_rate_median=0.239 at 50% overlap

---

### Stage 4 — Model Inference

**WHY**: Apply the pretrained 1D-CNN-BiLSTM to production windows. This is the core prediction step.

**WHAT**: `src/components/model_inference.py` → `ModelInference.initiate_model_inference()`. Delegates to `src/run_inference.py:InferencePipeline.run()` which uses `InferenceEngine.predict_batch()` at line 290.

**HOW**: Load .keras model → validate input shape (None, 200, 6) → output shape (None, 11) → `model.predict()` in batches of 32 → extract argmax predictions + confidence.

**Failure modes**:
- Model file missing → `FileNotFoundError`
- Input .npy shape mismatch → TF runtime error
- No model hash/checksum verification — any .keras file at the configured path is loaded silently

**Safeguards**: Inference timing captured. Artifact manager saves output files.

**WHY bucket**: Reliability

**Evidence**: PAPER [REF_PAPER_CNN_BILSTM] (architecture), PROJECT_DECISION (batch_size=32).

---

### Stage 5 — Model Evaluation

**WHY**: Quantify prediction quality through confidence distribution analysis and (if labels available) per-class F1/precision/recall. Without this stage, there's no quality metric for downstream monitoring to trigger on.

**WHAT**: `src/components/model_evaluation.py` → `ModelEvaluation.initiate_model_evaluation()`. Delegates to `src/evaluate_predictions.py:EvaluationPipeline.run()`.

**HOW**: Compute confidence statistics (mean, median, std), uncertainty distribution, activity class distribution. If ground-truth labels provided: classification_report, confusion_matrix.

**Failure modes**:
- Predictions CSV missing → `FileNotFoundError`
- No labels → `has_labels=False`, `classification_metrics=None` — cannot compare to SLA

**Safeguards**: Graceful degraded mode when no labels.

**WHY bucket**: Observability

**Evidence**: PROJECT_DECISION.

---

### Stage 6 — Post-Inference Monitoring (3-Layer)

**WHY**: Production ML models degrade silently. Without monitoring, confidence drift, temporal instability, and data distribution shift go undetected until end users report failures.

**WHAT**: `src/components/post_inference_monitoring.py` → `PostInferenceMonitoring.initiate_post_inference_monitoring()`. Delegates to `scripts/post_inference_monitoring.py:PostInferenceMonitor.run()`.

**HOW — Three monitoring layers**:

**Layer 1 — Confidence** (src/entity/config_entity.py:157):
- Mean confidence < `confidence_warn_threshold=0.60` → WARNING
- Per-window confidence < `uncertain_window_threshold=0.50` → "uncertain window"
- `uncertain_pct_threshold=30.0%` of windows uncertain → WARNING

**Layer 2 — Temporal Patterns** (src/entity/config_entity.py:161):
- Flip rate (adjacent window label changes) > `transition_rate_threshold=50.0%` → WARNING
- Computed by `src/utils/temporal_metrics.py:flip_rate_per_session()`

**Layer 3 — Drift Detection** (src/entity/config_entity.py:162):
- Per-channel z-score of `|production_mean - baseline_mean| / baseline_std`
- z-score >= `drift_zscore_threshold=2.0` → channel drifted
- `min_drifted_channels_warn=2` channels → WARNING

**Failure modes**:
- Baseline file missing → Layer 3 silently skipped (WARNING log, not CRITICAL)
- Stale baseline (>90 days) → WARNING log only; no automated trigger
- `is_training_session=True` → comparison skipped (self-reference would always show no drift)

**Safeguards**: Baseline age guard (max_baseline_age_days=90). Layer 3 skip on missing baseline. Calibration temperature auto-loaded from Stage 11 output.

**WHY bucket**: Observability

**Evidence**:
- drift_zscore=2.0: EMPIRICAL_CALIBRATION (reports/THRESHOLD_CALIBRATION.csv — zero FAR at 2.0σ)
- 3-sigma rule: PAPER [REF_GAMA_DDM], [REF_PAGE_CUSUM]
- confidence_warn=0.60: EMPIRICAL_CALIBRATION (reports/THRESHOLD_CALIBRATION.csv)

---

### Stage 7 — Trigger Evaluation

**WHY**: Manual retraining decisions are slow and inconsistent. An automated trigger policy with multi-signal voting reduces false alarms while ensuring real drift episodes are caught.

**WHAT**: `src/components/trigger_evaluation.py` → `TriggerEvaluation.initiate_trigger_evaluation()`. Delegates to `src/trigger_policy.py:TriggerPolicyEngine.evaluate()`.

**HOW**: The **2-of-3 voting scheme** evaluates three dimensions:
1. **Confidence** (src/trigger_policy.py:230): mean_conf < `confidence_warn=0.55` → vote YES
2. **Temporal** (src/trigger_policy.py:320): flip_rate > `flip_rate_warn=0.25` → vote YES
3. **Drift** (src/trigger_policy.py:400): drift_zscore > `drift_zscore_warn=2.0` → vote YES

`_aggregate_signals()` (line 470): Requires ≥ `min_signals_for_retrain=2` votes.

**Cooldown** (line 520): After triggering, `retrain_cooldown_hours=24` suppresses subsequent triggers.

**Output**: `TriggerDecision` with `should_retrain`, `action` (NONE/MONITOR/QUEUE_RETRAIN/TRIGGER_RETRAIN/ROLLBACK), `alert_level` (INFO/WARNING/CRITICAL).

**Failure modes**:
- Corrupted `trigger_state.json` → engine resets to defaults
- 24h cooldown can suppress legitimate cascading drift

**Safeguards**: State persistence with JSON. `consecutive_warnings` counter escalates from MONITOR → TRIGGER_RETRAIN.

**WHY bucket**: Reliability

**Evidence**: EMPIRICAL_CALIBRATION — reports/TRIGGER_POLICY_EVAL.csv shows 2-of-3 achieves precision=0.988, FAR=0.007, episode_recall=1.0 (500 simulated sessions, 16 drift episodes).

---

### Stage 8 — Model Retraining

**WHY**: When drift is detected, the model must be adapted to the new data distribution. Because production data is unlabeled, unsupervised adaptation methods (AdaBN, TENT) are required.

**WHAT**: `src/components/model_retraining.py` → `ModelRetraining.initiate_model_retraining()`. Dispatches to one of 5 strategies:
- `_run_adabn()` → BN statistics replacement (line 100)
- `_run_tent()` → BN affine param entropy minimization (line 160)
- `_run_adabn_then_tent()` → two-stage: AdaBN then TENT (line 230) **[recommended]**
- `_run_pseudo_label()` → confidence-filtered pseudo-labeling (line 310)
- `_run_standard()` → supervised retraining with labels (line 400)

**HOW (two-stage AdaBN+TENT)**:
1. Load pretrained model
2. AdaBN: Reset BN running stats → forward pass on target data (n_batches=10) → BN now calibrated to production distribution
3. TENT: Freeze all layers except BN gamma/beta → minimize prediction entropy on target data → OOD guard (skip if entropy > 0.85) → rollback guard (revert if entropy increases or confidence drops)

**Failure modes**:
- `mmd`/`dann` not implemented → `NotImplementedError` (line 68)
- AdaBN/TENT produce no `val_accuracy` (unsupervised) → Stage 9 registration gate has no metric to compare
- TENT divergence → rollback guard reverts to pre-TENT model

**Safeguards**: NotImplementedError guard. TENT rollback on entropy increase or confidence drop. BN running stats restored per TENT step to preserve AdaBN calibration.

**WHY bucket**: Reliability

**Evidence**: PAPER [REF_ADABN_PAPER], [REF_TENT_PAPER].

---

### Stage 9 — Model Registration

**WHY**: Retrained models must not replace deployed models without validation. A registration gate with proxy-based comparison protects against regressions.

**WHAT**: `src/components/model_registration.py` → `ModelRegistration.initiate_model_registration()`. Uses `src/model_rollback.py:ModelRegistry.register_model()`.

**HOW**:
1. Register new model version with SHA256 hash
2. Compare: `is_better = new_acc >= cur_acc - degradation_tolerance(0.005)` (model_registration.py:74)
3. If unsupervised (no `val_accuracy`): `block_if_no_metrics=False` → register but defer deployment
4. If `auto_deploy=True` AND `is_better=True` → deploy
5. Log REGRESSION warning if `is_better=False`

**Failure modes**:
- No prior version → always `is_better=True` (first registration passes automatically)
- AdaBN/TENT `val_accuracy=None` → gate deferred to manual deployment decision

**Safeguards**: `degradation_tolerance=0.005` absorbs training noise. `block_if_no_metrics` flag. SHA256 integrity hash. Deployment history tracking.

**WHY bucket**: Governance

**Evidence**: PROJECT_DECISION (degradation_tolerance=0.005 — tighter values caused false rejects in test, per reports/EVIDENCE_PACK_INDEX.md).

---

### Stage 10 — Baseline Update

**WHY**: After retraining, the drift baseline must be rebuilt from current labeled data. Otherwise, Stage 6 Layer 3 compares against a stale reference, causing spurious drift alerts.

**WHAT**: `src/components/baseline_update.py` → `BaselineUpdate.initiate_baseline_update()`. Delegates to `scripts/build_training_baseline.py:BaselineBuilder.build_from_csv()`.

**HOW**:
1. Load labeled CSV (data/all_users_data_labeled.csv)
2. Compute per-channel, per-class mean/std statistics
3. If `promote_to_shared=True` (`--update-baseline`): write to `models/normalized_baseline.json` + versioned archive
4. If `promote_to_shared=False` (default): write only to artifact directory (safe)

**Governance note**: Default `promote_to_shared=False` prevents silent baseline overwrites during experimentation. Production baseline updates require explicit `--update-baseline` flag.

**Failure modes**:
- Labeled CSV not found → `FileNotFoundError`
- Baseline NOT promoted (default) → monitoring drifts from stale reference indefinitely

**Safeguards**: Versioned archive on promote. MLflow artifact logging. Governance flag.

**WHY bucket**: Governance

**Evidence**: PROJECT_DECISION.

---

### Stage 11 — Calibration & Uncertainty Quantification

**WHY**: Neural networks with softmax produce overconfident predictions (Guo et al. 2017). Temperature scaling corrects this; MC Dropout provides epistemic uncertainty for OOD detection.

**WHAT**: `src/components/calibration_uncertainty.py` → `CalibrationUncertainty.initiate_calibration()`.

**HOW**:
1. Load model + inference probabilities
2. Fit temperature T via NLL minimization (initial T=1.5, scipy L-BFGS-B)
3. Apply temperature scaling to logits: `calibrated = softmax(logits / T)`
4. MC Dropout (30 forward passes): compute predictive entropy, mutual information, expected entropy
5. ECE evaluation (15 bins): expected calibration error + reliability diagram
6. Save `temperature.json` for Stage 6 to auto-load on subsequent runs

**Failure modes**:
- Missing probabilities .npy → approximate reconstruction from CSV confidence column
- No labels → temperature scaling uses unsupervised proxy

**Safeguards**: Fallback from .npy to .csv. Unsupervised proxy mode for unlabeled data.

**WHY bucket**: Reliability

**Evidence**: PAPER [REF_TEMP_SCALING], [REF_MC_DROPOUT].

---

### Stage 12 — Wasserstein Drift Detection

**WHY**: Z-score drift (Stage 6 Layer 3) detects mean shift but misses distributional shape changes (e.g., bimodality, tail expansion). Wasserstein-1 distance captures full distribution differences.

**WHAT**: `src/components/wasserstein_drift.py` → `WassersteinDrift.initiate_wasserstein_drift()`.

**HOW**:
1. Load baseline + production .npy arrays
2. Compute per-channel Wasserstein-1 distance
3. Integrated report: PSI + KS-test + Wasserstein with 2-of-3 consensus (wasserstein>0.3, KS p-value<0.01, PSI>0.10)
4. Change-point detection: rolling z-score CPD (window=50, threshold=2.0)
5. Multi-resolution analysis: window-level, hourly, daily

**Failure modes**:
- `baseline_X.npy` missing → returns `NO_BASELINE` status (no error)
- No auto-provisioning of baseline — must be created by Stage 10 or manually

**Safeguards**: Graceful `NO_BASELINE` status on missing reference data.

**WHY bucket**: Observability

**Evidence**: PAPER [REF_WASSERSTEIN].

---

### Stage 13 — Curriculum Pseudo-Labeling

**WHY**: When some labeled source data is available, progressive self-training with pseudo-labels can leverage both labeled and unlabeled data. EWC regularization prevents catastrophic forgetting of previously learned features.

**WHAT**: `src/components/curriculum_pseudo_labeling.py` → `CurriculumPseudoLabeling.initiate_curriculum_training()`.

**HOW**:
1. Load labeled source + unlabeled target data
2. Iteration 1: predict on unlabeled, accept pseudo-labels with confidence ≥ 0.95
3. Iteration 2–5: linearly decay threshold from 0.95 → 0.80
4. Each iteration: fine-tune model on source + pseudo-labeled data
5. EWC regularization (lambda=1000): penalize changes to weights important for source task
6. Teacher-student: EMA decay=0.999 for model averaging

**Failure modes**:
- Missing labeled data → empty artifact returned
- `ewc_lambda=1000` is a fixed hyperparameter — no ablation in codebase

**Safeguards**: Guard on labeled data existence. Empty artifact on failure.

**WHY bucket**: Reliability

**Evidence**: PAPER [REF_EWC_PAPER], [REF_PSEUDO_LABEL].
**P0 gap**: EWC lambda=1000 has no ablation artifact (GAP-EWC-01).

---

### Stage 14 — Sensor Placement Robustness

**WHY**: Garmin smartwatches can be worn on either wrist. Left/right hand placement causes systematic axis sign differences in accelerometer data. This stage detects dominant hand and evaluates axis-mirror augmentation.

**WHAT**: `src/components/sensor_placement.py` → `SensorPlacement.initiate_sensor_placement()`.

**HOW**:
1. Analyze dominant acceleration axis patterns to detect L/R hand
2. Apply axis-mirror augmentation (mirror_axes=[1,2,4,5], probability=0.5)
3. Report per-hand detection confidence

**Failure modes**:
- Production data not found → empty artifact
- `mirror_axes` indices out of range for non-6-channel data

**Safeguards**: Guard on data file existence.

**WHY bucket**: Reliability

**Evidence**: PROJECT_DECISION (sensor placement variability observed in pilot data).

---

## Cross-Cutting Concerns

### Training–Inference Parity

**Problem**: If training and inference use different preprocessing, the model sees a different distribution at inference time → silent quality degradation.

**How enforced in this repo**:
1. **Single preprocessing module**: `src/preprocess_data.py:UnifiedPreprocessor` used by both `src/train.py` and `src/components/data_transformation.py`.
2. **Config documentation**: `config/pipeline_config.yaml:1–16` explicitly states "Production preprocessing MUST match training preprocessing. Mismatch = domain shift = wrong predictions."
3. **Gravity removal guard**: `enable_gravity_removal=false` documented as mandatory because training data included gravity.
4. **Window size parity**: `src/config.py:67` defines `WINDOW_SIZE=200` used everywhere.

### Threshold Governance

**Problem**: Monitoring thresholds duplicated across Python config, Prometheus rules, and trigger policy → inconsistency causes missed alerts or false alarms.

**How enforced**:
1. **Single source of truth**: `src/entity/config_entity.py` dataclasses are the runtime SoT.
2. **Audit reference**: `config/monitoring_thresholds.yaml` documents all thresholds with alignment annotations.
3. **Automated consistency test**: `tests/test_threshold_consistency.py` verifies alignment between config_entity.py, trigger_policy.py, and Prometheus rules.
4. **Inline alignment comments**: `config/alerts/har_alerts.yml:1–30` documents which Python config each alert threshold maps to.

### Rollback Safety

**Problem**: Retrained models may perform worse than the incumbent. Without rollback, a bad model persists in production.

**How enforced**:
1. **Registration gate**: `degradation_tolerance=0.005` at src/entity/config_entity.py:253.
2. **Model registry**: `src/model_rollback.py:ModelRegistry` with version history and SHA256 hashing.
3. **TENT rollback**: src/domain_adaptation/tent.py — two-gate rollback (entropy increase OR confidence drop) reverts to pre-TENT model.
4. **Baseline governance**: `promote_to_shared=False` default prevents silent baseline corruption.
5. **MLflow model registry**: Tracks all model versions with metrics for audit.

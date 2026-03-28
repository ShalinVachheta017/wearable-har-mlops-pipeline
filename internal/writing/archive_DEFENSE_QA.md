# DEFENSE Q&A — Examiner Questions & Answers

> Anticipated examiner questions grouped by topic.
> Each answer has: Business Lens + Thesis Lens + Evidence pointer.
> Practice tip: Cover the "Answer" column and try answering from memory.

---

## Category 1: Architecture & Design

### Q1.1: "Why 14 stages? Isn't that over-engineered?"

**Answer:**
- Each stage maps to a specific MLOps responsibility (data quality, monitoring, triggering, etc.). Removing any stage creates a gap in the ML lifecycle.
- 14 stages ≠ 14 runs. The 3-phase grouping means a typical run executes 7 stages (Default). Retrain adds 3 more. Advanced analysis adds 4.
- Modular design enables: (1) independent testing per stage, (2) selective execution (`--stages monitoring,trigger`), (3) parallel development.
- **Business:** Each stage addresses a specific production risk. Stage 6 catches degradation; Stage 7 decides when to act; Stage 9 prevents deploying bad models.
- **Thesis:** Demonstrates incremental MLOps adoption — you don't need all 14 from day one.
- **Evidence:** REF_GOOGLE_MLOPS_CDCT (modular pipeline pattern), REF_CD4ML.

### Q1.2: "Why component/engine separation? It doubles the number of files."

**Answer:**
- Components are thin orchestrators (~63–139 lines): receive config, call engine, log artifacts to MLflow.
- Engines contain domain logic (~265–1345 lines): math, ML, data processing.
- This enables testing engines WITHOUT MLflow/pipeline setup (unit tests are fast).
- Follows "thin controller / fat service" pattern from web engineering.
- **Business:** Swap implementations (e.g., new drift detector) without touching orchestration.
- **Thesis:** Clean separation of concerns enables reproducible testing.

### Q1.3: "Why config dataclasses instead of YAML-only?"

**Answer:**
- Python dataclasses provide: type safety, IDE autocompletion, default values, docstrings.
- `config_entity.py` is the single source of truth for ALL thresholds (409 lines, 14 dataclasses).
- `pipeline_config.yaml` is a runtime toggle file for preprocessing flags only.
- `monitoring_thresholds.yaml` is an audit cross-reference, NOT runtime truth.
- **Verification:** `pytest tests/test_threshold_consistency.py` ensures all configs are aligned.
- **Thesis:** Config-driven architecture is a core MLOps pattern (REF_GOOGLE_MLOPS_CDCT).

---

## Category 2: Model & Training

### Q2.1: "Why 1D-CNN-BiLSTM and not a Transformer?"

**Answer:**
- CNN-BiLSTM is the established baseline for IMU-based HAR (REF_CNN_BILSTM_HAR, Ordóñez & Roggen 2016).
- 1D-CNN extracts local spatial features; BiLSTM captures temporal dependencies.
- ~499K parameters (v1) → runs on CPU; Transformers typically need >1M parameters.
- BatchNorm layers enable AdaBN domain adaptation — critical for this thesis.
- **Business:** CPU inference = lower deployment cost.
- **Thesis:** The contribution is the MLOps infrastructure, not the model architecture. Using an established architecture focuses the thesis on the pipeline.

### Q2.2: "Why window_size=200 and not 128 or 256?"

**Answer:**
- Empirical ablation: 6 configurations tested (see `reports/ABLATION_WINDOWING.csv`).
- ws=200 + overlap=50% → best F1 and accuracy.
- ws=128 (2.56s): insufficient temporal context for complex activities.
- ws=256 (5.12s): marginal gain (<0.5% F1), doubles memory, longer latency.
- 200 samples = 4 seconds at 50 Hz — captures complete activity cycles (REF_ABLATION_WINDOW, Banos et al. 2014).
- **Business:** 4s latency is acceptable for HAR; 5.12s adds noticeable delay.
- **Thesis:** This is a NUMBERS decision backed by EMPIRICAL data, not a METHODS decision.

### Q2.3: "Why z-score normalization and not MinMax?"

**Answer:**
- z-score (StandardScaler) is robust to outlier accelerometer spikes.
- MinMaxScaler compresses the entire range to [0,1] → single spike distorts all values.
- MUST match training normalization — config.json stores scaler parameters.
- **Business:** Consistent normalization = consistent predictions.
- **Evidence:** PROJECT_DECISION (validated during training).

### Q2.4: "Why 5-fold CV? Why not leave-one-subject-out (LOSO)?"

**Answer:**
- 5-fold is the standard in HAR literature (REF_CNN_BILSTM_HAR).
- ⚠️ GAP-LOSO-01: LOSO is acknowledged as future work. It would test cross-subject generalization.
- **Honest limitation:** 5-fold CV may overestimate accuracy if subjects appear in both train and test folds.
- **Mitigation:** Domain adaptation (AdaBN/TENT) addresses cross-subject distribution shifts at inference time.

---

## Category 3: Monitoring & Triggering

### Q3.1: "How do you monitor without labels?"

**Answer:**
- 3-layer monitoring architecture in Stage 6:
  - **Layer 1 (Confidence):** Mean prediction confidence, % uncertain windows, per-window cutoff.
  - **Layer 2 (Temporal):** Transition rate — how often consecutive windows change class.
  - **Layer 3 (Drift):** Z-score of mean shift per sensor channel vs. training baseline.
- No labels needed: all metrics derived from prediction distributions and raw sensor statistics.
- **Business:** Production HAR data is unlabeled — users don't annotate their activities.
- **Thesis:** Core contribution — novel 3-layer labelless monitoring for HAR.
- **Evidence:** All 52 threshold combinations tested (REF_THRESHOLD_CSV).

### Q3.2: "Why confidence=0.60 for monitoring but 0.65 for trigger?"

**Answer:**
- Monitoring (0.60): early warning — "confidence is declining." Low cost of false alarm (just a dashboard alert).
- Trigger (0.65): retraining decision — higher threshold avoids false retrains (each costs GPU hours).
- **Business:** Monitoring is informational; triggering is actionable. Different stakes = different thresholds.
- **Thesis:** Dual-threshold design demonstrates awareness of operational vs. automated decision boundaries.

### Q3.3: "Why 2-of-3 voting and not just confidence?"

**Answer:**
- Empirical evaluation: 500 simulated sessions, 5 policy variants (REF_TRIGGER_EVAL).
- 2-of-3: F1=0.976, FAR=0.007 (1 false alarm per 143 sessions).
- Confidence-only: FAR=0.079 (11× worse).
- Any-of-3: FAR=0.042 (6× worse).
- All-of-3: Recall=0.893 (misses 11% of real degradation).
- **Business:** False retrains waste compute; missed retrains degrade user experience.
- **Thesis:** Systematic trigger policy evaluation is a contribution — most HAR papers don't address when to retrain.

### Q3.4: "Why z-score for drift and not PSI or KL divergence?"

**Answer:**
- Z-score: symmetric, interpretable (2.0 = 95th percentile), no binning required.
- PSI: requires discretization into bins — choice of bins affects result.
- KL divergence: asymmetric — KL(P||Q) ≠ KL(Q||P).
- Wasserstein distance (Stage 12) complements z-score with distributional view.
- **Business:** Z-score is explainable to non-ML stakeholders: "drift is 2.5 standard deviations from baseline."
- **Evidence:** EMPIRICAL_CALIBRATION (REF_THRESHOLD_CSV).

---

## Category 4: Domain Adaptation

### Q4.1: "Why AdaBN as the default adaptation method?"

**Answer:**
- Zero-label: only needs unlabeled target data.
- Fast: updates BatchNorm running stats in ~10 forward passes.
- Safe: doesn't modify model weights — only running mean/variance of BN layers.
- Reversible: original BN stats can be restored.
- **Business:** Production data is unlabeled → AdaBN is the only method that works out-of-the-box.
- **Thesis:** Demonstrates practical domain adaptation for HAR (REF_ADABN, Li et al. 2018).
- **Limitation:** ⚠️ GAP-ADABN-01: n_batches=10 is the paper default; no project-specific ablation.

### Q4.2: "Why EWC and not just L2 regularization?"

**Answer:**
- EWC (Elastic Weight Consolidation) regularizes weights proportional to their importance for the SOURCE task.
- L2 regularization treats all weights equally — may constrain important weights too little and unimportant weights too much.
- Fisher Information Matrix identifies which weights are critical for previous knowledge.
- **Business:** EWC prevents catastrophic forgetting during curriculum pseudo-labeling.
- **Thesis:** EWC enables continual learning across adaptation iterations (REF_EWC, Kirkpatrick et al. 2017).
- **Limitation:** ⚠️ GAP-EWC-01: λ=1000 is paper default; needs ablation.

### Q4.3: "What if pseudo-labels are wrong?"

**Answer:**
- Curriculum schedule starts conservative (τ=0.95 → only highest confidence pseudo-labels).
- Gradually relaxes to τ=0.80 over 5 iterations.
- Teacher-student EMA (decay=0.999) stabilizes predictions across iterations.
- EWC prevents catastrophic forgetting from noisy labels.
- Max 20 samples per class prevents class imbalance.
- If no samples above τ for a class → that class is skipped (safe behavior).
- **Limitation:** ⚠️ GAP-PSEUDO-01: pseudo-label error rate at τ=0.80 not measured against labeled ground truth.
- **Defense:** "Curriculum learning is a systematic mitigation. The τ schedule ensures early iterations use only high-confidence labels, and EWC protects against drift."

---

## Category 5: Infrastructure & DevOps

### Q5.1: "Why not Kubernetes instead of Docker Compose?"

**Answer:**
- Single-machine thesis project — Kubernetes adds operational complexity (etcd, control plane, networking) without benefit.
- Docker Compose orchestrates 7 services with one command: `docker compose up -d`.
- **Business:** Kubernetes makes sense for multi-node production; Docker Compose is right-sized for thesis scale.
- **Thesis:** Demonstrates containerization as MLOps practice; Kubernetes would be a deployment concern, not a thesis concern.

### Q5.2: "Why single-stage Docker builds?"

**Answer:**
- ⚠️ GAP-DOCKER-01: This is a known gap. Multi-stage builds would reduce image size (build deps not in final image).
- Current single-stage builds work correctly — the gap is efficiency, not correctness.
- **Defense:** "Acknowledged as future work. Multi-stage builds reduce image size but don't change pipeline behavior."

### Q5.3: "Why no API authentication?"

**Answer:**
- ⚠️ GAP-AUTH-01: Acknowledged. Thesis scope is MLOps pipeline, not production security.
- Adding JWT/API-key middleware is orthogonal to the MLOps contribution.
- **Defense:** "Authentication is a deployment concern. Adding it is straightforward (FastAPI has built-in OAuth2/JWT support) but doesn't contribute to the MLOps research."

### Q5.4: "Why Prometheus and not just logging?"

**Answer:**
- Prometheus provides: numeric metrics, time-series queries, alerting rules, histogram aggregation.
- Logging provides: text events, grep-based searching.
- ML monitoring needs NUMERIC metrics (confidence, latency, drift scores) → Prometheus is purpose-built.
- 8 custom alert rules detect model degradation automatically.
- **Business:** Alert before users notice degradation.
- **Thesis:** Demonstrates observability as MLOps practice (not just "print accuracy").

---

## Category 6: Evidence & Methodology

### Q6.1: "How did you calibrate your thresholds?"

**Answer:**
- `reports/THRESHOLD_CALIBRATION.csv`: 52 threshold combinations across 5 metrics.
- Grid search over: confidence (0.50–0.75), drift z-score (1.5–3.0), transition rate (0.25–0.60), uncertain % (20–40%).
- Evaluation metrics: false alarm rate, missed detection rate, median detection delay.
- **Business:** Thresholds tuned to minimize costly false alarms while catching real issues.
- **Thesis:** Every NUMBER is backed by EMPIRICAL data. Methods are backed by PAPERS.

### Q6.2: "What is your ML Test Score?"

**Answer:**
- ML Test Score (REF_ML_TEST_SCORE, Breck et al. 2017) is a rubric with levels 0–5.
- This pipeline demonstrates:
  - Level 0: Model code, training code, validation ✅
  - Level 1: Data validation (Stage 2) ✅
  - Level 2: Feature computation (Stage 3) ✅
  - Level 3: Monitoring (Stage 6) ✅
  - Level 4: Model deployment (Stage 9) ✅
  - Level 5 (partial): Continuous training (Stages 7–8) ✅, A/B test ❌
- **Limitation:** A/B testing (GAP-AB-01) would be Level 5 achievement.

### Q6.3: "What would you do differently if starting over?"

**Answer (honest):**
1. **LOSO CV from the start** — would prove cross-subject generalization early.
2. **Multi-stage Docker builds** — smaller images, better security practice.
3. **Full ablations for AdaBN/EWC/TENT parameters** — empirical evidence for all numbers.
4. **Labeled validation set for pseudo-labeling** — measure error rate at each τ threshold.
5. **API authentication** — even if out of scope, it's a quick win.
6. **Tests for all 14 stages** — Stage 1, 4, 5 tests missing.

---

## Category 7: Scalability & Real-World Deployment

### Q7.1: "How would this work in production with 1000 users?"

**Answer:**
- FastAPI is async — handles concurrent requests out of the box.
- Docker Compose → Docker Swarm or Kubernetes for horizontal scaling.
- Prometheus handles multi-instance scraping natively.
- Model versioning via MLflow supports A/B rollout.
- Trigger policy cooldown prevents retrain storms across users.
- **Thesis:** Architecture is designed for single-user thesis scale but structurally scalable.

### Q7.2: "How does this transfer to fraud detection?"

**Answer:**
- Replace Stage 1 (sensor ingestion) with transaction ETL.
- Replace model (1D-CNN-BiLSTM → gradient boosting or DNN).
- Stage 6 monitoring works: confidence-based, no labels needed (fraud labels are delayed).
- Stage 7 trigger: replace temporal flip with fraud-rate spike.
- Stages 11–14 (calibration, Wasserstein, pseudo-labeling, sensor) → calibration and Wasserstein transfer directly; pseudo-labeling for delayed labels; sensor placement irrelevant.
- **Evidence:** REF_LABELLESS_DRIFT_FRAUD.

### Q7.3: "How does this transfer to industrial IoT?"

**Answer:**
- Replace Stage 1 with OPC-UA/MQTT connector.
- Model: 1D-CNN or TCN for vibration data.
- Monitoring: drift on vibration spectrum instead of acceleration.
- Sensor placement (Stage 14): multi-sensor positioning on machinery.
- Labels are scarce (failure events are rare) → pseudo-labeling valuable.
- **Evidence:** REF_PREDICTIVE_MAINT.

---

## Category 8: Honest Limitations

### Q8.1: "What are the main limitations of this work?"

**Answer (structured):**

| # | Limitation | Impact | Mitigation |
|---|---|---|---|
| 1 | No LOSO CV | Cross-subject generalization unproven | Domain adaptation addresses this at inference |
| 2 | Paper-default hyperparameters (AdaBN, EWC, TENT) | May not be optimal for this dataset | Methods are from peer-reviewed papers; numbers are reasonable priors |
| 3 | Pseudo-label error rate unmeasured | Could inject noise at τ=0.80 | Curriculum schedule + EWC protect against this |
| 4 | Single-stage Docker builds | Larger images | Correctness unaffected; efficiency gap |
| 5 | No A/B testing | Cannot compare models on live traffic | Model registry supports manual comparison |
| 6 | No API auth | Security gap | Out of thesis scope |
| 7 | Missing tests for 3 stages | Regressions in ingestion/inference/evaluation undetected | Integration test covers end-to-end |
| 8 | Single dataset | Generalization unproven | Architecture is domain-agnostic by design |

### Q8.2: "Why should we trust paper defaults for AdaBN n_batches, EWC λ, etc.?"

**Answer:**
- Papers justify METHODS: peer-reviewed validation that AdaBN/EWC/TENT work.
- Our data justifies NUMBERS where we have evidence: window sizes, thresholds, trigger policies.
- Paper defaults are reasonable priors: authors tested on similar problems.
- Full ablation for each parameter would be a separate paper.
- **Defense:** "We distinguish between method-level justification (paper) and number-level justification (empirical). Where numbers critically affect pipeline behavior (thresholds, window sizes, trigger policies), we ran our own experiments. Where they affect method internals (EWC λ, AdaBN n_batches), we use well-tested paper defaults and acknowledge the limitation."

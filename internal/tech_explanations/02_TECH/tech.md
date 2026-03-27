# HAR MLOps Thesis — Technical Terms (Easy Glossary)

**Purpose:** Simple explanations of the key technical terms used in this thesis project.  
For each term you get: **What**, **Where**, **When**, **How**, and **Input/Output**.

---

## A) Data & preprocessing terms

### Wearable sensor data (accelerometer, gyroscope)
- **What**: Time series signals from a wearable device.
  - Accelerometer: movement + gravity (units may differ by device).
  - Gyroscope: rotation / angular velocity.
- **Where used**: Data ingestion + preprocessing stages; also drift monitoring (distribution checks).
- **When used**: Before training and before inference (every time data arrives).
- **How used**: Read CSV → validate → clean → convert units → window → feed model.
- **Input**: Raw CSV with timestamps + sensor channels.  
- **Output**: Clean numeric arrays/windows ready for the model.

### Unit conversion (milliG ↔ m/s²)
- **What**: Fixing the sensor unit mismatch. Some devices store acceleration in **milliG**, while models often expect **m/s²**.
- **Where used**: Preprocessing step right after loading data.
- **When used**: Always, before windowing and inference/training.
- **How used**: Detect unit (heuristic / metadata) → convert → sanity check.
- **Input**: Raw acceleration channels.  
- **Output**: Acceleration channels in one consistent unit.

### Gravity removal
- **What**: Separating “real motion” from constant gravity (\(\approx 1g\)).
- **Where used**: Preprocessing before feature extraction / windowing (especially for accelerometer).
- **When used**: Before training and inference if the model expects gravity‑removed signals.
- **How used**: Common approaches:
  - High‑pass filter on accelerometer axes, or
  - Estimate gravity (low‑pass) and subtract it.
- **Input**: Accelerometer time series.  
- **Output**: Motion‑only accelerometer signal.

### Windowing (sliding windows)
- **What**: Split continuous time series into fixed‑length chunks (e.g., every 4 seconds).
- **Where used**: Preprocessing for training and inference.
- **When used**: After cleaning/normalization and before model inference.
- **How used**: Choose window length + stride → create window tensors.
- **Input**: Time series arrays.  
- **Output**: A batch of windows shaped like \([N, T, C]\) (windows, timesteps, channels).

### Data validation (schema/range/missing values)
- **What**: Checks to ensure input data is usable and safe.
- **Where used**: Data ingestion stage and/or API upload handler.
- **When used**: Every time new data arrives.
- **How used**: Validate columns, data types, ranges, missing values, timestamp order.
- **Input**: Raw uploaded CSV / parsed table.  
- **Output**: Pass/fail + a validated dataset (or error report).

---

## B) Model terms (HAR core)

### HAR (Human Activity Recognition)
- **What**: Predicting an activity class from wearable sensor windows (e.g., hand tapping, rest).
- **Where used**: Core ML model and evaluation.
- **When used**: Training (learn mapping) and inference (predict class per window).
- **How used**: Model takes sensor windows → outputs class probabilities → label.
- **Input**: Window tensor \([T, C]\) or \([N, T, C]\).  
- **Output**: Probabilities over classes + predicted label.

### 1D‑CNN‑BiLSTM (model architecture)
- **What**: A neural network for time series:
  - 1D‑CNN extracts local temporal patterns,
  - BiLSTM models longer dependencies in both directions.
- **Where used**: Training and inference model definition.
- **When used**: Always (it is the main HAR model).
- **How used**: Forward pass on windows to output class probabilities.
- **Input**: Windowed sensor signals.  
- **Output**: Softmax probability vector over activity classes.

### Softmax probabilities / confidence
- **What**: Softmax converts model scores into probabilities that sum to 1. “Confidence” is often the maximum probability.
- **Where used**: Inference outputs and monitoring layer 1.
- **When used**: After each inference window (or per session summary).
- **How used**: Use max probability as a confidence proxy; track mean confidence.
- **Input**: Model logits or scores.  
- **Output**: Probability distribution + confidence value.

### Temperature scaling (calibration)
- **What**: A post‑training method to make probabilities better calibrated by scaling logits with a temperature \(T\).
- **Where used**: After training, before monitoring thresholds that depend on confidence.
- **When used**: When you want calibration (reliable probabilities) for monitoring/decisions.
- **How used**: Fit \(T\) on validation → apply to logits → softmax.
- **Input**: Logits + validation labels (to fit \(T\)).  
- **Output**: Calibrated probabilities.

### ECE (Expected Calibration Error)
- **What**: A metric measuring how well predicted confidence matches true accuracy.
- **Where used**: Calibration evaluation (to justify confidence thresholds).
- **When used**: During model evaluation (requires labels).
- **How used**: Bin predictions by confidence → compare confidence vs accuracy.
- **Input**: Probabilities + true labels.  
- **Output**: Single calibration error number + reliability diagram (plot).

---

## C) Monitoring & drift terms (post‑inference)

### 3‑layer (multi‑signal) monitoring
- **What**: Monitoring system that checks model health using **multiple signals**, not just one drift detector.
- **Where used**: After inference (batch pipeline + API).
- **When used**: Each time a session/file is processed (or continuously in an online setting).
- **How used**: Compute several signals → compare to thresholds → raise WARNING/CRITICAL.
- **Input**: Model outputs + input feature summaries.  
- **Output**: Monitoring metrics + alerts + possible retrain trigger.

### Layer 1 — Uncertainty monitoring (confidence/entropy/% uncertain)
- **What**: Checks if the model is becoming unsure.
- **Where used**: Monitoring stage.
- **When used**: After inference windows/session.
- **How used**:
  - Track mean confidence, entropy.
  - Count “uncertain” predictions (below confidence threshold).
- **Input**: Softmax probabilities.  
- **Output**: Confidence/entropy metrics + uncertainty flags.

### Entropy (prediction uncertainty)
- **What**: A number that is high when probabilities are spread out (uncertain), low when one class dominates (confident).
- **Where used**:
  - Monitoring (Layer 1),
  - TENT adaptation objective (minimize entropy).
- **When used**: At inference time.
- **How used**: Compute entropy per prediction and aggregate.
- **Input**: Probability vector.  
- **Output**: Entropy score.

### Layer 2 — Temporal consistency (transition rate)
- **What**: Domain rule: humans usually do not switch activities every few seconds; too many switches can indicate trouble.
- **Where used**: Monitoring stage after window predictions.
- **When used**: Per session/file.
- **How used**: Count how often consecutive window labels change → compare to threshold.
- **Strict definition**: flip_rate(session) = (# label changes between adjacent windows in timestamp order) / (n_session_windows - 1). Aggregate across sessions with median/p95.
- **Input**: Sequence of predicted labels.  
- **Output**: Transition rate + flag if too high.

### Layer 3 — Drift detection (PSI / z‑score / Wasserstein / MMD)
- **What**: Detects distribution shift in sensor inputs or derived features.
- **Where used**: Monitoring stage.
- **When used**: Per session/file or periodic windows.
- **How used**: Compare “reference distribution” (training) vs “current distribution”.
- **Input**: Feature distributions from training + current data.  
- **Output**: Drift scores + drift flags.

### PSI (Population Stability Index)
- **What**: A binned distribution shift metric comparing reference vs current feature distributions.
- **Where used**: Drift monitoring (Layer 3).
- **When used**: When you want a simple, label‑free drift score.
- **How used**: Bin a feature → compare bin proportions → sum the differences.
- **Input**: Reference feature values + current feature values.  
- **Output**: PSI score (bigger = more shift).

### Z‑score drift
- **What**: Measures how far a current statistic is from the reference mean in standard deviations.
  \[
  z = \frac{x - \mu}{\sigma}
  \]
- **Where used**: Drift monitoring (Layer 3).
- **When used**: Fast check for unusual sensor/feature behaviour.
- **How used**: Compute \(x\) on current data (e.g., mean magnitude) and compare to reference \(\mu,\sigma\).
- **Input**: Reference mean/std + current statistic.  
- **Output**: z‑score (large |z| suggests drift).

### Wasserstein distance (drift detection)
- **What**: A distance between distributions (“how much you need to move the distribution”).
- **Where used**: Drift monitoring (Layer 3), often for continuous features.
- **When used**: When you want a stronger distribution distance than PSI for continuous signals.
- **How used**: Compute Wasserstein distance between reference and current feature distributions.
- **Input**: Reference samples + current samples.  
- **Output**: Distance value + thresholded drift flag.

### Synthetic drift injection
- **What**: Artificially modify clean data to simulate drift (scale, offset, noise, etc.).
- **Where used**: Threshold calibration experiments.
- **When used**: During evaluation to justify thresholds.
- **How used**: Apply controlled transformations → run monitors → check detection.
- **Input**: Clean dataset.  
- **Output**: Drifted dataset + detection results.

### Sensitivity analysis (threshold study)
- **What**: Systematically vary thresholds and measure outcomes (false alarms vs misses).
- **Where used**: Monitoring threshold justification.
- **When used**: If mentor expects deeper evaluation.
- **How used**: Sweep thresholds → compute detection metrics → plots/tables.
- **Input**: Data + range of thresholds.  
- **Output**: Curves/tables showing threshold trade‑offs.

### Trigger policy (e.g., “2‑of‑3 vote”)
- **What**: A rule for deciding when monitoring signals become a CRITICAL event.
- **Where used**: Monitoring → retrain decision logic.
- **When used**: After computing 3 layers.
- **How used**: Example: if at least 2 layers flag drift, then escalate.
- **Input**: Layer flags/metrics.  
- **Output**: WARNING/CRITICAL decision + trigger state update.

### Cooldown period
- **What**: A waiting time after a trigger to avoid repeated triggers.
- **Where used**: Trigger policy.
- **When used**: After retraining is triggered.
- **How used**: Store last trigger time → ignore triggers until cooldown ends.
- **Input**: Current time + last trigger time + cooldown length.  
- **Output**: Allow/deny new trigger.

### OOD detection (Out‑of‑Distribution)
- **What**: Detects inputs that are not like the training data (new device, corrupted signal, new behaviour).
- **Where used**: Monitoring (often before adaptation/retraining).
- **When used**: During inference on new sessions.
- **How used**: Compute an OOD score (energy, entropy, feature distance) → compare to threshold.
- **Input**: Model outputs and/or internal features.  
- **Output**: OOD score + OOD flag (and possibly “do not adapt on this data”).

---

## D) Adaptation & retraining terms (unlabeled + semi‑labeled)

### Test‑time adaptation (TTA)
- **What**: Adapt model using **test data**, often without labels, to handle domain shift.
- **Where used**: Inference path or an offline “adaptation run”.
- **When used**: When new user/device data differs from training.
- **How used**: Update some parameters or statistics using unlabeled target windows.
- **Input**: Pretrained model + target windows.  
- **Output**: Adapted model (temporary or saved) + predictions.

### AdaBN (Adaptive Batch Normalization)
- **What**: Update only BatchNorm running stats using target data; weights stay mostly fixed.
- **Where used**: TTA stage (before/with TENT).
- **When used**: Unlabeled target data is available.
- **How used**: Run forward passes with BN updating → new BN mean/variance.
- **Input**: Pretrained model + unlabeled target windows.  
- **Output**: Updated BN statistics (and sometimes improved predictions).

### TENT (Test‑time Entropy Minimization)
- **What**: Update selected parameters at test time by **minimizing prediction entropy** (no labels).
- **Where used**: TTA stage after model is deployed or during an offline adaptation run.
- **When used**: When you want stronger adaptation than AdaBN, but still unlabeled.
- **How used**: For each target batch: compute entropy → gradient step → repeat.
- **Input**: Pretrained model + unlabeled target windows.  
- **Output**: Slightly updated model parameters + hopefully more confident predictions.

### Pseudo‑labeling
- **What**: Create “fake labels” from high‑confidence predictions, then retrain as if they were real labels.
- **Where used**: Offline retraining stage (not typically inside live API).
- **When used**: Many unlabeled target sessions exist and you can run training jobs.
- **How used**: Predict → filter by confidence → train on pseudo‑labels.
- **Input**: Unlabeled target windows + pretrained model.  
- **Output**: Pseudo‑labeled dataset + retrained model.

### Curriculum pseudo‑labeling
- **What**: Pseudo‑labeling in steps: start with easiest (highest confidence), then gradually include harder examples.
- **Where used**: Offline retraining stage (advanced).
- **When used**: When plain pseudo‑labeling is too noisy.
- **How used**: Schedule confidence threshold high → lower over rounds.
- **Input**: Unlabeled target data + model.  
- **Output**: Multiple rounds of pseudo‑labels + progressively adapted model.

### Self‑consistency filter
- **What**: A filter that keeps only examples where the model is “consistent” (e.g., agrees with a label, or stable across predictions).
- **Where used**: Data selection for pseudo‑label training or source‑data filtering.
- **When used**: When you want higher‑quality training data at the cost of discarding many samples.
- **How used**: Apply rule → keep subset → retrain.
- **Input**: Candidate windows + model predictions (and possibly true labels).  
- **Output**: Smaller but “cleaner” training set.

### Class collapse (rare classes disappear)
- **What**: In pseudo‑labeling, rare classes may never be selected (low confidence), so the model stops learning them and performance drops.
- **Where used**: Risk analysis for pseudo‑labeling and filters.
- **When used**: When dataset is small + imbalanced + pseudo‑labels dominate.
- **How used**: Detect via per‑class recall trends; mitigate with class‑balanced sampling or thresholds.
- **Input**: Training data distribution + selected pseudo‑labels.  
- **Output**: Warning about bias + mitigation plan/experiment.

### DANN (Domain‑Adversarial Neural Network)
- **What**: Domain adaptation method that learns features that are good for classification and also “confuse” a domain classifier.
- **Where used**: Training‑time domain adaptation (more complex than AdaBN/TENT).
- **When used**: If you have source labels and target unlabeled data during training.
- **How used**: Add domain classifier + gradient reversal → train jointly.
- **Input**: Labeled source + unlabeled target.  
- **Output**: Domain‑invariant feature extractor + adapted classifier.

### MMD (Maximum Mean Discrepancy)
- **What**: Kernel distance between distributions; often used as a penalty to align source and target features.
- **Where used**: Domain adaptation (training‑time), or drift detection (monitoring‑time).
- **When used**: If you want a statistically grounded “two‑sample test / distance”.
- **How used**: Compute MMD between feature batches → minimize it (adaptation) or threshold it (drift detection).
- **Input**: Feature samples from reference and current/target.  
- **Output**: Distance score (and possibly gradient signal if used as loss).

---

## E) Evaluation terms (how we report results)

### Window‑level split vs subject‑wise split
- **What**:
  - Window‑level split mixes windows from same person into train and test (optimistic).
  - Subject‑wise split keeps each person only in train or test (more realistic).
- **Where used**: Model evaluation strategy.
- **When used**: Before writing results tables.
- **How used**: Choose split method; run cross‑validation; report metrics.
- **Input**: Windows + labels + (if available) subject IDs.  
- **Output**: Fold metrics (accuracy, macro F1, per‑class recall).

### GroupKFold
- **What**: Cross‑validation that keeps all samples from the same “group” (subject) in the same fold.
- **Where used**: Subject‑wise evaluation.
- **When used**: When you have subject IDs.
- **How used**: Provide `groups=subject_id` to the split.
- **Input**: Data + labels + subject IDs.  
- **Output**: Train/test splits with no subject leakage.

### LOSO (Leave‑One‑Subject‑Out)
- **What**: Strong subject‑wise evaluation: each fold tests on one subject, trains on all others.
- **Where used**: HAR evaluation best practice.
- **When used**: When number of subjects is not too large and you want strict generalization.
- **How used**: For each subject: train on others → test on that subject.
- **Input**: Data + labels + subject IDs.  
- **Output**: Per‑subject test results + aggregated metrics.

### Macro F1
- **What**: F1 score averaged equally across classes (good for imbalanced datasets).
- **Where used**: Main HAR metric in results tables.
- **When used**: Reported for each experiment and each split.
- **How used**: Compute per‑class F1 → average.
- **Input**: True labels + predicted labels.  
- **Output**: Macro F1 number.

### Per‑class recall
- **What**: For each activity class, how many true samples were correctly detected.
- **Where used**: To show performance on rare behaviours.
- **When used**: In results section and error analysis.
- **How used**: Compute recall for each class.
- **Input**: True labels + predicted labels.  
- **Output**: Recall per class + table/plot.

---

## F) MLOps / system terms

### FastAPI
- **What**: Python web framework for building an inference API.
- **Where used**: Online inference service (upload CSV → get predictions + monitoring results).
- **When used**: When running the system as a service instead of just scripts.
- **How used**: Endpoint receives file → runs pipeline steps → returns JSON output.
- **Input**: HTTP request + uploaded CSV.  
- **Output**: JSON with predictions + monitoring metrics/flags.

### Docker
- **What**: Container packaging for reproducible environments.
- **Where used**: Running training/inference stack consistently; CI builds.
- **When used**: Development + CI + demos.
- **How used**: Build image → run container → same dependencies everywhere.
- **Input**: Dockerfile + code + requirements.  
- **Output**: Container image.

### MLflow (experiment tracking)
- **What**: Tool to log experiments: parameters, metrics, artifacts, model files.
- **Where used**: Training and evaluation runs.
- **When used**: Every training/adaptation experiment you want to reproduce.
- **How used**: Log metrics per run; optionally register models.
- **Input**: Run metadata + metrics + artifacts.  
- **Output**: Traceable experiment history.

### DVC (data version control)
- **What**: Version control for datasets/large artifacts alongside Git.
- **Where used**: Managing raw/processed data and big artifacts.
- **When used**: When data changes and you need reproducibility.
- **How used**: Track files with DVC; push/pull from remote storage.
- **Input**: Data files + `dvc.yaml`/`dvc.lock` tracking.  
- **Output**: Versioned data + reproducible pipeline stages.

### Prometheus + Grafana
- **What**:
  - Prometheus collects time‑series metrics from running services.
  - Grafana visualizes dashboards and alerts.
- **Where used**: Live system monitoring (API health, drift signals over time).
- **When used**: When you run a continuous service and want dashboards.
- **How used**: API exposes `/metrics` → Prometheus scrapes → Grafana dashboard.
- **Input**: Exported metrics.  
- **Output**: Dashboards + alerts.

### Model registry / model promotion
- **What**:
  - Registry stores model versions and metadata.
  - Promotion sets which model is “current/production”.
- **Where used**: Deployment governance (even in a PoC).
- **When used**: After training/adaptation and evaluation.
- **How used**: Register artifact + metrics → decide “better” → promote.
- **Input**: Model artifact + metrics + version metadata.  
- **Output**: Updated “current model” pointer/version.

### Blue‑green / canary deployment (concept)
- **What**: Safe deployment strategies:
  - Blue‑green: switch traffic from old to new quickly.
  - Canary: send small % to new model first.
- **Where used**: Deployment design section / optional implementation.
- **When used**: When discussing production‑readiness and rollback.
- **How used**: Route traffic between versions; monitor; rollback if needed.
- **Input**: Two model versions + routing logic.  
- **Output**: Safer release + rollback path.

---

## G) Thesis scope terms

### Proof‑of‑concept (PoC) vs production‑grade
- **What**:
  - PoC: shows the full idea works end‑to‑end with clear design choices.
  - Production‑grade: hardened reliability, security, scaling, full automation.
- **Where used**: Thesis scope decisions and “limitations/future work”.
- **When used**: To justify why some parts are designed but not fully built (e.g., full CI/CD retrain loop).
- **How used**: Be explicit: what is implemented, what is designed, what is future work.
- **Input**: Your system components + evaluation evidence.  
- **Output**: Clear scope statement that examiners can accept.

### “Must be finished” vs “future work”
- **What**: Decision of what you complete before submission vs what you only describe.
- **Where used**: Thesis planning and mentor decision questions.
- **When used**: Before finalizing experiments and thesis chapters.
- **How used**: Mark items as “must‑have” (results included) vs “future work” (design described).
- **Input**: Project timeline + exam deadlines + mentor guidance.  
- **Output**: Final thesis scope checklist.

---

## Quick “map” (where each term usually appears)

- **Preprocessing**: units, gravity removal, windowing, validation  
- **Model**: 1D‑CNN‑BiLSTM, softmax, calibration (temperature/ECE)  
- **Monitoring**: 3 layers, PSI/z‑score/Wasserstein, triggers, cooldown, OOD  
- **Adaptation**: AdaBN, TENT, pseudo‑labeling, curriculum, self‑consistency  
- **Evaluation**: GroupKFold/LOSO, macro F1, per‑class recall  
- **MLOps**: FastAPI, Docker, MLflow, DVC, Prometheus/Grafana, registry, deployment patterns

## H) Pipeline stages (simple view)

This is a simple stage‑by‑stage map of how the pipeline works and where the terms are used.

### Stage 1 — Data ingestion
- **What happens**: Load raw CSV files or API uploads from the wearable.
- **Where**: Data ingestion script + FastAPI endpoint.
- **When**: As soon as new data arrives (offline or online).
- **How**: Read CSV → basic checks → pass to validation.
- **Input**: Raw accelerometer/gyroscope CSV.  
- **Output**: Parsed tables (dataframe‑like) ready for validation.

### Stage 2 — Data validation & unit handling
- **What happens**: Check columns, ranges, missing values; detect and fix units.
- **Where**: Validation part of the pipeline/API.
- **When**: Right after ingestion, before any ML work.
- **How**: Validate schema → check value ranges → detect milliG vs m/s² → convert → optional gravity sanity check.
- **Input**: Parsed raw data.  
- **Output**: Cleaned data in one consistent unit (or an error).

### Stage 3 — Preprocessing & windowing
- **What happens**: Turn clean time series into fixed‑length windows.
- **Where**: Preprocessing stage.
- **When**: After validation, before feeding the model.
- **How**: (Optional) gravity removal → resample → normalize → create sliding windows of length T with stride S.
- **Input**: Clean sensor time series.  
- **Output**: Window tensors \([N, T, C]\) ready for the HAR model.

### Stage 4 — HAR model inference
- **What happens**: Predict activities for each window.
- **Where**: Model inference code (script + FastAPI).
- **When**: During evaluation and during API calls.
- **How**: Load 1D‑CNN‑BiLSTM → run forward pass → apply softmax → get class probabilities and labels.
- **Input**: Window tensors.  
- **Output**: Per‑window probability vectors + predicted labels.

### Stage 5 — Calibration (optional)
- **What happens**: Make probabilities better match real accuracy.
- **Where**: Evaluation/calibration step.
- **When**: After training (to fit temperature), then reused during inference.
- **How**: Fit temperature \(T\) on validation data → apply to logits → softmax → compute ECE.
- **Input**: Logits + validation labels (for fitting).  
- **Output**: Calibrated probabilities used by monitoring.

### Stage 6 — Per‑session aggregation
- **What happens**: Summarize window‑level outputs for one session.
- **Where**: Post‑processing stage.
- **When**: After inference on all windows of a file/session.
- **How**: Build label sequence, count time per class, compute transitions, session statistics.
- **Input**: Window predictions for one session.  
- **Output**: Session summary features (label sequence, histograms, etc.).

### Stage 7 — 3‑layer monitoring
- **What happens**: Check model health with three types of signals.
- **Where**: Monitoring module called by pipeline and API.
- **When**: After each session/file (or over rolling windows).
- **How**:  
  - Layer 1: mean confidence, entropy, % uncertain.  
  - Layer 2: activity transition rate using adjacent windows in timestamp order per session; report median/p95 across sessions.  
  - Layer 3: PSI / z‑score / Wasserstein / (optional MMD) on features.
- **Input**: Probabilities, labels, feature summaries.  
- **Output**: Monitoring metrics + per‑layer OK/WARNING/CRITICAL flags.

### Stage 8 — Trigger policy & trigger state
- **What happens**: Decide if we only log a warning or actually trigger retraining.
- **Where**: Trigger policy logic (often using a JSON state file).
- **When**: After monitoring metrics are computed.
- **How**: Apply rules (e.g. “2 of 3 layers fired”) + check cooldown → update trigger_state.json.
- **Input**: Layer flags/metrics + previous trigger state.  
- **Output**: New trigger state and (maybe) a retrain signal.

### Stage 9 — Logging & tracking
- **What happens**: Save what happened so we can reproduce and analyze later.
- **Where**: MLflow + logs + DVC.
- **When**: For every important run (training, adaptation, monitoring experiments).
- **How**: Log metrics and parameters in MLflow; track data/models with DVC; store monitoring outputs.
- **Input**: Metrics, parameters, artifacts, data files.  
- **Output**: Full experiment history and versioned data/models.

### Stage 10 — Supervised retraining (labeled data)
- **What happens**: Train or fine‑tune the HAR model using labeled data.
- **Where**: Training pipeline.
- **When**: When new labeled data arrives or to build a strong baseline.
- **How**: Use GroupKFold/LOSO; compute macro F1 + per‑class recall; optionally run small HPO (grid/Optuna) on key hyperparameters.
- **Input**: Labeled windows + base model.  
- **Output**: New supervised model version with evaluation metrics.

### Stage 11 — Test‑time adaptation (AdaBN, TENT)
- **What happens**: Adapt the model on unlabeled target data.
- **Where**: Adaptation module (offline run or during deployment).
- **When**: When domain shift is detected and labels are not available.
- **How**:  
  - AdaBN: update BatchNorm stats with new data.  
  - TENT: make small gradient steps to reduce entropy on target batches (often on BN affine params).
- **Input**: Pretrained model + unlabeled target windows.  
- **Output**: Adapted model (BN stats and/or weights).

### Stage 12 — Advanced drift metrics (optional)
- **What happens**: Compute stronger drift distances for analysis.
- **Where**: Advanced monitoring stage (usually behind an `--advanced` flag).
- **When**: In research/ablation runs or future work.
- **How**: Compute Wasserstein distance or MMD between training and target feature distributions; compare to thresholds.
- **Input**: Feature samples from reference and target.  
- **Output**: Extra drift scores and plots.

### Stage 13 — Curriculum pseudo‑labeling (offline adaptation)
- **What happens**: Use high‑confidence predictions as pseudo‑labels and retrain in several rounds.
- **Where**: Advanced adaptation stage (offline, not in the live API).
- **When**: When you have many unlabeled target sessions and enough time for retraining.
- **How**: Predict on target → keep high‑confidence windows (with self‑consistency filter) → retrain model → optionally lower confidence threshold in next round.
- **Input**: Unlabeled target sessions + base model.  
- **Output**: Model adapted using pseudo‑labels.

### Stage 14 — Sensor placement / robustness analysis
- **What happens**: Check how well the model and monitoring work if the sensor position/orientation changes.
- **Where**: Evaluation / analysis section (often advanced/future work).
- **When**: When studying robustness beyond the main test setup.
- **How**: Use sessions with different placements or simulate mirrored/rotated signals → run pipeline → compare metrics and drift signals.
- **Input**: Data with different or simulated placements.  
- **Output**: Robustness metrics and discussion in the thesis.

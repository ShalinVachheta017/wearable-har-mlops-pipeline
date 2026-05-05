# Unlabeled Data, Model Improvement, and Governance Guide

Date: 2026-04-26

Purpose: reusable internal note for thesis writing, defense preparation, and pipeline hardening. This is not itself a thesis citation source. Use the primary sources listed at the end when writing thesis prose.

## 1. Core Answer

Unlabeled production data can improve the pipeline and can help produce candidate model updates, but it cannot by itself prove that the model is more accurate.

With unlabeled data, the pipeline can measure whether the data and model behavior look suspicious:

- data quality
- sensor validity
- timestamp and synchronization quality
- input drift
- feature drift
- prediction drift
- confidence drift
- entropy and top-2 margin
- temporal consistency
- out-of-distribution behavior

With unlabeled data, the pipeline cannot directly measure:

- true accuracy
- true macro F1
- true per-class recall
- true precision
- confusion matrix
- true production calibration error
- whether a retrained model is genuinely better than the defended model

Those metrics require ground-truth labels (`y_true`). For thesis writing, this distinction must stay explicit.

## 2. What We Can Legitimately Do With Unlabeled Data

### 2.1 Predict

The defended runtime model can predict an activity class for every valid window. For each window, save:

- `window_id`
- source file or session id
- start and end timestamp
- model version
- input contract version (raw physical units for final production inference)
- effective sampling rate
- predicted class
- top class probability
- top-2 class and probability
- entropy
- top-1/top-2 margin
- processing status

These are predictions and confidence signals, not proof of correctness.

### 2.2 Monitor Input and Sensor Behavior

For accelerometer and gyroscope channels, track:

- missing values
- duplicate timestamps
- timestamp gaps
- invalid values
- min, max, mean, standard deviation
- robust z-score shifts
- clipping or saturation
- spike rate
- zero rate
- accelerometer magnitude
- gyroscope magnitude

This is especially important when one gyro axis is much larger than the baseline. A severe axis shift should trigger data QA before retraining.

### 2.3 Monitor Prediction Behavior

Track prediction-side proxy metrics:

- predicted class distribution
- dominant-class percentage
- number of unique predicted classes
- mean confidence
- low-confidence ratio
- entropy
- top-2 margin
- class-switch rate
- average predicted activity duration

These can reveal collapse or unstable behavior, but they still do not prove real accuracy.

### 2.4 Detect Drift or OOD Behavior

Legitimate unlabeled drift/OOD signals include:

- per-channel z-score mean shift
- KS test or Wasserstein distance where implemented
- MMD for offline calibrated audit runs
- Mahalanobis or embedding distance if wired later
- confidence/entropy OOD proxies
- prediction distribution shift

Interpretation rule: drift is a warning, not proof that the model is wrong.

### 2.5 Select Samples for Manual Labeling

Active learning is the most practical way to turn unlabeled data into real improvement. Export windows for labeling when they are:

- low confidence
- high entropy
- small top-2 margin
- high OOD/drift score
- rare predicted class
- unstable over time
- from suspicious gyro-axis sessions

After labels are added, the same windows can support true accuracy/F1/recall and model promotion decisions.

### 2.6 Produce Candidate Adaptation Models

Unlabeled data can produce candidate models through:

- AdaBN: adapt batch-normalization statistics to a target domain
- TENT: test-time entropy minimization
- pseudo-labeling: train on high-confidence predicted labels
- future work: CORAL/MMD alignment, self-supervised learning, contrastive learning

These methods can be useful, but they remain candidate mechanisms until validated with labels.

## 3. What We Should Not Claim

Do not write:

- "Production accuracy improved" unless labeled production data exist.
- "The retrained model is better" unless a labeled holdout shows it.
- "Pseudo-labeling proved the model improved" without labeled confirmation.
- "Drift means the model is wrong."
- "High confidence means correct."

Safer thesis wording:

> The unlabeled production stream is used for operational monitoring, drift detection, uncertainty analysis, and candidate selection. Model improvement is only claimed when a labeled validation or production sample confirms that the candidate outperforms the defended runtime model.

## 4. Current Repo Support

### Stage 6 Monitoring

Current monitoring thresholds are in `src/entity/config_entity.py`.

Important defaults:

- mean confidence warning below `0.70`
- uncertain-window percentage warning above `20%`
- dominant-class warning at `85%`
- dominant-class critical at `95%`
- transition-rate warning above `35%`
- drift z-score warning above `1.8`

This is an early-warning layer for unlabeled production data.

### Stage 7 Trigger Policy

Current trigger logic is in `src/trigger_policy.py`.

Important defaults:

- confidence warning below `0.65`
- confidence critical below `0.50`
- entropy warning above `1.8`
- entropy critical above `2.2`
- drift warning above `2.0`
- drift critical above `3.0`
- 2 or more warning signals can queue review and labeling work
- 3 consecutive warnings can escalate to review, not automatic retraining
- 24-hour cooldown blocks rapid repeated retraining

The collapse guard is especially important. Dominant-class collapse returns `REVIEW`, not blind retraining. Unlabeled production drift, collapse, or low confidence must not mutate the model until labels, QA, and promotion criteria are available.

### Stage 8 Retraining and Adaptation

Current adaptation methods are configured in `ModelRetrainingConfig`:

- `none`
- `adabn`
- `tent`
- `adabn_tent`
- `pseudo_label`

Pseudo-labeling in `src/train.py` already uses:

- confidence gate
- entropy gate
- class-balanced selection
- soft labels
- rollback metadata

For thesis safety, pseudo-labeling should remain candidate-only unless labeled evaluation proves improvement.

### Stage 9 Registration and Promotion

Current registration logic is in `src/components/model_registration.py`.

Key point:

- registering a candidate is not the same as promoting it
- `auto_deploy` is false by default
- deployment requires the deploy gate
- strict mode should block deployment when accuracy metrics are absent

Recommended defense posture:

> Unsupervised candidates may be registered for lineage, but they are not promoted to defended runtime status without labeled evidence.

## 5. Recommended Governance States

Use these states in reports and defense explanations:

| State | Meaning | Example condition |
|---|---|---|
| `NONE` | System healthy | Confidence/drift/temporal signals normal |
| `MONITOR` | One warning signal | Mild drift or mild confidence drop |
| `REVIEW` | Suspicious but not safe to retrain | Dominant-class collapse, severe gyro-axis anomaly, preprocessing concern |
| `QUEUE_RETRAIN` | Review/label queue, not immediate deploy | 2 or more warning signals, cooldown active, or waiting for labels |
| `TRIGGER_RETRAIN` | Candidate generation allowed only after governance gates | Critical evidence plus labels/QA/review approval |
| `REGISTER_CANDIDATE` | Candidate stored for lineage | AdaBN/TENT/pseudo-label/supervised candidate created |
| `PROMOTE` | Candidate becomes defended runtime model | Labeled holdout confirms improvement over current defended model |
| `REJECT_OR_ARCHIVE` | Candidate kept but not used | Missing labels, worse metrics, unstable behavior, or no proof of improvement |

## 6. Conditions for Model Improvement

### 6.1 Strongest Condition: Labeled Production Sample

Promotion is justified when:

- production-like labeled sample exists
- current defended model is evaluated on it
- candidate model is evaluated on the same sample
- candidate improves chosen metrics
- no critical class regresses
- preprocessing contract is identical or explicitly justified
- model registry records the decision

Recommended metrics with labels:

- macro F1
- per-class recall
- confusion matrix
- accuracy
- calibration if probability quality matters

### 6.2 Acceptable Thesis Condition: Candidate Generated but Not Promoted

If labels are missing, the correct behavior is:

- run monitoring
- generate candidate only when policy allows
- register candidate as evidence
- do not promote
- explain that governance protected the defended baseline

This is the current Option A story.

### 6.3 Weak Condition: Unlabeled Proxy Improvement

Unlabeled proxy improvement can support investigation, not promotion.

Example:

- entropy decreases
- confidence improves
- OOD score decreases
- prediction distribution becomes less collapsed
- temporal stability improves

This can justify "candidate appears operationally better under proxy metrics", but not "candidate is more accurate."

## 7. Practical Pipeline Improvements To Consider

### PT-1 Window-Level Evidence Schema

Create or verify a per-window log with:

- `window_id`
- file/session id
- start/end time
- model version
- scaler version
- effective sampling rate
- per-axis stats
- predicted class
- class probabilities
- confidence
- entropy
- top-2 margin
- drift/OOD score
- processing status

### PT-2 Synchronization QA Artifact

Save an artifact for accel/gyro fusion:

- match rate
- mean timestamp delta
- max timestamp delta
- dropped rows
- missing synchronized rows
- effective sampling rate after resampling

This should become Ch4/Ch5 evidence if clean.

### PT-3 Gyro-Axis Drift Quarantine

If one gyro axis is extreme:

1. quarantine the session
2. check units
3. check axis mapping
4. check clipping/saturation
5. check calibration
6. check timestamp alignment
7. check wearing position
8. run ablations only after QA

Useful ablations:

- all channels
- accelerometer only
- gyroscope only
- all channels except suspicious gyro axis
- clipped/normalized suspicious axis

### PT-4 Strict Pseudo-Label Governance

Pseudo-label acceptance should require:

- high confidence
- low entropy
- low OOD score
- temporal stability
- class-balance control
- no severe sensor QA failure

Recommended thesis stance:

> Pseudo-labeling is implemented as an experimental candidate-generation path. It is not used to promote the defended runtime model without labeled validation.

### PT-5 Monitoring Report Completeness

Final monitoring evidence should include:

- data quality
- sampling rate
- unit conversion and input-contract provenance
- synchronization QA
- raw-axis drift
- magnitude drift
- prediction distribution
- confidence distribution
- entropy/top-2 margin
- temporal consistency
- OOD/drift status
- recommended action

## 8. Thesis Placement

Use this mapping:

| Thesis area | What to use from this note |
|---|---|
| Ch4 Methodology | unlabeled-data boundary, preprocessing QA, synchronization, window logging |
| Ch5 Implementation | Stage 6/7 monitoring and trigger implementation, registry/promotion gate |
| Ch6 Results | governance matrix, monitoring reports, candidate artifacts, no-promotion decision |
| Ch7 Discussion | why unlabeled data warns but does not confirm performance |
| Ch8 Future work | active learning, labeled production sample, self-supervised learning, stronger OOD |

## 9. Primary Sources To Cite In Thesis

Use these sources directly rather than citing `pt.md`.

- Google Cloud Architecture Center, "MLOps: Continuous delivery and automation pipelines in machine learning"  
  https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning

- Sculley et al. (2015), "Hidden Technical Debt in Machine Learning Systems", NeurIPS  
  https://papers.neurips.cc/paper_files/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html

- Gama et al. (2014), "A survey on concept drift adaptation", ACM Computing Surveys  
  https://researchportal.helsinki.fi/en/publications/a-survey-on-concept-drift-adaptation/

- Sohn et al. (2020), "FixMatch: Simplifying Semi-Supervised Learning with Consistency and Confidence", NeurIPS  
  https://papers.nips.cc/paper/2020/hash/06964dce9addb1c5cb5d6e3d9838f733-Abstract.html

- Li et al. (2016), "Revisiting Batch Normalization For Practical Domain Adaptation"  
  https://arxiv.org/abs/1603.04779

- Wang et al. (2020/2021), "Tent: Fully Test-time Adaptation by Entropy Minimization"  
  https://arxiv.org/abs/2006.10726

- Sun and Saenko (2016), "Deep CORAL: Correlation Alignment for Deep Domain Adaptation"  
  https://arxiv.org/abs/1607.01719

- scikit-learn documentation for supervised metrics requiring ground truth:
  - accuracy: https://sklearn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html
  - F1: https://sklearn.org/stable/modules/generated/sklearn.metrics.f1_score.html

## 10. One-Sentence Defense Answer

Unlabeled production data can make the pipeline more robust by detecting drift, uncertainty, OOD behavior, and preprocessing problems, and it can generate candidate adaptations through AdaBN, TENT, or pseudo-labeling; however, it cannot prove true model improvement, so promotion of any candidate requires labeled validation against the defended runtime model.

# Thesis Consistency Notes

Purpose: lock a single, reproducible interpretation for thresholding, ablation config labels, runtime preprocessing, and adaptation framing.

## 1) Threshold Design (Monitoring vs Trigger)

Final design is tiered and explicit:

- Stage 6 monitoring warning threshold (mean confidence): `0.70`
- Stage 7 trigger warning threshold (mean confidence): `0.65`
- Stage 7 trigger critical threshold (mean confidence): `0.50`

Implementation alignment:

- `PostInferenceMonitoringConfig.confidence_warn_threshold = 0.70`
- `TriggerEvaluationConfig.confidence_warn = 0.65`
- `TriggerEvaluationConfig.confidence_critical = 0.50`
- `TriggerThresholds` defaults are aligned to `0.65 / 0.50`

Why: monitoring is an early warning layer; trigger evaluation is a governance gate.

## 2) Collapse Guard Rule

Stage 7 includes a collapse guard that returns `REVIEW` and blocks auto-retrain when collapse-like proxies are detected, including:

- `dominant_pct >= 95`
- Stage 4 `collapse_level == "CRITICAL_COLLAPSE"`
- Stage 6 `low_motion_collapse_risk == true`
- other configured collapse guard conditions in `src/trigger_policy.py`

This behavior is intentionally conservative for unlabeled production data.

## 3) Ablation Config A/B/C/D Definitions

Canonical source: `scripts/run_ablation_experiment.py`.

- Config A: `gravity_removal=False`, `calibration=False`
- Config B: `gravity_removal=False`, `calibration=True`
- Config C: `gravity_removal=True`, `calibration=False`
- Config D: `gravity_removal=True`, `calibration=True`

Any statement that says "Config D = calibration only (no gravity removal)" is incorrect for the current repository state. That definition corresponds to Config B.

## 4) AdaBN Framing

Adaptation is optional and not the default pipeline mode.

- CLI default remains `--adapt none`
- `ModelRetrainingConfig.adaptation_method` default is `none`
- AdaBN/TENT/pseudo-label options are explicit research modes

This keeps the baseline production story and adaptation experiments separated.

## 5) Default Model, Input Contract, and Promotion Gate

### 5.1 Canonical Sentence (Locked 2026-05-05)

> **Defended runtime model and input contract:** `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` (1D-CNN-BiLSTM, 11 activity classes, 499 131 parameters, 200x6 input window). Final production inference uses raw physical IMU units: accelerometer values are converted from milli-g to m/s^2 when needed, gyroscope values remain in deg/s, sampling is 50 Hz, window size is 200 samples, stride is 100 samples, normalization is disabled, no external StandardScaler is applied, and gravity removal/calibration are disabled. Stage 6 compares against `models/raw_physical_baseline.json`; normalized/scaler artifacts remain training, legacy, or A-B diagnostic evidence only. Retraining is implemented as a **governance mechanism** that produces candidate artifacts (`models/retrained/`); promotion is label-gated and requires review, QA, labels, and demonstrated improvement on a labeled holdout. The production data stream is unlabeled, so drift/collapse/low confidence can require review but must not automatically replace the defended model.

### 5.2 Rules

- Default runtime model is the supervisor-provided pretrained baseline: `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`.
- Default production input is raw physical IMU units, not z-score-normalized tensors.
- Retrained artifacts under `models/retrained/` are research candidates, never automatic defaults.
- Promotion is label-gated. Without a labeled production sample confirming improvement, no candidate is promoted.
- If a candidate is equal or worse on the chosen metric, the current default is kept.

### 5.3 Citation Anchors

The methodological framing of candidate retraining plus label-gated promotion plus governance over blind automation rests on:

- `REF_HIDDEN_TECH_DEBT`: Sculley et al. (2015), *Hidden Technical Debt in Machine Learning Systems*, NeurIPS
- `REF_GOOGLE_MLOPS_CDCT`: Google Cloud (2020), *MLOps: Continuous Delivery and Automation Pipelines in Machine Learning*
- `REF_PSEUDO_LABEL`: Lee (2013), *Pseudo-Label*, ICML Workshop
- `REF_ADABN`: Li et al. (2018), *AdaBN*
- `REF_TENT`: Wang et al. (2021), *TENT*
- `REF_CNN_BILSTM_HAR`: Ordonez and Roggen (2016), CNN-LSTM HAR baseline
- `REF_SENSOR_INFO_GAIN`: Bulling, Blanke, Schiele (2014), body-worn inertial HAR tutorial

### 5.4 Pipeline Scope Clarification

The implemented production pipeline contains seven core operational stages, three conditional mutation stages, and one optional advanced stage:

`ingestion -> validation -> transformation -> inference -> evaluation -> monitoring -> trigger -> retraining -> registration -> baseline_update -> calibration`

Stages 1-7 are the defended runtime path. Stages 8-10 are conditional and require review, labels, QA, and promotion criteria. Stage 11 calibration/UQ is optional/future work unless directly evidenced. Earlier audit drafts referenced Stage 12 Wasserstein drift, Stage 13 curriculum pseudo-labeling, and Stage 14 sensor placement. These are future/archive references, not current evidence.

## 6) Monitoring Evidence Scope

Prometheus and Grafana were explored as optional monitoring infrastructure, but they are not part of the defended current implementation. The current thesis evidence focuses on offline-first monitoring artifacts generated by the pipeline, including confidence/uncertainty summaries, class-distribution checks, drift indicators, trigger-decision reports, logs, MLflow/DVC evidence, and saved run artifacts.

# Thesis Consistency Notes

Purpose: lock a single, reproducible interpretation for thresholding, ablation config labels, and adaptation framing.

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

Why: monitoring is an early warning layer; retraining trigger is a stricter governance gate.

## 2) Collapse Guard Rule

Stage 7 includes a collapse guard that returns `REVIEW` (and blocks auto-retrain) when collapse-like proxies are detected, including:

- `dominant_pct >= 95`, or
- other configured collapse guard conditions in `src/trigger_policy.py`

This behavior is intentionally conservative for unlabeled production data.

## 3) Ablation Config A/B/C/D Definitions

Canonical source: `scripts/run_ablation_experiment.py`.

- Config A: `gravity_removal=False`, `calibration=False`
- Config B: `gravity_removal=False`, `calibration=True`
- Config C: `gravity_removal=True`, `calibration=False`
- Config D: `gravity_removal=True`, `calibration=True`

Important reproducibility note:

Any statement that says "Config D = calibration only (no gravity removal)" is incorrect for the current repository state. That definition corresponds to Config B.

## 4) AdaBN Framing

Adaptation is optional and not the default pipeline mode.

- CLI default remains `--adapt none`
- `ModelRetrainingConfig.adaptation_method` default is `none`
- AdaBN/TENT/pseudo-label options are available as explicit research modes

This keeps the baseline production story and the adaptation experiments clearly separated.

## 5) Default Model and Promotion Gate

### 5.1 Canonical sentence (locked 2026-04-26 — Option A)

> **Defended runtime model:** `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` (1D-CNN-BiLSTM, 11 activity classes, 499 131 parameters, 200×6 input window). The model was provided by the supervisor and was pretrained on a research-grade IMU dataset and fine-tuned on the project's wearable IMU dataset. Inference loads the corresponding scaler from `data/prepared/config.json`. Retraining is implemented as a **governance mechanism** that produces candidate artifacts (`models/retrained/`); promotion is label-gated and requires demonstrated improvement on a labeled holdout. As of 2026-04-26 the model registry (`models/registry/model_registry.json`) reports `current_version: null`, confirming that no retrained candidate has been promoted to defended status. This is the intended behavior: the production data stream is unlabeled, so no candidate has yet satisfied the `is_better=True` gate, and the governance design protects the deployed baseline from unjustified replacement.

### 5.2 Rules

- Default runtime model is the supervisor-provided pretrained baseline: `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`.
- Retrained artifacts under `models/retrained/` (supervised, AdaBN, TENT, pseudo-label) are **research candidates**, never automatic defaults.
- Promotion is label-gated. Without a labeled production sample confirming improvement, no candidate is promoted.
- If a candidate is equal or worse on the chosen metric, the current default is kept.

### 5.3 Citation anchors (already present in `internal/workflow/EVIDENCE_LEDGER.md`)

The methodological framing of "candidate retraining + label-gated promotion + governance over blind automation" rests on:

- `REF_HIDDEN_TECH_DEBT` — Sculley et al. (2015), *Hidden Technical Debt in Machine Learning Systems*, NeurIPS — motivates governance over silent model swaps.
- `REF_GOOGLE_MLOPS_CDCT` — Google Cloud (2020), *MLOps: Continuous Delivery and Automation Pipelines in Machine Learning* — defines CT/CD with promotion gates.
- `REF_PSEUDO_LABEL` — Lee (2013), *Pseudo-Label*, ICML Workshop — basis for the candidate-only treatment of `pseudo_label_model.keras`.
- `REF_ADABN` — Li et al. (2018), *AdaBN* — basis for the AdaBN candidate artifacts.
- `REF_TENT` — Wang et al. (2021), *TENT* — basis for the TENT candidate artifact.
- `REF_CNN_BILSTM_HAR` — Ordóñez and Roggen (2016), *Deep Convolutional and LSTM Recurrent Neural Networks for Multimodal Wearable Activity Recognition* — architecture of the defended model.
- `REF_SENSOR_INFO_GAIN` — Bulling, Blanke, Schiele (2014), *A Tutorial on Human Activity Recognition Using Body-Worn Inertial Sensors*, ACM Computing Surveys — methodological frame for the wearable-IMU pipeline.

### 5.4 Pipeline scope clarification (locked 2026-04-26)

The implemented production pipeline (see `src/pipeline/production_pipeline.py:53-65`) contains **eleven** stages:

`ingestion → validation → transformation → inference → evaluation → monitoring → trigger → retraining → registration → baseline_update → calibration`

Earlier audit drafts referenced "Stage 12 (Wasserstein drift)", "Stage 13 (curriculum + advanced pseudo-labeling)", and "Stage 14 (sensor placement information gain)". These are **not** wired into `ALL_STAGES` and are not part of the defended pipeline. They are documented as **future work**, not as defended evidence.

## 6) Monitoring Evidence Scope

Prometheus and Grafana were explored as optional monitoring infrastructure, but they are not part of the defended current implementation. The current thesis evidence focuses on offline-first monitoring artifacts generated by the pipeline, including confidence/uncertainty summaries, class-distribution checks, drift indicators, trigger-decision reports, logs, MLflow/DVC evidence, and saved run artifacts.

# Component Improvement Review - 2026-04-27

Purpose: careful ML/MLOps engineering review of how to improve each major repo component without expanding thesis scope unnecessarily.

Scope: this is a planning and review artifact. It is not thesis prose, not a citation source, and not evidence that a fix is complete.

## 1. Problem Understanding

The repository contains a strong 11-stage offline MLOps pipeline, but it has several parallel surfaces: pipeline code, API path, Docker path, tracker files, reports, April report, main thesis, docs, scripts, notebooks, MLflow/DVC, and model artifacts.

The main improvement goal is:

> Make every component produce clear evidence, use one model/scaler truth, and avoid claiming improvement from unlabeled data.

The most important components inspected for this review were:

- `docs/PIPELINE_STAGE_MAP.md`
- `src/pipeline/production_pipeline.py`
- `src/entity/config_entity.py`
- `src/api/app.py`
- `src/components/model_retraining.py`
- `src/monitoring/post_inference_monitor.py`
- `src/trigger_policy.py`
- Docker and CI configuration

## 2. Assumptions

- The defended runtime model remains Option A: `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`.
- Retrained models are candidates, not automatic runtime replacements.
- April report is the active writing target for now.
- Unlabeled production data can support drift, confidence, collapse, and governance evidence, but not accuracy or macro-F1 improvement claims.
- Stages 1-7 are core; stages 8-11 are gated/optional; stages 12-14 are future work.

## 3. Recommended Approach

Use one rule for the whole repo:

> Every component should output a small, auditable artifact proving what it did, which model/scaler it used, and whether its output supports accuracy, monitoring, governance, or only future work.

| Component | Improvement idea |
|---|---|
| Config/model policy | Fix contradiction in `src/config.py`: `PRETRAINED_MODEL_STATUS` still says `EXCLUDED_*`. Reword to "defended runtime, excluded only from reproduced local quantitative comparison." |
| Stage 1 ingestion | Add a synchronization QA report: match rate, timestamp delta, dropped rows, effective Hz. |
| Stage 2 validation | Make validation fail/warn reasons machine-readable and thesis-ready. Include unit, range, frequency, and NaN summaries. |
| Stage 3 transformation | Add preprocessing manifest per run: unit conversion, scaler path/hash, window size, overlap, normalization mode, gravity/calibration flags. |
| Windowing | Add a test/report proving no user/session/activity boundary crossing. |
| Stage 4 inference | Save model path, model hash, scaler hash, input shape, and output classes in the inference artifact. |
| Stage 5 evaluation | Strictly separate labeled metrics from unlabeled proxy metrics. No accuracy/F1 without labels. |
| Stage 6 monitoring | Extend the final monitoring report to include sync/data-quality status, confidence, entropy, top-2 margin, dominance, drift, and temporal consistency. |
| Stage 7 trigger | Produce the governance decision matrix: healthy, warning, collapse, cooldown, no labels, worse candidate. |
| Stage 8 retraining | Enforce candidate-only behavior unless labeled promotion evidence exists. Pseudo-labeling must stay guarded. |
| Stage 9 registration | Make `block_if_no_metrics=True` the safe default for promotion. Missing labels should block deployment, not silently pass. |
| Stage 10 baseline update | Snapshot baseline data lineage: source data hash, scaler hash, model hash, timestamp. |
| Stage 11 calibration | Treat calibration as optional/evidence-only unless labeled validation exists. |
| API | Document as lightweight serving path unless it matches full Stage 6/7 behavior. Add `/health/ready` with model path/hash/scaler hash. |
| Docker | Prove model-loaded inference inside container. Reduce image size later with inference-only requirements. |
| CI/tests | Add model-identity, scaler-integrity, governance-matrix, and Docker-ready checks. |
| Docs/thesis | Keep one defended source of truth: April report plus `docs/THESIS_CONSISTENCY_NOTES.md`. Archive stale claims. |

## 4. Step-by-Step Implementation Plan

1. Fix model/scaler truth first.
   - Update `src/config.py` wording for pretrained model status.
   - Add a test that runtime default model equals `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`.
   - Add a test that all runtime paths use `data/prepared/scaler_train_only.json`.

2. Close evidence path.
   - Run full pytest.
   - Run stages 1-7.
   - Save a verification manifest under `reports/`.
   - Capture API smoke with model/scaler loaded.
   - Capture Docker smoke with real inference.

3. Strengthen data pipeline.
   - Add sync QA artifact in ingestion.
   - Add preprocessing manifest in transformation.
   - Add window-boundary hygiene test.

4. Strengthen monitoring/governance.
   - Add complete monitoring summary report.
   - Build retraining-governance matrix artifacts.
   - Block retraining/promotion when labels are missing.

5. Strengthen serving/deployment.
   - Add `/health/ready`.
   - Include model hash, scaler hash, baseline hash.
   - Make Docker health check hit readiness, not only liveness.

6. Clean writing/docs.
   - Keep April report as current working report.
   - Update only April report unless the April report is explicitly promoted into the main thesis source.
   - Move stale docs to historical/internal or mark them clearly.

## 5. Metrics and Checks

| Area | Check |
|---|---|
| Tests | `pytest` pass count captured under `reports/` |
| Pipeline | Stages 1-7 complete with artifacts |
| Model identity | API/pipeline/Docker all report pretrained model path |
| Scaler | All runtime paths load canonical train-only scaler |
| Data quality | Sync report, missingness, frequency, unit conversion status |
| Windowing | 0 user-boundary crossing windows |
| Monitoring | Confidence, entropy, dominance, drift, temporal metrics present |
| Trigger | Governance matrix has all six required cases |
| Retraining | No promotion without labeled improvement |
| Docker | Container returns real inference, not only HTTP health |
| Thesis | April report builds clean after edits |

## 6. Risks and Validation Steps

Main risks:

- Model-policy contradiction: `src/config.py` still uses "EXCLUDED" language for the defended model.
- API vs pipeline mismatch: API may be lighter than stages 1-7. Either align it or document it clearly.
- Docker false confidence: health can pass without proving model inference.
- Unlabeled-data overclaim: drift/confidence can warn, but cannot prove model improvement.
- Tracker drift: too many markdown trackers can contradict each other again.

Validation steps:

1. Run the immediate WORKLOG order: `P0-01` to `P0-12`.
2. Add tests for model path, scaler path, and no-label promotion block.
3. Capture every proof under `reports/`.
4. Rebuild April report.
5. Only after evidence closure, do cleanup/refactor.

## Worklog Hook

This document is tracked in `WORKLOG.md` as item `P1-11`. Review it before starting component-level implementation changes.

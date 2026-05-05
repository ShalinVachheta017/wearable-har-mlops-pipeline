# Pipeline Stage Map (Defense-Friendly)

Purpose: one concise map of all major pipeline stages without implementation noise.

Primary entrypoint:

- `run_pipeline.py`
- Orchestrator: `src/pipeline/production_pipeline.py`

## Stage-by-stage map

| Stage | Main file(s) | Purpose | Input | Output | Artifact / log | Key config dependency |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Ingestion | `src/components/data_ingestion.py` | Build fused 50 Hz sensor stream | accel/gyro raw files or input CSV | fused CSV | `DataIngestionArtifact`; `artifacts/<run_id>/data_ingestion/sensor_fused_50Hz.csv` | `DataIngestionConfig` |
| 2. Validation | `src/components/data_validation.py` | Schema/range/frequency checks | fused CSV | validation status + report | `DataValidationArtifact`; `artifacts/<run_id>/validation/validation_report.json` | `DataValidationConfig` |
| 3. Transformation | `src/components/data_transformation.py`; `src/preprocess_data.py` | Unit conversion, optional gravity/calibration, normalization, windowing | fused CSV | `production_X.npy` + metadata | `DataTransformationArtifact`; `artifacts/<run_id>/data_transformation/` | `DataTransformationConfig` |
| 4. Inference | `src/components/model_inference.py`; `src/run_inference.py` | Model prediction on production windows | `production_X.npy` + model | predictions CSV/NPY + probabilities NPY | `ModelInferenceArtifact`; `artifacts/<run_id>/inference/` | `ModelInferenceConfig` |
| 5. Evaluation | `src/components/model_evaluation.py` | Confidence/distribution analysis (+ labels if available) | predictions CSV | evaluation summaries + reports | `ModelEvaluationArtifact`; `artifacts/<run_id>/evaluation/` | `ModelEvaluationConfig` |
| 6. Monitoring | `src/components/post_inference_monitoring.py`; `src/monitoring/post_inference_monitor.py` | 3-layer health checks (confidence, temporal, drift) | predictions + optional baseline + optional production data | monitoring report + status | `PostInferenceMonitoringArtifact`; `artifacts/<run_id>/monitoring/monitoring_report.json` | `PostInferenceMonitoringConfig` |
| 7. Trigger | `src/components/trigger_evaluation.py`; `src/trigger_policy.py` | Decide monitor/review/retrain action | monitoring report (+ collapse signals) | trigger decision | `TriggerEvaluationArtifact`; `artifacts/<run_id>/trigger/trigger_decision.json` | `TriggerEvaluationConfig` |
| 8. Retraining (optional) | `src/components/model_retraining.py`; `src/train.py` | Retrain/adapt model if gate allows | trigger decision + training/target data | retrained model + report | `ModelRetrainingArtifact`; model saved under retraining output dir | `ModelRetrainingConfig` |
| 9. Registration (optional) | `src/components/model_registration.py`; `src/model_rollback.py` | Register and optionally deploy candidate model | retrained model artifact | version/deploy decision | `ModelRegistrationArtifact`; `models/registry/model_registry.json` | `ModelRegistrationConfig` |
| 10. Baseline Update (optional) | `src/components/baseline_update.py`; `src/monitoring/baseline_builder.py` | Rebuild monitoring baselines | labeled data + retraining context | baseline JSONs | `BaselineUpdateArtifact`; `models/training_baseline.json`, `models/normalized_baseline.json` | `BaselineUpdateConfig` |
| 11. Calibration (advanced optional) | `src/components/calibration_uncertainty.py`; `src/calibration.py` | Temperature scaling + uncertainty analysis | probabilities from stage 4 | calibration metrics + temperature file | `CalibrationUncertaintyArtifact`; calibration outputs under `outputs/` | `CalibrationUncertaintyConfig` |

## Notes for defense

1. Stages 1-7 are the primary operational path.
2. Stages 8-11 are gated by stage-7 decision and governance flags.
3. Stages 12-14 are retired from current runtime orchestration on this branch and should be treated as research/archive references only.

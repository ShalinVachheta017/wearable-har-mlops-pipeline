# Stage-by-Stage Technical Confidence Audit

Date: 2026-05-12

Scope: this is a manual defense aid for the defended Stage 1-7 runtime path. It does not change code, model artifacts, evidence artifacts, thresholds, or training state.

Defended evidence runs:

- Garmin unlabeled run: `artifacts/20260508_235323/`
- User 7 labeled run: `artifacts/20260508_235356/`

Current defense framing:

- Model A is the defended proof-of-concept runtime candidate.
- Stage 1-7 is the defended operational path.
- Stage 8-10 is a gated mutation path, not part of the live runtime demo.
- `auto_retrain=false` is the safe governance setting in the defended runs.
- `CRITICAL` is monitoring severity; `REVIEW` is governance action.
- The demo proves reproducible execution and governance routing, not clinical accuracy, population-level validity, or production-grade deployment.

## Cross-Stage Contract

The defended runtime path is:

`run_pipeline.py` -> `src/pipeline/production_pipeline.py` -> Stage 1-7 component wrappers.

The defended Model A contract is:

- Model path: `models/production_contract/model_a_final_20260508/fine_tuned_clean_model.keras`
- Model contract: `models/production_contract/model_a_final_20260508/model_contract.json`
- Input shape: `(N, 200, 6)`
- Feature order: `Ax, Ay, Az, Gx, Gy, Gz`
- Accelerometer unit after Stage 3: `m/s^2`
- Gyroscope unit after Stage 3: `deg/s`
- Window size: `200`
- Stride: `100`
- Sampling rate: `50 Hz`
- Runtime scaler: Garmin train-only StandardScaler from `models/production_contract/model_a_final_20260508/garmin_train_scaler.json`
- Monitoring baseline: `models/production_contract/model_a_final_20260508/garmin_train_scaled_baseline.json`

## Stage 1 - Data Ingestion

1. Stage purpose

   Convert one selected sensor recording into a fused 50 Hz CSV with canonical sensor columns. The stage supports direct CSV/Excel input or accelerometer plus gyroscope files.

2. Main source file(s)

   - `run_pipeline.py`
   - `src/pipeline/production_pipeline.py`
   - `src/components/data_ingestion.py`
   - `src/entity/config_entity.py`
   - `src/entity/artifact_entity.py`

3. Input

   - Explicit `--input-csv`, or
   - explicit `--accel-file` plus `--gyro-file`, or
   - automatic selection from available matched pairs under `data/raw/`.

   Explicit accelerometer/gyroscope files are preferred for defended evidence. Automatic selection is a convenience path and should not be framed as proof that "whatever newest file was present" is the defended session.

4. Output

   - `DataIngestionArtifact`
   - `data/processed/fused_<dataset>_50Hz.csv`
   - copied evidence under `artifacts/<run_id>/data_ingestion/`

5. Config values used

   - `DataIngestionConfig.target_hz = 50`
   - `DataIngestionConfig.merge_tolerance_ms = 1`
   - supported suffixes: `.csv`, `.xlsx`, `.xls`
   - output directory defaults to `data/processed/`

6. Evidence artifact path

   - Garmin: `artifacts/20260508_235323/data_ingestion/fused_2025_07_16_21_03_13_50Hz.csv`
   - User 7: `artifacts/20260508_235356/data_ingestion/fused_2026_05_05_15_11_15_labeled_50hz_user7_50Hz.csv`
   - run summaries: `artifacts/20260508_235323/run_info.json`, `artifacts/20260508_235356/run_info.json`

7. What can fail

   Wrong file selection, mismatched accelerometer/gyroscope files, timestamp parsing errors, strict merge tolerance dropping gyro rows, bad column aliases, empty fused data, or direct CSV input that was not actually sampled at 50 Hz.

8. What actually happened in the defended Garmin run

   Stage 1 completed successfully. It wrote `130500` rows and `9` columns at `50 Hz`. The fused evidence file is `fused_2025_07_16_21_03_13_50Hz.csv`. No label column was carried into validation.

9. What actually happened in the defended User 7 run

   Stage 1 completed successfully. It wrote `99017` rows and `10` columns at `50 Hz`. The fused evidence file is `fused_2026_05_05_15_11_15_labeled_50hz_user7_50Hz.csv`. The `activity` label column was preserved.

10. What I should say in defense

   "Stage 1 gives the rest of the pipeline one canonical fused 50 Hz CSV. The defended runs show that both the unlabeled Garmin session and the labeled User 7 session reached this handoff successfully."

11. What I should not claim

   Do not claim Stage 1 proves sensor placement correctness, clinical validity, or that every future Garmin file will be clean. It only proves the selected inputs were parsed and fused into the expected handoff format for these runs.

## Stage 2 - Data Validation

1. Stage purpose

   Validate that the fused CSV is safe enough for transformation: required schema, numeric sensor channels, missing values, timestamp quality, sampling frequency, unit detection, and range checks.

2. Main source file(s)

   - `src/components/data_validation.py`
   - `src/entity/config_entity.py`
   - `src/entity/artifact_entity.py`
   - `src/pipeline/production_pipeline.py`
   - `config/pipeline_config.yaml`

3. Input

   - The exact fused CSV path from `DataIngestionArtifact.fused_csv_path`.

4. Output

   - `DataValidationArtifact`
   - `artifacts/<run_id>/validation/validation_report.json`
   - pipeline abort if validation has hard errors.

5. Config values used

   - sensor columns: `Ax, Ay, Az, Gx, Gy, Gz`
   - timestamp candidates: `true_time`, `timestamp`, `timestamp_iso`, `timestamp_ms`
   - expected frequency: `50.0 Hz`
   - sampling tolerance: `0.1`
   - max missing ratio: `0.05`
   - max acceleration: `50.0 m/s^2`
   - max gyroscope: `500.0 deg/s`

6. Evidence artifact path

   - Garmin: `artifacts/20260508_235323/validation/validation_report.json`
   - User 7: `artifacts/20260508_235356/validation/validation_report.json`

7. What can fail

   Missing required channels, non-numeric sensor values, excessive missingness, duplicate or invalid timestamps, non-monotonic time, sampling-rate deviation, ambiguous acceleration units, sustained gyro clipping, or empty input.

8. What actually happened in the defended Garmin run

   Validation passed with `is_valid=true`, `0` errors, and `4` warnings. It detected unlabeled data, `130500` rows, `50.0 Hz`, no missing sensor values, and accelerometer unit `milliG`. Warnings were one extreme `Ay` value above the milliG-equivalent acceleration threshold and occasional gyro spikes on `Gx`, `Gy`, and `Gz`.

9. What actually happened in the defended User 7 run

   Validation passed with `is_valid=true`, `0` errors, and `2` warnings. It detected labeled data with label column `activity`, `99017` rows, `50.0 Hz` median sampling, no missing sensor values, and accelerometer unit `m/s2`. Warnings were `338` large timestamp gaps and `2` occasional `Gx` samples above `500 deg/s`.

10. What I should say in defense

   "Stage 2 is a gate, not a cleanup stage. It passed both defended inputs with no hard errors, while preserving warnings that remain visible in the evidence."

11. What I should not claim

   Do not claim the warnings are irrelevant. Say they are tolerated quality warnings that are carried into the audit trail, not hidden or used to fake success.

## Stage 3 - Data Transformation

1. Stage purpose

   Convert the validated fused CSV into Model A input windows: detect units, convert accelerometer values to `m/s^2` when needed, keep gyroscope in `deg/s`, skip optional gravity/calibration transforms, apply the defended Garmin train-only scaler, and create row-wise windows.

2. Main source file(s)

   - `src/components/data_transformation.py`
   - `src/preprocess_data.py`
   - `src/utils/scaler.py`
   - `src/utils/label_mapping.py`
   - `config/pipeline_config.yaml`

3. Input

   - Fused CSV from Stage 1 after Stage 2 validation.
   - Optional label column when the input is labeled.
   - Saved scaler JSON from Model A contract.

4. Output

   - `DataTransformationArtifact`
   - `production_X.npy`
   - `production_metadata.json`
   - `transformation_report.json`
   - `production_y.npy` only when labels are present.

5. Config values used

   - `enable_unit_conversion=true`
   - `unit_conversion_factor=0.00980665`
   - `enable_gravity_removal=false`
   - `enable_calibration=false`
   - `enable_normalization=true`
   - `normalization_variant=zscore`
   - `scaler_path=models/production_contract/model_a_final_20260508/garmin_train_scaler.json`
   - `window_size=200`
   - `overlap=0.5`
   - step size: `100`

6. Evidence artifact path

   - Garmin: `artifacts/20260508_235323/data_transformation/transformation_report.json`
   - Garmin tensor copy: `artifacts/20260508_235323/data_transformation/production_X.npy`
   - User 7: `artifacts/20260508_235356/data_transformation/transformation_report.json`
   - User 7 tensor copy: `artifacts/20260508_235356/data_transformation/production_X.npy`
   - runtime scaler: `models/production_contract/model_a_final_20260508/garmin_train_scaler.json`

7. What can fail

   Unit ambiguity, wrong channel order, scaler path missing, scaler dimension mismatch, normalization variant mismatch, NaN/inf in tensor, wrong window shape, stale labels being mistaken for current labels, or optional transforms being accidentally enabled.

8. What actually happened in the defended Garmin run

   Stage 3 completed successfully. It detected `milliG`, converted accelerometer values to `m/s^2`, kept gyroscope in `deg/s`, did not apply gravity removal or calibration, applied the saved Garmin train-only z-score scaler, and produced `1304` windows with shape `[1304, 200, 6]`. The run was unlabeled; an old `production_y.npy` was explicitly marked as stale and ignored.

9. What actually happened in the defended User 7 run

   Stage 3 completed successfully. It detected accelerometer values already in `m/s^2`, so no accelerometer conversion was applied. It kept gyroscope in `deg/s`, applied the same saved Garmin train-only scaler, and produced `989` windows with shape `[989, 200, 6]`. Labels were present and `production_y.npy` was written.

10. What I should say in defense

   "Stage 3 is where the defended Model A input contract is enforced: unit conversion when needed, Garmin train-only scaler, and row-wise 200 by 6 windows. User 7 was transformed using the saved scaler; it was not used to fit the scaler."

11. What I should not claim

   Do not claim the scaler was fitted on User 7, validation, or live data. Do not claim gravity removal or domain calibration were part of the defended Stage 3 runtime path.

## Stage 4 - Model Inference

1. Stage purpose

   Load Model A, validate model/input/output shape, run batch inference on `production_X.npy`, and persist predictions, probabilities, confidence, entropy, top-2 margin, class distribution, and collapse flags.

2. Main source file(s)

   - `src/components/model_inference.py`
   - `src/config.py`
   - `src/utils/label_mapping.py`
   - `src/pipeline/production_pipeline.py`

3. Input

   - `production_X.npy` from Stage 3.
   - Model A Keras file from `models/production_contract/model_a_final_20260508/fine_tuned_clean_model.keras`.

4. Output

   - `ModelInferenceArtifact`
   - prediction CSV
   - predicted-class NPY
   - probability NPY
   - prediction metadata JSON
   - `inference_report.json`
   - `inference_summary.json`

5. Config values used

   - default model path: `models/production_contract/model_a_final_20260508/fine_tuned_clean_model.keras`
   - batch size: `32`
   - confidence threshold: `0.50`
   - expected input shape: `(None, 200, 6)`
   - expected output shape: `(None, 11)`
   - class mapping: 11 fixed activity labels, with `hand_tapping` at index `4`

6. Evidence artifact path

   - Garmin: `artifacts/20260508_235323/inference/inference_report.json`
   - Garmin summary: `artifacts/20260508_235323/inference/inference_summary.json`
   - User 7: `artifacts/20260508_235356/inference/inference_report.json`
   - User 7 summary: `artifacts/20260508_235356/inference/inference_summary.json`
   - Model contract: `models/production_contract/model_a_final_20260508/model_contract.json`

7. What can fail

   Model file missing, wrong Keras input/output shape, wrong tensor shape, NaN/inf in input tensor, invalid probability matrix, probability rows not summing to 1, bad class mapping, or class collapse.

8. What actually happened in the defended Garmin run

   Stage 4 completed successfully with Model A MD5 `5eacfd52acc4d6aaad7a0af0ec5c54ae` and `87083` parameters. It produced `1304` predictions in about `0.933 s`, around `1398 windows/s`. The dominant class was `sitting` at `51.76%`, mean softmax confidence was about `0.393`, and `collapse_level` was `NONE`.

9. What actually happened in the defended User 7 run

   Stage 4 completed successfully with the same Model A MD5 and parameter count. It produced `989` predictions in about `0.723 s`, around `1368 windows/s`. The dominant class was `nape_rubbing` at `16.48%`, mean softmax confidence was about `0.359`, all 11 classes appeared, and `collapse_level` was `NONE`.

10. What I should say in defense

   "Stage 4 proves the frozen Model A artifact can run end-to-end on both defended sessions with the expected tensor and output contracts. Its confidence is explicitly treated as softmax confidence, not calibrated correctness probability."

11. What I should not claim

   Do not claim Stage 4 alone proves accuracy, clinical usefulness, or population generalization. For accuracy, only the labeled User 7 Stage 5 result is relevant, and it remains proof-of-concept evidence.

## Stage 5 - Model Evaluation

1. Stage purpose

   Validate the prediction CSV contract, summarize prediction distribution and confidence, compute temporal summaries, and compute supervised metrics only when paired labels exist.

2. Main source file(s)

   - `src/components/model_evaluation.py`
   - `src/utils/label_mapping.py`
   - `src/pipeline/production_pipeline.py`

3. Input

   - Stage 4 prediction CSV.
   - Optional labels path. In the full pipeline, Stage 5 auto-detects `production_y.npy` from Stage 3 when labels exist.

4. Output

   - `ModelEvaluationArtifact`
   - timestamped evaluation JSON
   - timestamped evaluation TXT
   - `evaluation_summary.json`

5. Config values used

   - `confidence_bins=10`
   - labels are optional
   - label/prediction lengths must match exactly when labels exist
   - distribution dominance warning threshold uses the Stage 6 critical dominance threshold, `95%`

6. Evidence artifact path

   - Garmin summary: `artifacts/20260508_235323/evaluation/evaluation_summary.json`
   - Garmin full report: `artifacts/20260508_235323/evaluation/evaluation_20260508_235347.json`
   - User 7 summary: `artifacts/20260508_235356/evaluation/evaluation_summary.json`
   - User 7 full report: `artifacts/20260508_235356/evaluation/evaluation_20260508_235406.json`

7. What can fail

   Missing prediction columns, missing probability columns, non-numeric values, probabilities not summing to 1, class/name mismatch, labels missing, labels wrong length, labels outside the canonical class IDs, or false interpretation of unlabeled data as accuracy evidence.

8. What actually happened in the defended Garmin run

   Stage 5 completed as an unlabeled evaluation. `has_labels=false`, `classification_metrics=null`, dominant class was `sitting` at `51.76%`, distribution dominance warning was `false`, mean confidence was about `0.393`, and no accuracy was computed.

9. What actually happened in the defended User 7 run

   Stage 5 completed as a labeled evaluation. `has_labels=true`, accuracy was `0.3761`, macro F1 was `0.34095`, macro recall/balanced accuracy was `0.37454`, weighted F1 was `0.34174`, dominant class was `nape_rubbing` at `16.48%`, and distribution dominance warning was `false`.

10. What I should say in defense

   "Stage 5 separates unlabeled runtime observability from labeled external evaluation. Garmin produces distribution and confidence evidence only; User 7 provides the labeled proof-of-concept metric."

11. What I should not claim

   Do not claim Garmin unlabeled accuracy. Do not claim User 7 accuracy is clinical accuracy or population-level accuracy. It is a labeled external session result for the defended proof-of-concept candidate.

## Stage 6 - Post-Inference Monitoring

1. Stage purpose

   Convert Stage 4/5 outputs into runtime health signals through confidence monitoring, temporal monitoring, motion-context checks, and z-score drift against the defended Model A baseline.

2. Main source file(s)

   - `src/components/post_inference_monitoring.py`
   - `src/monitoring/post_inference_monitor.py`
   - `src/monitoring/drift_monitor.py`
   - `src/pipeline/production_pipeline.py`
   - `config/pipeline_overrides.yaml`

3. Input

   - Stage 4 predictions CSV.
   - Stage 3 `production_X.npy`.
   - Normalized Model A baseline JSON.
   - Optional existing `outputs/calibration/temperature.json` for confidence rescaling.

4. Output

   - `PostInferenceMonitoringArtifact`
   - `monitoring_report.json`
   - `monitoring_summary.json`
   - monitoring status: `HEALTHY`, `WARNING`, or `CRITICAL`

5. Config values used

   - confidence warning threshold: `0.70`
   - uncertain window threshold: `0.50`
   - uncertain percentage threshold: `20.0`
   - dominant-class warning threshold: `85.0`
   - dominant-class critical threshold: `95.0`
   - transition rate threshold: `35.0`
   - low gyro motion threshold: `1.1`
   - low motion dominance threshold: `70.0`
   - drift z-score threshold: `1.8`
   - drift detector mode: `zscore_mean_shift`
   - baseline mode override: `normalized`
   - normalized baseline path: `models/production_contract/model_a_final_20260508/garmin_train_scaled_baseline.json`
   - existing calibration temperature file observed: `outputs/calibration/temperature.json` with `temperature=1.5`, `fitted=false`

6. Evidence artifact path

   - Garmin: `artifacts/20260508_235323/monitoring/monitoring_report.json`
   - Garmin summary: `artifacts/20260508_235323/monitoring/monitoring_summary.json`
   - User 7: `artifacts/20260508_235356/monitoring/monitoring_report.json`
   - User 7 summary: `artifacts/20260508_235356/monitoring/monitoring_summary.json`
   - baseline: `models/production_contract/model_a_final_20260508/garmin_train_scaled_baseline.json`

7. What can fail

   Missing predictions, missing production tensor, baseline missing, baseline feature-space mismatch, temperature file confusion, incorrect confidence interpretation, false drift from wrong baseline mode, or treating monitoring severity as a retraining command.

   Note on confidence fields: Stage 5 and the inference summary report raw mean confidence (`evaluation_summary.json -> confidence_summary.mean`, Garmin about `0.393`, User 7 about `0.359`). Stage 6 reports the monitoring-layer value (`monitoring_report.json -> layer1_confidence.mean_confidence`, Garmin about `0.424`, User 7 about `0.402`), which can differ because the monitor applies its internal confidence processing and can read an existing calibration temperature file. In both cases, the value remains below the warning threshold and leads to the same governance interpretation.

8. What actually happened in the defended Garmin run

   Stage 6 completed and reported `overall_status=CRITICAL`. The `CRITICAL` status came from Layer 1: monitoring mean confidence `0.424 < 0.700` and uncertain percentage `75.5% > 20.0%`. Layer 2 temporal status was `HEALTHY` with transition rate `27.32% < 35.0%`. Dominance was not critical: `sitting` at `51.76%`, below the `85%` warning threshold. Layer 3 drift status was `HEALTHY`, max z-score drift `1.1166 < 1.8`. Motion context had low gyro motion but no low-motion collapse risk because dominance was below `70%`.

9. What actually happened in the defended User 7 run

   Stage 6 completed and reported `overall_status=CRITICAL`. The `CRITICAL` status came from Layer 1: monitoring mean confidence `0.402 < 0.700` and uncertain percentage `80.5% > 20.0%`. Layer 2 temporal status was `HEALTHY` with transition rate `27.73% < 35.0%`. Dominance was not critical: `nape_rubbing` at `16.48%`. Layer 3 drift status was `HEALTHY`, max z-score drift `0.1639 < 1.8`. Motion context did not flag low-motion collapse risk.

10. What I should say in defense

   "Stage 6 does not say the model is clinically wrong. It says the runtime confidence/uncertainty profile deserves attention. In both defended runs, the alert is driven by low confidence and high uncertainty, while dominance and aggregate drift remain controlled."

11. What I should not claim

   Do not claim `CRITICAL` means automatic retraining. Do not claim the chunked drift diagnostic is the governance decision by itself. Do not claim the confidence score is a calibrated probability of correctness. Do not claim Stage 6 proves production-grade monitoring.

## Stage 7 - Trigger Evaluation

1. Stage purpose

   Convert Stage 6 monitoring signals and collapse signals into a governance action: no action, monitor, review, queue candidate, or trigger candidate generation. In the defended runs, this stage routes to review and blocks automatic retraining.

2. Main source file(s)

   - `src/components/trigger_evaluation.py`
   - `src/trigger_policy.py`
   - `src/pipeline/pipeline_safety.py`
   - `src/entity/config_entity.py`
   - `config/pipeline_overrides.yaml`

3. Input

   - `PostInferenceMonitoringArtifact`
   - confidence, temporal, drift, and collapse signals
   - persisted trigger state from `logs/trigger/trigger_state.json`

4. Output

   - `TriggerEvaluationArtifact`
   - `trigger_decision.json`
   - governance fields: `should_retrain`, `auto_retrain`, `review_required`, `label_required`, `qa_required`, `action`, `alert_level`

5. Config values used

   - `confidence_warn=0.65`
   - `confidence_critical=0.50`
   - `drift_zscore_warn=2.0`
   - `drift_zscore_critical=3.0`
   - `temporal_flip_warn=0.35`
   - `temporal_flip_critical=0.50`
   - cooldown hours: `24`
   - consecutive warnings for review escalation: `3`
   - `auto_retrain=false` in the policy decision

6. Evidence artifact path

   - Garmin: `artifacts/20260508_235323/trigger/trigger_decision.json`
   - User 7: `artifacts/20260508_235356/trigger/trigger_decision.json`
   - trigger state: `logs/trigger/trigger_state.json`

7. What can fail

   Missing monitoring artifact, stale persistent trigger state, severity/action confusion, cooldown-state confusion, treating `queue_retrain` as deployment, or ignoring label/QA gates.

8. What actually happened in the defended Garmin run

   Stage 7 completed successfully. It wrote `decision=LABEL_QA_REQUIRED`, `action=review`, `alert_level=CRITICAL`, `should_retrain=false`, `auto_retrain=false`, `review_required=true`, `label_required=true`, and `qa_required=true`. The reason mentions `6 consecutive warnings`, which comes from persisted trigger state, not from a single isolated batch only.

9. What actually happened in the defended User 7 run

   Stage 7 completed successfully. It wrote `decision=LABEL_QA_REQUIRED`, `action=review`, `alert_level=CRITICAL`, `should_retrain=false`, `auto_retrain=false`, `review_required=true`, `label_required=true`, and `qa_required=true`. The reason mentions `7 consecutive warnings`, again reflecting persisted trigger state.

   In defense, do not overinterpret the exact warning count as a property of only that session. It reflects the persisted trigger-state context at the time of the run.

10. What I should say in defense

   "Stage 7 is the governance boundary. The monitoring severity is critical, but the action is review. Both defended runs explicitly keep `auto_retrain=false` and require labels or QA before any retraining path is allowed."

11. What I should not claim

   Do not claim the pipeline retrained, deployed, or updated the baseline in these defended runs. Do not claim `REVIEW` is a failure. It is the intended safe action for uncertain or risky evidence.

## Ten Questions I Should Be Able To Answer

1. Which file is the single CLI entrypoint for the defended runtime path?
2. Which exact Model A file is loaded by Stage 4?
3. What input shape does Model A require?
4. Which six sensor channels are expected, and in what order?
5. When does Stage 3 convert accelerometer values from milliG to `m/s^2`?
6. Where is the Garmin train-only scaler stored, and what data was excluded from fitting it?
7. Why does the Garmin run not have an accuracy value?
8. What is the User 7 accuracy and macro F1 for Model A?
9. Why can Stage 6 report `CRITICAL` while Stage 7 still says `should_retrain=false`?
10. Why is Stage 8-10 not part of the defended live runtime demo?

## Ten Files I Must Not Move During Cleanup

1. `run_pipeline.py`
2. `src/pipeline/production_pipeline.py`
3. `src/components/data_ingestion.py`
4. `src/components/data_validation.py`
5. `src/components/data_transformation.py`
6. `src/components/model_inference.py`
7. `src/components/model_evaluation.py`
8. `src/components/post_inference_monitoring.py`
9. `src/components/trigger_evaluation.py`
10. `models/production_contract/model_a_final_20260508/`

Treat these supporting runtime files as protected too: `config/pipeline_config.yaml`, `config/pipeline_overrides.yaml`, `src/entity/config_entity.py`, `src/entity/artifact_entity.py`, `src/config.py`, `src/utils/label_mapping.py`, `src/utils/config_loader.py`, `src/monitoring/post_inference_monitor.py`, and `src/trigger_policy.py`.

Treat these evidence and defense files/folders as protected too:

1. `artifacts/20260508_235323/`
2. `artifacts/20260508_235356/`
3. `reports/abc_comparison/`
4. `docs/EVIDENCE_KIT_INDEX_2026-05.md`
5. `docs/FINAL_THESIS_CLAIMS_2026-06.md`
6. `docs/MODEL_DECISION_2026-05.md`
7. `docs/MODEL_ABC_MENTOR_BRIEF_2026-05.md`
8. `internal/writing/defense_qa.md`
9. `thesis/defense_demo_runbook.md`
10. `internal/writing/defense_slides.pptx`

## Ten Files/Folders Likely Safe To Archive Later

These are archive candidates only. Verify with `git status`, DVC status, and one final runbook check before moving anything.

Do not move old artifacts until `REPO_CLEANUP_INVENTORY_2026-05.md` confirms they are not referenced by the evidence kit, thesis, slides, or runbook.

1. `.pytest_cache/`
2. `.mypy_cache/`
3. `.tmp_pytest/`
4. `.tmp_pytest_current/`
5. `tmp_pytest_trigger/`
6. `tmp_pytest_trigger2/`
7. `tmp_run3/`
8. old non-defended `artifacts/<timestamp>/` folders, except the defended `20260508_235323` and `20260508_235356` evidence folders
9. large old `outputs/ablation/` or `outputs/experiments/` dumps after final summaries are preserved
10. root scratch notes such as `temp.txt`, `reasoningtxt.txt`, `thesis_doc.txt`, and `pt.md` after a quick skim for unique thesis text

## One-Sentence Defense Summary

"The defended system executes a reproducible Stage 1-7 path around frozen Model A, records every handoff as artifacts, and routes risky monitoring evidence to human review with `auto_retrain=false`; it does not claim clinical accuracy, population-level validity, or production-grade deployment."

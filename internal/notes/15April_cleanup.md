Script Classification — Full Picture
The key architectural insight
The src/ flat-level files are NOT duplicates of src/components/ — they are the actual implementation logic. The components layer wraps them. Confirmed from imports:

src/components/ wrapper	Imports from...
model_inference.py	src/run_inference.py
data_transformation.py	src/preprocess_data.py
data_validation.py	src/data_validator.py
model_evaluation.py	src/evaluate_predictions.py
model_registration.py	src/deployment_manager.py
calibration_uncertainty.py	src/calibration.py (lazy import)
curriculum_pseudo_labeling.py	src/curriculum_pseudo_labeling.py (lazy import)
sensor_placement.py	src/sensor_placement.py (lazy import)
wasserstein_drift.py	src/wasserstein_drift.py (lazy import)
So those flat src/ files are runtime-linked. They cannot be deleted.

Bucket Classification
BUCKET 1 — Runtime-linked (do not touch)
File	Why
src/run_inference.py	Imported by components/model_inference.py
src/preprocess_data.py	Imported by components/data_transformation.py
src/data_validator.py	Imported by components/data_validation.py
src/evaluate_predictions.py	Imported by components/model_evaluation.py
src/deployment_manager.py	Imported by components/model_registration.py
src/model_rollback.py	Stage 9 path
src/mlflow_tracking.py	Used across components
src/calibration.py	Lazy-imported by components/calibration_uncertainty.py
src/curriculum_pseudo_labeling.py	Lazy-imported by its component
src/sensor_placement.py	Lazy-imported by its component
src/wasserstein_drift.py	Lazy-imported by its component
src/trigger_policy.py	Stage 7 runtime engine
src/config.py	Used everywhere
scripts/post_inference_monitoring.py	Imported by components/post_inference_monitoring.py
scripts/build_training_baseline.py	Imported by components/baseline_update.py
BUCKET 2 — Legacy wrappers (Wave 1 already done)
Both already have deprecation notices + proper thin implementations:

File	Status
scripts/preprocess.py	Already a proper thin wrapper + runtime deprecation warning
scripts/train.py	Already a proper thin wrapper + runtime deprecation warning
Wave 1 from the cleanup plan is already complete. No action needed here.

BUCKET 3 — Research/thesis utilities (keep, clearly labelled)
File	Purpose
scripts/run_ablation_experiment.py	Generates ablation evidence for A7/Ch7
scripts/run_ab_comparison.py	A/B comparison runs
scripts/threshold_sweep.py	Policy analysis
scripts/windowing_ablation.py	Research utility
scripts/generate_thesis_figures.py	Figure pack for Ch7/Ch13
scripts/per_dataset_inference.py	Dataset analysis runner
scripts/trigger_policy_eval.py	Policy eval runner
scripts/analyze_drift_across_datasets.py	Drift analysis
scripts/batch_process_all_datasets.py	Batch runner
scripts/data_analysis/analyze_datasets.py	Dataset QC
scripts/preprocess_qc.py	QC diagnostics
BUCKET 4 — Archive candidates (safe to move/consolidate)
These are the only things you can safely act on today:

File	Why it's a candidate	Risk
src/sensor_data_pipeline.py	Historical ingestion path; not imported by any component	Low — verify with one grep first
src/train.py	Standalone trainer; components/model_retraining.py is canonical; check if scripts/train.py imports it	Low-medium
src/active_learning_export.py	No clear pipeline import	Low
scripts/build_normalized_baseline.py	Overlaps with build_training_baseline.py	Low
scripts/audit_artifacts.py	Likely overlaps with mlops_audit.py at root	Low
scripts/inference_smoke.py	May be superseded by run_pipeline.py --stages inference	Low
scripts/run_tests.py	Probably just a pytest wrapper	Low
Root: mlops_audit.py	Could move to scripts/ — not a runtime file	Zero
Root: generate_synthetic_data.py	Could move to scripts/	Zero
Bottom line for today
The real cleanup scope is smaller than it looks because most flat src/ files are actually the implementation layer behind src/components/. The two legacy wrappers in scripts/ are already done.

What's actually actionable today without any risk:

Move generate_synthetic_data.py and mlops_audit.py from root → scripts/ (zero risk, cosmetic)
Verify src/sensor_data_pipeline.py and src/active_learning_export.py have no imports → move to archive
Consolidate scripts/build_normalized_baseline.py into archive (overlap confirmed)
Check if scripts/run_tests.py is just pytest → delete if so
Want me to run the verification greps for the archive candidates before we touch anything?
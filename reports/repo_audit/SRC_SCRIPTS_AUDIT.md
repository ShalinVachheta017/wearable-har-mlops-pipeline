# SRC vs SCRIPTS Audit Report
**Generated**: 2026-03-05  
**Status**: Analysis only — no code changes made

---

## Scripts Directory (25 Python files)

| File | Purpose | Type | Imports from src/ | Inputs | Outputs |
|------|---------|------|-------------------|--------|---------|
| `train.py` | Training/retraining entry point with AdaBN | Entrypoint (argparse) | `entity.config_entity`, `components` | Training data, CLI args | Retrained model, baseline |
| `preprocess.py` | Stages 1–3: ingestion → validation → transformation | Entrypoint (argparse) | `entity.config_entity`, `components` | Raw CSV/Excel | Windowed .npy, config.json |
| `post_inference_monitoring.py` | 3-layer monitoring (confidence, temporal, drift) | **Library** (misplaced!) | None | Predictions CSV, baseline | Monitoring report JSON |
| `threshold_sweep.py` | Data-driven threshold calibration via synthetic data | Entrypoint (argparse) | `utils.temporal_metrics` | Baseline, model, temperature | THRESHOLD_CALIBRATION.csv/png |
| `trigger_policy_eval.py` | Compare trigger policies (single vs 2-of-3 vs cooldown) | Entrypoint (argparse) | None | Simulated sessions | TRIGGER_POLICY_EVAL.csv/png |
| `build_training_baseline.py` | Rebuild drift baselines from labeled CSV | Entrypoint + library | `config` | all_users_data_labeled.csv | training_baseline.json |
| `build_normalized_baseline.py` | Create baseline stats from reference data | Entrypoint (argparse) | None | production_X.npy | normalized_baseline.json |
| `analyze_drift_across_datasets.py` | Drift analysis across raw datasets | Entrypoint | None | Raw sensor files, baseline | Console output |
| `audit_artifacts.py` | Verify pipeline outputs per run | Entrypoint (argparse) | None | Artifacts folder | Pass/fail report |
| `benchmark_latency.py` | Per-request latency (p50/p95/p99) via HTTP or local | Entrypoint (argparse) | None | API endpoint / model | latency_report.json |
| `benchmark_throughput.py` | Requests/sec with concurrency scaling | Entrypoint (argparse) | None | API endpoint | throughput_report.json |
| `per_dataset_inference.py` | Run model on each raw dataset pair | Entrypoint | None | Raw files, model | Confidence/activity stats |
| `inference_smoke.py` | Smoke test for HAR API | Entrypoint (argparse) | None | API endpoint | Exit code |
| `run_ab_comparison.py` | A/B/C normalization strategy comparison | Entrypoint (argparse) | `src.train` | Data, CLI args | ab_comparison.json/csv |
| `export_mlflow_runs.py` | Export MLflow runs to CSV | Entrypoint (argparse) | None (MLflow API) | Experiment name | CSV export |
| `extract_papers_to_text.py` | Convert PDFs to text | Entrypoint (argparse) | None | PDF files | .txt files |
| `fetch_foundation_papers.py` | Download foundational PDFs | Entrypoint (argparse) | None | Hardcoded URLs | PDF files |
| `generate_thesis_figures.py` | Generate matplotlib figures for thesis | Entrypoint | None | Data files | PNG figures |
| `regenerate_support_map.py` | Rebuild PAPER_SUPPORT_MAP.json | Entrypoint (argparse) | None | Paper texts | JSON report |
| `update_progress_dashboard.py` | Generate progress dashboard MD | Entrypoint (argparse) | None | progress.yaml | DASHBOARD.md |
| `verify_prometheus_metrics.py` | Verify Prometheus metrics available | Entrypoint (argparse) | None | Metrics endpoint | Check report |
| `verify_repository.py` | Verify repo completeness | Entrypoint (argparse) | None | Project structure | Pass/fail |
| `run_tests.py` | Run pytest with presets | Entrypoint (argparse) | None | CLI flags | pytest output |
| `windowing_ablation.py` | Grid search window_size × overlap | Entrypoint (argparse) | `utils.temporal_metrics` | Labeled CSV | ABLATION.csv/png |
| `preprocess_qc.py` | QC checks on preprocessed data | Entrypoint | None | Preprocessed data | QC report |

## Src Directory (key modules)

| File | Purpose | Key Classes/Functions | Imported By |
|------|---------|----------------------|-------------|
| `train.py` | Training library (CV, MLflow, domain adaptation) | `TrainingConfig`, `DataLoader`, `HARModelBuilder` | `scripts/run_ab_comparison.py`, components |
| `preprocess_data.py` | Production preprocessing pipeline | `UnifiedPreprocessor`, `GravityRemover` | components |
| `trigger_policy.py` | Multi-signal retraining trigger engine | `TriggerPolicyEngine`, `TriggerDecision` | pipeline |
| `config.py` | Central paths/constants | Constants (PROJECT_ROOT, WINDOW_SIZE) | **All modules** |
| `run_inference.py` | Batch inference pipeline | `InferencePipeline`, `InferenceConfig` | components |
| `evaluate_predictions.py` | Prediction evaluation (confidence, ECE) | `EvaluationPipeline`, `CalibrationEvaluator` | components |
| `data_validator.py` | Schema/range validation | `DataValidator`, `ValidationResult` | components |
| `mlflow_tracking.py` | MLflow integration | `MLflowTracker` | train, components |
| `robustness.py` | Robustness evaluation framework | `RobustnessEvaluator` | Not yet integrated |
| `ood_detection.py` | Energy-based OOD detection | `EnergyOODDetector` | Optional |
| `wasserstein_drift.py` | Wasserstein drift detection | `WassersteinDriftDetector` | Optional |
| `calibration.py` | Post-hoc calibration | `TemperatureScaler`, `CalibrationEvaluator` | Optional |
| `sensor_data_pipeline.py` | Raw sensor Excel processing | `SensorDataLoader`, `SensorFusion` | components |
| `prometheus_metrics.py` | Prometheus metric exporter | `MetricsExporter` | Optional |
| `pipeline/production_pipeline.py` | 10-stage orchestrator | `PipelineOrchestrator` | Entry point |
| `components/*.py` (9 files) | Pipeline stage wrappers | Component classes | pipeline |

## Duplication Candidates

| Scripts File | Src File | Severity | Description |
|-------------|----------|----------|-------------|
| `scripts/post_inference_monitoring.py` | `src/components/post_inference_monitoring.py` | **CRITICAL** | Core `PostInferenceMonitor` class lives in scripts/; component just wraps it. Class should be in src/. |
| `scripts/build_training_baseline.py` | `src/components/baseline_update.py` | **HIGH** | `BaselineBuilder` class in scripts/; component imports and wraps it. Extract to src/utils/. |
| `scripts/train.py` | `src/train.py` | **HIGH** | Both orchestrate stages 8–10. scripts/ should be thin CLI wrapper around src/. |
| `scripts/preprocess.py` | `src/components/data_transformation.py` | Low | Scripts runs stages 1–3 end-to-end; component runs stage 3 only. Acceptable separation. |
| `scripts/threshold_sweep.py` | `src/trigger_policy.py` | Low | Different scope: sweep = calibration, policy = decision logic. Acceptable. |

## Suggested Refactor Plan

### High Priority
1. **Move `PostInferenceMonitor`** from `scripts/` → `src/post_inference_monitor.py`. Component wraps it. Scripts becomes optional CLI test.
2. **Extract `BaselineBuilder`** to `src/utils/baseline_builder.py`. Both scripts and component import from there.
3. **Make `scripts/train.py` a thin wrapper** around `src/train.py`. Avoid duplicating stage logic.

### Medium Priority
4. **Standardize inference interfaces** — create `src/inference_executor.py` with unified API.
5. **Document entrypoint hierarchy** — add README to scripts/ explaining which scripts to use and when.

### Low Priority
6. **Create `scripts/analysis/`** subdirectory for post-hoc analysis scripts (threshold_sweep, trigger_policy_eval, windowing_ablation, analyze_drift).
7. **Extract shared utilities** (`_generate_csv_bytes()`, `_stats()`) to `src/utils/`.

### Entrypoint Hierarchy (Recommended)

```
PRODUCTION:
  run_pipeline.py           ← Main orchestrator
  scripts/preprocess.py     ← Standalone Stages 1-3
  scripts/train.py          ← Standalone Stages 8-10

CI/TEST:
  scripts/inference_smoke.py
  scripts/audit_artifacts.py
  scripts/verify_repository.py
  scripts/run_tests.py

BENCHMARKING:
  scripts/benchmark_latency.py
  scripts/benchmark_throughput.py

ANALYSIS (post-hoc):
  scripts/threshold_sweep.py
  scripts/trigger_policy_eval.py
  scripts/windowing_ablation.py
  scripts/analyze_drift_across_datasets.py

THESIS TOOLING:
  scripts/extract_papers_to_text.py
  scripts/fetch_foundation_papers.py
  scripts/generate_thesis_figures.py
  scripts/regenerate_support_map.py
```

### Import Dependency Issues

| From | To | Status |
|------|----|--------|
| `scripts/run_ab_comparison.py` → `src/train.py` | ✅ Correct pattern |
| `scripts/preprocess.py` → `src/entity/*`, `src/components/*` | ✅ Correct pattern |
| `scripts/threshold_sweep.py` → `src/utils/temporal_metrics` | ✅ Correct pattern |
| `src/components/post_inference_monitoring.py` ← `scripts/post_inference_monitoring.py` | ❌ **Reversed!** Src depends on scripts |
| `src/components/baseline_update.py` ← `scripts/build_training_baseline.py` | ❌ **Reversed!** Src depends on scripts |

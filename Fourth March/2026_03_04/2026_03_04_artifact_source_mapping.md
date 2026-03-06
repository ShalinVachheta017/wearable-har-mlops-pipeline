# Pipeline Artifact Source Mapping
**Where each artifact field comes from — code-level traceability**

> Generated: 2026-03-04  
> Pipeline: `src/pipeline/production_pipeline.py`  
> Artifact entity definitions: `src/entity/artifact_entity.py`  
> Artifact writer: `src/utils/artifacts_manager.py`

---

## Overview

Every pipeline run creates a timestamped folder:

```
artifacts/<YYYYMMDD_HHMMSS>/
  run_info.json              ← start_time, stage completion log, end_time
  data_ingestion/            ← Stage 1
  validation/                ← Stage 2
  data_transformation/       ← Stage 3
  inference/                 ← Stage 4  ✦ enhanced 2026-03-04
  evaluation/                ← Stage 5
  monitoring/                ← Stage 6
  trigger/                   ← Stage 7  ✦ added 2026-03-04
```

Stages 8–14 (retraining, registration, baseline_update, calibration,
wasserstein_drift, curriculum_pseudo_labeling, sensor_placement) run only
when explicitly enabled and are written to additional subdirectories.

---

## Stage 1 — `data_ingestion/`

**Component**: `src/components/data_ingestion.py`  
**Artifact class**: `DataIngestionArtifact`  

### Files written
| File | Content |
|------|---------|
| `fused_csv_<timestamp>.csv` | Merged accelerometer + gyroscope data (copy) |

### Fields logged to `run_info.json`
| Field | Source in code | Example value |
|-------|---------------|---------------|
| `n_rows` | `DataIngestionArtifact.n_rows` | `385326` |
| `n_columns` | `DataIngestionArtifact.n_columns` | `6` |
| `sampling_hz` | `DataIngestionArtifact.sampling_hz` | `50` |
| `source_type` | `DataIngestionArtifact.source_type` | `"excel"` or `"csv"` |
| `ingestion_timestamp` | `DataIngestionArtifact.ingestion_timestamp` | ISO string |

### How ingestion works
`DataIngestion.initiate_data_ingestion()` scans `data/raw/` for the newest
accel/gyro pair (Excel or CSV), merges them on timestamp, resamples to 50 Hz,
and writes to `data/processed/sensor_fused_50Hz.csv`.

---

## Stage 2 — `validation/`

**Component**: `src/components/data_validation.py`  
**Artifact class**: `DataValidationArtifact`

### Files written
| File | Content |
|------|---------|
| `validation_report.json` | is_valid flag + errors + warnings |

### Fields
| Field | Source | Meaning |
|-------|--------|---------|
| `is_valid` | Schema + range checks pass | `true` / `false` |
| `errors` | List of hard failures | Missing columns, wrong dtype, value out of range |
| `warnings` | Non-fatal issues | e.g., optional column absent |

**Pipeline behaviour**: if `is_valid = false`, pipeline raises `DataValidationError`
and aborts. All downstream stages are skipped.

---

## Stage 3 — `data_transformation/`

**Component**: `src/components/data_transformation.py`  
**Artifact class**: `DataTransformationArtifact`

### Files written
| File | Content |
|------|---------|
| `production_X.npy` | Windowed array shape `(n_windows, 200, 6)` |
| `metadata.json` | Window count, flags, scaler params |

### Fields logged
| Field | Source | Notes |
|-------|--------|-------|
| `n_windows` | `DataTransformationArtifact.n_windows` | e.g., `1137` for 19 min session |
| `unit_conversion_applied` | `DataTransformationArtifact.unit_conversion_applied` | milliG → m/s² (×0.00981) |
| `gravity_removal_applied` | `DataTransformationArtifact.gravity_removal_applied` | high-pass filter |
| `normalization_applied` | `transformation_config.enable_normalization` | **StandardScaler** (mean=0, std=1) |
| `window_size` | 200 samples = 4 s at 50 Hz | fixed |
| `step_size` | 100 samples = 50 % overlap | fixed |

### Normalization decision
Evidence: labeled ground-truth accuracy **Norm ON 14.5% vs Norm OFF 10.6% (+3.9 pp)**.  
Full analysis: `Thesis_report/normalization_analysis.md`

---

## Stage 4 — `inference/`

**Component**: `src/components/model_inference.py`  
**Artifact class**: `ModelInferenceArtifact`

### Files written
| File | Content |
|------|---------|
| `predictions_<timestamp>.csv` | Per-window: predicted_activity, confidence, is_uncertain, confidence_level |
| `predictions_<timestamp>.npy` | Integer class indices array |
| `probabilities_<timestamp>.npy` | Softmax probability matrix `(n_windows, 11)` |
| `inference_summary.json` | All metrics below |

### Fields in `inference_summary.json`
| Field | How computed | Example |
|-------|-------------|---------|
| `n_predictions` | `len(results_df)` | `1137` |
| `inference_time_seconds` | `time.time() - t0` around `pipe.run()` (line 64–66) | `0.98` |
| `throughput_windows_per_sec` | `n_predictions / inference_time_seconds` | `1160.2` |
| `avg_ms_per_window` | `(inference_time_s / n_predictions) × 1000` | `0.862` |
| `activity_distribution` | `results_df["predicted_activity"].value_counts()` | `{"hand_tapping": 701, ...}` |
| `activity_share` | `count / n_predictions` per class | `{"hand_tapping": 0.616, ...}` |
| `confidence_stats.mean` | `conf.mean()` | `0.979` |
| `confidence_stats.std` | `conf.std()` | `0.021` |
| `confidence_stats.min` | `conf.min()` | `0.87` |
| `confidence_stats.max` | `conf.max()` | `0.9997` |
| `confidence_stats.median` | `conf.median()` | `0.991` |
| `confidence_stats.n_uncertain` | `results_df["is_uncertain"].sum()` | `2` |
| `confidence_stats.levels` | `confidence_level.value_counts()` | `{"HIGH": 1135, "LOW": 2}` |
| `model_version` | `Path(model_path).stem` | `"fine_tuned_model_1dcnnbilstm"` |

### Per-window time by activity
The model runs as a single vectorised batch (TF/Keras), so individual window
latency is not measurable per class. The correct thesis metric is:

```
avg_ms_per_window = total_inference_time_ms / n_windows
e.g.:  0.98 s / 1137 windows = 0.862 ms/window
```

To compare across activities, combine `avg_ms_per_window` with `activity_share`:

```
hand_tapping: 701 windows × 0.862 ms = 604 ms processing time share
```

---

## Stage 5 — `evaluation/`

**Component**: `src/components/model_evaluation.py`  
**Artifact class**: `ModelEvaluationArtifact`

### Files written
| File | Content | When present |
|------|---------|-------------|
| `report.json` | Full evaluation report | Always |
| `report.txt` | Human-readable summary | Always |
| `evaluation_summary.json` | Fields below | Always |

### Fields
| Field | Source | When populated |
|-------|--------|----------------|
| `has_labels` | Ground-truth labels present alongside predictions | Supervised run only |
| `distribution_summary` | Prediction distribution statistics | Always |
| `confidence_summary.mean` | Mean softmax confidence | Always |
| `confidence_summary.ece` | Expected Calibration Error | If calibration enabled |
| `classification_metrics.accuracy` | sklearn accuracy_score | `has_labels = true` only |
| `classification_metrics.f1_macro` | sklearn f1_score | `has_labels = true` only |
| `classification_metrics.per_class` | precision/recall/f1 per activity | `has_labels = true` only |

**Production runs** (unlabeled sensor data) → `has_labels = false`, evaluation
folder contains distribution + confidence stats but no accuracy/F1.

---

## Stage 6 — `monitoring/`

**Component**: `src/components/post_inference_monitoring.py`  
**Artifact class**: `PostInferenceMonitoringArtifact`

### Files written
| File | Content |
|------|---------|
| `monitoring_report_<timestamp>.json` | Full 3-layer report |
| `monitoring_summary.json` | Condensed fields below |

### 3-Layer monitoring fields

#### Layer 1 — Confidence
| Field | Meaning | Threshold |
|-------|---------|-----------|
| `mean_confidence` | Average softmax max-class probability | < 0.85 → WARNING |
| `std_confidence` | Confidence spread | high = unstable model |
| `uncertain_percentage` | % windows flagged is_uncertain | > 20% → WARNING |
| `mean_entropy` | Shannon entropy across class probs | high = uncertain |
| `status` | HEALTHY / WARNING / CRITICAL | — |

#### Layer 2 — Temporal stability
| Field | Meaning |
|-------|---------|
| `transition_rate` | % of consecutive windows with different prediction |
| `mean_dwell_time_seconds` | Average duration in one predicted activity |
| `short_dwell_ratio` | Ratio of dwells < minimum expected duration |
| `status` | HEALTHY / WARNING / CRITICAL |

#### Layer 3 — Distribution drift (Wasserstein)
| Field | Meaning |
|-------|---------|
| `n_drifted_channels` | # sensor channels exceeding drift threshold |
| `max_drift` | Peak Wasserstein distance across all channels |
| `per_channel_metrics` | Distance per channel: Ax, Ay, Az, Gx, Gy, Gz |
| `status` | HEALTHY / WARNING / CRITICAL |
| `overall_status` | Worst status across all three layers |

---

## Stage 7 — `trigger/`

**Component**: `src/components/trigger_evaluation.py` → `src/trigger_policy.py`  
**Artifact class**: `TriggerEvaluationArtifact`

> ⚠ This stage was not saving artifacts before 2026-03-04. Fixed in
> `production_pipeline.py` lines 480–504.

### Files written
| File | Content |
|------|---------|
| `trigger_decision.json` | All fields below |

### Fields
| Field | Source | Example values |
|-------|--------|----------------|
| `should_retrain` | `TriggerPolicyEngine.evaluate().should_trigger` | `true` / `false` |
| `action` | `decision.action.value` | `NONE` / `MONITOR` / `QUEUE_RETRAIN` / `TRIGGER_RETRAIN` / `ROLLBACK` |
| `alert_level` | `decision.alert_level.value` | `INFO` / `WARNING` / `CRITICAL` |
| `reasons` | `decision.recommendations` | `["Layer 3: Gx drift=0.48 > threshold 0.30", "Layer 1: uncertain_ratio=0.32 > 0.20"]` |
| `cooldown_active` | bool — prevents back-to-back retraining | `false` |

### How the trigger decision is made
The `TriggerPolicyEngine` evaluates the three monitoring layers in order:

```
Layer 1 check: mean_confidence < 0.85  OR  uncertain_ratio > 0.20
Layer 2 check: flip_rate > 0.40  OR  short_dwell_ratio > 0.30
Layer 3 check: n_drifted_channels >= 2  OR  aggregate_drift_score > 0.30
```

Each failing check adds a reason string. The worst alert level across all
checks determines the final action.

---

## `outputs/` and `reports/` — relationship to artifacts

### Current state
`outputs/` and `reports/` are **shared, run-agnostic** directories. Charts and
reports accumulate there across all runs without per-run isolation.

### Routing strategy
At end of each run, any file written to `outputs/` during that run (identified
by matching `*_fresh*` or timestamp suffix) can be copied into
`artifacts/<run_id>/outputs/` via:

```python
for f in pipeline_config.outputs_dir.glob("*_fresh*.png"):
    artifacts_manager.save_file(f, "outputs")
```

`reports/` is mixed-purpose. Keep governance/evidence files by default:
`DECISION_REGISTER.csv`, `EXTERNAL_REFERENCES.txt`, `PAPER_SUPPORT_MAP.json`,
`THRESHOLD_CALIBRATION.*`, `TRIGGER_POLICY_EVAL.*`, `ABLATION_WINDOWING.*`.
These do not need to be copied per run — the `run_info.json` can reference
them by path. Disposable verification outputs can be regenerated when needed.

### Safe cleanup summary

- Delete old `artifacts/<run_id>/` folders when they are no longer needed.
- Delete transient `outputs/*_fresh*` and timestamped prediction files freely.
- Keep cited thesis evidence in `reports/` unless you are intentionally regenerating it from the owning script.

---

## Fix summary (applied 2026-03-04)

| Change | File | Lines |
|--------|------|-------|
| Added `trigger_decision.json` save + `log_stage_completion` for Stage 7 | `src/pipeline/production_pipeline.py` | 480–504 |
| Added `throughput_windows_per_sec`, `avg_ms_per_window`, `activity_share` to `inference_summary.json` | `src/pipeline/production_pipeline.py` | 358–381 |
| Updated `log_stage_completion` for inference stage to include throughput metrics | `src/pipeline/production_pipeline.py` | 385–392 |

---

## Quick reference: artifact field → code location

| What you want to show | Artifact file | Field path |
|-----------------------|---------------|------------|
| Was data valid? | `validation/validation_report.json` | `.is_valid` |
| How many windows processed? | `data_transformation/metadata.json` | `.n_windows` |
| Was normalization on? | `data_transformation/metadata.json` | `.normalization_applied` |
| Total inference time | `inference/inference_summary.json` | `.inference_time_seconds` |
| Throughput | `inference/inference_summary.json` | `.throughput_windows_per_sec` |
| Avg time per window | `inference/inference_summary.json` | `.avg_ms_per_window` |
| Activity predictions | `inference/inference_summary.json` | `.activity_distribution` |
| Model confidence | `inference/inference_summary.json` | `.confidence_stats.mean` |
| Drift status | `monitoring/monitoring_summary.json` | `.layer3_drift.status` |
| Should retrain? | `trigger/trigger_decision.json` | `.should_retrain` |
| Why retrain? | `trigger/trigger_decision.json` | `.reasons[]` |
| Which layer triggered? | `trigger/trigger_decision.json` | `.reasons[]` prefix e.g. `"Layer 3:"` |

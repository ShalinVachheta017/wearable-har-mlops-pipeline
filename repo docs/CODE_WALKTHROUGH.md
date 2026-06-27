# Code Walkthrough — Every File, Annotated

> **What this is:** a guided read of the *actual* source, file by file, explaining what each
> piece does and **why it's written that way**. Grounded in the real code (not generic examples).
> Pair it with `PROJECT_DEEP_DIVE.md` (the *why* of the design) and `BUILD_FROM_SCRATCH.md` (the *how* to rebuild).

> **How to read this:** each stage section gives ① the file, ② its one-line job, ③ the public
> method the orchestrator calls, ④ the important/subtle lines with the reasoning, and ⑤ gotchas.
> Line numbers are approximate — open the file alongside.

---

## Map of the codebase

```
run_pipeline.py                         ← CLI entrypoint
└─ src/pipeline/production_pipeline.py   ← ORCHESTRATOR (the conductor)
   ├─ src/entity/config_entity.py        ← every stage's Config (the "what")
   ├─ src/entity/artifact_entity.py      ← every stage's Artifact (the "result")
   └─ src/components/                     ← one file per stage (the "how")
      ├─ data_ingestion.py        (S1)
      ├─ data_validation.py       (S2)
      ├─ data_transformation.py   (S3)
      ├─ model_inference.py       (S4)
      ├─ model_evaluation.py      (S5)
      ├─ post_inference_monitoring.py (S6)
      ├─ trigger_evaluation.py    (S7)   → wraps src/trigger_policy.py
      ├─ model_retraining.py      (S8, optional)
      ├─ model_registration.py    (S9, optional)
      ├─ baseline_update.py       (S10, optional)
      └─ calibration_uncertainty.py (S11, optional)

src/api/app.py                          ← FastAPI WebUI (the serving surface)
src/config.py                           ← all paths + model constants (single source)
src/utils/label_mapping.py              ← the 11-class id↔name mapping
```

The repeating shape (learn it once): **Config in → Component does one job → Artifact out**, and the
orchestrator chains the artifacts. Every component method is wrapped in try/except that logs and
re-raises — so a failure is always traced to the exact stage.

---

## The contracts — `src/entity/config_entity.py` and `artifact_entity.py`

These two files are the backbone. Read them first; everything else just fills them in.

**`config_entity.py`** — one frozen-ish `@dataclass` per stage holding *settings only* (no logic).
Key defaults that define the deployed system:

| Config | Decisive default | Meaning |
|---|---|---|
| `DataTransformationConfig.window_size` | `200` | 4 s at 50 Hz |
| `DataTransformationConfig.overlap` | `0.5` | 50% overlap → 100-sample stride |
| `DataTransformationConfig.enable_unit_conversion` | `True` | milliG → m/s² is applied |
| `DataTransformationConfig.enable_normalization` | dataclass `False`, **but production YAML sets `true`** | applies the z-score scaler — the deployed contract (`False` is only the paper/A-B fallback) |
| `DataTransformationConfig.enable_gravity_removal` / `enable_calibration` | `False` | optional A/B only |
| `ModelInferenceConfig.confidence_threshold` | `0.50` | per-window "uncertain" cutoff |
| `PostInferenceMonitoringConfig.confidence_warn_threshold` | `0.70` | Layer-1 mean-confidence warn |
| `…transition_rate_threshold` | `35.0` | Layer-2 flip-rate warn (%) |
| `…drift_zscore_threshold` | `1.8` | Layer-3 per-channel z warn |
| `…dominant_class_warn/critical_threshold` | `85.0 / 95.0` | Layer-1b collapse guard (%) |
| `…baseline_mode` | dataclass `"raw_physical"` | must match the run's input space; the deployed (scaled) serving path uses the scaled baseline |
| `TriggerEvaluationConfig.drift_zscore_warn/critical` | `2.0 / 3.0` | Stage-7 escalation |
| `TriggerEvaluationConfig.cooldown_hours` | `24` | retrain cooldown |

> 🔑 The dataclass *comment* says *"Paper-aligned default is raw physical units. Enable normalization
> only for A/B checks"* — but that's the **fallback**, not production. `config/pipeline_config.yaml`
> sets `enable_normalization: true` (with `garmin_train_scaler.json`), because the deployed Model D1
> was **trained on z-score-scaled windows**. So the deployed pipeline **does** scale; "raw physical
> units" is the paper/A-B path only.

**`artifact_entity.py`** — one `@dataclass` per stage holding *outputs only*, plus `PipelineResult`
which aggregates everything. Notable fields that encode the thesis story:
- `TriggerEvaluationArtifact.auto_retrain` — commented *"always False for unlabeled production inference."*
- `ModelEvaluationArtifact.distribution_dominance_warning` — *"Does NOT trigger retraining"* (informational).
- `DataTransformationArtifact.production_y_path` — set only when a label column exists (labeled vs unlabeled is data-driven, not a flag you flip).

---

## The orchestrator — `src/pipeline/production_pipeline.py`

**Job:** run the requested stages in order, pass each artifact to the next, log everything, never
let a silent failure through.

**The dispatch table (≈line 176).** Instead of a giant if/elif, stage name → handler method:
```python
_DISPATCH = {
    "ingestion": self._run_ingestion, "validation": self._run_validation,
    "transformation": self._run_transformation, "inference": self._run_inference,
    "evaluation": self._run_evaluation, "monitoring": self._run_monitoring,
    "trigger": self._run_trigger, "retraining": self._run_retraining,
    "registration": self._run_registration, "baseline_update": self._run_baseline_update,
    "calibration": self._run_calibration,
}
```
**Why:** adding a stage = add one dict entry + one method. The run loop stays untouched.

**The shared `ctx` dict (≈line 159).** Artifacts live here (`ingestion_art`, `transformation_art`, …)
so any handler can reach what earlier stages produced, plus cross-cutting state
(`dataset_has_labels`, `collapse_signals`, `update_baseline`).
**Why a dict, not attributes:** the handlers are uniform `(result, ctx) -> signal`; the ctx is their
shared scratchpad. A returned `"SKIP"` / `"BREAK"` string controls the loop.

**The run loop (≈line 192).** For each stage: call the handler; append to `stages_completed` /
`stages_skipped` / `stages_failed`; log the stage to MLflow if tracking is on.
Two deliberate exception rules:
- `except DataValidationError: raise` — a validation failure is **fatal**, always (fail-fast).
- `except Exception: … if not continue_on_failure: break` — any other stage error stops the run
  unless you explicitly opted into `continue_on_failure`.

**Final status (≈line 219).** `SUCCESS` if nothing failed, `PARTIAL` if some completed and some
failed, `FAILED` if nothing completed — computed in a `finally:` so it's set even on a crash.

**Lazy imports inside each handler** (e.g. `from src.components.model_inference import ModelInference`
inside `_run_inference`). **Why:** TensorFlow is heavy; importing it only when Stage 4 actually runs
keeps `--help` and ingestion-only runs fast.

**Governance lives here too:**
- `_run_retraining` (≈line 652) returns `"SKIP"` if the dataset is unlabeled **or** if the trigger
  said `should_retrain=False` (unless `force_retraining`). Supervised retraining requires labels.
- `_run_baseline_update` sets `promote_to_shared = ctx["update_baseline"]` — by default the rebuilt
  baseline is saved only as an MLflow artifact, never silently overwriting the shared one.

> 🎯 **Defense line:** "My orchestrator is a dispatch table over uniform `(result, ctx)` handlers.
> Validation failure is fatal; everything else respects a `continue_on_failure` flag; retraining
> self-skips without labels and a passing trigger. The no-auto-retrain rule is enforced in the
> conductor, not buried in a component."

---

## The config factory — `src/pipeline/pipeline_config_factory.py`

**Job:** turn CLI args + `config/pipeline_config.yaml` into the typed `*Config` objects the
orchestrator needs. This is the one place where "what the user asked for" becomes "settings the
stages read."

**Public function:** `build_runtime_configs(args) -> PipelineRuntimeConfigs` (a container of all 11
configs). It layers settings in priority order: **YAML defaults → CLI overrides**. For example
`enable_normalization` defaults to the YAML value (itself `False`), and `--enable-normalization` /
`--no-normalization` can flip it; `--no-unit-conversion`, `--gravity-removal`, `--calibrate`,
`--model`, `--labels`, `--epochs`, `--skip-cv`, `--auto-deploy`, `--mc-dropout-passes` similarly map
onto config fields. Monitoring/trigger configs come from `load_monitoring_config()` /
`load_trigger_config()`, with an optional `config/pipeline_overrides.yaml` applied on top.

**The runtime-contract guard `_ensure_runtime_contract_consistency` (≈line 102) — this is the F3
code.** The model path (CLI / `DEFAULT_MODEL_PATH`) and the scaler path (YAML) are *two independent
sources of truth*; if they disagree, inference silently normalizes with the wrong statistics. The
guard resolves the model's contract folder and:
- if `scaler_path` is unset → derives it from the model folder (or **raises** if none exists there);
- if `scaler_path` is in a *different* folder than the model → **warns and overrides** to the model's
  folder (or raises if no scaler there to recover with).

> 🔑 **Crucial detail:** the very first line is `if not transformation_cfg.enable_normalization:
> return`. Since production sets `enable_normalization: true` in the YAML, **this guard is active in
> production** — it ensures the active scaler (`garmin_train_scaler.json`) comes from the same contract
> folder as the active model. (If you ran with the raw/A-B fallback, `enable_normalization=False`, the
> guard would be a no-op — but that's not the deployed configuration.)

---

## Stage 1 — Ingestion (`src/components/data_ingestion.py`)

**Job:** turn whatever raw input exists into one canonical fused 50 Hz CSV with columns
`true_time, Ax, Ay, Az, Gx, Gy, Gz (+ optional label)`.

**Public method:** `initiate_data_ingestion()` (≈line 472) picks one of three input modes:
1. `config.input_csv` set → `_ingest_input_csv()` (a pre-fused CSV/Excel you provide).
2. `config.accel_file` + `gyro_file` set → `_ingest_sensor_pair()`.
3. neither → `_find_latest_sensor_pair()` auto-discovers the newest accel/gyro pair in `data/raw/`.

**The subtle bits:**
- **Column aliasing** (`DIRECT_SENSOR_ALIASES`, `RAW_AXIS_ALIASES`, `_normalize_key`): Garmin exports
  use many names (`accelX`, `calibratedAccelX`, `Ax_w`…). Everything is normalized to `Ax…Gz` so the
  rest of the pipeline sees one schema. **Why:** isolate messy real-world naming at the very edge.
- **Garmin list cells** (`_parse_list_cell`, `_explode_rows`): a single Garmin row can hold a *list*
  of samples; `_filter_valid_rows` drops rows whose x/y/z/offset list lengths disagree, then
  `explode` turns one row into one-sample-per-row. **Why:** the device batches samples; the model needs
  a flat stream.
- **Timestamp construction** (`_create_timestamps`, `_parse_timestamp_series`): handles `true_time`,
  `timestamp` (s or ms — auto-detected by magnitude `> 1e11`), `timestamp_iso`, `timestamp_ms`, plus
  sub-sample offsets. **Why:** the merge depends on a real time axis.
- **Fusion** (`_merge_and_resample`, ≈line 397): `pd.merge_asof(direction="nearest", tolerance=1ms)`
  aligns gyro to accel, then `resample("20ms").mean().interpolate(limit=2)` puts both on an exact
  50 Hz grid. It logs the match rate. **Why nearest+tolerance:** accel and gyro samples are never at
  *exactly* the same instant; nearest-within-1ms is the honest join.
- **Label detection** (`_detect_label_column`): only trusts known ground-truth column names and
  excludes non-ground-truth ones — so a stray column never gets mistaken for labels.

**Output:** `DataIngestionArtifact(fused_csv_path, n_rows, n_columns, sampling_hz, has_labels, label_column, …)`.

> ⚠️ **Gotcha:** the fused filename is dataset-derived (`fused_<dataset>_50Hz.csv`), and sorting for
> "latest" uses the **recording timestamp parsed from the filename**, not file mtime (which the
> pipeline itself perturbs). That's why `_filename_recorded_ts` exists.

---

## Stage 2 — Validation (`src/components/data_validation.py`)

**Job:** prove the fused CSV is safe to transform; abort the whole pipeline if not. *"One file, one
stage, one validation report."*

**Public method:** `initiate_data_validation()` → `_validate_dataframe()` runs the checks and returns
a `ValidationResult(is_valid, errors, warnings, stats)`. The orchestrator raises `DataValidationError`
when `is_valid` is False — the one fatal stage.

**The checks, and the judgment in each:**
- **Required columns** — all of `Ax…Gz` present, else error.
- **Numeric coercion** — text columns that *parse* to numbers become a warning + are fixed in place;
  text that *fails* to parse is an error. **Why:** tolerate "stored as string" CSVs, reject genuine junk.
- **Missing values** — per-channel missing ratio; `> max_missing_ratio (5%)` is an error, any missing
  is a warning.
- **Timestamps** (`_validate_timestamps`) — invalid ratio, **duplicates (error)**, **non-monotonic
  gaps (error)**, large gaps `> 2.5× expected period` (warning). **Why so strict:** windowing and
  flip-rate assume monotonic, de-duplicated time.
- **Sampling frequency** — median gap → actual Hz; deviation `> tolerance (10%)` from 50 Hz is a warning.
- **Unit-aware ranges** (`_detect_acceleration_unit` + `_validate_sensor_ranges`): it first *detects*
  milliG vs m/s² from the **magnitude** (median |a| ≈ 9.8 → m/s²; ≈ 1000 → milliG), then applies the
  right threshold. **Why:** a fixed "max 50" threshold would false-alarm on milliG data.
- **Gyro clipping** (`_check_gyro_clipping`): `> 10%` of samples above the FS ceiling (500 deg/s) is an
  **error** ("data saturated, re-record"); occasional spikes are a warning. **Why:** saturation is
  unrecoverable; spikes are tolerable.

**Output:** `DataValidationArtifact(is_valid, errors, warnings, stats)` — `stats` is a rich,
JSON-safe dict (every threshold + every measured value) that becomes `validation_report.json`.

> 🎯 **Defense line:** "Validation is unit-aware: it detects milliG vs m/s² from signal magnitude
> before range-checking, so it never false-alarms on a legitimate unit. Saturation is fatal; isolated
> spikes are warnings."

---

## Stage 3 — Transformation (`src/components/data_transformation.py`)

**Job:** fused CSV → the audited model tensor `production_X.npy` of shape `[n_windows, 200, 6]`
(+ `production_y.npy` when labels exist), with a full audit report.

**Public method:** `initiate_data_transformation()` runs a fixed sequence, capturing channel stats
*before and after each step* (that's the audit trail):
```
load CSV → detect format → unit conversion → experimental transforms → normalization → windowing → save
```

**The steps, and the reasoning:**
- **`_detect_format`** locks the 6 sensor columns and labeled/unlabeled format.
- **`_apply_unit_conversion`** (≈line 220): detects the accel unit (`> 100` ⇒ milliG, `< 50` ⇒ m/s²,
  else *ambiguous → raises*) and multiplies milliG by `0.00980665`. Gyro is coerced, never converted.
  **Why raise on ambiguous:** silently guessing the unit is exactly how HAR models break.
- **`_apply_experimental_transforms`**: gravity removal / calibration, both **off by default** (A/B only).
- **`_apply_normalization_if_enabled`** (≈line 294): **this is the scaler step.** In production
  (`enable_normalization: true` from the YAML) it loads `garmin_train_scaler.json`, *checks the variant
  in the JSON matches the requested variant*, and applies the z-score transform — setting
  `model_input_space = "zscore_scaled"`. **Why the variant check:** prevents applying a robust scaler
  where zscore was intended (silent corruption). Only in the fallback/A-B mode (`enable_normalization=False`)
  does it skip scaling and report `raw_physical_units_ms2_dps`.
- **`_create_windows`**: delegates to `UnifiedPreprocessor.create_windows` (in `src/preprocess_data.py`)
  using `window_size=200, overlap=0.5`; for labeled data it wires the 11-class `activity_to_label` map.
- **`_save_outputs`**: writes `production_X.npy`; writes `production_y.npy` only if `y` exists, and
  **explicitly ignores a stale `production_y.npy`** from a previous labeled run if the current input is
  unlabeled (logs it). **Why:** prevents Stage 5 from evaluating new predictions against old labels.
- **`_quality_checks`**: NaN/inf, constant channels, all-zero channels on the final tensor.

**Output:** `DataTransformationArtifact(production_X_path, production_y_path?, n_windows, window_size,
unit_conversion_applied, normalization_applied, model_input_space, channel_order, …)` +
`transformation_report.json` with the before/after channel stats.

> ⚠️ **Gotcha (the big one):** *unit conversion ≠ normalization* — they are two separate steps. Stage 3
> first converts milliG→m/s² (physical units), **then** applies the z-score scaler (in production). The
> model eats **scaled** windows; the drift baseline must be the **scaled** baseline to match. (Watch the
> dataclass default `enable_normalization=False` — it's the paper/A-B fallback, *not* what production runs.)

---

## Stage 4 — Inference (`src/components/model_inference.py`)

**Job:** load the model + the Stage-3 tensor, predict, and emit rich prediction artifacts + an
evidence report.

**Public method:** `initiate_model_inference()` → `run_inference()` orchestrates:
`validate_activity_mapping → load_model → load_input_tensor → predict → build_report → save_outputs → log_mlflow`.

**The contract enforcement (why this stage is strict):**
- `EXPECTED_MODEL_INPUT = (None, 200, 6)`, `EXPECTED_MODEL_OUTPUT = (None, 11)` — `load_model` **raises**
  if the loaded model's shapes don't match. **Why:** a wrong model is caught at load, not via garbage
  predictions.
- `load_input_tensor` re-checks the window shape is `(200, 6)`, dtype, and **`np.isfinite(...).all()`**
  (rejects NaN/inf from Stage 3).
- `validate_activity_mapping` asserts the 11-class map is exactly `0..10` and `hand_tapping == 4`
  (the canonical anchor). **Why:** a shuffled label map would silently relabel everything.
- **No scaling happens *here* — because Stage 3 already did it.** `predict()` calls `model.predict(data)`
  directly on the Stage-3 tensor, which is already z-score-scaled in production. (Stage 4 is just
  inference; the scaler lives in Stage 3 / the WebUI's `_apply_final_model_scaler`.) It then verifies
  probabilities are finite and **each row sums to 1.0 ± 1e-5**.

**The evidence it computes per window:** predicted class + activity name, confidence (max softmax),
a `confidence_level` band (HIGH/MODERATE/LOW/UNCERTAIN), `is_uncertain` (≤ threshold), **entropy**, and
**top-2 margin** — plus per-class probabilities. **Why entropy & margin:** confidence alone is a poor
uncertainty signal; entropy and margin add nuance for monitoring.

**Collapse evidence** (`build_report`): the dominant class %, and a `collapse_level`
(`NONE/WARNING_70/WARNING_90/CRITICAL_COLLAPSE`). **Why at inference:** it's the cheapest place to spot
"predicts one class for everything," and it's carried forward to Stage 6/7.

**`model_md5` / `_file_md5`:** hashes the model on every run (handles both a single `.keras` file and a
SavedModel **directory** by walking it deterministically). Recorded in the report + MLflow. **Why:** a
silent model swap changes the hash → detectable in run history.

**Output:** `ModelInferenceArtifact` (paths to predictions CSV/NPY, probabilities NPY, metadata,
`inference_report.json`; plus n_predictions, model_md5, confidence/entropy/margin stats, dominant
class/pct, collapse level). MLflow logging is best-effort (wrapped, warns on failure) so tracking
never breaks inference.

> 🎯 **Defense line:** "Stage 4 validates the model's input/output shape, the label map, and that every
> probability row sums to 1 — and it feeds the already-scaled Stage-3 windows to the model, matching how
> the model was trained. It hashes the model each run so provenance is auditable."

---

## Stage 5 — Evaluation (`src/components/model_evaluation.py`)

**Job:** analyze the Stage-4 predictions; compute supervised metrics **iff** labels are present,
otherwise distribution/confidence/temporal summaries only. *"Stays intentionally simple."*

**Public method:** `initiate_model_evaluation()` → `evaluate_predictions()`:
`read_predictions → validate_prediction_contract → read_labels → validate_label_alignment → summarize → save_reports`.

**The contract re-validation (`validate_prediction_contract`):** Stage 5 doesn't trust Stage 4
blindly — it re-checks the prediction CSV has all required columns + all 11 `prob_*` columns, that
numbers are finite, that `predicted_class ∈ 0..10`, that **`predicted_activity` matches the class via
the canonical map** (catches a label-map drift), that confidence ∈ [0,1], and that **probability
columns sum to 1 ± 1e-4**. **Why re-validate:** stages are independently testable; Stage 5 must be
correct even if Stage 4 changes.

**Labeled vs unlabeled (the label-optional design):**
- `read_labels` loads `production_y.npy` if configured/available; checks it's 1-D, finite, and all ids
  are canonical.
- `validate_label_alignment` **refuses to truncate** on a length mismatch — *"can poison evaluation."*
- The orchestrator (Stage 5 handler) auto-wires `labels_path` from Stage 3's `production_y_path` when
  it exists, so labeled data flows through without a manual flag.
- With labels → `_classification_metrics`: accuracy, macro precision/recall/F1, per-class
  `classification_report`, confusion matrix. Without labels → distribution + confidence + uncertainty
  + temporal only.

**`distribution_dominance_warning`:** True when the dominant class ≥ 95% (the critical threshold). The
artifact field comment is explicit: **informational, does NOT trigger retraining** — it's evidence for
Stage 6/7, not an action.

**Output:** `ModelEvaluationArtifact(report_json_path, report_text_path, distribution_summary,
confidence_summary, has_labels, classification_metrics?, distribution_dominance_warning, dominant_*)`
plus a human-readable `.txt` report.

> 🎯 **Defense line:** "Evaluation is label-optional by design: with ground truth it reports
> accuracy/F1/confusion; without it, only proxy summaries. It re-validates the prediction contract and
> refuses to truncate mismatched labels, so a metric is never computed on misaligned data."

---

## Stage 6 — Monitoring (`src/components/post_inference_monitoring.py` + `src/monitoring/`)

**Job:** run the three health layers on the run and produce a status. The component is a **config
resolver + safety guard**; the math lives in `src/monitoring/post_inference_monitor.py`
(`PostInferenceMonitor`), with drift detail in `src/monitoring/drift_monitor.py`.

**Public method:** `initiate_post_inference_monitoring()` resolves four inputs (predictions CSV,
`production_X.npy`, the baseline, the model), builds the monitor, and calls `monitor.run(...)`.

**The three layers (thresholds from `PostInferenceMonitoringConfig`):**
- **Layer 1 — confidence:** mean confidence `< 0.70` ⇒ WARNING; also the `% uncertain` windows and a
  **Layer-1b dominant-class collapse guard** (`> 85%` warn, `> 95%` critical), paired with a
  low-gyro-motion check to separate genuine stillness from collapse.
- **Layer 2 — temporal:** transition (flip) rate `> 35%` ⇒ WARNING, plus dwell-time context.
- **Layer 3 — drift:** per-channel z-score mean-shift `> 1.8` (default `drift_detector_mode =
  "zscore_mean_shift"`; MMD is available for offline audits).

**The baseline guard (`_resolve_baseline_path`) — the most important safety code in this stage.**
Because the drift baseline must match the run's input space — **scaled** for the deployed model
(the WebUI uses `garmin_train_scaled_baseline.json`), **raw** only for the paper/A-B path — the method:
1. selects the baseline for the active `baseline_mode` (`raw_physical` → `models/raw_physical_baseline.json`, `normalized`/scaled → the normalized baseline);
2. if missing → returns `DRIFT_BASELINE_MISSING` and **skips** Layer 3 (no fake numbers);
3. **reads the baseline's `feature_space` metadata** and, if `baseline_mode=raw_physical` but the file
   is `transformed`/normalized, returns `DRIFT_BASELINE_MISMATCH_REVIEW` and skips — *"raw Az ≈ −9.8
   vs normalized baseline mean ≈ 0 would produce fake-critical drift";*
4. warns if the baseline is older than `max_baseline_age_days (90)`;
5. if `is_training_session=True`, skips Layer 3 (self-comparison would be artificially clean).

**Calibration & MMD hooks:** `_resolve_calibration_temperature` loads Stage 11's `temperature.json`
(applies temperature scaling before Layer 1/3 if set); `_resolve_mmd_reference` finds the optional MMD
reference tensor.

**Chunked drift (in the orchestrator's `_run_monitoring`):** additionally runs `DriftMonitor` over
500-window chunks against `models/drift_reference.json` when present, appending a
`drift_monitor_chunked` block (max PSI, per-chunk drift). **Why chunks:** catch drift that emerges
partway through a long session.

**Output:** `PostInferenceMonitoringArtifact(overall_status, layer1_confidence, layer2_temporal,
layer3_drift, monitoring_report, report_path)`.

> 🎯 **Defense line:** "Monitoring fails *safe*: if the drift baseline is missing or in the wrong
> feature space, Layer 3 is skipped with an explicit status rather than emitting a fake-critical
> z-score. The unit-space guard is the safeguard that keeps the input-space contract honest."

---

## Stage 7 — Trigger (`src/components/trigger_evaluation.py` → `src/trigger_policy.py`)

**Job:** turn the Stage-6 monitoring artifact into a governed decision. The component is a thin
adapter; the policy lives in `src/trigger_policy.py` (`TriggerPolicyEngine`).

**Public method:** `initiate_trigger_evaluation()`:
1. builds a `TriggerThresholds` from config (confidence 0.65/0.50, drift z 2.0/3.0, flip 0.35/0.50),
2. builds a `CooldownConfig(24h)` with a `trigger_state.json` (so it won't re-fire during cooldown),
3. calls `engine.evaluate(report)` and maps the decision into `TriggerEvaluationArtifact`.

**`_build_trigger_report` (≈line 111)** is the interesting part: it flattens the three monitoring
layers + collapse + motion context into the engine's expected schema — converting percentages to
ratios (`transition_rate/100`, `uncertain_percentage/100`). **Why a translation layer:** keeps the
policy engine decoupled from the monitoring artifact's exact field names.

**Governance fields propagated** (note these are the no-auto-retrain contract, surfaced on the
artifact so callers don't dig into dicts): `should_retrain`, `auto_retrain` (False for unlabeled),
`review_required`, `label_required`, `qa_required`, `required_next_steps`, and a human-readable
`decision` label. Actions are `NONE / MONITOR / QUEUE_RETRAIN / TRIGGER_RETRAIN / ROLLBACK`.

> ⚠️ **Note:** Stage-6 thresholds are intentionally *tighter* than Stage-7 (warn early, escalate
> under voting). The config comment warns: *"Do not unify these without reading ch6 Threshold
> Calibration Gap."*

---

## Temporal smoothing — `_smooth_predictions()` in `src/api/app.py`

**Job:** de-noise single-window jitter for *reporting*, without touching the served output.

```python
SMOOTHING_WINDOW = 3   # ≈ 6 s of context (windows step every 2 s)

def _smooth_predictions(probabilities, window=3):
    # average the SOFTMAX VECTORS over [i-1, i, i+1], then argmax  → "soft vote"
    half = window // 2
    for i in range(n):
        lo, hi = max(0, i-half), min(n, i+half+1)
        averaged[i] = probabilities[lo:hi].mean(axis=0)
    return averaged.argmax(axis=1), averaged.max(axis=1)
```

- **Soft vote, not hard vote:** it averages *probabilities* then argmaxes, so an isolated
  low-confidence flip is outvoted by confident neighbours, but a confident real change survives.
- **Additive:** raw predictions still drive the served output and monitoring; the smoothed view is
  reported *alongside* (`transition_rate_smoothed_pct`, `accuracy_smoothed`, `macro_f1_smoothed`).
- It's the "decision" stage of the Activity Recognition Chain (Bulling et al., 2014).

> 🎯 **Defense line:** "Smoothing is additive — I show raw and smoothed side by side, so it can't hide
> a genuinely unstable model; it just reveals how much instability was single-window jitter."

---

## Still to document (being appended)

This file is being built incrementally. Already complete above: the contracts, the orchestrator, and
Stages 1, 2, 3, 4, 7, plus temporal smoothing. **Remaining sections to append:**

- **Stage 5 — Evaluation** (`model_evaluation.py`): labeled vs unlabeled metrics, dominance warning.
- **Stage 6 — Monitoring** (`post_inference_monitoring.py` + `src/monitoring/`): the three layers in
  code, drift modes (z-score vs MMD), the chunked drift monitor.
- **`src/trigger_policy.py`** — the `TriggerPolicyEngine` voting + cooldown internals.
- **`src/pipeline/pipeline_config_factory.py`** — how CLI args become per-stage configs; the
  runtime-contract consistency check.
- **`src/api/app.py`** — the full serving flow: upload modes, the S1–S10 stage strip, the labeled
  eval card, `should_retrain=False`, MLflow logging.
- **Stages 8–11** (`model_retraining.py`, `model_registration.py`, `baseline_update.py`,
  `calibration_uncertainty.py`) — the optional, human-gated mutation path.
- **`run_pipeline.py`** — the CLI surface and flags.

---

*Built from a direct read of the source on 2026-06-17. Stages 1–4, 7 + orchestrator + contracts +
smoothing verified line-by-line; remaining stages appended as read.*

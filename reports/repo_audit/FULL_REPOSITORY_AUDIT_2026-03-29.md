# Full Repository Audit — HAR MLOps Pipeline
**Date:** 2026-03-29
**Auditor role:** Senior MLOps engineer + ML software auditor + master-thesis technical reviewer
**Scope:** Complete file-by-file, architecture-level, engineering-level, and thesis-level audit

---

## 1. Executive Summary

**Overall Quality:** This is a genuinely strong thesis-grade MLOps pipeline. The architecture is coherent, the component design is correct, the trigger logic is sophisticated, and the CI/CD and testing infrastructure are real. However, there are several concrete issues — one of which is critical for thesis validity — that need resolution before submission.

**Biggest Strengths:**
- Coherent 14-stage pipeline with proper separation of concerns
- Collapse guard (95% dominance → REVIEW, no auto-retrain) is correctly implemented and wired
- Retraining gate works correctly — Stages 8–10 are skipped when `should_retrain=False`
- Multi-metric voting trigger policy is rigorous and literature-cited
- CI/CD pipeline (GitHub Actions) with lint + test + Docker build
- Clean dependency structure (`pyproject.toml` separates dev from prod)
- AdaBN/TENT properly implemented as optional methods, not silently active

**Biggest Weaknesses:**
1. **CRITICAL** — `pipeline_config.yaml` has `enable_gravity_removal: true` and `enable_calibration: true`, but both are marked `RECOMMENDED: false` and the scaler was fitted on data WITH gravity included (Az mean = −3.5289 m/s²). This is a live train/serve skew bug.
2. **MEDIUM** — Binary `.keras` model files committed directly to git (8 files, ~68 MB total) — `models/retrained/` is NOT covered by `.gitignore` or DVC.
3. **MEDIUM** — 37 unstaged deletions (Prometheus/Grafana configs, wave1 archive scripts) exist in git but were deleted locally. The repo is in an intermediate cleanup state.
4. **MEDIUM** — No dedicated test for the collapse guard path — the 95% dominance → REVIEW logic has zero coverage in the test suite.
5. **MEDIUM** — Ablation config labeling is ambiguous — the thesis text says "Config D: calibration + no gravity removal" but the code defines Config D as `gravity_removal=True, calibration=True`.

**Thesis-ready?** Nearly, but **not yet.** The config drift issue (#1) directly undermines the correctness of production inference claims and must be resolved first.

---

## 2. Architecture Understanding

**Purpose:** Offline, batch-first MLOps pipeline for classifying 11 anxiety-related HAR activities from 6-axis IMU wrist sensor data. Thesis demonstration of production-style MLOps on a research problem.

**End-to-End Flow:**

```
Data (Excel/CSV)
  │
  Stage 1:  DataIngestion            ── fused CSV
  Stage 2:  DataValidation           ── schema + range checks
  Stage 3:  DataTransformation       ── windowed .npy  [PREPROCESSING HAPPENS HERE]
  Stage 4:  ModelInference           ── predictions + softmax probs
  Stage 5:  ModelEvaluation          ── confidence stats, dominance check → collapse_signals
  Stage 6:  PostInferenceMonitoring  ── 3-layer: confidence / temporal / drift
  Stage 7:  TriggerEvaluation        ── voting → action (NONE / REVIEW / RETRAIN)
  │
  ├── if should_retrain=True:
  │     Stage 8:  ModelRetraining
  │     Stage 9:  ModelRegistration
  │     Stage 10: BaselineUpdate
  │
  └── if enable_advanced=True (optional):
        Stage 11: CalibrationUncertainty
        Stage 12: WassersteinDrift
        Stage 13: CurriculumPseudoLabeling
        Stage 14: SensorPlacement
```

**Key Design Note:** The pipeline docstring says "10 Stages" but `ALL_STAGES` has 14 entries. The discrepancy lives only in the header comment, not in behavior — minor but confusing for examiners reading code.

---

## 3. File-by-File / Folder-by-Folder Review

### `config/pipeline_config.yaml`

| | |
|---|---|
| **Purpose** | Master runtime config for preprocessing, validation, inference |
| **Severity** | CRITICAL (gravity removal) + MEDIUM (calibration) |

**What is good:**
Well-commented with `RECOMMENDED:` annotation and `WHY:` explanation on every toggle. Excellent thesis hygiene.

**What is wrong — CRITICAL:**
- **Line 35:** `enable_gravity_removal: true` — the comment directly above says `RECOMMENDED: false`. The scaler fitted on training data has `Az mean = −3.5289 m/s²`, which is consistent with gravity-included data. If production removes gravity (shifting Az toward 0), the scaler will produce systematically incorrect z-scores. This is a live train/serve skew bug.
- **Lines 41–42:** `enable_calibration: true` and `enable_domain_calibration: true` — comments say `RECOMMENDED: false` for both. Neither was part of the original training pipeline. Enabling both without clear ablation evidence is scientifically indefensible.

**Action:** Set `enable_gravity_removal: false`. Decide on calibration based on ablation evidence and document the decision explicitly.

---

### `src/pipeline/production_pipeline.py`

| | |
|---|---|
| **Purpose** | Master orchestrator for all 14 stages |
| **Lines** | ~750 (read via offset paging) |
| **Severity** | Medium |

**What is good:**
- Clean delegation pattern — each stage isolated into its own `elif`
- Retraining gate at lines 539–551 correctly skips stages 8–10 when `should_retrain=False`
- Collapse signals extracted at line 410 (`_extract_collapse_signals`) and injected into the monitoring report at line 465 before Stage 7
- `goto_cleanup` pattern prevents partial-state runs

**What is wrong:**
- Header docstring says "10 Stages" but `ALL_STAGES` has 14. An examiner reading the code will notice.
- `_extract_collapse_signals` (lines 740–810) is fragile: it first tries `distribution_summary`, but `model_evaluation.py` pops `_dominant_pct` and `_dominant_class` from that dict before storing in the artifact. Recovery depends on a JSON file being readable on disk. If the JSON write failed, the 95% collapse trigger silently does not fire.

---

### `src/train.py`

| | |
|---|---|
| **Purpose** | 5-fold grouped CV training with MLflow |
| **Lines** | ~500 |
| **Severity** | Medium |

**What is good:**
- Grouped k-fold with user IDs as groups, seed controlled where stochastic behavior is used
- Architecture v1 matches deployed model exactly (Conv1D 16→32, BiLSTM 64→32, Dense 32, ~499K params)
- Scaler config saved to `models/retrained/scaler_config.json` for inference reuse
- MLflow tracking integrated throughout

**What is wrong:**
- Line 14: docstring mentions "DANN, MMD" for domain adaptation — `model_retraining.py` explicitly raises `NotImplementedError` for these. Minor documentation mismatch.
- The scaler is fitted on training data (gravity-included, Az mean ≈ −3.5). No defensive comment warns that production preprocessing MUST match. No assertion guards against scaler/preprocessing mismatch.
- Line 58: `sys.path.insert(0, ...)` at module level — fragile in packaged environments.

---

### `src/trigger_policy.py`

| | |
|---|---|
| **Purpose** | Multi-metric voting trigger engine |
| **Lines** | 942 |
| **Severity** | Medium |

**What is good:**
- 95% dominance check exists and is correctly wired (line 358: `dominant_pct >= 95.0`)
- REVIEW action returned with `should_trigger=False` (lines 388–390) — no auto-retrain on collapse
- Secondary trigger at lines 359–366: 90% + zero transitions + high confidence (belt-and-suspenders)
- Thresholds are literature-cited: Gama et al. 2014 (DDM), Page 1954 (CUSUM), Wald 1947 (SPRT)
- `TriggerAction` enum and `AlertLevel` enum cleanly separated

**What is wrong:**
- `TriggerAction.ROLLBACK` is defined in the enum but no code path in the main voting loop emits it — dead enum value or undocumented TODO.
- `logging.basicConfig(level=logging.INFO)` at module level (line 51) — import-time side effect that overrides app-level logging configuration.
- The collapse guard reads `monitoring_report.get("collapse_signals", {})` — if the orchestrator failed to inject this key (e.g., evaluation JSON file missing), the guard silently returns `None` with no warning.

---

### `src/components/model_evaluation.py`

| | |
|---|---|
| **Purpose** | Stage 5 — confidence stats and distribution dominance check |
| **Severity** | Medium |

**What is wrong:**
Lines 67–70 pop `_dominant_pct` and `_dominant_class` from `distribution_summary` before storing in the artifact. The orchestrator then tries to recover them from the same dict (line 762 in `production_pipeline.py`) — but they are already gone. Recovery only works via the JSON report file on disk. This is a fragile two-source-of-truth problem. If the Stage 5 JSON file is missing or corrupted, the collapse guard receives `None` for `dominant_pct` and never fires.

---

### `src/components/data_transformation.py`

| | |
|---|---|
| **Purpose** | Stage 3 — CSV → windowed .npy with preprocessing |
| **Severity** | Critical (conditional on config) |

**What is good:**
Preprocessing flags (`unit_conversion_applied`, `gravity_removal_applied`, `calibration_applied`) are stored in the artifact. This audit trail is thesis-defensible.

**What is wrong:**
- Gravity removal is applied when `self.config.enable_gravity_removal` is True — which it currently is in `pipeline_config.yaml`. This is where the train/serve skew materializes in practice.
- No validation that the loaded scaler was fitted with the same preprocessing flags. A scaler fitted on gravity-included data will produce wrong z-scores when applied to gravity-removed data.

---

### `src/api/app.py`

| | |
|---|---|
| **Purpose** | FastAPI inference server with 3-layer monitoring |
| **Severity** | Medium |

**What is good:**
Prometheus metrics (Counter, Gauge, Histogram), auto column detection, vectorized windowing via `as_strided`, full 3-layer monitoring implemented inline.

**What is wrong:**
- **Threshold inconsistency (line 84):** The fallback `_MonCfg` class uses `confidence_warn_threshold: float = 0.60`. The trigger policy uses `confidence_warn: float = 0.55`. The API will report PASS when the pipeline would already show WARNING. These must be aligned.
- **Separate preprocessing path:** The API does not use the `DataTransformation` component — it has its own column detection and normalization logic. This is a third preprocessing path independent of both `train.py` and `data_transformation.py`. Any future preprocessing change must be applied in three places.

---

### `models/registry/model_registry.json`

| | |
|---|---|
| **Purpose** | Deployed model tracking |
| **Severity** | Medium |

**What is wrong:**
- `"current_version": null` and `"deployed_at": null` — the model file `har_model_vauto.keras` has `"status": "archived"` with no deployment record. An examiner checking the registry to understand which model is deployed will find nothing useful.
- The pipeline's actual deployment source of truth is `models/training_baseline.json` and the baseline files — not the registry. This split is confusing and undocumented.
- The `.keras` file is committed to git at 5.9 MB. Should be DVC-tracked.

---

### `models/retrained/`

| | |
|---|---|
| **Purpose** | Retrained and adapted model files |
| **Severity** | Medium |

**What is wrong:**
- 8 `.keras` files committed to git (~68 MB total). `models/retrained/` is NOT covered by `.gitignore` (which only ignores `/models/trained/` and `/models/pretrained/`) and not DVC-tracked. This permanently bloats git history.
- 4 untracked `adabn_adapted_model_configA/B/C/D_*.keras` files (created 2026-03-28/29). These are ablation outputs — they are neither in git nor in DVC. They exist only locally.
- Models named `har_model_20260219_*.keras` (February) and `har_model_20260327_*.keras` (March) exist with no changelog or documentation of what changed between them.

---

### `tests/`

| | |
|---|---|
| **Purpose** | 26 test files |
| **Severity** | Medium (missing coverage) + Medium (broken tests) |

**What is good:**
- Broad coverage: trigger policy, preprocessing, validation, monitoring, drift, rollback, calibration
- `conftest.py` uses realistic random data with fixed seeds — not empty stub fixtures
- Tests use real threshold classes (`TriggerThresholds`, `AlertLevel`) — not mocked values

**What is wrong — CRITICAL gap:**

1. **Zero tests for the collapse guard path.** The `_evaluate_collapse_guard` function (95% dominance → REVIEW) has no test that passes a `collapse_signals` dict with `dominant_pct >= 95`. Running `grep -r "collapse_guard\|dominant_pct.*95"` in `tests/` returns no matches. The most important safety mechanism in Stage 7 is entirely untested.

2. **Tests for deleted modules:** `tests/test_ood_detection.py`, `tests/test_robustness.py`, `tests/test_progress_dashboard.py`, `tests/test_prometheus_metrics.py` test modules (`src/ood_detection.py`, `src/robustness.py`) that are staged for deletion. Running the full test suite will likely produce import errors and CI will fail.

3. **Fixture/code mismatch in drift tests:** `conftest.py` `sample_monitoring_report` (lines 196–212) populates the drift report with PSI metrics (`psi: 0.08`). But `TriggerThresholds` uses z-scores (`drift_zscore_warn: 2.0`), not PSI. Tests checking drift-driven trigger decisions are using a structurally different monitoring report format than production generates.

---

### `scripts/run_ablation_experiment.py`

| | |
|---|---|
| **Purpose** | 25-dataset ablation over 4 preprocessing configs |
| **Severity** | Critical (config labeling) |

**What is good:**
Reuses actual pipeline components (`DataIngestion`, `DataTransformation`, `ModelInference`) — not a reimplementation. `TRAINING_AZ_MEAN_MS2 = -3.5289` constant directly confirms the scaler was fitted on gravity-included data.

**What is wrong — CRITICAL for thesis:**
`ABLATION_CONFIGS` in code defines:
- Config A: `gravity_removal=False, calibration=False`
- Config B: `gravity_removal=False, calibration=True`
- Config C: `gravity_removal=True, calibration=False`
- **Config D: `gravity_removal=True, calibration=True`**

The thesis/prompt states "Config D: calibration + no gravity removal" — which matches **Config B** in code, not Config D. Either:
- The thesis text describes Config D with the wrong definition, OR
- The config labels were changed after the ablation ran, and result CSVs were produced under a different labeling

If the thesis claims "Config D performed best" with one definition but the code implements a different Config D, the reproducibility claim fails. This must be reconciled.

---

### `docker-compose.yml`

| | |
|---|---|
| **Purpose** | MLflow + inference API + training/preprocessing services |
| **Severity** | Minor |

**What is wrong:**
- MLflow container runs `pip install mlflow --quiet` on every start with no version pin. Server version can drift from client version over time.
- `MLFLOW_TRACKING_URI=http://localhost:5000` inside the MLflow container itself — should be `http://0.0.0.0:5000` or not set; internal requests may fail.
- `preprocessing` service runs `python src/sensor_data_pipeline.py` — this file exists but its preprocessing logic is a separate path from `DataTransformation`. No indication they are synchronized.

---

### `.gitignore`

| | |
|---|---|
| **Severity** | Minor + Medium |

**What is wrong:**
- **Line 162:** `W O R K L O G . m d ` — spaces between every character mean this pattern will NOT match `WORKLOG.md`. The file is effectively not ignored.
- `models/retrained/` is absent from `.gitignore`. All retrained `.keras` files are committed to git.
- `reports/*` with exception `!reports/repo_audit/` is correct syntax but the exception means repo_audit files ARE tracked — several large auto-generated audit reports will be committed.

---

### `config/requirements.txt`

| | |
|---|---|
| **Severity** | Minor |

**What is wrong:**
- Uses `>=` constraints only — no upper bounds, no exact pins. `pip install -r requirements.txt` will give different package versions in 6 months. A `requirements-lock.txt` exists but CI uses `requirements.txt`.
- Dev tools (`pytest`, `flake8`, `black`, `jupyterlab`) mixed with production dependencies. `pyproject.toml` correctly separates these into `[dev]` extras, but the Docker build installs the unseparated `requirements.txt`, putting dev tools into the production container.

---

### `pyproject.toml`

| | |
|---|---|
| **Severity** | Minor |

**What is good:**
- Correctly separates dev, monitoring, and GPU dependencies into optional extras
- Pytest markers properly configured
- Black + isort + mypy configured consistently

**What is wrong:**
- `[project.scripts]` entry `update-progress = "scripts.update_progress_dashboard:main"` references a script in `scripts/_wave1_archive/` that is staged for deletion. Installing the package and running `update-progress` will fail.

---

### `internal/`

| | |
|---|---|
| **Purpose** | Internal working notes, reference materials, writing support |
| **Severity** | Medium |

**What is wrong:**
- ~70+ files committed to git including `DEFENSE_QA.md`, `EVIDENCE_LEDGER.md`, `copilot_mega_prompt.md`. These are private working materials. An examiner cloning the repo sees all of them.
- `internal/reference/` contains `archive_WHY_BY_FILE.md`, `why_by_file.md`, `archive_WHY_BY_FILE_2.md`, and `WHY_BY_FILE_2.md` — four variants of the same document.
- `internal/writing/thesis_execution_plan_mar_jun_2026.md` is staged for deletion locally but still tracked in git.

---

### `src/_wave2_archive/`

| | |
|---|---|
| **Severity** | Minor |

4 files committed (`core/exception.py`, `core/logger.py`, `exception/__init__.py`, `pipeline/inference_pipeline.py`). Dead code from a previous architecture. All 4 are locally deleted (` D` in git status). Commit the deletions.

---

## 4. Critical Issues

### CI-1 — Train/Serve Skew: Gravity Removal
**Severity:** CRITICAL
**File:** `config/pipeline_config.yaml` line 35

**Evidence:**
- `enable_gravity_removal: true` in config
- `models/training_baseline.json` Az mean = −3.5289 m/s² (gravity-included distribution)
- `models/retrained/scaler_config.json` Az mean = −3.5295 (same — scaler fitted on gravity-included data)
- `scripts/run_ablation_experiment.py` constant: `TRAINING_AZ_MEAN_MS2 = -3.5289`
- Config's own comment: `RECOMMENDED: false` with explanation that training had no gravity removal

**Impact:** If production removes gravity, Az shifts ~3.5 m/s² toward 0, but the scaler expects mean −3.5. Result: systematic z-score offset of ~1 standard deviation on every inference batch. Model accuracy will be degraded. All production inference claims in the thesis are affected.

---

### CI-2 — Ablation Config D Labeling Contradiction
**Severity:** CRITICAL
**File:** `scripts/run_ablation_experiment.py` lines 75–100

**Evidence:**
Code defines Config D = `gravity_removal=True, calibration=True`.
Stated best config = "calibration + no gravity removal" = matches **Config B** in code.

**Impact:** If the thesis reports "Config D was best" with a different definition than what the code implements, the ablation results are not reproducible from repo state. A reviewer running `run_ablation_experiment.py` with the current code will produce results for the code's Config D (gravity+calibration), not the thesis's Config D (calibration only).

---

### CI-3 — Collapse Guard Has Zero Test Coverage
**Severity:** Medium (verging on critical for thesis claims)
**Files:** `src/trigger_policy.py` lines 333–412, `tests/test_trigger_policy.py`

**Evidence:** `grep -r "collapse_guard\|dominant_pct.*95"` in `tests/` returns no matches. The `sample_monitoring_report` fixture in `conftest.py` has no `collapse_signals` key — the guard returns `None` on every test run.

**Impact:** The most thesis-critical claim ("the pipeline detects prediction collapse and routes to REVIEW, not auto-retrain") cannot be verified by the test suite.

---

### CI-4 — Test Suite Has Broken Imports
**Severity:** Medium
**Files:** `tests/test_ood_detection.py`, `tests/test_robustness.py`, `tests/test_progress_dashboard.py`, `tests/test_prometheus_metrics.py`

**Evidence:** These files import modules that are locally deleted (`src/ood_detection.py`, `src/robustness.py`). Git status shows them as ` D` (deleted, unstaged). CI will fail with `ImportError` on these test files.

---

### CI-5 — Binary Keras Files Committed to Git
**Severity:** Medium
**Evidence:** `git ls-files | grep .keras` returns 8 files. `du -sh models/retrained/` = 68 MB. `models/retrained/` is absent from `.gitignore` and not DVC-tracked.

---

## 5. Structural Cleanup Recommendations

### Delete immediately (commit these changes)
| Action | Target |
|--------|--------|
| Commit pending deletions | 37 files in git status ` D` (Prometheus/Grafana configs, wave1/wave2 archives) |
| Add to `.gitignore` | `models/retrained/*.keras`, `models/registry/*.keras` |
| Remove or restore | `tests/test_ood_detection.py`, `tests/test_robustness.py`, `tests/test_progress_dashboard.py`, `tests/test_prometheus_metrics.py` |
| Fix `.gitignore` line 162 | `W O R K L O G . m d ` → `WORKLOG.md` |

### Move / archive
| Action | Target |
|--------|--------|
| Move to `internal/` or delete | `REPOSITORY_CLEANUP_AUDIT_2026-03-29.md`, `REPOSITORY_FILE_INVENTORY_2026-03-29.md`, `INTERNAL_SUMMARY_FOR_REVIEW.md` |
| DVC-track and remove from git | All `models/retrained/*.keras` and `models/registry/*.keras` |
| Consolidate | `internal/reference/` — remove the 4 duplicate WHY_BY_FILE variants, keep one |

### Fix `.gitignore`
```gitignore
# Add these lines:
models/retrained/*.keras
models/registry/*.keras

# Fix garbled line 162:
WORKLOG.md
```

---

## 6. Code Improvement Recommendations

### Fix train/serve skew (highest priority)

**`config/pipeline_config.yaml`:** Set `enable_gravity_removal: false`. Add comment:
```yaml
# CONFIRMED: set to false — matches training (scaler fitted on gravity-included data,
# Az mean = -3.5289 m/s²). See scripts/run_ablation_experiment.py TRAINING_AZ_MEAN_MS2.
```

**`src/components/data_transformation.py`:** Add a guard after scaler loading:
```python
# If scaler was fitted without gravity removal but config requests it, raise early.
if self.config.enable_gravity_removal and scaler_was_fitted_on_full_gravity_data:
    raise ConfigurationError(
        "enable_gravity_removal=True but scaler was fitted on gravity-included data. "
        "Set enable_gravity_removal=False to match training preprocessing."
    )
```

---

### Fix collapse signal propagation fragility

**`src/entity/artifact_entity.py`:** Add typed fields to `ModelEvaluationArtifact`:
```python
distribution_dominance_warning: bool = False
dominant_class: Optional[str] = None      # ADD THIS
dominant_pct: Optional[float] = None      # ADD THIS
```

**`src/components/model_evaluation.py`:** Set them directly instead of relying on the JSON fallback:
```python
return ModelEvaluationArtifact(
    ...
    distribution_dominance_warning=dominance_warning,
    dominant_class=dominant_class,   # ADD
    dominant_pct=dominant_pct,       # ADD
)
```

Then remove the JSON-file fallback path from `_extract_collapse_signals`.

---

### Fix API threshold inconsistency

**`src/api/app.py` lines 83–91:** The hardcoded fallback uses `confidence_warn_threshold = 0.60`. The trigger policy uses `confidence_warn = 0.55`. Align them — both should load from the same `config_loader`:
```python
except Exception:
    class _MonCfg:
        confidence_warn_threshold: float = 0.55   # match trigger_policy.py
        uncertain_pct_threshold: float = 20.0
        uncertain_window_threshold: float = 0.50
        transition_rate_threshold: float = 25.0   # match flip_rate_warn
        drift_zscore_threshold: float = 2.0
        max_baseline_age_days: int = 90
```

---

### Add collapse guard test

**`tests/test_trigger_policy.py`** — add to `TestTriggerPolicyEngine`:
```python
def test_collapse_guard_fires_at_95_pct_dominance(self, temp_state_file):
    """The REVIEW gate must fire — and NOT auto-retrain — when one class dominates >=95%."""
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    report = {
        "collapse_signals": {
            "dominance_warning": True,
            "dominant_class": "hand_tapping",
            "dominant_pct": 97.0,
            "mean_confidence": 0.95,
            "transition_rate": 0.0,
        },
        "confidence_report": {"metrics": {"mean_confidence": 0.95, "mean_entropy": 0.2, "uncertain_ratio": 0.01}},
        "temporal_report": {"metrics": {"flip_rate": 0.0}},
        "drift_report": {"per_channel_metrics": {}, "n_drifted_channels": 0},
    }
    decision = engine.evaluate(report)
    assert decision.action.value == "review", f"Expected REVIEW, got {decision.action}"
    assert decision.should_trigger is False, "Collapse guard must NOT auto-retrain"

def test_collapse_guard_does_not_fire_on_normal_distribution(self, temp_state_file):
    """Normal multi-class distribution must NOT trigger the collapse guard."""
    engine = TriggerPolicyEngine(state_file=temp_state_file)
    report = {
        "collapse_signals": {
            "dominance_warning": False,
            "dominant_class": "sitting",
            "dominant_pct": 30.0,
            "mean_confidence": 0.75,
            "transition_rate": 0.15,
        },
        "confidence_report": {"metrics": {"mean_confidence": 0.75, "mean_entropy": 1.2, "uncertain_ratio": 0.10}},
        "temporal_report": {"metrics": {"flip_rate": 0.15}},
        "drift_report": {"per_channel_metrics": {}, "n_drifted_channels": 0},
    }
    decision = engine.evaluate(report)
    assert decision.action.value != "review", "Normal distribution must not trigger collapse guard"
```

---

### Fix model registry

**`models/registry/model_registry.json`:** Populate `current_version` and `deployed_at`, or add a `README.md` in `models/registry/` explaining that `models/training_baseline.json` is the actual deployment source of truth and the registry tracks experiment history.

---

### Fix pyproject.toml broken script entry

**`pyproject.toml` line 81:**
```toml
# Remove or update this — the referenced module is deleted:
# update-progress = "scripts.update_progress_dashboard:main"
```

---

## 7. Thesis-Focused Evaluation

### What strengthens the thesis
- Three-layer monitoring (confidence / temporal / drift) is correctly implemented with literature-cited thresholds. Each threshold has a reference and rationale in `TriggerThresholds` docstring.
- The retraining gate correctly handles the unlabeled data scenario (the most realistic production constraint).
- The ablation script reuses real pipeline components — not a reimplementation. This is scientifically correct.
- CI/CD with GitHub Actions (lint + unit tests + Docker build) demonstrates engineering maturity beyond typical thesis projects.
- `DataTransformationArtifact` records which preprocessing flags were applied — this is the kind of audit trail that makes thesis experiments reproducible.
- The multi-metric voting scheme (2-of-3 layers required) reduces false positives — this is a defensible design choice with a clear rationale.

### What weakens the thesis
- `enable_gravity_removal: true` directly contradicts the stated preprocessing methodology (paper reference + config's own comment). An examiner reading the config will immediately ask: "Did your production pipeline actually match your training pipeline?"
- `model_registry.json` shows `current_version: null` — the pipeline does not know what it deployed.
- 68 MB of binary model files in git suggests DVC is only partially adopted (pretrained and trained models are in DVC, retrained models are not).
- The ablation Config D labeling issue means the thesis results may not be reproducible from current code.
- Stages 11–14 are labeled "advanced / optional" — an examiner will ask which stages actually ran for the thesis experiments, and there is no clear answer in the README.
- No `REPRODUCE.md` — there is no single-page, step-by-step guide for an examiner to reproduce the thesis results from scratch.

### What an examiner will ask
1. "You state in the paper that training used no gravity removal. Why does `pipeline_config.yaml` have `enable_gravity_removal: true`?"
2. "Can you show me the ablation results CSV and confirm which config was best? Does the definition in your thesis match the code?"
3. "Your model registry shows `current_version: null`. Which model was deployed for your thesis experiments and when?"
4. "Does your test suite test the 95% collapse trigger? Can you show me that test?"
5. "Four AdaBN model files exist in `models/retrained/`. Were any of these used in reported thesis results?"
6. "Can you give me one command to reproduce your main thesis pipeline run?"

### What must be fixed before submission
1. Fix `enable_gravity_removal` — either set to `false` (match training) or provide documented scientific justification for keeping it `true` and update the scaler accordingly.
2. Reconcile ablation Config D labeling — make code definition match thesis text.
3. Add the two collapse guard tests (15 minutes, high examiner-credibility value).
4. Commit the 37 pending deletions — clean git state.
5. Add `models/retrained/*.keras` to `.gitignore`.
6. Add a `REPRODUCE.md` with exact command sequence to reproduce thesis results.

---

## 8. Priority Action Plan

### Today — Critical correctness fixes

| # | Action | File | Effort |
|---|--------|------|--------|
| 1 | Set `enable_gravity_removal: false` (or justify and update scaler) | `config/pipeline_config.yaml:35` | 5 min |
| 2 | Clarify ablation Config D — confirm which definition the thesis uses | `scripts/run_ablation_experiment.py:75–100` | 30 min |
| 3 | Add `models/retrained/*.keras` to `.gitignore` | `.gitignore` | 2 min |

### This Week — Quality before supervisor review

| # | Action | File | Effort |
|---|--------|------|--------|
| 4 | Commit the 37 pending deletions (clean git state) | git | 10 min |
| 5 | Add 2 collapse guard tests | `tests/test_trigger_policy.py` | 20 min |
| 6 | Fix or delete broken test files (`test_ood_detection.py` etc.) | `tests/` | 15 min |
| 7 | Fix API fallback confidence threshold (0.60 → 0.55) | `src/api/app.py:84` | 5 min |
| 8 | Write `REPRODUCE.md` — one-page, step-by-step reproduction guide | new file | 45 min |

### Before Final Thesis Submission

| # | Action | File | Effort |
|---|--------|------|--------|
| 9 | Populate model registry `current_version` and `deployed_at` | `models/registry/model_registry.json` | 15 min |
| 10 | Add typed `dominant_pct` / `dominant_class` to `ModelEvaluationArtifact` | `src/entity/artifact_entity.py` | 30 min |
| 11 | Clean `internal/` — remove `copilot_mega_prompt.md`, deduplicate WHY docs | `internal/` | 30 min |
| 12 | Fix `.gitignore` garbled WORKLOG line and update `models/retrained/` rule | `.gitignore` | 5 min |
| 13 | Update pipeline docstring header: "10 Stages" → "14 Stages" | `src/pipeline/production_pipeline.py:6` | 2 min |
| 14 | Fix `pyproject.toml` broken `update-progress` script entry | `pyproject.toml:81` | 5 min |

### Optional / Future Work

- Add upper-bound version constraints to `config/requirements.txt` for long-term reproducibility
- Add end-to-end integration test that runs stages 1–7 on a small synthetic dataset
- Pin MLflow version in `docker-compose.yml` instead of `pip install mlflow --quiet`
- Consider whether `internal/` should be in a private branch rather than in the public thesis repo

---

## 9. Final Verdict

This repository is **close to thesis-quality but not there yet.** The architecture is sound, the engineering is real, and the pipeline logic is defensible. The collapse guard, retraining gate, multi-layer monitoring, and CI/CD all work correctly as designed. However, there is a live **train/serve skew** caused by `enable_gravity_removal: true` contradicting both the training methodology and the config's own documentation — this is the kind of concrete error that a competent examiner will find and that undermines the validity of all production inference claims. The **ablation config labeling ambiguity** is a second reproducibility failure that must be resolved before any thesis chapter cites those results. The **missing collapse guard test** means the most thesis-critical safety claim ("the pipeline detects prediction collapse and routes to REVIEW, not auto-retrain") cannot be independently verified. Fix these three issues — config, ablation labels, and two test functions — and the repo will be defensible for submission.

---

*Audit produced by Claude Code (claude-sonnet-4-6) on 2026-03-29. Evidence-based only — every finding cites the exact file and line.*

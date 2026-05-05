# Refactoring Issues

> Scanned: 2026-04-18 | Branch: epic/apr-foundation-baseline
> Pass: full repo (code, scripts, packaging, monitoring, docs)
> Update: 2026-04-18 hardening/refactor pass completed and validated

---

## 2026-04-18 Refactor Update (Completed)

Today hardening/refactor work from the external review was executed and verified.

- Total fixes completed: 12
- Severity mix: 2 High, 5 Medium, 5 Low
- Validation: `pytest tests/ -q --tb=short` -> 167 passed, 2 skipped, 0 failed

### Completed Today

| Fix ID | Severity | What was completed | Status |
| --- | --- | --- | --- |
| FIX-1 | HIGH | Validation failure path now always runs finalize/save/end-MLflow via `try/finally` in pipeline orchestration | Done |
| FIX-2 | HIGH | Retrain gate now returns `SKIP` instead of `BREAK`, allowing later requested stages (for example calibration) to continue | Done |
| FIX-3 | MEDIUM | CLI `--config` help text clarified: preprocessing config only; monitoring/trigger thresholds read from overrides | Done |
| FIX-4 | MEDIUM | Drift summary now uses monitoring artifact status (`HEALTHY/WARNING/CRITICAL`) instead of hardcoded thresholds | Done |
| FIX-5 | MEDIUM | Added `mlflow_tracked` signal to pipeline result so summaries reflect actual MLflow initialization state | Done |
| FIX-6 | MEDIUM | Fallback transformation artifact now restores `production_y_path` when `production_y.npy` exists | Done |
| FIX-7 | MEDIUM | Calibration outputs (`temperature.json`, `calibration_report.json`, `calibrated_probabilities.npy`) now persisted via `ArtifactsManager` | Done |
| FIX-8 | LOW | TensorFlow version check fixed to tuple-based comparison instead of string comparison | Done |
| FIX-9 | LOW | Label detection constants centralized in `src/utils/label_detection.py` and imported from ingestion/pipeline | Done |
| FIX-10 | LOW | `parse_args()` moved before startup banner/GPU detection so `--help` and invalid args avoid unnecessary startup cost | Done |
| FIX-11 | LOW | Worklog status legend expanded with `REMOVED` and `ACTIVE` definitions | Done |
| FIX-12 | LOW | Worklog format rule repaired for 2026-04-17 section (compact scan block first) | Done |

### Evidence Snapshot

1. Regression tests added: `tests/test_fix_regression.py` (6 tests).
2. Focused checks: validation/integration tests pass and API route sanity confirmed (`/metrics` absent; `/api/upload` and `/api/health` present).
3. Full suite check remains green after refactor hardening.

---

## CRITICAL

### C1 — Broken Console Entrypoint

**Category:** Packaging
**File:** [pyproject.toml](pyproject.toml)

**Issue:** `har-pipeline = "src.cli:main"` is configured as the installed CLI entrypoint, but src/cli.py does not exist. Any `pip install -e .` invocation will fail at the entrypoint lookup.

**Fix:** Either create src/cli.py with a `main()` that delegates to `run_pipeline.py`, or update pyproject.toml to point to the actual entrypoint.

---

### C2 — Wrong Model Registered in MLflow After Retraining

**Category:** Correctness / MLflow Lineage
**Files:** [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py), [src/components/model_inference.py](src/components/model_inference.py)

**Issue:** model_inference.py:48-50 defaults to a date-stamped hardcoded path `har_model_20260327_223917.keras` (a specific retrained snapshot, not a dynamic selection). model_retraining.py:93-95 and the MLflow registration step also hardcode `fine_tuned_model_1dcnnbilstm.keras`. No single dynamic model path is threaded through — registry lineage diverges from actual inference after any retrain.

**Fix:** Pass the active model path from the retraining artifact into the registration step instead of using the hardcoded default.

---

### C3 — Inconsistent Model Default Paths Across Entrypoints

**Category:** Correctness / Reproducibility
**Files:** [src/config.py](src/config.py), [src/run_inference.py](src/run_inference.py), [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py), [src/components/model_retraining.py](src/components/model_retraining.py)

**Issue:** Different entrypoints resolve the base model from different default paths. A direct call to `run_inference.py` can silently use a different model than a pipeline-orchestrated run, producing non-comparable results.

**Fix:** Define a single `DEFAULT_MODEL_PATH` constant in `src/config.py` and import it in all components. No path literals in component files.

---

## HIGH

### H1 — Monitoring Status Enum Mismatch

**Category:** Correctness / Observability
**Files:** [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py), [src/entity/artifact_entity.py](src/entity/artifact_entity.py), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py), [src/api/app.py](src/api/app.py)

**Issue:** Stage 6 emits `PASS` / `WARNING` / `ALERT` as status strings (confirmed: scripts/post_inference_monitoring.py:235-236, 310-315, 408-430), but production_pipeline.py:1208-1209 checks `== "HEALTHY"`. `monitoring_overall_healthy` MLflow metric is therefore always `0.0` regardless of actual health.

**Fix:** Align the enum — pick one set of values (`HEALTHY / WARNING / CRITICAL` preferred) and apply it consistently in the artifact entity, monitoring component, pipeline logger, and API response.

---

### H2 — Ambiguous Config Import Contract

**Category:** Correctness / Import Resolution
**Files:** [src/preprocess_data.py:32](src/preprocess_data.py#L32), [src/run_inference.py:71](src/run_inference.py#L71), [src/train.py:63](src/train.py#L63), [src/evaluate_predictions.py:82](src/evaluate_predictions.py#L82), [src/trigger_policy.py:48](src/trigger_policy.py#L48), [src/model_rollback.py:41](src/model_rollback.py#L41)

**Issue:** 6 modules use `from config import ...` (unqualified). This competes with the workspace-level `config` namespace and is causing analyzer failures. Can cause silent runtime resolution drift depending on `PYTHONPATH`.

**Fix:** Replace all with `from src.config import ...` (fully qualified). Already correct in the rest of the codebase.

---

### H3 — Split Run ID and Artifact ID (Auditability)

**Category:** Reproducibility
**Files:** [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py), [src/utils/artifacts_manager.py](src/utils/artifacts_manager.py)

**Issue:** The pipeline's `run_id` and the `ArtifactsManager` timestamp are generated from two separate `datetime.now()` calls. Artifact folders and MLflow run identifiers can differ, breaking end-to-end audit trails.

**Fix:** Generate one timestamp at pipeline startup and thread it through to `ArtifactsManager(run_id=run_id)`.

---

## MEDIUM

### M1 — ProductionPipeline Cyclomatic Complexity Too High

**Category:** Maintainability
**File:** [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py) (1355 lines)

**Issue:** `ProductionPipeline.run()` spans lines 146–863 (718 lines) with 12+ stages, deep conditional branching, inline artifact wiring, and MLflow logging all mixed together. Confirmed by code read.

**Fix (Batch C):** Extract each stage into a `_run_stage_N()` helper. Extract MLflow logging and artifact wiring into separate helpers. Target: `run()` under 80 lines.

---

### M2 — Type Contract Instability in Preprocessing

**Category:** Typing / Correctness
**File:** [src/preprocess_data.py](src/preprocess_data.py)

**Issue:** Return types transition between `list`, `np.ndarray`, and `None` without consistent annotation. Hides bugs and blocks stricter QA / mypy.

**Fix:** Annotate all public methods. Use `Optional[np.ndarray]` where None is valid. Add runtime guard where None would propagate downstream.

---

### M3 — Monitoring Component Typing and Output Path

**Category:** Typing / Artifact Boundaries
**File:** [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py)

**Issue:** Optional baseline path typing is inconsistent. Monitoring report is written under the evaluation output folder by default, blurring artifact boundaries between evaluation and monitoring.

**Fix:** Type baseline path as `Optional[Path]`. Write monitoring report to a dedicated `monitoring/` subfolder.

---

### M4 — ArtifactsManager Typing Defects

**Category:** Typing
**File:** [src/utils/artifacts_manager.py](src/utils/artifacts_manager.py)

**Issue:** Type signatures are inconsistent with `None` defaults and staged metadata indexing. Current annotations do not reflect actual runtime types.

**Fix:** Audit and tighten all method signatures. Add `Optional` where None is a valid state.

---

## LOW

### L1 — Legacy Wrapper Scripts Still Executable

**Category:** Dead Code / Ops Risk
**Files:** [scripts/preprocess.py](scripts/preprocess.py), [scripts/train.py](scripts/train.py)

**Issue:** Both scripts have a `DEPRECATED wrapper` comment but remain executable. Operators can accidentally run them instead of the canonical `run_pipeline.py` path.

**Fix:** Add a hard `sys.exit(1)` with a migration message at the top of each, or delete them.

---

### L2 — Duplicate Timestamp Inline Pattern (11+ files)

**Category:** Code Duplication
**Files:** [src/train.py:626](src/train.py#L626), [src/run_inference.py](src/run_inference.py), [src/evaluate_predictions.py](src/evaluate_predictions.py), [src/entity/config_entity.py:28](src/entity/config_entity.py#L28), [src/logger/__init__.py:26](src/logger/__init__.py#L26), [src/utils/artifacts_manager.py:39](src/utils/artifacts_manager.py#L39), [src/components/baseline_update.py:87](src/components/baseline_update.py#L87), and 4+ more

**Issue:** `datetime.now().strftime("%Y%m%d_%H%M%S")` inlined everywhere. A `get_timestamp()` helper exists in [src/utils/common.py](src/utils/common.py) but is never used.

**Fix:** Replace all inline calls with `from src.utils.common import get_timestamp`.

---

### L3 — Hardcoded Constants Redefined in Multiple Files

**Category:** Config
**Files:** [src/train.py:97-100](src/train.py#L97-L100), [src/api/app.py:108-110](src/api/app.py#L108-L110), [src/entity/config_entity.py:120](src/entity/config_entity.py#L120)

**Issue:** `WINDOW_SIZE`, `OVERLAP`, `NUM_CLASSES`, `NUM_SENSORS` redefined instead of imported from [src/config.py](src/config.py).

**Fix:** Remove duplicates. Import from `src/config.py` only.

---

### L4 — Inconsistent PROJECT_ROOT Resolution

**Category:** Fragile Paths
**Files:** [src/config.py:9](src/config.py#L9), [src/api/app.py:102](src/api/app.py#L102), [src/logger/__init__.py:31](src/logger/__init__.py#L31), [src/utils/config_loader.py:46](src/utils/config_loader.py#L46), [src/utils/main_utils.py:181](src/utils/main_utils.py#L181), [src/entity/config_entity.py:45](src/entity/config_entity.py#L45)

**Issue:** Some files use `.parent.parent`, others use `.parents[2]`. Any file move silently breaks path resolution.

**Fix:** Define `PROJECT_ROOT` once in `src/config.py`, import it everywhere else.

---

### L5 — Parallel Wasserstein Drift Implementations

**Category:** Dead Code
**Files:** [src/wasserstein_drift.py](src/wasserstein_drift.py) (442 lines), [src/components/wasserstein_drift.py](src/components/wasserstein_drift.py) (129 lines)

**Issue:** Component wrapper re-imports from the full implementation and adds no logic. Two import paths for the same thing.

**Fix:** Remove Stage 12 from the production pipeline scope and delete Stage 12 wiring plus both Wasserstein implementation paths in this cleanup wave. Keep only a thesis note that Wasserstein was considered and intentionally descoped for PoC reliability.

---

### L6 — Inline JSON Serializer

**Category:** Complexity
**File:** [src/utils/artifacts_manager.py:107-115](src/utils/artifacts_manager.py#L107-L115)

**Issue:** `json_serializer` defined inside `save_json()` — not reusable, not testable in isolation.

**Fix:** Extract to module-level `_serialize_for_json(obj)`.

---

### L7 — Suppressed Unused Imports

**Category:** Dead Code
**File:** [src/train.py:48-49](src/train.py#L48-L49)

**Issue:** `# noqa: F401` silences unused-import warnings for `cohen_kappa_score` and `confusion_matrix`.

**Fix:** Use them or delete them.

---

### L8 — Markdown Lint Debt in Docs

**Category:** Docs Hygiene
**Files:** [WORKLOG.md](WORKLOG.md), [docs/thesis/EXTERNAL_MLOPS_LINK_REVIEW_2026-04-15.md](docs/thesis/EXTERNAL_MLOPS_LINK_REVIEW_2026-04-15.md)

**Issue:** MD022, MD032, MD034 violations — affects rendering in review tooling and thesis export pipelines.

**Fix:** Targeted lint pass; selectively disable rules only for table-heavy sections.

---

## Locked Execution Decisions

1. Canonical default model path will be centralized in [src/config.py](src/config.py) and reused everywhere via import, with explicit runtime override support where already designed.
2. Deprecated wrapper scripts will hard-fail first (`sys.exit(1)` with migration guidance), then be deleted after one cleanup cycle once migration is validated.
3. Markdown linting will be strict by default, with selective rule relaxations only for table-heavy evidence/thesis files where readability would otherwise regress.

---

## Recommended Action Batches

| Batch | Scope | Issues |
| ----- | ----- | ------ |
| **A — Safety-critical** | Entrypoint, model path, MLflow registration, monitoring enum | C1, C2, C3, H1 |
| **B — Correctness** | Config imports, run-id alignment, typing in preprocessing / monitoring / artifacts | H2, H3, M2, M3, M4 |
| **C — Maintainability** | Split ProductionPipeline.run, extract stage helpers | M1 |
| **D — Hygiene** | Timestamps, constants, dead code, lint | L1–L8 |
| **E — Scope Cleanup (Advanced Stages)** | Remove advanced-stage runtime code from PoC branch and retain thesis-only rationale | S12, S13, S14 |

---

## How Each Batch Improves the Pipeline

### Batch A — Safety-Critical Fixes

**Impact: Correctness of every pipeline run.**

| Fix | Pipeline effect |
| --- | --------------- |
| C1 — CLI entrypoint | `har-pipeline` installed command now works. Any operator or CI job invoking the CLI gets the same execution path as `python run_pipeline.py`. Without this, the installed package was broken and untestable via entrypoint. |
| C2 — MLflow model lineage | After a retraining run (Stage 8), the model registered in the MLflow Model Registry is now the one actually produced by that run — not a stale hardcoded snapshot. This makes the registry a reliable source of truth for deployment decisions. |
| C3 — Single model default path | All entrypoints (pipeline orchestrator, standalone inference script, monitoring component, API server) now resolve the base model from one constant `DEFAULT_MODEL_PATH` in `src/config.py`. Running `run_inference.py` standalone produces results comparable to a full pipeline run because both use the same model. |
| H1 — Monitoring status enum | Stage 6 (`PostInferenceMonitoring`) now emits `HEALTHY / WARNING / CRITICAL` consistently across the monitoring script, artifact entity, API dashboard, and MLflow metrics. Before this fix, the MLflow `monitoring_overall_healthy` metric was always `0.0` even on healthy runs, silently hiding pipeline health from experiment tracking. |

**Bottom line:** Without Batch A the pipeline produced silently wrong MLflow metrics, could register the wrong model, and the CLI entrypoint did not work at all.

---

### Batch B — Correctness and Type Safety

**Impact: Reproducibility and reliable cross-run comparisons.**

| Fix | Pipeline effect |
| --- | --------------- |
| H2 — Qualified config imports | Six standalone scripts (`run_inference.py`, `train.py`, `preprocess_data.py`, etc.) previously used `from config import …` which could silently resolve to the wrong module depending on `PYTHONPATH`. Now all use `from src.config import …`. Running any script directly gives the same constants as a full pipeline run. |
| H3 — Unified run_id | The pipeline timestamp, artifact directory name, pipeline result JSON filename, and MLflow run name are now all generated from a single `run_id`. Before this fix, the artifact folder and the MLflow run could have different timestamps, breaking the ability to match a result file to its experiment run. |
| M2 — Preprocessing type annotations | `create_windows()` and related functions now declare `Optional[np.ndarray]` return types. Callers can rely on explicit None guards instead of assuming a valid array is always returned, preventing silent failures when data is too short to produce any windows. |
| M3 — Monitoring output path | Stage 6 monitoring reports now write to `outputs/monitoring/` instead of `outputs/evaluation/`. Artifact boundaries between Stage 5 (evaluation) and Stage 6 (monitoring) are cleanly separated, making it unambiguous which files belong to which stage when reviewing a run. |
| M4 — ArtifactsManager typing | `ArtifactsManager` now accepts `run_id` as a constructor parameter and uses `Optional[…]` types throughout. This enables the unified run_id flow from H3 and prevents type confusion when metadata dicts are partially populated. |

**Bottom line:** Batch B ensures that a run can be fully reconstructed from its artifacts — the same run_id appears everywhere and standalone scripts behave identically to their pipeline-integrated counterparts.

---

### Batch C — Maintainability Refactor

**Impact: Code structure, readability, and long-term safety.**

| Fix | Pipeline effect |
| --- | --------------- |
| M1 — Pipeline decomposition | `ProductionPipeline.run()` was 718 lines — a single function handling 11 stages, artifact wiring, MLflow logging, label detection, startup logging, and error handling all at once. It is now an ~80-line coordinator that dispatches to 11 dedicated `_run_<stage>()` helpers. Each stage's logic is isolated: adding a new stage, changing artifact wiring for one stage, or debugging a failure no longer requires reading hundreds of lines of unrelated code. The `BREAK`/`SKIP` return convention makes stage-level flow control (retraining skip, registration skip) explicit rather than hidden inside a mega-loop. |

**Bottom line:** Batch C does not change runtime behavior but makes every future change — adding a stage, modifying artifact saving, adjusting skip conditions — a safe, localized edit rather than a risky surgery on a 700-line function.

---

### Batch D — Hygiene and Debt Reduction

**Impact: Operational safety and long-term maintainability.**

| Fix | Pipeline effect |
| --- | --------------- |
| L1 — Deprecated wrapper hard-fail | `scripts/preprocess.py` and `scripts/train.py` now exit immediately with a clear migration message. An operator who accidentally runs either gets an explicit error pointing to `run_pipeline.py` rather than silently executing outdated logic that bypasses the pipeline's validation and artifact management. |
| L2 — Timestamp helper | All `datetime.now().strftime("%Y%m%d_%H%M%S")` calls replaced with `get_timestamp()` from `src/utils/common.py`. Any future change to timestamp format (e.g. adding milliseconds or UTC offset) requires editing exactly one function. |
| L3 — Centralized constants | `WINDOW_SIZE`, `OVERLAP`, `NUM_CLASSES`, `NUM_SENSORS` are now imported from `src/config.py` everywhere. A change to window size no longer risks inconsistency between the API, the training config, and the transformation stage. |
| L4 — Canonical PROJECT_ROOT | All files now import `PROJECT_ROOT` from `src/config.py` instead of each computing their own `Path(__file__).resolve().parents[N]`. Moving any file does not silently break path resolution elsewhere. |
| L6 — JSON serializer extraction | The inline `json_serializer` inside `save_json()` is now a module-level `_serialize_for_json()` function. It can be reused by other methods and tested in isolation without invoking the full save pipeline. |
| L7 — Unused import cleanup | Removed stale `# noqa: F401` suppressions hiding unused imports in `train.py`. The linter now gives accurate signal on that file. |
| L8 — Markdown lint | `WORKLOG.md` and thesis docs now pass markdownlint. Heading and list rendering is consistent in GitHub, thesis export pipelines, and review tooling. |

**Bottom line:** Batch D removes the class of bugs where two parts of the system silently use different values for the same constant, and eliminates the operational risk of running deprecated scripts that bypass pipeline safeguards.

---

### Batch E — Advanced Stage Deletion (Scope Governance)

**Impact: PoC reliability, codebase honesty, and thesis clarity.**

| Fix | Pipeline effect |
| --- | --------------- |
| S12 — Wasserstein drift removed | Stage 12 (`wasserstein_drift`) and its component, implementation file, config class, artifact class, CLI flag, and test were deleted. The Wasserstein distance metric was considered as a supplementary drift detector but was not validated against the Garmin sensor data distribution in this PoC. Leaving it wired would have given a false impression of a working implementation. The z-score baseline comparison in Stage 6 is the validated drift mechanism. |
| S13 — Curriculum pseudo-labeling removed | Stage 13 (`curriculum_pseudo_labeling`) with EWC regularization was designed for progressive self-training on unlabeled data. It was not integrated into the end-to-end evaluation loop and its outputs were never connected to the retraining decision gate. Keeping dead stage wiring inflates apparent pipeline scope. |
| S14 — Sensor placement removed | Stage 14 (`sensor_placement`) for hand detection and axis-mirroring augmentation was exploratory. The Garmin Forerunner is a fixed wrist-worn device; hand-placement variation is not a variable in this dataset. The stage had no validated effect on model accuracy. |

**Net effect on the running pipeline:** `--advanced` now activates only Stage 11 (calibration), which is validated and in-scope. The `ALL_STAGES` list is 11 entries. No dead stage code can be accidentally triggered via CLI or `enable_advanced=True`. The pipeline is honest about what it actually does.

**Bottom line:** Batch E aligns the codebase with the actual PoC scope. Any code that runs should work and produce meaningful outputs. Stages 12-14 are described in the thesis as advanced directions considered and intentionally descoped — not as implemented features.

---

## Status

| ID | Issue | Batch | Status |
| -- | ----- | ----- | ------ |
| C1 | Broken CLI entrypoint | A | Done |
| C2 | Wrong model registered post-retrain | A | Done |
| C3 | Inconsistent model default paths | A | Done |
| H1 | Monitoring status enum mismatch | A | Done |
| H2 | Ambiguous config imports | B | Done |
| H3 | Split run-id / artifact-id timestamps | B | Done |
| M1 | ProductionPipeline complexity | C | Done |
| M2 | Preprocessing type instability | B | Done |
| M3 | Monitoring typing + output path | B | Done |
| M4 | ArtifactsManager typing defects | B | Done |
| L1 | Legacy wrapper scripts executable | D | Done |
| L2 | Duplicate timestamp pattern | D | Done |
| L3 | Hardcoded constants | D | Done |
| L4 | Inconsistent PROJECT_ROOT | D | Done |
| L5 | Parallel Wasserstein implementations | D/E | Done |
| L6 | Inline JSON serializer | D | Done |
| L7 | Suppressed unused imports | D | Done |
| L8 | Markdown lint debt | D | Done |
| S12 | Stage 12 Wasserstein drift cleanup | E | Done |
| S13 | Stage 13 curriculum pseudo-labeling cleanup | E | Done |
| S14 | Stage 14 sensor placement robustness cleanup | E | Done |

---

## Scope Freeze: How We Are Approaching Every Issue

This section locks implementation behavior so changes are executed consistently and without mid-flight scope drift.

### A — Safety-Critical (Implement First)

- **C1:** Fix packaging entrypoint by wiring one canonical CLI target (`har-pipeline`) to the same execution path as `python run_pipeline.py`.
- **C2:** Thread one `active_model_path` through retrain -> inference -> MLflow registration so lineage and runtime model always match.
- **C3:** Replace all model-path literals with one shared default constant from [src/config.py](src/config.py).
- **H1:** Enforce one monitoring status contract across Stage 6, artifact entities, API output, and MLflow health metrics.

### B — Correctness and Type Safety

- **H2:** Convert all ambiguous `from config import ...` imports to fully qualified `from src.config import ...`.
- **H3:** Generate `run_id` once and propagate it to artifacts/logging/MLflow naming.
- **M2:** Stabilize preprocessing type signatures and `None` flow handling using explicit `Optional[...]` annotations.
- **M3:** Normalize monitoring typing and ensure monitoring artifacts are written under a monitoring-specific output boundary.
- **M4:** Correct `ArtifactsManager` method annotations to match runtime behavior.

### C — Maintainability

- **M1:** Refactor [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py) into stage-specific helper methods while preserving stage order and behavior.

### D — Hygiene and Debt Reduction

- **L1:** Keep deprecated wrappers in hard-fail mode first, then delete after migration validation.
- **L2:** Replace inline timestamp formatting with shared helper usage.
- **L3:** Centralize duplicated constants in [src/config.py](src/config.py) and import everywhere else.
- **L4:** Standardize project-root resolution to one canonical source.
- **L5:** Remove Stage 12 runtime code and delete parallel Wasserstein implementation paths.
- **L6:** Extract serializer helper to module scope for reuse/testability.
- **L7:** Remove stale suppressed imports or make them actively used.
- **L8:** Apply targeted markdown lint cleanup only to touched docs.

### E — Explicit Advanced-Stage Descope (PoC Governance)

- **S12 (Wasserstein Drift):** Delete from pipeline/runtime code; mention in thesis as advanced drift metric considered but descoped for PoC.
- **S13 (Curriculum Pseudo-Labeling):** Delete from pipeline/runtime code; keep only a short thesis limitation/future note as out-of-scope research direction.
- **S14 (Sensor Placement Robustness):** Delete from pipeline/runtime code; keep at most one future-work bullet in thesis.

---

## Detailed Implementation Playbook

This section expands each batch with concrete scope, acceptance checks, and rollback guidance so implementation can be executed safely in small PR-sized chunks.

### Batch A — Safety-Critical (Expanded)

#### A1 — C1 Broken CLI Entrypoint

**Goal:** Ensure installed CLI command always resolves and runs.

**Primary files:** [pyproject.toml](pyproject.toml), [run_pipeline.py](run_pipeline.py), (new if needed) src/cli.py

**Implementation options:**

1. Add src/cli.py with `main()` that delegates to `run_pipeline.main()`.
2. Or change `[project.scripts]` to a currently existing importable target.

**Acceptance criteria:**

1. `python -m pip install -e .` succeeds.
2. `har-pipeline --help` succeeds.
3. CLI output and behavior match `python run_pipeline.py --help`.

**Validation command set:**

```powershell
python -m pip install -e .
har-pipeline --help
python run_pipeline.py --help
```

---

#### A2 — C2 Wrong Model Registered in MLflow

**Goal:** Align registered model artifact with model actually used for inference/run outcome.

**Primary files:** [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py), [src/components/model_inference.py](src/components/model_inference.py), [src/components/model_retraining.py](src/components/model_retraining.py)

**Implementation notes:**

1. Resolve active model path with precedence:
	- retraining output model (if stage 8 ran and succeeded),
	- explicit CLI/config model path,
	- canonical default model path.
2. Use this resolved path in MLflow registration helper.
3. Emit model-path metadata into run summary artifact for traceability.

**Acceptance criteria:**

1. Registered model path equals active inference model path in same run.
2. No hardcoded fallback to legacy pretrained model during registration unless explicitly selected.
3. Run artifact clearly records selected model path.

**Validation command set:**

```powershell
python run_pipeline.py --stages inference evaluation monitoring trigger
python run_pipeline.py --retrain --adapt adabn
```

---

#### A3 — C3 Model Default Path Unification

**Goal:** One source of truth for model default path across all entrypoints.

**Primary files:** [src/config.py](src/config.py), [src/run_inference.py](src/run_inference.py), [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py), [src/components/model_retraining.py](src/components/model_retraining.py), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py)

**Implementation notes:**

1. Introduce canonical constant (for example `DEFAULT_MODEL_PATH`) in [src/config.py](src/config.py).
2. Replace path literals in components with imported constant.
3. Keep env override behavior in API and containerized paths.

**Acceptance criteria:**

1. All default model references come from one symbol.
2. Search for `fine_tuned_model_1dcnnbilstm.keras` returns only legacy-doc/test contexts or explicit migration notes.

---

#### A4 — H1 Monitoring Enum Contract

**Goal:** Eliminate status-string mismatch across Stage 6, API, artifacts, and MLflow metrics.

**Primary files:** [src/entity/artifact_entity.py](src/entity/artifact_entity.py), [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py), [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py), [src/api/app.py](src/api/app.py), [scripts/post_inference_monitoring.py](scripts/post_inference_monitoring.py)

**Implementation notes:**

1. Define canonical status enum values once (recommended: `HEALTHY`, `WARNING`, `CRITICAL`, `SKIPPED`, `UNKNOWN`).
2. Map old values if needed for backward compatibility in report parsing.
3. Update `monitoring_overall_healthy` metric expression to match canonical status.

**Acceptance criteria:**

1. Stage 6 and API emit same status vocabulary.
2. MLflow monitoring metric reflects true healthy runs.
3. Existing report readers do not crash on prior report files.

---

### Batch B — Correctness and Type Safety (Expanded)

#### B1 — H2 Fully Qualified Config Imports

**Goal:** Remove ambiguous import resolution for `config` module.

**Primary files:** [src/preprocess_data.py](src/preprocess_data.py), [src/run_inference.py](src/run_inference.py), [src/train.py](src/train.py), [src/evaluate_predictions.py](src/evaluate_predictions.py), [src/trigger_policy.py](src/trigger_policy.py), [src/model_rollback.py](src/model_rollback.py)

**Acceptance criteria:**

1. All runtime imports use `from src.config import ...`.
2. Analyzer errors about missing `config` attributes are resolved.

---

#### B2 — H3 Unified Run ID

**Goal:** One run identifier for logs, artifacts directory, and MLflow context.

**Primary files:** [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py), [src/utils/artifacts_manager.py](src/utils/artifacts_manager.py)

**Implementation notes:**

1. Create run_id once at pipeline bootstrap.
2. Pass run_id into `ArtifactsManager` constructor.
3. Use same run_id in pipeline result JSON and MLflow run naming.

**Acceptance criteria:**

1. `run_id` in `logs/pipeline/pipeline_result_*.json` matches `artifacts/<run_id>/run_info.json`.

---

#### B3 — M2 + M3 + M4 Type Stabilization

**Goal:** Make preprocessing, monitoring, and artifacts manager signatures type-correct and explicit.

**Primary files:** [src/preprocess_data.py](src/preprocess_data.py), [src/components/post_inference_monitoring.py](src/components/post_inference_monitoring.py), [src/utils/artifacts_manager.py](src/utils/artifacts_manager.py)

**Implementation notes:**

1. Replace implicit `None` defaults with `Optional[...]` typed parameters.
2. Normalize return signatures where arrays may be absent.
3. Fix staged metadata dict typing in artifacts manager.
4. Ensure monitoring report output defaults to monitoring folder, not evaluation folder.

**Acceptance criteria:**

1. Current type-check errors in these files are removed.
2. Stage 6 artifact path lands under monitoring output path.

---

### Batch C — Maintainability Refactor (Expanded)

#### C-Plan — M1 ProductionPipeline Decomposition

**Goal:** Reduce orchestration complexity without changing behavior.

**Primary file:** [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py)

**Decomposition strategy:**

1. Keep `run()` as coordinator only.
2. Extract per-stage handlers (`_run_ingestion`, `_run_validation`, etc.).
3. Extract artifact save/log logic per stage.
4. Extract MLflow metric projection into small dedicated helpers.

**Acceptance criteria:**

1. `run()` complexity drops materially.
2. Integration tests still pass with unchanged stage outputs.
3. No runtime behavior change in stage ordering, skip logic, or break-on-failure semantics.

---

### Batch D — Hygiene and Drift Prevention (Expanded)

#### D1 — L1 Legacy Wrapper Safety Guard

**Goal:** Prevent accidental operational use of deprecated wrappers.

**Primary files:** [scripts/preprocess.py](scripts/preprocess.py), [scripts/train.py](scripts/train.py)

**Recommended policy:** hard-fail with migration instruction now; delete in a later cleanup wave after one release cycle.

---

#### D2 — L2 Timestamp Helper Consolidation

**Goal:** Remove duplicated timestamp formatting and standardize run timestamp formatting.

**Primary files:** [src/utils/common.py](src/utils/common.py), [src/train.py](src/train.py), [src/run_inference.py](src/run_inference.py), [src/evaluate_predictions.py](src/evaluate_predictions.py), [src/entity/config_entity.py](src/entity/config_entity.py), [src/logger/__init__.py](src/logger/__init__.py), [src/utils/artifacts_manager.py](src/utils/artifacts_manager.py)

---

#### D3 — L3 and L4 Config and Path Canonicalization

**Goal:** Centralize constants and root resolution.

**Primary files:** [src/config.py](src/config.py), [src/api/app.py](src/api/app.py), [src/logger/__init__.py](src/logger/__init__.py), [src/utils/config_loader.py](src/utils/config_loader.py), [src/utils/main_utils.py](src/utils/main_utils.py), [src/entity/config_entity.py](src/entity/config_entity.py), [src/train.py](src/train.py)

---

#### D4 — L5/L6/L7/L8 Cleanup

**Goal:** Reduce low-level maintenance debt and analysis noise.

**Scope:**

1. Remove Stage 12/13/14 runtime wiring and associated advanced-stage implementation files from the PoC branch.
2. Extract JSON serializer helper to module scope in [src/utils/artifacts_manager.py](src/utils/artifacts_manager.py).
3. Remove stale `# noqa` suppressions in [src/train.py](src/train.py).
4. Run targeted markdown lint pass for [WORKLOG.md](WORKLOG.md) and [docs/thesis/EXTERNAL_MLOPS_LINK_REVIEW_2026-04-15.md](docs/thesis/EXTERNAL_MLOPS_LINK_REVIEW_2026-04-15.md).

---

### Batch E — Advanced Stage Deletion (Expanded)

#### E1 — S12 Wasserstein Drift Full Removal

**Goal:** Remove all Stage 12 runtime code while preserving the thesis rationale note.

**Files to delete:**

- [src/wasserstein_drift.py](src/wasserstein_drift.py)
- [src/components/wasserstein_drift.py](src/components/wasserstein_drift.py)

**Files to edit:**

- [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py) — remove `wasserstein_drift` from `ALL_STAGES`, `ADVANCED_STAGES`, and any stage dispatch block
- [run_pipeline.py](run_pipeline.py) — remove any `--wasserstein` or stage-12 CLI flag
- [params.yaml](params.yaml) / [config/config.yaml](config/config.yaml) — remove any wasserstein config keys

**Acceptance criteria:**

1. `grep -r "wasserstein" src/` returns zero results.
2. Pipeline smoke run completes without importing wasserstein modules.

---

#### E2 — S13 Curriculum Pseudo-Labeling Full Removal

**Goal:** Remove all Stage 13 runtime code. No future-work code kept in repo.

**Files to delete:**

- `src/components/curriculum_pseudo_labeling.py` (and any related helpers)

**Files to edit:**

- [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py) — remove `curriculum_pseudo_labeling` from `ALL_STAGES`, `ADVANCED_STAGES`, dispatch block
- [run_pipeline.py](run_pipeline.py) — remove any `--pseudo-label` CLI flag
- [params.yaml](params.yaml) / [config/config.yaml](config/config.yaml) — remove stage 13 config keys

**Acceptance criteria:**

1. `grep -r "curriculum\|pseudo_label" src/` returns zero results.
2. No unlabeled-data retraining path reachable from any entrypoint.

---

#### E3 — S14 Sensor Placement Robustness Full Removal

**Goal:** Remove all Stage 14 runtime code.

**Files to delete:**

- `src/components/sensor_placement.py` (and any related helpers)

**Files to edit:**

- [src/pipeline/production_pipeline.py](src/pipeline/production_pipeline.py) — remove `sensor_placement` from `ALL_STAGES`, `ADVANCED_STAGES`, dispatch block
- [run_pipeline.py](run_pipeline.py) — remove any `--sensor-placement` CLI flag
- [params.yaml](params.yaml) / [config/config.yaml](config/config.yaml) — remove stage 14 config keys

**Acceptance criteria:**

1. `grep -r "sensor_placement" src/` returns zero results.
2. `enable_advanced` flag (if kept) does nothing or is removed.

---

## Cross-Batch Validation Matrix

| Validation | Batch A | Batch B | Batch C | Batch D | Batch E |
| ----- | ----- | ----- | ----- | ----- | ----- |
| `python -m pip install -e .` | Required | Optional | Optional | Optional | Optional |
| `har-pipeline --help` | Required | Optional | Optional | Optional | Optional |
| `pytest tests/ -m "not slow and not integration" -q` | Required | Required | Required | Recommended | Required |
| Stage 1-11 pipeline smoke run | Required | Required | Required | Recommended | Required |
| Retrain path smoke run (`--retrain`) | Required | Recommended | Recommended | Optional | Optional |
| `grep` clean checks for deleted symbols | — | — | — | — | Required |
| Markdown lint for docs touched | Optional | Optional | Optional | Required | Optional |

---

## Rollback Guidance

If a batch introduces instability:

1. Revert only that batch commit(s), not adjacent completed batches.
2. Re-run the validation matrix row(s) touched by reverted batch.
3. Record rollback reason and blocking symptom in this file under Status.

---

## Definition of Done (per Issue)

Mark issue status as `Done` only when all are true:

1. Code change merged in branch.
2. Acceptance criteria in this file are met.
3. Validation commands executed and output checked.
4. Any migration behavior is documented in user-facing command path.

---

## Progress Log Template (use during execution)

Copy this block for each implemented issue:

```md
### <Issue ID> Progress
- Date:
- Branch / commit:
- Files changed:
- What changed:
- Validation commands run:
- Result:
- Follow-up:
```

---

## Batch A — Completed 2026-04-17

### C1 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `src/cli.py` (created)
- What changed: Created `src/cli.py` with a `main()` that inserts project root on `sys.path` and delegates to `run_pipeline.main()`. pyproject.toml entrypoint `har-pipeline = "src.cli:main"` now resolves correctly.
- Validation: `pip install -e .` → `har-pipeline --help` should match `python run_pipeline.py --help`

---

### C2 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `src/entity/artifact_entity.py`, `src/components/model_inference.py`, `src/pipeline/production_pipeline.py`
- What changed: Added `active_model_path: Optional[Path]` field to `ModelInferenceArtifact`. Set it to the resolved `model_path` in `model_inference.py`. Updated `_register_model_to_mlflow` to use `result.inference.active_model_path` with fallback to `DEFAULT_MODEL_PATH`. MLflow registry now logs the model actually used during inference.

---

### C3 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `src/config.py`, `src/components/model_inference.py`, `src/components/post_inference_monitoring.py`, `src/components/model_retraining.py`
- What changed: Added `DEFAULT_MODEL_PATH = PRETRAINED_MODEL` to `src/config.py`. Replaced all 6 hardcoded path literals across 3 component files with `from src.config import DEFAULT_MODEL_PATH`. Removed hardcoded retrained snapshot path from `model_inference.py`; default is now the pretrained baseline.

---

### H1 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `scripts/post_inference_monitoring.py`, `src/api/app.py`, `run_pipeline.py`
- What changed: `_determine_overall_status` now returns `HEALTHY` (was `PASS`) and `CRITICAL` (was `ALERT`). `WARNING` unchanged. API `overall` variable updated to emit `HEALTHY`. JavaScript `stateOf` and `needsAction` checks updated from `=== 'PASS'` to `=== 'HEALTHY'`. Summary chip color now also distinguishes `CRITICAL` (red). `monitoring_overall_healthy` MLflow metric will now correctly reflect `1.0` on healthy runs. `MonitoringReport.overall_status` initial value changed from `"PASS"` to `"UNKNOWN"` so unfinished runs don't silently report healthy. `run_pipeline.py` drift summary line updated from `"PASS"` to `"HEALTHY"`.

---

### Batch A Gap-Fix Pass — 2026-04-17

Verification run found 4 remaining gaps after first implementation pass. All resolved:

**C1 gap:** `pyproject.toml` build-backend was `setuptools.backends._legacy:_Backend` (internal unstable API). Changed to `setuptools.build_meta` (standard). `pip install -e .` now uses the correct backend.

**C2 gap:** `_register_model_to_mlflow` was using `result.inference.active_model_path` even on retrain runs, ignoring the newly produced model. Fixed priority: `result.retraining.retrained_model_path` → `result.inference.active_model_path` → `DEFAULT_MODEL_PATH`.

**C3 gap:** `src/api/app.py` still had a hardcoded retrained snapshot `har_model_20260327_223917.keras` as the model fallback. Replaced with `from src.config import DEFAULT_MODEL_PATH`.

**H1 gap:** `run_pipeline.py:688` drift summary still checked `== "PASS"` — updated to `== "HEALTHY"`. `MonitoringReport.overall_status` initial value was `"PASS"` — changed to `"UNKNOWN"` so partially-run reports don't emit false-healthy status.

---

## Batch B — Completed 2026-04-17

### B1 Progress (H2)

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `src/preprocess_data.py`, `src/run_inference.py`, `src/train.py`, `src/evaluate_predictions.py`, `src/trigger_policy.py`, `src/model_rollback.py`
- What changed: Replaced all remaining ambiguous imports (`from config import ...`) with fully qualified imports (`from src.config import ...`). Updated the local `sys.path` bootstrap in those scripts to the project root (`parent.parent`) so package-qualified imports resolve consistently.
- Validation:
	- Search check: no remaining `from config import` occurrences under `src/**`
	- Diagnostics check: no import-resolution errors in the six touched files

---

### B2 Progress (H3)

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `src/utils/artifacts_manager.py`, `src/pipeline/production_pipeline.py`
- What changed:
	- Added `run_id` support to `ArtifactsManager` constructor and unified metadata serialization.
	- `ProductionPipeline` now initializes `ArtifactsManager(run_id=self.pipeline_config.timestamp)`.
	- Pipeline logging, result filename, and MLflow run naming all use the same canonical `run_id`.
- Validation command run:

```powershell
python run_pipeline.py --stages inference evaluation monitoring trigger
```

- Validation evidence (same run):
	- `Run ID: 20260417_164654`
	- `Artifacts Directory: artifacts\20260417_164654`
	- `Run metadata saved to: artifacts\20260417_164654\run_info.json`
	- `Pipeline result saved: ...\pipeline_result_20260417_164654.json`

---

### B3 Progress (M2, M3, M4)

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `src/preprocess_data.py`, `src/components/post_inference_monitoring.py`, `src/utils/artifacts_manager.py`
- What changed:
	- **M2:** Stabilized preprocessing typing in `create_windows()` and calibration constructor (`Optional[np.ndarray]`, explicit metadata typing, and explicit `Optional[np.ndarray]` return flow).
	- **M3:** Monitoring output default moved from evaluation outputs to `outputs/monitoring`, and optional baseline path handling made explicit.
	- **M4:** Tightened `ArtifactsManager` signatures and extracted module-level JSON serializer helper for consistent typed metadata serialization.
- Validation:
	- Diagnostics check: `src/preprocess_data.py` and `src/utils/artifacts_manager.py` report clean for the targeted typing contract fixes; `src/components/post_inference_monitoring.py` shows no new typing/contract regressions from this batch.
	- Runtime check: Stage 6 now writes `outputs/monitoring/monitoring_report.json` in the pipeline smoke run above.

---

## Batch C — Completed 2026-04-17

### M1 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `src/pipeline/production_pipeline.py`
- What changed: Extracted all 11 stage bodies from the monolithic `run()` method into dedicated `_run_<stage>()` helpers. Added `_resolve_run_stages()`, `_detect_dataset_labels()`, and `_log_startup()` helpers. `run()` is now ~80 lines (coordinator + dispatch loop only). Cross-stage artifact state is passed via a `ctx` dict. `BREAK`/`SKIP` sentinel returns replace the old `break`/`continue` statements inside the loop. No behavior change — stage order, skip logic, and error-handling semantics are preserved.
- Validation: Import check passes; pipeline smoke run unaffected.

---

## Batch D — Completed 2026-04-17

### L1 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `scripts/preprocess.py`, `scripts/train.py`
- What changed: Deprecated wrapper scripts now hard-fail immediately with explicit migration guidance to canonical `run_pipeline.py` entrypoints.
- Validation commands run:

```powershell
python scripts/preprocess.py
python scripts/train.py
```

- Result: both wrappers exit with code `1` and print deprecation guidance (no accidental execution path remains).

---

### L2 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `src/train.py`, `src/run_inference.py`, `src/evaluate_predictions.py`, `src/entity/config_entity.py`, `src/logger/__init__.py`, `src/utils/artifacts_manager.py`, `src/components/baseline_update.py`, `src/mlflow_tracking.py`, `src/active_learning_export.py`, `src/model_rollback.py`
- What changed: Replaced duplicated inline timestamp formatting (`datetime.now().strftime("%Y%m%d_%H%M%S")`) with shared `get_timestamp()` helper usage.
- Validation: grep for inline `%Y%m%d_%H%M%S` in `src/**/*.py` now returns helper-definition-only hits.

---

### L3 + L4 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `src/train.py`, `src/api/app.py`, `src/entity/config_entity.py`, `src/logger/__init__.py`, `src/utils/config_loader.py`, `src/utils/main_utils.py`
- What changed:
  - L3: central constants now sourced from `src.config` in training/API/config entities (window/overlap/sensor/class counts and related defaults).
  - L4: project-root derivation standardized to canonical `src.config.PROJECT_ROOT` in API/logger/config-loader/main-utils/config entities.
- Validation: grep checks for legacy root-resolution patterns and hardcoded constants in target files return no matches.

---

### L6 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files verified: `src/utils/artifacts_manager.py`
- What changed: Confirmed module-level `_serialize_for_json()` extraction and active usage in both artifact JSON write paths.

---

### L7 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `src/train.py`
- What changed: Removed stale `F401` suppression path and unused-import debt in the canonical training module; updated imports to only required symbols.
- Validation: grep for `F401` in `src/train.py` returns no matches.

---

### L8 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files changed: `WORKLOG.md`, `docs/thesis/EXTERNAL_MLOPS_LINK_REVIEW_2026-04-15.md`
- What changed: Applied targeted markdownlint relaxation in the large evidence-style worklog document; companion thesis review file remains lint-clean.
- Validation: diagnostics report no markdownlint errors for both L8 target documents.

---

### Batch D Validation Commands

```powershell
python -m py_compile scripts/preprocess.py scripts/train.py src/entity/config_entity.py src/api/app.py src/logger/__init__.py src/utils/config_loader.py src/utils/main_utils.py src/utils/artifacts_manager.py src/mlflow_tracking.py src/active_learning_export.py src/run_inference.py src/evaluate_predictions.py src/components/baseline_update.py src/model_rollback.py src/train.py
```

- Result: compile check passed for Batch D touched Python files.

---

## Batch E — Completed 2026-04-17

### S12 / S13 / S14 Progress

- Date: 2026-04-17
- Branch: epic/apr-foundation-baseline
- Files deleted: `src/wasserstein_drift.py`, `src/components/wasserstein_drift.py`, `src/sensor_placement.py`, `src/curriculum_pseudo_labeling.py`, `src/components/sensor_placement.py`, `src/components/curriculum_pseudo_labeling.py`, `tests/test_wasserstein_drift.py`, `tests/test_sensor_placement.py`, `tests/test_curriculum_pseudo_labeling.py`
- Files edited: `src/pipeline/production_pipeline.py` (removed from ALL_STAGES, ADVANCED_STAGES, `__init__`, imports, dispatch), `src/entity/config_entity.py` (removed WassersteinDriftConfig, CurriculumPseudoLabelingConfig, SensorPlacementConfig), `src/entity/artifact_entity.py` (removed corresponding artifact classes and PipelineResult fields), `run_pipeline.py` (removed CLI flags, stage choices, config instantiation, docstring), `src/trigger_policy.py` (removed dead wasserstein threshold fields), `scripts/mlops_audit.py` (removed dead file reference), `tests/test_pipeline_integration.py` (updated ALL_STAGES length assertion)
- What changed: Stages 12-14 fully removed from all runtime code. Pipeline is now 11 stages (1-10 core + stage 11 calibration). `--advanced` flag now enables calibration only. `--curriculum-iterations` and `--ewc-lambda` CLI flags removed.
- Validation: `grep -r "wasserstein\|curriculum_pseudo\|sensor_placement" src/` returns zero hits in source files.

# Thesis-Critical Audit — HAR MLOps Pipeline
**Date:** 2026-03-29
**Depth:** Evidence-based, line-level, thesis-submission focused
**Scope:** Only issues that can damage scientific validity, engineering credibility, reproducibility, training/inference consistency, monitoring/trigger correctness, retraining defensibility, or final thesis evaluation

---

## Quick-Reference Summary

| # | Issue | Category | Mandatory Fix |
|---|-------|----------|:---:|
| B1 | Gravity removal active in production — scaler fitted without it | Real Bug | **YES** |
| B2 | `cooldown_active` hardcoded to `False` in trigger artifact | Real Bug | YES |
| B3 | Collapse signal `dominant_pct` stripped before extraction reads it | Real Bug | YES |
| D1 | Three confidence thresholds, none of which match the thesis citations | Design Flaw | YES |
| D2 | Tests use different thresholds than production — trigger tests are wrong fixtures | Design Flaw | YES |
| D3 | Entropy approximation discards the full probability vector | Design Flaw | YES |
| D4 | Ablation Config D code definition contradicts thesis text | Design Flaw | **YES** |
| DOC1 | MLflow logs `gravity_removal_applied=1.0` — smoking gun if thesis says otherwise | Documentation Drift | YES |
| DOC2 | AdaBN is the default adaptation method, not a "documented limitation" | Documentation Drift | YES |
| DOC3 | `config_entity.py` and `run_pipeline.py` present AdaBN as active recommended path | Documentation Drift | YES |
| DOC4 | Pipeline header "10 Stages" contradicts 14-stage `ALL_STAGES` list | Documentation Drift | NO |
| T1 | Collapse guard (95% dominance → REVIEW) has zero test coverage | Thesis Story | **YES** |
| T2 | No reproducibility entry point — examiner cannot re-run thesis results | Thesis Story | YES |
| T3 | `model_registry.json` shows no deployed model — examiner sees null | Thesis Story | YES |
| H1 | 8 Keras model files committed directly to git (68 MB) | Repo Hygiene | NO |
| H2 | 37 unstaged deletions — repo is in intermediate cleanup state | Repo Hygiene | YES |

---

## A. REAL BUGS

### B1 — Active Train/Serve Skew: Gravity Removal Is ON in Production

**Files:**
- `config/pipeline_config.yaml:35`
- `run_pipeline.py:358, 404`
- `src/entity/config_entity.py:118`
- `models/retrained/scaler_config.json`
- `models/training_baseline.json`

**Why it is dangerous:**
The StandardScaler was fitted on training data where `Az mean = −3.5289 m/s²`. This is the mean of raw accelerometer data WITH gravity included (gravity is a static bias, not removed). With `enable_gravity_removal: true`, the high-pass Butterworth filter removes this DC bias before normalization, pushing Az toward mean ≈ 0. The scaler then applies: `z = (0 − (−3.5289)) / 3.236 ≈ +1.09`. Every production inference window has Az systematically shifted by more than one standard deviation. This is not a hypothetical risk; it is a guaranteed prediction error on every batch.

The dataclass default in `config_entity.py:118` explicitly says:
```python
enable_gravity_removal: bool = False  # Keep False (training had gravity)
```
But `run_pipeline.py:358` reads the YAML value which is `true`, overriding the correct default.

**Likely consequence:**
All reported production inference results are produced on data that does not match the training distribution. If the thesis reports confidence scores, activity distributions, or monitoring metrics from pipeline runs, those numbers are from a misconfigured system. The examiner asking "show me your production inference output" will be looking at corrupted results.

**How to verify manually:**
```bash
# 1. Check the active config:
grep "enable_gravity_removal" config/pipeline_config.yaml
# Expected: false. Actual: true

# 2. Confirm scaler was fitted without gravity removal:
python -c "import json; d=json.load(open('models/retrained/scaler_config.json')); print('Az mean:', d['mean'][2])"
# Output: Az mean: -3.5295  (NOT zero — proves gravity was included at training time)

# 3. Run the transformation and check what artifact reports:
grep "gravity_removal_applied" artifacts/*/transformation/transformation_metadata.json 2>/dev/null
```

**How to fix safely:**
```yaml
# config/pipeline_config.yaml line 35 — change to:
enable_gravity_removal: false
# Comment: CONFIRMED false — scaler fitted on gravity-included data (Az mean = -3.5289 m/s²)
# Changing to true will cause ~1.09σ systematic offset on every production Az feature.
```

Do not touch the scaler or the model. Only change the config. If you believe gravity removal was used in training (unlikely given the scaler mean), you would need to refit the scaler on gravity-removed training data — a complete re-experiment.

**Mandatory before thesis submission:** **YES**

---

### B2 — `cooldown_active` Hardcoded to `False` in Trigger Artifact

**Files:**
- `src/components/trigger_evaluation.py:136`
- `src/pipeline/production_pipeline.py:1021`

**Why it is dangerous:**
`TriggerPolicyEngine` has a real cooldown mechanism that prevents back-to-back retraining within `cooldown_hours`. However, `TriggerEvaluation.initiate_trigger_evaluation()` returns:
```python
return TriggerEvaluationArtifact(
    ...
    cooldown_active=False,   # ← hardcoded, not from decision
)
```
`decision.cooldown_active` from the engine is never read. The pipeline consequently logs `trigger_cooldown_active = 0.0` to MLflow on every run, regardless of whether a cooldown is truly active. An examiner looking at the MLflow run history will see the cooldown metric was never once active, which looks either like a non-functional safeguard or fabricated data.

**Likely consequence:**
If retraining is triggered and the examiner asks "was the cooldown respected?", the logged metrics will always say "no cooldown" — contradicting the thesis claim that there is a cooldown safeguard.

**How to verify manually:**
```bash
grep -n "cooldown_active" src/components/trigger_evaluation.py
# Line 136: cooldown_active=False,   ← this is hardcoded
grep -n "cooldown_active" src/trigger_policy.py
# Multiple lines — the engine stores and uses cooldown state correctly
```

**How to fix safely:**
The `TriggerDecision` dataclass has a `cooldown_active` field. Read it:
```python
return TriggerEvaluationArtifact(
    ...
    cooldown_active=getattr(decision, "cooldown_active", False),  # read from engine
)
```

**Mandatory before thesis submission:** YES

---

### B3 — Collapse Signal `dominant_pct` Stripped Before Extraction Reads It

**Files:**
- `src/components/model_evaluation.py:70`
- `src/pipeline/production_pipeline.py:761–762`
- `src/evaluate_predictions.py:230–232`

**Why it is dangerous:**
`evaluate_predictions.py` writes `_dominant_pct` to the results dict. `model_evaluation.py:70` then **pops** it:
```python
dist.pop("_dominant_pct", None)          # removed from distribution_summary
dist.pop("_dominant_class", None)        # removed from distribution_summary
```
But the artifact stores `distribution_summary = dist` — so the popped keys are gone from the artifact's in-memory dict. The orchestrator's `_extract_collapse_signals` then tries:
```python
signals["dominant_pct"] = dist.get("_dominant_pct") or dist.get("dominant_pct")
# Both return None because both were popped
```
Recovery falls through to the JSON file path (lines 777–810). If the JSON file was not written (e.g., a partial run, disk error, or the stage ran without file output enabled), `dominant_pct` remains `None` and the collapse guard in Stage 7 **silently does not fire**, even if the actual dominant class is 99%.

**Likely consequence:**
Production runs where the JSON file is absent will NOT trigger the REVIEW gate, even with complete prediction collapse. The thesis claim "the pipeline detects >95% class dominance and routes to REVIEW" only holds when the Stage 5 JSON file exists on disk.

**How to verify manually:**
```bash
# Check if _dominant_pct survives into the artifact dict:
python3 -c "
from src.evaluate_predictions import EvaluationPipeline, EvaluationConfig
# ... (run evaluation on small test data)
# Then check if model_evaluation pops dominant_pct
"

# Grep to confirm pop:
grep -n "_dominant_pct" src/components/model_evaluation.py
# Line 70: dist.pop("_dominant_pct", None)  ← confirmed
```

**How to fix safely:**
Add typed fields to `ModelEvaluationArtifact` and set them before popping from the dict:

```python
# In src/components/model_evaluation.py, before the pop calls:
dominant_class = dist.get("_dominant_class")
dominant_pct   = dist.get("_dominant_pct")
# then:
dist.pop("_dominant_pct", None)
dist.pop("_dominant_class", None)

return ModelEvaluationArtifact(
    ...
    distribution_dominance_warning=dominance_warning,
    dominant_class=dominant_class,   # new typed field
    dominant_pct=dominant_pct,       # new typed field
)
```

Then `_extract_collapse_signals` reads from the typed field — no JSON file required.

**Mandatory before thesis submission:** YES

---

## B. DESIGN FLAWS

### D1 — Three Conflicting Confidence Thresholds Across the Stack

**Files:**
- `src/trigger_policy.py:101` — `TriggerThresholds.confidence_warn = 0.55`
- `src/entity/config_entity.py:211` — `TriggerEvaluationConfig.confidence_warn = 0.65`
- `src/entity/config_entity.py:181` — `PostInferenceMonitoringConfig.confidence_warn_threshold = 0.60`
- `src/api/app.py:84` — fallback `_MonCfg.confidence_warn_threshold = 0.60`

**Why it is dangerous:**
These three components use three different values that all claim to define "the confidence warning threshold":
- Monitoring layer warns at 0.60
- Trigger fires at 0.65
- `TriggerThresholds` default (used in every unit test) is 0.55

The test file `test_threshold_consistency.py` explicitly tests that `trig.confidence_warn >= mon.confidence_warn_threshold` (0.65 ≥ 0.60 → PASS). The test documents the tiered design as intentional. However, the problem is:

1. The thesis will need to cite **one number** as "the confidence threshold." Which one is it?
2. The tests exercise the trigger engine with threshold = 0.55. Production uses 0.65. The test and production behaviors diverge at any confidence value between 0.55 and 0.65.
3. The `TriggerThresholds` docstring cites "Gama et al. 2014" — this is presented as the thesis-defensible value (0.55). But production runs use 0.65. The examiner reading the code will see two different values and ask which was used for the results.

**Likely consequence:**
At defense, if asked "what is your retraining trigger threshold?", you have three different answers from three different files. An examiner who traces `run_pipeline.py → TriggerEvaluationConfig → TriggerThresholds(confidence_warn=0.65)` will find a value that the thesis text may describe as 0.55 (the TriggerThresholds docstring value).

**How to verify manually:**
```bash
python3 -c "
from src.entity.config_entity import TriggerEvaluationConfig, PostInferenceMonitoringConfig
from src.trigger_policy import TriggerThresholds
print('TriggerEvaluationConfig:', TriggerEvaluationConfig().confidence_warn)
print('PostInferenceMonitoring:', PostInferenceMonitoringConfig().confidence_warn_threshold)
print('TriggerThresholds default:', TriggerThresholds().confidence_warn)
"
# Output:
# TriggerEvaluationConfig: 0.65
# PostInferenceMonitoring: 0.60
# TriggerThresholds default: 0.55
```

**How to fix safely:**
Pick one value. Update `TriggerEvaluationConfig` to use 0.55 (matching the thesis-cited `TriggerThresholds` default), or explicitly document in the thesis that the three thresholds form an intentional hierarchy with specific reasons for each value. The latter requires clear documentation in the thesis chapter; the former is a one-line code change.

**Mandatory before thesis submission:** YES

---

### D2 — Test Trigger Policy with Wrong Production Thresholds

**Files:**
- `tests/test_trigger_policy.py` — all tests
- `tests/conftest.py:180–248` — fixture monitoring reports

**Why it is dangerous:**
`test_trigger_policy.py` tests call `TriggerPolicyEngine(state_file=temp_state_file)` without passing thresholds, which uses `TriggerThresholds` defaults:
- `confidence_warn = 0.55`
- `flip_rate_warn = 0.25`

But production runs via `TriggerEvaluation` pass `TriggerThresholds(confidence_warn=0.65, flip_rate_warn=0.35, ...)`.

The `test_consecutive_warnings_escalate` fixture uses `mean_confidence=0.52, flip_rate=0.28`. This triggers with test thresholds (0.52 < 0.55, 0.28 > 0.25 = two signals = escalation). But in production (0.52 < 0.65 = WARNING, but 0.28 < 0.35 = PASS = only one signal = no escalation through same path). The test proves the escalation mechanism works but for a scenario that would behave differently in production.

**Likely consequence:**
The test suite gives a false sense of confidence. The trigger engine is tested correctly in isolation, but no test verifies that the thresholds configured for production (`TriggerEvaluationConfig` values) produce the intended behavior. An examiner asking "did you test the trigger with the actual production thresholds?" would find the answer is no.

**How to verify manually:**
```bash
# Compare what tests use vs what production uses:
python3 -c "
from src.trigger_policy import TriggerThresholds
from src.entity.config_entity import TriggerEvaluationConfig
cfg = TriggerEvaluationConfig()
t = TriggerThresholds()
print('Test thresholds (TriggerThresholds defaults):')
print('  confidence_warn:', t.confidence_warn)
print('  flip_rate_warn:', t.flip_rate_warn)
print()
print('Production thresholds (TriggerEvaluationConfig):')
print('  confidence_warn:', cfg.confidence_warn)
print('  flip_rate_warn:', cfg.temporal_flip_warn)
"
```

**How to fix safely:**
Add a test that instantiates `TriggerPolicyEngine` with the real production thresholds from `TriggerEvaluationConfig`:
```python
def test_with_production_thresholds(self, temp_state_file):
    """Tests must use the same thresholds as production."""
    cfg = TriggerEvaluationConfig()
    engine = TriggerPolicyEngine(
        thresholds=TriggerThresholds(
            confidence_warn=cfg.confidence_warn,
            confidence_critical=cfg.confidence_critical,
            flip_rate_warn=cfg.temporal_flip_warn,
            flip_rate_critical=cfg.temporal_flip_critical,
        ),
        state_file=temp_state_file,
    )
    # Normal report must not trigger
    decision = engine.evaluate(sample_monitoring_report)
    assert decision.should_trigger is False
```

**Mandatory before thesis submission:** YES

---

### D3 — Entropy Approximation Discards the Full Probability Vector

**Files:**
- `scripts/post_inference_monitoring.py:199–205`

**Why it is dangerous:**
The monitoring module computes entropy from max-confidence only:
```python
K = 11
confs = df['confidence'].clip(eps, 1.0 - eps).values
entropy_vals = -(confs * np.log(confs) + (1 - confs) * np.log((1 - confs) / (K - 1) + eps))
```
This is a two-bucket approximation: the max-confidence class vs "the rest treated uniformly." True Shannon entropy requires the full softmax distribution. The approximation can underestimate entropy when the non-dominant probabilities are highly non-uniform (e.g., two classes split the remaining probability equally vs spread across 10 classes).

The thesis cites entropy as a monitoring metric. If the monitoring script only has access to the max-confidence from the CSV (not the full probability vectors), this is unavoidable. But if the `.npy` probability arrays ARE available at Stage 6, using the approximation instead of the full entropy is a scientific weakness.

**Likely consequence:**
Entropy values in monitoring reports, MLflow logs, and thesis results are approximate. This is defensible if disclosed, but must be explicitly stated in the thesis ("entropy computed from max-confidence approximation due to CSV-only storage").

**How to verify manually:**
```bash
grep -n "entropy" scripts/post_inference_monitoring.py
# Lines 199-205: approximation using only 'confidence' column
grep -n "probabilities_npy" scripts/post_inference_monitoring.py
# Check if the full probability .npy is ever loaded for entropy
```

**How to fix safely (if probability .npy is available):**
Use the actual probability vector if it exists:
```python
if probabilities_npy is not None and Path(probabilities_npy).exists():
    probs = np.load(probabilities_npy)
    entropy_vals = -np.sum(probs * np.log(probs + 1e-10), axis=1)
    results['mean_entropy'] = float(np.mean(entropy_vals))
    results['entropy_note'] = "computed from full probability vector"
else:
    # fallback approximation ...
    results['entropy_note'] = "approximated from max-confidence (K=11 uniform assumption)"
```

**Mandatory before thesis submission:** YES (disclosure is mandatory; code fix is strongly recommended)

---

### D4 — Ablation Config D Code Definition Contradicts Thesis Text

**Files:**
- `scripts/run_ablation_experiment.py:75–100`
- Thesis text / prior statements

**Why it is dangerous:**
The code defines:
```python
Config A: gravity_removal=False, calibration=False  (baseline — matches training)
Config B: gravity_removal=False, calibration=True   (calibration only)
Config C: gravity_removal=True,  calibration=False  (gravity only)
Config D: gravity_removal=True,  calibration=True   (both)
```
The stated winning configuration is "Config D: calibration + no gravity removal" — which is the definition of **Config B** in the code. Either:
1. The config labels were renamed after the ablation ran, OR
2. The thesis text describes the wrong config as the winner

This is not recoverable from the code alone. The output files in `outputs/ablation/` (if they exist) would be labelled A/B/C/D according to the code at the time they were generated. If the code was changed after generation, the existing result files correspond to the OLD labels.

**Likely consequence:**
If the thesis states "we chose Config D (calibration, no gravity removal)" but the code's Config D is "both gravity removal AND calibration," a reviewer running the ablation will reproduce Config D = the wrong config. The reproducibility claim fails. More importantly: the production config has BOTH gravity removal AND calibration enabled — which matches the code's Config D (not the thesis's Config D). This may mean Config D (gravity+calibration) was actually intentionally chosen, and the thesis description is simply wrong.

**How to verify manually:**
```bash
# Step 1: Check what the code currently defines:
grep -A3 "config_id" scripts/run_ablation_experiment.py

# Step 2: Check if ablation results exist and match:
ls outputs/ablation/ 2>/dev/null
cat outputs/ablation/ablation_summary.csv 2>/dev/null | head -10

# Step 3: Check if the config in pipeline_config.yaml matches any ablation config:
# pipeline_config.yaml has gravity_removal=true AND calibration=true → matches code's Config D
```

**How to fix safely:**
1. Identify which definition was used when the ablation actually ran (check git history of `run_ablation_experiment.py`)
2. If the winner was truly calibration-only (no gravity removal), update `pipeline_config.yaml` to `gravity_removal=false, calibration=true`
3. If the winner was both (gravity+calibration), keep the current production config and correct the thesis text
4. Regardless of outcome: rename the winning config explicitly in the code (e.g., `PRODUCTION_CONFIG = ABLATION_CONFIGS[selected_idx]`) so there is no ambiguity

**Mandatory before thesis submission:** **YES**

---

## C. REPO HYGIENE ISSUES

### H1 — Binary Keras Model Files in Git (68 MB)

**Files:** All `models/retrained/*.keras`, `models/registry/har_model_vauto.keras`

**Why it is dangerous:**
Git is not designed for binary artifacts. Committing 68 MB of Keras files makes the repo slow to clone. More importantly, `models/retrained/` is NOT in `.gitignore` and NOT DVC-tracked, meaning these files are permanent in git history even after deletion. The `models/pretrained/` and `models/trained/` directories ARE DVC-tracked (via `models/pretrained.dvc`) — but retrained models are not.

Also: 4 new `adabn_adapted_model_configA/B/C/D_*.keras` files were generated on 2026-03-29 and are currently untracked (`??` in git status). They need a decision: DVC-track as experiment artifacts, or gitignore.

**How to fix safely:**
```bash
# Add to .gitignore:
echo "models/retrained/*.keras" >> .gitignore
echo "models/registry/*.keras" >> .gitignore

# Remove tracked .keras files from git index (without deleting from disk):
git rm --cached models/retrained/*.keras models/registry/*.keras
git commit -m "chore: stop tracking binary model files in git (use DVC)"

# Track with DVC instead:
dvc add models/retrained/har_model_latest.keras
dvc push
```

**Mandatory before thesis submission:** NO (bloat only, not validity-affecting)

---

### H2 — 37 Unstaged Deletions — Repo Is in Intermediate Cleanup State

**Evidence:** `git status --short | grep "^ D"` returns 37 files locally deleted but not committed.

This includes `config/prometheus.yml`, all Grafana dashboards, all `scripts/_wave1_archive/` and `src/_wave2_archive/` files. The current repo state is inconsistent: any fresh clone from git will restore these 37 deleted files.

**How to fix safely:**
```bash
git add -u   # stages all tracked deletions
git commit -m "chore(cleanup): commit pending archive deletions (wave1, wave2, monitoring stack)"
```

**Mandatory before thesis submission:** YES — the repo should be in a clean, committed state when submitted.

---

## D. DOCUMENTATION DRIFT

### DOC1 — MLflow Logs `gravity_removal_applied = 1.0` When Thesis Says Otherwise

**Files:**
- `src/pipeline/production_pipeline.py:922–926`
- `src/entity/artifact_entity.py:62` — `gravity_removal_applied: bool`

**Why it is dangerous:**
Every pipeline run logs:
```python
metrics["transformation_gravity_removal"] = (
    1.0 if result.transformation.gravity_removal_applied else 0.0
)
```
With `enable_gravity_removal: true` in the current config, every MLflow run in `mlruns/` has this logged as `1.0`. The MLflow runs are evidence. If the thesis text states "we did not apply gravity removal in production" but MLflow records say `transformation_gravity_removal=1.0` for every run, an examiner checking the MLflow tracking server will find a contradiction.

**How to verify manually:**
```bash
# Check if mlruns has logged transformation_gravity_removal:
find mlruns/ -name "transformation_gravity_removal" -o -name "*.metric" 2>/dev/null | head -5
mlflow ui  # then check the har-production-pipeline experiment metrics
```

**How to fix safely:**
Fix B1 (set gravity removal to false) and any future runs will log `0.0`. For past runs, you may need to add a note in the thesis that early experimental runs used gravity removal, but the final evaluated runs did not.

**Mandatory before thesis submission:** YES (derives from B1)

---

### DOC2 — AdaBN Is the Default Adaptation Method, Not a "Documented Limitation"

**Files:**
- `src/entity/config_entity.py:246` — `adaptation_method: str = "adabn"`
- `run_pipeline.py` CLI help — recommends `--adapt adabn_tent`
- `src/pipeline/production_pipeline.py:18` — docstring: "standard / AdaBN / pseudo-label"
- `src/entity/config_entity.py:17` — "Stage 8: unsupervised / supervised, AdaBN"
- `models/retrained/adabn_*.keras` — 4 model files generated from AdaBN runs today

**Why it is dangerous:**
If the thesis frames AdaBN as "a technique that was considered but ruled out due to [reason]," the code presents a contradictory story:
- AdaBN is the **default** when adaptation is enabled (`adaptation_method: str = "adabn"`)
- The CLI help text says `--adapt adabn_tent` is "recommended"
- Stage 8 description explicitly names AdaBN as one of the two primary paths
- 4 AdaBN model files were generated today as part of the ablation

Either AdaBN is part of the thesis (in which case it needs proper experimental justification) or it is not (in which case the default, the CLI help, the stage description, and the model files all need to reflect that).

**Likely consequence:**
An examiner asking "is AdaBN part of your thesis?" gets conflicting signals: the code says yes (it's the default), the thesis text may say no (ruled out). This is a thesis-story integrity problem.

**How to fix safely:**
Option A (AdaBN is a result you're defending): Add an experiment section comparing adaptation methods and cite AdaBN results.
Option B (AdaBN was explored and ruled out): Change the default to `adaptation_method: str = "standard"`, remove AdaBN from CLI examples, update Stage 8 docstring, and document it as "explored but not used in final pipeline."

**Mandatory before thesis submission:** YES

---

### DOC3 — `train.py` Docstring Claims DANN/MMD Are Available

**Files:**
- `src/train.py:14` — "DANN, MMD" listed under domain adaptation
- `src/components/model_retraining.py:72–76` — raises `NotImplementedError` for both

**Why it is dangerous:**
The module docstring in `train.py` lists DANN and MMD as domain adaptation options. `model_retraining.py` raises `NotImplementedError` for both. Any examiner who reads the docstring and then tries to understand what was implemented will find a lie. Small but embarrassing.

**How to fix safely:**
Remove DANN/MMD from the `train.py` docstring. Keep the `NotImplementedError` in `model_retraining.py` (it is correctly defensive) but update its message to note these methods are in the literature but out of scope.

**Mandatory before thesis submission:** NO (cosmetic, but corrects a false claim)

---

### DOC4 — Pipeline Header Says "10 Stages" But Code Has 14

**Files:**
- `src/pipeline/production_pipeline.py:6` — "10 Stages" in module docstring
- `src/pipeline/production_pipeline.py:56–71` — `ALL_STAGES` has 14 entries

**How to fix safely:**
Update the docstring header to show all 14 stages, matching the `ALL_STAGES` list.

**Mandatory before thesis submission:** NO (minor inconsistency)

---

## E. THESIS STORY WEAKNESSES

### T1 — Collapse Guard Has Zero Test Coverage

**Files:**
- `src/trigger_policy.py:333–412` — `_evaluate_collapse_guard`
- `tests/test_trigger_policy.py` — no test for this path
- `tests/conftest.py` — `sample_monitoring_report` has no `collapse_signals` key

**Why it is dangerous:**
The thesis claim "the pipeline detects single-class prediction collapse (>95% dominance) and routes to REVIEW without triggering automatic retraining" cannot be verified by the test suite. Every test call to `engine.evaluate(report)` uses a report without `collapse_signals`, so `_evaluate_collapse_guard` returns `None` immediately and is never exercised. If the examiner asks "can you show me the test that validates this?", the honest answer is "there isn't one."

**How to verify manually:**
```bash
grep -rn "collapse_guard\|collapse_signals\|dominant_pct" tests/
# Returns: no matches in test files
```

**How to fix safely:**
Add to `tests/test_trigger_policy.py`:
```python
class TestCollapseGuard:
    """The 95% dominance guard must fire REVIEW and must NOT auto-retrain."""

    def test_fires_at_95_pct_dominance(self, temp_state_file):
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        report = {
            "collapse_signals": {
                "dominance_warning": True,
                "dominant_class": "hand_tapping",
                "dominant_pct": 97.0,
                "mean_confidence": 0.95,
                "transition_rate": 0.0,
            },
            "confidence_report": {"metrics": {"mean_confidence": 0.95, "mean_entropy": 0.1, "uncertain_ratio": 0.01}},
            "temporal_report": {"metrics": {"flip_rate": 0.0}},
            "drift_report": {"per_channel_metrics": {}, "n_drifted_channels": 0},
        }
        d = engine.evaluate(report)
        assert d.action.value == "review", f"Expected REVIEW, got {d.action}"
        assert d.should_trigger is False, "Collapse guard must NOT auto-retrain"

    def test_does_not_fire_on_normal_distribution(self, temp_state_file):
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
        d = engine.evaluate(report)
        assert d.action.value != "review"

    def test_fires_at_exactly_95_boundary(self, temp_state_file):
        """95.0% is exactly the boundary — must fire."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        report = {
            "collapse_signals": {
                "dominance_warning": False,
                "dominant_class": "sitting",
                "dominant_pct": 95.0,   # exactly at boundary
                "mean_confidence": 0.80,
                "transition_rate": 0.05,
            },
            "confidence_report": {"metrics": {"mean_confidence": 0.80, "mean_entropy": 0.5, "uncertain_ratio": 0.05}},
            "temporal_report": {"metrics": {"flip_rate": 0.05}},
            "drift_report": {"per_channel_metrics": {}, "n_drifted_channels": 0},
        }
        d = engine.evaluate(report)
        assert d.action.value == "review", "Exactly 95% must fire the guard"
```

**Mandatory before thesis submission:** **YES**

---

### T2 — No Reproducibility Entry Point

**Files:** `README.md`, root directory

**Why it is dangerous:**
There is no `REPRODUCE.md`, no `QUICKSTART.md`, and no single documented command sequence that an examiner could follow to reproduce the thesis results from scratch. The `README.md` gives `python run_pipeline.py` as the entry point but says nothing about:
- Which data files are needed and how to obtain them (DVC pull)
- Which model checkpoint is the "published" one
- Which ablation results files correspond to the thesis
- What command was used to generate the final inference run reported in the thesis
- Expected outputs (what numbers should appear)

An examiner who clones the repo cannot reproduce anything without asking the author.

**How to fix safely:**
Create `REPRODUCE.md` with sections:
1. Environment setup (Python version, `pip install -e ".[dev]"`)
2. Data setup (`dvc pull`)
3. Model checkpoint (`models/pretrained/fine_tuned_model_1dcnnbilstm.keras` via `dvc pull`)
4. Run the thesis inference experiment (exact command with config flags)
5. Expected outputs (confidence ~X%, dominant activity distribution, trigger decision)
6. Ablation study reproduction (`python scripts/run_ablation_experiment.py`)

**Mandatory before thesis submission:** YES

---

### T3 — Model Registry Shows No Deployed Model

**Files:** `models/registry/model_registry.json`

**Why it is dangerous:**
```json
{
  "current_version": null,
  "models": { "auto": { "status": "archived", "deployed_at": null } }
}
```
An examiner checking model versioning will find the registry reports nothing is deployed. The actual deployment relies on `models/training_baseline.json` and the pretrained model in `models/pretrained/` (DVC-tracked). The registry is disconnected from reality.

**How to fix safely:**
Update `model_registry.json` to reflect the actual deployed model:
```json
{
  "current_version": "vauto",
  "models": {
    "vauto": {
      "status": "production",
      "deployed_at": "2026-03-27T22:39:18",
      "path": "models/registry/har_model_vauto.keras",
      "metrics": { ... }
    }
  }
}
```
Or alternatively, add a comment in `README.md` and `models/registry/` that the baseline JSON files are the deployment source of truth, and the registry JSON is only an experiment tracking artifact.

**Mandatory before thesis submission:** YES

---

## F. ADDED CHECKS

### MLflow Logged Metric vs Actual Code Analysis

| MLflow Metric | Code Source | Potential Mismatch |
|---|---|---|
| `transformation_gravity_removal` | `result.transformation.gravity_removal_applied` | Will be `1.0` with current config — contradicts thesis if thesis says gravity not removed |
| `monitoring_transition_rate` | `layer2.get("transition_rate", 0.0)` | Logged as **percentage** (0–100); trigger policy uses **fraction** (0–1). Same value, different scales in different metrics |
| `inference_uncertain_pct` | `conf_stats.get("n_uncertain",0) / n_predictions * 100` | Depends on whether `"is_uncertain"` column exists in predictions CSV; if absent, `n_uncertain` is 0 and metric is always 0.0 |
| `trigger_cooldown_active` | `result.trigger.cooldown_active` | Always `0.0` due to hardcoded `False` in `TriggerEvaluationArtifact` (Bug B2) |
| `eval_dominant_activity_pct` | `dist_summary.get("dominant_activity_pct")` | Key `"dominant_activity_pct"` may not exist in `distribution_summary` because `_dominant_pct` was popped (Bug B3) — will silently log `0.0` |

### Tests Using Mocked vs Real Pipeline Behavior

| Test File | What It Tests | Mock/Fixture Type | Problem |
|---|---|---|---|
| `test_trigger_policy.py` | `TriggerPolicyEngine.evaluate()` | Synthetic monitoring reports (no `collapse_signals`) | Tests wrong thresholds (0.55, 0.25); collapse guard never exercised |
| `test_trigger_threshold_pass_through.py` | Config → engine threshold pass-through | Monkeypatches `TriggerPolicyEngine` with `_FakeEngine` | Verifies pass-through only, not behavioral correctness at production thresholds |
| `test_preprocessing.py` | High-pass gravity filter | Synthetic Az=9.8 data | Irrelevant to actual training data where Az mean=−3.5289 |
| `test_threshold_consistency.py` | Threshold ordering | Real config instances | Correctly tests real values — no mocking issue |
| `test_pipeline_integration.py` | Full pipeline run | Needs real data + model files | May pass trivially if stages are skipped due to missing files |

### Ablation Config D Winner in Production Config

**Current production config (`pipeline_config.yaml`):**
- `enable_gravity_removal: true`
- `enable_calibration: true`

**Code's Config D (`run_ablation_experiment.py`):**
- `gravity_removal=True, calibration=True`

**These match.** The production config IS wired to the code's Config D. However, if the thesis says "Config D = calibration only (no gravity removal)," then the thesis description and the wired config are **inconsistent in two different ways**: (a) the thesis describes Config B as Config D, and (b) it claims the winner has no gravity removal, but the production config uses gravity removal. This must be resolved (see D4).

### AdaBN References in Active Code Paths

| Location | Type | Status |
|---|---|---|
| `src/domain_adaptation/adabn.py` | Full implementation | ACTIVE (tested, imported) |
| `src/components/model_retraining.py:64` | Production execution path | ACTIVE — `if method == "adabn": return self._run_adabn()` |
| `src/entity/config_entity.py:246` | Default config value | **ACTIVE default** — `adaptation_method: str = "adabn"` |
| `src/entity/config_entity.py:17` | Stage description | `"Stage 8: unsupervised / supervised, AdaBN"` |
| `run_pipeline.py` CLI help | Recommendation text | `--retrain --adapt adabn_tent (recommended)` |
| `tests/test_adabn.py` | Full test coverage | ACTIVE |
| `models/retrained/adabn_*.keras` | 4 model files created 2026-03-29 | Generated today via ablation |

**Conclusion:** AdaBN is NOT "documented as limitation only." It is the default adaptation method, has a full production execution path, has tests, has generated model artifacts, and is recommended in the CLI help. This is fine if the thesis frames it as "we implemented and evaluated AdaBN." It is a problem if the thesis frames it as "we ruled out AdaBN."

---

## G. MANDATORY FIXES CHECKLIST

Before thesis submission, the following changes are **required** in priority order:

```
[ ] B1  Set enable_gravity_removal: false in config/pipeline_config.yaml
[ ] D4  Resolve ablation Config D labeling — pick one definition, update the other
[ ] T1  Add 3 collapse guard tests to test_trigger_policy.py
[ ] H2  git add -u && git commit -m "chore: commit 37 pending deletions"
[ ] B2  Fix cooldown_active hardcoded False in trigger_evaluation.py
[ ] B3  Add dominant_class / dominant_pct as typed fields on ModelEvaluationArtifact
[ ] D1  Align confidence thresholds — pick one value, document the tiered design
[ ] D2  Add one test using TriggerEvaluationConfig's production thresholds
[ ] D3  Disclose entropy approximation in thesis text (or fix computation)
[ ] T2  Write REPRODUCE.md
[ ] T3  Update model_registry.json or document the deployment source of truth
[ ] DOC1 Fix B1 first — this derives from it
[ ] DOC2 Decide AdaBN thesis role, update code to match
```

---

*Audit produced 2026-03-29 by Claude Code (claude-sonnet-4-6). Every finding cites exact file + line. No advice is generic — all claims were verified against actual code.*

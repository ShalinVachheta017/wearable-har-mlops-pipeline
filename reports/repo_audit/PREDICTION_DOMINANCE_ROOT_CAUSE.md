# Prediction Dominance Root Cause Audit

Audit date: March 6, 2026  
Repository: `MasterArbeit_MLops`  
Scope: Diagnose why production-style wrist data is predicted almost entirely as `hand_tapping` and why trigger stayed `NONE`.

---

## A. Files inspected

### Pipeline orchestration and stage wiring
- `run_pipeline.py`
- `src/pipeline/production_pipeline.py`
- `src/utils/artifacts_manager.py`
- `src/utils/config_loader.py`

### Label mapping / class definitions
- `src/run_inference.py` (hardcoded `ACTIVITY_CLASSES`)
- `src/config.py` (`ACTIVITY_LABELS`)
- `src/utils/main_utils.py` (canonical activity labels helper)
- `data/prepared/config.json` (`activity_to_label`, scaler stats used at inference)
- `src/train.py` (`LabelEncoder`, window-majority labeling)

### Preprocessing, normalization, windowing
- `src/components/data_transformation.py`
- `src/preprocess_data.py`
- `config/pipeline_config.yaml`

### Inference and evaluation
- `src/components/model_inference.py`
- `src/run_inference.py`
- `src/components/model_evaluation.py`
- `src/evaluate_predictions.py`

### Monitoring and trigger policy
- `src/components/post_inference_monitoring.py`
- `scripts/post_inference_monitoring.py`
- `src/components/trigger_evaluation.py`
- `src/trigger_policy.py`
- `docs/TRIGGER_POLICY_EXPLANATION.md`

### Run artifacts/logs audited (latest production-style run)
- `logs/20260306_150635.log`
- `logs/20260306_141508.log`
- `artifacts/20260306_150640/inference/inference_summary.json`
- `artifacts/20260306_150640/evaluation/evaluation_summary.json`
- `outputs/evaluation/evaluation_20260306_150645.json`
- `artifacts/20260306_150640/monitoring/monitoring_summary.json`
- `artifacts/20260306_150640/trigger/trigger_decision.json`
- `artifacts/20260306_150640/data_transformation/production_metadata.json`
- `data/processed/ingestion_manifest.json`
- `models/normalized_baseline.json`

### Data distributions checked directly
- `data/all_users_data_labeled.csv` (sample-level + window-level class balance)
- `artifacts/20260306_150640/inference/predictions_20260306_150645.csv` (probabilities, top-1/top-2 behavior)

---

## B. Current prediction path (input to final class)

1. **Ingestion (Stage 1)**  
   `src/components/data_ingestion.py` auto-discovers sensor pairs and reuses cached fused CSV if already processed.  
   In both audited runs (`2026-03-06 14:15` and `15:06`), logs show:
   - one pair found,
   - pair skipped as already processed,
   - `data/processed/sensor_fused_50Hz.csv` reused.

2. **Validation (Stage 2)**  
   `src/components/data_validation.py` validates fused CSV; warnings are logged but run continues.

3. **Transformation (Stage 3)**  
   `src/components/data_transformation.py` + `src/preprocess_data.py`:
   - detect unlabeled format (`Ax,Ay,Az,Gx,Gy,Gz`),
   - detect units (`milliG`) and convert to `m/s2`,
   - load saved training scaler from `data/prepared/config.json`,
   - normalize production data,
   - create sliding windows (`window_size=200`, `step=100`, overlap 50%),
   - output `production_X.npy` with shape `(1814, 200, 6)`.

4. **Inference (Stage 4)**  
   `src/components/model_inference.py` calls `src/run_inference.py`:
   - model predicts softmax probs,
   - argmax class index converted via `ACTIVITY_CLASSES`,
   - per-window output written to predictions CSV.

5. **Evaluation (Stage 5)**  
   `src/evaluate_predictions.py` computes:
   - class distribution,
   - confidence stats,
   - uncertainty,
   - temporal transitions,
   - dominance warning if one class >95%.

6. **Monitoring (Stage 6)**  
   `src/components/post_inference_monitoring.py` calls `scripts/post_inference_monitoring.py`:
   - Layer 1: confidence/uncertainty,
   - Layer 2: temporal transitions,
   - Layer 3: drift vs baseline JSON.

7. **Trigger (Stage 7)**  
   `src/components/trigger_evaluation.py` builds trigger report and calls `src/trigger_policy.py`.  
   Decision is based on confidence + temporal + drift voting, **not** class semantics.

---

## C. Likely reasons for `hand_tapping` dominance in this repo

### 1. The production run repeatedly reuses the same single source session
- Evidence from logs (`2026-03-06 14:15` and `15:06`): ingestion skipped already-processed pair and reused `sensor_fused_50Hz.csv`.
- `data/processed/ingestion_manifest.json` shows the pair associated with the current fused CSV is `2025-03-23-15-23-10-...xlsx`.
- The same dominance pattern appears across many recent predictions files (local check: last 25 files all ~99.9% `hand_tapping`).

Implication: this is not random run noise; it is consistent behavior on the currently reused production stream.

### 2. Model confidence strongly supports one fine-motion class
From `artifacts/20260306_150640/inference/inference_summary.json`:
- `hand_tapping`: 1813 / 1814 (99.94%)
- mean confidence: `0.934`
- uncertain count: `0`

From prediction probabilities (`predictions_20260306_150645.csv`):
- mean class probabilities: `hand_tapping=0.934`, next `hand_scratching=0.048`, `sitting=0.000653`, `standing=0.000008`
- top-2 class is almost always `hand_scratching` (not posture classes)

This is a stable high-confidence fine-motor cluster, not low-confidence random guessing.

### 3. Production wrist signal is closer to training `hand_tapping` centroid than to `sitting/standing`
Local feature audit (normalized window means):
- distance(production, `hand_tapping`) approx `0.57`
- distance(production, `sitting`) approx `1.49`
- distance(production, `standing`) approx `2.40`

Implication: under this feature space, current production session resembles learned hand-motion patterns more than posture patterns.

### 4. Window-level argmax without temporal post-processing reinforces local wrist-motion dominance
- Windowing is short (`200@50Hz` = 4s, 50% overlap).
- Inference is pure per-window argmax (`np.argmax`).
- No temporal smoothing / HMM / sequence-level correction is applied post-inference.

For desk work with repetitive micro-movements (typing/mouse/gestures), local windows can consistently map to hand-motion classes.

### 5. Trigger design intentionally ignores semantic dominance
- Dominance warning is generated in Stage 5 (`evaluate_predictions.py` >95% rule),
- but Stage 7 consumes only confidence/temporal/drift (`trigger_evaluation.py` -> `trigger_policy.py`).
- Therefore `NONE` trigger with high confidence + low drift + low flip rate is expected by current policy.

### 6. Additional implementation issues reduce semantic visibility in operational summaries
- `ModelEvaluation` reads `pipe.run()` output incorrectly (`result.get("distribution", {})`), while `EvaluationPipeline.run()` returns `{"success": True, "results": ...}`.
  - Operational effect: `artifacts/.../evaluation/evaluation_summary.json` is mostly empty and run metadata logs `mean_confidence: 0`.
- Monitoring drift compares normalized production windows to baseline stats that are saved in raw scale (`models/normalized_baseline.json` is not actually standardized values).
  - Effect: drift can appear artificially mild (here max drift `0.569`) even with scale mismatch.

These do not create `hand_tapping` dominance by themselves, but they weaken the system's ability to diagnose it robustly.

---

## D. Are `sitting` / `standing` underrepresented or weakly separated?

### Underrepresented in training data?
Not strongly underrepresented.

From `data/all_users_data_labeled.csv`:
- sample-level shares are relatively balanced across 11 classes (roughly 8.5%-10.1% each),
- window-majority shares are similarly balanced,
- `hand_tapping` is not dominant in training (about 8.64% window share in local recomputation).

### Weakly separated for wrist-only real-life data?
Likely yes in this deployment context.

Evidence:
- Production windows are much closer to `hand_tapping` centroid than posture centroids.
- Predicted top-2 class is almost always another hand-motion class (`hand_scratching`), not `sitting/standing`.
- This suggests posture labels are being overshadowed by wrist movement signatures in the real session.

Conclusion: **not primarily a training class-imbalance issue; more likely label/feature-context mismatch for wrist-only daily-life behavior.**

---

## E. Is monitoring missing a semantic plausibility check?

Yes.

Current behavior:
- Stage 5 can detect dominance (`distribution_dominance_warning` >95% one class),
- Stage 6/7 do not consume semantic plausibility features (class entropy by meaning, posture-vs-motion consistency, expected context checks),
- trigger policy only evaluates confidence, flip-rate, and drift.

So a semantically suspicious but high-confidence/low-drift batch can remain `PASS` + trigger `NONE` (exactly what happened on March 6, 2026).

---

## F. Recommended fixes ranked by priority

### 1) No-code interpretation/documentation fixes (highest immediate value, lowest risk)
1. Reclassify this event as: **"single-session wrist-motion dominance on reused production stream"**, not immediate model collapse.
2. Document that `sitting/standing` from wrist-only signals represent posture only when hand movement is minimal.
3. Add a runbook note: when dominance >95%, request targeted labeling before retraining decisions.

### 2) Low-risk monitoring/evaluation improvements
1. Add semantic warning rule in monitoring: sustained single-class dominance (e.g., >95% over N windows) as explicit operational alert.
2. Keep it informational at first, but track persistence across sessions/runs.
3. Fix Stage 5 wrapper output parsing (`ModelEvaluation` vs `EvaluationPipeline.run()` shape) so dominance and confidence summaries propagate to artifacts/MLflow.
4. Log dominance metrics explicitly in MLflow (`dominant_class`, `dominant_pct`, `n_classes_detected`).
5. Align baseline scales for drift comparison (normalized production vs truly normalized baseline reference).
6. Wire monitoring/trigger configs consistently (currently some config thresholds are not passed through wrappers).

### 3) Medium-risk model/data improvements
1. Build a labeled "desk-work" audit set (especially sitting/standing with active hand use).
2. Re-evaluate posture-vs-hand labels under subject-wise split (GroupKFold/LOSO) for realistic generalization.
3. Consider a two-stage classifier (posture vs hand-behavior first, then subclass) or explicit temporal smoothing for deployment outputs.
4. If posture recognition is a hard requirement, consider additional context (extra sensors/features) beyond wrist-only IMU.

---

## G. Explicit recommendation

### Should this be only a warning?
For the current evidence: **yes, warning-level operationally** (not immediate auto-retrain trigger by itself), because:
- no production ground truth labels are present,
- confidence/temporal/drift are currently normal,
- retraining on unlabeled single-class-like data is risky.

### Should it affect trigger logic?
**Yes, but as a gated semantic signal**, not as a standalone retrain trigger.
- Recommended: incorporate dominance persistence and semantic plausibility into trigger voting as an additional warning channel.
- Escalate only if persistent across multiple sessions and/or confirmed by labeled audit slice.

### Should retraining be considered now?
**Not immediate blind retraining.**  
Retraining should be considered **after** collecting labeled desk-work samples and confirming systematic posture misclassification on labeled evaluation.

---

## Direct answers to requested questions

### Why would normal desk work while sitting be classified as `hand_tapping`?
Because this model is wrist-motion driven at 4-second window scale. Repetitive desk micro-motions can dominate local features, and in this run those features align more with learned `hand_tapping` than posture centroids (and top-2 is usually `hand_scratching`, not `sitting/standing`).

### Why might `sitting` and `standing` not appear often in wrist-only production data?
Wrist IMU captures hand movement strongly but posture weakly. If hands are active while sitting/standing, motion classes can dominate predictions; posture classes appear mostly when wrist movement is relatively still.

### Is this likely a data problem, label problem, model problem, monitoring problem, or a combination?
**Combination**, with strongest weight on:
1. **Data/context mismatch** (reused single-session production stream + desk-style wrist motion),
2. **Label/semantic mismatch** (posture labels in wrist-only real use),
3. **Monitoring/trigger design gap** (no semantic plausibility signal in trigger).

Training class imbalance is **not** the primary evidence-backed cause in this repo.

---

## Uncertainty / limits

1. Production run is unlabeled, so true activity cannot be confirmed from repo artifacts alone.
2. The March 24, 2025 source session may genuinely contain prolonged repetitive hand behavior; misclassification cannot be proven without labels/video/context.
3. Quantitative class-separation evidence here uses lightweight centroid analysis (helpful signal, not a full discriminative study).

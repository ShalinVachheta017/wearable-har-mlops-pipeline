<!-- markdownlint-disable MD013 MD024 MD033 -->

# Thesis Understanding & Defense Prep

*Prepared 2026-06-07. Study companion to `defense_qa.md` and `STAGE_BY_STAGE_TECHNICAL_CONFIDENCE.md`.*
*Numbers are the canonical deployed-D1 ground truth (build notebook, corrected 2026-06-04).*

---

## 0. The 30-second thesis story (say this first, always)

> "I did **not** build a mental-health diagnosis system. I built an **offline-first, governed MLOps pipeline** for wearable activity recognition. The real contribution is treating the **runtime contract** — model + scaler + label order + monitoring baseline + evidence, promoted together in one folder — as the deployment unit, not the model file. The model learns the in-distribution task well (5-fold CV 93.61%), but cross-user generalization is weak (LOUO 44.42%, User-7 36.96%). The pipeline's job is to **observe that risk honestly and refuse to retrain itself blindly** — separation of observation from action."

### Numbers you must know cold

| Metric | Value | Meaning |
|---|---|---|
| 5-fold window CV | **93.61% / 0.937 macro-F1** | In-distribution learnability; mentor-comparable benchmark (Oleh ~87%) |
| LOUO (users 1–6) | **44.42% / 0.419** | Strict unseen-user generalization — weak (this is the *finding*, not a failure) |
| User-7 blind probe | **36.96% / 0.350 / conf 0.858** | External post-freeze descriptive probe |
| Calibration gap | conf **0.858** vs acc **~0.37** | High-confidence *mis*prediction — confidence alone won't catch failures |
| User-2 LOUO | **0.088** | Documented outlier / domain-shift case (drags LOUO down) |
| D1 params | **~967,000** | Final runtime model |
| Window / stride / rate | **200 / 100 / 50 Hz** | 4 s window, 2 s cadence, 50% overlap |
| Channels / classes | **6 / 11** | Ax,Ay,Az,Gx,Gy,Gz → 11 activity labels |
| Unlabeled monitoring | **23/25 REVIEW, 0/25 retrain** | Governance worked: flagged risk, never auto-retrained |

---

## 1. Chapter-by-chapter breakdown

For each chapter: **why it exists · why this choice · limitation · likely examiner question · plain-language explanation.**

### Ch 1 — Introduction

- **Why it exists:** Frames the problem and narrows the claim. Sets the scope boundary that protects you the whole defense.
- **Why this framing:** Wearable sensing gives objective, continuous signals where clinical interviews are episodic. But recognizing a *behavior* (nail-biting) ≠ diagnosing a *condition* (anxiety). The thesis deliberately claims only behavioral-proxy HAR in a mental-health-*adjacent* context.
- **Limitation:** The title still says "Mental Health Monitoring," which over-reaches relative to §1.5. Be ready to own this verbally.
- **Examiner may ask:** *"Are you claiming to detect anxiety?"* → No. I recognize observable wrist-motion activities; clinical interpretation is explicitly out of scope (§1.5).
- **Plain language:** "I'm building the *plumbing and safety system* for a behavior-monitoring app, not the doctor."

### Ch 2 — Background & Related Work

- **Why it exists:** Positions the thesis in two literatures — wearable HAR (deep learning) and MLOps — and shows the gap is their *intersection* for label-scarce health-adjacent data.
- **Why this method:** Builds the CNN→LSTM→BiLSTM lineage (Hochreiter, Schuster & Paliwal, Ordóñez & Roggen, Hammerla) and the "lab-to-life / train–serve mismatch" motivation that the whole pipeline answers.
- **Limitation:** It's a master's-level review; depth varies by section. Synthesis Table 2.1 carries the weight.
- **Examiner may ask:** *"What's actually new versus existing HAR papers?"* → Existing work optimizes accuracy in-distribution. I add the lifecycle/governance layer and an honest cross-user evaluation.
- **Plain language:** "Other people proved the model can work in the lab. I focus on what breaks when it leaves the lab."

### Ch 3 — Offline-First MLOps System Architecture (your strongest chapter)

- **Why it exists:** Defines the system-level rules: two execution paths and the runtime-contract invariant.
- **Why this design:**
  - **Stages 1–7 = operational assessment path** (ingest → validate → transform → infer → evaluate → monitor → trigger) — runs on every session, **never mutates the model**.
  - **Stages 8–10 = governed mutation path** (retrain → register → promote) — entered only with review + labels + validation evidence.
  - **Same-folder invariant:** model, scaler, label order, baseline, metadata, evidence are promoted *together*, so the model can't silently load a mismatched scaler.
- **Limitation:** The invariant is enforced in code for model↔scaler, but the **monitoring baseline** is aligned via config/API defaults, not the same helper — so don't overclaim "everything is auto-enforced."
- **Examiner may ask:** *"Why offline-first and not cloud/Kubernetes?"* → Distributed orchestration adds infra complexity without strengthening the evidence about preprocessing contracts, monitoring, and governance. Offline-first = reproducible on one machine from versioned code + data + artifacts.
- **Plain language:** "The model is just one part. Shipping only the model file is like shipping an engine with no fuel spec — it'll run, but on the wrong fuel it quietly produces garbage. I ship the engine *and* the fuel spec, locked together."

### Ch 4 — Data & Model Development

- **Why it exists:** Specifies the **data contract** (sources, units, schema, label space) and the model the architecture must preserve.
- **Why these choices:**
  - **Evidence-role separation:** ADAMSense = pretraining; Garmin 1–6 = adaptation + CV/LOUO; **User-7 = blind probe** held out of training, scaler fit, and HP selection. This is your methodological shield.
  - **Units/schema:** milli-g → m/s² (`1 mg = 0.00980665 m/s²`); fixed channel order; 50 Hz; window 200 / stride 100; 11 classes.
  - **Model D1:** 1D-CNN (local motion motifs) + BiLSTM (temporal dependency) → 11-class softmax.
- **Limitation:** The architecture table is block-level; exact filter/kernel/unit/dropout counts and full training hyperparameters belong in the text/appendix. Class imbalance handling should be stated explicitly.
- **Examiner may ask:** *"Why fit the scaler only on training data?"* → To prevent leakage and keep train–serve consistency; refitting on an inference batch would change the feature space the model was trained on.
- **Plain language:** "I kept one user (User 7) in a sealed envelope and never let the model or the scaler see them until the very end — so any number on User 7 is honest."

### Ch 5 — Pipeline Implementation

- **Why it exists:** Shows the architecture is *real code*, not a diagram — auditable stage→module mapping, config layering, run-scoped artifacts.
- **Why this design:** Single entrypoint (`run_pipeline.py`), config precedence (env/CLI > YAML > Python defaults), `DEFAULT_MODEL_PATH`/`assert_scaler_integrity()` enforcing the contract, SHA-256/`artifact_md5` integrity, API↔batch parity (~10⁻⁶ max abs diff).
- **Limitation:** Strongest recognition numbers come from notebook artifacts; the pipeline consumes the frozen contract. A provenance table makes this impossible to misread. `artifact_md5.json` doesn't hash the SavedModel directory.
- **Examiner may ask:** *"How do I know the API and the batch pipeline do the same thing?"* → Parity check: same input through both paths agrees to ~10⁻⁶. It's an *implementation-consistency* claim, not an accuracy claim.
- **Plain language:** "Every run leaves a paper trail — same input always gives the same output, and you can trace any prediction back to the exact model, scaler, and config that produced it."

### Ch 6 — Monitoring, Drift & Retraining Governance

- **Why it exists:** At inference there are **no labels**, so you can't compute accuracy live. You need *proxy* signals and a *safe* response policy.
- **Why these signals:** Confidence/uncertainty, temporal stability (class-switch rate), dominant-class collapse, distribution drift vs the training baseline. Trigger maps signals → accept / warning / review. **`auto_retrain = false` is a deliberate governance policy.**
- **Limitation:** The calibration gap (conf 0.858 vs acc 0.37) means confidence *alone* misses User-7-style failures — high-confidence wrong answers. Thresholds are conservative defaults, not calibrated/clinical limits.
- **Examiner may ask:** *"If drift is detected, why not retrain automatically?"* → Because a drift/collapse signal indicates *risk*, not that retraining would *help*. On label-scarce, possibly-collapsed data, blind retraining can reinforce the model's own errors. So risk → human review, not auto-mutation.
- **Plain language:** "The system is allowed to raise its hand and say 'something looks off,' but it's not allowed to operate on itself. A human decides."

### Ch 7 — Experiments & Evaluation

- **Why it exists:** Delivers the honest two-number story and the evidence behind every claim.
- **Why these metrics:** Three protocols answer three different questions — 5-fold CV (in-distribution learnability), LOUO (unseen-user generalization), User-7 (external blind probe). Plus ECE/reliability for calibration, confusion matrix for per-class behavior, 23/25-REVIEW unlabeled run for governance.
- **Limitation:** 6 training users + 1 external user is small; User-7 is a single self-recorded session. Don't generalize beyond it.
- **Examiner may ask:** *"Your accuracy is 37% — isn't the system broken?"* → No. 93.61% in-distribution proves the pipeline and model are sound; the drop to 44% LOUO / 37% User-7 is the *measured* cross-user domain-shift gap — which is exactly the phenomenon the MLOps layer exists to detect and govern.
- **Plain language:** "On people it has seen, it's strong. On a brand-new person, it struggles — and instead of hiding that, the system measures it and reacts safely."

### Ch 8 — Discussion & Conclusion

- **Why it exists:** Answers RQ1–4, states limitations and non-claims, sets future work.
- **Why this framing:** Reframes the weak cross-user number as a *contribution* (an MLOps system that surfaces and governs the gap), not a defect. Future work: on-device, more users, post-hoc calibration, optional cloud multi-user.
- **Limitation:** Honest negative result on RQ4 (collapse can be the pipeline's own fault); not clinical, not production-ready.
- **Examiner may ask:** *"What would you do with six more months?"* → More users for LOUO power, fitted calibration to close the confidence-accuracy gap, and on-device inference.
- **Plain language:** "The headline isn't 'I solved wearable anxiety detection.' It's 'I built the safety-and-governance scaffolding that makes such a system trustworthy to operate.'"

---

## 2. The nine examiner questions (crisp answers)

**Q1 — Why wearable HAR?**
Wrist IMUs are unobtrusive, already widely worn, and capture continuous objective motion — unlike episodic clinical questionnaires. Anxiety-related behaviors (nail-biting, hair-pulling, scratching, tapping) are *observable wrist motions*, so they're a natural HAR target. I recognize the behavior, not the mental state.

**Q2 — Why Garmin?**
It's the commercial-wearable target of the supervising group's study (Oleh & Obermaisser), so it grounds the "lab-to-life" transfer question on a real consumer device with real users 1–6. It gives me a labeled commercial-wearable adaptation set plus my own external User-7 recording on the same device and protocol.

**Q3 — Why ADAMSense?**
It's the source-domain anxiety-/behavior-activity dataset used for **supervised pretraining**. It teaches the model a useful initial representation of these activities before I fine-tune on the smaller, noisier commercial-wearable Garmin data. Pretrain-then-adapt is standard when target labeled data are limited.

**Q4 — Why 50 Hz?**
It's the defended runtime sampling-rate contract — enough temporal resolution for wrist micro-movements while keeping inputs compact, and consistent with wearable-HAR norms (UCI-HAR heritage). Crucially, 50 Hz *defines the temporal meaning* of a window: 200 samples = 4 s, 100-sample stride = 2 s. Recordings are resampled to a strict 50 Hz grid so the model always sees the same time-scale.

**Q5 — Why window size 200?**
At 50 Hz, 200 samples = **4 seconds** — long enough to contain a full repetitive wrist pattern (a tap cycle, a rub, a bite motion) but short enough not to mix multiple activities into one input. Stride 100 (50% overlap) reduces boundary sensitivity and gives a 2-second prediction cadence. Windows never cross an activity boundary (segment-safe labeling).

**Q6 — Why 1D-CNN-BiLSTM?**
The task has two structures: **local motion motifs** (handled by 1D convolutions over the time axis) and **sequential dependency across the window** (handled by the bidirectional LSTM, which uses both past and future context within the fixed window). It's also the architecture family established by the supervising group's Garmin work, so results are comparable. I'm not proposing a new architecture — it's the recognition component inside the MLOps lifecycle.

**Q7 — Why MLOps (not just a model)?**
A trained classifier alone isn't a trustworthy monitoring system. When a model meets production-style data — new users, unit/placement differences, drift — its behavior changes and labels are usually unavailable to catch it. MLOps treats ingestion, validation, transformation, inference, monitoring, evaluation, and *governed* retraining as one reproducible, auditable lifecycle. That lifecycle — especially the runtime contract and the no-auto-retrain governance — is the contribution.

**Q8 — Why is 5-fold high (93.61%) but User-7 low (36.96%)?**
Different questions. **5-fold window CV** mixes windows from all users across folds, so train and test share users → it measures *in-distribution learnability* and is high. **LOUO / User-7** holds an entire person out → it measures *cross-user generalization*, which is genuinely hard for fine-grained wrist behaviors with only 6 training users (and User-2 is a documented outlier at 0.088). The gap isn't a bug; it's the train–serve/domain-shift phenomenon the thesis is built to expose and govern. The dangerous part is that confidence stays high (0.858) while accuracy falls — high-confidence misprediction — which is exactly why confidence alone isn't a safe trigger.

**Q9 — What is the real contribution?**
An **offline-first, governed MLOps pipeline for wearable behavioral-proxy HAR**, whose core ideas are: (1) **the runtime contract is the deployment unit** — model + scaler + label order + baseline + evidence promoted together in one folder (same-folder invariant); (2) **separation of observation from action** — Stages 1–7 can flag risk without ever mutating the model; Stages 8–10 require human-gated governance; (3) an **honest cross-user evaluation** that measures, rather than hides, the generalization gap and the calibration gap. It is explicitly *not* a clinical, production-grade, or solved-generalization system.

---

## 3. Traps & non-claims (memorize the negatives)

- ❌ Not diagnosis / prognosis / treatment — ✅ behavioral-proxy recognition, mental-health-*adjacent*.
- ❌ Not production-ready, not clinical, not a medical device.
- ❌ Not solved cross-user generalization — it's *measured* and *governed*.
- ❌ Don't say "the system retrains when it drifts" — it **routes to review**; `auto_retrain=false`.
- ❌ Don't claim "all artifacts are hashed" — the SavedModel directory isn't covered by `artifact_md5.json`.
- ❌ Don't claim the same-folder invariant auto-enforces the monitoring baseline — that's aligned via config/API defaults.
- ✅ Do say: "in-distribution success rules out a *gross* pipeline break" (not "proves the pipeline is correct").
- ✅ Do frame the weak numbers as the **motivation and the finding**, delivered honestly.

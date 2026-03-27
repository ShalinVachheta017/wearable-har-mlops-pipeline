# HAR MLOps Thesis — Proposed Answers to Mentor Questions

**Date:** February 24, 2026  
**Author:** Shalin (working notes, not for submission as-is)

These are **draft answers and options** for the questions in `mentor_questions.md`. They are based on:

- Current codebase and implementation
- Standard practice in wearable HAR research  
- Test-time adaptation papers (AdaBN, TENT, pseudo-labeling)  
- Domain adaptation and MLOps literature (DANN, MMD, Google/AWS MLOps guides)

**Purpose of this document:**
- Prepare for meetings with your mentor  
- Decide which work is **must-do now** vs **future work**  
- Turn parts into thesis text later

---

## 1. Monitoring thresholds (Q1–Q2)

### Q1 — Minimum requirement for threshold calibration

**Recommended thesis-level solution:**

- Pick **one consistent set of thresholds** and justify them with **simple experiments**, not a huge sensitivity study.
- Suggested process:
  - Start from literature defaults (e.g., PSI 0.1/0.2, 2σ for z-score, etc.).
  - Replay the 26 sessions and also create **2–3 synthetic drift scenarios** (scale sensors, add offset, change class proportions).
  - For each threshold setting, measure:
    - How often each monitor layer fires on "normal" data (false alarms).
    - Whether it fires on the synthetic drift scenarios (detection).
  - Choose thresholds that:
    - Rarely trigger on clean data.
    - Do trigger on clearly drifted scenarios.
- Document this as a **practical calibration** rather than fully formal statistics.

**Why this is thesis-appropriate:**

- Many "standard" thresholds in monitoring (e.g., PSI 0.10/0.25) are **heuristics**, not laws; papers in credit risk explicitly note they are not statistically 'magic' constants.[^psi]
- **Empirical calibration on your multi-channel HAR data** is actually better than blindly copying numbers from different domains.
- A full sensitivity analysis (many thresholds, ROC-like curves, optimal trade-offs) would be more like a separate research paper.

**What to say to mentor:**  
"I will choose one set of thresholds and do small, focused experiments (including synthetic drift) to show they behave sensibly. I do not plan a very large sensitivity study unless you feel it is necessary."

---

### Q2 — Canonical config (pipeline vs API thresholds)

**Recommendation:**

- Define **one "canonical" config** (e.g., `PostInferenceMonitoringConfig`) and make both:
  - the pipeline script, and
  - the FastAPI service  
  read from it.
- In the thesis, state clearly:
  - "All monitoring thresholds used in this work are defined in a single config file and shared between batch and API paths."

**Why this matters for the thesis:**

- Avoids confusion ("which thresholds produced these results?").  
- Makes experiments **reproducible**.  
- Matches good MLOps practice: config-driven behaviour, not magic constants spread in code.

---

## 2. Scalability and latency (Q3–Q4)

### Q3 — What counts as "scalable" here?

For a **master's thesis PoC**, you do **not** need Kubernetes or a big cluster. A realistic level is:

**Offline evidence:**
- Run timing experiments on **one machine**:
  - Inference time vs number of windows/sessions (scaling curve).
  - Show that cost grows **roughly linearly** with data size.
  
**Design evidence:**
- In Methods/Discussion, show a **diagram** that explains:
  - Where you could put horizontal scaling (API replicas, batch workers).
  - How state (e.g., trigger file, models, data) could move to shared storage or a DB.

**Positioning in thesis:**

You can then claim: "We demonstrate single-machine scalability empirically, and we design (but do not fully implement) a horizontally scalable architecture." 

This aligns with Google/AWS MLOps "Level 1–2" style PoC systems and matches your original plan's emphasis on "proof-of-concept and scalability principles, rather than full production-grade system."

---

### Q4 — Latency in the API

**Recommended minimum:**

- Implement a **simple latency benchmark**:
  - Send many requests through the API (or direct model calls).
  - Measure typical and worst-case latency (e.g., median, p90, p95) on your laptop/VM.
- Report these numbers with:
  - Hardware details (CPU, RAM).
  - Batch size and window length.

**Why measure:**

You don't need deep queuing theory, but a simple measurement is better than leaving latency totally unmeasured. If mentor says numbers are not needed, you can still keep the script for your own confidence.

---

## 3. Prognosis model & MLOps scope (Q5–Q8)

### Overall recommendation

Given the current state of your work and the time available:

- Make **HAR + monitoring + adaptation** the **main scientific focus**.
- Treat the prognosis model as **designed but not fully implemented**.

### Minimum work for prognosis side (Q5–Q7)

1. **Clear problem statement** in the thesis:
   - Example: "Given aggregated behaviour features over a week (e.g., time spent in each activity), the prognosis model would output a risk score/clinical category for anxiety severity."

2. **Interface design:**
   - Define what the prognosis stage would **input** and **output**:
     - Input: per-session or per-week summary vectors from HAR (e.g., 11-dim activity distribution, transition features).
     - Output: scalar risk score or multi-class label.

3. **Storage choice:**
   - Choose a simple storage form (e.g., Parquet/CSV files or SQLite) for HAR outputs that would feed into prognosis.

4. **Minimal placeholder implementation (optional but good):**
   - Add a dummy stage in the pipeline:
     - Reads the HAR summary.
     - Writes a placeholder risk value or "TODO" marker.
   - This shows where a real prognosis model would plug in.

**Why this is acceptable:**

This is usually enough for a **"future work" prognosis layer** in a master's thesis, especially if your main contributions are in monitoring and adaptation. Many clinical ML papers outline prognosis as a **conceptual pipeline** but focus the thesis on one key stage due to time and data constraints.

---

### Q8 — "Coral" clarification

**What "CORAL" could mean:**

1. **CORAL (Domain Adaptation Method):**
   - CORrelation ALignment
   - A technique to align feature covariances between source and target domains.
   - Would sit between feature extraction and classification.

2. **Clinical Assessment Scale:**
   - Some clinical/mental health assessment tool.
   - Would be used as prognosis target/output.

3. **Something project-specific**

**What to ask mentor:**

"When you mentioned 'coral', did you mean the CORAL domain adaptation method, a clinical assessment tool, or something else? And where should it conceptually sit in the pipeline?"

Once clarified, document it properly in your design.

---

## 4. Online vs offline monitoring and automation (Q9–Q11)

### Q9 — Online simulation

**Acceptable thesis setup:**

- Treat "online" as:
  - **Per-file** processing through the API, one session at a time, in the order they would arrive.
  - Run the monitoring after each upload.
- Run a **session-replay experiment**:
  - Replay all 26 sessions through the API in sequence.
  - Log monitoring signals per session (confidence, drift, transitions).

**Why this is appropriate:**

In applied ML systems, it is common to **simulate online** by replaying historical data through the API. This is acceptable for PoC and commonly done in papers where live devices are not available. Explain clearly that this simulates a live service without requiring BLE streaming.

---

### Q10 — Manual vs automatic retrain

**Recommended compromise:**

- Implement and document a **manual retrain loop**:
  - Monitor writes its state.
  - Human reads a summary report/flag.
  - Human runs `--retrain` when needed.
  
- Also design (on paper + code skeleton) a **CI/CD workflow** that could:
  - Read the trigger state.
  - Start retraining automatically.
  - Register/promote a model.

**Positioning in thesis:**

"We implement a manual retrain trigger and provide a design for full automation; full automation is future work as it would require production infrastructure."

This is acceptable at master's level, especially since your original plan says "initial retraining strategy/prototype."

---

### Q11 — Prometheus/Grafana vs MLflow

**Reasonable positioning:**

- Make **MLflow** your **main evaluation and model tracking tool** (runs, metrics, artifacts).
- Treat **Prometheus + Grafana** as **designed but not fully deployed**:
  - Metrics are defined and exported in code.
  - Dashboards JSON prepared.
  - You explain how they would be hooked up in a real deployment.

**Why this works:**

This keeps your monitoring story coherent while respecting the "proof-of-concept, not full production" scope. For a PoC thesis, MLflow + logs + static plots are enough for demonstrating monitoring concepts.

---

## 5. Evaluation and metrics (Q12–Q16)

### Q12 — Subject-wise evaluation

**Background from literature:**

Subject-wise evaluation is standard in wearable HAR; common setups use **GroupKFold** (subjects as groups) or **LOSO (Leave-One-Subject-Out)**.[^loso] This avoids leakage where data from the same person appears in both train and test.

**Your situation:**

You have two data scenarios:

1. **Original labeled lab dataset (Oleh & Obermaisser):**
   - These data **do have subject information**, so you can:
     - Use **GroupKFold** or **LOSO** (Leave-One-Subject-Out).
   
2. **Unlabeled/"production-style" data:**
   - Here you cannot do subject-wise evaluation (no labels and maybe no IDs).
   - Treat this as **unlabeled monitoring only**.

**Recommended position:**

- Use **subject-wise splits** (GroupKFold or LOSO) **only** on the labeled dataset for main accuracy evaluation.
- Clearly state that unlabeled real-world data is used **only for monitoring experiments**, not for accuracy evaluation.

---

### Q13 — Minimum acceptable performance

**Reasoning:**

Because the field has no strict universal threshold, you should **let your mentor choose** a number. But to prepare, you can reason:

- If subject-wise macro F1 is still **>~0.75**, that is usually considered "good" for a small HAR dataset with 11 classes including rare ones.
- If it drops very low (e.g., <0.6), you will need to **discuss limitations honestly**, but it can still pass if:
  - You analyze *why* it drops.
  - You show that your monitoring and adaptation are robust given this baseline.

**Key point:**

The thesis's novelty is in **pipeline + monitoring + adaptation**, not achieving state-of-the-art accuracy.

---

### Q14 — Which results to report

**Strong recommendation:**

- Only report **MLflow-traceable, reproducible** results as main numbers.
- Older values that you cannot reproduce should be:
  - Mentioned, if at all, only as **planning estimates**, not evaluation results.
  - Clearly marked as obsolete/untraceable.

**Why:** This is crucial for reproducibility and scientific integrity.

---

### Q15 — Per-class metrics and statistics

**Best practice in HAR and imbalanced classification:**

- **Main metric:** macro F1 across all 11 classes.
- **Also report:**
  - **Per-class recall** (so you can show nail-biting, etc., explicitly).
  - Mean ± standard deviation across folds for main metrics.
- **Statistical tests:**
  - Wilcoxon signed-rank test for comparing adaptation methods is **nice to have** but not mandatory for a master's, unless your mentor insists.
  - Descriptive statistics (mean ± std) are usually sufficient.

---

### Q16 — Hyperparameter optimization (HPO)

**Reasonable level for a master's:**

- Choose **one simple HPO strategy** for labeled retraining experiments:
  - Grid search on 2–3 key parameters (learning rate, batch size, maybe dropout).
  - Or a small **Optuna** search with a limited number of trials.
  
- The goal is to show:
  - You are not using totally arbitrary hyperparameters.
  - The search space is small and reproducible.

**What to emphasize:**

Full, heavy HPO frameworks are not necessary if they cost too much time. A small, well-documented search tracked in MLflow is enough. Treat extensive HPO as **future work**.

---

## 6. Data quality and generalization (Q17–Q19)

### Q17 — Unit check as data quality gate

**Good idea and thesis-worthy:**

- Add a final check after conversion:
  - Example: "Median magnitude at rest should lie in a plausible range (around 1 g = 9.8 m/s²)."
- If it fails, mark the session as "suspect units" and **stop** or log an error.
- Describe this as a **data quality gate** in the Methods chapter.

**Why this matters:**

The milliG vs m/s² bug almost destroyed performance. This check would catch similar issues early and demonstrates good ML engineering practice.

---

### Q18 — How to describe generalization (single-site data)

**Reality of your data:**

- 26 sessions from a **real recording setup**, but from a **single lab protocol/site**.

**Recommended wording for thesis:**

- "The dataset represents **controlled, real-world recordings** from a single site."
- "Results are expected to transfer best to **similar setups** (same device, similar protocol)."
- "Generalization to very different settings (other devices, free-living conditions) is **not guaranteed** and would require further data and validation."

**Why this works:**

This is honest and matches how many HAR theses describe their scope. You're not claiming universal generalization, which would be unrealistic.

---

### Q19 — PSI/Z-score recalibration as contribution

**The finding:**

- Literature thresholds (e.g., PSI 0.1, |z| > 2) are often defined for **single variables** or simpler settings.
- When aggregating **multiple channels** (6 sensors, many windows), you observed:
  - PSI and z-scores tend to be **inflated**, causing constant false alarms.
- You empirically recalibrated these thresholds on your dataset to find values that:
  - Rarely fire on stable training-like data.
  - Do fire on clearly perturbed data.

**How to position:**

This can be a **small methodological contribution**: "multi-channel calibration of drift thresholds in HAR monitoring."

Present both PSI and Z-score as part of a **single theme**: adapting drift detection thresholds from single-variable domains to multi-channel time series.

---

## 7. Adaptation methods (Q20–Q22)

### Q20 — AdaBN + TENT interaction

**Background from research:**

- **AdaBN** (Li et al., 2016) adapts to new domains by updating batch-norm statistics without changing weights.[^adabn]
- **TENT** (Wang et al., 2021) performs test-time adaptation by minimizing prediction entropy and updating specific parameters (often BN affine params and/or running statistics) on incoming batches.[^tent]
- Papers typically apply one of these methods alone; **interaction bugs** when combining them are not well documented.

**Your finding:**

- TENT's backward pass was resetting AdaBN's batch-norm statistics, effectively undoing AdaBN's work.
- Your fix (snapshot & restore BN running statistics around TENT updates) resolves this.

**How to position:**

This discovered bug plus your fix is **legitimate technical novelty**. Present it as **one of the main technical contributions**, with:
- A clear description of the bug's effect (performance degradation, confidence collapse).
- A small before/after comparison showing the fix works.
- Implementation guidance for others combining these methods.

---

### Q21 — Self-consistency filter and rare classes

**The trade-off:**

Your filter keeps only windows where the model's prediction matches the true label (for source data) and/or has high confidence (for pseudo-labels).

**Pros:**
- Reduces noisy labels.
- Focuses retraining on "reliable" examples.

**Cons (especially in your data):**
- Rare classes like nail-biting, knuckle-cracking may never reach high confidence.
- These classes then barely appear in retraining, which risks **class collapse** (model forgets them).
- Made worse by: not all 11 classes appear in every dataset.
- Hand-tapping prevalence (possibly artifact of "hands on table" position).

**Recommended experiment:**

Run at least **one ablation**:
- Pseudo-labeling **with** the self-consistency filter.
- Pseudo-labeling **without** it (or with a looser threshold).

Evaluate:
- Overall macro F1.
- Per-class performance, especially for rare classes.

In text, explain that strict self-consistency filtering retains only ~14.5% of data and can starve rare classes. Use the ablation to justify your final choice.

---

### Q22 — Implementation details (TENT slowdown)

**Recommended approach:**

- Mention the TensorFlow graph retracing issue briefly in the main text (as an example of engineering challenges with test-time adaptation).
- Put technical details (e.g., `model.predict` vs direct `model(...)` calls, `@tf.function` compilation issues) in an appendix or engineering log.

**Why:** This shows you did serious engineering without cluttering the main narrative.

---

## 8. CI/CD and code completeness (Q23–Q27)

### Q23–Q24 — CI/CD completeness and registry evidence

**Reasonable PoC level (matching Google/AWS MLOps maturity models):**

**You already have:**
- Dockerized training and inference.
- GitHub Actions tests and builds.
- A model registry and basic promotion logic.
- Monitoring code and manual retrain trigger.

**You should also have:**
- One **demonstrated run** of:
  - "train → evaluate → register → promote" with logs or screenshots.

**You are NOT required to have:**
- Fully automatic retrain and deploy to production.
- Complex approval workflows and rollback automation.

**Positioning:**

This matches "proof-of-concept pipeline with clear path to production," which is realistic for a master's project and aligns with your original plan.

---

### Q25–Q27 — DANN, MMD, and PoC vs production expectations

**Background from research:**

- **DANN** (Ganin et al., 2016) is a classic domain-adversarial network with a gradient reversal layer for domain-invariant features.[^dann]
- **MMD** (Gretton et al., 2012) is a kernel two-sample test widely used as a discrepancy measure in domain adaptation and drift detection.[^mmd]

**Recommended answer direction:**

Given time constraints and thesis scope:

- Keep DANN and MMD as **clearly labeled future work** rather than implementing them now.
- Mention them in the related-work/future-work section as potential next-step methods beyond AdaBN/TENT/pseudo-labeling.

**For PoC vs production:**

- Argue that your current system (Dockerized pipeline, API, CI, registry, monitoring, manual retrain) **meets the original PoC goals**.
- Full DANN/MMD implementation and fully automated CI/CD can be framed explicitly as **Level-2+ MLOps** and future work.
- Your original plan states: "emphasis on proof-of-concept and scalability principles, rather than full production-grade system."

---

### Q26 — How many bugs to show

**Recommendation:**

- Show only the **most important bugs** (unit mismatch, PSI/Z-score recalibration, AdaBN+TENT interaction) in the main text.
- Move the full bug list (all 19) to an appendix.

**Why:** This keeps the main narrative focused on scientifically interesting findings rather than exhaustive debugging logs.

---

## 9. Thesis expectations and priorities (Q29–Q34)

### Q29 — Which targets must be measured

**Suggested split to propose to mentor:**

**Must measure** (with real experiments):
- Inference latency (per window or per session) on known hardware.
- At least some evidence on monitoring behavior (examples of true/false alarms on replayed sessions).

**Can be design-level** (architecture + reasoning only, unless mentor insists):
- Weekly false-trigger rate in deployment (you don't have long-term production logs).
- Availability/rollback time (you can describe expected behavior, not guarantee it).

**Why this split:** Be explicit in the thesis which metrics are **measured** vs **design targets**.

---

### Q30 — Thesis structure priority

**Given your timeline (final deadline June 30, 2026), recommended order of work:**

1. **Finish core experiments:**
   - Subject-wise evaluation (GroupKFold/LOSO).
   - Main adaptation ablations (baseline, AdaBN, TENT, pseudo-labeling +/- self-consistency).
   - Simple latency and monitoring experiments.
   - Class distribution analysis (hand-tapping prevalence).

2. **Write core chapters:**
   - Methods (pipeline, monitoring, adaptation).
   - Results (with clear tables/plots).
   - Discussion and future work.

3. **Then** refine:
   - Introduction and related work.
   - Extras (OOD, advanced flags, etc.).

**Why this order:** Even if time gets tight, you still secure the main scientific content first.

---

### Q31 — (About primary contribution)

See Q32 below.

---

### Q32 — Primary scientific contribution

**Given your actual work and literature landscape, the most defensible core contributions are:**

1. **3-layer label-free monitoring framework** for HAR with empirically calibrated multi-channel thresholds (confidence, temporal consistency, drift).

2. **Practical composition strategy for AdaBN + TENT** that avoids corruption of batch-norm statistics, plus corresponding engineering lessons for test-time adaptation.

3. **Complete MLOps pipeline** (14 stages) as the engineering vehicle that makes contributions 1 and 2 concrete.

**How to frame:**

- Contributions 1 and 2 are the **scientific novelty**.
- The 14-stage pipeline is **engineering context**:
  - "We embed these contributions into a 14-stage MLOps pipeline for continuous monitoring and retraining."

**For prognosis:**

If mentor requires prognosis as co-equal focus:
- Add: "Design and interface specification for HAR → prognosis integration" as a contribution.
- Emphasize: "Complete MLOps infrastructure that supports both HAR and future prognosis models."

---

### Q33 — Freezing the code

**Recommendation:**

- Freeze the code **2-3 weeks before final submission**.
- After all experiments are done.
- Before you start writing detailed code discussion in thesis.

**How:**

```bash
git commit -m "FREEZE: Code for thesis submission"
git tag thesis-final-v1.0
```

Use commit-pinned links in thesis:
```
https://github.com/You/Repo/blob/<COMMIT_SHA>/src/train.py#L245
```

**Benefits:**
- Thesis and code always match.
- Reproducible: anyone can checkout exact version you used.
- Professional software engineering practice.

---

### Q34 — Advanced stages and future work

**Recommended approach:**

Treat the following as **future work / optional evaluation** unless your mentor strongly pushes otherwise:

- Wasserstein drift (Stage 12) as a complementary advanced drift detector.
- Curriculum pseudo-labeling (Stage 13) beyond your core self-consistency ablation.
- OOD detection evaluation and sensor placement robustness analysis.

**In Chapter 6 (Future Work), explain:**

For each of these:
- How it fits into the overall architecture.
- How it would be evaluated in a larger-scale or multi-site follow-up study.
- Why it's beyond the scope of this master's thesis.

---

## Summary: Key Recommendations

### Core "Must-Do" Items

1. **Subject-wise evaluation** on labeled data (GroupKFold or LOSO)
2. **Adaptation ablations**: baseline, AdaBN, TENT, pseudo-labeling (with/without filter)
3. **One full ML lifecycle run** with logs (train → register → promote)
4. **Simple latency measurement** with hardware specs
5. **Threshold calibration experiments** (including synthetic drift)
6. **Class distribution analysis** (hand-tapping prevalence, rare class handling)

### Acceptable "Design-Level" Items

1. **Prometheus/Grafana**: metrics defined, dashboards designed, not fully deployed
2. **Automatic retraining**: design described, manual trigger implemented
3. **Prognosis model**: interface designed, placeholder implemented, full model as future work
4. **DANN/MMD**: discussed in related work and future work, not implemented
5. **Advanced drift methods**: Wasserstein, OOD, curriculum pseudo-labeling as future work

### Main Contributions to Emphasize

1. 3-layer monitoring framework with multi-channel threshold calibration
2. AdaBN + TENT composition fix and engineering guidelines
3. Complete 14-stage MLOps pipeline (engineering context)
4. (If required) Prognosis model integration design

### Timeline Strategy

- **By early May**: All core experiments complete
- **May-June**: Thesis writing (Methods, Results, Discussion first)
- **Late June**: Code freeze, final proofreading
- **June 30**: Submission deadline

---

## References

[^psi]: PSI thresholds of 0.10/0.25 are widely used in credit risk monitoring, but recent work (e.g., Journal of Risk Model Validation) notes they are not statistically 'magic' constants and should be adapted to specific contexts.

[^loso]: See scikit-learn's `GroupKFold`/`LeaveOneGroupOut` documentation and wearable HAR papers (e.g., Ordóñez & Roggen, 2016; Reiss & Stricker, 2012) that use LOSO evaluation as best practice.

[^adabn]: Li et al., "Revisiting Batch Normalization for Practical Domain Adaptation," arXiv:1603.04779, 2016.

[^tent]: Wang et al., "Tent: Fully Test-Time Adaptation by Entropy Minimization," ICLR 2021 (arXiv:2006.10726).

[^dann]: Ganin et al., "Domain-Adversarial Training of Neural Networks," Journal of Machine Learning Research, 2016.

[^mmd]: Gretton et al., "A Kernel Two-Sample Test," Journal of Machine Learning Research, 2012.

---

*End of working notes — update as your mentor responds. These answers are starting points based on research best practices and your current progress.*


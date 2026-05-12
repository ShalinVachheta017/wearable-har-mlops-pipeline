# Defense Slides - First Draft Outline

> **Format:** 15-18 slides. Blue visual palette. One key message per slide. Minimal text.
> **Target runtime:** 20-25 minutes spoken + 10 minutes Q&A.
> **Structure:** Problem -> Domain -> Architecture -> Model -> Contract -> Monitoring -> Evidence -> Limits -> Conclusion

---

## Slide 1 - Title

**Key message:** State the thesis in one breath.

**Visual:** Clean blue background, no figure. University logo top-right.

**Text on slide:**
```
Offline-First, Scalable, and Monitored MLOps Pipeline
for Wearable Human Activity Recognition

[Your name]
Master's Thesis Defense - [Date]
[University / Supervisor]
```

**Verbal:**
> "This thesis is about what happens after a wearable HAR model is trained. Not the model itself - the lifecycle around it: how you run it reliably, how you detect when something is wrong, and how you decide whether to change anything."

---

## Slide 2 - The Gap: What HAR Papers Skip

**Key message:** Published HAR papers stop at offline accuracy. This thesis starts there.

**Visual:** Simple two-column split. Left: "Standard HAR paper" (train -> evaluate -> report accuracy). Right: "This thesis" (the same plus a lifecycle arrow continuing past accuracy into operate -> monitor -> govern -> decide).

**Text on slide:**
```
Standard wearable HAR paper:
  Train -> Evaluate -> Report accuracy

This thesis:
  Train -> Execute -> Monitor -> Govern -> Decide
  (offline-first, single-machine, reproducible)
```

**Verbal:**
> "Most wearable HAR papers train a model, measure accuracy on a held-out test, and publish. That's necessary. But when the same model runs on data from a different user, with slightly different preprocessing, or months later - how does it behave? Who decides whether to retrain? That is the question this thesis addresses."

---

## Slide 3 - Application Domain: Why Repetitive Wrist Behaviors?

**Key message:** Anxiety-relevant repetitive behaviors can be studied as wrist-IMU activity patterns without claiming clinical diagnosis or clinical taxonomy.

**Visual:** One wrist-sensor image (or icon) left. Right: a simple list of 6 behaviors in blue bullet points. Bottom: one anchor sentence in a bordered box.

**Text on slide:**
```
Repetitive hand- and wrist-centered behaviors:
  hand tapping - hand scratching - nail biting
  hair pulling - skin picking - hand rubbing

Expressed as short, repeated wrist movements
-> observable from accelerometer + gyroscope

"This thesis does not diagnose mental health conditions.
 It treats these as observable behavioral proxies."
```

**Verbal:**
> "The application domain is repetitive hand- and wrist-centered behavior relevant to anxiety or distress contexts. A wrist-worn IMU can observe these movement patterns passively, without a clinician present, without recall bias. This thesis does not claim a clinical diagnostic system or a clinical taxonomy. It treats these behaviors as an engineering target that motivates building a governed pipeline."

---

## Slide 4 - Thesis Claim (One Sentence)

**Key message:** The contribution is lifecycle engineering, not a new model.

**Visual:** Full-slide single statement in large text, blue accent on key terms. Consider using `fig_03_scope_map.png` as a background watermark at 20% opacity.

**Text on slide:**
```
The contribution is not a new classifier.

It is a reproducible, monitored, and governed
offline-first MLOps lifecycle for wearable HAR -

using a governed 7-stage operational path
and a 3-stage gated mutation path.
```

**Verbal:**
> "Here is the claim. Not: I built the most accurate HAR model. Not: I built a clinical system. The claim is: the lifecycle can be designed so that preprocessing decisions are traceable, monitoring signals are multi-dimensional, and retraining is a deliberate act - not an automatic reflex."

---

## Slide 5 - Architecture: Two Paths

**Key message:** Stage 1-7 observes. Stage 8-10 mutates. They are explicitly separated.

**Visual:** `fig_05_core_vs_conditional_pipeline.png` (the swim-lane figure). Full width.

**Text on slide:**
```
Stage 1-7    Operational assessment path
             (observe, infer, evaluate, monitor, govern)

Stage 8-10   Governed mutation path
             (retrain, register, promote baseline)
             - activated by explicit flag only -

Stage 11     Calibration (optional future extension)
```

**Verbal:**
> "The architecture has two linked but distinct flows. The blue band - Stages 1 to 7 - runs every session. It ingests data, validates the preprocessing contract, runs inference, evaluates, monitors, and makes a governance decision. The orange band - Stages 8 to 10 - only runs when explicitly activated. Retraining changes operational state, so it must be gated. That separation is not cosmetic. It is the core governance design."

---

## Slide 6 - What "Scalable" Actually Means

**Key message:** Scalable does not mean cloud-scale. It means modular, reproducible, configurable, artifact-tracked, and extendable without redesign.

**Visual:** Two-column split. Left: x "Not this" - cloud diagram or cloud icon. Right: OK "This" - five bullet points. Use a blue accent box for the anchor sentence.

**Text on slide:**
```
x  Cloud-scale deployment
x  Multi-tenant streaming
x  Automated continuous retraining

OK  Each stage is independently replaceable
OK  YAML config layer - no code edits for thresholds
OK  All artifacts run-scoped and versioned
OK  Mutation stages activated by flag, not by default
OK  Stage 8-10 extensible without redesigning Stage 1-7
```

**Verbal:**
> "The word 'scalable' in the thesis title does not mean cloud infrastructure. It means the pipeline can absorb a new model checkpoint, a changed dataset, or an updated threshold without dismantling and rebuilding. Each stage has one responsibility, one component file. The configuration layer controls behavior without touching code. That is what scalable means here."

---

## Slide 7 - Data and Model A Contract

**Key message:** Model A is the defended proof-of-concept runtime candidate. Its contract is fully persisted and verified.

**Visual:** A simple three-row comparison table (Model A / B / C) with a green highlight on Model A row. Or use a clean contract-box diagram showing the artifact chain: `model.keras` -> `scaler.json` -> `model_contract.json` -> `label_order.json`.

**Text on slide:**
```
Training data:   Garmin Venu 3, all_users training split, 11 classes
                 (ADAMSense behavioral taxonomy)
                 User 7 excluded from training, scaler fit, and model selection;
                 used only for external evaluation after freeze

Model A:         87,083 params - 1D-CNN + BiLSTM
                 Row-wise time-major - (batch, 200, 6)
                 Garmin train-only scaler (persisted + verified)
                 SHA-256 label order fingerprint persisted and checked

Status:          Proof-of-concept runtime candidate
                 Not: production-grade, not: clinical device
```

**Verbal:**
> "Model A is the defended runtime candidate. 87,000 parameters. The scaler is fitted only on Garmin training data - not on the external evaluation set. That scaler is persisted in two redundant forms and verified to agree to 0.0 absolute difference at evaluation time. The label order of 11 classes has a persisted SHA-256 fingerprint. Every parameter that matters is frozen and checked. That is what a runtime contract means."

---

## Slide 8 - ABC Comparison: Three Models, One Lesson

**Key message:** Same tensor shape, different contracts - wildly different behavior. Internal accuracy is not a deployment claim.

**Visual:** `fig_ch7_abc_comparison.png` (grouped bars - accuracy left, mean confidence right). Full width.

**Text on slide:**
```
Model A   reproducible contract, modest but honest
Model B   strong native diagnostic, not fixed runtime contract
Model C   same checkpoint, wrong contract -> collapse

(See figure for numbers)
```

**Verbal:**
> "Three models, all with the same nominal input shape - batch by 200 by 6. Completely different behavior. Model A is the honest candidate: modest external accuracy, reproducible, all 11 classes used. Model B uses a non-persisted scaler recomputed from the full evaluation dataframe, so its native diagnostic result is not a fixed reproducible runtime contract - that is why the 47-point internal-to-external gap exists. Model C is the contract-mismatch lesson: the same checkpoint as B, but run without its scaler, collapses to 7.6 percent and uses only 4 of 11 classes. Same shape is not enough. The contract matters."

---

## Slide 9 - Monitoring: Three Signals, One Governance Decision

**Key message:** No single signal decides. Three groups are assessed independently, then voted on.

**Visual:** `fig_ch6_monitoring_governance.png` (S5->S6 three groups->S7 governance gate). Full width.

**Text on slide:**
```
Stage 5   Session metrics computed

Stage 6   Three signal groups rated independently:
          1) Confidence + uncertainty  (HEALTHY / WARNING / CRITICAL)
          2) Temporal transitions      (HEALTHY / WARNING / CRITICAL)
          3) Distribution drift        (HEALTHY / WARNING / CRITICAL)

Stage 7   Two-of-three voting + collapse guard + cooldown
          -> Governance action: NO_ACTION / REVIEW / RETRAIN
          -> auto_retrain field (always false in defended runs)

CRITICAL = severity.   REVIEW = governance action.   (Different fields.)
```

**Verbal:**
> "Stage 6 computes three independent monitoring assessments: one on confidence and uncertainty, one on prediction stability over time, one on distribution drift. Each gets its own rating. Stage 7 combines them with a two-of-three voting rule, a collapse guard that catches single-class dominance, and a cooldown gate. The output is a governance action - not a severity label. CRITICAL is a severity rating. REVIEW is the action. They are two separate fields. On both defended evidence runs, CRITICAL signals fired, and the action was REVIEW, not RETRAIN."

---

## Slide 10 - Trigger Policy: Why Two-of-Three Voting?

**Key message:** Single-signal triggering has a 13.9% false alarm rate. Two-of-three voting reduces it to 0.7% with no loss of episode recall.

**Visual:** `fig_08_trigger_policy_comparison.png` (bar chart across 5 policies x 4 metrics). Full width.

**Text on slide:**
```
Policy              Precision   FAR     Episode recall
single_signal       0.84        13.9%   100%
two_of_three        0.99        0.7%    100%   <- defended
+ cooldown 24h      1.00        0.0%     87.5%  (misses 2/16)

-> Two-of-three: full recall, 20x fewer false alarms than single-signal.
-> 24h cooldown: zero false alarms but misses 2 episodes.
-> Governance trade-off is explicit and documented.
```

**Verbal:**
> "The trigger policy comparison replays 16 monitored episodes. Single-signal triggering fires too easily - 1 in 7 alerts is spurious, a false alarm rate of nearly 14 percent. The two-of-three policy requires two of the three signal groups to be in a concerning state before firing. That gives precision of 0.99 and a false alarm rate under 1 percent while still catching every genuine episode. The 24-hour cooldown eliminates false alarms entirely but misses 2 episodes. The trade-off is documented. Two-of-three without cooldown is the defended choice."

---

## Slide 11 - Preprocessing Sensitivity: Gravity Removal Made It Worse

**Key message:** Intuitively reasonable signal cleaning worsened collapse. Train-serve parity is empirically real, not theoretical.

**Visual:** `fig_07_ablation_config_comparison.png` (four config bars). Or a simple two-metric table with color coding: A=yellow, B=green, C=red, D=darkgreen.

**Text on slide:**
```
Config    Unique classes   Hand-tapping share
A  baseline      7.08          78.4%
B  +calibration  7.88          73.2%
C  +gravity      5.32  lower diversity  96.7%  higher dominance  <- worse
D  +both         9.72  higher diversity 50.1%  lower dominance   <- best

Gravity removal alone worsened collapse.
-> Preprocessing is part of the model contract.
-> "Intuitively reasonable" != "operationally safe."
```

**Verbal:**
> "We ran 25 session pairs under four preprocessing configurations, holding the model constant. Gravity removal alone - configuration C - made class collapse dramatically worse: only 5 classes predicted on average, and 97 percent of predictions concentrated on hand-tapping. Adding calibration on top recovered diversity. The lesson is that preprocessing is not neutral preamble - it is part of the operational contract. Changing it at inference time without retraining is the exact train-serve mismatch the thesis is built around."

---

## Slide 12 - Model Choice Drives Collapse: Same Input, Different Behavior

**Key message:** The old model's hand-tapping dominance was reproduced on a controlled rerun - it is a model property, not an input property.

**Visual:** `fig_10_old_vs_new_model_comparison.png` (three bars: old model / new model / old model rerun). Full width.

**Text on slide:**
```
Same unlabeled raw session pair used for all three runs.

Old model (pseudo-label fine-tuned):
  Top-class share 85.6% - 9/11 classes - conf 0.876

New retrained model:
  Top-class share 29.0% - 11/11 classes - conf 0.790

Old model control rerun (same input):
  Top-class share 85.6% - 9/11 classes - conf 0.876  <- reproduced

-> Collapse is a model property, not an input property.
-> This motivates the collapse guard in Stage 7.
```

**Verbal:**
> "We ran the same raw sensor file through the old model, the new retrained model, and the old model a second time as a control. The old model reproduced the same collapse pattern exactly - 85 percent hand-tapping, 9 classes, both times. The new model used all 11 classes with 29 percent dominance. The input was identical. The collapse was model-specific. That is why Stage 7 includes a collapse guard: a model that collapses with high confidence is not detectable by confidence thresholds alone."

---

## Slide 13 - Negative Result: Routing Change != Quality Improvement

**Key message:** A plausible intervention bundle changed routing behavior but left mean confidence unchanged at 0.8578. Routing changes must not be reported as quality improvements.

**Visual:** Clean two-column before/after table (no scatter plots - the table makes the point more cleanly).

**Text on slide:**
```
26-session before/after experiment
(unit-fix + abstain-to-review intervention)

                    Before    After
Mean confidence     0.8578    0.8578  <- unchanged
Mean dominant share  81.2%    67.3%   <- appears better
Mean review share     0.0%    66.1%   <- explains the drop

-> Lower dominance = windows routed to REVIEW, not better classification.
-> The quality signal did not move.
-> This is a deliberate negative result.
```

**Verbal:**
> "One of the most academically important results in this thesis is a negative one. We applied a plausible bundle of interventions - unit detection, stream-reuse guarding, abstain-on-low-confidence routing - to 26 sessions. Dominant-class share dropped from 81 to 67 percent, which looks like an improvement. But mean confidence was unchanged at 0.8578 before and after. The apparent improvement was entirely explained by routing windows into REVIEW. The underlying quality signal did not move. This is the empirical argument for why governance must track quality signals, not routing distributions."

---

## Slide 14 - User 7 Evidence Run: The Honest External Ceiling

**Key message:** 37.6% external accuracy + REVIEW routing + auto\_retrain=false is the correct behavior of a governed system on an uncertain labeled external run.

**Visual:** A split layout. Left: a simple metrics summary box (Model A / User 7 numbers). Right: a governance flow arrow showing monitoring -> CRITICAL -> Stage 7 -> REVIEW / auto\_retrain=false.

**Text on slide:**
```
User 7 external evaluation (989 windows)
  Accuracy       37.6%   Macro F1  34.1%
  Mean confidence 0.359   Uncertain rate 80.5%
  Classes used    11/11

Garmin unlabeled run (1,304 windows)
  Mean confidence 0.393   Drift status: HEALTHY
  Trigger action  REVIEW   auto_retrain: false

-> Both runs: Stage 1-7 completed. Status SUCCESS.
-> Risk flagged. Routed to human review. No mutation.
-> This is the correct output of a governed pipeline.
```

**Verbal:**
> "The two defended evidence runs. User 7: an external participant not in the training set. 37 percent accuracy - low, honest, expected for cross-user transfer. Mean confidence 0.36. The monitoring layer correctly identified low confidence and high uncertainty, while drift and temporal status remained healthy. Stage 7 routed the run to REVIEW, not retraining. The Garmin unlabeled run: 1,304 windows of real wrist sensor data, no labels. Drift status HEALTHY, but confidence low enough to trigger REVIEW. Both runs: auto\_retrain=false. That is not a missing feature. That is the governance policy working as designed."

---

## Slide 15 - What the Pipeline Does NOT Claim

**Key message:** Scope limits are explicit non-claims, not hidden gaps.

**Visual:** A clean table or bulleted list, each item starting with "x Not claimed:". Use subdued text (lighter blue or grey) to signal these are boundaries, not failures.

**Text on slide:**
```
x  Clinical diagnosis or population-level generalisation
x  Model A is production-grade or deployable
x  Subject-independent generalization
x  Confidence calibration solved (mean conf 0.359 on User 7)
x  Auto-retraining as a live feature
x  CRITICAL monitoring severity means automatic retraining
x  Stages 8-10/11 are live automatic runtime features

OK  Reproducible offline-first lifecycle
OK  Honest external accuracy ceiling reported
OK  Risk observable without ground-truth labels
OK  Retraining gated by policy, not automatic
```

**Verbal:**
> "These are the explicit non-claims. They are not weaknesses the examiner found. They are scope boundaries the thesis documents. A system that reports its limitations clearly is a stronger contribution than one that overstates. The positive side: the lifecycle is reproducible, the external ceiling is honestly reported, risk is detectable without labels, and retraining is gated by an auditable policy."

---

## Slide 16 - Research Questions: Bounded Answers

**Key message:** All four RQs are answered - each with explicit bounds.

**Visual:** A four-row table. Each row: RQ | One-line answer | Supported / Partial / Not claimed.

**Text on slide:**
```
RQ1  Can the pipeline detect risk without labels?
     -> Yes, partially. Monitoring signals respond directionally.
       (Not: recover label-level accuracy)

RQ2  How strongly do preprocessing decisions affect behavior?
     -> Strongly and non-monotonically.
       (Gravity removal alone worsened collapse)

RQ3  Can governed trigger policy improve safety?
     -> Yes. Two-of-three: precision 0.99, FAR 0.7%.
       (Bounded to one replay set and one threshold family)

RQ4  How much collapse is from model choice vs input?
     -> Materially from model choice.
       (Controlled rerun reproduced old-model collapse)
```

**Verbal:**
> "Four bounded answers. Partial on RQ1 - the signals move in the right direction but they are proxies, not ground truth. Strong on RQ2 - preprocessing matters more than expected, and in a non-obvious direction. Strong on RQ3 - the voting policy is a clear improvement over single-signal. Clear on RQ4 - the controlled rerun shows the collapse is model-specific. Each answer is tied to archived run artifacts. None of them is a claim beyond the available evidence."

---

## Slide 17 - Contribution Statement

**Key message:** The contribution is one sentence. Say it out loud.

**Visual:** Full-slide statement in large text. Blue background with white or light-blue text. Bold key terms.

**Text on slide:**
```
A reproducible, auditable, and governance-aware
offline-first MLOps lifecycle for wearable HAR -

with Model A as the frozen proof-of-concept runtime candidate,
Model B and C retained as diagnostic and contract-mismatch evidence,
and a review-first trigger policy in which

CRITICAL severity routes to human review,
not to automatic retraining.
```

**Verbal:**
> "That is the contribution. Not a new architecture. Not a clinical tool. A lifecycle in which the distinctions that matter - between observation and mutation, between monitoring severity and governance action, between internal accuracy and deployment transferability - are all observable from archived artifacts. The pipeline is not broken. It executes end-to-end, detects uncertainty, and routes risk to review. The remaining limitation is model confidence and external generalisation. Those limitations are documented, not hidden."

---

## Slide 18 - Closing View + Questions

**Key message:** Thank the committee and open Q&A.

**Visual:** Reuse `fig_05_core_vs_conditional_pipeline.png` (swim-lane) as background at low opacity, or `fig_03_scope_map.png` (scope boundary). Text centered on top.

**Text on slide:**
```
Thank you.

Offline-first - Reproducible - Governed
MLOps Level 1 - by design, not by limitation

Questions?
```

**Verbal:**
> "Thank you. The system is not Level 2 MLOps because Level 2 is not safe here - unlabeled data, label-scarce monitoring, health-adjacent context. Level 1 with explicit governance is the correct target. I am happy to go into any of the model decision, monitoring signals, trigger policy, or preprocessing ablation in more detail."

---

## Figure Map - Which Figure Goes Where

| Slide | Figure | Path |
| --- | --- | --- |
| 5 | Pipeline swim-lane | `thesis/figures/thesis_journey/fig_05_core_vs_conditional_pipeline.png` |
| 8 | ABC comparison | `thesis/figures/thesis_journey/fig_ch7_abc_comparison.png` |
| 9 | Monitoring governance flow | `thesis/figures/thesis_journey/fig_ch6_monitoring_governance.png` |
| 10 | Trigger policy comparison | `thesis/figures/thesis_journey/fig_08_trigger_policy_comparison.png` |
| 11 | Preprocessing ablation | `thesis/figures/thesis_journey/fig_07_ablation_config_comparison.png` |
| 12 | Old vs new model | `thesis/figures/thesis_journey/fig_10_old_vs_new_model_comparison.png` |
| 13 | Before/after table (no figure - table only) | - |
| 4/18 | Scope map (optional background) | `thesis/figures/thesis_journey/fig_03_scope_map.png` |

---

## Speaker Timing Guide

| Slides | Block | Target time |
| --- | --- | --- |
| 1-4 | Problem + claim | 3-4 min |
| 5-6 | Architecture | 2-3 min |
| 7-8 | Model decision | 3-4 min |
| 9-10 | Monitoring + trigger | 3-4 min |
| 11-13 | Evidence experiments | 3-4 min |
| 14 | Defended evidence runs | 1-2 min |
| 15-17 | Limits + contribution | 2-3 min |
| 18 | Close | 30 sec |
| **Total** | | **18-22 min** |

---

## After Slides: Demo Runbook

When slides are done, create `internal/writing/demo_runbook.md` with:
- Exact commands to run the two defended evidence runs (Garmin + User 7)
- What the examiner will see on screen
- What to say while it runs
- How to handle common failure modes (missing file, slow execution)
- Where the output artifacts are and how to read them

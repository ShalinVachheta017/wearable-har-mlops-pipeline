# Ruthless Examiner Review — main.pdf (compiled 5 June 2026, 106 pages)
**Thesis:** "Developing an MLOps Pipeline for Continuous Mental Health Monitoring Using Wearable Sensor Data"
**Reviewed against:** strict PhD-committee standard, per your review prompt.
**Verification basis:** full text extraction, visual inspection of title page, declaration, Figures 4.1, 7.1, 7.3, 7.5, and the Section 6.2 math page; independent recomputation of all headline numbers.

**One-line verdict up front:** This is now a genuinely strong, honest, defensible engineering thesis — far stronger than earlier drafts. The 93.6% → 44.4% → 37.0% arc, reported without inflation, is its best feature. But it has **one structural evidence gap (RQ2 / the missing preprocessing ablation), two internal contradictions, one broken figure, and one unexplained name ("D1")** that a competent examiner will find within twenty minutes. All are fixable in days, not weeks. Fix list and scores at the end.

---

## Section: Front Matter (Title page, Abstract, Zusammenfassung, Eidesstattliche Erklärung, Lists)

### Overall Verdict
**Acceptable–Strong.** All previously missing elements are now present and render correctly. The title remains the single largest defense liability, but the body now manages it about as well as a fixed title can be managed.

### Main Problems
1. **Title–scope tension persists by necessity.** Title promises "Continuous Mental Health Monitoring"; Abstract immediately retreats to "behavioral-proxy recognition in a mental-health-adjacent monitoring context… not a diagnostic or prognosis model." The body's mitigation (§1.1, §2.1, §3.6 "In line with the fixed thesis title…") is the correct strategy *if the title is administratively locked*. If it is not locked, change it. If it is locked, the first defense question is predictable — script the answer (see Defense Danger Zone).
2. **Zusammenfassung German error:** "bei einer **Darstellung** von 50 Hz" is wrong — *Darstellung* means representation/depiction. It must be "bei einer **Abtastrate** von 50 Hz" (sampling rate). This is on page II; the German examiner reads this page.
3. "Haareziehen" is colloquial; "Haarezupfen" or "Ziehen an den Haaren" is more standard. Minor.

### Line-by-Line Review (selected)
| Location | Original text | Problem | Risk | Suggested fix |
|---|---|---|---|---|
| Title page | "Continuous Mental Health Monitoring" | Promises what the body explicitly disclaims | **Critical (defense)** | If changeable: "…for Wearable Behavioral Monitoring in a Mental-Health Context". If fixed: keep current in-text mitigation, prepare scripted answer |
| Zusammenfassung | "bei einer Darstellung von 50 Hz" | Wrong word (Darstellung ≠ sampling rate) | Medium | "bei einer Abtastrate von 50 Hz" |
| Zusammenfassung | "Haareziehen" | Colloquial register | Low | "Haarezupfen" |
| Abstract | "The thesis shows that reliable wearable monitoring requires more than model accuracy" | Fine, but "shows" is strong for a single-pipeline case study | Low | "argues and demonstrates on one pipeline that…" (optional) |

### Visual/Rendering Check
- Title page: the previously flagged ligature failure is **fixed** — "fulfillment" renders with a correct fi-ligature; no missing glyphs. ✔
- Eidesstattliche Erklärung: signature line present, German + English, umlauts correct. ✔ **Remember to physically sign before submission.**
- Verify whether the Chair of Embedded Systems template requires the University of Siegen logo on the cover — current cover has none.

### AI-Writing Risk
Low. Abstract is specific and number-anchored.

### Citation/Plagiarism Risk
Low. Declaration is standard boilerplate (expected).

---

## Section: Chapter 1 — Introduction

### Overall Verdict
**Strong.** The motivation→problem→RQ→contribution chain is clean, the scope boundary is explicit, and the diagnostic-disclaimer strategy is consistent. Two real defects: RQ2 is malformed as a question, and §1.6 makes a promise Chapter 7 does not keep.

### Main Problems
1. **§1.6 promises evidence that does not exist in the document.** "Chapter 7 reports the experimental evidence, including **preprocessing sensitivity**, trigger-policy evaluation, model-contract diagnostics, **and negative results**." Chapter 7 contains **no preprocessing-sensitivity table, no config comparison, and no explicitly labeled negative result**. (Full analysis under Chapter 7.) Either Chapter 7 gains that content or this sentence must be rewritten. As it stands, an examiner can quote §1.6 and ask you to point to the table. You cannot.
2. **RQ2 is a "How" question; Table 8.1 answers it "Strongly yes."** "How do preprocessing and train–serve contract choices affect recognition behavior…?" cannot be answered yes/no — a category error visible to any reviewer. Either reword RQ2 ("**Do** preprocessing and train–serve contract choices **materially** affect recognition behavior…?") or rewrite the Table 8.1 answer as a description of the *how*.
3. The five objectives and four RQs map imperfectly (five→four with objective 5 absorbed into RQ framing) — acceptable, but be ready to state which objective maps to which RQ.

### Line-by-Line Review (selected)
| Location | Original text | Problem | Risk | Suggested fix |
|---|---|---|---|---|
| §1.3 RQ2 | "How do preprocessing and train–serve contract choices affect…" | Form mismatch with the yes/no answer given in §8.1 | **High** | Reword to "To what extent do…/Do…materially affect…" *or* fix the answer in Table 8.1 |
| §1.6 | "including preprocessing sensitivity… and negative results" | Promised content absent from Ch. 7 | **Critical** | Add the ablation evidence to Ch. 7 (preferred — the data exists per Appendix C) or delete/soften this clause |
| §1.1 | "Wrist-worn consumer devices are particularly relevant because they are unobtrusive and already widely used." | Uncited prevalence claim | Low | Optional market/penetration citation; or leave as common knowledge |
| §1.2 | "These factors are not minor details. They define the numerical and temporal contract…" | Good — keep. This sentence earns its keep | — | — |
| §1.4, Contribution 3 | "can materially change deployment-style model behavior" | The word "evaluates" earlier in the item implies quantitative evidence in Ch. 7 that is currently not shown | High | Same root cause as §1.6 — resolve via the ablation fix |

### AI-Writing Risk
**Low–Medium.** The chapter is specific, but the antithesis tic begins here ("The contribution of this thesis is therefore X, not Y") and recurs through the whole document. Individually fine; cumulatively a fingerprint. See global note in the final summary.

### Citation/Plagiarism Risk
Low. Claims are cited; [3–18] coverage is appropriate.

### Defense Risk
**Possible examiner question:** "Your Section 1.6 says Chapter 7 reports preprocessing sensitivity and negative results. Show me the table."
**Why this is risky:** It is currently unanswerable from the document.
**How to fix:** Add §7.x "Contract-Sensitivity Ablation" with the config comparison (see Chapter 7 review), or rewrite §1.6.

---

## Section: Chapter 2 — Background and Related Work

### Overall Verdict
**Strong.** Seven well-bounded sections, each ending by tying back to the thesis problem; Table 2.2 (gap synthesis) is exactly what examiners want. The chapter's weakness is repetition — both internal and against Chapters 1/3.

### Main Problems
1. **Verbatim self-duplication.** "Monitoring in this thesis is therefore not treated as a dashboard add-on. It is part of the runtime control logic" (§2.6) reappears nearly word-for-word as the Chapter 6 opener ("Monitoring here is therefore not a dashboard add-on; it is part of the runtime control logic"). Twice is once too many for an examiner reading linearly.
2. **The offline-first definition appears three times near-verbatim** (§1.5, §2.5, §3.6: "offline-first means that the complete pipeline can be executed and inspected on a local machine using versioned code, configuration files, model artifacts…"). Define once, cross-reference twice.
3. §2.6 and §6.1/6.2 substantially overlap (confidence limits, drift, collapse). Background-vs-design separation is defensible, but trim §2.6 by ~20% and point forward.
4. The no-diagnosis disclaimer appears 10+ times across the thesis (Abstract, §1.1×2, §1.3, §1.4, §2.1, §2.2 ×3, §3.6, §4.4, §8.3). Strategic repetition given the title — but at this frequency it starts reading as anxiety rather than discipline. Keep ~6 strongest instances; cut the rest.

### Line-by-Line Review (selected)
| Location | Original text | Problem | Risk | Suggested fix |
|---|---|---|---|---|
| §2.1 | "A smartwatch cannot infer anxiety, depression, or distress simply from motion signals without clinical context and validation." | Good, but an unsourced negative universal | Low | Add "cf. [3, 6]" or soften to "should not be assumed to infer" |
| §2.2 | "A behavioral proxy is an externally observable action that serves as an indirect, measurable stand-in…" | Same definition already given verbatim in §1.1 parenthetical | Medium | Define once (here, in Background), drop the §1.1 parenthetical or shorten it |
| §2.3 | "…has become the dominant approach in recent sensor-based HAR [29, 30]" | Fine; "dominant" is supported by the survey citations | Low | — |
| §2.5 | "This is a form of hidden technical debt… [42]" | Correct use of Sculley et al. | — | Keep |
| §2.6 | "Monitoring in this thesis is therefore not treated as a dashboard add-on…" | Duplicated at Ch. 6 opening | Medium | Keep the Ch. 6 instance; delete or rephrase here |
| §2.4 | "Concretely, under LOUO every window belonging to the held-out wearer is removed from training…" | Excellent didactic paragraph — one of the best in the chapter | — | Keep |

### AI-Writing Risk
**Medium in §2.3 and §2.5.** The CNN/LSTM exposition and the MLOps-definition passages read like polished survey paraphrase — competent, cited, but generic in cadence ("Hybrid CNN–LSTM architectures combine these strengths. The convolutional part extracts…, while the recurrent part models…"). Not a misconduct risk (sources are cited); a style risk. Rewrite 2–3 of the most textbook-sounding sentences with project anchors, e.g.:
> *Instead of:* "Hybrid CNN–LSTM architectures combine these strengths."
> *Write:* "Model D1 inherits both properties: its convolutional front end captures the 0.2–0.5 s motion motifs of tapping and rubbing, while the BiLSTM models how those motifs repeat across the four-second window."

### Citation/Plagiarism Risk
**Low.** Figures 2.2 ("Adapted from Wang et al. [1]") and 2.5/2.6 ("Redrawn for this thesis after Hewage and Meedeniya") are properly attributed — redrawing is the right call. Definitions are cited. No uncited "state-of-the-art/robust/widely used" claims found that need sourcing beyond what's given.

### Defense Risk
**Possible examiner question:** "Your gap statement says these strands are 'often treated separately' — name one work that comes closest to combining them, and say precisely what it lacks."
**How to prepare:** Pick one row of Table 2.2 (e.g., Bodor et al. [61] for MLOps monitoring) and rehearse a two-sentence differentiation.

---

## Section: Chapter 3 — Offline-First MLOps System Architecture

### Overall Verdict
**Strong**, with **one Critical internal inconsistency** that is maximally embarrassing given the chapter's own thesis.

### Main Problems
1. **CRITICAL — Figure 3.2 names the runtime contract folder `model_d1_final_20260526/`; Chapter 5 (§5.4), Appendix B, and Appendix C all say `model_d1_final_20260528/`.** A two-day mismatch in the very artifact that demonstrates the "same-folder invariant." An examiner who notices will enjoy this far too much: *"Your thesis argues that silent artifact mismatch is the central failure mode — and your own Figure 3.2 points to a different contract folder than your implementation chapter."* Fix the figure. Then grep the LaTeX source for both strings to be sure.
2. Stage S11 (Calibration) floats awkwardly: it appears in Figure 3.1 and Table 3.2 as "optional," then effectively vanishes until Future Work. Acceptable, but one sentence in §3.2 saying "S11 was implemented as a stub/branch and not exercised in the defended runs" (whichever is true) closes the loop.
3. Table 3.2's "Mutates model?" column says "Conditional" for S8–S10 — strictly, S8 produces a *candidate* and does not mutate the *active* model; only S10 does. Tighten: S8 "No (produces candidate)", S9 "No (registers candidate)", S10 "Conditional (promotes)". This precision is free marks in a governance-themed thesis.

### Line-by-Line Review (selected)
| Location | Original text | Problem | Risk | Suggested fix |
|---|---|---|---|---|
| Fig. 3.2 | `model_d1_final_20260526/` | Contradicts §5.4 / App. B / App. C (`…20260528/`) | **Critical** | Regenerate figure with the correct folder name |
| §3.4 | "it protects the active runtime from being replaced by a candidate that only improves a narrow diagnostic case" | "diagnostic case" is ambiguous — diagnostic in the debugging sense, but the word collides with the medical-diagnosis disclaimer | Medium | "…that only improves one narrow diagnostic scenario observed during debugging" or "one specific failure case" |
| §3.5 | "The strongest architectural rule in this thesis is that the model is not the deployment unit; the runtime contract is." | Excellent thesis sentence — keep, and reuse verbatim in the defense | — | — |
| Table 3.2 | S8–S10 "Conditional" | Imprecise per stage | Low–Med | Differentiate S8/S9 (No) from S10 (Conditional) |
| §3.6 | Third near-verbatim "offline-first means…" definition | Repetition | Medium | "Offline-first retains the meaning fixed in Section 1.5: …" + one-line reminder |

### Technical Accuracy Check
- Two-path separation (S1–7 vs S8–10) is coherent and consistently enforced in later chapters. ✔
- Table 3.3 fail-fast/override/accept semantics match the §5.4.1 implementation description. ✔
- The "override stale path with same-folder artifact + warning" rule is defensible but debatable — silently *correcting* a misconfiguration is itself a governance choice. Be ready to defend why correct-and-warn beats fail-always (answer: operator intent, warning is logged, fail-fast still guards the truly incompatible case).

### Defense Risk
**Possible examiner question:** "Why does the runtime *correct* a stale path instead of always failing fast? Isn't silent correction exactly the hidden behavior you argue against?"
**How to fix:** Pre-build the answer: the correction is (a) logged as a warning, (b) only applied when an exactly matching same-folder artifact exists, (c) chosen so that a stale config cannot quietly mix two contracts — the dangerous case still fails fast.

---

## Section: Chapter 4 — Data Sources, Preprocessing, and Model Contract

### Overall Verdict
**Strong.** The evidence-role separation (Tables 4.1–4.3) is the methodological backbone of the thesis and is done well. Defects are local: an unexplained model name, a redundant figure, and two wording tensions.

### Main Problems
1. **CRITICAL — "Model D1" is never explained.** §4.4: "Model D1 keeps this general 1D-CNN–BiLSTM structure." The name implies a lineage (A, B, C, D → D1) that the document never mentions. Earlier drafts had Models A/D/D1 and preprocessing configs A–D; the cleanup removed the lineage but kept the label. First question from any attentive reader: *"What were models A through D?"* One sentence fixes it: "The label D1 is a repository-internal version identifier: D denotes the selected preprocessing configuration (calibration plus gravity-aware unit harmonization) among four candidates evaluated during development, and D1 the first promoted runtime built under it." — **and this sentence becomes natural once the ablation evidence is restored in Chapter 7.**
2. **Figure 4.1 duplicates Table 4.4 exactly** (same means/stds as bars). Keep the table; move the figure to Appendix E or delete. Also, the figure's internal title literally renders "train--serve" (double hyphen — matplotlib string, not LaTeX). Fix the string to an en-dash or "train–serve".
3. **"raw channel statistics" vs "after unit normalization."** Table 4.4's caption says values are "after unit normalization"; the paragraph below begins "Even at the level of raw channel statistics…". Both are true (unit-harmonized but unscaled), but the wording collides. Say "unit-harmonized, unscaled channel statistics" once.
4. No data-provenance/ethics line. Users 1–6 presumably come from the supervisor's study [10]; User 7 is the author. One sentence in §4.1 on consent/approval provenance preempts an ethics question that the mental-health framing invites.

### Line-by-Line Review (selected)
| Location | Original text | Problem | Risk | Suggested fix |
|---|---|---|---|---|
| §4.4 | "Model D1 keeps this general 1D-CNN–BiLSTM structure." | Name "D1" unexplained anywhere in 106 pages | **Critical (defense)** | Add naming sentence (above); link to restored ablation |
| §4.1 text below Table 4.4 | "Even at the level of raw channel statistics…" | Contradicts caption "after unit normalization" | Medium | "unit-harmonized, unscaled channel statistics" |
| Fig. 4.1 (rendered) | plot title "train--serve" | Literal double hyphen in rendered figure | Low | Fix matplotlib title string |
| §4.2 | "1 milli-g = 0.00980665 m/s2" | Verified correct (1 g = 9.80665 m/s²) ✔ | — | — |
| §4.3 | "while remaining short enough for low-latency offline inference" | "Low-latency" claimed; no latency number anywhere in the thesis | Medium | Add one measured number (e.g., windows/s on the thesis machine) in Ch. 5 or 7, or drop "low-latency" |
| §4.3 | "Compared with the ADAMSense study, which reported its strongest configuration with longer 12-second windows and a magnitude feature…" | Good, honest differentiation | — | Keep |
| Table 4.3, ADAMSense row | "Exact source-domain window counts are not used as thesis performance evidence in this chapter." | Slightly evasive — just state the count or state why it is unavailable | Low | "Window counts for the source domain depend on the pretraining configuration and are not reproduced here; only row counts are contract-relevant." |

### Technical Accuracy Check (verified by recomputation)
- User 7: 99,017 rows → (99,017 − 200)/100 + 1 = **989 windows** — matches exactly. ✔
- Garmin 1–6: 385,326 rows → 3,755 windows under within-segment construction (< 3,852 continuous upper bound) — plausible. ✔
- Parameter count: 966,347 + 1,152 = 967,499. ✔
- Scaler formula and train-only policy (§4.5) are correct and correctly motivated. ✔

### Defense Risk
**Possible examiner question:** "Your gyroscope stays in deg/s while acceleration is converted to SI. Why not rad/s?"
**How to prepare:** Answer: contract consistency with the training data convention of [9, 10]; the unit is fixed in the contract, conversion would be a contract change. Know this cold — it's a one-line answer that demonstrates the whole thesis mindset.

---

## Section: Chapter 5 — Pipeline Implementation

### Overall Verdict
**Strong.** The architecture→module→artifact mapping (Tables 5.3–5.5) is exactly the auditable style the thesis preaches, and Table 5.1 (technology rationale) preempts "why X?" questions well. Two issues, one of which matters in the defense.

### Main Problems
1. **Headline-results provenance is buried in Appendix C.** Appendix C honestly states the 5-fold and LOUO numbers come from a *notebook* (`Model_D1_Final_Build_Runtime_Contract.ipynb`), not from the pipeline this chapter describes. That honesty is good — but Chapter 5 sells "reproducible from one command," and Chapter 7 never mentions the notebook. An examiner who reads Appendix C will ask: *"Your reproducibility story is the pipeline; your headline numbers come from a notebook. Reconcile."* Add one sentence to §7.1: "The model-building results (five-fold, LOUO) were produced in the version-controlled build notebook that constructs the runtime contract (Appendix C); the pipeline of Chapter 5 consumes that contract for inference, evaluation, monitoring, and governance." This converts a gotcha into a design statement.
2. The §5.2 claim "The implementation choices in this chapter are deliberate rather than incidental; **each one** supports the offline-first, contract-driven goals" — "each one" is an absolute. Harmless, but absolutes invite hunting. "The main implementation choices are deliberate…" is safer.
3. §5.6.2 maturity self-placement at Level 1 is well-bounded and honest. Keep. Be ready to name what *specifically* would be required for Level 2 (automated retraining trigger + validation gate + deployment automation) — Table 5.6 implies it; say it fluently.

### Line-by-Line Review (selected)
| Location | Original text | Problem | Risk | Suggested fix |
|---|---|---|---|---|
| §5.2 | "deliberate rather than incidental; each one supports…" | Absolute claim; also a mildly AI-flavored construction | Low–Med | "The main implementation choices below each map to a goal from Chapters 3–4." |
| §5.4 | `model_d1_final_20260528/` | Correct here — but contradicts Fig. 3.2 | **Critical (cross-ref)** | Fix Figure 3.2 (see Ch. 3) |
| §5.5 | Composition R = S7(S6(…S1(x)…)) | Nice formalization, but S5 (evaluation) only runs when labels exist — the composition as written implies unconditional S5 | Low | Footnote: "S5 is the identity on unlabeled runs" |
| §5.6.1 | "Where richer experiment tracking… MLflow and DVC can record metrics and versions [46, 47], although the reproducibility evidence defended here comes from the local run-scoped artifact trail" | Honest and good — but make sure this matches the repo reality (DVC *is* listed as used in Table 5.1 and Appendix A `dvc pull`) | Medium | Clarify: DVC is used for data/model versioning; MLflow-style *tracking server* is what is not relied upon. Currently the sentence lumps them together and slightly undercuts Table 5.1 |

### Technical Accuracy Check
- Table 5.2 precedence (Python defaults < YAML < CLI < env) is coherent and matches §5.4 description. ✔
- Same-folder invariant enforcement narrative matches Table 3.3 outcomes. ✔
- **Latency/runtime numbers absent** — "low-latency" (§4.3) is never substantiated. One number (e.g., "Stage 3–4 process a 632,700-row session in N s on the reference machine") would close it.

### Defense Risk
**Possible examiner question:** "Run `pytest tests -q` — how many tests, and what exactly do the contract tests assert?"
**How to prepare:** Know the current test count and the 3–4 specific assertions of `test_runtime_contract_consistency.py` by heart.

---

## Section: Chapter 6 — Monitoring and Governance

### Overall Verdict
**Strong on design, with one Critical contradiction and one orphaned mechanism.** The tiered-threshold logic, collapse guard, cooldown semantics, and the formal definitions block are the most technically mature part of the thesis. The math (verified visually) renders correctly and the definitions are correct.

### Main Problems
1. **CRITICAL — Raw vs. scaled drift baseline contradiction.** §6.2: "Drift is computed against the **raw physical monitoring baseline** that belongs to the active runtime contract." Appendix B, Table B.1: `garmin_train_scaled_baseline.json` — "Monitoring baseline **in the scaled feature space**, used as the Stage 6 drift reference." Both cannot be true. Check the code (`post_inference_monitoring.py` + the baseline JSON actually loaded) and align the text. In a thesis whose core claim is "drift is meaningful only in the same feature space as the model input" (§4.5), getting your own feature space ambiguous is the worst possible own goal. *(If both baselines exist and serve different checks, say exactly that — which signal uses which.)*
2. **Orphaned entropy-drift signal.** The Formal Definitions block defines predictive entropy H_i and says "whose session mean the drift monitor compares against the upper percentile of the training-distribution entropy to flag an entropy drift." This entropy-drift mechanism appears **nowhere else**: not in Table 6.1, not in the trigger policy, not in Chapter 7's results. Either it exists in code and deserves a row in Table 6.1, or it doesn't and the sentence must go. Orphans are examiner bait.
3. **The runtime drift statistic compares channel *means* only.** z = max_j |µ̂_j − µ_j| / σ_j is a per-channel mean-shift detector. A session could match all six means while having wildly different variance or spectral content and produce z ≈ 0. The thesis *does* hedge (MMD audit branch, "surface a shift for review rather than characterize it precisely"), but never states the blind spot plainly. Add one clause: "the z-score is blind to variance and higher-moment shift; the MMD audit branch exists precisely to cover that gap offline."
4. Spelling inconsistency: "authoris**e**s" (Table 6.2 caption, 4 occurrences document-wide) vs "authoriz**e**s" (§7.4, 3 occurrences). Pick American (majority) and normalize.
5. Terminology friction: the action named `queue_retrain` is described as "review/label queue" and Figure 7.5 buckets outcomes as review/monitor/none with **no queue_retrain bucket**. If no session ever produced the two-warning pattern, *say so* — it is itself a finding (risk surfaced via critical signals and the collapse guard, not via warning accumulation).

### Line-by-Line Review (selected)
| Location | Original text | Problem | Risk | Suggested fix |
|---|---|---|---|---|
| §6.2 | "Drift is computed against the raw physical monitoring baseline" | Contradicts Appendix B ("scaled feature space… Stage 6 drift reference") | **Critical** | Verify in code; align both passages; if two baselines exist, document which signal consumes which |
| §6.2 Formal defs | entropy-drift sentence | Mechanism absent from Table 6.1, policy, and results | High | Add to Table 6.1 + report in Ch. 7, or delete |
| §6.2 | "using a per-channel z-score statistic" | Underspecifies that only session *means* are compared | Medium | "…a per-channel z-score on session mean statistics; variance and spectral shift are deferred to the MMD audit" |
| Table 6.2 | "Severity never authorises mutation" | UK spelling vs US elsewhere | Low | Normalize to "authorizes" |
| §6.3 | "it is easy to raise a review but impossible to trigger automatic mutation" | "Impossible" is an absolute about your own code | Medium | "by construction, no code path converts severity into mutation without the label/QA gate" — same content, audit-proof phrasing |
| §6.5 | "They are therefore not clinical limits, not statistical guarantees, and not validated wearable-HAR constants." | Excellent honest hedge — keep verbatim | — | — |

### Technical Accuracy Check (verified)
- Mean confidence, U, T, D formulas: correct (T uses 1/(N−1), sum from i=2 ✔).
- ECE formula: correct.
- MMD²: biased V-statistic form (includes i=i′ diagonal). Fine and standard as written with [52]; if pushed, know that the unbiased U-statistic excludes the diagonal with 1/(n(n−1)).
- Voting policy (collapse → review; c≥1 → review; w≥2 → queue_retrain; w=1 → monitor; cooldown last) is internally consistent with Table 6.2 and Figure 6.2. ✔
- **Threshold provenance is the soft spot:** "chosen against this repository's training distribution and a bounded set of curated sessions." If any of those curated sessions are among the 25 evaluated in §7.4, the monitoring evaluation is partially circular. You must be able to answer this with a clean yes/no. If the answer is "some overlap," disclose it in §7.4 *before* the examiner finds it.

### Defense Risk
**Possible examiner question:** "Were any of the twenty-five sessions in Figure 7.5 used when you chose the Table 6.1 thresholds?"
**Why this is risky:** A yes without disclosure converts your headline monitoring result into a partially self-fulfilling one.
**How to fix:** Add one sentence to §6.5 or §7.4 stating exactly which sessions informed threshold selection.

---

## Section: Chapter 7 — Experiments and Evaluation

### Overall Verdict
**Strong results chapter with one structural hole.** The protocol separation (7.1), the three-number arc, the calibration analysis, and the 25-session monitoring evaluation are genuinely good. The hole: **the contract-sensitivity evidence that RQ2 and §1.6 depend on is referenced but never shown.**

### Main Problems
1. **CRITICAL — The preprocessing/contract-sensitivity ablation is missing.** §7.4 says: "The preprocessing and threshold sweeps reported alongside these runs are treated as diagnostic contract-sensitivity evidence… They show that monitoring severity responds to controlled changes in preprocessing, normalization, and windowing." **No numbers, no table, no figure.** Appendix C even points to the artifacts (`reports/ABLATION_WINDOWING.csv`, `THRESHOLD_CALIBRATION.csv`) — so the evidence exists in the repository but not in the document. Meanwhile Table 8.1 answers RQ2 "Strongly yes" citing "the contract-sensitivity sweeps (Sections 7.2.1, 7.4)". **A claim of "strongly yes" resting on evidence the reader cannot see is the most attackable point in the thesis.** Fix (preferred): add a half-page §7.4.1 "Contract-Sensitivity Ablation" — one table (configurations × monitoring severity/accuracy deltas), three sentences of interpretation, and this simultaneously (a) redeems §1.6's promise, (b) grounds RQ2, (c) gives "D1" its meaning, and (d) restores your strongest earlier empirical result (the config-D superiority finding). Fix (fallback): soften §1.6, §7.4, and Table 8.1 to claim only what is shown.
2. **The 23/25 review routing is not decomposed.** Stated policy: review requires the collapse guard, ≥1 critical signal, or consecutive-warning escalation. Stated evidence: confidence healthy on *all 25* sessions, drift "mostly contained" with *one* critical excursion, transitions "frequently" above the 35% warning line. From Figure 7.5, perhaps 10–12 sessions exceed the 50% transition-*critical* line — that does not obviously produce 23 reviews. The remaining reviews presumably came from the collapse guard — but **the dominant-class share, the one signal tied to the collapse guard, is the only Stage 6 signal *not* plotted in Figure 7.5.** Add a small table: review reason × session count (collapse guard / critical transition / critical drift / escalation / queue_retrain / monitor / none). Without it, the headline RQ1/RQ3 evidence is a black box.
3. **5-fold leakage is understated by one mechanism.** §7.2.1 correctly discloses scaler-before-split and same-user windows across folds. It omits the third leak: with 50% window overlap and a shuffled window-level split, **adjacent windows sharing 100 raw samples land in different folds** — direct sample-level leakage. You already frame the 93.61% as "optimistic by construction"; name this mechanism explicitly and the framing becomes airtight instead of incomplete.
4. **The benchmark comparison is a defense landmine because the examiner wrote the benchmark.** "consistent with, and slightly above, the published Garmin HAR benchmark of 87.0% ± 1.2% obtained under the same five-fold family [10]." "Same five-fold *family*" is doing heavy lifting. If [10]'s protocol differs in any respect (scaler policy, window construction, augmentation, splits), Mr. Oleh will know instantly. Either verify protocol identity and state it precisely, or soften to "in the same range as the published benchmark, noting protocol differences in augmentation and scaler policy."
5. **Bootstrap CI on overlapping windows.** [33.9%, 39.8%] for User 7 is computed over windows that overlap 50% — correlated samples → the naive bootstrap **understates** the interval width. You already bound the CI's meaning well ("window-level… not population-level"); add "and adjacent windows overlap, so the interval is approximate; a block bootstrap would widen it."
6. Tables 7.3/7.4: the "Mean" row carries **3,755** in the Windows column — that is the *total*, not a mean. Relabel row "Mean / Total" or footnote.
7. The LOUO "mean" 44.42% is the **unweighted across-user mean**; the window-weighted accuracy is ≈44.05% (recomputed). Not wrong — arguably the right choice (each user equally weighted) — but state it: "mean is the unweighted average over the six held-out users."
8. **Figure 7.3 (calibration) has a corrupted legend** — "perfect calibration / mean conf 0.858 / Model D1 (User-7) / accuracy 0.370" render *on top of each other*, unreadable. Verified visually. Regenerate (`scripts/generate_ch7_figures.py`, fix legend placement). This is the kind of defect that primes an examiner to hunt for more.
9. §7.5 "The within-distribution number is legitimate and **mentor-comparable**" — "mentor-comparable" is private jargon that should never have survived into the document. Replace with "comparable with the published Garmin benchmark [10]".
10. §7.2.3 "This is the most **honest** deployment-like measurement" — editorializing; "strictest" carries the meaning with academic register.

### Line-by-Line Review (selected)
| Location | Original text | Problem | Risk | Suggested fix |
|---|---|---|---|---|
| §7.4 | "preprocessing and threshold sweeps… are treated as diagnostic contract-sensitivity evidence" | Evidence asserted, never shown | **Critical** | Add §7.4.1 ablation table from `reports/ABLATION_WINDOWING.csv` |
| §7.4 | "routed 23 of the 25 sessions to review" | No per-reason decomposition; dominant-class share unplotted | **High** | Add reason-breakdown table; add dominant-share panel or column |
| §7.2.1 | "Because the scaler is fitted on all six users before the windows are split, and because windows from the same wearer appear in both training and validation folds" | Omits overlap-leakage between adjacent windows | High | Append: "and adjacent overlapping windows share half their samples across folds" |
| §7.2.1 | "consistent with, and slightly above, the published Garmin HAR benchmark… under the same five-fold family" | Protocol identity unverified; examiner is the benchmark author | High | Verify or soften ("in the same range as") |
| §7.2.3 | "95% bootstrap confidence interval of [33.9%, 39.8%]" | Naive bootstrap over correlated overlapping windows | Medium | Add approximation caveat / block-bootstrap mention |
| §7.5 | "legitimate and mentor-comparable" | Informal private jargon | Medium | "comparable with the published Garmin benchmark [10]" |
| §7.2.3 | "the most honest deployment-like measurement" | Editorial tone | Low | "the strictest deployment-like measurement" |
| Tables 7.3/7.4 | Mean row, "3,755" under Windows | Total mislabeled as mean | Low | "Mean / Total" |
| Fig. 7.3 | overlapping legend text | Rendering defect (verified) | **High (optics)** | Regenerate figure |
| §7.2.2 | "User 2 is reported as part of the primary result and is not removed to inflate the mean" | Excellent — keep verbatim | — | — |

### Technical Accuracy Check (independently recomputed)
- 5-fold mean: (93.34+94.41+94.14+93.48+92.68)/5 = **93.61** ✔; macro-F1 mean 0.937 ✔; 751×5 = 3,755 ✔.
- LOUO unweighted mean: **44.43** (thesis 44.42 from higher-precision per-user values — fine); macro-F1 0.419 ✔.
- User 7: 989 windows ✔; CI width consistent with p(1−p)/n at n=989 ✔ (subject to the overlap caveat above).
- User-7 labeled 36.96% vs unlabeled schedule-aligned 36.70% (Fig. 7.6): a genuinely clever validation of the monitoring proxies — under-sold; consider one extra sentence in §7.5.

### Defense Risk
**Possible examiner question (highest probability in the whole defense):** "You answer RQ2 'strongly yes' citing Section 7.4 — walk me to the quantitative contract-sensitivity result."
**Why this is risky:** It does not exist in the document today.
**How to fix:** Add §7.4.1 (half a page). The CSVs already exist.

---

## Section: Chapter 8 — Discussion and Conclusion

### Overall Verdict
**Acceptable — the thinnest chapter.** §8.2 (interpretation) and §8.3 (limitations) are strong; §8.1 outsources the entire RQ discussion to one table; §8.5 is a competent close. ~4 pages of discussion for a 77-page body is light.

### Main Problems
1. **§8.1 is one paragraph + Table 8.1.** For each RQ, write 3–5 sentences of prose *in addition to* the table row: claim → evidence pointer → bound. That is ~1 extra page and converts the chapter from "summary" to "discussion."
2. **RQ2 row: "Strongly yes"** — (a) category error against a "How" question (see Ch. 1), (b) strength unsupported until the ablation is added. Rewrite the answer as: "Materially: under the fixed contract the model reaches 93.6% within-distribution, while controlled contract perturbations (Section 7.4.1) change monitoring severity and recognition behavior; units, scaler, channel order, windowing, and baseline must therefore remain bound to the model."
3. **Self-repetition across 7.5 → 8.1 → 8.2.** "Within-distribution accuracy is an insufficient basis…" appears three times in near-identical skeleton, and the 93.61/44.42/5.69/36.96/0.858 number block is recited in full in §7.5, the Ch. 8 intro, §8.1, and §8.5 — four times in eight pages. Recite once (Ch. 8 intro), reference thereafter.
4. §8.3 limitations are honest and well-chosen — the strongest limitation section I have seen in this project's drafts. Two additions: (i) author-as-subject bias for User 7 (the wearer knew the class definitions — demand characteristics; distinct from the label-timing point already made), (ii) threshold–evaluation circularity disclosure (see Ch. 6).
5. §8.4 Future Work is a single dense paragraph; fine, but the EWC abbreviation is defined in the abbreviations list yet never used in the body — either mention EWC where continual learning is discussed [56, 57] or drop it from the list.

### Line-by-Line Review (selected)
| Location | Original text | Problem | Risk | Suggested fix |
|---|---|---|---|---|
| Table 8.1, RQ2 | "Strongly yes: units, scaler, channel order…" | Yes/no answer to a How question; evidence not in document | **Critical** | Rewrite answer (above) + add §7.4.1 |
| Table 8.1, RQ4 | "the contract is sound (within-distribution success rules out a broken pipeline)" | Logical overreach: within-distribution success rules out *gross* pipeline breakage, not all contract issues | Medium | "within-distribution success indicates the pipeline and contract function as specified" |
| §8.2 | "it is wrong while confident, which is the most dangerous behavior for a health-adjacent system" | Strong but defensible; keep | — | — |
| §8.5 | Number block repeated a fourth time | Repetition | Low | Reference, don't recite |

### Defense Risk
**Possible examiner question:** "RQ4 asks whether degradation is caused by model-contract issues rather than input data — but you only show the contract is *not* broken. How do you attribute the degradation positively to cross-user shift?"
**How to prepare:** Point to (a) Table 4.4/Fig. 4.3 distribution differences, (b) per-user LOUO spread (5.7%–61.1%) under an *identical* contract, (c) the labeled-vs-unlabeled User-7 agreement (Fig. 7.6) showing the pipeline measures consistently. Rehearse this chain; it is your best RQ4 answer and it is scattered across three chapters.

---

## Section: References and Appendices

### Overall Verdict
**Acceptable.** 61 references, mostly high-quality and well-matched to claims. Appendices A–E are a genuine strength — the runbook, contract inventory, and result-to-artifact mapping (Table C.1) are exactly what "auditable" should mean.

### Main Problems
| Item | Problem | Risk | Fix |
|---|---|---|---|
| [5] Oleh et al., EHB 2025 | "conference paper" — no pages/DOI/location | Medium | Complete the entry (it is the examiner's paper) |
| [10] Oleh & Obermaisser, ICTH 2025 | "accepted conference paper / proceedings version" — by June 2026 the Procedia volume should exist | Medium | Cite volume/pages/DOI; this is the foundation reference |
| [38] UCI HAR | Editorial annotation ("dataset page documents 50 Hz…") embedded *inside* the bibliography entry; canonical paper is Anguita et al. 2013 (ESANN) | Medium | Move the note to the text; cite Anguita et al. 2013 + dataset DOI |
| [2], [13], [22], [41], [48], etc. | arXiv preprints where published versions may exist | Low–Med | Sweep once: replace arXiv with the published venue where available |
| Appendix C | Notebook provenance honesty | Good — but surface one sentence of it in §7.1 (see Ch. 5/7) | — |
| Appendix D | Duplicates every Ch. 6/7 formula verbatim | Low | Acceptable as a collected reference; alternatively keep formulas only in Appendix D and cite from the chapters to reduce duplication |

---

# FINAL REPORT SUMMARY

## 1. Overall Thesis Quality Score

| Dimension | Score /10 | One-line justification |
|---|---|---|
| Academic structure | 8.5 | Disciplined chapter architecture; Ch. 8 thin, repetition across 7.5/8.1/8.2 |
| Technical correctness | 8.0 | All headline numbers recompute correctly; drift-baseline contradiction and folder-name mismatch deduct |
| Methodology | 8.0 | Exemplary protocol separation and blind-probe discipline; notebook provenance and threshold circularity need surfacing |
| Results interpretation | 9.0 | The two-number framing and refusal to inflate is the best thing in this thesis |
| Language quality | 8.0 | Clean, consistent, controlled; UK/US mix, "mentor-comparable", minor German error |
| Human writing style | 6.5 | Heavy "X is not Y; it is Z" cadence + verbatim self-duplication reads machine-assisted in places |
| Citation quality | 7.5 | Well-matched sources; several incomplete entries ([5],[10],[38]) and arXiv-where-published-exists |
| Reproducibility | 8.5 | Runbook + hashes + result-to-artifact map are genuinely strong; latency number missing |
| Defense readiness | 7.0 | Six predictable attack vectors, all preparable; RQ2 gap is the one that must be closed in the document |

**Weighted overall: ~7.9/10 — a good thesis one focused week away from a very good one.**

## 2. Top 10 Critical Fixes (ranked)

1. **Restore the contract-sensitivity ablation to Chapter 7 (new §7.4.1).** One table from `reports/ABLATION_WINDOWING.csv` + 3 sentences. This single fix repairs §1.6's broken promise, grounds RQ2, justifies the name "D1", and reinstates your strongest earlier empirical finding. *(If truly impossible: soften §1.6, §7.4, Contribution 3, and Table 8.1 to match shown evidence.)*
2. **Explain "Model D1"** — one sentence in §4.4 defining the D/D1 lineage.
3. **Resolve the drift-baseline contradiction** (§6.2 "raw physical" vs Appendix B "scaled feature space, Stage 6 drift reference"). Check the code; align both passages.
4. **Fix Figure 3.2 folder name** `20260526` → `20260528`; grep the LaTeX source for stragglers.
5. **Decompose the 23/25 review routing** — small table of review reason × count; state whether `queue_retrain` ever fired; add the dominant-class-share view for the 25 sessions.
6. **Fix RQ2's question/answer mismatch** — reword RQ2 to yes/no form or rewrite Table 8.1's "Strongly yes" as a descriptive answer.
7. **Regenerate Figure 7.3** — the reliability-diagram legend renders as overlapping unreadable text.
8. **Name the third 5-fold leak** — adjacent 50%-overlapping windows split across folds share half their samples; one appended clause in §7.2.1.
9. **Surface notebook provenance in §7.1** (one sentence pointing to Appendix C) instead of letting the examiner discover it.
10. **Disclose threshold provenance** relative to the 25 evaluated sessions (§6.5 or §7.4) — kill the circularity question before it is asked; add author-as-subject bias to §8.3.

## 3. Top 10 Smaller Fixes

1. Deduplicate the verbatim "offline-first means…" definition (3×: §1.5, §2.5, §3.6) and the "dashboard add-on" sentence (2×: §2.6, Ch. 6 intro).
2. Normalize "authorise/authorize" to one spelling (US is your majority).
3. Tables 7.3/7.4: "Mean" row shows total windows (3,755) — relabel "Mean / Total".
4. State the LOUO mean is the unweighted across-user average (window-weighted ≈ 44.05%).
5. Replace "mentor-comparable" (§7.5) and "the most honest" (§7.2.3) with academic register.
6. Zusammenfassung: "Darstellung von 50 Hz" → "Abtastrate von 50 Hz"; consider "Haarezupfen".
7. Fix the literal "train--serve" double hyphen inside Figure 4.1's plot title; consider moving Fig. 4.1 to Appendix E (it duplicates Table 4.4 exactly).
8. Complete references [5] and [10] (pages/DOI); move the editorial note out of [38] and cite Anguita et al. 2013; sweep arXiv→published versions.
9. Remove or document the orphaned entropy-drift mechanism (in formal definitions, absent from Table 6.1/policy/results); same for unused EWC abbreviation.
10. Add one measured latency/throughput number (or delete "low-latency" in §4.3) and one data-provenance/consent sentence in §4.1.

## 4. Claims That Must Be Softened

| Current claim | Safer version |
|---|---|
| "consistent with, and slightly above, the published Garmin HAR benchmark… under the same five-fold family" (§7.2.1) | "in the same range as the published benchmark [10]; protocol differences in augmentation and scaler policy preclude an exact comparison" — *unless* you verify protocol identity, in which case state it precisely |
| "Strongly yes" (Table 8.1, RQ2) | Descriptive answer tied to §7.4.1 evidence |
| "impossible to trigger automatic mutation" (§6.3) | "by construction, no code path converts severity into mutation without the label/QA gate" |
| "within-distribution success rules out a broken pipeline" (Table 8.1, RQ4) | "indicates the pipeline and contract function as specified" |
| "each one supports the offline-first, contract-driven goals" (§5.2) | "the main implementation choices each map to…" |
| 95% bootstrap CI [33.9, 39.8] (§7.2.3) | Add: window overlap → correlated samples → interval is approximate (block bootstrap would widen it) |
| "the most honest deployment-like measurement" (§7.2.3) | "the strictest deployment-like measurement" |

## 5. Missing Evidence

1. **Contract-sensitivity ablation table** (configs × accuracy/monitoring deltas) — exists as repo CSV per Appendix C, absent from document. ← the big one
2. **Review-reason decomposition** for the 23/25 sessions + dominant-class-share per session.
3. **Promised "negative results"** (§1.6) — no explicitly labeled negative result appears; the earlier AdaBN-instability finding (or whichever negative result was meant) must be reported or the promise deleted.
4. Latency/throughput number to back "low-latency."
5. Data-provenance/consent statement for Garmin users 1–6 and User 7.
6. Threshold-provenance statement (which sessions informed Table 6.1 values).
7. Whether the `queue_retrain` branch ever fired across all evidence runs.

## 6. AI-Like Sentences (worst offenders, with rewrites)

**Overall AI-writing risk: Medium.** The content is deeply project-specific (file paths, hashes, exact counts) — no one will mistake the substance for generic text. The *cadence* is the tell: a relentless "X is not Y; it is Z" antithesis pattern (≥15 instances), triadic lists, and identical sentence skeletons recycled across chapters. One editing pass varying rhythm in the worst spots is enough.

| Original | Risk | Humanized rewrite |
|---|---|---|
| "Monitoring here is therefore not a dashboard add-on; it is part of the runtime control logic." (2nd occurrence, Ch. 6 intro) | High (duplicated) | "Stage 6 sits inside the control flow itself: its outputs are inputs to the Stage 7 decision, not a display layer." |
| "The implementation choices in this chapter are deliberate rather than incidental; each one supports the offline-first, contract-driven goals" (§5.2) | Medium | "Each implementation choice below is tied to a specific goal from Chapters 3 and 4; none is a framework default kept for convenience." |
| "Read together, the results form one coherent argument." (§7.5) | Medium | "Taken together, the four results support a single conclusion:" |
| "This is a deliberate governance policy, not a missing feature." (§6.3.2) | Low–Med (punchy but formulaic) | Keep one such construction per chapter at most; here it can stay — delete two neighbors instead |
| "Hybrid CNN–LSTM architectures combine these strengths." (§2.3) | Medium (textbook cadence) | "Model D1 inherits both properties: the convolutional front end captures sub-second motion motifs of tapping and rubbing, while the BiLSTM models their repetition across the four-second window." |
| "The gap between them is the result, not a failure to be hidden." (§7.5) / "The distance between the two is the result." (§8.1) | Medium (same skeleton 2×) | Keep §7.5's version; in §8.1 write "That fifty-point distance is the thesis's central empirical fact." |

## 7. Defense Danger Zone (the exact attack list — prepare scripted answers)

1. **The title.** "Your title says Continuous Mental Health Monitoring; page after page disclaims it. Why should this title pass?" → 30-second answer: title was fixed at registration; the thesis converts it into an *application context* (§1.1, §2.1, §3.6) and defines the defended technical claim as bounded behavioral-proxy HAR; the boundary is itself a contribution (Contribution 5).
2. **RQ2 evidence.** "Show me the quantitative contract-sensitivity result." → must exist in the document (Fix #1) before the defense.
3. **"What were Models A–D?"** → naming sentence + ablation history (Fix #2).
4. **"Decompose the 23/25 reviews."** → breakdown table (Fix #5); know the per-reason counts cold.
5. **"Raw or scaled feature space for drift?"** → currently contradictory (Fix #3); after fixing, be able to say which file, which space, one sentence.
6. **"93.6% vs my 87% — same protocol?"** — remember the second examiner *authored* [10]. Verify before the defense; if protocols differ, your comparison sentence must already say so.
7. **"User 7 is you."** → procedural blindness (excluded from training/scaler/selection, evaluated once post-freeze) + acknowledged label-timing and demand-characteristics bias (§8.3 after Fix #10) + Fig. 7.6 labeled/unlabeled agreement as a consistency check.
8. **"Your headline numbers come from a notebook."** → Stage-8-equivalent controlled build environment, version-controlled, artifact-pinned via `artifact_md5.json`, consumed by the pipeline; Appendix C maps every number to its file (Fix #9 puts this in §7.1).
9. **"Overlapping windows: is your 5-fold CV and your bootstrap CI statistically valid?"** → concede optimism by construction (it is framed as learnability, not deployment), name all three leak mechanisms, point to LOUO as the deployment-relevant number; CI is approximate (overlap caveat).
10. **"Were the 25 sessions used to set the thresholds?"** → must have a clean, disclosed answer (Fix #10).
11. **"Why does the runtime silently *correct* a stale contract path instead of always failing?"** → logged warning + exact-match-only correction + fail-fast preserved for incompatibility (rehearse §3.5.1 logic).
12. **"Gyroscope in deg/s, not SI rad/s — why?"** → contract fidelity to the training data convention of [9, 10]; changing units = contract change.

## 8. Final Recommendation

**Is this ready to submit? Not today — but it is close, and the distance is measured in days.**

The thesis's spine is sound: the runtime-contract idea is real, implemented, and tested; the evaluation is unusually honest; the limitations section actually limits. What stands between this and a confident submission is a short, concrete list:

**Must fix before submission (blocking):** Fixes 1–7 from the critical list — the ablation/RQ2 gap, D1 naming, drift-baseline contradiction, Figure 3.2 folder name, the 23/25 decomposition, RQ2 wording, Figure 7.3 regeneration. Estimated effort: 3–5 focused days, because every required artifact already exists in the repository.

**Should fix (marks at stake):** Fixes 8–10 + the softening table + smaller fixes 1–8. One additional day.

**Can wait / defense-prep only:** Expanding §8.1 prose, the latency number, arXiv sweep, the writing-cadence pass — do them if time remains after the blockers; otherwise carry the answers into the defense verbally.

**What would likely cost marks if untouched:** (1) the RQ2 evidence gap — examiners grade claims against shown evidence; (2) the two internal contradictions (drift baseline, folder name) — in a consistency-themed thesis they read as symptomatic; (3) the broken Figure 7.3 — cosmetic, but it primes scrutiny of every other figure; (4) walking into the [10]-benchmark comparison unprepared against its own author.

Fix the seven blockers, rehearse the twelve-question danger list, and this defends well.
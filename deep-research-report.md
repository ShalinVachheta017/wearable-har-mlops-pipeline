# Thesis Review of *An Offline-First MLOps Pipeline with Governance for Wearable Human Activity Recognition*

This review is based on the uploaded thesis PDF only. The thesis itself documents a precise Model A contract, persisted train-only scaler semantics, API/batch parity claims, and Stage 7 governance outputs, but the repository named in the text was not supplied here, so code-backed claims could be assessed only as documented thesis claims, not independently executed facts. fileciteturn0file0L2807-L2825 fileciteturn0file0L3895-L3974 fileciteturn0file0L4218-L4249

## Core Formal and Structural Review

### Structural Integrity
Score: 2/5  
Verdict: Fail  
Top 3 issues, most severe first:
  1. [p.2, p.4 front matter / Contents] — The required German **Zusammenfassung** is missing. The front matter contains an English Abstract and the table of contents shows no German summary section. That is a formal submission-risk item at a German university, not a stylistic preference. Concrete fix: insert a 200–300 word German Zusammenfassung in the front matter, have it checked by a native speaker, and add it to the contents.
  2. [p.1 title page; p.3 Eidesstattliche Erklärung] — The date metadata is inconsistent. The title page is dated **15 June 2026**, while the declaration is dated **19 April 2026**. That looks careless and can trigger avoidable administrative scrutiny. Concrete fix: use the final submission date consistently across title page, declaration, and metadata.
  3. [pp.4–7, Contents / Appendices] — The appendix set is incomplete relative to the scope of the claims. You have mathematical foundations and a technology stack appendix, but no dedicated reproducibility checklist appendix, no config reference appendix, no ethics/data-handling appendix, and no glossary beyond abbreviations. Concrete fix: add appendices for reproducibility, config/artifact reference, GDPR/ethics, and key runtime commands.

Strengths worth keeping: Chapter 1 largely does promise the bounded system that Chapters 3, 5, 6, and 7 later defend: offline-first, 7+3 stage structure, no unrestricted auto-deployment, and no clinical claim. The scope boundary is repeatedly visible and mostly coherent. 

### Typography & Layout
Score: 3/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [front matter overall] — Formal front-matter compliance is weakened by the missing German Zusammenfassung and the declaration/title-page date inconsistency. Concrete fix: repair front matter before touching any prose polish.
  2. [p.13 Figure 3.1; p.14 Figure 3.2; p.73 Figure 7.5 by caption/listing] — Several diagrams look likely to be under-readable at A4 print size. The historical stage-evolution diagram and the multi-panel dashboard are especially at risk. Concrete fix: enlarge box text to print-safe size or split overloaded figures into two.
  3. [throughout Chapters 2–8] — The thesis is professionally typeset, but the running prose is so uniform in rhythm that the page texture reads machine-smoothed rather than human authored. That is not a typography defect strictly speaking, but it affects presentation quality. Concrete fix: vary paragraph length and remove repetitive chapter-tail “synthesis” sentences.

Strengths worth keeping: Roman numeral front matter, Arabic numbering from Chapter 1, lists of figures/tables/abbreviations, and a generally clean chapter hierarchy are all present on the face of the PDF.

## Scientific Argument and Writing

### Scientific & Technical Correctness
Score: 3/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [pp.65–66, §7.4; Table 7.4] — The preprocessing ablation is presented as if it supports strong causal interpretation, but the evidence shown is descriptive only. Table 7.4 reports means for unique classes and hand-tapping share across A/B/C/D, but I did not find variance, confidence intervals, p-values, effect sizes, or any multiple-comparison control. Concrete fix: report per-session paired statistics for all four configs, state the test used, add effect sizes, and explicitly say what is descriptive versus inferential. fileciteturn0file0L4921-L4935 fileciteturn0file0L4936-L4954
  2. [p.47, §5.6.6] — API/batch parity is asserted strongly, but the thesis does not show the parity evidence as a compact in-thesis audit table. It says 989/989 predictions matched and max softmax difference was 1.9×10⁻⁶, but the reader must trust an external report path. Concrete fix: add one appendix table showing identical model path, scaler path, feature order, unit conversion, windowing, class map, and softmax diff for both routes. fileciteturn0file0L3965-L3974
  3. [pp.27–29, §4.5.4–§4.6; pp.46–47, §5.6.2–§5.6.3] — The Model A contract is materially improved and mostly precise, but the contract is spread across multiple sections and file-path references rather than frozen once in one canonical contract table. Concrete fix: create a single “Final Runtime Contract” table in Chapter 5 and refer every later chapter back to it. fileciteturn0file0L2807-L2825 fileciteturn0file0L2882-L2942 fileciteturn0file0L3917-L3939

Strengths worth keeping: The thesis is explicit about the defended preprocessing order: unit conversion first, persisted Garmin train-only StandardScaler before windowing, row-wise windows, fixed `(batch, 200, 6)` shape, fixed label order, and prohibition on fitting new scalers on replay/external data. That is technically the strongest part of the document. fileciteturn0file0L2807-L2825 fileciteturn0file0L3917-L3928

### Storyline & Argumentation
Score: 3/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [pp.5–15, Chapters 2–3] — The thesis spends too much time telling the reader what it does **not** claim. That defensive framing is necessary once, not every few pages. Concrete fix: compress all non-claims into one short scope-boundary subsection and let the method/results carry the rest.
  2. [pp.61–79, Chapter 7] — The experiments are individually understandable, but the chapter still reads partly like a stitched sequence of engineering episodes rather than one cumulative argument. Concrete fix: add a one-page “evidence map to RQ” figure/table at the start of Chapter 7 and end each experiment with a one-sentence answer to one research question.
  3. [p.82, §8.2; Table 8.1] — The research questions are answered, but too compactly. They need explicit, individual answer paragraphs instead of a terse summary table alone. Concrete fix: rewrite §8.2 so each RQ gets four sentences: answer, evidence, limitation, boundary.

Strengths worth keeping: The basic chain exists and is visible: problem → bounded scope → architecture → preprocessing/model contract → monitoring/governance → experiments → limitations. It is not incoherent. It is just over-defended and under-sharpened in the final argumentative compression.

### Writing Quality
Score: 3/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [pp.5–10, Chapter 2] — The prose is consistently grammatical but too polished and too uniform. Repeated “synthesis” and “the thesis boundary” sentences flatten the voice and make it read generated. Concrete fix: cut the meta-commentary by at least 30% and replace it with direct claim-evidence prose.
  2. [throughout Chapters 3, 5, 6] — You overuse contrastive constructions: “not X but Y,” “does not claim A, claims B,” “not a missing feature, a governance policy.” It becomes a tic. Concrete fix: keep the first occurrence and delete or rewrite the rest.
  3. [throughout] — Runtime-role terminology is not tight enough. “Defended runtime,” “proof-of-concept runtime,” “retained model,” “A1 baseline,” and “retained deployment model” all refer to nearby concepts and create avoidable reader load. Concrete fix: define one term per artifact role and enforce it globally.

Strengths worth keeping: Sentence-level clarity is generally high. I did not see serious grammar collapse, acronym chaos, or broken technical English.

### AI-Authorship Footprint
Score: 2/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [pp.5–10, Chapter 2] — The background chapter shows strong AI-assisted style markers: repeated mini-synthesis tails, citation stacking, and uniform paragraph cadence. Concrete fix: rewrite Chapter 2 in a blunter, more source-specific voice.
  2. [pp.12–15, Chapter 3] — The architecture chapter repeatedly explains its own framing instead of just specifying the architecture. Concrete fix: replace meta-framing with decision tables and branch logic.
  3. [pp.51–59, Chapter 6] — Governance prose is polished to the point of sounding pre-packaged. Concrete fix: add actual engineering failures, thresholds changed late, and what broke.

Strengths worth keeping: The thesis does contain some genuinely engineering-specific details — especially around scaler persistence, collapse guard semantics, and API/batch parity — which pull it back toward authentic authorship. fileciteturn0file0L3931-L3974 fileciteturn0file0L4185-L4216

Flagged passages:

[p.6, §2.2]  
Quote: “The mini-synthesis here is…”  
Classification: Likely AI  
Problem: This is textbook LLM transition prose. It adds polish, not substance.  
Rewrite in candidate’s own direct register:  
**Before** | **After**  
“The mini-synthesis here is that wearable sensing literature…” | “These papers support the application context, but they do not solve the deployment problem I am addressing.”

[p.9, §2.4]  
Quote: “The synthesis of this section defines the thesis boundary directly.”  
Classification: Likely AI  
Problem: That sentence sounds like a model narrating essay structure.  
Rewrite in candidate’s own direct register:  
**Before** | **After**  
“The synthesis of this section defines the thesis boundary directly.” | “This section matters because it shows exactly where my thesis starts: after training, when deployment constraints appear.”

[p.10, §2.5]  
Quote: “The thesis sits in the overlap…”  
Classification: Human but reads AI-ish  
Problem: The phrase is vague and abstract. It evades the harder sentence.  
Rewrite in candidate’s own direct register:  
**Before** | **After**  
“The thesis sits in the overlap…” | “My contribution is not a new HAR model. It is a governed runtime and retraining workflow for that model under label-scarce use.”

### Citations & References
Score: 3/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [pp.5–10, Chapter 2] — The citation style appears consistently numeric, which is good, but the related-work chapter often stacks sources to support broad umbrella statements instead of making source-specific distinctions. Concrete fix: rewrite each related-work paragraph so each citation is tied to one concrete claim.
  2. [pp.94–96, Appendix B] — The technology stack appendix risks reading like product documentation summaries rather than research support. Concrete fix: for each tool, state only what function it served in this thesis and why that mattered scientifically or operationally.
  3. [pp.57–59, §6.8–§6.9] — Some threshold-justification language is under-cited relative to the strength of the monitoring-governance claims. Concrete fix: add literature specifically on threshold calibration under weak labels and on proxy monitoring limitations.

Strengths worth keeping: In-text numeric citation style appears consistent with IEEE norms, and the thesis does cite both wearable HAR and MLOps literature instead of pretending either side is sufficient alone.

## Visual and Tabular Communication

### Figures
Score: 3/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [p.13 Figure 3.1; p.14 Figure 3.2] — The architectural figures likely contain too much small text for comfortable print reading. Concrete fix: reduce text inside boxes and move explanatory detail to caption or body text.
  2. [p.73 Figure 7.5, by caption/listing] — The six-panel dashboard is too dense for a thesis page unless the font is unusually large. Concrete fix: split it into two figures and state the one take-away sentence for each panel in the body text.
  3. [pp.21–22 Figures 4.2–4.4] — The distribution-comparison figures appear to carry interpretive load that should also be stated explicitly in prose. Concrete fix: after each figure reference, write one sentence giving the exact empirical takeaway and boundary.

Strengths worth keeping: Figure captions are generally self-contained and better than average. The captions often tell the reader what claim the figure can and cannot support.

### Diagrams
Score: 3/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [pp.13–14, Figures 3.1–3.2] — You put historical stage evolution and final defended architecture close together in the main text. That invites confusion over which stage count is final. Concrete fix: move the historical-evolution diagram to an appendix and keep only the final 7+3 diagram in Chapter 3.
  2. [p.14, Figure 3.2] — Calibration is shown as an optional extension, but the visual separation from the defended core is not forceful enough. Concrete fix: use dashed borders plus a legend that marks “not part of defended runtime path.”
  3. [p.52, Figure 6.1] — Stage 5–7 governance is conceptually clear, but the exact branch semantics are not visually auditable enough for a reviewer. Concrete fix: add a compact decision table under Figure 6.1 listing every output combination.

Strengths worth keeping: The core thesis truth is not the old 14-stage story; it is the 7-stage core plus 3-stage governed branch, and the PDF does reflect that final framing. fileciteturn0file0L4143-L4150

### Tables
Score: 3/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [p.66 / Table 7.4] — The ablation table is too weak for the argumentative work it is doing. Means alone are not enough. Concrete fix: add n, spread, paired deltas, and inferential statistics. fileciteturn0file0L4939-L4954
  2. [p.68 / Table 7.5] — The trigger-policy table reports strong numbers, but the denominator and event structure are partly left to prose. Concrete fix: put episode count, threshold family, and alert definition directly in the caption.
  3. [pp.39–42, Tables 4.12–4.15] — The runtime contract and reproducibility anchors are useful but scattered. Concrete fix: merge them into a single appendix “runtime contract and evidence matrix.”

Strengths worth keeping: The thesis uses tables for the right kinds of things — contract specification, ablation summaries, and evidence maps — rather than dumping screenshots.

## Reproducibility and Defense

### Reproducibility & Engineering Rigor
Score: 3/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [pp.46–49; pp.94–96] — There is no single reproducibility checklist appendix giving tag/commit, environment, package versions, hashes, seeds, training time, runtime commands, and exact artefact map. Concrete fix: add a one-stop appendix that a reviewer can follow linearly. fileciteturn0file0L3885-L3893 fileciteturn0file0L4062-L4074
  2. [Chapter 4 and Chapter 8 overall] — I did not find a dedicated GDPR/consent/anonymisation/retention/ethics section for the Garmin collection that is prominent enough for an examiner to trust immediately. Concrete fix: add a dedicated subsection stating participant count, who collected the data, consent basis, anonymisation method, storage location, and retention period.
  3. [p.49, §5.9; pp.46–47, §5.6] — The thesis claims MLflow, DVC, CI, and parity evidence, but it does not give the hard audit items a reviewer wants: release tag, license, test count evidence, coverage %, and frozen reproduction commands. Concrete fix: add an appendix snapshot with the exact release/tag, test transcript summary, and coverage if available.

Strengths worth keeping: The thesis is much better than average at stating artifact semantics. The scaler is persisted in two forms, JSON/joblib parity is checked, label order is fixed, and Stage 7 explicitly separates alert severity from mutation authorization. fileciteturn0file0L3931-L3939 fileciteturn0file0L4218-L4249

### Defense / Kolloquium Readiness
Score: 2/5  
Verdict: Borderline  
Top 3 issues, most severe first:
  1. [throughout] — The thesis is not ready for the examiner question “Why no Kubernetes?” because I did not find that defense in the text. Concrete fix: add a short paragraph tying scope, hardware, offline-first architecture, and thesis maturity level to the Kubernetes exclusion.
  2. [§6.9] — The thesis is not ready for “Why MMD over KS or PSI?” because it defends MMD against the lightweight runtime monitor, not against those two alternatives. Concrete fix: add a paragraph explicitly comparing MMD to KS and PSI for multi-channel windowed IMU drift. fileciteturn0file0L4456-L4490
  3. [§7.4; §8.2] — The thesis is not ready enough for “Why is hand-tapping dominance posture shift and not a bug?” because the causal argument is not statistically locked down and the ruling-out matrix is not shown compactly. Concrete fix: add one diagnostics table that rules out units, scaler, feature order, class map, and double scaling.

Strengths worth keeping: The thesis can answer the scaler/governance questions better than most student theses. It does have a defensible answer for offline-first, for why retraining is gated, and for why critical alert does not equal auto-retrain. fileciteturn0file0L4218-L4249

Question: What is your scientific contribution in one sentence?  
Status: partially answered in §1.4 and §8.2  
What is missing: one tight sentence that distinguishes this work from generic MLOps and generic HAR.  
How to fix in one sentence: write a single-sentence contribution claim and repeat it verbatim in abstract, introduction, and conclusion.

Question: Why offline-first and not cloud?  
Status: answered clearly in §1.5 and Chapter 3  
What is missing: little; this is one of the stronger defended decisions.  
How to fix in one sentence: add one explicit “why cloud is out of thesis scope” sentence in §3.1.

Question: Why no Kubernetes?  
Status: not in thesis  
What is missing: an explicit defense of scope, complexity, and deployment mismatch.  
How to fix in one sentence: add one paragraph saying Kubernetes would not strengthen the thesis evidence relative to a single-machine governed runtime.

Question: Why Model A?  
Status: answered clearly in §5.6.1 and §7.6  
What is missing: one summary table up front rather than scattered explanations.  
How to fix in one sentence: add a table comparing Model A/B/C selection criteria and failure reasons.

Question: Why does Model A require a Garmin train-only scaler?  
Status: answered clearly in §4.5.4 and §5.6.3  
What is missing: almost nothing conceptually.  
How to fix in one sentence: add one boxed statement: “Model A is invalid without this persisted scaler.”

Question: How do you prevent double scaling?  
Status: partially answered in §4.5.4, §5.6.2, §5.6.6  
What is missing: an explicit end-to-end route check for both API and batch.  
How to fix in one sentence: add an appendix parity matrix stating exactly once where scaling happens in each path.

Question: Why MMD over KS or PSI?  
Status: partially answered in §6.9  
What is missing: direct comparison to KS and PSI.  
How to fix in one sentence: add a rationale paragraph saying why MMD better fits multivariate window summaries than univariate marginal tests.

Question: Why MC Dropout and not deep ensembles?  
Status: partially answered  
What is missing: comparative justification on compute, implementation complexity, and thesis scope.  
How to fix in one sentence: add one paragraph in Chapter 4 or 6 defending MC Dropout as the cheapest uncertainty method consistent with thesis scope.

Question: Why is hand_tapping dominance a posture/domain-shift issue and not a bug?  
Status: partially answered in §7.4 and discussion  
What is missing: a formal bug-exclusion matrix and inferential evidence.  
How to fix in one sentence: add a diagnostics table ruling out units, scaler, feature order, class map, and double scaling.

Question: How did you rule out wrong units, wrong feature order, wrong scaler, and wrong class map?  
Status: partially answered in §4.5.2–§4.5.4 and §5.6.2–§5.6.5  
What is missing: one consolidated proof table.  
How to fix in one sentence: add an appendix “contract verification checklist” table.

Question: What does Stage 7 do when collapse is detected?  
Status: answered clearly in §6.3–§6.5  
What is missing: nothing major.  
How to fix in one sentence: keep the existing answer and add a small branching pseudocode block.

Question: Why does Stage 7 not automatically retrain?  
Status: answered clearly in §6.5  
What is missing: little.  
How to fix in one sentence: explicitly repeat that `auto_retrain=false` is a design decision, not an unfinished feature.

Question: What would trigger Stages 8–10?  
Status: partially answered in §6.2–§6.4  
What is missing: exact necessary and sufficient conditions.  
How to fix in one sentence: add a decision table with all gate conditions for retrain/register/promote.

Question: What would you do differently with another 6 months?  
Status: partially answered in §8.6  
What is missing: prioritization.  
How to fix in one sentence: rank the next three steps by expected scientific value, not by feature count.

Question: How is your work different from MLflow examples or Made-With-ML?  
Status: partially answered  
What is missing: an explicit comparison paragraph.  
How to fix in one sentence: state that the novelty is governed HAR-specific monitoring and retraining separation under label scarcity, not generic MLOps plumbing.

Question: Why was the prognosis layer dropped?  
Status: partially answered in §1.5  
What is missing: who removed it and why that improved thesis validity.  
How to fix in one sentence: add one sentence stating it was removed to keep claims aligned with evidence and supervisor-approved scope.

Question: What single number best summarizes your pipeline’s value?  
Status: not in thesis  
What is missing: a crisp headline metric.  
How to fix in one sentence: choose one number and justify it, likely trigger-policy precision/FAR or API/batch parity difference, not raw accuracy alone.

Question: What is the biggest weakness of the thesis?  
Status: partially answered in §8.3–§8.5  
What is missing: one brutally direct sentence.  
How to fix in one sentence: explicitly state that the real-world evidence is narrow and still mostly single-user / label-scarce.

Question: What is the strongest evidence that the pipeline is reproducible?  
Status: partially answered in §5.6 and §5.9  
What is missing: one evidence sentence with artifact path, command path, and parity result.  
How to fix in one sentence: state the single strongest reproducibility fact in the conclusion.

Question: What is the strongest evidence that it is production-credible?  
Status: partially answered in §5.6.6, §6.5, §7.5  
What is missing: one synthesis sentence linking train-serve contract, Stage 7 gating, and parity.  
How to fix in one sentence: add a closing claim that production credibility here means contract discipline plus governed non-automatic mutation.

## Final Deliverable

### One-Paragraph Verdict

**Major revisions.** Academically, this is not an empty thesis. There is a real systems contribution here: the train-only scaler contract is explicit, the runtime path is better specified than in most student work, the governance logic is conceptually sound, and the thesis does distinguish monitoring severity from mutation authorization. But the document is not submission-safe in its current form. The missing German Zusammenfassung is a formal compliance problem. The title page and declaration dates do not match. The strongest experimental interpretation — the explanation of collapse behavior and preprocessing effects — is not statistically defended at the standard implied by the prose. Several examiner-critical answers are only partially in the text, especially Kubernetes exclusion, MMD versus KS/PSI, and the bug-versus-domain-shift ruling-out story. Estimated academic grade **as written**: **2.7–3.0**. Administrative submission risk is higher than that grade because of the front-matter compliance issues.

### Top 10 Must-Fix Issues

1. **[p.2, p.4] Missing German Zusammenfassung** — This can cost you submission compliance before anyone even grades the science. **Fix:** Add a technically accurate German summary and list it in the contents.
2. **[p.1; p.3] Front-matter date mismatch** — It makes the thesis look procedurally sloppy. **Fix:** Align all dates to the final submission date.
3. **[p.3] Eidesstattliche Erklärung signature visibility** — The PDF shows the declaration text, but the visible page does not clearly show a signed declaration. **Fix:** Ensure the submitted PDF contains the signed and dated declaration in the exact faculty wording.
4. **[pp.65–66, Table 7.4] Descriptive ablation presented too strongly** — Means without inferential statistics cannot carry the causal weight you assign to them. **Fix:** Add paired inferential testing, uncertainty estimates, and effect sizes for Configs A–D.
5. **[§7.4; §8.2] Hand-tapping collapse explanation overclaimed** — You have a plausible explanation, not a fully proven one. **Fix:** Add a compact ruling-out matrix for units, scaler, feature order, class map, and double scaling.
6. **[p.47, §5.6.6] API/batch parity not shown in-thesis** — The claim is strong, but the evidence is outsourced to a report path. **Fix:** Put a parity audit table in the appendix.
7. **[§6.9] MMD rationale incomplete for defense** — You argue MMD against a lightweight monitor, not against KS or PSI. **Fix:** Add one paragraph comparing MMD to those baselines for this exact data structure.
8. **[throughout; especially Ch.2] AI-smoothed prose footprint too visible** — This can hurt examiner trust even if the work is real. **Fix:** Rewrite the background and transition-heavy sections in a plainer, more personal engineering voice.
9. **[pp.46–49; Appendices] No single reproducibility checklist** — Reviewers should not have to reconstruct your environment from dispersed mentions. **Fix:** Add one appendix with tag, environment, commands, hashes, seeds, timing, and artifact tree.
10. **[Chapter 4 / Garmin collection] Ethics and GDPR treatment not prominent enough** — In Germany, that is not optional for human-collected wearable data. **Fix:** Add a dedicated data-protection and consent subsection.

### Top 5 Quick Wins

1. Replace every “The synthesis of this section…” style sentence with a direct claim sentence.
2. Add one boxed “Final Runtime Contract” summary table consolidating Model A assumptions.
3. Add one appendix “API vs batch parity” table with exact artifact paths and max probability delta.
4. Add one explicit paragraph: “Why no Kubernetes in this thesis.”
5. Add one explicit paragraph: “Why MMD here, and why not KS or PSI.”

### AI-Authorship Risk Paragraph

Right now, the thesis reads like **real engineering work that has been heavily AI-smoothed at the prose layer**. The strongest evidence that the underlying work is yours is the specificity around scaler persistence, runtime contract semantics, Stage 7 behavior, and the difference between alert severity and retrain authorization. Those are not generic filler. The weak point is the writing around them. Chapter 2 in particular sounds like a model trying to sound academic: repeated mini-syntheses, symmetric paragraph endings, and polished but bloodless framing. To close that gap, rewrite the literature review and transitions in your own speaking register. Say what failed, what you tried, what you removed, and why. Replace abstract “the thesis sits in the overlap” language with blunt engineering sentences. If you do not do that, an examiner may conclude that the ideas are yours but the thesis voice is not.

### Defense Readiness Rating

**2/5**

The three questions you are least prepared for from the current text are:

1. **Why no Kubernetes?**  
2. **Why MMD over KS or PSI?**  
3. **Why is hand-tapping dominance definitely posture/domain shift and not a contract bug?**

### Plagiarism / Turnitin Risk Paragraph

I do **not** see obvious hard-copy plagiarism from the PDF alone, but I do see **moderate Turnitin/PlagScan risk** in the generic, citation-dense background prose and in tool-description passages. The danger points are the literature review paragraphs that compress several sources into polished umbrella summaries, the MLOps-definition material, and any Appendix B pages that describe tools like MLflow/DVC in documentation-like language rather than thesis-specific language. Those passages may not be copied, but they are written in a way that can resemble close paraphrase or AI-generated synthesis. Rewrite those sections so every paragraph does one source-specific job, and make the methodology/tooling paragraphs explicitly about **your** pipeline decisions, not generic platform descriptions.

### Final Examiner Decision

Final decision: **Major revisions**  
Estimated grade: **2.7–3.0 academically; formal submission risk higher if front matter stays as-is**  
Submission risk: **High until German summary, declaration/signature, and date consistency are fixed**  
Defense risk: **Moderate to high unless the candidate prepares explicit answers on Kubernetes, MMD vs KS/PSI, and bug-vs-shift diagnostics**  
Most urgent fix: **Add the missing German Zusammenfassung and repair formal front-matter compliance before doing any cosmetic editing**
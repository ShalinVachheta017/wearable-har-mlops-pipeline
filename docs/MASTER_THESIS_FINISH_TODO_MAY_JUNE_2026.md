# Master Thesis Finish Board — May–June 2026

*Last updated: 2026-05-13 (after pipeline-centering sweep, Ch6 threshold explanation, and final active-thesis wording sweep).*
*Replaces all previous versions. Source of truth for what is done, what is open, and what is blocked.*

---

## Current Freeze State

```text
Model A  = defended clean proof-of-concept runtime candidate (FROZEN — do not retrain or change contract)
Model B  = legacy/mentor diagnostic reference only (not a defended runtime)
Model C  = checkpoint-contract mismatch evidence (retained as proof, not used)

auto_retrain = false (deliberate governance policy, not a bug)
Scaler       = Garmin train-only StandardScaler, persisted, SHA-256 verified
               Applied in defended runtime path: unit conversion → Garmin train-only scaler → row-wise windowing → Model A
Pipeline     = Stage 1–7 governed pipeline, verified; Stage 1+2 validation gates operate as designed
Stage 8–11   = optional/gated extensions, not defended live runtime features

No model improvement until docs/evidence/thesis sync and PDF submission are complete.
No production-grade, clinical, production-ready, or population-level generalisation claims anywhere.
```

---

## Completed and Committed

```text
✓ Test suite: 240/240 green (200 unit / 23 integration / 17 slow)
✓ Test suite cleaned: 370 → 240 tests, 34 → 23 files
✓ .dockerignore hardened
✓ cd.yml deleted; workflows README rewritten as CI-only
✓ Dockerfile.inference: tensorflow-cpu pin + requirements split → 4.52 GB → 2.63 GB (−42%)
✓ Stage 1–7 dry run on Model A (5/7 stages; Stage 1+2 correctly gated)
✓ Model A batch/API parity verified: 100% agreement, 1.9e-6 max abs diff on User 7
✓ LEGACY_PRETRAINED_MODEL gated in src/config.py via EXCLUDED_UNDOCUMENTED_PROVENANCE
✓ KS / PSI / MMD / z-score drift audit complete
✓ reports/THESIS_QA_REFERENCE_2026_05_08.md created
✓ reports/FINAL_RUNTIME_RUN_SUMMARY_2026-05-09.md created
✓ ABC model-contract comparison runner: hardened, re-run, evidence committed
✓ ABC evaluation: all_users diagnostic + User 7 labeled + Garmin unlabeled — all three datasets
✓ ABC model registry: model_a / model_b / model_c contract JSONs created and committed
✓ Model A scaler JSON/joblib parity verified: 0.0 absolute diff
✓ docs/MODEL_ABC_MENTOR_BRIEF_2026-05.md — committed
✓ docs/MODEL_DECISION_2026-05.md — verified and current
✓ docs/EVIDENCE_KIT_INDEX_2026-05.md — created, 25+ evidence files mapped to claims/chapters/slides
✓ docs/FINAL_THESIS_CLAIMS_2026-06.md — created, 20 verified claims C-01–C-20, 5 open gaps documented
✓ Ch5 pipeline implementation — updated with Model A contract, scaler, ABC evidence, Stage 1–7 evidence runs (ac676ef)
✓ Ch6 monitoring/drift/retraining — updated with CRITICAL vs. REVIEW distinction, governance scope
✓ Ch7 experiments/evaluation — updated with runtime contract check, preprocessing ablation, trigger comparison (b404300 + 2026-05-13 pipeline-centering sweep)
✓ Ch7 Synth Other metrics corrected from authoritative artifact (0e2c23e)
✓ Ch7 98.9% baseline reference explicitly attributed to pre-sprint model, not Model A (0e2c23e)
✓ Ch8 discussion/conclusion — scope boundaries, non-claims section, final contribution statement (096e984)
✓ Ch4 scaler contradiction fixed — Garmin train-only StandardScaler confirmed in runtime contract (9bdbaae)
✓ Ch4 parameter count clarified — Model A 87,083 params vs 499,131 full baseline (9bdbaae)
✓ Ch4 data/model provenance section updated (528ddfb)
✓ Ch2 BFRBs paragraph, anchor sentence, recognition-layer synthesis added (64b1f27)
✓ Ch2 mini-synthesis and Section 3 bridge (74d107e)
✓ Ch3 stage role names, concrete governance example, "scalable" anchor sentence (74d107e)
✓ Font fixed: Latin Modern vector fonts throughout PDF (49c1d1e)
✓ Figures rebuilt: fig_05, fig_08, fig_10, fig_ch6, fig_ch7 — thesis-quality vector diagrams (4808e14)
✓ PDF rebuilt: 112 pages, no undefined references, no missing figures, no missing citations (2026-05-12)
✓ internal/writing/defense_qa.md — complete overhaul, 10 sections, wording guards enforced (4a571d3)
✓ internal/writing/defense_slides_outline.md — 18-slide outline used as the source for the finalized defense deck
✓ thesis/main.tex title page — updated to "Siegen, 15 June 2026" (P0-04, 2026-05-12)
✓ PDF final build — 113 pages, no undefined refs, no missing figures, Latin Modern font confirmed (P0-08, 2026-05-12)
✓ internal/writing/demo_runbook.md — created with exact commands, fallback script, numbers table, what-not-to-claim (P0-11, 2026-05-12)
✓ internal/writing/defense_slides.pptx — 18-slide PPTX built, 1.32 MB, all 6 figures embedded, verbatim speaker notes (P0-10, 2026-05-12)
✓ internal/writing/build_slides.py — re-runnable python-pptx builder script
✓ README.md — proof-of-concept wording and final scaler/runtime contract aligned (`57ddb75`)
✓ thesis/references.bib and wording cleanup — bibliography pass + softened BFRB scope wording (`0f0f92a`)
✓ internal/writing/STAGE_BY_STAGE_TECHNICAL_CONFIDENCE.md — added as defense-prep support (`7064293`)
✓ docs appendix/support material — formal defense cleanup and reproducibility appendix added (`2e8de29`)
✓ CI/test hygiene — whitespace fix, formatter pass, API upload scaler-contract alignment, Windows-safe relative `--basetemp` (`b56c79c`, `38bdd4b`, `8ff925d`, `dfdd44c`)
✓ Ch6 threshold explanation — conservative operating thresholds clarified; not clinical/statistical guarantees (2026-05-13)
✓ Abstract/Ch6/Ch7/Ch8 wording sweep — active thesis files softened around production readiness, deployment, clinical validity, and broad generalisation (2026-05-13)
✓ Ch7 dense evidence-map table simplified — overview now shows evidence role and claim boundary, detailed metrics remain in sections (2026-05-13)
✓ Ch5/Ch7/Ch8 pipeline-centering sweep — ABC/model artifacts reframed as supporting runtime-contract diagnostics, not the thesis centerpiece (2026-05-13)
✓ PDF rebuilt after 2026-05-13 wording/pipeline-centering sweep — 116 pages, fallback pdflatex/bibtex path completed successfully
✓ docs/MASTER_THESIS_FINISH_TODO_MAY_JUNE_2026.md — updated 2026-05-12
```

---

## P0 — Must Fix Before Submission / Defense

These are blocking. Any one of them unresolved makes the PDF or defense unsafe.

---

### P0-01 — Fix Ch4 Scaler Contradiction *(NEW — PDF review)*

**Status:** DONE — commit `9bdbaae` fix(ch4): align scaler and parameter wording with Model A contract  
**Source:** `thesis/chapters/ch4_data_model_development.tex`, lines 200–205 and preprocessing Table 4.x

**Problem:**
Ch4 "Normalization State" section currently says:
> "The defended final production path does not apply an external StandardScaler. After accelerometer unit conversion, the model receives raw physical IMU units. The train-only scaler artifact remains in the repository for model-development, leakage checks, and controlled A/B diagnostics, but it is not a final production inference dependency."

The preprocessing table also shows Normalization as **Disabled**.

This directly contradicts:
- `thesis/chapters/ch5_pipeline_implementation.tex` — Section "Train-Only Scaler with Persisted Verification"
- `docs/MODEL_DECISION_2026-05.md` — Final input contract explicitly includes the Garmin train-only StandardScaler
- `docs/THESIS_CONSISTENCY_NOTES.md` — Section 5.1 canonical sentence: "the saved Garmin train-only StandardScaler is applied from `garmin_train_scaler.json`"
- `docs/EVIDENCE_KIT_INDEX_2026-05.md` — Model A contract row
- The defended runtime: unit conversion → Garmin train-only scaler → windowing → Model A

**Fix required in Ch4:**
Replace the normalization state paragraph with text that matches the final defended contract:
- Unit conversion (milliG → m/s²) is applied when needed.
- The Garmin train-only StandardScaler (persisted, SHA-256 verified) is then applied before windowing.
- The scaler is fit only on Garmin training-set windows; validation and User 7 are excluded from the fit.
- This is NOT the same as fitting a scaler on each inference batch or on the full evaluation dataframe.
- Update the preprocessing table: Normalization row should read "Enabled — Garmin train-only StandardScaler, fit on training set only, applied before windowing."
- Do NOT use "production path" or "production inference dependency" — use "defended runtime path" and "defended proof-of-concept runtime dependency".

**Time:** 1–2 hours  
**Suggested commit:** `fix(ch4): correct normalization state for defended PoC runtime contract`

---

### P0-02 — Fix Ch4 Architecture Parameter Count *(NEW — chapter audit)*

**Status:** DONE — commit `9bdbaae` fix(ch4): align scaler and parameter wording with Model A contract  
**Source:** `thesis/chapters/ch4_data_model_development.tex`, architecture section

**Problem:**
Ch4 describes the 1D-CNN+BiLSTM architecture and states "Total trainable parameters: 499,131". This matches Models B and C (the legacy/full architecture). Model A has 87,083 parameters (5.7× smaller), as stated in `docs/FINAL_THESIS_CLAIMS_2026-06.md` (claim C-06) and `docs/MODEL_ABC_MENTOR_BRIEF_2026-05.md`.

Ch4 does not explain the relationship between the described architecture (499,131 params) and Model A (87,083 params).

**Fix required:**
- Add a short clarifying note in Ch4 architecture section stating: The chapter describes the full baseline CNN-BiLSTM architecture (499,131 params) inherited from the ADAMSense pretraining route. Model A (the defended proof-of-concept runtime candidate) uses a fine-tuned variant with 87,083 parameters; the full ABC parameter comparison is reported in Chapter 7.
- Alternatively, update the parameter count to 87,083 and explain the smaller fine-tuned variant is Model A.
- Verify which is more accurate by checking Model A's actual layer config.

**Time:** 1–2 hours  
**Suggested commit:** `fix(ch4): clarify architecture parameter count — Model A is 87,083 params vs 499,131 for full baseline`

---

### P0-03 — Clarify Ch7 Baseline Reference Model *(NEW — chapter audit)*

**Status:** DONE — commits `0e2c23e` (Synth Other correction + 98.9% attribution clarified) and `b404300` (ABC section + explicit model role distinction)  
**Source:** `thesis/chapters/ch7_experiments_evaluation.tex`, Section "Baseline Reference on Labeled Data"

**Problem:**
Ch7 "Baseline Reference on Labeled Data" uses `har_model_20260327_223917.keras` and reports 98.9% accuracy on 3,852 labeled windows. This is a different model from Model A (the defended proof-of-concept runtime candidate, which achieves 42.4% on all_users and 37.6% on User 7). Without explicit clarification, an examiner reading Ch7 could believe Model A achieves 98.9%.

**Fix required:**
- Add a sentence explicitly stating that `har_model_20260327_223917.keras` is the original baseline deployment model used for the preprocessing ablation and labeled reference experiments, and is distinct from Model A (the defended proof-of-concept runtime candidate selected in the May 2026 model sprint).
- Reference the runtime contract check section for Model A's actual numbers.
- Make clear the two models serve different roles in the chapter.

**Time:** 1 hour  
**Suggested commit:** `fix(ch7): clarify baseline reference model is not Model A — add explicit note`

---

### P0-04 — Update Title Page Date *(NEW — PDF review)*

**Status:** DONE — updated to "Siegen, 15 June 2026" in `thesis/main.tex` (submission date confirmed by user)  
**Source:** `thesis/main.tex`, line 49 — previously said "Siegen, 19 April 2026"

**Time:** 15 minutes  
**Suggested commit:** `fix(main.tex): update title page submission date`

---

### P0-05 — Strengthen Chapter 2 Background and Related Work *(NEW — PDF review)*

**Status:** DONE — commits `64b1f27` (BFRBs paragraph, anchor sentence, recognition-layer synthesis) + `74d107e`  
**Source:** `thesis/chapters/ch2_background_related_work.tex`

**Current state:** Ch2 has 5 sections, a synthesis table (10 studies), and a gap-positioning conclusion. The structure is sound. However the PDF review flagged the chapter as "too weak/small" — likely the issue is depth and synthesis rather than structure.

**Fix required:**
- Audit each of the 5 sections for paragraph depth. Thin sections should be expanded with 1–2 additional cited findings.
- The synthesis table is already good; ensure it is referenced from the main text with specific cross-pointers.
- The gap paragraph (final paragraph) is strong; ensure the 4-item gap (HAR + MLOps + wearable HAR lifecycle + this thesis) is unambiguous.
- Consider adding a mini-summary paragraph at the end of the 3 longer sections that synthesizes what the section contributes to the thesis gap argument.
- Check total word/page count and compare with HAR thesis norms (Ch2 should be at least 15–20 pages).

**Time:** 4–6 hours  
**Suggested commit:** `docs(ch2): deepen background sections and synthesis — add cited findings and section summaries`

---

### P0-06 — Strengthen Ch3 Offline Architecture Explanation *(NEW — PDF review)*

**Status:** DONE — commit `74d107e` (stage roles, concrete session example, "scalable" anchor sentence)  
**Source:** `thesis/chapters/ch3_offline_mlops_architecture.tex`

**Current state:** Ch3 covers design goals, execution views, core vs. conditional pipeline, artifact lineage, and offline-first boundary. The pipeline architecture figure is referenced but the chapter may be too brief to stand on its own.

**Fix required:**
- Expand "Execution Views" to explain the Stage 1–7 operational path in more concrete terms (what each stage does, what artifact it emits).
- Add a data flow description for a typical session: input files → ingestion → validation gate → preprocessing → inference → monitoring → trigger output.
- Ensure the distinction between "core runtime" and "governed mutation branch" is explained using a concrete example (e.g., what happens on the Garmin unlabeled session run).

**Time:** 3–4 hours  
**Suggested commit:** `docs(ch3): expand architecture explanation — data flow, stage roles, concrete run example`

---

### P0-07 — Rebuild PDF After Fixes and Verify *(previously P0-06)*

**Status:** DONE — multiple clean builds on 2026-05-12; passes with no undefined references and the previously open P0-03/P0-04 items were later closed the same day.  
**Source:** `thesis/build_thesis.ps1`

After P0-01 through P0-06 are fixed, rebuild the PDF:

```text
thesis/build_thesis.ps1
```

Verify:
- No undefined references
- No blank sections  
- Figures and tables visible
- ToC / LoF / LoT updated
- Title page date is correct submission date
- Scaler wording in Ch4 matches Ch5 and MODEL_DECISION
- Architecture parameter note in Ch4 is consistent with Ch7 ABC numbers
- Ch7 baseline reference model is explicitly distinguished from Model A
- Abstract wording: no "production-grade", "production-ready", or "population-level generalisation" claims

**Time:** 3–5 hours  
**Suggested commit:** `build: rebuild thesis PDF after Ch4 scaler fix, architecture note, title page date update`

---

### P0-08 — Verify Font and PDF Visual Appearance *(NEW — PDF review)*

**Status:** DONE — clean build on 2026-05-12: 113 pages, no undefined references, no missing figures, no missing citations. Latin Modern vector fonts confirmed. Only cosmetic Overfull/Underfull hbox warnings remain (acceptable for academic LaTeX).  
**Source:** `thesis/main.tex`, PDF output

PDF review flagged font and visual appearance as "weak or broken."

Check:
- LaTeX font package is consistent (T1 encoding, main font, math font)
- Page margins, line spacing, section heading styles are uniform
- No artifacts from repeated `pdflatex` runs (stale `.aux`/`.toc` files)
- Run a full clean build (`pdflatex` × 3 + `bibtex`) and inspect page 1, chapter pages, and table of contents pages

**Time:** 2–3 hours  
**Suggested commit:** No code change; document findings and apply LaTeX fixes if needed.

---

### P0-09 — Update Defense Q&A *(previously P0-07)*

**Status:** DONE — complete rewrite committed `4a571d3`; 10-section structure, numbers table, all wording rules enforced  
**File:** `internal/writing/defense_qa.md` (create if missing)

Update for:
- Runtime contract (Model A, clean PoC, 87,083 params)
- Scaler policy (train-only, persisted) — must now be consistent with Ch4 fix
- Runtime contract check and why Model A was chosen
- Monitoring and trigger behavior (CRITICAL ≠ auto-retrain)
- auto_retrain=false governance
- Self-recorded Garmin evaluation (what it proves and what it does not)
- Domain shift / low accuracy explanation
- Ch4 architecture vs. Model A parameter count question (prepare for examiner)
- Limitations

**Time:** 3–4 hours  
**Suggested commit:** `docs: update defense Q&A with Model A contract and Ch4 fixes`

---

### P0-10 — Build Defense Slides *(previously P0-08)*

**Status:** DONE — finalized into `internal/writing/defense_slides.pptx`; the outline remains the source script/document for the committed deck  
**Target:** 15–20 slides

| Slide | Topic |
| ---: | --- |
| 1 | Title |
| 2 | Problem statement and research questions |
| 3 | Why MLOps for wearable HAR |
| 4 | Full pipeline overview (Stage 1–11) |
| 5 | Stage 1–7 operational path |
| 6 | Stage 8–11 gated extensions |
| 7 | Dataset and 11 classes |
| 8 | Final runtime/model contract (Model A, scaler, contract) |
| 9 | Model architecture (87,083 params — Model A) |
| 10 | Runtime contract check — one slide |
| 11 | Main evaluation results |
| 12 | Monitoring and drift behavior |
| 13 | Trigger governance — REVIEW, no auto-retrain |
| 14 | External Garmin evaluation |
| 15 | What low accuracy means (domain shift, honest pipeline) |
| 16 | Limitations |
| 17 | Future work |
| 18 | Contribution summary |
| 19–20 | Backup Q&A slides |

**Time:** 10–14 hours  
**Suggested commit:** `docs: add defense slides first draft`

---

### P0-11 — Create Demo Runbook *(previously P0-09)*

**Status:** DONE — created `internal/writing/demo_runbook.md` with exact commands, expected output per stage, model contract verification step, fallback script, numbers table, and "What NOT to claim" section  
**File:** `internal/writing/demo_runbook.md`

Include:
- Exact commands (python run_pipeline.py, docker compose, curl)
- Expected output at each stage
- Where evidence is saved
- What to say if demo is slow or fails
- What not to claim

**Time:** 4–6 hours  
**Suggested commit:** `docs: add defense demo runbook`

---

### P0-12 — Repo Cleanup Wave *(previously P0-10)*

**Status:** open — do not start before P0-07 (PDF rebuild) is done  

Archive candidates (move to `_archive/`, do not delete):

```text
Root noise: analyze_alluser_transitions.py, analyze_predictions.py, analyze_user7_timestamps.py
Root noise: COMPARATIVE_ANALYSIS_2026-05-08.md, temp.txt, reasoningtxt.txt, pt.md
Root noise: stage1_7_run_20260508_213835.log, tmp_run3/
Root noise: dataset_comparison_analysis.ipynb
docs/: old April planning docs (DRIFT_INVESTIGATION, COMPONENT_IMPROVEMENT_REVIEW, etc.)
reports/: _smoke_29_*.csv, _tmp_*.csv, older sprint reports
6th may/ folder — archive after ABC evidence is committed
old notebooks: nb/processing.ipynb, nb/gpt.ipynb
```

Do not delete `docs/MODEL_ABC_COMPARISON_2026-05.md` yet — check if any thesis chapter cites it first.

**Time:** 6–10 hours  
**Suggested commit:** `chore: archive root noise and old planning docs`

---

## Next Priority (current real open block as of 2026-05-12 evening)

All thesis/defense P0 content items are done. The remaining work is now curation, packaging, and one unresolved evidence decision.

1. **ABC evidence decision** — review the dirty `reports/abc_comparison/` outputs that remove `all_users_diagnostic`; either commit this narrowed two-dataset bundle intentionally or revert it before final sharing.
2. **P0-12** — Repo cleanup audit-to-action wave: only after the evidence bundle and wording are stable.

---

## P1 — Important Quality Improvements

Not all defense-blocking, but significantly improve quality.

---

### P1-01 — Figure and Visual Redesign *(NEW — PDF review)*

**Status:** DONE — commit `4808e14`; five thesis-quality figures created (fig_05, fig_08, fig_10, fig_ch6, fig_ch7)

PDF review found all figures are notebook-style screenshots, not thesis-quality visuals. Priority redesign targets:

| Figure | Current state | Needed |
| --- | --- | --- |
| Pipeline architecture diagram | Placeholder / notebook screenshot | Clean vector diagram showing Stage 1–7 + 8–10 split |
| Stage 1–7 operational flow | Missing or weak | Step-by-step labeled flow with stage names and artifacts |
| ABC model-contract comparison | Table only | Visual bar chart or annotated comparison figure |
| Confidence/uncertainty chart | Missing | Chart showing mean confidence across datasets |
| Trigger governance state machine | Missing | State diagram: HEALTHY → WARNING → CRITICAL → REVIEW |
| Dataset split / evidence role diagram | Missing | Shows which data goes to training vs. evaluation |
| Ch4 channel distribution figures | Exist (PDF) | Check they render correctly in the PDF |

**Time:** 8–16 hours (total across figures)  
**Suggested commit:** `fig: replace notebook-style figures with thesis-quality vector diagrams`

---

### P1-02 — Simplify Dense Tables or Move to Appendix *(NEW — PDF review)*

**Status:** DONE — 2026-05-13 Ch7 evidence-map table simplified; no appendix move needed for this pass.

Several tables are dense and may overwhelm the reader. Candidates:
- Ch4 channel statistics table (`ch4_channel_statistics.tex`) — consider moving to appendix
- Ch7 ABC full metrics table — ensure only key rows appear in body; full confusion matrices in appendix
- Evidence kit index table in Ch7 — verify it isn't duplicating Ch4 data table

**Time:** 3–4 hours  
**Suggested commit:** `tex: simplify dense tables — move full stats to appendix, keep summary in body`

---

### P1-03 — DVC Reproducibility Clarification *(previously P1-01)*

**Status:** DONE — README and Ch5 now state the defended DVC boundary clearly.

Write clearly what DVC is used for in this thesis:

```text
DVC is used for artifact and data versioning.
Pipeline orchestration is handled by run_pipeline.py.
dvc repro is not configured for the full pipeline in this thesis version.
```

**Time:** 2–4 hours

---

### P1-04 — Threshold and Trigger Justification *(previously P1-02)*

**Status:** DONE — 2026-05-13 active thesis sweep

Document the monitoring thresholds in one place (already in `config/pipeline_overrides.yaml`). Write a short thesis paragraph for Ch6 explaining:

```text
Why confidence_warn=0.70
Why uncertain_pct=20%
Why dominant_class_warn=85%
Why these thresholds are not calibrated; they are conservative defaults
```

Final wording added in Ch6:
- `confidence_warn_threshold=0.70` and `uncertain_pct_threshold=20%` are conservative operating thresholds for surfacing low-decisiveness batches.
- Dominant-class warning/critical thresholds catch high-confidence class collapse that confidence alone can miss.
- These values are not clinical limits, statistical guarantees, or validated wearable-HAR constants.

---

### P1-05 — Bibliography Cleanup *(previously P1-05)*

**Status:** DONE — commit `0f0f92a`

Target was 55–65 strong references with less padding and clearer thesis relevance. This cleanup landed together with wording softening around the BFRB scope.

**Time:** 5–8 hours

---

### P1-06 — README Consistency Update

**Status:** DONE

Verify README uses only proof-of-concept language for Model A, correct scaler wording, and no "production-grade" or "production-ready" claims.

**Time:** 1–2 hours  
**Suggested commit:** `docs(readme): align Model A description and scaler wording with final contract`

---

### P1-07 — Stage 11 Calibration Wording *(previously P1-07)*

Recommended framing: calibration is implemented as an optional uncertainty extension but final fitted calibration is left as future work because available labeled external data are insufficient for reliable post-hoc calibration.

**Time:** 1–2 hours

---

### P1-08 — CI Smoke Workflow *(previously P1-09)*

Drop the `-m "not slow and not integration"` filter from CI unit-tests job so all 240 tests run. Deferred until test cleanup is settled.

**Time:** 2–3 hours

---

## P2 — Optional Polish

Do not start these until P0 and main P1 tasks are safe.

- Model A improvement: calibration, higher-capacity variant, weak-class retune
- Stage 8–10 retraining demo with labeled data
- Stage 11 calibration/UQ finalization
- Optional model comparison sweep (CNN-GAP, CNN-GRU)
- Notebook hygiene: mark canonical, archive old
- Ingestion ordering hygiene: verify session selection is by filename/timestamp, not file modified time

---

## Archive / No Longer Defended

```text
docs/MODEL_ABC_COMPARISON_2026-05.md  — superseded by mentor brief + abc_comparison reports
                                        keep until no thesis chapter cites it, then archive
old "production-grade" / "production-ready" wording anywhere in docs
May 9/10 calendar items — completed or superseded
"Use Model B if production-safe" framing — resolved: Model B is diagnostic reference only
```

---

## Do Not Touch

```text
reports/abc_comparison/            — all evidence files, committed
models/model_registry/             — 3 contract JSONs
models/production_contract/model_a_final_20260508/  — frozen model package
src/config.py                      — Model A runtime config
tests/                             — 240 passing tests
```

No retraining. No contract changes until defense is over.

**Protected unless audited:**

```text
config/pipeline_config.yaml        — runtime config
config/pipeline_overrides.yaml     — monitoring thresholds (threshold parity still needs manual review)
```

---

## Figure and Visual Redesign Board

| Priority | Figure | Status | Chapter |
| --- | --- | --- | --- |
| P0 | Pipeline overview (Stage 1–7 + 8–10 split) | DONE | fig_05_core_vs_conditional_pipeline |
| P1 | Stage 1–7 operational flow with artifacts | DONE | fig_05_core_vs_conditional_pipeline |
| P1 | ABC model-contract comparison | DONE | fig_ch7_abc_comparison |
| P1 | Mean confidence across datasets | P2 polish only | Ch7 |
| P1 | Trigger governance state machine | DONE | fig_ch6_monitoring_governance |
| P1 | Trigger policy comparison | DONE | fig_08 fixed x-axis |
| P1 | Old vs new model comparison | DONE | fig_10 with control rerun |
| P1 | Dataset split / evidence role | P2 polish only | Ch4 |
| P2 | Ch4 channel boxplots / mean / std | exists (PDF) | Ch4 |
| P2 | Preprocessing flow diagram | exists (PDF) | Ch4 |

---

## Thesis Writing Board

| Item | Chapter | Status | Blocker |
| --- | --- | --- | --- |
| Fix scaler contradiction in Normalization State section | Ch4 | DONE | none |
| Fix preprocessing table — Normalization row | Ch4 | DONE | none |
| Fix architecture parameter count / Model A note | Ch4 | DONE | none |
| Clarify Ch7 baseline reference model vs. Model A | Ch7 | DONE | none |
| Update title page date | main.tex | DONE | none |
| Deepen Ch2 background sections | Ch2 | DONE | none |
| Expand Ch3 offline architecture explanation | Ch3 | DONE | none |
| Abstract — verify no stale wording | main.tex | DONE | swept 2026-05-13 |
| Threshold justification paragraph | Ch6 | DONE | conservative operating thresholds clarified |
| Dense table simplification / appendix move | Ch4/Ch7 | DONE | Ch7 evidence-map table simplified |
| Bibliography cleanup | refs | DONE | none |
| Defense Q&A | internal/ | DONE | none |
| Demo runbook | internal/ | DONE | none |
| Defense slides | internal/ | DONE | none |

---

## PDF / Build Board

| Item | Status | Notes |
| --- | --- | --- |
| First PDF build | DONE | Build passes; not submission-ready |
| Ch4 scaler fix → rebuild | DONE | Clean rebuild completed |
| Font and visual appearance check | DONE | Latin Modern confirmed; only cosmetic hbox warnings remain |
| Undefined reference check | DONE | Clean build reported no undefined references |
| 2026-05-13 wording/pipeline-centering rebuild | DONE | 116 pages; `latexmk` missing Perl, fallback `pdflatex`/`bibtex` completed |
| Final PDF submission build | PENDING | Final supervisor feedback and evidence-bundle decision only |

---

## Repo Cleanup Board

| Item | Status | Notes |
| --- | --- | --- |
| Root noise files (analyze_*.py, temp.txt, reasoningtxt.txt) | P0-12 open | Do not start before PDF rebuild |
| docs/ old April planning docs | P0-12 open | Archive, not delete |
| reports/ smoke and tmp files | P0-12 open | Archive |
| 6th may/ folder | P0-12 open | Archive after final ABC evidence decision/commit |
| Old notebooks | P2 | Low priority |

---

## Current Working Tree Note

Uncommitted as of 2026-05-12 evening:

- `reports/abc_comparison/ABC_MODEL_COMPARISON_REPORT_2026-05-11.md`
- `reports/abc_comparison/abc_results.csv`
- `reports/abc_comparison/abc_results.json`
- `reports/abc_comparison/comparison_summary.json`
- `reports/abc_comparison/contract_runtime_verification.json`
- `reports/abc_comparison/dataset_validation_summary.json`
- `docs/REPO_CLEANUP_CANDIDATES_2026-05.md`

Interpretation:
- The ABC bundle appears to have been regenerated in a narrower two-dataset mode, removing `all_users_diagnostic` from the active output set while keeping User 7 and Garmin as the primary evidence.
- This is potentially a good final-defense simplification, but it is not yet committed and should be treated as a pending decision, not as finished evidence.
- The cleanup-candidates document is an audit only. No archive move has happened yet.

---

## Final May–June Calendar (revised)

### May 12–17

```text
✓ Ch2/Ch3 strengthened
✓ Ch4/Ch7 contradictions fixed
✓ Figures improved
✓ PDF rebuilt
✓ Defense Q&A done
✓ Slides first draft done
✓ Demo runbook done
→ Finish bibliography/DVC/README cleanup
→ Final slide QA pass
→ Mock defense 1
```

### May 18–24

```text
→ Dense table cleanup if needed
→ Repo archive cleanup
→ Final PDF visual pass
→ Mock defense 2
→ Supervisor feedback integration
```

### May 25–31

```text
→ Final PDF polish
→ Final slides polish
→ Demo rehearsal
→ Submission formatting
```

### June

```text
→ Final PDF polish
→ Slides polish
→ Demo rehearsal
→ Supervisor feedback fixes
→ Submission formatting
```

Do not change the model story or evidence in June unless supervisor explicitly requires it.

---

## Final Defense Story

> The thesis does not claim a perfect or universally generalizable HAR model. It contributes an offline-first MLOps pipeline for wearable IMU-based human activity recognition, where ingestion, validation, transformation, inference, monitoring, and trigger evaluation are reproducible and governed. The self-recorded Garmin evaluation exposed domain shift, and the pipeline correctly avoided unsafe automatic retraining from weak or unlabeled evidence.

The final runtime contract is:  
**milliG → m/s² unit conversion (when needed) → Garmin train-only StandardScaler → row-wise windowing → Model A inference**

---

## Definition of Done

```text
pytest is green (currently 240/240)
Ch4 normalization state matches Ch5 and MODEL_DECISION (scaler contradiction resolved)
Ch4 architecture section correctly describes Model A parameter count (87,083)
Ch7 baseline reference model is explicitly distinguished from Model A
Title page date is the actual submission date
Fresh thesis PDF builds from source with no undefined references
One final model contract is stated consistently across Ch4, Ch5, MODEL_DECISION, and THESIS_CONSISTENCY_NOTES
Model A is identified as defended proof-of-concept runtime candidate in code, thesis, slides, and demo
Evidence kit index maps each artifact to a thesis claim
Self-recorded Garmin evaluation is honestly explained as a single-participant external test
Defense slides answer the main examiner questions
Demo runbook works from clean shell
Stale docs are archived or marked historical
README, thesis, slides, and defense Q&A tell the same story
Font and PDF visual appearance checked and confirmed clean
```

> By end of May, the thesis should be technically frozen and PDF-ready.
> June is writing polish, supervisor feedback, slides, and rehearsal only.

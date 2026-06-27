# Defense Deck Blueprint — 19 Main Slides + 9 Backups
**Defense:** M.Sc. Mechatronics, University of Siegen — 30 June 2026
**Audience:** Prof. Dr.-Ing. Roman Obermaisser (1st), M.Sc. Ugonna Oleh (2nd — author of your benchmark paper [10])
**Talk length target:** ~20 minutes (≈ 1 slide/min + title + close), then Q&A from backups.
**Single source of truth for every number: the thesis PDF (main.pdf, 5 June build) — NOT the GitHub README.**

---

## ⚠️ READ FIRST — Repo/Thesis mismatch (fix before the defense)

Your public README (last updated 26 Feb 2026) contradicts the defended thesis. The examiners *will* open the repo — you literally gave them an "Examiner Quickstart." Conflicts that must not leak into the deck, and should be fixed in the README:

| README (Feb 2026, stale) | Thesis (June 2026, defended) |
|---|---|
| "14-stage pipeline", `--advanced` flag | **Stages 1–7 assessment + 8–10 governed mutation + optional S11** |
| "~499K trainable parameters, v1" | **Model D1: 967,499 parameters (966,347 trainable)** |
| "val_acc 0.969, F1 0.814" | **5-fold 93.61% / macro-F1 0.937; LOUO 44.42%; blind probe 36.96%** |
| "225/225 tests passing" | Use the *current* count from `pytest tests -q` on the defended tag |
| Trigger outputs "RETRAIN / ADAPT_ONLY / NO_ACTION" | **none / monitor / review / queue_retrain, should_retrain=false** |
| "Domain Adaptation: AdaBN / TENT / Pseudo-label ✅ Complete" | **Excluded from the defended runtime** under the no-auto-retrain policy (§8.4) |
| "26 recording sessions" | **25 unlabeled sessions** evaluated (Fig. 7.5) |
| Prometheus/Grafana "config ready" | **Explicitly outside defended scope** (§6.5) |
| Temperature calibration "✅ Complete" | **S11 optional extension, not the defended runtime** |

**Action:** sync README to the defended state (or add a banner: "README describes the development history; the defended system is specified in the thesis, tag `v1.0-thesis`"). Every slide below uses thesis numbers only.

**Also before building:** regenerate Figure 7.3 (broken legend) and fix Figure 3.2's folder name (`20260528`) — both figures appear in this deck.

---

## Design system (consistent across all slides)

- **Canvas:** 16:9, 1920×1080. Dark premium: background `#0E1116`, panel `#161B22`, text `#E6EDF3`, muted `#8B949E`.
- **Accents:** teal `#2DD4BF` = assessment/safe; amber `#F59E0B` = warning; red `#EF4444` = critical/risk; violet `#8B5CF6` = governance/mutation path.
- **Fonts:** Inter or Source Sans 3; titles 36–40 pt bold, body 20–24 pt, numbers 64–96 pt. Max ~25 words of body text per slide — you speak the rest.
- **Footer:** slide number + "Vachheta — Offline-First MLOps for Wearable HAR — 30.06.2026".
- **Animation policy (German engineering defense = sober):** only **Fade/Appear** for staged builds and **Morph** for diagram evolution between consecutive slides. Duration 0.3–0.4 s. Nothing flies, spins, or bounces. Every build is triggered on-click so you control pacing.

---

# MAIN DECK

---

### Slide 1 — Title (0:30)
**Layout:** Title centered; thin teal rule; meta block bottom-left; small pipeline glyph watermark right.
**Content (verbatim):**
- Developing an MLOps Pipeline for Continuous Mental Health Monitoring Using Wearable Sensor Data
- *An Offline-First, Governed Lifecycle for Wearable Human Activity Recognition*
- Shalin Vachheta · Matriculation 1701359
- M.Sc. Mechatronics · Chair of Embedded Systems · University of Siegen
- 1st Supervisor: Prof. Dr.-Ing. Roman Obermaisser · 2nd Examiner: M.Sc. Ugonna Oleh
- Siegen, 30 June 2026
**Animation:** none (static).
**Speaker notes:** Greet; one sentence: "This thesis asks what it takes to *operate* — not just train — a wearable activity-recognition model in a mental-health context, and answers it with a reproducible, governed pipeline and an honest evaluation."
**Note:** the subtitle line quietly performs the title-scope correction in print before anyone asks.

---

### Slide 2 — What this thesis is — and is not (1:00)
**Layout:** two columns. Left (teal check icons) "Defended claim"; right (red ✕ icons) "Explicitly out of scope". Bottom strip: one-line definition.
**Content:**
- ✓ Recognizes **observable anxiety-related behaviors** (nail biting, hair pulling, scratching, tapping, rubbing…) from wrist IMU data
- ✓ A **reproducible, monitored, governed MLOps lifecycle** around that model — offline-first, auditable
- ✓ "Continuous mental health monitoring" = the **application context** of the fixed title
- ✕ No diagnosis, no prognosis, no clinical validity claim
- ✕ No on-device / real-time / cloud deployment claim
- ✕ No automatic retraining — ever, by policy
- Bottom strip: *Behavioral proxy = an observable action standing in for an internal state that cannot be sensed directly (§1.1).*
**Animation:** left column fades in as a block (click 1), right column (click 2), bottom strip (click 3).
**Speaker notes (script the title answer here, 45 s):** "The title was fixed at registration. The thesis converts it into a bounded engineering claim: the system recognizes behavioral proxies; clinical interpretation stays with humans. Defining and enforcing that boundary is itself Contribution 5."
**Preempts:** Danger question #1 (title).

---

### Slide 3 — The problem: a trained model is not a trustworthy system (1:15)
**Layout:** three stacked horizontal bands, each with icon + label + one line.
**Content:**
1. **Technical** — same tensor shape ≠ same meaning: units, channel order, scaler, gravity handling, sampling can silently change the input (§1.2)
2. **Operational** — at inference time, **labels are unavailable**: accuracy cannot be computed; only proxy signals exist
3. **Governance** — retraining on a model's own unlabeled predictions can **amplify** errors (confirmation bias); a risky batch ≠ permission to mutate
- Footer line: *Failure mode to fear: dominant-class collapse — most windows → one class, with high confidence.*
**Animation:** bands appear top→bottom (3 clicks); footer line last, in red.
**Speaker notes:** "Three layers of failure, and only the first one is visible in a notebook. The other two define this thesis."

---

### Slide 4 — Research questions (0:45)
**Layout:** 4 numbered cards, 2×2 grid.
**Content (compressed but faithful):**
- **RQ1** Can an offline-first pipeline detect operational risk **without labels**?
- **RQ2** How strongly do preprocessing & train–serve **contract choices** shape recognition behavior?
- **RQ3** Is a **governed trigger policy** safer than unrestricted automatic retraining?
- **RQ4** Are collapse/degradation patterns caused by the **contract/model** — or by the **data**?
**Animation:** all four appear together (1 click) — don't waste clicks here.
**Speaker notes:** 10 s each; say RQ2 in the "how strongly" form (this matches the fixed thesis wording after your revision).

---

### Slide 5 — Related work in one breath → the gap (1:00)
**Layout:** 5 thin rows (strand → what it gives → what it lacks), then a highlighted gap banner. This is Table 2.2 compressed.
**Content:**
- Wearable mental-health sensing [3,4,6] → motivation → little pipeline-level operationalization
- Anxiety-behavior HAR: **ADAMSense** [9], **Garmin 1D-CNN-BiLSTM** [10] → feasibility → not integrated with a governed lifecycle
- Deep HAR [29,30,1] → models → model-centric, no deployment governance
- Domain shift / device heterogeneity [40,12,13] → why models degrade → rarely tied to runtime contracts
- MLOps [15,16,17,42] → lifecycle discipline → not specific to wearable health-adjacent HAR
- **Gap banner (violet):** *No bounded, offline-first MLOps lifecycle that binds wearable HAR model + preprocessing contract + monitoring + retraining governance into one auditable system.*
**Animation:** rows fade as one block (click 1); gap banner (click 2).
**Speaker notes:** Name-drop [10] deliberately: "…including the Garmin study by Oleh and Obermaisser, which this thesis builds on directly." (Respectful nod to the examiner; also frames the benchmark comparison you'll make on Slide 13.)

---

### Slide 6 — Solution architecture: observe everywhere, mutate nowhere (1:30)
**Layout:** rebuilt Figure 3.1. Top lane (teal): S1 Ingestion → S2 Validation → S3 Transformation → S4 Inference → S5 Evaluation → S6 Monitoring → S7 Trigger Decision. Below: **Governance Gate** (labels + review + validation evidence). Bottom lane (violet): S8 Retraining → S9 Registration → S10 Baseline Update. Side chip: S11 Calibration/Uncertainty — *optional, not the defended runtime*.
**Content (labels only, no sentences).** Caption: *Stages 1–7 run on every session and never mutate the model. Stages 8–10 open only through the gate.*
**Animation:** teal lane builds left→right (one click per pair of stages = 4 clicks, or one click for the lane if you prefer pace); gate appears (click) with a "lock" icon; violet lane fades in dimmed (click); S11 chip last.
**Speaker notes:** "The architecture is the thesis in one picture: assessment and mutation are different paths, and severity alone can never cross the gate."
**Preempts:** sets up RQ3.

---

### Slide 7 — The runtime contract is the deployment unit (1:30)
**Layout:** **Morph from Slide 6** — zoom into a folder card: `models/runtime_contract/model_d1_final_20260528/`. Inside, 7 file chips; right side, the tuple.
**Content:**
- File chips: `model (.keras + SavedModel)` · `garmin_train_scaler.json/.joblib` · `label_order.json` · `garmin_train_scaled_baseline.json` · `model_contract.json` · `artifact_md5.json` · `evaluation evidence (User-7 summaries)`
- Big formula: **C_D1 = (M, S, L, B, Ω)** — model, train-only scaler, fixed 11-label order, monitoring baseline, preprocessing/windowing metadata
- Three-row mini-table (same-folder invariant, Table 3.3): coherent → **accept** · stale path but match inside → **correct + warn** · no compatible artifact → **fail fast**
**Animation:** Morph transition (folder grows from the S10 box); chips appear as one block; tuple highlights teal; invariant rows appear one per click (3 clicks: green/amber/red).
**Speaker notes:** "A model file alone is meaningless. The scaler is fitted only on Garmin users 1–6 and never refitted — refitting on incoming data would silently move the feature space. Promotion means promoting this whole folder, hash-verified by `artifact_md5.json`."
**Preempts:** Danger questions #5 (drift feature space — *state clearly which baseline file the drift check reads, per your fixed §6.2*) and #11 (why correct-and-warn instead of always fail: logged, exact-match-only, incompatibility still fails fast).

---

### Slide 8 — Data: four sources, four evidence roles (1:15)
**Layout:** 4 horizontal cards with role badges; small log-scale volume bar at right (Fig. 4.2 style).
**Content:**
- **ADAMSense** — 709,582 rows — *source-domain pretraining* [9]
- **Garmin users 1–6** — 385,326 rows → **3,755 windows** — *fine-tuning + 5-fold + LOUO design*
- **User 7 (self-recorded)** — 99,017 rows → **989 windows** — *blind external probe: excluded from training, scaler fitting, hyperparameter & model selection; evaluated once, post-freeze*
- **Unlabeled Garmin session(s)** — 632,700 rows (+ 25-session corpus) — *deployment-style monitoring; no accuracy claims possible*
- Strip: *Evidence boundary: labeled sources → accuracy/F1/confusion; unlabeled → monitoring & trigger evidence only (Table 7.1).*
**Animation:** cards appear one per click (4); boundary strip last.
**Speaker notes:** "The sources are deliberately not interchangeable — each may support only the claims its labels allow. This boundary is enforced through Chapter 7."
**Preempts:** Danger question #7 (User 7 = you): say proactively, "User 7 is self-recorded by me; the blindness is procedural — no development decision saw it — and its label-timing and demand-characteristic risks are stated in the limitations."

---

### Slide 9 — Preprocessing contract: raw CSV → (N, 200, 6) (1:00)
**Layout:** 8-step horizontal chevron flow (Fig. 4.5 rebuilt): Raw acc+gyro CSVs → Schema alignment → **Unit harmonization (milli-g → m/s², 1 milli-g = 0.00980665; gyro deg/s)** → 50 Hz alignment → Canonical order **Ax Ay Az Gx Gy Gz** → **Saved train-only scaler** → Sliding window **200 / stride 100 (4 s / 2 s, 50 % overlap)** → Tensor **(N, 200, 6)**.
**Content:** the chevrons; bottom rule: *Windows never cross a labeled activity or participant boundary; these are contract steps, not optional choices.*
**Animation:** chevrons wipe left→right as one build (1 click); the two red-outlined chevrons (units, scaler) pulse once on a second click.
**Speaker notes:** "Two steps cause silent disasters when wrong: units and the scaler. Both live in the contract."
**Preempts:** Danger question #12 (why deg/s, not SI rad/s → fidelity to the training convention of [9,10]; changing units = contract change).

---

### Slide 10 — Model D1: a deliberately standard recognizer (0:45)
**Layout:** left, block diagram (Fig. 4.6 rebuilt): Input (200×6) → 1D-CNN (local motion motifs) → BiLSTM (temporal context) → Dense → Softmax (11). Right, fact chips.
**Content chips:** **967,499 parameters** (966,347 trainable) · 11 fixed-order classes (ear_rubbing → standing) · fine-tuned from ADAMSense-pretrained base on Garmin 1–6 · augmentation (time-warp, magnitude-scale, jitter) **training-time only** · balanced class weights · *named D1 = first promoted runtime of preprocessing configuration D*.
**Animation:** diagram appears (click 1); chips as one block (click 2).
**Speaker notes:** "The architecture is not the contribution — it instantiates the family validated in the ADAMSense and Garmin studies. The contribution is everything wrapped around it." (Have the D-naming sentence ready — this is Danger question #3.)

---

### Slide 11 — Implementation: every claim maps to a file (1:15)
**Layout:** left, mini repo tree; center, vertical artifact-trail chain (Fig. 5.2 style); right, proof chips.
**Content:**
- Repo tree: `src/components/` (S1–S10 modules) · `config/` (YAML layering) · `models/runtime_contract/` · `scripts/` · `tests/` · `artifacts/<run_id>/`
- Artifact chain: `run_info.json → validation_report.json → transformation_metadata.json + production_X.npy → predictions → evaluation/monitoring reports → trigger_decision.json → pipeline_result_<run_id>.json`
- Proof chips: single entry point `run_pipeline.py` · contract tests (`test_runtime_contract_consistency.py`, `test_api_upload_modes.py`) · FastAPI serving the **same** contract · DVC + Docker for data & environment · **MLOps maturity: Level 1 — pipeline automation; Level 2 deliberately not claimed**
**Animation:** tree (click 1), chain top→bottom in one wipe (click 2), chips (click 3).
**Speaker notes:** "One command per claim — Appendix A is the runbook. The headline model numbers were produced in the version-controlled build notebook that *constructs* the runtime contract; the pipeline consumes that contract for everything downstream — every number in Chapter 7 maps to a file in Appendix C." (This sentence is Danger question #8, answered before it's asked.)

---

### Slide 12 — Evaluation design: four questions, four protocols (1:00)
**Layout:** 4-row table (Table 7.1 rebuilt), difficulty arrow on the left going down.
**Content:**
- 5-fold window-level CV → *can it learn the known distribution?* → optimistic by construction (scaler pre-split; same-user **and 50 %-overlapping** windows cross folds)
- Leave-one-user-out → *does it transfer to a new wearer?* → the deployment-relevant estimate (train-only scaler per fold)
- Blind User-7 probe → *frozen model on a truly unseen person?* → single descriptive measurement
- 25 unlabeled sessions → *can risk be detected without labels?* → monitoring & trigger evidence only
- Footer: *Nothing — architecture, hyperparameters, thresholds — was changed after seeing held-out or blind data (§7.1).*
**Animation:** rows one per click (4); footer last.
**Speaker notes:** "Each protocol answers a different question; reporting them as one number would be dishonest. Note I name all three optimism mechanisms in the five-fold myself." (Defuses Danger question #9 before the results appear.)

---

### Slide 13 — THE RESULT: the generalization cliff (1:45) ★ the money slide
**Layout:** full-width bar chart (Fig. 7.1 rebuilt): three protocol groups, accuracy + macro-F1(×100) pairs. Huge numbers above bars.
**Content:**
- 5-fold CV: **93.61 %** / 0.937 (folds 92.68–94.41 — stable)
- LOUO: **44.42 %** / 0.419
- Blind User 7: **36.96 %** / 0.350 — 95 % bootstrap CI [33.9, 39.8] (window-level, approximate under overlap)
- Annotation arrow across the drop: **“−49.2 points: the gap *is* the finding”**
- Footnote: 5-fold consistent with the published Garmin benchmark 87.0 % ± 1.2 % [10] — *protocol-family comparison; see backup B6 for caveats*
**Animation:** the dramatic moment of the talk — bars rise one protocol per click (wipe-from-bottom, 0.4 s): teal 93.6 first (pause: "the model learns the distribution"), amber 44.4 (pause), red 37.0; annotation arrow last (click 4).
**Speaker notes:** "I report the drop without inflation because it is the empirical justification for the whole pipeline: within-distribution accuracy is an insufficient basis for trusting a wearable HAR model. User 7 — never seen by any development decision — lands at 37 %."
**Preempts:** Danger question #6 — keep the benchmark sentence exactly as calibrated against [10]'s protocol; details live in B6.

---

### Slide 14 — The gap is per-person and structured (1:00)
**Layout:** left, per-user LOUO bar chart (Fig. 7.2): users 1–6. Right, three confusion arrows.
**Content:**
- Bars: U1 45.5 · **U2 5.7 (red)** · U3 50.5 · U4 53.8 · U5 50.0 · U6 61.1 — *mean 44.42 % (unweighted across users)*
- Right: errors are structured, not random (Fig. 7.4): nail biting → smoking · hand scratching → nape rubbing · standing → hair pulling; a few classes absorb most predictions
- Strip: *User 2 stays in the primary result — not excluded to inflate the mean.*
**Animation:** bars rise together (click 1); U2 pulses red (click 2); confusion arrows (click 3); strip (click 4).
**Speaker notes:** "A single wearer can collapse to 5.7 % under an identical, verified contract — that is exactly the failure the monitoring layer must surface, and it points to cross-user shift, not a broken pipeline." (This is your RQ4 chain — rehearse it here.)

---

### Slide 15 — Confidently wrong: the calibration gap (1:15)
**Layout:** left, the **regenerated** reliability diagram (Fig. 7.3 — fix the legend before export!); right, two giant numbers stacked.
**Content:**
- Right: **0.858** mean confidence ↑ vs **36.96 %** accuracy ↓ (blind probe)
- Reliability curve below the diagonal in the high-confidence bins; confidence histogram massed near 1.0
- Banner: *Dominant failure mode = high-confidence misprediction → a single confidence threshold passes a confident-but-wrong session silently.*
**Animation:** "0.858" lands first (click 1 — let it look good), "36.96 %" slams under it (click 2 — the laugh/wince beat of the talk), diagram fades in (click 3), banner (click 4).
**Speaker notes:** "This is why monitoring cannot be a confidence threshold. It motivates everything on the next slide."

---### Slide 16 — Monitoring + governance under fire: 25 real sessions (1:45)
**Layout:** top strip = signal → threshold chips; middle = Fig. 7.5 condensed (3 mini-panels: confidence, transition, drift) ; bottom = big outcome chips.
**Content:**
- Signal chips (Stage 6 warn): mean conf < 0.70 · uncertain-rate > 20 % · transition > 35 % · drift z > 1.8 · dominance 85/95 % — *Stage 7 stricter (0.65/0.50 · 0.35/0.50 · 2.0/3.0) + collapse guard + 24 h cooldown*
- Panels: confidence high everywhere (mean 0.83, all > 0.70) · transitions frequently > 35 % (mean 40 %) · drift mostly contained (mean z 1.18, **one critical excursion**)
- Outcome chips: **23 / 25 → review** · 1 monitor · 1 none · **0 / 25 retrains authorized** · `should_retrain = false` on every run
- Validation chip: same User-7 session, labeled vs unlabeled: **36.96 % vs 36.70 %**, conf 0.858 vs 0.846 → *unlabeled proxies track labeled truth* (Fig. 7.6)
**Animation:** threshold strip (click 1); panels fade in together (click 2); outcome chips pop one by one (clicks 3–5; "0/25 retrains" in violet last); validation chip (click 6).
**Speaker notes:** "Risk was surfaced on the large majority of real sessions with zero labels, and the no-auto-retrain policy held on every one — RQ1 and RQ3 in one experiment. Review decisions decompose into collapse-guard and critical-signal cases — breakdown in backup B3." (Have that breakdown ready — Danger question #4.)

---

### Slide 17 — Answers to the research questions (1:00)
**Layout:** 4 rows: RQ → verdict chip → one evidence line (Table 8.1 condensed).
**Content:**
- **RQ1** ✓ *Yes, bounded* — unlabeled risk detected & routed to review; signals indicate risk, not verified error
- **RQ2** ✓ *Materially* — recognition & monitoring behavior depend on the bound contract (units, scaler, order, windowing, baseline); changing them changes outcomes
- **RQ3** ✓ *Yes* — severity routes to review/label queue; collapse guard + cooldown; mutation only through the evidence gate
- **RQ4** ✓ *Not the data alone* — contract verified sound (within-distribution success); degradation pattern = cross-user shift + calibration limits
**Animation:** rows one per click.
**Speaker notes:** 10–12 s per row; this slide is your Q&A anchor — point back to it during discussion.

---

### Slide 18 — Limitations, stated before you ask (0:45)
**Layout:** two columns of short red-bullet rows (left: evidence limits; right: system limits). No softening.
**Content:**
- 6 labeled users + 1 blind probe → high-variance cross-user estimates; no population claim
- User 7 self-recorded & self-labeled → timing/boundary noise; author-as-subject bias acknowledged
- Thresholds = conservative defaults, not longitudinally calibrated limits
- No clinical validation; outputs are activity labels, never clinical conclusions
- Retraining path validated as a *mechanism*, not as an accuracy gain; single-user retraining unsupported
- Offline-first single machine; no on-device/real-time claim
**Animation:** both columns as one fade (1 click) — limitations should not be drip-fed; show them all at once, confidently.
**Speaker notes:** "These bounds are stated in §8.3 — and most of the future work (calibration, personalization, larger cohorts, governed adaptation) falls directly out of them."

---

### Slide 19 — Conclusion + thank you (0:45)
**Layout:** one statement, three contribution chips, the contract-folder icon, contact/repo line.
**Content:**
- Statement: *A wearable HAR model becomes responsible to operate only inside an explicit runtime contract, label-free monitoring, and a governance boundary that separates risk observation from model mutation — this thesis builds, evaluates, and bounds exactly that lifecycle.*
- Chips: **Runtime contract as deployment unit** · **93.6 → 44.4 → 37.0 reported without inflation** · **23/25 reviews, 0 automatic retrains**
- Footer: github.com/ShalinVachheta017/MasterArbeit_MLops · tag `v1.0-thesis` · "Thank you — I look forward to your questions."
**Animation:** statement (click 1), chips together (click 2).
**Speaker notes:** Land it in under 40 seconds and stop talking. Silence invites questions on your terms.

**Running total ≈ 19:50 — on target.**

---

# BACKUP SLIDES (B1–B9, shown only on demand)

**B1 — Contract sensitivity / preprocessing ablation.** The configuration-D story behind "D1": the gravity/unit mismatch episode (training-style Az ≈ −3.5 m/s² vs raw gravity Az ≈ −9.8 m/s² → near-total hand_tapping collapse) and the controlled sweeps (`reports/ABLATION_WINDOWING.csv`, `THRESHOLD_CALIBRATION.csv`) showing monitoring severity responds to contract changes while the model stays fixed. **Build this slide from whatever lands in your final §7.4.1 — numbers must match the submitted PDF exactly.**
**B2 — Threshold tiering table.** Full Table 6.3 (Stage 6 warn vs Stage 7 warn/critical per signal + 24 h cooldown) + the sentence "conservative defaults chosen on the training distribution and curated sessions — recalibration is named future work."
**B3 — Trigger decision logic + 23/25 decomposition.** The piecewise action function (collapse → review; c≥1 → review; w≥2 → queue_retrain; w=1 → monitor; cooldown rewrites), Fig. 6.2 flow, and a small table: review reason × session count (collapse guard / critical transition / critical drift / escalation) + whether queue_retrain ever fired. **Compute these counts from `reports/unlabeled_sessions_monitoring.json` before the defense.**
**B4 — Full result tables.** Table 7.3 (per-fold: 93.34/94.41/94.14/93.48/92.68) and Table 7.4 (per-user LOUO with window counts; note: mean is unweighted across users).
**B5 — Confusion matrix + per-class F1.** Fig. 7.4 and Fig. E.2: hand_tapping recognized reliably; several fine-grained classes near F1 = 0; macro-F1 0.350 is the average of few-good-many-zero.
**B6 — Benchmark comparison details.** [10]: 87.0 % ± 1.2 % — list precisely what is identical and what differs (window family, scaler policy, augmentation, splits). *Verify against the paper before the defense — its author is in the room.*
**B7 — User-7 blindness protocol.** Timeline graphic: recorded → quarantined → model frozen → evaluated once; excluded from training/scaler/HP/model selection; bias acknowledgments (self-labeling, demand characteristics); labeled-vs-unlabeled agreement as a consistency check.
**B8 — Reproducibility runbook.** Appendix A condensed: `conda create … python=3.11` → `pip install -r config/requirements.txt` → `dvc pull` → `python run_pipeline.py --stages …` → `pytest tests -q` → `latexmk -pdf main.tex`; `artifact_md5.json` integrity; SavedModel portability; current test count.
**B9 — Glossary card.** Behavioral proxy · runtime contract · same-folder invariant · offline-first · assessment vs mutation — one line each, for any definitional question.

---

# Numbers you must know cold (flash-card box)

93.61 / 0.937 (5-fold) · 44.42 / 0.419 (LOUO) · 36.96 / 0.350 / CI 33.9–39.8 / conf 0.858 (blind) · 36.70 / 0.846 (unlabeled User 7) · 5.69 % (user 2) · 61.09 % (user 6) · 967,499 params · (200, 6) @ 50 Hz, stride 100 · 11 classes · 3,755 / 989 windows · 709,582 / 385,326 / 99,017 / 632,700 rows · thresholds 0.70 / 20 % / 35 % / z 1.8 / 85–95 % (S6) and 0.65–0.50 / 0.35–0.50 / 2.0–3.0 / 24 h (S7) · 23–1–1 of 25, 0 retrains · 0.00980665 · 87.0 ± 1.2 [10] · Level 1 maturity · contract folder `model_d1_final_20260528`.

# Build checklist (before exporting the deck)
1. Sync README to defended state (or banner + tag reference).
2. Regenerate Fig. 7.3 (legend) and re-export Fig. 3.2 with `20260528` — both feed Slides 7/15.
3. Compute the B3 review-reason counts from the monitoring JSON.
4. Verify [10] protocol details for Slide 13's footnote / B6.
5. Rehearse: full run ×3 with clicker; the Slide 13 and Slide 15 reveals carry the talk — don't rush them.

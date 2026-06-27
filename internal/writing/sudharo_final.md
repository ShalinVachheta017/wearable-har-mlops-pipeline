# SUDHARO FINAL — Consolidated Thesis Fix Plan (2026-06-11)

**Merges three review passes:**
1. `[E]` = Examiner-style review (`sudharo.md`, against main.pdf of 5 June 2026)
2. `[S]` = Shalin's own Ch4–8 read-through (11 June 2026)
3. `[V]` = Claude's cross-verification against pipeline code, contract artifacts, and result CSVs (11 June 2026)

**Guiding principle for every fix (Shalin's directive):** This thesis is about *developing an MLOps pipeline* for activity recognition. The model is **one artifact that moves through the pipeline** — not the protagonist. Wherever a fix touches prose, push the framing from "the model achieves X" toward "the pipeline detects / enforces / governs X."

---

## Part 0 — Verification results (settled — do NOT re-litigate)

Everything below was checked against the repo on 11 June. These are **confirmed correct** in the thesis; no changes needed:

| Claim in thesis | Verified against | Result |
|---|---|---|
| 5-fold: 93.34 / 94.41 / 94.14 / 93.48 / 92.68 → mean 93.61, F1 0.937 | `notebooks/Model_D1_Final_Build_Runtime_Contract.ipynb` outputs | ✅ exact match |
| LOUO: U1 45.52, U2 5.69, U3 50.50, U4 53.75, U5 50.00, U6 61.09 → mean 44.42, F1 0.419 | same notebook | ✅ exact match |
| User-7 blind: 36.96% / 0.350 / conf 0.858, CI [33.88, 39.84] | `models/runtime_contract/model_d1_final_20260528/user7_blind_probe_summary.json` | ✅ exact match |
| Schedule-aligned 36.70% | `user7_unlabeled_probe_summary.json` (`schedule_window_accuracy_pct`) | ✅ exact match |
| Label order (Table 4.x, p. 37): alphabetical 0=ear_rubbing … 10=standing | 4-way: `label_order.json` = `src/config.py ACTIVITY_LABELS` = `src/utils/label_mapping.py _CANONICAL_ACTIVITY_CLASSES` (used by FastAPI serving) = `data/prepared/config.json` | ✅ full parity, softmax-order claim is safe |
| Augmentation (§7.1.2): time-warp, magnitude scaling, jitter, training split only | notebook contains `augment_array`, `time_warp`, `jitter`, train-time only | ✅ accurate |
| User 7: 99,017 rows → 989 windows; params 967,499; milli-g constant | recomputed | ✅ (per `[E]`) |

**Repo evidence inventory discovered during verification (currently UNUSED in the thesis — this is the raw material for the MLOps refocus):**

| Asset | Location | What it proves |
|---|---|---|
| Trigger-policy comparison | `reports/TRIGGER_POLICY_EVAL.csv` | Governed two-of-three voting: precision **0.988**, FAR **0.007** vs naive single-signal precision 0.841, FAR 0.139 — both at episode recall 1.0. **Direct quantitative RQ3 evidence.** |
| Windowing/contract ablation | `reports/ABLATION_WINDOWING.csv` | window_size × overlap → accuracy, F1, confidence, entropy, flip-rate. **The missing RQ2 evidence.** |
| Threshold calibration sweep | `reports/THRESHOLD_CALIBRATION.csv` | Threshold provenance evidence. |
| 25-session monitoring run | `reports/unlabeled_sessions_monitoring.csv` | Per-session signals + actions. Breakdown: **23 review / 1 monitor / 1 none; 5 CRITICAL / 19 WARNING / 1 HEALTHY; `should_retrain=False` on all 25** (queue_retrain never fired). Signal counts: transition>35% in 21, >50% in 7; drift z>1.8 in 4; dominant>50% in 4. |
| Test suite | `tests/` | **89 test functions / 13 files.** Largest suites are the MLOps ones: Stage 6 monitoring (16), Stage 7 trigger (14), pipeline (12), runtime-contract consistency (5), API upload (4). |
| Two Docker images | `docker/Dockerfile.training`, `docker/Dockerfile.inference` | Train/serve environment separation — reproducibility evidence. |
| A/B/C comparison | `reports/abc_comparison/abc_results.csv` + old tex tree `thesis/chapters/ch7_experiments_evaluation.tex` (~line 394) | The D-lineage / contract-contrast material that was dropped during polishing. Reusable prose exists. |

---

## Part 1 — The MLOps refocus `[S — primary directive]`

**Diagnosis.** The RQs in §1.3 are already pipeline-framed (RQ1 pipeline risk detection, RQ3 governance, RQ4 attribution) — the framing is right. The drift happens in the *evidence and discussion*: Chapter 7 spends roughly 3× more space on model metrics (§7.2 recognition + §7.3 calibration) than on pipeline/monitoring evidence (§7.4), and Chapter 8 discusses mostly accuracy numbers. Meanwhile the strongest MLOps evidence in the repo (trigger-policy eval, ablation, 89 tests, 25-session decomposition, two Docker images) is absent from the document.

**The refocus is NOT a rewrite.** It is: (a) add the missing pipeline evidence to Ch7, (b) add the missing engineering subsections to Ch5, (c) rebalance Ch8 prose. Each edit below already appears in Parts 2–4; this part explains the *narrative goal*:

- **Ch7 after the fix** should read: protocol separation → model numbers (kept as-is, they are honest) → calibration failure mode → **§7.4 grows into the chapter's second pillar**: contract-sensitivity ablation (RQ2), trigger-policy comparison (RQ3), 25-session decomposition with the queue_retrain finding (RQ1), schedule-aligned proxy validation. The model section answers "what does the model do"; the expanded §7.4 answers "what does the *pipeline* do about it" — which is the thesis.
- **Ch8 after the fix** should answer each RQ with pipeline-first prose: reproducibility (artifact trail, contract enforcement, 89 tests, Docker pair), monitoring (decomposition + proxy validation), governance (trigger-policy numbers + never-fired retrain queue as a *positive* finding: the system surfaced risk through review, not through mutation).
- **Framing sentence to reuse** (already in thesis, §3.5): *"the model is not the deployment unit; the runtime contract is."* Every new paragraph should be consistent with it.

---

## Part 2 — Blocking content fixes (do these first, in order)

### 2.1 New §7.4.1 "Contract-Sensitivity Ablation" `[E#1][S][V: data exists]`
- One table from `reports/ABLATION_WINDOWING.csv` (configurations × accuracy / F1 / confidence / flip-rate), 3–5 sentences of interpretation.
- Optionally fold in the A/B/C contrast from `reports/abc_comparison/abc_results.csv`; reusable prose in the old tex tree.
- This one fix simultaneously: repairs §1.6's promise, grounds RQ2 / Table 8.1, gives "D1" its meaning, restores the negative-results promise, and adds MLOps weight to Ch7.

### 2.2 New trigger-policy evaluation table in §7.4 `[V: new finding — not in either review]`
- From `reports/TRIGGER_POLICY_EVAL.csv`: single-signal vs two-of-three voting — precision 0.841→0.988, false-alarm rate 0.139→0.007, episode recall 1.0 for both.
- This is the *quantitative* answer to RQ3 ("can a governed trigger policy support safer decisions than unrestricted automatic retraining?") that the thesis currently answers only architecturally.
- Note: Appendix C already points to this CSV (`appendix_c_reproducibility.tex:23`), so the document promises it implicitly. The abbreviation FAR is in the list (`main.tex:232`) and becomes *used* once this table exists.

### 2.3 Decompose the 23/25 review routing `[E#5][S-ch8][V: numbers computed]`
- Small table in §7.4: action × count (review 23 / monitor 1 / none 1), severity × count (CRITICAL 5 / WARNING 19 / HEALTHY 1), and per-signal incidence (transition warn 21, transition critical 7, drift critical 4, dominant>50% 4).
- **State explicitly: `should_retrain=False` on all 25 sessions — the queue_retrain branch never fired.** Present as a finding: risk surfaced via critical signals and review routing, never via warning-accumulation escalation; the no-auto-retrain invariant held on real data.
- Add the dominant-class-share view (the one Stage 6 signal not plotted in Fig 7.5).

### 2.4 Resolve the drift-baseline contradiction — it's TWO baselines, TWO paths `[E#3][V: code answer]`
Code reality (verified):
- **Pipeline Stage 6** (`src/entity/config_entity.py:237`): `baseline_mode="raw_physical"` → `models/raw_physical_baseline.json` (**outside** the contract folder). Used by the defended labeled Stage 1–7 run (`artifacts/20260528_122625`).
- **API path** (`src/api/app.py:98-103`): `garmin_train_scaled_baseline.json` **inside** the contract folder, drift computed on scaled windows. Used by `scripts/run_unlabeled_sessions.py` → i.e. the 25-session Figure 7.5 evidence.
- Fix: §6.2 and Appendix B must both say *two drift checks exist in two feature spaces* and which evidence used which. §6.2's claim that the raw baseline "belongs to the active runtime contract" is currently wrong (it lives in `models/`, not the contract folder) — fix that sentence regardless.

### 2.5 Explain "Model D1" `[E#2][S]`
- One sentence in §4.4: D = the selected preprocessing/contract configuration among the A–D candidates evaluated during development (cf. new §7.4.1); D1 = the first promoted runtime built under it.

### 2.6 Explain schedule-aligned accuracy (Fig 7.6) `[S][V: source confirmed]`
- Source: `user7_unlabeled_probe_summary.json` — the unlabeled session followed a scripted recording schedule (each activity in a known time slot: ear_rubbing 0–180 s, …, standing 1895–2080 s). Windows inherit the scheduled activity as proxy ground truth → 36.70%.
- Add 2–3 sentences in §7.4 + one caption sentence: *"Schedule-aligned accuracy is the fraction of windows whose prediction matches the activity scheduled for that time interval — proxy ground truth derived from the recording protocol, not manual annotation."*
- The 36.70% (proxy) ≈ 36.96% (labeled) agreement is under-sold `[E]` — add one sentence in §7.5 presenting it as validation of the unlabeled monitoring proxies.

### 2.7 Explain the Stage 6 vs Stage 7 threshold tiers `[S: Fig 6.1 + Tables 6.3/6.4 confusion]`
- 2–3 prose sentences: Stage 6 warns **earlier** (sensitive — for visibility in session reports); Stage 7 votes **conservatively** (specific — its output feeds governance). Example: drift warns at z=1.8 in Stage 6 while Stage 7 votes warning/critical at 2.0/3.0.
- Threshold provenance: sigma rationale is in code (`src/trigger_policy.py:96-126` — 2.0σ ≈ 95th pct, 3.0σ ≈ 99.7th pct / 3-sigma rule). State it.

### 2.8 Threshold provenance + circularity disclosure `[E#10]`
- One sentence in §6.5 or §7.4: which sessions informed Table 6.1 threshold selection, and whether any overlap with the 25 evaluated sessions (`reports/THRESHOLD_CALIBRATION.csv` is the artifact). A clean yes/no must exist before the defense.

### 2.9 Delete the orphaned entropy-drift sentence `[E#9][V: confirmed dormant]`
- Stage 6 (`src/components/post_inference_monitoring.py`) computes **no entropy**; the entropy thresholds in `trigger_policy.py:106-107` are dormant config no signal feeds; entropy lives only in the optional S11 calibration stage (`src/calibration.py`), not exercised in defended runs.
- Fix: remove the entropy-drift sentence from the §6.2 formal-definitions block (or footnote it as "defined for the optional calibration stage S11; not part of the defended Stage 6 signal set").

### 2.10 RQ2 question/answer mismatch `[E#6]`
- Reword RQ2 to "To what extent do preprocessing and train–serve contract choices affect…" **or** rewrite Table 8.1's "Strongly yes" as a descriptive answer citing §7.4.1.

### 2.11 Chapter 8 rebalance `[S: primary point][E: Ch8 thin]`
- §8.1: 3–5 sentences of prose per RQ in addition to Table 8.1. RQ1/RQ3 answers must cite the new §7.4 evidence (decomposition, trigger-policy table, queue_retrain finding). RQ2 cites §7.4.1.
- §8.2: add one paragraph on what the *pipeline* delivered operationally — contract enforcement outcomes, run-scoped artifact trail, 89-test suite, train/inference Docker pair, monitoring that routed 23/25 sessions to review with zero unauthorized mutations.
- §8.4 Future Work: add the online/cloud path `[S-ch5 point]` — the FastAPI inference container is registry-push away from a cloud host; continuous delivery of governed model updates extends Stage 8–10; currently §8.4 only mentions on-device/real-time.
- §8.3 additions `[E]`: author-as-subject bias for User 7 (demand characteristics); threshold–evaluation circularity disclosure (cf. 2.8).
- Fix Table 8.1 RQ4 overreach: "rules out a broken pipeline" → "indicates the pipeline and contract function as specified."

### 2.12 Five-fold leakage: name the third mechanism `[E#8]`
- §7.2.1 append: adjacent 50%-overlapping windows share half their samples across folds — sample-level leakage in addition to scaler-before-split and same-user folds.

### 2.13 Benchmark comparison softening `[E#4 — examiner authored the benchmark]`
- §7.2.1: "consistent with, and slightly above… under the same five-fold family" → "in the same range as the published benchmark [10]; protocol differences in augmentation and scaler policy preclude an exact comparison" — unless protocol identity is verified before submission. (Augmentation differs: D1 uses time-warp/scale/jitter ×3 — verified in notebook.)

### 2.14 Bootstrap CI caveat `[E]`
- §7.2.3: add "adjacent windows overlap, so the interval is approximate; a block bootstrap would widen it."

### 2.15 Notebook provenance in §7.1 `[E#9-orig]`
- One sentence: model-building results (5-fold, LOUO) come from the version-controlled build notebook that constructs the runtime contract (Appendix C); the Chapter 5 pipeline consumes that contract for inference, evaluation, monitoring, governance. Converts a gotcha into a design statement.

### 2.16 User-2 outlier appendix `[S]`
- New appendix section (reference from §7.2.2): User-2 vs other users per-channel statistics, its per-class confusion, 2–3 sentences of diagnosis (5.69% at n=668 windows ⇒ systematic distribution shift — device fit / motion style), plus chart. Main text stays lean; §7.2.2's existing "not removed to inflate the mean" paragraph is good — keep verbatim `[E]`.

### 2.17 Cooldown motivation `[S]`
- §6.3.x: one sentence on *why* — prevents oscillation: repeated runs over similar data would raise duplicate retrain requests faster than human review can absorb (code: 24 h retrain / 30 min alert cooldown).

### 2.18 Z-score blind spot `[E][S: "explain z-score more"]`
- §6.2: 2–3 sentences — per-channel z on **session means** vs baseline means in baseline-std units; blind to variance and spectral shift; the MMD audit branch exists to cover that gap offline.

---

## Part 3 — Chapter 5 engineering additions `[S]`

1. **Tests subsection** (§5.6): short paragraph + small table — 89 test functions / 13 files; families: Stage 6 monitoring (16), Stage 7 trigger (14), pipeline E2E (12), runtime-contract consistency (5), API upload modes (4), stage tests (rest). Name the 3–4 assertions of `test_runtime_contract_consistency.py` (also defense prep `[E]`). Full listing → appendix.
2. **Docker subsection** (§5.6.2): the two images — `docker/Dockerfile.training` and `docker/Dockerfile.inference` — and what each pins; train/serve environment separation as reproducibility evidence.
3. **DVC vs MLflow clarification** (§5.6.1) `[E]`: DVC *is* used (data/model versioning); what is not relied upon is an MLflow-style tracking server. Current sentence lumps them and undercuts Table 5.1.
4. **Latency/throughput number** `[E]`: one measured number (e.g., windows/s or session-processing seconds on the reference machine) — or delete "low-latency" in §4.3.
5. **Technology rationale stays in Ch5** `[S asked: move to Ch8?]` → keep *why-these-tools* here (Table 5.1 is good); only the *future online/cloud* sentences go to §8.4 (see 2.11).
6. Soften "each one supports…" absolute (§5.2) `[E]`.
7. S5-composition footnote: "S5 is the identity on unlabeled runs" `[E]`.

---

## Part 4 — Figures batch (one regeneration session)

| Fig | Fix | Source |
|---|---|---|
| 3.2 | Folder name `20260526` → `20260528` `[E — CONFIRMED in drawio source]` | `thesis/draw.io/figure_3_2_runtime_contract_folder.drawio:11`; then re-export + grep LaTeX for stragglers |
| 7.3 | Regenerate — legend renders as overlapping text `[E][S]` | `scripts/generate_ch7_figures.py`, fix legend placement |
| 4.3 (magnitude distributions) | Change chart type `[S]` — overlaid histograms → per-source KDE curves or box/violin | repo file is `Figure_4_6_magnitude_hist.png` (note: ch4 figure *filenames* don't match PDF numbers — rename during regeneration to avoid future confusion) |
| 4.5 (preprocessing contract) | Adjust spacing between steps 7 and 8 `[S]` | drawio source of `Figure_4_2_Preprocessing_Window_Construction.pdf` |
| 6.2 (governance flow) | Make horizontal `[S]` — currently vertical TikZ stack of 9 cm boxes; left→right flow uses the page better | TikZ in `ch6_monitoring_governance.tex:208-229` (cheap, it's code not an image) |
| 7.4 (User-7 confusion) | Resize/reposition for page-space `[S]` — do *after* content fixes so layout is done once | `0.72\textwidth` currently |
| 4.1 | Fix literal `train--serve` double hyphen in plot title `[E]`; optionally move to appendix (duplicates Table 4.4) | matplotlib title string |
| 6.1 (tiered thresholds bars) | Keep, but the explaining prose of fix 2.7 must reference it explicitly `[S: "what is figure 6.1?"]` | `Figure_6_2_tiered_thresholds.png` (filename mismatch again) |
| 7.5 | Add dominant-class-share panel/column (cf. 2.3) `[E]` | regenerate from `reports/unlabeled_sessions_monitoring.csv` |

---

## Part 5 — Language, tables, polish

1. **Table fonts** `[S — confirmed]`: big tables in Ch4/5/7 are `\scriptsize`; raise to `\footnotesize` where pages allow.
2. Normalize **authorise → authorize** (US majority) `[E]`.
3. Replace "**mentor-comparable**" (§7.5, confirmed at `ch7…tex:250`) → "comparable with the published Garmin benchmark [10]" `[E]`.
4. "the most honest" → "the strictest" (§7.2.3) `[E]`.
5. Zusammenfassung: "Darstellung von 50 Hz" → "**Abtastrate** von 50 Hz"; consider "Haarezupfen" `[E]`.
6. Deduplicate: "offline-first means…" (3×), "dashboard add-on" (2×), the 93.61/44.42/36.96 number block (4× in Ch7/8 — recite once in Ch8 intro, reference after) `[E]`.
7. Tables 7.3/7.4 "Mean" row carries total 3,755 → relabel "Mean / Total"; state LOUO mean is unweighted across users (window-weighted ≈ 44.05%) `[E]`.
8. Equation diet `[S]`: Ch5 has only one equation (keep it). The cut target is Ch6's formal-definitions block — keep the signals used in results (mean conf, U, T, drift z, dominant share D) and ECE; move MMD detail to Appendix D; delete entropy (2.9).
9. Softening table `[E]`: "impossible to trigger automatic mutation" → "by construction, no code path converts severity into mutation without the label/QA gate"; Table 8.1 RQ4 wording (2.11); §5.2 absolute (Part 3.6).
10. References: complete [5] and [10] (pages/DOI — examiner's papers); move editorial note out of [38], cite Anguita et al. 2013; one arXiv→published sweep `[E]`.
11. Abbreviations: EWC unused → mention with continual learning in §8.4 or drop; FAR becomes used via fix 2.2 `[E][V]`.
12. Repetition of no-diagnosis disclaimer (10+×) → keep ~6 strongest `[E]`.
13. "diagnostic case" wording collision in §3.4 → "one specific failure case" `[E]`.
14. Table 3.2 S8–S10 "Conditional" → S8 "No (produces candidate)", S9 "No (registers)", S10 "Conditional (promotes)" `[E]`.
15. S11 one-liner in §3.2: implemented but not exercised in defended runs `[E]` (consistent with 2.9).
16. Data-provenance/consent sentence in §4.1 (users 1–6 from supervisor's study [10]; User 7 = author) `[E]`.
17. "raw channel statistics" vs "after unit normalization" → "unit-harmonized, unscaled" once (§4.1) `[E]`.
18. §7.3 calibration section: **keep, don't trim** `[S asked]` — the high-confidence failure (0.858 conf at 37% acc) is the safety backbone of the monitoring argument; it only needs the Fig 7.3 fix.

---

## Part 6 — Defense danger list (rehearse; some answers improved by the fixes)

1. **Title vs scope** → scripted answer: title fixed at registration; thesis converts it into an application context; boundary itself is a contribution.
2. **"Show me the RQ2 evidence"** → §7.4.1 (after fix 2.1).
3. **"What were Models A–D?"** → naming sentence + §7.4.1 history.
4. **"Decompose the 23/25"** → table from fix 2.3; numbers: 23/1/1, 5 critical, 21 transition warnings, queue_retrain never fired.
5. **"Raw or scaled drift space?"** → after fix 2.4: *both, by path* — pipeline Stage 6 raw-physical (`models/raw_physical_baseline.json`), API scaled (contract folder), Fig 7.5 evidence via API path. One sentence, know the two file paths.
6. **"93.6 vs my 87 — same protocol?"** → softened comparison (2.13); augmentation verified different/unverifiable — say so.
7. **"User 7 is you"** → procedural blindness + demand-characteristics limitation (§8.3 after 2.11) + Fig 7.6 proxy agreement.
8. **"Headline numbers from a notebook?"** → §7.1 provenance sentence (2.15) + Appendix C artifact map.
9. **"Is 5-fold/bootstrap valid with overlapping windows?"** → concede optimism by construction; name all three leaks (2.12); LOUO is the deployment-relevant number; CI approximate (2.14).
10. **"Were the 25 sessions used to set thresholds?"** → disclosed answer from 2.8.
11. **"Why correct-and-warn instead of fail-always on stale path?"** → logged warning + exact-match-only correction + fail-fast preserved for incompatibility.
12. **"Gyroscope deg/s not rad/s?"** → contract fidelity to training-data convention of [9,10]; conversion = contract change.
13. *(new)* **"How many tests, what do they assert?"** → 89 tests / 13 files; contract tests assert scaler/label-order/shape/baseline binding (memorize the exact 5 assertions of `test_runtime_contract_consistency.py`).

---

## Suggested execution order

| Session | Items | Outcome |
|---|---|---|
| 1 — Ch7 evidence | 2.1, 2.2, 2.3, 2.6, 2.12–2.15 | RQ1/RQ2/RQ3 all have visible quantitative evidence; Ch7 becomes pipeline-balanced |
| 2 — Ch6 + drift | 2.4, 2.7, 2.8, 2.9, 2.17, 2.18 | Internal contradictions gone; monitoring chapter self-explanatory |
| 3 — Ch5 + Ch8 | Part 3, 2.5, 2.10, 2.11, 2.16 | Engineering evidence surfaced; discussion MLOps-first; D1 named |
| 4 — Figures | Part 4 (all) | One regeneration pass, layout last |
| 5 — Polish | Part 5, references | Language pass, fonts, dedup |
| 6 — Defense prep | Part 6 rehearsal + appendix Q&A | Scripted answers for all 13 |

**Estimated effort:** sessions 1–3 are the blocking work (~3 focused days — every required artifact already exists in the repo); 4–5 one day; 6 ongoing.

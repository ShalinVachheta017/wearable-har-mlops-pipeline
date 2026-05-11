# Master Thesis Finish TODO - May to June 2026

## 2026-05-09 Close-of-Day Update

This update supersedes the older May 8 planning notes where they conflict.

### Model Decision Direction

Keep A/B/C comparison, but use it as bounded final decision evidence, not another open-ended model sprint.

```text
A = clean-contract Model A, current deployable candidate
B = mentor/vendor legacy model, forensic unless made clean-contract
C = previous current/default pipeline model, replaced/rejected
```

Current rule:

```text
Use Model A unless Model B can be made production-safe under the same clean contract.
Do not keep Model C as the runtime model.
```

### New Evidence Runs

Two full Model A Stage 1-7 runs now exist:

```text
Normal production-style raw Garmin session:
artifacts/20260508_235323/
windows: 1304
label status: unlabeled
mean confidence: 0.3928
dominant class: sitting, 51.8%
classes used: 10 / 11
drift: HEALTHY, max 1.1166
trigger: REVIEW, no auto-retrain
```

```text
Labeled User 7 external session:
artifacts/20260508_235356/
windows: 989
accuracy: 0.3761
macro F1: 0.3410
classes used: 11 / 11
mean confidence: 0.3594
dominant class: nape_rubbing, 16.5%
drift: HEALTHY, max 0.1639
trigger: REVIEW, no auto-retrain
```

Interpretation: the pipeline/runtime contract works, Model A avoids full collapse and uses most/all classes, but confidence remains low. The next issue is calibration, threshold policy, class-level weakness, and final evidence framing, not basic pipeline failure.

### User 7 Size Caveat

User 7 is much smaller than `all_users` and uses overlapping windows, so accuracy/F1 have higher variance than a large independent test set. It is still useful as external self-recorded evidence, but it must not be described as population-level proof.

### Next Work Order

1. Finalize A/B/C comparison and decide the defended runtime model.
2. Create `reports/FINAL_RUNTIME_RUN_SUMMARY_2026-05-09.md` so raw logs are not the main reading artifact.
3. Sync stale docs: README, model decision, A/B/C comparison, Q&A reference, and thesis TODO.
4. Audit Model A confidence/calibration, monitoring thresholds, and trigger thresholds.
5. If time allows, run one labeled User 7 retraining-cycle demonstration as Stage 8-10 governance evidence, not as a blind final evaluation.
6. After model/evidence freeze, run a repo cleanup wave. Archive/delete noise only after the evidence map is written.

### Updated Priority Status

```text
P0-01 final model contract: 95% done; A/B/C final wording remains.
P0-04 canonical Stage 1-7 evidence: 55% done; two successful runs exist, evidence folder still needs curation.
P0-05 claim-to-evidence register: not started; should be created immediately after readable run summary.
P0-11 repo cleanup: wait until model/evidence freeze.
```

## Current Position (updated 2026-05-08, evening)

The thesis is around **84-86 % defendable** after today's session.

Updated weak-point list:

1. ~~Model-contract contradiction~~ → **resolved**: Model A is the deployed default in `src/config.py` (`DEFAULT_MODEL_PATH = FINAL_MODEL_A_PATH`); legacy model is gated by `PRETRAINED_MODEL_STATUS["status"] = "EXCLUDED_UNDOCUMENTED_PROVENANCE"`; batch/API parity verified at 100 % agreement (1.9e-6 max abs diff, 989 windows each).
2. ~~2 failing tests~~ → **resolved**: scoped `test_continue_on_failure` to ingestion-only so it stops colliding with the validation-gate hard-stop invariant. Suite is 240/240 green.
3. **Stale thesis PDF** — still open. `thesis/main.pdf` last built 2026-04-27; needs Ch4/5/6/7/8 May-findings update + rebuild.
4. **May findings not fully integrated into thesis chapters** — still open. Concrete chapter-by-chapter list now in WORKLOG (see "Main Report Upgrade Items" 2026-05-08 entry).
5. **Defense slides/demo not ready** — still open.
6. ~~Repo has old/stale/contradictory files~~ → **partially resolved**: 11 test files deleted (370→240 tests), `.dockerignore` hardened, `cd.yml` removed, `internal/` and `_archive/` flagged but kept (active evidence). Branch consolidation still pending.

The target is unchanged:

> Make the thesis, code, evidence, slides, and demo all tell the same story.

## Progress Log

### 2026-05-08 (Done Today)

- Fixed 2 failing tests; full suite 240/240 green.
- Test suite cleanup: 370 → 240 tests, 34 → 23 files. Pyramid 200 unit / 23 integration / 17 slow (83/10/7).
- Deleted out-of-scope test files (active learning, model rollback) plus 7 pre-stage-naming duplicate files; ported 7 unique tests into stage6/stage7 canonical files.
- Renamed `tests/test_drift_detection.py` → `tests/test_offline_drift_metrics.py` with header rewrite to clarify offline-only scope.
- `.dockerignore` hardened: added historical heavy folders, runtime outputs, pytest workspaces, notebooks, Office/PDF/LaTeX byproducts. Defensive AWS/credential patterns dropped because the repo has no AWS usage and no secrets files.
- `.github/workflows/cd.yml` deleted; CI-only stance documented in `.github/workflows/README.md`. Manual release-image command documented for the mentor reproducer flow.
- KS / PSI / MMD / z-score audit complete with code references. z-score is Stage 6 default; PSI is secondary runtime monitor (gated on `drift_reference.json`); MMD is opt-in for Stage 6 audit + retraining DA loss; KS is offline-only (config field defined but not consumed at runtime). Two loose ends documented: dead `ks_pvalue_threshold` field; legacy `psi` alias to migrate to `drift_zscore`.
- `Dockerfile.inference` slimmed: pinned `tensorflow-cpu` (saved 0.9 GB) and split `requirements.txt` → `requirements-runtime.txt` for the inference image (saved another 0.99 GB). **Final size 2.63 GB, down from 4.52 GB (42 % reduction)**, verified end-to-end with healthy container + `/api/health` HTTP 200.
- Stage 1-7 dry run on the new Model A config succeeded for stages 3-7 (5 of 7 completed; Stage 1 ingestion correctly required raw accel+gyro pair, Stage 2 validation correctly hard-stopped on User 7 timestamp gaps). Result: 3,852 predictions, mean confidence 0.378, top-3 spread 19.8 / 14.8 / 13.3 %, drift 0.24, trigger CRITICAL → REVIEW. **Compared to no-scaler baseline collapse**: failure mode shifted from "collapse" to "low-confidence", and Stage 7 routed both correctly to REVIEW (no auto-retrain).
- Verified Model A parity: batch and API paths produce identical predictions on User 7 (100 % agreement, 1.9e-6 max abs diff). No double scaling.
- Verified `LEGACY_PRETRAINED_MODEL` is structured-gated via `PRETRAINED_MODEL_STATUS["status"] = "EXCLUDED_UNDOCUMENTED_PROVENANCE"` in `src/config.py:96-98`.
- WORKLOG fully updated. Defendable thesis paragraphs drafted for Ch5 (parity) and Ch7 (failure-mode shift).
- Reference document created: `reports/THESIS_QA_REFERENCE_2026_05_08.md` with full threshold table, KS/PSI/MMD usage map, and state-machine logic for Ch5/Ch6 reuse.

## Final Defense Story

Use this as the core thesis direction:

> The thesis does not claim a perfect or universally generalizable HAR model. It contributes an offline-first MLOps pipeline for wearable IMU-based human activity recognition, where ingestion, validation, transformation, inference, monitoring, and trigger evaluation are reproducible and governed. The self-recorded Garmin evaluation exposed domain shift, and the pipeline correctly avoided unsafe automatic retraining from weak or unlabeled evidence.

This is strong and defendable.

## P0 - Critical Tasks

These must be finished first. Without these, defense confidence is weak.

### P0-01 - Decide the Final Model Contract — STATUS: 90 % DONE (2026-05-08)

`src/config.py` already declares `DEFAULT_MODEL_PATH = FINAL_MODEL_A_PATH`. Parity verified between batch and API. Remaining work: write the one-page `docs/MODEL_DECISION_2026-05.md` summarising the chosen contract (already partially exists per earlier sessions; verify content against current state).

What to do:

Choose one canonical runtime story:

```text
Final deployed model:
Final model path:
Input units:
Scaler:
Sampling rate:
Window size:
Stride:
Channels:
Class order:
Auto-retrain:
```

You must answer clearly:

> Which model is actually deployed?

Possible final answer:

```text
The deployed runtime uses the final production-contract model with six wrist IMU channels, 50 Hz sampling, 200-sample windows, stride 100, fixed class order, physical sensor units, and no unsafe automatic retraining.
```

Why this matters:

This is the biggest defense risk. If README, thesis, code, and slides say different things, the examiner will catch it.

Output:

```text
docs/MODEL_DECISION_2026-05.md
```

Time: 6-10 hours.

### P0-02 - Fix the Two Failing Tests — STATUS: DONE (2026-05-08)

Resolved. Scoped both `test_continue_on_failure` cases to `stages=["ingestion"]` so they no longer collide with the validation-gate hard-stop invariant. Full suite is **240/240 green**; the test count drop (from 370) is from a separate audit-driven cleanup (see Progress Log).

Current issue:

370 tests collected, 368 passed, 2 failed:

```text
tests/test_pipeline.py::TestSkipAndContinue::test_continue_on_failure
tests/test_pipeline_integration.py::TestSkipAndContinue::test_continue_on_failure
```

What to do:

Fix the behavior or intentionally revise the tests if the old expectation is no longer correct.

Why this matters:

You cannot defend "verified pipeline" with a red test suite.

Output:

```text
Full pytest green
or
documented expected failure with reason
```

Time: 1-2 hours.

### P0-03 - Fix or Remove `current_model.keras` Stub — STATUS: EFFECTIVELY CLOSED (2026-05-08)

The 10-byte stub still exists at `models/pretrained/current_model.keras`, but the only references are in `src/model_rollback.py` (lines 192 and 518), which is part of the rollback subsystem already classified as out-of-thesis-scope (auto-rollback contradicts `auto_retrain=false` governance). No production code path loads the stub. Final cleanup is to delete the file in the same wave that drops the rollback module references. Not blocking defense.

Current issue:

```text
models/pretrained/current_model.keras
```

is a 10-byte stub, not a real model.

What to do:

Either:

1. Replace it with the real final model, or
2. Remove all references to it from config/code/docs.

Why this matters:

If someone loads this path, it crashes. That is a visible defense risk.

Time: 1-2 hours.

### P0-04 - Freeze One Canonical Stage 1-7 Evidence Run — STATUS: 30 % DONE (2026-05-08)

Dry run completed today on the new Model A config; stages 3-7 ran cleanly (3,852 predictions, mean confidence 0.378, top-3 spread 19.8 / 14.8 / 13.3 %, drift 0.24, trigger CRITICAL → REVIEW). Artifacts at `artifacts/20260508_211723/` are a seed for the final pack. Remaining work: fix User 7 timestamp gaps so Stage 2 validation passes, then run the full Stage 1-7 sequence on a clean session and assemble the canonical evidence folder with README map.

What to do:

Create one final evidence folder:

```text
evidence/defense_run_2026_06/
```

Include:

```text
ingestion log
validation report
transformation summary
inference output
evaluation report
monitoring_report.json
trigger_decision.json
prediction CSV
README mapping evidence to thesis chapters/slides
```

Why this matters:

You need one place where every defense claim can be proven.

Time: 4-6 hours.

### P0-05 - Create Final Claim-to-Evidence Register

What to do:

Create:

```text
docs/FINAL_THESIS_CLAIMS_2026-06.md
```

Use this structure:

| Claim | Evidence file | Thesis chapter | Defense slide |
|---|---|---|---|
| Stage 1-7 pipeline works | canonical run logs | Ch5 | Slide 5 |
| Runtime contract is fixed | model decision note | Ch5/Ch7 | Slide 6 |
| Monitoring detects drift/risk | monitoring report | Ch6 | Slide 10 |
| Trigger blocks unsafe retraining | trigger decision JSON | Ch6/Ch8 | Slide 11 |
| Garmin result shows domain shift | evaluation report | Ch7 | Slide 12 |

Why this matters:

This makes the thesis evidence-first.

Time: 2-3 hours.

### P0-06 - Sync Thesis Chapters with May Findings

Chapters to update:

```text
ch4_data_model_development.tex
ch5_pipeline_implementation.tex
ch6_monitoring_drift_retraining.tex
ch7_experiments_evaluation.tex
ch8_discussion_conclusion.tex
ch8_garmin_evaluation.tex
```

Add these findings:

1. Runtime contract freeze from May 5
2. Raw physical units / final scaler decision
3. `auto_retrain=false` governance policy
4. Drift formula correction and 9.797 sigma false alarm story
5. Self-recorded Garmin evaluation
6. Low accuracy as domain-shift evidence, not pipeline failure
7. Mentor-vs-clean model contract comparison
8. Why no automatic retraining was triggered
9. Stage 8-11 as optional/gated extensions

Why this matters:

The thesis PDF must describe the actual repo state.

Time: 14-20 hours.

### P0-07 - Rebuild Thesis PDF

What to do:

Fix LaTeX environment first:

```text
pdflatex not on PATH
```

Then rebuild:

```text
thesis/build_thesis.ps1
```

Check:

```text
no undefined refs
no broken citations
figures visible
tables visible
ToC updated
LoF/LoT updated
main.pdf fresh
```

Why this matters:

The final deliverable is the PDF.

Time: 3-5 hours, including PATH/install fix.

### P0-08 - Update Defense Q&A

File:

```text
internal/writing/defense_qa.md
```

Update especially:

```text
Data & preprocessing
Model architecture
Runtime contract
Monitoring
Trigger policy
Retraining governance
Model governance
Self-recorded Garmin evaluation
Limitations
```

Why this matters:

The spoken defense must match the final thesis.

Time: 3-4 hours.

### P0-09 - Build Defense Slides

Target: 15-20 slides.

Suggested structure:

| Slide | Topic |
|---:|---|
| 1 | Title |
| 2 | Problem statement |
| 3 | Research questions |
| 4 | Why MLOps for wearable HAR |
| 5 | Full pipeline overview |
| 6 | Stage 1-7 operational path |
| 7 | Stage 8-11 gated extensions |
| 8 | Dataset and 11 classes |
| 9 | Final runtime/model contract |
| 10 | Model architecture |
| 11 | Main experiments |
| 12 | Monitoring and drift |
| 13 | Trigger governance |
| 14 | Garmin external evaluation |
| 15 | What negative result means |
| 16 | Limitations |
| 17 | Future work |
| 18 | Final contribution |
| 19-20 | Backup Q&A slides |

Why this matters:

Defense is a visual story. Do not wait until the last week.

Time: 10-14 hours.

### P0-10 - Create Demo Runbook and Dry-Run

Create:

```text
thesis/defense_demo_runbook.md
```

Include exact commands:

```bash
python run_pipeline.py --stages inference evaluation monitoring trigger
docker compose up
curl localhost:8000/health
curl localhost:8000/api/health
```

Also include:

```text
expected output
where evidence is saved
what to say if demo is slow
what not to claim
```

Why this matters:

If examiner asks "show me," you need a safe demo.

Time: 4-6 hours.

### P0-11 - Clean/Archive Stale Docs After Evidence Is Frozen

Do not do this before evidence freeze.

Clean:

```text
old TODO files
old diagnostics
6th may folder
stale README claims
old notebooks
stale model notes
duplicate API notes
```

Archive old planning files:

```text
_archive/planning/
_archive/notebooks/
_archive/diagnostics/
```

Why this matters:

Contradictory files reduce trust.

Time: 6-10 hours.

## P1 - Important Tasks

These are not all defense-blocking, but they strongly improve quality.

### P1-01 - API vs Pipeline Parity Audit — STATUS: DONE (2026-05-08)

Verified end-to-end on User 7: 989 windows on each side, first-window max abs diff 1.9e-6, prediction agreement 100 %, identical dominant-class percentage 16.48 %. No double scaling. Both paths apply the saved Garmin train-only scaler exactly once after unit conversion and before row-wise windowing.

Caveat: direct Stage 3 (batch path) expects canonical sensor columns `Ax, Ay, Az, Gx, Gy, Gz`. The API also accepts training-style `Ax_w, ...` and converts internally. Document this column-naming difference in Ch5 wording rather than claim full input-format agnosticism.

Check:

```text
src/api/app.py
docker/api/main.py
```

Decide which one is authoritative.

Verify `/predict` uses the same:

```text
model path
input units
windowing
channel order
scaler/no-scaler
class mapping
```

Time: 4-6 hours.

### P1-02 - Add or Clarify DVC Reproducibility

Best option:

Add:

```text
dvc.yaml
```

with stages 1-7.

Minimum option:

If full `dvc repro` is too much, write clearly:

```text
DVC is used for artifact/data versioning, while pipeline orchestration is handled by run_pipeline.py.
```

Time: 4-6 hours.

### P1-03 - Finalize Chapter 4 Data Tables

Add tables for:

```text
participants
sessions
class distribution
train/validation/test split
self-recorded Garmin session
```

Also add this limitation sentence:

```text
This evaluation supports baseline operational and external sanity-check analysis, but it is not equivalent to subject-wise generalization across a large population.
```

Time: 4-6 hours.

### P1-04 - Bibliography and Literature Cleanup

There are around 83 BibTeX entries, but not all may be useful.

Do:

```text
remove weak/padding entries
verify metadata
keep 55-65 strong references
prioritize MLOps, HAR, wearable sensors, domain shift, monitoring, calibration, drift
```

Time: 5-8 hours.

### P1-05 - Chapter 2 Synthesis Table

Add one strong related-work table:

| Area | What literature says | Gap | Thesis response |
|---|---|---|---|
| Wearable HAR | Models work under controlled data | Domain shift remains | External Garmin evaluation |
| MLOps | Lifecycle needs monitoring/versioning | Few small offline thesis pipelines | 11-stage offline-first pipeline |
| Drift monitoring | Production data changes | Labels often unavailable | Warning + review-gated trigger |
| Retraining | Can improve model | Unsafe without labels | `auto_retrain=false` |

Time: 6-10 hours.

### P1-06 - Stage 11 Calibration Wording

Decide one:

Option A - finalize calibration:

Fit temperature scaling properly and report result.

Option B - scope out:

```text
Calibration is implemented as an optional uncertainty extension, but final fitted calibration is left as future work because the available labeled external data are insufficient for reliable post-hoc calibration.
```

For this timeline, Option B is safer.

Time: 2-4 hours.

### P1-07 - Gyroscope Clipping/Validation Policy

Document what happens if gyroscope values are high, for example:

```text
Values near 900-1000 deg/s are treated as warning-level anomalies, not automatic errors, because fast wrist motion can produce high angular velocity. The event is logged for review.
```

Or make it stricter if config supports it.

Time: 1-2 hours.

### P1-08 - Single Canonical Class Mapping Source

Make this the only source:

```text
src/utils/label_mapping.py
```

Avoid silent overrides from:

```text
data/prepared/config.json
```

Why:

Class-order mismatch is a serious silent ML bug.

Time: 2-3 hours.

### P1-09 - Fix Ingestion Ordering Hygiene

Change dataset selection from file modified time to filename/session timestamp if still needed.

Why:

Modified time can change accidentally and cause the wrong session to be selected.

Time: 1-2 hours.

### P1-10 - CI Smoke Workflow — STATUS: PARTIAL (2026-05-08)

`cd.yml` deleted; CI-only stance documented in `.github/workflows/README.md`. CI lint + unit-tests + docker-build-check still runs on PRs/pushes to main. Remaining work: drop the `-m "not slow and not integration"` filter from the unit-tests job so all 240 tests run in CI (currently the 23 integration tests in `test_pipeline.py` are silently skipped). Deferred until the test cleanup is fully settled to avoid CI-on-CI churn.

Add or verify GitHub Actions can run:

```bash
pytest
python run_pipeline.py --stages inference evaluation monitoring trigger
```

on a small fixture.

Time: 3-4 hours.

## P2 - Nice-to-Have Polish

Do these only after P0 and main P1 tasks are safe.

### P2-01 - Notebook Hygiene

Mark canonical notebook:

```text
nb/production_contract_adamsense_finetune.ipynb
```

Archive old notebooks:

```text
nb/processing.ipynb
nb/gpt.ipynb
nb/mentor_vs_pipeline_contract_comparison.ipynb
```

Time: 2-3 hours.

### P2-02 - Front Matter Cleanup

Check:

```text
submission date
supervisor names
declaration date
title consistency
no \today placeholder
```

Time: 30-60 minutes.

### P2-03 - Optional Model Comparison Sweep

Only do this if everything else is done.

Possible baselines:

```text
small CNN-GAP
CNN-GRU
existing CNN-BiLSTM
```

This should probably be skipped unless the supervisor asks.

Time: 6-8 hours.

## Drop Unless Supervisor Asks

Do not start these now:

```text
Airflow / Prefect migration
Kubernetes deployment
Cloud deployment
full Prometheus/Grafana system
multi-user labeled retraining
active learning closed loop
new model architecture experiments
large new ablation study
```

These can create new problems and are not needed for defense.

## Best Starting Order

| Order | Task |
|---:|---|
| 1 | Final model-contract decision |
| 2 | Fix 2 failing tests |
| 3 | Fix/remove `current_model.keras` stub |
| 4 | Freeze one Stage 1-7 evidence run |
| 5 | Create final claim-to-evidence register |
| 6 | Update thesis Ch4/5/6/7/8 |
| 7 | Fix LaTeX and rebuild PDF |
| 8 | Update defense Q&A |
| 9 | Build slides |
| 10 | Build demo runbook |
| 11 | API parity audit |
| 12 | Repo cleanup/archive stale docs |
| 13 | DVC/reproducibility clarification |
| 14 | Final polish |

## Recommended Calendar

### May 8 (DONE)

Actual outcomes (see Progress Log for detail):

```text
✓ Failing tests fixed (240/240 green)
✓ Test suite cleanup 370 → 240 (pyramid 200/23/17)
✓ KS / PSI / MMD / z-score audit complete with code references
✓ .dockerignore hardened
✓ cd.yml removed; workflows README rewritten as CI-only
✓ Dockerfile.inference: tensorflow-cpu pin + requirements split → 4.52 GB → 2.63 GB (-42 %)
✓ Stage 1-7 dry run on Model A (5/7 stages clean; Stage 1+2 expected gates)
✓ Model A batch/API parity verified (100 % agreement, 1.9e-6 max abs diff)
✓ LEGACY_PRETRAINED_MODEL exclusion verified in src/config.py
✓ Worklog + main-report upgrade list drafted
✓ Reference document at reports/THESIS_QA_REFERENCE_2026_05_08.md
```

### May 9 (Tomorrow — Concrete)

Pick **two** items, in priority order:

```text
1. Fix User 7 timestamp gaps (sort + dedupe) so Stage 2 validation passes
2. Run a clean full Stage 1-7 on the fixed session → seed for evidence pack
3. Drop dead ks_pvalue_threshold field; finish psi → drift_zscore migration
4. Verify docs/MODEL_DECISION_2026-05.md exists and matches current src/config.py
```

Items 1+2 are the highest-value sequence: they unlock P0-04 (evidence pack) which is the chapter-7 anchor.

### May 10

```text
1. Assemble evidence/defense_run_2026_06/ with logs, reports, JSON decisions
2. Add README mapping each artifact → thesis chapter / defense slide
3. Start P0-05 claim-to-evidence register draft (table form)
```

### May 11-17

Finish:

```text
Ch4/5/6 main-report updates (see Worklog "Main Report Upgrade Items" 2026-05-08)
Ch5 parity paragraph (already drafted — paste-ready)
Ch7 failure-mode-shift paragraph (no-scaler collapse vs scaler-on diversity)
Data tables for Ch4 (participants, class distribution, split logic)
defense Q&A update to reflect Model A as deployed contract
```

### May 18-24

Finish:

```text
Ch7/8 updates
fresh PDF build
bibliography cleanup
Chapter 2 synthesis table
first slide deck
```

### May 25-31

Finish:

```text
evidence pack final
demo runbook
repo cleanup
mock defense 1
mock defense 2
```

### June

Only:

```text
final PDF polish
slides polish
demo rehearsal
supervisor feedback fixes
submission formatting
```

Do not change the model story in June unless the supervisor explicitly requires it.

## Final Definition of Done

The thesis is ready when:

```text
pytest is green
fresh thesis PDF builds from source
one final model contract is stated everywhere
one Stage 1-7 evidence run is reproducible
evidence pack contains metrics, monitoring, trigger decision, and predictions
self-recorded Garmin evaluation is honestly explained
slides answer the main examiner questions
demo runbook works from clean shell
stale docs are archived or marked historical
README, thesis, slides, and defense Q&A tell the same story
```

Main target:

> By end of May, the thesis should be technically frozen. June should be only writing polish, supervisor feedback, slides, and rehearsal.

 
 # # #   P 1 - 0 5   -   F i x   o r   r e m o v e   � 4 . 2 . 5   T O D O   p l a c e h o l d e r   i n   L a T e X   ( H i g h )  
 W h a t   t o   d o :  
 -   O p e n   t h e   A p r i l - r e p o r t   L a T e X   s o u r c e ,   f i n d   t h e   \ %   T O D O \   i n   \ � 4 . 2 . 5 \ .  
 -   R e b u i l d   t h e   P D F   t o   c o n f i r m   n o   u n d e f i n e d - r e f e r e n c e   e r r o r s .  
 W h y   t h i s   m a t t e r s :   A n   e x a m i n e r   r e a d i n g   a   c o m p i l e d   b l a n k   s e c t i o n   i s   n o t   a c c e p t a b l e .  
  
 # # #   P 1 - 0 6   -   A d d   G _ m a g   s i g n a l   t o   S t a g e   6   ( M e d i u m )  
 W h a t   t o   d o :  
 -   I n   \ s r c / c o m p o n e n t s / p o s t _ i n f e r e n c e _ m o n i t o r i n g . p y \ ,   a f t e r   t h e   \ m o n i t o r . r u n ( ) \   c a l l ,   l o a d   \ p r o d u c t i o n _ X . n p y \   ( c h a n n e l s   3  5   a r e   G x ,   G y ,   G z ) ,   c o m p u t e   G _ m a g   p e r   w i n d o w   =   \ s q r t ( G x �   +   G y �   +   G z � ) \ ,   t a k e   t h e   m e d i a n   a c r o s s   a l l   w i n d o w s .  
 W h y   t h i s   m a t t e r s :   A d d s   p h y s i c a l   s t a b i l i t y   t r a c k i n g .  
  
 
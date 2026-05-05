# 2026-04-26 - ORANGE Audit Closure Plan

Goal: Convert the read-only audit result into a clean verification plan and resolve the thesis/code evidence contradictions before doing new fixes.

Mode: Planning artifact only. Do not treat any item as closed until evidence exists.

## Audit Interpretation

The read-only audit result is useful because it separates implemented features from verified evidence.

The pipeline is structurally strong:

- pipeline stages exist
- artifacts exist
- DVC exists
- MLflow exists
- monitoring exists
- trigger logic exists
- retraining is gated
- Docker/API/CI structure exists

The main problem is not the pipeline shape. The main problem is that the thesis story, README, April report, docs, and runtime code are not all saying the same thing.

Final audit status from the read-only audit: ORANGE.

## Main P0 Risk

The biggest submission risk is model identity contradiction.

Original contradiction identified by the audit:

```text
Runtime default model = models/pretrained/fine_tuned_model_1dcnnbilstm.keras

But some docs say:
- pretrained model is excluded
- default model is retrained
- retained model is retrained artifact
```

This became P0.1 and was closed on 2026-04-26 with Option A: the defended runtime model is `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`.

One final answer is required:

```text
Which model is the defended runtime model?
```

Remaining work is the P0.6 consistency sweep across README and thesis chapters so every defended-scope document uses the same canonical sentence from `docs/THESIS_CONSISTENCY_NOTES.md`.

## P0 - Must Fix Or Verify Before Submission

| Priority | Item | Required closure |
|---|---|---|
| P0.1 | Resolve model identity | **CLOSED 2026-04-26:** Option A selected. The defended runtime model is `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`; retraining produces governed candidates and no retrained candidate is promoted as of this closure note. |
| P0.2 | Fresh current-branch verification | Run full pytest, pipeline stages 1-7, API smoke, and Docker smoke |
| P0.3 | Prometheus/Grafana/alerting scope decision | **CLOSED 2026-04-26:** Prometheus, Grafana, and alert-rule files are historical/optional/future-work only. Do not use them as active evidence for the defended thesis pipeline. |
| P0.4 | Docker model-loaded proof | Health endpoint alone is not enough; capture proof that model is loaded and inference works inside Docker |
| P0.5 | Retraining governance proof | Produce evidence matrix for healthy, warning, collapse, cooldown, no labels, and worse-model cases |
| P0.6 | Thesis/report consistency | Align README, April Ch4, original Ch4, Ch7, exclusion docs, and worklogs |

## Verification Order

1. Resolve defended runtime model identity. **Closed 2026-04-26.**
2. Align documentation and thesis text to that model decision. **Open under P0.6.**
3. Run fresh full pytest in the intended thesis environment.
4. Run pipeline stages 1-7 on a known session and capture artifacts.
5. Run local API smoke with the defended model loaded.
6. Run Docker smoke with the defended model loaded and an inference request.
7. Mark Prometheus/Grafana/alerting as out-of-scope for defended current implementation and remove them from active evidence claims. **Closed 2026-04-26 for the files touched in this pass; P0.6 will catch any remaining defended-scope docs.**
8. Produce retraining-governance decision matrix.
9. Re-run thesis build only after the story is aligned.

## Retraining Governance Matrix To Prove

| Case | Expected decision | Evidence required |
|---|---|---|
| Healthy input | No retrain | Trigger report with `should_retrain=false` |
| Warning input | Review or monitor | Trigger report with reasons |
| Dominant-class collapse | Review or governed trigger, not blind retrain | Monitoring + trigger report showing dominance handling |
| Cooldown active | No retrain | Trigger state and cooldown decision |
| No labels | Skip retraining | Stage 8 skip evidence |
| Worse candidate model | No promotion | Registration/proxy validation artifact |

## Worklog Update To Paste

```markdown
## 2026-04-25 Evening - Read-Only Pipeline Robustness and Evidence Audit

A read-only audit was completed on branch `feature/api-two-file-upload` to evaluate pipeline robustness, code quality, and thesis evidence consistency. No files were changed.

The audit verdict was **ORANGE**: the pipeline is structurally strong but not yet 100% evidence-verified. Strong evidence exists for the 11-stage pipeline, artifact generation, train-only scaler, monitoring reports, trigger decision saving, DVC/MLflow presence, Docker/CI structure, and retraining gating.

The main submission-critical weakness was a model-lineage contradiction: the runtime default points to `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`, while other documentation made incompatible claims about excluded pretrained artifacts or retrained defaults. This was resolved on 2026-04-26 by locking Option A: the pretrained supervisor-provided model is the defended runtime model, while retrained artifacts remain governed candidates.

A scope decision was also made for monitoring infrastructure: Prometheus, Grafana, and alert-rule files will **not** be treated as active evidence for the defended current implementation. The defended monitoring evidence will come from pipeline monitoring artifacts, trigger reports, logs, saved run outputs, MLflow/DVC evidence, and thesis-documented governance behavior.

Other P0 items identified: fresh current-branch verification, Docker/API smoke with the model actually loaded, API monitoring parity, retraining-governance decision matrix, and thesis/report/code consistency.

Conclusion: pipeline implementation is promising, but the next session must focus on evidence closure rather than new features.
```

## `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md` Block To Paste

```markdown
### Newly raised from read-only audit - 2026-04-25

| ID | Weak link | Severity | Status | Required closure |
|---|---|---:|---|---|
| P0-AUDIT-1 | Runtime model identity contradiction: pretrained default vs retrained/excluded documentation | Critical | **CLOSED 2026-04-26** | Option A locked; defended runtime model is `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`; remaining README/Ch4/Ch7 sweep is P0.6 |
| P0-AUDIT-2 | Current branch not fully verified after hardening | High | Open | Run full pytest, pipeline stages 1-7, API smoke, and Docker smoke with defended model loaded |
| P0-AUDIT-3 | Prometheus/Grafana/alerting are not part of the defended current implementation | High | **CLOSED 2026-04-26** | Keep only as historical/optional/future-work if mentioned |
| P0-AUDIT-4 | Docker health check can pass without proving model-loaded inference | High | Open | Capture Docker run evidence with actual defended model loaded and inference request |
| P0-AUDIT-5 | Retraining governance matrix not fully proven | High | Open | Evidence healthy/warning/collapse/cooldown/no-labels/worse-model cases |
| P0-AUDIT-6 | API monitoring weaker than pipeline monitoring | High | Open | Either align API monitoring or document API monitoring as lightweight/demo path |
```

## `NEXT_WEEK_PIPELINE_FIX_REGISTER_2026-04-23.md` Block To Paste

```markdown
## Audit refresh - 2026-04-25

A read-only Codex audit returned **ORANGE** status. The pipeline is structurally strong but not yet 100% evidence-verified.

Scope decision: Prometheus, Grafana, and alert-rule files are **not part of the defended current thesis implementation**. They may remain as historical/optional/future-work material, but they should not be used as active evidence for monitoring or deployment readiness.

Net-open items for next verification session:

1. Resolve defended runtime model identity.
2. Align README, original Ch4, April Ch4, Ch7, and exclusion docs.
3. Run fresh current-branch full test evidence.
4. Verify Docker/API with actual model-loaded inference.
5. Remove Prometheus/Grafana/alerting from active thesis evidence claims or clearly mark them as historical/future-work.
6. Produce retraining-governance decision matrix.
7. Verify API monitoring parity or document it as a lightweight API path.
8. Keep landed-but-unverified items open until evidence is captured.
```

## Final Judgment

This audit is a good result, even though it says ORANGE, because it identifies the exact evidence risks.

The next focus should not be making the pipeline bigger. The next focus should be making the code, docs, thesis, and evidence say one same story.

Once the model identity is resolved, Prometheus/Grafana are removed from active claims, and fresh current-branch evidence is captured, ORANGE can realistically become YELLOW, and then GREEN after full pipeline/API/Docker/CI verification.

---

## Proposed Solutions Per P0 Item (updated 2026-04-26)

Each section below proposes a concrete way to close the corresponding P0 item. These are recommendations, not decisions — each one needs the user's confirmation before execution. The order matches the verification order on lines 64-72.

### P0.1 — Resolve Model Identity Contradiction (CLOSED 2026-04-26)

Closure decision: **Option A** is locked. The defended runtime model is `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`, with scaler `data/prepared/config.json`. Retraining remains part of the pipeline as a governed candidate-generation mechanism, not as an automatic source of the defended runtime model. The registry state (`models/registry/model_registry.json`, `current_version: null`) supports this decision.

Immediate closure writes completed:

- `docs/THESIS_CONSISTENCY_NOTES.md` section 5 now carries the canonical sentence and rules.
- `internal/workflow/EVIDENCE_LEDGER.md` EV-009 marks the pretrained model as **DEFENDED RUNTIME MODEL**.
- `internal/writing/defense_qa.md` section 0 answers the model-identity, retraining-governance, and stages-12-14 questions.
- `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md` P0-AUDIT-1 is marked **CLOSED 2026-04-26**.
- Stages 12, 13, and 14 are documented as future work, not as defended pipeline stages.

#### P0.1 — The two real options

**Option A — Defend the pretrained model** (`models/pretrained/fine_tuned_model_1dcnnbilstm.keras`)

- Pick this if: MLflow evidence exists for it, runtime already loads it, no retrained candidate has formally passed the governance gate.
- Story: "The pretrained 1D-CNN-BiLSTM is the defended baseline. Retraining is a *governance mechanism* that produces candidates; no candidate has yet been promoted because [no labeled production data / governance gate not satisfied / collapse detected]."
- Honest, defensible, smallest code change.

**Option B — Defend a retrained model** (`models/retrained/<X>.keras`)

- Pick this only if: a specific retrained artifact passed `is_better=True` with real evidence, lineage (pretrained → trigger → candidate → promoted) is fully documented, MLflow run + trigger report + registration artifact all exist.
- Stronger story but only viable if the lineage proof is real.

#### P0.1 — Recommendation: Option A

- Runtime code already points there → minimal churn.
- MLflow evidence exists for it.
- "Retrained model is the default" appears aspirational, not proven.
- P0.5 (governance matrix) is still open — defending a model whose lineage isn't fully proven is itself a defense risk.
- Reversible later: if P0.5 evidence shows a retrained candidate genuinely beats the pretrained on a real holdout, swap to Option B before submission.

#### P0.1 — Canonical sentence to write down once Option A is confirmed

> **Defended runtime model:** `models/pretrained/fine_tuned_model_1dcnnbilstm.keras`, scaler `data/prepared/config.json`, architecture 1D-CNN-BiLSTM (Ordóñez and Roggen 2016). Retraining is implemented as a governance mechanism; no retrained candidate has been promoted to defended status as of 2026-04-26.

This sentence becomes the single source of truth. Every doc must agree with it or be updated to match.

#### P0.1 — Files to align

| Layer | File | Action |
| --- | --- | --- |
| Code | `src/api/app.py`, `src/inference.py`, config loaders | Confirm default points to chosen `.keras` + scaler |
| Code | `config/pipeline_config.yaml` | Confirm `default_model_path` matches |
| Code | `Dockerfile.inference` / `docker-compose.yml` | Confirm `MODEL_PATH` env / volume mount matches |
| Doc | `README.md` | Replace any "default = retrained" wording with the canonical sentence |
| Doc | `thesis/.../Chapter4.tex` (original) | Match canonical sentence |
| Doc | April Ch4 report | Match canonical sentence |
| Doc | `Chapter7.tex` | Match canonical sentence; reframe retraining as governance |
| Doc | Exclusion docs (`.dvcignore`, exclusion notes) | Remove any line claiming pretrained is excluded |
| Doc | `EVIDENCE_LEDGER.md` EV-009 | Mark pretrained as **defended runtime model** |
| Doc | `defense_qa.md` | Add Q "Which model is your defended runtime model?" with the canonical sentence |
| Doc | `WORKLOG.md` | New entry recording the decision and rationale |

#### P0.1 — Closure checks (all three must pass)

1. **grep test:** `grep -rn "models/retrained" .` returns only references framing retraining as governance/candidate, never as "the default runtime model."
2. **runtime test:** Start the API → `/health` or model-info endpoint reports the canonical model path.
3. **doc test:** README, Ch4, Ch7, defense_qa, exclusion docs, EVIDENCE_LEDGER all contain the canonical sentence (or link to it).

---

### P0.2 — Fresh Current-Branch Verification

#### P0.2 — Plan

1. Create a fresh evidence folder: `reports/verification_2026-04-26/`.
2. Run in this order, capturing stdout+stderr to numbered log files:
   - `pytest tests/ -v --tb=short > 01_pytest.log 2>&1`
   - `python run_pipeline.py --stages 1-7 > 02_pipeline_stages.log 2>&1`
   - Start API in background → `curl /health`, `curl /predict` with sample input → `03_api_smoke.log`
   - `docker compose up inference` → same `/health` + `/predict` → `04_docker_smoke.log`
3. Save each artifact path in a single `MANIFEST.md` inside the verification folder.
4. Update `EVIDENCE_LEDGER.md` with EV-6xx entries pointing at these logs.

#### P0.2 — Closure checks

- All four log files exist, all show pass/2xx outcomes.
- `MANIFEST.md` lists every artifact with one-line description.
- WORKLOG entry references the manifest.

#### P0.2 — Risks to mitigate before running

- Confirm Python env matches the defended one (don't accidentally verify in the wrong env).
- Confirm DVC state is clean (`dvc status`) — don't verify with stale data.
- Confirm the `.keras` file from P0.1 is actually present on disk.

---

### P0.3 — Prometheus/Grafana/Alerting Scope (CLOSED 2026-04-26)

Already closed in this session. Evidence:

- `EVIDENCE_LEDGER.md` EV-205, EV-208, EV-419, EV-505, EV-506, EV-507 annotated as **HISTORICAL/FUTURE-WORK**.
- `internal/writing/defense_qa.md` Docker services Q&A reframed with explicit scope note.
- `FIX_BEFORE_SUBMISSION_WEAK_LINKS.md` P0-AUDIT-3 marked **CLOSED 2026-04-26**.

No further action required unless a new doc surfaces that makes active claims about Prometheus/Grafana/alerting.

---

### P0.4 — Docker Model-Loaded Proof

#### P0.4 — The problem

`/health` returning 200 only proves the FastAPI process is alive. It does not prove the `.keras` model loaded successfully or that inference works inside the container.

#### P0.4 — Plan

1. **Add a model-loaded indicator** to the existing `/health` (or a new `/health/ready`) endpoint:
   - Returns the loaded model path, model hash (sha256 of the `.keras` file), and load timestamp.
   - This is a ~10-line change to `src/api/app.py`.
2. **Capture three pieces of evidence in one Docker run**:
   - `docker compose up inference` → wait for ready
   - `curl /health/ready` → JSON proves the canonical path from P0.1 is loaded → save as `04a_health_ready.json`
   - `curl -X POST /predict -d @sample_window.json` → real prediction returned → save as `04b_predict_response.json`
   - `docker logs inference > 04c_container_logs.txt` → grep for the model-load line
3. **Save under** `reports/verification_2026-04-26/docker/`.

#### P0.4 — Closure checks

- `04a_health_ready.json` shows model_path == canonical sentence path.
- `04b_predict_response.json` contains a class label + confidence (not 500 error).
- `04c_container_logs.txt` shows a "Model loaded from PATH" log line.
- New `EVIDENCE_LEDGER.md` rows EV-510, EV-511, EV-512 reference these.

#### P0.4 — Why a new endpoint instead of just reading logs

- An endpoint is part of the runtime contract — auditable, scriptable, repeatable.
- Logs are easy to lose; an endpoint can be hit from CI on every deploy.

---

### P0.5 — Retraining Governance Decision Matrix

#### P0.5 — The problem

The trigger policy code exists, but there is no single document showing: *for each input scenario, here is what the system decided and here is the artifact that proves it.*

#### P0.5 — Plan

Build a 6-row evidence table by running each scenario as a synthetic test and capturing the trigger report each time.

| Case | Synthetic input | Expected decision | Evidence artifact |
|---|---|---|---|
| Healthy | Recent prod-like windows, balanced classes | `should_retrain=false` | `reports/governance_matrix/01_healthy_trigger.json` |
| Warning | Mild drift (Wasserstein > warning threshold, < critical) | `monitor` / `review` | `02_warning_trigger.json` |
| Dominant-class collapse | Synthetic windows where one class > 80% | Governed action, **not blind retrain** | `03_collapse_trigger.json` + monitoring report |
| Cooldown active | Trigger fired recently, cooldown window not expired | `should_retrain=false` (cooldown reason) | `04_cooldown_trigger.json` + `trigger_state.json` |
| No labels | Stage 8 invoked without labeled data available | Skip retraining | `05_no_labels_skip.log` |
| Worse candidate | Force a retrain that produces a model with lower proxy metric | `is_better=false` → no promotion | `06_worse_candidate_registration.json` |

#### P0.5 — Implementation steps

1. Create `scripts/run_governance_matrix.py` that orchestrates the 6 scenarios using existing test fixtures + small synthetic data generators (~150 lines).
2. Run it once → produces all 6 artifacts under `reports/governance_matrix/`.
3. Write `reports/governance_matrix/SUMMARY.md` that renders the table with links to each artifact and the actual decision recorded.
4. Add EV-6xx rows to `EVIDENCE_LEDGER.md`.
5. Reference the summary from Ch6 of the thesis.

#### P0.5 — Closure checks

- All 6 artifacts exist with the expected decision.
- `SUMMARY.md` table is complete with no MISSING rows.
- Worse-candidate case explicitly shows `is_better=False` and no model promotion in MLflow registry.

#### P0.5 — Why this matters for defense

This is the single strongest piece of evidence that the pipeline is *governed*, not just *automated*. A blind retrain-on-drift loop is a known anti-pattern; this matrix proves you avoided it.

---

### P0.6 — Thesis/Report/Code Consistency

#### P0.6 — The problem

Multiple chapter sources (original Ch4, April Ch4, Ch7), README, exclusion docs, and worklogs have drifted apart. Different docs make different claims about the same artifacts.

#### P0.6 — Plan

1. **Establish a single consistency-source-of-truth file:** `docs/THESIS_CONSISTENCY_NOTES.md` already exists — extend it to be the canonical reference for *every* contested claim:
   - Defended model identity (from P0.1)
   - Monitoring scope (from P0.3)
   - Retraining governance (from P0.5)
   - CV strategy (GroupKFold, not stratified — already flagged in FIX_BEFORE)
   - Dataset version + size + split policy
2. **Build a consistency matrix** as a new section in that file:

   | Claim | Canonical statement | README | Orig Ch4 | April Ch4 | Ch7 | Exclusion docs | EVIDENCE_LEDGER |
   | --- | --- | --- | --- | --- | --- | --- | --- |
   | Defended model | (from P0.1) | ok | warn | warn | ok | ok | ok |
   | Monitoring scope | Offline-first only | ok | ok | ok | ok | n/a | ok |
   | CV strategy | GroupKFold by user | warn | miss | ok | ok | n/a | ok |
   | ... | | | | | | | |

3. **Process for each row:** for every `warn` or `miss`, open the file, replace the contradicting passage with the canonical statement, then flip the cell to `ok`.
4. **Decide the April-vs-original chapter question:** the audit notes both versions exist. Pick one as defended (likely April Ch4 since it's most recent and aligned with hardening), mark the other as `archive/` or `historical/`.
5. **Worklog entry** recording every doc that was changed and why.

#### P0.6 — Closure checks

- Consistency matrix shows all `ok` in every cell.
- `grep -rn` for the old contradicting phrases returns nothing in defended-scope files.
- One chapter version is clearly marked as defended; the other is in `archive/` or has a banner saying "superseded by X."
- Defense Q&A pulls every claim directly from the canonical statements.

#### P0.6 — Why this is last in the order

Doing P0.1, P0.3, P0.4, P0.5 first generates the *facts* that need to be made consistent. Aligning docs before the facts are settled means doing the work twice.

---

## Suggested execution order (combining all the above)

1. **P0.1** → **closed 2026-04-26** with Option A; remaining defended-doc sweep is handled under P0.6.
2. **P0.4** → small endpoint addition + Docker proof capture (cheap, blocks nothing).
3. **P0.5** → build `run_governance_matrix.py` and capture the 6 artifacts (largest scripting effort).
4. **P0.2** → run fresh full verification with the canonical model + all evidence in place.
5. **P0.6** → final consistency sweep with all facts now settled.
6. **P0.3** → already closed.

After step 5, ORANGE → YELLOW. After CI/full-Docker/full-pipeline verification on the aligned branch, YELLOW → GREEN.

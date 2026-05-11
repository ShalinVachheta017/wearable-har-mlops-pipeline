# DEFENSE Q&A — Final Thesis Story

> **Purpose**: Defense-ready spoken answers for every examiner question.
> Built from complete thesis scan, May 2026.
> Follow the wording rules exactly: never say "data leakage" about Model B, never say "auto-retraining", never claim clinical diagnosis or population-level generalization.

---

## 0. Numbers You Must Know Cold

| Item | Value |
| --- | --- |
| Model A params | 87,083 |
| Model B / C params | 499,131 |
| Model A — User 7 external accuracy | 37.6% (macro F1 34.1%) |
| Model A — all\_users diagnostic | 42.4% (macro F1 39.5%) |
| Model A — mean confidence on User 7 | 0.359 |
| Model A — mean confidence on Garmin (unlabeled) | 0.393 |
| Model B — User 7 external | 43.8% (mean conf 0.775) |
| Model B — all\_users diagnostic | 90.8% (mean conf 0.930) |
| Model B — internal-to-external gap | ~47 pp |
| Model C — User 7 accuracy | 7.6%, only 4/11 classes |
| two\_of\_three trigger policy precision | 0.9878 |
| two\_of\_three false alarm rate | 0.0069 |
| single\_signal false alarm rate | 0.1389 |
| 24h cooldown episode recall | 0.875 (misses 2/16 episodes) |
| Negative result: mean confidence before/after | 0.8578 / 0.8578 (unchanged) |
| Garmin run: windows / trigger / auto\_retrain | 1,304 / REVIEW / false |
| User 7 run: windows | 989 |
| API-batch parity: prediction match | 989/989 (max softmax diff 1.9×10⁻⁶) |
| Garmin training population | all_users training split (6 participants); User 7 excluded from Model A scaler fit and external evaluation |
| Stage 6 confidence threshold | 0.70 |
| Stage 6 uncertain-window threshold | 20% |
| Stage 6 transition-rate threshold | 35% |
| Stage 6 drift z-score | 1.8 |
| Stage 6 dominant-class share threshold | 85% |

---

## 1. Thesis Motivation

### Q: "What problem does this thesis solve?"

**Short answer:** It builds the lifecycle engineering that standard HAR papers skip: what happens after the model is trained — how does it behave operationally, when should it be retrained, and how do you know the preprocessing is still correct?

**Explanation:** Most wearable HAR papers deliver offline accuracy on a held-out test set and stop. The model is trained, evaluated once, and the paper is written. What they do not address is what happens when that model is used with different data, slightly different preprocessing, or on a user not in the training set. This thesis answers that question by building a governed 7-stage inference-and-monitoring lifecycle in which preprocessing decisions are traceable, monitoring signals are multi-dimensional, trigger policy is explainable, and no retraining happens without justified human review. The contribution is not a new classifier — it is the operational layer that makes a classifier defensible over time.

**What not to say:** Do not say "I solved wearable HAR" or "the system is production-ready." The claim is: a lifecycle can be built such that operational risk is observable and acted on conservatively.

---

### Q: "Why anxiety-related behaviors as the application domain?"

**Short answer:** They are a well-defined engineering target — observable wrist movements that a wrist-worn IMU can capture — while also being clinically relevant as behavioral proxies associated with anxiety and distress.

**Explanation:** Body-focused repetitive behaviors (BFRBs) — hand tapping, hand scratching, nail biting, hair pulling, skin picking, hand rubbing — are expressed as short, repeated wrist and hand movements. That makes them tractable for wrist-worn IMU recognition without requiring any physiological sensor beyond accelerometer and gyroscope. At the same time, they are studied in the mental-health literature as behaviors associated with anxiety or distress states, which gives the recognition target clinical relevance without requiring me to claim that recognizing them constitutes clinical diagnosis. The literature supports recognition of these behaviors from wrist motion; it does not support unrestricted inference about internal anxiety state.

**What not to say:** Do not say "my system diagnoses anxiety" or "it monitors anxiety in real time." Say: it recognizes observable behavioral proxies that are associated with anxiety-related contexts.

---

### Q: "What are the four research questions?"

**Short answer:** RQ1: can the pipeline detect operational risk without labels? RQ2: how much do preprocessing decisions change runtime inference behavior? RQ3: can governed trigger policy improve safety over single-signal triggering? RQ4: how much of prediction collapse is driven by model choice versus input data?

**Evidence:** All four are answered in Chapter 7 and summarized in Table 8.2. Each answer is bounded: RQ1 is "yes, partially — monitoring signals respond directionally but cannot recover label-level accuracy." RQ2 is "strongly and non-monotonically — gravity removal alone worsened collapse." RQ3 is "yes within scope — two-of-three voting dominates single-signal." RQ4 is "materially attributable to model choice — the same input produced different collapse with different models."

---

## 2. Data and Mental-Health Scope

### Q: "What data did you use?"

**Short answer:** Garmin Venu 3 wrist-sensor sessions (accelerometer + gyroscope at 50 Hz) collected from the project participants, with 11 activity classes derived from the ADAMSense behavioral activity taxonomy.

**Explanation:** The primary training data is from Garmin Venu 3 wrist sensor recordings exported as CSV files through Garmin Connect. The sensor streams are accelerometer (three axes, milliG or m/s²) and gyroscope (three axes, deg/s) at 50 Hz. The 11 activity classes are a subset of the ADAMSense behavioral taxonomy: the model was trained on labeled windowed sessions from project participants. The labeled external evaluation uses User 7, an external participant whose data was not in the training set. The Garmin production-style unlabeled run uses a real wrist sensor session without labels. There is no hospital data, no EEG, no clinical dataset.

**What not to say:** Do not say "population-level generalisation" — the training set is 6 participants, and the external evaluation is one external participant.

---

### Q: "Why only 6 participants? Is that enough?"

**Short answer:** The available Garmin labeled corpus is sufficient to build and evaluate a governed proof-of-concept lifecycle, but not enough to claim subject-independent or population-level generalisation. The thesis explicitly states this as a scope boundary.

**Explanation:** The thesis claim is an engineering and governance contribution, not a generalisation claim. The all_users corpus (6 participants, 3,852 windows) provides enough labeled data to train a baseline classifier, run a preprocessing ablation, evaluate monitoring signals, and compare trigger policies. It does not establish that the model generalizes across the population. Chapter 8 records this explicitly: external validity is limited to one external participant (User 7) and one unlabeled Garmin session. A larger multi-participant evaluation would be needed before characterizing the deployment generalization ceiling.

**What not to say:** Do not say "six is enough for real deployment" or "the model is subject-independent." The claim is specifically bounded.

---

### Q: "Is this a clinical system? Does it diagnose anxiety?"

**Short answer:** No. This thesis does not diagnose mental health conditions. It treats anxiety-related repetitive activities as observable behavioral proxies and uses them to study the engineering problem of building a reproducible, monitored, offline-first MLOps pipeline for wearable sensor models.

**Explanation:** The system recognizes motor behaviors from wrist IMU data. Recognizing that someone is performing a hand-tapping motion is a behavior-recognition task, not a clinical assessment. Whether that behavior is clinically significant in a given context is a question for a clinician using multiple sources of information — not for a wrist sensor model. Chapter 8 records this explicitly as a non-claim. The mental-health literature motivates why these behaviors are worth recognizing; it does not authorize clinical inference from recognition results alone.

**What not to say:** Do not use the words "diagnoses," "clinical assessment," "anxiety detection system," or "mental health monitoring" without immediately qualifying that the claim is behavioral recognition, not clinical inference.

---

### Q: "How were the activity windows labeled?"

**Short answer:** Pre-annotated session files with majority-label-with-lexicographic-tiebreak windowing policy. Mixed-label windows exist: 2.02% on User 7 (20 of 989 windows), 3.35% on all\_users.

**Explanation:** Labels were assigned per window using a majority-label policy: whichever activity occupies the most time in a window is assigned as the window label, with lexicographic tiebreaking when two activities tie. This is a standard windowing labeling approach in HAR. The Chapter 7 ABC section explicitly rules out mixed-label boundary noise as the primary explanation for the 37.6% User 7 accuracy: 2.02% mixed windows is negligible. The dominant explanation is cross-user domain shift.

---

## 3. Architecture and Scalability

### Q: "What does 'offline-first' mean?"

**Short answer:** The pipeline runs on a single machine, uses file-based batch inputs (CSV pairs from Garmin Connect), and produces a complete run-scoped artifact set. There is no continuous streaming, no cloud orchestration, and no multi-tenant inference path.

**Explanation:** Offline-first is a deliberate scope decision, not a missing feature. The Garmin Venu 3 exports bounded session files — there is no real-time raw sensor API. Monitoring signals (mean confidence, transition rate, drift z-score) are computed over a complete session worth of windowed predictions, so they require batch inputs by design. Reproducibility requires a fixed, versioned input artifact: a streaming system would make exact replay ambiguous. Chapter 3 states this clearly: the system prioritizes controlled execution over distributed orchestration, and a reproducible local architecture is more defensible than a partially implemented cloud platform.

---

### Q: "What does 'scalable' mean in the thesis title?"

**Short answer:** Scalable does not mean cloud-scale deployment. It means the pipeline is modular, reproducible, configurable, artifact-tracked, and extendable from a fixed Stage 1–7 runtime path into gated Stage 8–10 mutation stages without redesigning the whole system.

**Explanation:** Each of the seven operational stages has a single dedicated component file (`data_ingestion.py`, `data_validation.py`, `data_transformation.py`, `model_inference.py`, `model_evaluation.py`, `post_inference_monitoring.py`, `trigger_evaluation.py`). Behavior is controlled through a three-layer configuration system (code defaults, `pipeline_config.yaml`, `pipeline_overrides.yaml`) without requiring code changes for threshold tuning. Artifacts are run-scoped and versioned. The mutation stages (S8–10) are activated by explicit runtime flag. That means a new model checkpoint, a changed dataset, or an updated threshold can be integrated without dismantling the pipeline. That is what scalable means here.

**What not to say:** Do not say "scalable to cloud" or "production-ready infrastructure." If asked about cloud extension, point to the FastAPI containerization in `src/api/app.py` and acknowledge it is designed as a future extension (Ch8 future work), not a defended current claim.

---

### Q: "Why MLOps Level 1 and not Level 2?"

**Short answer:** Level 2 requires automated continuous retraining without operator intervention. In a label-scarce, health-adjacent setting, that poses a safety risk the evidence does not justify.

**Explanation:** Level 1 means: automated stage pipeline, experiment tracking, artifact lineage, governed retraining gate. That is what this thesis delivers. Level 2 means: models are retrained and redeployed automatically when monitoring signals fire. In this system, labels are not available at inference time, so the monitoring signals are proxies for risk — they are not ground-truth performance measurements. The negative result from the 26-session unit-fix plus abstain experiment is direct evidence of why Level 2 is unsafe here: an apparently sensible intervention changed routing behavior without changing mean confidence at all (0.8578 before and after). Automating retraining on the basis of such signals would produce a pipeline that mutates its model in response to routing artifacts, not learning signals.

---

### Q: "Why not use Airflow or Prefect for orchestration?"

**Short answer:** A linear stage list controlled by a single Python entrypoint is sufficient for this scope, and it allows tight MLflow and trigger-policy integration that would be harder to express in a DAG YAML.

**Explanation:** The pipeline runs one session at a time on a single machine. A DAG orchestrator would add infrastructure complexity without a corresponding operational benefit. The custom Python orchestrator in `src/pipeline/production_pipeline.py` integrates directly with MLflow experiment tracking and the trigger-policy evaluation logic, and keeps configuration fidelity explicit. If the thesis scope were extended to multi-user parallel sessions, a proper DAG orchestrator would become necessary — that is noted as a future work direction in Ch8.

---

## 4. Model Decision A/B/C

### Q: "Why is Model A the defended runtime candidate?"

**Short answer:** Model A is the only model with a fully specified, persisted, and verified preprocessing contract: Garmin train-only scaler, row-wise time-major tensor layout, SHA-256-verified label order. It is the clean proof-of-concept runtime candidate.

**Explanation:** Model A was selected in the May 2026 model sprint and frozen as the A1 baseline. Its artifact package includes `fine_tuned_clean_model.keras`, `garmin_train_scaler.json`, `garmin_train_scaler.joblib`, `model_contract.json`, `label_order.json`, and a monitoring baseline. The scaler JSON and joblib forms are verified to agree to 0.0 maximum absolute difference. The label order is SHA-256-verified at runtime. The legacy pretrained model is structurally excluded in `src/config.py` with `PRETRAINED_MODEL_STATUS["status"] = "EXCLUDED_UNDOCUMENTED_PROVENANCE"`. Model A is presented as a proof-of-concept runtime candidate, not a production-grade deployment.

**What not to say:** Do not say "Model A is the best performing model" — it is the most defensible model from a contract and reproducibility standpoint, not the highest-accuracy one.

---

### Q: "Model B scores 43.8% external and 90.8% internal — why not use Model B?"

**Short answer:** Model B's non-persisted full-evaluation scaler and legacy native setup limit transferability. Its internal score is not a deployment claim.

**Explanation:** Model B's internal accuracy (90.8% on all\_users diagnostic) is achieved by fitting a StandardScaler on the entire evaluation dataframe at runtime — including validation and external users. That scaler is not persisted; it is computed fresh each time from whatever data is available. Under an external evaluation, this means the scaler's mean and standard deviation include the external user's statistics. This makes the diagnostic preprocessing dependent on the evaluation batch itself, so the result is not reproducible as a fixed runtime contract. The internal-to-external gap of roughly 47 percentage points (90.8% → 43.8%) is consistent with a non-persisted full-evaluation scaler and legacy channel-major tensor layout limiting transferability outside the native diagnostic context. Model B is retained as a forensic reference to document that the internal score overstates deployment performance.

**What not to say:** Do not use the phrase "data leakage." The correct framing is: "non-persisted full-evaluation scaler and legacy native setup limit transferability."

---

### Q: "What does Model C prove?"

**Short answer:** That same tensor shape is not enough — loading the same checkpoint as Model B under a different preprocessing contract collapses accuracy to 7.6% on User 7 and uses only 4 of 11 classes.

**Explanation:** Model C uses the exact same Keras checkpoint as Model B but runs it under the clean row-wise layout with no scaler. The result is near-total collapse: 7.6% accuracy, 2.5% macro F1, 4/11 classes used, mean confidence 0.748. This directly proves that a checkpoint is not a runtime artifact — the preprocessing contract under which the checkpoint was trained is what determines runnable behavior. Without the matching scaler and tensor layout, the model is unusable. This is one of the clearest findings in Chapter 7, and it motivates the heavy emphasis on contract verification in the governed runtime.

---

### Q: "ABC comparison: what is the conclusion?"

**Short answer:** Model A is honest but modest. Model B looks strong internally but does not transfer. Model C proves contract-mismatch risk. Together, they show that production governance must verify the preprocessing contract end-to-end, not just the checkpoint.

**Explanation:** The ABC comparison is designed to answer whether each model carries the production properties its internal score would suggest. Model A is the only one that is reproducible and honest: consistent 37–42% accuracy across external and diagnostic datasets, 11 classes used, low mean confidence (0.359) that honestly reflects generalization limits. Model B achieves 43.8% on User 7 in its native diagnostic mode but is not transferable as a runtime artifact. Model C proves the contract-mismatch lesson. The governance conclusion is: internal accuracy is not a sufficient deployment criterion; contract-level verification is required.

---

## 5. Runtime Contract and Scaler

### Q: "What is Model A's input contract?"

**Short answer:** Row-wise time-major windows of shape (batch, 200, 6) — 200 samples × 6 channels (Ax, Ay, Az, Gx, Gy, Gz) — at 50 Hz, 50% overlap, accelerometer in m/s², gyroscope in deg/s, with Garmin milliG conversion applied at ingest when needed.

**Explanation:** The contract is fully specified in `model_contract.json` in the Model A artifact package. Key items: `legacy_mentor_reshape=false`, `row_wise_windows=true`, gravity removal disabled, runtime calibration disabled, unit conversion enabled at ingest (Garmin Venu 3 exports milliG; the pipeline converts to m/s² at Stage 1). The label order of 11 classes is persisted in `label_order.json` and SHA-256-verified at evaluation time. This is what makes the runtime reproducible: every behavioral and preprocessing parameter is frozen and checked, not inferred from context.

---

### Q: "Why a train-only scaler? Why not scale the full dataset?"

**Short answer:** Fitting the scaler on training data only prevents the scaler statistics from encoding information about the validation or external users, which would make the model's preprocessing artificially well-matched to each test set.

**Explanation:** A StandardScaler fitted on the full dataset (including validation and external users) produces mean and std values that reflect the statistics of the evaluation population. On deployment, a new user's data would be normalized with statistics that partially include that new user's own distribution. This makes preprocessing artificially aligned with each test set. The Garmin train-only scaler is fitted exclusively on Garmin training-set windows; User 7 and the Garmin unlabeled session are transformed using the stored training statistics. This is the correct approach for estimating deployment performance honestly, and it is verified: the JSON and joblib forms of the scaler agree to 0.0 maximum absolute difference.

**What not to say:** Do not describe the alternative (full-eval scaler) as "data leakage" — say "non-persisted full-evaluation scaler that limits transferability."

---

### Q: "How do you verify that the API and the batch pipeline produce identical predictions?"

**Short answer:** Both paths were run on the same User 7 session (989 windows) and all 989 predictions matched exactly, with a maximum absolute softmax probability difference of 1.9×10⁻⁶.

**Explanation:** This is recorded in `reports/FINAL_RUNTIME_RUN_SUMMARY_2026-05-09.md`. API-batch parity is not an implementation assumption — it is a verified property of the defended runtime. Both execution paths load the same Model A artifact from the same frozen package, apply the same scaler, and produce the same per-window predictions. The tiny floating-point difference (1.9×10⁻⁶) is numerical precision noise, not a meaningful discrepancy.

---

### Q: "What is the runtime entrypoint?"

**Short answer:** `run_pipeline.py` with explicit `--stages` and `--accel-file`/`--gyro-file` arguments. The canonical command is documented in `REPRODUCE.md`.

**Explanation:** The single entrypoint constructs typed configuration objects, applies YAML overrides, and invokes the stage orchestrator in `src/pipeline/production_pipeline.py`. Stages 1–7 run by default. Stages 8–10 (retraining mutation) and Stage 11 (calibration) are explicitly gated behind runtime flags. This means the normal evidence run — ingest, validate, transform, infer, evaluate, monitor, trigger — never touches the model artifact.

---

## 6. Monitoring, Drift, and Trigger Policy

### Q: "What does Stage 6 monitor?"

**Short answer:** Three signal groups: (1) confidence and uncertainty — mean confidence, uncertain-window rate, mean entropy; (2) temporal transitions — prediction-sequence stability; (3) distribution drift — mean-shift z-score against the training-set baseline.

**Explanation:** Each signal group is independently rated HEALTHY, WARNING, or CRITICAL based on the Stage 6 thresholds (confidence 0.70, uncertain windows 20%, transition rate 35%, drift z-score 1.8, dominant-class share 85%). The three ratings are passed to Stage 7. No single signal drives a governance decision — all three assessments are combined. This multi-signal architecture is motivated empirically: a model can be confidently wrong, poorly calibrated without obvious shift evidence, or shifted without confidence collapse. One signal alone is insufficient.

---

### Q: "What does CRITICAL mean? Does it mean the system retrains?"

**Short answer:** CRITICAL is a monitoring severity level — a rating that one signal group is above the warning threshold. REVIEW is the governance action. They are two separate fields. In both defended evidence runs, severity reached CRITICAL but the governance action was REVIEW and auto\_retrain=false.

**Explanation:** Stage 6 outputs a severity rating (HEALTHY, WARNING, CRITICAL) for each signal group based on how far each signal is from the configured thresholds. Stage 7 combines the three ratings using a two-of-three voting policy, a collapse guard, and a cooldown gate, and produces a governance action field (NO\_ACTION, REVIEW, or RETRAIN) together with an `auto_retrain` boolean. On both defended evidence runs (Garmin unlabeled and User 7), the action field was `review` and `auto_retrain=false`. Chapter 8 records this explicitly as a non-claim: "CRITICAL is severity; REVIEW is governance action. Severity and mutation decision are two separate fields, by design."

**What not to say:** Do not say "when monitoring is CRITICAL the system retrains" — this is exactly wrong.

---

### Q: "Why two-of-three voting and not single-signal triggering?"

**Short answer:** Single-signal triggering produces a false alarm rate of 13.9%. Two-of-three voting reduces it to 0.7% while keeping full episode recall.

**Explanation:** The trigger policy evaluation replayed 16 monitored episodes. The single\_signal policy fired alerts at precision 0.8406 with a false alarm rate of 0.1389 — meaning roughly 1 in 7 alerts was spurious. The two\_of\_three policy achieved precision 0.9878, episode recall 1.0, trade-off F1 0.9939, and false alarm rate 0.0069. That means 14 times fewer false alarms while still detecting every genuine episode. The 24-hour cooldown further reduces noise but sacrifices recall: it misses 2 of 16 episodes (recall 0.875). The two\_of\_three policy without cooldown is the strongest overall balance in the tested set.

---

### Q: "Why not use TENT or AdaBN for test-time adaptation?"

**Short answer:** These methods adapt the model to target data — they change the deployed artifact. This thesis deliberately prioritizes observation before mutation. Adapting a model without labeled data and without a governance gate is precisely the unsafe pattern the architecture is designed to avoid.

**Explanation:** TENT (entropy minimization at test time) and AdaBN (batch normalization statistics update) both modify the model's behavior on the target domain without ground-truth labels. They are powerful, but they raise a governance question: when should the model be modified, and how do you know the modification improved things? In this pipeline, the governance layer (Stage 7) must approve any state change. TENT and AdaBN are available in the repository as experimental modes, but they are not the defended runtime default. The negative result from the unit-fix plus abstain experiment reinforces this: an intervention that changed routing behavior left mean confidence unchanged, showing that observable routing changes cannot substitute for verified quality improvement.

---

### Q: "What is the MMD drift branch and why is it not the defended runtime?"

**Short answer:** Calibrated Maximum Mean Discrepancy improves drift visibility and non-mutating risk alerts, but does not improve queue/retrain decisions under the tested policies. The defended runtime stays with the lightweight multi-signal z-score approach.

**Explanation:** The MMD branch experiment calibrated 500 reference-vs-reference comparisons to set an empirical warning threshold of 0.00276403 (95th percentile). With MMD active, drift warnings increased from 0/4 to 3/4 degraded datasets, and risk alerts increased from 0 to 3 with risk precision 1.0. However, queue/retrain decisions remained 0 in all tested policies because no behavior-risk signal corroborated the MMD drift signal under the configured thresholds. The result shows that monitoring sensitivity and governance quality are separate claims: a more sensitive detector does not automatically improve mutation decisions. MMD is retained as a calibrated offline audit and a future alerting direction, not as the defended runtime trigger.

---

## 7. Evaluation Results and User 7

### Q: "37.6% accuracy on User 7 — is that good?"

**Short answer:** It is the honest external accuracy ceiling under the defended contract on one external participant. It is not claimed as strong accuracy. It is claimed as honest reporting of cross-user generalization limits.

**Explanation:** 37.6% on 11 classes with a chance level of about 9% is above chance, but it is not strong. The thesis does not claim strong cross-user generalization — in fact, Chapter 8 explicitly records it as a non-claim. The important thing about the User 7 result is not the number itself, but what it tells us: the pipeline reports its honest accuracy limitation without inflation, the monitoring layer correctly identifies risk (low confidence 0.359, high uncertain rate, CRITICAL signals), and the governance layer routes to REVIEW rather than claiming success. That behavior is exactly what a governed system should do.

**What not to say:** Do not say "37.6% proves the system works as a classifier." Say: "37.6% is the honest external ceiling that the monitoring layer correctly identifies as uncertain and routes to review."

---

### Q: "What is the negative result? Why is it academically valuable?"

**Short answer:** A plausible intervention bundle (unit-fix + abstain) changed routing behavior without improving mean confidence at all — 0.8578 before and after. This shows that routing changes cannot be conflated with genuine quality improvement.

**Explanation:** The 26-session before/after experiment applied g-unit detection, stream-reuse guarding, and abstain-to-review behavior on low-confidence windows. The result: mean dominant-class share dropped from 81.17% to 67.34%, and review share increased to 66.09%. But mean confidence was unchanged at 0.8578 in both cases. The apparent improvement in dominance was entirely explained by routing windows into REVIEW, not by better class discrimination. This negative result is academically valuable because it forces a more disciplined interpretation of monitoring evidence: a change in routing distribution should not be reported as evidence of quality improvement unless the underlying quality signal also improves.

---

### Q: "What does the preprocessing ablation show?"

**Short answer:** Preprocessing consistency is not a cosmetic detail. Gravity removal alone worsened class collapse dramatically (configuration C: 5.32 unique classes, 96.72% hand-tapping dominance), while gravity removal combined with calibration produced the broadest diversity (configuration D: 9.72 unique classes, 50.14% dominance).

**Explanation:** The ablation ran 25 session pairs under four configurations: A (baseline), B (calibration only), C (gravity removal only), D (gravity removal + calibration). Configuration C is the clearest warning case: intuitively reasonable signal cleaning worsened collapse instead of improving it. This supports the thesis claim that train--serve parity is empirically visible and not just a theoretical concern: changing preprocessing at inference time without retraining can produce materially different behavior even if the model architecture and class taxonomy remain unchanged.

---

### Q: "What does the same-input old-vs-new comparison prove?"

**Short answer:** A same-input controlled rerun shows that the hand-tapping collapse on a fixed unlabeled session is primarily a property of the model, not the input data.

**Explanation:** The old model (pseudo-label fine-tuned) produced 85.6% top-class share and 9/11 classes on one unlabeled session. The new retrained model produced 29.0% top-class share and 11/11 classes on the same session. A controlled rerun of the old model reproduced the same collapse (85.64%, 9 classes). Because the input pair was held constant, the collapse cannot be attributed to the data. Across 25 sessions, the pseudo-label fine-tuned model was hand-tapping-dominant in 24/25 runs (mean dominant share 82.4%), while the raw retrained model was hand-tapping-dominant in 1/25 (mean share 37.2%). This motivates the collapse guard in Stage 7 and the requirement that training strategy is an auditable part of the governance record.

---

### Q: "Why is auto\_retrain=false on both defended evidence runs?"

**Short answer:** It is a deliberate governance policy, not a missing feature. Retraining requires labeled data and explicit human confirmation. The system detected risk and routed to REVIEW — that is the correct output for an uncertain, unlabeled production run.

**Explanation:** On both defended runs (Garmin unlabeled: 1,304 windows, mean conf 0.393; User 7: 37.6% accuracy, mean conf 0.359), the monitoring layer correctly detected risk across multiple signal groups, Stage 7 voted REVIEW, and `auto_retrain=false`. Retraining without confirmed labels would produce a model updated on low-confidence, potentially collapsed outputs — exactly the pseudo-label bias problem documented in the 25-session comparison. The system's response is correct: flag risk, route to human review, do not mutate the model.

---

## 8. Tools: Docker, FastAPI, MLflow, DVC, CI

### Q: "Why Docker?"

**Short answer:** Reproducible environment — both the inference path (FastAPI + Model A) and the full pipeline path are containerized, so the experiment can be reproduced from the same image.

**Explanation:** Two separate Dockerfiles (`docker/Dockerfile.inference`, `docker/Dockerfile.training`) minimize image size and attack surface. The inference image packages FastAPI, the Model A artifact, and the preprocessing stack. The training image adds the full ML dependencies. `docker-compose.yml` wires them with an MLflow server. A reviewer can `docker compose up` and run the defended pipeline without configuring Python environments manually.

**Scope note:** Prometheus, Alertmanager, and Grafana config files exist in the repository but are not part of the defended thesis implementation. The defended monitoring evidence comes from offline pipeline artifacts: monitoring JSONs, trigger reports, MLflow/DVC lineage. If asked, frame those three services as designed infrastructure for a future production extension.

---

### Q: "Why FastAPI and not Flask?"

**Short answer:** FastAPI provides async support, automatic OpenAPI documentation, and Pydantic validation out of the box — all useful for an inference endpoint that needs to accept wrist sensor uploads and return per-window predictions.

**Explanation:** The inference endpoint at `src/api/app.py` accepts raw CSV uploads via `POST /api/upload` and returns activity predictions with confidence scores per window. FastAPI's async model means it can handle preprocessing-heavy requests without blocking other requests. The OpenAPI schema auto-generated from function signatures makes the API self-documenting. The verified parity between the API path and the batch pipeline path (989/989 matching predictions) confirms that both execution paths use the same model contract.

---

### Q: "Why MLflow?"

**Short answer:** Self-hosted, open-source experiment tracking with a built-in model registry that links run parameters, input files, and output artifacts in a single traceable record.

**Explanation:** MLflow is configured under `config/mlflow_config.yaml` and tracks every pipeline run: configuration values, input file paths, per-stage metrics, and artifact locations. This is what makes the evidence in Chapter 7 reproducible rather than ad hoc — each result in the thesis tables can be traced to a run ID in the MLflow log. The model registry allows the governed model lifecycle to be audited: which checkpoint was evaluated, under which configuration, and what the outcome was. W&B would offer better visualization, but introduces an external cloud dependency and data residency concerns that are inappropriate for health-adjacent data.

---

### Q: "Why DVC?"

**Short answer:** Dataset and model artifact versioning so that run-specific results can be reproduced from versioned inputs, not from memory.

**Explanation:** DVC tracks input data files and model artifacts using content-addressed `.dvc` pointers. Any given thesis run can be reproduced by checking out the correct git commit and running `dvc pull` to restore the exact artifact versions linked to that commit. There is no `dvc.yaml` pipeline — DVC is used for artifact versioning only, while the Python orchestrator handles stage execution. The local DVC remote is a deliberate thesis-scope choice; migrating to S3 or GCS requires only changing `.dvc/config` remote URL, not restructuring the workflow.

---

### Q: "What does CI do?"

**Short answer:** Lint, unit tests (excluding slow model-training tests), and a Docker build viability check on every push.

**Explanation:** `.github/workflows/ci.yml` runs on push to `main`/`develop` and on PRs. The job chain is: lint → unit-tests → docker-build-check. Slow tests (model training, full pipeline integration) are excluded from CI by the `not slow` marker. The repository currently follows a CI-only stance. The previous CD workflow was removed because the defended thesis scope is reproducible proof-of-concept execution, not automatic deployment. CI verifies code correctness at the stage level; it does not constitute continuous deployment of the defended model.

---

## 9. Limitations and Future Work

### Q: "What are the explicit scope limits of this thesis?"

**Short answer:** Single machine, all_users corpus (6 participants), 1 external user, unlabeled runtime-style sessions, conservative governance only — no clinical claims, no population-level generalisation, no automated retraining.

**Explicit non-claims from Chapter 8:**

- No clinical diagnosis, population-level generalisation, or production-grade deployment
- Model A is a proof-of-concept runtime candidate, not a robust generalizing model
- Confidence calibration is not solved — mean confidence 0.359 on User 7, uncertain rate 80.5%
- External generalisation is not solved — one external participant
- Model B is a diagnostic reference, not a competing runtime candidate
- Model C is checkpoint-contract mismatch evidence, not a candidate
- auto\_retrain=false is a governance policy, not a gap
- CRITICAL is severity; REVIEW is action — they are separate
- Stages 8–11 are optional/gated extensions, not defended live runtime

---

### Q: "What would you do next if you had more time?"

**Short answer:** (1) labeled-evaluation expansion, (2) governed adaptation study (TENT/AdaBN under governance control), (3) class-collapse diagnosis and prevention, (4) trigger-policy longitudinal calibration, (5) automated figure/evidence regeneration, (6) cloud multi-user extension.

**Explanation:** The most impactful next step is labeled-evaluation expansion — a larger cross-subject labeled set would upgrade monitoring claims from "proxy observation" to "verified against known error rates." The second most impactful is a governed adaptation study that tests TENT and AdaBN within the Stage 7 governance gate rather than as unconstrained test-time modifications. The pseudo-label bias finding (25-session comparison) suggests a third direction: controlled study of which training strategies prevent collapse. The trigger-policy longitudinal calibration addresses the known gap that Stage 6 thresholds were calibrated against 26 curated sessions, not a multi-participant held-out deployment stream.

---

## 10. Examiner Challenge Questions

### Q: "37.6% is low. Why should the examiner accept this as a thesis contribution?"

**Short answer:** The contribution is not the accuracy number. The contribution is the lifecycle that makes the accuracy number honest, traceable, and acted on correctly.

**Explanation:** The claim is: an offline-first governed pipeline can be built such that (1) preprocessing contract is explicit and verified, (2) monitoring detects risk without ground-truth labels, (3) trigger policy suppresses false alarms while preserving episode recall, and (4) governance routes risk to human review rather than automatic mutation. The 37.6% accuracy is the honest ceiling — the system correctly identifies it as uncertain (CRITICAL severity, REVIEW action, auto\_retrain=false) and does not claim otherwise. A system that inflated internal scores (like Model B at 90.8%) while hiding the cross-user gap would be a weaker contribution, not a stronger one.

---

### Q: "Why not use TENT or AdaBN? That would have improved the external accuracy."

**Short answer:** Adaptation methods change the deployed artifact. In a label-scarce, health-adjacent setting, that requires governance justification. The thesis deliberately addresses when and whether to adapt, not just how.

**Explanation:** The thesis is about lifecycle governance, not about maximizing a single accuracy benchmark. TENT and AdaBN are available in the repository and evaluated as experimental modes. The reason they are not the defended runtime default is the same reason Level 2 automation is out of scope: unsupervised model mutation without governance is the unsafe pattern. The negative result from the unit-fix + abstain experiment shows that a plausible intervention changed routing behavior without improving quality — applying the same logic to model weights rather than routing labels would be even more risky. The correct research question is "under what conditions and governance controls should adaptation be applied?" — and that is identified as future work.

---

### Q: "Model B has a higher external accuracy than Model A (43.8% vs 37.6%). Why not defend Model B?"

**Short answer:** Model B's external accuracy comes from a non-persisted full-evaluation scaler that includes the external user's statistics at normalization time. The score is not reproducible as a deployment artifact.

**Explanation:** Model B fits its StandardScaler on the entire evaluation dataframe at runtime, including the external evaluation set. That means on User 7, the scaler encodes User 7's distribution — giving the model artificially favorable normalization. When Model B is assessed on the all\_users diagnostic set without external users, it reaches 90.8%. The 47pp internal-to-external gap is the forensic evidence that this scaler approach overstates transferability. Model A's 37.6% is lower, but it is reproducible under a fixed persisted scaler that was fitted only on training data, so the number is honest. A runtime candidate whose preprocessing statistics are recomputed from each evaluation batch is not a fixed reproducible runtime contract.

---

### Q: "Your system doesn't retrain automatically — is that a weakness?"

**Short answer:** No. auto\_retrain=false is a governance policy. The system detected risk, flagged it correctly, and routed to human review. Automatic retraining without confirmed labels and human review would be unsafe by design.

**Explanation:** The purpose of the governed pipeline is not to automate as much as possible; it is to automate what can be automated safely and to gate what requires human judgment. Without ground-truth labels at inference time, there is no way to confirm that a candidate retrained model is genuinely better before deploying it. The negative result from the 26-session unit-fix experiment makes this concrete: an apparently sensible intervention looked like improvement (lower dominance) but left the actual quality signal unchanged (mean confidence 0.8578). Automating retraining on unlabeled monitoring signals would create a pipeline that mutates itself in response to routing artifacts, not learning signals. Sculley et al. (2015) describe this as hidden technical debt; Chapter 8 frames it as the reason Level 2 automation is out of scope.

---

### Q: "Why is the monitoring threshold calibration uncertain? Is that a weakness?"

**Short answer:** The Stage 6 thresholds are engineering operating points calibrated against 26 runtime-style replay sessions and the training distribution. A multi-participant held-out longitudinal reference would be needed to establish them as statistically robust deployment limits. This is recorded as an explicit scope boundary, not hidden.

**Explanation:** The thresholds (confidence 0.70, uncertain windows 20%, transition rate 35%, drift z-score 1.8, dominant-class 85%) were set by calibrating against the available evidence: 6 training participants, 26 unlabeled production-style sessions, and the trigger-policy replay over 16 episodes. The thesis explicitly records this limitation in Chapter 8 with appropriate citations (Hendrycks and Gidaris 2017, Shewhart 1931, Montgomery 2009). The limitation is not hidden — it is stated as a scope boundary. The correct future work is a longitudinal multi-participant calibration study.

---

### Q: "Could this be used in a clinical setting?"

**Short answer:** No, and the thesis does not claim it could. The system is an engineering artifact, not a medical device or clinical assessment tool.

**Explanation:** A clinical system requires clinical validation: labeled cohorts of patients diagnosed by qualified clinicians, rigorous test methodology following clinical evaluation frameworks, regulatory assessment, and typically a randomized trial. None of those are part of this thesis. The system recognizes motor behaviors from wrist IMU data. Whether a recognized hand-tapping sequence is clinically significant is a judgment that requires clinical context — not a software decision. Chapter 2 anchors this explicitly: the thesis treats anxiety-related repetitive activities as observable behavioral proxies used to study the engineering problem of building a reproducible, governed MLOps pipeline. That framing is both honest and sufficient to justify the thesis topic.

---

### Q: "Why grouped cross-validation instead of leave-one-subject-out?"

**Short answer:** Grouped cross-validation with user IDs as groups is more defensible than naive window-level splitting, and is the correct implementation for this dataset size. Leave-one-subject-out (LOSO) would be more realistic for deployment generalization but is out of scope for the thesis contribution.

**Explanation:** Naive window-level splitting would place windows from the same participant in both training and test folds, inflating held-out accuracy because the model has seen other windows from the same person. Grouped cross-validation prevents this. LOSO would further ensure that each fold holds out an entire participant — the gold standard for estimating subject-independent accuracy. The thesis acknowledges this as a known limitation in Chapter 8 and notes that the six-participant dataset is too small to draw robust LOSO generalization conclusions. The grouped CV results (labeled reference: 98.9%) establish that the baseline model is competent on matched data; the User 7 external evaluation (37.6%) establishes the honest cross-user ceiling.

---

### Q: "Is 98.9% labeled reference accuracy inconsistent with 37.6% on User 7?"

**Short answer:** No, and there is no contradiction — they belong to different experiments. The 98.9% result belongs to the earlier labeled reference / pre-sprint baseline experiment, not to the defended Model A proof-of-concept runtime candidate. The 37.6% is Model A's external evaluation on User 7, a different participant. Cross-user domain shift is well documented in wearable HAR literature and is expected.

**Explanation:** This is not a paradox — it is the core finding the thesis documents. When train and test conditions are aligned (same participants, same sensor, same session structure), the model performs strongly. When they are not aligned (different participant), performance drops sharply. The entire monitoring and governance apparatus is designed precisely because this gap exists and because it can appear at deployment time without obvious warning. The monitoring layer on the User 7 run correctly flagged low confidence and high uncertainty — the system reported the gap, not hid it.

---

*All numbers sourced from archived run artifacts, Chapter 7 tables, and Chapter 8 non-claims list.*
*Wording rules: never "data leakage" for Model B; use "non-persisted full-evaluation scaler and legacy native setup limit transferability." Always "proof-of-concept runtime candidate" for Model A. Always "CRITICAL is severity; REVIEW is governance action."*

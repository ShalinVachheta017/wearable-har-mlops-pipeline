# HAR MLOps Pipeline — Complete Project Deep Dive

> **Purpose:** Understand, recreate, and explain this project from zero. Covers every decision with *why*, *why not*, *when*, *where*, *what*, and *how*. Use this for interview prep, future projects, and knowledge transfer.

---

## Table of Contents

- [System at a Glance](#system-at-a-glance) — *read this first*
- [Why This Is a Valid Thesis](#why-this-is-a-valid-thesis) — *the research framing*
- [Design Decisions — Why This, Why Not That](#design-decisions--why-this-why-not-that) — *every fork in the road*
- [The Modular Architecture Philosophy](#the-modular-architecture-philosophy) — *the reusable template*
1. [The Problem](#1-the-problem)
2. [Why MLOps for a Thesis?](#2-why-mlops-for-a-thesis)
3. [Dataset](#3-dataset)
4. [Project Structure — Why This Layout?](#4-project-structure--why-this-layout)
5. [The 7-Stage Pipeline](#5-the-7-stage-pipeline)
6. [The Model (D1)](#6-the-model-d1)
7. [Windowing — The Core Preprocessing Decision](#7-windowing--the-core-preprocessing-decision)
8. [Evaluation Strategy — LOUO vs 5-Fold CV](#8-evaluation-strategy--louo-vs-5-fold-cv)
9. [Monitoring — Three Layers](#9-monitoring--three-layers)
10. [Governance — No Auto-Retrain](#10-governance--no-auto-retrain)
11. [Experiment Tracking with MLflow](#11-experiment-tracking-with-mlflow)
12. [Data Versioning with DVC](#12-data-versioning-with-dvc)
13. [The WebUI (FastAPI Dashboard)](#13-the-webui-fastapi-dashboard)
14. [Runtime Contract](#14-runtime-contract)
15. [Docker — Two Images](#15-docker--two-images)
16. [Dependencies — Why Each One](#16-dependencies--why-each-one)
17. [Technical Tools — Deep Dive](#17-technical-tools--deep-dive)
18. [How to Recreate This Project](#18-how-to-recreate-this-project)
19. [Extending to Cloud or Edge](#19-extending-to-cloud-or-edge)
20. [Interview Q&A Prep](#20-interview-qa-prep)

---

## System at a Glance

Before the details, here is the whole system on one screen. Everything below is just a zoom-in on a piece of this picture.

```
                            HAR MLOps SYSTEM
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  OFFLINE (once)                          PRODUCTION (repeats forever)      │
│  ───────────────                         ────────────────────────────     │
│                                                                            │
│  Garmin watch                                                              │
│  ┌──────────┐    ┌──────────────────┐         ┌──────────────────────┐    │
│  │ accel +  │───▶│  Train notebook  │         │   run_pipeline.py    │    │
│  │ gyro CSV │    │ • window data    │         │   7 stages:          │    │
│  └──────────┘    │ • fit scaler     │         │   ingest → validate  │    │
│                  │ • train CNN+LSTM │         │   → transform →      │    │
│                  │ • 5-fold + LOUO  │         │   infer → evaluate   │    │
│                  └────────┬─────────┘         │   → monitor → trigger│    │
│                           │                   └──────────┬───────────┘    │
│                           ▼                              │                │
│              ┌─────────────────────────────┐            │                │
│              │   RUNTIME CONTRACT (4 files) │            │                │
│              │   model.keras  scaler.json   │◀───reads───┘                │
│              │   baseline.json label.json   │◀───reads───┐                │
│              └─────────────────────────────┘            │                │
│                                                          │                │
│  FastAPI WebUI  ─────── upload a session ────────────────┘                │
│  ┌────────────────────────────────────────┐                              │
│  │ see: predictions + 3-layer monitoring   │                              │
│  │      + governance decision              │                              │
│  └────────────────────────────────────────┘                              │
│                           │                                                │
│                           ▼                                                │
│              ┌────────────────────────┐                                   │
│              │  MLflow  (logs runs)   │   DVC  (versions data + model)     │
│              └────────────────────────┘                                   │
│                           │                                                │
│                           ▼                                                │
│              Docker packages it all  →  runs anywhere                      │
└──────────────────────────────────────────────────────────────────────────┘
```

### The mental model (analogies that stick)

These analogies are worth memorizing — they make the whole system click, and they are great for explaining it in an interview.

| Concept | Think of it as... | Because |
|---|---|---|
| **Runtime contract** | A **passport** | The model can't travel anywhere without its 4 documents stamped together. |
| **DVC** | A **coat-check ticket** | Git holds the small ticket; the heavy coat (data) sits in storage. |
| **Docker image** | A **shipping container** | Packed once, runs identically on any ship (machine). |
| **MLflow** | A **flight recorder** (black box) | Logs everything that happened on every run, for later audit. |
| **3 monitoring layers** | **Three smoke detectors** | Heat, smoke, CO — each catches a different kind of fire. |
| **The scaler** | A **translator** | After milliG→m/s², a z-score scaler (users 1–6) maps values into the scaled "language" the model was trained on. |
| **Windowing** | **Film frames** | Continuous motion sliced into fixed 4-second clips. |
| **Governance gate** | A **two-key launch protocol** | Multiple keys must turn together before anything fires. |

### The one-sentence story

> Raw watch data is **converted to m/s² and z-score-scaled** (the deployed contract), **sliced into 4-second windows**, **classified by a CNN+LSTM model** into 11 anxiety-linked behaviors, **watched by three monitors**, and **governed by a gate that never lets the model retrain itself** — with every run **recorded by MLflow** and every file **versioned by DVC**, all **packaged in Docker**.

---

## 1. The Problem

**What:** Detect anxiety-related physical activities from wrist-worn sensor data (Garmin smartwatch).

**Why this matters:** Anxiety disorders are among the most common mental health conditions. Wearable sensors offer a passive, continuous monitoring path — no self-reporting needed. Human Activity Recognition (HAR) is the bridge: classify what activity the person is doing, then build anxiety-linked patterns from that.

**Why HAR and not direct anxiety detection?**
- Direct physiological anxiety signals (HRV, GSR) require medical-grade sensors.
- Accelerometer + gyroscope are standard in consumer wearables.
- Activity patterns (restlessness, avoidance, fidgeting) are indirect but detectable proxies.

**The research gap:** Most HAR papers stop at model accuracy. Nobody asks: *what happens after deployment?* This thesis answers that question with an MLOps pipeline.

---

## 2. Why MLOps for a Thesis?

**MLOps = ML + Operations.** It is the discipline of getting models from notebooks into reliable, monitored, maintainable production systems.

**Why not just train a model and report accuracy?**

| Notebook approach | MLOps approach |
|---|---|
| Train once, report accuracy | Train → deploy → monitor → govern |
| No reproducibility | Every run tracked (MLflow + DVC) |
| Model = static artifact | Model has a lifecycle (drift → review → retrain) |
| No deployment story | FastAPI + Docker + runtime contract |
| No failure handling | Stage-by-stage fail-fast with status tracking |

**The thesis claim:** A HAR model deployed without monitoring will silently degrade. This pipeline detects and governs that degradation.

---

## Why This Is a Valid Thesis

A master's thesis is not "I built an app." It needs three things: a **gap** in existing knowledge, a **contribution** that addresses it, and **critical evaluation** of the result. Here is how this project delivers all three — and why each design choice serves the research, not just the code.

### The gap (what the world is missing)

Wearable HAR research is *mature on modeling* — hundreds of papers report accuracy on benchmark datasets. But two things are consistently under-addressed:

1. **The deployment lifecycle is ignored.** Papers report one accuracy number and stop. What happens when the model meets a *new* user, a *drifted* sensor, or an *unlabeled* live stream? Largely unstudied.
2. **Cross-person evaluation is often optimistic.** Many papers report mixed-user cross-validation (which lets the model peek at every subject) without Leave-One-User-Out. The result: the *personalization gap* is hidden behind a flattering number.

### The contribution (what this thesis adds)

A **reference MLOps architecture for wearable HAR**, concretely:

| Contribution | Why it's novel/useful |
|---|---|
| Reproducible modular 7-stage pipeline | Raw sensor → governed decision, every run tracked + versioned |
| Three-layer **label-free** monitoring | Detects degradation when no ground truth exists (the production reality) |
| Explicit **no-auto-retrain** governance | Makes the safety invariant auditable, not implicit |
| Honest **dual reporting** (5-fold *and* LOUO) | Quantifies the personalization gap instead of hiding it |

### Why it's master's-level (not "just engineering")

- **Systems integration as research:** combining modeling, serving, monitoring, versioning, and governance into one coherent, defensible system is itself the contribution.
- **Critical evaluation:** the LOUO collapse (93% → 44%) is *analyzed*, not buried. Limitations (uncalibrated confidence, small subject count) are stated openly.
- **Reproducibility:** every run tracked (MLflow) and every artifact versioned (DVC) — a scientific requirement, not a nicety.

### The thesis statement (memorize this)

> *A HAR model that performs well in-distribution can fail silently on unseen users; an MLOps pipeline with label-free monitoring and explicit retraining governance can detect that failure and manage the model's lifecycle safely.*

> 🎓 **Why this matters for your defense:** every chapter maps to one clause of that sentence. Modeling → "performs well in-distribution." LOUO → "fails on unseen users." Monitoring → "detect that failure." Governance → "manage the lifecycle safely." If a section doesn't serve a clause, it doesn't belong.

---

## Design Decisions — Why This, Why Not That

This is the heart of the "why." Every project is a series of forks in the road. At each fork there were other paths — here is what was chosen, what was rejected, **why**, and **when you would choose differently.** This is exactly the reasoning an examiner probes, and exactly what you reuse when designing your *next* system.

### Decision summary (scan this, then read the ones you care about)

| # | The fork | Chosen | Main reason |
|---|---|---|---|
| 1 | Batch vs streaming | **Batch** | Research is about lifecycle, not latency |
| 2 | Modular vs notebook/monolith | **Modular components** | Testable, reproducible, auditable |
| 3 | Model family | **1D-CNN + BiLSTM** | Best fit for small-N temporal sensor data |
| 4 | Config style | **Central YAML** | Single source of truth, reproducible |
| 5 | Stage I/O | **Typed Artifact dataclasses** | Fails at type-check, not at runtime |
| 6 | Scaler format | **JSON** | Readable, portable, version-stable |
| 7 | Web framework | **FastAPI** | Async + validation + auto-docs |
| 8 | Experiment tracking | **MLflow** | Free, local, full lifecycle |
| 9 | Data versioning | **DVC** | Git-linked, storage-agnostic |
| 10 | Docker images | **Two (slim + full)** | Small/safe production surface |
| 11 | Retraining | **Human-gated, never auto** | Safety in a health domain |
| 12 | Monitoring | **3 hand-built layers** | Works without labels; explainable |
| 13 | Hosting | **Local-first** | Reproducible on examiner's laptop |
| 14 | Model format | **`.keras`** | Single-file, portable, hashable |

---

#### Decision 1 — Batch pipeline, not real-time streaming
- **Chosen:** process a whole session file at once (batch).
- **Alternatives:** real-time per-window streaming; micro-batching.
- **Why not them:** the research question is about the *lifecycle and monitoring*, not latency. Streaming adds heavy infrastructure (a message broker, windowing state, backpressure handling) with **zero research payoff**. Anxiety-related activity detection does not need sub-second response.
- **Choose differently when:** latency *is* the product — fall detection, arrhythmia alerts, live captioning.

#### Decision 2 — Modular components, not a notebook or one big script
- **Chosen:** one class per stage, typed artifacts, a thin orchestrator.
- **Alternatives:** a single Jupyter notebook; one monolithic script; a heavy DAG framework (Airflow / Kedro / ZenML / Dagster).
- **Why not them:** a notebook has hidden state, is hard to test, and is irreproducible. A monolith script can't be unit-tested and one failure kills everything. A heavy DAG framework makes you spend your thesis time learning the *framework* instead of doing the *research*. Hand-rolled modular components are the sweet spot: testable + readable + no infrastructure.
- **Choose differently when:** you run many scheduled pipelines with retries across a team → adopt Airflow/Kedro/ZenML.

#### Decision 3 — 1D-CNN + BiLSTM, not Transformer / classical ML / plain LSTM
- **Chosen:** a 1D-CNN front-end feeding a Bidirectional LSTM.
- **Alternatives:** Transformer; pure 1D-CNN; Temporal Convolutional Network (TCN); classical ML (Random Forest / SVM on hand-crafted features); plain LSTM.

| Alternative | Why not (here) |
|---|---|
| Transformer | Data-hungry; with few subjects it overfits; heavier to train and serve |
| Classical ML + hand features | Strong baseline but plateaus; needs manual feature engineering; discards raw temporal structure |
| Pure CNN | Great at local patterns, weak at long-range temporal context |
| Plain LSTM | Slower to converge, noisier without a CNN front-end |
| TCN | Genuinely viable and comparable — CNN-BiLSTM chosen for its established HAR track record and mentor's prior work |

- **Choose differently when:** you have a large dataset (→ Transformer), an ultra-low-power microcontroller (→ tiny CNN/TCN), or interpretability is paramount (→ classical ML + SHAP).

#### Decision 4 — Central YAML config, not hardcoded constants or CLI flags
- **Chosen:** one `pipeline_config.yaml` read by every stage.
- **Alternatives:** hardcoded constants in code; an argparse CLI; environment variables; Hydra.
- **Why not them:** hardcoding scatters magic numbers everywhere; a CLI with 30 parameters is unusable; env vars handle flat secrets, not nested config. Hydra is excellent but adds a dependency and concepts unjustified for a single pipeline.
- **Choose differently when:** you run large hyperparameter sweeps or compose many configs → Hydra earns its keep.

#### Decision 5 — Typed Artifact dataclasses, not raw dicts or path strings
- **Chosen:** each stage returns a typed `@dataclass` artifact.
- **Alternatives:** plain dicts; tuples; passing file-path strings around.
- **Why not them:** dicts are typo-prone (`artifact["windws"]` fails silently at runtime), give no IDE autocomplete, and have no schema. Dataclasses fail at *import / type-check* time — the cheapest place to catch a bug.
- **Choose differently when:** writing genuinely throwaway prototype code.

#### Decision 6 — JSON scaler, not pickle/joblib
- **Chosen:** store the scaler as `{"mean_": [...], "scale_": [...]}` in JSON.
- **Alternatives:** `pickle`, `joblib`, or baking the scaler into the model graph.
- **Why not them:** pickle/joblib are version-fragile (a different sklearn version can fail to load), are opaque binaries, and are a security risk to load from untrusted sources. JSON is human-readable, language-agnostic (you could re-implement the math in C for an edge device), and stable across versions.
- **Choose differently when:** you have a complex multi-step sklearn `Pipeline` → joblib is the pragmatic choice.

#### Decision 7 — FastAPI, not Flask / Django / Streamlit / Gradio
- **Chosen:** FastAPI for the serving dashboard.
- **Alternatives:** Flask, Django, Streamlit, Gradio.
- **Why not them:** Streamlit/Gradio are wonderful for *demos* but are not real, testable, deployable services and give little control over the request lifecycle. Django is too heavy (ORM, admin, migrations) for a stateless inference service. Flask works but you hand-build validation, docs, and async. FastAPI gives async, Pydantic validation, and auto-generated OpenAPI docs out of the box.
- **Choose differently when:** you only need a throwaway visual demo → Streamlit/Gradio in 20 lines.

#### Decision 8 — MLflow, not Weights & Biases / Neptune / TensorBoard / plain logs
- **Chosen:** MLflow, run locally.
- **Alternatives:** Weights & Biases, Neptune, TensorBoard, CSV log files.
- **Why not them:** W&B/Neptune are cloud-first — they need accounts and API keys and your run data leaves the machine (a real concern for a health dataset), with paid tiers beyond limits. TensorBoard is TF-only and shows scalars/graphs, not a full run lifecycle with artifacts and a model registry. CSV logs have no UI and aren't queryable. MLflow is free, local, open-source, framework-agnostic, and covers tracking + artifacts + registry.
- **Choose differently when:** a large team needs hosted, collaborative dashboards → W&B.

#### Decision 9 — DVC, not Git-LFS / raw cloud bucket / nothing
- **Chosen:** DVC for data and model versioning.
- **Alternatives:** Git-LFS; a manually managed S3 bucket; committing data straight into git; nothing.
- **Why not them:** committing data bloats the git history forever and clones crawl. Git-LFS ties storage to your git host with paid quotas and has no pipeline/lineage features. A raw bucket has no versioning semantics and no link back to the exact git commit. DVC is storage-agnostic (local, S3, GCS, SSH), versions data *linked to git commits*, and tracks pipeline lineage.
- **Choose differently when:** you only version a model or two and already live on the Hugging Face Hub → HF + LFS may be enough.

#### Decision 10 — Two Docker images, not one
- **Chosen:** a slim inference image and a full training image.
- **Alternatives:** one big image for everything; a single multi-stage Dockerfile.
- **Why not them:** one image ships dev/training tools to production — bigger, slower, larger attack surface, and it lets someone trigger training from the serving container. (A multi-stage Dockerfile is actually a fine alternative that achieves the same separation in one file.)
- **Choose differently when:** you prefer one file to maintain → use a multi-stage build to emit both a slim and a full target.

#### Decision 11 — Human-gated retraining, never automatic
- **Chosen:** `should_retrain = False` is hardcoded; retraining requires labels + QA + human approval.
- **Alternatives:** continuous training (CT); scheduled retraining; online/incremental learning.
- **Why not them:** in a *health* domain, an automatic update on uncertain or mislabeled production data is an ethical and safety hazard with no audit trail. Online learning can be poisoned by a single bad session. CT only pays off when you have a trustworthy, high-volume label stream — which wearable anxiety data does not.
- **Choose differently when:** abundant trustworthy labels in a low-risk domain (e.g. ad ranking, recommendations) → CT is the right call.

#### Decision 12 — Three hand-built monitoring layers, not one metric or a heavy library
- **Chosen:** confidence + temporal consistency + drift, implemented transparently.
- **Alternatives:** a single accuracy metric; a full drift suite (Evidently / NannyML / Alibi-Detect).
- **Why not them:** accuracy *needs labels*, which production data lacks — so it can't be your production monitor. Heavy libraries add dependencies and opacity; for a thesis you must be able to explain every number on a slide, and hand-built layers are fully transparent and defensible.
- **Choose differently when:** running at production scale → Evidently/NannyML give richer, maintained, battle-tested drift detection.

#### Decision 13 — Local-first, not cloud-native
- **Chosen:** everything runs on one machine; cloud is documented as a *future* path.
- **Alternatives:** cloud-native from day one (S3 + SageMaker / Vertex AI).
- **Why not them:** a thesis must be reproducible on the examiner's laptop with no cloud bill, no account friction, and no data leaving the machine. Cloud adds cost and complexity without research payoff. (Section 19 shows the exact migration path when real scale arrives.)
- **Choose differently when:** you have real users, real scale, and a team → go cloud.

#### Decision 14 — `.keras` format, not `.h5` / SavedModel / ONNX
- **Chosen:** the single-file `.keras` format.
- **Alternatives:** legacy `.h5`; TensorFlow `SavedModel` directory; ONNX.
- **Why not them:** `.h5` is legacy and fragile with custom objects; `SavedModel` is a directory (clumsier to hash and version as one artifact); ONNX is excellent for cross-runtime/edge but adds a conversion step not needed for CPU serving.
- **Choose differently when:** you need cross-framework or edge runtimes → export to ONNX or TFLite.

---

## The Modular Architecture Philosophy

This is the **transferable** part — the template you can lift into *any* ML thesis or project. If you remember nothing else, remember these four building blocks and the rules around them.

### The core principle: separation of concerns

Each piece does **one job** and knows as little as possible about the others. A stage knows its inputs and its outputs — nothing about how any other stage works inside. Change one stage's internals and nothing else needs to know.

### The four building blocks (reusable pattern)

```
            ┌──────────────────────────────────────────┐
            │              ORCHESTRATOR                 │  ← decides ORDER
            │   (production_pipeline.py: stage1→…→7)    │
            └───────────────────┬──────────────────────┘
                                │ runs each stage in turn
            ┌───────────────────▼──────────────────────┐
            │   CONFIG  ──▶  COMPONENT  ──▶  ARTIFACT    │
            │   (what)       (how)          (result)     │
            │   settings     logic, 1 job   typed output │
            └───────────────────────────────────────────┘
                                │ artifact becomes next stage's input
                                ▼
```

| Block | Answers | Contains | Example |
|---|---|---|---|
| **Config** | *what* to do | data only (paths, thresholds) | `TransformationConfig(window=200)` |
| **Component** | *how* to do it | logic, one responsibility | `class DataTransformation` |
| **Artifact** | *what was produced* | typed data only | `DataTransformationArtifact(path=…)` |
| **Orchestrator** | *in what order* | flow, no stage logic | `ProductionPipeline.run()` |

### Why this gives you superpowers

- **Testable:** hand a component a fake config + a fake input artifact, assert on its output — no need to run the whole pipeline.
- **Replaceable:** swap Stage 1 from "read CSV" to "read from Kafka"; as long as it returns the same artifact, nothing downstream changes.
- **Auditable:** every cross-stage value is a typed object you can log and inspect.
- **Parallelizable (team):** people own different components without merge conflicts.
- **Fail-fast:** each stage validates its inputs first; the chain stops at the broken link instead of corrupting everything after it.

### The "config as single source of truth" rule

All knobs live in **one** YAML. Code *reads* config; code never hardcodes a path or a threshold. You change behavior by editing config, not code — which is precisely what makes an experiment reproducible: **the config file *is* the experiment.**

### Design patterns used (name them in your defense)

| Pattern | Where it shows up |
|---|---|
| **Factory** | the config factory builds each stage's config object |
| **DTO / Dataclass** | artifacts are data-transfer objects between stages |
| **Dependency Injection** | config is passed *into* a component, not built inside it |
| **Pipeline / Chain of Responsibility** | stage N hands off to stage N+1 |
| **Single Responsibility Principle** | one class, one job, one reason to change |

### How to apply this to YOUR next project (copy this template)

```
yourproject/
├── src/
│   ├── components/      # one file per stage — the "how"
│   ├── pipeline/        # config factory + orchestrator — the "order"
│   └── <domain>/        # your domain logic (monitoring, calibration, …)
├── config/              # one YAML = one source of truth — the "what"
├── models/              # versioned artifacts (your "runtime contract")
├── tests/               # one test file per component
└── run_pipeline.py      # the single entrypoint
```

**Rules of thumb (tape these to your monitor):**

1. If a function is longer than one screen, split it.
2. If you copy a constant twice, move it to config.
3. If stage A needs to know how stage B works *inside*, your boundaries are wrong.
4. Every value that crosses a stage boundary should be a **typed object**, not a loose dict.
5. Every component gets a test before you trust it.

> 💡 **This is the real reusable asset.** The HAR model is specific to this thesis; this *architecture* is something you can rebuild for any ML system — fraud detection, churn, recommendation, anything with a data-in → decision-out shape.

---

## 3. Dataset

**Source:** Garmin Venu 3 wrist sensor data collected by second supervisor and examiner M.Sc. Ugonna Oleh (University of Siegen).

**Sensors used:**
- Accelerometer: 3-axis (x, y, z) in m/s²
- Gyroscope: 3-axis (x, y, z) in deg/s
- Combined: 6 input features

**Sampling rate:** 50 Hz (50 samples per second)

**Activity classes:** 11 anxiety-linked behaviors — mostly *body-focused repetitive behaviors* (BFRBs) plus postures/habits: `ear_rubbing`, `forehead_rubbing`, `hair_pulling`, `hand_scratching`, `hand_tapping`, `knuckles_cracking`, `nail_biting`, `nape_rubbing`, `sitting`, `smoking`, `standing`. The behaviors themselves *are* the anxiety signal — nail-biting and hair-pulling are textbook BFRBs.

**Users:** Multiple subjects. User 7 is the held-out test subject used for LOUO evaluation.

**Why 50 Hz?** It captures fine-grained motion without excessive data volume. Standard for wrist HAR research.

**The deployed preprocessing: unit conversion → z-score scaler.** Two steps, in order:
1. **Unit conversion** — milliG → m/s² (factor `0.00980665`); gyroscope stays in deg/s. `model_contract.json` records this physical-unit space (`accelerometer_unit: "m/s^2"`, `gyroscope_unit: "deg/s"`).
2. **Z-score StandardScaler** — `garmin_train_scaler.json`, fit on **Garmin users 1–6 only** (User 7 excluded), applied *after* unit conversion. Its `fit_rule` says exactly that.

**Why this is the deployed contract (not raw units):** the model was *trained* on scaled windows (the build notebook scales per-fold and for the final freeze), so inference must scale too. The production config `config/pipeline_config.yaml` sets `enable_normalization: true` (the dataclass default `False` is only a fallback). All three paths — build notebook, batch pipeline (with the production YAML), and the WebUI — apply the scaler, so they agree.

> ⚠️ **Don't confuse two things:** the *paper baseline* (Oleh & Obermaisser, ICTH 2025) used **no external scaler** (milliG→m/s²→window only). The **deployed Model D1 adds** the users-1–6 train-only StandardScaler as part of its contract. So "raw physical units" describes the paper/A-B path; the deployed model expects **z-score-scaled** input.

### What the data actually looks like

The 6 channels are 3 accelerometer axes + 3 gyroscope axes. One "row" is one 50 Hz sample (every 20 ms). One "window" is 200 rows stacked together:

```
       ACCELEROMETER (m/s²)      GYROSCOPE (deg/s)
      ┌─────┬─────┬─────┬─────┬─────┬─────┐
 t=0  │ ax  │ ay  │ az  │ gx  │ gy  │ gz  │  ← one sample (20 ms)
 t=1  │ ax  │ ay  │ az  │ gx  │ gy  │ gz  │
 t=2  │ ax  │ ay  │ az  │ gx  │ gy  │ gz  │
  ··  │ ··  │ ··  │ ··  │ ··  │ ··  │ ··  │   200 rows = 4 seconds
  ··  │ ··  │ ··  │ ··  │ ··  │ ··  │ ··  │
t=199 │ ax  │ ay  │ az  │ gx  │ gy  │ gz  │
      └─────┴─────┴─────┴─────┴─────┴─────┘
       └──────────── 6 columns ───────────┘

      shape = [200, 6]  ──▶  MODEL  ──▶  11 class probabilities  P(ear_rubbing) … P(standing)
```

> 💡 **Key insight:** The model never sees "raw CSV." It sees fixed `[200, 6]` numeric blocks. Everything in Stage 1–3 exists to turn messy sensor files into these clean blocks.

---

## 4. Project Structure — Why This Layout?

```
MasterArbeit_MLops/
├── src/
│   ├── components/         # One file per pipeline stage
│   ├── pipeline/           # Orchestrator + config factory
│   ├── api/                # FastAPI WebUI (app.py)
│   └── monitoring/         # Baseline builder, post-inference monitor
├── config/
│   ├── pipeline_config.yaml    # Single source of truth for all paths/thresholds
│   ├── requirements.txt        # Full deps (training + dev)
│   └── requirements-runtime.txt # Slim deps (inference only)
├── models/
│   └── runtime_contract/       # Deployed model + scaler + baseline + label_order
├── docker/
│   ├── Dockerfile.inference    # Slim image for WebUI serving
│   └── Dockerfile.training     # Full image for pipeline + training
├── tests/                  # pytest suite
├── notebooks/              # Training notebooks (mentor's + experimental)
├── docs/                   # Pipeline stage map, architecture notes
├── scripts/                # One-off analysis scripts
├── thesis/                 # LaTeX source for the written thesis
├── artifacts/              # Pipeline run outputs (gitignored)
├── mlruns/                 # MLflow tracking (gitignored)
├── run_pipeline.py         # Main entrypoint
└── pyproject.toml          # Minimal project config + pytest settings
```

**Why `src/components/` one-file-per-stage?**
Each stage is independently testable, replaceable, and auditable. If Stage 3 breaks, you don't touch Stage 4.

**Why `config/pipeline_config.yaml`?**
Centralizes all thresholds, paths, and flags. Change one value, it propagates everywhere. No magic numbers scattered in code.

**Why separate `models/runtime_contract/`?**
The deployed model is a fixed, versioned artifact. It should never be overwritten by a pipeline run without a deliberate promotion step. Keeping it separate makes accidental mutation obvious.

---

## 5. The 7-Stage Pipeline

**Entrypoint:** `run_pipeline.py` → `src/pipeline/production_pipeline.py`

Each stage produces an *Artifact* object (a typed dataclass) and a *Config* object. The artifact of stage N is the input to stage N+1.

| # | Stage | File | What it does |
|---|---|---|---|
| 1 | Ingestion | `data_ingestion.py` | Fuse accel + gyro CSVs into one 50 Hz stream |
| 2 | Validation | `data_validation.py` | Schema, range, frequency checks — fail fast if data is bad |
| 3 | Transformation | `data_transformation.py` | Unit conversion → windowing → `production_X.npy` |
| 4 | Inference | `model_inference.py` | Load model + scaler → predict → save predictions |
| 5 | Evaluation | `model_evaluation.py` | Confidence analysis + metrics if labels present |
| 6 | Monitoring | `post_inference_monitoring.py` | 3-layer health check (confidence, temporal, drift) |
| 7 | Trigger | `trigger_evaluation.py` | Governance decision: NO_ACTION / MONITOR / REVIEW / RETRAIN |

**Stages 8-10** (retraining, registration, baseline update) are conditional — gated by human review, labels, and QA evidence. They are never triggered automatically.

**Stage 11** (calibration/uncertainty) is optional research work.

**Why fail-fast at each stage?**
If validation fails, running inference on bad data wastes time and produces misleading results. Each stage checks its inputs before proceeding.

**Why Artifact objects instead of raw file paths?**
Type safety. The orchestrator knows exactly what each stage produced and what the next stage needs. No path string mismatches.

### How the stages connect (the artifact chain)

Each stage hands a typed *Artifact* to the next. It is a relay race — the baton is the artifact:

```
run_pipeline.py
      │
      ▼
┌──────────────┐  DataIngestionArtifact       ┌───────────────┐
│ 1. INGESTION │ ──── fused_csv_path ────────▶│ 2. VALIDATION │
└──────────────┘                              └───────┬───────┘
                                                      │ status = PASSED
            ┌─────────────────────────────────────────┘
            ▼
┌──────────────────┐  windows_path (.npy)       ┌──────────────┐
│ 3. TRANSFORMATION│ ──── [N, 200, 6] ─────────▶│ 4. INFERENCE │
└──────────────────┘                            └──────┬───────┘
                                                       │ predictions + confidence
            ┌───────────────────────────────────────────┘
            ▼
┌──────────────┐  metrics + report          ┌───────────────┐
│ 5. EVALUATION│ ─────────────────────────▶ │ 6. MONITORING │
└──────────────┘                            └───────┬───────┘
                                                    │ 3-layer health status
            ┌────────────────────────────────────────┘
            ▼
┌──────────────┐
│ 7. TRIGGER   │ ──▶  NO_ACTION │ MONITOR │ REVIEW │ RETRAIN
└──────────────┘
```

> 🔑 **If a stage fails, the chain stops there.** No bad data ever reaches the model. This is "fail-fast" — you find out at Stage 2 that the data is broken, not after wasting time on inference.

---

## 6. The Model (D1)

**Architecture:** 1D CNN + Bidirectional LSTM (1DCNNBiLSTM)

**Why this architecture?**

- **1D CNN:** Extracts local temporal features from the raw sensor signal (e.g., a step pattern over 0.2 seconds). Efficient, fast.
- **Bidirectional LSTM:** Captures long-range dependencies in both forward and backward time directions. Important for activities with buildup (e.g., sitting-down vs sitting-still).
- **Combined:** CNN reduces dimensionality before LSTM, making training stable and fast.

### The architecture, layer by layer

```
  INPUT  [200, 6]              ── 4 seconds of 6-channel sensor data
    │
    ▼
  Conv1D(64, kernel=3)         ── slides a 3-step filter, learns local motion patterns
    │                             (e.g. "the shape of one footstep")
    ▼
  MaxPooling1D(2)              ── halves the length: 200 → 100, keeps strongest signals
    │
    ▼
  Bidirectional LSTM(64)       ── reads the sequence forwards AND backwards,
    │                             captures "what led up to" and "what follows" each moment
    ▼
  Dense(64, relu)              ── combines features
    │
    ▼
  Dense(11, softmax)           ── outputs 11 probabilities that sum to 1.0
    │
    ▼
  OUTPUT [0.01, …, 0.88, …]    ── argmax → class 2 ("hair_pulling"), confidence 0.88
```

| Layer | Job | Analogy |
|---|---|---|
| Conv1D | Finds short local patterns | Spotting individual dance steps |
| MaxPooling | Keeps only the strongest signals | Summarizing — "lots of movement here" |
| BiLSTM | Understands the sequence over time | Watching the whole dance to name it |
| Dense + softmax | Turns features into a decision | The judge giving final scores |

**Why not a Transformer?**
Transformers need large datasets. With ~10 users of wearable data, a CNN-BiLSTM generalizes better and trains in minutes on CPU.

**Why not a pure LSTM?**
Without the CNN front-end, the LSTM sees raw 6-channel input at every timestep. Noisier, slower to converge.

**Training (transfer learning):** The model is **pretrained on the ADAMSense dataset** (`data/anxiety_dataset.csv`), then **fine-tuned and frozen on Garmin users 1–6** (`data/all_users_data_labeled.csv`), with **User 7 held out** entirely. Validation protocol: a pre-augmentation 10% stratified split, augmentation applied only to the training partition (within-distribution val accuracy ≈ 94.4%). Evaluated two ways — 5-fold window CV (in-distribution) and LOUO (cross-person). See [Section 8](#8-evaluation-strategy--louo-vs-5-fold-cv).

**Input:** `[batch, 200, 6]` — 200 timesteps × 6 sensor channels

**Output:** Softmax probabilities over 11 activity classes

**File format:** `.keras` (TensorFlow/Keras native format, more portable than `.h5`)

---

## 7. Windowing — The Core Preprocessing Decision

**Parameters:**
- `WINDOW = 200` samples
- `STRIDE = 100` samples (50% overlap)
- Sampling rate: 50 Hz

**What this means:**
- Window duration: 200 / 50 = **4 seconds** of sensor data per window
- Prediction cadence: 100 / 50 = **2 seconds** (a new prediction every 2 seconds)
- Each window overlaps 50% with the previous one

### Windowing, visualized

The sensor produces an endless stream. The model needs fixed-size bites. Windowing slices the stream into overlapping 4-second clips:

```
Continuous 50 Hz stream:
 s0  s1  s2  s3  ...                                          ... s998 s999
 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▶ time

 Window 1  [■■■■■■■■■■■■■■■■■■■■]                         → predict @ 0s
           └─── 200 samples ───┘
 Window 2            [■■■■■■■■■■■■■■■■■■■■]               → predict @ 2s
                     └─── 200 samples ───┘
 Window 3                      [■■■■■■■■■■■■■■■■■■■■]      → predict @ 4s
                               └─── 200 samples ───┘
                     ◀──50%──▶
                     overlap

 STRIDE = 100 samples (the jump between windows) = 2 seconds
```

> ⚠️ **Common confusion: "50% overlap" ≠ "25% on each side."**
> It means two *consecutive* windows share exactly half their length — the **last half of one window is literally the first half of the next**:
> ```
> seconds:  0   1   2   3   4   5   6   7   8
> W1:      [===============]                    covers 0–4s
> W2:              [===============]            covers 2–6s
> W3:                      [===============]    covers 4–8s
>  W1∩W2 = 2–4s (last half of W1 = first half of W2)
> ```
> Every interior second belongs to exactly **2** windows. A scheme that shares 25% with the previous window and 25% with the next (unshared middle) would be **25% overlap, stride = 3s** — which shares *less*, not more. Cross-window "past + future" context actually comes from the **BiLSTM** (within a window) and **temporal smoothing k=3** (across windows), not from the overlap itself.

**Why the 50% overlap matters (concrete numbers):**

| | No overlap (stride=200) | 50% overlap (stride=100) |
|---|---|---|
| Windows from 1000 samples | 5 | 9 |
| Prediction every | 4 seconds | 2 seconds |
| Training samples | fewer | ~2× more |
| Misses activity at window edge? | yes | rarely |

**Why 4 seconds?**
Long enough to capture a complete motion cycle (one full step ~0.5-1s, one squat ~2-3s). Short enough to be responsive.

**Why 50% overlap?**
Doubles the number of training samples. Reduces temporal gaps between predictions. Standard in HAR literature.

**The scaler (part of the deployed contract):** `garmin_train_scaler.json` is a JSON z-score scaler fit on **Garmin users 1–6 only** (User 7 excluded), applied in Stage 3 *after* unit conversion and *before* windowing. Production enables it (`enable_normalization: true` in `config/pipeline_config.yaml`); the WebUI applies the same scaler via `_apply_final_model_scaler()`. It stores `scaler_mean` / `scaler_scale` per channel. (The model was trained on scaled windows, so inference must scale to match — train/inference parity.)

**Why JSON and not a pickle file?**
JSON is human-readable and not Python-version dependent. You can open it and inspect the mean/scale values directly. Pickle files can break across Python/sklearn version changes.

### Train/inference parity — the golden rule

The #1 way HAR models silently break in production: **the inference pipeline preprocesses data differently than training did.** This project guarantees they match by sharing the exact same *unit conversion*, *scaler*, and *window parameters*:

```
       TRAINING (offline, once)              INFERENCE (production, every run)
       ════════════════════════              ════════════════════════════════
        raw Garmin data                       raw Garmin data
              │                                     │
        milliG → m/s²                         milliG → m/s²        ◀── SAME unit conversion
              │                                     │
        FIT z-score scaler ─saves─▶ scaler.json ─▶ LOAD scaler.json ◀── SAME stats (users 1–6)
              │                                     │
        apply scaler                          apply scaler         ◀── SAME transform
              │                                     │
        window(200, stride 100)               window(200, stride 100)  ◀── SAME params
              │                                     │
        TRAIN model ─saves─▶ model.keras ─────▶ LOAD model.keras   ◀── SAME weights
              │                                     │
        evaluate (5-fold / LOUO)              predict + monitor
```

> ⚠️ **Gotcha (the real one):** the deployed model was trained on **z-score-scaled** windows, so inference **must** apply `garmin_train_scaler.json` (fit on users 1–6, after unit conversion). Feeding it raw m/s²/deg/s would be the mismatch. The drift baseline is therefore the **scaled** baseline (`garmin_train_scaled_baseline.json`) to match the model's input space. Parity = use the *same* scaler at train and inference; never *re-fit* one on inference data.

---

## 8. Evaluation Strategy — LOUO vs 5-Fold CV

**Two very different numbers — both correct, different questions:**

| Strategy | Accuracy | F1 | What it measures |
|---|---|---|---|
| 5-Fold Cross-Validation | 93.61% | 0.937 | In-distribution performance (seen users) |
| LOUO (Leave-One-User-Out) | 44.42% | 0.419 | Cross-person generalization (unseen user) |
| User-7 held-out | 36.96% | 0.350 | Specific held-out subject test |

### Why the two numbers differ so much

The split strategy decides whether the model is tested on people it has *seen* or *never seen*:

```
5-FOLD CV  (mixes all users into every fold)
  Users:  [1][2][3][4][5][6][7]
  Fold 1: train on 80% of ALL users' data, test on the other 20%
          → the model has seen user 7's movement style during training
          → EASY → 93.61%   ✅ "can it recognize activities?"

LOUO  (Leave-One-User-Out — holds out a whole person)
  Train:  [1][2][3][4][5][6]            test: [7]  ← completely unseen person
          → the model has NEVER seen user 7
          → HARD → 44.42%   ⚠️ "can it generalize to a NEW person?"
```

**Why does LOUO drop so much?**
HAR models are heavily subject-dependent. Each person moves differently. A model trained on users 1-6 has never seen user 7's motion signature. This is the **personalization gap** — a known open problem in wearable HAR.

> 🎯 **Interview gold:** "My 93% is in-distribution (5-fold); my 44% is cross-person (LOUO). The gap *is* my thesis motivation — it's exactly why a deployed HAR model needs monitoring and a retraining path, which is what my pipeline provides."

**Why report both?**
Reporting only 5-fold would be misleading — it hides the personalization problem. Reporting both honestly shows the model works well in-distribution but struggles cross-person. The MLOps pipeline (drift detection, monitoring, retraining gates) is the *answer* to this gap.

**Why not use more advanced domain adaptation?**
Out of scope for this thesis. The retraining pipeline (stages 8-10) is the mechanism for personalization — collect labeled data from a new user, retrain, promote.

---

## 9. Monitoring — Three Layers

After each inference run, the pipeline applies three health checks:

### Layer 1: Confidence Monitoring
- **What:** Mean softmax confidence across all windows
- **Threshold:** Configurable (e.g., <0.70 = warning)
- **Why:** Low confidence = model is uncertain = potential distribution shift
- **Limitation:** Confidence is not calibrated. A model can be confidently wrong.

### Layer 2: Temporal Consistency
- **What:** the *transition rate* — the fraction of adjacent window pairs where the predicted class changes (a flip), computed as `changes / (n_windows − 1)`
- **With smoothing (additive, soft-vote, k=3):** a smoothed transition rate is *also* reported (see the dedicated subsection below); the raw rate stays the primary signal
- **Threshold:** transition rate > 35% = warning (Stage 6 `transition_rate_threshold`)
- **Why:** Real activities don't change every 2 seconds. High flip rate = noise or model confusion.

### Layer 3: Drift Detection
- **What:** Z-score comparing current run's feature distribution to the training baseline
- **Baseline:** the deployed serving path compares against the **scaled** baseline `garmin_train_scaled_baseline.json` (matching the model's z-score input space); a `raw_physical_baseline.json` exists for the paper/A-B raw path. The baseline must match whatever input space the run uses, or drift is meaningless.
- **Threshold:** per-channel |z| > 1.8 = warning at Stage 6; the Stage 7 trigger escalates at z > 2.0 (warn) / 3.0 (critical)
- **Why:** If incoming sensor data looks statistically different from training data, predictions are unreliable regardless of confidence.

### The three layers at a glance

```
                  Inference output
       (predictions + confidence + input features)
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
 ┌───────────┐     ┌───────────┐     ┌───────────┐
 │  LAYER 1  │     │  LAYER 2  │     │  LAYER 3  │
 │Confidence │     │ Temporal  │     │  Drift    │
 │           │     │(smooth k=3)│     │ (z-score) │
 │ mean<0.70?│     │ flips>35%?│     │  |z|>1.8? │
 └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
       ▼                 ▼                 ▼
   "Is the model     "Are predictions   "Does the input
    unsure?"          jumping around?"   look unfamiliar?"
       └─────────────────┼─────────────────┘
                         ▼
                count the WARNINGs  ──▶  Stage 7 Trigger
```

| Layer | Catches this failure | Real-world example |
|---|---|---|
| Confidence | Model is unsure | New activity it was never trained on |
| Temporal | Predictions are noisy/jumpy | Sensor glitch causing rapid flips |
| Drift | Input distribution shifted | User wears watch on the other wrist |

**Layer 1b — dominant-class collapse guard.** Bundled with the confidence layer is a separate check: if one class wins **> 85%** of all windows it raises a WARNING, and **> 95%** is CRITICAL. This catches "mode collapse," where the model confidently predicts a single class for almost everything (high confidence, but useless). It is paired with a low-motion check (median gyro magnitude) to separate genuine stillness from collapse.

**Why three layers instead of one?**
Each catches different failure modes. A model can have high confidence but drifted inputs (layer 3 catches it). A model can have reasonable inputs but chaotic predictions (layer 2 catches it). Defense in depth.

> 💡 **Smoke detector analogy:** A heat detector, a smoke detector, and a CO detector. You install all three because each is blind to the dangers the others catch.

### Temporal smoothing — the additive soft-vote (the 2026-06-15 enhancement)

The model classifies each 4-second window **independently**, so a single noisy window can flip to a wrong class for ~2 seconds and then flip back. That single-window jitter inflates the Layer-2 transition rate and makes a healthy session look unstable. The fix is **temporal smoothing** — the "decision" stage of the Activity Recognition Chain (Bulling et al., 2014), implemented in `_smooth_predictions()` (`src/api/app.py`).

**How it works (soft vote, k=3):** for each window *i*, average the **softmax probability vectors** of windows `[i-1, i, i+1]`, then take the argmax of that average. Because it averages *probabilities* (not just votes labels), a low-confidence outlier is outvoted by confident neighbours, while a genuinely confident change survives.

```
window:        … 7      8      9      10     11   …
raw argmax:      sit    sit  nail_b   sit    sit       ← window 9 is a lone flip
                              ▲ isolated single-window jitter

soft vote over [8,9,10]:  avg softmax → argmax = sit   ← outvoted, flip removed
smoothed:        sit    sit    sit     sit    sit
```

**Why "additive" matters (the honesty rule):** smoothing is reported **alongside** the raw signal, never instead of it.

| Signal | Raw (primary) | Smoothed (reported beside it) |
|---|---|---|
| Served per-window predictions | ✅ what the user sees | — (raw stays the output) |
| Layer-2 transition rate | `transition_rate_pct` | `transition_rate_smoothed_pct` |
| Labeled eval card | `accuracy`, `macro_f1` | `accuracy_smoothed`, `macro_f1_smoothed` |

- `SMOOTHING_WINDOW = 3` ≈ ~6 s of context (windows step every 2 s).
- The raw predictions still **drive monitoring and the served output** — so smoothing can't mask a real problem; it just lets you *see* how much of the instability was mere jitter (if raw=40% but smoothed=18%, most flips were single-window noise).
- Edge windows use a truncated neighbourhood (the first/last window averages over the 2 it has).

> 🎯 **Defense line:** "Smoothing is additive, not destructive. I report raw *and* smoothed side by side, so the reviewer sees both the honest jitter and the de-noised view — I never let a smoother hide a genuinely unstable model."

---

## 10. Governance — No Auto-Retrain

**Hard rule:** The model is NEVER retrained automatically. `should_retrain = False` is hardcoded in `src/api/app.py:481`.

**The retrain gate requires ALL of:**
1. Trigger decision = RETRAIN (not just REVIEW)
2. Labeled data available for the new user
3. QA evidence (validation pass)
4. Human approval

**Why?**
Auto-retrain on production data is dangerous:
- Labels may be wrong or absent
- One bad session can corrupt the model
- Regulatory/ethical concerns in health applications
- Hard to audit what changed and why

**The governance decisions:**

| Decision | Meaning |
|---|---|
| `NO_ACTION` | All layers healthy, continue serving |
| `MONITOR` | One layer warning, watch but don't act |
| `REVIEW` | Multiple warnings, flag for human inspection |
| `RETRAIN` | Strong evidence of degradation + labels available |

### Escalation ladder — and the gate that never opens itself

The number of warnings decides how loud the alarm gets. But even the loudest alarm **cannot** retrain the model on its own:

```
  0 warnings      1 warning       2 warnings      3 warnings
      │               │               │               │
      ▼               ▼               ▼               ▼
 ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
 │NO_ACTION│     │ MONITOR │     │ REVIEW  │     │ RETRAIN │
 └─────────┘     └─────────┘     └─────────┘     └────┬────┘
 keep serving    watch closely   human inspects       │
                                 the run               ▼
                                            ┌──────────────────────┐
                                            │     RETRAIN GATE      │
                                            │  ALL must be true:    │
                                            │   ☐ labels exist      │
                                            │   ☐ QA / validation OK │
                                            │   ☐ human approves    │
                                            └──────────┬───────────┘
                                       ┌───────────────┴───────────────┐
                                       ▼                               ▼
                                  ANY box unchecked:              ALL boxes checked:
                                  ⛔ STAYS BLOCKED                ✅ manual retrain
                                  (never auto-retrains)              allowed
```

> 🔒 **The invariant:** `should_retrain = False` is hardcoded in [src/api/app.py](src/api/app.py). There is no code path where the WebUI or pipeline mutates the model by itself. A human must pull the trigger. This is the single most important safety property of the whole system.

---

## 11. Experiment Tracking with MLflow

**Two separate experiments:**

### `inference-production`
- Captures every serving run (WebUI + Stage 4 batch)
- Logs: mean confidence, per-activity counts, total windows, model MD5, runtime mode, batch size, confidence threshold
- Why separate? Interactive serving runs are frequent and noisy — mixing them with governed batch runs would pollute the batch history

### `har-production-pipeline`
- Captures every full pipeline run (all 7 stages)
- Logs: 13 curated stage metrics, run parameters (all stage statuses, retrain flags), `run_info.json` artifact
- Tags: author, model type, task, version, source commit

### How MLflow organizes everything

```
MLflow
│
├── Experiment: "har-production-pipeline"   (governed batch runs)
│   ├── Run abc123
│   │   ├── params    →  overall_status=SUCCESS, should_retrain=False
│   │   ├── metrics   →  n_windows=989, mean_confidence=0.846, drift_z=0.24
│   │   ├── tags      →  author=Shalin, model_type=1DCNNBiLSTM, version=2.1
│   │   └── artifacts →  run_info.json
│   └── Run def456 ...
│
└── Experiment: "inference-production"       (serving / WebUI runs)
    ├── Run ghi789   ⟶ parent_run_id = abc123   (links serving back to its batch run)
    │   ├── params    →  model_md5=00bd…, runtime_mode=fused
    │   └── metrics   →  mean_confidence=0.865, total_windows=758
    └── Run jkl012 ...
```

**Why 13 metrics specifically?**
One or two metrics per stage — enough to audit what happened without overwhelming the dashboard.

**Parent-child runs:** Each WebUI/serving run is linked to its parent pipeline run via MLflow's parent run ID. This ties serving evidence back to the governed batch context.

---

## 12. Data Versioning with DVC

**What DVC does:** Tracks large files (data, models) outside git. Stores a small `.dvc` pointer file in git; the actual data lives in a remote storage (local cache, S3, GCS, etc.).

**Why not just git?**
Git is not designed for large binary files. A 500MB dataset in git history bloats the repo permanently.

### How DVC splits the work with Git

```
   YOUR REPO (in Git)              DVC STORAGE (local / S3 / GCS)
   ─────────────────              ──────────────────────────────
   data.csv.dvc   (120 bytes)  ──points to──▶  data.csv   (500 MB)
   model.keras.dvc (120 bytes) ──points to──▶  model.keras (10 MB)
        │                                            ▲
        │ git clone  → you get the tiny pointers     │
        │ dvc pull   → DVC fetches the big files ─────┘

   Git tracks the TICKET. DVC stores the COAT.
```

**What's tracked:**
- Raw sensor data files
- Processed artifacts (`production_X.npy`)
- Model files

**In this thesis:** DVC remote is local (not cloud). For production, you'd point it at S3/GCS.

---

## 13. The WebUI (FastAPI Dashboard)

**File:** `src/api/app.py`

**What it does:** A browser-based dashboard for submitting sensor sessions and seeing inference results without running the pipeline from the command line.

**Upload modes:**
1. **Fused CSV** — pre-merged accel+gyro in one file
2. **Raw pair** — two separate files (accel CSV + gyro CSV)

**What you get back:**
- Run summary (mode, windows, stage strip S1–S10)
- Monitoring signals (confidence, temporal flip rate, drift z-score)
- Governance decision (NO_ACTION / MONITOR / REVIEW / RETRAIN)
- Per-window predictions with confidence
- *If labels present:* Evaluation card (accuracy, macro-F1, smoothed variants, confusion matrix)

### What happens when you click "Upload"

```
  Browser                 FastAPI (app.py)                Runtime Contract
  ───────                 ────────────────                ────────────────
  pick CSV ──POST /upload──▶ save to temp file
                             │
                             ├─▶ Stage 1–3: window the data
                             ├─▶ Stage 4: load model+scaler ──reads──▶ 📦 contract
                             ├─▶ Stage 5: evaluate (if labels)
                             ├─▶ Stage 6: 3-layer monitoring
                             ├─▶ Stage 7: governance decision
                             ├─▶ log run ──▶ MLflow
                             │
            ◀──HTML result───┤
  see:                       │
  • predictions + confidence
  • monitoring signals
  • governance decision
  • evaluation card (if labels)
```

**Why FastAPI and not Flask?**
FastAPI gives automatic request validation (Pydantic), async support, and auto-generated API docs (`/docs`). Flask would work but requires more boilerplate for the same result.

**Why a stage strip (S1–S10)?**
Visual transparency. The user sees exactly which stages ran and whether they passed. This is a core MLOps principle: observability at every step.

---

## 14. Runtime Contract

**Location:** `models/runtime_contract/model_d1_final_20260528/`

**What actually lives in the contract folder:**

| File | Purpose |
|---|---|
| `finetuned_1DCNNBILSTM_HAR_model.keras` | The trained model (native Keras format) |
| `finetuned_1DCNNBILSTM_HAR_model_savedmodel/` | The same model as a TF SavedModel directory (alternate load path) |
| `model_contract.json` | **The authoritative spec**: input shape `[200,6]`, 11-class `label_order`, units (`m/s²`/`deg/s`), `window_size 200` / `stride 100`, scaler-fit users 1–6 |
| `label_order.json` | The 11 class names in index order |
| `garmin_train_scaler.json` (+ `.joblib`) | **The deployed z-score scaler** (fit on users 1–6, applied after unit conversion) |
| `garmin_train_scaled_baseline.json` | The drift baseline in the model's **scaled** input space (used by the WebUI serving path) |
| `artifact_md5.json` | MD5 checksums of the contract artifacts |

> A `models/raw_physical_baseline.json` also exists for the *paper/A-B raw-units* path; the deployed (scaled) serving path uses the scaled baseline above. The baseline must always match the run's input space.

### The contract as a sealed package

These files are only correct together. Think of it as a passport — change one stamp without the others and border control (the MD5 check) rejects it:

```
   models/runtime_contract/model_d1_final_20260528/
   ┌────────────────────────────────────────────────────────┐
   │  📦 RUNTIME CONTRACT                                      │
   │                                                          │
   │   finetuned_1DCNNBILSTM_HAR_model.keras  ← the brain      │
   │   model_contract.json   ← the spec (units, 11 labels)    │
   │   label_order.json      ← index → name map               │
   │   garmin_train_scaler.json ← the deployed z-score scaler  │
   │                                                          │
   │   artifact_md5.json     ← seal: hashes of the files      │
   └────────────────────────────────────────────────────────┘
                          │
                          ▼ at startup, Stage 4 hashes the model and
                            records its MD5 in every run + MLflow.
```

**Why MD5 checksums?**
Stage 4 computes the model's MD5 on every run and records it (in the run report and MLflow). If the deployed file ever changes unexpectedly, the recorded hash changes — so a silent model swap is detectable in the run history.

**Why JSON for the contract and label order?**
Human-readable, version-stable, inspectable without Python. You can open `model_contract.json` and read exactly which units, classes, and window parameters the model expects.

**The contract check** (in `pipeline_config_factory.py`): when normalization is enabled (it is, in production), `_ensure_runtime_contract_consistency` guarantees the active scaler comes from the same folder as the active model — warning-and-correcting on a folder mismatch, raising if no compatible scaler exists. The drift baseline must match the input space (scaled for the deployed path) and is validated by the pytest contract tests.

---

## 15. Docker — Two Images

**Why two images instead of one?**

| Image | File | Base | Size | Purpose |
|---|---|---|---|---|
| Inference | `Dockerfile.inference` | python:3.10-slim | Slim | FastAPI WebUI + Stage 1–7 serving |
| Training | `Dockerfile.training` | python:3.10 | Full | Full pipeline + training capability |

### Two images, two jobs

```
   ┌─────────────────────────┐     ┌─────────────────────────┐
   │  INFERENCE IMAGE (slim)  │     │  TRAINING IMAGE (full)   │
   │  python:3.10-slim        │     │  python:3.10             │
   │  ─────────────────────   │     │  ─────────────────────   │
   │  ✓ tensorflow-cpu        │     │  ✓ everything in slim    │
   │  ✓ fastapi + uvicorn     │     │  ✓ pytest, black, mypy   │
   │  ✓ numpy, pandas, mlflow │     │  ✓ flake8, dvc           │
   │  ✗ no dev/test tools     │     │  ✓ full pipeline + train │
   │                          │     │                          │
   │  runs: the WebUI 24/7    │     │  runs: run_pipeline.py   │
   │  goal: small & safe      │     │  goal: complete & capable│
   └─────────────────────────┘     └─────────────────────────┘
        deployed to users               used by developers / CI
```

**Why slim for inference?**
The inference image runs in production 24/7. You don't need `jupyterlab`, `black`, `mypy`, or training tools in it. Smaller image = faster pull, smaller attack surface, less memory.

**Why not GPU in either image?**
This thesis uses `tensorflow-cpu`. GPU training was done locally in a conda environment (`tf-gpu`). In production (cloud), you'd switch the base image to a CUDA-enabled TensorFlow image and change `tensorflow-cpu` → `tensorflow`.

**Runtime:** `uvicorn src.api.app:app --host 0.0.0.0 --port 8000`

---

## 16. Dependencies — Why Each One

### Core
| Package | Why |
|---|---|
| `numpy` | Array operations everywhere — windowing, normalization, prediction arrays |
| `pandas` | CSV I/O, DataFrame manipulation in ingestion and evaluation stages |
| `scipy` | Signal processing utilities in transformation stage |

### Deep Learning
| Package | Why |
|---|---|
| `tensorflow-cpu` | Runs the 1DCNNBiLSTM model. CPU version sufficient for inference; GPU used only during training |

### Metrics
| Package | Why |
|---|---|
| `scikit-learn` | Accuracy, macro-F1, confusion matrix in evaluation stage |

### MLOps
| Package | Why |
|---|---|
| `mlflow` | Experiment tracking, run logging, artifact storage |
| `dvc` | Data + model versioning outside git |

### API
| Package | Why |
|---|---|
| `fastapi` | WebUI backend — async, Pydantic validation, auto docs |
| `uvicorn` | ASGI server to run FastAPI |
| `pydantic` | Request/response validation (FastAPI dependency) |
| `python-multipart` | File upload support in FastAPI |

### Visualization
| Package | Why |
|---|---|
| `matplotlib` | Figures in pipeline reports and thesis |
| `seaborn` | Confusion matrix heatmap in MLflow tracking (`src/mlflow_tracking.py`) |

### Utilities
| Package | Why |
|---|---|
| `pyyaml` | Parse `config/pipeline_config.yaml` |

### Dev/Test
| Package | Why |
|---|---|
| `pytest` | Test suite runner |
| `pytest-cov` | Coverage reports |
| `flake8` | Linting |
| `black` | Auto-formatting |
| `mypy` | Static type checking |

**What was removed and why:**
- `tqdm` — not imported anywhere in `src/`, `scripts/`, or `tests/`
- `python-dotenv` — not imported anywhere; secrets managed via config yaml
- `jupyterlab` — not a project dependency; IDE tool only
- `isort` — dev tool, not used in CI or tests
- `pytest-xdist` — parallel test execution, not configured or used

---

## 17. Technical Tools — Deep Dive

Every tool used in this project explained technically: what it is, how it works internally, how it is used here, and why it was chosen over alternatives.

---

### 17.1 MLflow

**What it is:** An open-source platform for the complete ML lifecycle — experiment tracking, model registry, artifact storage, and project packaging.

**Core concepts:**

| Concept | What it is |
|---|---|
| **Experiment** | A named group of runs (like a folder). We have two: `inference-production` and `har-production-pipeline`. |
| **Run** | A single execution. Has a unique run ID, start/end time, status. |
| **Parameters** | Key-value strings logged per run. Immutable after logging. e.g., `model_md5`, `stage_1_status`. |
| **Metrics** | Key-value numbers. Can be logged at a step (for time series) or once. e.g., `mean_confidence=0.846`. |
| **Artifacts** | Files attached to a run. e.g., `run_info.json`, inference CSV, confusion matrix PNG. |
| **Tags** | Freeform metadata. We tag runs with `author`, `model_type`, `task`, `version`. |
| **Parent-child runs** | A run can have a `parent_run_id` linking it to another run. We use this to link WebUI serving runs back to their parent pipeline run. |

**How MLflow stores data (locally):**
```
mlruns/
  <experiment_id>/
    <run_id>/
      meta.yaml          # run metadata
      params/            # one file per parameter
      metrics/           # one file per metric (TSV format)
      tags/              # one file per tag
      artifacts/         # your logged files
```

**How we use it in this project:**

```python
import mlflow

mlflow.set_experiment("har-production-pipeline")

with mlflow.start_run() as run:
    mlflow.log_param("stage_1_status", "SUCCESS")
    mlflow.log_metric("mean_confidence", 0.846)
    mlflow.log_artifact("artifacts/run_info.json")
    mlflow.set_tag("author", "Shalin Vachheta")
```

**Key files:**
- `src/pipeline/pipeline_mlflow_logger.py` — logs the 13 stage metrics + run parameters
- `src/api/app.py` → `_log_inference_mlflow()` — logs WebUI serving runs

**Why MLflow and not alternatives?**

| Tool | Why not |
|---|---|
| Weights & Biases | Paid/cloud-first, overkill for a thesis |
| Neptune.ai | Same — cloud-centric |
| TensorBoard | TensorFlow-specific, no general pipeline tracking |
| Plain CSV logs | Not queryable, no UI, no artifact storage |
| MLflow | Free, local-first, UI included, Python-native |

**MLflow UI:** `mlflow ui --port 5000` — starts a local Flask server. Browse experiments, compare runs, download artifacts, view metrics as time series.

---

### 17.2 DVC (Data Version Control)

**What it is:** Git for large files. DVC tracks data and model files outside git using lightweight pointer files (`.dvc`), while the actual binary content lives in a separate storage (local cache, S3, GCS, Azure Blob).

**The problem it solves:**
```
# Without DVC:
git add data/garmin_user7.csv   # 500MB file → bloats git forever
git commit -m "add data"         # every clone downloads 500MB

# With DVC:
dvc add data/garmin_user7.csv   # creates garmin_user7.csv.dvc (100 bytes)
git add data/garmin_user7.csv.dvc  # only the pointer goes in git
dvc push                          # actual file goes to DVC remote (S3/local)
```

**How a `.dvc` file looks:**
```yaml
outs:
- md5: a1b2c3d4e5f6...          # hash of the actual file
  size: 524288000               # file size in bytes
  path: garmin_user7.csv
```

**Core commands:**
```bash
dvc init                  # initialize DVC in a git repo
dvc add data/file.csv     # start tracking a file
dvc push                  # upload tracked files to remote
dvc pull                  # download tracked files from remote
dvc repro                 # re-run the pipeline if inputs changed
dvc status                # show what's changed vs. cache
```

**DVC remote in this thesis:** Local filesystem (another directory). For cloud: `dvc remote add myremote s3://bucket-name/path`.

**What's tracked:** Raw sensor CSVs, processed `.npy` arrays, model `.keras` file.

**DVC + Git together:** Git tracks code and `.dvc` files. DVC tracks the data those `.dvc` files point to. A `git clone` + `dvc pull` gives you a fully reproducible environment.

**Why DVC and not Git LFS?**
- Git LFS stores large files in a special GitHub/GitLab server — still paid beyond free limits.
- DVC is storage-agnostic (local, S3, GCS, SSH) and has pipeline tracking (`dvc.yaml`).
- DVC integrates with MLflow for full data+experiment provenance.

---

### 17.3 Docker

**What it is:** A containerization platform. A container is an isolated process with its own filesystem, libraries, and environment — but shares the host OS kernel (unlike a VM which has its own OS).

**Key concepts:**

| Concept | What it is |
|---|---|
| **Image** | A read-only snapshot: OS layer + your code + dependencies. Built once, run anywhere. |
| **Container** | A running instance of an image. Ephemeral — stops when the process stops. |
| **Dockerfile** | Instructions for building an image, layer by layer. |
| **Layer caching** | Each instruction in a Dockerfile creates a layer. If the layer hasn't changed, Docker reuses the cached version. Put infrequently-changing instructions first (e.g., `pip install` before `COPY src/`). |
| **Base image** | The starting point. `python:3.10-slim` = Debian with Python 3.10 and minimal extras. |
| **Registry** | A store for images: DockerHub (public), ECR (AWS), GCR (Google). |

**Our Dockerfile.inference (annotated):**
```dockerfile
FROM python:3.10-slim                    # start from slim Debian + Python

WORKDIR /app                             # all commands run from /app

COPY config/requirements-runtime.txt .  # copy ONLY the slim requirements first
RUN pip install --no-cache-dir \         # install — this layer is cached
    -r requirements-runtime.txt          # unless requirements-runtime.txt changes

COPY src/ ./src/                         # copy source after pip install
COPY models/ ./models/                   # copy the runtime contract
COPY config/ ./config/                   # copy config yaml

EXPOSE 8000                              # document which port the app uses

CMD ["uvicorn", "src.api.app:app",       # start FastAPI on container launch
     "--host", "0.0.0.0",
     "--port", "8000"]
```

**Why layer order matters:**
`COPY requirements.txt` + `RUN pip install` come BEFORE `COPY src/`. This means: if only code changes (not dependencies), Docker reuses the cached pip install layer. Rebuilds take seconds instead of minutes.

**Why `--no-cache-dir` in pip install?**
Pip normally caches downloaded packages in `~/.cache/pip`. Inside a Docker build, that cache is thrown away after the layer — but it temporarily inflates the layer size. `--no-cache-dir` keeps the image lean.

**Why `python:3.10-slim` and not `python:3.10`?**
The slim variant strips documentation, man pages, and optional system packages — saves ~200MB. Inference doesn't need build tools; slim is enough.

**Essential commands:**
```bash
docker build -f docker/Dockerfile.inference -t har-inference .
docker run -p 8000:8000 har-inference          # map container port 8000 to host 8000
docker images                                   # list local images
docker ps                                       # list running containers
docker logs <container_id>                      # view container stdout
docker exec -it <container_id> bash             # open shell inside a running container
```

**Why Docker for this project?**
Without Docker, "it works on my machine" is a real problem. With Docker, the same image runs on any machine, any cloud, any CI runner — same Python version, same library versions, same behavior.

---

### 17.4 FastAPI

**What it is:** A modern Python web framework for building APIs. Built on top of Starlette (async web framework) and Pydantic (data validation).

**Why "Fast"?** Two reasons:
1. **Fast to run:** Uses `asyncio` — non-blocking I/O means one process can handle many concurrent requests without blocking.
2. **Fast to develop:** Auto-generates OpenAPI docs (`/docs`), auto-validates requests via Pydantic, type hints drive everything.

**Core concepts:**

```python
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI()

# A route decorator — maps HTTP GET /health to this function
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# File upload endpoint
@app.post("/upload")
async def upload(
    accel_file: UploadFile = File(...),   # UploadFile = multipart form file
    gyro_file: UploadFile = File(None),   # optional second file
):
    content = await accel_file.read()     # async read
    # ... process ...
    return {"windows": 989, "status": "SUCCESS"}
```

**How our WebUI works (simplified flow):**
```
Browser POST /upload (with CSV file)
    ↓
FastAPI receives UploadFile
    ↓
Saves to temp file → runs Stage 1–7 pipeline logic
    ↓
Runs monitoring + trigger
    ↓
Logs to MLflow
    ↓
Returns JSON result
    ↓
Browser renders HTML dashboard (Jinja2 or raw HTML in response)
```

**Key FastAPI features used:**
- `UploadFile` — handles multipart file uploads (requires `python-multipart`)
- `HTMLResponse` — returns rendered HTML directly (our WebUI is server-rendered)
- `BackgroundTasks` — could run cleanup after response is sent
- Auto `/docs` — Swagger UI at `http://localhost:8000/docs` (free, always up to date)

**Why async (`async def`) for file uploads?**
File I/O is slow. `async def` lets FastAPI handle other requests while waiting for the file to be read from disk — better throughput without extra threads.

**Why not Flask?**
Flask is synchronous by default and requires extensions for validation, async, and docs. FastAPI gives all three out of the box. For new projects, FastAPI is the modern choice.

---

### 17.5 Pydantic

**What it is:** A Python library for data validation using type annotations. Define a class with type hints, pass data in, get a validated object out — or a clear error if the data is wrong.

**Core idea:**
```python
from pydantic import BaseModel

class PipelineConfig(BaseModel):
    window_size: int = 200
    stride: int = 100
    confidence_threshold: float = 0.70
    model_path: str

# Valid — types match
cfg = PipelineConfig(window_size=200, stride=100, confidence_threshold=0.8, model_path="/models/d1.keras")

# Invalid — will raise ValidationError, not silently pass wrong types
cfg = PipelineConfig(window_size="not_an_int", ...)
# → pydantic.ValidationError: window_size: value is not a valid integer
```

**What Pydantic does for FastAPI:**
- Every request body is a Pydantic model → auto-validated before your function is called
- Wrong types → 422 Unprocessable Entity response with a clear error message
- No manual `if not isinstance(x, int)` checks needed

**How we use it here:**
- Config dataclasses for pipeline stages (type-safe configuration)
- FastAPI request/response models for the WebUI endpoints
- Ensures `window_size`, `stride`, `threshold` values are the right types at pipeline startup

**Pydantic v1 vs v2:** This project uses Pydantic v2 (`pydantic>=2.5`). V2 rewrote the core in Rust — 5-50x faster validation. The API changed slightly (e.g., `model.dict()` → `model.model_dump()`).

---

### 17.6 pytest

**What it is:** Python's standard testing framework. Discovers and runs test functions automatically, provides rich assertion introspection, and has a powerful fixture and plugin system.

**How tests are organized here:**
```
tests/
├── conftest.py              # shared fixtures available to all tests
├── test_api_upload_modes.py # WebUI upload endpoint tests
├── test_contract.py         # runtime contract integrity tests
├── test_pipeline_*.py       # per-stage pipeline tests
└── ...
```

**Core concepts:**

```python
import pytest

# A simple test — any function starting with test_
def test_window_size():
    assert 200 / 50 == 4.0   # 200 samples / 50 Hz = 4 seconds

# A fixture — shared setup/teardown
@pytest.fixture
def sample_config():
    return {"window_size": 200, "stride": 100}

# Using a fixture
def test_stride(sample_config):
    assert sample_config["stride"] == 100

# Parametrize — run same test with multiple inputs
@pytest.mark.parametrize("window,expected", [(200, 4.0), (100, 2.0)])
def test_duration(window, expected):
    assert window / 50 == expected

# Markers — categorize tests
@pytest.mark.integration
def test_full_pipeline():
    ...
```

**Our custom markers** (defined in `pyproject.toml`):
- `slow` — tests that take > a few seconds
- `integration` — tests that hit real files or the real pipeline
- `unit` — isolated, no external dependencies
- `robustness` — noise injection tests
- `calibration` — uncertainty/calibration tests

**Contract tests** (`test_contract.py`): Verify that the runtime contract files exist, have correct MD5s, and the scaler has the right number of features. These are the safety net — if someone changes a model file without updating the contract, these tests catch it.

**Running tests:**
```bash
pytest tests/ -v                     # all tests, verbose
pytest tests/ -m unit                # only unit tests
pytest tests/ -m "not slow"          # skip slow tests
pytest tests/ --cov=src --cov-report=html   # with coverage report
```

**`conftest.py`:** Special file that pytest auto-loads. Define fixtures here and they're available to all test files without importing. We use it for things like a shared pipeline config fixture or a temp directory.

---

### 17.7 TensorFlow / Keras

**What it is:** TensorFlow is Google's deep learning framework. Keras is its high-level API — the interface you actually write models in.

**Model definition (how D1 was built):**
```python
from tensorflow import keras
from tensorflow.keras import layers

def build_model(window_size=200, n_features=6, n_classes=5):
    inputs = keras.Input(shape=(window_size, n_features))   # [batch, 200, 6]

    # 1D CNN block — extracts local patterns
    x = layers.Conv1D(64, kernel_size=3, activation='relu', padding='same')(inputs)
    x = layers.MaxPooling1D(pool_size=2)(x)

    # Bidirectional LSTM — long-range temporal dependencies
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=False))(x)

    # Classification head
    x = layers.Dense(64, activation='relu')(x)
    outputs = layers.Dense(n_classes, activation='softmax')(x)   # probabilities

    model = keras.Model(inputs, outputs)
    return model
```

**Training:**
```python
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_val, y_val))
```

**Saving and loading:**
```python
model.save("model_d1.keras")           # save in .keras format
model = keras.models.load_model("model_d1.keras")   # load
```

**Why `.keras` and not `.h5`?**
`.keras` is TensorFlow's new native format (TF 2.12+). More portable, version-stable, and supports custom layers better than `.h5`. The `.h5` format is HDF5-based and can have compatibility issues across TF versions.

**Inference in production (Stage 4):**
```python
model = keras.models.load_model(contract_dir / "finetuned_1DCNNBILSTM_HAR_model.keras")
probabilities = model.predict(X_windows)   # shape: [n_windows, 5]
predictions = np.argmax(probabilities, axis=1)   # class index per window
confidence = np.max(probabilities, axis=1)        # max softmax prob per window
```

**Why `tensorflow-cpu`?** Inference on ~1000 windows takes <5 seconds on CPU. No GPU needed for serving. GPU-accelerated training was done offline during model development.

---

### 17.8 scikit-learn

**What it is:** Python's standard machine learning library for classical ML, preprocessing, and evaluation metrics. We use it only for preprocessing and evaluation — not for the model itself.

**StandardScaler — how it works:**
```python
from sklearn.preprocessing import StandardScaler
import json, numpy as np

# During training:
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)   # fit = compute mean/std, transform = apply

# Serialize to JSON (instead of pickle):
scaler_data = {
    "mean_": scaler.mean_.tolist(),
    "scale_": scaler.scale_.tolist(),
    "n_features_in_": scaler.n_features_in_
}
with open("garmin_train_scaler.json", "w") as f:
    json.dump(scaler_data, f)

# Deployed path (Stage 3 with enable_normalization=true, and the WebUI):
with open("garmin_train_scaler.json") as f:
    data = json.load(f)
# z = (x - mean) / scale
X_scaled = (X_windows - np.array(data["mean_"])) / np.array(data["scale_"])
```

> ℹ️ **In this project the deployed path DOES scale.** The block above is exactly the deployed flow: fit the z-score scaler on users 1–6 at train time, save it to JSON, and load + apply it at inference. scikit-learn is therefore used both for the **deployed scaler** and for **evaluation metrics** (below).

**Evaluation metrics used:**
```python
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

acc = accuracy_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred, average='macro')   # macro = unweighted mean across classes
cm = confusion_matrix(y_true, y_pred)
```

**Why macro-F1 and not accuracy alone?**
With imbalanced classes (one activity more common than others), a model can get 80% accuracy by just predicting the majority class. Macro-F1 treats all classes equally — it penalizes poor performance on minority classes.

---

### 17.9 PyYAML

**What it is:** Python library for reading and writing YAML files.

**How it's used:**
```python
import yaml

with open("config/pipeline_config.yaml") as f:
    config = yaml.safe_load(f)   # safe_load prevents arbitrary code execution

# Access nested values:
window_size = config["transformation"]["window_size"]   # 200
threshold = config["monitoring"]["confidence_threshold"] # 0.70
```

**Why YAML for config and not JSON/TOML/environment variables?**
- YAML supports comments (great for documenting thresholds inline).
- More readable than JSON for nested configuration.
- TOML is better for project metadata (`pyproject.toml`), not runtime config.
- Environment variables work for secrets but not for complex nested config structures.

**`safe_load` vs `load`:** Always use `safe_load`. The full `yaml.load()` can execute arbitrary Python when parsing malicious YAML files — a known security vulnerability.

---

### 17.10 pyproject.toml and setuptools

**What it is:** The modern Python project configuration file. Replaces `setup.py`, `setup.cfg`, and parts of `tox.ini`. Defined in PEP 518/621.

**Our minimal `pyproject.toml`:**
```toml
[build-system]
requires = ["setuptools>=68.0", "wheel>=0.41"]
build-backend = "setuptools.build_meta"

[project]
name = "har-mlops-pipeline"
version = "2.1.0"
requires-python = ">=3.10"
dynamic = ["dependencies"]   # tell setuptools to read deps from a file

[tool.setuptools.dynamic]
dependencies = {file = "config/requirements.txt"}  # actual deps live here

[tool.setuptools]
packages = {find = {include = ["src*"]}}   # auto-discover packages under src/

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --strict-markers -ra"
markers = [...]
```

**What `pip install -e .` does:**
- `-e` = editable mode (development install)
- Reads `pyproject.toml`, finds `src/` packages, installs them as a symlink
- So `import src.api.app` works from anywhere without adding sys.path hacks
- Changes to `src/` are immediately reflected — no reinstall needed

**Why `dynamic = ["dependencies"]`?**
Keeps the single source of truth in `config/requirements.txt`. No duplication between `pyproject.toml` and the requirements file.

---

### 17.11 NumPy and pandas

**NumPy** — the foundation of numerical Python.
- All windowed data is stored as `numpy.ndarray` with shape `[n_windows, window_size, n_features]`
- Operations: `np.argmax`, `np.max`, `np.mean`, `np.std`, slicing, broadcasting
- `.npy` files (`np.save` / `np.load`) are the standard format for numerical arrays — fast binary, no CSV parsing overhead

**pandas** — tabular data manipulation.
- Reading CSVs: `pd.read_csv("sensor_data.csv")`
- Merging accel + gyro on timestamp: `pd.merge(accel_df, gyro_df, on="timestamp")`
- Writing prediction results: `predictions_df.to_csv("predictions.csv", index=False)`
- Used primarily in Stage 1 (ingestion), Stage 5 (evaluation output)

**Why store windows as `.npy` not CSV?**
A window array with shape `[1000, 200, 6]` is a 3D tensor — CSV is 2D. Flattening to CSV loses the structure and is 10x slower to read/write. `.npy` is the right tool for arrays.

---

### 17.12 Git — Branch Strategy

**Branch used:** `model-d-retrain-may18` — all development for this thesis version.

**Plan:**
```
model-d-retrain-may18  (all work here)
         ↓
   squash-merge        (one clean commit to main)
         ↓
        main           ← tag v1.0-submission here
```

**Why squash-merge?**
The branch has hundreds of small commits (fixes, experiments, thesis edits). A squash-merge collapses all of them into one atomic commit on main — the final state, cleanly captured. This is the submission artifact.

**Stale branches to delete** (6 total): `audit/stage1-7-manual-check`, `cleanup/repo-tidy-may16`, `epic/apr-foundation-baseline`, `feature/api-two-file-upload`, `feature/inference-parity-gpt-no-scaler`, `repo-noise-plan-2026-04-29`.

---

## 18. How to Recreate This Project

### Step 1: Clone and install
```bash
git clone <repo-url>
cd MasterArbeit_MLops
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -e .                # installs config/requirements.txt
```

### Step 2: Verify install
```bash
python -c "import tensorflow, mlflow, fastapi; print('all good')"
```

### Step 3: Configure
Edit `config/pipeline_config.yaml` — set your data paths, model path, thresholds.

### Step 4: Run the pipeline
```bash
python run_pipeline.py
```

This runs all 7 stages: ingestion → validation → transformation → inference → evaluation → monitoring → trigger.

### Step 5: Start the WebUI
```bash
uvicorn src.api.app:app --reload --port 8000
```
Open `http://localhost:8000` in a browser.

### Step 6: View experiment tracking
```bash
mlflow ui --port 5000
```
Open `http://localhost:5000` — see `inference-production` and `har-production-pipeline` experiments.

### Step 7: Run tests
```bash
pytest tests/ -v
```

### Step 8: Docker (optional)
```bash
# Inference image
docker build -f docker/Dockerfile.inference -t har-inference .
docker run -p 8000:8000 har-inference

# Training image
docker build -f docker/Dockerfile.training -t har-training .
```

---

## 19. Extending to Cloud or Edge

### Cloud Deployment

**What changes:**

| Component | Thesis (local) | Cloud |
|---|---|---|
| Model storage | `models/runtime_contract/` | S3 / GCS bucket |
| DVC remote | Local cache | S3 / GCS |
| MLflow tracking | Local `mlruns/` | MLflow Tracking Server (EC2/GKE) |
| WebUI | `uvicorn` local | Kubernetes pod / ECS task |
| Docker registry | Local | ECR / GCR / DockerHub |
| Data ingestion | Local CSV | S3 event trigger / Kafka stream |

**Architecture for cloud:**
```
Sensor data → S3 bucket
     ↓
Lambda trigger / Airflow DAG
     ↓
Pipeline container (ECS/GKE) → MLflow Server → artifact store (S3)
     ↓
Inference results → database (RDS/BigQuery)
     ↓
FastAPI WebUI → CloudFront / ALB
```

**Key additions:**
- IAM roles for S3 access (replace local paths with `s3://` URIs in DVC + MLflow)
- Secrets manager (AWS Secrets Manager / GCP Secret Manager) instead of config yaml for credentials
- Horizontal scaling: put the WebUI behind a load balancer, run multiple uvicorn instances
- CI/CD: GitHub Actions → build Docker → push to ECR → deploy to ECS on merge to main

### Edge Deployment (on-device)

**The challenge:** The 1DCNNBiLSTM model is ~10MB. A Garmin watch has ~64KB RAM for apps.

**What you need:**

| Step | Tool | What it does |
|---|---|---|
| Quantize the model | TensorFlow Lite (TFLite) | Reduce model from float32 to int8: ~4x smaller, faster |
| Convert | `tf.lite.TFLiteConverter` | `.keras` → `.tflite` |
| Runtime | TFLite runtime | Runs on ARM Cortex-M, Android, Raspberry Pi |
| Scaler | Embed as a lookup table | Apply mean/scale normalization in firmware |

**Realistic edge targets:**
- **Smartphone** (Android/iOS): TFLite with GPU delegate. Full model works.
- **Raspberry Pi**: TFLite or ONNX. Full model works.
- **Microcontroller (STM32, nRF52)**: Requires quantization + pruning. Model may need architecture simplification.

**The monitoring gap on edge:** You lose MLflow, drift detection, and central logging. Solutions:
- Periodic sync: run local inference, batch upload statistics when WiFi is available
- On-device anomaly detection: a lightweight threshold check before sending data upstream
- Federated learning: train locally, send only model weight deltas (not raw data)

---

## 20. Interview Q&A Prep

### Core questions

**Q: What is your thesis about in one sentence?**
> An MLOps pipeline that takes raw wrist-sensor data, runs it through a 7-stage batch pipeline with a 1DCNNBiLSTM model, monitors the deployed model's health in production, and governs whether retraining is needed — without ever auto-retraining.

**Q: What is the difference between MLOps and just ML?**
> ML is training a model. MLOps is everything that happens after: deployment, monitoring, drift detection, retraining governance, reproducibility, versioning. Most research stops at training; production systems need the full lifecycle.

**Q: Why did your model's accuracy drop from 93% to 44%?**
> The 93% is 5-fold cross-validation — the model has seen data from the same users. The 44% is LOUO (Leave-One-User-Out) — the model has never seen User 7's motion signature. This is the personalization gap: HAR models don't generalize well across people because everyone moves differently. The monitoring and retraining pipeline exists to close this gap by adapting to new users over time.

**Q: Why no auto-retraining?**
> Health applications require human oversight. If the model silently retrains on bad or mislabeled data, it could produce dangerous predictions with no audit trail. The governance gate (review + labels + QA + human approval) ensures every model change is intentional and traceable.

**Q: How does drift detection work?**
> We compute the z-score of the incoming session's feature distribution against the training baseline. If |z| > 2.0, the data looks statistically different from what the model was trained on. Combined with confidence and temporal consistency checks, this gives three independent signals of model health.

**Q: What is temporal smoothing and why?**
> A k=3 **soft-vote** smoothing over the prediction stream: for each window I average the softmax probability vectors of it and its two neighbours, then take the argmax — so an isolated low-confidence flip gets outvoted by confident neighbours. Crucially it's **additive**: the raw per-window predictions still drive the served output and the monitoring signal; the smoothed accuracy/F1 and smoothed transition rate are reported *alongside* so the monitoring stays honest. It's the "decision" stage of the Activity Recognition Chain (Bulling et al., 2014). It reduces single-window jitter (e.g. one "nail_biting" window in the middle of a sitting session) without hiding genuine instability.

**Q: Why two Docker images?**
> The inference image (slim) runs in production and only needs the packages required to serve predictions. Adding training tools, linting, and jupyter to a production image increases the attack surface and image size unnecessarily. Separation also prevents a developer from accidentally triggering training from the serving container.

**Q: How would you scale this to 10,000 users?**
> Replace local file paths with S3, put MLflow on a dedicated server, containerize the pipeline and run it on ECS or Kubernetes, put the WebUI behind a load balancer. The architecture already supports this: the pipeline is stateless per run, the model is a versioned artifact, and all outputs go to configurable paths. The main addition would be a job queue (SQS/Pub-Sub) to handle concurrent pipeline runs.

**Q: What would you do differently?**
> Three things: (1) Collect more labeled data per user for proper personalization evaluation. (2) Add model calibration (temperature scaling) to make confidence scores more reliable — right now a confident prediction isn't necessarily a correct one. (3) Use a proper remote MLflow tracking server from the start rather than local `mlruns/` — it makes collaboration and history management much easier.

**Q: What is the runtime contract?**
> A fixed folder containing four files: the model, the scaler, the monitoring baseline, and the label order. These four must always travel together. The contract is enforced by MD5 checksums at startup — if any file has changed unexpectedly, the pipeline refuses to run. This prevents silent model corruption.

**Q: How do you know your pipeline actually works?**
> Three ways: (1) pytest contract tests that verify the runtime contract files are consistent; (2) MLflow run history showing every stage completed with SUCCESS status; (3) the Appendix F walkthrough showing live screenshots of the WebUI serving User 7's session with the expected monitoring signals and governance decision.

---

*Generated 2026-06-17. Covers thesis version submitted as `v1.0-submission`.*

# THESIS WORKFLOW (March – June 2026)

Master Thesis: **Offline MLOps Pipeline for Human Activity Recognition**

Student: **Shalin Vachheta**

University: **University of Siegen**

Submission Deadline: **1 July 2026**

---

# 1. Thesis Objective

Design and implement an **offline-first MLOps pipeline** for Human Activity Recognition that supports:

* reproducible model training
* monitoring of production predictions
* drift detection
* trigger-based retraining
* containerized deployment
* reproducible experiments

---

# 2. System Pipeline Overview

Pipeline stages implemented in the repository:

```
Stage 0  Data ingestion
Stage 1  Data validation
Stage 2  Data preprocessing
Stage 3  Model training
Stage 4  Model inference
Stage 5  Model evaluation
Stage 6  Monitoring and drift detection
Stage 7  Trigger decision
Stage 8  Retraining pipeline
Stage 9  Model management
Stage 10 Deployment interface
```

---

# 3. Phase Plan

## Phase 1 — Exam Mode

**Now → April 15**

Focus:

* exam preparation
* thesis structure
* documentation
* diagrams
* evidence organization

Engineering allowed:

* bug fixes
* pipeline stability fixes

Engineering blocked:

* architecture redesign
* new infrastructure
* major refactoring

---

## Phase 2 — Pipeline Finalization

**April 16 → April 30**

Objectives:

* verify pipeline reproducibility
* finalize monitoring logic
* run experiments
* generate artifacts

Tasks:

* clean environment pipeline run
* baseline training
* drift detection experiments
* trigger policy evaluation

---

## Phase 3 — Thesis Writing

**May 1 → May 31**

Write main thesis chapters.

Focus:

* architecture explanation
* pipeline implementation
* monitoring system
* experiments

---

## Phase 4 — Finalization

**June 1 → June 20**

Tasks:

* editing
* figures
* citations
* formatting

---

## Phase 5 — Defense Preparation

**June 20 → June 30**

Tasks:

* presentation slides
* demo preparation
* defense rehearsal

---

# 4. Weekly Roadmap

## March 16 – March 22

* finalize thesis chapter structure
* create thesis LaTeX project
* build figure inventory
* create evidence tracking file

---

## March 23 – March 29

* draft Chapter 1
* draft system architecture overview
* map repository components to thesis chapters

---

## March 30 – April 5

* prepare pipeline architecture diagrams
* collect Wave 1 and Wave 2 evidence
* update documentation

---

## April 6 – April 15

Exam period.

Tasks:

* finalize architecture diagrams
* prepare experiment plan
* minimal pipeline sanity run if necessary

---

## April 16 – April 22

* run reproducibility pipeline
* validate monitoring pipeline
* verify trigger logic

---

## April 23 – April 30

Run experiments:

* baseline evaluation
* drift detection
* trigger behaviour
* runtime analysis

Export artifacts.

---

## May 1 – May 7

Write:

* dataset description
* preprocessing
* model architecture

---

## May 8 – May 14

Write:

* MLOps pipeline implementation
* DVC usage
* MLflow tracking

---

## May 15 – May 21

Write:

* monitoring system
* drift detection
* trigger policy

---

## May 22 – May 31

Write results chapter.

Include:

* experiment tables
* evaluation plots
* runtime charts

---

## June 1 – June 10

Editing pass.

Fix:

* grammar
* diagrams
* cross references

---

## June 10 – June 20

Finalize:

* bibliography
* appendix
* reproducibility instructions

---

## June 20 – June 30

Defense preparation.

Tasks:

* build presentation slides
* prepare demo pipeline run
* rehearse defense talk

---

# 5. Experiments Required

The thesis requires **five experiments**.

### Experiment 1

Model performance evaluation.

Metrics:

* accuracy
* precision
* recall
* F1 score

---

### Experiment 2

Drift detection validation.

Measure detection sensitivity.

---

### Experiment 3

Prediction monitoring behaviour.

Evaluate:

* confidence
* entropy
* prediction distribution

---

### Experiment 4

Trigger policy evaluation.

Demonstrate retraining trigger logic.

---

### Experiment 5

Pipeline runtime evaluation.

Measure:

* runtime vs dataset size
* resource consumption

---

# 6. Repository Validation Checklist

Pipeline:

* full pipeline executes end-to-end
* artifacts are reproducible

Monitoring:

* drift detection works
* baseline statistics valid

CI/CD:

* tests run successfully
* Docker images build successfully

Documentation:

* README updated
* thesis docs aligned with repo structure

---

# 7. Evidence Tracking

Create mapping between experiments and artifacts.

Example:

| Experiment          | Artifact              | Chapter   |
| ------------------- | --------------------- | --------- |
| Baseline evaluation | MLflow run            | Chapter 7 |
| Drift experiment    | monitoring logs       | Chapter 6 |
| Trigger evaluation  | trigger_decision.json | Chapter 6 |

---

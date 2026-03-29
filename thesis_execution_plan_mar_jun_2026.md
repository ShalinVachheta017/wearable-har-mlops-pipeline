# Thesis Execution Plan (March to June 2026)

## Context Lock
- Exams active until 2026-04-15
- Thesis submission target: 2026-07-01
- Strategy: exam-safe scope before 2026-04-15, then thesis execution in fixed waves
- Engineering rule: avoid broad redesign waves; isolate one integrity issue per wave

## Final Thesis Chapter Structure

### Chapter 1 - Introduction
- Background and motivation
- Problem statement
- Objectives and research questions
- Thesis contributions

### Chapter 2 - Background and Related Work
- Human Activity Recognition fundamentals
- Wearable sensor constraints and opportunities
- Production ML and MLOps lifecycle
- Offline-first vs cloud-first MLOps

### Chapter 3 - Offline MLOps System Architecture
- Design goals and constraints
- End-to-end architecture
- Data and model pipelines
- Artifact and model storage
- Deployment and CI/CD architecture

### Chapter 4 - Data Processing and Model Development
- Dataset and sensor profile
- Preprocessing and windowing
- Model architecture and training
- Evaluation metrics

### Chapter 5 - MLOps Pipeline Implementation
- Repository and orchestration design
- DVC data versioning
- MLflow experiment tracking
- Docker runtime setup
- FastAPI inference service
- Testing and CI integration

### Chapter 6 - Monitoring, Drift Detection, and Retraining
- Monitoring architecture
- Drift detection logic
- Prediction quality monitoring
- Trigger policy
- Retraining pipeline and model lifecycle

### Chapter 7 - Experiments and System Evaluation
- Model performance
- Monitoring and drift experiments
- Trigger behavior
- Runtime and scalability measurements

### Chapter 8 - Discussion and Conclusion
- Interpretation of findings
- Limitations
- Future work

## Timeline and Weekly TODO

## Phase 1: Exam-Safe Mode (Now to 2026-04-15)
Workload split:
- 90% exam preparation
- 10% thesis progress

Week of 2026-03-16
- Freeze chapter structure and section headings
- Draft Chapter 1 skeleton
- Draft Chapter 3 section map
- Create figure inventory list

Week of 2026-03-23
- Write Chapter 1 first draft (short)
- Write Chapter 3 architecture overview (short)
- Create experiment matrix (what, metric, artifact path)

Week of 2026-03-30
- Collect evidence links from existing artifacts
- Build thesis figure TODO list by chapter
- Record known integrity risks and open assumptions

Week of 2026-04-06
- Finalize Chapter 1 draft
- Finalize Chapter 3 diagram placeholders
- Prepare post-exam execution checklist

## Phase 2: Pipeline Finalization (2026-04-16 to 2026-04-30)
Week of 2026-04-16
- Run stable baseline pipeline
- Verify monitoring and trigger outputs are traceable
- Lock experiment protocols and random seeds

Week of 2026-04-23
- Run final training/evaluation batch
- Run drift-focused experiments
- Run trigger behavior experiments
- Export all result artifacts for thesis chapter references

## Phase 3: Results Writing (2026-05-01 to 2026-05-31)
Week of 2026-05-01
- Write Chapter 4 draft (data/model)
- Insert preprocessing and model figures

Week of 2026-05-08
- Write Chapter 5 draft (implementation)
- Add repository and pipeline flow diagrams

Week of 2026-05-15
- Write Chapter 6 draft (monitoring/retraining)
- Add drift and trigger evidence tables

Week of 2026-05-22
- Write Chapter 7 draft (experiments)
- Build consolidated results table and discussion notes

Week of 2026-05-29
- Write Chapter 8 draft
- Resolve internal cross-references and placeholders

## Phase 4: Finalization (2026-06-01 to 2026-06-20)
Week of 2026-06-05
- Language edits and chapter coherence pass
- Figure/table numbering and caption quality pass

Week of 2026-06-12
- Citation consistency and bibliography cleanup
- Appendix completion and reproducibility notes

Week of 2026-06-19
- Final formatting, PDF quality check, submission package readiness

## Phase 5: Defense Preparation (2026-06-20 to 2026-06-30)
Week of 2026-06-23
- Build slide deck
- Build demo script from stable pipeline artifacts

Week of 2026-06-27
- Mock defense sessions
- Tighten answers to architecture, monitoring, and retraining questions

## Validation Checklist
- Reproducible full pipeline run from clean environment
- Evidence for each thesis claim mapped to artifact/log/report
- Monitoring outputs and trigger decisions consistently versioned
- All figures reproducible from code or static evidence sources
- Final PDF builds cleanly with no fatal LaTeX errors

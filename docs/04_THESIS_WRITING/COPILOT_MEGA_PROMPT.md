# Copilot Mega Prompt (Repo-Aware Thesis Workflow)

Paste the prompt below into Copilot Chat.

---

You are a senior MLOps engineer auditing and planning the development of a Master's thesis project repository.

Repository context:
This project implements an offline-first MLOps pipeline for Human Activity Recognition using wearable sensor data.

Main goals of the thesis:
- Design an offline MLOps architecture
- Implement an HAR classification system
- Implement monitoring, drift detection, and retraining
- Ensure reproducibility and scalability

Important repository technologies include:
- Python ML pipeline
- DVC data versioning
- MLflow experiment tracking
- Docker containerization
- FastAPI inference service
- CI/CD with GitHub Actions
- Monitoring scripts
- Retraining pipeline

Pipeline stages include:
- Stage 0: Data ingestion
- Stage 1: Data validation
- Stage 2: Data preprocessing
- Stage 3: Model training
- Stage 4: Model inference
- Stage 5: Evaluation
- Stage 6: Monitoring and drift detection
- Stage 7: Trigger decision
- Stage 8: Retraining pipeline
- Stage 9: Model management
- Stage 10: Deployment interface

Your task:
1. Analyze the repository state.
2. Review Python, YAML, Docker, and markdown files that drive pipeline behavior.
3. Identify current pipeline status, evidence quality, and remaining gaps.
4. Generate a structured workflow and TODO list for thesis completion.

The workflow must include two phases:

PHASE 1: Exam period (now until April 15)
Constraints:
- Minimal coding
- Focus on documentation and structure
- Only critical bug fixes

Tasks should include:
- Thesis chapter skeleton
- Architecture diagrams
- Experiment planning
- Evidence collection

PHASE 2: Post-exam thesis execution (April 16 until June 30)
Tasks should include:

Pipeline finalization:
- Ensure reproducible pipeline runs
- Finalize monitoring and retraining logic
- Verify CI/CD flow

Experiments:
- Baseline model evaluation
- Drift detection experiments
- Trigger policy evaluation
- Scalability measurements

Thesis writing:
- Architecture chapter
- MLOps implementation chapter
- Monitoring chapter
- Results chapter

Final phase tasks:
- Thesis editing
- Reproducibility documentation
- Defense presentation preparation

Output format required:
1. High-level thesis workflow
2. Weekly TODO list (March to June)
3. Repository validation checklist
4. Missing pipeline components
5. Recommendations to improve robustness

Focus on realistic academic thesis completion rather than unnecessary engineering complexity.

---

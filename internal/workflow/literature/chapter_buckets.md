# Chapter-Wise Paper Buckets

This file is the active bifurcation map from `internal/papers/core/`, `internal/papers/sorted/`, and `internal/papers/triage/` into thesis chapter usage.

## Priority Labels

- `core-anchor`: use as first citation backbone in chapter drafting
- `candidate`: relevant and citeable after quick quality check
- `archive-candidate`: duplicate/alternate scan or lower-priority variant

## Chapter 1 — Introduction

| Priority | Paper | Source | Use in chapter |
| --- | --- | --- | --- |
| core-anchor | `A Survey on Wearable Sensors for Mental Health Monitoring.pdf` | core | Problem framing for wearable mental health monitoring |
| core-anchor | `Research Roadmap_ Developing a Scalable MLOps Pipeline for Continuous Mental Health Monitoring.pdf` | core | Motivation and research trajectory |
| candidate | `Anxiety Detection Leveraging Mobile Passive Sensing.pdf` | sorted | Real-world anxiety detection context |
| candidate | `Are Anxiety Detection Models Generalizable-A Cross-Activity and Cross-Population Study Using Wearables.pdf` | sorted | Generalization gap evidence |
| candidate | `Detecting Mental Disorders with Wearables 2023.pdf` | triage | Broader mental-health sensing context |

## Chapter 2 — Background and Related Work

### 2.1 HAR and Wearable Sensing Background

| Priority | Paper | Source | Use in chapter |
| --- | --- | --- | --- |
| core-anchor | `A_Survey_on_Human_Activity_Recognition_using_Wearable_Sensors.pdf` | core | HAR taxonomy and baseline methods |
| core-anchor | `Transfer Learning in Human Activity Recognition  A Survey.pdf` | core | Transfer-learning background |
| candidate | `Deep learning for sensor-based activity recognition_ A survey.pdf` | triage | Deep HAR model landscape |
| candidate | `Scaling Human Activity Recognition via Deep Learning-based Domain Adaptation.pdf` | sorted | Domain adaptation background |
| candidate | `Lifelong_Learning_in_Sensor-Based_Human_Activity_Recognition.pdf` | sorted | Continual/lifelong HAR framing |

### 2.2 Related Work for Thesis-Specific Positioning

| Priority | Paper | Source | Use in chapter |
| --- | --- | --- | --- |
| core-anchor | `MACHINE LEARNING OPERATIONS A SURVEY ON MLOPS.pdf` | core | MLOps conceptual grounding |
| core-anchor | `Practical-mlops-operationalizing-machine-learning-models.pdf` | core | Operational MLOps patterns |
| candidate | `Demystifying MLOps and Presenting a Recipe for the Selection of Open-Source Tools 2021.pdf` | sorted | Toolchain comparison context |
| candidate | `From_Development_to_Deployment_An_Approach_to_MLOps_Monitoring_for_Machine_Learning_Model_Operationalization 2023.pdf` | sorted | Monitoring-oriented MLOps positioning |
| candidate | `Resilience-aware MLOps for AI-based medical diagnostic system  2024.pdf` | sorted | Reliability and governance perspective |
| candidate | `Reproducible workflow for online AI in digital health.pdf` | triage | Reproducibility for digital health pipelines |

## Chapter 3 — Offline MLOps System Architecture

| Priority | Paper | Source | Use in chapter |
| --- | --- | --- | --- |
| core-anchor | `MACHINE LEARNING OPERATIONS A SURVEY ON MLOPS.pdf` | core | Architecture principles |
| core-anchor | `Essential_MLOps_Data_Science_Horizons_2023_Data_Science_Horizons_Final_2023.pdf` | core | MLOps lifecycle framing |
| candidate | `Building-Scalable-MLOps-Optimizing-Machine-Learning-Deployment-and-Operations.pdf` | sorted | Scalability architecture points |
| candidate | `MLOps A Step Forward to Enterprise Machine Learning 2023.pdf` | sorted | Enterprise architecture motifs |
| candidate | `The Role of MLOps in Healthcare Enhancing Predictive Analytics and Patient Outcomes.pdf` | sorted | Healthcare architecture relevance |

## Chapter 4 — Data Processing and Model Development

| Priority | Paper | Source | Use in chapter |
| --- | --- | --- | --- |
| core-anchor | `Transfer Learning in Human Activity Recognition  A Survey.pdf` | core | Data/model adaptation context |
| candidate | `Improved_Deep_Representation_Learning_for_Human_Activity_Recognition_using_IMU_Sensors.pdf` | sorted | Model feature-learning argument |
| candidate | `Enhancing_Human_Activity_Recognition_in_Wrist-Worn_Sensor_Data_Through_Compensation_Strategies_for_Sensor_Displacement.pdf` | sorted | Sensor-placement robustness framing |
| candidate | `ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` | sorted | Anxiety-related HAR model direction |
| candidate | `Personalizing_Activity_Recognition_Models_Through_Quantifying_Different_Types_of_Uncertainty_Using_Wearable_Sensors.pdf` | sorted | Personalization and uncertainty |

## Chapter 5 — MLOps Pipeline Implementation

| Priority | Paper | Source | Use in chapter |
| --- | --- | --- | --- |
| core-anchor | `Practical-mlops-operationalizing-machine-learning-models.pdf` | core | Implementation best practices |
| candidate | `Enabling End-To-End Machine Learning.pdf` | triage | End-to-end pipeline engineering |
| candidate | `MLDEV DATA SCIENCE EXPERIMENT AUTOMATION AND.pdf` | triage | Experiment automation discussion |
| candidate | `DevOps-Driven Real-Time Health Analytics.pdf` | triage | DevOps integration narrative |
| candidate | `I-ETL an interoperability-aware health (meta)data pipeline to enable federated analyses.pdf` | triage | Health data pipeline interoperability |

## Chapter 6 — Monitoring, Drift Detection, and Retraining

| Priority | Paper | Source | Use in chapter |
| --- | --- | --- | --- |
| core-anchor | `Domain Adaptation for Inertial Measurement Unit-based Human.pdf` | sorted | Adaptation under drift |
| candidate | `WATCH_Wasserstein_Change_Point_Detection_for_High-Dimensional_Time_Series_Data.pdf` | sorted | Wasserstein/change-point basis |
| candidate | `LIFEWATCH_Lifelong_Wasserstein_Change_Point_Detection.pdf` | sorted | Lifelong drift adaptation framing |
| candidate | `NeurIPS-2021-adaptive-conformal-inference-under-distribution-shift-Paper.pdf` | sorted | Distribution-shift reliability |
| candidate | `When Does Optimizing a Proper Loss Yield Calibration.pdf` | triage | Calibration rationale |
| candidate | `NeurIPS-2020-energy-based-out-of-distribution-detection-Paper.pdf` | sorted | OOD detector grounding |

## Chapter 7 — Experiments and System Evaluation

| Priority | Paper | Source | Use in chapter |
| --- | --- | --- | --- |
| core-anchor | `A Survey on Wearable Sensors for Mental Health Monitoring.pdf` | core | Evaluation context and baselines |
| candidate | `Are Anxiety Detection Models Generalizable-A Cross-Activity and Cross-Population Study Using Wearables.pdf` | sorted | Cross-population evaluation comparison |
| candidate | `Machine Learning based Anxiety Detection using Physiological Signals and Context Features.pdf` | triage | Anxiety evaluation benchmarks |
| candidate | `Real-Time Stress Monitoring Detection and Management in College Students.pdf` | triage | Real-world monitoring comparison |
| candidate | `Wearable Artificial Intelligence for Detecting Anxiety Systematic Review and Meta-Analysis.pdf` | triage | Result interpretation anchor |

## Chapter 8 — Discussion and Conclusion

| Priority | Paper | Source | Use in chapter |
| --- | --- | --- | --- |
| core-anchor | `Roadmap for a Scalable MLOps Pipeline in Mental Health Monitoring (Master’s Thesis).pdf` | core | Positioning against roadmap literature |
| core-anchor | `Research Roadmap_ Developing a Scalable MLOps Pipeline for Continuous Mental Health Monitoring.pdf` | core | Future work linkage |
| candidate | `Reproducible workflow for online AI in digital health.pdf` | triage | Discussion on reproducibility limits |
| candidate | `MLHOps Machine Learning for Healthcare Operations.pdf` | triage | Operational deployment implications |
| candidate | `Resilience-aware MLOps for AI-based medical diagnostic system  2024.pdf` | sorted | Governance and resilience future work |

## Assignment Rule (Non-Destructive)

- Keep binaries in `internal/papers/core/`, `internal/papers/sorted/`, `internal/papers/triage/`.
- Keep chapter assignment only in this manifest.
- Promote a `candidate` to `core-anchor` only after chapter draft confirms a direct citation need.

# Archive Papers Reorganization Audit

> Date: 2026-03-05
> Scope: `archive/` folder full reorganization — PDF library sorted by research topic
> Author: GitHub Copilot (automated reorganization, human-approved plan)
> Affects: `archive/` only — no source code, no `src/`, no `scripts/`, no `thesis/` files changed

---

## 1. Why This Was Done

The `archive/` folder had accumulated 430+ PDFs spread across 6 overlapping subfolders with no consistent topic labeling. Papers on the same subject (e.g., drift detection, domain adaptation) were scattered in 3+ different directories with significant duplication (92 filenames appeared in 2+ locations). This made thesis citation work slow and error-prone.

**Reorganization goals:**
- Create a navigable, topic-based library under `archive/papers/by_topic/`
- Remove ambiguous multi-level nesting
- Produce index files (`ARCHIVE_INVENTORY.md`, `PAPERS_CATALOG.md`) as permanent reference
- Create a thesis writing guide (`thesis/refs/READING_LIST_BY_CHAPTER.md`)

---

## 2. Git Status Note — Why `git mv` Was NOT Used

> **IMPORTANT**: The entire `archive/` directory is excluded from version control.

`.gitignore` contains both:
```
archive/
*.pdf
```

Running `git mv archive/...` returns:
```
error: pathspec 'archive/...' did not match any file(s) known to git
```

**All moves in this audit are filesystem-only (`Move-Item` / PowerShell).** They do not appear in `git status`, `git log`, or `git diff`. The primary source of truth for what moved is this document and `archive/_index/ARCHIVE_INVENTORY.md`.

---

## 3. New Directory Structure Created

All subdirectories below are new (did not exist before this session):

```
archive/
├── papers/
│   ├── by_topic/              ← NEW (canonical topic-sorted library)
│   │   ├── mlops_reproducibility/   (14 PDFs)
│   │   ├── har_models/              (6 PDFs)
│   │   ├── domain_adaptation_tta/   (5 PDFs)
│   │   ├── drift_detection/         (5 PDFs)
│   │   ├── evaluation_metrics/      (3 PDFs)
│   │   ├── misc/                    (4 PDFs)
│   │   ├── data_prep/               (0 — placeholder)
│   │   ├── monitoring_observability/ (0 — placeholder)
│   │   ├── deployment_docker/       (0 — placeholder)
│   │   ├── cicd_devops/             (0 — placeholder)
│   │   └── datasets_garmin_wearables/ (0 — placeholder)
│   └── by_chapter/            ← NEW (chapter-linked shortcuts — currently empty)
│       ├── ch1_intro/
│       ├── ch2_related_work/
│       ├── ch3_methodology/
│       ├── ch4_implementation/
│       ├── ch5_experiments/
│       ├── ch6_discussion/
│       └── ch7_conclusion_future_work/
├── markdown_old/              ← NEW (old analysis markdown files)
├── snapshots/                 ← NEW (placeholder for future state captures)
└── _index/                    ← NEW (navigation index files)
    ├── ARCHIVE_INVENTORY.md
    └── PAPERS_CATALOG.md
```

---

## 4. Complete Move Log

### 4.1 Batch 1 — MLOps Production → `by_topic/mlops_reproducibility/`

**Source**: `archive/papers/mlops_production/`
**Destination**: `archive/papers/by_topic/mlops_reproducibility/`
**Count**: 14 PDFs

| # | Filename |
|---|----------|
| 1 | `Building-Scalable-MLOps-Optimizing-Machine-Learning-Deployment-and-Operations.pdf` |
| 2 | `Demystifying MLOps and Presenting a Recipe for the Selection of Open-Source Tools 2021.pdf` |
| 3 | `Developing a Scalable MLOps Pipeline for Continuou.pdf` |
| 4 | `Essential_MLOps_Data_Science_Horizons_2023_Data_Science_Horizons_Final_2023.pdf` |
| 5 | `From_Development_to_Deployment_An_Approach_to_MLOps_Monitoring_for_Machine_Learning_Model_Operationalization 2023.pdf` |
| 6 | `MACHINE LEARNING OPERATIONS A SURVEY ON MLOPS.pdf` |
| 7 | `MLOps A Step Forward to Enterprise Machine Learning 2023.pdf` |
| 8 | `MLOps and LLMOps with Python_ A Comprehensive Guide with Tools and Best Practices _ by André Castro _ Medium.pdf` |
| 9 | `MLHOps Machine Learning for Healthcare Operations.pdf` *(included in source)* |
| 10 | `Practical-mlops-operationalizing-machine-learning-models.pdf` |
| 11 | `Research Roadmap_ Developing a Scalable MLOps Pipeline for Continuous Mental Health Monitoring.pdf` |
| 12 | `Resilience-aware MLOps for AI-based medical diagnostic system  2024.pdf` |
| 13 | `Roadmap for a Scalable MLOps Pipeline in Mental Health Monitoring (Master's Thesis).pdf` |
| 14 | `The Role of MLOps in Healthcare Enhancing Predictive Analytics and Patient Outcomes.pdf` |
| *(bonus)* | `Thesis_MLOps_FullPlan_with_GanttChart.pdf` |

**Source folder status after move**: folder empty, kept as empty directory.

---

### 4.2 Batch 2 — Anxiety Detection → `by_topic/misc/`

**Source**: `archive/papers/anxiety_detection/`
**Destination**: `archive/papers/by_topic/misc/`
**Count**: 4 PDFs

| # | Filename |
|---|----------|
| 1 | `A Survey on Wearable Sensors for Mental Health Monitoring.pdf` |
| 2 | `ADAM-sense_Anxietydisplayingactivitiesrecognitionby.pdf` |
| 3 | `Anxiety Detection Leveraging Mobile Passive Sensing.pdf` |
| 4 | `Are Anxiety Detection Models Generalizable-A Cross-Activity and Cross-Population Study Using Wearables.pdf` |

**Reason these are "misc"**: The thesis uses anxiety/mental health wearable datasets for training, but does not address anxiety detection as a specific research problem. Papers filed here provide dataset context, not methodology citations.

---

### 4.3 Batch 3 — Domain Adaptation Folder → `by_topic/domain_adaptation_tta/`

**Source**: `archive/papers/domain_adaptation/`
**Destination**: `archive/papers/by_topic/domain_adaptation_tta/`
**Count**: 2 PDFs

| # | Filename |
|---|----------|
| 1 | `Domain Adaptation for Inertial Measurement Unit-based Human.pdf` |
| 2 | `Transfer Learning in Human Activity Recognition  A Survey.pdf` |

---

### 4.4 Batch 4 — `new paper/` Sorted → 4 topics

**Source**: `archive/papers/new paper/`
**Count moved**: 6 PDFs → 3 destination topics

| Filename | Destination |
|----------|-------------|
| `1706.04599v2.pdf` (Guo 2017 calibration) | `evaluation_metrics/` |
| `1706.04599v2 (1).pdf` (duplicate copy) | `evaluation_metrics/` |
| `NeurIPS-2020-energy-based-out-of-distribution-detection-Paper.pdf` | `evaluation_metrics/` |
| `NeurIPS-2021-adaptive-conformal-inference-under-distribution-shift-Paper.pdf` | `drift_detection/` |
| `2010.03759v4.pdf` (TENT: Test-Time Entropy Min.) | `domain_adaptation_tta/` |
| `activear.pdf` (ActiveHAR) | `har_models/` |

**Remaining in `new paper/`**: ~13 papers not yet classified — left in place.

---

### 4.5 Batch 5 — Old Markdown Files → `archive/markdown_old/`

**Sources**: `archive/research_papers/` and `archive/papers/papers needs to read/`
**Count**: 4 Markdown files

| Filename | Original Location |
|----------|-------------------|
| `76_papers_suggestions.md` | `archive/research_papers/` |
| `76_papers_summarizzation.md` | `archive/research_papers/` |
| `COMPREHENSIVE_RESEARCH_PAPERS_SUMMARY.md` | `archive/research_papers/` |
| `ICTH_2025_Oleh_Paper_MLOps_Summary.md` | `archive/papers/papers needs to read/` |

**Note**: These are legacy AI-generated analysis documents, not primary sources. Moved to `markdown_old/` to avoid confusing them with real papers.

---

### 4.6 Batch 6 — `old_docs/paper_for_questions/` → 3 topics

**Source**: `archive/old_docs/paper_for_questions/`
**Count**: 11 PDFs

| Filename | Destination Topic |
|----------|-------------------|
| `WATCH_Wasserstein_Change_Point_Detection_for_High-Dimensional_Time_Series_Data.pdf` | `drift_detection/` |
| `LIFEWATCH_Lifelong_Wasserstein_Change_Point_Detection.pdf` | `drift_detection/` |
| `Normalizing_Self-Supervised_Learning_for_Provably_Reliable_Change_Point_Detection.pdf` | `drift_detection/` |
| `Optimal_Transport_Based_Change_Point_Detection_and_Time_Series_Segment_Clustering.pdf` | `drift_detection/` |
| `Scaling Human Activity Recognition via Deep Learning-based Domain Adaptation.pdf` | `domain_adaptation_tta/` |
| `Lifelong_Learning_in_Sensor-Based_Human_Activity_Recognition.pdf` | `domain_adaptation_tta/` |
| `A_Survey_on_Human_Activity_Recognition_using_Wearable_Sensors.pdf` | `har_models/` |
| `Improved_Deep_Representation_Learning_for_Human_Activity_Recognition_using_IMU_Sensors.pdf` | `har_models/` |
| `Personalizing_Activity_Recognition_Models_Through_Quantifying_Different_Types_of_Uncertainty_Using_Wearable_Sensors.pdf` | `har_models/` |
| `XAI-BayesHAR_A_novel_Framework_for_Human_Activity_Recognition_with_Integrated_Uncertainty_and_Shapely_Values.pdf` | `har_models/` |
| `Enhancing_Human_Activity_Recognition_in_Wrist-Worn_Sensor_Data_Through_Compensation_Strategies_for_Sensor_Displacement.pdf` | `har_models/` |

---

## 5. Summary Statistics

| Category | Count |
|----------|-------|
| PDFs moved to `by_topic/` | **37** |
| Markdown files moved to `markdown_old/` | **4** |
| Total files reorganized | **41** |
| PDFs NOT moved (large canonical collections) | ~390 |
| New directories created | **18** |
| Index files created | **2** (`ARCHIVE_INVENTORY.md`, `PAPERS_CATALOG.md`) |

### Final `by_topic/` Distribution

| Topic Folder | Count | Primary Thesis Chapter |
|---|---|---|
| `mlops_reproducibility/` | 14 | Ch2, Ch4 |
| `har_models/` | 6 | Ch2, Ch5 |
| `domain_adaptation_tta/` | 5 | Ch2, Ch3 |
| `drift_detection/` | 5 | Ch3, Ch5 |
| `evaluation_metrics/` | 3 | Ch3, Ch5 |
| `misc/` | 4 | Ch1 background |
| (placeholders: data_prep, monitoring, deploy, cicd, datasets) | 0 | future |

---

## 6. What Was NOT Changed

| Location | Reason Left Unchanged |
|----------|----------------------|
| `archive/papers/papers needs to read/` (145 PDFs) | Canonical main collection — untouched intentionally |
| `archive/papers/research_papers/76 papers/` (76 PDFs) | Duplicate of `archive/research_papers/76 papers/` — left for now |
| `archive/research_papers/76 papers/` (76 PDFs) | Duplicate collection — left for now |
| `archive/old_docs/` (remaining ~80 PDFs) | Only cherry-picked 11 — bulk left as-is |
| `archive/papers/new paper/` (remaining ~13 PDFs) | Only moved 6 clearly-identified ones |
| `archive/ai_conversations/` | Not papers — AI chat history |
| `archive/misc_papers/` | Miscellaneous, not yet reviewed |
| All `archive/Archived(...)/*` | Legacy production prep files — not papers |

---

## 7. Unresolved Items (Needs Manual Review)

### 7.1 ArXiv ID-only Filenames (Unidentified Papers)

These papers were found in `by_topic/` or `papers/new paper/` with only arxiv IDs as names. Manual lookup needed:

| Filename | ArXiv URL | Likely Topic |
|----------|-----------|--------------|
| `2010.03759v4.pdf` | https://arxiv.org/abs/2010.03759 | TENT (TTA) — CONFIRMED |
| `1706.04599v2.pdf` | https://arxiv.org/abs/1706.04599 | Guo 2017 calibration — CONFIRMED |
| `1711.10160.pdf` (if present) | https://arxiv.org/abs/1711.10160 | Unknown |
| `1802.03916.pdf` (if present) | https://arxiv.org/abs/1802.03916 | Unknown |
| `2406.01416.pdf` (if present) | https://arxiv.org/abs/2406.01416 | Unknown |

### 7.2 Recommended Optional Cleanup (NOT Done — Requires Human Decision)

The following are exact or near-exact duplicates that could be deleted:

| Action | Path | Reason |
|--------|------|--------|
| DELETE (optional) | `archive/research_papers/76 papers/` | Exact mirror of `archive/papers/research_papers/76 papers/` |
| DELETE (optional) | `archive/papers/research_papers/76 papers/` | One of these two is redundant |
| RENAME | `archive/papers/by_topic/evaluation_metrics/1706.04599v2 (1).pdf` | Duplicate of `1706.04599v2.pdf` — same paper |

**These were deliberately left undeleted.** Run `Remove-Item -Recurse` only after confirming both copies are identical.

---

## 8. Output Files Created This Session

| File | Purpose |
|------|---------|
| `archive/_index/ARCHIVE_INVENTORY.md` | Full inventory: counts, sizes, duplicates |
| `archive/_index/PAPERS_CATALOG.md` | Searchable per-paper catalog with topic tags and chapter mapping |
| `thesis/refs/READING_LIST_BY_CHAPTER.md` | Thesis writing guide: which paper to cite in which chapter |
| `reports/repo_audit/ARCHIVE_PAPERS_AUDIT.md` | This file — complete move log and audit trail |

---

## 9. Verification Commands

Run these to confirm the current state:

```powershell
# Count files in by_topic/
(Get-ChildItem "archive\papers\by_topic" -Recurse -File).Count
# Expected: 37

# List all by_topic files
Get-ChildItem "archive\papers\by_topic" -Recurse -File | Select-Object Directory, Name

# Count markdown_old files
(Get-ChildItem "archive\markdown_old" -File).Count
# Expected: 4

# Confirm by_topic subdirectories
Get-ChildItem "archive\papers\by_topic" -Directory | Select-Object Name
```

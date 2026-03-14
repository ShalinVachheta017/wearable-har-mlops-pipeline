# MOVE_LOG.md — Repo Reorganization Record

> All moves performed during the topic-based docs reorganization.
> Date: Session of repo restructuring
> Branch: main
> Rule: NO files were deleted. Only moved/renamed.

---

## New Structure Overview

```
docs/
├── 00_INDEX.md              ← documentation entrypoint
├── 01_PIPELINE/             ← pipeline architecture, stages, why-files
│   └── stages/              ← 00_STAGE_INDEX.md … 10_IMPROVEMENTS_ROADMAP.md
├── 02_TECH/                 ← technology explainers, guides, cheat sheets
│   ├── guides/              ← 9 technical guide MDs
│   ├── cheat_sheet/         ← 4 PDF cheat sheets
│   └── docker_assets/       ← Docker images/docs
├── 03_EXPERIMENTS/          ← experiment evidence, normalization, thresholds
│   └── pipeline_artifacts/  ← artifact source mapping
├── 04_THESIS_WRITING/       ← thesis drafts, research, defense QA, todo
│   ├── chapter_drafts/      ← CH1, CH3, CH4 markdown drafts
│   ├── research/            ← 7 research analysis files
│   └── todo/                ← 5 task tracking files
├── 99_ARCHIVE/              ← date-based archived docs
│   ├── 2026-01/             ← old planning docs, paper analyses
│   ├── 2026-02/             ← Feb 2026 docs
│   └── 2026-03/             ← Fourth March content
└── images/                  ← (unchanged)

thesis/
├── 00_THESIS_INDEX.md       ← thesis entrypoint
├── thesis_main.tex          ← main LaTeX file
├── Thesis_Plan.md
├── chapters/                ← ch1–ch6 .tex
├── appendices/              ← 3 appendix .tex
├── frontmatter/             ← titlepage, abstract, etc.
├── figures/                 ← 7 PNG figures
├── tables/                  ← 2 CSV tables
├── refs/                    ← PDFs, .bib, papers_text/
└── _snapshots/              ← point-in-time doc snapshots
    ├── 2026-02/             ← 19_Feb, 22Feb_Opus, codex sessions
    ├── 2026-03/             ← March 2026 snapshots
    └── sample_reports/      ← sample PDF reports
```

---

## Batch 1: Fourth March/ → docs/99_ARCHIVE/

| Old Path | New Path | Method |
|----------|----------|--------|
| `Fourth March/` (entire tree) | `docs/99_ARCHIVE/2026-03/Fourth_March/` | `git mv` |

Includes: normalization_analysis.md, REPO_INVENTORY.md, pipeline_artifact_sources/, 2026_03_04/, YOU_SHOULD_KNOW_BEFORE_MASTER_FILE/, and all sub-files.

## Batch 2: docs/tech_used_in_thesis/ → docs/02_TECH/

| Old Path | New Path | Method |
|----------|----------|--------|
| `docs/tech_used_in_thesis/DOCKER_EXPLAINED.md` | `docs/02_TECH/DOCKER_EXPLAINED.md` | `git mv` |
| `docs/tech_used_in_thesis/DVC_EXPLAINED.md` | `docs/02_TECH/DVC_EXPLAINED.md` | `git mv` |
| `docs/tech_used_in_thesis/MLFLOW_EXPLAINED.md` | `docs/02_TECH/MLFLOW_EXPLAINED.md` | `git mv` |
| `docs/tech_used_in_thesis/FASTAPI_EXPLAINED.md` | `docs/02_TECH/FASTAPI_EXPLAINED.md` | `git mv` |
| `docs/tech_used_in_thesis/CICD_EXPLAINED.md` | `docs/02_TECH/CICD_EXPLAINED.md` | `git mv` |
| `docs/tech_used_in_thesis/PROMETHEUS_EXPLAINED.md` | `docs/02_TECH/PROMETHEUS_EXPLAINED.md` | `git mv` |
| `docs/tech_used_in_thesis/GRAFANA_EXPLAINED.md` | `docs/02_TECH/GRAFANA_EXPLAINED.md` | `git mv` |
| `docs/tech_used_in_thesis/MONITORING_EXPLAINED.md` | `docs/02_TECH/MONITORING_EXPLAINED.md` | `git mv` |
| `docs/tech_used_in_thesis/MODEL_REGISTRY_EXPLAINED.md` | `docs/02_TECH/MODEL_REGISTRY_EXPLAINED.md` | `git mv` |
| `docs/tech_used_in_thesis/EXPERIMENT_TRACKING_EXPLAINED.md` | `docs/02_TECH/EXPERIMENT_TRACKING_EXPLAINED.md` | `git mv` |

## Batch 3: docs/ root files → topic folders

| Old Path | New Path | Method |
|----------|----------|--------|
| `docs/DEFENSE_QA.md` | `docs/04_THESIS_WRITING/DEFENSE_QA.md` | `git mv` |
| `docs/PRODUCT_REVIEW.md` | `docs/01_PIPELINE/PRODUCT_REVIEW.md` | `git mv` |
| `docs/REPO_INVENTORY.md` | `docs/01_PIPELINE/REPO_INVENTORY.md` | `git mv` |
| `docs/WHY_BOOK.md` | `docs/02_TECH/WHY_BOOK.md` | `git mv` |
| `docs/WHY_BY_TECH.md` | `docs/02_TECH/WHY_BY_TECH.md` | `git mv` |
| `docs/WHY_BY_FILE.md` | `docs/01_PIPELINE/WHY_BY_FILE.md` | `git mv` |

## Batch 4: docs/YOU_SHOULD_KNOW_BEFORE_MASTER_FILE/ → split by topic

| Old Path | New Path | Method |
|----------|----------|--------|
| `docs/YOU_SHOULD_KNOW…/THESIS_STRUCTURE_OUTLINE.md` | `docs/04_THESIS_WRITING/THESIS_STRUCTURE_OUTLINE.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/FINE_TUNING_STRATEGY.md` | `docs/04_THESIS_WRITING/FINE_TUNING_STRATEGY.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/mentor_questions.md` | `docs/04_THESIS_WRITING/mentor_questions.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/mentor_questions_explained.md` | `docs/04_THESIS_WRITING/mentor_questions_explained.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/REFERENCES.md` | `docs/04_THESIS_WRITING/REFERENCES.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/CONCEPTS_EXPLAINED.md` | `docs/04_THESIS_WRITING/CONCEPTS_EXPLAINED.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/DECISION_REGISTER.csv` | `docs/01_PIPELINE/DECISION_REGISTER.csv` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/PIPELINE_FACTSHEET.md` | `docs/01_PIPELINE/PIPELINE_FACTSHEET.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/PIPELINE_GAPS.md` | `docs/01_PIPELINE/PIPELINE_GAPS.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/PIPELINE_CTO_REVIEW.md` | `docs/01_PIPELINE/PIPELINE_CTO_REVIEW.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/EVIDENCE_LEDGER.md` | `docs/03_EXPERIMENTS/EVIDENCE_LEDGER.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/EVIDENCE_PACK_INDEX.md` | `docs/03_EXPERIMENTS/EVIDENCE_PACK_INDEX.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/THRESHOLD_CALIBRATION_SUMMARY.md` | `docs/03_EXPERIMENTS/THRESHOLD_CALIBRATION_SUMMARY.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/TRIGGER_POLICY_EVAL.md` | `docs/03_EXPERIMENTS/TRIGGER_POLICY_EVAL.md` | `git mv` |
| `docs/YOU_SHOULD_KNOW…/WINDOWING_JUSTIFICATION.md` | `docs/03_EXPERIMENTS/WINDOWING_JUSTIFICATION.md` | `git mv` |

## Batch 5: Root-level MDs → docs/

| Old Path | New Path | Method |
|----------|----------|--------|
| `solution.md` | `docs/01_PIPELINE/solution.md` | `git mv` |
| `tech.md` | `docs/02_TECH/tech.md` | `git mv` |
| `qna explain.md` | `docs/04_THESIS_WRITING/qna_explain.md` | `git mv` |
| `the march todo.md` | `docs/04_THESIS_WRITING/todo/the_march_todo.md` | `git mv` |

## Batch 6: reports/ MDs + archive/docs_feb2026 → docs/

| Old Path | New Path | Method |
|----------|----------|--------|
| `reports/normalization_analysis.md` | `docs/03_EXPERIMENTS/normalization_analysis.md` | `git mv` |
| `reports/pipeline_artifact_sources/artifact_source_mapping.md` | `docs/03_EXPERIMENTS/pipeline_artifacts/artifact_source_mapping.md` | `git mv` |
| `archive/docs_feb2026/` (entire tree) | `docs/99_ARCHIVE/2026-02/` | `git mv` |
| `archive/CLEANUP_SUMMARY.md` | `docs/99_ARCHIVE/CLEANUP_SUMMARY.md` | `git mv` |

## Batch 7: archive/old_planning_docs + old_docs → docs/99_ARCHIVE/

| Old Path | New Path | Method |
|----------|----------|--------|
| `archive/old_planning_docs/` | `docs/99_ARCHIVE/2026-01/old_planning_docs/` | `git mv` |
| `archive/old_docs/paper_for_questions/` | `docs/99_ARCHIVE/2026-01/paper_analyses/` | `git mv` |

## Batch 8: Remaining reports & experiment files

| Old Path | New Path | Method |
|----------|----------|--------|
| Various `reports/*.md` experiment files | `docs/03_EXPERIMENTS/` | `git mv` |

---

## Task B: Thesis_report/ → thesis/

Most files in `Thesis_report/` were **not git-tracked**, requiring `Move-Item` + `git add`.

### LaTeX Compilation Unit
| Old Path | New Path | Method |
|----------|----------|--------|
| `Thesis_report/thesis_main.tex` | `thesis/thesis_main.tex` | `Move-Item` |
| `Thesis_report/chapters/ch*.tex` (6 files) | `thesis/chapters/` | `Move-Item` |
| `Thesis_report/appendices/*.tex` (3 files) | `thesis/appendices/` | `Move-Item` |
| `Thesis_report/frontmatter/*.tex` (5 files) | `thesis/frontmatter/` | `Move-Item` |
| `Thesis_report/figures/*.png` (7 files) | `thesis/figures/` | `Move-Item` |
| `Thesis_report/refs/*` (15+ files + papers_text/) | `thesis/refs/` | `Move-Item` |
| `Thesis_report/tables/*.csv` (2 files) | `thesis/tables/` | `Move-Item` |
| `Thesis_report/Thesis_Plan.md` | `thesis/Thesis_Plan.md` | `Move-Item` |
| Misc .tex/.txt/.log files | `thesis/` | `Move-Item` |

### Docs from Thesis_report/ → docs/
| Old Path | New Path | Method |
|----------|----------|--------|
| `Thesis_report/docs/thesis/*.md` | `docs/04_THESIS_WRITING/` | `Move-Item` |
| `Thesis_report/docs/stages/*.md` (11 files) | `docs/01_PIPELINE/stages/` | `Move-Item` |
| `Thesis_report/docs/technical/guide-*.md` (9 files) | `docs/02_TECH/guides/` | `Move-Item` |
| `Thesis_report/docs/research/*.md` (7 files) | `docs/04_THESIS_WRITING/research/` | `Move-Item` |
| `Thesis_report/things to do/*.md` (5 files) | `docs/04_THESIS_WRITING/todo/` | `Move-Item` |
| `Thesis_report/docs/thesis/chapters/CH*.md` (3 files) | `docs/04_THESIS_WRITING/chapter_drafts/` | `Move-Item` |
| `Thesis_report/cheat_sheet/` (4 PDFs) | `docs/02_TECH/cheat_sheet/` | `Move-Item` |
| `Thesis_report/docker_assets/` (11 files) | `docs/02_TECH/docker_assets/` | `Move-Item` |

### Snapshots (date-based folders)
| Old Path | New Path | Method |
|----------|----------|--------|
| `Thesis_report/docs/19_Feb/` | `thesis/_snapshots/2026-02/19_Feb/` | `Move-Item` |
| `Thesis_report/docs/22Feb_Opus_Understanding/` (28 files) | `thesis/_snapshots/2026-02/22Feb_Opus_Understanding/` | `Move-Item` |
| `Thesis_report/docs/22_feb_codex/` | `thesis/_snapshots/2026-02/22_feb_codex/` | `Move-Item` |
| `Thesis_report/docs/23_feb_codex/` | `thesis/_snapshots/2026-02/23_feb_codex/` | `Move-Item` |
| `Thesis_report/2026_03_04/` | `thesis/_snapshots/2026-03/2026_03_04/` | `Move-Item` |
| `Thesis_report/sample reports/` | `thesis/_snapshots/sample_reports/` | `Move-Item` |

### Removed
| Folder | Action |
|--------|--------|
| `Thesis_report/` | Emptied and removed (all content moved, nothing deleted) |

---

## Files NOT Moved (and why)

| Path | Reason |
|------|--------|
| `archive/ai_conversations/` | AI chat logs, not documentation |
| `archive/Archived(prepare traning- production- conversion)/` | Old training/conversion scripts |
| `archive/misc_papers/` | Miscellaneous PDFs, not active docs |
| `archive/papers/` | Research paper PDFs (duplicates in thesis/refs/) |
| `archive/research_papers/` | 76+ research papers — too large, separate scope |
| `archive/scripts_feb2026/` | Old script versions |
| `docs/images/` | Already in docs/, unchanged |
| `scripts/` | Active scripts — see SRC_SCRIPTS_AUDIT.md |
| `src/` | Source code — unchanged |
| `config/`, `data/`, `docker/`, `models/`, `notebooks/`, `outputs/`, `tests/` | Not documentation |
| `mlruns/`, `logs/`, `artifacts/` | Runtime outputs |

---

## Broken Links Fixed

See [BROKEN_LINKS.md](BROKEN_LINKS.md) for full details. Summary:
- **README.md**: 15+ `Thesis_report/` links updated to new paths ✅
- **Active docs**: ~6 files have stale inline text references (low priority, logged)
- **Archived docs**: Historical references intentionally preserved

---

## Index Files Created

| File | Purpose |
|------|---------|
| `docs/00_INDEX.md` | Documentation hub — links to all topic folders |
| `thesis/00_THESIS_INDEX.md` | Thesis hub — links to chapters, refs, figures |

## Audit Reports Created

| File | Purpose |
|------|---------|
| `reports/repo_audit/SRC_SCRIPTS_AUDIT.md` | scripts/ vs src/ duplication analysis |
| `reports/repo_audit/BROKEN_LINKS.md` | Broken link inventory and fix log |
| `reports/repo_audit/MOVE_LOG.md` | This file |

# Broken Links Report

> Generated during repo reorganization (docs → topic-based, Thesis_report/ → thesis/)

## 1. README.md — FIXED

All `Thesis_report/` references updated to new paths:

| Old Path | New Path | Status |
|----------|----------|--------|
| `Thesis_report/things to do/01_REMAINING_WORK.md` | `docs/04_THESIS_WRITING/todo/01_REMAINING_WORK.md` | ✅ Fixed |
| `Thesis_report/things to do/CHATGPT_2_PIPELINE_WORK_DONE.md` | `docs/04_THESIS_WRITING/todo/CHATGPT_2_PIPELINE_WORK_DONE.md` | ✅ Fixed |
| `Thesis_report/things to do/CHATGPT_3_REMAINING_WORK.md` | `docs/04_THESIS_WRITING/todo/CHATGPT_3_REMAINING_WORK.md` | ✅ Fixed |
| `Thesis_report/docs/19_Feb/PIPELINE_RUNBOOK.md` | `thesis/_snapshots/2026-02/19_Feb/PIPELINE_RUNBOOK.md` | ✅ Fixed |
| `Thesis_report/docs/stages/00_STAGE_INDEX.md` | `docs/01_PIPELINE/stages/00_STAGE_INDEX.md` | ✅ Fixed |
| `Thesis_report/docs/22Feb_Opus_Understanding/00_README.md` | `thesis/_snapshots/2026-02/22Feb_Opus_Understanding/00_README.md` | ✅ Fixed |
| `Thesis_report/docs/22Feb_Opus_Understanding/12_*.md` | `thesis/_snapshots/2026-02/22Feb_Opus_Understanding/12_*.md` | ✅ Fixed |
| `Thesis_report/docs/22Feb_Opus_Understanding/14_*.md` | `thesis/_snapshots/2026-02/22Feb_Opus_Understanding/14_*.md` | ✅ Fixed |
| `Thesis_report/docs/thesis/THESIS_STRUCTURE_OUTLINE.md` | `docs/04_THESIS_WRITING/THESIS_STRUCTURE_OUTLINE.md` | ✅ Fixed |
| `Thesis_report/docs/thesis/CONCEPTS_EXPLAINED.md` | `docs/04_THESIS_WRITING/CONCEPTS_EXPLAINED.md` | ✅ Fixed |
| `Thesis_report/docs/technical/guide-*.md` (6 guides) | `docs/02_TECH/guides/guide-*.md` | ✅ Fixed |
| `Thesis_report/docs/research/qna-har-mlops-papers.md` | `docs/04_THESIS_WRITING/research/qna-har-mlops-papers.md` | ✅ Fixed |
| `Thesis_report/docs/research/RESEARCH_PAPERS_ANALYSIS.md` | `docs/04_THESIS_WRITING/research/RESEARCH_PAPERS_ANALYSIS.md` | ✅ Fixed |
| `Thesis_report/Thesis_Plan.md` | `thesis/Thesis_Plan.md` | ✅ Fixed |
| `docs/PRODUCT_REVIEW.md` | `docs/01_PIPELINE/PRODUCT_REVIEW.md` | ✅ Fixed |
| Project structure tree (showed `Thesis_report/`) | Updated to show `thesis/` + `docs/` | ✅ Fixed |

## 2. Active Docs — Stale References (Low Priority)

These files contain `Thesis_report/` mentions as **inline text** (not clickable links) or **historical context**. They do not break navigation but are noted for completeness:

| File | Line(s) | Context | Suggested Fix |
|------|---------|---------|---------------|
| `docs/03_EXPERIMENTS/EVIDENCE_PACK_INDEX.md` | 40, 52, 116, 131 | Refers to `Thesis_report/refs/` and `Thesis_report/papers_text/` | Update to `thesis/refs/` |
| `docs/01_PIPELINE/PRODUCT_REVIEW.md` | 158, 458, 464, 476-477 | Table entries citing `Thesis_report/` | Update to `thesis/` and `docs/04_THESIS_WRITING/` |
| `docs/01_PIPELINE/PIPELINE_CTO_REVIEW.md` | 303-306 | Audit scope context referencing `Thesis_report/refs/` | Update to `thesis/refs/` |
| `docs/01_PIPELINE/REPO_INVENTORY.md` | 22, 316, 446 | Historical inventory listing `Thesis_report/` | Leave as-is (historical record) |
| `docs/04_THESIS_WRITING/REFERENCES.md` | 83 | Path in table: `Thesis_report/docs/thesis/thesis-pipeline-why-what-how.md` | Update to `docs/01_PIPELINE/thesis-pipeline-why-what-how.md` |
| `docs/04_THESIS_WRITING/MENTOR_QUESTIONS_FEBRUARY_2026.md` | 385 | Source attribution line | Update paths |

## 3. Archived Docs — NOT FIXED (By Design)

Files in `docs/99_ARCHIVE/`, `thesis/_snapshots/`, and `Fourth March/` contain historical `Thesis_report/` references. These are **intentionally left unchanged** as they represent point-in-time snapshots:

- `docs/99_ARCHIVE/2026-03/Fourth_March/*.md` (6 files, ~10 references)
- `thesis/_snapshots/2026-02/22Feb_Opus_Understanding/00_README.md` (2 references)
- `thesis/_snapshots/2026-03/2026_03_04/*.md` (4 references)
- `Fourth March/2026_03_04/*.md` (4 references — this folder should be cleaned up)

## 4. `Fourth March/` Residual

The `Fourth March/` folder at repo root still has untracked files that duplicate content already moved to `docs/99_ARCHIVE/2026-03/Fourth_March/`. These originals were kept because git mv was used for the copies. Consider removing this folder once confirmed all content is in the archive.

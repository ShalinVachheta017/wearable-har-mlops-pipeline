# Internal Move Index

Date: 2026-03-27  
Branch: chore/repo-cleanup  
Purpose: Track organization-only moves into `internal/`.

| Original Path | New Path | Summary | Category | Status |
|---|---|---|---|---|
| `docs/04_THESIS_WRITING/` | `internal/writing_support/04_THESIS_WRITING/` | Thesis writing helper files (Q&A drafts, solution notes, execution-plan notes). | Writing Support | Active |
| `docs/DEFENSE_QA.md` | `internal/writing_support/DEFENSE_QA.md` | Defense-oriented Q&A support notes. | Writing Support | Reference |
| `docs/02_TECH/` | `internal/tech_explanations/02_TECH/` | Technology explainers and cheatsheet assets used as support material. | Tech Explanations | Reference |
| `docs/tech_used_in_thesis/` | `internal/tech_explanations/tech_used_in_thesis/` | Extended technical explainers and media assets for thesis support. | Tech Explanations | Reference |
| `docs/WHY_BOOK.md` | `internal/notes/WHY_BOOK.md` | High-level rationale narrative for repository decisions. | Notes | Reference |
| `docs/WHY_BY_FILE.md` | `internal/notes/WHY_BY_FILE.md` | File-level rationale notes for project structure. | Notes | Reference |
| `docs/WHY_BY_TECH.md` | `internal/notes/WHY_BY_TECH.md` | Technology-level rationale notes. | Notes | Reference |
| `docs/PRODUCT_REVIEW.md` | `internal/notes/PRODUCT_REVIEW.md` | Product/review discussion notes. | Notes | Reference |
| `docs/REPO_STRUCTURE_SNAPSHOT.txt` | `internal/snapshots/REPO_STRUCTURE_SNAPSHOT.txt` | Static repo-structure snapshot for audit/reference. | Snapshots | Archive |
| `docs/legacy/` | `internal/old_plans/legacy/` | Historical dated documentation (including old March plan packs). | Old Plans | Archive |
| `docs/REPO_INVENTORY.md` | `internal/workflow/REPO_INVENTORY.md` | Repository inventory used for planning/cleanup coordination. | Workflow | Reference |
| `docs/YOU_SHOULD_KNOW_BEFORE_MASTER_FILE/` | `internal/workflow/YOU_SHOULD_KNOW_BEFORE_MASTER_FILE/` | Decision ledgers and support files for thesis planning context. | Workflow | Reference |
| `docs/thesis/FROM_APRIL_15_COMPLETION_AUDIT_AND_EXECUTION_PLAN.md` | `internal/workflow/FROM_APRIL_15_COMPLETION_AUDIT_AND_EXECUTION_PLAN.md` | Dated execution audit and completion plan note. | Workflow | Archive |

## Explicitly Kept Outside Internal

- Runtime and code paths: `src/`, `scripts/`, `tests/`, `config/`, `docker/`
- Thesis source and evidence paths: `thesis/`, `docs/thesis/`
- Core docs and entrypoints: `README.md`, `run_pipeline.py`, `pyproject.toml`, `pytest.ini`, `.gitignore`
- Required workflow file remains in main repo: `docs/thesis/THESIS_WORKFLOW_MAR_JUN_2026.md`

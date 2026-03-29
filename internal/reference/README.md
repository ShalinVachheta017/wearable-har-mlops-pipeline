# Internal Workspace

This directory is the private support workspace for non-runtime materials. It is intentionally separated from the technical runtime surface of the repository.

## Final Structure

- archive/
  - archive/deprecated_support/
    - archive/deprecated_support/ai_conversations/
      - archive/deprecated_support/ai_conversations/ai_helps/
    - archive/deprecated_support/scripts_feb2026/
  - archive/docs_old/
    - archive/docs_old/markdown_old/
    - archive/docs_old/old_docs/
      - archive/docs_old/old_docs/paper_for_questions/
      - archive/docs_old/old_docs/papers_jan25/
  - archive/misc/
  - archive/misc_papers/
  - archive/old_plans/
    - archive/old_plans/legacy_march_pack/
      - archive/old_plans/legacy_march_pack/Fourth_March/
        - archive/old_plans/legacy_march_pack/Fourth_March/2026_03_04/
        - archive/old_plans/legacy_march_pack/Fourth_March/pipeline_artifact_sources/
        - archive/old_plans/legacy_march_pack/Fourth_March/tech_used_in_thesis/
        - archive/old_plans/legacy_march_pack/Fourth_March/YOU_SHOULD_KNOW_BEFORE_MASTER_FILE/
    - archive/old_plans/old_planning_docs/
  - archive/snapshots/
    - archive/snapshots/_index/
  - archive/superseded/
    - archive/superseded/prepare_training_production_conversion/
      - archive/superseded/prepare_training_production_conversion/training_cv_experiment/
- notes/
  - notes/qna/
  - notes/repo_notes/
  - notes/rough/
- papers/
  - papers/domain_adaptation/
    - papers/domain_adaptation/domain_adaptation_tta/
  - papers/har_wearables/
    - papers/har_wearables/har_models/
  - papers/mental_health/
    - papers/mental_health/misc/
  - papers/mlops/
    - papers/mlops/mlops_reproducibility/
  - papers/monitoring_drift/
    - papers/monitoring_drift/drift_detection/
    - papers/monitoring_drift/evaluation_metrics/
  - papers/uncategorized/
    - papers/uncategorized/new_papers/
    - papers/uncategorized/papers_needs_to_read/
    - papers/uncategorized/research_papers_current/
      - papers/uncategorized/research_papers_current/76 papers/
    - papers/uncategorized/research_papers_legacy/
      - papers/uncategorized/research_papers_legacy/76 papers/
- snapshots/
  - snapshots/repo_structure/
- tech_explanations/
  - tech_explanations/deployment/
    - tech_explanations/deployment/cheat_sheets/
    - tech_explanations/deployment/docker_assets/
    - tech_explanations/deployment/docker_visuals/
  - tech_explanations/mlops/
  - tech_explanations/monitoring/
- workflow/
  - workflow/audits/
  - workflow/planning/
    - workflow/planning/you_should_know_before_master_file/
- writing_support/
  - writing_support/chapter_support/
  - writing_support/defense/
  - writing_support/evidence_notes/

## Folder Intent

- workflow: active planning, inventory, and audit coordination files.
- writing_support: defense and chapter-adjacent writing support notes.
- tech_explanations: reference explainers and supporting technical media.
- notes: qna, rationale, and rough thinking documents.
- papers: literature collections grouped by thesis-relevant themes.
- snapshots: structural snapshots and export-style references.
- archive: inactive or superseded materials kept for traceability.

## Handling Rules

- Keep runtime project files out of internal.
- Prefer move and archive over delete.
- Keep naming lowercase with underscores when practical.
- When uncertain, place material in archive/superseded rather than deleting.

# Draw.io Figure Rebuild Plan

This plan standardizes how to rebuild all thesis figures manually in draw.io (diagrams.net) so they are consistent, auditable, and thesis-ready.

## Goal

- Rebuild all thesis journey figures with one visual style.
- Keep editable source files (.drawio) and exported deliverables (.svg/.png).
- Ensure each figure is traceable to data or chapter evidence.

## Folder convention

- Editable sources: `thesis/figures/thesis_journey/src_drawio/`
- Final SVG exports: `thesis/figures/thesis_journey/`
- Optional PNG exports: `thesis/figures/thesis_journey/png/`

## Style standard (apply to all figures)

- Canvas: 16:9 default artboard for process diagrams, 4:3 for dense charts.
- Font: Source Sans Pro or Arial (pick one and keep consistent).
- Heading size: 20; body size: 13; footnote size: 11.
- Primary color: #1F4E79
- Secondary color: #2A9D8F
- Accent/warning color: #E76F51
- Neutral: #6B7280
- Line width: 1.5 px; connector arrows: classic filled.
- Border radius for blocks: 6.

## Export standard

- Preferred thesis insertion format: SVG.
- Export scale: 2x for PNG fallback.
- Filename pattern: `fig_XX_short_name.svg`
- Keep text as text (do not flatten) when possible.

## Rebuild checklist by figure

1. `fig_01_journey_timeline.svg`
- Type: Timeline
- Data source: `THESIS_JOURNEY_tillapril.md`
- Checkpoints: date labels, phase bands, milestone markers

2. `fig_02_document_layers.svg`
- Type: Layered concept diagram
- Data source: thesis memo structure
- Checkpoints: 3 layers, boundary notes, usage guidance

3. `fig_03_scope_map.svg`
- Type: Scope map
- Data source: chapter scope statements
- Checkpoints: in-scope vs out-of-scope visual separation

4. `fig_04_stage_evolution.svg`
- Type: Comparative pipeline evolution
- Data source: architecture chapter notes
- Checkpoints: historical vs defended vs runtime lane

5. `fig_05_core_vs_conditional_pipeline.svg`
- Type: Branching architecture flow
- Data source: runtime stage design
- Checkpoints: stages 1-7 core, stages 8-10 conditional branch

6. `fig_06_data_pipeline.svg`
- Type: Data preprocessing flow
- Data source: preprocessing section and config
- Checkpoints: validation, conversion, resample, normalize, window

7. `fig_07_ablation_config_comparison.svg`
- Type: Comparative bar chart
- Data source: ablation table values
- Checkpoints: A/B/C/D consistency, axis labels, legend

8. `fig_08_trigger_policy_comparison.svg`
- Type: Multi-metric policy chart
- Data source: trigger policy evaluation table
- Checkpoints: precision/F1/FAR/recall clearly separated

9. `fig_09_actual_vs_synthetic.svg`
- Type: Grouped comparison chart
- Data source: actual vs synthetic metrics
- Checkpoints: metric normalization and labeling

10. `fig_10_old_vs_new_model_comparison.svg`
- Type: Side-by-side comparison
- Data source: old vs new same-input results
- Checkpoints: confidence, uncertain rate, class spread

11. `fig_11_challenges_resolutions_matrix.svg`
- Type: Matrix
- Data source: challenge-resolution log
- Checkpoints: category rows and resolved actions

12. `fig_12_thesis_readiness_dashboard.svg` (internal)
- Type: Dashboard panel
- Data source: readiness notes
- Checkpoints: progress bars and status flags

13. `fig_13_risk_matrix.svg` (internal)
- Type: Risk matrix
- Data source: risk register
- Checkpoints: likelihood-impact placement and legend

14. `fig_14_evidence_to_chapter_map.svg` (internal)
- Type: Mapping graph
- Data source: evidence map and chapter plan
- Checkpoints: one-to-many link clarity, no crossing clutter

## Quality gate before commit

- Label readability at 100% zoom.
- Visual consistency with style standard.
- Caption matches figure semantics.
- Exported filename exactly matches figure index.
- Source `.drawio` saved under `src_drawio/`.

## Practical rollout order

1. Rebuild thesis-body-critical figures first: 04, 05, 07, 08, 09, 10.
2. Rebuild architecture/support figures: 01, 02, 03, 06, 11.
3. Rebuild internal-only figures: 12, 13, 14.

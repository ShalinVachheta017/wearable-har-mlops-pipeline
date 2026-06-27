# Figure Index

This index lists the thesis journey figure pack, suggested insertion points, and paste-ready captions.

| Filename | Title | Suggested insertion point | Internal only |
| --- | --- | --- | --- |
| `fig_01_journey_timeline.svg` | Journey timeline from scaffold to writing convergence | Section 4.1 Timeline Overview | No |
| `fig_02_document_layers.svg` | Document layers in the thesis journey memo | Section 1.5 Document Layers | No |
| `fig_03_scope_map.svg` | In-scope versus out-of-scope thesis boundary | Section 2.3 In Scope vs Out of Scope | No |
| `fig_04_stage_evolution.svg` | Stage evolution from broad design to defended thesis framing | Section 3.2 Current Runtime Shape vs Historical Design Shape | No |
| `fig_05_core_vs_conditional_pipeline.svg` | Core runtime versus governed mutation branch | Section 5.5 Why Stage-Based Orchestration or Section 5.6 Why 7 Core + 3 Conditional Is Better Than a Flat 10 or 14 | No |
| `fig_06_data_pipeline.svg` | Train-serve consistent preprocessing pipeline | Section 6.2 Preprocessing Path | No |
| `fig_07_ablation_config_comparison.svg` | A/B/C/D preprocessing ablation comparison | Section 7.2 Preprocessing Ablation A/B/C/D | No |
| `fig_08_trigger_policy_comparison.svg` | Trigger policy comparison | Section 7.3 Trigger Policy Evaluation | No |
| `fig_09_actual_vs_synthetic.svg` | Actual versus synthetic dataset comparison | Section 7.4 Actual vs Synthetic Comparison | No |
| `fig_10_old_vs_new_model_comparison.svg` | Same-input old versus new model comparison | Section 7.5 Same-Input Old-vs-New Model Comparison | No |
| `fig_11_challenges_resolutions_matrix.svg` | Challenges and resolutions matrix | Section 8 Challenges and Resolutions Log | No |
| `fig_12_thesis_readiness_dashboard.svg` | Internal readiness snapshot | Section 11.1 Practical Internal Completion Estimate by Thesis Component | Yes |
| `fig_13_risk_matrix.svg` | Internal risk exposure map | Section 11.5 Internal Risk Register | Yes |
| `fig_14_evidence_to_chapter_map.svg` | Evidence-to-chapter writing map | Section 11.6 Immediate Next Actions or near Section 3.3 Current Thesis Writing Index | Yes |

## Detailed entries

### Fig. 1 - Journey timeline from scaffold to writing convergence
- Filename: `fig_01_journey_timeline.svg`
- Suggested insertion point: Section 4.1 Timeline Overview
- Why it helps: Breaks up the longest section in the memo and gives the reader a fast chronological anchor before the detailed phase-by-phase narrative.
- Caption: Timeline of the thesis journey from the first repository scaffold on 2025-10-23 to the writing push on 2026-04-18. The milestones show the shift from setup and sensor debugging toward governance hardening, retraining evidence, and final writing convergence.
- Internal only: No

### Fig. 2 - Document layers in the thesis journey memo
- Filename: `fig_02_document_layers.svg`
- Suggested insertion point: Section 1.5 Document Layers
- Why it helps: Helps the reader distinguish between thesis-usable evidence, project-history material, and internal planning content.
- Caption: Conceptual view of the memo's three layers: thesis facts, development history, and internal readiness. The figure clarifies that the support document mixes different text types and should not be pasted directly into thesis body prose.
- Internal only: No

### Fig. 3 - In-scope versus out-of-scope thesis boundary
- Filename: `fig_03_scope_map.svg`
- Suggested insertion point: Section 2.3 In Scope vs Out of Scope
- Why it helps: Makes the defended scope visible at a glance and reduces the risk that a reader over-reads the contribution.
- Caption: Scope map contrasting the defended thesis boundary with explicitly excluded or reduced ambitions. It highlights the thesis as an offline-first, single-machine, governed HAR lifecycle rather than a full cloud or clinical deployment.
- Internal only: No

### Fig. 4 - Stage evolution from broad design to defended thesis framing
- Filename: `fig_04_stage_evolution.svg`
- Suggested insertion point: Section 3.2 Current Runtime Shape vs Historical Design Shape
- Why it helps: This is one of the key conceptual clarifiers in the memo and helps reconcile differing stage counts across older notes, the runtime, and the thesis framing.
- Caption: Comparison of the historical 14-stage design, the thesis presentation target of seven core plus three conditional stages, and the current 11-stage runtime that still exposes calibration. The figure shows how the project moved from broad ambition to a tighter and more defensible thesis scope.
- Internal only: No

### Fig. 5 - Core runtime versus governed mutation branch
- Filename: `fig_05_core_vs_conditional_pipeline.svg`
- Suggested insertion point: Section 5.5 Why Stage-Based Orchestration or Section 5.6 Why 7 Core + 3 Conditional Is Better Than a Flat 10 or 14
- Why it helps: This is the cleanest visual statement of the thesis identity: observation and assessment happen routinely, while mutation happens only under policy control.
- Caption: Stage-based architecture showing the seven-stage operational core and the conditional retraining branch for stages 8-10, with calibration shown separately as optional. The visual makes explicit that model mutation is governed rather than automatic.
- Internal only: No

### Fig. 6 - Train-serve consistent preprocessing pipeline
- Filename: `fig_06_data_pipeline.svg`
- Suggested insertion point: Section 6.2 Preprocessing Path
- Why it helps: Provides a compact visual explanation of the production preprocessing chain and reduces the need for the reader to reconstruct it from prose alone.
- Caption: Compact data-flow view from raw wrist IMU files through validation, unit conversion, normalization, resampling, and windowing to the saved `production_X.npy` tensor. The figure explains why preprocessing consistency is a thesis-level engineering concern rather than an implementation detail.
- Internal only: No

### Fig. 7 - A/B/C/D preprocessing ablation comparison
- Filename: `fig_07_ablation_config_comparison.svg`
- Suggested insertion point: Section 7.2 Preprocessing Ablation A/B/C/D
- Why it helps: Transforms one of the strongest numerical findings into a fast visual argument about why the chosen configuration is defensible.
- Caption: Two aligned bar charts comparing the four preprocessing configurations on mean unique classes predicted and mean hand_tapping share. Config D gives the strongest class diversity, while Config C shows that gravity removal alone worsened collapse in this setup.
- Internal only: No

### Fig. 8 - Trigger policy comparison
- Filename: `fig_08_trigger_policy_comparison.svg`
- Suggested insertion point: Section 7.3 Trigger Policy Evaluation
- Why it helps: Makes the governance trade-off visible without forcing the reader to scan a dense numerical table.
- Caption: Coordinated policy comparison using precision, tradeoff F1, false alarm rate, and episode recall from the memo's trigger-policy table. The figure shows why `two_of_three` is the strongest available balance among the tested policies.
- Internal only: No

### Fig. 9 - Actual versus synthetic dataset comparison
- Filename: `fig_09_actual_vs_synthetic.svg`
- Suggested insertion point: Section 7.4 Actual vs Synthetic Comparison
- Why it helps: Gives a compact visual explanation of the synthetic-data result without collapsing very different metrics into a less readable radar chart.
- Caption: Comparison of actual labeled data with two synthetic datasets across accuracy, macro F1, mean confidence, uncertain rate, and drift. The pattern shows that degraded realism is associated with worse performance and higher uncertainty.
- Internal only: No

### Fig. 10 - Same-input old versus new model comparison
- Filename: `fig_10_old_vs_new_model_comparison.svg`
- Suggested insertion point: Section 7.5 Same-Input Old-vs-New Model Comparison
- Why it helps: This is one of the cleanest pieces of thesis evidence and should stand out as a major visual result.
- Caption: Flagship same-input comparison between the historical pretrained model and the retrained model on the same raw pair. The old model is more overconfident and collapses into a dominant class, whereas the retrained model is less overconfident and behaviorally broader.
- Internal only: No

### Fig. 11 - Challenges and resolutions matrix
- Filename: `fig_11_challenges_resolutions_matrix.svg`
- Suggested insertion point: Section 8 Challenges and Resolutions Log
- Why it helps: Visually reinforces the engineering struggle-and-correction story that makes the memo more credible.
- Caption: Compact engineering map grouping the challenge log into train-serve mismatch, orchestration bugs, model collapse and adaptation, environment drift, and scope control. The figure underscores that the thesis preserves negative evidence and correction work rather than presenting only final positive claims.
- Internal only: No
- Note: Theme grouping is editorial; individual issue and resolution statements come directly from the memo.

### Fig. 12 - Internal readiness snapshot
- Filename: `fig_12_thesis_readiness_dashboard.svg`
- Suggested insertion point: Section 11.1 Practical Internal Completion Estimate by Thesis Component
- Why it helps: Useful in the support memo and for supervisor updates because it compresses the planning state into one view.
- Caption: Internal progress view across code, experiments, writing, documentation, and defense preparation using the memo's readiness estimates. This is a planning figure for supervision and execution, not a thesis-evidence figure.
- Internal only: Yes

### Fig. 13 - Internal risk exposure map
- Filename: `fig_13_risk_matrix.svg`
- Suggested insertion point: Section 11.5 Internal Risk Register
- Why it helps: Useful for supervision, appendix planning, and defense preparation because it makes completion risks visible without burying them in prose.
- Caption: Risk map based on the memo's internal risk register, grouping risks by stated current level and affected area. The memo does not provide separate numeric impact and probability scores, so the figure stays at the level explicitly supported by the source text.
- Internal only: Yes
- Note: Separate impact/probability scores are not specified in the memo.

### Fig. 14 - Evidence-to-chapter writing map
- Filename: `fig_14_evidence_to_chapter_map.svg`
- Suggested insertion point: Section 11.6 Immediate Next Actions or near Section 3.3 Current Thesis Writing Index
- Why it helps: Helps convert the memo into a chapter-writing plan and is especially useful for supervisor discussion or internal execution.
- Caption: Writing-execution diagram linking the strongest evidence families to their target thesis chapters. The map turns the memo into a practical drafting aid by showing where architecture, experiments, monitoring, and limitations should land in the manuscript.
- Internal only: Yes
- Note: This is an editorial mapping aid derived from the chapter structure and requested chapter mapping.

## Recommendation summary

### Six essential figures for the thesis-support memo
- `fig_01_journey_timeline.svg` - Journey timeline from scaffold to writing convergence
- `fig_04_stage_evolution.svg` - Stage evolution from broad design to defended thesis framing
- `fig_05_core_vs_conditional_pipeline.svg` - Core runtime versus governed mutation branch
- `fig_07_ablation_config_comparison.svg` - A/B/C/D preprocessing ablation comparison
- `fig_10_old_vs_new_model_comparison.svg` - Same-input old versus new model comparison
- `fig_14_evidence_to_chapter_map.svg` - Evidence-to-chapter writing map

### Four figures best suited to the thesis body
- `fig_04_stage_evolution.svg` - Stage evolution from broad design to defended thesis framing
- `fig_05_core_vs_conditional_pipeline.svg` - Core runtime versus governed mutation branch
- `fig_07_ablation_config_comparison.svg` - A/B/C/D preprocessing ablation comparison
- `fig_10_old_vs_new_model_comparison.svg` - Same-input old versus new model comparison

### Internal-only figures
- `fig_12_thesis_readiness_dashboard.svg` - Internal readiness snapshot
- `fig_13_risk_matrix.svg` - Internal risk exposure map
- `fig_14_evidence_to_chapter_map.svg` - Evidence-to-chapter writing map

### Figures with partially inferred structure or incomplete source fields
- `fig_11_challenges_resolutions_matrix.svg` - Theme grouping is editorial. The underlying challenge and resolution statements are taken directly from the memo.
- `fig_13_risk_matrix.svg` - The memo specifies current risk level but does not provide separate numeric impact and probability scores.
- `fig_14_evidence_to_chapter_map.svg` - The mapping is an editorial writing aid derived from the memo's chapter structure and the requested chapter-to-evidence mapping.
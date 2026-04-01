# Main Analysis Workspace Guide

This folder is the working area for analysis notebooks and generated artifacts used in reporting and thesis writing.

## 1) What is in this folder

- Core audit notebook: [main/data_intelligence_audit.ipynb](data_intelligence_audit.ipynb)
- Dataset-comparison package: [main/data_comparison](data_comparison)

## 2) Analysis files inventory

### A) Notebooks and scripts

| File | Purpose | Use in report/thesis |
|---|---|---|
| [main/data_comparison/data_fit_analysis.ipynb](data_comparison/data_fit_analysis.ipynb) | Main deep-dive data-fit analysis notebook | Methods and results narrative (recommended: Chapters 4, 7, 8) |
| [main/data_comparison/dataset_comparison_analysis.ipynb](data_comparison/dataset_comparison_analysis.ipynb) | Cross-dataset descriptive comparison | Dataset overview and baseline comparison figures (recommended: Chapters 4 and 7) |
| [main/data_intelligence_audit.ipynb](data_intelligence_audit.ipynb) | Pipeline-level audit and diagnostics | MLOps validation and process reliability discussion (recommended: Chapters 5 and 6) |
| [main/data_comparison/data_fit_analysis_helper.py](data_comparison/data_fit_analysis_helper.py) | Reproducible artifact generator | Reproducibility section and appendix |
| [main/data_comparison/_write_notebook.py](data_comparison/_write_notebook.py) | Notebook writing/helper utility | Technical appendix only (optional) |

### B) Numeric outputs (tables/metrics)

| File | What it contains | Where to cite |
|---|---|---|
| [main/data_comparison/data_fit_analysis_summary.json](data_comparison/data_fit_analysis_summary.json) | Final summary flags and recommendation signals | Executive summary, findings section |
| [main/data_comparison/data_fit_transform_scores.csv](data_comparison/data_fit_transform_scores.csv) | Ranking of candidate transformations | Method comparison table |
| [main/data_comparison/data_fit_harmonized_dataset_metrics.csv](data_comparison/data_fit_harmonized_dataset_metrics.csv) | Same-unit dataset-level metrics | Dataset harmonization subsection |
| [main/data_comparison/data_fit_harmonized_feature_metrics.csv](data_comparison/data_fit_harmonized_feature_metrics.csv) | Feature-level mismatch metrics | Feature diagnostics subsection |
| [main/data_comparison/data_fit_affine_calibration_parameters.csv](data_comparison/data_fit_affine_calibration_parameters.csv) | Affine calibration slopes/intercepts | Calibration method details |
| [main/data_comparison/data_fit_barriers_and_actions.csv](data_comparison/data_fit_barriers_and_actions.csv) | Gap-to-action mapping | Discussion and deployment recommendations |
| [main/data_comparison/data_fit_chapter_defense_mapping.csv](data_comparison/data_fit_chapter_defense_mapping.csv) | Chapter and defense mapping | Thesis planning and defense deck structure |
| [main/data_comparison/data_fit_citation_based_solution_comparison.csv](data_comparison/data_fit_citation_based_solution_comparison.csv) | Citation-backed solution matrix | Related work and recommendation justification |

### C) Figures (ready for report/thesis)

| File | Figure meaning | Suggested placement |
|---|---|---|
| [main/data_comparison/data_fit_chart_scale.png](data_comparison/data_fit_chart_scale.png) | Unit/scale mismatch visualization | Chapter 4 (data understanding) |
| [main/data_comparison/data_fit_chart_quantiles.png](data_comparison/data_fit_chart_quantiles.png) | Quantile profile alignment | Chapter 7 (experimental evidence) |
| [main/data_comparison/data_fit_chart_transform_scores.png](data_comparison/data_fit_chart_transform_scores.png) | Transformation performance comparison | Chapter 7 and conclusion summary |

## 3) How to regenerate analysis outputs

Run from repository root:

```powershell
C:/Users/shali/anaconda3/envs/thesis-mlops/python.exe main/data_comparison/data_fit_analysis_helper.py --output-dir main/data_comparison
```

Then open and run:

- [main/data_comparison/data_fit_analysis.ipynb](data_comparison/data_fit_analysis.ipynb)
- [main/data_comparison/dataset_comparison_analysis.ipynb](data_comparison/dataset_comparison_analysis.ipynb)
- [main/data_intelligence_audit.ipynb](data_intelligence_audit.ipynb)

## 4) How to use these files in your report and thesis

Use this practical flow:

1. Start with dataset context using [main/data_comparison/dataset_comparison_analysis.ipynb](data_comparison/dataset_comparison_analysis.ipynb).
2. Present mismatch diagnosis and transformation strategy from [main/data_comparison/data_fit_analysis.ipynb](data_comparison/data_fit_analysis.ipynb).
3. Support claims with numeric evidence from:
   - [main/data_comparison/data_fit_harmonized_dataset_metrics.csv](data_comparison/data_fit_harmonized_dataset_metrics.csv)
   - [main/data_comparison/data_fit_harmonized_feature_metrics.csv](data_comparison/data_fit_harmonized_feature_metrics.csv)
   - [main/data_comparison/data_fit_transform_scores.csv](data_comparison/data_fit_transform_scores.csv)
4. Add decision guidance using:
   - [main/data_comparison/data_fit_barriers_and_actions.csv](data_comparison/data_fit_barriers_and_actions.csv)
   - [main/data_comparison/data_fit_citation_based_solution_comparison.csv](data_comparison/data_fit_citation_based_solution_comparison.csv)
5. Map results into thesis structure via [main/data_comparison/data_fit_chapter_defense_mapping.csv](data_comparison/data_fit_chapter_defense_mapping.csv).

## 5) Suggested chapter mapping

- Chapter 4 (Data): scale mismatch, harmonization metrics, quantile behavior.
- Chapter 5 (Implementation): helper script workflow and reproducibility process.
- Chapter 6 (Monitoring/Drift): audit notebook findings and operational checks.
- Chapter 7 (Experiments): transform-score comparisons and key charts.
- Chapter 8 (Conclusion): final recommendation and barriers/actions summary.

## 6) Quick citation-ready claim examples

- "Production and training data required unit harmonization before valid comparison."
- "Residual mismatch after unit conversion was primarily feature-level variance/domain shift, not only raw scaling."
- "A ranked transform comparison enabled selection of safer inference-time alignment options for deployment."


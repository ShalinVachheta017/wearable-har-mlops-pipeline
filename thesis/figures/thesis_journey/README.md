# Thesis Journey Figure Pack

This folder contains a reproducible figure pack for the support document:

`Thesis Journey and Evidence Reconstruction up to 2026-04-18`

All figures are generated from the values and scope statements explicitly present in the memo and the user specification for this figure pack. The default output format is SVG to keep the assets vector-friendly for thesis PDFs and print workflows.

## Contents

- `generate_figures.py`
- `fig_01_journey_timeline.svg`
- `fig_02_document_layers.svg`
- `fig_03_scope_map.svg`
- `fig_04_stage_evolution.svg`
- `fig_05_core_vs_conditional_pipeline.svg`
- `fig_06_data_pipeline.svg`
- `fig_07_ablation_config_comparison.svg`
- `fig_08_trigger_policy_comparison.svg`
- `fig_09_actual_vs_synthetic.svg`
- `fig_10_old_vs_new_model_comparison.svg`
- `fig_11_challenges_resolutions_matrix.svg`
- `fig_12_thesis_readiness_dashboard.svg`
- `fig_13_risk_matrix.svg`
- `fig_14_evidence_to_chapter_map.svg`
- `FIGURE_INDEX.md`
- `CAPTIONS_AND_INSERTION_GUIDE.md`

## Dependencies

The generator uses only standard Python plus:

- `matplotlib`
- `numpy`

These are already listed in the project metadata.

## How To Run

From the repository root:

```powershell
python thesis/figures/thesis_journey/generate_figures.py
```

If your default `python` does not have the plotting dependencies installed, run the script with any interpreter that has `matplotlib` and `numpy` available.

Tested command on this machine:

```powershell
& 'C:\Program Files\Python311\python.exe' thesis/figures/thesis_journey/generate_figures.py
```

To also export PNG fallback files next to the SVGs:

```powershell
python thesis/figures/thesis_journey/generate_figures.py --with-png
```

## Notes

- The figure pack is intentionally thesis-safe and conservative in style.
- Figures 12-14 are primarily for the support memo, supervision, and execution planning.
- Where the memo did not provide a fully specified numeric field, the generator avoids inventing one and adds a note in the index files instead.

# Thesis LaTeX Guide (Step by Step)

This is the practical operating guide for writing and compiling the thesis.

## 1. Start Here

Main thesis entry file:

- main.tex

Chapter files:

- chapters/ch1_introduction.tex
- chapters/ch2_background_related_work.tex
- chapters/ch3_offline_mlops_architecture.tex
- chapters/ch4_data_model_development.tex
- chapters/ch5_pipeline_implementation.tex
- chapters/ch6_monitoring_drift_retraining.tex
- chapters/ch7_experiments_evaluation.tex
- chapters/ch8_discussion_conclusion.tex

Bibliography file:

- references.bib

Generated output:

- main.pdf

Chapter-process synchronization index:

- CHAPTER_PROCESS_INDEX.md

VS Code shortcuts quick guide:

- LATEX_VSCODE_SHORTCUTS.md

## 2. Daily Writing Workflow

1. Open main.tex so you keep the full document structure visible.
2. Edit the target chapter file in chapters/.
3. Compile from the thesis folder (not from project root).
4. Check main.pdf.
5. Repeat.

## 3. Compile Commands (Windows PowerShell)

From repository root:

Set-Location "D:\study apply\ML Ops\MasterArbeit_MLops\thesis"

Recommended one-command helper (new):

./build_thesis.ps1

Useful options:

./build_thesis.ps1 -Quick
./build_thesis.ps1 -Clean
./build_thesis.ps1 -OpenPdf

Or from repository root without changing directory:

./thesis/build_thesis.ps1

Full build sequence (safe for citations):

pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

If latexmk is installed, one-command build:

latexmk -pdf -interaction=nonstopmode -synctex=1 main.tex

## 4. Fast Chapter-Only Editing Pattern

1. Edit one chapter file under chapters/.
2. Run:

pdflatex main.tex

1. If you changed citations, run full sequence again:

pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

## 5. How to Add Citations

1. Add BibTeX entry in references.bib.
2. Cite in chapter text with: \cite{your_key}
3. Rebuild using full sequence:

pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

## 6. How to Add a New Chapter

1. Create a new file in chapters/ (for example chapters/ch9_future_extensions.tex).
2. Add include line in main.tex in the desired order:

\include{chapters/ch9_future_extensions}

1. Compile and verify in table of contents.

## 7. Figures and Tables

Recommended placement:

- figures/ for images
- tables/ for table assets

Typical include usage in chapter files:

\includegraphics[width=0.9\textwidth]{figures/your_figure_name}

## 8. Clean Build Artifacts

If the build gets inconsistent, clean aux files and rebuild.

Preferred:

./build_thesis.ps1 -Clean

Quick clean command:

Remove-Item main.aux, main.bbl, main.blg, main.log, main.toc, main.synctex.gz -ErrorAction SilentlyContinue

Then run full build again.

If latexmk is installed:

latexmk -c
latexmk -pdf -interaction=nonstopmode -synctex=1 main.tex

## 9. Common Issues and Fixes

Undefined citation warning:

- Run bibtex main and then pdflatex twice.

Reference/cross-reference not updated:

- Run pdflatex one more time.

Missing chapter content:

- Ensure chapter file is included in main.tex with \include{...}.

Cannot find image file:

- Check path relative to thesis folder and verify extension.

## 10. Thesis-Specific Note for Chapter 2.2

Working note file for related-work mapping:

- chapters/ch2_2_related_work_paper_map.md

This markdown note is for planning support and is not directly included by LaTeX. Keep chapter text in chapters/ch2_background_related_work.tex.

## 11. Quick Command Block

Set-Location "D:\study apply\ML Ops\MasterArbeit_MLops\thesis"
./build_thesis.ps1

If citations are still unresolved, run:
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

## 12. Latest Update (2026-04-19)

Today's thesis writing wave produced two evidence documents at repository root:

- THESIS_WRITING_AUDIT.md
- THESIS_WRITING_POST_FIX_REPORT.md

Current snapshot from latest local checks:

- references.bib entries: 47
- main.pdf pages (latest main.log): 107
- updated chapter files in this wave: ch1, ch3, ch4, ch5, ch6, ch7, ch8

Dashboard sync:

- handbook dashboard source updated in `thesis/handbook-dashboard/src/App.jsx`
- dashboard handbook guide updated in `thesis/handbook-dashboard/README.md`

If you continue writing in the next session, start with Chapter 2 synthesis strengthening, then rerun a full build and citation pass.

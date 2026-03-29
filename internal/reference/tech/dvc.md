# DVC

## What it is

DVC (Data Version Control) tracks large data/model artifacts outside Git while keeping small metadata files in Git.

## Why it is used in this thesis

The thesis pipeline needs reproducible data/model inputs without committing large binary datasets directly into Git history.

## Repository locations

- `.dvc/config`
- `data/raw.dvc`
- `data/processed.dvc`
- `data/prepared.dvc`
- `models/pretrained.dvc`

## Role in this project

- Core:
  - Versioning of raw/processed/prepared data and pretrained model artifact pointer.
- Optional:
  - Local runs can still execute if required files are already present in workspace.
- Future work:
  - Extend DVC coverage to additional large generated model artifacts when needed.

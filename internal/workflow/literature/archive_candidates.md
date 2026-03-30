# Archive-Candidate Rules for `internal/papers/triage`

This file defines which triage files should stay active and which should be treated as archive-candidates.

## Current Pattern Snapshot

- Total files in triage: `417`
- Duplicate-suffix pattern (`_2`, `_3`): `156`
- Explicit archive-prefix pattern (`archive_*`): `82`

## Archive-Candidate Heuristics

Mark as `archive-candidate` when any of the following is true:

1. Filename begins with `archive_`.
2. Filename ends with duplicate marker `_2` or `_3` and the base paper without suffix exists.
3. File is a scan/format duplicate and does not improve readability or metadata quality.
4. File is not mapped to any chapter in `chapter_buckets.md`.

Keep as `candidate` when:

1. It is the only available version of that paper title.
2. It contains better OCR/readability than the base duplicate.
3. It is directly mapped to a chapter section and likely to be cited.

## Sample Archive-Candidate Items

- `A Close Look into Human Activity Recognition Models using Deep Learning_2.pdf`
- `A Close Look into Human Activity Recognition Models using Deep Learning_3.pdf`
- `A DIFFUSION MODEL FOR MULTIVARIATE_2.pdf`
- `A DIFFUSION MODEL FOR MULTIVARIATE_3.pdf`
- `A Multi-Task Deep Learning Approach for Sensor-based Human Activity Recognition and Segmentation_2.pdf`
- `A Multi-Task Deep Learning Approach for Sensor-based Human Activity Recognition and Segmentation_3.pdf`
- `A Survey on Wearable Sensors for Mental Health Monitoring_2.pdf`
- `ADAM-sense_Anxietydisplayingactivitiesrecognitionby_2.pdf`
- `archive_1-s2.0-S0020025521003911-main.pdf`
- `archive_MLOps Lifecycle Framework and LLMOps Integration – Repository Analysis.pdf`

## Workflow

1. Use `chapter_buckets.md` to determine chapter relevance first.
2. For duplicates, keep one best-quality version active and mark others as archive-candidate.
3. Do not delete binaries in this pass; apply non-destructive status via manifests.
4. If you later want physical folder cleanup, move archive-candidates in one dedicated migration commit.

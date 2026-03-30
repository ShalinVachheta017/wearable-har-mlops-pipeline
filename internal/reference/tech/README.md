<!-- markdownlint-disable MD060 -->

# Technology References (Canonical Set)

This folder is the canonical, defense-friendly technology reference set for the thesis.

## Files

- `docker.md`
- `dvc.md`
- `mlflow.md`
- `fastapi.md`
- `ci_cd.md`
- `monitoring.md`
- `model_registry.md`
- `tensorflow_keras.md`
- `deployment.md`
- `scalability.md`
- `reproducibility.md`

## Folder Policy

All tech reference assets stay in this same folder: `internal/reference/tech/`.

- Keep all tech markdown files here.
- Keep related static assets here too (for example PNG/JPG/SVG diagrams) when added.
- Do not split core tech docs across other folders.

## Scope Rule

Each tech markdown now follows one common structure:

1. General concept.
2. General pseudocode + explanation (technology pattern).
3. Thesis-centric pseudocode + explanation (exact implementation path in this repo).
4. Repository code map.
5. What is used here.
6. What exists but is not used yet.
7. Graph/flow view for fast defense explanation.
8. Role in thesis (core/optional/future).

This ensures every document is both conceptually complete and implementation-accurate.

## Reading Order (Recommended)

1. `docker.md`
2. `ci_cd.md`
3. `deployment.md`
4. `fastapi.md`
5. `monitoring.md`
6. `scalability.md`
7. `dvc.md`
8. `mlflow.md`
9. `tensorflow_keras.md`
10. `model_registry.md`
11. `reproducibility.md`

## Cross-Cutting Thesis Topics

The following thesis topics are intentionally covered across multiple tech documents.

### Deployment

- Primary doc: `deployment.md`
- Supporting docs: `docker.md`, `ci_cd.md`, `fastapi.md`, `model_registry.md`
- Focus: container packaging, release pipeline, runtime service exposure, model promotion/rollback.

### Scalability

- Primary doc: `scalability.md`
- Supporting docs: `fastapi.md`, `docker.md`, `monitoring.md`, `ci_cd.md`
- Focus: API serving path, container-based scale-out readiness, observability for load behavior, automation guardrails for frequent changes.

### Reproducibility

- Primary doc: `reproducibility.md`
- Supporting docs: `dvc.md`, `mlflow.md`, `tensorflow_keras.md`, `ci_cd.md`
- Focus: data/model version control, experiment lineage, deterministic training/inference stack, repeatable validation in automation.

## Thesis Chapter Mapping (Chapter -> Exact Doc Sections)

Use this table to map thesis chapters directly to exact section titles in this folder.

| Thesis chapter/theme | Exact doc sections to cite |
|---|---|
| Chapter: System architecture and stack | `docker.md -> 5. Container Architecture in This Project`; `ci_cd.md -> 5. High-Level Automation Topology`; `fastapi.md -> 5. Endpoint and Runtime Map`; `monitoring.md -> 9. Monitoring Governance Graph` |
| Chapter: Data and experiment management | `dvc.md -> 5. Current DVC Configuration`; `dvc.md -> 6. Tracked Artifacts in This Repository`; `mlflow.md -> 5. Configuration Snapshot in This Repository`; `mlflow.md -> 8. Flow Graph` |
| Chapter: Model implementation and serving | `tensorflow_keras.md -> 4. Architecture Notes in This Repository`; `tensorflow_keras.md -> 8. Model Lifecycle Graph`; `fastapi.md -> 3. Thesis-Centric Pseudocode (Exact Repository Flow)` |
| Chapter: Deployment engineering | `deployment.md -> 5. Release Deployment Flow in This Repository`; `deployment.md -> 6. Runtime Deployment Topology`; `deployment.md -> 8. Rollback and Recovery Path`; `ci_cd.md -> 7. CD Workflow (\`cd.yml\`) in Detail` |
| Chapter: Scalability engineering | `scalability.md -> 4. Scalability Dimensions in This Repository`; `scalability.md -> 5. Inference Path Scalability`; `scalability.md -> 9. Observability for Scale Decisions`; `docker.md -> 8. Docker Compose Service Map` |
| Chapter: Monitoring and trigger governance | `monitoring.md -> 3. Thesis-Centric Pseudocode (Exact Repository Flow)`; `monitoring.md -> 6. Signals and Threshold Sources`; `monitoring.md -> 9. Monitoring Governance Graph`; `model_registry.md -> 3. Thesis-Centric Pseudocode (Exact Repository Flow)` |
| Chapter: Reproducibility and traceability | `reproducibility.md -> 3. Reproducibility Stack in This Thesis`; `reproducibility.md -> 4. Data and Model Artifact Reproducibility (DVC)`; `reproducibility.md -> 5. Experiment Reproducibility (MLflow)`; `reproducibility.md -> 10. Reproducibility Evidence Checklist` |
| Chapter: Limitations and future work | `deployment.md -> 10. Deployment Capabilities Not Used Yet`; `scalability.md -> 11. Scalability Capabilities Not Used Yet`; `reproducibility.md -> 12. Reproducibility Capabilities Not Fully Used Yet`; `ci_cd.md -> 14. Current Boundaries and Future Enhancements` |

## Note on older files

Prometheus and Grafana are now canonical docs in this folder (`prometheus.md`, `grafana.md`).
Legacy supplementary/compatibility files remain in `internal/reference/` (`experiment_tracking_explained.md` plus legacy `*_explained.md` pointer files).
Moved Docker/CI-DVC figures and PDFs are under `internal/reference/tech/assets/`.

For thesis writing and defense consistency, prefer this `internal/reference/tech/` set as the source of truth.

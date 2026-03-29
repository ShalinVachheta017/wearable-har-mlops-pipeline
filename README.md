# MLOps Pipeline for Wearable HAR (Master Thesis)

This repository contains an offline-first MLOps pipeline for anxiety-related human activity recognition (HAR) from wearable IMU data.

The project focus is thesis-grade reproducibility and technical defensibility:

- reproducible data/model workflow
- explicit pipeline stages
- monitoring + trigger policy for retraining decisions
- experiment tracking and artifacts for thesis evidence

## Scope

- Domain: HAR on accelerometer + gyroscope time series
- Objective: classify anxiety-related behaviors and monitor model behavior over time
- Usage mode: batch-first pipeline with optional service/inference utilities

## Quick Start

1. Install dependencies.
2. Configure paths/parameters in [config/pipeline_config.yaml](config/pipeline_config.yaml).
3. Run the pipeline:

```bash
python run_pipeline.py
```

## Minimal Repo Map

- [run_pipeline.py](run_pipeline.py): main entrypoint
- [src/](src/): core pipeline implementation
- [scripts/](scripts/): utility and maintenance scripts
- [tests/](tests/): test suite
- [config/](config/): runtime configuration
- [docker/](docker/) and [docker-compose.yml](docker-compose.yml): container setup
- [docs/](docs/): technical and thesis support docs
- [thesis/](thesis/): thesis manuscript sources
- [internal/](internal/): non-core support, historical, and private working materials

## Thesis-Critical Docs

- Workflow plan: [docs/thesis/THESIS_WORKFLOW_MAR_JUN_2026.md](docs/thesis/THESIS_WORKFLOW_MAR_JUN_2026.md)
- Evidence tracker: [docs/thesis/THESIS_EVIDENCE.md](docs/thesis/THESIS_EVIDENCE.md)
- Experiment plan: [docs/thesis/EXPERIMENT_PLAN.md](docs/thesis/EXPERIMENT_PLAN.md)
- Defense plan: [docs/thesis/DEFENSE_PLAN.md](docs/thesis/DEFENSE_PLAN.md)
- Trigger policy explanation: [docs/TRIGGER_POLICY_EXPLANATION.md](docs/TRIGGER_POLICY_EXPLANATION.md)
- Pipeline data flow map: [docs/PIPELINE_DATA_FLOW_MAP.md](docs/PIPELINE_DATA_FLOW_MAP.md)
- Consistency decisions (thresholds, Config D, AdaBN): [docs/THESIS_CONSISTENCY_NOTES.md](docs/THESIS_CONSISTENCY_NOTES.md)

## Testing

Run a fast smoke subset:

```bash
pytest -q --maxfail=1
```

If you only need import/runtime sanity for core modules:

```bash
python -m compileall src scripts run_pipeline.py
```

## Notes

- Root is intentionally kept minimal for defense readability.
- Working notes and historical support materials are consolidated under `internal/`.

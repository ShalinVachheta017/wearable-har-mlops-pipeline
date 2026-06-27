# Docker Guide — HAR MLOps Pipeline

Two images, one compose file. The container boundary deliberately follows the
governance boundary of the thesis architecture: the frozen Stage 1–7 runtime
path and the Stage 8–10 candidate-building path get separate environments.

## Roles

| Unit | Role | Contains | Does not contain |
|---|---|---|---|
| `Dockerfile.training` | Training, retraining, and full Stage 1–7 pipeline execution | `src/`, `config/`, `run_pipeline.py`, full training dependencies | data, models (mounted volumes) |
| `Dockerfile.inference` | Lean FastAPI serving of the D1 runtime contract | `src/`, `config/`, runtime-only dependencies (`requirements-runtime.txt`) | training stack, model binaries (contract mounted read-only) |
| DVC / release bundle | Data, model, and evidence restore | datasets, D1 runtime contract, defended run | application code |
| `docker-compose.yml` | Local orchestration | service wiring (mlflow, inference, training), mounts, env vars | artifacts themselves |

## Why two images — not one, not three

- **Not one:** training and serving have different dependency sets and risk
  profiles. A single image would put the full training stack inside the
  serving environment and erase the train/serve boundary that the runtime
  contract enforces — the exact hidden-coupling pattern the thesis argues
  against.
- **Not three:** monitoring, evaluation, and the trigger policy share the
  inference runtime's dependencies. A third image would duplicate one of the
  existing environments without adding isolation.
- **Two:** the split mirrors the pipeline's two-path separation. The inference
  image serves the frozen runtime; the training image builds candidates and
  can execute the complete pipeline.

No model or data is baked into either image by default. The deployment unit is
the runtime contract folder (`models/runtime_contract/model_d1_final_20260528/`),
mounted read-only into the inference container — one source of truth on disk,
verified by `artifact_md5.json`, promotable without an image rebuild.

Image size is minimal by construction: `python:3.11-slim` base,
`tensorflow-cpu` (no GPU stack), no pip cache, `.dockerignore` excludes data
and models from the build context.

## Usage profiles

### 1. Standard (DVC available)

```powershell
git clone <repo> ; cd MasterArbeit_MLops
dvc pull
docker compose up -d            # mlflow + inference API
```

### 2. Without DVC (release artifact bundle)

Unzip the release bundle (data, runtime contract, defended run) over the
repository root, then run compose as above. Docker reproduces the software
environment; the bundle supplies the artifacts. See `REPRODUCE.md`.

### 3. Full pipeline run inside the container

```powershell
docker compose run training python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger --accel-file data/raw/<session>_accelerometer.csv --gyro-file data/raw/<session>_gyroscope.csv
```

### 4. Retraining (governed, labeled data required)

```powershell
docker compose run training python run_pipeline.py --stages retraining
```

Retraining fails fast if the canonical D1 scaler is missing
(`allow_unscaled_finetune` exists for explicit experiments only) and never
promotes automatically — promotion is a separate, governed stage.

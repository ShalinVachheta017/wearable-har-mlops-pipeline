# Docker

## What it is

Docker packages an application and its dependencies into container images so the same runtime can be executed across machines.

## Why it is used in this thesis

Docker is used to provide reproducible serving/tracking environments and to validate deployability beyond local notebooks/scripts.

## Repository locations

- `docker-compose.yml`
- `docker/Dockerfile.inference`
- `docker/Dockerfile.training`
- `.github/workflows/cd.yml`

## Role in this project

- Core:
  - Inference API container build and deployment path.
  - MLflow service orchestration in local stack.
- Optional:
  - Training and preprocessing compose profiles are on-demand, not always-running.
- Future work:
  - Stronger production hardening (version pinning, secrets handling, environment-specific compose overlays).

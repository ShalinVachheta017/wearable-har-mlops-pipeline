# FastAPI

## What it is

FastAPI is a Python web framework for building high-performance APIs with validation and OpenAPI support.

## Why it is used in this thesis

FastAPI exposes the trained HAR model as an inference service and enables runtime monitoring endpoints for operational evaluation.

## Repository locations

- `src/api/app.py`
- `docker/Dockerfile.inference`
- `docker-compose.yml` (inference service)

## Role in this project

- Core:
  - Service interface for API-based inference and monitoring metrics export.
- Optional:
  - Thesis baseline experiments can be run fully offline with `run_pipeline.py` without launching the API.
- Future work:
  - Additional auth/rate limiting and production gateway integration.

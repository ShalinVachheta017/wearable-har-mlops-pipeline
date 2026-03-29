# CI/CD (GitHub Actions)

## What it is

CI/CD automates build, test, and deployment tasks using version-controlled workflows.

## Why it is used in this thesis

It demonstrates engineering maturity and guards code quality/release consistency for a research-to-production style repository.

## Repository locations

- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`

## Role in this project

- Core:
  - CI checks linting, tests, and container build viability.
- Optional:
  - Local thesis runs do not require GitHub Actions to execute.
- Future work:
  - Add stricter policy gates and environment-specific deployment stages.

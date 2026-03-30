# GitHub Workflows Guide

This folder contains the active CI/CD workflows for the repository.

## Files

- [.github/workflows/ci.yml](.github/workflows/ci.yml): pull-request and push quality checks.
- [.github/workflows/cd.yml](.github/workflows/cd.yml): release image build/push and smoke validation.

## CI Workflow Summary

### Trigger

- Pull requests to main.
- Pushes to main and develop.

### Jobs

```mermaid
graph LR
  L[lint] --> U[unit-tests]
  U --> B[docker-build-check]
```

### Purpose

- Validate style and static quality.
- Run fast unit test suite.
- Verify inference image builds.

## CD Workflow Summary

### CD Trigger

- Tag push matching v*.*.*.
- Manual workflow dispatch with optional image tag.

### CD Jobs

```mermaid
graph LR
  P[build-and-push] --> S[smoke-test]
```

### CD Purpose

- Build and push GHCR image.
- Start container and verify health endpoint.

## End-to-End Release Flow

```mermaid
sequenceDiagram
  participant Dev as Developer
  participant CI as CI Workflow
  participant CD as CD Workflow
  participant Reg as GHCR

  Dev->>CI: Push or PR
  CI->>CI: lint -> unit-tests -> docker-build-check
  CI-->>Dev: pass/fail feedback

  Dev->>CD: Push release tag
  CD->>Reg: build-and-push image
  CD->>CD: smoke-test container
  CD-->>Dev: release status
```

## Thesis Mapping

| Thesis topic | Workflow evidence |
| --- | --- |
| Continuous integration | [.github/workflows/ci.yml](.github/workflows/ci.yml) |
| Release engineering | [.github/workflows/cd.yml](.github/workflows/cd.yml) |
| Deployment validation | smoke-test job in [.github/workflows/cd.yml](.github/workflows/cd.yml) |
| Reproducibility guardrails | deterministic CI checks in [.github/workflows/ci.yml](.github/workflows/ci.yml) |

## Maintenance Rule

Whenever workflow logic changes, also update:

- [internal/reference/tech/ci_cd.md](internal/reference/tech/ci_cd.md)
- [internal/workflow/README.md](internal/workflow/README.md)

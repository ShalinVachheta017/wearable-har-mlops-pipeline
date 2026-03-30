<!-- markdownlint-disable MD060 -->

# Scalability

This standalone deep dive explains scalability for the thesis system.
It links general scale engineering principles to the concrete implementation in this repository.

---

## 1. What Scalability Means (General Concept)

Scalability is the ability of a system to maintain acceptable performance as workload grows.

In ML serving systems, scaling concerns include:

- request throughput,
- latency under load,
- model inference efficiency,
- operational stability during workload spikes.

---

## 2. General Pseudocode (Scalability Pattern)

```text
MONITOR runtime load continuously

IF load exceeds capacity threshold:
  SCALE service resources or replicas
  PROTECT system with rate/queue/backpressure controls

MEASURE latency, throughput, error rate after scaling

IF SLO not met:
  tune model/runtime/batching
  re-evaluate capacity model
```

### Explanation

- Scaling requires both capacity change and observability.
- Without backpressure or limits, high load can cause cascading failures.
- Performance metrics must be tracked before and after tuning.

---

## 3. Scalability Scope in This Thesis

This repository addresses scalability at engineering-readiness level through:

- containerized service boundaries,
- measurable inference latency and API metrics,
- batch inference operations in pipeline and API path,
- stage-separated workflow to keep heavy operations off always-on service path.

It is not yet a full autoscaling cloud deployment.

---

## 4. Scalability Dimensions in This Repository

| Dimension | Current mechanism |
|---|---|
| Service isolation | Dockerized inference and supporting services |
| Workload segmentation | Always-on services vs profile-gated heavy jobs |
| Request observability | Prometheus counters, gauges, latency histogram |
| Release safety at scale | CI and CD checks before artifact promotion |
| Adaptation pressure control | Trigger policy with cooldown and multi-signal gating |

---

## 5. Inference Path Scalability

Primary inference path:

- API receives CSV upload.
- Data is windowed.
- Model predicts in batches (`batch_size=64` in API path).
- Monitoring metrics are emitted per request.

Scalability implications:

- Batching improves throughput relative to per-window prediction loops.
- Upload-size dependent processing means runtime cost scales with number of windows.
- Health endpoint availability supports readiness monitoring under load.

---

## 6. Pipeline Scalability and Workload Isolation

The system separates concerns:

- Always-on: API serving and core observability export.
- On-demand: training and preprocessing services via compose profiles.

This avoids forcing expensive training workloads onto the same always-on serving process.

---

## 7. CI/CD and Scalability Readiness

- CI verifies code quality, tests, and container build viability.
- CD validates that release artifact starts and responds.

While not load-testing automation, this establishes scale readiness by preventing unstable artifacts from becoming release candidates.

---

## 8. Thesis-Centric Pseudocode (Exact Repository Flow)

```text
API upload request arrives:
  parse csv
  detect sensor columns
  create windows
  predict with model.predict(windows, batch_size=64)
  compute monitoring metrics
  export metrics to /metrics endpoint
  return response

Operational controls:
  monitor latency histogram and request counters
  use trigger policy cooldown to avoid repeated heavy retraining actions
  run training/preprocessing only through profile-gated services
```

### Thesis-Centric Explanation

- Scalability is implemented as controlled workload partitioning plus runtime measurement.
- The repo is designed for reliable scaling progression, not immediate hyperscale operation.

---

## 9. Observability for Scale Decisions

Key runtime indicators already available:

- API request counter,
- inference latency histogram,
- confidence/entropy/flip-rate drift-facing indicators,
- health endpoints for liveness checks.

These indicators support decisions such as worker replication, batching changes, and endpoint protection.

---

## 10. What We Use Here

- Container boundaries for service decomposition.
- Batch inference behavior in serving path.
- Runtime metrics required for scale diagnosis.
- Trigger cooldown policy to reduce repeated expensive operations.
- Profile-gated heavy jobs for controlled resource usage.

---

## 11. Scalability Capabilities Not Used Yet

- Horizontal pod autoscaling or cloud-native auto-replica control.
- Queue-based async inference buffering.
- Explicit rate limiting and admission control in API gateway layer.
- Distributed training with elastic compute scheduling.
- Automated load/performance regression testing in CI/CD.

---

## 12. Role in This Thesis

- **Core role:** demonstrates scalable architecture direction with measurable operational signals.
- **Evidence role:** supports claims about production-readiness progression.
- **Future role:** direct bridge to autoscaled cloud deployment patterns.

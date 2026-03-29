# EXPERIMENT PLAN

## Required Experiments

1. Baseline model evaluation
- Metrics: accuracy, precision, recall, F1
- Artifacts: MLflow run + evaluation summary JSON

2. Drift detection validation
- Metric: drift sensitivity and stability across controlled shifts
- Artifacts: monitoring summary + drift reports

3. Prediction monitoring behavior
- Metrics: confidence, entropy, class distribution concentration
- Artifacts: evaluation and monitoring outputs
- Disclosure: Stage 6 entropy is currently an approximation from top-1 confidence; see `METRIC_DISCLOSURES.md`

4. Trigger policy evaluation
- Metrics: warning/alert behavior under synthetic and real runs
- Artifacts: trigger decision JSON + policy eval outputs

5. Runtime and scalability evaluation
- Metrics: throughput, latency, resource profile vs dataset size
- Artifacts: benchmark outputs and run logs

## Freeze Rules

- Do not redesign architecture during exam period.
- Isolate one integrity fix per wave.
- Record command, run_id, timestamp, and artifact location for each experiment.

## Accuracy/Disclosure Notes

- Metric caveats that must be written transparently in thesis text are documented in `METRIC_DISCLOSURES.md`.

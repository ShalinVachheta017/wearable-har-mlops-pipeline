# Metric Disclosures for Thesis Writing

This file records implementation-level metric caveats that must be stated accurately in the thesis text.

## Entropy in Stage 6 Monitoring

Current behavior in Stage 6 monitoring computes mean entropy from top-1 confidence only (not from full per-class probability vectors).

Source implementation:

- `scripts/post_inference_monitoring.py` (`_analyze_confidence`)
- Wrapped by `src/components/post_inference_monitoring.py`

Implemented approximation:

- Uses `confidence` as `c` and assumes remaining probability mass is uniformly distributed across the other `K-1` classes (`K=11`).
- Formula used in code:
  - `H = -c*log(c) - (1-c)*log((1-c)/(K-1))`

What to claim safely:

- Stage 6 entropy is an operational uncertainty proxy derived from top-1 confidence.
- It is useful for monitoring alerts, but it is not equivalent to entropy from full softmax vectors.

# ABC Model-Contract Comparison — Proof-of-Concept Runtime Decision

**Date:** 2026-05-11  
**Branch:** `feature/inference-parity-gpt-no-scaler`

## Executive takeaway

Three model candidates were compared not only by accuracy, but by their full runtime contract: preprocessing, scaler policy, sensor units, tensor layout, label order, monitoring behavior, and trigger decision.

**Model A is selected as the defended proof-of-concept runtime candidate.**
**Model B is kept as a legacy/mentor diagnostic reference.**
**Model C is kept as evidence that wrong preprocessing can break the same checkpoint.**

---

## 1. Why this comparison was done

A model checkpoint alone is not enough to define a reliable runtime model. The same `.keras` file can behave very differently depending on how the input data is scaled, windowed, ordered, and converted.

This was the main reason for the ABC comparison. I wanted to avoid choosing a model only because it has the highest accuracy under one evaluation setup. Instead, I checked which model has the cleanest and most reproducible contract for the thesis proof-of-concept pipeline.

Model C demonstrates this problem clearly: it uses the same weights as Model B, but under the wrong/no-scaler contract it reaches only **7.6% accuracy** on User 7 while still showing **0.748 mean confidence**. So the model is not simply "bad"; the preprocessing contract is wrong.

---

## 2. The three candidates

| Candidate | Role | Origin / training note | Parameters |
| --- | --- | --- | ---: |
| **A — Clean PoC Runtime Candidate** | Final defended candidate | ADAMSense-pretrained CNN-BiLSTM, fine-tuned on Garmin `all_users` training split with focal loss and weak-class recovery | **87,083** |
| **B — Legacy Native / Mentor Reference** | Diagnostic reference | Mentor legacy checkpoint; full training provenance is not fully verified | **499,131** |
| **C — Previous Pipeline Baseline** | Historical mismatch proof | Same checkpoint weights as Model B, tested through the previous row-wise no-scaler contract | **499,131** |

Model A is about **5.7× smaller** than Model B/C. This may partly explain its lower absolute accuracy. Future improvement can explore calibration, higher capacity, and weak-class tuning, but without changing the clean contract.

---

## 3. What is different between the contracts?

| Property | A — Clean PoC | B — Legacy Native | C — Previous Baseline |
| --- | --- | --- | --- |
| Tensor layout | Time-major row-wise | Legacy channel-major → reshape | Time-major row-wise |
| Row meaning | One timestamp, six channels | Semantics differ after legacy reshape | One timestamp, six channels |
| Scaler | Train-only StandardScaler | StandardScaler refitted on full evaluation dataframe | None |
| Scaler persisted? | Yes, JSON + joblib verified | No | Not applicable |
| Unit handling | milli-g converted to m/s² before scaling | milli-g converted to m/s² before diagnostic scaling | milli-g converted to m/s² before windowing |
| Clean runtime contract | Supported | Not supported | Row-wise layout, but checkpoint-contract mismatch |

This is the core point: all three models may accept `(batch, 200, 6)`, but they do **not** receive the same meaning inside that tensor.

---

## 4. Results summary

### Internal diagnostic: `all_users`

This is useful as a sanity check, but it is **not primary evidence** because it comes from the same Garmin/all_users data family used for training and model selection.

| Candidate | Accuracy | Macro F1 | Mean confidence | Trigger |
| --- | ---: | ---: | ---: | --- |
| **A — Clean PoC** | 42.4% | 39.5% | 0.378 | REVIEW |
| **B — Legacy Native** | 90.8% | 90.9% | 0.930 | NO\_ACTION |
| **C — Previous Baseline** | 10.6% | 3.6% | 0.767 | REVIEW |

### External labeled evaluation: User 7

This is the main labeled evidence. User 7 was not used for training. Mixed-label windows are only **2.02%**, so the low score is not mainly caused by label-boundary noise.

| Candidate | Accuracy | Macro F1 | Mean confidence | Trigger |
| --- | ---: | ---: | ---: | --- |
| **A — Clean PoC** | 37.6% | 34.1% | 0.359 | REVIEW |
| **B — Legacy Native** | 43.8% | 41.9% | 0.775 | REVIEW |
| **C — Previous Baseline** | 7.6% | 2.5% | 0.748 | REVIEW |

### Unlabeled Garmin proof-of-concept runtime-style run

This checks monitoring and trigger behavior without ground-truth labels.

| Candidate | Classes used | Mean confidence | Monitoring | Trigger | Auto-retrain |
| --- | ---: | ---: | --- | --- | --- |
| **A — Clean PoC** | 10 / 11 | 0.393 | WARNING | REVIEW | No |
| **B — Legacy Native** | 11 / 11 | 0.717 | WARNING | REVIEW | No |
| **C — Previous Baseline** | 6 / 11 | 0.730 | WARNING | REVIEW | No |

For Model A, the unlabeled Garmin run is routed to REVIEW because the mean confidence is below the warning threshold and the uncertain-window percentage is above the warning threshold. Drift remains healthy for Model A in this run.

---

## 5. Decision

### ✅ Model A — selected as the clean proof-of-concept runtime candidate

Model A does not have the highest accuracy, but it has the cleanest and most reproducible contract:

- train-only scaler, persisted and verified
- row-wise time-major input layout
- fixed feature and label order
- verified model/scaler/label-order artefacts
- monitoring correctly routes uncertainty to REVIEW
- smaller internal-to-external gap: **42.4% → 37.6%**

This makes Model A the most defensible candidate for the thesis proof-of-concept runtime.

### ⚠️ Model B — kept as diagnostic reference only

Model B gives the highest internal diagnostic score, but it depends on a native setup that does not transfer cleanly to the external User 7 recording:

- scaler is not persisted
- scaler is refitted on the full evaluation dataframe during diagnostic evaluation
- tensor layout is legacy channel-major
- clean runtime contract is not supported
- score drops strongly: **90.8% → 43.8%**

So Model B is useful for comparison, but not suitable as the defended runtime model without rebuilding its scaler and input pipeline.

### ❌ Model C — kept as checkpoint-contract mismatch evidence

Model C uses the same checkpoint as Model B, but without the matching preprocessing contract. Its result is near-random and uses only a few classes, while confidence remains high.

This proves the main MLOps lesson from the comparison:

> The checkpoint file alone is not enough. The preprocessing contract controls what the model actually receives.

---

## 6. Limitations and next step

Model A is selected because it is the most reproducible and honest runtime candidate, **not because it is fully robust**.

The current limitations are:

- User 7 accuracy and macro F1 are still low.
- Confidence calibration is not solved.
- External generalisation is not solved.
- User 7 is only one external participant.
- Model A is much smaller than the legacy checkpoint, so capacity may also be a factor.


Full machine-readable evidence is stored in `reports/abc_comparison/` and can be shared if needed.

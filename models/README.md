# `models/` — Model Artifacts & Runtime Contract

This folder holds the **deployment unit** (the Model D1 runtime contract) plus
the drift baselines and pretrained base the pipeline consumes. The thesis
argument is that *the runtime contract — not a loose `.keras` file — is the
deployment unit*; this folder is that contract made explicit on disk.

Superseded artifacts (Model A, the A/B/C lineage, old retraining reports) have
been moved to
`_archive/presubmission_2026-06-27/models/` and are restorable for rollback.

---

## `runtime_contract/model_d1_final_20260528/` — the deployed model (DVC-tracked)

The frozen, defended package. Referenced by `src/config.py` (`MODEL_D1_FINAL_DIR`),
`src/utils/scaler.py`, the Docker inference image, and thesis Appendix C.
The folder is large/binary so it is **DVC-tracked**; only the small pointer
`model_d1_final_20260528.dvc` ships in git (`dvc pull`/`checkout` restores it).

| File | What it is | Used by |
|---|---|---|
| `finetuned_1DCNNBILSTM_HAR_model.keras` | The deployed 1D-CNN+BiLSTM weights (967,499 params) | inference, evaluation |
| `finetuned_..._savedmodel/` | TensorFlow SavedModel export (serving-format twin of the .keras) | portable serving |
| `garmin_train_scaler.json` / `.joblib` | Train-only StandardScaler fit on users 1–6 (the D1 scaler contract) | preprocessing at inference |
| `garmin_train_scaled_baseline.json` | Drift baseline in the **scaled** feature space (API/contract drift path) | Stage 6 drift (API path) |
| `label_order.json` | Canonical 11-class label order | inference decode, parity checks |
| `model_contract.json` | Contract spec: input shape, units, scaler users, window/stride, discipline statement | contract enforcement, defense |
| `model_param_count.json` | Parameter counts (967,499 total) | provenance |
| `artifact_md5.json` | MD5 checksums of contract files | integrity verification |
| `user7_blind_probe_summary.json` | User-7 blind result: 36.96% / F1 0.350 / conf 0.858 | thesis Ch7 evidence |
| `user7_unlabeled_probe_summary.json` | User-7 schedule-aligned probe: 989 windows, 36.70% | thesis Ch7 evidence |

`model_d1_final_20260528.dvc` (in `runtime_contract/`) — DVC pointer for the
folder above; this is the part tracked in git.

---

## Drift baselines (loose at `models/` root)

Two active drift baselines in two feature spaces (documented in thesis §6.2):

| File | What it is | Used by | Tracked |
|---|---|---|---|
| `raw_physical_baseline.json` | Drift baseline in **raw physical** units; the pipeline Stage 6 default | `post_inference_monitoring.py`, `config_entity.py` (`baseline_mode="raw_physical"`) | git |
| `normalized_baseline.json` | Drift baseline in **normalized/scaled** units (alternative mode) | `post_inference_monitoring.py` (normalized mode) | gitignored |
| `training_baseline.json` | Training-distribution baseline written/read by the baseline builder | `src/monitoring/baseline_builder.py` | git |
| `drift_reference.json` | DriftMonitor reference (per-channel train mean/std, PSI/z thresholds) | `drift_monitor.py`, `production_pipeline.py`, `pipeline_chunked_drift.py` | git |

---

## `pretrained/` — base model (DVC-tracked)

The supervisor-provided base the D1 contract was fine-tuned from.

| File | What it is | Used by |
|---|---|---|
| `fine_tuned_model_1dcnnbilstm.keras` | Pretrained 1D-CNN+BiLSTM base (499,131 params) | `src/train.py` fine-tune start; `src/config.py` (`LEGACY_PRETRAINED_MODEL`) |
| `model_info.json` | Base model shape/param metadata | provenance |

Folder is gitignored (`models/.gitignore: /pretrained`); tracked via
`pretrained.dvc`.

---

## `registry/model_registry.json` — governance state

The model-registry record. Key defended fact: `current_version: null` and the
only entry has `status: archived` — i.e. **no retrained candidate has been
auto-promoted**, evidence for the review-gated (no automatic mutation)
governance claim. Used by the registry/promotion logic.

---

## Plumbing

| File | Purpose |
|---|---|
| `.gitignore` | ignores `pretrained/` (DVC-managed) |
| `runtime_contract/.gitignore` | git-ignore rules inside the contract folder |

---

## Archived (not here — see `_archive/presubmission_2026-06-27/models/`)

- `runtime_contract/model_a_final_20260508/` — superseded Model A contract; **rollback target**
- `model_registry/model_a|b|c_*_contract.json` — A/B/C lineage (defense provenance)
- `retrained/` — historical retraining reports and configs

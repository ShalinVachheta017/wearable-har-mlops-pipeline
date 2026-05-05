# Model Matrix Cleanup Archive

Created: 2026-04-27

This archive preserves historical model binaries that are no longer active
runtime choices. Files were moved here to make the active model matrix explicit
without deleting evidence.

Active model locations after cleanup:

- `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` - defended runtime baseline
- `models/retrained/har_model_latest.keras` - retained promotion candidate/reference

Archived categories:

- duplicate pretrained copy from `models/actual model/`
- stale `current_model.keras` placeholder
- registry copy already marked archived
- AdaBN/TENT/pseudo-label adaptation experiments
- older supervised candidate aliases
- tiny failed/test checkpoints

Policy:

- Do not use archived binaries for runtime inference.
- Do not report archived binaries as promoted models.
- Restore from this folder only for historical inspection or a deliberately
  documented comparison.

# Clean Production-Contract HAR Model Training Report

Generated: `2026-05-06 21:16:59`

## Purpose

This notebook trains a thesis-defendable HAR model using the same input contract expected by the production pipeline.

The main goal is to avoid the previous training-serving mismatch where the deployed checkpoint expected a hidden mentor notebook contract.

## Production Contract

- Features: `['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz']`
- Window size: `200`
- Stride: `100`
- Tensor layout: `normal_rowwise_time_by_channel`
- Number of classes: `11`
- Class order: `['ear_rubbing', 'forehead_rubbing', 'hair_pulling', 'hand_scratching', 'hand_tapping', 'knuckles_cracking', 'nail_biting', 'nape_rubbing', 'sitting', 'smoking', 'standing']`
- Scaler mode: `train_only_standard`
- Accelerometer target unit: `m/s^2`
- Gyroscope handling: `unchanged`
- Mentor legacy reshape: `not used`
- User 7: held out for external testing only

## Training Augmentation

- `use_train_augmentation`: `True`
- `copies`: `1`
- `noise_std_fraction_of_channel_std`: `0.02`
- `magnitude_scale_std`: `0.04`
- `max_time_shift_samples`: `8`
- `applies_to`: `training windows only`
- `not_applied_to`: `validation windows or User 7 external test`

## Datasets

- ADAMSense pretraining: `d:\study apply\ML Ops\MasterArbeit_MLops\nb\ADAMSENSE.csv`
- Garmin all_users fine-tuning: `d:\study apply\ML Ops\MasterArbeit_MLops\data\all_users_data_labeled.csv`
- User 7 external test: `d:\study apply\ML Ops\MasterArbeit_MLops\data\raw\2026-05-05-15-11-15_labeled_50Hz_user7.csv`

## Tensor Shapes

- `ADAMSense train`: X `(5603, 200, 6)`, y `(5603,)`
- `ADAMSense validation`: X `(1326, 200, 6)`, y `(1326,)`
- `Garmin train`: X `(2496, 200, 6)`, y `(2496,)`
- `Garmin validation`: X `(1259, 200, 6)`, y `(1259,)`
- `User 7 external`: X `(974, 200, 6)`, y `(974,)`

## Split Summary

| dataset                      | split_group              |   val_size_requested |   seed_offset_used |   train_windows |   val_windows |   train_groups |   val_groups |   group_overlap | validation_missing_classes   |
|:-----------------------------|:-------------------------|---------------------:|-------------------:|----------------:|--------------:|---------------:|-------------:|----------------:|:-----------------------------|
| ADAMSense pretraining        | user_group               |                  0.2 |                  0 |            5603 |          1326 |              8 |            2 |               0 | []                           |
| Garmin all_users fine-tuning | user_group+session_group |                  0.2 |                  0 |            2496 |          1259 |              4 |            2 |               0 | []                           |

## Unit Conversion Decision

- `target_accelerometer_unit`: `m/s^2`
- `target_gyroscope_unit`: `unchanged`
- `adamsense_accelerometer_original_unit_estimate`: `g`
- `adamsense_accelerometer_conversion_factor`: `9.80665`
- `adamsense_robust_abs_range_p01_p99`: `1.08`
- `adamsense_raw_abs_range_min_max`: `2.0`
- `garmin_all_users_conversion`: `none`
- `user7_conversion`: `none`
- `note`: `ADAMSense accel converted only if its range indicates g or milli-g. Garmin all_users and User 7 are treated as already preprocessed/reference-style.`

## ADAMSense Pretraining Validation Metrics

- `dataset`: `ADAMSense validation after pretraining`
- `accuracy`: `0.31070889894419307`
- `macro_f1`: `0.28567868462225526`
- `weighted_f1`: `0.2848905395912719`
- `mean_confidence`: `0.5619941353797913`
- `median_confidence`: `0.5007553100585938`
- `n_predicted_classes`: `11`
- `dominant_class`: `nail_biting`
- `dominant_class_pct`: `0.2933634992458522`

## Garmin Fine-Tuning Validation Metrics

- `dataset`: `Garmin all_users validation after fine-tuning`
- `accuracy`: `0.2621127879269261`
- `macro_f1`: `0.24776619542229214`
- `weighted_f1`: `0.2511198277528902`
- `mean_confidence`: `0.7318846583366394`
- `median_confidence`: `0.7541555166244507`
- `n_predicted_classes`: `11`
- `dominant_class`: `standing`
- `dominant_class_pct`: `0.2509928514694202`

## User 7 External Final Metrics

- `dataset`: `User 7 external final evaluation`
- `accuracy`: `0.5`
- `macro_f1`: `0.4514738832141667`
- `weighted_f1`: `0.4516713310213671`
- `mean_confidence`: `0.6141453981399536`
- `median_confidence`: `0.5472782850265503`
- `n_predicted_classes`: `11`
- `dominant_class`: `knuckles_cracking`
- `dominant_class_pct`: `0.2464065708418891`

## Saved Artifacts

- Final package directory: `d:\study apply\ML Ops\MasterArbeit_MLops\models\production_contract\clean_contract_train_only_standard_20260506_211658`
- Final model: `d:\study apply\ML Ops\MasterArbeit_MLops\models\production_contract\clean_contract_train_only_standard_20260506_211658\fine_tuned_clean_model.keras`
- Model contract: `d:\study apply\ML Ops\MasterArbeit_MLops\models\production_contract\clean_contract_train_only_standard_20260506_211658\model_contract.json`
- Scaler contract: `d:\study apply\ML Ops\MasterArbeit_MLops\diagnostics\model_contract_debug\clean_model_scaler_contract.json`
- Model directory: `d:\study apply\ML Ops\MasterArbeit_MLops\models\production_contract`
- Report directory: `d:\study apply\ML Ops\MasterArbeit_MLops\diagnostics\model_contract_debug`

## Interpretation

This model is trained under a clean production contract: normal row-wise `(time, channel)` windows and explicit scaler behavior.

The mentor legacy tensor layout is not used for this clean model. If mentor-layout results are discussed, they should be reported separately as a legacy compatibility benchmark, not as the production model contract.

User 7 should be interpreted as external deployment-style evidence. It must not be used to tune the model after seeing the result.

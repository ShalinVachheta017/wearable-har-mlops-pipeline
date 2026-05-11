# 20 Mentor vs Pipeline Dataset Comparison

## Short Summary

This diagnostic compares the paper/current production contract against the hidden mentor notebook contract on labeled and unlabeled datasets. The main result remains contract-specific: the deployed `fine_tuned_model_1dcnnbilstm.keras` is only strong on `all_users` when using the explicitly named `legacy_mentor_tensor_layout` plus full-dataframe `StandardScaler`. That does not automatically make it the best deployable contract, because `all_users` may be close to the mentor training representation, the scaler leaks validation distribution, and the paper does not document the hidden scaler or channel-major reshape.

Best primary labeled result per dataset:

| dataset | best_primary_contract | accuracy | macro_F1 | note |
| --- | --- | --- | --- | --- |
| all_users | legacy_mentor_contract | 0.907840 | 0.908931 | All-users may be close to the mentor training representation |
| user7 | legacy_mentor_contract | 0.437816 | 0.418590 | External/self-recorded evaluation |

## What Was Tested

Primary deployable contracts:

| contract | model | scaler | layout | description |
| --- | --- | --- | --- | --- |
| current_pipeline_contract | pretrained_fine_tuned | none | normal_rowwise | Production default: physical units, no StandardScaler, normal time-by-channel windows. |
| current_plus_scaler | pretrained_fine_tuned | standard_full_dataset | normal_rowwise | Current deployed model with mentor full-dataframe StandardScaler but production row-wise layout. |
| legacy_mentor_contract | pretrained_fine_tuned | standard_full_dataset | legacy_mentor_tensor_layout | Mentor notebook contract: full-dataframe StandardScaler plus literal channel-major reshape. |
| clean_local_scaled_contract | pretrained_garmin_finetuned | standard_full_dataset | normal_rowwise | Local Garmin fine-tuned candidate with scaled normal row-wise windows. |
| local_model_with_mentor_layout | pretrained_garmin_finetuned | standard_full_dataset | legacy_mentor_tensor_layout | Local Garmin fine-tuned candidate forced through the mentor literal layout. |

Compatible requested models:

| model_key | path | role | compatible | input_shape | output_shape | skip_reason |
| --- | --- | --- | --- | --- | --- | --- |
| pretrained_fine_tuned | models\pretrained\fine_tuned_model_1dcnnbilstm.keras | deployed_default | True | [null, 200, 6] | [null, 11] |  |
| pretrained_garmin_finetuned | models\pretrained\garmin_finetuned_v1_20260504.keras | local_scaled_candidate | True | [null, 200, 6] | [null, 11] |  |
| pretrained_finetune_best | models\pretrained\_finetune_best.keras | local_scaled_candidate | True | [null, 200, 6] | [null, 11] |  |
| sixth_may_fine_tuned | 6th may\models\fine_tuned_model_1dcnnbilstm.keras | mentor_folder_copy | True | [null, 200, 6] | [null, 11] |  |
| sixth_may_cnnbilstm | 6th may\models\model_wrist_acc_gyro_cnnbilstm.keras | mentor_base_cnnbilstm | True | [null, 200, 6] | [null, 11] |  |
| sixth_may_cnnlstm | 6th may\models\model_wrist_acc_gyro_cnnlstm.keras | mentor_base_cnnlstm | True | [null, 200, 6] | [null, 11] |  |

`6th may/models/model_all.keras` was intentionally not tested in the primary or sweep tables because it expects the ADAMSense-style 18-channel input and is not compatible with the six-channel production pipeline contract.

Datasets and preprocessing metadata:

| dataset | rows | windows | features | label_col | unit_summary | transpose_safe_equals_normal |
| --- | --- | --- | --- | --- | --- | --- |
| all_users | 385326 | 3852 | ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"] | activity | {"accelerometer_conversion_applied": false, "accelerometer_conversion_factor": null, "accelerometer_detected_unit": "m/s^2", "accelerometer_max_abs_before": 45.23043422790527, "gyroscope_unit_assumption": "unchanged, deg/s-style"} | True |
| user7 | 99017 | 989 | ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"] | activity | {"accelerometer_conversion_applied": false, "accelerometer_conversion_factor": null, "accelerometer_detected_unit": "m/s^2", "accelerometer_max_abs_before": 31.362947597888184, "gyroscope_unit_assumption": "unchanged, deg/s-style"} | True |
| unlabeled_1_fused_accelerometer_data_50Hz | 2914 | 28 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | None | {"accelerometer_conversion_applied": true, "accelerometer_conversion_factor": 0.00980665, "accelerometer_detected_unit": "milliG", "accelerometer_max_abs_before": 1005.8649871253969, "gyroscope_unit_assumption": "unchanged, deg/s-style"} | True |
| unlabeled_2_fused_2026_05_04_23_52_10_50Hz | 5371 | 52 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | None | {"accelerometer_conversion_applied": true, "accelerometer_conversion_factor": 0.00980665, "accelerometer_detected_unit": "milliG", "accelerometer_max_abs_before": 2038.883899230957, "gyroscope_unit_assumption": "unchanged, deg/s-style"} | True |
| unlabeled_3_fused_2025_07_17_17_39_05_50Hz | 8799 | 86 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | None | {"accelerometer_conversion_applied": true, "accelerometer_conversion_factor": 0.00980665, "accelerometer_detected_unit": "milliG", "accelerometer_max_abs_before": 3626.0, "gyroscope_unit_assumption": "unchanged, deg/s-style"} | True |
| unlabeled_4_fused_2025_07_17_18_53_05_50Hz | 45699 | 455 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | None | {"accelerometer_conversion_applied": true, "accelerometer_conversion_factor": 0.00980665, "accelerometer_detected_unit": "milliG", "accelerometer_max_abs_before": 4428.255126953125, "gyroscope_unit_assumption": "unchanged, deg/s-style"} | True |
| unlabeled_5_fused_2025_07_17_13_49_10_50Hz | 75999 | 758 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | None | {"accelerometer_conversion_applied": true, "accelerometer_conversion_factor": 0.00980665, "accelerometer_detected_unit": "milliG", "accelerometer_max_abs_before": 6429.315185546875, "gyroscope_unit_assumption": "unchanged, deg/s-style"} | True |

Unlabeled CSV discovery candidates, selected rows included in scoring:

| selected | path | size_MB | feature_cols | score |
| --- | --- | --- | --- | --- |
| True | data\processed\fused_accelerometer_data_50Hz.csv | 0.510000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 135 |
| True | data\processed\fused_2026_05_04_23_52_10_50Hz.csv | 0.930000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 135 |
| True | data\processed\fused_2025_07_17_17_39_05_50Hz.csv | 1.530000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 134 |
| True | data\processed\fused_2025_07_17_18_53_05_50Hz.csv | 7.890000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 128 |
| True | data\processed\fused_2025_07_17_13_49_10_50Hz.csv | 13.130000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 122 |
| False | data\processed\fused_2025_07_17_21_42_30_50Hz.csv | 17.850000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 118 |
| False | data\processed\fused_2026_05_05_15_11_15_50Hz.csv | 18.000000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 118 |
| False | data\processed\fused_2025_07_17_14_16_20_50Hz.csv | 18.580000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 117 |
| False | data\processed\fused_2025_07_16_23_13_09_50Hz.csv | 19.010000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 116 |
| False | data\processed\fused_2025_08_11_12_33_33_50Hz.csv | 20.020000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 115 |
| False | data\processed\fused_2025_07_16_21_46_56_50Hz.csv | 20.910000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 115 |
| False | data\processed\fused_2025_08_12_17_01_38_50Hz.csv | 21.130000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 114 |
| False | data\processed\fused_2025_07_16_22_29_04_50Hz.csv | 21.900000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 114 |
| False | data\processed\fused_2025_07_16_21_03_13_50Hz.csv | 22.600000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 113 |
| False | data\processed\fused_2025_03_23_15_23_10_50Hz.csv | 25.190000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 110 |
| False | data\processed\fused_2025_07_17_15_05_26_50Hz.csv | 26.770000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 109 |
| False | data\processed\fused_2025_07_21_13_58_56_50Hz.csv | 27.760000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 108 |
| False | data\processed\fused_2025_07_17_15_59_12_50Hz.csv | 51.380000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 84 |
| False | data\processed\fused_2025_07_17_19_27_18_50Hz.csv | 52.090000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 83 |
| False | data\processed\fused_2025_08_19_08_58_40_50Hz.csv | 54.810000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 81 |
| False | data\processed\fused_2025_07_21_16_30_24_50Hz.csv | 63.100000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 72 |
| False | artifacts\20260504_140827\data_ingestion\fused_accelerometer_data_50Hz.csv | 0.510000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 35 |
| False | artifacts\20260505_161638\data_ingestion\fused_2026_05_04_23_52_10_50Hz.csv | 0.930000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 35 |
| False | artifacts\20260505_162212\data_ingestion\fused_2026_05_04_23_52_10_50Hz.csv | 0.930000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 35 |
| False | artifacts\20260505_162121\data_ingestion\fused_2026_05_05_15_11_15_50Hz.csv | 1.100000 | ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"] | 34 |

## Labeled Data Results

Primary-contract results for `data/all_users_data_labeled.csv`:

| dataset | contract | model | scaler | layout | n_windows | accuracy | macro_F1 | weighted_F1 | mean_confidence | n_predicted_classes | dominant_class | dominant_class_percentage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_users | current_pipeline_contract | pretrained_fine_tuned | none | normal_rowwise | 3852 | 0.105659 | 0.035797 | 0.034788 | 0.766585 | 7 | hand_tapping | 0.496625 |
| all_users | current_plus_scaler | pretrained_fine_tuned | standard_full_dataset | normal_rowwise | 3852 | 0.144860 | 0.076023 | 0.073516 | 0.850477 | 10 | hand_tapping | 0.688993 |
| all_users | legacy_mentor_contract | pretrained_fine_tuned | standard_full_dataset | legacy_mentor_tensor_layout | 3852 | 0.907840 | 0.908931 | 0.908046 | 0.929686 | 11 | nail_biting | 0.102544 |
| all_users | clean_local_scaled_contract | pretrained_garmin_finetuned | standard_full_dataset | normal_rowwise | 3852 | 0.485462 | 0.454159 | 0.452511 | 0.729995 | 11 | forehead_rubbing | 0.185877 |
| all_users | local_model_with_mentor_layout | pretrained_garmin_finetuned | standard_full_dataset | legacy_mentor_tensor_layout | 3852 | 0.447300 | 0.390129 | 0.387651 | 0.808749 | 11 | smoking | 0.244289 |

## User 7 External Evaluation Results

Primary-contract results for `data/raw/2026-05-05-15-11-15_labeled_50Hz_user7.csv`:

| dataset | contract | model | scaler | layout | n_windows | accuracy | macro_F1 | weighted_F1 | mean_confidence | n_predicted_classes | dominant_class | dominant_class_percentage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| user7 | current_pipeline_contract | pretrained_fine_tuned | none | normal_rowwise | 989 | 0.075834 | 0.024797 | 0.024702 | 0.748384 | 4 | ear_rubbing | 0.471183 |
| user7 | current_plus_scaler | pretrained_fine_tuned | standard_full_dataset | normal_rowwise | 989 | 0.131446 | 0.062952 | 0.062627 | 0.836968 | 7 | hand_tapping | 0.758342 |
| user7 | legacy_mentor_contract | pretrained_fine_tuned | standard_full_dataset | legacy_mentor_tensor_layout | 989 | 0.437816 | 0.418590 | 0.417110 | 0.774558 | 11 | hand_tapping | 0.195147 |
| user7 | clean_local_scaled_contract | pretrained_garmin_finetuned | standard_full_dataset | normal_rowwise | 989 | 0.214358 | 0.183642 | 0.184245 | 0.684530 | 11 | forehead_rubbing | 0.201213 |
| user7 | local_model_with_mentor_layout | pretrained_garmin_finetuned | standard_full_dataset | legacy_mentor_tensor_layout | 989 | 0.407482 | 0.368029 | 0.367062 | 0.760971 | 11 | nape_rubbing | 0.186047 |

User 7 is an external/self-recorded labeled evaluation. Its result should carry more weight for deployment risk than `all_users` when judging generalization, even though it is smaller and may have its own collection differences.

## Unlabeled / Production Confidence Results

No accuracy is calculated for unlabeled data. These rows report confidence, entropy, class spread, temporal flip rate, and agreement with reference contracts:

| dataset | contract | model | scaler | layout | n_windows | mean_confidence | median_confidence | entropy_mean | n_predicted_classes | dominant_class | dominant_class_percentage | transition_flip_rate | agreement_with_legacy_mentor_contract | agreement_with_clean_local_scaled_contract |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| unlabeled_1_fused_accelerometer_data_50Hz | current_pipeline_contract | pretrained_fine_tuned | none | normal_rowwise | 28 | 0.687458 | 0.669298 | 0.736895 | 3 | ear_rubbing | 0.500000 | 0.555556 | 0.321429 | 0.071429 |
| unlabeled_1_fused_accelerometer_data_50Hz | current_plus_scaler | pretrained_fine_tuned | standard_full_dataset | normal_rowwise | 28 | 0.956526 | 0.998624 | 0.160564 | 2 | hand_tapping | 0.928571 | 0.074074 | 0.250000 | 0.107143 |
| unlabeled_1_fused_accelerometer_data_50Hz | legacy_mentor_contract | pretrained_fine_tuned | standard_full_dataset | legacy_mentor_tensor_layout | 28 | 0.667870 | 0.704393 | 0.986743 | 6 | nail_biting | 0.250000 | 0.629630 | 1.000000 | 0.178571 |
| unlabeled_1_fused_accelerometer_data_50Hz | clean_local_scaled_contract | pretrained_garmin_finetuned | standard_full_dataset | normal_rowwise | 28 | 0.629445 | 0.625679 | 1.088576 | 9 | nail_biting | 0.250000 | 0.703704 | 0.178571 | 1.000000 |
| unlabeled_1_fused_accelerometer_data_50Hz | local_model_with_mentor_layout | pretrained_garmin_finetuned | standard_full_dataset | legacy_mentor_tensor_layout | 28 | 0.757583 | 0.825971 | 0.695843 | 8 | sitting | 0.428571 | 0.629630 | 0.071429 | 0.107143 |
| unlabeled_2_fused_2026_05_04_23_52_10_50Hz | current_pipeline_contract | pretrained_fine_tuned | none | normal_rowwise | 52 | 0.658764 | 0.644116 | 0.773342 | 2 | ear_rubbing | 0.576923 | 0.509804 | 0.326923 | 0.076923 |
| unlabeled_2_fused_2026_05_04_23_52_10_50Hz | current_plus_scaler | pretrained_fine_tuned | standard_full_dataset | normal_rowwise | 52 | 0.975903 | 0.996370 | 0.106359 | 2 | hand_tapping | 0.980769 | 0.039216 | 0.288462 | 0.134615 |
| unlabeled_2_fused_2026_05_04_23_52_10_50Hz | legacy_mentor_contract | pretrained_fine_tuned | standard_full_dataset | legacy_mentor_tensor_layout | 52 | 0.699146 | 0.697246 | 0.882719 | 7 | ear_rubbing | 0.461538 | 0.647059 | 1.000000 | 0.057692 |
| unlabeled_2_fused_2026_05_04_23_52_10_50Hz | clean_local_scaled_contract | pretrained_garmin_finetuned | standard_full_dataset | normal_rowwise | 52 | 0.648726 | 0.636358 | 1.010864 | 9 | forehead_rubbing | 0.211538 | 0.745098 | 0.057692 | 1.000000 |
| unlabeled_2_fused_2026_05_04_23_52_10_50Hz | local_model_with_mentor_layout | pretrained_garmin_finetuned | standard_full_dataset | legacy_mentor_tensor_layout | 52 | 0.664727 | 0.683401 | 0.933482 | 10 | knuckles_cracking | 0.211538 | 0.745098 | 0.076923 | 0.173077 |
| unlabeled_3_fused_2025_07_17_17_39_05_50Hz | current_pipeline_contract | pretrained_fine_tuned | none | normal_rowwise | 86 | 0.760435 | 0.799340 | 0.636728 | 3 | hand_tapping | 0.616279 | 0.435294 | 0.093023 | 0.116279 |
| unlabeled_3_fused_2025_07_17_17_39_05_50Hz | current_plus_scaler | pretrained_fine_tuned | standard_full_dataset | normal_rowwise | 86 | 0.905523 | 0.965657 | 0.330461 | 4 | hand_tapping | 0.930233 | 0.141176 | 0.139535 | 0.139535 |
| unlabeled_3_fused_2025_07_17_17_39_05_50Hz | legacy_mentor_contract | pretrained_fine_tuned | standard_full_dataset | legacy_mentor_tensor_layout | 86 | 0.653970 | 0.660879 | 1.021461 | 11 | hand_tapping | 0.162791 | 0.705882 | 1.000000 | 0.151163 |
| unlabeled_3_fused_2025_07_17_17_39_05_50Hz | clean_local_scaled_contract | pretrained_garmin_finetuned | standard_full_dataset | normal_rowwise | 86 | 0.627634 | 0.629063 | 1.062214 | 11 | forehead_rubbing | 0.186047 | 0.764706 | 0.151163 | 1.000000 |
| unlabeled_3_fused_2025_07_17_17_39_05_50Hz | local_model_with_mentor_layout | pretrained_garmin_finetuned | standard_full_dataset | legacy_mentor_tensor_layout | 86 | 0.744619 | 0.757711 | 0.736191 | 10 | nape_rubbing | 0.279070 | 0.541176 | 0.186047 | 0.069767 |
| unlabeled_4_fused_2025_07_17_18_53_05_50Hz | current_pipeline_contract | pretrained_fine_tuned | none | normal_rowwise | 455 | 0.749269 | 0.765914 | 0.693878 | 6 | ear_rubbing | 0.569231 | 0.429515 | 0.024176 | 0.140659 |
| unlabeled_4_fused_2025_07_17_18_53_05_50Hz | current_plus_scaler | pretrained_fine_tuned | standard_full_dataset | normal_rowwise | 455 | 0.883124 | 0.977799 | 0.353725 | 7 | hand_tapping | 0.813187 | 0.169604 | 0.028571 | 0.195604 |
| unlabeled_4_fused_2025_07_17_18_53_05_50Hz | legacy_mentor_contract | pretrained_fine_tuned | standard_full_dataset | legacy_mentor_tensor_layout | 455 | 0.695250 | 0.703003 | 0.864413 | 11 | hair_pulling | 0.221978 | 0.548458 | 1.000000 | 0.118681 |
| unlabeled_4_fused_2025_07_17_18_53_05_50Hz | clean_local_scaled_contract | pretrained_garmin_finetuned | standard_full_dataset | normal_rowwise | 455 | 0.695289 | 0.695679 | 0.871000 | 11 | forehead_rubbing | 0.221978 | 0.541850 | 0.118681 | 1.000000 |
| unlabeled_4_fused_2025_07_17_18_53_05_50Hz | local_model_with_mentor_layout | pretrained_garmin_finetuned | standard_full_dataset | legacy_mentor_tensor_layout | 455 | 0.718614 | 0.716304 | 0.786592 | 10 | sitting | 0.397802 | 0.416300 | 0.294505 | 0.105495 |
| unlabeled_5_fused_2025_07_17_13_49_10_50Hz | current_pipeline_contract | pretrained_fine_tuned | none | normal_rowwise | 758 | 0.745180 | 0.751439 | 0.677536 | 4 | ear_rubbing | 0.534301 | 0.447820 | 0.050132 | 0.046174 |
| unlabeled_5_fused_2025_07_17_13_49_10_50Hz | current_plus_scaler | pretrained_fine_tuned | standard_full_dataset | normal_rowwise | 758 | 0.825655 | 0.912490 | 0.488041 | 6 | hand_tapping | 0.708443 | 0.171731 | 0.212401 | 0.292876 |
| unlabeled_5_fused_2025_07_17_13_49_10_50Hz | legacy_mentor_contract | pretrained_fine_tuned | standard_full_dataset | legacy_mentor_tensor_layout | 758 | 0.612019 | 0.583840 | 1.121451 | 11 | forehead_rubbing | 0.283641 | 0.524439 | 1.000000 | 0.304749 |
| unlabeled_5_fused_2025_07_17_13_49_10_50Hz | clean_local_scaled_contract | pretrained_garmin_finetuned | standard_full_dataset | normal_rowwise | 758 | 0.733677 | 0.775987 | 0.784235 | 11 | forehead_rubbing | 0.437995 | 0.453104 | 0.304749 | 1.000000 |
| unlabeled_5_fused_2025_07_17_13_49_10_50Hz | local_model_with_mentor_layout | pretrained_garmin_finetuned | standard_full_dataset | legacy_mentor_tensor_layout | 758 | 0.721816 | 0.726005 | 0.761342 | 10 | smoking | 0.311346 | 0.387054 | 0.125330 | 0.110818 |

## Contract Agreement / Disagreement

| dataset | left_contract | right_contract | agreement_percentage | top_disagreement_pairs | mean_confidence_difference_left_minus_right | mean_abs_confidence_difference |
| --- | --- | --- | --- | --- | --- | --- |
| all_users | current_pipeline_contract | legacy_mentor_contract | 0.096314 | {"ear_rubbing -> hair_pulling": 195, "ear_rubbing -> nail_biting": 185, "ear_rubbing -> smoking": 196, "hand_tapping -> forehead_rubbing": 188, "hand_tapping -> hair_pulling": 189, "hand_tapping -> hand_scratching": 194, "hand_tapping -> nail_biting": 209, "hand_tapping -> nape_rubbing": 187} | -0.163101 | 0.214475 |
| all_users | current_pipeline_contract | clean_local_scaled_contract | 0.132399 | {"ear_rubbing -> forehead_rubbing": 352, "ear_rubbing -> hand_scratching": 164, "ear_rubbing -> hand_tapping": 224, "ear_rubbing -> nail_biting": 223, "hand_tapping -> forehead_rubbing": 355, "hand_tapping -> hand_scratching": 203, "hand_tapping -> nail_biting": 185, "hand_tapping -> standing": 183} | 0.036590 | 0.217893 |
| all_users | legacy_mentor_contract | clean_local_scaled_contract | 0.473520 | {"hair_pulling -> ear_rubbing": 95, "hair_pulling -> forehead_rubbing": 85, "knuckles_cracking -> hand_scratching": 105, "knuckles_cracking -> hand_tapping": 80, "nail_biting -> forehead_rubbing": 95, "nape_rubbing -> hand_tapping": 72, "smoking -> forehead_rubbing": 133, "smoking -> nail_biting": 79} | 0.199691 | 0.242459 |
| user7 | current_pipeline_contract | legacy_mentor_contract | 0.164813 | {"ear_rubbing -> forehead_rubbing": 71, "ear_rubbing -> hair_pulling": 41, "ear_rubbing -> hand_tapping": 102, "hand_tapping -> ear_rubbing": 74, "hand_tapping -> forehead_rubbing": 43, "hand_tapping -> hair_pulling": 70, "hand_tapping -> nape_rubbing": 48, "smoking -> sitting": 59} | -0.026173 | 0.224728 |
| user7 | current_pipeline_contract | clean_local_scaled_contract | 0.113246 | {"ear_rubbing -> forehead_rubbing": 115, "ear_rubbing -> hand_scratching": 66, "ear_rubbing -> hand_tapping": 57, "ear_rubbing -> nail_biting": 91, "ear_rubbing -> nape_rubbing": 40, "hand_tapping -> forehead_rubbing": 83, "hand_tapping -> hand_scratching": 90, "hand_tapping -> nail_biting": 48} | 0.063855 | 0.223506 |
| user7 | legacy_mentor_contract | clean_local_scaled_contract | 0.279070 | {"ear_rubbing -> forehead_rubbing": 41, "hair_pulling -> forehead_rubbing": 35, "hand_tapping -> hand_scratching": 23, "hand_tapping -> nail_biting": 29, "knuckles_cracking -> hand_scratching": 36, "nape_rubbing -> hand_scratching": 38, "sitting -> nail_biting": 41, "sitting -> standing": 41} | 0.090028 | 0.235006 |
| unlabeled_1_fused_accelerometer_data_50Hz | current_pipeline_contract | legacy_mentor_contract | 0.321429 | {"ear_rubbing -> hair_pulling": 4, "ear_rubbing -> hand_tapping": 1, "ear_rubbing -> nail_biting": 3, "hand_tapping -> nail_biting": 2, "hand_tapping -> nape_rubbing": 3, "hand_tapping -> standing": 2, "smoking -> hand_tapping": 1, "smoking -> nail_biting": 2} | 0.019588 | 0.212479 |
| unlabeled_1_fused_accelerometer_data_50Hz | current_pipeline_contract | clean_local_scaled_contract | 0.071429 | {"ear_rubbing -> forehead_rubbing": 3, "ear_rubbing -> nail_biting": 3, "ear_rubbing -> nape_rubbing": 2, "ear_rubbing -> sitting": 2, "ear_rubbing -> standing": 1, "hand_tapping -> hand_scratching": 3, "hand_tapping -> nail_biting": 2, "smoking -> nail_biting": 2} | 0.058013 | 0.187198 |
| unlabeled_1_fused_accelerometer_data_50Hz | legacy_mentor_contract | clean_local_scaled_contract | 0.178571 | {"ear_rubbing -> nail_biting": 1, "ear_rubbing -> nape_rubbing": 2, "ear_rubbing -> sitting": 1, "hand_tapping -> forehead_rubbing": 1, "hand_tapping -> hand_scratching": 2, "hand_tapping -> nail_biting": 1, "nail_biting -> forehead_rubbing": 1, "nail_biting -> nape_rubbing": 2} | 0.038425 | 0.255874 |
| unlabeled_2_fused_2026_05_04_23_52_10_50Hz | current_pipeline_contract | legacy_mentor_contract | 0.326923 | {"ear_rubbing -> forehead_rubbing": 2, "ear_rubbing -> hair_pulling": 2, "ear_rubbing -> hand_scratching": 2, "ear_rubbing -> hand_tapping": 9, "ear_rubbing -> nail_biting": 3, "hand_tapping -> ear_rubbing": 13, "hand_tapping -> forehead_rubbing": 1, "hand_tapping -> nail_biting": 2} | -0.040382 | 0.245678 |
| unlabeled_2_fused_2026_05_04_23_52_10_50Hz | current_pipeline_contract | clean_local_scaled_contract | 0.076923 | {"ear_rubbing -> forehead_rubbing": 10, "ear_rubbing -> hand_scratching": 5, "ear_rubbing -> hand_tapping": 4, "ear_rubbing -> knuckles_cracking": 2, "ear_rubbing -> nail_biting": 4, "ear_rubbing -> nape_rubbing": 3, "hand_tapping -> hand_scratching": 6, "hand_tapping -> nape_rubbing": 8} | 0.010037 | 0.190088 |
| unlabeled_2_fused_2026_05_04_23_52_10_50Hz | legacy_mentor_contract | clean_local_scaled_contract | 0.057692 | {"ear_rubbing -> forehead_rubbing": 7, "ear_rubbing -> hand_scratching": 5, "ear_rubbing -> hand_tapping": 4, "ear_rubbing -> nail_biting": 2, "ear_rubbing -> nape_rubbing": 3, "hand_tapping -> forehead_rubbing": 3, "hand_tapping -> hand_scratching": 5, "hand_tapping -> nape_rubbing": 3} | 0.050420 | 0.274051 |
| unlabeled_3_fused_2025_07_17_17_39_05_50Hz | current_pipeline_contract | legacy_mentor_contract | 0.093023 | {"ear_rubbing -> hand_scratching": 7, "ear_rubbing -> hand_tapping": 6, "ear_rubbing -> knuckles_cracking": 5, "hand_tapping -> hair_pulling": 5, "hand_tapping -> knuckles_cracking": 7, "hand_tapping -> nape_rubbing": 6, "hand_tapping -> smoking": 5, "hand_tapping -> standing": 8} | 0.106465 | 0.235777 |
| unlabeled_3_fused_2025_07_17_17_39_05_50Hz | current_pipeline_contract | clean_local_scaled_contract | 0.116279 | {"ear_rubbing -> forehead_rubbing": 6, "ear_rubbing -> knuckles_cracking": 6, "ear_rubbing -> nape_rubbing": 5, "hand_tapping -> ear_rubbing": 5, "hand_tapping -> forehead_rubbing": 9, "hand_tapping -> knuckles_cracking": 7, "hand_tapping -> nail_biting": 7, "hand_tapping -> standing": 6} | 0.132801 | 0.252685 |
| unlabeled_3_fused_2025_07_17_17_39_05_50Hz | legacy_mentor_contract | clean_local_scaled_contract | 0.151163 | {"hair_pulling -> ear_rubbing": 2, "hand_scratching -> nape_rubbing": 3, "hand_tapping -> forehead_rubbing": 4, "hand_tapping -> standing": 3, "knuckles_cracking -> forehead_rubbing": 3, "nail_biting -> hand_tapping": 3, "nape_rubbing -> forehead_rubbing": 3, "standing -> hand_tapping": 3} | 0.026335 | 0.244311 |
| unlabeled_4_fused_2025_07_17_18_53_05_50Hz | current_pipeline_contract | legacy_mentor_contract | 0.024176 | {"ear_rubbing -> forehead_rubbing": 54, "ear_rubbing -> hair_pulling": 59, "ear_rubbing -> nail_biting": 25, "ear_rubbing -> nape_rubbing": 25, "ear_rubbing -> smoking": 41, "hand_tapping -> forehead_rubbing": 33, "hand_tapping -> hair_pulling": 40, "hand_tapping -> sitting": 30} | 0.054019 | 0.218013 |
| unlabeled_4_fused_2025_07_17_18_53_05_50Hz | current_pipeline_contract | clean_local_scaled_contract | 0.140659 | {"ear_rubbing -> forehead_rubbing": 60, "ear_rubbing -> hand_scratching": 50, "ear_rubbing -> hand_tapping": 41, "ear_rubbing -> nail_biting": 28, "ear_rubbing -> nape_rubbing": 19, "hand_tapping -> forehead_rubbing": 34, "hand_tapping -> hand_scratching": 31, "hand_tapping -> standing": 27} | 0.053980 | 0.256307 |
| unlabeled_4_fused_2025_07_17_18_53_05_50Hz | legacy_mentor_contract | clean_local_scaled_contract | 0.118681 | {"forehead_rubbing -> hand_scratching": 26, "hair_pulling -> ear_rubbing": 29, "hair_pulling -> forehead_rubbing": 34, "hair_pulling -> standing": 13, "knuckles_cracking -> hand_tapping": 14, "nape_rubbing -> hand_tapping": 13, "sitting -> hand_scratching": 24, "smoking -> forehead_rubbing": 18} | -0.000040 | 0.258637 |
| unlabeled_5_fused_2025_07_17_13_49_10_50Hz | current_pipeline_contract | legacy_mentor_contract | 0.050132 | {"ear_rubbing -> forehead_rubbing": 126, "ear_rubbing -> hand_scratching": 75, "ear_rubbing -> knuckles_cracking": 28, "ear_rubbing -> nail_biting": 36, "ear_rubbing -> nape_rubbing": 46, "hand_tapping -> forehead_rubbing": 89, "hand_tapping -> hand_scratching": 54, "hand_tapping -> knuckles_cracking": 34} | 0.133161 | 0.241656 |
| unlabeled_5_fused_2025_07_17_13_49_10_50Hz | current_pipeline_contract | clean_local_scaled_contract | 0.046174 | {"ear_rubbing -> forehead_rubbing": 213, "ear_rubbing -> hand_scratching": 32, "ear_rubbing -> knuckles_cracking": 18, "ear_rubbing -> nail_biting": 48, "ear_rubbing -> standing": 35, "hand_tapping -> forehead_rubbing": 119, "hand_tapping -> nape_rubbing": 19, "hand_tapping -> standing": 64} | 0.011503 | 0.206152 |
| unlabeled_5_fused_2025_07_17_13_49_10_50Hz | legacy_mentor_contract | clean_local_scaled_contract | 0.304749 | {"forehead_rubbing -> standing": 33, "hand_scratching -> forehead_rubbing": 90, "hand_scratching -> standing": 20, "hand_tapping -> nail_biting": 16, "knuckles_cracking -> hand_tapping": 18, "nail_biting -> forehead_rubbing": 20, "nape_rubbing -> forehead_rubbing": 23, "sitting -> nail_biting": 17} | -0.121659 | 0.272452 |

## What Is Right In Production Pipeline

- It matches the paper-level physical-unit path: Garmin accelerometer milliG is converted to m/s^2 when needed, gyroscope is unchanged, sampling target is 50 Hz, window size is 200, and stride is 100.
- It creates normal row-wise `(time, channel)` tensors, which is the standard 1D time-series representation.
- It has a fixed canonical 11-class mapping and does not silently fit a scaler on the current inference batch by default.

## What Is Wrong In Production Pipeline

- The active model pointer currently targets `fine_tuned_model_1dcnnbilstm.keras`, but that checkpoint behaves as if it expects the mentor notebook contract, not the production tensor contract.
- Therefore, production is internally coherent relative to the paper, but incoherent relative to the deployed checkpoint.
- If the goal is to deploy this specific checkpoint, the production tensor builder/scaler contract does not match it.

## What Is Right In Mentor Notebook Contract

- It reproduces the high `all_users` accuracy for `fine_tuned_model_1dcnnbilstm.keras` when implemented literally as `legacy_mentor_tensor_layout` plus full-dataframe `StandardScaler`.
- It uses the same six wrist accelerometer/gyroscope channels and the same 200/100 window geometry.

## What Is Wrong / Risky In Mentor Notebook Contract

- The hidden `StandardScaler.fit_transform` on the full dataframe is not documented in the paper and leaks validation/test feature statistics when used before splitting.
- The literal channel-major reshape is not normal row-wise time-series layout. If used, it must be named explicitly as `legacy_mentor_tensor_layout`; pretending it is normal `(time, channel)` would hide the root cause.
- Mentor inference fits a fresh scaler on the inference CSV, making predictions batch-dependent. Adding/removing rows can change all standardized windows.
- Paper results report 5-fold CV, while the inspected notebooks use holdout splits after scaling/windowing.

## Pros / Cons Of Each Deployable Choice

| choice | pros | cons |
| --- | --- | --- |
| Keep current production contract and current model | Paper-aligned preprocessing; normal tensor layout; clean production semantics. | Known low accuracy/collapse with current checkpoint. |
| Patch production to legacy_mentor_tensor_layout for current checkpoint | Recovers high all_users accuracy for this checkpoint. | Uses undocumented scaler and nonstandard tensor layout; batch-dependent if scaler is fit per inference file; may not generalize to User 7/production. |
| Use local Garmin fine-tuned model with scaled normal layout | Normal row-wise layout; less hidden tensor behavior; often broader class usage. | Requires explicit scaler contract/provenance and validation; may still underperform reported paper metric. |
| Retrain/export a model for the paper/current production contract | Best long-term MLOps contract: normal tensors, physical units, saved provenance, clean train/val split. | Requires retraining and mentor/training-data confirmation; not a diagnostic-only change. |

## Recommended Solution

Do not silently rename the mentor layout as normal time-series preprocessing. The safest production solution is to train or obtain a checkpoint whose documented input contract is the paper/current production contract: six wrist features in physical units, no hidden per-file scaler, normal row-wise `(time, channel)` windows, fixed class mapping, and validation without scaler leakage. If deadlines require using `fine_tuned_model_1dcnnbilstm.keras`, add an explicit legacy compatibility mode named `legacy_mentor_tensor_layout` and document the full-dataframe StandardScaler behavior as a checkpoint-specific legacy contract, then gate it on User 7 and additional labeled external recordings before deployment.

## Output Files

| file | description |
| --- | --- |
| diagnostics\model_contract_debug\contract_comparison_labeled_summary.csv | All labeled summary rows, including primary contracts and requested model sweep. |
| diagnostics\model_contract_debug\contract_comparison_unlabeled_summary.csv | All unlabeled summary rows; no accuracy fields. |
| diagnostics\model_contract_debug\contract_prediction_agreement.csv | Contract prediction agreement/disagreement rows. |
| diagnostics\model_contract_debug\contract_comparison_unlabeled_candidates.csv | Unlabeled CSV discovery candidates. |
| diagnostics/model_contract_debug/confusion_<dataset>_<model>_<contract>.csv | Confusion matrices for labeled rows. |
| nb\mentor_vs_pipeline_contract_comparison.ipynb | Reproducible diagnostic notebook. |

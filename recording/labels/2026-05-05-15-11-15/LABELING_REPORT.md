# Labeling Report: 2026-05-05-15-11-15

## Inputs
- Fused input: `data/processed/fused_2026_05_05_15_11_15_50Hz.csv`
- Timestamp column used: `true_time`
- First timestamp: `2026-05-05 13:11:14.440000`
- Fused rows: `104,057`

## Outputs
- Timeline CSV: `recording/labels/2026-05-05-15-11-15/label_timeline.csv`
- Labeled row CSV: `recording/labels/2026-05-05-15-11-15/2026-05-05-15-11-15_labeled_50Hz_user7.csv`
- Corrected m/s2 labeled row CSV: `recording/labels/2026-05-05-15-11-15/2026-05-05-15-11-15_labeled_50Hz_user7_ms2.csv`
- Excluded rows CSV: `recording/labels/2026-05-05-15-11-15/2026-05-05-15-11-15_excluded_transition_rows.csv`
- Window labels CSV: `recording/labels/2026-05-05-15-11-15/2026-05-05-15-11-15_window_labels_user7.csv`

## Official Labels Used
- `ear_rubbing`
- `forehead_rubbing`
- `hair_pulling`
- `hand_scratching`
- `hand_tapping`
- `knuckles_cracking`
- `nail_biting`
- `nape_rubbing`
- `sitting`
- `smoking`
- `standing`

## Alias Mapping Applied
- `knuckle_cracking -> knuckles_cracking`
- `nail_rubbing -> nape_rubbing` (user-confirmed correction after initial mismatch)

## Label Mismatches
- None after applying the user-confirmed correction to `nape_rubbing`.

## Unit Correction
Initial labeled CSV was generated from the fused Stage-1 file where accelerometer values were still in milli-g. A corrected version was created by converting `Ax_w`, `Ay_w`, and `Az_w` to m/s2 using factor `0.00980665`. Gyroscope values were kept in deg/s.

Use `2026-05-05-15-11-15_labeled_50Hz_user7_ms2.csv` as the training-style/evaluation file. The original `2026-05-05-15-11-15_labeled_50Hz_user7.csv` was retained unchanged as the direct row-labeling output.

Corrected accelerometer/gyroscope summary:

| statistic | Ax_w | Ay_w | Az_w | Gx_w | Gy_w | Gz_w |
| --- | --- | --- | --- | --- | --- | --- |
| mean | 3.646196 | 2.334429 | -4.075539 | 0.715919 | 0.553730 | 0.000813 |
| min | -19.479350 | -25.150272 | -31.188915 | -558.664124 | -276.423706 | -317.773743 |
| max | 30.100136 | 31.362948 | 14.485230 | 670.033081 | 278.920868 | 269.842072 |

## Timeline
| start_offset | end_offset | activity_raw | activity_final | include | notes |
| --- | --- | --- | --- | --- | --- |
| 00:00.00 | 03:00.00 | ear_rubbing | ear_rubbing | yes |  |
| 03:00.00 | 03:05.00 | transition_hand_on_table | transition_hand_on_table | no | manual transition interval excluded |
| 03:05.00 | 06:00.64 | forehead_rubbing | forehead_rubbing | yes |  |
| 06:00.64 | 09:06.22 | hair_pulling | hair_pulling | yes |  |
| 09:06.22 | 12:13.55 | hand_scratching | hand_scratching | yes |  |
| 12:13.55 | 12:19.02 | transition_hand_on_table | transition_hand_on_table | no | manual transition interval excluded |
| 12:19.02 | 15:19.84 | hand_tapping | hand_tapping | yes |  |
| 15:19.84 | 15:25.23 | transition_hand_on_table | transition_hand_on_table | no | manual transition interval excluded |
| 15:25.23 | 18:26.76 | knuckle_cracking | knuckles_cracking | yes | alias mapped to official class |
| 18:26.76 | 18:37.35 | transition_hand_on_table | transition_hand_on_table | no | manual transition interval excluded |
| 18:37.35 | 21:39.96 | nail_biting | nail_biting | yes |  |
| 21:39.96 | 21:50.08 | transition_hand_on_table | transition_hand_on_table | no | manual transition interval excluded |
| 21:50.08 | 24:57.07 | nail_rubbing | nape_rubbing | yes | corrected to official class after user clarification |
| 24:57.07 | 25:08.14 | transition_hand_on_table | transition_hand_on_table | no | manual transition interval excluded |
| 25:08.14 | 28:10.64 | sitting | sitting | yes |  |
| 28:10.64 | 28:21.74 | transition_hand_on_table | transition_hand_on_table | no | manual transition interval excluded |
| 28:21.74 | 31:23.93 | smoking | smoking | yes |  |
| 31:23.93 | 31:35.42 | transition_hand_on_table | transition_hand_on_table | no | manual transition interval excluded |
| 31:35.42 | 34:40.41 | standing | standing | yes |  |

## Row Counts And Durations
Durations are timestamp-span durations per activity, not row_count * 0.02, because this fused file contains occasional timestamp gaps.
| activity | row_count | duration_sec | manual_duration_sec | duration_delta_sec |
| --- | --- | --- | --- | --- |
| ear_rubbing | 8916 | 180.0 | 180.0 | 0.0 |
| forehead_rubbing | 8699 | 175.64 | 175.64 | 0.0 |
| hair_pulling | 9156 | 185.58 | 185.58 | 0.0 |
| hand_scratching | 9199 | 187.34 | 187.33 | 0.01 |
| hand_tapping | 8940 | 180.82 | 180.82 | 0.0 |
| knuckles_cracking | 8949 | 181.52 | 181.53 | -0.01 |
| nail_biting | 9020 | 182.6 | 182.61 | -0.01 |
| nape_rubbing | 9225 | 187.0 | 186.99 | 0.01 |
| sitting | 8994 | 182.5 | 182.5 | 0.0 |
| smoking | 8915 | 182.2 | 182.19 | 0.01 |
| standing | 9004 | 185.0 | 184.99 | 0.01 |

## Excluded Rows
- Total excluded rows: `5,040`
- Transition rows: `3,477`; manual transition duration `70.23` sec; sample-count equivalent `69.54` sec
- Out-of-range rows: `1,563`; sample-count equivalent `31.26` sec
| exclusion_reason | row_count | sample_count_equiv_sec |
| --- | --- | --- |
| transition_hand_on_table | 3477 | 69.54 |
| out_of_range | 1563 | 31.26 |

## Timestamp Interval Statistics
- Fused min/median/mean/max interval sec: `0.020000` / `0.020000` / `0.020298` / `0.320000`
- Labeled min/median/mean/max interval sec: `0.020000` / `0.020000` / `0.021011` / `11.500000`

## Window Labels
- Window size: `200` samples
- Step size: `100` samples
- Include rule: majority-label purity >= `0.80` and included-row fraction >= `0.80`
- Total windows: `1,039`
| include | window_count |
| --- | --- |
| yes | 977 |
| no | 62 |

### Included Windows By Activity
| activity | included_window_count |
| --- | --- |
| ear_rubbing | 88 |
| forehead_rubbing | 86 |
| hair_pulling | 90 |
| hand_scratching | 91 |
| hand_tapping | 88 |
| knuckles_cracking | 88 |
| nail_biting | 89 |
| nape_rubbing | 91 |
| sitting | 89 |
| smoking | 88 |
| standing | 89 |

## Validation Checks
- `final_columns_exact`: `True`
- `timestamps_monotonic`: `True`
- `median_interval_approx_0_020`: `True`
- `activities_official`: `True`
- `user_column_7`: `True`
- `no_transition_in_labeled`: `True`
- `no_include_no_in_labeled`: `True`
- `training_header_matches`: `True`
- `training_labels_match_official`: `True`
- `corrected_ms2_columns_exact`: `True`
- `corrected_ms2_rows_same`: `True`
- `corrected_ms2_accelerometer_factor_ok`: `True`
- `corrected_ms2_gyroscope_numeric_unchanged`: `True`
- `corrected_ms2_user_column_7`: `True`
- `corrected_ms2_no_transition_in_labeled`: `True`
- Manual included duration: `2010.18` sec
- Actual included duration from timestamp spans: `2010.20` sec
- Included row-count equivalent duration: `1980.34` sec

## Final Verdict
- Ready for evaluation/analysis using the corrected `_ms2.csv` labeled file. Do not use for retraining unless explicitly planned later.

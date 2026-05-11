# 08 Windowing Parity Audit

Reference-style row-index windows are reconstructed from the source/reference CSVs. Segment-aware windows prevent user/activity/gap crossings. Production calculated windows mirror current row-index Stage 3 behavior. Saved artifacts are loaded from the requested run directories.

| dataset | window set | X shape | y shape | window count | windows per class | crosses activity | crosses user | gap-cross windows | window size | stride | label assignment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_users | reference_row_index | 3852, 200, 6 | 3852 | 3852 | {'ear_rubbing': 347, 'forehead_rubbing': 353, 'hair_pulling': 355, 'hand_scratching': 349, 'hand_tapping': 333, 'knuckles_cracking': 349, 'nail_biting': 390, 'nape_rubbing': 327, 'sitting': 351, 'smoking': 361, 'standing': 337} | 129 | 9 | 521 | 200 | 100 | majority_over_rows |
| all_users | gpt_segment_aware | 3449, 200, 6 | 3449 | 3449 | {'ear_rubbing': 318, 'forehead_rubbing': 319, 'hair_pulling': 317, 'hand_scratching': 303, 'hand_tapping': 303, 'knuckles_cracking': 315, 'nail_biting': 342, 'nape_rubbing': 293, 'sitting': 312, 'smoking': 322, 'standing': 305} | 0 | 0 | 0 | 200 | 100 | segment_activity_majority |
| all_users | pipeline_calculated_row_index | 3852, 200, 6 | 3852 | 3852 | {'ear_rubbing': 347, 'forehead_rubbing': 353, 'hair_pulling': 355, 'hand_scratching': 349, 'hand_tapping': 333, 'knuckles_cracking': 349, 'nail_biting': 390, 'nape_rubbing': 327, 'sitting': 351, 'smoking': 361, 'standing': 337} | 129 | 0 | 521 | 200 | 100 | majority_over_rows |
| all_users | production_saved_artifact | 3852, 200, 6 | 3852 | 3852 | {'ear_rubbing': 347, 'forehead_rubbing': 353, 'hair_pulling': 355, 'hand_scratching': 349, 'hand_tapping': 333, 'knuckles_cracking': 349, 'nail_biting': 390, 'nape_rubbing': 327, 'sitting': 351, 'smoking': 361, 'standing': 337} | 0 | 0 | 0 | 200 | 100 | artifact_metadata_or_global_y |
| user7 | reference_row_index | 989, 200, 6 | 989 | 989 | {'ear_rubbing': 89, 'forehead_rubbing': 87, 'hair_pulling': 91, 'hand_scratching': 92, 'hand_tapping': 90, 'knuckles_cracking': 89, 'nail_biting': 90, 'nape_rubbing': 93, 'sitting': 89, 'smoking': 90, 'standing': 89} | 20 | 0 | 277 | 200 | 100 | majority_over_rows |
| user7 | gpt_segment_aware | 768, 200, 6 | 768 | 768 | {'ear_rubbing': 78, 'forehead_rubbing': 78, 'hair_pulling': 73, 'hand_scratching': 74, 'hand_tapping': 78, 'knuckles_cracking': 69, 'nail_biting': 72, 'nape_rubbing': 70, 'sitting': 67, 'smoking': 55, 'standing': 54} | 0 | 0 | 0 | 200 | 100 | segment_activity_majority |
| user7 | pipeline_calculated_row_index | 989, 200, 6 | 989 | 989 | {'ear_rubbing': 89, 'forehead_rubbing': 87, 'hair_pulling': 91, 'hand_scratching': 92, 'hand_tapping': 90, 'knuckles_cracking': 89, 'nail_biting': 90, 'nape_rubbing': 93, 'sitting': 89, 'smoking': 90, 'standing': 89} | 20 | 0 | 277 | 200 | 100 | majority_over_rows |
| user7 | production_saved_artifact | 989, 200, 6 | None | 989 | {} | 0 | 0 | 0 | 200 | 100 | artifact_metadata_or_global_y |

## First 3 Windows

| dataset | window set | window_id | start_idx | end_idx_exclusive | timestamp_start | timestamp_end |
| --- | --- | --- | --- | --- | --- | --- |
| all_users | reference_row_index | 0 | 0 | 200 | 2005-05-01T00:04:59 | 2005-05-01T00:05:03 |
| all_users | reference_row_index | 1 | 100 | 300 | 2005-05-01T00:05:01.020000 | 2005-05-01T00:05:05 |
| all_users | reference_row_index | 2 | 200 | 400 | 2005-05-01T00:05:03.020000 | 2005-05-01T00:05:07.020000 |
| all_users | gpt_segment_aware | 0 | 0 | 200 | 2005-05-01T00:04:59 | 2005-05-01T00:05:03 |
| all_users | gpt_segment_aware | 1 | 100 | 300 | 2005-05-01T00:05:01.020000 | 2005-05-01T00:05:05 |
| all_users | gpt_segment_aware | 2 | 200 | 400 | 2005-05-01T00:05:03.020000 | 2005-05-01T00:05:07.020000 |
| all_users | pipeline_calculated_row_index | 0 | 0 | 200 | 2005-05-01T00:04:59 | 2005-05-01T00:05:03 |
| all_users | pipeline_calculated_row_index | 1 | 100 | 300 | 2005-05-01T00:05:01.020000 | 2005-05-01T00:05:05 |
| all_users | pipeline_calculated_row_index | 2 | 200 | 400 | 2005-05-01T00:05:03.020000 | 2005-05-01T00:05:07.020000 |
| all_users | production_saved_artifact | 0 | 0 | 200 | 2005-05-01T00:04:59.000000 | 2005-05-01T00:05:03.000000 |
| all_users | production_saved_artifact | 1 | 100 | 300 | 2005-05-01T00:05:01.020000 | 2005-05-01T00:05:05.000000 |
| all_users | production_saved_artifact | 2 | 200 | 400 | 2005-05-01T00:05:03.020000 | 2005-05-01T00:05:07.020000 |
| user7 | reference_row_index | 0 | 0 | 200 | 2026-05-05T13:11:14.440000 | 2026-05-05T13:11:18.720000 |
| user7 | reference_row_index | 1 | 100 | 300 | 2026-05-05T13:11:16.740000 | 2026-05-05T13:11:20.740000 |
| user7 | reference_row_index | 2 | 200 | 400 | 2026-05-05T13:11:18.740000 | 2026-05-05T13:11:22.800000 |
| user7 | gpt_segment_aware | 0 | 0 | 200 | 2026-05-05T13:11:15.160000 | 2026-05-05T13:11:19.180000 |
| user7 | gpt_segment_aware | 1 | 100 | 300 | 2026-05-05T13:11:17.200000 | 2026-05-05T13:11:21.200000 |
| user7 | gpt_segment_aware | 2 | 0 | 200 | 2026-05-05T13:11:21.840000 | 2026-05-05T13:11:25.860000 |
| user7 | pipeline_calculated_row_index | 0 | 0 | 200 | 2026-05-05T13:11:14.440000 | 2026-05-05T13:11:18.720000 |
| user7 | pipeline_calculated_row_index | 1 | 100 | 300 | 2026-05-05T13:11:16.740000 | 2026-05-05T13:11:20.740000 |
| user7 | pipeline_calculated_row_index | 2 | 200 | 400 | 2026-05-05T13:11:18.740000 | 2026-05-05T13:11:22.800000 |
| user7 | production_saved_artifact | 0 | 0 | 200 | 2026-05-05T13:11:14.440000 | 2026-05-05T13:11:18.720000 |
| user7 | production_saved_artifact | 1 | 100 | 300 | 2026-05-05T13:11:16.740000 | 2026-05-05T13:11:20.740000 |
| user7 | production_saved_artifact | 2 | 200 | 400 | 2026-05-05T13:11:18.740000 | 2026-05-05T13:11:22.800000 |

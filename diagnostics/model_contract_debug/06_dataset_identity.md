# 06 Dataset Identity Audit

## Dataset Summaries

| dataset | rows | columns | activity_counts | user_count | timestamp_min | timestamp_max |
| --- | --- | --- | --- | --- | --- | --- |
| all_users | 385326 | timestamp, Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w, activity, User, Ax, Ay, Az, Gx, Gy, Gz, timestamp_dt, _orig_index | nail_biting:38924, smoking:36093, hair_pulling:35461, forehead_rubbing:35219, hand_scratching:34975, sitting:34949, knuckles_cracking:34863, ear_rubbing:34768, standing:33859, hand_tapping:33366, nape_rubbing:32849 | 6 | 2005-04-27T20:36:16 | 2005-05-08T09:34:32 |
| user7 | 99017 | timestamp, Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w, activity, User, Ax, Ay, Az, Gx, Gy, Gz, timestamp_dt, _orig_index | nape_rubbing:9225, hand_scratching:9199, hair_pulling:9156, nail_biting:9020, standing:9004, sitting:8994, knuckles_cracking:8949, hand_tapping:8940, ear_rubbing:8916, smoking:8915, forehead_rubbing:8699 | 1 | 2026-05-05T13:11:14.440000 | 2026-05-05T13:45:54.840000 |

## Key File Identity

| path | exists | size_bytes | sha256 | modified_time |
| --- | --- | --- | --- | --- |
| data\all_users_data_labeled.csv | True | 58739815 | 368e516f24c98a60dd13ecf94d248b8088fe07b3524afa5171465fd9f34a2baf | 2025-12-11T18:23:17 |
| nb\all_users_data_labeled.csv | True | 58739815 | 368e516f24c98a60dd13ecf94d248b8088fe07b3524afa5171465fd9f34a2baf | 2025-08-08T11:10:30 |
| data\prepared\config.json | True | 1366 | 6ff9d0bb5c6cb7b97d66c4f0a7d8dc67214fad00936be6c2279d0e9df3ad8313 | 2026-02-16T12:53:37 |

## Discovered Training / Window / Label Artifacts

| file | size_bytes | modified_time | shape |
| --- | --- | --- | --- |
| _archive\internal\workflow\archive_04_tests_reference.md | 14660 | 2026-03-30T01:43:12 |  |
| _archive\root\MLOps Deep Dive_ From Notebook Nightmare to Scalable AI—The Feature Store, Containers, and Continuous Training Revolution.mp3 | 2424614 | 2025-09-21T14:13:02 |  |
| artifacts\20260329_204655\data_transformation\production_X.npy | 8707328 | 2026-03-29T20:47:04 | 1814, 200, 6 |
| artifacts\20260329_204732\data_transformation\production_X.npy | 8707328 | 2026-03-29T20:47:40 | 1814, 200, 6 |
| artifacts\20260329_204901\data_transformation\production_X.npy | 8707328 | 2026-03-29T20:49:09 | 1814, 200, 6 |
| artifacts\20260329_204927\data_transformation\production_X.npy | 8707328 | 2026-03-29T20:49:36 | 1814, 200, 6 |
| artifacts\20260329_205012\data_transformation\production_X.npy | 8707328 | 2026-03-29T20:50:20 | 1814, 200, 6 |
| artifacts\20260329_205039\data_transformation\production_X.npy | 8707328 | 2026-03-29T20:50:47 | 1814, 200, 6 |
| artifacts\20260329_205106\data_transformation\production_X.npy | 6259328 | 2026-03-29T20:51:17 | 1304, 200, 6 |
| artifacts\20260329_205136\data_transformation\production_X.npy | 6259328 | 2026-03-29T20:51:47 | 1304, 200, 6 |
| artifacts\20260329_205206\data_transformation\production_X.npy | 5803328 | 2026-03-29T20:52:17 | 1209, 200, 6 |
| artifacts\20260329_205236\data_transformation\production_X.npy | 5803328 | 2026-03-29T20:52:46 | 1209, 200, 6 |
| artifacts\20260329_205304\data_transformation\production_X.npy | 6057728 | 2026-03-29T20:53:13 | 1262, 200, 6 |
| artifacts\20260329_205331\data_transformation\production_X.npy | 6057728 | 2026-03-29T20:53:41 | 1262, 200, 6 |
| artifacts\20260329_205359\data_transformation\production_X.npy | 5260928 | 2026-03-29T20:54:07 | 1096, 200, 6 |
| artifacts\20260329_205425\data_transformation\production_X.npy | 5260928 | 2026-03-29T20:54:33 | 1096, 200, 6 |
| artifacts\20260329_205451\data_transformation\production_X.npy | 103190528 | 2026-03-29T20:56:57 | 21498, 200, 6 |
| artifacts\20260329_205729\data_transformation\production_X.npy | 103190528 | 2026-03-29T20:59:33 | 21498, 200, 6 |
| artifacts\20260329_210004\data_transformation\production_X.npy | 3638528 | 2026-03-29T21:00:10 | 758, 200, 6 |
| artifacts\20260329_210028\data_transformation\production_X.npy | 3638528 | 2026-03-29T21:00:34 | 758, 200, 6 |
| artifacts\20260329_210052\data_transformation\production_X.npy | 5140928 | 2026-03-29T21:01:00 | 1071, 200, 6 |
| artifacts\20260329_210118\data_transformation\production_X.npy | 5140928 | 2026-03-29T21:01:26 | 1071, 200, 6 |
| artifacts\20260329_210144\data_transformation\production_X.npy | 7416128 | 2026-03-29T21:01:55 | 1545, 200, 6 |
| artifacts\20260329_210214\data_transformation\production_X.npy | 7416128 | 2026-03-29T21:02:25 | 1545, 200, 6 |
| artifacts\20260329_210243\data_transformation\production_X.npy | 14232128 | 2026-03-29T21:03:03 | 2965, 200, 6 |
| artifacts\20260329_210322\data_transformation\production_X.npy | 14232128 | 2026-03-29T21:03:42 | 2965, 200, 6 |
| artifacts\20260329_210401\data_transformation\production_X.npy | 412928 | 2026-03-29T21:04:03 | 86, 200, 6 |
| artifacts\20260329_210421\data_transformation\production_X.npy | 412928 | 2026-03-29T21:04:23 | 86, 200, 6 |
| artifacts\20260329_210440\data_transformation\production_X.npy | 2184128 | 2026-03-29T21:04:45 | 455, 200, 6 |
| artifacts\20260329_210502\data_transformation\production_X.npy | 2184128 | 2026-03-29T21:05:07 | 455, 200, 6 |
| artifacts\20260329_210524\data_transformation\production_X.npy | 14419328 | 2026-03-29T21:05:44 | 3004, 200, 6 |
| artifacts\20260329_210603\data_transformation\production_X.npy | 14419328 | 2026-03-29T21:06:23 | 3004, 200, 6 |
| artifacts\20260329_210642\data_transformation\production_X.npy | 4929728 | 2026-03-29T21:06:50 | 1027, 200, 6 |
| artifacts\20260329_210708\data_transformation\production_X.npy | 4929728 | 2026-03-29T21:07:16 | 1027, 200, 6 |
| artifacts\20260329_210734\data_transformation\production_X.npy | 89452928 | 2026-03-29T21:09:22 | 18636, 200, 6 |
| artifacts\20260329_210952\data_transformation\production_X.npy | 89452928 | 2026-03-29T21:11:40 | 18636, 200, 6 |
| artifacts\20260329_211210\data_transformation\production_X.npy | 7694528 | 2026-03-29T21:12:22 | 1603, 200, 6 |
| artifacts\20260329_211240\data_transformation\production_X.npy | 7694528 | 2026-03-29T21:12:52 | 1603, 200, 6 |
| artifacts\20260329_211311\data_transformation\production_X.npy | 17452928 | 2026-03-29T21:13:35 | 3636, 200, 6 |
| artifacts\20260329_211355\data_transformation\production_X.npy | 17452928 | 2026-03-29T21:14:18 | 3636, 200, 6 |
| artifacts\20260329_211438\data_transformation\production_X.npy | 43612928 | 2026-03-29T21:15:32 | 9086, 200, 6 |
| artifacts\20260329_211555\data_transformation\production_X.npy | 43612928 | 2026-03-29T21:16:50 | 9086, 200, 6 |
| artifacts\20260329_211714\data_transformation\production_X.npy | 20491328 | 2026-03-29T21:17:41 | 4269, 200, 6 |
| artifacts\20260329_211801\data_transformation\production_X.npy | 20491328 | 2026-03-29T21:18:29 | 4269, 200, 6 |
| artifacts\20260329_211849\data_transformation\production_X.npy | 38534528 | 2026-03-29T21:19:37 | 8028, 200, 6 |
| artifacts\20260329_212000\data_transformation\production_X.npy | 38534528 | 2026-03-29T21:20:49 | 8028, 200, 6 |
| artifacts\20260329_212112\data_transformation\production_X.npy | 5457728 | 2026-03-29T21:21:21 | 1137, 200, 6 |
| artifacts\20260329_212139\data_transformation\production_X.npy | 5457728 | 2026-03-29T21:21:48 | 1137, 200, 6 |
| artifacts\20260329_212206\data_transformation\production_X.npy | 47491328 | 2026-03-29T21:23:06 | 9894, 200, 6 |
| artifacts\20260329_212330\data_transformation\production_X.npy | 47491328 | 2026-03-29T21:24:29 | 9894, 200, 6 |
| artifacts\20260329_212454\data_transformation\production_X.npy | 26486528 | 2026-03-29T21:25:28 | 5518, 200, 6 |
| artifacts\20260329_212550\data_transformation\production_X.npy | 26486528 | 2026-03-29T21:26:24 | 5518, 200, 6 |
| artifacts\20260329_212645\data_transformation\production_X.npy | 5841728 | 2026-03-29T21:26:54 | 1217, 200, 6 |
| artifacts\20260329_212713\data_transformation\production_X.npy | 5841728 | 2026-03-29T21:27:23 | 1217, 200, 6 |
| artifacts\20260329_212754\data_transformation\production_X.npy | 15177728 | 2026-03-29T21:28:14 | 3162, 200, 6 |
| artifacts\20260329_212835\data_transformation\production_X.npy | 15177728 | 2026-03-29T21:28:55 | 3162, 200, 6 |
| artifacts\20260329_220202\data_transformation\production_X.npy | 15177728 | 2026-03-29T22:02:04 | 3162, 200, 6 |
| artifacts\20260330_002345\data_transformation\production_X.npy | 15177728 | 2026-03-30T00:23:46 | 3162, 200, 6 |
| artifacts\20260330_005744\data_transformation\production_X.npy | 15177728 | 2026-03-30T00:57:46 | 3162, 200, 6 |
| artifacts\20260330_010430\data_transformation\production_X.npy | 15177728 | 2026-03-30T01:04:32 | 3162, 200, 6 |
| artifacts\20260330_011323\data_transformation\production_X.npy | 15177728 | 2026-03-30T01:13:24 | 3162, 200, 6 |
| artifacts\20260330_012804\data_transformation\production_X.npy | 15177728 | 2026-03-30T01:28:06 | 3162, 200, 6 |
| artifacts\20260428_155716\data_transformation\production_X.npy | 18489728 | 2026-04-28T15:57:25 | 3852, 200, 6 |
| artifacts\20260428_230950\data_transformation\production_X.npy | 8707328 | 2026-04-28T23:10:04 | 1814, 200, 6 |
| artifacts\20260428_232253\data_transformation\production_X.npy | 8707328 | 2026-04-28T23:23:05 | 1814, 200, 6 |
| artifacts\20260430_175531\data_transformation\production_X.npy | 8707328 | 2026-04-30T17:55:46 | 1814, 200, 6 |
| artifacts\20260430_175720\data_transformation\production_X.npy | 8707328 | 2026-04-30T17:57:29 | 1814, 200, 6 |
| artifacts\20260430_175744\data_transformation\production_X.npy | 8707328 | 2026-04-30T17:57:52 | 1814, 200, 6 |
| artifacts\20260430_175810\data_transformation\production_X.npy | 8707328 | 2026-04-30T17:58:19 | 1814, 200, 6 |
| artifacts\20260430_175842\data_transformation\production_X.npy | 8707328 | 2026-04-30T17:58:51 | 1814, 200, 6 |
| artifacts\20260430_175911\data_transformation\production_X.npy | 8707328 | 2026-04-30T17:59:20 | 1814, 200, 6 |
| artifacts\20260430_175934\data_transformation\production_X.npy | 8707328 | 2026-04-30T17:59:42 | 1814, 200, 6 |
| artifacts\20260503_125051\data_transformation\production_X.npy | 8707328 | 2026-05-03T12:51:00 | 1814, 200, 6 |
| artifacts\20260503_125342\data_transformation\production_X.npy | 8707328 | 2026-05-03T12:53:51 | 1814, 200, 6 |
| artifacts\20260503_125418\data_transformation\production_X.npy | 8707328 | 2026-05-03T12:54:27 | 1814, 200, 6 |
| artifacts\20260503_125729\data_transformation\production_X.npy | 8707328 | 2026-05-03T12:57:39 | 1814, 200, 6 |
| artifacts\20260503_125800\data_transformation\production_X.npy | 8707328 | 2026-05-03T12:58:08 | 1814, 200, 6 |
| artifacts\20260503_125835\data_transformation\production_X.npy | 8707328 | 2026-05-03T12:58:46 | 1814, 200, 6 |
| artifacts\20260503_125909\data_transformation\production_X.npy | 8707328 | 2026-05-03T12:59:19 | 1814, 200, 6 |
| artifacts\20260503_130036\data_transformation\production_X.npy | 8707328 | 2026-05-03T13:00:45 | 1814, 200, 6 |
| artifacts\20260503_130746\data_transformation\production_X.npy | 8707328 | 2026-05-03T13:07:55 | 1814, 200, 6 |
| artifacts\20260503_130821\data_transformation\production_X.npy | 8707328 | 2026-05-03T13:08:30 | 1814, 200, 6 |
| artifacts\20260503_130906\data_transformation\production_X.npy | 8707328 | 2026-05-03T13:09:14 | 1814, 200, 6 |
| artifacts\20260503_161728\data_transformation\production_X.npy | 8707328 | 2026-05-03T16:17:40 | 1814, 200, 6 |
| artifacts\20260503_161757\data_transformation\production_X.npy | 8707328 | 2026-05-03T16:18:05 | 1814, 200, 6 |
| artifacts\20260503_184608\data_transformation\production_X.npy | 8707328 | 2026-05-03T18:46:19 | 1814, 200, 6 |
| artifacts\20260503_185027\data_transformation\production_X.npy | 8707328 | 2026-05-03T18:50:35 | 1814, 200, 6 |
| artifacts\20260503_190645\data_transformation\production_X.npy | 8707328 | 2026-05-03T19:06:58 | 1814, 200, 6 |
| artifacts\20260503_191402\data_transformation\production_X.npy | 8707328 | 2026-05-03T19:14:15 | 1814, 200, 6 |
| artifacts\20260503_194533\data_transformation\production_X.npy | 412928 | 2026-05-03T19:45:39 | 86, 200, 6 |
| artifacts\20260504_114625\data_transformation\production_X.npy | 412928 | 2026-05-04T11:46:31 | 86, 200, 6 |
| artifacts\20260504_114746\data_transformation\production_X.npy | 412928 | 2026-05-04T11:47:55 | 86, 200, 6 |
| artifacts\20260504_114957\data_transformation\production_X.npy | 7694528 | 2026-05-04T11:50:19 | 1603, 200, 6 |
| artifacts\20260504_115114\data_transformation\production_X.npy | 26486528 | 2026-05-04T11:52:07 | 5518, 200, 6 |
| artifacts\20260504_115258\data_transformation\production_X.npy | 43612928 | 2026-05-04T11:54:22 | 9086, 200, 6 |
| artifacts\20260504_140827\data_transformation\production_X.npy | 134528 | 2026-05-04T14:08:42 | 28, 200, 6 |
| artifacts\20260504_222936\data_transformation\production_X.npy | 15177728 | 2026-05-04T22:30:17 | 3162, 200, 6 |
| artifacts\20260504_223937\data_transformation\production_X.npy | 15177728 | 2026-05-04T22:40:10 | 3162, 200, 6 |
| artifacts\20260504_230319\data_transformation\production_X.npy | 15177728 | 2026-05-04T23:03:51 | 3162, 200, 6 |
| artifacts\20260504_230439\data_transformation\production_X.npy | 8707328 | 2026-05-04T23:04:49 | 1814, 200, 6 |
| artifacts\20260504_230515\data_transformation\production_X.npy | 6259328 | 2026-05-04T23:05:32 | 1304, 200, 6 |
| artifacts\20260504_230558\data_transformation\production_X.npy | 5803328 | 2026-05-04T23:06:14 | 1209, 200, 6 |
| artifacts\20260504_230640\data_transformation\production_X.npy | 6057728 | 2026-05-04T23:06:56 | 1262, 200, 6 |
| artifacts\20260504_230723\data_transformation\production_X.npy | 5260928 | 2026-05-04T23:07:37 | 1096, 200, 6 |
| artifacts\20260504_230803\data_transformation\production_X.npy | 103190528 | 2026-05-04T23:11:00 | 21498, 200, 6 |
| artifacts\20260504_231140\data_transformation\production_X.npy | 3638528 | 2026-05-04T23:11:52 | 758, 200, 6 |
| artifacts\20260504_231218\data_transformation\production_X.npy | 5140928 | 2026-05-04T23:12:33 | 1071, 200, 6 |
| artifacts\20260504_231259\data_transformation\production_X.npy | 7416128 | 2026-05-04T23:13:17 | 1545, 200, 6 |
| artifacts\20260504_231344\data_transformation\production_X.npy | 14232128 | 2026-05-04T23:14:14 | 2965, 200, 6 |
| artifacts\20260504_231442\data_transformation\production_X.npy | 412928 | 2026-05-04T23:14:47 | 86, 200, 6 |
| artifacts\20260504_231513\data_transformation\production_X.npy | 2184128 | 2026-05-04T23:15:22 | 455, 200, 6 |
| artifacts\20260504_231548\data_transformation\production_X.npy | 14419328 | 2026-05-04T23:16:19 | 3004, 200, 6 |
| artifacts\20260504_231652\data_transformation\production_X.npy | 4929728 | 2026-05-04T23:17:07 | 1027, 200, 6 |
| artifacts\20260504_231737\data_transformation\production_X.npy | 89452928 | 2026-05-04T23:20:20 | 18636, 200, 6 |
| artifacts\20260504_232104\data_transformation\production_X.npy | 7694528 | 2026-05-04T23:21:25 | 1603, 200, 6 |
| artifacts\20260504_232155\data_transformation\production_X.npy | 17452928 | 2026-05-04T23:22:32 | 3636, 200, 6 |
| artifacts\20260504_232304\data_transformation\production_X.npy | 43612928 | 2026-05-04T23:24:27 | 9086, 200, 6 |
| artifacts\20260504_232503\data_transformation\production_X.npy | 20491328 | 2026-05-04T23:25:46 | 4269, 200, 6 |
| artifacts\20260504_232618\data_transformation\production_X.npy | 38534528 | 2026-05-04T23:27:33 | 8028, 200, 6 |
| artifacts\20260504_232808\data_transformation\production_X.npy | 5457728 | 2026-05-04T23:28:24 | 1137, 200, 6 |
| artifacts\20260504_232854\data_transformation\production_X.npy | 47491328 | 2026-05-04T23:30:23 | 9894, 200, 6 |
| artifacts\20260504_233101\data_transformation\production_X.npy | 5841728 | 2026-05-04T23:31:17 | 1217, 200, 6 |
| artifacts\20260504_233155\data_transformation\production_X.npy | 15177728 | 2026-05-04T23:32:28 | 3162, 200, 6 |
| artifacts\20260505_122415\data_transformation\production_X.npy | 15177728 | 2026-05-05T12:24:42 | 3162, 200, 6 |
| artifacts\20260505_122555\data_transformation\production_X.npy | 15177728 | 2026-05-05T12:26:29 | 3162, 200, 6 |
| artifacts\20260505_122757\data_transformation\production_X.npy | 15177728 | 2026-05-05T12:28:31 | 3162, 200, 6 |
| artifacts\20260505_123112\data_transformation\production_X.npy | 8707328 | 2026-05-05T12:31:25 | 1814, 200, 6 |
| artifacts\20260505_123259\data_transformation\production_X.npy | 8707328 | 2026-05-05T12:33:14 | 1814, 200, 6 |
| artifacts\20260505_123353\data_transformation\production_X.npy | 8707328 | 2026-05-05T12:34:08 | 1814, 200, 6 |
| artifacts\20260505_123457\data_transformation\production_X.npy | 8707328 | 2026-05-05T12:35:14 | 1814, 200, 6 |
| artifacts\20260505_123717\data_transformation\production_X.npy | 8707328 | 2026-05-05T12:37:33 | 1814, 200, 6 |
| artifacts\20260505_123846\data_transformation\production_X.npy | 8707328 | 2026-05-05T12:39:01 | 1814, 200, 6 |
| artifacts\20260505_123959\data_transformation\production_X.npy | 8707328 | 2026-05-05T12:40:14 | 1814, 200, 6 |
| artifacts\20260505_140104\data_transformation\production_X.npy | 8707328 | 2026-05-05T14:01:19 | 1814, 200, 6 |
| artifacts\20260505_140709\data_transformation\production_X.npy | 15177728 | 2026-05-05T14:07:42 | 3162, 200, 6 |
| artifacts\20260505_140837\data_transformation\production_X.npy | 8707328 | 2026-05-05T14:08:47 | 1814, 200, 6 |
| artifacts\20260505_143302\data_transformation\production_X.npy | 8707328 | 2026-05-05T14:33:21 | 1814, 200, 6 |
| artifacts\20260505_161638\data_transformation\production_X.npy | 249728 | 2026-05-05T16:16:58 | 52, 200, 6 |
| artifacts\20260505_162121\data_transformation\production_X.npy | 297728 | 2026-05-05T16:21:35 | 62, 200, 6 |
| artifacts\20260505_162212\data_transformation\production_X.npy | 249728 | 2026-05-05T16:22:25 | 52, 200, 6 |
| artifacts\20260505_162305\data_transformation\production_X.npy | 297728 | 2026-05-05T16:23:20 | 62, 200, 6 |
| artifacts\20260505_232743\data_transformation\production_X.npy | 4987328 | 2026-05-05T23:28:06 | 1039, 200, 6 |
| artifacts\20260506_100400\data_transformation\production_X.npy | 4747328 | 2026-05-06T10:04:12 | 989, 200, 6 |
| artifacts\20260506_101242\data_transformation\production_X.npy | 4747328 | 2026-05-06T10:12:50 | 989, 200, 6 |
| artifacts\20260506_103805\data_transformation\production_X.npy | 18489728 | 2026-05-06T10:38:17 | 3852, 200, 6 |
| artifacts\20260506_104921\data_transformation\production_X.npy | 18489728 | 2026-05-06T10:49:34 | 3852, 200, 6 |
| artifacts\stage3_ab_diagnostics\raw_physical_units_ms2_dps\production_X.npy | 8707328 | 2026-04-30T17:56:28 | 1814, 200, 6 |
| artifacts\stage3_ab_diagnostics\zscore_scaled_current_scaler\production_X.npy | 8707328 | 2026-04-30T17:56:31 | 1814, 200, 6 |
| data\prepared\paired_windows\all_users_data_labeled_users_1_2_3_4_canonical_scaled_X.npy | 12153728 | 2026-04-28T15:35:49 | 2532, 200, 6 |
| data\prepared\paired_windows\all_users_data_labeled_users_1_2_3_4_canonical_scaled_y.npy | 10256 | 2026-04-28T15:35:49 | 2532 |
| data\prepared\paired_windows\all_users_data_labeled_users_6_canonical_scaled_X.npy | 3230528 | 2026-04-28T15:35:49 | 673, 200, 6 |
| data\prepared\paired_windows\all_users_data_labeled_users_6_canonical_scaled_y.npy | 2820 | 2026-04-28T15:35:49 | 673 |
| data\prepared\paired_windows\all_users_data_labeled_users_6_raw_X.npy | 3230528 | 2026-04-28T15:45:09 | 673, 200, 6 |
| data\prepared\paired_windows\all_users_data_labeled_users_6_raw_y.npy | 2820 | 2026-04-28T15:45:09 | 673 |
| data\prepared\production_X.npy | 18489728 | 2026-05-06T10:49:34 | 3852, 200, 6 |
| data\prepared\production_y.npy | 15536 | 2026-05-06T10:49:34 | 3852 |
| data\prepared\scaler_train_only.json | 1256 | 2026-05-04T12:13:44 |  |
| diagnostics\model_contract_debug\02_class_mapping_audit.md | 111206 | 2026-05-06T12:12:11 |  |
| diagnostics\model_contract_debug\03_class_permutation_test.md | 1579 | 2026-05-06T12:08:54 |  |
| diagnostics\model_contract_debug\12_controlled_transform_tests.md | 8455 | 2026-05-06T12:09:47 |  |
| diagnostics\model_contract_debug\13_learnability_test.md | 979 | 2026-05-06T12:09:50 |  |
| docker\Dockerfile.training | 1507 | 2026-04-20T17:57:27 |  |
| docs\pretrained_model_exclusion_report.md | 4723 | 2026-04-26T23:39:24 |  |
| docs\thesis_section_4x_pretrained_analysis.md | 5592 | 2026-04-26T23:39:33 |  |
| evidence\final_runtime_freeze_2026_05_05\verification\latest_commit.txt | 72 | 2026-05-05T14:01:37 |  |
| evidence\final_runtime_freeze_2026_05_05\verification\pytest_369_passed.txt | 3138 | 2026-05-05T14:01:30 |  |
| internal\papers\triage\Development and Testing of Retrieval Augmented Generation in Large Language Models.pdf | 620548 | 2025-12-13T23:04:48 |  |
| internal\papers\triage\Development and Testing of Retrieval Augmented Generation in Large Language Models_2.pdf | 620548 | 2026-02-12T15:02:17 |  |
| internal\papers\triage\Development and Testing of Retrieval Augmented Generation in Large Language Models_3.pdf | 620548 | 2025-12-13T23:04:48 |  |
| internal\papers\triage\Pre-trained 1DCNN-BiLSTM Hybrid Network for Temperature Prediction of Wind Turbine Gearboxes.pdf | 12892126 | 2025-08-16T14:56:04 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__pretrained__current_model.keras | 10 | 2026-04-27T17:58:56 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__adabn_adapted_model_configA_20260329_002340.keras | 6095582 | 2026-03-29T00:23:58 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__adabn_adapted_model_configB_20260329_002515.keras | 6095582 | 2026-03-29T00:25:32 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__adabn_adapted_model_configC_20260329_002638.keras | 6095582 | 2026-03-29T00:26:54 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__adabn_adapted_model_configD_20260328_232204.keras | 6095582 | 2026-03-28T23:22:24 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__adabn_tent_adapted_model.keras | 6095598 | 2026-02-23T00:31:53 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__best_model.keras | 17826 | 2026-04-25T01:26:19 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__har_model_20260219_123616.keras | 3797263 | 2026-02-19T12:36:16 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__har_model_20260219_124914.keras | 3797264 | 2026-02-19T12:49:14 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__har_model_20260327_213930.keras | 6096167 | 2026-03-27T21:39:31 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__har_model_20260327_223917.keras | 6096168 | 2026-03-27T22:39:17 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__har_model_fixed_20260425_032714.keras | 17826 | 2026-04-25T03:27:14 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__pseudo_label_model.keras | 2091784 | 2026-02-25T14:00:12 |  |
| models\archive\2026-04-27_model_matrix_cleanup\models__retrained__retrained_model.keras | 6096168 | 2026-03-30T01:43:12 |  |
| models\mmd_reference_windows.npy | 5755328 | 2026-04-21T19:02:21 | 1199, 200, 6 |
| models\pretrained.dvc | 115 | 2025-12-11T17:45:34 |  |
| models\retrained\har_model_latest.keras | 6096168 | 2026-03-30T01:43:12 |  |
| models\retrained\retrained_model.keras | 6096168 | 2026-04-27T19:29:24 |  |
| models\retrained\training_report_20260219_124914.json | 3243 | 2026-02-19T12:49:14 |  |
| models\retrained\training_report_20260327_213930.json | 9299 | 2026-03-30T01:43:12 |  |
| models\retrained\training_report_20260327_223917.json | 7201 | 2026-03-30T01:43:12 |  |
| models\training_baseline.json | 8715 | 2026-03-30T01:43:12 |  |
| nb\model_artifacts\label_encoder.joblib | 1075 | 2026-05-04T13:41:50 |  |
| notebooks\27april_model_preprocess_test.ipynb | 79017 | 2026-04-28T15:39:19 |  |
| notebooks\27april_model_preprocess_test_OPTIMIZED.ipynb | 830955 | 2026-04-28T15:52:34 |  |
| notebooks\27april_model_preprocess_test_cells.py | 53869 | 2026-04-28T12:41:48 |  |
| notebooks\train_synthetic_production_distribution_comparison.ipynb | 65738 | 2026-05-02T04:38:48 |  |
| outputs\ablation\runs\2025-03-23-15-23-10\config_A\prepared\production_X.npy | 8707328 | 2026-03-28T15:09:16 | 1814, 200, 6 |
| outputs\ablation\runs\2025-03-23-15-23-10\config_B\prepared\production_X.npy | 8707328 | 2026-03-28T15:09:23 | 1814, 200, 6 |
| outputs\ablation\runs\2025-03-23-15-23-10\config_C\prepared\production_X.npy | 8707328 | 2026-03-28T15:09:27 | 1814, 200, 6 |
| outputs\ablation\runs\2025-03-23-15-23-10\config_D\prepared\production_X.npy | 8707328 | 2026-03-28T15:09:31 | 1814, 200, 6 |
| outputs\ablation\runs\2025-07-16-21-03-13\config_A\prepared\production_X.npy | 6259328 | 2026-03-28T15:09:43 | 1304, 200, 6 |
| outputs\ablation\runs\2025-07-16-21-03-13\config_B\prepared\production_X.npy | 6259328 | 2026-03-28T15:09:46 | 1304, 200, 6 |
| outputs\ablation\runs\2025-07-16-21-03-13\config_C\prepared\production_X.npy | 6259328 | 2026-03-28T15:09:49 | 1304, 200, 6 |
| outputs\ablation\runs\2025-07-16-21-03-13\config_D\prepared\production_X.npy | 6259328 | 2026-03-28T15:09:52 | 1304, 200, 6 |
| outputs\ablation\runs\2025-07-16-21-46-56\config_A\prepared\production_X.npy | 5803328 | 2026-03-28T15:10:04 | 1209, 200, 6 |
| outputs\ablation\runs\2025-07-16-21-46-56\config_B\prepared\production_X.npy | 5803328 | 2026-03-28T15:10:08 | 1209, 200, 6 |
| outputs\ablation\runs\2025-07-16-21-46-56\config_C\prepared\production_X.npy | 5803328 | 2026-03-28T15:10:11 | 1209, 200, 6 |
| outputs\ablation\runs\2025-07-16-21-46-56\config_D\prepared\production_X.npy | 5803328 | 2026-03-28T15:10:14 | 1209, 200, 6 |
| outputs\ablation\runs\2025-07-16-22-29-04\config_A\prepared\production_X.npy | 6057728 | 2026-03-28T15:10:25 | 1262, 200, 6 |
| outputs\ablation\runs\2025-07-16-22-29-04\config_B\prepared\production_X.npy | 6057728 | 2026-03-28T15:10:29 | 1262, 200, 6 |
| outputs\ablation\runs\2025-07-16-22-29-04\config_C\prepared\production_X.npy | 6057728 | 2026-03-28T15:10:32 | 1262, 200, 6 |
| outputs\ablation\runs\2025-07-16-22-29-04\config_D\prepared\production_X.npy | 6057728 | 2026-03-28T15:10:35 | 1262, 200, 6 |
| outputs\ablation\runs\2025-07-16-23-13-09\config_A\prepared\production_X.npy | 5260928 | 2026-03-28T15:10:45 | 1096, 200, 6 |
| outputs\ablation\runs\2025-07-16-23-13-09\config_B\prepared\production_X.npy | 5260928 | 2026-03-28T15:10:48 | 1096, 200, 6 |
| outputs\ablation\runs\2025-07-16-23-13-09\config_C\prepared\production_X.npy | 5260928 | 2026-03-28T15:10:51 | 1096, 200, 6 |
| outputs\ablation\runs\2025-07-16-23-13-09\config_D\prepared\production_X.npy | 5260928 | 2026-03-28T15:10:54 | 1096, 200, 6 |
| outputs\ablation\runs\2025-07-17-01-48-33\config_A\prepared\production_X.npy | 103190528 | 2026-03-28T15:13:10 | 21498, 200, 6 |
| outputs\ablation\runs\2025-07-17-01-48-33\config_B\prepared\production_X.npy | 103190528 | 2026-03-28T15:13:45 | 21498, 200, 6 |
| outputs\ablation\runs\2025-07-17-01-48-33\config_C\prepared\production_X.npy | 103190528 | 2026-03-28T15:14:17 | 21498, 200, 6 |
| outputs\ablation\runs\2025-07-17-01-48-33\config_D\prepared\production_X.npy | 103190528 | 2026-03-28T15:14:46 | 21498, 200, 6 |
| outputs\ablation\runs\2025-07-17-13-49-10\config_A\prepared\production_X.npy | 3638528 | 2026-03-28T15:15:12 | 758, 200, 6 |
| outputs\ablation\runs\2025-07-17-13-49-10\config_B\prepared\production_X.npy | 3638528 | 2026-03-28T15:15:14 | 758, 200, 6 |
| outputs\ablation\runs\2025-07-17-13-49-10\config_C\prepared\production_X.npy | 3638528 | 2026-03-28T15:15:16 | 758, 200, 6 |
| outputs\ablation\runs\2025-07-17-13-49-10\config_D\prepared\production_X.npy | 3638528 | 2026-03-28T15:15:19 | 758, 200, 6 |
| outputs\ablation\runs\2025-07-17-14-16-20\config_A\prepared\production_X.npy | 5140928 | 2026-03-28T15:15:27 | 1071, 200, 6 |
| outputs\ablation\runs\2025-07-17-14-16-20\config_B\prepared\production_X.npy | 5140928 | 2026-03-28T15:15:30 | 1071, 200, 6 |
| outputs\ablation\runs\2025-07-17-14-16-20\config_C\prepared\production_X.npy | 5140928 | 2026-03-28T15:15:33 | 1071, 200, 6 |
| outputs\ablation\runs\2025-07-17-14-16-20\config_D\prepared\production_X.npy | 5140928 | 2026-03-28T15:15:36 | 1071, 200, 6 |
| outputs\ablation\runs\2025-07-17-15-05-26\config_A\prepared\production_X.npy | 7416128 | 2026-03-28T15:15:48 | 1545, 200, 6 |
| outputs\ablation\runs\2025-07-17-15-05-26\config_B\prepared\production_X.npy | 7416128 | 2026-03-28T15:15:51 | 1545, 200, 6 |
| outputs\ablation\runs\2025-07-17-15-05-26\config_C\prepared\production_X.npy | 7416128 | 2026-03-28T15:15:55 | 1545, 200, 6 |
| outputs\ablation\runs\2025-07-17-15-05-26\config_D\prepared\production_X.npy | 7416128 | 2026-03-28T15:15:59 | 1545, 200, 6 |
| outputs\ablation\runs\2025-07-17-15-59-12\config_A\prepared\production_X.npy | 14232128 | 2026-03-28T15:16:23 | 2965, 200, 6 |
| outputs\ablation\runs\2025-07-17-15-59-12\config_B\prepared\production_X.npy | 14232128 | 2026-03-28T15:16:38 | 2965, 200, 6 |
| outputs\ablation\runs\2025-07-17-15-59-12\config_C\prepared\production_X.npy | 14232128 | 2026-03-28T15:16:51 | 2965, 200, 6 |
| outputs\ablation\runs\2025-07-17-15-59-12\config_D\prepared\production_X.npy | 14232128 | 2026-03-28T15:17:02 | 2965, 200, 6 |
| outputs\ablation\runs\2025-07-17-17-39-05\config_A\prepared\production_X.npy | 412928 | 2026-03-28T15:17:11 | 86, 200, 6 |
| outputs\ablation\runs\2025-07-17-17-39-05\config_B\prepared\production_X.npy | 412928 | 2026-03-28T15:17:13 | 86, 200, 6 |
| outputs\ablation\runs\2025-07-17-17-39-05\config_C\prepared\production_X.npy | 412928 | 2026-03-28T15:17:14 | 86, 200, 6 |
| outputs\ablation\runs\2025-07-17-17-39-05\config_D\prepared\production_X.npy | 412928 | 2026-03-28T15:17:16 | 86, 200, 6 |
| outputs\ablation\runs\2025-07-17-18-53-05\config_A\prepared\production_X.npy | 2184128 | 2026-03-28T15:17:20 | 455, 200, 6 |
| outputs\ablation\runs\2025-07-17-18-53-05\config_B\prepared\production_X.npy | 2184128 | 2026-03-28T15:17:23 | 455, 200, 6 |
| outputs\ablation\runs\2025-07-17-18-53-05\config_C\prepared\production_X.npy | 2184128 | 2026-03-28T15:17:25 | 455, 200, 6 |
| outputs\ablation\runs\2025-07-17-18-53-05\config_D\prepared\production_X.npy | 2184128 | 2026-03-28T15:17:28 | 455, 200, 6 |
| outputs\ablation\runs\2025-07-17-19-27-18\config_A\prepared\production_X.npy | 14419328 | 2026-03-28T15:17:51 | 3004, 200, 6 |
| outputs\ablation\runs\2025-07-17-19-27-18\config_B\prepared\production_X.npy | 14419328 | 2026-03-28T15:17:59 | 3004, 200, 6 |
| outputs\ablation\runs\2025-07-17-19-27-18\config_C\prepared\production_X.npy | 14419328 | 2026-03-28T15:18:08 | 3004, 200, 6 |
| outputs\ablation\runs\2025-07-17-19-27-18\config_D\prepared\production_X.npy | 14419328 | 2026-03-28T15:18:15 | 3004, 200, 6 |
| outputs\ablation\runs\2025-07-17-21-42-30\config_A\prepared\production_X.npy | 4929728 | 2026-03-28T15:18:27 | 1027, 200, 6 |

## Interpretation

- `data/all_users_data_labeled.csv` and `nb/all_users_data_labeled.csv` are compared by SHA256 above.
- `data/prepared/config.json` is historical training/preparation metadata, but the deployed Keras archive itself does not encode enough training-data provenance to prove this CSV was the exact representation used to create the checkpoint.

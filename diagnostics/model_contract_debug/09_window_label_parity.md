# 09 Window-Label Parity Audit

| dataset | window set | n | first==majority | center==majority | y==majority | all three identical | production_y_path_checked | production_y_shape_now |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_users | reference_row_index | 3852 | 3787 | 3852 | 3852 | 3787 |  |  |
| all_users | gpt_segment_aware | 3449 | 3449 | 3449 | 3449 | 3449 |  |  |
| all_users | pipeline_calculated_row_index | 3852 | 3787 | 3852 | 3852 | 3787 |  |  |
| all_users | production_saved_artifact | 3852 | n/a | n/a | n/a | n/a | data\prepared\production_y.npy | 3852 |
| user7 | reference_row_index | 989 | 979 | 989 | 989 | 979 |  |  |
| user7 | gpt_segment_aware | 768 | 768 | 768 | 768 | 768 |  |  |
| user7 | pipeline_calculated_row_index | 989 | 979 | 989 | 989 | 979 |  |  |

The saved run artifacts do not include a run-local `production_y.npy`; their transformation reports point to the mutable global `data/prepared/production_y.npy`. That is a reproducibility risk for old run re-evaluation, even when the metrics written during the run used the then-current labels.

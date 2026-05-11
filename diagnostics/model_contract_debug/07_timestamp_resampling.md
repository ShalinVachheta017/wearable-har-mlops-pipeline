# 07 Timestamp / Resampling Audit

Both requested CSVs are treated as already preprocessed/reference-style; this audit checks continuity only.

| dataset | rows | segment_count | median_gap_ms | mean_gap_ms | large_gaps_gt_60ms | non_positive_gaps | duplicate_timestamps_within_segments |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_users | 385326 | 284 | 20.0 | 20.041553908404797 | 0 | 0 | 0 |
| user7 | 99017 | 176 | 20.0 | 20.148521362592447 | 0 | 0 | 0 |

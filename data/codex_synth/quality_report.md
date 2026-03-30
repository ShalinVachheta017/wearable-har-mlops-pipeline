# Synthetic Dataset Quality Report

## Summary

- Reference rows: `385,326`
- Synthetic rows: `385,326`
- Reference users: `6`
- Synthetic users: `6`
- Activities: `11`

## Overall Sensor Comparison

| Sensor | Real mean | Synth mean | Real std | Synth std | Wasserstein |
|---|---:|---:|---:|---:|---:|
| Ax_w | 3.2186 | 3.2116 | 6.5683 | 6.5588 | 0.1598 |
| Ay_w | 1.2821 | 1.2821 | 4.3515 | 4.3484 | 0.0660 |
| Az_w | -3.5289 | -3.5305 | 3.2362 | 3.2303 | 0.1257 |
| Gx_w | 0.5993 | 0.6049 | 49.9302 | 49.8872 | 8.2007 |
| Gy_w | 0.2252 | 0.2260 | 14.8117 | 14.8031 | 2.9112 |
| Gz_w | 0.0887 | 0.0863 | 14.1668 | 14.1329 | 2.6524 |

## Activity Counts

| Activity | Real rows | Synthetic rows |
|---|---:|---:|
| ear_rubbing | 34,768 | 34,768 |
| forehead_rubbing | 35,219 | 35,219 |
| hair_pulling | 35,461 | 35,461 |
| hand_scratching | 34,975 | 34,975 |
| hand_tapping | 33,366 | 33,366 |
| knuckles_cracking | 34,863 | 34,863 |
| nail_biting | 38,924 | 38,924 |
| nape_rubbing | 32,849 | 32,849 |
| sitting | 34,949 | 34,949 |
| smoking | 36,093 | 36,093 |
| standing | 33,859 | 33,859 |

## Notes

- Synthetic data was generated per user and per activity block.
- Row counts were matched to the reference dataset at `scale_factor = 1.0`.
- Temporal structure was approximated with a per-channel AR(1) process.
- Sensor values were clipped to the observed reference min/max per group.

# Synthetic Data Generation — References

Papers cited to justify the synthetic data augmentation strategy used in this folder.

---

## Core Papers (confirmed, safe to cite)

**[1]** J. Yoon, D. Jarrett, and M. van der Schaar, "Time-series generative adversarial networks,"
in *Advances in Neural Information Processing Systems*, vol. 32, 2019.

> Justification: Establishes that synthetic time-series generation must preserve temporal dynamics,
> not only per-channel statistics. Supports the use of temporal Gaussian smoothing (sigma=5 samples)
> in this generator to add realistic autocorrelation structure.

**[2]** T. T. Um et al., "Data augmentation of wearable sensor data for Parkinson's disease
monitoring using convolutional neural networks,"
in *Proc. 19th ACM Int. Conf. Multimodal Interaction (ICMI)*, Glasgow, UK, 2017, pp. 216-220.

> Justification: Canonical reference for jitter, scaling, and time-warp augmentation on wearable
> HAR sensor data. Directly supports the augmentation-over-replacement principle used here.
> The inter-axis covariance preservation in this generator is aligned with the scaling strategy
> described in this paper.

---

## Supporting Papers (verify exact details before citing)

**[3]** E. Brophy, Z. Wang, Q. She, and T. Ward, "Generative adversarial networks in time series:
A survey and taxonomy," *ACM Computing Surveys*, vol. 55, no. 10, 2023.

> Justification: Survey confirming GAN-based time-series synthesis is an established field but
> method choice and downstream-task validation are required. Supports the no-fixed-ratio argument.
> **Verify:** scholar.google.com -> search "Brophy GAN time series survey ACM 2023"

**[4]** Y. Lu et al., "Machine learning for synthetic data generation: A review,"
arXiv preprint arXiv:2302.04062, 2023.

> Justification: States no universal synthetic-to-real mixing ratio exists; evaluation must be
> task-specific. Directly supports the ablation design (10/20/30/50 pct mixing experiments).
> **Verify:** arxiv.org/abs/2302.04062

**[5]** L. Uhlenberg et al., "Augmenting human activity recognition with synthetic inertial sensor
data generated from human surface models," *Sensors*, 2024.

> Justification: HAR + inertial sensor synthetic generation paper. Shows synthetic IMU data can
> improve HAR but requires downstream-task evaluation. Closely related to this project.
> **Verify:** scholar.google.com -> search "Uhlenberg synthetic inertial HAR 2024"

**[6]** L. Lange et al., "Generating synthetic health sensor data for privacy-preserving wearable
stress detection," 2024.

> Justification: Wearable health sensor synthesis showing GAN-based generation is feasible but
> still needs downstream validation. Relevant because this dataset involves anxiety-related
> wearable behaviors.
> **Verify:** scholar.google.com -> search "Lange synthetic wearable stress GAN 2024"

---

## Recommended Thesis Claim

> "Synthetic samples were generated per-class using multivariate Gaussian sampling with
> inter-axis covariance preservation and temporal Gaussian smoothing (sigma = 5 samples at 50 Hz),
> following the augmentation-over-replacement principle supported by Um et al. (2017) and
> Yoon et al. (2019). Mixing ratios were evaluated empirically via ablation against a
> real-data-only baseline, as no universal synthetic-to-real ratio is established in the
> literature for wearable HAR tasks [Lu et al., 2023; Brophy et al., 2023]."

---

## Ablation Design

| Experiment | Real data | Synthetic data | Notes |
|---|---|---|---|
| Baseline | 100% (385K rows) | 0% | Real users 1-6 only |
| Mix 1 | ~90% | ~10% (~38K rows) | Sample from synthetic_labeled.csv |
| Mix 2 | ~80% | ~20% (~77K rows) | |
| Mix 3 | ~70% | ~30% (~116K rows) | |
| Mix 4 | ~50% | ~50% (~193K rows) | |

Stop if validation accuracy or calibration degrades relative to baseline.

---

## Generation Details

| Parameter | Value |
|---|---|
| Method | Multivariate Gaussian + temporal Gaussian smoothing |
| Smooth sigma | 5 samples (0.1 sec at 50 Hz) |
| Sampling rate | 50 Hz |
| Sensor channels | Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w |
| Classes | 11 (ear_rubbing, forehead_rubbing, hair_pulling, hand_scratching, hand_tapping, knuckles_cracking, nail_biting, nape_rubbing, sitting, smoking, standing) |
| Real users | 1-6 |
| Synthetic users | 7-12 (each mirrors corresponding real user's class distribution) |
| Total rows generated | 385,326 (matches real dataset exactly) |
| Class balance | Preserved (ratio = 1.0 for all 11 classes) |
| User marker | User column values 7-12 (distinguishable from real users 1-6) |
| Clipping | Per-class [min, max] from real data applied per channel |
| Covariance | Full 6x6 covariance matrix per class from real data |

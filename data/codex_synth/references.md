# Codex Synthetic Data References

This folder is reserved for synthetic datasets and related notes created for the HAR thesis experiments.

## Scope

These references justify the plan to use synthetic data as a controlled augmentation strategy for wearable HAR and time-series experiments. They do not imply a universal synthetic-to-real mixing ratio.

## Core References

1. J. Yoon, D. Jarrett, and M. van der Schaar, "Time-series Generative Adversarial Networks," in *Advances in Neural Information Processing Systems 32 (NeurIPS 2019)*, pp. 5509-5519, 2019.
   Link: https://proceedings.neurips.cc/paper/2019/hash/c9efe5f26cd17ba6216bbe2a7d26d490-Abstract.html
   Why it matters: supports sequence-aware synthetic generation and preservation of temporal dynamics.

2. E. Brophy, Q. She, Z. Wang, and T. E. Ward, "Generative Adversarial Networks in Time Series: A Systematic Literature Review," *ACM Computing Surveys*, vol. 55, no. 10, Art. 199, 2023.
   DOI: https://doi.org/10.1145/3559540
   Why it matters: supports the claim that time-series synthesis is established, but method choice and evaluation are task-dependent.

3. Q. Wen, L. Sun, F. Yang, X. Song, J. Gao, X. Wang, and H. Xu, "Time Series Data Augmentation for Deep Learning: A Survey," in *Proceedings of the Thirtieth International Joint Conference on Artificial Intelligence (IJCAI 2021)*, pp. 4653-4660, 2021.
   DOI: https://doi.org/10.24963/ijcai.2021/631
   Why it matters: supports augmentation-based experimentation rather than assuming one fixed best ratio.

4. M. Lupión, F. Cruciani, I. Cleland, C. D. Nugent, and P. M. Ortigosa, "Data Augmentation for Human Activity Recognition With Generative Adversarial Networks," *IEEE Journal of Biomedical and Health Informatics*, vol. 28, no. 4, pp. 2350-2361, 2024.
   DOI: https://doi.org/10.1109/JBHI.2024.3364910
   Why it matters: HAR-specific evidence that GAN-based augmentation can be useful when validated on downstream recognition performance.

5. A. Hoelzemann, N. Sorathiya, and K. Van Laerhoven, "Data Augmentation Strategies for Human Activity Data Using Generative Adversarial Neural Networks," in *2021 IEEE International Conference on Pervasive Computing and Communications Workshops (PerCom Workshops)*, pp. 8-13, 2021.
   DOI: https://doi.org/10.1109/PerComWorkshops51409.2021.9431046
   Why it matters: directly supports empirical augmentation experiments for HAR instead of claiming a universal recipe.

6. L. Uhlenberg, L. O. Haeusler, and O. Amft, "SynHAR: Augmenting Human Activity Recognition With Synthetic Inertial Sensor Data Generated From Human Surface Models," *IEEE Access*, vol. 12, pp. 194839-194858, 2024.
   DOI: https://doi.org/10.1109/ACCESS.2024.3513477
   Why it matters: very relevant to inertial-sensor HAR and synthetic motion generation.

7. L. Alawneh, T. Alsarhan, M. Al-Zinati, M. Al-Ayyoub, Y. Jararweh, and H. Lu, "Enhancing human activity recognition using deep learning and time series augmented data," *Journal of Ambient Intelligence and Humanized Computing*, vol. 12, no. 12, pp. 10565-10580, 2021.
   DOI: https://doi.org/10.1007/s12652-020-02865-4
   Why it matters: additional HAR evidence that augmentation value should be measured empirically against a real-data baseline.

8. L. Lange, N. Wenzlitschke, and E. Rahm, "Generating Synthetic Health Sensor Data for Privacy-Preserving Wearable Stress Detection," *Sensors*, vol. 24, no. 10, Art. 3052, 2024.
   DOI: https://doi.org/10.3390/s24103052
   Why it matters: wearable-sensor context for synthetic data generation in health-adjacent applications.

## Thesis-Safe Position

Synthetic data should be treated as an augmentation strategy and validated empirically against a real-only baseline. The literature supports synthetic generation for time-series and wearable sensing, but it does not establish a universal synthetic-to-real mixing ratio for HAR.

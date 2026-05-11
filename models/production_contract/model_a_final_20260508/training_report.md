# Training Report - Final Model A

Created: 2026-05-08T20:57:23.190181

Selected run: `model_a_sprint_gamma05_weak3_x4_noaug`

Route: ADAMSense-pretrained CNN-BiLSTM, Garmin all_users fine-tuning, weak-class recovery, class-balanced focal loss.

Garmin validation:
- accuracy: 0.3116
- balanced accuracy: 0.3117
- macro F1: 0.3101
- weighted F1: 0.3136
- classes used: 11/11
- dominant class: nape_rubbing (23.5%)

User 7 external evaluation:
- accuracy: 0.3810
- balanced accuracy: 0.3769
- macro F1: 0.3397
- weighted F1: 0.3426
- classes used: 11/11
- dominant class: nape_rubbing (17.2%)

Decision: selected over the mentor/vendor legacy path because it has a documented production contract, avoids full-data scaler leakage, and uses normal row-wise windows. The model is not high-performing; it is the cleanest defendable candidate.

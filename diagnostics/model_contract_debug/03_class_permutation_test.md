# 03 Class Permutation Sanity Test

If class order were the main bug, best-permuted accuracy would jump to a high value. The diagnostic conclusion should be based on the table below.

| dataset | window set | original accuracy | original macro F1 | best-permuted accuracy | best-permuted macro F1 | best mapping pred_index->true_class |
| --- | --- | --- | --- | --- | --- | --- |
| all_users | gpt_segment_aware | 0.10292838503914178 | 0.035229340562127606 | 0.14873876485937954 | 0.08475124137360958 | {'0': 'smoking', '1': 'forehead_rubbing', '2': 'hair_pulling', '3': 'hand_scratching', '4': 'hand_tapping', '5': 'nail_biting', '6': 'standing', '7': 'knuckles_cracking', '8': 'ear_rubbing', '9': 'sitting', '10': 'nape_rubbing'} |
| all_users | production_saved_artifact | 0.10565939771547248 | 0.03578824594603918 | 0.1490134994807892 | 0.08504336976947435 | {'0': 'smoking', '1': 'standing', '2': 'nape_rubbing', '3': 'hair_pulling', '4': 'hand_tapping', '5': 'nail_biting', '6': 'hand_scratching', '7': 'knuckles_cracking', '8': 'ear_rubbing', '9': 'sitting', '10': 'forehead_rubbing'} |
| user7 | gpt_segment_aware | 0.09635416666666667 | 0.03302134514242952 | 0.19401041666666666 | 0.11711350507157374 | {'0': 'nail_biting', '1': 'hand_scratching', '2': 'hair_pulling', '3': 'hand_tapping', '4': 'ear_rubbing', '5': 'knuckles_cracking', '6': 'forehead_rubbing', '7': 'nape_rubbing', '8': 'smoking', '9': 'sitting', '10': 'standing'} |

Original and best-permuted confusion matrices are saved as `confusion_original_*.csv` and `confusion_best_permuted_*.csv`.

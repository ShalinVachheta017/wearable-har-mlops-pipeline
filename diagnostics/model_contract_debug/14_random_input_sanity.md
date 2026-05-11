# 14 Random/Constant-Input Sanity Test (Decisive Evidence)

This is the most direct proof that the deployed `fine_tuned_model_1dcnnbilstm.keras` is structurally degenerate. If the checkpoint were a healthy 11-class classifier, random noise input should produce a roughly uniform output class distribution. It does not.

## Setup

- Model: `models/pretrained/fine_tuned_model_1dcnnbilstm.keras` (SHA256 `3a35f3bd6f74293bfe5e5a7599d1741430a6f76db26b46c0023355d09c1a5bc2`)
- TensorFlow 2.20.0, Keras 3.11.3
- Input: `(N=1000, 200, 6)` Gaussian noise, accel block N(0, 5), gyro block N(0, 25). Numpy seed 0; tf seed 0.
- Two extra tests: all-zero input (100 windows) and all-one input (100 windows).

## Results

| input | classes used | predicted class distribution | mean confidence |
| --- | --- | --- | --- |
| Random Gaussian, sensor-scale (accel σ=5, gyro σ=25), N=1000 | 2 | class 0: 421, class 4: 579 | 0.7054 |
| Constant zero, N=100 | 1 | class 1 (forehead_rubbing): 100 | 0.4996 |
| Constant one, N=100 | 1 | class 9 (smoking): 100 | 0.7710 |
| N(0,1) all channels, N=1000 | 1 | class 4: 1000 | 0.998 |
| N(0,0.1) all channels, N=1000 | 3 | class 1: 261, class 3: 734, class 7: 5 | 0.515 |
| Uniform(-1,1), N=1000 | 1 | class 4: 1000 | 0.997 |

## Alternative Local Checkpoints

The other two locally available `.keras` files were also smoke-tested for completeness:

| checkpoint | classes used on sensor-scale Gaussian, N=1000 | dominant predictions |
| --- | --- | --- |
| `models/pretrained/_finetune_best.keras` | 5 | class 0: 280, class 3: 716 (still bimodal) |
| `models/pretrained/garmin_finetuned_v1_20260504.keras` | 5 | class 0: 280, class 3: 716 (identical to above) |

Both alternatives are also degenerate; they merely collapse to a different bimodal pair (class 0 + class 3) than the deployed checkpoint (class 0 + class 4). No locally available checkpoint passes the random-noise spread test, so no swap-in candidate was promoted.

## Interpretation

- On pure noise the model collapses into the **same two classes** (`ear_rubbing` and `hand_tapping`) it collapses into on labeled `all_users` and User 7 windows. The deployed labeled-data prediction histogram from Task 11 was: `ear_rubbing: 1668, forehead_rubbing: 4, hair_pulling: 20, hand_scratching: 4, hand_tapping: 1913, nail_biting: 2, smoking: 241`. It is the same bimodal collapse.
- Mean confidence on random noise is ~0.70, near the same band as on real data (~0.77). The model is "confidently wrong" regardless of signal content.
- A class-order mismatch cannot produce this behavior: a healthy classifier with shuffled labels would still spread predictions across all 11 indices on random input.
- A unit/feature-order/window mismatch cannot produce this behavior either, because random Gaussian noise has no unit, no feature semantics, and no window structure.
- Constant inputs produce single deterministic predictions, indicating the network has well-defined output without input dependence — typical of a checkpoint whose final dense layer dominates over learned features (e.g. extreme class-bias prior, or a near-untrained final layer).

## Conclusion

The deployed checkpoint is the dominant root cause of the 7–10% production accuracy. No preprocessing change, class re-mapping, unit conversion, or windowing fix can recover accuracy because the model output is essentially independent of input. This corroborates the controlled-transform results (no variant > 13%) and the permutation results (best Hungarian remap < 20%) and matches the learnability finding that tiny baselines hit 100% overfit and 35–58% user-holdout on the same regenerated windows.

## Reproduction

```powershell
C:\Users\shali\anaconda3\envs\thesis-mlops\python.exe -c "import os, numpy as np, tensorflow as tf; os.environ['TF_CPP_MIN_LOG_LEVEL']='3'; np.random.seed(0); tf.random.set_seed(0); m=tf.keras.models.load_model(r'models/pretrained/fine_tuned_model_1dcnnbilstm.keras', compile=False); X=np.random.normal(0,5,(1000,200,6)).astype('float32'); X[:,:,3:]*=5.0; p=m.predict(X, verbose=0); u,c=np.unique(p.argmax(1), return_counts=True); print(dict(zip(u.tolist(), c.tolist())), 'meanconf=', float(p.max(1).mean()))"
```

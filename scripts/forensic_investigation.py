"""Forensic investigation of pretrained vs retrained HAR models.

Runs: architecture inspection, weight stats, raw vs normalized inference,
per-user breakdown, and scaler diff.
"""
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler

ROOT = Path('D:/study apply/ML Ops/MasterArbeit_MLops')

SENSOR_COLS = ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz']
LABEL_MAP = {
    'ear_rubbing': 0, 'forehead_rubbing': 1, 'hair_pulling': 2,
    'hand_scratching': 3, 'hand_tapping': 4, 'knuckles_cracking': 5,
    'nail_biting': 6, 'nape_rubbing': 7, 'sitting': 8,
    'smoking': 9, 'standing': 10,
}
LABEL_MAP_INV = {v: k for k, v in LABEL_MAP.items()}

PRE_PATH = ROOT / 'models/pretrained/fine_tuned_model_1dcnnbilstm.keras'
RE_PATH = ROOT / 'models/retrained/har_model_20260327_213930.keras'
DATA_CSV = ROOT / 'data/all_users_data_labeled.csv'
CONFIG_JSON = ROOT / 'data/prepared/config.json'


# =====================================================================
# STEP 8 — Deep model inspection
# =====================================================================
print("=" * 70)
print("STEP 8 — DEEP PRETRAINED MODEL INSPECTION")
print("=" * 70)

pre = tf.keras.models.load_model(PRE_PATH, compile=False)
print(f"File: {PRE_PATH}")
print(f"Input shape:  {pre.input_shape}")
print(f"Output shape: {pre.output_shape}")
print(f"Total params: {pre.count_params():,}")
print(f"Num layers:   {len(pre.layers)}")
print()

print("--- Summary ---")
pre.summary(line_length=100)
print()

print("--- Weight statistics per layer ---")
first_conv_std = None
for layer in pre.layers:
    weights = layer.get_weights()
    if weights:
        for j, w in enumerate(weights):
            s = (f"  {layer.name:<35} w[{j}] shape={str(w.shape):<22} "
                 f"mean={w.mean():+.5f} std={w.std():.5f} "
                 f"min={w.min():+.4f} max={w.max():+.4f}")
            print(s)
            if first_conv_std is None and 'conv' in layer.name.lower() and j == 0:
                first_conv_std = float(w.std())

print(f"\nFirst Conv layer kernel std = {first_conv_std:.5f}")
if first_conv_std < 0.05:
    print("  -> SUSPICIOUS: weights look possibly untrained (std < 0.05)")
elif first_conv_std < 0.2:
    print("  -> LOOKS TRAINED (std in typical trained range 0.05-0.3)")
else:
    print("  -> LOOKS TRAINED (std > 0.2)")


# =====================================================================
# STEP 9 — Layer-by-layer comparison
# =====================================================================
print("\n" + "=" * 70)
print("STEP 9 — PRETRAINED vs RETRAINED ARCHITECTURE")
print("=" * 70)

re_m = tf.keras.models.load_model(RE_PATH, compile=False)
print(f"{'Property':<25} {'Pretrained':>22} {'Retrained':>22}")
print("-" * 72)
print(f"{'Total params':<25} {pre.count_params():>22,} {re_m.count_params():>22,}")
print(f"{'Input shape':<25} {str(pre.input_shape):>22} {str(re_m.input_shape):>22}")
print(f"{'Output shape':<25} {str(pre.output_shape):>22} {str(re_m.output_shape):>22}")
print(f"{'Num layers':<25} {len(pre.layers):>22} {len(re_m.layers):>22}")
print()

print("--- Layer-by-layer ---")
n = max(len(pre.layers), len(re_m.layers))
for i in range(n):
    pl = pre.layers[i] if i < len(pre.layers) else None
    rl = re_m.layers[i] if i < len(re_m.layers) else None
    pn = pl.__class__.__name__ if pl is not None else "-"
    rn = rl.__class__.__name__ if rl is not None else "-"
    match = "OK" if pn == rn else "MISMATCH"
    pname = pl.name if pl is not None else "-"
    rname = rl.name if rl is not None else "-"
    print(f"  L{i:2d} [{match:<8}] "
          f"PRE: {pn:<22} ({pname:<30}) | "
          f"RE: {rn:<22} ({rname})")
    # Compare weight shapes
    pw = pl.get_weights() if pl is not None else []
    rw = rl.get_weights() if rl is not None else []
    if pw and rw:
        for j, (p, r) in enumerate(zip(pw, rw)):
            sm = "OK" if p.shape == r.shape else "SHAPE MISMATCH"
            print(f"         w[{j}] PRE:{str(p.shape):<20} RE:{str(r.shape):<20} [{sm}]")


# =====================================================================
# STEP 5 — dataset stats
# =====================================================================
print("\n" + "=" * 70)
print("STEP 5 — LABELED DATASET STATISTICS")
print("=" * 70)

df = pd.read_csv(DATA_CSV)
print(f"Columns: {list(df.columns)}")
print(f"Rows: {len(df):,}")

# Rename if needed
rename_map = {f'{c}_w': c for c in ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz']}
df = df.rename(columns=rename_map)
print(f"Columns after rename: {list(df.columns)}")
print()

print("Per-channel stats (raw, after _w rename):")
for c in SENSOR_COLS:
    v = df[c].values
    print(f"  {c:<4} mean={v.mean():+.4f} std={v.std():.4f} "
          f"min={v.min():+.4f} max={v.max():+.4f}")

print(f"\nUnique users: {sorted(df['User'].unique())}")
print("User row counts:")
for u in sorted(df['User'].unique()):
    n_u = (df['User'] == u).sum()
    n_act = df[df['User'] == u]['activity'].nunique()
    print(f"  User {u}: rows={n_u:,} activities={n_act}")

print(f"\nUnique activities: {sorted(df['activity'].unique())}")
print("Activity counts:")
for a in sorted(df['activity'].unique()):
    n_a = (df['activity'] == a).sum()
    print(f"  {a:<20} rows={n_a:,}")


# =====================================================================
# STEP 10 — Definitive test
# =====================================================================
print("\n" + "=" * 70)
print("STEP 10 — DEFINITIVE ACCURACY TEST")
print("=" * 70)

with open(CONFIG_JSON) as f:
    cfg = json.load(f)
mean = np.array(cfg['scaler_mean'])
scale = np.array(cfg['scaler_scale'])
print("Using config.json scaler")
print(f"  mean  = {mean}")
print(f"  scale = {scale}")


def make_windows(data, label_arr, ws=200, step=100):
    X, y = [], []
    for s in range(0, len(data) - ws + 1, step):
        X.append(data[s:s + ws])
        y.append(np.bincount(label_arr[s:s + ws]).argmax())
    return np.array(X), np.array(y)


def evaluate_model(model, X, y, name):
    probs = model.predict(X, batch_size=64, verbose=0)
    preds = probs.argmax(axis=1)
    acc = accuracy_score(y, preds)
    f1 = f1_score(y, preds, average='macro')
    dom = LABEL_MAP_INV[np.bincount(preds).argmax()]
    dom_pct = np.bincount(preds).max() / len(preds) * 100
    conf = probs.max(axis=1).mean()
    print(f"\n  {name}")
    print(f"    Accuracy:   {acc:.4f} ({acc * 100:.2f}%)")
    print(f"    F1 macro:   {f1:.4f}")
    print(f"    Confidence: {conf:.4f}")
    print(f"    Dominant pred: {dom} ({dom_pct:.1f}% of windows)")
    return acc


labels = df['activity'].map(LABEL_MAP).values

# Normalized windows
data_norm = (df[SENSOR_COLS].values - mean) / scale
X_norm, y_norm = make_windows(data_norm, labels)

# Raw windows
X_raw, y_raw = make_windows(df[SENSOR_COLS].values, labels)

# Per-user retrained-style scaler: fit on whole data with StandardScaler
full_sc = StandardScaler().fit(df[SENSOR_COLS].values)
X_full_norm, _ = make_windows(full_sc.transform(df[SENSOR_COLS].values), labels)

print(f"\nTotal windows: {len(X_norm)}")

print("\n" + "-" * 70)
print("PRETRAINED MODEL (fine_tuned_model_1dcnnbilstm.keras)")
print("-" * 70)
evaluate_model(pre, X_norm, y_norm, "With config.json normalization")
evaluate_model(pre, X_raw, y_raw, "Without normalization (raw m/s²)")
evaluate_model(pre, X_full_norm, y_norm, "Fit-on-all StandardScaler")

print("\n" + "-" * 70)
print("RETRAINED MODEL (har_model_20260327_213930.keras)")
print("-" * 70)
evaluate_model(re_m, X_norm, y_norm, "With config.json normalization")
evaluate_model(re_m, X_raw, y_raw, "Without normalization (raw m/s²)")

# Per-user on pretrained
print("\n" + "-" * 70)
print("PRETRAINED — PER USER BREAKDOWN (config.json normalization)")
print("-" * 70)
for u in sorted(df['User'].unique()):
    mask = (df['User'] == u).values
    df_u = df[mask]
    labels_u = labels[mask]
    data_u = (df_u[SENSOR_COLS].values - mean) / scale
    X_u, y_u = make_windows(data_u, labels_u)
    if len(X_u) == 0:
        continue
    probs = pre.predict(X_u, batch_size=64, verbose=0)
    preds = probs.argmax(axis=1)
    acc = accuracy_score(y_u, preds)
    f1 = f1_score(y_u, preds, average='macro')
    dom = LABEL_MAP_INV[np.bincount(preds).argmax()]
    dom_pct = np.bincount(preds).max() / len(preds) * 100
    print(f"  User {u}: n_windows={len(X_u):4d} acc={acc:.3f} f1={f1:.3f} "
          f"dom={dom}({dom_pct:.0f}%)")

# Scaler diff
print("\n" + "=" * 70)
print("STEP 2 — SCALER DIFF (config.json vs retrained scaler_config.json)")
print("=" * 70)
with open(ROOT / 'models/retrained/scaler_config.json') as f:
    rscfg = json.load(f)
rmean = np.array(rscfg['scaler_mean'])
rscale = np.array(rscfg['scaler_scale'])
print(f"{'ch':<4} {'cfg mean':>12} {'ret mean':>12} {'Δmean':>10} "
      f"{'cfg scale':>12} {'ret scale':>12} {'Δscale':>10}")
for i, c in enumerate(SENSOR_COLS):
    print(f"{c:<4} {mean[i]:>12.6f} {rmean[i]:>12.6f} "
          f"{mean[i] - rmean[i]:>+10.6f} {scale[i]:>12.6f} "
          f"{rscale[i]:>12.6f} {scale[i] - rscale[i]:>+10.6f}")

print("\n--- DONE ---")

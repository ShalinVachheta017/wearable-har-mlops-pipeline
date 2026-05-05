"""
Compare all models on a fresh, previously-unseen session.
Preprocesses the chosen fused CSV inline (does NOT overwrite production_X.npy).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import os

import numpy as np
import pandas as pd

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import tensorflow as tf

# ── configuration ────────────────────────────────────────────────────────────

SESSION_CSV = PROJECT_ROOT / "data" / "processed" / "fused_2025_08_12_17_01_38_50Hz.csv"
SCALER_CFG  = PROJECT_ROOT / "models" / "retrained" / "scaler_config.json"

SENSOR_COLS    = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
WINDOW_SIZE    = 200
STEP_SIZE      = 100
MILLIG_TO_MS2  = 0.00981   # conversion factor

ACTIVITY_CLASSES = {
    0: "ear_rubbing",    1: "forehead_rubbing", 2: "hair_pulling",
    3: "hand_scratching",4: "hand_tapping",     5: "knuckles_cracking",
    6: "nail_biting",    7: "nape_rubbing",     8: "sitting",
    9: "smoking",       10: "standing",
}

MODELS = {
    "actual_model (fine_tuned_1dcnnbilstm)": PROJECT_ROOT / "models" / "actual model" / "fine_tuned_model_1dcnnbilstm.keras",
    "retrained_best (Mar2026, 92.2%)":       PROJECT_ROOT / "models" / "retrained" / "har_model_20260327_223917.keras",
    "pseudo_label_model":                    PROJECT_ROOT / "models" / "retrained" / "pseudo_label_model.keras",
}


# ── preprocessing ─────────────────────────────────────────────────────────────

def load_and_preprocess(csv_path: Path) -> np.ndarray:
    print(f"Loading session: {csv_path.name}")
    df = pd.read_csv(csv_path)
    print(f"  Rows: {len(df):,}  Columns: {list(df.columns)}")

    data = df[SENSOR_COLS].copy().astype(np.float32)
    data = data.ffill().bfill()

    # unit detection
    accel_abs_max = data[["Ax", "Ay", "Az"]].abs().values.max()
    if accel_abs_max > 100:
        print(f"  Accel max={accel_abs_max:.1f} → milliG detected, converting to m/s²")
        data[["Ax", "Ay", "Az"]] *= MILLIG_TO_MS2
    else:
        print(f"  Accel max={accel_abs_max:.2f} → already m/s²")

    # z-score normalization using training scaler
    with open(SCALER_CFG) as f:
        cfg = json.load(f)
    mean  = np.array(cfg["scaler_mean"],  dtype=np.float32)
    scale = np.array(cfg["scaler_scale"], dtype=np.float32)
    data_norm = (data.values - mean) / scale
    print(f"  Normalized  mean={data_norm.mean():.4f}  std={data_norm.std():.4f}")

    # sliding windows
    n_rows = len(data_norm)
    windows = []
    idx = 0
    while idx + WINDOW_SIZE <= n_rows:
        windows.append(data_norm[idx: idx + WINDOW_SIZE])
        idx += STEP_SIZE

    X = np.stack(windows).astype(np.float32)
    print(f"  Windows: {X.shape}  (size={WINDOW_SIZE}, step={STEP_SIZE})")
    return X


# ── inference helpers ─────────────────────────────────────────────────────────

def run_inference(model, data, batch_size=64):
    probs = model.predict(data, batch_size=batch_size, verbose=0)
    preds = np.argmax(probs, axis=1)
    confs = np.max(probs, axis=1)
    return preds, confs


def confidence_bands(confs):
    n = len(confs)
    return {
        "HIGH >90%":   f"{np.sum(confs>0.90):4d} ({100*np.sum(confs>0.90)/n:.1f}%)",
        "MOD 70-90%":  f"{np.sum((confs>0.70)&(confs<=0.90)):4d} ({100*np.sum((confs>0.70)&(confs<=0.90))/n:.1f}%)",
        "LOW 50-70%":  f"{np.sum((confs>0.50)&(confs<=0.70)):4d} ({100*np.sum((confs>0.50)&(confs<=0.70))/n:.1f}%)",
        "UNCERT <50%": f"{np.sum(confs<=0.50):4d} ({100*np.sum(confs<=0.50)/n:.1f}%)",
    }


def sep(c="=", w=90): print(c * w)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    sep()
    print(f" NEW SESSION INFERENCE — {SESSION_CSV.name}")
    print(f" TensorFlow {tf.__version__}")
    sep()

    X = load_and_preprocess(SESSION_CSV)
    n = len(X)

    results = {}
    for name, model_path in MODELS.items():
        sep("-")
        print(f"  Loading: {name}")
        if not model_path.exists():
            print(f"  [SKIP] Not found: {model_path}")
            continue
        model = tf.keras.models.load_model(model_path)
        print(f"  Input: {model.input_shape}  Output: {model.output_shape}  Params: {model.count_params():,}")
        preds, confs = run_inference(model, X)
        results[name] = {"preds": preds, "confs": confs}
        print(f"  Mean conf: {confs.mean():.3f}  Min: {confs.min():.3f}  Max: {confs.max():.3f}")

    # ── confidence summary ────────────────────────────────────────────────────
    print()
    sep()
    print(" CONFIDENCE SUMMARY")
    sep()
    col_w = 28
    hdr = f"{'Band':<16}" + "".join(f"{n[:col_w-2]:<{col_w}}" for n in results)
    print(hdr); print("-" * len(hdr))
    bands = ["HIGH >90%", "MOD 70-90%", "LOW 50-70%", "UNCERT <50%"]
    bd = {name: confidence_bands(v["confs"]) for name, v in results.items()}
    for b in bands:
        print(f"{b:<16}" + "".join(f"{bd[n][b]:<{col_w}}" for n in results))
    print(f"{'Mean conf':<16}" + "".join(f"{results[n]['confs'].mean():.4f}{'':>{col_w-6}}" for n in results))

    # ── activity distribution ─────────────────────────────────────────────────
    print()
    sep()
    print(f" ACTIVITY DISTRIBUTION  (% of {n} windows)")
    sep()
    hdr2 = f"{'Activity':<22}" + "".join(f"{n[:col_w-2]:<{col_w}}" for n in results)
    print(hdr2); print("-" * len(hdr2))
    for idx, activity in ACTIVITY_CLASSES.items():
        row = f"{activity:<22}"
        for name, v in results.items():
            cnt = int(np.sum(v["preds"] == idx))
            pct = 100 * cnt / n
            cell = f"{cnt:4d} ({pct:5.1f}%)"
            row += f"{cell:<{col_w}}"
        print(row)

    # ── agreement ─────────────────────────────────────────────────────────────
    if len(results) >= 2:
        print()
        sep()
        print(" PAIRWISE PREDICTION AGREEMENT")
        sep()
        names = list(results.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = results[names[i]]["preds"], results[names[j]]["preds"]
                print(f"  {names[i][:30]:30s}  vs  {names[j][:30]:30s}  =>  {np.mean(a==b)*100:.1f}% agree")

    # ── sample windows ────────────────────────────────────────────────────────
    print()
    sep()
    print(" SAMPLE PREDICTIONS — first 10 windows")
    sep()
    hdr3 = f"{'Win':>4}  " + "".join(f"{n[:col_w-2]:<{col_w}}" for n in results)
    print(hdr3); print("-" * len(hdr3))
    for w in range(min(10, n)):
        row = f"{w:>4}  "
        for name, v in results.items():
            act  = ACTIVITY_CLASSES[v["preds"][w]]
            conf = v["confs"][w]
            row += f"{act} ({conf:.2f})   "[:col_w]
        print(row)

    print()
    sep()
    print(" DONE")
    sep()


if __name__ == "__main__":
    main()

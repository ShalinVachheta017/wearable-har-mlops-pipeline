"""
Multi-model inference comparison on production unlabeled data.
Compares: actual model vs retrained (best) vs pseudo-label model.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import tensorflow as tf

# Suppress TF logs
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

ACTIVITY_CLASSES = {
    0: "ear_rubbing",
    1: "forehead_rubbing",
    2: "hair_pulling",
    3: "hand_scratching",
    4: "hand_tapping",
    5: "knuckles_cracking",
    6: "nail_biting",
    7: "nape_rubbing",
    8: "sitting",
    9: "smoking",
    10: "standing",
}

MODELS = {
    "actual_model (fine_tuned_1dcnnbilstm)": PROJECT_ROOT / "models" / "actual model" / "fine_tuned_model_1dcnnbilstm.keras",
    "retrained_best (Mar2026, 92.2%)":       PROJECT_ROOT / "models" / "retrained" / "har_model_20260327_223917.keras",
    "pseudo_label_model":                    PROJECT_ROOT / "models" / "retrained" / "pseudo_label_model.keras",
}

DATA_PATH = PROJECT_ROOT / "data" / "prepared" / "production_X.npy"


def load_data():
    data = np.load(DATA_PATH)
    print(f"Loaded production data: {data.shape}  (windows x timesteps x channels)")
    return data


def run_inference(model, data, batch_size=64):
    probs = model.predict(data, batch_size=batch_size, verbose=0)
    preds = np.argmax(probs, axis=1)
    confs = np.max(probs, axis=1)
    return preds, confs


def confidence_band(confs):
    n = len(confs)
    high    = np.sum(confs > 0.90)
    mod     = np.sum((confs > 0.70) & (confs <= 0.90))
    low     = np.sum((confs > 0.50) & (confs <= 0.70))
    uncert  = np.sum(confs <= 0.50)
    return {
        "HIGH >90%":     f"{high:4d} ({100*high/n:.1f}%)",
        "MOD  70-90%":   f"{mod:4d} ({100*mod/n:.1f}%)",
        "LOW  50-70%":   f"{low:4d} ({100*low/n:.1f}%)",
        "UNCERT <50%":   f"{uncert:4d} ({100*uncert/n:.1f}%)",
    }


def print_separator(char="=", width=80):
    print(char * width)


def main():
    print_separator()
    print(" MULTI-MODEL INFERENCE COMPARISON — Production Unlabeled Data")
    print_separator()
    print(f"Data: {DATA_PATH.name}  |  TensorFlow {tf.__version__}")
    print()

    data = load_data()
    n = len(data)

    results = {}

    for name, model_path in MODELS.items():
        print_separator("-")
        print(f"  Loading: {name}")
        if not model_path.exists():
            print(f"  [SKIP] Model not found: {model_path}")
            continue
        model = tf.keras.models.load_model(model_path)
        in_shape  = model.input_shape
        out_shape = model.output_shape
        params    = model.count_params()
        print(f"  Input: {in_shape}  Output: {out_shape}  Params: {params:,}")

        preds, confs = run_inference(model, data)
        results[name] = {"preds": preds, "confs": confs, "params": params}
        print(f"  Done. Mean confidence: {confs.mean():.3f}  Min: {confs.min():.3f}  Max: {confs.max():.3f}")

    # ---- Summary comparison ------------------------------------------------
    print()
    print_separator()
    print(" CONFIDENCE SUMMARY")
    print_separator()
    header = f"{'Band':<16}" + "".join(f"{n[:22]:<26}" for n in results)
    print(header)
    print("-" * len(header))

    bands = ["HIGH >90%", "MOD  70-90%", "LOW  50-70%", "UNCERT <50%"]
    band_data = {name: confidence_band(v["confs"]) for name, v in results.items()}
    for band in bands:
        row = f"{band:<16}" + "".join(f"{band_data[name][band]:<26}" for name in results)
        print(row)

    print()
    mean_row = f"{'Mean conf':<16}" + "".join(f"{results[n]['confs'].mean():.4f}{'':<20}" for n in results)
    print(mean_row)

    # ---- Activity distribution per model -----------------------------------
    print()
    print_separator()
    print(" ACTIVITY DISTRIBUTION  (% of 3162 windows)")
    print_separator()
    header2 = f"{'Activity':<22}" + "".join(f"{n[:22]:<25}" for n in results)
    print(header2)
    print("-" * len(header2))

    for idx, activity in ACTIVITY_CLASSES.items():
        row = f"{activity:<22}"
        for name, v in results.items():
            count = int(np.sum(v["preds"] == idx))
            pct   = 100 * count / n
            row  += f"{count:4d} ({pct:5.1f}%)          "[:25]
        print(row)

    # ---- Agreement between models ------------------------------------------
    if len(results) >= 2:
        print()
        print_separator()
        print(" PAIRWISE PREDICTION AGREEMENT")
        print_separator()
        names = list(results.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a = results[names[i]]["preds"]
                b = results[names[j]]["preds"]
                agree = np.mean(a == b) * 100
                print(f"  {names[i][:28]:28s}  vs  {names[j][:28]:28s}  =>  {agree:.1f}% agree")

    # ---- Sample windows (first 10) -----------------------------------------
    print()
    print_separator()
    print(" SAMPLE PREDICTIONS — first 10 windows")
    print_separator()
    hdr = f"{'Win':>4}  " + "".join(f"{n[:22]:<28}" for n in results)
    print(hdr)
    print("-" * len(hdr))
    for w in range(min(10, n)):
        row = f"{w:>4}  "
        for name, v in results.items():
            act  = ACTIVITY_CLASSES[v["preds"][w]]
            conf = v["confs"][w]
            cell = f"{act} ({conf:.2f})"
            row += f"{cell:<28}"
        print(row)

    print()
    print_separator()
    print(" DONE")
    print_separator()


if __name__ == "__main__":
    main()

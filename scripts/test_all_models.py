"""
Test every model in the repo against the labeled training dataset.
Uses already-prepared production_X.npy (normalized) + production_y.npy.
Outputs a ranked table: accuracy, F1, dominant class, dead classes.
"""

import os
import sys
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, f1_score, classification_report

LABEL_MAP = {
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
    "pretrained/fine_tuned_1dcnnbilstm":          PROJECT_ROOT / "models/pretrained/fine_tuned_model_1dcnnbilstm.keras",
    "pretrained/current_model":                    PROJECT_ROOT / "models/pretrained/current_model.keras",
    "actual_model/fine_tuned_1dcnnbilstm":         PROJECT_ROOT / "models/actual model/fine_tuned_model_1dcnnbilstm.keras",
    "registry/har_model_vauto":                    PROJECT_ROOT / "models/registry/har_model_vauto.keras",
    "retrained/har_20260327_223917 (Mar27 best)":  PROJECT_ROOT / "models/retrained/har_model_20260327_223917.keras",
    "retrained/har_20260327_213930":               PROJECT_ROOT / "models/retrained/har_model_20260327_213930.keras",
    "retrained/har_20260219_124914":               PROJECT_ROOT / "models/retrained/har_model_20260219_124914.keras",
    "retrained/har_20260219_123616":               PROJECT_ROOT / "models/retrained/har_model_20260219_123616.keras",
    "retrained/best_model":                        PROJECT_ROOT / "models/retrained/best_model.keras",
    "retrained/har_model_latest":                  PROJECT_ROOT / "models/retrained/har_model_latest.keras",
    "retrained/retrained_model":                   PROJECT_ROOT / "models/retrained/retrained_model.keras",
    "retrained/pseudo_label_model":                PROJECT_ROOT / "models/retrained/pseudo_label_model.keras",
    "retrained/adabn_configA":                     PROJECT_ROOT / "models/retrained/adabn_adapted_model_configA_20260329_002340.keras",
    "retrained/adabn_configB":                     PROJECT_ROOT / "models/retrained/adabn_adapted_model_configB_20260329_002515.keras",
    "retrained/adabn_configC":                     PROJECT_ROOT / "models/retrained/adabn_adapted_model_configC_20260329_002638.keras",
    "retrained/adabn_configD":                     PROJECT_ROOT / "models/retrained/adabn_adapted_model_configD_20260328_232204.keras",
    "retrained/adabn_tent_adapted":                PROJECT_ROOT / "models/retrained/adabn_tent_adapted_model.keras",
}

X_PATH = PROJECT_ROOT / "data/prepared/production_X.npy"
Y_PATH = PROJECT_ROOT / "data/prepared/production_y.npy"


def load_data():
    X = np.load(X_PATH)
    y = np.load(Y_PATH)
    print(f"Data: X={X.shape}  y={y.shape}  (mean={X.mean():.3f} std={X.std():.3f})")
    print(f"Label distribution: { {LABEL_MAP[i]: int((y==i).sum()) for i in range(11)} }\n")
    return X, y


def test_model(name, path, X, y):
    if not path.exists():
        return {"name": name, "status": "FILE NOT FOUND"}
    try:
        model = tf.keras.models.load_model(str(path), compile=False)
        probs = model.predict(X, batch_size=64, verbose=0)

        if probs.shape[1] != 11:
            return {"name": name, "status": f"WRONG OUTPUT ({probs.shape[1]} classes, expected 11)"}

        preds = np.argmax(probs, axis=1)
        confs = np.max(probs, axis=1)

        acc   = accuracy_score(y, preds)
        f1    = f1_score(y, preds, average="macro", zero_division=0)
        dom_cls = LABEL_MAP[int(np.bincount(preds).argmax())]
        dom_pct = float(np.bincount(preds).max()) / len(preds) * 100
        dead    = [LABEL_MAP[i] for i in range(11) if i not in preds]
        mean_conf = float(confs.mean())

        return {
            "name": name,
            "status": "OK",
            "accuracy": acc,
            "f1_macro": f1,
            "mean_conf": mean_conf,
            "dominant": f"{dom_cls} ({dom_pct:.1f}%)",
            "dead_classes": len(dead),
            "dead_list": dead,
        }
    except Exception as e:
        return {"name": name, "status": f"ERROR: {e}"}


def print_table(results):
    ok = [r for r in results if r["status"] == "OK"]
    failed = [r for r in results if r["status"] != "OK"]

    ok.sort(key=lambda r: r["accuracy"], reverse=True)

    print("\n" + "="*100)
    print("MODEL COMPARISON — ranked by accuracy on labeled training dataset (normalized input)")
    print("="*100)
    print(f"{'Rank':<5} {'Model':<45} {'Acc%':>6} {'F1%':>6} {'Conf%':>6} {'Dead':>5}  Dominant class")
    print("-"*100)
    for i, r in enumerate(ok, 1):
        print(
            f"{i:<5} {r['name']:<45} {r['accuracy']*100:>5.1f}% "
            f"{r['f1_macro']*100:>5.1f}% "
            f"{r['mean_conf']*100:>5.1f}% "
            f"{r['dead_classes']:>5}  {r['dominant']}"
        )
    print("="*100)

    if failed:
        print("\nFAILED / NOT FOUND:")
        for r in failed:
            print(f"  {r['name']:<45}  {r['status']}")

    print(f"\nBest model: {ok[0]['name']}")
    print(f"  Accuracy : {ok[0]['accuracy']*100:.2f}%")
    print(f"  F1 macro : {ok[0]['f1_macro']*100:.2f}%")
    print(f"  Dead cls : {ok[0]['dead_classes']}  {ok[0]['dead_list']}")

    return ok[0]["name"]


def print_best_detail(best_name, best_result, X, y):
    path = None
    for k, v in MODELS.items():
        if k == best_name:
            path = v
            break
    if path is None or not path.exists():
        return
    print(f"\n--- Per-class detail for best model: {best_name} ---")
    model = tf.keras.models.load_model(str(path), compile=False)
    probs = model.predict(X, batch_size=64, verbose=0)
    preds = np.argmax(probs, axis=1)
    target_names = [LABEL_MAP[i] for i in range(11)]
    print(classification_report(y, preds, target_names=target_names, zero_division=0))


if __name__ == "__main__":
    print("Loading data...")
    X, y = load_data()

    results = []
    for name, path in MODELS.items():
        print(f"  Testing: {name} ...", end=" ", flush=True)
        r = test_model(name, path, X, y)
        if r["status"] == "OK":
            print(f"acc={r['accuracy']*100:.1f}%  f1={r['f1_macro']*100:.1f}%")
        else:
            print(r["status"])
        results.append(r)

    best_name = print_table(results)
    ok = [r for r in results if r["status"] == "OK"]
    ok.sort(key=lambda r: r["accuracy"], reverse=True)
    print_best_detail(best_name, ok[0], X, y)

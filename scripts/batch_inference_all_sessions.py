"""
Batch inference across all 26 unlabeled sessions.
Saves per-session CSVs + aggregate summary to outputs/22 april 2026/
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import tensorflow as tf

# ── config ────────────────────────────────────────────────────────────────────

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SCALER_CFG    = PROJECT_ROOT / "models" / "retrained" / "scaler_config.json"
OUTPUT_DIR    = PROJECT_ROOT / "outputs" / "22 april 2026"

SENSOR_COLS   = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
WINDOW_SIZE   = 200
STEP_SIZE     = 100
MILLIG_TO_MS2 = 0.00981

ACTIVITY_CLASSES = {
    0: "ear_rubbing",    1: "forehead_rubbing", 2: "hair_pulling",
    3: "hand_scratching",4: "hand_tapping",     5: "knuckles_cracking",
    6: "nail_biting",    7: "nape_rubbing",     8: "sitting",
    9: "smoking",       10: "standing",
}

MODEL_SPECS = {
    "actual_model":    PROJECT_ROOT / "models" / "actual model" / "fine_tuned_model_1dcnnbilstm.keras",
    "retrained_best":  PROJECT_ROOT / "models" / "retrained" / "har_model_20260327_223917.keras",
    "pseudo_label":    PROJECT_ROOT / "models" / "retrained" / "pseudo_label_model.keras",
}

SESSION_FILES = sorted(PROCESSED_DIR.glob("fused_2025_*.csv"))


# ── helpers ───────────────────────────────────────────────────────────────────

def load_scaler():
    with open(SCALER_CFG) as f:
        cfg = json.load(f)
    return (
        np.array(cfg["scaler_mean"],  dtype=np.float32),
        np.array(cfg["scaler_scale"], dtype=np.float32),
    )


def preprocess(csv_path: Path, mean: np.ndarray, scale: np.ndarray):
    df   = pd.read_csv(csv_path)
    try:
        data = df[SENSOR_COLS].copy().astype(np.float32).ffill().bfill()
    except (ValueError, KeyError):
        return None

    accel_abs_max = data[["Ax", "Ay", "Az"]].abs().values.max()
    if accel_abs_max > 100:
        data[["Ax", "Ay", "Az"]] *= MILLIG_TO_MS2

    data_norm = (data.values - mean) / scale

    n = len(data_norm)
    windows, idx = [], 0
    while idx + WINDOW_SIZE <= n:
        windows.append(data_norm[idx: idx + WINDOW_SIZE])
        idx += STEP_SIZE

    return np.stack(windows).astype(np.float32) if windows else None


def run_inference(model, X, batch_size=64):
    probs = model.predict(X, batch_size=batch_size, verbose=0)
    preds = np.argmax(probs, axis=1)
    confs = np.max(probs, axis=1)
    return preds, confs, probs


def activity_dist(preds, n):
    return {ACTIVITY_CLASSES[i]: int(np.sum(preds == i)) for i in range(11)}


def conf_stats(confs):
    n = len(confs)
    return {
        "mean_conf":       round(float(confs.mean()), 4),
        "high_pct":        round(100 * float(np.sum(confs > 0.90)) / n, 1),
        "moderate_pct":    round(100 * float(np.sum((confs > 0.70) & (confs <= 0.90))) / n, 1),
        "low_pct":         round(100 * float(np.sum((confs > 0.50) & (confs <= 0.70))) / n, 1),
        "uncertain_pct":   round(100 * float(np.sum(confs <= 0.50)) / n, 1),
        "uncertain_count": int(np.sum(confs <= 0.50)),
    }


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output: {OUTPUT_DIR}")
    print(f"TensorFlow: {tf.__version__}")
    print(f"Sessions: {len(SESSION_FILES)}")
    print()

    # Load scaler once
    mean, scale = load_scaler()

    # Load models once
    models = {}
    for model_name, model_path in MODEL_SPECS.items():
        if not model_path.exists():
            print(f"[SKIP] {model_name}: not found")
            continue
        print(f"Loading {model_name} …")
        models[model_name] = tf.keras.models.load_model(model_path)
        print(f"  Params: {models[model_name].count_params():,}")
    print()

    # Aggregate summary rows
    summary_rows = []

    total_start = time.time()

    for si, csv_path in enumerate(SESSION_FILES, 1):
        session_id = csv_path.stem  # e.g. fused_2025_08_12_17_01_38_50Hz
        print(f"[{si:02d}/{len(SESSION_FILES)}] {session_id}")

        t0 = time.time()
        X = preprocess(csv_path, mean, scale)
        if X is None or len(X) == 0:
            print("  Skipped (no windows)")
            continue

        n_windows = len(X)
        print(f"  Windows: {n_windows}")

        # Per-window results DataFrame
        window_df = pd.DataFrame({"window_id": range(n_windows), "session": session_id})

        session_row = {"session": session_id, "n_windows": n_windows}

        for model_name, model in models.items():
            preds, confs, probs = run_inference(model, X)

            # Per-window columns
            window_df[f"{model_name}_pred"]       = [ACTIVITY_CLASSES[p] for p in preds]
            window_df[f"{model_name}_pred_idx"]   = preds
            window_df[f"{model_name}_confidence"] = confs.round(4)

            # Summary stats
            stats = conf_stats(confs)
            dist  = activity_dist(preds, n_windows)
            top1  = max(dist, key=dist.get)
            top1_pct = round(100 * dist[top1] / n_windows, 1)

            session_row[f"{model_name}_mean_conf"]     = stats["mean_conf"]
            session_row[f"{model_name}_high_pct"]      = stats["high_pct"]
            session_row[f"{model_name}_uncertain_pct"] = stats["uncertain_pct"]
            session_row[f"{model_name}_top_activity"]  = top1
            session_row[f"{model_name}_top_pct"]       = top1_pct
            for act, cnt in dist.items():
                session_row[f"{model_name}_{act}"] = cnt

        # Agreement columns
        model_names = list(models.keys())
        if len(model_names) >= 2:
            for i in range(len(model_names)):
                for j in range(i + 1, len(model_names)):
                    a = window_df[f"{model_names[i]}_pred_idx"].values
                    b = window_df[f"{model_names[j]}_pred_idx"].values
                    agree_pct = round(100 * np.mean(a == b), 1)
                    key = f"agree_{model_names[i]}_vs_{model_names[j]}"
                    session_row[key] = agree_pct

        summary_rows.append(session_row)

        # Save per-session CSV
        out_csv = OUTPUT_DIR / f"{session_id}_predictions.csv"
        window_df.to_csv(out_csv, index=False)

        elapsed = time.time() - t0
        print(f"  Done in {elapsed:.1f}s  → {out_csv.name}")

    # ── aggregate summary ─────────────────────────────────────────────────────
    summary_df = pd.DataFrame(summary_rows)
    summary_path = OUTPUT_DIR / "summary_all_sessions.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"\nSaved summary: {summary_path.name}  ({len(summary_df)} sessions)")

    # ── print aggregate table ─────────────────────────────────────────────────
    total_elapsed = time.time() - total_start
    print(f"\nTotal time: {total_elapsed:.1f}s\n")
    print("=" * 100)
    print(" AGGREGATE — mean_conf | top_activity (%) | uncertain_%")
    print("=" * 100)

    col_w = 38
    hdr = f"{'Session':<38}" + "".join(f"{m[:col_w-2]:<{col_w}}" for m in models)
    print(hdr)
    print("-" * len(hdr))

    for _, row in summary_df.iterrows():
        sess = str(row["session"]).replace("fused_", "").replace("_50Hz", "")[:36]
        line = f"{sess:<38}"
        for m in models:
            mc  = row.get(f"{m}_mean_conf",     "?")
            top = row.get(f"{m}_top_activity",  "?")
            tp  = row.get(f"{m}_top_pct",       "?")
            unc = row.get(f"{m}_uncertain_pct", "?")
            cell = f"conf={mc:.3f} top={top[:12]}({tp:.0f}%) unc={unc:.0f}%"
            line += f"{cell:<{col_w}}"
        print(line)

    print("=" * 100)

    # ── per-model across-session stats ────────────────────────────────────────
    print()
    print("ACROSS ALL SESSIONS — per model")
    print("-" * 60)
    for m in models:
        mc_col  = f"{m}_mean_conf"
        unc_col = f"{m}_uncertain_pct"
        if mc_col in summary_df.columns:
            print(f"  {m}:")
            print(f"    Mean confidence:  {summary_df[mc_col].mean():.4f}  (std {summary_df[mc_col].std():.4f})")
            print(f"    Uncertain% mean:  {summary_df[unc_col].mean():.1f}%")

            # Most predicted activity across all sessions
            act_cols = [f"{m}_{a}" for a in ACTIVITY_CLASSES.values()]
            act_totals = summary_df[act_cols].sum()
            act_totals.index = [c.replace(f"{m}_", "") for c in act_totals.index]
            top = act_totals.idxmax()
            top_pct = 100 * act_totals[top] / act_totals.sum()
            print(f"    Dominant activity: {top} ({top_pct:.1f}% of all windows)")
            print()

    # Save metadata
    meta = {
        "generated": datetime.now().isoformat(),
        "sessions": len(summary_df),
        "total_windows": int(summary_df["n_windows"].sum()),
        "models": list(models.keys()),
        "output_dir": str(OUTPUT_DIR),
    }
    with open(OUTPUT_DIR / "run_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Total windows processed: {summary_df['n_windows'].sum():,}")
    print(f"All results saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

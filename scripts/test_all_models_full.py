"""
Full from-scratch model evaluation — with AND without z-score normalization.
Every preprocessing step is run explicitly. No cached .npy files used.

Usage:
  # Run both variants (default — recommended):
  python scripts/test_all_models_full.py

  # Normalized only:
  python scripts/test_all_models_full.py --normalize

  # Raw only (no normalization):
  python scripts/test_all_models_full.py --no-normalize

Steps:
  1. Load raw CSV
  2. Column rename (ingestion)
  3. Unit detection + conversion (milliG → m/s²)
  4. Z-score normalization  ← controlled by --normalize / --no-normalize
  5. Sliding window creation (200 samples, 50% overlap)
  6. Inference on every model
  7. Evaluation (accuracy, F1, per-class)
  8. Side-by-side comparison table
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, classification_report, f1_score

# ── CONFIG ────────────────────────────────────────────────────────────────────

RAW_CSV     = PROJECT_ROOT / "data" / "all_users_data_labeled.csv"
SCALER_CFG  = PROJECT_ROOT / "data" / "prepared" / "config.json"
WINDOW_SIZE = 200
STEP        = 100   # 50% overlap
BATCH_SIZE  = 64

LABEL_MAP = {
    0: "ear_rubbing",    1: "forehead_rubbing", 2: "hair_pulling",
    3: "hand_scratching", 4: "hand_tapping",    5: "knuckles_cracking",
    6: "nail_biting",    7: "nape_rubbing",     8: "sitting",
    9: "smoking",       10: "standing",
}
CLASS_TO_IDX = {v: k for k, v in LABEL_MAP.items()}
SENSOR_COLS  = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
LABEL_COL    = "activity"
MILLIG_TO_MS2 = 9.80665 / 1000.0

RENAME_MAP = {
    "Ax_w": "Ax", "Ay_w": "Ay", "Az_w": "Az",
    "Gx_w": "Gx", "Gy_w": "Gy", "Gz_w": "Gz",
    "acc_x": "Ax", "acc_y": "Ay", "acc_z": "Az",
    "gyr_x": "Gx", "gyr_y": "Gy", "gyr_z": "Gz",
}

MODELS = {
    "pretrained/fine_tuned_1dcnnbilstm":  "models/pretrained/fine_tuned_model_1dcnnbilstm.keras",
    "pretrained/current_model":           "models/pretrained/current_model.keras",
    "actual_model/fine_tuned_1dcnnbilstm":"models/actual model/fine_tuned_model_1dcnnbilstm.keras",
    "registry/har_model_vauto":           "models/registry/har_model_vauto.keras",
    "retrained/har_20260327_223917":      "models/retrained/har_model_20260327_223917.keras",
    "retrained/har_20260327_213930":      "models/retrained/har_model_20260327_213930.keras",
    "retrained/har_20260219_124914":      "models/retrained/har_model_20260219_124914.keras",
    "retrained/har_20260219_123616":      "models/retrained/har_model_20260219_123616.keras",
    "retrained/best_model":               "models/retrained/best_model.keras",
    "retrained/har_model_latest":         "models/retrained/har_model_latest.keras",
    "retrained/retrained_model":          "models/retrained/retrained_model.keras",
    "retrained/pseudo_label_model":       "models/retrained/pseudo_label_model.keras",
    "retrained/adabn_configA":            "models/retrained/adabn_adapted_model_configA_20260329_002340.keras",
    "retrained/adabn_configB":            "models/retrained/adabn_adapted_model_configB_20260329_002515.keras",
    "retrained/adabn_configC":            "models/retrained/adabn_adapted_model_configC_20260329_002638.keras",
    "retrained/adabn_configD":            "models/retrained/adabn_adapted_model_configD_20260328_232204.keras",
    "retrained/adabn_tent_adapted":       "models/retrained/adabn_tent_adapted_model.keras",
}

# ── PREPROCESSING STEPS ───────────────────────────────────────────────────────

def step1_load_raw():
    print("\n" + "="*70)
    print("STEP 1 — Load raw CSV")
    print("="*70)
    print(f"  File : {RAW_CSV}")
    df = pd.read_csv(RAW_CSV)
    print(f"  Shape: {df.shape}")
    print(f"  Cols : {list(df.columns)}")
    return df


def step2_ingestion(df):
    print("\n" + "="*70)
    print("STEP 2 — Ingestion (column rename + label encode)")
    print("="*70)
    renamed = {}
    for old, new in RENAME_MAP.items():
        if old in df.columns:
            df = df.rename(columns={old: new})
            renamed[old] = new
    print(f"  Renamed      : {renamed if renamed else 'none needed'}")

    missing_sensors = [c for c in SENSOR_COLS if c not in df.columns]
    if missing_sensors:
        raise ValueError(f"MISSING sensor columns after rename: {missing_sensors}")
    if LABEL_COL not in df.columns:
        raise ValueError(f"MISSING label column: '{LABEL_COL}'")

    unknown = set(df[LABEL_COL].unique()) - set(CLASS_TO_IDX.keys())
    if unknown:
        raise ValueError(f"Unknown activity labels in CSV: {unknown}")

    df = df.copy()
    df["label_idx"] = df[LABEL_COL].map(CLASS_TO_IDX)
    print(f"  Rows         : {len(df)}")
    print(f"  Label dist   :")
    for name, idx in sorted(CLASS_TO_IDX.items(), key=lambda x: x[1]):
        print(f"    [{idx:2d}] {name:<22} {(df['label_idx']==idx).sum():>6} rows")
    return df


def step3_unit_detection(df):
    print("\n" + "="*70)
    print("STEP 3 — Unit detection & conversion")
    print("="*70)
    accel_cols = ["Ax", "Ay", "Az"]
    max_abs  = float(df[accel_cols].abs().max().max())
    mean_abs = float(df[accel_cols].abs().mean().mean())
    print(f"  Accel  max_abs={max_abs:.3f}   mean_abs={mean_abs:.3f}")

    if max_abs > 100:
        print(f"  Detected : milliG  → converting to m/s²  (factor={MILLIG_TO_MS2})")
        df = df.copy()
        for c in accel_cols:
            df[c] = df[c] * MILLIG_TO_MS2
        print(f"  After    : max_abs={df[accel_cols].abs().max().max():.3f} m/s²")
        units = "milliG→m/s²"
    elif max_abs < 50:
        print(f"  Detected : m/s²  (max_abs < 50) — no conversion")
        units = "m/s²"
    else:
        print(f"  WARNING  : ambiguous (50–100) — treating as m/s², no conversion")
        units = "ambiguous/m/s²"

    gyro_cols = ["Gx", "Gy", "Gz"]
    print(f"  Gyro   max_abs={df[gyro_cols].abs().max().max():.1f}  "
          f"mean_std={df[gyro_cols].std().mean():.1f}  (assumed deg/s)")
    return df, units


def step4_normalization(df, enabled: bool):
    print("\n" + "="*70)
    print(f"STEP 4 — Z-score normalization  [{'ENABLED' if enabled else 'DISABLED'}]")
    print("="*70)

    raw_vals = df[SENSOR_COLS].values.astype(np.float32)
    if np.isnan(raw_vals).any():
        raise ValueError("NaN values found before normalization.")
    print(f"  Input  — mean={raw_vals.mean():.4f}  std={raw_vals.std():.4f}  "
          f"min={raw_vals.min():.3f}  max={raw_vals.max():.3f}")
    print("  Per-channel input stats:")
    for i, ch in enumerate(SENSOR_COLS):
        col = raw_vals[:, i]
        print(f"    {ch}: mean={col.mean():.4f} std={col.std():.4f} min={col.min():.3f} max={col.max():.3f}")

    if not enabled:
        print("  Skipping normalization — raw values passed to windows.")
        return df

    if not SCALER_CFG.exists():
        raise FileNotFoundError(f"Scaler config not found: {SCALER_CFG}")

    with open(SCALER_CFG) as f:
        cfg = json.load(f)

    mean  = np.array(cfg["scaler_mean"])
    scale = np.array(cfg["scaler_scale"])
    print(f"  Scaler from  : {cfg.get('input_file', 'unknown')}")
    print(f"  Created at   : {cfg.get('created_at', 'unknown')}")
    print(f"  mean  : {np.round(mean,  3)}")
    print(f"  scale : {np.round(scale, 3)}")

    normed = (raw_vals - mean) / scale
    if np.isnan(normed).any():
        raise ValueError("NaN values produced by normalization.")
    print(f"  Output — mean={normed.mean():.4f}  std={normed.std():.4f}  "
          f"min={normed.min():.3f}  max={normed.max():.3f}")
    print("  Per-channel normalized stats:")
    for i, ch in enumerate(SENSOR_COLS):
        col = normed[:, i]
        print(f"    {ch}: mean={col.mean():.4f} std={col.std():.4f} min={col.min():.3f} max={col.max():.3f}")

    df = df.copy()
    for i, col in enumerate(SENSOR_COLS):
        df[col] = normed[:, i]
    return df


def step5_windowing(df):
    print("\n" + "="*70)
    print("STEP 5 — Sliding window creation")
    print("="*70)
    data   = df[SENSOR_COLS].values.astype(np.float32)
    labels = df["label_idx"].values.astype(np.int32)

    X_list, y_list = [], []
    majority_purities = []
    mixed_windows = 0
    start = 0
    while start + WINDOW_SIZE <= len(data):
        X_list.append(data[start : start + WINDOW_SIZE])
        label_slice = labels[start : start + WINDOW_SIZE]
        binc = np.bincount(label_slice, minlength=11)
        majority = int(binc.argmax())
        y_list.append(majority)
        purity = float(binc[majority]) / float(WINDOW_SIZE)
        majority_purities.append(purity)
        if purity < 1.0:
            mixed_windows += 1
        start += STEP

    X = np.stack(X_list)
    y = np.array(y_list)
    print(f"  Windows  : {len(X)}   shape={X.shape}")
    print(f"  mean={X.mean():.4f}  std={X.std():.4f}  min={X.min():.3f}  max={X.max():.3f}")
    print(f"  Label distribution (windows):")
    for idx in range(11):
        print(f"    [{idx:2d}] {LABEL_MAP[idx]:<22} {(y==idx).sum():>5} windows")
    qc = {
        "n_windows": int(len(X)),
        "mixed_windows": int(mixed_windows),
        "mixed_window_pct": float(mixed_windows) * 100.0 / float(len(X)),
        "mean_majority_purity": float(np.mean(majority_purities)),
        "min_majority_purity": float(np.min(majority_purities)),
    }
    print(
        "  Window QC — "
        f"mixed={qc['mixed_windows']}/{qc['n_windows']} ({qc['mixed_window_pct']:.2f}%), "
        f"mean_purity={qc['mean_majority_purity']:.4f}, min_purity={qc['min_majority_purity']:.4f}"
    )
    return X, y, qc

# ── MODEL INFERENCE + EVAL ────────────────────────────────────────────────────

def run_model(name, rel_path, X, y):
    path = PROJECT_ROOT / rel_path
    if not path.exists():
        return {"name": name, "status": "FILE NOT FOUND"}
    try:
        model = tf.keras.models.load_model(str(path), compile=False)
        if model.output_shape[-1] != 11:
            return {"name": name, "status": f"WRONG OUTPUT ({model.output_shape[-1]} classes)"}

        probs = model.predict(X, batch_size=BATCH_SIZE, verbose=0)
        preds = np.argmax(probs, axis=1)
        confs = np.max(probs, axis=1)
        cls_report = classification_report(
            y, preds, labels=list(range(11)), output_dict=True, zero_division=0
        )

        acc    = accuracy_score(y, preds)
        f1     = f1_score(y, preds, average="macro", zero_division=0)
        counts = np.bincount(preds, minlength=11)
        dom_i  = int(counts.argmax())
        dom_pct = counts[dom_i] / len(preds) * 100
        dead    = [LABEL_MAP[i] for i in range(11) if counts[i] == 0]

        return {
            "name": name, "status": "OK",
            "accuracy": acc, "f1_macro": f1,
            "mean_conf": float(confs.mean()),
            "dominant": f"{LABEL_MAP[dom_i]} ({dom_pct:.1f}%)",
            "dead_count": len(dead), "dead_list": dead,
            "preds": preds,
            "class_report": cls_report,
        }
    except Exception as e:
        return {"name": name, "status": f"ERROR: {e}"}

# ── RANKING TABLE ─────────────────────────────────────────────────────────────

def print_single_ranking(results, label):
    ok     = sorted([r for r in results if r["status"] == "OK"],
                    key=lambda r: r["accuracy"], reverse=True)
    failed = [r for r in results if r["status"] != "OK"]

    print(f"\n{'='*105}")
    print(f"RANKING — {label}")
    print(f"{'='*105}")
    print(f"{'#':<4} {'Model':<48} {'Acc%':>6} {'F1%':>6} {'Conf%':>6} {'Dead':>5}  Dominant class")
    print(f"{'-'*105}")
    for i, r in enumerate(ok, 1):
        mark = " ◀ BEST" if i == 1 else ""
        print(f"{i:<4} {r['name']:<48} "
              f"{r['accuracy']*100:>5.1f}% "
              f"{r['f1_macro']*100:>5.1f}% "
              f"{r['mean_conf']*100:>5.1f}% "
              f"{r['dead_count']:>5}  {r['dominant']}{mark}")
    if failed:
        print(f"\n  NOT OK: {[r['name']+' → '+r['status'] for r in failed]}")
    return ok


def print_side_by_side(norm_results, raw_results):
    all_names = list(MODELS.keys())
    norm_map  = {r["name"]: r for r in norm_results}
    raw_map   = {r["name"]: r for r in raw_results}

    print(f"\n\n{'='*120}")
    print("SIDE-BY-SIDE: WITH normalization  vs  WITHOUT normalization")
    print(f"{'='*120}")
    print(f"{'Model':<48}  {'── WITH norm ──':^22}  {'── WITHOUT norm ──':^22}  {'Δ Acc':>7}")
    print(f"{'':48}  {'Acc%':>6} {'F1%':>6} {'Dead':>5}   {'Acc%':>6} {'F1%':>6} {'Dead':>5}")
    print(f"{'-'*120}")

    rows = []
    for name in all_names:
        nr = norm_map.get(name)
        rr = raw_map.get(name)
        n_acc  = nr["accuracy"] if nr and nr["status"] == "OK" else None
        r_acc  = rr["accuracy"] if rr and rr["status"] == "OK" else None
        n_f1   = nr["f1_macro"] if nr and nr["status"] == "OK" else None
        r_f1   = rr["f1_macro"] if rr and rr["status"] == "OK" else None
        n_dead = nr["dead_count"] if nr and nr["status"] == "OK" else None
        r_dead = rr["dead_count"] if rr and rr["status"] == "OK" else None
        delta  = (n_acc - r_acc) * 100 if (n_acc is not None and r_acc is not None) else None
        rows.append((name, n_acc, n_f1, n_dead, r_acc, r_f1, r_dead, delta))

    rows.sort(key=lambda x: (x[1] or 0), reverse=True)

    for name, n_acc, n_f1, n_dead, r_acc, r_f1, r_dead, delta in rows:
        n_str  = f"{n_acc*100:>5.1f}% {n_f1*100:>5.1f}% {n_dead:>5}" if n_acc is not None else f"{'FAIL':>22}"
        r_str  = f"{r_acc*100:>5.1f}% {r_f1*100:>5.1f}% {r_dead:>5}" if r_acc is not None else f"{'FAIL':>22}"
        d_str  = f"{delta:>+6.1f}%" if delta is not None else "     N/A"
        better = " ← norm better" if (delta is not None and delta > 1) else \
                 " ← raw  better" if (delta is not None and delta < -1) else ""
        print(f"{name:<48}  {n_str}    {r_str}   {d_str}{better}")

    print(f"{'='*120}")
    print("Δ Acc = (with_norm − without_norm).  Positive = normalization helps.")

    # best overall
    all_ok = [(name, n_acc, "WITH norm") for (name, n_acc, *_) in rows if n_acc is not None] + \
             [(name, r_acc, "WITHOUT norm") for (name, _, _, _, r_acc, *_) in rows if r_acc is not None]
    if all_ok:
        best = max(all_ok, key=lambda x: x[1])
        print(f"\nOVERALL BEST: [{best[2]}]  {best[0]}  →  accuracy={best[1]*100:.2f}%")

# ── PER-CLASS DETAIL ──────────────────────────────────────────────────────────

def print_best_detail(ok_results, X, label):
    if not ok_results:
        return
    best = ok_results[0]
    name = best["name"]
    path = PROJECT_ROOT / MODELS[name]
    if not path.exists():
        return
    print(f"\n{'='*70}")
    print(f"PER-CLASS DETAIL — {label}")
    print(f"  Model : {name}")
    print("="*70)
    model = tf.keras.models.load_model(str(path), compile=False)
    probs = model.predict(X, batch_size=BATCH_SIZE, verbose=0)
    preds = np.argmax(probs, axis=1)
    tnames = [LABEL_MAP[i] for i in range(11)]
    print(classification_report(Y_GLOBAL, preds, target_names=tnames, zero_division=0))


def save_results_csv(norm_results, raw_results, out_path: Path, mode: str):
    """Save machine-readable comparison table."""
    norm_map = {r["name"]: r for r in norm_results}
    raw_map = {r["name"]: r for r in raw_results}
    names = sorted(set(norm_map.keys()) | set(raw_map.keys()))
    rows = []

    for name in names:
        nr = norm_map.get(name, {})
        rr = raw_map.get(name, {})
        n_acc = nr.get("accuracy")
        r_acc = rr.get("accuracy")
        rows.append(
            {
                "model": name,
                "mode": mode,
                "norm_status": nr.get("status"),
                "norm_accuracy": n_acc,
                "norm_f1_macro": nr.get("f1_macro"),
                "norm_mean_conf": nr.get("mean_conf"),
                "norm_dominant": nr.get("dominant"),
                "norm_dead_count": nr.get("dead_count"),
                "raw_status": rr.get("status"),
                "raw_accuracy": r_acc,
                "raw_f1_macro": rr.get("f1_macro"),
                "raw_mean_conf": rr.get("mean_conf"),
                "raw_dominant": rr.get("dominant"),
                "raw_dead_count": rr.get("dead_count"),
                "delta_acc_norm_minus_raw": (
                    (n_acc - r_acc)
                    if isinstance(n_acc, float) and isinstance(r_acc, float)
                    else None
                ),
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False, encoding="utf-8")
    print(f"\nSaved comparison CSV: {out_path}")


def save_per_class_csv(
    norm_results,
    raw_results,
    y_true_norm,
    y_true_raw,
    norm_qc,
    raw_qc,
    out_path: Path,
):
    rows = []

    def _append_rows(results, y_true, variant_name, qc):
        if y_true is None:
            return
        true_counts = np.bincount(y_true, minlength=11)
        for r in results:
            if r.get("status") != "OK":
                continue
            preds = r.get("preds")
            pred_counts = np.bincount(preds, minlength=11)
            report = r.get("class_report", {})
            for cls_idx in range(11):
                cls_key = str(cls_idx)
                rep = report.get(cls_key, {})
                rows.append(
                    {
                        "variant": variant_name,
                        "model": r["name"],
                        "class_idx": cls_idx,
                        "class_name": LABEL_MAP[cls_idx],
                        "true_count": int(true_counts[cls_idx]),
                        "pred_count": int(pred_counts[cls_idx]),
                        "pred_pct": float(pred_counts[cls_idx]) * 100.0 / float(len(y_true)),
                        "precision": rep.get("precision"),
                        "recall": rep.get("recall"),
                        "f1_score": rep.get("f1-score"),
                        "support": rep.get("support"),
                        "window_count": qc.get("n_windows") if qc else None,
                        "mixed_window_pct": qc.get("mixed_window_pct") if qc else None,
                        "mean_majority_purity": qc.get("mean_majority_purity") if qc else None,
                    }
                )

    _append_rows(norm_results, y_true_norm, "with_normalization", norm_qc)
    _append_rows(raw_results, y_true_raw, "without_normalization", raw_qc)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False, encoding="utf-8")
    print(f"Saved per-class CSV: {out_path}")

# ── MAIN ──────────────────────────────────────────────────────────────────────

Y_GLOBAL = None

def parse_args():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group()
    g.add_argument("--normalize",    dest="mode", action="store_const", const="norm",
                   help="Run normalized variant only")
    g.add_argument("--no-normalize", dest="mode", action="store_const", const="raw",
                   help="Run raw (no normalization) variant only")
    p.add_argument(
        "--data-csv",
        type=str,
        default=str(RAW_CSV),
        help="Path to labeled CSV used for evaluation.",
    )
    p.add_argument(
        "--scaler-config",
        type=str,
        default=str(SCALER_CFG),
        help="Path to scaler config JSON used in normalized mode.",
    )
    p.add_argument(
        "--results-csv",
        type=str,
        default="reports/model_comparison_full_matrix.csv",
        help="Path for machine-readable comparison output CSV.",
    )
    p.add_argument(
        "--per-class-csv",
        type=str,
        default="reports/model_comparison_per_class.csv",
        help="Path for per-class prediction/evaluation output CSV.",
    )
    p.set_defaults(mode="both")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    RAW_CSV = Path(args.data_csv)
    SCALER_CFG = Path(args.scaler_config)

    print("\n" + "█"*70)
    print("  FULL FROM-SCRATCH MODEL EVALUATION")
    print(f"  Mode: {args.mode.upper()}")
    print("  No cached .npy used — every step run explicitly")
    print(f"  Data CSV: {RAW_CSV}")
    print(f"  Scaler  : {SCALER_CFG}")
    print("█"*70)

    # ── shared preprocessing (steps 1–3 are always identical) ──
    df_raw       = step1_load_raw()
    df_ingested  = step2_ingestion(df_raw)
    df_converted, units = step3_unit_detection(df_ingested)

    norm_results = []
    raw_results  = []
    y_true_norm = None
    y_true_raw = None
    norm_qc = None
    raw_qc = None

    # ── WITH normalization ──
    if args.mode in ("norm", "both"):
        print("\n\n" + "▓"*70)
        print("  VARIANT A — WITH Z-SCORE NORMALIZATION")
        print("▓"*70)
        df_norm = step4_normalization(df_converted, enabled=True)
        X_norm, y, qc = step5_windowing(df_norm)
        Y_GLOBAL = y
        y_true_norm = y
        norm_qc = qc

        print(f"\n  Testing {len(MODELS)} models on NORMALIZED data...")
        for name, rel_path in MODELS.items():
            print(f"    {name} ...", end=" ", flush=True)
            r = run_model(name, rel_path, X_norm, y)
            if r["status"] == "OK":
                print(f"acc={r['accuracy']*100:.1f}%  f1={r['f1_macro']*100:.1f}%  dead={r['dead_count']}")
            else:
                print(r["status"])
            norm_results.append(r)

        ok_norm = print_single_ranking(norm_results, "WITH Z-SCORE NORMALIZATION")
        if ok_norm:
            print_best_detail(ok_norm, X_norm, "WITH normalization")

    # ── WITHOUT normalization ──
    if args.mode in ("raw", "both"):
        print("\n\n" + "▓"*70)
        print("  VARIANT B — WITHOUT NORMALIZATION (raw m/s² values)")
        print("▓"*70)
        df_raw2 = step4_normalization(df_converted, enabled=False)
        X_raw, y, qc = step5_windowing(df_raw2)
        Y_GLOBAL = y
        y_true_raw = y
        raw_qc = qc

        print(f"\n  Testing {len(MODELS)} models on RAW data...")
        for name, rel_path in MODELS.items():
            print(f"    {name} ...", end=" ", flush=True)
            r = run_model(name, rel_path, X_raw, y)
            if r["status"] == "OK":
                print(f"acc={r['accuracy']*100:.1f}%  f1={r['f1_macro']*100:.1f}%  dead={r['dead_count']}")
            else:
                print(r["status"])
            raw_results.append(r)

        ok_raw = print_single_ranking(raw_results, "WITHOUT NORMALIZATION (raw values)")
        if ok_raw:
            print_best_detail(ok_raw, X_raw, "WITHOUT normalization")

    # ── side-by-side ──
    if args.mode == "both":
        print_side_by_side(norm_results, raw_results)

    save_results_csv(
        norm_results=norm_results,
        raw_results=raw_results,
        out_path=Path(args.results_csv),
        mode=args.mode,
    )
    save_per_class_csv(
        norm_results=norm_results,
        raw_results=raw_results,
        y_true_norm=y_true_norm,
        y_true_raw=y_true_raw,
        norm_qc=norm_qc,
        raw_qc=raw_qc,
        out_path=Path(args.per_class_csv),
    )

"""
Test model accuracy on training data with ZERO external normalization.
Hypothesis: model was fine-tuned May 2025, before any scaler existed.
Paper (ICTH_16) says NO explicit z-score — just milliG->m/s² + windowing.

Tests:
  A) raw milliG   -> window -> model
  B) m/s²         -> window -> model  (milliG × 0.00980665)
  C) z-score new  -> window -> model  (scaler_train_only.json)
"""

import sys, json, pathlib
import numpy as np
import pandas as pd

REPO = pathlib.Path("d:/study apply/ML Ops/MasterArbeit_MLops")
TF_PYTHON = "C:/Users/shali/anaconda3/envs/thesis-mlops/python.exe"

CSV_PATH   = REPO / "data" / "all_users_data_labeled.csv"
MODEL_PATH = REPO / "models" / "pretrained" / "fine_tuned_model_1dcnnbilstm.keras"
SCALER_NEW = REPO / "data" / "prepared" / "scaler_train_only.json"
LABEL_MAP  = REPO / "data" / "prepared" / "config.json"

ACCEL_COLS = ["Ax_w", "Ay_w", "Az_w"]
GYRO_COLS  = ["Gx_w", "Gy_w", "Gz_w"]
SENSOR_COLS = ACCEL_COLS + GYRO_COLS
LABEL_COL  = "activity"
WINDOW_SIZE = 200
STEP_SIZE   = 100   # 50% overlap
CONV_FACTOR = 0.00980665

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

try:
    import tensorflow as tf
    tf.get_logger().setLevel("ERROR")
except ImportError:
    print("TensorFlow not available — run with thesis-mlops python", file=sys.stderr)
    sys.exit(1)


def window_data(X_arr, y_arr, window_size, step):
    windows, labels = [], []
    for start in range(0, len(X_arr) - window_size + 1, step):
        windows.append(X_arr[start: start + window_size])
        # majority label in window
        chunk = y_arr[start: start + window_size]
        labels.append(np.bincount(chunk).argmax())
    return np.array(windows, dtype=np.float32), np.array(labels, dtype=np.int32)


def load_and_window(df, label_ids, scale_fn=None, name=""):
    arr = df[SENSOR_COLS].values.astype(np.float64)
    if scale_fn is not None:
        arr = scale_fn(arr)
    X, y = window_data(arr, label_ids, WINDOW_SIZE, STEP_SIZE)
    print(f"  [{name}] X shape={X.shape}  X mean={X.mean():.4f}  X std={X.std():.4f}")
    return X, y


def report(preds, y_true, class_names, tag):
    acc = (preds == y_true).mean()
    print(f"\n=== {tag} ===")
    print(f"  Overall accuracy : {acc:.4f}  ({acc*100:.2f}%)")
    dominant_cls = np.bincount(preds).argmax()
    dominant_pct = (preds == dominant_cls).mean()
    print(f"  Dominant class   : {class_names[dominant_cls]} ({dominant_pct*100:.1f}%)")

    # per-class breakdown
    print("  Per-class accuracy:")
    for ci, cname in enumerate(class_names):
        mask = y_true == ci
        if mask.sum() == 0:
            continue
        cls_acc = (preds[mask] == ci).mean()
        print(f"    [{ci:2d}] {cname:<25s}  n={mask.sum():5d}  acc={cls_acc:.3f}")
    return acc


def main():
    print(f"TensorFlow {tf.__version__}")

    # ── Load CSV ──────────────────────────────────────────────────────────────
    print(f"\nLoading {CSV_PATH.name} ...")
    df = pd.read_csv(CSV_PATH)
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)[:12]} ...")

    # Map activity strings -> int labels
    with open(LABEL_MAP) as f:
        cfg = json.load(f)
    act2lbl = cfg["activity_to_label"]
    class_names = [k for k, v in sorted(act2lbl.items(), key=lambda x: x[1])]
    print(f"  Classes ({len(class_names)}): {class_names}")

    df = df[df[LABEL_COL].isin(act2lbl)].copy()
    label_ids = df[LABEL_COL].map(act2lbl).values.astype(np.int32)
    print(f"  Labeled rows: {len(df)}")

    # Detect input unit by magnitude of Ax
    ax_mean = df[ACCEL_COLS[0]].abs().mean()
    print(f"\n  Ax abs-mean = {ax_mean:.2f}  "
          f"{'-> milliG detected' if ax_mean > 10 else '-> m/s² detected'}")
    is_milliG = ax_mean > 10

    # ── Load model ────────────────────────────────────────────────────────────
    print(f"\nLoading model: {MODEL_PATH.name}  ({MODEL_PATH.stat().st_size // 1024} KB)")
    model = tf.keras.models.load_model(str(MODEL_PATH), compile=False)
    print(f"  Input shape : {model.input_shape}")
    print(f"  Output shape: {model.output_shape}")

    # ── Load new scaler ───────────────────────────────────────────────────────
    with open(SCALER_NEW) as f:
        sc = json.load(f)
    sc_mean  = np.array(sc["scaler_mean"],  dtype=np.float64)
    sc_scale = np.array(sc["scaler_scale"], dtype=np.float64)
    print(f"\nNew scaler  mean : {sc_mean}")
    print(f"New scaler scale : {sc_scale}")

    # ── Define scale functions ────────────────────────────────────────────────
    def to_ms2(arr):
        out = arr.copy()
        out[:, :3] *= CONV_FACTOR   # only accel
        return out

    def zscore_new_from_ms2(arr):
        return (arr - sc_mean) / sc_scale

    def zscore_new_from_milliG(arr):
        # convert first then scale
        return zscore_new_from_ms2(to_ms2(arr))

    # ── Run experiments ───────────────────────────────────────────────────────
    results = {}

    BATCH = 512

    def predict(X):
        logits = model.predict(X, batch_size=BATCH, verbose=0)
        return np.argmax(logits, axis=1)

    # A: raw milliG (no conversion, no scaler)
    if is_milliG:
        X_a, y_a = load_and_window(df, label_ids, scale_fn=None, name="raw milliG")
        p_a = predict(X_a)
        results["A_raw_milliG"] = report(p_a, y_a, class_names, "A — raw milliG (no conversion, no scaler)")

    # B: m/s² only (unit conversion, no external scaler)
    scale_b = to_ms2 if is_milliG else None
    X_b, y_b = load_and_window(df, label_ids, scale_fn=scale_b, name="m/s²")
    p_b = predict(X_b)
    results["B_ms2_no_scaler"] = report(p_b, y_b, class_names, "B — m/s² only (no external scaler)")

    # C: m/s² + new z-score scaler
    scale_c = zscore_new_from_ms2 if not is_milliG else zscore_new_from_milliG
    X_c, y_c = load_and_window(df, label_ids, scale_fn=scale_c, name="m/s²+zscore")
    p_c = predict(X_c)
    results["C_ms2_zscore_new"] = report(p_c, y_c, class_names, "C — m/s² + new z-score scaler")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for tag, acc in results.items():
        print(f"  {tag:<30s}  acc={acc:.4f}  ({acc*100:.2f}%)")

    best = max(results, key=results.get)
    print(f"\n  Best preprocessing: {best}  ({results[best]*100:.2f}%)")
    print("\nDone.")


if __name__ == "__main__":
    main()

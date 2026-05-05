"""
Batch inference across all raw accel/gyro pairs.
Run from the nb/ folder:   python batch_inference.py

Produces:
  inference_outputs/batch_comparison.csv   — one row per dataset, all activity stats
  inference_outputs/batch_summary.csv      — compact view: top activities + confidence per run
"""

import ast
import time
from pathlib import Path

import numpy as np
import pandas as pd
import keras

# ---------------------------------------------------------------------------
# CONFIG  (matches gpt.ipynb exactly)
# ---------------------------------------------------------------------------

MODEL_PATH   = Path("fine_tuned_model_1dcnnbilstm.keras")
RAW_DIR      = Path("../data/raw")
OUT_DIR      = Path("inference_outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_HZ    = 50
RESAMPLE_MS  = 20
WINDOW_SIZE  = 200
STRIDE_SIZE  = 100
MERGE_TOL_MS = 1

FEATURE_COLS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]

CLASS_NAMES = [
    "ear_rubbing", "forehead_rubbing", "hair_pulling", "hand_scratching",
    "hand_tapping", "knuckles_cracking", "nail_biting", "nape_rubbing",
    "sitting", "smoking", "standing",
]

HIGH_CONF  = 0.80
MED_CONF   = 0.60
UNCERTAIN  = 0.60

# ---------------------------------------------------------------------------
# PREPROCESSING  (exact copy of gpt.ipynb helpers)
# ---------------------------------------------------------------------------

def _to_list_if_list_like(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        txt = x.strip()
        if txt.startswith("[") and txt.endswith("]"):
            try:
                return ast.literal_eval(txt)
            except Exception:
                return x
    return x


def expand_list_columns(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return df.copy()
    out = df.copy()
    has_list = False
    for c in cols:
        out[c] = out[c].map(_to_list_if_list_like)
        if out[c].map(lambda v: isinstance(v, list)).any():
            has_list = True
    if not has_list:
        return out.reset_index(drop=True)
    for c in cols:
        out[c] = out[c].map(lambda v: v if isinstance(v, list) else [v])
    try:
        out = out.explode(cols, ignore_index=True)
    except ValueError:
        rows = []
        for _, row in out.iterrows():
            max_len = max(len(row[c]) if isinstance(row[c], list) else 1 for c in cols)
            for i in range(max_len):
                new_row = row.copy()
                for c in cols:
                    v = row[c]
                    new_row[c] = v[i] if isinstance(v, list) and i < len(v) else np.nan
                rows.append(new_row)
        out = pd.DataFrame(rows).reset_index(drop=True)
    return out.reset_index(drop=True)


def parse_timestamp_series(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        med = pd.to_numeric(s, errors="coerce").dropna().median()
        if pd.notna(med) and med > 1e12:
            return pd.to_datetime(s, unit="ms", origin="unix", errors="coerce")
        return pd.to_datetime(s, unit="s", origin="unix", errors="coerce")
    return pd.to_datetime(s, errors="coerce")


def parse_prod_sensor_csv(path: Path, sensor_prefix: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    list_like_cols = [
        "sample_time_offset",
        "accel_x", "accel_y", "accel_z",
        "gyro_x", "gyro_y", "gyro_z",
        "calibrated_accel_x", "calibrated_accel_y", "calibrated_accel_z",
        "calibrated_gyro_x", "calibrated_gyro_y", "calibrated_gyro_z",
    ]
    df = expand_list_columns(df, list_like_cols)

    base_ts = parse_timestamp_series(df["timestamp"])
    ts_ms = pd.to_numeric(df.get("timestamp_ms", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
    offset = pd.to_numeric(df.get("sample_time_offset", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
    precise_ts = base_ts + pd.to_timedelta(ts_ms + offset, unit="ms")

    out = pd.DataFrame({"timestamp": precise_ts})

    if sensor_prefix == "accel":
        for cols in [("accel_x","accel_y","accel_z"), ("calibrated_accel_x","calibrated_accel_y","calibrated_accel_z")]:
            if all(c in df.columns for c in cols):
                out["Ax_w"] = pd.to_numeric(df[cols[0]], errors="coerce")
                out["Ay_w"] = pd.to_numeric(df[cols[1]], errors="coerce")
                out["Az_w"] = pd.to_numeric(df[cols[2]], errors="coerce")
                break
        # Auto-detect unit: if median abs > 100, assume milli-g
        med = out[["Ax_w","Ay_w","Az_w"]].abs().stack().median()
        if pd.notna(med) and med > 100:
            out[["Ax_w","Ay_w","Az_w"]] *= 0.00981

    elif sensor_prefix == "gyro":
        for cols in [("gyro_x","gyro_y","gyro_z"), ("calibrated_gyro_x","calibrated_gyro_y","calibrated_gyro_z")]:
            if all(c in df.columns for c in cols):
                out["Gx_w"] = pd.to_numeric(df[cols[0]], errors="coerce")
                out["Gy_w"] = pd.to_numeric(df[cols[1]], errors="coerce")
                out["Gz_w"] = pd.to_numeric(df[cols[2]], errors="coerce")
                break

    return out.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)


def build_production_df(accel_path: Path, gyro_path: Path) -> pd.DataFrame:
    acc = parse_prod_sensor_csv(accel_path, "accel")
    gyr = parse_prod_sensor_csv(gyro_path, "gyro")
    merged = pd.merge_asof(
        acc.sort_values("timestamp"),
        gyr.sort_values("timestamp"),
        on="timestamp", direction="nearest",
        tolerance=pd.Timedelta(milliseconds=MERGE_TOL_MS),
    )
    return merged.dropna(subset=FEATURE_COLS).reset_index(drop=True)


def downsample(df: pd.DataFrame) -> pd.DataFrame:
    out = df.dropna(subset=["timestamp"]).sort_values("timestamp").set_index("timestamp")
    return (
        out.resample(f"{RESAMPLE_MS}ms")
        .agg({c: "mean" for c in FEATURE_COLS})
        .dropna(subset=FEATURE_COLS)
        .reset_index()
    )


def build_windows(df: pd.DataFrame):
    arr = df[FEATURE_COLS].to_numpy(dtype=np.float32)
    X, meta = [], []
    for start in range(0, len(arr) - WINDOW_SIZE + 1, STRIDE_SIZE):
        end = start + WINDOW_SIZE
        X.append(arr[start:end])
        meta.append({"start_time": df.iloc[start]["timestamp"], "end_time": df.iloc[end-1]["timestamp"]})
    return np.asarray(X, dtype=np.float32) if X else np.empty((0, WINDOW_SIZE, len(FEATURE_COLS)), dtype=np.float32), pd.DataFrame(meta)


# ---------------------------------------------------------------------------
# FIND ALL PAIRS
# ---------------------------------------------------------------------------

def find_pairs(raw_dir: Path):
    accel_files = sorted(raw_dir.glob("*accelerometer*.csv"))
    pairs = []
    for af in accel_files:
        stem = af.stem.replace("_accelerometer", "").replace("-accelerometer", "").replace("accelerometer_", "")
        # find matching gyro
        for gf in raw_dir.glob("*gyroscope*.csv"):
            gstem = gf.stem.replace("_gyroscope", "").replace("-gyroscope", "").replace("gyroscope_", "")
            if stem == gstem:
                pairs.append((af, gf))
                break
    return pairs


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def run_inference_on_pair(accel_path, gyro_path, model):
    prod_raw = build_production_df(accel_path, gyro_path)
    prod_ds  = downsample(prod_raw)
    X_prod, meta = build_windows(prod_ds)
    if X_prod.shape[0] == 0:
        return None
    probs = np.asarray(model.predict(X_prod, verbose=0, batch_size=256))
    classes = np.array(CLASS_NAMES)
    top1_idx  = probs.argmax(axis=1)
    top1_conf = probs[np.arange(len(probs)), top1_idx]
    pred_label = classes[top1_idx]
    return pred_label, top1_conf, probs, len(prod_ds), X_prod.shape[0]


def main():
    print("Loading model...")
    model = keras.models.load_model(MODEL_PATH, compile=False)
    print(f"Model ready. Input: {model.input_shape}  Output: {model.output_shape}")

    pairs = find_pairs(RAW_DIR)
    print(f"\nFound {len(pairs)} dataset pairs in {RAW_DIR}\n")

    all_rows = []   # detailed per-activity rows
    summary_rows = []  # one row per dataset

    for accel_path, gyro_path in pairs:
        session = accel_path.stem.replace("_accelerometer", "")
        print(f"  Processing {session} ...", end=" ", flush=True)
        t0 = time.perf_counter()
        try:
            result = run_inference_on_pair(accel_path, gyro_path, model)
            if result is None:
                print("SKIPPED (no windows)")
                continue
            pred_label, top1_conf, probs, n_rows, n_windows = result
            elapsed = round(time.perf_counter() - t0, 2)

            # per-activity stats
            for cls in CLASS_NAMES:
                mask = pred_label == cls
                count = int(mask.sum())
                if count == 0:
                    continue
                confs = top1_conf[mask]
                all_rows.append({
                    "session": session,
                    "activity": cls,
                    "window_count": count,
                    "pct_windows": round(100 * count / n_windows, 1),
                    "mean_confidence": round(float(confs.mean()), 4),
                    "median_confidence": round(float(np.median(confs)), 4),
                    "min_confidence": round(float(confs.min()), 4),
                    "max_confidence": round(float(confs.max()), 4),
                    "high_conf_windows": int((confs >= HIGH_CONF).sum()),
                    "uncertain_windows": int((confs < UNCERTAIN).sum()),
                })

            # summary row — top 4 activities
            vc = pd.Series(pred_label).value_counts()
            top4 = vc.head(4)
            uncertain_pct = round(100 * (top1_conf < UNCERTAIN).mean(), 1)
            mean_conf_all = round(float(top1_conf.mean()), 4)

            srow = {
                "session": session,
                "n_raw_rows": n_rows,
                "n_windows": n_windows,
                "mean_confidence_all": mean_conf_all,
                "uncertain_pct": uncertain_pct,
                "n_classes_detected": int((vc > 5).sum()),
            }
            for rank, (act, cnt) in enumerate(top4.items(), 1):
                mask = pred_label == act
                srow[f"top{rank}_activity"] = act
                srow[f"top{rank}_pct"] = round(100 * cnt / n_windows, 1)
                srow[f"top{rank}_mean_conf"] = round(float(top1_conf[mask].mean()), 4)

            summary_rows.append(srow)
            print(f"{n_windows} windows | mean conf {mean_conf_all} | {elapsed}s")

        except Exception as e:
            print(f"ERROR: {e}")

    # Save
    detail_df  = pd.DataFrame(all_rows)
    summary_df = pd.DataFrame(summary_rows)

    detail_path  = OUT_DIR / "batch_comparison.csv"
    summary_path = OUT_DIR / "batch_summary.csv"
    detail_df.to_csv(detail_path,  index=False)
    summary_df.to_csv(summary_path, index=False)

    print(f"\nSaved: {detail_path}")
    print(f"Saved: {summary_path}")
    print("\n========== BATCH SUMMARY ==========")
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.width", 160)
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()

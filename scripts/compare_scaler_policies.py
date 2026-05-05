"""Compare train-only and all-user scaler policies on the labeled dataset.

This is an evidence script, not a runtime switch. It keeps the defended runtime
scaler unchanged and writes an experimental all-user scaler plus a comparison
report so the thesis can show the effect of fitting the scaler on users 1-4
versus users 1-6.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.label_mapping import get_activity_classes, get_class_to_index


DATA_PATH = PROJECT_ROOT / "data" / "all_users_data_labeled.csv"
TRAIN_ONLY_SCALER = PROJECT_ROOT / "data" / "prepared" / "scaler_train_only.json"
ALL_USERS_SCALER = PROJECT_ROOT / "data" / "prepared" / "scaler_all_users_experimental.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "scaler_policy_comparison_2026-04-27.json"

DEFAULT_MODELS = {
    "defended_runtime": PROJECT_ROOT / "models" / "pretrained" / "fine_tuned_model_1dcnnbilstm.keras",
    "candidate_har_model_latest": PROJECT_ROOT / "models" / "retrained" / "har_model_latest.keras",
}

SENSOR_COLS_RAW = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
SENSOR_COLS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
WINDOW_SIZE = 200
STEP_SIZE = 100
TRAIN_USERS = [1, 2, 3, 4]
VAL_USERS = [5]
TEST_USERS = [6]
ALL_USERS = [1, 2, 3, 4, 5, 6]


def _load_dataset() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing dataset: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH).rename(columns=dict(zip(SENSOR_COLS_RAW, SENSOR_COLS)))
    missing = [c for c in [*SENSOR_COLS, "activity", "User"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    activity_to_label = get_class_to_index()
    unknown = sorted(set(df["activity"].dropna().unique()) - set(activity_to_label.keys()))
    if unknown:
        raise ValueError(f"Unknown activities in labeled dataset: {unknown}")
    df["label_idx"] = df["activity"].map(activity_to_label).astype(int)
    return df


def _fit_all_users_scaler(df: pd.DataFrame) -> Dict:
    fit_df = df[df["User"].isin(ALL_USERS)]
    scaler = StandardScaler().fit(fit_df[SENSOR_COLS].values.astype(np.float32))
    payload = {
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "sensor_cols": SENSOR_COLS,
        "fit_dataset": str(DATA_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "fit_users": ALL_USERS,
        "n_train_rows": int(len(fit_df)),
        "normalization_variant": "zscore",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": "EXPERIMENTAL_ALL_USERS_FINAL_DEPLOYMENT_CANDIDATE",
        "note": (
            "Experimental scaler fit on users 1-6. Useful for final-deployment "
            "normalization comparison only; not leakage-safe for user-holdout metrics."
        ),
    }
    ALL_USERS_SCALER.parent.mkdir(parents=True, exist_ok=True)
    ALL_USERS_SCALER.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _load_scaler(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing scaler: {path}")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if len(cfg.get("scaler_mean", [])) != 6 or len(cfg.get("scaler_scale", [])) != 6:
        raise ValueError(f"Scaler has invalid dimensions: {path}")
    return cfg


def _apply_scaler(df: pd.DataFrame, cfg: Dict) -> pd.DataFrame:
    out = df.copy()
    mean = np.asarray(cfg["scaler_mean"], dtype=np.float32)
    scale = np.asarray(cfg["scaler_scale"], dtype=np.float32)
    raw = out[SENSOR_COLS].values.astype(np.float32)
    out.loc[:, SENSOR_COLS] = (raw - mean) / np.where(scale == 0, 1.0, scale)
    return out


def _window_labeled(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    X_all: List[np.ndarray] = []
    y_all: List[int] = []
    users_all: List[int] = []

    for user_id in sorted(df["User"].dropna().unique()):
        df_u = df[df["User"] == user_id].reset_index(drop=True)
        for activity in df_u["activity"].dropna().unique():
            df_ua = df_u[df_u["activity"] == activity].reset_index(drop=True)
            values = df_ua[SENSOR_COLS].values.astype(np.float32)
            labels = df_ua["label_idx"].values.astype(np.int32)
            for start in range(0, len(df_ua) - WINDOW_SIZE + 1, STEP_SIZE):
                end = start + WINDOW_SIZE
                X_all.append(values[start:end])
                y_all.append(int(np.bincount(labels[start:end]).argmax()))
                users_all.append(int(user_id))

    return np.asarray(X_all), np.asarray(y_all), np.asarray(users_all)


def _evaluate_model(model_path: Path, X: np.ndarray, y: np.ndarray, users: np.ndarray) -> Dict:
    if not model_path.exists():
        return {"available": False, "path": str(model_path)}

    model = tf.keras.models.load_model(str(model_path), compile=False)
    probs = model.predict(X, batch_size=128, verbose=0)
    pred = np.argmax(probs, axis=1)

    splits = {
        "train_users_1_4": np.isin(users, TRAIN_USERS),
        "val_user_5": np.isin(users, VAL_USERS),
        "test_user_6": np.isin(users, TEST_USERS),
        "all_users_1_6": np.isin(users, ALL_USERS),
    }

    result = {
        "available": True,
        "path": str(model_path),
        "input_shape": list(model.input_shape),
        "output_shape": list(model.output_shape),
        "params": int(model.count_params()),
        "splits": {},
    }
    for name, mask in splits.items():
        y_split = y[mask]
        pred_split = pred[mask]
        result["splits"][name] = {
            "n_windows": int(len(y_split)),
            "accuracy": float(accuracy_score(y_split, pred_split)),
            "macro_f1": float(f1_score(y_split, pred_split, average="macro", zero_division=0)),
        }
    return result


def _scalar_diff(a: Dict, b: Dict) -> List[Dict]:
    mean_a = np.asarray(a["scaler_mean"], dtype=float)
    mean_b = np.asarray(b["scaler_mean"], dtype=float)
    scale_a = np.asarray(a["scaler_scale"], dtype=float)
    scale_b = np.asarray(b["scaler_scale"], dtype=float)
    return [
        {
            "channel": SENSOR_COLS[i],
            "train_only_mean": float(mean_a[i]),
            "all_users_mean": float(mean_b[i]),
            "delta_mean": float(mean_b[i] - mean_a[i]),
            "train_only_scale": float(scale_a[i]),
            "all_users_scale": float(scale_b[i]),
            "delta_scale": float(scale_b[i] - scale_a[i]),
        }
        for i in range(len(SENSOR_COLS))
    ]


def _print_summary(report: Dict) -> None:
    print("\nScaler policy comparison")
    print("========================")
    for channel in report["scaler_diff"]:
        print(
            f"{channel['channel']}: "
            f"mean {channel['train_only_mean']:.4f} -> {channel['all_users_mean']:.4f} "
            f"(delta {channel['delta_mean']:+.4f}), "
            f"scale {channel['train_only_scale']:.4f} -> {channel['all_users_scale']:.4f} "
            f"(delta {channel['delta_scale']:+.4f})"
        )

    for scaler_name, scaler_report in report["evaluations"].items():
        print(f"\n{scaler_name}")
        for model_name, model_report in scaler_report.items():
            print(f"  {model_name}")
            if not model_report["available"]:
                print("    unavailable")
                continue
            for split, metrics in model_report["splits"].items():
                print(
                    f"    {split:16s} n={metrics['n_windows']:4d} "
                    f"acc={metrics['accuracy']:.4f} macro_f1={metrics['macro_f1']:.4f}"
                )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args(list(argv) if argv is not None else None)

    df = _load_dataset()
    train_only_cfg = _load_scaler(TRAIN_ONLY_SCALER)
    all_users_cfg = _fit_all_users_scaler(df)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(DATA_PATH),
        "window_size": WINDOW_SIZE,
        "step_size": STEP_SIZE,
        "scalers": {
            "train_only_users_1_4": str(TRAIN_ONLY_SCALER),
            "all_users_1_6_experimental": str(ALL_USERS_SCALER),
        },
        "class_order": get_activity_classes(),
        "scaler_diff": _scalar_diff(train_only_cfg, all_users_cfg),
        "evaluations": {},
        "interpretation": {
            "train_only_users_1_4": (
                "Leakage-safe for validation/test reporting because users 5 and 6 "
                "do not influence preprocessing statistics."
            ),
            "all_users_1_6_experimental": (
                "Valid as a final-deployment normalization candidate after all six "
                "users are accepted into the training corpus; not valid for claiming "
                "unseen-user evaluation on users 5 or 6."
            ),
        },
    }

    for scaler_name, cfg in {
        "train_only_users_1_4": train_only_cfg,
        "all_users_1_6_experimental": all_users_cfg,
    }.items():
        X, y, users = _window_labeled(_apply_scaler(df, cfg))
        report["evaluations"][scaler_name] = {
            model_name: _evaluate_model(model_path, X, y, users)
            for model_name, model_path in DEFAULT_MODELS.items()
        }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _print_summary(report)
    print(f"\nSaved report: {args.report}")
    print(f"Saved experimental scaler: {ALL_USERS_SCALER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

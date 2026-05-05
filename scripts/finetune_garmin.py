"""
Fine-tune the ADAMSense pre-trained model on Garmin Venu 3 labeled data.

Process mirrors ICTH_16 paper:
  1. Load ADAMSense base  (fine_tuned_model_1dcnnbilstm.keras)
  2. Apply canonical z-score scaler (fit on train users 1-4 only)
  3. Fine-tune with low LR (0.0001) and early stopping
  4. Evaluate: train users 1-4, val user 5, test user 6
  5. Save  ->  models/pretrained/garmin_finetuned_v1_<date>.keras

Usage:
    C:/Users/shali/anaconda3/envs/thesis-mlops/python.exe scripts/finetune_garmin.py
    # quick test (no CV, 10 epochs):
    ... scripts/finetune_garmin.py --skip-cv --epochs 10
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("d:/study apply/ML Ops/MasterArbeit_MLops")
sys.path.insert(0, str(REPO))

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, classification_report

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_MODEL   = REPO / "models/pretrained/fine_tuned_model_1dcnnbilstm.keras"
DATA_CSV     = REPO / "data/all_users_data_labeled.csv"
LABEL_MAP    = REPO / "data/prepared/config.json"
OUTPUT_DIR   = REPO / "models/pretrained"

SENSOR_COLS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
LABEL_COL   = "activity"
USER_COL    = "User"
WINDOW_SIZE = 200
STEP_SIZE   = 100   # 50% overlap

TRAIN_USERS = [1, 2, 3, 4]
VAL_USERS   = [5]
TEST_USERS  = [6]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--epochs",   type=int,   default=50)
    p.add_argument("--lr",       type=float, default=0.0001)
    p.add_argument("--batch",    type=int,   default=64)
    p.add_argument("--skip-cv",  action="store_true")
    p.add_argument("--n-folds",  type=int,   default=5)
    return p.parse_args()


def window_user(arr, labels, window_size, step):
    X, y = [], []
    for s in range(0, len(arr) - window_size + 1, step):
        X.append(arr[s:s + window_size])
        chunk = labels[s:s + window_size]
        y.append(Counter(chunk).most_common(1)[0][0])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def build_windows(df, act2lbl):
    X_all, y_all, u_all = [], [], []
    for uid in sorted(df[USER_COL].unique()):
        sub = df[df[USER_COL] == uid].reset_index(drop=True)
        arr = sub[SENSOR_COLS].values.astype(np.float64)
        labels = sub[LABEL_COL].map(act2lbl).values.astype(np.int32)
        Xu, yu = window_user(arr, labels, WINDOW_SIZE, STEP_SIZE)
        X_all.append(Xu)
        y_all.append(yu)
        u_all.extend([uid] * len(yu))
    return (np.concatenate(X_all),
            np.concatenate(y_all),
            np.array(u_all, dtype=np.int32))


def apply_scaler(X_train, X_val, X_test):
    scaler = StandardScaler()
    shape = X_train.shape
    flat_tr = X_train.reshape(-1, shape[-1])
    flat_va = X_val.reshape(-1, X_val.shape[-1])
    flat_te = X_test.reshape(-1, X_test.shape[-1])
    scaler.fit(flat_tr)
    Xs_tr = scaler.transform(flat_tr).reshape(shape).astype(np.float32)
    Xs_va = scaler.transform(flat_va).reshape(X_val.shape).astype(np.float32)
    Xs_te = scaler.transform(flat_te).reshape(X_test.shape).astype(np.float32)
    return Xs_tr, Xs_va, Xs_te, scaler


def compile_for_finetune(model, lr, n_classes):
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=lr),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def get_callbacks(ckpt_path):
    return [
        keras.callbacks.ModelCheckpoint(
            str(ckpt_path), save_best_only=True, monitor="val_accuracy", verbose=1
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=10, restore_best_weights=True, verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6, verbose=1
        ),
    ]


def run_cv(X, y, groups, base_model_path, args, n_classes, class_names):
    from sklearn.model_selection import GroupKFold
    print(f"\n{'='*60}")
    print(f"5-FOLD CROSS-VALIDATION (group=user)")
    print(f"{'='*60}")
    gkf = GroupKFold(n_splits=args.n_folds)
    fold_accs, fold_f1s = [], []
    for fold, (tr_idx, va_idx) in enumerate(gkf.split(X, y, groups)):
        print(f"\n-- Fold {fold+1}/{args.n_folds} --")
        Xtr, ytr = X[tr_idx], y[tr_idx]
        Xva, yva = X[va_idx], y[va_idx]

        scaler = StandardScaler()
        Xtr_s = scaler.fit_transform(Xtr.reshape(-1, 6)).reshape(Xtr.shape).astype(np.float32)
        Xva_s = scaler.transform(Xva.reshape(-1, 6)).reshape(Xva.shape).astype(np.float32)

        model = keras.models.load_model(str(base_model_path), compile=False)
        compile_for_finetune(model, args.lr, n_classes)

        ckpt = REPO / "models/pretrained/_cv_fold_best.keras"
        hist = model.fit(
            Xtr_s, ytr,
            validation_data=(Xva_s, yva),
            epochs=args.epochs,
            batch_size=args.batch,
            callbacks=get_callbacks(ckpt),
            verbose=0,
        )
        model = keras.models.load_model(str(ckpt), compile=False)
        preds = np.argmax(model.predict(Xva_s, batch_size=256, verbose=0), axis=1)
        acc = accuracy_score(yva, preds)
        f1  = f1_score(yva, preds, average="macro", zero_division=0)
        fold_accs.append(acc)
        fold_f1s.append(f1)
        print(f"   Fold {fold+1}: acc={acc:.4f}  f1={f1:.4f}")
        keras.backend.clear_session()

    print(f"\nCV Summary:")
    print(f"  Accuracy: {np.mean(fold_accs):.4f} +/- {np.std(fold_accs):.4f}")
    print(f"  F1 macro: {np.mean(fold_f1s):.4f} +/- {np.std(fold_f1s):.4f}")
    return {"cv_acc_mean": float(np.mean(fold_accs)),
            "cv_acc_std":  float(np.std(fold_accs)),
            "cv_f1_mean":  float(np.mean(fold_f1s)),
            "cv_f1_std":   float(np.std(fold_f1s))}


def main():
    args = parse_args()
    print(f"TensorFlow {tf.__version__}")
    print(f"Fine-tuning: {BASE_MODEL.name}")
    print(f"Data:        {DATA_CSV.name}")
    print(f"LR={args.lr}  epochs={args.epochs}  batch={args.batch}")

    with open(LABEL_MAP) as f:
        act2lbl = json.load(f)["activity_to_label"]
    class_names = [k for k, v in sorted(act2lbl.items(), key=lambda x: x[1])]
    n_classes = len(class_names)
    print(f"Classes ({n_classes}): {class_names}")

    # ── Load and window data ───────────────────────────────────────────────────
    df = pd.read_csv(DATA_CSV)
    df = df[df[LABEL_COL].isin(act2lbl)].copy()
    print(f"\nLoaded {len(df):,} rows, {df[USER_COL].nunique()} users")

    X, y, groups = build_windows(df, act2lbl)
    print(f"Total windows: {X.shape[0]}  shape={X.shape}")

    # ── User holdout split ─────────────────────────────────────────────────────
    tr_mask  = np.isin(groups, TRAIN_USERS)
    val_mask = np.isin(groups, VAL_USERS)
    te_mask  = np.isin(groups, TEST_USERS)

    X_train, y_train = X[tr_mask],  y[tr_mask]
    X_val,   y_val   = X[val_mask], y[val_mask]
    X_test,  y_test  = X[te_mask],  y[te_mask]

    print(f"\nSplit: train={len(X_train)} (u{TRAIN_USERS})"
          f"  val={len(X_val)} (u{VAL_USERS})"
          f"  test={len(X_test)} (u{TEST_USERS})")

    X_tr_s, X_va_s, X_te_s, scaler = apply_scaler(X_train, X_val, X_test)
    print(f"Scaler fit on train users. X_train after scaling: "
          f"mean={X_tr_s.mean():.4f}  std={X_tr_s.std():.4f}")

    # ── Optional cross-validation ─────────────────────────────────────────────
    cv_results = {}
    if not args.skip_cv:
        cv_results = run_cv(X, y, groups, BASE_MODEL, args, n_classes, class_names)

    # ── Final fine-tuning on all train users ──────────────────────────────────
    print(f"\n{'='*60}")
    print("FINAL FINE-TUNING (train=u1-4, val=u5, test=u6)")
    print(f"{'='*60}")

    date_tag = datetime.now().strftime("%Y%m%d")
    out_name = f"garmin_finetuned_v1_{date_tag}.keras"
    ckpt_path = OUTPUT_DIR / "_finetune_best.keras"

    model = keras.models.load_model(str(BASE_MODEL), compile=False)
    print(f"Loaded base model  params={model.count_params():,}")
    compile_for_finetune(model, args.lr, n_classes)

    history = model.fit(
        X_tr_s, y_train,
        validation_data=(X_va_s, y_val),
        epochs=args.epochs,
        batch_size=args.batch,
        callbacks=get_callbacks(ckpt_path),
        verbose=1,
    )

    # Reload best checkpoint
    model = keras.models.load_model(str(ckpt_path), compile=False)

    # ── Evaluation ────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("EVALUATION")
    print(f"{'='*60}")
    for split_name, Xs, ys in [("Val (user 5)", X_va_s, y_val),
                                ("Test (user 6)", X_te_s, y_test)]:
        preds = np.argmax(model.predict(Xs, batch_size=256, verbose=0), axis=1)
        acc = accuracy_score(ys, preds)
        f1  = f1_score(ys, preds, average="macro", zero_division=0)
        print(f"\n{split_name}:  acc={acc:.4f}  f1_macro={f1:.4f}")
        print(classification_report(ys, preds, target_names=class_names, zero_division=0))

    # ── Save fine-tuned model ─────────────────────────────────────────────────
    save_path = OUTPUT_DIR / out_name
    model.save(str(save_path))
    print(f"\nSaved fine-tuned model -> {save_path}")
    print(f"Size: {save_path.stat().st_size // 1024} KB")

    # Save report
    report = {
        "created_at": datetime.now().isoformat(),
        "base_model": str(BASE_MODEL),
        "training_data": str(DATA_CSV),
        "train_users": TRAIN_USERS,
        "val_users": VAL_USERS,
        "test_users": TEST_USERS,
        "n_train_windows": int(len(X_train)),
        "epochs_config": args.epochs,
        "lr": args.lr,
        "batch_size": args.batch,
        "cv_results": cv_results,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "sensor_cols": SENSOR_COLS,
        "class_names": class_names,
        "output_model": out_name,
        "note": "Fine-tuned from ADAMSense base (ICTH_16 protocol). "
                "Use garmin_finetuned_v1_<date>.keras + this scaler for inference.",
    }
    report_path = OUTPUT_DIR / out_name.replace(".keras", "_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved report       -> {report_path.name}")

    print(f"\nDONE. To deploy:")
    print(f"  copy models/pretrained/{out_name} models/pretrained/current_model.keras")
    print(f"  Update scaler_train_only.json with the scaler stats in {report_path.name}")


if __name__ == "__main__":
    main()

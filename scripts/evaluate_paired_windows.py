"""Evaluate a Keras HAR model on an explicitly paired X/y window set."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.label_mapping import get_activity_classes


DEFAULT_X = (
    PROJECT_ROOT
    / "data"
    / "prepared"
    / "paired_windows"
    / "all_users_data_labeled_users_6_canonical_scaled_X.npy"
)
DEFAULT_Y = (
    PROJECT_ROOT
    / "data"
    / "prepared"
    / "paired_windows"
    / "all_users_data_labeled_users_6_canonical_scaled_y.npy"
)
DEFAULT_MODEL = PROJECT_ROOT / "models" / "pretrained" / "fine_tuned_model_1dcnnbilstm.keras"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--x", type=Path, default=DEFAULT_X)
    parser.add_argument("--y", type=Path, default=DEFAULT_Y)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    if not args.x.exists():
        raise FileNotFoundError(f"Missing X file: {args.x}")
    if not args.y.exists():
        raise FileNotFoundError(f"Missing y file: {args.y}")
    if not args.model.exists():
        raise FileNotFoundError(f"Missing model file: {args.model}")

    X = np.load(args.x)
    y = np.load(args.y)
    if len(X) != len(y):
        raise ValueError(f"Refusing to evaluate mismatched arrays: len(X)={len(X)} len(y)={len(y)}")
    if X.ndim != 3 or X.shape[1:] != (200, 6):
        raise ValueError(f"Expected X shape (N, 200, 6), got {X.shape}")

    import tensorflow as tf

    model = tf.keras.models.load_model(str(args.model), compile=False)
    probs = model.predict(X, batch_size=args.batch_size, verbose=0)
    pred = probs.argmax(axis=1)

    label_to_activity = get_activity_classes()
    labels = list(range(len(label_to_activity)))
    target_names = [label_to_activity[i] for i in labels]

    acc = float(accuracy_score(y, pred))
    f1 = float(f1_score(y, pred, average="macro", zero_division=0))
    conf = float(probs.max(axis=1).mean())
    cm = confusion_matrix(y, pred, labels=labels)

    print("Paired-window evaluation")
    print(f"  X:     {args.x}  shape={X.shape}")
    print(f"  y:     {args.y}  shape={y.shape}")
    print(f"  model: {args.model}")
    print(f"  accuracy:        {acc:.4f}")
    print(f"  f1_macro:        {f1:.4f}")
    print(f"  mean confidence: {conf:.4f}")
    print("\nClassification report:")
    print(
        classification_report(
            y,
            pred,
            labels=labels,
            target_names=target_names,
            zero_division=0,
        )
    )
    print("Confusion matrix rows=true, cols=pred:")
    print(cm)

    if args.out:
        payload = {
            "x": str(args.x),
            "y": str(args.y),
            "model": str(args.model),
            "x_shape": list(X.shape),
            "y_shape": list(y.shape),
            "accuracy": acc,
            "f1_macro": f1,
            "mean_confidence": conf,
            "confusion_matrix": cm.tolist(),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nSaved: {args.out}")


if __name__ == "__main__":
    main()

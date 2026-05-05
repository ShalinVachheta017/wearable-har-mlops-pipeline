"""Retrain with user-holdout protocol without MLflow run orchestration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.train import HARTrainer, TrainingConfig
from src.utils.scaler import CANONICAL_SCALER_PATH, assert_scaler_integrity


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--learning-rate", type=float, default=0.001)
    p.add_argument(
        "--data",
        type=str,
        default="data/all_users_data_labeled.csv",
    )
    p.add_argument(
        "--output-dir",
        type=str,
        default="models/retrained",
    )
    p.add_argument(
        "--summary-out",
        type=str,
        default="reports/retrain_user_holdout_summary.json",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    assert_scaler_integrity(CANONICAL_SCALER_PATH)

    config = TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        output_dir=Path(args.output_dir),
        experiment_name="har-training-user-holdout-offline",
    )
    trainer = HARTrainer(config)

    df = trainer.data_loader.load_training_data(Path(args.data))
    X, y, groups = trainer.data_loader.prepare_data(df)
    _, metrics = trainer.train_final_model(X, y, groups, save_artifacts=True)

    summary = {
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "data": str(args.data),
        "output_dir": str(args.output_dir),
        "metrics": metrics,
    }
    out = Path(args.summary_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

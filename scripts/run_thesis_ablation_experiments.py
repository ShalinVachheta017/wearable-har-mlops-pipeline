"""Run thesis-safe preprocessing and drift-monitor ablation experiments.

This script intentionally keeps Z-score normalization and MMD in separate
methodological roles:

Experiment A:
    preprocessing variants with a fixed retained model and fixed input data.

Experiment B:
    drift-detector variants with preprocessing fixed to the z-score baseline.

The script writes thesis-usable CSV/JSON summaries and optional plots under
outputs/thesis_ablation_experiments/.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.metrics import accuracy_score, f1_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_MODEL_PATH  # noqa: E402
from src.preprocess_data import PreprocessLogger, UnifiedPreprocessor, UnitDetector  # noqa: E402
from src.utils.label_mapping import get_activity_classes, get_class_to_index  # noqa: E402


SENSOR_COLUMNS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
DEFAULT_DATASETS = [
    "reference_labeled=data/synthetic_runs/all_users_data_labeled_actual_input.csv",
    "synthetic_codex_labeled=data/synthetic_runs/synthetic_codex_input.csv",
    "synthetic_other_labeled=data/synthetic_runs/synthetic_other_input.csv",
    "synthetic_codex_unlabeled=data/synthetic_runs/synthetic_codex_input_unlabeled.csv",
]


@dataclass
class DatasetSpec:
    name: str
    path: Path


@dataclass
class WindowBundle:
    dataset: str
    variant: str
    X: np.ndarray
    y: Optional[np.ndarray]
    data_format: str
    sensor_columns: List[str]
    unit_conversion_applied: bool
    n_rows: int
    n_windows: int


def _project_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _parse_dataset_specs(items: Iterable[str]) -> List[DatasetSpec]:
    specs: List[DatasetSpec] = []
    for raw in items:
        if "=" not in raw:
            path = _project_path(raw)
            name = path.stem
        else:
            name, path_raw = raw.split("=", 1)
            path = _project_path(path_raw)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")
        specs.append(DatasetSpec(name=name.strip(), path=path))
    return specs


def _make_logger(output_dir: Path) -> logging.Logger:
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("thesis_ablation")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    file_handler = logging.FileHandler(output_dir / "experiment.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    return logger


def _read_csv(path: Path, max_rows: int) -> pd.DataFrame:
    nrows = None if max_rows <= 0 else max_rows
    return pd.read_csv(path, nrows=nrows)


def _load_zscore_scaler(path: Path) -> Dict[str, np.ndarray]:
    with path.open("r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    return {
        "mean": np.asarray(cfg["scaler_mean"], dtype=np.float64),
        "scale": np.asarray(cfg["scaler_scale"], dtype=np.float64),
        "source": str(path),
    }


def _detect_and_convert_units(
    df: pd.DataFrame,
    sensor_cols: List[str],
    logger: logging.Logger,
) -> Tuple[pd.DataFrame, bool]:
    accel_cols = [c for c in sensor_cols if c in {"Ax", "Ay", "Az", "Ax_w", "Ay_w", "Az_w"}]
    detector = UnitDetector(logger)
    return detector.process_units(df, accel_cols)


def _normalise(
    df: pd.DataFrame,
    sensor_cols: List[str],
    variant: str,
    zscore: Dict[str, np.ndarray],
    robust: Dict[str, np.ndarray],
) -> pd.DataFrame:
    out = df.copy()
    values = out[sensor_cols].astype(np.float64)
    if variant == "zscore":
        out[sensor_cols] = (values - zscore["mean"]) / (zscore["scale"] + 1e-12)
    elif variant == "none":
        out[sensor_cols] = values
    elif variant == "robust":
        out[sensor_cols] = (values - robust["center"]) / (robust["scale"] + 1e-12)
    else:
        raise ValueError(f"Unknown normalization variant: {variant}")
    return out


def _fit_robust_scaler(
    reference_csv: Path,
    max_rows: int,
    logger: logging.Logger,
) -> Dict[str, np.ndarray]:
    df = _read_csv(reference_csv, max_rows)
    prep_logger = PreprocessLogger("ablation_robust_scaler").get_logger()
    prep = UnifiedPreprocessor(logger=prep_logger)
    data_format, sensor_cols = prep.detect_data_format(df)
    if data_format not in {"labeled", "unlabeled"}:
        raise ValueError(f"Unsupported reference data format: {data_format}")
    df, _ = _detect_and_convert_units(df, sensor_cols, logger)
    q25 = df[sensor_cols].quantile(0.25).to_numpy(dtype=np.float64)
    q50 = df[sensor_cols].quantile(0.50).to_numpy(dtype=np.float64)
    q75 = df[sensor_cols].quantile(0.75).to_numpy(dtype=np.float64)
    scale = q75 - q25
    scale = np.where(np.abs(scale) < 1e-12, 1.0, scale)
    return {
        "center": q50,
        "scale": scale,
        "source": str(reference_csv),
        "fit_note": (
            "RobustScaler parameters fitted from the reference replay source for "
            "ablation only. The retained model was not retrained on robust-scaled data."
        ),
    }


def _prepare_windows(
    spec: DatasetSpec,
    variant: str,
    max_rows: int,
    zscore: Dict[str, np.ndarray],
    robust: Dict[str, np.ndarray],
    logger: logging.Logger,
) -> WindowBundle:
    df = _read_csv(spec.path, max_rows)
    prep_logger = PreprocessLogger(f"ablation_{spec.name}_{variant}").get_logger()
    prep = UnifiedPreprocessor(logger=prep_logger)
    data_format, sensor_cols = prep.detect_data_format(df)
    df, converted = _detect_and_convert_units(df, sensor_cols, logger)
    df = _normalise(df, sensor_cols, variant, zscore, robust)

    if data_format == "labeled" and "activity" in df.columns:
        activity_to_label = get_class_to_index()
        prep.activity_to_label = activity_to_label
        prep.label_to_activity = {v: k for k, v in activity_to_label.items()}

    X, y, _metadata = prep.create_windows(df, sensor_cols, data_format)
    return WindowBundle(
        dataset=spec.name,
        variant=variant,
        X=X,
        y=y,
        data_format=data_format,
        sensor_columns=list(sensor_cols),
        unit_conversion_applied=converted,
        n_rows=len(df),
        n_windows=int(X.shape[0]),
    )


def _load_model(model_path: Path):
    import tensorflow as tf

    return tf.keras.models.load_model(str(model_path))


def _predict(model: Any, X: np.ndarray, batch_size: int) -> Tuple[np.ndarray, np.ndarray]:
    probabilities = model.predict(X, batch_size=batch_size, verbose=0)
    predicted = np.argmax(probabilities, axis=1)
    return predicted.astype(int), probabilities


def _entropy(probabilities: np.ndarray) -> np.ndarray:
    p = np.clip(probabilities, 1e-12, 1.0)
    return -np.sum(p * np.log(p), axis=1)


def _transition_rate(predicted: np.ndarray) -> float:
    if len(predicted) <= 1:
        return 0.0
    return float(100.0 * np.mean(predicted[1:] != predicted[:-1]))


def _prediction_summary(
    bundle: WindowBundle,
    predicted: np.ndarray,
    probabilities: np.ndarray,
) -> Dict[str, Any]:
    class_names = get_activity_classes()
    conf = probabilities.max(axis=1)
    counts = pd.Series(predicted).value_counts()
    dominant_class_id = int(counts.index[0]) if len(counts) else -1
    dominant_pct = float(100.0 * counts.iloc[0] / len(predicted)) if len(predicted) else 0.0
    row: Dict[str, Any] = {
        "experiment": "preprocessing_ablation",
        "dataset": bundle.dataset,
        "normalization_variant": bundle.variant,
        "data_format": bundle.data_format,
        "n_rows": bundle.n_rows,
        "n_windows": bundle.n_windows,
        "unit_conversion_applied": bundle.unit_conversion_applied,
        "mean_confidence": float(np.mean(conf)),
        "std_confidence": float(np.std(conf)),
        "uncertain_pct": float(100.0 * np.mean(conf < 0.50)),
        "mean_entropy": float(np.mean(_entropy(probabilities))),
        "dominant_class": class_names.get(dominant_class_id, f"class_{dominant_class_id}"),
        "dominant_pct": dominant_pct,
        "unique_predicted_classes": int(len(np.unique(predicted))),
        "transition_rate_pct": _transition_rate(predicted),
    }
    if bundle.y is not None:
        labels = list(range(len(class_names)))
        row["accuracy"] = float(accuracy_score(bundle.y, predicted))
        row["macro_f1"] = float(
            f1_score(bundle.y, predicted, labels=labels, average="macro", zero_division=0)
        )
    else:
        row["accuracy"] = math.nan
        row["macro_f1"] = math.nan
    return row


def _write_predictions(
    output_path: Path,
    bundle: WindowBundle,
    predicted: np.ndarray,
    probabilities: np.ndarray,
) -> None:
    class_names = get_activity_classes()
    conf = probabilities.max(axis=1)
    df = pd.DataFrame(
        {
            "window_id": np.arange(len(predicted)),
            "predicted_class": predicted,
            "predicted_activity": [class_names.get(int(i), f"class_{int(i)}") for i in predicted],
            "confidence": conf,
            "is_uncertain": conf < 0.50,
        }
    )
    if bundle.y is not None:
        df["true_class"] = bundle.y
        df["true_activity"] = [class_names.get(int(i), f"class_{int(i)}") for i in bundle.y]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def _window_features(X: np.ndarray) -> np.ndarray:
    means = X.mean(axis=1)
    stds = X.std(axis=1)
    return np.concatenate([means, stds], axis=1).astype(np.float64)


def _sample_rows(arr: np.ndarray, n: int, rng: np.random.Generator, replace: bool = False) -> np.ndarray:
    if len(arr) == 0:
        raise ValueError("Cannot sample from an empty array.")
    replace = replace or len(arr) < n
    idx = rng.choice(len(arr), size=n, replace=replace)
    return arr[idx]


def _sq_dists(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a2 = np.sum(a * a, axis=1)[:, None]
    b2 = np.sum(b * b, axis=1)[None, :]
    d = a2 + b2 - 2.0 * (a @ b.T)
    return np.maximum(d, 0.0)


def _median_bandwidth(x: np.ndarray) -> float:
    d = _sq_dists(x, x)
    vals = d[np.triu_indices_from(d, k=1)]
    vals = vals[vals > 1e-12]
    if len(vals) == 0:
        return 1.0
    return float(np.sqrt(np.median(vals)))


def _mmd2_rbf(x: np.ndarray, y: np.ndarray, bandwidth: float) -> float:
    gamma = 1.0 / (2.0 * bandwidth * bandwidth + 1e-12)
    kxx = np.exp(-gamma * _sq_dists(x, x)).mean()
    kyy = np.exp(-gamma * _sq_dists(y, y)).mean()
    kxy = np.exp(-gamma * _sq_dists(x, y)).mean()
    return float(max(kxx + kyy - 2.0 * kxy, 0.0))


def _standardise_by_reference(
    reference: np.ndarray,
    current: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    center = reference.mean(axis=0)
    scale = reference.std(axis=0)
    scale = np.where(scale < 1e-12, 1.0, scale)
    return (reference - center) / scale, (current - center) / scale


def _mmd_detector(
    reference_features: np.ndarray,
    current_features: np.ndarray,
    sample_size: int,
    bootstrap: int,
    rng: np.random.Generator,
) -> Dict[str, Any]:
    ref_z, cur_z = _standardise_by_reference(reference_features, current_features)
    n = int(min(sample_size, max(32, len(ref_z)), max(32, len(cur_z))))
    ref_sample = _sample_rows(ref_z, n, rng)
    cur_sample = _sample_rows(cur_z, n, rng)
    bw = _median_bandwidth(np.vstack([ref_sample, cur_sample]))
    score = _mmd2_rbf(ref_sample, cur_sample, bw)

    null_scores = []
    for _ in range(max(bootstrap, 1)):
        a = _sample_rows(ref_z, n, rng)
        b = _sample_rows(ref_z, n, rng)
        null_scores.append(_mmd2_rbf(a, b, bw))
    threshold = float(np.quantile(null_scores, 0.95))
    return {
        "detector": "mmd",
        "drift_score": score,
        "threshold": threshold,
        "status": "WARNING" if score > threshold else "HEALTHY",
        "bandwidth": bw,
        "sample_size": n,
        "bootstrap_iterations": int(max(bootstrap, 1)),
        "threshold_method": "95th percentile of reference-vs-reference bootstrap MMD scores",
    }


def _zscore_detector(X: np.ndarray, baseline_path: Path, threshold: float) -> Dict[str, Any]:
    with baseline_path.open("r", encoding="utf-8") as fh:
        baseline = json.load(fh)
    prod_mean = X.mean(axis=(0, 1))
    baseline_mean = np.asarray(baseline["mean"], dtype=np.float64)
    baseline_std = np.asarray(baseline["std"], dtype=np.float64)
    z = np.abs(prod_mean - baseline_mean) / (baseline_std + 1e-12)
    return {
        "detector": "current_zscore",
        "drift_score": float(np.max(z)),
        "threshold": float(threshold),
        "status": "WARNING" if float(np.max(z)) > threshold else "HEALTHY",
        "n_drifted_channels_gt_1sigma": int(np.sum(z > 1.0)),
        "per_channel_zscore": z.tolist(),
        "threshold_method": "fixed Stage 6 drift_zscore_threshold",
    }


def _ks_detector(
    reference_features: np.ndarray,
    current_features: np.ndarray,
    p_threshold: float = 0.01,
) -> Dict[str, Any]:
    ref_z, cur_z = _standardise_by_reference(reference_features, current_features)
    stats = []
    pvalues = []
    for i in range(ref_z.shape[1]):
        res = ks_2samp(ref_z[:, i], cur_z[:, i])
        stats.append(float(res.statistic))
        pvalues.append(float(res.pvalue))
    n_sig = int(np.sum(np.asarray(pvalues) < p_threshold))
    return {
        "detector": "ks",
        "drift_score": float(np.max(stats)),
        "threshold": float(p_threshold),
        "status": "WARNING" if n_sig > 0 else "HEALTHY",
        "n_significant_features": n_sig,
        "min_pvalue": float(np.min(pvalues)),
        "threshold_method": "per-window-feature KS test, warning if any p < threshold",
    }


def _none_detector() -> Dict[str, Any]:
    return {
        "detector": "none",
        "drift_score": math.nan,
        "threshold": math.nan,
        "status": "SKIPPED",
        "threshold_method": "drift detector disabled for ablation",
    }


def _save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)


def _plot_outputs(pre_df: pd.DataFrame, drift_df: pd.DataFrame, output_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return

    plot_dir = output_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    for metric in ["mean_confidence", "dominant_pct", "unique_predicted_classes", "macro_f1"]:
        if metric not in pre_df.columns:
            continue
        pivot = pre_df.pivot(index="dataset", columns="normalization_variant", values=metric)
        ax = pivot.plot(kind="bar", figsize=(10, 5))
        ax.set_title(f"Preprocessing ablation: {metric}")
        ax.set_ylabel(metric)
        ax.legend(title="normalization")
        plt.tight_layout()
        plt.savefig(plot_dir / f"preprocessing_{metric}.png", dpi=160)
        plt.close()

    plot_df = drift_df[drift_df["detector"] != "none"].copy()
    if not plot_df.empty:
        pivot = plot_df.pivot(index="dataset", columns="detector", values="drift_score")
        ax = pivot.plot(kind="bar", figsize=(10, 5))
        ax.set_title("Drift-monitor ablation: detector score by dataset")
        ax.set_ylabel("detector score")
        ax.legend(title="detector")
        plt.tight_layout()
        plt.savefig(plot_dir / "drift_detector_scores.png", dpi=160)
        plt.close()


def _write_markdown_summary(
    output_dir: Path,
    args: argparse.Namespace,
    pre_df: pd.DataFrame,
    drift_df: pd.DataFrame,
) -> None:
    lines: List[str] = []
    lines.append("# Thesis Ablation Experiment Summary")
    lines.append("")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "These experiments keep Z-score normalization and MMD in separate methodological "
        "roles. Z-score is evaluated as a preprocessing choice; MMD is evaluated as a "
        "batch-level drift-monitoring signal."
    )
    lines.append("")
    lines.append("## Setup")
    lines.append("")
    lines.append(f"- Model: `{Path(args.model).as_posix()}`")
    lines.append(f"- Max rows per dataset: `{args.max_rows if args.max_rows > 0 else 'all'}`")
    lines.append("- Preprocessing variants: `" + "`, `".join(args.preprocessing_variants) + "`")
    lines.append("- Drift detectors: `" + "`, `".join(args.drift_detectors) + "`")
    lines.append("")
    lines.append("## Experiment A - Preprocessing Ablation")
    lines.append("")
    lines.append(
        "Question: how strongly does normalization choice affect model behavior under the "
        "same retained model and the same input rows?"
    )
    lines.append("")
    cols = [
        "dataset",
        "normalization_variant",
        "n_windows",
        "mean_confidence",
        "uncertain_pct",
        "dominant_class",
        "dominant_pct",
        "unique_predicted_classes",
        "transition_rate_pct",
        "accuracy",
        "macro_f1",
    ]
    lines.append(pre_df[cols].round(4).to_markdown(index=False))
    lines.append("")
    lines.append("Thesis-safe interpretation:")
    lines.append("")
    lines.append(
        "- Differences between variants support the claim that preprocessing is not a "
        "cosmetic step. It can change confidence, class concentration, temporal behavior, "
        "and labeled metrics."
    )
    lines.append(
        "- The z-score variant is the train-serve parity baseline because the retained "
        "model was trained with StandardScaler-style normalization."
    )
    lines.append(
        "- The `none` and `robust` variants are ablations with the same retained model; "
        "they should not be interpreted as final production alternatives unless the model "
        "is retrained under matching preprocessing."
    )
    lines.append("")
    lines.append("## Experiment B - Drift-Monitor Ablation")
    lines.append("")
    lines.append(
        "Question: does MMD add a useful batch-level distribution signal compared with the "
        "current lightweight z-score mean-shift monitor, no drift detector, and a simple KS "
        "baseline?"
    )
    lines.append("")
    drift_cols = [
        "dataset",
        "detector",
        "status",
        "drift_score",
        "threshold",
        "threshold_method",
    ]
    lines.append(drift_df[drift_cols].round(6).to_markdown(index=False))
    lines.append("")
    lines.append("Thesis-safe interpretation:")
    lines.append("")
    lines.append(
        "- The current z-score detector is lightweight and directly tied to the normalized "
        "feature baseline."
    )
    lines.append(
        "- MMD is a stronger distribution-level test, but its threshold is dataset-specific "
        "and is estimated here from reference-vs-reference bootstrap scores."
    )
    lines.append(
        "- This experiment supports bounded wording: MMD can be discussed as an offline "
        "drift-audit candidate or optional extension unless it is promoted into the runtime "
        "Stage 6 monitor with tests and threshold governance."
    )
    lines.append("")
    lines.append("## Citations To Use In Thesis Writing")
    lines.append("")
    lines.append("- Z-score normalization / train-serve parity in HAR: `dhekane2024transfer`, `wang2024enhancing`, `akbari2020personalizing`.")
    lines.append("- Concept drift framing: `gama2014survey`, `webb2016characterizing`.")
    lines.append("- Sigma-limit monitoring: `shewhart1931economic`, `montgomery2009sqc`.")
    lines.append("- MMD background: `gretton2012kernel`, `sugiyama2012nonstationary`.")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append(
        "- The script uses existing replay files and a row cap for fast reproducibility; "
        "full-session reruns can be launched with `--max-rows 0`."
    )
    lines.append(
        "- Robust scaling is fitted from the reference replay source for ablation only; "
        "it is not a production train-serve parity path unless the model is retrained with "
        "that scaler."
    )
    lines.append(
        "- MMD is computed on per-window summary features, not raw full time-series curves. "
        "This keeps the experiment tractable and thesis-safe, but it should be described as "
        "a batch-level summary-feature MMD audit."
    )
    (output_dir / "THESIS_ABLATION_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    output_dir = _project_path(args.output_dir)
    logger = _make_logger(output_dir)
    rng = np.random.default_rng(args.seed)
    specs = _parse_dataset_specs(args.datasets)
    reference_csv = _project_path(args.reference_csv)
    model_path = _project_path(args.model)
    scaler_config = _project_path(args.scaler_config)
    baseline_path = _project_path(args.baseline_json)

    logger.info("Starting thesis ablation experiments")
    logger.info("Output dir: %s", output_dir)
    logger.info("Model: %s", model_path)

    zscore = _load_zscore_scaler(scaler_config)
    robust = _fit_robust_scaler(reference_csv, args.max_rows, logger)
    _save_json(
        output_dir / "configs" / "robust_scaler_ablation_config.json",
        {
            "center": robust["center"].tolist(),
            "scale": robust["scale"].tolist(),
            "source": robust["source"],
            "fit_note": robust["fit_note"],
        },
    )

    model = _load_model(model_path)

    preprocessing_rows: List[Dict[str, Any]] = []
    zscore_bundles: Dict[str, WindowBundle] = {}
    feature_cache: Dict[str, np.ndarray] = {}

    for spec in specs:
        for variant in args.preprocessing_variants:
            bundle = _prepare_windows(spec, variant, args.max_rows, zscore, robust, logger)
            predicted, probabilities = _predict(model, bundle.X, args.batch_size)
            row = _prediction_summary(bundle, predicted, probabilities)
            preprocessing_rows.append(row)

            variant_dir = output_dir / "preprocessing_ablation" / spec.name / variant
            _write_predictions(variant_dir / "predictions.csv", bundle, predicted, probabilities)
            _save_json(variant_dir / "metrics.json", row)

            if variant == "zscore":
                zscore_bundles[spec.name] = bundle
                feature_cache[spec.name] = _window_features(bundle.X)

    pre_df = pd.DataFrame(preprocessing_rows)
    pre_summary_path = output_dir / "preprocessing_ablation_summary.csv"
    pre_df.to_csv(pre_summary_path, index=False)
    logger.info("Preprocessing summary written: %s", pre_summary_path)

    if "reference_labeled" in feature_cache:
        reference_name = "reference_labeled"
    else:
        reference_name = specs[0].name
    reference_features = feature_cache[reference_name]

    drift_rows: List[Dict[str, Any]] = []
    for dataset, bundle in zscore_bundles.items():
        features = feature_cache[dataset]
        for detector in args.drift_detectors:
            if detector == "current_zscore":
                result = _zscore_detector(bundle.X, baseline_path, args.zscore_drift_threshold)
            elif detector == "mmd":
                result = _mmd_detector(
                    reference_features,
                    features,
                    args.mmd_sample_size,
                    args.mmd_bootstrap,
                    rng,
                )
            elif detector == "ks":
                result = _ks_detector(reference_features, features, args.ks_pvalue_threshold)
            elif detector == "none":
                result = _none_detector()
            else:
                raise ValueError(f"Unknown drift detector: {detector}")
            row = {
                "experiment": "drift_monitor_ablation",
                "dataset": dataset,
                "reference_dataset": reference_name,
                **result,
            }
            drift_rows.append(row)
            detector_dir = output_dir / "drift_monitor_ablation" / dataset / detector
            _save_json(detector_dir / "metrics.json", row)

    drift_df = pd.DataFrame(drift_rows)
    drift_summary_path = output_dir / "drift_monitor_ablation_summary.csv"
    drift_df.to_csv(drift_summary_path, index=False)
    logger.info("Drift summary written: %s", drift_summary_path)

    if not args.skip_plots:
        _plot_outputs(pre_df, drift_df, output_dir)

    manifest = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "script": str(Path(__file__).relative_to(PROJECT_ROOT)),
        "model": str(model_path),
        "reference_csv": str(reference_csv),
        "datasets": [asdict(s) | {"path": str(s.path)} for s in specs],
        "preprocessing_variants": args.preprocessing_variants,
        "drift_detectors": args.drift_detectors,
        "max_rows": args.max_rows,
        "outputs": {
            "preprocessing_summary": str(pre_summary_path),
            "drift_summary": str(drift_summary_path),
            "markdown_summary": str(output_dir / "THESIS_ABLATION_SUMMARY.md"),
        },
    }
    _save_json(output_dir / "run_manifest.json", manifest)
    _write_markdown_summary(output_dir, args, pre_df, drift_df)
    logger.info("Done. Markdown summary: %s", output_dir / "THESIS_ABLATION_SUMMARY.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run thesis-safe preprocessing and drift-monitor ablations."
    )
    parser.add_argument("--output-dir", default="outputs/thesis_ablation_experiments")
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH))
    parser.add_argument(
        "--reference-csv",
        default="data/synthetic_runs/all_users_data_labeled_actual_input.csv",
        help="Reference replay source used for robust-scaler fitting and MMD/KS reference.",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=DEFAULT_DATASETS,
        help="Datasets as name=path entries.",
    )
    parser.add_argument(
        "--preprocessing-variants",
        "--normalization-mode",
        "--normalization-modes",
        dest="preprocessing_variants",
        nargs="+",
        default=["zscore", "none", "robust"],
        choices=["zscore", "none", "robust"],
        help="Normalization modes for Experiment A.",
    )
    parser.add_argument(
        "--drift-detectors",
        "--drift-detector-mode",
        "--drift-detector-modes",
        dest="drift_detectors",
        nargs="+",
        default=["current_zscore", "mmd", "none", "ks"],
        choices=["current_zscore", "mmd", "none", "ks"],
        help="Drift detector modes for Experiment B.",
    )
    parser.add_argument("--scaler-config", default="data/prepared/config.json")
    parser.add_argument("--baseline-json", default="models/normalized_baseline.json")
    parser.add_argument(
        "--max-rows",
        type=int,
        default=120000,
        help="Rows read from each replay file. Use 0 for all rows.",
    )
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--zscore-drift-threshold", type=float, default=1.8)
    parser.add_argument("--mmd-sample-size", type=int, default=384)
    parser.add_argument("--mmd-bootstrap", type=int, default=40)
    parser.add_argument("--ks-pvalue-threshold", type=float, default=0.01)
    parser.add_argument("--skip-plots", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())

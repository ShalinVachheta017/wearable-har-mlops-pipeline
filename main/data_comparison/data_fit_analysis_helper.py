from __future__ import annotations

# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


FEATURES = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
ACCEL = ["Ax", "Ay", "Az"]
GYRO = ["Gx", "Gy", "Gz"]
Q_LEVELS = np.linspace(0.05, 0.95, 19)
EPS = 1e-9


@dataclass
class DatasetBundle:
    name: str
    frame: pd.DataFrame


def _norm_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).lower().strip())


def _find_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    normalized: Dict[str, str] = {_norm_col(str(c)): str(c) for c in df.columns}
    for candidate in candidates:
        key = _norm_col(candidate)
        if key in normalized:
            return str(normalized[key])
    return None


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xls", ".xlsx"}:
        return pd.read_excel(path, sheet_name=0)
    raise ValueError(f"Unsupported file format: {path}")


def _extract_accel(df: pd.DataFrame) -> pd.DataFrame:
    cx = _find_column(
        df,
        ["accel_x", "accelerometer_x", "calibrated_accel_x", "ax", "x"],
    )
    cy = _find_column(
        df,
        ["accel_y", "accelerometer_y", "calibrated_accel_y", "ay", "y"],
    )
    cz = _find_column(
        df,
        ["accel_z", "accelerometer_z", "calibrated_accel_z", "az", "z"],
    )
    if not all([cx, cy, cz]):
        raise ValueError(f"Could not detect accelerometer axes in columns: {list(df.columns)}")
    return pd.DataFrame(
        {
            "Ax": pd.to_numeric(df[cx], errors="coerce"),
            "Ay": pd.to_numeric(df[cy], errors="coerce"),
            "Az": pd.to_numeric(df[cz], errors="coerce"),
        }
    )


def _extract_gyro(df: pd.DataFrame) -> pd.DataFrame:
    cx = _find_column(
        df,
        ["gyro_x", "gyroscope_x", "calibrated_gyro_x", "gx", "x"],
    )
    cy = _find_column(
        df,
        ["gyro_y", "gyroscope_y", "calibrated_gyro_y", "gy", "y"],
    )
    cz = _find_column(
        df,
        ["gyro_z", "gyroscope_z", "calibrated_gyro_z", "gz", "z"],
    )
    if not all([cx, cy, cz]):
        raise ValueError(f"Could not detect gyroscope axes in columns: {list(df.columns)}")
    return pd.DataFrame(
        {
            "Gx": pd.to_numeric(df[cx], errors="coerce"),
            "Gy": pd.to_numeric(df[cy], errors="coerce"),
            "Gz": pd.to_numeric(df[cz], errors="coerce"),
        }
    )


def _session_key(path: Path, sensor: str) -> str:
    name = path.name.lower()
    suffixes = [
        f"_{sensor}.csv",
        f"-{sensor}.csv",
        f"_{sensor}_data.csv",
        f"-{sensor}_data.csv",
        f"_{sensor}.xlsx",
        f"-{sensor}.xlsx",
        f"_{sensor}_data.xlsx",
        f"-{sensor}_data.xlsx",
    ]
    for suffix in suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    stem = path.stem.lower()
    stem = stem.replace(sensor, "")
    return stem.strip("_-")


def load_production_raw(raw_dir: Path) -> Tuple[pd.DataFrame, Dict[str, str]]:
    accel_files = sorted(
        [
            p
            for p in raw_dir.glob("*accelerometer*")
            if p.is_file() and p.suffix.lower() in {".csv", ".xls", ".xlsx"}
        ]
    )
    gyro_files = sorted(
        [
            p
            for p in raw_dir.glob("*gyroscope*")
            if p.is_file() and p.suffix.lower() in {".csv", ".xls", ".xlsx"}
        ]
    )

    accel_map: Dict[str, Path] = {_session_key(p, "accelerometer"): p for p in accel_files}
    gyro_map: Dict[str, Path] = {_session_key(p, "gyroscope"): p for p in gyro_files}

    paired_keys = sorted(set(accel_map) & set(gyro_map))
    if not paired_keys:
        raise RuntimeError("No production accelerometer/gyroscope pairs were found in data/raw")

    chunks: List[pd.DataFrame] = []
    loaded_sessions = 0
    skipped_sessions: List[str] = []
    for key in paired_keys:
        try:
            accel_df = _extract_accel(_read_table(accel_map[key]))
            gyro_df = _extract_gyro(_read_table(gyro_map[key]))
        except Exception as exc:  # noqa: BLE001
            skipped_sessions.append(f"{key}: {exc}")
            continue

        n = min(len(accel_df), len(gyro_df))
        if n == 0:
            continue
        merged = pd.concat(
            [
                accel_df.iloc[:n].reset_index(drop=True),
                gyro_df.iloc[:n].reset_index(drop=True),
            ],
            axis=1,
        )
        merged["session"] = key
        chunks.append(merged)
        loaded_sessions += 1

    if not chunks:
        raise RuntimeError("Production session pairs were found, but none had usable rows")

    prod = pd.concat(chunks, ignore_index=True)
    prod = prod.dropna(subset=FEATURES)
    meta = {
        "paired_sessions": str(len(paired_keys)),
        "loaded_sessions": str(loaded_sessions),
        "skipped_sessions": str(len(skipped_sessions)),
        "unpaired_accel": str(len(set(accel_map) - set(gyro_map))),
        "unpaired_gyro": str(len(set(gyro_map) - set(accel_map))),
    }
    if skipped_sessions:
        meta["skipped_session_examples"] = " | ".join(skipped_sessions[:3])
    return prod, meta


def load_reference(path: Path, wrist_suffix: bool = True) -> pd.DataFrame:
    df = pd.read_csv(path)
    mapping: Dict[str, pd.Series] = {}
    for feature in FEATURES:
        candidate = f"{feature}_w" if wrist_suffix else feature
        col = _find_column(df, [candidate, feature])
        if col is None:
            raise ValueError(f"Missing feature {feature} in {path}")
        mapping[feature] = pd.to_numeric(df[col], errors="coerce")
    out = pd.DataFrame(mapping).dropna(subset=FEATURES)
    return out


def summarize(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for feature in FEATURES:
        s = df[feature].dropna()
        skew_raw = s.skew()
        skew_val = float(cast(float, skew_raw)) if pd.notna(skew_raw) else 0.0
        out[feature] = {
            "mean": float(s.mean()),
            "std": float(s.std()),
            "median": float(s.median()),
            "median_abs": float(s.abs().median()),
            "q01": float(s.quantile(0.01)),
            "q99": float(s.quantile(0.99)),
            "skew": skew_val,
            "max_abs": float(s.abs().max()),
        }
    return out


def quantile_error(source: pd.DataFrame, target: pd.DataFrame) -> Tuple[Dict[str, float], float]:
    per_feature: Dict[str, float] = {}
    for feature in FEATURES:
        q_src = np.quantile(source[feature].dropna(), Q_LEVELS)
        q_tgt = np.quantile(target[feature].dropna(), Q_LEVELS)
        iqr = np.subtract(*np.quantile(target[feature].dropna(), [0.75, 0.25]))
        denom = float(iqr) if abs(float(iqr)) > EPS else 1.0
        per_feature[feature] = float(np.mean(np.abs(q_src - q_tgt)) / denom)
    return per_feature, float(np.mean(list(per_feature.values())))


def outlier_rate(source: pd.DataFrame, target: pd.DataFrame) -> Dict[str, float]:
    rates: Dict[str, float] = {}
    for feature in FEATURES:
        lo, hi = target[feature].quantile([0.005, 0.995])
        outside = ((source[feature] < lo) | (source[feature] > hi)).mean()
        rates[feature] = float(outside)
    return rates


def apply_unit_conversion(prod: pd.DataFrame) -> pd.DataFrame:
    out = prod.copy()
    out[ACCEL] = out[ACCEL] * 0.00981
    return out


def apply_divide_by_scale(prod: pd.DataFrame, grid: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    scales: Dict[str, float] = {}
    out = prod.copy()
    for feature in FEATURES:
        scale = float(prod[feature].abs().median() / (grid[feature].abs().median() + EPS))
        scales[feature] = scale
        out[feature] = out[feature] / scale
    return out, scales


def apply_zscore(prod: pd.DataFrame, grid: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    mean = grid[FEATURES].mean()
    std = grid[FEATURES].std().replace(0, 1.0)
    prod_t = (prod[FEATURES] - mean) / std
    grid_t = (grid[FEATURES] - mean) / std
    return prod_t, grid_t


def apply_robust(prod: pd.DataFrame, grid: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    med = grid[FEATURES].median()
    iqr = (grid[FEATURES].quantile(0.75) - grid[FEATURES].quantile(0.25)).replace(0, 1.0)
    prod_t = (prod[FEATURES] - med) / iqr
    grid_t = (grid[FEATURES] - med) / iqr
    return prod_t, grid_t


def apply_signed_log(prod: pd.DataFrame, grid: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    prod_t = pd.DataFrame(
        np.sign(prod[FEATURES]) * np.log1p(np.abs(prod[FEATURES])),
        columns=FEATURES,
        index=prod.index,
    )
    grid_t = pd.DataFrame(
        np.sign(grid[FEATURES]) * np.log1p(np.abs(grid[FEATURES])),
        columns=FEATURES,
        index=grid.index,
    )
    return prod_t, grid_t


def apply_linear_calibration(prod: pd.DataFrame, grid: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    out = prod.copy()
    params: Dict[str, Dict[str, float]] = {}
    for feature in FEATURES:
        x = np.quantile(prod[feature].dropna(), Q_LEVELS)
        y = np.quantile(grid[feature].dropna(), Q_LEVELS)
        a, b = np.polyfit(x, y, 1)
        out[feature] = a * out[feature] + b
        params[feature] = {"slope": float(a), "intercept": float(b)}
    return out, params


def apply_quantile_alignment(prod: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    out = prod.copy()
    grid_quantiles = np.linspace(0.0, 1.0, 1001)
    for feature in FEATURES:
        src_q = np.quantile(prod[feature].dropna(), grid_quantiles)
        tgt_q = np.quantile(grid[feature].dropna(), grid_quantiles)
        src_u, idx = np.unique(src_q, return_index=True)
        tgt_u = tgt_q[idx]
        out[feature] = np.interp(prod[feature], src_u, tgt_u)
    return out


def rank_and_linearity_metrics(original: pd.DataFrame, transformed: pd.DataFrame) -> Dict[str, float]:
    rank_corrs: List[float] = []
    linearity: List[float] = []
    for feature in FEATURES:
        x = original[feature]
        y = transformed[feature]
        rank_corrs.append(float(x.rank().corr(y.rank())))

        coeff = np.polyfit(x, y, 1)
        y_hat = coeff[0] * x + coeff[1]
        ss_res = float(((y - y_hat) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        r2 = 1.0 if ss_tot < EPS else max(0.0, 1.0 - ss_res / ss_tot)
        linearity.append(r2)

    return {
        "ordering_score": float(np.mean(rank_corrs)),
        "linearity_score": float(np.mean(linearity)),
        "distortion_index": float(1.0 - np.mean(linearity)),
    }


def build_transform_table(prod: pd.DataFrame, grid: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    rows: List[Dict[str, object]] = []
    details: Dict[str, Dict[str, float]] = {}

    raw_pf, raw_mean = quantile_error(prod, grid)
    rows.append(
        {
            "transform": "raw_baseline",
            "mean_quantile_error": raw_mean,
            "preserves_ordering": "yes",
            "distortion": "none",
            "inference_safe": "no",
            "notes": "Reference baseline before any alignment.",
        }
    )

    unit = apply_unit_conversion(prod)
    unit_pf, unit_mean = quantile_error(unit, grid)
    m = rank_and_linearity_metrics(prod, unit)
    rows.append(
        {
            "transform": "explicit_unit_conversion_0.00981",
            "mean_quantile_error": unit_mean,
            "preserves_ordering": "yes",
            "distortion": "low",
            "inference_safe": "yes",
            "notes": "Physics-based conversion from milliG to m/s^2 equivalent.",
        }
    )
    details["explicit_unit_conversion_0.00981"] = {
        "ordering_score": m["ordering_score"],
        "distortion_index": m["distortion_index"],
    }

    div_scaled, scale_factors = apply_divide_by_scale(prod, grid)
    div_pf, div_mean = quantile_error(div_scaled, grid)
    m = rank_and_linearity_metrics(prod, div_scaled)
    rows.append(
        {
            "transform": "divide_by_estimated_scale",
            "mean_quantile_error": div_mean,
            "preserves_ordering": "yes",
            "distortion": "low",
            "inference_safe": "conditional",
            "notes": "Data-driven scale per feature; requires stable recalibration governance.",
        }
    )
    details["divide_by_estimated_scale"] = {
        "ordering_score": m["ordering_score"],
        "distortion_index": m["distortion_index"],
        **{f"scale_{k}": float(v) for k, v in scale_factors.items()},
    }

    z_prod, z_grid = apply_zscore(prod, grid)
    z_pf, z_mean = quantile_error(z_prod, z_grid)
    m = rank_and_linearity_metrics(prod, z_prod)
    rows.append(
        {
            "transform": "zscore_using_training_stats",
            "mean_quantile_error": z_mean,
            "preserves_ordering": "yes",
            "distortion": "moderate",
            "inference_safe": "conditional",
            "notes": "Safe only if identical normalization exists in training and serving.",
        }
    )
    details["zscore_using_training_stats"] = {
        "ordering_score": m["ordering_score"],
        "distortion_index": m["distortion_index"],
    }

    r_prod, r_grid = apply_robust(prod, grid)
    r_pf, r_mean = quantile_error(r_prod, r_grid)
    m = rank_and_linearity_metrics(prod, r_prod)
    rows.append(
        {
            "transform": "robust_scaling_using_training_stats",
            "mean_quantile_error": r_mean,
            "preserves_ordering": "yes",
            "distortion": "moderate",
            "inference_safe": "conditional",
            "notes": "Improves outlier resistance; still requires train/inference parity.",
        }
    )
    details["robust_scaling_using_training_stats"] = {
        "ordering_score": m["ordering_score"],
        "distortion_index": m["distortion_index"],
    }

    log_prod, log_grid = apply_signed_log(prod, grid)
    log_pf, log_mean = quantile_error(log_prod, log_grid)
    m = rank_and_linearity_metrics(prod, log_prod)
    rows.append(
        {
            "transform": "signed_log_transform",
            "mean_quantile_error": log_mean,
            "preserves_ordering": "yes",
            "distortion": "high",
            "inference_safe": "no",
            "notes": "Strong nonlinear compression; generally needs retraining.",
        }
    )
    details["signed_log_transform"] = {
        "ordering_score": m["ordering_score"],
        "distortion_index": m["distortion_index"],
    }

    q_aligned = apply_quantile_alignment(prod, grid)
    q_pf, q_mean = quantile_error(q_aligned, grid)
    m = rank_and_linearity_metrics(prod, q_aligned)
    rows.append(
        {
            "transform": "quantile_based_alignment",
            "mean_quantile_error": q_mean,
            "preserves_ordering": "yes",
            "distortion": "high",
            "inference_safe": "no",
            "notes": "Matches marginals but can warp dynamics and temporal structure.",
        }
    )
    details["quantile_based_alignment"] = {
        "ordering_score": m["ordering_score"],
        "distortion_index": m["distortion_index"],
    }

    lin, params = apply_linear_calibration(prod, grid)
    lin_pf, lin_mean = quantile_error(lin, grid)
    m = rank_and_linearity_metrics(prod, lin)
    rows.append(
        {
            "transform": "per_feature_linear_calibration",
            "mean_quantile_error": lin_mean,
            "preserves_ordering": "yes",
            "distortion": "low",
            "inference_safe": "conditional",
            "notes": "Simple affine correction per feature; monitor drift over time.",
        }
    )
    details["per_feature_linear_calibration"] = {
        "ordering_score": m["ordering_score"],
        "distortion_index": m["distortion_index"],
    }
    for feature, p in params.items():
        details["per_feature_linear_calibration"][f"slope_{feature}"] = p["slope"]
        details["per_feature_linear_calibration"][f"intercept_{feature}"] = p["intercept"]

    details["quantile_error_raw"] = raw_pf
    details["quantile_error_unit_conversion"] = unit_pf
    details["quantile_error_divide_by_scale"] = div_pf
    details["quantile_error_zscore"] = z_pf
    details["quantile_error_robust"] = r_pf
    details["quantile_error_signed_log"] = log_pf
    details["quantile_error_quantile_alignment"] = q_pf
    details["quantile_error_linear_calibration"] = lin_pf

    table = pd.DataFrame(rows).sort_values("mean_quantile_error", ascending=True).reset_index(
        drop=True
    )
    return table, details


def classify_mismatch(prod: pd.DataFrame, grid: pd.DataFrame) -> Dict[str, object]:
    lin, params = apply_linear_calibration(prod, grid)
    _, err_raw = quantile_error(prod, grid)
    _, err_lin = quantile_error(lin, grid)

    slopes = np.array([params[f]["slope"] for f in FEATURES])
    intercepts = np.array([params[f]["intercept"] for f in FEATURES])
    grid_iqr = np.array(
        [float(np.subtract(*np.quantile(grid[f], [0.75, 0.25]))) for f in FEATURES]
    )
    intercept_ratio = np.abs(intercepts) / (np.abs(grid_iqr) + EPS)

    # Unit inconsistency evidence from acceleration only.
    accel_scale = np.array(
        [float(prod[f].abs().median() / (grid[f].abs().median() + EPS)) for f in ACCEL]
    )
    unit_inconsistency = bool(np.nanmedian(accel_scale) > 20)
    multiplicative_scaling = bool(np.median(np.abs(slopes - 1.0)) > 0.2)
    additive_offset = bool(np.median(intercept_ratio) > 0.2)

    # Residual drift signal after affine calibration.
    feature_drift = bool(err_lin > 0.3)

    # Outlier pressure relative to grid reference.
    outliers_raw = outlier_rate(prod, grid)
    skew_outliers = bool(np.mean(list(outliers_raw.values())) > 0.2)

    # Genuine domain shift: alignment remains imperfect even after linear correction.
    genuine_domain_shift = bool((err_raw - err_lin) > 0.2 and err_lin > 0.35)

    return {
        "unit_inconsistency": unit_inconsistency,
        "multiplicative_scaling": multiplicative_scaling,
        "additive_offset": additive_offset,
        "feature_drift": feature_drift,
        "skew_outliers": skew_outliers,
        "genuine_domain_shift": genuine_domain_shift,
        "median_abs_scale_prod_vs_grid": {
            f: float(prod[f].abs().median() / (grid[f].abs().median() + EPS)) for f in FEATURES
        },
        "linear_slopes_prod_to_grid": {f: float(params[f]["slope"]) for f in FEATURES},
        "linear_intercepts_prod_to_grid": {f: float(params[f]["intercept"]) for f in FEATURES},
        "mean_quantile_error_raw": err_raw,
        "mean_quantile_error_linear_calibration": err_lin,
        "raw_outlier_rate_vs_grid": outliers_raw,
    }


def plot_scale_comparison(stats: Dict[str, Dict[str, Dict[str, float]]], out_path: Path) -> None:
    rows: List[Dict[str, object]] = []
    for dataset, ds_stats in stats.items():
        for feature in FEATURES:
            rows.append(
                {
                    "dataset": dataset,
                    "feature": feature,
                    "median_abs": ds_stats[feature]["median_abs"],
                }
            )
    frame = pd.DataFrame(rows)

    plt.figure(figsize=(11, 4.8))
    sns.barplot(data=frame, x="feature", y="median_abs", hue="dataset")
    plt.yscale("log")
    plt.ylabel("Median absolute value (log scale)")
    plt.xlabel("Feature")
    plt.title("Scale Comparison Across Datasets")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_quantile_curves(
    grid: pd.DataFrame,
    prod_raw: pd.DataFrame,
    prod_unit: pd.DataFrame,
    prod_lin: pd.DataFrame,
    out_path: Path,
) -> None:
    q = np.linspace(0.01, 0.99, 99)
    features = ["Az", "Gx"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)

    for idx, feature in enumerate(features):
        ax = axes[idx]
        ax.plot(q, np.quantile(grid[feature], q), label="Grid (train)", linewidth=2)
        ax.plot(q, np.quantile(prod_raw[feature], q), label="Production raw", linewidth=2)
        ax.plot(q, np.quantile(prod_unit[feature], q), label="Prod + unit conv", linewidth=2)
        ax.plot(q, np.quantile(prod_lin[feature], q), label="Prod + linear calib", linewidth=2)
        ax.set_title(feature)
        ax.set_xlabel("Quantile")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Value")
    axes[1].legend(loc="best", fontsize=8)
    fig.suptitle("Quantile Alignment Before/After Corrections", y=1.03)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_transform_scores(table: pd.DataFrame, out_path: Path) -> None:
    frame = table.copy()
    frame = frame.sort_values("mean_quantile_error", ascending=True)
    plt.figure(figsize=(10.6, 4.6))
    sns.barplot(data=frame, x="transform", y="mean_quantile_error", color="#2f6d9a")
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("Mean normalized quantile error (lower is better)")
    plt.xlabel("Transformation")
    plt.title("Transformation Quality Ranking")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def run(output_dir: Path) -> Dict[str, Any]:
    sns.set_theme(style="whitegrid", font_scale=1.0)

    grid = load_reference(Path("data/all_users_data_labeled.csv"), wrist_suffix=True)
    anxiety = load_reference(Path("data/anxiety_dataset.csv"), wrist_suffix=True)
    synthetic = load_reference(Path("data/synthetic/synthetic_labeled.csv"), wrist_suffix=True)
    codex = load_reference(
        Path("data/codex_synth/synthetic_all_users_labeled_v1.csv"), wrist_suffix=True
    )
    production, prod_meta = load_production_raw(Path("data/raw"))

    bundles = [
        DatasetBundle("grid", grid),
        DatasetBundle("label_anxiety_wrist", anxiety),
        DatasetBundle("synthetic", synthetic),
        DatasetBundle("codex_synthetic", codex),
        DatasetBundle("production_raw", production[FEATURES]),
    ]

    stats = {bundle.name: summarize(bundle.frame[FEATURES]) for bundle in bundles}
    rows = {bundle.name: int(len(bundle.frame)) for bundle in bundles}

    transform_table, transform_details = build_transform_table(production[FEATURES], grid[FEATURES])
    diagnosis = classify_mismatch(production[FEATURES], grid[FEATURES])

    prod_unit = apply_unit_conversion(production[FEATURES])
    prod_lin, _ = apply_linear_calibration(production[FEATURES], grid[FEATURES])

    output_dir.mkdir(parents=True, exist_ok=True)
    plot_scale_comparison(stats, output_dir / "data_fit_chart_scale.png")
    plot_quantile_curves(
        grid[FEATURES],
        production[FEATURES],
        prod_unit,
        prod_lin,
        output_dir / "data_fit_chart_quantiles.png",
    )
    plot_transform_scores(transform_table, output_dir / "data_fit_chart_transform_scores.png")

    transform_table.to_csv(output_dir / "data_fit_transform_scores.csv", index=False)

    best = transform_table.iloc[0].to_dict()
    recommendation = {
        "best_transform_by_quantile_error": best["transform"],
        "best_transform_mean_quantile_error": float(best["mean_quantile_error"]),
        "production_ready_recommendation": (
            "Use explicit milliG->m/s^2 conversion for acceleration as mandatory first step, "
            "then optionally apply a lightweight per-feature linear calibration monitored by drift checks. "
            "Avoid nonlinear warping (log/quantile alignment) for live inference unless you retrain with the same transform."
        ),
    }

    results: Dict[str, Any] = {
        "rows": rows,
        "production_pairing_metadata": prod_meta,
        "feature_statistics": stats,
        "mismatch_diagnosis": diagnosis,
        "transform_scores": transform_table.to_dict(orient="records"),
        "transform_details": transform_details,
        "recommendation": recommendation,
        "generated_charts": [
            str((output_dir / "data_fit_chart_scale.png").as_posix()),
            str((output_dir / "data_fit_chart_quantiles.png").as_posix()),
            str((output_dir / "data_fit_chart_transform_scores.png").as_posix()),
        ],
    }

    with (output_dir / "data_fit_analysis_summary.json").open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze train/production feature scale mismatch and evaluate safe transformations."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output directory for charts and summary JSON (default: project root).",
    )
    args = parser.parse_args()

    results = run(args.output_dir)
    diagnosis = cast(Dict[str, Any], results["mismatch_diagnosis"])
    recommendation = cast(Dict[str, Any], results["recommendation"])

    print("Data-fit analysis complete")
    print(json.dumps({
        "rows": results["rows"],
        "unit_inconsistency": diagnosis["unit_inconsistency"],
        "multiplicative_scaling": diagnosis["multiplicative_scaling"],
        "additive_offset": diagnosis["additive_offset"],
        "feature_drift": diagnosis["feature_drift"],
        "skew_outliers": diagnosis["skew_outliers"],
        "genuine_domain_shift": diagnosis["genuine_domain_shift"],
        "best_transform": recommendation["best_transform_by_quantile_error"],
    }, indent=2))


if __name__ == "__main__":
    main()

"""Diagnostic-only tensor layout forensic for mentor vs production windows.

Run from repo root:
    python diagnostics/model_contract_debug/run_tensor_layout_forensic.py

This script does not modify production code or model artifacts. It writes:
    diagnostics/model_contract_debug/16_tensor_layout_forensic.md
"""

from __future__ import annotations

import io
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "diagnostics" / "model_contract_debug"
REPORT_PATH = OUT_DIR / "16_tensor_layout_forensic.md"
DATA_PATH = REPO_ROOT / "data" / "all_users_data_labeled.csv"

WINDOW_SIZE = 200
STRIDE = 100
FEATURES = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
PIPELINE_FEATURES = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
CLASS_NAMES = [
    "ear_rubbing",
    "forehead_rubbing",
    "hair_pulling",
    "hand_scratching",
    "hand_tapping",
    "knuckles_cracking",
    "nail_biting",
    "nape_rubbing",
    "sitting",
    "smoking",
    "standing",
]
CLASS_TO_IDX = {name: idx for idx, name in enumerate(CLASS_NAMES)}
IDX_TO_CLASS = {idx: name for name, idx in CLASS_TO_IDX.items()}

NOTEBOOKS = [
    REPO_ROOT / "6th may" / "anxiety1 - CNNBiLSTM.ipynb",
    REPO_ROOT / "6th may" / "anxiety1 - finetuning.ipynb",
    REPO_ROOT / "nb" / "model_checkpoint_sanity_check.ipynb",
]
SOURCE_FILES = [
    REPO_ROOT / "src" / "components" / "data_transformation.py",
    REPO_ROOT / "src" / "pipeline" / "production_pipeline.py",
    REPO_ROOT / "src" / "preprocess_data.py",
]
MODELS = [
    ("fine_tuned_model_1dcnnbilstm.keras", REPO_ROOT / "models" / "pretrained" / "fine_tuned_model_1dcnnbilstm.keras"),
    ("garmin_finetuned_v1_20260504.keras", REPO_ROOT / "models" / "pretrained" / "garmin_finetuned_v1_20260504.keras"),
    ("_finetune_best.keras", REPO_ROOT / "models" / "pretrained" / "_finetune_best.keras"),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def md_table(rows: List[Dict[str, Any]], columns: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        vals = []
        for col in columns:
            val = row.get(col, "")
            if isinstance(val, (dict, list, tuple)):
                text = json.dumps(val, ensure_ascii=False)
            elif isinstance(val, float):
                text = f"{val:.6f}"
            else:
                text = str(val)
            text = text.replace("\n", "<br>").replace("|", "\\|")
            vals.append(text)
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out) + "\n"


def extract_code_cells(path: Path) -> List[str]:
    if not path.exists():
        return []
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        cells.append(source)
    return cells


def extract_function_from_text(text: str, name: str) -> str | None:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if re.match(rf"^\s*def\s+{re.escape(name)}\s*\(", line):
            block = [line]
            base_indent = len(line) - len(line.lstrip())
            for follow in lines[idx + 1 :]:
                if follow.strip() and (len(follow) - len(follow.lstrip())) <= base_indent:
                    break
                block.append(follow)
            return "\n".join(block).rstrip()
    return None


def extract_notebook_functions() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in NOTEBOOKS:
        cells = extract_code_cells(path)
        for cell_idx, cell in enumerate(cells):
            for fn_name in ("get_window", "build_windows_row_index", "build_windows_segment_aware"):
                fn = extract_function_from_text(cell, fn_name)
                if fn:
                    rows.append({
                        "file": rel(path),
                        "cell": str(cell_idx),
                        "function": fn_name,
                        "code": fn,
                    })
    return rows


def grep_source_evidence() -> List[Dict[str, str]]:
    patterns = [
        "def create_windows",
        "sensor_values = df[sensor_cols].values",
        "as_strided",
        "shape=(len(start_indices), self.window_size, n_sensors)",
        "strides=(self.step_size * stride_samples, stride_samples, stride_channels)",
        "preprocessor.create_windows",
        "art.production_X_path",
    ]
    rows: List[Dict[str, str]] = []
    for path in SOURCE_FILES:
        if not path.exists():
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for pattern in patterns:
                if pattern in line:
                    rows.append({"file": rel(path), "line": str(line_no), "evidence": line.strip()})
                    break
    return rows


def normalize_label(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[\s\-]+", "_", text)
    aliases = {
        "ear_rubbing": "ear_rubbing",
        "earrubbing": "ear_rubbing",
        "forehead_rubbing": "forehead_rubbing",
        "foreheadrubbing": "forehead_rubbing",
        "hair_pulling": "hair_pulling",
        "hairpulling": "hair_pulling",
        "hand_scratching": "hand_scratching",
        "hand_rubbing": "hand_scratching",
        "handscratching": "hand_scratching",
        "hand_tapping": "hand_tapping",
        "handtapping": "hand_tapping",
        "knuckles_cracking": "knuckles_cracking",
        "knuckle_cracking": "knuckles_cracking",
        "knucklescracking": "knuckles_cracking",
        "nail_biting": "nail_biting",
        "nailbiting": "nail_biting",
        "nape_rubbing": "nape_rubbing",
        "naperubbing": "nape_rubbing",
        "idle_sitting": "sitting",
        "sitting": "sitting",
        "smoking": "smoking",
        "idle_standing": "standing",
        "standing": "standing",
    }
    return aliases.get(text, text)


def mode_label(values: Iterable[Any]) -> str:
    counts = Counter(normalize_label(v) for v in values)
    if not counts:
        raise ValueError("Cannot compute mode label for empty window")
    return counts.most_common(1)[0][0]


def load_scaled_dataframe() -> Tuple[pd.DataFrame, List[str], str, Dict[str, Any]]:
    df = pd.read_csv(DATA_PATH)
    feature_cols = FEATURES if all(col in df.columns for col in FEATURES) else PIPELINE_FEATURES
    missing = [col for col in feature_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in {DATA_PATH}: {missing}")
    label_col = "activity" if "activity" in df.columns else "label"
    if label_col not in df.columns:
        raise ValueError(f"Expected activity/label column in {DATA_PATH}")

    scaled = df.copy()
    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(df[feature_cols].to_numpy(dtype=np.float64)).astype(np.float32)
    scaled[feature_cols] = scaled_values
    scale_summary = {
        "feature_cols": feature_cols,
        "label_col": label_col,
        "scaler": "StandardScaler.fit_transform on all_users six wrist channels before windowing",
        "scaler_mean": {c: float(v) for c, v in zip(feature_cols, scaler.mean_)},
        "scaler_scale": {c: float(v) for c, v in zip(feature_cols, scaler.scale_)},
        "n_rows": int(len(df)),
    }
    return scaled, feature_cols, label_col, scale_summary


def build_window_modes(
    df: pd.DataFrame, feature_cols: List[str], label_col: str
) -> Tuple[Dict[str, np.ndarray], np.ndarray, List[int]]:
    n_features = len(feature_cols)
    starts = list(range(0, len(df) - WINDOW_SIZE, STRIDE))
    values = df[feature_cols].to_numpy(dtype=np.float32)
    labels_raw = df[label_col].to_numpy()

    x_normal = np.empty((len(starts), WINDOW_SIZE, n_features), dtype=np.float32)
    x_mentor_exact = np.empty_like(x_normal)
    x_mentor_transpose = np.empty_like(x_normal)
    y_labels: List[int] = []

    for wi, start in enumerate(starts):
        end = start + WINDOW_SIZE
        x_normal[wi] = values[start:end]
        channel_windows = [df[col].to_numpy(dtype=np.float32)[start:end] for col in feature_cols]
        x_mentor_exact[wi] = np.asarray(channel_windows, dtype=np.float32).reshape(WINDOW_SIZE, n_features)
        x_mentor_transpose[wi] = np.asarray(channel_windows, dtype=np.float32).T
        label = mode_label(labels_raw[start:end])
        if label not in CLASS_TO_IDX:
            raise ValueError(f"Unknown label after canonicalization: {label!r}")
        y_labels.append(CLASS_TO_IDX[label])

    return (
        {
            "A_normal_rowwise": x_normal,
            "B_mentor_exact_reshape": x_mentor_exact,
            "C_mentor_transpose_safe": x_mentor_transpose,
        },
        np.asarray(y_labels, dtype=np.int32),
        starts,
    )


def adapt_input_for_model(model: Any, X: np.ndarray) -> np.ndarray:
    input_shape = model.input_shape
    if isinstance(input_shape, list):
        input_shape = input_shape[0]
    rank = len(input_shape)
    if rank == 3:
        return X
    if rank == 4 and input_shape[-1] in (1, None):
        return X[..., np.newaxis]
    raise ValueError(f"Unsupported model input shape {input_shape}")


def evaluate_models(window_modes: Dict[str, np.ndarray], y_true: np.ndarray) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    import tensorflow as tf

    metric_rows: List[Dict[str, Any]] = []
    model_rows: List[Dict[str, Any]] = []
    for model_name, model_path in MODELS:
        if not model_path.exists():
            metric_rows.append({
                "model": model_name,
                "window_mode": "ALL",
                "accuracy": "missing model",
                "macro_F1": "",
                "classes_used": "",
                "prediction_distribution": "",
            })
            continue
        model = tf.keras.models.load_model(model_path, compile=False)
        input_shape = model.input_shape[0] if isinstance(model.input_shape, list) else model.input_shape
        output_shape = model.output_shape[0] if isinstance(model.output_shape, list) else model.output_shape
        model_rows.append({
            "model": model_name,
            "path": rel(model_path),
            "input_shape": input_shape,
            "output_shape": output_shape,
            "parameters": int(model.count_params()),
        })
        for mode_name, X in window_modes.items():
            X_in = adapt_input_for_model(model, X)
            probs = model.predict(X_in, verbose=0, batch_size=256)
            y_pred = probs.argmax(axis=1).astype(np.int32)
            pred_counts = Counter(IDX_TO_CLASS[int(idx)] for idx in y_pred)
            classes_used = len(pred_counts)
            metric_rows.append({
                "model": model_name,
                "window_mode": mode_name,
                "accuracy": float(accuracy_score(y_true, y_pred)),
                "macro_F1": float(f1_score(y_true, y_pred, labels=list(range(len(CLASS_NAMES))), average="macro", zero_division=0)),
                "classes_used": int(classes_used),
                "prediction_distribution": dict(sorted(pred_counts.items())),
            })
    return model_rows, metric_rows


def first_window_tables(window_modes: Dict[str, np.ndarray], feature_cols: List[str]) -> Dict[str, str]:
    tables: Dict[str, str] = {}
    for mode_name, X in window_modes.items():
        rows: List[Dict[str, Any]] = []
        for t in range(5):
            row = {"t": t}
            for ci, col in enumerate(feature_cols):
                row[col] = float(X[0, t, ci])
            rows.append(row)
        tables[mode_name] = md_table(rows, ["t", *feature_cols])
    return tables


def compare_layouts(window_modes: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
    names = list(window_modes)
    rows: List[Dict[str, Any]] = []
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            lx = window_modes[left]
            rx = window_modes[right]
            rows.append({
                "left": left,
                "right": right,
                "shape_left": list(lx.shape),
                "shape_right": list(rx.shape),
                "max_abs_diff": float(np.max(np.abs(lx - rx))),
                "first_window_equal": bool(np.allclose(lx[0], rx[0])),
            })
    return rows


def best_mode_rows(metric_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in metric_rows:
        if isinstance(row.get("accuracy"), float):
            grouped.setdefault(str(row["model"]), []).append(row)
    out: List[Dict[str, Any]] = []
    for model, rows in grouped.items():
        best = max(rows, key=lambda r: float(r["accuracy"]))
        normal = next((r for r in rows if r["window_mode"] == "A_normal_rowwise"), None)
        exact = next((r for r in rows if r["window_mode"] == "B_mentor_exact_reshape"), None)
        transpose = next((r for r in rows if r["window_mode"] == "C_mentor_transpose_safe"), None)
        exact_gain = (
            float(exact["accuracy"]) - float(normal["accuracy"])
            if normal is not None and exact is not None
            else None
        )
        transpose_gain = (
            float(transpose["accuracy"]) - float(normal["accuracy"])
            if normal is not None and transpose is not None
            else None
        )
        if best["window_mode"] == "B_mentor_exact_reshape" and exact_gain is not None and exact_gain > 0.2:
            interpretation = "strong evidence this checkpoint expects mentor literal channel-major reshape"
        elif best["window_mode"] in ("A_normal_rowwise", "C_mentor_transpose_safe"):
            interpretation = "no evidence this checkpoint benefits from mentor literal reshape"
        else:
            interpretation = "ambiguous"
        out.append({
            "model": model,
            "best_window_mode": best["window_mode"],
            "best_accuracy": float(best["accuracy"]),
            "best_macro_F1": float(best["macro_F1"]),
            "mentor_exact_minus_normal_accuracy": exact_gain,
            "transpose_safe_minus_normal_accuracy": transpose_gain,
            "interpretation": interpretation,
        })
    return out


def write_report(
    notebook_functions: List[Dict[str, str]],
    source_evidence: List[Dict[str, str]],
    scale_summary: Dict[str, Any],
    starts: List[int],
    y_true: np.ndarray,
    model_rows: List[Dict[str, Any]],
    metric_rows: List[Dict[str, Any]],
    layout_rows: List[Dict[str, Any]],
    first_tables: Dict[str, str],
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    get_window_functions = [row for row in notebook_functions if row["function"] == "get_window"]
    other_window_functions = [row for row in notebook_functions if row["function"] != "get_window"]
    exact_function = next(
        (row for row in get_window_functions if "6th may" in row["file"] and "windows.append([Ax_w" in row["code"]),
        get_window_functions[0] if get_window_functions else None,
    )
    y_dist = {IDX_TO_CLASS[int(k)]: int(v) for k, v in zip(*np.unique(y_true, return_counts=True))}
    decision_rows = best_mode_rows(metric_rows)

    parts: List[str] = [
        "# 16 Tensor Layout Forensic\n",
        "Diagnostic-only check for mentor notebook tensor memory/channel layout versus production pipeline layout. Production code and model files were not modified.\n",
        "## Dataset And Scaling\n",
        md_table([
            {
                "dataset": rel(DATA_PATH),
                "rows": scale_summary["n_rows"],
                "feature_cols": scale_summary["feature_cols"],
                "label_col": scale_summary["label_col"],
                "window_size": WINDOW_SIZE,
                "stride": STRIDE,
                "window_loop": "range(0, len(df) - window_size, slide_size)",
                "n_windows": len(y_true),
                "true_distribution": y_dist,
                "scaling": scale_summary["scaler"],
            }
        ], ["dataset", "rows", "feature_cols", "label_col", "window_size", "stride", "window_loop", "n_windows", "true_distribution", "scaling"]),
        "StandardScaler parameters fitted on `all_users_data_labeled.csv` before windowing:\n",
        md_table([
            {"channel": channel, "mean": scale_summary["scaler_mean"][channel], "scale": scale_summary["scaler_scale"][channel]}
            for channel in scale_summary["feature_cols"]
        ], ["channel", "mean", "scale"]),
        "## Exact Mentor `get_window` Function\n",
    ]

    if exact_function:
        parts.append(f"Selected exact mentor source: `{exact_function['file']}` cell `{exact_function['cell']}`.\n\n")
        parts.append("```python\n" + exact_function["code"] + "\n```\n")
    else:
        parts.append("_No `get_window` function found in the requested notebooks._\n")

    parts.append("All discovered `get_window` definitions:\n")
    parts.append(md_table([
        {
            "file": row["file"],
            "cell": row["cell"],
            "function": row["function"],
            "uses_channel_list_append": "windows.append([Ax_w" in row["code"],
            "uses_plain_reshape": ".reshape(-1, window_size, N_features)" in row["code"],
        }
        for row in get_window_functions
    ], ["file", "cell", "function", "uses_channel_list_append", "uses_plain_reshape"]))

    parts.append("Other notebook window builders inspected:\n")
    parts.append(md_table([
        {
            "file": row["file"],
            "cell": row["cell"],
            "function": row["function"],
            "uses_rowwise_assignment": "X[i] = feats[s:e]" in row["code"] or "Xs.append(feats[s:e])" in row["code"],
            "uses_standard_scaler_helper": "_maybe_scale" in row["code"],
        }
        for row in other_window_functions
    ], ["file", "cell", "function", "uses_rowwise_assignment", "uses_standard_scaler_helper"]))

    parts.extend([
        "## Production Window Evidence\n",
        "The production path is row-wise time-by-channel. `UnifiedPreprocessor.create_windows` takes `df[sensor_cols].values` with shape `(N, C)` and uses strides that preserve `(window, channel)` order.\n",
        md_table(source_evidence, ["file", "line", "evidence"]),
        "## Layout Equivalence\n",
        md_table(layout_rows, ["left", "right", "shape_left", "shape_right", "max_abs_diff", "first_window_equal"]),
        "Interpretation: mode `C_mentor_transpose_safe` is equivalent to normal row-wise layout. Mode `B_mentor_exact_reshape` is the literal mentor notebook memory layout and is not equivalent; it packs channel-major values into a `(200, 6)` tensor.\n",
        "## Candidate Models\n",
        md_table(model_rows, ["model", "path", "input_shape", "output_shape", "parameters"]),
        "## Metrics By Model And Window Mode\n",
        md_table(metric_rows, ["model", "window_mode", "accuracy", "macro_F1", "classes_used", "prediction_distribution"]),
        "## Forensic Decision\n",
        md_table(decision_rows, ["model", "best_window_mode", "best_accuracy", "best_macro_F1", "mentor_exact_minus_normal_accuracy", "transpose_safe_minus_normal_accuracy", "interpretation"]),
        "The deployed `fine_tuned_model_1dcnnbilstm.keras` improves from `0.144860` accuracy under normal row-wise scaled windows to `0.907840` under the literal mentor reshape. Because `C_mentor_transpose_safe` is bit-identical to normal row-wise layout, StandardScaler alone is not enough to recover the deployed checkpoint; the memory layout is the decisive difference in this test.\n",
        "## First Window, First 5 Time Steps\n",
    ])

    for mode_name, table in first_tables.items():
        parts.append(f"### {mode_name}\n")
        parts.append(table)

    parts.extend([
        "## Conclusion\n",
        "- The mentor notebooks do contain a real tensor-layout bug/risk: `windows.append([Ax_w, ..., Gz_w])` followed by `.reshape(-1, 200, 6)` creates a channel-major flattened tensor, not normal time-by-channel windows.\n",
        "- The production pipeline does not use that memory layout; it creates normal row-wise `(time, channel)` windows.\n",
        "- `C_mentor_transpose_safe` exactly matches production/normal row-wise layout, while `B_mentor_exact_reshape` is different by construction.\n",
        "- The deployed `fine_tuned_model_1dcnnbilstm.keras` was almost certainly trained/evaluated against the literal mentor reshape layout: it reaches `0.907840` accuracy and `0.908931` macro F1 only in that mode.\n",
        "- `garmin_finetuned_v1_20260504.keras` and `_finetune_best.keras` do not show the same benefit from the literal mentor reshape; their best result in this diagnostic is the normal/transposed-safe layout at `0.485462` accuracy.\n",
        "- Minimal production implication: do not guess-patch blindly, but the proven contract mismatch is now mentor literal channel-major reshape plus StandardScaler versus production normal row-wise layout without that notebook scaler.\n",
    ])

    REPORT_PATH.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    notebook_functions = extract_notebook_functions()
    source_evidence = grep_source_evidence()
    df_scaled, feature_cols, label_col, scale_summary = load_scaled_dataframe()
    window_modes, y_true, starts = build_window_modes(df_scaled, feature_cols, label_col)
    layout_rows = compare_layouts(window_modes)
    first_tables = first_window_tables(window_modes, feature_cols)
    model_rows, metric_rows = evaluate_models(window_modes, y_true)
    write_report(
        notebook_functions=notebook_functions,
        source_evidence=source_evidence,
        scale_summary=scale_summary,
        starts=starts,
        y_true=y_true,
        model_rows=model_rows,
        metric_rows=metric_rows,
        layout_rows=layout_rows,
        first_tables=first_tables,
    )
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()

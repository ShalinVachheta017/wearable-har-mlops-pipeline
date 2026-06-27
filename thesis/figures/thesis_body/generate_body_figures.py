from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


OUTDIR = Path(__file__).resolve().parent
PROJECT_ROOT = OUTDIR.parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "all_users_data_labeled.csv"
MODEL_INFO_FILE = PROJECT_ROOT / "models" / "pretrained" / "model_info.json"

PALETTE = {
    "navy": "#243b53",
    "slate": "#52606d",
    "teal": "#3a7d7c",
    "gold": "#c5a46d",
    "gray": "#9aa5b1",
    "grid": "#d9e2ec",
    "light_blue": "#d9e2ec",
    "light_teal": "#d3eceb",
    "light_gold": "#efe5d0",
    "light_gray": "#f0f4f8",
    "text": "#1f2933",
    "rust": "#b85c38",
}

SENSOR_COLUMNS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 10.5,
            "axes.edgecolor": PALETTE["slate"],
            "axes.linewidth": 0.8,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "grid.color": PALETTE["grid"],
            "grid.linewidth": 0.7,
            "grid.alpha": 0.85,
            "text.color": PALETTE["text"],
            "xtick.color": PALETTE["text"],
            "ytick.color": PALETTE["text"],
            "svg.fonttype": "none",
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    fig.savefig(OUTDIR / f"{stem}.svg", format="svg", bbox_inches="tight")
    fig.savefig(OUTDIR / f"{stem}.png", format="png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def add_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    *,
    facecolor: str,
    edgecolor: str,
    fontsize: float = 10.0,
    linestyle: str = "-",
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        transform=ax.transAxes,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.2,
        linestyle=linestyle,
    )
    ax.add_patch(patch)
    ax.text(
        x + 0.03 * w,
        y + h - 0.09 * h,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=fontsize + 0.4,
        fontweight="bold",
        color=edgecolor,
    )
    ax.text(
        x + w / 2,
        y + 0.44 * h,
        body,
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=fontsize,
    )


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str | None = None,
    linestyle: str = "-",
) -> None:
    patch = FancyArrowPatch(
        start,
        end,
        transform=ax.transAxes,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.4,
        linestyle=linestyle,
        color=color or PALETTE["slate"],
        connectionstyle="arc3,rad=0.0",
    )
    ax.add_patch(patch)


def load_dataset() -> pd.DataFrame:
    return pd.read_csv(DATA_FILE, usecols=["timestamp", *SENSOR_COLUMNS, "activity", "User"])


def find_activity_block(df: pd.DataFrame, activity: str, min_length: int = 200) -> pd.DataFrame:
    run_id = df["activity"].ne(df["activity"].shift()).cumsum()
    for _, block in df.groupby(run_id, sort=False):
        if block["activity"].iat[0] == activity and len(block) >= min_length:
            return block.iloc[:min_length].copy()
    raise ValueError(f"Could not find a block of length >= {min_length} for activity={activity!r}")


def build_dataset_overview() -> None:
    fig, ax = plt.subplots(figsize=(12.8, 6.6))
    ax.axis("off")
    ax.set_title("Dataset inputs and thesis data boundary", loc="left", pad=12)

    add_box(
        ax,
        0.04,
        0.58,
        0.24,
        0.24,
        "Raw session inputs",
        "Garmin wrist IMU\naccelerometer CSV\n+\ngyroscope CSV",
        facecolor=PALETTE["light_blue"],
        edgecolor=PALETTE["navy"],
    )
    add_box(
        ax,
        0.04,
        0.20,
        0.24,
        0.24,
        "Training source",
        "all_users_data_labeled.csv\n6 participants\n11 classes\n385,326 samples\n50 Hz",
        facecolor=PALETTE["light_teal"],
        edgecolor=PALETTE["teal"],
    )
    add_box(
        ax,
        0.38,
        0.58,
        0.24,
        0.24,
        "Sensor structure",
        "Ax, Ay, Az\nGx, Gy, Gz\nwrist-worn IMU",
        facecolor=PALETTE["light_gold"],
        edgecolor=PALETTE["gold"],
    )
    add_box(
        ax,
        0.38,
        0.20,
        0.24,
        0.24,
        "Label space",
        "8 anxiety-related\nbehaviors\n+\n3 baseline classes",
        facecolor=PALETTE["light_gray"],
        edgecolor=PALETTE["slate"],
    )
    add_box(
        ax,
        0.72,
        0.36,
        0.22,
        0.28,
        "Preprocessing entry point",
        "validation\nunit conversion\nresampling\nnormalization\nwindowing",
        facecolor="white",
        edgecolor=PALETTE["rust"],
    )

    add_arrow(ax, (0.28, 0.70), (0.38, 0.70), color=PALETTE["navy"])
    add_arrow(ax, (0.28, 0.32), (0.38, 0.32), color=PALETTE["teal"])
    add_arrow(ax, (0.62, 0.70), (0.72, 0.54), color=PALETTE["gold"])
    add_arrow(ax, (0.62, 0.32), (0.72, 0.46), color=PALETTE["slate"])

    ax.text(
        0.73,
        0.18,
        "Controlled lab-style labeled data define the\ntraining baseline; paired raw session files define\nthe reproducible inference path.",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=9.2,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": PALETTE["grid"]},
    )

    save_figure(fig, "fig_dataset_input_overview")


def build_raw_signal_examples(df: pd.DataFrame) -> None:
    hand_tapping = find_activity_block(df, "hand_tapping", min_length=200)
    sitting = find_activity_block(df, "sitting", min_length=200)
    time_s = np.arange(200) / 50.0

    fig, axes = plt.subplots(2, 2, figsize=(13.2, 7.8), sharex="col")
    fig.suptitle("Raw IMU signal examples from the labeled dataset", x=0.08, y=0.98, ha="left", fontsize=15, fontweight="bold")

    accel_colors = [PALETTE["navy"], PALETTE["teal"], PALETTE["gold"]]
    gyro_colors = [PALETTE["navy"], PALETTE["teal"], PALETTE["rust"]]

    for ax, block, title in (
        (axes[0, 0], hand_tapping, "Hand tapping - accelerometer"),
        (axes[0, 1], sitting, "Sitting - accelerometer"),
    ):
        for column, color in zip(["Ax_w", "Ay_w", "Az_w"], accel_colors):
            ax.plot(time_s, block[column].to_numpy(), label=column.replace("_w", ""), linewidth=1.15, color=color)
        ax.set_title(title, loc="left", fontsize=11)
        ax.set_ylabel("m/s^2")
        ax.grid(True)

    for ax, block, title in (
        (axes[1, 0], hand_tapping, "Hand tapping - gyroscope"),
        (axes[1, 1], sitting, "Sitting - gyroscope"),
    ):
        for column, color in zip(["Gx_w", "Gy_w", "Gz_w"], gyro_colors):
            ax.plot(time_s, block[column].to_numpy(), label=column.replace("_w", ""), linewidth=1.15, color=color)
        ax.set_title(title, loc="left", fontsize=11)
        ax.set_ylabel("deg/s")
        ax.set_xlabel("Time (s)")
        ax.grid(True)

    axes[0, 0].legend(frameon=False, ncol=3, loc="upper right")
    axes[1, 0].legend(frameon=False, ncol=3, loc="upper right")

    for ax in axes.flat:
        ax.spines[["top", "right"]].set_visible(False)

    save_figure(fig, "fig_raw_signal_examples")


def build_windowing_diagram(df: pd.DataFrame) -> None:
    signal = df["Ax_w"].iloc[:400].to_numpy()
    time_s = np.arange(signal.shape[0]) / 50.0

    fig, ax = plt.subplots(figsize=(12.8, 4.8))
    ax.plot(time_s, signal, color=PALETTE["navy"], linewidth=1.4)
    ax.set_title("Sliding-window segmentation for model input construction", loc="left", pad=12)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Ax_w")
    ax.grid(True)

    windows = [
        (0, 200, PALETTE["light_blue"], "Window 1"),
        (100, 300, PALETTE["light_teal"], "Window 2"),
        (200, 400, PALETTE["light_gold"], "Window 3"),
    ]
    for start, end, color, label in windows:
        ax.axvspan(start / 50.0, end / 50.0, color=color, alpha=0.55)
        ax.text((start + end) / 100.0, signal.max() + 0.8, label, ha="center", va="bottom", fontsize=9.1)

    ax.text(
        0.02,
        0.93,
        "window size = 200 samples = 4 s\nstep size = 100 samples = 50% overlap",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.2,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": PALETTE["grid"]},
    )
    ax.text(
        0.985,
        0.12,
        "Majority vote assigns one label per window.",
        transform=ax.transAxes,
        ha="right",
        va="center",
        fontsize=9.2,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": PALETTE["gold"]},
    )
    ax.spines[["top", "right"]].set_visible(False)

    save_figure(fig, "fig_windowing_diagram")


def build_input_tensor_heatmap(df: pd.DataFrame) -> None:
    window = df.loc[:199, SENSOR_COLUMNS].to_numpy(dtype=float)
    window = (window - window.mean(axis=0)) / window.std(axis=0)

    fig, ax = plt.subplots(figsize=(12.4, 4.5))
    im = ax.imshow(window.T, aspect="auto", cmap="RdBu_r", vmin=-2.5, vmax=2.5)
    ax.set_title("Illustrative (200, 6) input tensor", loc="left", pad=12)
    ax.set_xlabel("Time step")
    ax.set_ylabel("Sensor channel")
    ax.set_yticks(np.arange(len(SENSOR_COLUMNS)), [name.replace("_w", "") for name in SENSOR_COLUMNS])
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Standardized value")
    ax.text(
        0.985,
        1.02,
        "200 time steps x 6 channels",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9.2,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": PALETTE["grid"]},
    )
    save_figure(fig, "fig_input_tensor_heatmap")


def build_model_architecture() -> None:
    with MODEL_INFO_FILE.open("r", encoding="utf-8") as handle:
        model_info = json.load(handle)

    fig, ax = plt.subplots(figsize=(14.0, 4.6))
    ax.axis("off")
    ax.set_title("Baseline 1D-CNN + BiLSTM architecture", loc="left", pad=12)

    boxes = [
        ("Input", "(200, 6)"),
        ("CNN block 1", "Conv1D 16, k=2\nBatchNorm\nDropout 0.1"),
        ("CNN block 2", "Conv1D 32, k=2\nBatchNorm\nDropout 0.2"),
        ("BiLSTM 1", "64 units\nreturn_sequences=True\nBatchNorm + Dropout 0.2"),
        ("BiLSTM 2", "32 units\nreturn_sequences=True\nBatchNorm + Dropout 0.2"),
        ("Dense head", "Flatten\nDense 32 ReLU\nBatchNorm\nDropout 0.5"),
        ("Output", "Dense 11\nSoftmax"),
    ]
    colors = [
        PALETTE["light_blue"],
        PALETTE["light_teal"],
        PALETTE["light_teal"],
        PALETTE["light_gold"],
        PALETTE["light_gold"],
        PALETTE["light_gray"],
        "white",
    ]

    x_positions = np.linspace(0.03, 0.86, len(boxes))
    for idx, ((title, body), x_pos) in enumerate(zip(boxes, x_positions)):
        add_box(
            ax,
            float(x_pos),
            0.28,
            0.10,
            0.44,
            title,
            body,
            facecolor=colors[idx],
            edgecolor=PALETTE["navy"] if idx in (0, 6) else PALETTE["slate"],
            fontsize=8.6,
        )
        if idx < len(boxes) - 1:
            add_arrow(ax, (x_pos + 0.10, 0.50), (x_positions[idx + 1], 0.50), color=PALETTE["navy"])

    ax.text(
        0.03,
        0.10,
        f"Model info: input shape {tuple(model_info['input_shape'])}, output shape {tuple(model_info['output_shape'])}, total parameters {model_info['total_params']:,}.",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=9.2,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": PALETTE["grid"]},
    )

    save_figure(fig, "fig_model_architecture")


def build_training_workflow() -> None:
    fig, ax = plt.subplots(figsize=(13.2, 6.0))
    ax.axis("off")
    ax.set_title("Training workflow for the baseline model", loc="left", pad=12)

    add_box(
        ax,
        0.05,
        0.62,
        0.18,
        0.18,
        "Step 1",
        "Load labeled dataset\nand define grouped\nuser-fold CV",
        facecolor=PALETTE["light_blue"],
        edgecolor=PALETTE["navy"],
    )
    add_box(
        ax,
        0.30,
        0.62,
        0.18,
        0.18,
        "Step 2",
        "Within each fold:\ntrain users / held-out\nuser fold",
        facecolor=PALETTE["light_teal"],
        edgecolor=PALETTE["teal"],
    )
    add_box(
        ax,
        0.55,
        0.62,
        0.18,
        0.18,
        "Step 3",
        "Fit StandardScaler\non train only,\nthen transform val",
        facecolor=PALETTE["light_gold"],
        edgecolor=PALETTE["gold"],
    )
    add_box(
        ax,
        0.80,
        0.62,
        0.14,
        0.18,
        "Step 4",
        "Window data\n(200 samples,\n50% overlap)",
        facecolor=PALETTE["light_gray"],
        edgecolor=PALETTE["slate"],
    )

    add_box(
        ax,
        0.22,
        0.20,
        0.22,
        0.20,
        "Step 5",
        "Train 1D-CNN + BiLSTM\nwith Adam\nmax 100 epochs\nbatch size 64",
        facecolor="white",
        edgecolor=PALETTE["navy"],
    )
    add_box(
        ax,
        0.53,
        0.20,
        0.22,
        0.20,
        "Step 6",
        "Callbacks:\nearly stopping\nLR reduction\nrestore best weights",
        facecolor="white",
        edgecolor=PALETTE["rust"],
    )
    add_box(
        ax,
        0.80,
        0.20,
        0.14,
        0.20,
        "Step 7",
        "Store best model\nand fold metrics",
        facecolor="white",
        edgecolor=PALETTE["teal"],
    )

    add_arrow(ax, (0.23, 0.71), (0.30, 0.71), color=PALETTE["navy"])
    add_arrow(ax, (0.48, 0.71), (0.55, 0.71), color=PALETTE["navy"])
    add_arrow(ax, (0.73, 0.71), (0.80, 0.71), color=PALETTE["navy"])
    add_arrow(ax, (0.87, 0.62), (0.87, 0.40), color=PALETTE["navy"])
    add_arrow(ax, (0.80, 0.30), (0.75, 0.30), color=PALETTE["navy"])
    add_arrow(ax, (0.53, 0.30), (0.44, 0.30), color=PALETTE["navy"])

    ax.text(
        0.05,
        0.07,
        "Fixed seed = 42. The scaler is fitted only on the training partition in each fold, which protects the validation estimate from leakage.",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=9.2,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": PALETTE["grid"]},
    )

    save_figure(fig, "fig_training_workflow")


def main() -> None:
    apply_style()
    dataset = load_dataset()
    build_dataset_overview()
    build_raw_signal_examples(dataset)
    build_windowing_diagram(dataset)
    build_input_tensor_heatmap(dataset)
    build_model_architecture()
    build_training_workflow()


if __name__ == "__main__":
    main()

"""
Generate Chapter 4 F9 data-evidence figures from the real source CSVs.

Sources (4):
  - ADAMSense        data/anxiety_dataset.csv            (wrist *_w cols, accel in g)
  - Garmin users 1-6 data/all_users_data_labeled.csv     (accel already m/s^2)
  - User 7           data/labels/.../*_user7_ms2.csv      (accel already m/s^2)
  - Unlabeled       data/raw/2025-08-19-08-58-40_{accelerometer,gyroscope}.csv

Outputs (PNG, written next to this script):
  ch4_f9_class_distribution.png   Garmin 11-class distribution
  ch4_f9_channel_stats.png        per-source channel mean & std (accel + gyro)
  ch4_f9_magnitude_hist.png       accel/gyro magnitude histograms by source
  ch4_f9_source_counts.png        row counts per source

All accelerometer signals are normalized to m/s^2 (heuristic by median magnitude)
so the cross-source comparison is on a consistent physical unit. The detected unit
per source is printed so it can be verified.

Run:  python generate_ch4_data_figures.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]            # thesis/draw.io/ch4_data_figures -> repo root
DATA = ROOT / "data"
CH = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
G = 9.80665
LABEL_ORDER = ["ear_rubbing", "forehead_rubbing", "hair_pulling", "hand_scratching",
               "hand_tapping", "knuckles_cracking", "nail_biting", "nape_rubbing",
               "sitting", "smoking", "standing"]
COLORS = {"ADAMSense": "#4C72B0", "Garmin 1-6": "#DD8452",
          "User 7": "#55A868", "Unlabeled": "#C44E52"}
HIST_SAMPLE = 150_000


def normalize_accel(df):
    """Scale Ax,Ay,Az to m/s^2 using median accel-magnitude heuristic."""
    mag = float(np.sqrt(df["Ax"] ** 2 + df["Ay"] ** 2 + df["Az"] ** 2).median())
    if mag < 3:            factor, unit = G, "g"
    elif mag > 100:        factor, unit = 0.00980665, "milli-g"
    else:                  factor, unit = 1.0, "m/s^2"
    for c in ("Ax", "Ay", "Az"):
        df[c] = df[c] * factor
    return unit, factor


def load_adamsense():
    cols = ["Activity", "Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
    df = pd.read_csv(DATA / "anxiety_dataset.csv", usecols=cols)
    df = df.rename(columns={f"{c}_w": c for c in CH})
    df["activity"] = df["Activity"]
    return df[CH + ["activity"]]


def load_garmin(path):
    cols = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w", "activity"]
    df = pd.read_csv(path, usecols=cols)
    return df.rename(columns={f"{c}_w": c for c in CH})


def load_unlabelled():
    a = pd.read_csv(DATA / "raw/2025-08-19-08-58-40_accelerometer.csv",
                    usecols=["accel_x", "accel_y", "accel_z"])
    g = pd.read_csv(DATA / "raw/2025-08-19-08-58-40_gyroscope.csv",
                    usecols=["gyro_x", "gyro_y", "gyro_z"])
    n = min(len(a), len(g))
    df = pd.DataFrame({
        "Ax": a["accel_x"][:n].values, "Ay": a["accel_y"][:n].values, "Az": a["accel_z"][:n].values,
        "Gx": g["gyro_x"][:n].values, "Gy": g["gyro_y"][:n].values, "Gz": g["gyro_z"][:n].values,
    })
    return df


def main():
    print("Loading sources ...")
    sources = {
        "ADAMSense":  load_adamsense(),
        "Garmin 1-6": load_garmin(DATA / "all_users_data_labeled.csv"),
        "User 7":     load_garmin(DATA / "labels/2026-05-05-15-11-15/"
                                  "2026-05-05-15-11-15_labeled_50Hz_user7_ms2.csv"),
        "Unlabeled": load_unlabelled(),
    }
    units = {}
    for name, df in sources.items():
        unit, factor = normalize_accel(df)
        units[name] = unit
        print(f"  {name:11s}: {len(df):>9,} rows | accel detected as {unit} (x{factor})")

    # ---- stats table (printed; real numbers for the thesis) ----
    print("\nPer-source channel mean / std (accel m/s^2, gyro deg/s):")
    stats = {}
    for name, df in sources.items():
        stats[name] = {c: (df[c].mean(), df[c].std()) for c in CH}
        print(f"  {name}: " + ", ".join(f"{c}={df[c].mean():+.2f}±{df[c].std():.2f}" for c in CH))

    # ---- Figure 1: class distribution (Garmin) ----
    g = sources["Garmin 1-6"]
    counts = g["activity"].value_counts().reindex(LABEL_ORDER).fillna(0).astype(int)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(range(len(LABEL_ORDER)), counts.values, color="#4C72B0")
    ax.set_xticks(range(len(LABEL_ORDER)))
    ax.set_xticklabels(LABEL_ORDER, rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("Raw rows")
    ax.set_title("Class distribution — Garmin labelled users 1-6")
    for i, v in enumerate(counts.values):
        ax.text(i, v, f"{v/counts.sum()*100:.1f}%", ha="center", va="bottom", fontsize=7)
    fig.tight_layout()
    fig.savefig(HERE / "ch4_f9_class_distribution.png", dpi=200)
    plt.close(fig)

    # ---- Figure 2: channel mean & std (accel + gyro) ----
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    groups = [("Accelerometer (m/s$^2$)", ["Ax", "Ay", "Az"]),
              ("Gyroscope (deg/s)", ["Gx", "Gy", "Gz"])]
    names = list(sources)
    w = 0.2
    for row, stat in enumerate(["mean", "std"]):
        for col, (title, chans) in enumerate(groups):
            ax = axes[row][col]
            x = np.arange(len(chans))
            for k, name in enumerate(names):
                vals = [stats[name][c][0 if stat == "mean" else 1] for c in chans]
                ax.bar(x + (k - 1.5) * w, vals, w, label=name, color=COLORS[name])
            ax.set_xticks(x); ax.set_xticklabels(chans)
            ax.set_title(f"{title} — channel {stat}")
            ax.axhline(0, color="gray", lw=0.6)
            if row == 0 and col == 1:
                ax.legend(fontsize=8, ncol=2)
    fig.suptitle("Per-source channel statistics (train--serve distribution comparison)")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(HERE / "ch4_f9_channel_stats.png", dpi=200)
    plt.close(fig)

    # ---- Figure 3: magnitude histograms ----
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for name, df in sources.items():
        s = df.sample(min(HIST_SAMPLE, len(df)), random_state=0)
        amag = np.sqrt(s["Ax"] ** 2 + s["Ay"] ** 2 + s["Az"] ** 2)
        gmag = np.sqrt(s["Gx"] ** 2 + s["Gy"] ** 2 + s["Gz"] ** 2)
        axes[0].hist(amag, bins=80, density=True, histtype="step", lw=1.6,
                     label=name, color=COLORS[name], range=(0, 30))
        axes[1].hist(gmag, bins=80, density=True, histtype="step", lw=1.6,
                     label=name, color=COLORS[name], range=(0, 300))
    axes[0].set_title("Accel magnitude (m/s$^2$)"); axes[0].set_xlabel("|a|")
    axes[1].set_title("Gyro magnitude (deg/s)"); axes[1].set_xlabel("|g|")
    for ax in axes:
        ax.set_ylabel("density"); ax.legend(fontsize=8)
    fig.suptitle("Signal-magnitude distributions by source")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(HERE / "ch4_f9_magnitude_hist.png", dpi=200)
    plt.close(fig)

    # ---- Figure 4: row counts per source ----
    fig, ax = plt.subplots(figsize=(7, 4))
    names = list(sources); vals = [len(sources[n]) for n in names]
    ax.bar(names, vals, color=[COLORS[n] for n in names])
    ax.set_ylabel("Rows (50 Hz samples)"); ax.set_yscale("log")
    ax.set_title("Sample count per data source")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "ch4_f9_source_counts.png", dpi=200)
    plt.close(fig)

    print(f"\nDone. 4 figures written to {HERE}")


if __name__ == "__main__":
    main()

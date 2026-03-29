import os
import pandas as pd
import numpy as np
import json
from pathlib import Path


# ===============================
# CONFIG — EDIT THESE PATHS
# ===============================
DATA_ROOT = Path("data")

OUTPUT_DIR = Path("reports/data_analysis")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


print(*["=" * 60, "DATASET ANALYSIS", "=" * 60], sep="\n")

# ===============================
# HELPER FUNCTIONS
# ===============================

def detect_dataset_type(df: pd.DataFrame):
    if "label" in df.columns or "activity" in df.columns:
        return "labeled (training/research)"
    return "unlabeled (production)"


def basic_stats(df):
    stats = {}

    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        stats[col] = {
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "skew": float(df[col].skew()),
        }

    return stats


def label_distribution(df):
    if "label" in df.columns:
        return df["label"].value_counts(normalize=True).to_dict()
    if "activity" in df.columns:
        return df["activity"].value_counts(normalize=True).to_dict()
    return None


def analyze_file(file_path):
    print(f"\n🔍 Analyzing: {file_path}")

    try:
        if file_path.suffix == ".csv":
            df = pd.read_csv(file_path)
        elif file_path.suffix == ".xlsx":
            df = pd.read_excel(file_path)
        else:
            print("⚠️ Skipped (unsupported format)")
            return None

        dataset_type = detect_dataset_type(df)

        report = {
            "file": str(file_path),
            "shape": df.shape,
            "dataset_type": dataset_type,
            "stats": basic_stats(df),
            "label_distribution": label_distribution(df),
        }

        return report

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ===============================
# MAIN
# ===============================

def main():
    all_reports = []

    for root, dirs, files in os.walk(DATA_ROOT):
        for file in files:
            file_path = Path(root) / file

            if file_path.suffix in [".csv", ".xlsx"]:
                report = analyze_file(file_path)
                if report:
                    all_reports.append(report)

    # Save JSON
    json_path = OUTPUT_DIR / "dataset_analysis.json"
    with open(json_path, "w") as f:
        json.dump(all_reports, f, indent=4)

    print(f"\n✅ JSON report saved: {json_path}")

    # Save Markdown (THESIS READY)
    md_path = OUTPUT_DIR / "dataset_analysis.md"
    with open(md_path, "w") as f:
        for r in all_reports:
            f.write(f"# Dataset: {r['file']}\n")
            f.write(f"- Shape: {r['shape']}\n")
            f.write(f"- Type: {r['dataset_type']}\n\n")

            f.write("## Feature Stats\n")
            for col, stats in r["stats"].items():
                f.write(f"- {col}: mean={stats['mean']:.3f}, std={stats['std']:.3f}\n")

            if r["label_distribution"]:
                f.write("\n## Label Distribution\n")
                for k, v in r["label_distribution"].items():
                    f.write(f"- {k}: {v:.3f}\n")

            f.write("\n---\n\n")

    print(f"✅ Markdown report saved: {md_path}")


if __name__ == "__main__":
    main()
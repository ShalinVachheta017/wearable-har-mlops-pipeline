#!/usr/bin/env python3
"""
scripts/run_all_production_parity.py

Evaluation harness that runs the fixed production HAR pipeline on all raw Garmin
production sessions in data/raw, records logs and output artifacts per session,
and compares the results with the existing gpt.ipynb benchmark report.

Usage:
  python scripts/run_all_production_parity.py [--dry-run] [--limit N] [--session prefix]
"""

import argparse
import csv
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run production parity checks on all raw sessions."
    )
    parser.add_argument("--dry-run", action="store_true", help="List matching sessions without running anything.")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N valid pairs.")
    parser.add_argument("--session", type=str, default=None, help="Process only the session matching this prefix.")
    return parser.parse_args()

def extract_session_prefix(accelerometer_path: Path) -> str:
    """Extract the timestamp prefix from a filename."""
    # Matches '2025-07-16-21-03-13' from '2025-07-16-21-03-13_accelerometer.csv'
    # or '2025-03-23-15-23-10' from '2025-03-23-15-23-10-accelerometer_data.csv'
    name = accelerometer_path.name
    # Try replacing some known suffixes
    if "_accelerometer.csv" in name:
        return name.replace("_accelerometer.csv", "")
    elif "-accelerometer_data.csv" in name:
        return name.replace("-accelerometer_data.csv", "")
    elif "accelerometer" in name.lower():
        # Fallback regex extracting datetime pattern
        match = re.search(r"(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})", name)
        if match:
            return match.group(1)
    return name

def verify_config():
    """Verify that the production pipeline config has normalization/gravity removal/calibration turned off."""
    config_path = PROJECT_ROOT / "config" / "pipeline_config.yaml"
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return False
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    prep = config.get("preprocessing", {})
    issues = []
    
    # We want these to be False or None in YAML
    if prep.get("enable_normalization", False):
        issues.append("enable_normalization is True (should be False)")
    if prep.get("enable_gravity_removal", False):
        issues.append("enable_gravity_removal is True (should be False)")
    if prep.get("enable_calibration", False) or prep.get("enable_domain_calibration", False):
        issues.append("calibration is True (should be False)")
        
    if issues:
        logger.error(f"Config check failed! Please fix {config_path}:\n  - " + "\n  - ".join(issues))
        return False
        
    return True

def run_pipeline(session_id, accel_path, gyro_path, session_folder):
    """Invoke the production pipeline with the specified files."""
    cmd = [
        sys.executable,
        os.path.join(PROJECT_ROOT, "run_pipeline.py"),
        "--accel-file", str(accel_path),
        "--gyro-file", str(gyro_path),
        "--no-normalization",  # Extra safeguard
        "--no-unit-conversion" # No wait we DO need unit conversion for the inference contract, let's remove this flag
    ]
    # Unit conversion milliG -> m/s2 should be ON (default in config or no-op flag).
    # The requirement: accelerometer: milli-g * 0.00981 -> m/s2
    
    # We also remove --no-unit-conversion from cmd above so it defaults to true in config
    cmd_run = [
        sys.executable,
        os.path.join(PROJECT_ROOT, "run_pipeline.py"),
        "--accel-file", str(accel_path),
        "--gyro-file", str(gyro_path),
    ]

    log_path = session_folder / "pipeline.log"
    logger.info(f"Running pipeline for {session_id}...")
    
    env = os.environ.copy()
    
    with open(log_path, "w") as log_f:
        # Popen to capture both stdout and stderr
        process = subprocess.Popen(
            cmd_run,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            cwd=str(PROJECT_ROOT)
        )
        for line in process.stdout:
            sys.stdout.write(line)
            log_f.write(line)
            
        process.wait()
        
    # Copy outputs from outputs/ to the session folder
    outputs_dir = PROJECT_ROOT / "outputs" / "inference"
    monitoring_dir = PROJECT_ROOT / "outputs" / "monitoring"
    trigger_dir = PROJECT_ROOT / "outputs" / "trigger"
    
    copied = []
    # Using specific copied items to know what outputs were generated
    for src_dir in [outputs_dir, monitoring_dir, trigger_dir]:
        if src_dir.exists():
            for filepath in src_dir.glob("*"):
                if filepath.is_file():
                    shutil.copy2(filepath, session_folder / filepath.name)
                    copied.append(filepath.name)
                    
    return process.returncode == 0, copied

def parse_pipeline_outputs(session_id, accel_path, gyro_path, session_folder):
    """Parse out session metrics from the outputs and log."""
    result = {
        "session_id": session_id,
        "accel_file": accel_path.name,
        "gyro_file": gyro_path.name,
        "number_of_windows": None,
        "mean_confidence_raw": None,
        "mean_confidence_after_temperature": None,
        "uncertain_percentage": None,
        "number_of_classes_predicted": None,
        "top1_activity": None,
        "top1_percentage": None,
        "top1_confidence": None,
        "top2_activity": None,
        "top2_percentage": None,
        "top2_confidence": None,
        "top3_activity": None,
        "top3_percentage": None,
        "collapse_detected": False,
        "monitoring_status": None,
        "trigger_decision": None,
        "normalization_enabled_from_log": False,
        "model_path": None,
        "input_shape": None,
        "output_shape": None,
    }
    
    log_file = session_folder / "pipeline.log"
    if log_file.exists():
        with open(log_file, "r") as f:
            for line in f:
                lower_line = line.lower()
                if "normalization" in lower_line and "enabled" in lower_line and "disabled" not in lower_line:
                    if "enable_normalization: false" not in line:
                        result["normalization_enabled_from_log"] = True
                if "model:" in lower_line or "loaded model" in lower_line:
                    # crude extraction
                    result["model_path"] = line.strip()

    predictions_file = session_folder / "production_window_predictions.csv"
    if predictions_file.exists():
        df = pd.read_csv(predictions_file)
        if len(df) > 0:
            result["number_of_windows"] = len(df)
            
            # Identify columns
            pred_col = "predicted_class" if "predicted_class" in df.columns else "prediction"
            if "activity" in df.columns:
                pred_col = "activity"
                
            conf_col = "confidence" if "confidence" in df.columns else "probability"
            if "calibrated_confidence" in df.columns:
                conf_col = "calibrated_confidence"
                
            result["mean_confidence_raw"] = df[conf_col].mean() if conf_col in df.columns else None
            
            if conf_col in df.columns:
                uncertain_windows = (df[conf_col] < 0.60).sum()
                result["uncertain_percentage"] = (uncertain_windows / len(df)) * 100
                
            if pred_col in df.columns:
                counts = df[pred_col].value_counts(normalize=True) * 100
                val_counts = df[pred_col].value_counts()
                classes = counts.index.tolist()
                result["number_of_classes_predicted"] = len(classes)
                
                # Check collapse
                if len(classes) == 1 and counts.iloc[0] > 98:
                    result["collapse_detected"] = True
                    
                if len(classes) > 0:
                    result["top1_activity"] = classes[0]
                    result["top1_percentage"] = counts.iloc[0]
                    if conf_col in df.columns:
                        result["top1_confidence"] = df[df[pred_col] == classes[0]][conf_col].mean()
                if len(classes) > 1:
                    result["top2_activity"] = classes[1]
                    result["top2_percentage"] = counts.iloc[1]
                    if conf_col in df.columns:
                        result["top2_confidence"] = df[df[pred_col] == classes[1]][conf_col].mean()
                if len(classes) > 2:
                    result["top3_activity"] = classes[2]
                    result["top3_percentage"] = counts.iloc[2]
                    
    return result

def parse_gpt_report():
    """Extract baseline metrics from INFERENCE_ANALYSIS_REPORT.md"""
    # Since we need to know the baseline, we implement a simple parser for the GPT report table.
    report_paths = [
        PROJECT_ROOT / "reports" / "INFERENCE_ANALYSIS_REPORT.md",
        PROJECT_ROOT / "INFERENCE_ANALYSIS_REPORT.md"
    ]
    report_path = None
    for p in report_paths:
        if p.exists():
            report_path = p
            break
            
    if not report_path:
        logger.warning("No INFERENCE_ANALYSIS_REPORT.md found. Benchmarking will be skipped.")
        return {}
        
    baselines = {}
    with open(report_path, "r") as f:
        # Simple markdown table parser looking for session IDs
        lines = f.readlines()
        in_table = False
        headers = []
        for line in lines:
            line = line.strip()
            if line.startswith("|") and "Session" in line:
                in_table = True
                headers = [h.strip().lower() for h in line.split("|")[1:-1]]
                continue
            if line.startswith("|---"):
                continue
            if in_table and line.startswith("|"):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if not cols:
                    in_table = False
                    continue
                session_raw = cols[0]
                # Clean up bolding markdown
                session = session_raw.replace("**", "")
                
                # We need to map table columns to our baseline vars.
                # Assuming table has: Windows, Classes, Top-1, Uncertain %
                # We just do a best effort matching
                baseline_data = {
                    "gpt_windows": None,
                    "gpt_classes": None,
                    "gpt_top1_activity": None,
                    "gpt_top1_pct": None,
                    "gpt_uncertain_pct": None,
                    "gpt_mean_conf": None
                }
                
                for c, h in zip(cols, headers):
                    if "window" in h.lower():
                        try:
                            baseline_data["gpt_windows"] = int(c)
                        except: pass
                    elif "class" in h.lower():
                        try:
                            baseline_data["gpt_classes"] = int(c)
                        except: pass
                    elif "top-1" in h.lower() and "activity" in h.lower(): # e.g. "Walking (65%)"
                        match = re.search(r"([A-Za-z_]+).*?(\d+(\.\d+)?)%", c)
                        if match:
                            baseline_data["gpt_top1_activity"] = match.group(1)
                            baseline_data["gpt_top1_pct"] = float(match.group(2))
                        else:
                            baseline_data["gpt_top1_activity"] = c
                    elif "uncertain" in h.lower():
                        try:
                            val = c.replace("%", "").strip()
                            baseline_data["gpt_uncertain_pct"] = float(val) if val else None
                        except: pass
                        
                if "2025" in session: # simple check to ensure it's a session row
                    baselines[session] = baseline_data
                    
    return baselines

def compare_results(pipeline_data, baseline_data):
    """Compare pipeline run vs GPT baseline."""
    # Defaults
    diff = {
        "gpt_windows": None, "pipeline_windows": pipeline_data.get("number_of_windows"), "window_diff": None,
        "gpt_mean_conf": None, "pipeline_mean_conf": pipeline_data.get("mean_confidence_raw"), "mean_conf_diff": None,
        "gpt_uncertain_pct": None, "pipeline_uncertain_pct": pipeline_data.get("uncertain_percentage"),
        "gpt_classes": None, "pipeline_classes": pipeline_data.get("number_of_classes_predicted"),
        "gpt_top1_activity": None, "pipeline_top1_activity": pipeline_data.get("top1_activity"),
        "gpt_top1_pct": None, "pipeline_top1_pct": pipeline_data.get("top1_percentage"), "top1_pct_diff": None,
        "parity_status": "MISSING_BASELINE", "notes": []
    }
    
    if not baseline_data:
        diff["notes"].append("No baseline found")
        return diff
        
    diff.update({
        "gpt_windows": baseline_data.get("gpt_windows"),
        "gpt_mean_conf": baseline_data.get("gpt_mean_conf"),
        "gpt_uncertain_pct": baseline_data.get("gpt_uncertain_pct"),
        "gpt_classes": baseline_data.get("gpt_classes"),
        "gpt_top1_activity": baseline_data.get("gpt_top1_activity"),
        "gpt_top1_pct": baseline_data.get("gpt_top1_pct"),
    })
    
    # Compute diffs
    if diff["gpt_windows"] is not None and diff["pipeline_windows"] is not None:
        diff["window_diff"] = abs(diff["gpt_windows"] - diff["pipeline_windows"])
    if diff["gpt_mean_conf"] is not None and diff["pipeline_mean_conf"] is not None:
        diff["mean_conf_diff"] = abs(diff["gpt_mean_conf"] - diff["pipeline_mean_conf"])
    if diff["gpt_top1_pct"] is not None and diff["pipeline_top1_pct"] is not None:
        diff["top1_pct_diff"] = abs(diff["gpt_top1_pct"] - diff["pipeline_top1_pct"])
        
    # Evaluate Parity
    notes = []
    status = "PASS"
    
    # Helper extract text
    def safe_upper(v): return str(v).upper() if v else ""
    
    pipeline_top1_act = safe_upper(diff["pipeline_top1_activity"])
    gpt_top1_act = safe_upper(diff["gpt_top1_activity"])
    pipeline_top2_act = safe_upper(pipeline_data.get("top2_activity"))
    
    # PASS criteria: top1 activity matches OR top1/top2 pair matches
    act_match = (pipeline_top1_act in gpt_top1_act or gpt_top1_act in pipeline_top1_act)
    if not act_match and pipeline_top2_act and (pipeline_top2_act in gpt_top1_act or gpt_top1_act in pipeline_top2_act):
        act_match = True
        notes.append("Top-1 / Top-2 swapped")
        status = "REVIEW"
        
    # Diff criteria
    if diff["mean_conf_diff"] is not None and diff["mean_conf_diff"] > 0.03:
        status = "FAIL" if diff["mean_conf_diff"] > 0.1 else "REVIEW"
        notes.append(f"Mean conf diff {diff['mean_conf_diff']:.3f} > 0.03")
        
    if diff["top1_pct_diff"] is not None and diff["top1_pct_diff"] > 7.0:
        notes.append(f"Top1 pct diff {diff['top1_pct_diff']:.1f}% > 7%")
        status = "REVIEW" if diff["top1_pct_diff"] <= 15.0 else "FAIL"

    if diff["window_diff"] is not None and diff["gpt_windows"]:
        pct_diff = diff["window_diff"] / diff["gpt_windows"]
        if pct_diff > 0.01 and diff["window_diff"] > 10:
            notes.append(f"Window diff {diff['window_diff']} exceeds 1% or 10")
            status = "REVIEW" if pct_diff < 0.05 else "FAIL"
            
    # Collapse criteria
    if pipeline_data.get("collapse_detected"):
        if diff["gpt_classes"] is not None and diff["gpt_classes"] > 2:
            status = "FAIL"
            notes.append(f"Single-class collapse detected but GPT predicted {diff['gpt_classes']} classes")
            
    # Rules
    if pipeline_data.get("normalization_enabled_from_log"):
        status = "FAIL"
        notes.append("Normalization scaler applied in log!")
        
    if not act_match:
        status = "FAIL"
        notes.append("Top-1 activity completely mismatched")
        
    diff["parity_status"] = status
    diff["notes"] = "; ".join(notes)
    
    return diff

def main():
    args = parse_args()
    
    if not verify_config():
        if not args.dry_run:
            sys.exit(1)
            
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_dir = PROJECT_ROOT / "evidence" / f"inference_parity_all_{timestamp}"
    
    data_dir = PROJECT_ROOT / "data" / "raw"
    if not data_dir.exists():
        logger.error(f"Raw data directory not found: {data_dir}")
        sys.exit(1)
        
    accel_files = list(data_dir.glob("*accelerometer*.csv")) + list(data_dir.glob("*accelerometer*.xlsx"))
    
    pairs = []
    failed_sessions = []
    
    for accel in accel_files:
        prefix = extract_session_prefix(accel)
        
        gyro_matches = list(data_dir.glob(f"{prefix}*gyroscope*.csv")) + list(data_dir.glob(f"{prefix}*gyroscope*.xlsx"))
        if not gyro_matches:
            failed_sessions.append({
                "session_id": prefix, 
                "accel_file": accel.name,
                "gyro_file": None,
                "reason": "Missing gyroscope file"
            })
            continue
            
        pairs.append({
            "session_id": prefix,
            "accel": accel,
            "gyro": gyro_matches[0]
        })
        
    logger.info(f"Found {len(accel_files)} accelerometer files. Paired {len(pairs)} complete sessions.")
    
    if args.session:
        pairs = [p for p in pairs if args.session in p["session_id"]]
        logger.info(f"Filtered to {len(pairs)} pairs using session={args.session}")
        
    if args.limit:
        pairs = pairs[:args.limit]
        logger.info(f"Limited to {len(pairs)} pairs.")
        
    if args.dry_run:
        for p in pairs:
            print(f"- {p['session_id']}")
            print(f"  Accel: {p['accel'].name}")
            print(f"  Gyro: {p['gyro'].name}")
        return
        
    evidence_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using evidence directory: {evidence_dir}")
    
    baselines = parse_gpt_report()
    logger.info(f"Loaded {len(baselines)} baselines from report.")
    
    all_results = []
    all_comparison_rows = []
    
    metrics_counters = {"PASS": 0, "REVIEW": 0, "FAIL": 0, "MISSING_BASELINE": 0}
    
    for pair in pairs:
        session_id = pair["session_id"]
        sess_dir = evidence_dir / session_id
        sess_dir.mkdir(exist_ok=True)
        
        success, copied = run_pipeline(session_id, pair["accel"], pair["gyro"], sess_dir)
        if not success:
            failed_sessions.append({
                "session_id": session_id,
                "accel_file": pair["accel"].name,
                "gyro_file": pair["gyro"].name,
                "reason": "Pipeline execution failed or crashed"
            })
            # Try parsing anyway for partial output
            
        try:
            parsed = parse_pipeline_outputs(session_id, pair["accel"], pair["gyro"], sess_dir)
            all_results.append(parsed)
            
            baseline = next((v for k, v in baselines.items() if k in session_id or session_id in k), None)
            comp = compare_results(parsed, baseline)
            
            row = {"session_id": session_id}
            row.update(comp)
            all_comparison_rows.append(row)
            
            metrics_counters[comp["parity_status"]] = metrics_counters.get(comp["parity_status"], 0) + 1
            
        except Exception as e:
            failed_sessions.append({
                "session_id": session_id,
                "accel_file": pair["accel"].name,
                "gyro_file": pair["gyro"].name,
                "reason": f"Parsing failed: {str(e)}"
            })
            
    # Write outputs
    if all_results:
        df_manifest = pd.DataFrame(all_results)
        df_manifest.to_csv(evidence_dir / "run_manifest.csv", index=False)
        
    if all_comparison_rows:
        df_comp = pd.DataFrame(all_comparison_rows)
        # Reorder columns as requested
        cols = [
            "session_id", "gpt_windows", "pipeline_windows", "window_diff",
            "gpt_mean_conf", "pipeline_mean_conf", "mean_conf_diff",
            "gpt_uncertain_pct", "pipeline_uncertain_pct",
            "gpt_classes", "pipeline_classes",
            "gpt_top1_activity", "pipeline_top1_activity",
            "gpt_top1_pct", "pipeline_top1_pct", "top1_pct_diff",
            "parity_status", "notes"
        ]
        # Keep only existing columns
        final_cols = [c for c in cols if c in df_comp.columns]
        df_comp[final_cols].to_csv(evidence_dir / "final_comparison_summary.csv", index=False)
        
    if failed_sessions:
        df_failed = pd.DataFrame(failed_sessions)
        df_failed.to_csv(evidence_dir / "failed_sessions.csv", index=False)
        
    print("\n" + "="*50)
    print("FINAL SUMMARY")
    print("="*50)
    print(f"Total sessions found:       {len(accel_files)}")
    print(f"Sessions run successfully:  {len(all_results)}")
    print(f"Skipped/Failed sessions:    {len(failed_sessions)}")
    print(f"PASS count:                 {metrics_counters.get('PASS', 0)}")
    print(f"REVIEW count:               {metrics_counters.get('REVIEW', 0)}")
    print(f"FAIL count:                 {metrics_counters.get('FAIL', 0)}")
    print(f"MISSING BASELINE count:     {metrics_counters.get('MISSING_BASELINE', 0)}")
    print(f"Evidence folder:            {evidence_dir}")
    print("="*50)

if __name__ == "__main__":
    main()

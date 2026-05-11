import pandas as pd
import json
import glob
import os

def analyze_latest_predictions():
    # 1. Find the latest artifact run
    artifact_dirs = sorted(glob.glob("artifacts/*"), key=os.path.getmtime, reverse=True)
    if not artifact_dirs:
        print("No pipeline runs found.")
        return
    
    latest_run = artifact_dirs[0]
    print(f"Analyzing Latest Unlabeled Run: {os.path.basename(latest_run)}")
    
    # 2. Get inference summary
    summary_path = os.path.join(latest_run, "inference", "inference_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            summary = json.load(f)
            print(f"\n--- OVERALL INFERENCE SUMMARY ---")
            print(f"Total Predictions:    {summary['n_predictions']} windows")
            print(f"Average Confidence:   {summary['confidence_stats']['mean'] * 100:.1f}%")
            print(f"Dominant Activity:    {summary['dominant_class']} ({summary['dominant_pct']:.1f}%)")
            
            print(f"\n--- ACTIVITY PREDICTION FREQUENCY ---")
            for activity, count in summary['activity_distribution'].items():
                share = summary['activity_share'][activity] * 100
                print(f"  {activity:20}: {count:4d} windows ({share:4.1f}%)")

    # 3. Analyze raw predictions CSV for confidence breakdown
    pred_files = glob.glob(os.path.join(latest_run, "inference", "predictions_*.csv"))
    if pred_files:
        pred_csv = pred_files[0]
        df = pd.read_csv(pred_csv)
        
        # Hardcoded fallback mapping
        class_names = {
            0: 'ear_rubbing', 1: 'forehead_rubbing', 2: 'hair_pulling', 
            3: 'hand_scratching', 4: 'hand_tapping', 5: 'knuckles_cracking', 
            6: 'nail_biting', 7: 'nape_rubbing', 8: 'sitting', 9: 'smoking', 10: 'standing'
        }
        
        # Determine mapping from metadata if available
        meta_path = pred_csv.replace(".csv", "_metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                if 'class_mapping' in meta and meta['class_mapping']:
                    class_names = {int(k): v for k, v in meta['class_mapping'].items()}

        # Add Activity Name Column
        df['Activity'] = df['predicted_class'].map(class_names)
        
        print("\n--- PREDICTED CONFIDENCE PER ACTIVITY ---")
        res = df.groupby('Activity').agg(
            Count=('window_id', 'count'),
            Mean_Confidence=('confidence', 'mean')
        ).sort_values('Count', ascending=False)
        
        res['Mean_Confidence'] = (res['Mean_Confidence'] * 100).map('{:.1f}%'.format)
        print(res.to_string())

if __name__ == "__main__":
    analyze_latest_predictions()

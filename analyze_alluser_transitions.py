import pandas as pd
import numpy as np
from collections import defaultdict

# Read the production training dataset (all users)
df = pd.read_csv('data/processed/fused_all_users_data_labeled_50Hz.csv')

print(f'Total rows: {len(df)}')
print(f'Columns: {list(df.columns)}')
print(f'Date range: {df["timestamp_iso"].min()} to {df["timestamp_iso"].max()}')

# Convert timestamp to datetime (use timestamp_iso or true_time)
df['ts'] = pd.to_datetime(df['timestamp_iso'] if 'timestamp_iso' in df.columns else df['true_time'])
df['delta_ms'] = df['ts'].diff().dt.total_seconds() * 1000

print(f'\n--- Time Delta Statistics (ms) ---')
print(f'Min delta: {df["delta_ms"].min():.2f} ms')
print(f'Max delta: {df["delta_ms"].max():.2f} ms')
print(f'Mean delta: {df["delta_ms"].mean():.2f} ms')
print(f'Median delta: {df["delta_ms"].median():.2f} ms')
print(f'Std delta: {df["delta_ms"].std():.2f} ms')

# Activity statistics
print(f'\n--- Activity Distribution ---')
activities = df['activity'].unique()
print(f'Total unique activities: {len(activities)}')
print(df['activity'].value_counts().to_string())

# Analyze activity transitions and gaps
print(f'\n--- ACTIVITY TRANSITIONS AND GAPS ANALYSIS ---')

activity_transitions = []
large_gaps = []

for i in range(1, len(df)):
    if df['activity'].iloc[i] != df['activity'].iloc[i-1]:
        activity_transitions.append({
            'row': i,
            'prev_activity': df['activity'].iloc[i-1],
            'curr_activity': df['activity'].iloc[i],
            'gap_ms': df['delta_ms'].iloc[i],
            'timestamp': df['timestamp_iso'].iloc[i] if 'timestamp_iso' in df.columns else df['true_time'].iloc[i]
        })

print(f'\nTotal activity transitions: {len(activity_transitions)}')

# Statistics on transition gaps
transition_gaps = [t['gap_ms'] for t in activity_transitions]
print(f'\nTransition gap statistics:')
print(f'  Mean gap: {np.mean(transition_gaps):.1f} ms')
print(f'  Median gap: {np.median(transition_gaps):.1f} ms')
print(f'  Min gap: {np.min(transition_gaps):.1f} ms')
print(f'  Max gap: {np.max(transition_gaps):.1f} ms')
print(f'  Std gap: {np.std(transition_gaps):.1f} ms')

# Gaps >= 50ms (large transitions)
large_transition_gaps = [t for t in activity_transitions if t['gap_ms'] >= 50]
print(f'\nLarge transitions (gap >= 50ms): {len(large_transition_gaps)}')

# Gaps >= 1000ms (longer breaks)
extra_large_gaps = [t for t in activity_transitions if t['gap_ms'] >= 1000]
print(f'Extra-large transitions (gap >= 1000ms): {len(extra_large_gaps)}')

if len(extra_large_gaps) > 0:
    print(f'\nTop 10 extra-large transitions:')
    for t in sorted(extra_large_gaps, key=lambda x: x['gap_ms'], reverse=True)[:10]:
        print(f"  {t['prev_activity']:20} → {t['curr_activity']:20} gap={t['gap_ms']:.0f} ms ({t['gap_ms']/1000:.2f}s)")

# Transition pair frequency
print(f'\n--- Most Frequent Activity Transition Pairs ---')
transition_pairs = defaultdict(int)
for t in activity_transitions:
    pair = f"{t['prev_activity']} → {t['curr_activity']}"
    transition_pairs[pair] += 1

for pair, count in sorted(transition_pairs.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"  {count:4d}x  {pair}")

# Per-activity analysis
print(f'\n--- Per-Activity Session Analysis ---')
print(f'(showing sample count for each activity)\n')

for activity in sorted(activities):
    activity_df = df[df['activity'] == activity]
    outgoing_transitions = len([t for t in activity_transitions if t['prev_activity'] == activity])
    incoming_transitions = len([t for t in activity_transitions if t['curr_activity'] == activity])
    
    if len(activity_df) > 0:
        samples = len(activity_df)
        
        print(f'{activity:25} samples={samples:6d}  incoming={incoming_transitions:4d}x  outgoing={outgoing_transitions:4d}x')

# Normal vs anomalous sampling
print(f'\n--- Sampling Rate Analysis ---')
expected_deltas = df["delta_ms"][df["delta_ms"].notna()]
normal_deltas = expected_deltas[(expected_deltas >= 19.5) & (expected_deltas <= 20.5)]
print(f'Normal 20ms deltas (50Hz): {len(normal_deltas)} ({100*len(normal_deltas)/len(expected_deltas):.1f}%)')
print(f'Anomalies (not 20ms): {len(expected_deltas) - len(normal_deltas)}')

# Anomaly breakdown
anomalies = expected_deltas[(expected_deltas < 19.5) | (expected_deltas > 20.5)]
print(f'\nAnomaly distribution:')
print(f'  < 19.5 ms: {len(anomalies[anomalies < 19.5])}')
print(f'  20.5–50 ms: {len(anomalies[(anomalies > 20.5) & (anomalies <= 50)])}')
print(f'  50–100 ms: {len(anomalies[(anomalies > 50) & (anomalies <= 100)])}')
print(f'  100–1000 ms: {len(anomalies[(anomalies > 100) & (anomalies <= 1000)])}')
print(f'  > 1000 ms: {len(anomalies[anomalies > 1000])}')

print(f'\n--- Summary For Thesis ---')
print(f'Production dataset (all_users) has {len(df):,} samples across {len(activities)} activities')
print(f'Duration: ~{(df["ts"].max() - df["ts"].min()).total_seconds() / 3600:.1f} hours of IMU data')
print(f'Activity transitions: {len(activity_transitions)} (mean gap {np.mean(transition_gaps):.0f} ms)')
print(f'Large transitions (>50ms): {len(large_transition_gaps)} ({100*len(large_transition_gaps)/len(activity_transitions):.1f}%)')
print(f'Data quality: {100*len(normal_deltas)/len(expected_deltas):.1f}% normal sampling, {100*(len(expected_deltas)-len(normal_deltas))/len(expected_deltas):.1f}% anomalies')

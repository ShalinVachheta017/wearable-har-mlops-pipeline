import pandas as pd
import numpy as np

# Read the CSV
df = pd.read_csv('data/raw/2026-05-05-15-11-15_labeled_50Hz_user7.csv')
print(f'Total rows: {len(df)}')
print(f'Columns: {list(df.columns)}')
print(f'\n--- Timestamp Analysis ---')
print(f'First timestamp: {df.iloc[0]["timestamp"]}')
print(f'Last timestamp: {df.iloc[-1]["timestamp"]}')

# Convert to datetime
df['ts'] = pd.to_datetime(df['timestamp'])
df['delta_ms'] = df['ts'].diff().dt.total_seconds() * 1000

print(f'\n--- Time Delta Statistics (ms) ---')
print(f'Min delta: {df["delta_ms"].min():.2f} ms')
print(f'Max delta: {df["delta_ms"].max():.2f} ms')
print(f'Mean delta: {df["delta_ms"].mean():.2f} ms')
print(f'Median delta: {df["delta_ms"].median():.2f} ms')
print(f'Std delta: {df["delta_ms"].std():.2f} ms')

# Expected delta at 50Hz = 20ms
print(f'\n--- Expected delta at 50Hz: 20 ms ---')
expected_deltas = df["delta_ms"][df["delta_ms"].notna()]
normal_deltas = expected_deltas[(expected_deltas >= 19.5) & (expected_deltas <= 20.5)]
print(f'Normal 20ms deltas: {len(normal_deltas)} ({100*len(normal_deltas)/len(expected_deltas):.1f}%)')

# Find anomalies (gaps significantly different from 20ms)
print(f'\n--- Anomalies (delta != 20ms within tolerance) ---')
anomalies = df[(df['delta_ms'] < 19.5) | (df['delta_ms'] > 20.5)]
print(f'Total anomalies: {len(anomalies)}')
if len(anomalies) > 0:
    print('\nTop 20 anomalies:')
    print(anomalies[['timestamp', 'activity', 'delta_ms']].head(20).to_string())
    
    # Large gaps (> 50ms)
    large_gaps = anomalies[anomalies['delta_ms'] > 50]
    print(f'\nLarge gaps (>50ms): {len(large_gaps)}')
    if len(large_gaps) > 0:
        print(large_gaps[['timestamp', 'activity', 'delta_ms']].to_string())

# Check for duplicate timestamps
print(f'\n--- Duplicate Timestamps ---')
dupes = df[df.duplicated(subset=['timestamp'], keep=False)].sort_values('timestamp')
print(f'Total duplicate rows: {len(dupes)}')
if len(dupes) > 0:
    print('Duplicate timestamps:')
    print(dupes[['timestamp', 'activity', 'Ax_w']].head(20).to_string())

# Activity distribution
print(f'\n--- Activity Distribution ---')
print(df['activity'].value_counts().to_string())

# Session analysis (time spans for each activity)
print(f'\n--- Activity Time Spans ---')
for activity in sorted(df['activity'].unique()):
    activity_df = df[df['activity'] == activity]
    start = activity_df.iloc[0]['timestamp']
    end = activity_df.iloc[-1]['timestamp']
    duration = (pd.to_datetime(activity_df.iloc[-1]['timestamp']) - pd.to_datetime(activity_df.iloc[0]['timestamp'])).total_seconds()
    print(f'{activity}: {start} to {end} ({duration:.1f}s)')

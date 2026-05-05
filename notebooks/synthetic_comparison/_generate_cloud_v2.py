"""
Regenerate synthetic_other_input.csv (Synth Cloud) so its sensor distribution
matches the training distribution.

Method: same AR(1) per-user per-activity generator as Synth Codex, but:
  - Different RNG seed (20260416 vs Codex seed 20260330)
  - Slight global scale perturbation (±10%) per sensor channel so the two
    synthetic sets are not identical — some natural variation, same ballpark
  - Source: all_users_data_labeled_actual_input.csv (same as Codex)

Overwrites data/synthetic_runs/synthetic_other_input.csv
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT   = Path('../..')
SOURCE = ROOT / 'data/synthetic_runs/all_users_data_labeled_actual_input.csv'
OUTPUT = ROOT / 'data/synthetic_runs/synthetic_other_input.csv'

SENSOR_COLS     = ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz']
SAMPLE_RATE_HZ  = 50
STEP_MS         = 1000 // SAMPLE_RATE_HZ
GAP_MS          = 2000
SEED            = 20260416   # different from Codex (20260330)
USER_ID_OFFSET  = 200        # different from Codex (100) so user ids don't clash

# Per-channel scale factor:  drawn once from Uniform(0.90, 1.10) so the
# Cloud dataset is in the same ballpark as training but not a carbon copy.
rng_scale = np.random.default_rng(SEED + 99)
CHANNEL_SCALE = rng_scale.uniform(0.90, 1.10, size=len(SENSOR_COLS))
print(f'Channel scale factors (Cloud variation): {dict(zip(SENSOR_COLS, CHANNEL_SCALE.round(3)))}')


# ── Helpers (mirrors generate_synthetic_data.py) ──────────────────────────────
@dataclass
class GroupProfile:
    mean: np.ndarray
    cov: np.ndarray
    innovation_cov: np.ndarray
    lag1_rho: np.ndarray
    min_vals: np.ndarray
    max_vals: np.ndarray
    count: int


def stabilize_cov(m: np.ndarray, floor: float = 1e-6) -> np.ndarray:
    sym = (m + m.T) / 2.0
    ev, evec = np.linalg.eigh(sym)
    return evec @ np.diag(np.clip(ev, floor, None)) @ evec.T


def lag1_rho(values: np.ndarray) -> np.ndarray:
    if len(values) < 3:
        return np.full(values.shape[1], 0.85)
    rho = []
    for i in range(values.shape[1]):
        x, y = values[:-1, i], values[1:, i]
        if np.std(x) < 1e-8 or np.std(y) < 1e-8:
            rho.append(0.85); continue
        c = np.corrcoef(x, y)[0, 1]
        rho.append(float(np.clip(np.nan_to_num(c, nan=0.85), 0.20, 0.995)))
    return np.array(rho)


def build_profiles(df: pd.DataFrame) -> Dict[Tuple[int, str], GroupProfile]:
    profiles = {}
    for (user, activity), grp in df.groupby(['User', 'activity'], sort=False):
        s = grp[SENSOR_COLS].to_numpy(dtype=np.float64)
        mean = s.mean(axis=0)
        cov  = stabilize_cov(np.cov(s, rowvar=False))
        rho  = lag1_rho(s)
        icov = stabilize_cov(cov * (1.0 - np.outer(rho, rho)))
        # Apply per-channel scale to mean and bounds (varies Cloud from Codex)
        scaled_mean     = mean     * CHANNEL_SCALE
        scaled_min_vals = s.min(axis=0) * CHANNEL_SCALE
        scaled_max_vals = s.max(axis=0) * CHANNEL_SCALE
        # Sort min/max in case scale flipped sign
        min_vals = np.minimum(scaled_min_vals, scaled_max_vals)
        max_vals = np.maximum(scaled_min_vals, scaled_max_vals)
        profiles[(int(user), str(activity))] = GroupProfile(
            mean=scaled_mean, cov=cov, innovation_cov=icov, lag1_rho=rho,
            min_vals=min_vals, max_vals=max_vals, count=int(len(grp))
        )
    return profiles


def sample_sequence(profile: GroupProfile, n: int, rng: np.random.Generator) -> np.ndarray:
    if n <= 0:
        return np.empty((0, len(SENSOR_COLS)), dtype=np.float32)
    state = np.empty((n, len(SENSOR_COLS)), dtype=np.float64)
    state[0] = rng.multivariate_normal(profile.mean, profile.cov)
    innov = rng.multivariate_normal(np.zeros(len(SENSOR_COLS)), profile.innovation_cov,
                                    size=max(n - 1, 1))
    rho = profile.lag1_rho
    for i in range(1, n):
        state[i] = profile.mean + rho * (state[i-1] - profile.mean) + innov[i-1]
    # Align moments
    cm, cs = state.mean(axis=0), np.clip(state.std(axis=0), 1e-8, None)
    ts = np.sqrt(np.clip(np.diag(profile.cov), 1e-8, None))
    state = ((state - cm) / cs) * ts + profile.mean
    return np.clip(state, profile.min_vals, profile.max_vals).astype(np.float32)


def make_timestamps(start: datetime, n: int) -> List[str]:
    return [(start + timedelta(milliseconds=i * STEP_MS)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            for i in range(n)]


# ── Main generation ───────────────────────────────────────────────────────────
print(f'Loading source: {SOURCE}')
src_df = pd.read_csv(SOURCE)
print(f'  Rows: {len(src_df):,}  Users: {src_df["User"].nunique()}  Classes: {src_df["activity"].nunique()}')

profiles = build_profiles(src_df)

user_order = [int(u) for u in src_df['User'].drop_duplicates()]

# Activity order per user (contiguous blocks)
act_order = {}
for user, grp in src_df.groupby('User', sort=False):
    acts, prev = [], None
    for a in grp['activity']:
        if a != prev:
            acts.append(str(a))
        prev = a
    act_order[int(user)] = acts

chunks = []
base_dt = datetime(2016, 6, 1, 9, 0, 0)

for u_idx, real_user in enumerate(user_order):
    synth_user = real_user + USER_ID_OFFSET
    cur_dt = base_dt + timedelta(days=u_idx)
    u_rng = np.random.default_rng(SEED + synth_user * 1000)

    for a_idx, activity in enumerate(act_order[real_user]):
        profile = profiles[(real_user, activity)]
        n = profile.count
        seq_rng = np.random.default_rng(SEED + synth_user * 1000 + a_idx * 97)
        data = sample_sequence(profile, n, seq_rng)
        chunk = pd.DataFrame(data, columns=SENSOR_COLS)
        chunk['timestamp'] = make_timestamps(cur_dt, n)
        chunk['activity']  = activity
        chunk['User']      = synth_user
        chunks.append(chunk)
        cur_dt += timedelta(milliseconds=n * STEP_MS + GAP_MS)
        _ = u_rng.integers(0, 1_000_000)

synth_df = pd.concat(chunks, ignore_index=True)
synth_df = synth_df[['timestamp'] + SENSOR_COLS + ['activity', 'User']]

# ── Quality check ─────────────────────────────────────────────────────────────
print('\n=== QUALITY CHECK: src vs Synth Cloud v2 ===')
print(f'  Rows:  src={len(src_df):,}  synth={len(synth_df):,}')
print(f'  Users: src={src_df["User"].nunique()}  synth={synth_df["User"].nunique()}')
print()
print(f'  {"Channel":<6}  {"src mean":>10}  {"synt mean":>10}  {"src std":>9}  {"synt std":>9}  {"src max|v|":>10}  {"synt max|v|":>10}')
for col in SENSOR_COLS:
    sm, ss = src_df[col].mean(), src_df[col].std()
    gm, gs = synth_df[col].mean(), synth_df[col].std()
    smx    = src_df[col].abs().max()
    gmx    = synth_df[col].abs().max()
    print(f'  {col:<6}  {sm:>10.3f}  {gm:>10.3f}  {ss:>9.3f}  {gs:>9.3f}  {smx:>10.3f}  {gmx:>10.3f}')

print()
print('=== Activity counts ===')
src_counts  = src_df['activity'].value_counts().sort_index()
synt_counts = synth_df['activity'].value_counts().sort_index()
for act in src_counts.index:
    print(f'  {act:<22}  src={src_counts[act]:>5}  synth={synt_counts.get(act, 0):>5}')

# ── Save ──────────────────────────────────────────────────────────────────────
synth_df.to_csv(OUTPUT, index=False)
print(f'\nSaved to: {OUTPUT}')
print(f'File size: {OUTPUT.stat().st_size / 1e6:.1f} MB')

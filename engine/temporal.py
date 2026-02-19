"""
MullBar — Temporal Analysis (OPTIMIZED)
Computes transaction velocity and burst activity per node.
Uses pre-grouped DataFrames instead of per-node filtering.
"""

import pandas as pd
import numpy as np
import networkx as nx


def compute_temporal_features(G: nx.DiGraph, df: pd.DataFrame) -> dict:
    """
    Compute temporal features for every node.
    Returns dict: account_id -> {velocity, burst_score, avg_interval_hours}
    """
    df_ts = df.copy()
    df_ts["timestamp"] = pd.to_datetime(df_ts["timestamp"])

    # Pre-group timestamps by account (both sent and received)
    account_timestamps = {}
    sent_groups = df_ts.groupby("sender_id")["timestamp"].apply(list)
    recv_groups = df_ts.groupby("receiver_id")["timestamp"].apply(list)

    for node in G.nodes():
        ts_list = []
        if node in sent_groups.index:
            ts_list.extend(sent_groups[node])
        if node in recv_groups.index:
            ts_list.extend(recv_groups[node])
        if ts_list:
            ts_list.sort()
        account_timestamps[node] = ts_list

    results = {}
    for node in G.nodes():
        ts_list = account_timestamps.get(node, [])

        if len(ts_list) < 2:
            results[node] = {
                "velocity": 0.0,
                "burst_score": 0.0,
                "avg_interval_hours": 0.0,
            }
            continue

        # --- Transaction velocity (txns per day) ---
        time_span = (ts_list[-1] - ts_list[0]).total_seconds()
        days = max(time_span / 86400, 0.01)
        velocity = len(ts_list) / days

        # --- Burst activity (sliding window with two-pointer) ---
        # Count max transactions in any 1-hour window using O(n) two-pointer
        max_burst = 1
        hour_ns = np.timedelta64(1, 'h')
        left = 0
        for right in range(len(ts_list)):
            while ts_list[right] - ts_list[left] > hour_ns:
                left += 1
            max_burst = max(max_burst, right - left + 1)

        avg_hourly = len(ts_list) / max(time_span / 3600, 1)
        burst_score = max_burst / max(avg_hourly, 0.01) if avg_hourly > 0 else 0

        # --- Average interval ---
        intervals = [
            (ts_list[i + 1] - ts_list[i]).total_seconds() / 3600
            for i in range(len(ts_list) - 1)
        ]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0

        results[node] = {
            "velocity": round(velocity, 2),
            "burst_score": round(burst_score, 2),
            "avg_interval_hours": round(avg_interval, 2),
        }

    return results

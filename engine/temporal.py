"""
MullBar — Temporal Analysis
Computes transaction velocity and burst activity per node.
"""

import pandas as pd
import networkx as nx
from datetime import timedelta


def compute_temporal_features(G: nx.DiGraph, df: pd.DataFrame) -> dict:
    """
    Compute temporal features for every node.
    Returns dict: account_id -> {velocity, burst_score, avg_interval_hours}
    """
    df_ts = df.copy()
    df_ts["timestamp"] = pd.to_datetime(df_ts["timestamp"])
    results = {}

    for node in G.nodes():
        # Gather all timestamps for this account
        node_txns = df_ts[
            (df_ts["sender_id"] == node) | (df_ts["receiver_id"] == node)
        ].sort_values("timestamp")

        if len(node_txns) < 2:
            results[node] = {
                "velocity": 0.0,
                "burst_score": 0.0,
                "avg_interval_hours": 0.0,
            }
            continue

        timestamps = node_txns["timestamp"].values

        # --- Transaction velocity (txns per day) ---
        time_span = (
            pd.Timestamp(timestamps[-1]) - pd.Timestamp(timestamps[0])
        ).total_seconds()
        days = max(time_span / 86400, 0.01)  # avoid div zero
        velocity = len(node_txns) / days

        # --- Burst activity ---
        # Count max transactions in any 1-hour window
        max_burst = 0
        for i in range(len(timestamps)):
            start = pd.Timestamp(timestamps[i])
            end = start + timedelta(hours=1)
            burst_count = ((node_txns["timestamp"] >= start) & (node_txns["timestamp"] <= end)).sum()
            max_burst = max(max_burst, burst_count)

        # Normalize burst: ratio of max-hourly-burst to average hourly rate
        avg_hourly = len(node_txns) / max(time_span / 3600, 1)
        burst_score = max_burst / max(avg_hourly, 0.01) if avg_hourly > 0 else 0

        # --- Average interval ---
        intervals = [
            (pd.Timestamp(timestamps[i + 1]) - pd.Timestamp(timestamps[i])).total_seconds() / 3600
            for i in range(len(timestamps) - 1)
        ]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0

        results[node] = {
            "velocity": round(velocity, 2),
            "burst_score": round(burst_score, 2),
            "avg_interval_hours": round(avg_interval, 2),
        }

    return results

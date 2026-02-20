"""
MullBar — Temporal Analysis (VECTORIZED)
Computes transaction velocity and burst activity per node using optimized Pandas operations.
"""

import pandas as pd
import numpy as np
import networkx as nx


def compute_temporal_features(G: nx.DiGraph, df: pd.DataFrame) -> dict:
    """
    Compute temporal features for every node.
    Returns dict: account_id -> {velocity, burst_score, avg_interval_hours}
    """
    if df.empty:
        return {}

    # 1. Prepare Long-Format Data (Sender + Receiver combined)
    # We need a single stream of timestamps per account
    sent = df[["sender_id", "timestamp"]].rename(columns={"sender_id": "account_id"})
    recv = df[["receiver_id", "timestamp"]].rename(columns={"receiver_id": "account_id"})
    
    all_txns = pd.concat([sent, recv], ignore_index=True)
    all_txns["timestamp"] = pd.to_datetime(all_txns["timestamp"])
    
    # Sort for rolling operations
    all_txns = all_txns.sort_values(["account_id", "timestamp"])

    # 2. Compute Basic Stats (Count, Time Span, Velocity)
    # Aggregation per account
    stats = all_txns.groupby("account_id")["timestamp"].agg(["min", "max", "count"])
    
    # Avoid division by zero: clip min duration to 0.01 days (~15 mins)
    stats["days"] = (stats["max"] - stats["min"]).dt.total_seconds() / 86400
    stats["days"] = stats["days"].clip(lower=0.01) 
    
    stats["velocity"] = stats["count"] / stats["days"]
    stats["avg_hourly_rate"] = stats["count"] / (stats["days"] * 24)

    # 3. Compute Burst Score (Rolling Time Window)
    # We set index to timestamp to use time-aware rolling
    # We group by account_id to isolate bursts per account
    
    # Note: We must ensure index is sorted (it is).
    # We use a dummy column to count.
    temp_df = all_txns.set_index("timestamp")
    
    # .rolling('1h') on groupby object looks at time index
    # .count() counts non-null values in window
    # We group again by account_id to find the MAX burst peak for each account
    max_bursts = temp_df.groupby("account_id")["account_id"].rolling("1h").count().groupby("account_id").max()
    
    stats["max_burst"] = max_bursts
    
    # Burst Score = Peak Rate / Average Rate
    # Handle zero average rate (though count >= 1 implies avg > 0 due to clip)
    stats["burst_score"] = stats["max_burst"] / stats["avg_hourly_rate"].clip(lower=0.01)

    # 4. Compute Average Interval
    # diff() computes time between consecutive transactions per group
    all_txns["interval_hours"] = all_txns.groupby("account_id")["timestamp"].diff().dt.total_seconds() / 3600
    avg_intervals = all_txns.groupby("account_id")["interval_hours"].mean()
    
    stats["avg_interval_hours"] = avg_intervals.fillna(0)

    # 5. Format Results
    # Convert to dictionary {account_id: {...}}
    # We use round() to keep JSON clean
    
    results = {}
    for acc_id, row in stats.iterrows():
         results[acc_id] = {
             "velocity": round(row["velocity"], 2),
             "burst_score": round(row["burst_score"], 2),
             "avg_interval_hours": round(row["avg_interval_hours"], 2)
         }

    # Ensure all graph nodes are in results (handle isolated nodes with no txns? Graph build guarantees edges)
    # But just in case
    for n in G.nodes():
        if n not in results:
            results[n] = {"velocity": 0.0, "burst_score": 0.0, "avg_interval_hours": 0.0}
            
    return results
